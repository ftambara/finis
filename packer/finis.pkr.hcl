packer {
  required_plugins {
    hcloud = {
      version = ">= 1.6.0"
      source  = "github.com/hetznercloud/hcloud"
    }
  }
}

variable "hcloud_token" {
  type        = string
  description = "The Hetzner Cloud API token used to authenticate and build the image."
  sensitive   = true
}

variable "app_version" {
  type        = string
  description = "The specific version tag of the application to pre-pull and bake into the image."
  default     = "latest"
}

source "hcloud" "finis" {
  token         = var.hcloud_token
  image         = "ubuntu-24.04"
  location      = "nbg1"
  server_type   = "cx23"
  ssh_username  = "root"
  snapshot_name = "finis-${formatdate("YYYYMMDD-hhmmss", timestamp())}"
  snapshot_labels = {
    project = "finis"
  }
}

build {
  sources = ["source.hcloud.finis"]

  provisioner "shell" {
    environment_vars = [
      "APP_VERSION=${var.app_version}"
    ]
    scripts = [
      "packer/scripts/setup.sh"
    ]
  }
}
