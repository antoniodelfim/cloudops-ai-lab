# Compatibilidade e evidências — infraestrutura local

Validação inicial: 6 de novembro de 2026. Dados sintéticos; sem conta ou credenciais GCP. Esta evidência não representa GKE real nem validação de produção.

## Ambiente

- Windows, Docker Desktop com backend WSL 2 e cgroup v2.
- WSL atualizado de 2.1.5 para 3.0.3; kernel em uso 6.18.54.1-microsoft-standard-WSL2.
- kind 0.33.0, Kubernetes 1.35.5, kubectl 1.35.5.
- floci-gcp 0.12.0 e provider hashicorp/google 8.10.0.
- Terraform 1.11.2 e Python 3.13 na máquina de validação.
- OpenTelemetry Collector Contrib 0.164.0; Prometheus 3.16.0; Loki 3.7.9; Tempo 3.1.1; Grafana 13.3.0; Alertmanager 0.34.2; kube-state-metrics 2.20.0; Argo CD 3.6.1.

## Matriz inicial

| Operação | Caminho | Resultado observado |
| --- | --- | --- |
| Bucket criar/excluir | Storage REST, smoke.py | Passou |
| Objeto upload/download/excluir | Storage REST, smoke.py | Passou; conteúdo comparado |
| Tópico e assinatura criar/excluir | Pub/Sub REST, smoke.py | Passou |
| Publicar, pull e acknowledge | Pub/Sub REST, smoke.py | Passou; payload comparado |
| Bucket, tópico e assinatura | Terraform apply | Três recursos criados |
| Segundo plan | Terraform -detailed-exitcode | Código 0, sem alterações |
| Destroy e reaplicação | Terraform local | Três recursos removidos e recriados; plan final sem mudanças |
| Ingestão e consulta de trace | OTLP HTTP → Collector → Tempo | Passou; trace_id consultado |
| Ingestão e consulta de log | OTLP HTTP → Collector → Loki | Passou; marcador encontrado |
| Ingestão e consulta de métrica | OTLP HTTP → Collector → Prometheus | Passou; série encontrada |
| Invariantes dos manifestos | unittest | Quatro testes passaram |
| Dashboard e métricas Kubernetes | API Grafana e consulta Prometheus | Dashboard provisionado e séries presentes |
| RBAC do investigador | kubectl auth can-i por impersonação | Listar pods: permitido; ler Secrets/excluir pods: negado |
| Argo CD | Rollout de deployments e StatefulSet | Controladores disponíveis |

Comandos de reprodução estão no guia de infraestrutura; scripts/smoke.py cria identificadores aleatórios, compara resultados e remove seus recursos cloud temporários. A telemetria da sonda permanece pelo período de retenção. O pipeline repete os contratos em Linux.

## Problemas encontrados e resolvidos

1. **WSL antigo/cgroup v1:** kubelet 1.35 recusava a inicialização. Atualização oficial do WSL, reinício do Docker e confirmação de cgroup v2. O bootstrap final exige v2 e não aplica failCgroupV1=false.
2. **Entrypoint do Floci:** a imagem inicia como root e tenta trocar de identidade com chroot. Com capabilities removidas, isso falhava. O pod agora inicia diretamente como UID 1001, com grupo compatível e fsGroup no volume; não foi necessário privilegiar o container nem montar socket Docker.
3. **Conflito de variável de porta:** Service Links injetava FLOCI_GCP_PORT como tcp://..., mas o emulador espera inteiro. enableServiceLinks=false evita essa injeção nos pods gerenciados pelo bootstrap.
4. **Configuração do Tempo 3:** o campo legado compactor não existe nessa versão. A configuração usa o modo single-binary atual e retenção em overrides.defaults.compaction.block_retention.

## Limites ainda não validados

Primeira reprodução em runner Linux: [GitHub Actions — execução 42167653397](https://github.com/antoniodelfim/cloudops-ai-lab/actions/runs/42167653397), concluída com sucesso em 1 minuto e 46 segundos. Executou configuração, criação do cluster, contratos, telemetria, Terraform, idempotência e limpeza. A instalação Argo CD foi validada localmente, fora deste job.

Observação de capacidade local: aproximadamente 3,9 GiB de memória no container do nó com observabilidade e Argo CD ativos, sem carga de aplicação. É uma leitura pontual do docker stats, não um requisito mínimo nem resultado de benchmark.

- IAM real, rede/VPC, quotas, escalabilidade e disponibilidade do GCP/GKE.
- Semântica de reentrega sob falhas, concorrência e idempotência da futura aplicação.
- Serviços cloud além das operações Storage/PubSub listadas.
- Capacidade sob carga, SLOs e recuperação de aplicações de negócio.
- Captura completa de logs do cluster e uso de CPU/memória dos nós.
- Tempo real de retenção e restauração de backup; os testes atuais confirmam ingestão/consulta, não uma espera de 24 horas.
