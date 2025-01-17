#!/bin/bash

set -e
set -o pipefail

echo "Initiate ConfigMap manifest file"

configmap_file=/tmp/os-image-details.yaml

cat <<EOF >> $configmap_file
apiVersion: v1
kind: ConfigMap
metadata:
  name: os-images-info
  labels:
    sylva.os-images-info: ""
data:
  values.yaml: |
    os_images:
EOF

echo "Looping over OS images..."

while read os_image_key; do
  echo "-- processing image $os_image_key"
  export os_image_key
  echo "      $os_image_key:" >> $configmap_file
  # Check if the artifact is a Sylva diskimage-builder artifact
  uri=$(yq '.os_images.[env(os_image_key)].uri' /opt/images.yaml)
  sylva_dib_image=$(yq '.os_images.[env(os_image_key)].sylva_dib_image' /opt/images.yaml)

  if [[ "$sylva_dib_image" == "true" ]]; then
    echo "This is a Sylva diskimage-builder image. Updating image details from artifact at $uri"
    url=$(echo $uri| sed 's|oci://||')

    if ! $SKIP_IMAGE_VERIFICATION; then
      echo "Verifying diskimage-builder image signature for $url" 

      yq '.os_images.[env(os_image_key)].cosign_publickey' /opt/images.yaml > /tmp/cosign.pub

      if ! cosign verify  --allow-insecure-registry=$oci_registry_insecure --key /tmp/cosign.pub --insecure-ignore-tlog=true $url; then
         echo "[ERROR] Invalid signature for $url"
         exit 1
      fi
    fi
    # Get artifact annotations and insert them as image details
    insecure=$([[ $oci_registry_insecure == "true" ]] && echo "--insecure" || true)
    manifest=$(oras manifest fetch $url $insecure)
    echo $manifest | yq '.annotations |with_entries(select(.key|contains("sylva")))' -P | sed "s|.*/|        |" >> $configmap_file
  fi
  echo "Adding user provided details"
  yq '.os_images.[env(os_image_key)] |del(.. | select(has("sylva_dib_image")).sylva_dib_image)' /opt/images.yaml | sed 's/^/        /' >> $configmap_file
  echo ---
done < <(yq '.os_images | keys | .[]' /opt/images.yaml)

# Update configmap
echo "Updating os-images-info configmap"
# Unset proxy settings, if any were needed for oras tool, before connecting to local bootstrap cluster
unset https_proxy
kubectl apply -f $configmap_file

# delete the os-images-info-max-size ConfigMap that this
# script was producing in a previous version
#
# (this code can be removed after the release of Sylva where it was added)
kubectl delete configmap os-images-info-max-size --ignore-not-found
