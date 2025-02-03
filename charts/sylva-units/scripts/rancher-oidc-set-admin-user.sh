#!/bin/bash

# Read the UUID assigned by Keycloak to the sylva-admin user
sylva_admin_uuid=$(kubectl get -n keycloak keycloakuser sylva-user -o jsonpath={.spec.user.id})
echo ID of sylva-admin in Keycloak: $sylva_admin_uuid

# Find the rancher identifier of the admin User
admin_user=$(kubectl get users -o=jsonpath='{.items[?(@.username=="admin")].metadata.name}')
echo ID of the admin user in Rancher: $admin_user

# Set this UUID as a principalID of the local admin user
kubectl patch user $admin_user --type json -p '[{"op":"add", "path":"/principalIds/1", "value": "keycloakoidc_user://'$sylva_admin_uuid'"}]'
