# Provider mapping (AWS reference; GCP / Azure adapters)

The anonymization engine is a portable OCI container; only the orchestration is
provider-specific. Each capability in
[`../deployment-contract.yaml`](../deployment-contract.yaml) maps to a concrete
managed service per cloud. AWS is the worked reference
([`../../docs/production-architecture.md`](../../docs/production-architecture.md));
GCP/Azure are documented adapters, not maintained infrastructure.

| Capability | AWS (reference) | GCP | Azure |
|---|---|---|---|
| Object store (input/release/quarantine) | S3 (versioned) | Cloud Storage | Blob Storage |
| Key service | KMS | Cloud KMS | Key Vault / Managed HSM |
| Batch compute (OCI job) | AWS Batch / ECS | Batch | Container Apps Jobs / Batch |
| Work queue | SQS (+ DLQ) | Pub/Sub | Service Bus |
| Orchestration (durable retries/replay) | Step Functions | Workflows | Durable Functions |
| Event/admission | EventBridge | Eventarc | Event Grid |
| Audit log | CloudTrail | Cloud Audit Logs | Azure Activity Log |
| Metrics | CloudWatch | Cloud Monitoring | Azure Monitor |

## What stays the same across providers
- The `anonymization-trial` container image (unchanged).
- The data contract: `policy.json` + `corpus/` → `report.json` + `corpus/`.
- The verification semantics: stage → independent verify → atomic verified-only
  publish, report last.
- Fail-closed publication and "no mapping/keys in release or logs".

## What differs (and must be re-evaluated per provider)
Security defaults, IAM/role model, orchestration failure/replay semantics,
conditional-write primitives for the atomic release pointer, and pricing. These
are why "one Terraform config for any cloud" is a false claim; Terraform is a
common language and an adapter layer, not the portability boundary.

## Terraform posture
`infra/terraform/` is the AWS **reference** module. It is validated read-only
(`terraform fmt`, `terraform validate`, and `$ops-terraform`), pins its
`required_version`, and **commits no state** (see `.gitignore`). No `init` with a
live backend, `plan` against real state, or `apply` is performed for the
submission — deployment earns no extra credit over a measured design.
