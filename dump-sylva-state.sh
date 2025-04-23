#!/bin/bash

# This script can be used to dump sylva clusters state (bootstrap/management/workload)
# it generates an archive 'sylva-dump-YYYY-MM-DDThh-mm-ss.tar.gz' which may shared (in issue by example)

USER_PWD=$(pwd)
DUMPS_DIR="$USER_PWD/dumps"
CURRENT_DUMP_DIR="$USER_PWD/dumps/current-dump"

source $(dirname $(realpath $0))/tools/shell-lib/common.sh

ensure_sylva_toolbox

rm -rf "$CURRENT_DUMP_DIR"
mkdir -p "$CURRENT_DUMP_DIR"
cd "$CURRENT_DUMP_DIR"

echo_b "👀 Dumping sylva state"
${BASE_DIR}/tools/shell-lib/debug-on-exit.sh 2>&1 | tee sylva-dump.log

archive_name="$DUMPS_DIR/sylva-dump-$(date -u '+%Y%m%d-%H%M%S').tar.gz"
relative_archive_name=$(realpath -s --relative-to="$USER_PWD" "$archive_name")

echo_b "🎁 Creating archive $relative_archive_name"
ls
tar -czf "$archive_name" "."
echo "File $relative_archive_name is ready"
