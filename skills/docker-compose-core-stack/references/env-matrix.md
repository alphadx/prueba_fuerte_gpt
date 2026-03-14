# Environment Matrix

| Variable | Service(s) | Required | Default | Notes |
|---|---|---|---|---|
| POSTGRES_DB | postgres, api, worker | yes | erp | DB name |
| POSTGRES_USER | postgres, api, worker | yes | erp | DB user |
| POSTGRES_PASSWORD | postgres, api, worker | yes | erp | DB password |
| REDIS_URL | api, worker | yes | redis://redis:6379/0 | Queue/cache |
| API_PORT | api | yes | 8000 | API listen port |
| WEB_PORT | web | yes | 3000 | Web listen port |
