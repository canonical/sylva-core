variable "KEYCLOAK_USERNAME" {
  type        = string
  description = "The username for authenticating with Keycloak"
}

variable "KEYCLOAK_PASSWORD" {
  type        = string
  description = "The password for authenticating with Keycloak"
  sensitive   = true
}

variable "KEYCLOAK_URL" {
  type        = string
  description = "The URL of the Keycloak server"
}

