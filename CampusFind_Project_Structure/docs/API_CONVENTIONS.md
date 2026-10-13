# API conventions

Base path: `/api/v1`. Use JSON for standard requests/responses, Pydantic validation, appropriate HTTP status codes and consistent error responses.

Never return password hashes, private contact details, or ownership-proof files to unauthorized users. Public item search must show approved reports only. Document endpoints as implemented.

Proposed endpoints (not implemented yet):
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/verify-email`
- `POST /auth/password-reset/request`
- `POST /auth/password-reset/confirm`
- `POST /reports/lost`
- `POST /reports/found`
- `GET /items`
- `GET /items/{item_id}`
- `POST /items/{item_id}/claims`
- `GET /claims/mine`
- `GET /admin/reports/pending`
- `POST /admin/reports/{report_id}/decision`
- `POST /claims/{claim_id}/decision`
- `GET /notifications`
