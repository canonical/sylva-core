# Sylva tests on vSphere infrastructure

The Sylva stack is automatically tested **daily** at TIM labs on vSphere infrastructure.

Tests logs of failed jobs are published as attachments of the project wiki.

The results are summarized by the following table:

| Date                      | Management Cluster CAPI Providers | Sylva-Core main commit ID        | Management cluster result                    | Workload cluster result              | Test logs (only for failed tests) |
|---------------------------|-----------------------------------|----------------------------------|----------------------------------------------|--------------------------------------|-----------------------------------|
|2024-06-25 02:38|rke2-capv|e7e891b6536e7e783ac39cc3f5ba769f87b48f70|:white_check_mark:|:white_check_mark:||
|2024-06-25 02:27|kubeadm-capv|e7e891b6536e7e783ac39cc3f5ba769f87b48f70|:white_check_mark:|:white_check_mark:||
|2024-06-22 02:28|kubeadm-capv|58d0e7a61a1abfb64af3f6d83e515f3400ae99fe|:white_check_mark:|:white_check_mark:||
|2024-06-22 02:33|rke2-capv|58d0e7a61a1abfb64af3f6d83e515f3400ae99fe|:white_check_mark:|:x:||
|2024-06-22 02:33|rke2-capv|58d0e7a61a1abfb64af3f6d83e515f3400ae99fe|:white_check_mark:|:x:||
|2024-06-22 02:28|kubeadm-capv|58d0e7a61a1abfb64af3f6d83e515f3400ae99fe|:white_check_mark:|:white_check_mark:||
|2024-06-21 02:35|rke2-capv|420b796b0424820b2496c0d149adbaa7e8c4189c|:white_check_mark:|:x:||
|2024-06-21 02:27|kubeadm-capv|420b796b0424820b2496c0d149adbaa7e8c4189c|:white_check_mark:|:white_check_mark:||
|2024-06-20 02:41|rke2-capv|d5722e3436022bd8823709a6cf782e2e4de7435d|:white_check_mark:|:white_check_mark:|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/d8affff7ef99498591ea81c60a94a8a1/capv-logs.gz)|
|2024-06-20 02:56|kubeadm-capv|d5722e3436022bd8823709a6cf782e2e4de7435d|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/d8affff7ef99498591ea81c60a94a8a1/capv-logs.gz)|
|2024-06-19 03:03|rke2-capv|ad7c1df2ef5441bc10d6db530b6f28ec3b4e4116|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/1bda58833eb7131f4d588ec3c5562380/capv-logs.gz)|
|2024-06-19 02:26|kubeadm-capv|ad7c1df2ef5441bc10d6db530b6f28ec3b4e4116|:white_check_mark:|:white_check_mark:|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/1bda58833eb7131f4d588ec3c5562380/capv-logs.gz)|
|2024-06-18 02:42|rke2-capv|56cc0b94ead5d747b30c2088c74aae6ff015b1d4|:white_check_mark:|:white_check_mark:||
|2024-06-18 02:27|kubeadm-capv|56cc0b94ead5d747b30c2088c74aae6ff015b1d4|:white_check_mark:|:white_check_mark:||
|2024-06-16 03:06|rke2-capv|bca14d15b4ac02f8de693f8d14aaf8b8f50f297f|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/0b9bf5def961b58859c0bf22b57e3fbb/capv-logs.gz)|
|2024-06-16 03:06|rke2-capv|bca14d15b4ac02f8de693f8d14aaf8b8f50f297f|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/9b29baf2f581c908f0fe1170497f05b7/capv-logs.gz)|
|2024-06-16 02:29|kubeadm-capv|bca14d15b4ac02f8de693f8d14aaf8b8f50f297f|:white_check_mark:|:white_check_mark:|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/9b29baf2f581c908f0fe1170497f05b7/capv-logs.gz)|
|2024-06-15 03:05|rke2-capv|85de1ed2ba06abc534464c09e30af0d5851f8a3a|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/7e2d15a0c4f8f689646c259d98be2979/capv-logs.gz)|
|2024-06-15 02:29|kubeadm-capv|85de1ed2ba06abc534464c09e30af0d5851f8a3a|:white_check_mark:|:white_check_mark:|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/7e2d15a0c4f8f689646c259d98be2979/capv-logs.gz)|
|2024-06-14 03:07|rke2-capv|1afdeb96f2190c5754032e3fe53d05cab6fe3aeb|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/58597881833d192b56c89056f22d6c21/capv-logs.gz)|
|2024-06-14 02:46|kubeadm-capv|1afdeb96f2190c5754032e3fe53d05cab6fe3aeb|:white_check_mark:|:white_check_mark:|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/58597881833d192b56c89056f22d6c21/capv-logs.gz)|

Old layout table:

| Date                      | Management Cluster CAPI Providers | Sylva-Core main commit ID        | Result                                       | Test logs (only for failed tests) |
|---------------------------|-----------------------------------|----------------------------------|----------------------------------------------|-----------------------------------|
|2024-01-16 01:34|rke2-capv|5256dbf34a7ce7cb6618ecb8d0179a7eae5fbd46|:white_check_mark: success||
|2024-01-16 01:21|kubeadm-capv|5256dbf34a7ce7cb6618ecb8d0179a7eae5fbd46|:white_check_mark: success||
|2024-01-14 01:33|rke2-capv|2695f09635cce6e4c1f5991efe718e497702f32b|:white_check_mark: success||
|2024-01-14 01:24|kubeadm-capv|2695f09635cce6e4c1f5991efe718e497702f32b|:white_check_mark: success||
|2024-01-14 01:33|rke2-capv|2695f09635cce6e4c1f5991efe718e497702f32b|:white_check_mark: success||
|2024-01-14 01:24|kubeadm-capv|2695f09635cce6e4c1f5991efe718e497702f32b|:white_check_mark: success||
|2024-01-13 01:35|rke2-capv|e3b0dd7ad10c7af250a016da36564264287586bf|:white_check_mark: success||
|2024-01-13 01:19|kubeadm-capv|e3b0dd7ad10c7af250a016da36564264287586bf|:white_check_mark: success||
|2024-01-12 01:32|rke2-capv|18c76e1dc3b307979d78c54f81b07fec0d80d511|:white_check_mark: success||
|2024-01-12 01:25|kubeadm-capv|18c76e1dc3b307979d78c54f81b07fec0d80d511|:white_check_mark: success||
|2024-01-11 01:57|rke2-capv|8826cb80b3b12514a05b5686da9e52505c577704|:x: failed|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/f8332c73b645753fb674c6ec8d7eeabf/capv-logs.gz)|
|2024-01-11 01:24|kubeadm-capv|8826cb80b3b12514a05b5686da9e52505c577704|:white_check_mark: success||
|2024-01-10 01:34|rke2-capv|3f2a72a466200d1a5371a70c00cf5f57d35b73fe|:white_check_mark: success||
|2024-01-10 01:57|kubeadm-capv|3f2a72a466200d1a5371a70c00cf5f57d35b73fe|:x: failed|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/8138bd7fc116d62d656f66aab4c677ac/capv-logs.gz)|
|2023-12-30 01:40|rke2-capv|e320370a481772acbe361046585b779bc4c772fe|:x: failed|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/17d4ffbdc8036903ad000196987782ea/capv-logs.gz)|
|2023-12-30 01:30|kubeadm-capv|e320370a481772acbe361046585b779bc4c772fe|:x: failed|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/17d4ffbdc8036903ad000196987782ea/capv-logs.gz)|
|2023-12-23 01:30|rke2-capv|cf4b9dee6b0addb94b54b70530d0a25365ba937e|:x: failed|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/758ab1ecc725e797a06261c62cc77788/capv-logs.gz)|
|2023-12-23 01:26|kubeadm-capv|cf4b9dee6b0addb94b54b70530d0a25365ba937e|:white_check_mark: success||
|2023-12-23 01:30|rke2-capv|cf4b9dee6b0addb94b54b70530d0a25365ba937e|:x: failed|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/d3bb7c8c3be36d81a9f9930f81189f56/capv-logs.gz)|
|2023-12-23 01:26|kubeadm-capv|cf4b9dee6b0addb94b54b70530d0a25365ba937e|:white_check_mark: success||
|2023-12-23 01:30|rke2-capv|cf4b9dee6b0addb94b54b70530d0a25365ba937e|:x: failed|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/6e58c059b348d378ad25155a7f3ed1c8/capv-logs.gz)|

