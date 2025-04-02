#!/bin/bash
set -e

LOG_FILE=$1
ALLOWED_EXCEPTIONS=(
  "metallb-resources"
  "ingress-nginx"
  # Add more exceptions here if needed
)

# Extract HelmReleases that had drift corrections
DRIFTED_HRS=$(grep "running 'correct cluster drift'" "$LOG_FILE" | sed -E 's/.*"HelmRelease":\{"name":"([^"]+)".*/\1/' | sort | uniq)

# Track unexpected drifts
UNEXPECTED_DRIFTS=()

echo "🚨 Drift detected in the following components:"

for hr in $DRIFTED_HRS; do
  echo "🔹 $hr"
  if ! printf "%s\n" "${ALLOWED_EXCEPTIONS[@]}" | grep -qFx "$hr"; then
    UNEXPECTED_DRIFTS+=("$hr")
  fi
done

# Fail if any unexpected drift is found
if [ ${#UNEXPECTED_DRIFTS[@]} -ne 0 ]; then
  echo -e "\n❌ Unexpected drift detected in:"
  for component in "${UNEXPECTED_DRIFTS[@]}"; do
    echo "   🔹 $component"
  done
  exit 1
fi

echo "✅ No unexpected drift detected."
