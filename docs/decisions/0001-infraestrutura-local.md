# ADR 0001 — Infraestrutura local orientada a Kubernetes/GKE

Estado: aceito. Data: 6 de novembro de 2026.

## Contexto

O portfólio precisa demonstrar Kubernetes, observabilidade e investigação assistida por IA com execução reproduzível e custos controlados. O primeiro provedor é GCP; validação de GKE real será feita em etapa própria.

## Decisão

Usar um cluster kind dedicado, com kubeconfig isolado, para executar floci-gcp e a base de observabilidade. Terraform gerencia apenas Storage/PubSub emulados neste incremento. O Argo CD prepara a entrega GitOps das futuras aplicações.

Exigir Docker com cgroup v2. A máquina inicial precisou de atualização oficial do WSL e reinício do Docker; o código final não contém exceção para cgroup v1.

Separar namespaces cloud, observability, apps, ai-tools e argocd. Expor acessos do laboratório somente em loopback. A conta do investigador tem leitura restrita a recursos de diagnóstico em apps e nenhuma permissão de remediação.

## Alternativas

- Compose para toda a base: simples, mas não exercita operação de workloads Kubernetes. Poderá ser adicionado como perfil reduzido se houver necessidade.
- GKE emulado: útil para contratos de API específicos, mas não substitui a validação do serviço gerenciado.
- GKE real desde o início: acrescenta custo e dependências de identidade/rede antes do primeiro cenário funcional; fica para a etapa controlada.

## Consequências

Um único comando prepara a infraestrutura Kubernetes, mas exige recursos locais e downloads iniciais. PVCs preservam dados entre reinícios de pods; destruir o cluster remove seus dados. Sem alta disponibilidade ou garantia de produção. Métricas de estado já estão disponíveis; instrumentação da aplicação, logs completos de pods, SLOs e integração da IA serão incrementos posteriores.

O hub hospeda o bootstrap inicial para facilitar a primeira reprodução. Extração para repositórios técnicos não deve quebrar o guia: será feita com releases e contratos documentados.
