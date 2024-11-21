GET https://thanos.{{domain}}/-/healthy
[BasicAuth]
{{user_thanos}}: {{password_thanos}}
HTTP 200
[Asserts]
body matches "OK"


GET https://thanos-query.{{domain}}/-/healthy
[BasicAuth]
{{user_thanos}}: {{password_thanos}}
HTTP 200
[Asserts]
body matches "OK"


GET https://thanos-receive.{{domain}}/-/healthy
[BasicAuth]
{{user_thanos}}: {{password_thanos}}
HTTP 200
[Asserts]
body matches "OK"


GET https://thanos-storegateway.{{domain}}/-/healthy
[BasicAuth]
{{user_thanos}}: {{password_thanos}}
HTTP 200
[Asserts]
body matches "OK"

