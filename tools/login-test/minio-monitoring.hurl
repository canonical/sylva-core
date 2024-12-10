GET https://{{vault_url}}/v1/secret/data/minio-monitoring-user-password
X-Vault-Token: {{token}}
HTTP 200
[Captures]
password_minio_monitoring: jsonpath "$.data.data.password"

GET https://{{minio_monitoring_url}}/minio/health/live
HTTP 200

GET https://{{minio_monitoring_console_url}}/minio/health/live
HTTP 200

POST https://{{minio_monitoring_console_url}}/api/v1/login
Content-Type: application/json
{
  "accessKey": "minio-monitoring-user",
  "secretKey": "{{password_minio_monitoring}}"
}
HTTP 204