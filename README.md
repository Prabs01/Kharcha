# Kharcha

Simple expense-splitting API built with FastAPI and SQLModel.

**Tech stack:** FastAPI, SQLModel (SQLAlchemy), SQLite, pytest

**What it does**
- Create/list/get/delete users and groups
- Add/remove group members
- Create/list/get/delete expenses within groups
- Add/list expense splits per expense

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
uvicorn backend.main:app --reload
```

- The API will be available at http://127.0.0.1:8000 and the OpenAPI docs at http://127.0.0.1:8000/docs

**Run tests**

From the repository root run:

```bash
python -m pytest backend/tests/test_api.py
```

**Project layout**
- `backend/main.py` — FastAPI application and route handlers
- `backend/models.py` — SQLModel models and DB setup
- `backend/database.db` — SQLite file (created at runtime)
- `backend/tests/test_api.py` — tests for the main API flows

**API (high level)**
- `POST /users` — create user
- `GET /users` — list users
- `GET /users/{id}` — get user
- `DELETE /users/{id}` — delete user
- `POST /groups` — create group
- `GET /groups` — list groups
- `GET /groups/{id}` — get group
- `DELETE /groups/{id}` — delete group
- `POST /groups/{group_id}/members` — add member
- `GET /groups/{group_id}/members` — list members
- `DELETE /groups/{group_id}/members/{user_id}` — remove member
- `POST /groups/{group_id}/expenses` — add expense
- `GET /groups/{group_id}/expenses` — list expenses
- `GET /groups/{group_id}/expenses/{expense_id}` — get expense
- `DELETE /groups/{group_id}/expenses/{expense_id}` — delete expense
- `POST /groups/{group_id}/expenses/{expense_id}/splits` — add split
- `GET /groups/{group_id}/expenses/{expense_id}/splits` — list splits

**Notes & maintenance**
- The project uses SQLite by default. For concurrent or production usage, switch to a DB server (Postgres, MySQL).
- Tests run against an in-memory SQLite engine to keep them isolated.
- Recent fixes: some SQLAlchemy relationship "overlaps" hints were added to silence mapper warnings when using an association object for many-to-many group membership. See `backend/models.py`.

If you'd like, I can also:
- add a `requirements.txt` in the repo root or `pyproject.toml`
- add a Makefile or simple startup script
- expand the API docs with example requests
