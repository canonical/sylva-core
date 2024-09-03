GET https://{{vault_url}}/v1/secret/data/{{cluster_name}}/gitea-admin-user
X-Vault-Token: {{token}}
HTTP 200
[Captures]
password_gitea: jsonpath "$.data.data.password"

GET https://{{gitea_url}}/api/v1/user
Content-Type: application/json
[BasicAuth]
gitea-admin: {{password_gitea}} 
HTTP 200
[Asserts]
jsonpath "$.active" == true

