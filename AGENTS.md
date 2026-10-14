# Repository development instructions

Read [docs/PRODUCT_BASELINE.md](docs/PRODUCT_BASELINE.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and the affected module/API/event documentation before changing behavior. These files are the project baseline; a separate installed skill or past chat is not required.

- Inspect the relevant implementation and Git state. Preserve unrelated changes.
- For a feature or material change, state the use case, scope, contracts, data/event impact and acceptance before implementation. Unapproved product choices remain proposals.
- Route handlers adapt HTTP; services own domain use cases; repositories own SQL; rules are pure. Cross-domain writes go through workflows and public capabilities in a shared UoW.
- Do not import another module's private repository, commit in a repository, call a concrete external SDK in business logic, or add implicit startup DDL/seed/schedulers.
- HTTP models define fields. Regenerate OpenAPI and TypeScript with `python scripts/contracts.py`; do not hand-edit generated files.
- Session/action/resource authorization is enforced on the server. Client role/name values never grant permission.
- Keep business audit in the business transaction; external notifications run after commit. Do not claim reliable event replay or exactly-once delivery without implementing and proving it.
- Database schema changes need an explicit migration, adoption, verification and recovery plan. Existing `schema.sql` is for an empty synthetic database, never an upgrade script.
- Verify proportional to risk; the release gate is `python scripts/verify.py`. Update affected docs and report actual verification and remaining limits.
- Public demo uses synthetic data/Fake notifications. Real DingTalk calls require explicit configuration and dedicated test recipients.
- Do not publish credentials, runtime directories, personal uploads or real company data. Commit/push/deploy only within user authorization.
