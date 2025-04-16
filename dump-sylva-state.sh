#!/bin/bash

# This script can be used to dump sylva clusters state (bootstrap/management/workload)
# it generates an archive 'sylva-dump-YYYY-MM-DDThh-mm-ss.tar.gz' which may shared (in issue by example)

source tools/shell-lib/common.sh

echo_b "👀 Dumping sylva state"
./tools/shell-lib/debug-on-exit.sh 2>&1 | tee sylva-dump.log

archive_name="sylva-dump-$(date -u '+%Y%M%d-%H%M%S').tar.gz"
contents=""
[ -d bootstrap-cluster-dump ] && contents="${contents} bootstrap-cluster-dump"
[ -d management-cluster-dump ] && contents="${contents} management-cluster-dump"
[ -d workload-cluster-dump ] && contents="${contents} workload-cluster-dump"
[ -f crust-gather.tar.gz ] && contents="${contents} crust-gather.tar.gz"
[ -f sylva-dump.log ] && contents="${contents} sylva-dump.log"

if [ -n "$contents" ]; then
  echo_b "🎁 Creating archive $archive_name"
  tar -czf "$archive_name" ${contents}
  echo "File $archive_name is ready"
else
  echo "No archive to create"
fi
