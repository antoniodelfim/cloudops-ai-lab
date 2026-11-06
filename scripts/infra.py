"""Infraestrutura local. Python 3.11+, sem bibliotecas externas."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request
from dashboards import dashboards

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / '.state'
CONTEXT = 'kind-cloudops-ai-lab'
CLUSTER = 'cloudops-ai-lab'
IMAGES = {
    'floci-gcp': 'floci/floci-gcp:0.12.0',
    'prometheus': 'prom/prometheus:v3.16.0',
    'grafana': 'grafana/grafana:13.3.0',
    'loki': 'grafana/loki:3.7.9',
    'tempo': 'grafana/tempo:3.1.1',
    'otel-collector': 'otel/opentelemetry-collector-contrib:0.164.0',
    'alertmanager': 'prom/alertmanager:v0.34.2',
    'kube-state-metrics': 'registry.k8s.io/kube-state-metrics/kube-state-metrics:v2.20.0',
}


def tool(name):
    candidates = [ROOT / '.tools' / (name + '.exe'), ROOT / '.tools' / name]
    if name == 'kind':
        candidates.insert(0, ROOT / '.tools' / 'kind-windows-amd64.exe')
    return str(next((p for p in candidates if p.exists()), shutil.which(name) or name))


def run(args, **kwargs):
    print('> ' + ' '.join(map(str, args)), flush=True)
    return subprocess.run(list(map(str, args)), cwd=ROOT, check=True, **kwargs)


def kube(*args, **kwargs):
    # Sempre seleciona o contexto do laboratório, independentemente do contexto atual.
    return run([tool('kubectl'), '--kubeconfig', STATE / 'kubeconfig', '--context', CONTEXT, *args], **kwargs)


def obj(kind, name, ns, **fields):
    return {'apiVersion': 'v1', 'kind': kind,
            'metadata': {'name': name, 'namespace': ns, 'labels': {'app.kubernetes.io/part-of': CLUSTER}}, **fields}


def manifests():
    items = []
    for ns in ('cloud', 'observability', 'apps', 'ai-tools'):
        items.append({'apiVersion': 'v1', 'kind': 'Namespace', 'metadata': {'name': ns}})
    configs = {
        'prometheus': ('prometheus.yml', '''global:
  scrape_interval: 15s
scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: ['localhost:9090']
  - job_name: otel-applications
    static_configs:
      - targets: ['otel-collector:8889']
  - job_name: kubernetes-state
    static_configs:
      - targets: ['kube-state-metrics:8080']
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
rule_files: ['/config/alerts.yml']
'''),
        'alertmanager': ('alertmanager.yml', '''route:
  receiver: local
  group_by: [alertname, namespace]
  group_wait: 10s
  group_interval: 1m
  repeat_interval: 1h
receivers:
  - name: local
'''),
        'loki': ('loki.yaml', '''auth_enabled: false
server:
  http_listen_port: 3100
common:
  path_prefix: /data
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory
  storage:
    filesystem:
      chunks_directory: /data/chunks
      rules_directory: /data/rules
schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h
limits_config:
  allow_structured_metadata: true
  retention_period: 24h
compactor:
  working_directory: /data/compactor
  retention_enabled: true
  delete_request_store: filesystem
'''),
        'tempo': ('tempo.yaml', '''server:
  http_listen_port: 3200
distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317
        http:
          endpoint: 0.0.0.0:4318
storage:
  trace:
    backend: local
    local:
      path: /data/blocks
    wal:
      path: /data/wal
overrides:
  defaults:
    compaction:
      block_retention: 24h
usage_report:
  reporting_enabled: false
'''),
        'otel-collector': ('collector.yaml', '''receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 192
  batch: {}
exporters:
  prometheus:
    endpoint: 0.0.0.0:8889
    resource_to_telemetry_conversion:
      enabled: true
  otlphttp/loki:
    endpoint: http://loki:3100/otlp
  otlp/tempo:
    endpoint: tempo:4317
    tls:
      insecure: true
extensions:
  health_check:
    endpoint: 0.0.0.0:13133
service:
  extensions: [health_check]
  pipelines:
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlphttp/loki]
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/tempo]
'''),
        'grafana': ('datasources.yaml', '''apiVersion: 1
datasources:
  - name: Prometheus
    uid: prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
  - name: Loki
    uid: loki
    type: loki
    access: proxy
    url: http://loki:3100
  - name: Tempo
    uid: tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
''')}
    specs = {
        'floci-gcp': ('cloud', [(4588, 30588)], [], None, '/'),
        'prometheus': ('observability', [(9090, 30900)], ['--config.file=/config/prometheus.yml', '--storage.tsdb.path=/data', '--storage.tsdb.retention.time=24h'], '/config', '/-/ready'),
        'loki': ('observability', [(3100, 30310)], ['-config.file=/config/loki.yaml'], '/config', '/ready'),
        'tempo': ('observability', [(3200, 30320), (4317, None)], ['-config.file=/config/tempo.yaml'], '/config', '/ready'),
        'otel-collector': ('observability', [(4317, None), (4318, 30418), (8889, None), (13133, None)], ['--config=/config/collector.yaml'], '/config', '/'),
        'grafana': ('observability', [(3000, 30300)], [], '/etc/grafana/provisioning/datasources', '/api/health'),
        'alertmanager': ('observability', [(9093, None)], ['--config.file=/config/alertmanager.yml', '--storage.path=/data', '--cluster.listen-address='], '/config', '/-/ready'),
        'kube-state-metrics': ('observability', [(8080, None)], ['--namespaces=apps,cloud,observability,ai-tools', '--resources=pods,deployments,replicasets,persistentvolumeclaims'], None, '/healthz'),
    }
    for name, (ns, ports, args, mount, health) in specs.items():
        persistent = name not in ('otel-collector', 'kube-state-metrics')
        volumes, mounts = [], []
        if name in configs:
            filename, content = configs[name]
            config_data = {filename: content}
            if name == 'prometheus':
                config_data['alerts.yml'] = '''groups:
  - name: infrastructure
    rules:
      - alert: TelemetryTargetDown
        expr: up == 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: Alvo de coleta indisponivel
      - alert: KubernetesDeploymentUnavailable
        expr: kube_deployment_status_replicas_unavailable > 0
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: Deployment com replicas indisponiveis
'''
            items.append(obj('ConfigMap', name, ns, data=config_data))
            volumes.append({'name': 'config', 'configMap': {'name': name}})
            mounts.append({'name': 'config', 'mountPath': mount, 'readOnly': True})
        if persistent:
            items.append(obj('PersistentVolumeClaim', name, ns, spec={
                'accessModes': ['ReadWriteOnce'], 'resources': {'requests': {'storage': '2Gi'}}}))
            volumes.append({'name': 'data', 'persistentVolumeClaim': {'claimName': name}})
            mounts.append({'name': 'data', 'mountPath': '/app/data' if name == 'floci-gcp' else '/var/lib/grafana' if name == 'grafana' else '/data'})
        container = {'name': name, 'image': IMAGES[name], 'args': args,
                     'ports': [{'containerPort': p} for p, _ in ports], 'volumeMounts': mounts,
                     'resources': {'requests': {'cpu': '100m', 'memory': '128Mi'}, 'limits': {'cpu': '1000m', 'memory': '768Mi' if name == 'floci-gcp' else '512Mi'}},
                     'securityContext': {'allowPrivilegeEscalation': False, 'capabilities': {'drop': ['ALL']}}}
        if name == 'floci-gcp':
            container['securityContext'].update({'runAsUser': 1001, 'runAsGroup': 0, 'runAsNonRoot': True})
            container['env'] = [{'name': 'FLOCI_GCP_STORAGE_MODE', 'value': 'hybrid'},
                                {'name': 'FLOCI_GCP_DEFAULT_PROJECT_ID', 'value': 'cloudops-local'}]
        if name == 'grafana':
            dashboard = {'uid': 'cloudops-infrastructure', 'title': 'CloudOps — Infraestrutura local', 'schemaVersion': 39, 'version': 1,
                         'time': {'from': 'now-30m', 'to': 'now'}, 'refresh': '15s', 'panels': []}
            for i, (title, expr) in enumerate([
                ('Alvos de coleta ativos', 'up'),
                ('Replicas disponiveis', 'kube_deployment_status_replicas_available'),
                ('Reinicios de containers', 'kube_pod_container_status_restarts_total'),
                ('Sonda OTLP', 'cloudops_infra_probe')]):
                dashboard['panels'].append({'id': i + 1, 'type': 'timeseries', 'title': title,
                    'gridPos': {'x': (i % 2) * 12, 'y': (i // 2) * 8, 'w': 12, 'h': 8},
                    'datasource': {'type': 'prometheus', 'uid': 'prometheus'}, 'targets': [{'expr': expr, 'refId': 'A'}]})
            dashboard_files = {'infrastructure.json': json.dumps(dashboard)}
            dashboard_files.update({d['uid'] + '.json': json.dumps(d) for d in dashboards()})
            items.append(obj('ConfigMap', 'grafana-dashboards', ns, data=dashboard_files))
            items.append(obj('ConfigMap', 'grafana-dashboard-provider', ns, data={'provider.yaml': '''apiVersion: 1
providers:
  - name: cloudops
    type: file
    options:
      path: /dashboards
'''}))
            volumes.extend([{'name': 'dashboards', 'configMap': {'name': 'grafana-dashboards'}},
                            {'name': 'dashboard-provider', 'configMap': {'name': 'grafana-dashboard-provider'}}])
            mounts.extend([{'name': 'dashboards', 'mountPath': '/dashboards', 'readOnly': True},
                           {'name': 'dashboard-provider', 'mountPath': '/etc/grafana/provisioning/dashboards', 'readOnly': True}])
            container['env'] = [{'name': 'GF_AUTH_ANONYMOUS_ENABLED', 'value': 'true'},
                                {'name': 'GF_AUTH_ANONYMOUS_ORG_ROLE', 'value': 'Viewer'},
                                {'name': 'GF_SECURITY_ADMIN_PASSWORD', 'valueFrom': {'secretKeyRef': {'name': 'grafana-admin', 'key': 'password'}}}]
        if name == 'kube-state-metrics':
            items.append(obj('ServiceAccount', name, ns))
            for target_ns in ('apps', 'cloud', 'observability', 'ai-tools'):
                items.append({'apiVersion': 'rbac.authorization.k8s.io/v1', 'kind': 'Role', 'metadata': {'name': name, 'namespace': target_ns}, 'rules': [
                    {'apiGroups': [''], 'resources': ['pods', 'persistentvolumeclaims'], 'verbs': ['list', 'watch']},
                    {'apiGroups': ['apps'], 'resources': ['deployments', 'replicasets'], 'verbs': ['list', 'watch']}]})
                items.append({'apiVersion': 'rbac.authorization.k8s.io/v1', 'kind': 'RoleBinding', 'metadata': {'name': name, 'namespace': target_ns},
                              'subjects': [{'kind': 'ServiceAccount', 'name': name, 'namespace': ns}],
                              'roleRef': {'apiGroup': 'rbac.authorization.k8s.io', 'kind': 'Role', 'name': name}})
        hp = 13133 if name == 'otel-collector' else ports[0][0]
        probe = {'tcpSocket': {'port': hp}} if name == 'floci-gcp' else {'httpGet': {'path': health, 'port': hp}}
        container['readinessProbe'] = {**probe, 'periodSeconds': 5, 'failureThreshold': 12}
        container['startupProbe'] = {**probe, 'periodSeconds': 5, 'failureThreshold': 60}
        items.append({'apiVersion': 'apps/v1', 'kind': 'Deployment', 'metadata': {'name': name, 'namespace': ns},
                      'spec': {'replicas': 1, 'strategy': {'type': 'Recreate'}, 'selector': {'matchLabels': {'app': name}},
                               'template': {'metadata': {'labels': {'app': name}, 'annotations': {
                                   'cloudops/config-hash': hashlib.sha256(json.dumps(configs.get(name, '')).encode()).hexdigest()}}, 'spec': {
                                   'automountServiceAccountToken': name == 'kube-state-metrics',
                                   'enableServiceLinks': False,
                                   **({'serviceAccountName': name} if name == 'kube-state-metrics' else {}),
                                   'securityContext': {'fsGroup': 1001 if name == 'floci-gcp' else 472 if name == 'grafana' else 10001 if name in ('loki', 'tempo') else 65534},
                                   'containers': [container], 'volumes': volumes}}}})
        items.append(obj('Service', name, ns, spec={'type': 'NodePort' if any(np for _, np in ports) else 'ClusterIP', 'selector': {'app': name},
                     'ports': [{'name': f'p{p}', 'port': p, 'targetPort': p, **({'nodePort': np} if np else {})} for p, np in ports]}))
    items.extend([
        obj('ServiceAccount', 'incident-investigator', 'ai-tools'),
        {'apiVersion': 'rbac.authorization.k8s.io/v1', 'kind': 'Role', 'metadata': {'name': 'incident-investigator', 'namespace': 'apps'},
         'rules': [{'apiGroups': [''], 'resources': ['pods', 'events'], 'verbs': ['get', 'list']},
                   {'apiGroups': ['apps'], 'resources': ['deployments', 'replicasets'], 'verbs': ['get', 'list']}]},
        {'apiVersion': 'rbac.authorization.k8s.io/v1', 'kind': 'RoleBinding', 'metadata': {'name': 'incident-investigator', 'namespace': 'apps'},
         'subjects': [{'kind': 'ServiceAccount', 'name': 'incident-investigator', 'namespace': 'ai-tools'}],
         'roleRef': {'apiGroup': 'rbac.authorization.k8s.io', 'kind': 'Role', 'name': 'incident-investigator'}}])
    return {'apiVersion': 'v1', 'kind': 'List', 'items': items}


def wait_http(url, timeout=180):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    print('OK ' + url, flush=True)
                    return
        except (OSError, ValueError):
            pass
        time.sleep(3)
    raise RuntimeError('Endpoint indisponível: ' + url)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['render', 'up', 'gitops', 'status', 'test', 'down'])
    args = parser.parse_args()
    STATE.mkdir(exist_ok=True)
    manifest = STATE / 'infrastructure.json'
    manifest.write_text(json.dumps(manifests(), indent=2), encoding='utf-8')
    if args.action == 'render':
        print(manifest)
    elif args.action == 'up':
        run(['docker', 'info'], stdout=subprocess.DEVNULL)
        clusters = run([tool('kind'), 'get', 'clusters'], capture_output=True, text=True).stdout.splitlines()
        if CLUSTER not in clusters:
            config = ROOT / 'infra/kind.yaml'
            cgroup = run(['docker', 'info', '--format', '{{.CgroupVersion}}'], capture_output=True, text=True).stdout.strip()
            if cgroup != '2':
                raise RuntimeError('Este laboratório exige cgroup v2. Atualize WSL/Docker e reinicie o Docker antes de continuar.')
            run([tool('kind'), 'create', 'cluster', '--name', CLUSTER, '--image', 'kindest/node:v1.35.5', '--config', config, '--kubeconfig', STATE / 'kubeconfig', '--wait', '180s'])
        else:
            run([tool('kind'), 'export', 'kubeconfig', '--name', CLUSTER, '--kubeconfig', STATE / 'kubeconfig'])
        kube('apply', '-f', '-', input=json.dumps({'apiVersion': 'v1', 'kind': 'Namespace', 'metadata': {'name': 'observability'}}), text=True)
        import secrets
        secret = STATE / 'grafana-password'
        if not secret.exists():
            secret.write_text(secrets.token_urlsafe(24), encoding='utf-8')
        # O segredo não é impresso nem passado como argumento de processo.
        import base64
        data = obj('Secret', 'grafana-admin', 'observability', data={'password': base64.b64encode(secret.read_bytes()).decode()})
        kube('apply', '-f', '-', input=json.dumps(data), text=True)
        kube('apply', '-f', manifest)
        for ns in ('cloud', 'observability'):
            kube('-n', ns, 'wait', '--for=condition=Available', 'deployment', '--all', '--timeout=300s')
        print('Infra aplicada. Execute: python scripts/infra.py test')
    elif args.action == 'gitops':
        kube('apply', '-f', '-', input=json.dumps({'apiVersion': 'v1', 'kind': 'Namespace', 'metadata': {'name': 'argocd'}}), text=True)
        url = 'https://raw.githubusercontent.com/argoproj/argo-cd/v3.6.1/manifests/install.yaml'
        vendor = STATE / 'argocd-v3.6.1.yaml'
        with urllib.request.urlopen(url, timeout=60) as response:
            vendor.write_bytes(response.read())
        kube('apply', '--server-side', '-n', 'argocd', '-f', vendor)
        kube('-n', 'argocd', 'wait', '--for=condition=Available', 'deployment', '--all', '--timeout=300s')
        kube('-n', 'argocd', 'rollout', 'status', 'statefulset/argocd-application-controller', '--timeout=300s')
    elif args.action == 'status':
        kube('get', 'nodes', '-o', 'wide')
        kube('get', 'pods,pvc,svc', '-A')
    elif args.action == 'test':
        for port, path in [(3000, '/api/health'), (9090, '/-/ready'), (3100, '/ready'), (3200, '/ready')]:
            wait_http(f'http://127.0.0.1:{port}{path}')
        run([sys.executable, ROOT / 'scripts/smoke.py'])
    elif args.action == 'down':
        # Destrói exclusivamente o cluster de nome fixo deste laboratório e seus volumes.
        run([tool('kind'), 'delete', 'cluster', '--name', CLUSTER])


if __name__ == '__main__':
    main()
