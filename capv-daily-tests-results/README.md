# Sylva tests on vSphere infrastructure

The Sylva stack is automatically tested **daily** at TIM labs on vSphere infrastructure.

Tests logs of failed jobs are published as attachments of the project wiki.

The results are summarized by the following table:

| Date                      | Management Cluster CAPI Providers | Sylva-Core main commit ID        | Management cluster result                    | Workload cluster result              | Test logs (only for failed tests) |
|---------------------------|-----------------------------------|----------------------------------|----------------------------------------------|--------------------------------------|-----------------------------------|
|2024-07-10 02:37|rke2-capv|0fa551a86e96351b68e8977d15203da50d22cb39|:white_check_mark:|:white_check_mark:||
|2024-07-10 02:32|kubeadm-capv|0fa551a86e96351b68e8977d15203da50d22cb39|:white_check_mark:|:white_check_mark:||
|2024-07-09 02:32|rke2-capv|85936477a619c1d4545447423f10cffd57416abb|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/3c0a44d8eb0357084ded6ddc1c9f0796/capv-logs.gz)|
|2024-07-09 02:31|kubeadm-capv|85936477a619c1d4545447423f10cffd57416abb|:white_check_mark:|:white_check_mark:|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/3c0a44d8eb0357084ded6ddc1c9f0796/capv-logs.gz)|
|2024-07-07 02:31|rke2-capv|b7306721da25b41dc4bfeb952c40815a58a3616a|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/20e9611b7feb490548a73652bbe7fd51/capv-logs.gz)|
|2024-07-07 02:31|rke2-capv|b7306721da25b41dc4bfeb952c40815a58a3616a|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/40f850584e611de9461b89e8fcf46e6b/capv-logs.gz)|
|2024-07-07 02:57|kubeadm-capv|b7306721da25b41dc4bfeb952c40815a58a3616a|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/40f850584e611de9461b89e8fcf46e6b/capv-logs.gz)|
|2024-07-06 02:31|rke2-capv|77c7d3926083c5b55d5f3ea4bb311edba94a724b|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/c7029e5a5cd80e0beb220adef9e6db53/capv-logs.gz)|
|2024-07-06 02:29|kubeadm-capv|77c7d3926083c5b55d5f3ea4bb311edba94a724b|:white_check_mark:|:white_check_mark:|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/c7029e5a5cd80e0beb220adef9e6db53/capv-logs.gz)|
|2024-07-05 02:41|rke2-capv|14cca8ca3fd6749f00e799481b7993e314cb182a|:white_check_mark:|:white_check_mark:||
|2024-07-05 02:30|kubeadm-capv|14cca8ca3fd6749f00e799481b7993e314cb182a|:white_check_mark:|:white_check_mark:||
|2024-07-04 03:07|rke2-capv|a8939b1e91a53a5ac0e4afc606f61bfb6d8209e2|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/4e581eb4cf66817fa7a3123147867870/capv-logs.gz)|
|2024-07-04 02:33|kubeadm-capv|a8939b1e91a53a5ac0e4afc606f61bfb6d8209e2|:white_check_mark:|:white_check_mark:|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/4e581eb4cf66817fa7a3123147867870/capv-logs.gz)|
|2024-07-03 02:39|rke2-capv|07e35e0183213658d95a62b4f7a8389942dfc467|:white_check_mark:|:white_check_mark:||
|2024-07-03 02:29|kubeadm-capv|07e35e0183213658d95a62b4f7a8389942dfc467|:white_check_mark:|:white_check_mark:||
|2024-06-29 02:31|kubeadm-capv|584a0245492dc607083f9f76ca9053ef5c146a47|:white_check_mark:|:white_check_mark:||
|2024-06-29 02:39|rke2-capv|584a0245492dc607083f9f76ca9053ef5c146a47|:white_check_mark:|:white_check_mark:||
|2024-06-29 02:39|rke2-capv|584a0245492dc607083f9f76ca9053ef5c146a47|:white_check_mark:|:white_check_mark:||
|2024-06-29 02:31|kubeadm-capv|584a0245492dc607083f9f76ca9053ef5c146a47|:white_check_mark:|:white_check_mark:||
|2024-06-28 02:36|rke2-capv|1bb49c582a3b85070fa66f3a44ed21630f66a385|:white_check_mark:|:white_check_mark:||
|2024-06-28 02:29|kubeadm-capv|1bb49c582a3b85070fa66f3a44ed21630f66a385|:white_check_mark:|:white_check_mark:||

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

