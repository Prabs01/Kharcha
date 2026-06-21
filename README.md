# Kharcha

Keep track of shared expenses with friends and groups. Split bills easily, see who owes whom, and settle up in minutes.

**What it does**
- Create groups for your friends, roommates, or project teams
- Track expenses paid by any group member
- Automatically calculate splits and balances
- View a clear breakdown of who owes who

**Quickstart**

- Prerequisites: Python 3.11+, pip
- Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

- Run the app (development):

```bash
uvicorn backend.app.main:app --reload
```

- The API will be available at http://127.0.0.1:8000 and the OpenAPI docs at http://127.0.0.1:8000/docs

**Run tests**

From the repository root run:

```bash
python -m pytest backend/tests/test_api.py
```

**Tech Stack**
- **Backend:** FastAPI, SQLModel (SQLAlchemy), SQLite
- **Frontend:** React, TypeScript, Vite
- **Testing:** pytest

**Project Structure**
- `backend/` — RESTful API with user management, group management, and expense tracking
- `frontend/` — Web UI for creating groups, adding expenses, and viewing balances
- `migrations/` — Alembic database migrations
