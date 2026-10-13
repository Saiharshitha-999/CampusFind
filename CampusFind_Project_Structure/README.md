# CampusFind — Project Starter

CampusFind is a Smart Lost-and-Found Matching and Recovery Management System.

**Stack:** React + Vite frontend, FastAPI backend, PostgreSQL database. This is a starter scaffold, not a completed application.

## Structure
- `frontend/` React UI and feature folders
- `backend/` FastAPI API and feature modules
- `database/` SQL schema outline
- `docs/` team workflow, ownership, API conventions, tracker
- `tests/` test notes

## Run backend
Install Python 3.11+, then:
```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Docs: http://127.0.0.1:8000/docs

## Run frontend
Install Node.js 20+, then:
```bash
cd frontend
npm install
npm run dev
```

Copy `.env.example` to `.env` for local settings. Never commit `.env`, credentials, tokens, real user data, uploads, `node_modules/`, or `.venv/`.

## Team collaboration
**Best option:** push this scaffold to one shared GitHub repository. Every teammate should clone the same repository, create a feature branch, commit, push their branch, and open a Pull Request. Do not each edit separate ZIP copies and push them independently.

Read `docs/TEAM_WORKFLOW.md` and `docs/FILE_OWNERSHIP.md` before coding. Coordinate before editing shared files such as `frontend/src/App.jsx`, `backend/app/main.py`, API router, or database schema.

## Security rules
- Never store plain-text passwords; use a maintained password-hashing library.
- Enforce authorization on the backend.
- Public search must show approved reports only.
- Keep finder contact details and ownership proof private.
- Validate uploaded file type and size.
- Smart matches are suggestions, not proof of ownership.

This scaffold contains placeholder modules. Features are not fully implemented yet.
