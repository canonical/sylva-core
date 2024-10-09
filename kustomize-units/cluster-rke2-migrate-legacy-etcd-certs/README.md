# `cluster-rke2-migrate-legacy-etcd-certs`

## Context

This defines a Job that is meant to handle a transition related to how
for RKE2 the etcd certificates are managed, to transition from the legacy mode
(the one implemented by RKE2 CAPI bootstrap/CP provider until version 0.2.7
which we had used in Sylva 1.1.1, where RKE2 manages the certificates itself)
to the new mode where etcd certificates are managed from the management cluster
by CAPI controllers.

## Description

The Job runs in the management cluster. It is instantiated once in sylva-system
namespace and processes all RKE2 clusters managed by CAPI from the mgmt cluster
(any workload clusters or the management cluster itself).

It retrieves the RKE2-managed etcd certificates by connecting to a CP node
of the managed cluster (with `kubectl debug node`) and getting the certs
from where RKE2 stores them (`/var/lib/rancher/rke2/server/tls/etcd`).

It then creates *in the management cluster*, two Secrets containing those
certs: `<cluster-name>-etcd` and `<cluster-name>-peer-etcd`.

Those Secrets will then be used by the RKE2 CAPI bootstrap/CP provider.

## Troubleshooting

The job sets the label `sylva/rke2-etcd-secrets-migrate` on RKE2ControlPlane resources:

* `not-needed` indicates that no migration was necessary (cluster provisioned with a recent-enough version of the RKE2 CAPI bootstrap/CP provider)
* `attempted` indicates that a migration was attempted, but that none succeeded yet
* `done` indicates that a migration was done

On completion of the migration of *all clusters*, it sets the `sylva/rke2-etcd-secrets-migrate`
label on the `sylva-units` HelmRelease in `sylva-system` namespace.
