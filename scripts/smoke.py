"""Contratos locais de Storage/PubSub e telemetria OTLP real, sem SDK ou cloud."""
import base64
import json
import time
import urllib.parse
import urllib.request
import uuid


def request(url, method='GET', data=None, raw=None, content_type='application/json'):
    body = raw if raw is not None else json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method, headers={'Content-Type': content_type})
    with urllib.request.urlopen(req, timeout=15) as response:
        payload = response.read()
        if not payload:
            return {}
        try:
            return json.loads(payload)
        except ValueError:
            return payload


def eventually(check, timeout=90):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if check():
                return
        except (OSError, KeyError, ValueError):
            pass
        time.sleep(2)
    raise AssertionError('Condição não atingida dentro do limite')


def cloud():
    host = 'http://127.0.0.1:4588'
    tag = uuid.uuid4().hex[:12]
    bucket = 'smoke-' + tag
    topic = f'projects/cloudops-local/topics/smoke-{tag}'
    subscription = f'projects/cloudops-local/subscriptions/smoke-{tag}'
    message = 'cloudops-infra-' + tag
    created = []
    try:
        request(host + '/storage/v1/b?project=cloudops-local', 'POST', {'name': bucket})
        created.append(host + '/storage/v1/b/' + bucket)
        request(host + f'/upload/storage/v1/b/{bucket}/o?uploadType=media&name=health.txt', 'POST', raw=message.encode(), content_type='text/plain')
        created.append(host + f'/storage/v1/b/{bucket}/o/health.txt')
        assert request(host + f'/storage/v1/b/{bucket}/o/health.txt?alt=media') == message.encode()
        request(host + '/v1/' + topic, 'PUT', {})
        created.append(host + '/v1/' + topic)
        request(host + '/v1/' + subscription, 'PUT', {'topic': topic})
        created.append(host + '/v1/' + subscription)
        request(host + '/v1/' + topic + ':publish', 'POST', {'messages': [{'data': base64.b64encode(message.encode()).decode()}]})
        received = request(host + '/v1/' + subscription + ':pull', 'POST', {'maxMessages': 1})['receivedMessages'][0]
        assert base64.b64decode(received['message']['data']).decode() == message
        request(host + '/v1/' + subscription + ':acknowledge', 'POST', {'ackIds': [received['ackId']]})
        print('PASS Storage: criar/upload/download; PubSub: criar/publicar/consumir/ack', flush=True)
    finally:
        errors = []
        for url in reversed(created):
            try:
                request(url, 'DELETE')
            except OSError as exc:
                errors.append(str(exc))
        if errors:
            raise RuntimeError('Falha na limpeza: ' + '; '.join(errors))
        print('PASS limpeza dos recursos temporários', flush=True)


def telemetry():
    now = time.time_ns()
    marker = 'infra-smoke-' + uuid.uuid4().hex[:12]
    trace_id = uuid.uuid4().hex
    span_id = uuid.uuid4().hex[:16]
    metric_value = int(uuid.uuid4().hex[:8], 16)
    resource = {'attributes': [{'key': 'service.name', 'value': {'stringValue': 'infra-smoke'}}]}
    base = 'http://127.0.0.1:4318/v1/'
    request(base + 'traces', 'POST', {'resourceSpans': [{'resource': resource, 'scopeSpans': [{'spans': [{
        'traceId': trace_id, 'spanId': span_id, 'name': marker, 'kind': 1,
        'startTimeUnixNano': str(now), 'endTimeUnixNano': str(now + 1000000), 'status': {'code': 1}}]}]}]})
    request(base + 'logs', 'POST', {'resourceLogs': [{'resource': resource, 'scopeLogs': [{'logRecords': [{
        'timeUnixNano': str(now), 'severityNumber': 9, 'severityText': 'INFO',
        'traceId': trace_id, 'spanId': span_id, 'body': {'stringValue': marker}}]}]}]})
    request(base + 'metrics', 'POST', {'resourceMetrics': [{'resource': resource, 'scopeMetrics': [{'metrics': [{
        'name': 'cloudops_infra_probe', 'gauge': {'dataPoints': [{'timeUnixNano': str(now), 'asInt': str(metric_value)}]}}]}]}]})
    eventually(lambda: marker in json.dumps(request('http://127.0.0.1:3200/api/traces/' + trace_id)))
    query = urllib.parse.quote('{service_name="infra-smoke"} |= "' + marker + '"')
    eventually(lambda: marker in json.dumps(request('http://127.0.0.1:3100/loki/api/v1/query_range?query=' + query)))
    eventually(lambda: any(float(row['value'][1]) == metric_value for row in request(
        'http://127.0.0.1:9090/api/v1/query?query=cloudops_infra_probe')['data']['result']))
    eventually(lambda: bool(request('http://127.0.0.1:9090/api/v1/query?query=kube_deployment_status_replicas_available')['data']['result']))
    dashboard = request('http://127.0.0.1:3000/api/dashboards/uid/cloudops-infrastructure')
    assert dashboard['dashboard']['uid'] == 'cloudops-infrastructure'
    print('PASS OTLP: trace consultável no Tempo, log no Loki e métrica no Prometheus', flush=True)
    print('trace_id=' + trace_id, flush=True)
    print('PASS dashboard Grafana e metricas de estado Kubernetes', flush=True)


if __name__ == '__main__':
    cloud()
    telemetry()
