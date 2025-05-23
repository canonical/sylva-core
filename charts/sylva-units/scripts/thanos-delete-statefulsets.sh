#!/bin/bash

thanos_statefulsets=(receive storegateway ruler)

for component in "${thanos_statefulsets[@]}"
do
  echo '---'
  echo Checking $component annotation hashes
  echo

  CURRENT_HASH=$(kubectl -n thanos get statefulsets thanos-"$component" -o jsonpath="{.metadata.annotations.thanos\.persistent-config-hash}" 2>/dev/null)
  echo "Current  hash: $CURRENT_HASH"
  EXPECTED_HASH="EXPECTED_HASH_$component"
  echo "Expected hash: ${!EXPECTED_HASH}"
  echo
  if [ "${CURRENT_HASH}" != "${!EXPECTED_HASH}" ]
  then
    echo "Annotation hash mismatch - deleting StatefulSet and pods..."
    kubectl -n thanos delete statefulsets thanos-"$component" --ignore-not-found=true
  else
    echo "Hashes match - no deletion needed"
  fi
done
