#!/usr/bin/env bash

set -e
set -o pipefail

NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)

set_kubeconfig() {
    set -e
    kubectl config set-cluster $NAMESPACE --server=https://${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT} --certificate-authority=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    kubectl config set-credentials user --token=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
    kubectl config set-context $NAMESPACE --cluster=$NAMESPACE --user=user --namespace=$NAMESPACE
    kubectl config use-context $NAMESPACE
}

NAMESPACE=sylva-system

function exit_trap() {
    EXIT_CODE=$?

    BACKUP_SUCCEEDED=$(( EXIT_CODE == 0 ? 1 : 0 ))
    BACKUP_FAILED=$(( EXIT_CODE == 1 ? 1 : 0 ))
    UPLOAD_FAILED=$(( EXIT_CODE == 2 ? 1 : 0 ))

    echo "-- Summary"
    echo "Backup succeeded : ${BACKUP_SUCCEEDED}"
    echo "Backup failed : ${BACKUP_FAILED}"
    echo "Upload failed : ${UPLOAD_FAILED}"

    if [[ -n "$PUSHGATEWAY_URL" ]]
    then
        echo "-- Inform monitoring"
        
        cat <<EOF | curl -s --data-binary @- $PUSHGATEWAY_URL/metrics/job/backup-cluster-capi/instance/capi
# TYPE backup_status_succeeded gauge
backup_status_succeeded{namespace="${NAMESPACE}"} ${BACKUP_SUCCEEDED}
# TYPE backup_duration_seconds gauge
backup_duration_seconds{namespace="${NAMESPACE}"} ${BACKUP_SECONDS}
# TYPE backup_status_failed gauge
backup_status_failed{namespace="${NAMESPACE}", reason="BackupFailed"} ${BACKUP_FAILED}
backup_status_failed{namespace="${NAMESPACE}", reason="UploadFailed"} ${UPLOAD_FAILED}
EOF
    fi

    exit $EXIT_CODE
}
trap exit_trap EXIT

SECONDS=0

echo "-- Set kubectl configuration."
export KUBECONFIG=/tmp/kubeconfig
set_kubeconfig || exit 1

echo "-- Clusters to backup from namespace '$NAMESPACE':"
kubectl get cluster || exit 1

echo "-- Start backing up clusters from namespace '$NAMESPACE'."
mkdir -p /tmp/$NAMESPACE
clusterctl move --to-directory /tmp/$NAMESPACE || exit 1
echo "-- Clusters from namespace '$NAMESPACE' backed up."

tar -czf /tmp/backup_cluster_capi_${NAMESPACE}.tar.gz /tmp/$NAMESPACE || exit 1
echo "-- Backup compressed."

BACKUP_SECONDS=$SECONDS

echo "-- Upload backup to S3"
mcli --config-dir /s3-config mb backup/${S3_BUCKET} && \
    mcli --config-dir /s3-config put /tmp/backup_cluster_capi_${NAMESPACE}.tar.gz backup/${S3_BUCKET} || exit 2

echo "-- Backup uploaded"
BACKUP_SUCCEEDED=1
