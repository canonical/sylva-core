# `rke2-etcd-secrets`

## Context

This defines a Job that is meant to handle a transition related to how
for RKE2 the etcd certificates are managed, to transition from the legacy mode
(the one implemented by RKE2 CAPI bootstrap/CP provider until version 0.2.7
which we had used in Sylva 1.1.1, where RKE2 manages the certificates itself)
to the new mode where etcd certificates are managed from the management cluster
by CAPI controllers.

## Description

The Job runs in the management cluster. It is instantiated once for each
managed cluster (a workload cluster, or the management cluster itself).

It runs in the namespace of the workload cluster.

It retrieves the RKE2-managed etcd certificates by connecting to a CP node
of the managed cluster (with `kubectl debug node`) and getting the certs
from where RKE2 stores them (`/var/lib/rancher/rke2/server/tls/etcd`).

It then creates *in the management cluster*, two Secrets containing those
certs: `<cluster-name>-etcd` and `<cluster-name>-peer-etcd`.

Those Secrets will then be used by the RKE2 CAPI bootstrap/CP provider.

## Parameters

The following parameters must be applied with envsubst:

* `CLUSTER_NAME`
