#!/bin/bash

set -eu
set -o pipefail

# For each cronjob defined in the current cluster, this script will:
# - Create a job from it
# - Wait 300s for job completion
#
# When all jobs are proceed, it will create a report with the status of the job
# For each failed jobs we push in $DUMP_DIR
# job describe output
# get pod -o yaml
# pod logs
#
# exit in error if at least one job failed

export DUMP_DIR="${DUMP_DIR:-failed-jobs-dump}"
mkdir -p "${DUMP_DIR}"
export REPORT_FILE="${REPORT_FILE:-cronjob_report.txt}"
echo "CronJob Test Report - $(date)" > "${REPORT_FILE}"
echo "------------------------------------" >> "${REPORT_FILE}"
export SHORT_UUID=$(uuidgen | cut -c1-8)

# Array to track background process IDs
declare -a JOB_PIDS

# Function to trigger a job, wait for completion, and log status
trigger_and_wait_for_job() {
  NAMESPACE=$1
  CRONJOB_NAME=$2

  MAX_NAME_LENGTH=$((63 - ${#SHORT_UUID} - 6))  # Reserve space for "-test-" and UUID
  SHORT_NAME=$(echo "${CRONJOB_NAME}" | cut -c1-"${MAX_NAME_LENGTH}")
  JOB_NAME="${SHORT_NAME}-test-${SHORT_UUID}"

  echo "Creating job ${JOB_NAME} from cronjob ${CRONJOB_NAME} in namespace ${NAMESPACE}..."
  if ! kubectl create job --namespace="${NAMESPACE}" --from=cronjob/"${CRONJOB_NAME}" "${JOB_NAME}"; then
    echo "KO: Failed to create job for cronjob ${CRONJOB_NAME} in namespace ${NAMESPACE}" | tee -a "${REPORT_FILE}"
    return
  fi

  echo "Waiting for job ${JOB_NAME} to complete..."
  if kubectl wait --for=condition=complete --timeout=300s -n "${NAMESPACE}" job/"${JOB_NAME}"; then
    echo "OK: Job ${JOB_NAME} for cronjob ${CRONJOB_NAME} in namespace ${NAMESPACE} completed successfully." | tee -a "${REPORT_FILE}"
  else
    echo "KO: Job ${JOB_NAME} for cronjob ${CRONJOB_NAME} in namespace ${NAMESPACE} did not complete successfully within timeout." | tee -a "${REPORT_FILE}"
    echo "Dumping ${JOB_NAME} for cronjob ${CRONJOB_NAME} in namespace ${NAMESPACE}"
    kubectl describe job "${JOB_NAME}" -n "${NAMESPACE}" > "${DUMP_DIR}/${JOB_NAME}.yaml" || true
    kubectl get pods -n "${NAMESPACE}" --selector=job-name="${JOB_NAME}" -o yaml > "${DUMP_DIR}/pods-${JOB_NAME}.yaml" || true
    kubectl get pods --selector=job-name="${JOB_NAME}" --no-headers -o custom-columns=":metadata.name" | xargs -I % sh -c "kubectl logs % > ${DUMP_DIR}/%.log" || true
  fi

  echo "Cleaning up job ${JOB_NAME}..."
  kubectl delete job "${JOB_NAME}" -n "${NAMESPACE}" --ignore-not-found
}

# Export the function to make it available in subshells
export -f trigger_and_wait_for_job

# Fetch all cronjobs from all namespaces and 
# process them in parallel
while read NAMESPACE CRONJOB_NAME; do
  # Generate a short UUID and create a unique job name within 63 characters (k8s limitation)
  # Run the job trigger and wait function in the background
  trigger_and_wait_for_job "${NAMESPACE}" "${CRONJOB_NAME}" &
  JOB_PIDS+=("$!") # Save the process ID of the background job
done < <(kubectl get cronjobs --all-namespaces -o custom-columns="NAMESPACE:.metadata.namespace,NAME:.metadata.name" --no-headers)


# Wait for all background jobs to finish
for PID in "${JOB_PIDS[@]}"; do
  wait "${PID}"
done

echo ""
echo "All jobs processed. Report generated at ${REPORT_FILE}."
echo ""
cat "${REPORT_FILE}"
echo ""

if grep KO "${REPORT_FILE}"; then
  echo "Some jobs failed"
  exit 1
fi
