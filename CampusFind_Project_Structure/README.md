# CampusFind

CampusFind is a college lost-and-found application built with React + Vite, FastAPI, SQLAlchemy/Alembic, and PostgreSQL. PostgreSQL runs in Docker for local development; teammates use separate local named volumes and do not need PostgreSQL installed on their computers.

## Local setup

Run commands from `CampusFind_Project_Structure` unless the command changes directory.

1. Copy the example environment file once and replace the local database password and `SECRET_KEY` placeholders with private values. The root `.env` is ignored by Git.

   ```powershell
   if (-not (Test-Path .env)) { Copy-Item .env.example .env }
   ```

2. Start PostgreSQL in Docker and verify health:

   ```powershell
   docker compose up -d db
   docker compose ps
   ```

   Wait for `db` to report `healthy`. The default host port is 5432; change `POSTGRES_PORT` in `.env` if needed. Compose uses the official `postgres:16-alpine` image, database `campusfind_db`, user `campusfind_user`, and named volume `campusfind_postgres_data`. Each teammate has an independent local database unless they intentionally configure a remote URL. Never remove the named volume or reset a database as a troubleshooting shortcut.

3. Install backend dependencies, migrate, create the first admin, and start FastAPI:

   ```powershell
   cd backend
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   alembic upgrade head
   python -m app.create_admin
   uvicorn app.main:app --reload
   ```

   The admin command prompts for email, display name, and password. API docs are at `http://127.0.0.1:8000/docs`. Alembic migration `0002_uml_workflows` adds the normalized UML tables and copies legacy reports without dropping legacy tables. `alembic downgrade` is intentionally non-destructive; use a separately reviewed backup/restore process for any database rollback.

4. In a second terminal, start the React app:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

   Vite prints its URL (normally `http://localhost:5173`). The frontend calls `http://localhost:8000/api/v1` by default. Set `VITE_API_URL` if the backend is hosted elsewhere. Set `FRONTEND_ORIGIN` to the exact URL shown by Vite if it selected port 5174.

5. Stop PostgreSQL when finished, keeping the persistent database volume:

   ```powershell
   docker compose stop db
   ```

## Email in development

The example `.env` values use Mailpit, a local SMTP inbox. Start it with `docker compose up -d mailpit`, then open `http://localhost:8025` to read verification and password-reset messages. Mailpit captures messages; it does not deliver them to real mailboxes. `localhost` links only work from the machine running the app.

For real email, set `SMTP_HOST`, `SMTP_PORT`, `SMTP_STARTTLS`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `SMTP_FROM_EMAIL` to values from an SMTP provider in the ignored `.env`, then restart FastAPI. Test that a message arrives in the intended mailbox before relying on real delivery. Never use a public `localhost` frontend URL in a real verification email; configure `FRONTEND_ORIGIN` to the deployed HTTPS site first. Keep SMTP credentials out of source control and chat.

## Seed demo accounts and reports

After migration, you can seed one Administrator, two verified Campus Users, and one sample lost/found pair. Set six shell environment variables to your own private values, then run from `backend/`:

```powershell
$env:SEED_ADMIN_EMAIL = "admin@example.edu"
$env:SEED_ADMIN_PASSWORD = "choose-a-private-password-of-at-least-12-chars"
$env:SEED_USER1_EMAIL = "reporter@example.edu"
$env:SEED_USER1_PASSWORD = "choose-another-private-password"
$env:SEED_USER2_EMAIL = "finder@example.edu"
$env:SEED_USER2_PASSWORD = "choose-a-third-private-password"
python -m app.seed_data
```

The command is idempotent: it leaves existing users and reports untouched. Passwords above are placeholders; replace them locally.

## UML workflows

- Roles: `Campus User` and `Administrator`. Email verification is required before protected use; deactivated accounts cannot authenticate.
- Reports begin as `Pending Approval`; administrator moderation sets `Active` or `Rejected`. Pending and rejected reports are hidden from public search.
- Matching persists `Match` rows with High/Medium/Low confidence. Default weights are category 0.4, description 0.3, location 0.2, and date 0.1. Configure `MATCH_HIGH_THRESHOLD` and `MATCH_MEDIUM_THRESHOLD` in `.env` (defaults 75 and 45).
- Exact report state flow: `Pending Approval -> Active | Rejected`; `Active -> Match Found`; `Match Found -> Claim Requested`; `Claim Requested -> Approved for Return | Match Found`; `Approved for Return -> Returned -> Closed`. Report owners confirm handoff; administrators close recovery.
- Only a found report in `Match Found` can be claimed. Claim submission requires a valid proof file. Only administrators decide claims. Claim proof downloads are available to the claimant and administrator; the report owner gets no proof text or file.
- Status changes are stored in `StatusHistory`; administrator audit events are available in the Admin page. Each notification is recipient-scoped and records delivery status.

## Tests and build

Run backend tests from `backend/` and the frontend production build from `frontend/`:

```powershell
python -m pytest -q
npm run build
```

The current local Python virtual environment must be created with an installed Python 3.11+ interpreter. Alembic uses `DATABASE_URL` if set; otherwise it builds the PostgreSQL URL from `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`.

## Planned hosted deployment

These are setup instructions only; no Vercel, Render, or managed database deployment is claimed as live or tested.

1. Deploy `frontend/` to Vercel and set `VITE_API_URL` to the Render backend URL ending in `/api/v1`.
2. Deploy `backend/` to Render. Install `requirements.txt` and start with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. Provision managed PostgreSQL. Set Render's `DATABASE_URL` to its PostgreSQL URL and run `alembic upgrade head` as the release/pre-deploy migration step after reviewing backups.
4. Configure `APP_ENV=production`, a unique long `SECRET_KEY`, `FRONTEND_ORIGIN` as the Vercel HTTPS origin, and real provider SMTP settings. Set CORS origins to the deployed frontend URL. Use persistent storage for uploaded files if they must survive service restarts.
5. Test registration, email links, moderation, matching, claim privacy, notifications, and recovery closure on the hosted URLs before sharing the website.

## Data and source control

`backend/app/models/` defines the ORM models, `backend/migrations/` defines schema changes, and `database/schema.sql` is a reference. Never commit `.env`, secrets, uploads, `node_modules/`, or `.venv/`. Public report images are served from the upload directory; claim proof is stored outside the public static directory and served only after authorization. See [`TRACEABILITY.md`](TRACEABILITY.md) for the diagram-to-code matrix and known gaps.
