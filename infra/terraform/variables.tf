variable "project" {
  description = "Project name used to prefix anonymization pipeline resources."
  type        = string
  default     = "oai-trial-anonymization"
}

variable "region" {
  description = "Cloud region for the anonymization pipeline (see SUBMISSION.md cost math)."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment label."
  type        = string
  default     = "trial"
}
