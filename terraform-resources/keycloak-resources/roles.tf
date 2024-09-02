resource "keycloak_role" "infra_admins_view_users_roles" {
  name     = "infra-admins-view-users-roles"
  realm_id = "sylva"
}

resource "keycloak_role" "grafanaadmin_role" {
  name     = "grafanaadmin-role"
  realm_id = "sylva"
}

