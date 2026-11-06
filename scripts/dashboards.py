"""Dashboards versionados e contratos de observabilidade das aplicações futuras."""
def panel(pid, title, source, query, x, y, kind='timeseries', unit=None):
    target = {'refId': 'A', 'expr': query, 'query': query}
    if source == 'tempo':
        target.update({'queryType': 'traceql', 'limit': 20})
    ds = {'type': {'prometheus': 'prometheus', 'loki': 'loki', 'tempo': 'tempo'}[source], 'uid': source}
    return {'id': pid, 'title': title, 'type': kind, 'datasource': ds,
            'gridPos': {'x': x, 'y': y, 'w': 12, 'h': 8}, 'targets': [target],
            'fieldConfig': {'defaults': {'unit': unit or 'short'}, 'overrides': []}, 'options': {}}


def application_dashboard(uid, title, focus, scenarios, panels):
    return {'uid': uid, 'title': title, 'schemaVersion': 39, 'version': 1,
            'tags': ['cloudops', 'aplicacoes', 'aguardando-instrumentacao'],
            'time': {'from': 'now-30m', 'to': 'now'}, 'refresh': '15s',
            'description': 'Estrutura provisionada; aplicação e instrumentação ainda não implementadas.',
            'links': [{'title': 'Infraestrutura', 'type': 'link', 'url': '/d/cloudops-infrastructure'}],
            'panels': [{'id': 100, 'type': 'text', 'title': 'Estado e roteiro de investigação',
                        'gridPos': {'x': 0, 'y': 0, 'w': 24, 'h': 5},
                        'options': {'mode': 'markdown', 'content':
                            '**Aguardando a aplicação e sua instrumentação.** Painéis vazios não significam ambiente saudável.\n\n'
                            + '**Foco:** ' + focus + '\n\n**Cenários:** ' + scenarios
                            + '\n\nInvestigar: sintoma → logs/traces → mudança recente → mitigação → teste de recuperação.\n'
                            + 'Contratos e limites: docs/observabilidade-aplicacoes.md no repositório.'}}, *panels]}


def dashboards():
    checkout = application_dashboard('cloudops-checkout', 'CloudOps — Checkout / Métricas',
        'Tráfego, erros e latência; não substituir ausência de dados por zero.',
        'A01: dependência lenta; A02: reentrega; A03: deployment regressivo.', [
            panel(1, 'Requisições por segundo', 'prometheus', 'sum(rate(lab_http_requests_total{service_name="checkout-api"}[2m]))', 0, 5, unit='reqps'),
            panel(2, 'Proporção de erros 5xx', 'prometheus', 'sum(rate(lab_http_requests_total{service_name="checkout-api",status_class="5xx"}[2m])) / sum(rate(lab_http_requests_total{service_name="checkout-api"}[2m]))', 12, 5, unit='percentunit'),
            panel(3, 'Latência p95', 'prometheus', 'histogram_quantile(0.95, sum by (le) (rate(lab_http_request_duration_seconds_bucket{service_name="checkout-api"}[2m])))', 0, 13, unit='s'),
            panel(4, 'Reinícios de pods — namespace apps', 'prometheus', 'sum by (pod) (kube_pod_container_status_restarts_total{namespace="apps"})', 12, 13),
            panel(5, 'Logs correlacionáveis do checkout', 'loki', '{service_name="checkout-api"}', 0, 21, 'logs'),
            panel(6, 'Traces de checkout com erro', 'tempo', '{resource.service.name="checkout-api" && status=error}', 12, 21, 'table')])
    files = application_dashboard('cloudops-files', 'CloudOps — Processamento / Logs',
        'Eventos estruturados, falhas, tentativas e causa do processamento interrompido.',
        'B01: backlog; B02: memória; B03: mensagem inválida e quarentena.', [
            panel(1, 'Eventos do worker', 'loki', '{service_name="file-worker"}', 0, 5, 'logs'),
            panel(2, 'Erros estruturados', 'loki', '{service_name="file-worker"} | json | level="ERROR" | __error__=""', 12, 5, 'logs'),
            panel(3, 'Erros por segundo', 'loki', 'sum(rate({service_name="file-worker"} | json | level="ERROR" | __error__="" [2m]))', 0, 13),
            panel(4, 'Tentativas e quarentena', 'loki', '{service_name="file-worker"} | json | event=~"retry_scheduled|quarantined" | __error__=""', 12, 13, 'logs'),
            panel(5, 'Idade do trabalho mais antigo', 'prometheus', 'lab_oldest_pending_job_age_seconds{service_name="file-worker"}', 0, 21, unit='s'),
            panel(6, 'Traces de processamento com erro', 'tempo', '{resource.service.name="file-worker" && status=error}', 12, 21, 'table')])
    hooks = application_dashboard('cloudops-webhooks', 'CloudOps — Webhooks / Traces',
        'Caminho distribuído, spans lentos, erros e tentativas de entrega.',
        'C01: parceiro 429; C02: timeout/indisponibilidade; C03: credencial rotacionada.', [
            panel(1, 'Traces de entrega', 'tempo', '{resource.service.name="webhook-worker"}', 0, 5, 'table'),
            panel(2, 'Spans acima de 500 ms — filtro exploratório', 'tempo', '{resource.service.name="webhook-worker" && duration>500ms}', 12, 5, 'table'),
            panel(3, 'Traces com erro', 'tempo', '{resource.service.name="webhook-worker" && status=error}', 0, 13, 'table'),
            panel(4, 'Respostas 429 do parceiro', 'tempo', '{resource.service.name="webhook-worker" && span.http.response.status_code=429}', 12, 13, 'table'),
            panel(5, 'Tentativas de entrega por segundo', 'prometheus', 'sum by (outcome) (rate(lab_webhook_delivery_attempts_total{service_name="webhook-worker"}[2m]))', 0, 21),
            panel(6, 'Logs de entrega e trace_id', 'loki', '{service_name="webhook-worker"}', 12, 21, 'logs')])
    return [checkout, files, hooks]
