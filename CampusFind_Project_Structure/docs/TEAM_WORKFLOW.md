# Team workflow

## Recommended: shared GitHub repository
1. One person pushes this scaffold to the team's shared repository.
2. Each teammate clones it: `git clone <repository-url>`.
3. Open the project root in VS Code.
4. Before coding: `git checkout main` then `git pull origin main`.
5. Create a branch: `git checkout -b feature/CF-11-registration-api`.
6. Edit only your assigned files where possible, then test.
7. Commit and push:
   `git add <your-files>`
   `git commit -m "feat(CF-11): add registration API"`
   `git push -u origin feature/CF-11-registration-api`
8. Open a Pull Request into `main` and request review.

A ZIP is okay as a starter, but separate ZIP copies are not a safe collaboration method. Everyone should ultimately work from the same GitHub repository and use branches. Do not push directly to `main` unless the team agrees.

## Shared-file rules
- `frontend/src/App.jsx` and `backend/app/main.py` are shared integration files. Coordinate before editing.
- Put feature UI in `frontend/src/features/<feature>/`.
- Put API routers/services/schemas in `backend/app/features/<feature>/`.
- Coordinate database changes in `database/schema.sql`.
- Never commit secrets, `.env`, real user information, user uploads, or database dumps.
