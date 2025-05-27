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
  "sriov-network-operator:.*SriovOperatorConfig.cattle-sriov-system.default changed .[0-3] additions, 0 changes, 0 removals.*" # ignore the first drift correction on this object (normal)
  # Add more exceptions here in the format "resource:action_pattern"
)

# Extract HelmReleases that had drift corrections with their associated actions
declare -A DRIFT_ACTIONS
declare -A DRIFT_MODIFICATIONS

while IFS= read -r line; do
  if [[ "$line" == *"Cluster state of release"*"has drifted"* ]]; then
    # Extract HelmRelease name and the drift action
    hr_name=$(echo "$line" | sed -E 's/.*HelmRelease.*"name":"([^"]+)".*/\1/')
    timestamp=$(echo "$line" | sed -E 's/.*"ts":"([^"]+)".*/\1/')
    action=$(echo "$line" | sed -E 's/.*has drifted from the desired state:\\n(.*)"/\1/')

    # Store the action for this HelmRelease
    if [[ -z "${DRIFT_ACTIONS[$hr_name]}" ]]; then
      DRIFT_ACTIONS[$hr_name]="[$timestamp] $action"
    else
      DRIFT_ACTIONS[$hr_name]="${DRIFT_ACTIONS[$hr_name]}|[$timestamp] $action"
    fi
  elif [[ "$line" == *"resource modified"* || "$line" == *"resource added"* || "$line" == *"resource removed"* ]]; then
    # Extract modification details with patch
    hr_name=$(echo "$line" | sed -E 's/.*"name":"([^"]+)".*/\1/')
    timestamp=$(echo "$line" | sed -E 's/.*"ts":"([^"]+)".*/\1/')
    resource=$(echo "$line" | sed -E 's/.*"resource":"([^"]+)".*/\1/')

    # Extract patch details if available
    if [[ "$line" == *"\"patch\":"* ]]; then
      patch=$(echo "$line" | sed -E 's/.*"patch":(\[.*\]).*/\1/' | sed 's/\\//g')
      modification="[$timestamp] $resource -> $patch"
    else
      modification="[$timestamp] $resource -> No patch details"
    fi

    # Store modification details
    if [[ -z "${DRIFT_MODIFICATIONS[$hr_name]}" ]]; then
      DRIFT_MODIFICATIONS[$hr_name]="$modification"
    else
      DRIFT_MODIFICATIONS[$hr_name]="${DRIFT_MODIFICATIONS[$hr_name]}|$modification"
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

    # Display actions with timestamps
    if [[ -n "$actions" ]]; then
      IFS='|' read -ra ACTION_ARRAY <<< "$actions"
      for action in "${ACTION_ARRAY[@]}"; do
        echo "      🔄 $action"
      done
    fi

    # Display modifications with patches
    if [[ -n "${DRIFT_MODIFICATIONS[$hr]}" ]]; then
      echo "      🔧 Patches applied:"
      IFS='|' read -ra MOD_ARRAY <<< "${DRIFT_MODIFICATIONS[$hr]}"
      for mod in "${MOD_ARRAY[@]}"; do
        timestamp_resource=$(echo "$mod" | cut -d'>' -f1)
        patch_part=$(echo "$mod" | cut -d'>' -f2-)

        echo "        - $timestamp_resource>"
        if echo "$patch_part" | jq . >/dev/null 2>&1; then
          echo "$patch_part" | jq . | sed 's/^/          /'
        else
          echo "          $patch_part"
        fi
      done
    else
      echo "      🔧 No additional patch information found"
    fi

    echo ""

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
