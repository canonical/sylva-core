#!/bin/bash

set -e

kubectl -n metallb-system patch deployment metallb-controller --type='json' --patch '[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--lb-class=sylva.org/metallb-class" }]'
kubectl -n metallb-system patch daemonset metallb-speaker --type='json' --patch '[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--lb-class=sylva.org/metallb-class" }]'
