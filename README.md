# CloudOps AI Lab

Reproducible labs for DevOps, SRE, Platform Engineering and AI-assisted operations.

## Status

Foundation stage: this repository is the portfolio hub and roadmap. Application code, infrastructure, pipelines and demos are planned; no cloud resources have been provisioned.

## Cloud roadmap

1. **GCP first:** local Kubernetes foundations, Terraform, GitOps, OpenTelemetry, SLOs and evidence-based incident investigation; progress toward a controlled GCP/GKE deployment.
2. **AWS next:** extend validated workflows with provider-specific infrastructure and documented differences.
3. **Azure afterward:** extend the same engineering practices with explicit provider-specific validation.

Start locally to control costs. Local tests and emulators do not establish parity with managed cloud services. Floci is a possible later AWS lab component, subject to compatibility validation; it is not a GCP or Azure prerequisite.

## Planned projects

| Project | Purpose | Status |
| --- | --- | --- |
| AI SRE Incident Investigator | Correlate metrics, logs, traces and Kubernetes events into reports with evidence | Planned |
| Infrastructure Lab | Terraform and reproducible local/cloud integration tests, starting with GCP | Planned |
| GitOps Platform Lab | Local Kubernetes, Helm, Argo CD and service onboarding | Planned |
| AI Terraform Reviewer | Policy checks and evidence-based review of infrastructure changes | Planned |
| SRE Reliability Lab | SLIs, SLOs, error budgets and controlled incidents | Planned |

## First milestone

- [x] Create the public portfolio hub with an MIT license.
- [x] Record the provider order: GCP, AWS, Azure.
- [ ] Document the initial architecture and GCP-first ADR.
- [ ] Define the sample application and local bootstrap.
- [ ] Add CI with tests, lint and security checks.
- [ ] Demonstrate an instrumented service running locally.
- [ ] Define the GCP environment, access model, budget controls and cleanup before provisioning.

## Engineering principles

- Publish reproducible instructions, versioned decisions, tests and measured results.
- Never commit credentials, private data, Terraform state or real environment files.
- Use mocked AI responses in CI; validate outputs and cite retrieved evidence.
- Separate observed facts, hypotheses and recommendations in incident reports.
- Keep investigation tools read-only; require human review for remediation.
- Document limitations and cleanup for every runnable lab.

## Português

Este é o repositório central do portfólio CloudOps AI Lab. O foco inicial será **GCP**, seguido de **AWS** e depois **Azure**. A execução começa localmente e evolui para validação controlada na nuvem. Os projetos estão planejados; a implementação será publicada por etapas, com documentação, testes e evidências.

## License

[MIT](LICENSE)
