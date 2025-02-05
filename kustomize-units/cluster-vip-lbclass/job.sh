#!/bin/bash
if [[ $(kubectl -n kube-system get svc cluster-vip -o jsonpath='{ .spec.loadBalancerClass }') != "sylva.org/metallb-class" ]]; then
  kubectl -n kube-system get service cluster-vip -o json \
    | jq '. | del(.metadata.resourceVersion)
            | del(.metadata.uid)
            | del(.metadata.creationTimestamp)
            | del(.status)
            | .spec += {loadBalancerClass : "sylva.org/metallb-class"}' > /tmp/cluster-vip.json
  kubectl -n kube-system delete service cluster-vip
  kubectl apply -f /tmp/cluster-vip.json
  kubectl -n kube-system annotate service cluster-vip kubectl.kubernetes.io/last-applied-configuration-
  kubectl -n metallb-system patch deployment metallb-controller --type='json' \
    --patch '[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--lb-class=sylva.org/metallb-class" }]'
  kubectl -n metallb-system patch daemonset metallb-speaker --type='json' \
    --patch '[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--lb-class=sylva.org/metallb-class" }]'
fi
