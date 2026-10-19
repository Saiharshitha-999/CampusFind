# CampusFind diagram-to-code traceability

This table maps the supplied UML, use cases, DFD processes, state chart, and sequence to the current code. “Partial” means a compatibility or runtime verification gap remains; it is listed in the final section rather than implied complete.

## Class diagram

| Diagram element | Implementation | Status / notes |
|---|---|---|
| User (`user_id`, `name`, `email`, `password_hash`, `role`, `verification_status`, `active`) | `backend/app/models/__init__.py`; `backend/app/features/auth/{router,schemas,service}.py`; `backend/app/core/security.py` | Exact ORM fields; roles `Campus User`/`Administrator`; verified/active checks. |
| LostReport | `backend/app/models/__init__.py`; `backend/app/features/reports/router.py`; `backend/migrations/versions/0002_uml_workflows.py` | Created with a compatibility `ItemReport` row; legacy API still reads/writes the compatibility row. |
| FoundReport | Same as LostReport; contact email is sourced from the private User account | Finder contact is not returned to public search. |
| Match (`score`, confidence High/Medium/Low, status Match Found) | `backend/app/models/__init__.py`; `backend/app/features/matching/service.py`; `backend/app/features/admin/router.py`; `backend/app/features/search/router.py` | Persisted for Medium/High scores after moderation; high-confidence match notifies both owners. |
| Claim | `backend/app/models/__init__.py`; `backend/app/features/claims/{router,schemas,service}.py`; `frontend/src/features/claims/ClaimForm.jsx` | Required file proof validated and stored outside public uploads; only administrator decides. |
| Notification (`read_at`, delivery status Pending/Sent/Failed) | `backend/app/models/__init__.py`; `backend/app/features/notifications/{router,service}.py` | Recipient-scoped read endpoint; SMTP sending is optional and must be verified against a configured provider. |
| AuditEvent | `backend/app/models/__init__.py`; `backend/app/features/audit/service.py`; `backend/app/features/admin/router.py` | Admin audit route/page; legacy `AuditLog` is retained for decision detail during transition. |
| StatusHistory | `backend/app/models/__init__.py`; `backend/app/features/status/{router,service}.py`; `backend/app/features/claims/router.py`; report detail page | Report and claim status changes recorded; report owner/admin can view report timeline. |

## Use cases and pages

| Actor/use case | Route/page | Implementation |
|---|---|---|
| Campus User: register and verify | `/auth/register`, `/auth/verify-email`; `frontend/src/features/auth/AuthPage.jsx` | Email link generation/delivery via configured SMTP. |
| Campus User: log in, reset password | `/auth/login`, `/auth/password-reset/*`; Auth page | Password hashes and signed, purpose-bound tokens. |
| Campus User: report lost/found | `/reports/{lost,found}`; `frontend/src/features/reports/Reports.jsx` | Verified users only; found report requires custody location. |
| Campus User: search/filter | `/items`; `frontend/src/features/search/SearchPage.jsx` | Hides Pending Approval and Rejected; contact details excluded. |
| Campus User: view potential matches | `/items/{id}/matches`; `frontend/src/features/matching/Matches.jsx` | Owner-only and backed by persisted Match rows. |
| Campus User: submit claim with proof | `/items/{id}/claims`; `frontend/src/features/claims/ClaimForm.jsx` | Only a Match Found found-report may be claimed; proof file required. |
| Campus User: track status | `/items/{id}/history`; `frontend/src/features/reports/Reports.jsx`; dashboard | Owner sees current state and recorded timeline. |
| Campus User: view notifications | `/notifications`; `frontend/src/features/notifications/Notifications.jsx` | Authenticated recipient only. |
| Administrator: approve/reject reports | `/admin/reports/*`; `frontend/src/features/admin/Admin.jsx` | Rejection requires a reason; state, audit, matching, and notifications are recorded. |
| Administrator: review/decide claims | `/admin/claims/pending`, `/claims/{id}/decision`; Admin page | Proof download and decision require Administrator role. |
| Administrator: close recovery | `/items/{id}/close`; Admin page | Only Returned reports may be closed. |
| Administrator: view audit records | `/admin/audit`; Admin page | Administrator-only. |

## DFD process mapping

| DFD process | Backend module(s) | Frontend entry point |
|---|---|---|
| 1.0 Register and Authenticate | `features/auth/router.py`, `features/auth/service.py` | `features/auth/AuthPage.jsx` |
| 2.0 Report Lost/Found Item | `features/reports/router.py`, `features/reports/service.py` | `features/reports/Reports.jsx` |
| 3.0 Moderate Reports | `features/admin/router.py` | `features/admin/Admin.jsx` |
| 4.0 Search and Match Items | `features/search/`, `features/matching/service.py` | `features/search/SearchPage.jsx`, `features/matching/Matches.jsx` |
| 5.0 Submit Claim with Proof | `features/claims/router.py`, `features/claims/service.py` | `features/claims/ClaimForm.jsx` |
| 6.0 Verify Claim and Decide | `features/claims/router.py`, `features/admin/router.py` | `features/admin/Admin.jsx` |
| 7.0 Track Item Status | `features/status/router.py`, `features/status/service.py` | `features/status/StatusControl.jsx`, report detail, dashboard |
| 8.0 Send Notifications | `features/notifications/router.py`, `features/notifications/service.py` | `features/notifications/Notifications.jsx` |
| D1 Users / D2 Item Reports / D3 Matches / D4 Claims / D5 Notifications / D6 Audit | SQLAlchemy models and Alembic migrations | API client calls the backend routes above. |

## State chart and sequence

| Required behavior | Enforcing code | Verification coverage |
|---|---|---|
| Pending Approval -> Active or Rejected | Admin report decision route | Report moderation tests; runtime test execution is currently blocked by the local Python interpreter issue. |
| Active -> Match Found | Matching after an approval; `run_matching` | High-confidence persistence and notification test added. |
| Match Found -> Claim Requested | Claim submission route, which requires proof | Claim workflow test added. |
| Claim Requested -> Approved for Return or Match Found | Administrator claim decision route | Approve and reject workflow tests added. |
| Approved for Return -> Returned -> Closed | Owner status endpoint then Administrator close endpoint | Authorization and transition test added. |
| Every status change has StatusHistory | `record_status_change`; claim history writes | Workflow tests assert report and claim history. |
| Approval saves score/confidence and notifies owners for High | Admin moderation and matching service | High-match integration test added. |
| Rejection records a reason and notifies reporter | Admin moderation; `moderation_comment`, AuditLog/AuditEvent detail, notification | Rejection test added; execute it in a working Python environment. |
| Claim proof is validated, private, and admin-reviewed | Claim router and admin UI | Proof privacy test updated; run it in a working Python environment. |

## Known gaps and verification limits

- Reports are dual-written to exact LostReport/FoundReport models and a legacy `ItemReport` table because existing frontend/API contracts use item names, images, and one shared report ID. Existing search/moderation endpoints still use that compatibility table as their read model. Completing a full normalized-only API cutover is not done.
- Migration `0002_uml_workflows` was not run against the local PostgreSQL container in this review. Docker was unavailable/stopped and the local venv Python launcher references an absent Python 3.11 install. The bundled Python is 3.12 and cannot load the venv's compiled Pydantic core. Do not claim PostgreSQL migration or database connection was verified.
- Backend pytest collection could not run for the same interpreter/dependency mismatch. Feature tests were added/updated but have not been observed passing in this environment.
- Frontend production build passed, but SMTP provider delivery and deployed Vercel/Render operation were not tested here. Only a configured-provider inbox test can establish real email delivery; Mailpit is local capture only.
- The migration deliberately retains legacy tables and downgrade is non-destructive. A separately reviewed cleanup migration is needed after the compatibility API is retired.
