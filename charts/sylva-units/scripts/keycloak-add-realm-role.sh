#!/bin/bash

set -e
set -o pipefail

LOGFILE="/tmp/keycloak_script.log"

function cleanup {
    echo "-- Script failed. Displaying log file:"
    cat $LOGFILE
}
trap cleanup EXIT

echo "-- Wait for Keycloak realm resource to be ready and created by keycloak operators"
kubectl wait --for=condition=Done --timeout=15s -n keycloak keycloakrealmimport.k8s.keycloak.org/sylva || (echo "timed out waiting for sylva keycloakrealmimport to become ready" && exit -1)

KEYCLOAK_BASE_URL="https://keycloak-service.keycloak.svc.cluster.local:8443"
KEYCLOAK_INITIAL_USERNAME="admin"
KEYCLOAK_REALM="sylva"
KEYCLOAK_ROLE="grafanaadmin"
KEYCLOAK_USERNAME="sylva-admin"

echo "-- Retrieve Keycloak admin initial password" | tee -a $LOGFILE
KEYCLOAK_INITIAL_PASSWORD=$(kubectl -n keycloak get secret keycloak-initial-admin -o jsonpath='{.data.password}' | base64 -d)

echo $KEYCLOAK_INITIAL_PASSWORD | tee -a $LOGFILE

echo "-- Retrieve Keycloak access token" | tee -a $LOGFILE
ACCESS_TOKEN=$(curl -k -s -X POST \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=${KEYCLOAK_INITIAL_USERNAME}" \
-d "password=${KEYCLOAK_INITIAL_PASSWORD}" \
-d "grant_type=password" \
-d "client_id=admin-cli" \
${KEYCLOAK_BASE_URL}/realms/master/protocol/openid-connect/token \
| tee -a $LOGFILE | jq -r '.access_token')

if [ -z "${ACCESS_TOKEN-unset}" ]; then
    echo "ACCESS_TOKEN is set to the empty string, will try again" | tee -a $LOGFILE
    exit 1
fi

echo "-- Check that sylva realm was already created by keycloak-operator" | tee -a $LOGFILE
NON_MASTER_REALM=$(curl -k -s -X GET \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${ACCESS_TOKEN}" \
${KEYCLOAK_BASE_URL}/admin/realms \
| tee -a $LOGFILE | jq -r '.[] | select( (.realm | test("^master$")|not) ).realm')

if [ "$NON_MASTER_REALM" != "sylva" ]; then
    echo "The sylva realm is not yet ready, will try again" | tee -a $LOGFILE
    exit 1
fi

echo "-- Create custom realm role" | tee -a $LOGFILE
curl -k -s -X POST \
-H "Content-Type: application/json" \
-H "Authorization: Bearer ${ACCESS_TOKEN}" \
-d '{
        "name": "grafanaadmin",
        "description": "Admin role for Grafana",
        "composite": false,
        "clientRole": false,
        "containerId": "sylva"
}' \
${KEYCLOAK_BASE_URL}/admin/realms/${KEYCLOAK_REALM}/roles | tee -a $LOGFILE

# Debugging output
echo -e "\n-- Debug: Retrieve User Info --" | tee -a $LOGFILE
echo "${KEYCLOAK_BASE_URL}/admin/realms/${KEYCLOAK_REALM}/users?username=${KEYCLOAK_USERNAME}" | tee -a $LOGFILE

# Find user ID
USER_ID=$(curl -k -s -X GET "${KEYCLOAK_BASE_URL}/admin/realms/${KEYCLOAK_REALM}/users?username=${KEYCLOAK_USERNAME}" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        -H "Content-Type: application/json" | tee -a $LOGFILE | jq -r '.[0].id')

# Debugging output
echo "User ID: $USER_ID" | tee -a $LOGFILE

if [ -z "$USER_ID" ]; then
    echo "User ID not found for username: $KEYCLOAK_USERNAME" | tee -a $LOGFILE
    exit 1
fi

echo "-- Find role ID" | tee -a $LOGFILE
# Find role ID
ROLE_ID=$(curl -k -s -X GET "${KEYCLOAK_BASE_URL}/admin/realms/${KEYCLOAK_REALM}/roles/${KEYCLOAK_ROLE}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | tee -a $LOGFILE | jq -r '.id')

# Debugging output
echo "Role ID: $ROLE_ID" | tee -a $LOGFILE

if [ -z "$ROLE_ID" ]; then
    echo "Role ID not found for role: $KEYCLOAK_ROLE" | tee -a $LOGFILE
    exit 1
fi

echo "-- Assign role to user" | tee -a $LOGFILE
# Assign role to user
curl -k -s -X POST "$KEYCLOAK_BASE_URL/admin/realms/${KEYCLOAK_REALM}/users/$USER_ID/role-mappings/realm" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "id": "'"$ROLE_ID"'",
      "name": "'"$KEYCLOAK_ROLE"'"
    }
  ]' | tee -a $LOGFILE

echo "Role $KEYCLOAK_ROLE assigned to user $KEYCLOAK_USERNAME" | tee -a $LOGFILE

echo "-- All done" | tee -a $LOGFILE

trap - EXIT