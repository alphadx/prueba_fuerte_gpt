# Fixture Catalog Template

| Scenario | Fixture ID | Preconditions | Expected Result | Smoke Check |
|---|---|---|---|---|
| cash sale | FX-SALE-CASH | stock + open session | sale paid + stock decremented | pass/fail |
| web pickup | FX-WEB-PICKUP | active catalog | order `recibido` | pass/fail |
| billing sandbox | FX-BILLING-SBX | paid sale | tax doc created | pass/fail |
