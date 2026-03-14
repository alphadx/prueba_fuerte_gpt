# Migration Quality Gates

- [ ] Fresh install applies all migrations without errors.
- [ ] Rollback of latest migration succeeds.
- [ ] Re-apply after rollback succeeds (idempotent chain behavior).
- [ ] Foreign keys and unique constraints enforce expected invariants.
- [ ] Seed data does not violate constraints.
- [ ] Performance sanity checked for core transactional queries.
