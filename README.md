# CloudOps AI Lab

Laboratórios reproduzíveis de DevOps, SRE, Engenharia de Plataforma e operações assistidas por inteligência artificial.

## Estado atual

Infraestrutura local implementada: Kubernetes com kind, floci-gcp, OpenTelemetry Collector, Prometheus, Loki, Tempo, Grafana, Alertmanager, kube-state-metrics e instalação do Argo CD. Terraform configura Storage e Pub/Sub no emulador. Aplicações de negócio, SLOs e investigador de IA são as próximas entregas. Nenhum recurso de nuvem real foi provisionado.

## Executar a infraestrutura

Pré-requisitos: Docker Linux com cgroup v2, Python 3.11+ e Terraform 1.11+. Na raiz do repositório:

```sh
python scripts/setup_tools.py
python scripts/infra.py up
python scripts/infra.py test
python scripts/infra.py gitops
terraform -chdir=infra/terraform/local init
terraform -chdir=infra/terraform/local apply
```

Abrir [Grafana local](http://127.0.0.1:3000) para visualizar o dashboard de infraestrutura. A senha de administração é gerada localmente e não é versionada. Ferramentas e kubeconfig ficam isolados neste projeto.

- [Guia de operação, acessos, diagnóstico e limpeza](docs/infraestrutura-local.md)
- [Plano detalhado dos cinco projetos e casos operacionais](docs/plano-de-execucao.md)
- [Compatibilidade validada e evidências](docs/compatibilidade.md)

Para remover exclusivamente o cluster do laboratório e seus dados: `python scripts/infra.py down`.

## Foco principal

O portfólio será construído em torno de três pilares integrados:

1. **Kubernetes e GKE:** implantação e operação de aplicações, Helm, Argo CD, configuração, probes, recursos, escalabilidade, políticas, diagnóstico e recuperação. O laboratório local prepara os fluxos; a validação das capacidades gerenciadas será feita em GKE real em uma etapa controlada.
2. **Observabilidade e confiabilidade:** instrumentação com OpenTelemetry, métricas com Prometheus, logs com Loki, traces com Tempo e painéis com Grafana. Definir SLIs, SLOs, orçamento de erro, alertas e runbooks; correlacionar telemetria com alterações de deployment.
3. **Ferramentas de IA para operações:** construir um investigador de incidentes com consultas somente leitura à telemetria e aos eventos Kubernetes; adicionar integração MCP, relatórios com evidências e avaliação de qualidade. Começar com correlação determinística e depois incorporar LLM. A revisão de Terraform com IA será uma entrega posterior.

### Cenário demonstrável

Aplicação no Kubernetes → entrega via GitOps → métricas, logs e traces → falha controlada → alerta de SLO → investigação assistida por IA → relatório com evidências → validação humana e recuperação.

### Ordem de implementação

1. Arquitetura e decisão inicial, cluster Kubernetes local e floci-gcp para integrações GCP suportadas.
2. Aplicação de exemplo e entrega com Helm e Argo CD.
3. OpenTelemetry, Prometheus, Loki, Tempo e Grafana.
4. SLOs, alertas, testes de carga e incidentes reproduzíveis.
5. Investigador de incidentes com IA e ferramentas de consulta, com avaliação por cenários.
6. Terraform e validação em GKE real, com orçamento e limpeza definidos.
7. Expansão para AWS e depois Azure.

## Roteiro de nuvem

1. **GCP primeiro:** fundamentos com Kubernetes local, Terraform, GitOps, OpenTelemetry, SLOs e investigação de incidentes baseada em evidências; evolução para implantação controlada em GCP/GKE.
2. **AWS em seguida:** ampliar os fluxos validados com infraestrutura específica do provedor e documentação das diferenças.
3. **Azure depois:** aplicar as mesmas práticas de engenharia com validação específica para o provedor.

A execução começa localmente para controlar custos. Testes locais e emuladores não comprovam equivalência com serviços gerenciados de nuvem. Usaremos floci-gcp desde a fase inicial para emular as integrações GCP suportadas. A versão e as operações utilizadas serão registradas em uma matriz de compatibilidade. O cluster local e os testes do emulador terão evidências separadas da validação em GKE real.

## Projetos planejados

| Projeto | Objetivo | Situação |
| --- | --- | --- |
| Investigador de Incidentes SRE com IA | Correlacionar métricas, logs, traces e eventos Kubernetes em relatórios com evidências | Planejado |
| Laboratório de Infraestrutura | Terraform e testes de integração reproduzíveis, locais e em nuvem, começando por GCP | Planejado |
| Laboratório de Plataforma GitOps | Kubernetes local, Helm, Argo CD e padronização da entrada de novos serviços | Planejado |
| Revisor de Terraform com IA | Verificar políticas e revisar mudanças de infraestrutura com evidências | Planejado |
| Laboratório de Confiabilidade SRE | SLIs, SLOs, orçamento de erro e incidentes controlados | Planejado |

## Primeiro marco

- [x] Criar o repositório público central do portfólio com licença MIT.
- [x] Registrar a ordem dos provedores: GCP, AWS e Azure.
- [ ] Documentar a arquitetura inicial e a decisão arquitetural de priorizar GCP.
- [ ] Definir a aplicação de exemplo e a inicialização do ambiente local.
- [ ] Adicionar integração contínua com testes, análise de código e verificações de segurança.
- [ ] Demonstrar um serviço instrumentado em execução local.
- [ ] Definir o ambiente GCP, o modelo de acesso, os controles de orçamento e a remoção dos recursos antes do provisionamento.

## Princípios de engenharia

- Publicar instruções reproduzíveis, decisões versionadas, testes e resultados medidos.
- Nunca versionar credenciais, dados privados, arquivos de estado do Terraform ou arquivos reais de configuração de ambiente.
- Usar respostas simuladas de IA na integração contínua; validar as saídas e citar as evidências consultadas.
- Separar fatos observados, hipóteses e recomendações nos relatórios de incidentes.
- Manter as ferramentas de investigação com acesso somente leitura e exigir revisão humana para ações de correção.
- Documentar limitações e procedimentos de remoção de recursos para cada laboratório executável.

## Licença

[MIT](LICENSE)
