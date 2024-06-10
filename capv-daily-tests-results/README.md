# Sylva tests on vSphere infrastructure

The Sylva stack is automatically tested **daily** at TIM labs on vSphere infrastructure.

Tests logs of failed jobs are published as attachments of the project wiki.

The results are summarized by the following table:

| Date                      | Management Cluster CAPI Providers | Sylva-Core main commit ID        | Management cluster result                    | Workload cluster result              | Test logs (only for failed tests) |
|---------------------------|-----------------------------------|----------------------------------|----------------------------------------------|--------------------------------------|-----------------------------------|
|2024-06-08 02:56|kubeadm-capv|2268b6215d511786ef1df7d46f2dfd4c48e84ea5|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/9654cf3da7aed4686173d8bf138167a7/capv-logs.gz)|
|2024-06-08 03:01|rke2-capv|2268b6215d511786ef1df7d46f2dfd4c48e84ea5|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/6f4325ec75f5984bfbbdd92ae033e1d0/capv-logs.gz)|
|2024-06-08 03:01|rke2-capv|2268b6215d511786ef1df7d46f2dfd4c48e84ea5|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/9c91978ca11af8ad03b0514e9227586a/capv-logs.gz)|
|2024-06-08 02:56|kubeadm-capv|2268b6215d511786ef1df7d46f2dfd4c48e84ea5|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/9c91978ca11af8ad03b0514e9227586a/capv-logs.gz)|
|2024-06-07 03:07|rke2-capv|d7cbaed5632f920d7367ace2578faf3cd04df679|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/e3a5ca621c4629ffc4b26ce14ab6c13f/capv-logs.gz)|
|2024-06-07 02:54|kubeadm-capv|d7cbaed5632f920d7367ace2578faf3cd04df679|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/e3a5ca621c4629ffc4b26ce14ab6c13f/capv-logs.gz)|
|2024-06-06 03:06|rke2-capv|9ebc025dd2f5a7277cc7d46a9465b8a3165523a9|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/6ab9e9d375a2fb43adc9f38a3a6e7f52/capv-logs.gz)|
|2024-06-06 02:55|kubeadm-capv|9ebc025dd2f5a7277cc7d46a9465b8a3165523a9|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/6ab9e9d375a2fb43adc9f38a3a6e7f52/capv-logs.gz)|
|2024-06-05 02:41|rke2-capv|65d11a8b1e7adf47418c76275034f70a441a9bd7|:white_check_mark:|:x:|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/d13363c20e2dfc575d20c1c8eaed0ad2/capv-logs.gz)|
|2024-06-05 02:56|kubeadm-capv|65d11a8b1e7adf47418c76275034f70a441a9bd7|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/d13363c20e2dfc575d20c1c8eaed0ad2/capv-logs.gz)|
|2024-06-04 02:42|rke2-capv|e711195fcd1919a16aa421c5df7efb38d4c8a0c4|:white_check_mark:|:x:|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/16e87d81b00cb5d375084ed5d5fb444f/capv-logs.gz)|
|2024-06-04 02:56|kubeadm-capv|e711195fcd1919a16aa421c5df7efb38d4c8a0c4|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/16e87d81b00cb5d375084ed5d5fb444f/capv-logs.gz)|
|2024-05-31 02:56|rke2-capv|87bb6fd019dfaf4584fd30cbeee664d135adbe9f|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/fd09d78ffa651673729d911a5dfc6a9f/capv-logs.gz)|
|2024-05-31 02:00|kubeadm-capv|87bb6fd019dfaf4584fd30cbeee664d135adbe9f|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/fd09d78ffa651673729d911a5dfc6a9f/capv-logs.gz)|
|2024-05-30 02:56|rke2-capv|a1d803bc51302429c71412eb1498e7f238856703|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/fe36c2c9130895c182753597c42ea293/capv-logs.gz)|
|2024-05-30 02:00|kubeadm-capv|a1d803bc51302429c71412eb1498e7f238856703|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/fe36c2c9130895c182753597c42ea293/capv-logs.gz)|
|2024-05-29 02:56|rke2-capv|bc311d854f3862544cbe1d52aeb47a413b877233|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/90baa6e8943ead5258bd1bd20951327b/capv-logs.gz)|
|2024-05-29 02:00|kubeadm-capv|bc311d854f3862544cbe1d52aeb47a413b877233|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/90baa6e8943ead5258bd1bd20951327b/capv-logs.gz)|
|2024-05-28 02:56|rke2-capv|4b7f0a5a066603a9c53c7dc7af8bc2316b2f3896|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/c64be60566a72d38272d0aab1148a7ea/capv-logs.gz)|
|2024-05-28 02:00|kubeadm-capv|4b7f0a5a066603a9c53c7dc7af8bc2316b2f3896|:x:|N/A|[link](https://gitlab.com/sylva-projects/sylva-core/-/wikis/uploads/c64be60566a72d38272d0aab1148a7ea/capv-logs.gz)|

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

