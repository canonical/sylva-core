#!/bin/bash

set -e
set -o pipefail


NEUVECTOR_BASE_URL="https://neuvector-svc-controller-api.neuvector.svc.cluster.local:10443"
NEUVECTOR_USERNAME="admin"

echo "-- Retrieve Neuvector admin initial password"
NEUVECTOR_PASSWORD=`kubectl -n neuvector get secret neuvector-init -o jsonpath='{.data.userinitcfg\.yaml}' | base64 -d | yq eval '.users[0].Password'`

echo "-- Retrieve Neuvector access token"
ACCESS_TOKEN=$(curl -k -s -X POST \
    -H "Content-Type: application/json" \
    -d '{"password": {"username":"'${NEUVECTOR_USERNAME}'", "password":"'${NEUVECTOR_PASSWORD}'"}}' \
    ${NEUVECTOR_BASE_URL}/v1/auth | jq -r '.token.token')

if [ -z "${ACCESS_TOKEN-unset}" ]; then
    echo "ACCESS_TOKEN is set to the empty string, will try again"
    exit 1
fi

echo "-- Assign fedAdmin role to infra-admins group"
curl -s -k -H 'Content-Type: application/json' -H "X-Auth-Token: ${ACCESS_TOKEN}" \
    ${NEUVECTOR_BASE_URL}/v1/server/openId1 \
    -X PATCH -d '{"config":{"name": "openId1", "oidc": { "group_mapped_roles": [{"global_role": "fedAdmin","group": "infra-admins"},{"global_role": "reader","group": "neuvector-readers"}] }}}'

echo "-- All done"
