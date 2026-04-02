variable "hcloud_token" {
  type        = string
  description = "The Hetzner Cloud API token used to manage resources."
  sensitive   = true
}

variable "ssh_public_key" {
  type        = string
  description = "The SSH public key to be added to the server for root access."
}

variable "ci_ssh_public_key" {
  type        = string
  description = "The SSH public key for the CI/CD pipeline."
}

variable "location" {
  type        = string
  description = "The Hetzner data center location."
  default     = "nbg1"
}

variable "server_type" {
  type        = string
  description = "The Hetzner server type."
  default     = "cx23"
}

variable "project_name" {
  type        = string
  description = "The name of the project, used for labeling and identification."
  default     = "finis"
}

variable "cloudflare_api_token" {
  type        = string
  description = "Cloudflare API token with DNS Edit permissions for the zone."
  sensitive   = true
}

variable "cloudflare_zone_id" {
  type        = string
  description = "The Cloudflare Zone ID for ftambara.com."
}
