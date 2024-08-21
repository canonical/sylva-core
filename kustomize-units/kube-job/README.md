# kube-job

This job is intended to be run as a Flux Kustomization that will overload the content of `kube-job.sh`.

This can be used (with moderation) to introduce some specific jobs in flux dependency chain, when they can not be done in other way. For example, we may use it to copy secrets and configs or to perform cluster-api pivot from bootstrap to management cluster.

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: podinfo
  namespace: flux-system
spec:
  # ...ommitted for brevity
  patches:
    - patch: |-
        apiVersion: v1
        kind: ConfigMap
        metadata:
          name: job-scripts
          namespace: sylva-system
        data:
          kube-job.sh: |
            #!/bin/sh
            kubectl get pods
```

In practice this kustomization is used in sylva-units unit definitions, relying on the `kube-job` unit template.
