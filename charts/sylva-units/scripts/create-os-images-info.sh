#!/usr/bin/env bash

set -e
set -o pipefail

echo "Initiate ConfigMap manifest file"

configmap_file=/tmp/os-image-details.yaml

cat <<EOF >> $configmap_file
apiVersion: v1
kind: ConfigMap
metadata:
  name: os-images-info
  namespace: ${TARGET_NAMESPACE}
  labels:
    sylva.os-images-info: ""
data:
  values.yaml: |
    os_images:
EOF

echo "Looping over OS images..."

MAX_IMAGE_SIZE=0

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
    # Get artifact annotations and insert them as image details
    insecure=$([[ $oci_registry_insecure == "true" ]] && echo "--insecure" || true)
    manifest=$(oras manifest fetch $url $insecure)
    echo $manifest | yq '.annotations |with_entries(select(.key|contains("sylva")))' -P | sed "s|.*/|        |" >> $configmap_file
    # we compute the size needed to process the current image as:
    # - the size of the compressed image plus the size of the uncompressed image
    #   (because the tools manipulating the image may need to have both on disk at the same time during decompression)
    # - a margin of 100MB
    # - account for the ext4 inode tables and journal overhead (with a margin): 97% usable space
    current_image_size=$(echo $manifest | jq '([.annotations."sylvaproject.org/diskimage/archive-size", .annotations."sylvaproject.org/diskimage/size"] | map(tonumber) | add / pow(1024;2) + 100) / 0.97 | ceil')
    if [ $current_image_size -gt $MAX_IMAGE_SIZE ]; then
      MAX_IMAGE_SIZE=$current_image_size
    fi
  fi
  echo "Adding user provided details"
  yq '.os_images.[env(os_image_key)] |del(.. | select(has("sylva_dib_image")).sylva_dib_image)' /opt/images.yaml | sed 's/^/        /' >> $configmap_file
  echo ---
done < <(yq '.os_images | keys | .[]' /opt/images.yaml)

echo "Adding maximum image size ConfigMap"
cat <<EOF >> $configmap_file
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: os-images-info-max-size
  namespace: ${TARGET_NAMESPACE}
data:
  MAX_IMAGE_SIZE: ${MAX_IMAGE_SIZE}Mi
EOF

# Update configmap
echo "Updating os-images-info configmap"
# Unset proxy settings, if any were needed for oras tool, before connecting to local bootstrap cluster
unset https_proxy
kubectl apply -f $configmap_file
