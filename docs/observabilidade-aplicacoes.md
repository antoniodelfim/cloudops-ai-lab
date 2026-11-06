# Aplicações, pilares e dashboards

## Estado

O dashboard de infraestrutura já recebe dados reais do cluster. Os três dashboards de aplicações são estruturas provisionadas, com consultas e roteiro de diagnóstico; aguardam a implementação das aplicações. Não demonstram incidentes nem resoluções executadas. Painéis sem dados não indicam saúde.

Cada aplicação terá os três sinais; a divisão abaixo define o foco pedagógico, sem perder correlação.

| Aplicação | Foco | Problemas a reproduzir | Dashboard |
| --- | --- | --- | --- |
| Checkout API + order-worker | Métricas | Latência de dependência, reentrega e deployment regressivo | /d/cloudops-checkout |
| Processamento de arquivos + file-worker | Logs | Backlog, OOM e mensagem inválida | /d/cloudops-files |
| Webhook API + webhook-worker + partner-mock | Traces | 429, timeout e credencial rotacionada | /d/cloudops-webhooks |

## Contratos de instrumentação a implementar

- service.name: checkout-api, order-worker, file-worker, webhook-worker e partner-mock; o mapeamento em Prometheus/Loki usa service_name.
- Checkout: lab_http_requests_total com status_class de valores limitados e lab_http_request_duration_seconds como histograma em segundos. Excluir health checks do recorte de negócio e inicializar as classes esperadas com zero para distinguir ausência de erro de ausência da série.
- Processamento: lab_oldest_pending_job_age_seconds mede a idade do trabalho pendente mais antigo, com zero apenas quando a fila foi consultada e está vazia. Falha de consulta não deve virar zero.
- Webhooks: lab_webhook_delivery_attempts_total com outcome limitado a success, rate_limited, timeout, unauthorized e failed.
- Logs: corpo JSON com level, event, message, timestamp UTC, service/version e trace_id; job_id/order_id em campos, nunca em labels de métricas. Eventos incluem retry_scheduled e quarantined.
- Traces: contexto propagado via HTTP e atributos Pub/Sub; spans de publicação, consumo, processamento, Storage e chamada ao parceiro. status=error em falha e atributo http.response.status_code quando aplicável.

Os nomes lab_* são contratos didáticos próprios, não nomes automaticamente gerados por um SDK. A implementação terá de exportá-los exatamente nesse formato ou atualizar consultas e testes juntos.

O filtro de trace acima de 500 ms é exploratório, não um SLO definido. Percentis não são calculados a partir da média. Uma proporção de erros sem tráfego deve permanecer sem valor, em vez de aparentar 0% saudável.

## Estrutura dos painéis

Cada dashboard contém estado explícito, cenários associados e seis painéis. Checkout prioriza tráfego, erros e p95; arquivos prioriza eventos, erros e tentativas; webhooks prioriza busca por traces lentos, com erro e com 429. Os sinais complementares permitem confirmar hipóteses.

Consulta de trace abre a investigação detalhada no Tempo/Grafana. A correlação automática clicável entre todos os sinais ainda é uma entrega futura: presença de trace_id não equivale a links já configurados.

## Aceite por aplicação

1. Executar fluxo saudável com carga sintética e confirmar dados nos três backends.
2. Validar métricas e logs contra resultados funcionais conhecidos; verificar unidade, cardinalidade e propagação de contexto.
3. Injetar apenas uma falha, registrar início e mudança de versão/configuração.
4. Demonstrar sintoma no painel principal e investigar com os sinais complementares.
5. Aplicar mitigação/correção, repetir a mesma carga e comparar o resultado.
6. Publicar evidências e postmortem; só então remover a faixa aguardando instrumentação.

Ordem: checkout saudável → primeiro caso A03 completo → A01/A02 → processamento de arquivos → webhooks. Não preencher painéis com zeros ou fixtures para aparentar aplicação funcionando.

## Manutenção

Dashboards são definidos em scripts/dashboards.py e provisionados pelo bootstrap. Reaplicar com python scripts/infra.py up. O Grafana observa os arquivos provisionados; pode levar cerca de um minuto para refletir a atualização do ConfigMap. Não editar apenas pela interface e perder a versão em Git.
