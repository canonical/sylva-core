#!/usr/bin/env bash

# Helper script used to clean management and workload clusters OpenStack resources. USE WITH CARE, AT YOU OWN RISK

OS_ARGS=""
PLATFORM=$1
if [ ! -z $PLATFORM ]; then
  OS_ARGS="--os-cloud $PLATFORM"
fi
OS_ARGS="$OS_ARGS --insecure --os-compute-api-version 2.26"
CAPO_TAG=${2:-sylva-$(openstack ${OS_ARGS} configuration show -f json | jq -r '."auth.username"')}

if openstack ${OS_ARGS} endpoint list &> /dev/null; then
    echo "This script should not be run with admin role, otherwise it may impact other tenants"
    exit 1
fi

echo -e "\U0001F5D1 Start cleanup for tag '${CAPO_TAG}' at $(date)"

SERVERS="$(openstack ${OS_ARGS} server list --tags ${CAPO_TAG} -f value -c Name)"

if [ -n "$SERVERS" ] ; then
  echo -e "The following servers match the '${CAPO_TAG}' tag:\n${SERVERS}\n"
  
  echo -e "\U0001F5D1 Pausing servers: ${SERVERS//$'\n'/ }"
  openstack ${OS_ARGS} server pause ${SERVERS//$'\n'/ }
  echo -e "\U0001F5D1 Deleting servers: ${SERVERS//$'\n'/ }"
  openstack ${OS_ARGS} server delete --wait ${SERVERS//$'\n'/ }
  echo -e "\U0001F5D1 Deleting volumes: ${SERVERS//$'\n'/-root }"
  openstack ${OS_ARGS} volume delete ${SERVERS//$'\n'/-root } --purge || true
else
  echo -e "(no server to cleanup)"
fi

for i in $(seq 1 10)
do
  if (openstack ${OS_ARGS} port list --tags ${CAPO_TAG} -f value -c name -c status -c device_owner -c id | grep -v "DOWN" >& /dev/null)
  then
    echo "Waiting for all ports to be DOWN"
    sleep 3
  else
    echo "All ports are DOWN"
    openstack ${OS_ARGS} port list --tags ${CAPO_TAG} -f value -c name -c status -c device_owner -c id | awk '$2=="DOWN" {print $4}' | xargs -tr openstack ${OS_ARGS} port delete || true
    break
  fi
done

for i in $(seq 1 10)
do
  if [ $(openstack ${OS_ARGS} port list --tags ${CAPO_TAG} -f value -c name -c status -c device_owner -c id | wc -l) -gt 0 ]
  then
    echo "Waiting for all ports to be deleted"
    sleep 3
  else
    echo "All ports are deleted"
    openstack ${OS_ARGS} security group list --tags ${CAPO_TAG} -f value -c ID | xargs -tr openstack ${OS_ARGS} security group delete || true
    break
  fi
done

volumes=$(openstack ${OS_ARGS} volume list --status available --long -c Name -c Properties -f json | jq -r ".[] | select(.Properties.\"cinder.csi.openstack.org/cluster\" == \"$CAPO_TAG\").Name")
echo "openstack ${OS_ARGS} volume delete --purge $volumes"
openstack ${OS_ARGS} volume delete --purge $volumes

if [ -n "$(openstack ${OS_ARGS} server list -f value --tags ${CAPO_TAG})" ]; then
    echo "The following CAPO machines tagged ${CAPO_TAG} were not removed, please try again, and delete the corresponding stacks"
    openstack ${OS_ARGS} server list --tags ${CAPO_TAG} -f value -c Name
    exit 1
elif [ -n "$(openstack ${OS_ARGS} security group list -f value --tags ${CAPO_TAG})" ]; then
    echo "The following CAPO security group tagged ${CAPO_TAG} were not removed, please try again, and delete the corresponding stacks"
    openstack ${OS_ARGS} security group list --tags ${CAPO_TAG} -f value -c Name
    exit 1
elif [ -n "$(openstack ${OS_ARGS} volume list --long -c Name -c Properties -f json | jq -r ".[] | select(.Properties.\"cinder.csi.openstack.org/cluster\" == \"$CAPO_TAG\").Name")" ]; then
    echo "The following CAPO PVC volume tagged ${CAPO_TAG} were not removed, please try again, and delete the corresponding stacks"
    openstack ${OS_ARGS} volume list --long -c Name -c Properties -f json | jq -r ".[] | select(.Properties.\"cinder.csi.openstack.org/cluster\" == \"$CAPO_TAG\").Name"
    exit 1
else
    openstack ${OS_ARGS} stack list --tags ${CAPO_TAG} -f value -c ID | xargs -tr openstack ${OS_ARGS} stack delete || true
fi
