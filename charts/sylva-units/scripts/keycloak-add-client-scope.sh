#!/bin/bash

set -e
set -o pipefail

# workaround for https://gitlab.com/sylva-projects/sylva-core/-/issues/144
echo "-- Wait for Keycloak realm resource to be ready and created by keycloak operators"
attempts=0
max_attempts=5
until kubectl get -n keycloak keycloakrealmimport.k8s.keycloak.org sylva -o json | jq -e '.status.conditions[]|select(.type=="Done")|.status'; do
sleep 3
((attempts++)) && ((attempts==max_attempts)) && echo "timed out waiting for sylva keycloakrealmimport to become ready" && exit 1
done

KEYCLOAK_BASE_URL="https://keycloak-service.keycloak.svc.cluster.local:8443"
KEYCLOAK_INITIAL_USERNAME="admin"

echo "-- Retrieve Keycloak admin initial password"
KEYCLOAK_INITIAL_PASSWORD=`kubectl -n keycloak get secret keycloak-initial-admin -o jsonpath='{.data.password}' | base64 -d`

echo "-- Retrieve Keycloak access token"
ACCESS_TOKEN=$(curl -k -s -X POST \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=${KEYCLOAK_INITIAL_USERNAME}" \
--data-urlencode "password=${KEYCLOAK_INITIAL_PASSWORD}" \
-d "grant_type=password" \
-d "client_id=admin-cli" \
${KEYCLOAK_BASE_URL}/realms/master/protocol/openid-connect/token \
| jq -r '.access_token')
if [ -z "${ACCESS_TOKEN-unset}" ]; then
    echo "ACCESS_TOKEN is set to the empty string, will try again"
    exit 1
fi

echo "-- Check that sylva realm was already created by keycloak-operator"
NON_MASTER_REALM=$(curl -k -s -X GET \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${ACCESS_TOKEN}" \
${KEYCLOAK_BASE_URL}/admin/realms \
| jq -r '.[] | select( (.realm | test("^master$")|not) ).realm')
if [ "$NON_MASTER_REALM" != "sylva" ]; then
    echo "The sylva realm is not yet ready, will try again"
    exit 1
fi

echo "-- Create client scope"
curl -k -s -X POST \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${ACCESS_TOKEN}" \
-d '{
    "name": "groups",
    "protocol": "openid-connect",
    "attributes": {
    "include.in.token.scope": "true",
    "default.client.scope": "false"
    }
}' \
${KEYCLOAK_BASE_URL}/admin/realms/sylva/client-scopes

echo "-- All done"
