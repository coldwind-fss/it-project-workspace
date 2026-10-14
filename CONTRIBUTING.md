# Contributing

The application baseline is [PRODUCT_BASELINE](docs/PRODUCT_BASELINE.md). Start with [DEVELOPMENT](docs/DEVELOPMENT.md) and the [module map](docs/MODULES.md).

## Adding a feature

1. State the user, use case, scope and observable acceptance conditions. Clarify business changes before coding.
2. Identify the owning module and affected callers. Define HTTP fields, permissions, errors, transaction, idempotency and external effects using [API_CONVENTIONS](docs/API_CONVENTIONS.md).
3. Register any new event's producer, consumers, payload, timing and failure behavior in [EVENTS](docs/EVENTS.md). Cross-domain required facts remain in the workflow transaction.
4. Implement in the owner module; expose public capabilities, and use a workflow for cross-domain writes. Frontend pages call features, typed clients and the transport.
5. Add tests for actual rules and failure risks. Update generated contracts with `python scripts/contracts.py`. If accepted template/style behavior changes, explain the scope and review the corresponding `contracts/ui-baseline.json` update.
6. Run `python scripts/verify.py`, update only affected documentation, and report implementation/verification/release separately.

## Fixing a bug

Record a reproduction and intended result. A local fix does not need a new full roadmap. Cover the concrete regression and relevant permission/state/transaction risks. If it changes a business rule, record that decision first.

## Changing the database or a public contract

Do not silently run `schema.sql` against an existing database or rename fields used by clients/history. Define compatibility, migration/adoption, backup, verification and recovery. All callers and generated schemas must agree before release.

## Review expectations

- One module owns each write; no private cross-module imports or dependency cycles.
- Request role/name and client-computed status/eligibility are not authoritative.
- GET does not create business records, send notifications or fill missing history.
- Notification failure does not undo already committed business facts.
- README/demo/screenshots do not claim actual DingTalk delivery from Fake or protocol simulations.
- Keep the dependency locks, configuration examples and run commands usable from a clean clone.

Public version provenance and known limitations are in [MAINTENANCE](docs/MAINTENANCE.md). No open-source license has been selected; contribution and reuse terms must be agreed with the owner.
