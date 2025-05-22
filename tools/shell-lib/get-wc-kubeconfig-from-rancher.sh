#!/bin/bash

# Get workload cluster kubeconfig from Rancher API
# parameter: workload cluster name

set -eu

WORKLOAD_CLUSTER_NAME=$1

if  [[ -z $WORKLOAD_CLUSTER_NAME ]]; then
    echo Missing parameter for workload cluster name
    exit 1
fi

KUBECONFIG_OUTPUT=$2

if  [[ -z $KUBECONFIG_OUTPUT ]]; then
    echo Missing parameter for kubeconfig output file
    exit 1
fi

RANCHER_WORKLOAD_CLUSTER_NAME=$WORKLOAD_CLUSTER_NAME

echo "---- Retrieving kubeconfig for cluster $WORKLOAD_CLUSTER_NAME from Rancher API"

RANCHER_URL=$(kubectl get ingress -n cattle-system rancher -o jsonpath='{ .spec.tls[].hosts[] }')
echo "-- RANCHER_URL = $RANCHER_URL"
BOOTSTRAP_PASSWORD=$(kubectl -n cattle-system get secret rancher-bootstrap-secret -o jsonpath='{.data.bootstrapPassword}' | base64 -d)
TOKEN=$(curl --insecure -s -S -f https://$RANCHER_URL/v3-public/localProviders/local?action=login -H 'content-type: application/json' --data-binary '{"username":"admin","password":"'$BOOTSTRAP_PASSWORD'","ttl":60000}' | yq eval .token -)
CLUSTER=$(curl --insecure -s -S -f https://$RANCHER_URL/v3/clusters/?name=$RANCHER_WORKLOAD_CLUSTER_NAME  -H "Authorization: Bearer $TOKEN" )

if [[ -z "$CLUSTER" ]]; then
    echo "[ERROR] The $RANCHER_WORKLOAD_CLUSTER_NAME Rancher cluster was not found in Rancher"
    exit 1
fi

KUBECONFIG_URL=$(echo "$CLUSTER" | yq eval '.data[0] | .actions.generateKubeconfig' - | tr -d '"')

if [[ -n "$KUBECONFIG_URL" ]]; then
    curl --insecure -s -S -f -X POST $KUBECONFIG_URL -H "Authorization: Bearer $TOKEN" | yq eval .config - > $KUBECONFIG_OUTPUT
    echo "-- Kubeconfig for $RANCHER_WORKLOAD_CLUSTER_NAME cluster written to $KUBECONFIG_OUTPUT"
else
    echo "[ERROR] unable to find kubeconfig for cluster $WORKLOAD_CLUSTER_NAME"
    exit 1
fi
