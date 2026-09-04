# Plan-only production-design handoff. No provider blocks, so `terraform init`
# and `terraform validate` run offline with no downloads. Swap in the real
# provider (aws/gcp/azure) when the SUBMISSION.md cloud design is chosen.
terraform {
  required_version = ">= 1.5.0"
}
