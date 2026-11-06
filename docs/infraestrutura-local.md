# Infraestrutura local — operação

Este bootstrap cria um cluster kind dedicado chamado cloudops-ai-lab. O Kubernetes executa floci-gcp, OpenTelemetry Collector, Prometheus, Loki, Tempo, Grafana, Alertmanager e kube-state-metrics. O Argo CD é instalado por um comando separado. Os arquivos ficam inicialmente no hub; a separação em repositórios técnicos será feita com versões e contratos definidos.

## Requisitos

- Docker com containers Linux e cgroup v2; no Windows, Docker Desktop com WSL atualizado.
- Python 3.11 ou superior; Terraform 1.11 ou superior para o recorte cloud local.
- Acesso à internet para imagens, ferramentas e providers.
- Orçamento inicial de recursos: 4 CPUs e 8 GB disponíveis no Docker para a base; preferir 12 GB ao acrescentar Argo CD. São valores de partida, não um benchmark de capacidade.
- Portas locais livres: 3000, 9090, 4588, 4318, 3100 e 3200.

O script usa kubeconfig isolado em .state/kubeconfig e seleciona explicitamente kind-cloudops-ai-lab. Não aplica recursos ao contexto atual do usuário. O cluster k8s-lab e outros clusters não são alvos deste bootstrap.

## Inicializar

Na raiz do repositório, em PowerShell ou Linux:

```sh
python scripts/setup_tools.py
python scripts/infra.py up
python scripts/infra.py test
python scripts/infra.py status
```

No Linux, usar python3 se python não estiver disponível. setup_tools baixa kind 0.33.0 e kubectl 1.35.5 para .tools e verifica checksums oficiais. Não modifica o PATH nem substitui instalações globais. up é reaplicável; se o cluster já existir, preserva volumes e reaplica os manifestos.

O cluster usa kindest/node:v1.35.5. Imagens dos componentes estão fixadas em scripts/infra.py; atualizar versões exige repetir testes de configuração e integração. Atualmente as referências usam tags fixas; a fixação por digest é uma melhoria pendente.

## Recursos cloud locais por Terraform

Depois de a infraestrutura ficar saudável:

```sh
terraform -chdir=infra/terraform/local init -input=false
terraform -chdir=infra/terraform/local validate
terraform -chdir=infra/terraform/local apply
terraform -chdir=infra/terraform/local plan -detailed-exitcode
```

Cria bucket cloudops-local-orders, tópico orders e assinatura order-worker no projeto sintético cloudops-local. Os endpoints Storage e Pub/Sub estão fixados em loopback e o token é fictício. Não alterar esses endpoints para nuvem real: criar configuração GKE/GCP separada. O segundo plan deve retornar código 0. O estado local não é versionado. Não remover o estado enquanto os recursos correspondentes estiverem em uso.

## Acessos locais

| Serviço | Endereço no computador | Endereço dentro do cluster |
| --- | --- | --- |
| Grafana | http://127.0.0.1:3000 | grafana.observability.svc.cluster.local:3000 |
| Prometheus | http://127.0.0.1:9090 | prometheus.observability.svc.cluster.local:9090 |
| Floci GCP | http://127.0.0.1:4588 | floci-gcp.cloud.svc.cluster.local:4588 |
| OTLP HTTP | http://127.0.0.1:4318 | otel-collector.observability.svc.cluster.local:4318 |
| OTLP gRPC | Sem exposição ao host | otel-collector.observability.svc.cluster.local:4317 |
| Loki | http://127.0.0.1:3100 | loki.observability.svc.cluster.local:3100 |
| Tempo | http://127.0.0.1:3200 | tempo.observability.svc.cluster.local:3200 |
| Alertmanager | Usar port-forward | alertmanager.observability.svc.cluster.local:9093 |

Grafana abre com acesso anônimo somente de visualização para este laboratório local. O dashboard CloudOps — Infraestrutura local e três fontes de dados são provisionados. Para administrar, usar usuário admin e a senha gerada no arquivo .state/grafana-password. Não publicar esse arquivo. O isolamento em loopback não é um modelo de autenticação para produção.

As aplicações futuras devem receber GOOGLE_CLOUD_PROJECT=cloudops-local, PUBSUB_EMULATOR_HOST=floci-gcp.cloud.svc.cluster.local:4588 e STORAGE_EMULATOR_HOST=http://floci-gcp.cloud.svc.cluster.local:4588. Instrumentação OTLP aponta para o Collector interno. Não usar localhost dentro de um pod para acessar outro serviço.

## GitOps

```sh
python scripts/infra.py gitops
```

Instala o manifesto oficial do Argo CD v3.6.1 no namespace argocd e aguarda os controladores. Ainda não configura entrega de aplicações de negócio; essa integração será a próxima etapa. O Argo CD mantém autenticação e não recebe porta pública.

Para interface, com kubectl da pasta .tools ou equivalente:

```sh
kubectl --kubeconfig .state/kubeconfig --context kind-cloudops-ai-lab -n argocd port-forward svc/argocd-server 8080:443 --address 127.0.0.1
```

Abrir https://127.0.0.1:8080; certificado local é autoassinado. A senha inicial está no Secret argocd-initial-admin-secret, acessível ao administrador do cluster. Não publicar a senha nem colocar sua extração em logs do CI.

## O que os testes comprovam

- Storage: criar bucket, enviar e baixar objeto, excluir objeto/bucket.
- Pub/Sub: criar tópico/assinatura, publicar, consumir, confirmar e remover recursos.
- OTLP: enviar trace, log e métrica e consultá-los no Tempo, Loki e Prometheus.
- Estrutura: recursos persistentes têm PVC, imagens não usam latest, serviços apontam para portas corretas e o papel do investigador não lê Secrets nem escreve recursos.
- Terraform: validação, apply, segundo plan sem mudanças e destroy no CI.

Os testes cloud criam recursos com nomes aleatórios e os removem no final. Os registros de telemetria da sonda permanecem até a retenção expirar. As sondas são dados de teste, não resultados de desempenho da aplicação.

## Observabilidade inicial e limites

Prometheus coleta a si próprio, métricas OTLP e estado dos deployments/pods. Alertas iniciais detectam alvo de coleta indisponível e deployment com réplicas indisponíveis. O Alertmanager usa receptor local sem envio externo; integração com o agente e alertas de SLO ainda serão implementados.

Não há coleta completa de logs de todos os pods, métricas de CPU/memória do nó, ingress, TLS público, backups, alta disponibilidade ou aplicação instrumentada de negócio nesta base. Não confundir estado de pods fornecido por kube-state-metrics com métricas de utilização de recursos. Logs e traces chegam por OTLP; coleta adicional do cluster será uma entrega posterior.

Prometheus, Loki e Tempo têm retenção de 24 horas. PVCs usam o provisionador local do kind e não têm alta disponibilidade. Excluir o cluster destrói os dados. A conta do futuro investigador pode ler pods, eventos, deployments e ReplicaSets apenas em apps; não tem shell, acesso a Secrets ou permissão de remediação.

## Parar e remover

Para remover apenas recursos gerenciados pelo Terraform, antes de excluir o cluster:

```sh
terraform -chdir=infra/terraform/local destroy
```

Bucket com objetos não é apagado automaticamente (force_destroy=false): remover dados de teste deliberadamente antes de destruir. Para excluir exclusivamente o cluster do laboratório e todos os seus volumes:

```sh
python scripts/infra.py down
```

O comando não exclui outros clusters. .state pode conter kubeconfig, senha e logs; está no .gitignore. Nenhum comando desta base provisiona GCP ou GKE real.

## Diagnóstico

- Erro de cgroup: confirmar docker info e cgroup v2; atualizar WSL e reiniciar Docker. Não ativar failCgroupV1=false como solução permanente.
- ImagePullBackOff: verificar acesso ao registro e eventos do pod, sem trocar silenciosamente por latest.
- Pending: verificar recursos do Docker e PVCs.
- CrashLoopBackOff: consultar logs do componente e validar seu arquivo de configuração.
- Falha OTLP: conferir logs do Collector, saúde do backend e consultas do smoke test.
- Alteração de ConfigMap: reiniciar o deployment correspondente para garantir recarga quando o componente não a suporta automaticamente.

Referências: [kind](https://kind.sigs.k8s.io/docs/user/quick-start/), [floci-gcp](https://github.com/floci-io/floci-gcp), [cgroup v2 e Kubernetes](https://kubernetes.io/blog/2026/10/06/kubernetes-cgroups-v2-shift/).
