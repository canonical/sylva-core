# Sylva Supply Chain Security

This work is in progress

## Provenance Attestation

### Docker images

Each Sylva built-in Docker image are shipped with its **SLSA provenance** (how an image was built) and **SBOM** (list of softwares in the image, or artifacts that were used to build the image) attestations created at build-time by [BuildKit](https://docs.docker.com/build/attestations/).

The purpose of attestations is to make it possible to inspect an image and see where it comes from, who created it and how, and what it contains.

The attestations are attached to the image as metadata, as illustrated below (the second manifest covers the attestations):

```shell
docker manifest inspect registry.gitlab.com/sylva-projects/sylva-elements/container-images/sylva-toolbox:v0.3.14
{
   "schemaVersion": 2,
   "mediaType": "application/vnd.oci.image.index.v1+json",
   "manifests": [
      {
         "mediaType": "application/vnd.oci.image.manifest.v1+json",
         "size": 862,
         "digest": "sha256:1f2c62f97c41f9c9d5df75df9bb6a1c539fa9ae361ac85e28c4eb93fac30f906",
         "platform": {
            "architecture": "amd64",
            "os": "linux"
         }
      },
      {
         "mediaType": "application/vnd.oci.image.manifest.v1+json",
         "size": 840,
         "digest": "sha256:54b08c64c6b8b34b2eb3a451cb0c5ee7dec30f62286ac3c9576381012bebd6f8",
         "platform": {
            "architecture": "unknown",
            "os": "unknown"
         }
      }
   ]
}
```

 inspecting the attestation manifest with the `--verbose` flag

```shell
 $ docker manifest inspect --verbose registry.gitlab.com/sylva-projects/sylva-elements/container-images/sylva-toolbox@sha256:54b08c64c6b8b34b2eb3a451cb0c5ee7dec30f62286ac3c9576381012bebd6f8
{
        "Ref": "registry.gitlab.com/sylva-projects/sylva-elements/container-images/sylva-toolbox@sha256:54b08c64c6b8b34b2eb3a451cb0c5ee7dec30f62286ac3c9576381012bebd6f8",
        "Descriptor": {
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "digest": "sha256:54b08c64c6b8b34b2eb3a451cb0c5ee7dec30f62286ac3c9576381012bebd6f8",
                "size": 840,
                "platform": {
                        "architecture": "unknown",
                        "os": "unknown"
                }
        },
        "Raw": "ewo....XQp9",
        "OCIManifest": {
                "schemaVersion": 2,
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "config": {
                        "mediaType": "application/vnd.oci.image.config.v1+json",
                        "digest": "sha256:fc38be3f5fbb0af5dfebc4623b18fa92ff21f785ab970fc0335dc74b645a4989",
                        "size": 241
                },
                "layers": [
                        {
                                "mediaType": "application/vnd.in-toto+json",
                                "digest": "sha256:82435dccb73efc762466cda93b9141cd4a19f0a84bc33cf559bb56cf2be6ad42",
                                "size": 872621,
                                "annotations": {
                                        "in-toto.io/predicate-type": "https://spdx.dev/Document"
                                }
                        },
                        {
                                "mediaType": "application/vnd.in-toto+json",
                                "digest": "sha256:6fe4da0571cad755675cb7845012510d564ddcb128a25b118258f113f7bf6871",
                                "size": 12471,
                                "annotations": {
                                        "in-toto.io/predicate-type": "https://slsa.dev/provenance/v0.2"
                                }
                        }
                ]
        }
}
```

You can also use `docker buildx` to inspect the list of image manifests:

```shell
$ docker buildx imagetools inspect registry.gitlab.com/sylva-projects/sylva-elements/container-images/sylva-toolbox:v0.3.14
Name:      registry.gitlab.com/sylva-projects/sylva-elements/container-images/sylva-toolbox:v0.3.14
MediaType: application/vnd.oci.image.index.v1+json
Digest:    sha256:41995533b13b575f7fe6cf204be2e76752297a46cd972d361a31261df851730b

Manifests:
  Name:        registry.gitlab.com/sylva-projects/sylva-elements/container-images/sylva-toolbox:v0.3.14@sha256:1f2c62f97c41f9c9d5df75df9bb6a1c539fa9ae361ac85e28c4eb93fac30f906
  MediaType:   application/vnd.oci.image.manifest.v1+json
  Platform:    linux/amd64

  Name:        registry.gitlab.com/sylva-projects/sylva-elements/container-images/sylva-toolbox:v0.3.14@sha256:54b08c64c6b8b34b2eb3a451cb0c5ee7dec30f62286ac3c9576381012bebd6f8
  MediaType:   application/vnd.oci.image.manifest.v1+json
  Platform:    unknown/unknown
  Annotations:
    vnd.docker.reference.digest: sha256:1f2c62f97c41f9c9d5df75df9bb6a1c539fa9ae361ac85e28c4eb93fac30f906
    vnd.docker.reference.type:   attestation-manifest
```

An attestation can be retrieved by using  `docker buildx imagetools` . The **SLSA provenance** and the **SBOM** can respectively be retrieved as follow:

```shell
docker buildx imagetools inspect [image]:[TAG] --format "{{json .Provenance.SLSA}}"

docker buildx imagetools inspect [image]:[TAG]--format "{{json .SBOM.SPDX}}"
```

For example:

```shell
docker buildx imagetools inspect registry.gitlab.com/sylva-projects/sylva-elements/container-images/sylva-toolbox:v0.3.14 --format "{{json .Provenance.SLSA}}"

docker buildx imagetools inspect registry.gitlab.com/sylva-projects/sylva-elements/container-images/sylva-toolbox:v0.3.14 --format "{{json .SBOM.SPDX}}"
```

## Artifacts Signature

### Sylva-Elements

The signature of a sylva-element (currently only disk images are signed) is verified against the public key fetched from an environment variable or from the GitLab project hosting the cosign keypair:

```shell
cosign verify --key env://COSIGN_PUBLIC_KEY registry.gitlab.com/sylva-projects/sylva-elements/diskimage-builder/diskimage-builder-hardened@sha256:b4affd8071d5c30f302b50a29b524d97cc25727dddc3d1ab9a46275ac5471a3b
```

When using the GitLab provider, set the environment variable `GITLAB_TOKEN` with read access on GitLab CI/CD variable:

```shell
$ export GITLAB_TOKEN=glpat-..... 

$ cosign verify --key gitlab://43786055 registry.gitlab.com/sylva-projects/sylva-elements/diskimage-builder/diskimage-builder-hardened@sha256:b4affd8071d5c30f302b50a29b524d97cc25727dddc3d1ab9a46275ac5471a3b

Verification for registry.gitlab.com/sylva-projects/sylva-elements/diskimage-builder/diskimage-builder-hardened@sha256:b4affd8071d5c30f302b50a29b524d97cc25727dddc3d1ab9a46275ac5471a3b --
The following checks were performed on each of these signatures:
  - The cosign claims were validated
  - Existence of the claims in the transparency log was verified offline
  - The signatures were verified against the specified public key

[{"critical":{"identity":{"docker-reference":"registry.gitlab.com/sylva-projects/sylva-elements/diskimage-builder/diskimage-builder-hardened"},"image":{"docker-manifest-digest":"sha256:b4affd8071d5c30f302b50a29b524d97cc25727dddc3d1ab9a46275ac5471a3b"},"type":"cosign container image signature"},"optional":{"Bundle":{"SignedEntryTimestamp":"MEQCIA3H+hWtfxrNLP/3kQh4wqrpaZmRZyi+Asr2c8mSCFqJAiBJR0OdX+hXvvMegZgOpVhflvOXgCu8gowh+tiHY/CD4g==","Payload":{"body":"eyJhcGlWZXJzaW9uIjoiMC4wLjEiLCJraW5kIjoiaGFzaGVkcmVrb3JkIiwic3BlYyI6eyJkYXRhIjp7Imhhc2giOnsiYWxnb3JpdGhtIjoic2hhMjU2IiwidmFsdWUiOiI0MDMxNmU4YzE2ZjBkNTE2YjQyYzU2NDZlMWM2MDhkN2JmMGU0YTIyODdlNmE3ZTJkY2QwMDZkY2JmNjgyYTJmIn19LCJzaWduYXR1cmUiOnsiY29udGVudCI6Ik1FVUNJUURpa3EwOEpVNzFaR0lZaGp2UHRnV2prbTdSLzNNS3RGU21qcDZwWGM4dkN3SWdXWmxRVjJSVUV1dFljQ0JaVEZJVDNWQkZIN3p1ZHBkK3V6dktSZGppQm5rPSIsInB1YmxpY0tleSI6eyJjb250ZW50IjoiTFMwdExTMUNSVWRKVGlCUVZVSk1TVU1nUzBWWkxTMHRMUzBLVFVacmQwVjNXVWhMYjFwSmVtb3dRMEZSV1VsTGIxcEplbW93UkVGUlkwUlJaMEZGVTJKMVUwVlZRa1pYTUhsdVpGRkJRbTl0U2t0Qk0yUlJkMkpMUkFwalUxZGlSM0J1UlVOeldqZEpkbVJWYWpsSFIwZHNiVkJ3V1d3NFNEQlhRMGhEVW5WWFIxTkhXRFU0V21scFUzVlZVVkpFVVc5SVFYaDNQVDBLTFMwdExTMUZUa1FnVUZWQ1RFbERJRXRGV1MwdExTMHRDZz09In19fX0=","integratedTime":1689609607,"logIndex":27773186,"logID":"c0d23d6ad406973f9559f3ba2d1ca01f84147d8ffc5b8445c224f98b9591801d"}}}}]
```

The payload is actually a [Hashed Rekord](https://github.com/sigstore/rekor/blob/main/types.md#hashed-rekord) which can be decoded as a [JWT](https://jwt.io/):

```json
{
  "apiVersion": "0.0.1",
  "kind": "hashedrekord",
  "spec": {
    "data": {
      "hash": {
        "algorithm": "sha256",
        "value": "40316e8c16f0d516b42c5646e1c608d7bf0e4a2287e6a7e2dcd006dcbf682a2f"
      }
    },
    "signature": {
      "content": "MEUCIQDikq08JU71ZGIYhjvPtgWjkm7R/3MKtFSmjp6pXc8vCwIgWZlQV2RUEutYcCBZTFIT3VBFH7zudpd+uzvKRdjiBnk=",
      "publicKey": {
        "content": "LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUZrd0V3WUhLb1pJemowQ0FRWUlLb1pJemowREFRY0RRZ0FFU2J1U0VVQkZXMHluZFFBQm9tSktBM2RRd2JLRApjU1diR3BuRUNzWjdJdmRVajlHR0dsbVBwWWw4SDBXQ0hDUnVXR1NHWDU4WmlpU3VVUVJEUW9IQXh3PT0KLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg=="
      }
    }
  }
}
```

### OCI Artifacts

Signatures are stored on the sylva-core OCI registry as artifact tags.

You can vertify manually the signature of the OCI artifact by using the cosign public key `cosign.pub` available in the directory `sylva-core/tools/oci`:

```shell
$ COSIGN_REPOSITORY=registry.gitlab.com/sylva-projects/sylva-core/signatures cosign verify --key tools/oci/cosign.pub --insecure-ignore-tlog quay.io/keycloak/keycloak:21.1.2 | jq
WARNING: Skipping tlog verification is an insecure practice that lacks of transparency and auditability verification for the signature.

Verification for quay.io/keycloak/keycloak:21.1.2 --
The following checks were performed on each of these signatures:
  - The cosign claims were validated
  - The signatures were verified against the specified public key
[
  {
    "critical": {
      "identity": {
        "docker-reference": "quay.io/keycloak/keycloak"
      },
      "image": {
        "docker-manifest-digest": "sha256:3408c186dde4a95c2b99ef1290721bf1d253d64ba3a1de0a46c667b8288051f0"
      },
      "type": "cosign container image signature"
    },
    "optional": null
  }
]
```
