#!/usr/bin/env bash

function backup_sumup() {
    ERROR_CODE=$1
    BACKUP_SECONDS=$2

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

    if [[ -n "$PUSHGATEWAY_URL" ]]
    then
        echo "-- Push result to the pushgateway"

        curl -fs -o /dev/null --data-binary "@-" \
            "$PUSHGATEWAY_URL/metrics/job/backup-etcd/instance/etcd" > /dev/null <<< "$(cat <<EOF
# TYPE backup_status_succeeded gauge
backup_status_succeeded{cluster="${CLUSTER_NAME}"} ${BACKUP_SUCCEEDED}
# TYPE backup_duration_seconds gauge
backup_duration_seconds{cluster="${CLUSTER_NAME}"} ${BACKUP_SECONDS}
# TYPE backup_status_failed gauge
backup_status_failed{cluster="${CLUSTER_NAME}", reason="BackupFailed"} ${BACKUP_FAILED}
backup_status_failed{cluster="${CLUSTER_NAME}", reason="UploadFailed"} ${UPLOAD_FAILED}
EOF
            )" || echo "Pushgateway call failed"
    fi
}

function backup_etcd() {
    TIMESTAMP=$1

    echo ""
    echo "-- Start backing up etcd from cluster '$CLUSTER_NAME'."

    DIR=$(mktemp -d)
    BACKUP_NAME="${CLUSTER_NAME}_etcd_backup${TIMESTAMP}"

    mkdir -p ${DIR}/${BACKUP_NAME}

    etcdctl snapshot save ${DIR}/${BACKUP_NAME}/${CLUSTER_NAME}_etcd_snapshot.db --endpoints=https://127.0.0.1:2379 --cacert=/etc/kubernetes/pki/etcd/peer-ca.crt --cert=/etc/kubernetes/pki/etcd/peer-client.crt --key=/etc/kubernetes/pki/etcd/peer-client.key
    echo "-- Etcd backed up."

    ARCHIVE=$(mktemp)
    tar -czf ${ARCHIVE} -C ${DIR} ${BACKUP_NAME} || return 1
    echo "-- Backup compressed."

    BACKUP_SECONDS=$SECONDS

    mcli --config-dir /s3-config alias set backup https://${S3_HOST} ${S3_ACCESS_KEY} ${S3_SECRET_KEY} || return 2
    mcli --config-dir /s3-config put ${ARCHIVE} backup/${S3_BUCKET}/${BACKUP_NAME}.tar.gz || return 2

    echo "-- Backup uploaded"
}

SECONDS=0

if [[ -n "${TIMESTAMPED:-}" ]]
then
    TIMESTAMP="_"$(date +"%Y%m%d%H%M")
fi

backup_etcd "${TIMESTAMP:-}"
EXIT_CODE=$?
backup_sumup $EXIT_CODE $SECONDS
