This component prepares the `sylva-units` `HelmRelease` and the associated
resources to deploy a Sylva *workload cluster* based solely on OCI artifacts (instead
of fetching manifests, kustomize-based software from Git, and Helm charts
from a mix of Helm repos and Git repos).

To use this component, you'll need to add a patch in your environment values
`kustomization.yaml` to have the HelmRelease point to the version of sylva-core
that you want to deploy.

The possible tags for this artifact are the tags of the `sylva-units` Helm repository.

The `registry.gitlab.com/sylva-projects/sylva-core/sylva-units` registry can be
accessed at [here](https://gitlab.com/sylva-projects/sylva-core/container_registry/?search%5B%5D=sylva-units):

Example:

```yaml
components:
  - path/to/environment-values/components/workload-cluster-oci-artifacts

patches:
- target:
    kind: OCIRepository
    name: sylva-units
  patch: |
    - op: replace
      path: /spec/ref/tag
      value: 0.0.0-test   ## <<< the tag you want to use
```
