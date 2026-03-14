# Payment State Model

- `initiated`
- `pending_confirmation`
- `approved`
- `rejected`
- `reconciled`

## Transition rule
Only forward transitions are allowed; ignore stale callbacks.
