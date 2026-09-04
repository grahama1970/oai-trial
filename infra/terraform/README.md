# infra/terraform — plan-only handoff

Scaffold for the production cloud design in `../../SUBMISSION.md`. It is
**plan-only**: no provider blocks, no backend, no resources — so it validates
offline and never touches cloud state.

```bash
cd infra/terraform
terraform init      # offline, no provider downloads
terraform fmt -check
terraform validate
terraform plan -out plan.tfplan   # empty plan until resources are added
```

Read-only posture check via the ops skill:

```bash
skills/ops-terraform/run.sh   # binary/version, fmt, validate, saved-plan summary
```

The `locals.boundaries` map names the durable/trust boundaries (intake, work,
release, quarantine) that the SUBMISSION.md flow diagram and prose must match.
