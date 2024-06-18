# Using OS images built in Sylva

## Available images

In Sylva we build OS images using [diskimage-builder](https://gitlab.com/sylva-projects/sylva-elements/diskimage-builder) based on Ubuntu and openSUSE and adding the necessary packages to deploy Kubeadm or RKE2 clusters air-gapped. These are exposed as [OCI artifacts](https://gitlab.com/sylva-projects/sylva-elements/diskimage-builder/container_registry). <br/> The images are available as *plain* cloud images or *hardened* according to CIS standards. <br/> The **sylva-units** value `sylva_diskimagebuilder_images` contains all available options, with the Ubuntu plain flavor and latest supported Kubernetes version set as default. <br/> The name of the image is composed of "OS distro"-"OS version"-"plain/hardened"-"k8s distro"-"k8s version".

```yaml
sylva_diskimagebuilder_images:
  ubuntu-jammy-plain-rke2-1-27-6:
    default_enabled:  true
  ubuntu-jammy-plain-rke2-1-26-9:  {}
  ubuntu-jammy-plain-rke2-1-25-14:  {}
  ubuntu-jammy-hardened-rke2-1-27-6:  {}
  ubuntu-jammy-hardened-rke2-1-26-9:  {}
  ubuntu-jammy-hardened-rke2-1-25-14:  {}
  opensuse-15-5-plain-rke2-1-27-6:  {}
  opensuse-15-5-plain-rke2-1-26-9:  {}
  opensuse-15-5-plain-rke2-1-25-14:  {}
  opensuse-15-5-hardened-rke2-1-27-6:  {}
  opensuse-15-5-hardened-rke2-1-26-9:  {}
  opensuse-15-5-hardened-rke2-1-25-14:  {}
```

The version of [Sylva diskimage-builder](https://gitlab.com/sylva-projects/sylva-elements/diskimage-builder) used for building the images is specified as

```yaml

sylva_diskimagebuilder_version: 0.1.7

```

## Using custom images

Aditional images can be created by forking the [Sylva diskimage-builder](https://gitlab.com/sylva-projects/sylva-elements/diskimage-builder) repository and producing the desired images then pushing them as oci artifacts. These can then be used by specifying the oci repository and adding the image key under `sylva_diskimagebuilder_images`

```yaml
os_images_oci_registries:
  my-custom-repo:
    url: oci://registry.gitlab.com/my-custom-project
    tag: 0.1.1

sylva_diskimagebuilder_images:
  my-custom-image-rke2:
    os_images_oci_registry: my-custom-repo
    enabled: true
```

## How these values can simplify the deployment process

The available keys for each image are `default_enabled` and `enabled`, of boolean type. In order to use an image, it must first be enabled, unless it's the `default_enabled` one.<br/>

**Tip**: the `default_enabled` image will always be downloaded and available for usage unless specifically disabled. So if you don't intend to use it you should disable it in order to save space and time. For example if you want to deploy using Ubuntu plain and k8s version 1.26:

```yaml
sylva_diskimagebuilder_images:
  ubuntu-jammy-plain-rke2-1-27-6:
    default_enabled:  false
  ubuntu-jammy-plain-rke2-1-26-9:
    enabled: true
```

Using `sylva_diskimagebuilder_images` has different implications for CAPO versus CAPM3:<br/>

- for CAPO:<br/>by enabling the desired image(s) will make the unit `get-openstack-images` check the existence of the image(s) in Glance (based on the MD5 sum contained in the OCI artifact annotations) and, in the case an image is not found, download the artifact and push the image automatically.<br/>

```yaml
cluster:
  capo:
    image_key: ubuntu-jammy-plain-rke2-1-27-6
  control_plane:
    capo:
      image_key: ubuntu-jammy-hardened-rke2-1-27-6
```

- for CAPM3:<br/>the enabled images are automatically pulled and served by `os-image-server` and the necessary values used to consume these images are automatically computed by [`sylva-capi-cluster`](https://gitlab.com/sylva-projects/sylva-elements/helm-charts/sylva-capi-cluster).<br/>

```yaml
cluster:
  capm3:
    image_key: ubuntu-jammy-plain-rke2-1-27-6
  control-plane:
    capm3:
      image_key: ubuntu-jammy-hardened-rke2-1-27-6
```

**Note:**<br/>

- for CAPO, `image_name` is still available, but not recomended to be used. Either `image_key` or `image_name` can be specified under the same `capo` key, not both.
- for CAPM3 the same applies for `machine_image_*`. Either `image_key` or `machine_image_url` can be specified under the same `capm3` key, not both.

## Using custom images distributed over HTTP instead of OCI (legacy)

Custom images provided using a simple webserver can be used by specifying them under `os_images` key:

```yaml
os_images:
  my-custom-image:
    uri: http://192.168.130.1:8080/custom-image.raw
    filename: custom-image.raw
    md5: 4f9f1ef17cf8ecd580a682f8bb4577fa
    sha256: 916afbbf52a177fec996ee20d980bcac7c62e475f389f172dd0b5d56b9da5c77
    image-format: raw
```

**Note:** <br/>

- `uri` and `filename` are always required fields;

- `md5` is required for CAPO;

- `sha256` and `image-format` are required for CAPM3.

## bootstrap optimization

In order to save time and space during bootstrap deployment, we introduced a new optional value **bootstrap_os_images_override_enabled**

The aim of this new optional list is to enable manually only **OS images** required for management cluster deployment.
Furthermore all image_key(s) declared for management cluster will be automatically added to this dict:

- `cluster.capo.image_key` or `cluster.capm3.image_key`
- `cluster.control_plane.capo.image_key` or `cluster.control_plane.capm3.image_key` if defined
- `cluster.machine_deployment_default.capo.image_key` or `cluster.machine_deployment_default.capm3.image_key` if defined
- every `cluster.machine_deployments.*.capo.image_key` or `cluster.machine_deployments.*.capm3.image_key` if defined

The objective is to save time and disk space during the bootstrap deployment, and avoid useless image download.

In most case, you don't have to set the following dict but you can if you want to force download of OS images.

Example of settings:

```yaml
bootstrap_os_images_override_enabled:
  - ubuntu-jammy-plain-rke2-1-27-10
  - ubuntu-jammy-plain-rke2-1-26-9
```

items of this array are same as the ones used in **`sylva_diskimagebuilder_images`** and **`os_images`**.

In case you specify unknown images, an error message will be displayed
