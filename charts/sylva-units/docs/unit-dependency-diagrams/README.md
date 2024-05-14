## Unit dependency diagrams

The diagrams here allow to visually inspect the [Kustomization dependencies](https://fluxcd.io/flux/components/kustomize/kustomizations/#dependencies) set for the units in the varioud Sylva cluster lifecycle stages (bootstrap/management/workload).

Such diagrams can be created using [tools/unit-dependency-diagram](../../../../tools/unit-dependency-diagram) and (calling [mermaid-cli](https://github.com/mermaid-js/mermaid-cli) for SVG transformation). <br/>
This tool is based on Go unmarshaling the output of `helm template --show-only templates/units.yaml` for different cluster types (bootstrap/management/workload) and flavors (kubeadm-capd/kubeadm-capo/kubeadm-capv/rke2-capd/rke2-capo/rke2-capv/rke2-capm3/rke2-capm3-virt) into Flux Kustomization objects (all other K8s objects - `Secret` and `HelmRepository` are discarded), and parsing the `Kustomization.spec.dependsOn`. <br/>
There a number of script arguments available:

| Argument                 | Description             | Default        |
| ------------------------ | ----------------------- | -------------- |
| `--suPath`/`-suPath` | relative path to sylva-units helm chart | `../../charts/sylva-units/` |
| `--allFlavors`/`-allFlavors` | boolean conditioning creation of diagrams for all sylva environment-values flavors | `false` |
| `--clusterType`/`-clusterType` | specific cluster type (`bootstrap`/`management`/`workload`) | `bootstrap` |
| `--clusterFlavor`/`-clusterFlavor` | specific environment-values flavor (`{kubeadm,rke2}-{capd,capo,capv} rke2-{capm3,capm3-virt}`) | `rke2-capo` |
| `--skipUnit`/`-skipUnit` | unit to be skipped from the diagram computation, multiple such units can be provided with repeated `--skipUnit <ks name>` args) | "" |

### Developer using the tool

If one is looking to inspect the new dependency graph after altering the dependencies of sylva-units (for e.g. in the management cluster for the rke2-capm3 setup), he/she could run:

```shell

# from sylva-core dir
$ cd tools/unit-dependency-diagram/
$ go run . --clusterType management --clusterFlavor rke2-capm3 --skipUnit root-dependency

```

### CI using this tool

To generate the Markdown files where the diagrams for each cluster type and flower would be inserted, we need to:

1) call the script that would generate Mermaid diagrams in the Markdown files;

2) have the [mermaid-cli](https://github.com/mermaid-js/mermaid-cli?tab=readme-ov-file#mermaid-cli) automatically transform the Mermaid diagram syntax from the Markdown files in individual SVG files, automatically inserted inside Markdown files at their respective Mermaid source syntax position.

```shell

# from sylva-core dir
$ cd tools/unit-dependency-diagram/
$ go run . --skipUnit root-dependency --allFlavors true
# from sylva-core dir
$ cd charts/sylva-units/docs/unit-dependency-diagrams/;
$ for mdfile in `ls  *md`; do docker run --rm -u `id -u`:`id -g` -v /root/sylva/sylva-core/charts/sylva-units/docs/unit-dependency-diagrams/:/data minlag/mermaid-cli -i $mdfile -e svg -o $mdfile; done

```
