#!/bin/bash

for vm in $(kubectl get vm -n kubevirt-manager -o jsonpath='{.items[*].metadata.name}'); do
  echo "Checking $vm..."

  if kubectl get vm "$vm" -n kubevirt-manager -o json | grep -q '"type": "RestartRequired"'; then
    echo "Stopping VM $vm..."
    kubectl patch vm "$vm" -n kubevirt-manager --type merge -p '{"spec":{"running":false}}'

    echo "Waiting for VM to stop..."
    while true; do
      phase=$(kubectl get vmi "$vm" -n kubevirt-manager -o jsonpath='{.status.phase}' 2>/dev/null || echo "Stopped")
      if [ "$phase" = "Stopped" ]; then
        break
      fi
      sleep 5
    done

    echo "VM is stopped. Restarting..."
    kubectl patch vm "$vm" -n kubevirt-manager --type merge -p '{"spec":{"running":true}}'
  fi
done