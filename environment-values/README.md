This directory contains some Kustomizations to install a flux HelmRelease of the sylva-units chart.

It is not the only way to instanciate the chart, neither the simplest one, but it enables to merge several layers of values that correspond to various environemnts. At the end, it will help to limit the amount of variables that users have provide for a specific deployment.

# Managing sylva-units helmrelease values

We use [Kustomize](https://kubectl.docs.kubernetes.io/references/kustomize/kustomization/) to generate ConfigMaps and Secrets that are used to instantiate the `sylva-units` Helm chart [helm-release.yaml](../kustomize-units/sylva-units/base/helm-release.yaml) as override values over the chart default values [values.yaml](../charts/sylva-units/values.yaml). These kustomizations are just provided as samples to help users build resources that follow the expected format, feel free to build them to see how they look like (you can use `kubectl kustomize environment-values/kubeadm-capd` for example, or `kustomize build --load-restrictor LoadRestrictionsNone environment-values/rke2-capo` if your `environment-values/rke2-capo/kustomization.yaml` is a symbolic link).

The typical pattern used to inject values consists in creating a ConfigMap or a Secret, and append it to the list of values used by the chart, for example:

```
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../kustomize-units/sylva-units/base

configMapGenerator:
- name: sylva-units-values
  options:
    disableNameSuffixHash: true
  files:
  - values=values.yaml

patches:
- target:
    kind: HelmRelease
    name: sylva-units
  patch: |
    - op: add
      path: /spec/valuesFrom/-
      value:
        kind: ConfigMap
        name: sylva-units-values
        valuesKey: values
```

where `values.yaml` is a plain yaml file that will be merged over charts defaults, for example, it could override the number of control plane nodes:

```
cluster:
  control_plane_replicas: 5
```

# Sharing configurations

This mechanism can be extended to provide a convenient way to add various layers of specialisation for the chart. For example, you can override chart defaults with your company default, and another layer of values that corresponds to the environment. Kustomize units are very convenient for that purpose, as they'll allow to define various sets of parameters that can be appended to the values.

For example, your could host your company proxy definition in some internal repository, containing the following kustomization.yaml:

```
apiVersion: kustomize.config.k8s.io/v1alpha1
kind: Component

configMapGenerator:
- name: acme-corp-proxy
  options:
    disableNameSuffixHash: true
  files:
  - proxy-values=values.yaml

patches:
- target:
    kind: HelmRelease
    name: sylva-units
  patch: |
    - op: add
      path: /spec/valuesFrom/-
      value:
        kind: ConfigMap
        name: acme-corp-proxy
        valuesKey: proxy-values
```

And the associated values.yaml containing proxy definitions:

```
proxies:
  http_proxy: http_proxy=http://acme.corp.proxy.com
  https_proxy: http_proxy=http://acme.corp.proxy.com

no_proxy_additional:
  corp.com: true
```

These configuration values can then be easely consumed by any deployment that just has to reference this unit in its environment-value's kustomization:

```
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../kustomize-units/sylva-units/base

units:
  - ssh://git@acme.git.repo.com/repo.git/environment-values/proxy?ref=main

configMapGenerator:
[...] # Some additionnal values relative to the deployment
```

:::note
In environments where the bootstrap cluster host is behind a forward proxy, usage of [Kustomize remote targets](https://github.com/kubernetes-sigs/kustomize/blob/master/examples/remoteBuild.md) in environment-value's kustomization is dependent on Git reachability over SSH or HTTPS.
To ensure that is provided, running `kustomize build` for the remote build target should be done prior to running `bootstrap.sh`.
For HTTPS transport, this would mean:

```console

export GIT_SSL_NO_VERIFY=true    # disable git TLS cert validation if needed
git config --global http.proxy $HTTP_PROXY    # set a proxy for git
git config --global credential.helper cache    # enable credentials storage in git, if preferred. Attention, this method saves credentials in plaintext on disk
git config --global credential.helper "cache --timeout=604800"    # enable git credentials caching for 1 week
git clone <REMOTE_REPOSITORY_URL>    # run some operation to set git credentials
kustomize build git::<REMOTE_REPOSITORY_URL>/path/to/kustomization-in-your-dev-env/?ref=master #kustomize build should then work and bootstrap.sh would fetch remote targets

```

:::

# How values are merged

All the provided values will be applied by Flux to the chart, in the following order of precedence (an item appearing later in the following list overrides the same item if it was specified earlier, see https://fluxcd.io/flux/units/helm/helmreleases/#values-overrides):

- `spec.chart.spec.valuesFiles`
- items in `spec.valuesFrom` (in the specified order)
- `spec.values`

Keep in mind that these values will be merged by helm over default values of the chart (as in json-merge, not strategic merge) so list/arrays will be overriden, for example:

```
CHART VALUES.YAML:
ports_list:
  - 80
  - 443

USER-SUPPLIED VALUES:
ports_list:
  - 8080
  - 8443

COMPUTED VALUES:
ports_list:
  - 8080
  - 8443
```

You must also pay attention to null values, as Helm interprets them as an [instrution to delete the corresponding key](https://helm.sh/docs/chart_template_guide/values_files/#deleting-a-default-key), which is fairly different from typical dict merge behaviour:

```
CHART VALUES.YAML:
proxies:
  http_proxy: ""
  https_proxy: ""

USER-SUPPLIED VALUES:
proxies:
  http_proxy:
  https_proxy:

COMPUTED VALUES:
proxies: {}
```

As the values may be defined and overwritten by several ConfigMaps and Secrets, it may be hard to figure out how the final merge will look like. In order to enable users to preview how the final chart value will look like, the `preview.sh` enables to instanciate the sylva-units chart in a specific namespace, with all flux child resources suspended. This way, you'll be able to test if chart works properly with provided values, how user-values will be merged, and the result of values go-templating rendering.
