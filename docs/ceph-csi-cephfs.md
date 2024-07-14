# Ceph-csi-cephfs in Sylva

Within Sylva, [`Ceph-csi-cephfs`](https://github.com/ceph/ceph-csi/tree/devel/charts/ceph-csi-cephfs#ceph-csi-cephfs) can be used to provide persistent storage for the workload clusters.

An existing, centrally located, Ceph cluster can be integrated to allow workload clusters store their data in it.

Persistent volumes with different access modes, like ReadWriteOnce and ReadWriteMany, can be created as per requirements.

Ceph CSI ceph fs supports multitenancy, allowing you to segregate data for each workload cluster on separate filesystems. This segregation ensures that data access is restricted for unauthorized users, enhancing security and data isolation. It helps maintain the integrity and privacy of data within the system.

## How a management/workload cluster can consume Ceph

### Ceph config

* Create new Ceph file system

```shell
ceph fs volume create <filesystem_name>
```

* List down the file system

```shell
ceph fs ls
ceph osd pool ls detail
```

* Verify MDS status

```shell
ceph -s
ceph mds status
```

* Create new user with below capabilities which is required to support multi-tenancy , following [CephFS authentication capabilities](https://docs.ceph.com/en/reef/cephfs/client-auth/)

```shell
ceph auth get-or-create client.CEPH_USER}\
   mds 'allow rw fsname=${CEPH_FS}' \
    mgr "allow command 'fs subvolume ls' with vol_name=${CEPH_FS}, allow command 'fs subvolume create' with vol_name=${CEPH_FS}, allow command 'fs subvolume rm' with vol_name=${CEPH_FS}, allow command 'fs subvolume authorize' with vol_name=${CEPH_FS}, allow command 'fs subvolume deauthorize' with vol_name=${CEPH_FS}, allow command 'fs subvolume authorized_list' with vol_name=${CEPH_FS}, allow command 'fs subvolume evict' with vol_name=${CEPH_FS}, allow command 'fs subvolume getpath' with vol_name=${CEPH_FS}, allow command 'fs subvolume info' with vol_name=${CEPH_FS}, allow command 'fs subvolume metadata set' with vol_name=${CEPH_FS}, allow command 'fs subvolume metadata get' with vol_name=${CEPH_FS}, allow command 'fs subvolume metadata ls' with vol_name=${CEPH_FS}, allow command 'fs subvolume metadata rm' with vol_name=${CEPH_FS}, allow command 'fs subvolume resize' with vol_name=${CEPH_FS}, allow command 'fs subvolumegroup ls' with vol_name=${CEPH_FS}, allow command 'fs subvolumegroup create' with vol_name=${CEPH_FS}, allow command 'fs subvolumegroup rm' with vol_name=${CEPH_FS}, allow command 'fs subvolumegroup getpath' with vol_name=${CEPH_FS}, allow command 'fs subvolumegroup pin' with vol_name=${CEPH_FS}, allow command 'fs subvolume snapshot ls' with vol_name=${CEPH_FS}, allow command 'fs subvolume snapshot create' with vol_name=${CEPH_FS}, allow command 'fs subvolume snapshot rm' with vol_name=${CEPH_FS}, allow command 'fs subvolume snapshot protect' with vol_name=${CEPH_FS}, allow command 'fs subvolume snapshot unprotect' with vol_name=${CEPH_FS}, allow command 'fs subvolume snapshot clone' with vol_name=${CEPH_FS}, allow command 'fs subvolume snapshot info' with vol_name=${CEPH_FS}, allow command 'fs subvolume snapshot metadata set' with vol_name=${CEPH_FS}, allow command 'fs subvolume snapshot metadata get' with vol_name=${CEPH_FS}, allow command 'fs subvolume snapshot metadata ls' with vol_name=${CEPH_FS}, allow command 'fs subvolume snapshot metadata rm' with vol_name=${CEPH_FS}, allow command 'fs subvolumegroup snapshot create' with vol_name=${CEPH_FS}, allow command 'fs subvolumegroup snapshot ls' with vol_name=${CEPH_FS}, allow command 'fs subvolumegroup snapshot rm' with vol_name=${CEPH_FS}" \
   mon 'allow r fsname=${CEPH_FS}' \
   osd 'allow rw pool=cephfs.${CEPH_FS}.data, allow rw pool=cephfs.${CEPH_FS}.meta' \
   -o /etc/ceph/ceph.client.{CEPH_USER}.keyring
```

* Verify the capabilities.

```shell
ceph auth get client.test
[client.foo]
      key = AQDFakeTokenFakeTokenFakeTokenGSoSbLkA==
      caps mds = "allow rw fsname=test"
      caps mgr = "allow command 'fs subvolume ls' with vol_name=test, allow command 'fs subvolume create' with vol_name=test, allow command 'fs subvolume rm' with vol_name=test, allow command 'fs subvolume authorize' with vol_name=test, allow command 'fs subvolume deauthorize' with vol_name=test, allow command 'fs subvolume authorized_list' with vol_name=test, allow command 'fs subvolume evict' with vol_name=test, allow command 'fs subvolume getpath' with vol_name=test, allow command 'fs subvolume info' with vol_name=test, allow command 'fs subvolume metadata set' with vol_name=test, allow command 'fs subvolume metadata get' with vol_name=test, allow command 'fs subvolume metadata ls' with vol_name=test, allow command 'fs subvolume metadata rm' with vol_name=test, allow command 'fs subvolume resize' with vol_name=test, allow command 'fs subvolumegroup ls' with vol_name=test, allow command 'fs subvolumegroup create' with vol_name=test, allow command 'fs subvolumegroup rm' with vol_name=test, allow command 'fs subvolumegroup getpath' with vol_name=test, allow command 'fs subvolumegroup pin' with vol_name=test, allow command 'fs subvolume snapshot ls' with vol_name=test, allow command 'fs subvolume snapshot create' with vol_name=test, allow command 'fs subvolume snapshot rm' with vol_name=test, allow command 'fs subvolume snapshot protect' with vol_name=test, allow command 'fs subvolume snapshot unprotect' with vol_name=test, allow command 'fs subvolume snapshot clone' with vol_name=test, allow command 'fs subvolume snapshot info' with vol_name=test, allow command 'fs subvolume snapshot metadata set' with vol_name=test, allow command 'fs subvolume snapshot metadata get' with vol_name=test, allow command 'fs subvolume snapshot metadata ls' with vol_name=test, allow command 'fs subvolume snapshot metadata rm' with vol_name=test, allow command 'fs subvolumegroup snapshot create' with vol_name=test, allow command 'fs subvolumegroup snapshot ls' with vol_name=test, allow command 'fs subvolumegroup snapshot rm' with vol_name=test"
      caps mon = "allow r fsname=test"
      caps osd = "allow rw pool=cephfs.test.data, allow rw pool=cephfs.test.meta"
```

## Consuming Cephfs for a cluster

* Make sure that Ceph monitor IPs are reachable from each Sylva cluster trying to provide Persistent Storage via `ceph-csi-cephfs` unit.
* New Ceph user and file system should be created for each cluster.
* Define your environment-values for the ceph secrets and ceph config as follows:

```shell
# for a management cluster, e.g. in environment-values/my-rke2-capo-
env/values.yaml
# or for a workload cluster, e.g. in environment-values/workload-clusters/my-rke2-capm3-env/values.yaml

ceph:
  cephfs_csi:
    clusterID: "72451b38-2d3c-11ee-80a2-652991486dfa"
    fs_name: "test"
    monitors_ips:
      - "192.168.128.45"
      - "192.168.128.46"
      - "192.168.128.47"

units:
  ceph-csi-cephfs:
    enabled: yes

# for a management cluster, e.g. in environment-values/my-rke2-capo-
env/secrets.yaml
# or for a workload cluster, e.g. in environment-values/workload-clusters/my-rke2-capm3-env/secrets.yaml

ceph:
  cephfs_csi:
    adminID: "user-1"
    adminKey: "AQDFakeTokenFakeTokenFakeTokenGSoSbLkA=="
```
