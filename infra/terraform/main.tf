# Intentionally resource-free scaffold: it names the durable boundaries the
# production design in SUBMISSION.md must fill (intake bucket, work queue,
# release bucket, quarantine bucket) without provisioning anything yet.
locals {
  name_prefix = "${var.project}-${var.environment}"

  # Durable/trust boundaries the pipeline crosses; kept in sync with the
  # SUBMISSION.md flow diagram labels.
  boundaries = {
    intake     = "${local.name_prefix}-intake"     # raw customer exports (ro)
    work       = "${local.name_prefix}-work"        # sensitive intermediate state
    release    = "${local.name_prefix}-release"     # verified, publishable corpus
    quarantine = "${local.name_prefix}-quarantine" # failed/unsafe files, never released
  }
}
