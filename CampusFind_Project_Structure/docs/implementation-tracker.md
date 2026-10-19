# Implementation and verification tracker

This tracker follows the supplied CampusFind UML/sequence specification. The complete mapping and known gaps are in [`../TRACEABILITY.md`](../TRACEABILITY.md). A feature marked “implemented” is present in source; it is not a claim that its integration tests passed in the current environment.

| Feature | Implementation | Current status / verification |
|---|---|---|
| Registration, verification, login, reset | Auth API, hashed passwords, signed tokens, active/verification checks, auth pages | Source implemented; backend pytest could not run with current Python environment. Real SMTP delivery not retested in this pass. |
| Lost/found reports and moderation | Exact Pending Approval/Active/Rejected status, normalized tables with compatibility rows, admin queue | Source implemented; PostgreSQL migration not run in this environment. |
| Public search and filters | Search API/page; hides Pending Approval and Rejected | Source implemented; frontend build passed. |
| Matching | Persisted Match rows, configurable thresholds, owner/admin match view, High confidence notices to both owners | Source implemented; integration tests added but not executed. |
| Claims and evidence | Match Found-only claim, required validated proof, claimant/admin proof access, admin-only decision | Source implemented; privacy/workflow tests added but not executed. |
| Status tracking and recovery closure | Exact report transitions, owner handoff confirmation, admin close, StatusHistory | Source implemented; integration tests added but not executed. |
| Notifications and audit | Recipient-scoped read route, delivery state, audit events/admin page | Source implemented; SMTP/provider integration not verified here. |
| Seed data and documentation | Idempotent local seed command, README, TRACEABILITY.md, ownership map | Source/docs updated; no production deployment performed. |

## Checks performed in this review

- `npm.cmd run build` from `frontend/` — passed (Vite production bundle).
- Python AST parse of 47 app, migration, and test source files — passed.
- SQLAlchemy mapper configuration and SQLite in-memory schema creation — passed. This is a model/schema smoke check only; it does not verify application requests or migrations.
- `python -m pytest -q` — not runnable. The project `.venv` launcher points to an absent Python 3.11 installation. Bundled Python 3.12 cannot import the venv's compiled Pydantic Core extension.
- `docker compose ps` — not runnable in this environment because the Docker CLI is not available. PostgreSQL health, `alembic upgrade head`, and data migration behavior remain unverified here.
- SMTP — not sent to a real configured provider during this review. Configure SMTP and verify the received message before relying on it.

No GitHub push or hosted deployment was performed. Do not use `docker compose down -v` or migration downgrade as a database reset.
