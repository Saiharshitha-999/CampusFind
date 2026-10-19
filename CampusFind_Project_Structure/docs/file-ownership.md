# CampusFind file ownership and integration map

Each active feature file has one primary owner. Shared contracts have one integration owner; obtain review from a feature owner when changing a cross-feature contract. The table was reconciled against the current working-tree changes on 2026-10-19. It describes ownership, not authorship, and does not indicate that every changed file has been fully validated.

## Feature ownership

| Primary owner | Feature | Files |
|---|---|---|
| Team Lead | Authentication and status | `backend/app/features/auth/router.py`, `backend/app/features/auth/schemas.py`, `backend/app/features/auth/service.py`, `backend/app/features/status/router.py`, `backend/app/features/status/schemas.py`, `backend/app/features/status/service.py`, `frontend/src/features/auth/AuthPage.jsx`, `frontend/src/features/status/StatusControl.jsx` |
| Muskaan Choudhary | Lost/found reports | `backend/app/features/reports/router.py`, `backend/app/features/reports/schemas.py`, `backend/app/features/reports/service.py`, `frontend/src/features/reports/Reports.jsx` |
| Farhaan | Search and matching | `backend/app/features/search/router.py`, `backend/app/features/search/service.py`, `backend/app/features/matching/service.py`, `frontend/src/features/search/SearchPage.jsx`, `frontend/src/features/matching/Matches.jsx` |
| Vasavi Satya Sathvika | Claims and claim decisions | `backend/app/features/claims/router.py`, `backend/app/features/claims/schemas.py`, `backend/app/features/claims/service.py`, `frontend/src/features/claims/ClaimForm.jsx`, `frontend/src/features/claims/Dashboard.jsx` |
| N Chegue Veer | Moderation, admin audit UI, notifications | `backend/app/features/admin/router.py`, `backend/app/features/notifications/router.py`, `backend/app/features/notifications/service.py`, `frontend/src/features/admin/Admin.jsx`, `frontend/src/features/notifications/Notifications.jsx` |

## Shared integration files

| Primary integration owner | Shared contract | Files |
|---|---|---|
| Team Lead | Domain models, authentication/permissions, DB/session, audit service, app/router registration | `backend/app/models/__init__.py`, `backend/app/core/config.py`, `backend/app/core/security.py`, `backend/app/db/session.py`, `backend/app/features/audit/__init__.py`, `backend/app/features/audit/service.py`, `backend/app/api/router.py`, `backend/app/main.py`, `backend/app/create_admin.py`, `backend/app/seed_data.py` |
| Team Lead | Compose, local secrets template, migrations and schema | `compose.yaml`, `.env.example`, `backend/alembic.ini`, `backend/migrations/env.py`, `backend/migrations/script.py.mako`, `backend/migrations/versions/0001_initial.py`, `backend/migrations/versions/0002_uml_workflows.py`, `database/schema.sql` |
| Team Lead | Frontend shell/API contracts and shared visual system | `frontend/src/App.jsx`, `frontend/src/api/client.js`, `frontend/src/shared/Feedback.jsx`, `frontend/src/pages/HomePage.jsx`, `frontend/src/styles/app.css`, `frontend/src/styles/global.css`, `frontend/package-lock.json` |
| Team Lead | Verification and project documentation | `backend/tests/test_features.py`, `docs/API_CONVENTIONS.md`, `docs/implementation-tracker.md`, `docs/requirements-traceability.md`, `TRACEABILITY.md`, `docs/file-ownership.md`, nested `README.md`, outer `../README.md`, `.gitignore` |

## Integration rules

- The FastAPI endpoint contract and SQLAlchemy model changes are shared; the Team Lead integrates these files after review from the affected feature owner.
- Notification service calls cross report, matching, claim, and status features; N Chegue owns that shared notification contract.
- `backend/app/features/status/` is owned by the Team Lead as the cross-feature state machine. Other features should record changes through its service.
- The normalized report models and `ItemReport` compatibility table are currently dual-written. Do not remove the compatibility table until the frontend/API migration and legacy data retirement are separately reviewed.
- Previously tracked uppercase `docs/FILE_OWNERSHIP.md` and `docs/IMPLEMENTATION_TRACKER.md` were replaced with lowercase paths; do not restore their stale copies over the current documents.
- The outer README is existing top-level project documentation and remains a shared integration file; preserve unrelated edits when updating it.
