# OCI artifacts component

This component prepares the `sylva-units` `HelmRelease` and the associated
resources to deploy Sylva based solely on OCI artifacts (instead
of fetching manifests, kustomize-based software from Git, and Helm charts
from a mix of Helm repos and Git repos).

## Usage

/!\ FIXME: this README should be revisited /!\

To use this component, you'll need to add a patch in your environment values
`kustomization.yaml` to have the HelmRelease point to the version of sylva-core
that you want to deploy.

The possible tags for this artifact are the tags of the `sylva-units` Helm repository.

The `registry.gitlab.com/sylva-projects/sylva-core/sylva-units` registry can be
accessed at [here](https://gitlab.com/sylva-projects/sylva-core/container_registry/?search%5B%5D=sylva-units):

Example:

```yaml
components:
  - path/to/environment-values/components/oci-artifacts

patches:
- target:
    kind: HelmRelease
    name: sylva-units
  patch: |
    - op: replace
      path: /spec/chart/spec/version
      value: 0.0.0-test   ## <<< the tag you want to use
```

### OCI Artifact verification configuration

The OCI artifact verification settings is including on the following configuration in `values.yaml` file:

```yaml
security:
  oci_artifacts:
    skip_signing_check: false
    cosign_public_key: | # The OCI public key is not the default public key used to verify Sylva elements, e.g., os_images
      -----BEGIN PUBLIC KEY-----
      MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEEN6LNycNA/OB8/dtqTPZcPDuLnxW
      hR0Rskmno7Lx1WqBl2ylN/sfkLEAPfCkizceHiu/fw8lnsPq9uSGlAICeQ==
      -----END PUBLIC KEY-----
```

> Currently, only tagged versions of OCI artifacts are signed. Therefore, it is necessary to override the user configuration in the `values.yaml` file if this check is not necessary:

```yaml
security:
  oci_artifacts:
    skip_signing_check: true
```
