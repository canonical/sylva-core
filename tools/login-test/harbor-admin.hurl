GET https://{{vault_url}}/v1/secret/data/{{cluster_name}}/harbor-passwd
X-Vault-Token: {{token}}
HTTP 200
[Captures]
password_harbor: jsonpath "$.data.data.password"

GET https://{{harbor_url}}/service/token?service=harbor-registry
[BasicAuth]
admin: {{password_harbor}}
HTTP 200
