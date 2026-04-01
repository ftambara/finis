terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.45"
    }
  }
}

provider "hcloud" {
  token = var.hcloud_token
}

data "hcloud_image" "latest_finis" {
  with_selector = "project=${var.project_name}"
  most_recent   = true
}

resource "hcloud_ssh_key" "default" {
  name       = "${var.project_name}-ssh-key"
  public_key = var.ssh_public_key
}

resource "hcloud_firewall" "finis_fw" {
  name = "${var.project_name}-firewall"
  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "22"
    source_ips = [
      "0.0.0.0/0",
      "::/0"
    ]
    description = "Allow SSH"
  }
  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "80"
    source_ips = [
      "0.0.0.0/0",
      "::/0"
    ]
    description = "Allow HTTP"
  }
  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "443"
    source_ips = [
      "0.0.0.0/0",
      "::/0"
    ]
    description = "Allow HTTPS"
  }
}

resource "hcloud_server" "finis_app" {
  name         = "${var.project_name}-app"
  image        = data.hcloud_image.latest_finis.id
  server_type  = var.server_type
  location     = var.location
  ssh_keys     = [hcloud_ssh_key.default.id]
  firewall_ids = [hcloud_firewall.finis_fw.id]

  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }

  labels = {
    project = var.project_name
  }
}

output "server_ipv4" {
  description = "The public IPv4 address of the Finis server."
  value       = hcloud_server.finis_app.ipv4_address
}
