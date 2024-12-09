GET https://{{vault_url}}/v1/secret/data/minio-logging-user-password
X-Vault-Token: {{token}}
HTTP 200
[Captures]
password_minio_logging: jsonpath "$.data.data.password"

GET https://{{minio_logging_url}}/minio/health/live
HTTP 200

GET https://{{minio_logging_console_url}}/minio/health/live
HTTP 200

POST https://{{minio_logging_console_url}}/api/v1/login
Content-Type: application/json
{
  "accessKey": "minio-logging-user",
  "secretKey": "{{password_minio_logging}}"
}
HTTP 204