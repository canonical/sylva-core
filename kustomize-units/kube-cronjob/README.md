# kube-cronjob

This cronjob is intended to be run as a Flux Kustomization that will overload the content of `kube-cronjob.sh`.

This can be used (with moderation) to introduce some specific cronjobs to execute regularly some tasks, when they can not be done in other way. For example, we may use it to renew secrets and configs.

The schedule can be overridden by patching the CronJob.spec.schedule.

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: podinfo
  namespace: foo
spec:
  path: ./kustomize-units/kube-cronjob
  # ...ommitted for brevity
  patches:
    - patch: |-
        apiVersion: v1
        kind: ConfigMap
        metadata:
          name: _unused_
          namespace: sylva-system
        data:
          kube-cronjob.sh: |
            #!/bin/sh
            kubectl get pods
      target:
        kind: ConfigMap
        name: kube-cronjob-cm
```

In practice this kustomization is used in sylva-units unit definitions, relying on the `kube-cronjob` unit template.
