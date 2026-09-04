output "name_prefix" {
  description = "Resource name prefix for the anonymization pipeline."
  value       = local.name_prefix
}

output "boundaries" {
  description = "Durable/trust boundary names the production design must provision."
  value       = local.boundaries
}
