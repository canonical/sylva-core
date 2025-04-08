#!/bin/bash
set -e

export KUBECONFIG=management-cluster-kubeconfig

echo "📝 Checking Helm controller logs for drift..."

# Set log file path
LOG_FILE="helm_logs.txt"

# Get logs once and store in file
kubectl -n flux-system logs deployments/helm-controller > "$LOG_FILE"

ALLOWED_EXCEPTIONS=(
  "metallb-resources:*" # Allow all actions for metallb-resources
  "ingress-nginx:Service.*removed" # Only allow service removal for ingress-nginx
  "k8s-gateway:Service.*removed" # Only allow service removal for k8s-gateway
  # Add more exceptions here in the format "resource:action_pattern"
)

# Extract HelmReleases that had drift corrections with their associated actions
declare -A DRIFT_ACTIONS
while IFS= read -r line; do
  if [[ "$line" == *"Cluster state of release"*"has drifted"* ]]; then
    # Extract HelmRelease name and the drift action
    hr_name=$(echo "$line" | sed -E 's/.*HelmRelease.*"name":"([^"]+)".*/\1/')
    action=$(echo "$line" | sed -E 's/.*has drifted from the desired state:\\n(.*)"/\1/')
    
    # Store the action for this HelmRelease
    if [[ -z "${DRIFT_ACTIONS[$hr_name]}" ]]; then
      DRIFT_ACTIONS[$hr_name]="$action"
    else
      DRIFT_ACTIONS[$hr_name]="${DRIFT_ACTIONS[$hr_name]}|$action"
    fi
  fi
done < "$LOG_FILE"

# Find HelmReleases with drift corrections
DRIFTED_HRS=$(grep "running 'correct cluster drift'" "$LOG_FILE" | sed -E 's/.*"HelmRelease":\{"name":"([^"]+)".*/\1/' | sort | uniq)

# Track unexpected drifts
UNEXPECTED_DRIFTS=()

if [[ -z "$DRIFTED_HRS" ]]; then
  echo "✅ No drift detected in any components."
else
  echo "🚨 Drift detected in the following components:"

  for hr in $DRIFTED_HRS; do
    echo "   🔹 $hr"
    
    is_unexpected=true
    actions="${DRIFT_ACTIONS[$hr]}"
    
    # Check if this specific action is allowed for this helm release
    for exception in "${ALLOWED_EXCEPTIONS[@]}"; do
      exception_helmrelease="${exception%%:*}"
      exception_pattern="${exception#*:}"
      
      if [[ "$hr" == "$exception_helmrelease" ]]; then
        if [[ "$exception_pattern" == "*" ]] || [[ -n "$actions" && "$actions" =~ $exception_pattern ]]; then
          is_unexpected=false
          break
        fi
      fi
    done
    
    if [[ "$is_unexpected" == true ]]; then
      UNEXPECTED_DRIFTS+=("$hr")
    fi
  done

  # Fail if any unexpected drift is found
  if [ ${#UNEXPECTED_DRIFTS[@]} -ne 0 ]; then
    echo -e "\n❌ Unexpected drift detected in:"
    for component in "${UNEXPECTED_DRIFTS[@]}"; do
      echo "   🔹 $component"
      echo "      Action: ${DRIFT_ACTIONS[$component]}"
    done
    
    # Clean up log file
    rm -f "$LOG_FILE"
    exit 1
  fi
fi

echo "✅ No unexpected drift detected."

# Clean up log file
rm -f "$LOG_FILE"
exit 0
