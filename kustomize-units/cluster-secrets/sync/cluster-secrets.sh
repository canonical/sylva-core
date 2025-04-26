#!/bin/bash

set -ue
set -o pipefail
#set -x

# Process cluster-secrets rsources to compute encrypted_password
for csns in $(kubectl get secrets -l 'sylvaproject.org/cluster-secrets'='true' -o json -A | jq -r '.items[].metadata.namespace' | uniq);
do
  echo "Found cluster-secrets resources in namespace [$csns]"

  # Get the list of secrets in the namespace
  secrets=$(kubectl get secrets -l 'sylvaproject.org/cluster-secrets'='true' -o json -n "$csns" | jq -c '.items[]')

  # Init JSON for creating/patching the cluster-secrets in the current NS
  JSON="[]"

  # LOOP to fetch process all cluster-secrets of the current NS
  for current_secret in $secrets;
  do

    # Get secret name
    secret_name=$(echo $current_secret | jq -r '.metadata.name')
    # Get secret password
    secret_password=$(echo $current_secret | jq -r '.data.password' | base64 -d)
    # Get secret username
    secret_username=$(echo $current_secret | jq -r '.data.username' | base64 -d)


    # Get encrypted password if exists
    #encrypted_password=$(echo $current_secret | jq -r '.data.encrypted_password // ""' | base64 -d)
    encrypted_password=''

    # Get annotations of the sha256sum password
    current_sha256sum=$(echo $current_secret | jq -r '.metadata.annotations."sylvaproject.org/password-sha256sum" // "0"')
    synced_sha256sum=$(echo $current_secret | jq -r '.metadata.annotations."sylvaproject.org/cluster-secrets-synced-sha256sum" // "0"')

    # Get secret type from annotations
    secret_type=$(echo $current_secret | jq -r '.metadata.annotations."sylvaproject.org/cluster-secrets-type"')

    # Rotated password detected
    #if [[ $current_sha256sum != $synced_sha256sum || $encrypted_password == '' ]]; then
#    if [[ $current_sha256sum != $synced_sha256sum ]]; then
      echo "New password detected in [$csns/$secret_name]"

      if [ "$secret_type" = "user" ]; then
        encrypted_password=$(echo $secret_password | mkpasswd --method=SHA-512 --stdin)
      fi
      if [ "$secret_type" = "grub" ]; then
        encrypted_password=$(echo -e "$secret_password\n$secret_password" | LC_ALL=C grub-mkpasswd-pbkdf2 | awk '/hash of / {print $NF}')
      fi

      # Patching the secret
      kubectl patch secret $secret_name -n $csns --type 'merge' -p '{"metadata":{"annotations":{"sylvaproject.org/cluster-secrets-synced-sha256sum":"'$current_sha256sum'"}}}'
#    fi

    # Add secret form
    # {
    #   type: "grub|user"
    #   encrypted_password: "my encrypted password"
    #   username: "my username"
    # }
    _json_secret=$(jq -n --arg type "$secret_type" --arg username "$secret_username" --arg encrypted_password "$encrypted_password" --arg sha256sum "$current_sha256sum" '{"type": $type, "encrypted_password": $encrypted_password, "username": $username, "sha256sum": $sha256sum}')

    # Add to the final JSON object
    JSON=$(jq --argjson new "$_json_secret" '. + [$new]' <<< "$JSON")

  done

  echo "Patching $JSON"

  # Convert JSON to YAML
  yaml_content=$(echo "$JSON" | yq e -P)

  # Create the cluster-secrets CM with all encrypted password
  kubectl apply -n "$csns" -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-secrets
data:
  secrets.yaml: |
    secrets:
      data:
$(echo "$yaml_content" | sed 's/^/        /')
EOF

done

