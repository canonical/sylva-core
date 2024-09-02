terraform {
  required_providers {
    keycloak = {
      source = "mrparkers/keycloak"
      version = "~> 3.0"
    }
  }
}

provider "keycloak" {
  client_id = "admin-cli"
  username  = var.KEYCLOAK_USERNAME
  password  = var.KEYCLOAK_PASSWORD
  url       = var.KEYCLOAK_URL
  tls_insecure_skip_verify = true
  base_path = ""
}

