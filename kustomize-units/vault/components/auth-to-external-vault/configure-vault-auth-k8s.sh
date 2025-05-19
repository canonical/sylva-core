#!/bin/bash

kubectl wait --for=create -n vault secret vault-k8s-auth-secret --timeout=10s

REVIEWER_TOKEN=$(kubectl -n vault get secret vault-k8s-auth-secret -o jsonpath='{.data.token}' | base64 -d)
K8S_CA_CERT=$(kubectl  -n vault get secret vault-k8s-auth-secret -o jsonpath='{.data.ca\.crt}' | base64 -d | sed 's/$/\\n/' |  tr -d '\n')

CLUSTER_HOST=$(kubectl -n sylva-system get cluster mgmt-cluster -o jsonpath='{.spec.controlPlaneEndpoint.host}')
CLUSTER_PORT=$(kubectl -n sylva-system get cluster mgmt-cluster -o jsonpath='{.spec.controlPlaneEndpoint.port}')

cat > /tmp/payload.json <<EOF
{
      "token_reviewer_jwt": "$REVIEWER_TOKEN",
      "kubernetes_host": "https://$CLUSTER_HOST:$CLUSTER_PORT",
      "kubernetes_ca_cert": "$K8S_CA_CERT"
}
EOF

kubectl wait --for=create -n vault secret ext-vault --timeout=10s

VAULT_URL=$(kubectl -n vault get secret ext-vault -o jsonpath='{.data.addr}' | base64 -d)
VAULT_TOKEN=$(kubectl -n vault get secret ext-vault -o jsonpath='{.data.token}' | base64 -d)
AUTH_PATH=$(kubectl -n vault get secret ext-vault -o jsonpath='{.data.path}' | base64 -d)

curl -k --header "X-Vault-Token: $VAULT_TOKEN" --request POST --data @/tmp/payload.json $VAULT_URL/v1/auth/$AUTH_PATH/config

rm /tmp/payload.json
