# Step 8 Webhook Idempotency Checklist

- [ ] `PaymentGateway` interface defined for all drivers.
- [ ] Cash and stub gateways implemented with canonical states.
- [ ] Unified webhook endpoint validates signatures/metadata.
- [ ] Idempotency key enforcement prevents duplicate state mutation.
- [ ] Feature flags control payment methods by branch/channel.
- [ ] Reconciliation report compares sales vs payment outcomes.
