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

echo "-- Generate federation token"
FEDERATION_TOKEN=$(curl -s -k -H 'Content-Type: application/json' -H "X-Auth-Token: ${ACCESS_TOKEN}" \
    ${NEUVECTOR_BASE_URL}/join_token | jq -r .join_token)

cat <<EOF >> $secret_federation_token_file
---
apiVersion: v1
kind: Secret
metadata:
  name: neuvector-federation
data:
  join_token: ${FEDERATION_TOKEN}
  cluster_name: ${CLUSTER_NAME}
EOF

# Update secret
echo "Updating os-images-info secret"
kubectl apply -f $secret_federation_token_file


echo "-- All done"
