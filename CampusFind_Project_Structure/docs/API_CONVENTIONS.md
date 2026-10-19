# API conventions

Base path: `/api/v1`. JSON is used except report creation and proof submissions, which use `multipart/form-data`. FastAPI validation errors use HTTP 422 with a `detail` response. Protected routes require a valid active account; user workflows additionally require verified email. Administrator routes require role `Administrator`.

Public search excludes `Pending Approval` and `Rejected` reports. Never return password hashes, private contact email, or claim proof to an unauthorized user. Claim proof is available only to the claimant and an Administrator. Notification read and history routes are scoped to the authenticated recipient.

## Routes

| Method | Path | Access / behavior |
|---|---|---|
| `POST` | `/auth/register` | Public; sends email verification link; does not return a token |
| `POST` | `/auth/verify-email` | Public, signed verification token |
| `POST` | `/auth/verification/request` | Public; generic response to avoid account enumeration |
| `POST` | `/auth/login` | Public; requires verified and active account |
| `GET` | `/auth/me` | Signed-in active account |
| `POST` | `/auth/password-reset/request`, `/auth/password-reset/confirm` | Public; signed purpose-limited token |
| `POST` | `/reports/lost`, `/reports/found` | Verified user; found report requires custody location |
| `GET` | `/reports/mine` | Verified user; own reports |
| `GET` | `/items` | Public; excludes Pending Approval and Rejected |
| `GET` | `/items/{item_id}` | Public for visible report; owner/admin can access a pending or rejected report |
| `GET` | `/items/{item_id}/matches` | Verified report owner; persisted matches |
| `GET` | `/items/{item_id}/history` | Verified report owner or Administrator |
| `POST` | `/items/{item_id}/claims` | Verified user; multipart proof description + required file; FoundReport must be Match Found |
| `GET` | `/claims/mine`, `/claims/received` | Verified user; own claim details or status-only details for owned reports |
| `POST` | `/claims/{claim_id}/proof` | Claimant; legacy repair path only when a pending claim has no proof |
| `GET` | `/claims/{claim_id}/proof` | Claimant or Administrator |
| `POST` | `/claims/{claim_id}/decision` | Administrator only; approve/reject with comment |
| `POST` | `/items/{item_id}/status` | Report owner; only Approved for Return -> Returned |
| `POST` | `/items/{item_id}/close` | Administrator; only Returned -> Closed |
| `GET` | `/admin/reports/pending`, `/admin/claims/pending`, `/admin/recoveries`, `/admin/audit` | Administrator only |
| `POST` | `/admin/reports/{report_id}/decision` | Administrator; Pending Approval -> Active or Rejected; reject requires reason |
| `GET` | `/notifications` | Verified user; own notifications |
| `POST` | `/notifications/{notification_id}/read` | Verified recipient only |

Search accepts `q`, `kind`, `category`, `location`, `sort` (`newest`, `oldest`, `name`), `page`, and `limit`. Item images accept JPEG/PNG/WebP; proof accepts JPEG/PNG/WebP/PDF. Uploads are limited by `MAX_UPLOAD_BYTES` (default 5 MiB).
