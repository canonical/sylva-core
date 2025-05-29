#!/usr/bin/env bash

set -o pipefail

function exit_trap() {
    echo ""
    echo "Backup summary:"
    echo "  $(printf "%3d" $nb_succeeded) Succeeded:$succeeded"
    echo "  $(printf "%3d" $nb_failed) Failed   :$failed"
}
trap exit_trap EXIT

function backup_sumup() {
    NAMESPACE=$1
    ERROR_CODE=$2
    BACKUP_SECONDS=$3

    BACKUP_SUCCEEDED=$(( ERROR_CODE == 0 ? 1 : 0 ))
    BACKUP_FAILED=$(( ERROR_CODE == 1 ? 1 : 0 ))
    UPLOAD_FAILED=$(( ERROR_CODE == 2 ? 1 : 0 ))

    if [ $BACKUP_SUCCEEDED -eq 1 ]; then
        echo "Backup succeeded in ${BACKUP_SECONDS} seconds"
    elif [ $BACKUP_FAILED -eq 1 ]; then
        echo "Backup failed in ${BACKUP_SECONDS} seconds"
    elif [ $UPLOAD_FAILED -eq 1 ]; then
        echo "Upload failed in ${BACKUP_SECONDS} seconds"
    fi

    if [[ -n "${PUSHGATEWAY_URL:-}" ]]
    then
        echo "-- Push result to the pushgateway"

        curl -fs -o /dev/null --data-binary "@-" \
            "$PUSHGATEWAY_URL/metrics/job/backup-capi-resources/instance/capi" > /dev/null <<< "$(cat <<EOF
# TYPE backup_status_succeeded gauge
backup_status_succeeded{namespace="${NAMESPACE}"} ${BACKUP_SUCCEEDED}
# TYPE backup_duration_seconds gauge
backup_duration_seconds{namespace="${NAMESPACE}"} ${BACKUP_SECONDS}
# TYPE backup_status_failed gauge
backup_status_failed{namespace="${NAMESPACE}", reason="BackupFailed"} ${BACKUP_FAILED}
backup_status_failed{namespace="${NAMESPACE}", reason="UploadFailed"} ${UPLOAD_FAILED}
EOF
            )" || echo "Pushgateway call failed"
    fi
}

function backup_namespace() {
    TIMESTAMP=$1
    NAMESPACE=$2

    echo ""
    echo "-- Start backing up clusters from namespace '$NAMESPACE'."

    DIR=$(mktemp -d)
    BACKUP_NAME="${NAMESPACE}_capi_resources_backup${TIMESTAMP}"

    mkdir -p ${DIR}/${BACKUP_NAME}

    clusterctl move -n "$NAMESPACE" --to-directory ${DIR}/${BACKUP_NAME} || return 1

    if [[ -n "${ADDITIONAL_RESOURCES:-}" ]]; then
        echo "-- Backing up additional resources : ${ADDITIONAL_RESOURCES}"
        kubectl get $ADDITIONAL_RESOURCES -n "$NAMESPACE" -o yaml --ignore-not-found > ${DIR}/${BACKUP_NAME}/${NAMESPACE}_additional_resources.yaml || return 1
    fi

    echo "-- Cluster backed up."

    ARCHIVE=$(mktemp)
    tar -czf ${ARCHIVE} -C ${DIR} ${BACKUP_NAME} || return 1
    echo "-- Backup compressed."

    BACKUP_SECONDS=$SECONDS

    mcli --config-dir /s3-config alias set backup https://${S3_HOST} ${S3_ACCESS_KEY} ${S3_SECRET_KEY} || return 2
    mcli --config-dir /s3-config put ${ARCHIVE} backup/${S3_BUCKET}/${BACKUP_NAME}.tar.gz || return 2

    echo "-- Backup uploaded"
}

# clusterctl is moving all CAPI resources from a namespace, even if it contains several clusters. Backup is per namespace, not per cluster.
NAMESPACES_LIST=$(kubectl get clusters.cluster.x-k8s.io --all-namespaces -o=json | jq -r -c '[.items[] | .metadata.namespace].[]' | sort | uniq) || exit 2

if [ -z "$NAMESPACES_LIST" ]; then
  echo "No namespaces found to backup."
  exit 0
fi

echo "List of namespaces to backup :" $(IFS=, ; echo "${NAMESPACES_LIST[*]}")

nb_failed=0
failed=""
nb_succeeded=0
succeeded=""

if [[ -n "${TIMESTAMPED:-}" ]]
then
    TIMESTAMP="_"$(date +"%Y%m%d%H%M")
fi

while read -r NAMESPACE; do
    SECONDS=0

    backup_namespace "${TIMESTAMP:-}" $NAMESPACE
    EXIT_CODE=$?
    backup_sumup $NAMESPACE $EXIT_CODE $SECONDS

    if [ $EXIT_CODE -ne 0 ]; then
        ((nb_failed++))
        failed="$failed $NAMESPACE"
    else
        ((nb_succeeded++))
        succeeded="$succeeded $NAMESPACE"
    fi
done < <(echo "${NAMESPACES_LIST}")
