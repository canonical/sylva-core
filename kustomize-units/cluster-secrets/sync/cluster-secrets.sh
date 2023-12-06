#!/bin/bash

set -ue
set -o pipefail
set -x

# Detect current NAMESPACE
NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
# Name of configmap storing the encrypted passwords
CM_NAME="cluster-secrets"
# Init ConfigMap YAML
CM_YAML=""

if kubectl get configmap -n "$NAMESPACE" $CM_NAME > /dev/null 2>&1; then
# Get the ConfigMap YAML if exists
  CM_YAML=$(kubectl get configmap -n "$NAMESPACE" $CM_NAME -o yaml | yq -r '.data["secrets.yaml"]' | yq .secrets.data)
fi

# Get the list of secrets in the namespace
secrets=$(kubectl get secrets -l 'sylvaproject.org/cluster-secrets'='true' -o json -n "$NAMESPACE" | jq -c '.items[]')

# Init JSON for creating/patching the cluster-secrets in the current NS
JSON="[]"

# Init patch boolean
B_PATCH=false

# LOOP to fetch process all cluster-secrets of the current NS
for current_secret in $secrets;
do

  # Get secret password
  secret_password=$(echo $current_secret | jq -r '.data.password' | base64 -d)
  # Get secret username
  secret_username=$(echo $current_secret | jq -r '.data.username' | base64 -d)
  # Get secret type from annotations
  secret_type=$(echo $current_secret | jq -r '.metadata.annotations."sylvaproject.org/cluster-secrets-type"')

  # Compute the sha256sum of the current password
  current_sha256sum=$(echo $current_secret | sha256sum  | awk '{ print $1 }')

  # Init encrypted_password variable
  encrypted_password=''

  # Rotated password detected
  if [ "$secret_type" = "user" ]; then
    encrypted_password=$(echo $secret_password | mkpasswd --method=SHA-512 --stdin)
  fi
  if [ "$secret_type" = "grub" ]; then
    encrypted_password=$(echo -e "$secret_password\n$secret_password" | LC_ALL=C grub-mkpasswd-pbkdf2 | awk '/hash of / {print $NF}')
  fi

  # Add secret form
  # {
  #   type: "grub|user"
  #   encrypted_password: "my encrypted password"
  #   username: "my username"
  # }
  _json_secret=$(jq -n --arg type "$secret_type" --arg username "$secret_username" --arg encrypted_password "$encrypted_password" --arg sha256sum "$current_sha256sum" '{"type": $type, "encrypted_password": $encrypted_password, "username": $username, "sha256sum": $sha256sum}')

  # Add to the final JSON object
  JSON=$(jq --argjson new "$_json_secret" '. + [$new]' <<< "$JSON")

  # Set boolean if the sha256sum is not known in the current CM
  RESULT=$(echo "$CM_YAML" | yq eval '.[] | select(.sha256sum == "'${current_sha256sum}'")' | wc -l)
  if [ "$RESULT" -eq 0 ]; then
    B_PATCH=true
  fi
done

if [ "$B_PATCH" = true ]; then
  echo "[NS=${NAMESPACE}] Patching $JSON"

  # Convert JSON to YAML
  yaml_content=$(echo "$JSON" | yq e -P)

  # Create the cluster-secrets CM with all encrypted password
  kubectl apply -n "$NAMESPACE" -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: "$CM_NAME"
  annotations:
    sylvaproject.org/cluster-secrets-hash: $(echo "$yaml_content" | sha256sum | awk '{ print $1 }')
data:
  secrets.yaml: |
    secrets:
      data:
$(echo "$yaml_content" | sed 's/^/        /')
EOF
else
  echo "[NS=${NAMESPACE}] Everything already synced"
fi


