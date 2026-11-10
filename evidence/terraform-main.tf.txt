# Lab exercise: manage ONE throwaway DNS record with Terraform.
# Real records (grafana, lab) are NOT imported on purpose: a destroy would delete them.

terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5"
    }
  }
}

# The API token is read from the environment variable CLOUDFLARE_API_TOKEN (never written in a file).
provider "cloudflare" {}

variable "zone_id" {
  description = "Zone ID of jdjagustin-lab.dev (not a secret)"
  type        = string
}

resource "cloudflare_dns_record" "tf_test" {
  zone_id = var.zone_id
  name    = "tf-test.jdjagustin-lab.dev"
  type    = "TXT"
  content = "created by Terraform during lab 2026-11-10"
  ttl     = 120
}
