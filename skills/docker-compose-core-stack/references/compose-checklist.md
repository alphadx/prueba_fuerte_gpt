# Step 3 Closure Checklist

- [ ] `docker compose --profile core up` starts all core services healthy.
- [ ] API depends on healthy DB and Redis.
- [ ] Worker depends on healthy DB and Redis.
- [ ] `.env.example` covers all required variables.
- [ ] Optional services run with `--profile full` without breaking core.
- [ ] Cold start completes within target threshold.
