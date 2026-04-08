terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.45"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.0"
    }
    http = {
      source  = "hashicorp/http"
      version = "~> 3.0"
    }
  }
}

provider "hcloud" {
  token = var.hcloud_token
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

data "http" "my_ip" {
  url = "https://ipv4.icanhazip.com"
}

data "hcloud_image" "latest_finis" {
  with_selector = "project=${var.project_name}"
  most_recent   = true
}

resource "hcloud_ssh_key" "default" {
  name       = "${var.project_name}-ssh-key"
  public_key = var.ssh_public_key
}

resource "hcloud_ssh_key" "ci" {
  name       = "${var.project_name}-ci-ssh-key"
  public_key = var.ci_ssh_public_key
}

resource "hcloud_firewall" "finis_fw" {
  name = "${var.project_name}-firewall"
  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "22"
    # I would like to be more restrictive but GH pipelines become hard to manage.
    source_ips = [
      "0.0.0.0/0",
      "::/0",
    ]
    description = "Allow SSH from all IPs"
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
  ssh_keys     = [hcloud_ssh_key.default.id, hcloud_ssh_key.ci.id]
  firewall_ids = [hcloud_firewall.finis_fw.id]

  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }

  labels = {
    project = var.project_name
  }
}

resource "cloudflare_dns_record" "finis_dns" {
  zone_id = var.cloudflare_zone_id
  type    = "A"
  name    = "finis"
  content = hcloud_server.finis_app.ipv4_address
  proxied = true
  ttl     = 1 // Automatic
}

output "server_ipv4" {
  description = "The public IPv4 address of the Finis server."
  value       = hcloud_server.finis_app.ipv4_address
}
