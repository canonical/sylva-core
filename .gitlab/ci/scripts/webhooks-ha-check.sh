#!/bin/bash

# --- Configuration ---
REPORT_FILE="${REPORT_FILE:-webhooks_report.txt}"

# --- Script Setup ---
total_services_checked=0
failed_services_count=0
declare -a WEBHOOK_ENDPOINT_CHECK_PIDS

# Function to check a single service's endpoints
check_service_endpoints() {
    local webhook=$1
    local service_name=$2
    local service_namespace=$3
    
    if [[ -z "$service_name" || -z "$service_namespace" ]]; then
        echo "Skipping invalid entry: service='${service_name}', namespace='${service_namespace}'" | tee -a "${REPORT_FILE}"
        return
    fi

    endpointslice_json=$(kubectl get endpointslices \
        -n "${service_namespace}" \
        -l "kubernetes.io/service-name=${service_name}" \
        -o json)
    total_endpoint_count=$(echo "${endpointslice_json}" | jq '[.items[].endpoints | length] | add // 0')

    if ! [[ "$total_endpoint_count" =~ ^[0-9]+$ ]]; then
        echo "  WARN: Could not determine total endpoint count (received: ${total_endpoint_count}). Assuming 0." | tee -a "${REPORT_FILE}"
        total_endpoint_count=0
    fi

    if [[ "${total_endpoint_count}" -lt "${MIN_REPLICAS}" ]]; then
        echo "  FAILED: Webhook '${webhook}' uses service '${service_name}' in '${service_namespace}' namespace with ${total_endpoint_count} endpoints (requires ${MIN_REPLICAS})" | tee -a "${REPORT_FILE}"
        return 1
    else
        echo "  PASSED: Webhook '${webhook}' uses service '${service_name}' in '${service_namespace}' namespace with ${total_endpoint_count} endpoints" | tee -a "${REPORT_FILE}"
        return 0
    fi
}

# Export the function to make it available in subshells
export -f check_service_endpoints
export MIN_REPLICAS

echo "This script verifies webhook services have sufficient endpoints (minimum: ${MIN_REPLICAS}) for high availability." | tee -a "${REPORT_FILE}"
echo "---" | tee -a "${REPORT_FILE}"

# --- Main Logic ---
if [[ ${#EXEMPT_WEBHOOKS[@]} -gt 0 ]]; then
    echo "The following webhooks are exempt from HA checks:" | tee -a "${REPORT_FILE}"
    echo "${EXEMPT_WEBHOOKS[@]}" | tr ' ' '\n' | tee -a "${REPORT_FILE}"
fi

echo "---" | tee -a "${REPORT_FILE}"
echo "Fetching webhooks using current kubectl context..." | tee -a "${REPORT_FILE}"

# Prepare exemptions array for jq
exemptions_json_array=$(printf '%s\n' "${EXEMPT_WEBHOOKS[@]}" | jq -R . | jq -s .)

# Get webhook configurations excluding exempt ones
webhooks_list=$(kubectl get validatingwebhookconfigurations,mutatingwebhookconfigurations -o json \
    | jq -r --argjson exemptions "$exemptions_json_array" '
        .items[] | select(.metadata.name as $name | $exemptions | index($name) | not) | .metadata.name
    ')

echo "The following webhooks will be analyzed for HA compliance:" | tee -a "${REPORT_FILE}"
echo "$webhooks_list" | tee -a "${REPORT_FILE}"

# Get webhook configs, filter out exempted ones and extract unique service details
webhook_services_list=$(kubectl get validatingwebhookconfigurations,mutatingwebhookconfigurations -o json \
    | jq -r --argjson exemptions "$exemptions_json_array" '
        .items[] as $item
        | select($item.metadata.name as $name | $exemptions | index($name) | not)
        | $item.webhooks[]?
        | select(.clientConfig.service?)
        | "\($item.metadata.name) \(.clientConfig.service.name) \(.clientConfig.service.namespace)"
    ' | sort -u)

if [[ -z "$webhook_services_list" ]]; then
    echo "No non-exempt webhook services found referencing Kubernetes services in the current context." | tee -a "${REPORT_FILE}"
    exit 0 # Nothing to check
fi

echo "---" | tee -a "${REPORT_FILE}"
echo "Found non-exempt services to check. Analyzing total endpoint counts..." | tee -a "${REPORT_FILE}"

# Process each service in parallel
while IFS=' ' read -r webhook service_name service_namespace; do
    total_services_checked=$((total_services_checked + 1))
    check_service_endpoints "${webhook}" "${service_name}" "${service_namespace}" &
    WEBHOOK_ENDPOINT_CHECK_PIDS+=("$!")
done <<< "${webhook_services_list}"

# Wait for all background processes to complete and count failures
for PID in "${WEBHOOK_ENDPOINT_CHECK_PIDS[@]}"; do
    if ! wait "${PID}"; then
        failed_services_count=$((failed_services_count + 1))
    fi
done

# --- Summary ---
echo "---" | tee -a "${REPORT_FILE}"
echo "Total Non-Exempt Webhook Services Checked: ${total_services_checked}" | tee -a "${REPORT_FILE}"
echo "Services Failing HA Check (< ${MIN_REPLICAS} total endpoints): ${failed_services_count}" | tee -a "${REPORT_FILE}"

if [[ ${failed_services_count} -gt 0 ]]; then
    echo "HA Check FAILED (based on total endpoints for non-exempt services)." | tee -a "${REPORT_FILE}"
    exit 1 # Exit with error
else
    echo "All checked non-exempt webhook services meet the HA requirement of >= ${MIN_REPLICAS} total endpoints." | tee -a "${REPORT_FILE}"
    echo "HA Check PASSED (based on total endpoints for non-exempt services)." | tee -a "${REPORT_FILE}"
    exit 0 # Exit successfully
fi
