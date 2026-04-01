variable "hcloud_token" {
  type        = string
  description = "The Hetzner Cloud API token used to manage resources."
  sensitive   = true
}

variable "ssh_public_key" {
  type        = string
  description = "The SSH public key to be added to the server for root access."
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
