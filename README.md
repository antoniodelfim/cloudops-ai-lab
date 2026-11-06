# CloudOps AI Lab

Laboratórios reproduzíveis de DevOps, SRE, Engenharia de Plataforma e operações assistidas por inteligência artificial.

## Estado atual

Etapa de fundação: este repositório reúne a apresentação do portfólio e o roteiro de execução. O código da aplicação, a infraestrutura, os pipelines e as demonstrações estão planejados; nenhum recurso de nuvem foi provisionado.

## Roteiro de nuvem

1. **GCP primeiro:** fundamentos com Kubernetes local, Terraform, GitOps, OpenTelemetry, SLOs e investigação de incidentes baseada em evidências; evolução para implantação controlada em GCP/GKE.
2. **AWS em seguida:** ampliar os fluxos validados com infraestrutura específica do provedor e documentação das diferenças.
3. **Azure depois:** aplicar as mesmas práticas de engenharia com validação específica para o provedor.

A execução começa localmente para controlar custos. Testes locais e emuladores não comprovam equivalência com serviços gerenciados de nuvem. O Floci poderá integrar um laboratório posterior de AWS, sujeito à validação de compatibilidade; ele não é um pré-requisito para GCP ou Azure.

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
