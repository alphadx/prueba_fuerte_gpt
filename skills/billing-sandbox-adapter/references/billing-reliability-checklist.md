# Step 7 Billing Reliability Checklist

- [ ] `BillingProvider` interface defined and documented.
- [ ] Sandbox adapter supports folio/XML/PDF/trackID/status.
- [ ] Emission decoupled from synchronous POS path.
- [ ] Retry policy with bounded attempts and visibility.
- [ ] Idempotency protection for duplicate emissions.
- [ ] Status query endpoint verified with integration tests.
