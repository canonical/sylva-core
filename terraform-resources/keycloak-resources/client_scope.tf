resource "keycloak_openid_client_scope" "groups_client_scope" {
  name     = "groups-client-scope"
  realm_id = "sylva"
}

