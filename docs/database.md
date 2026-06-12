# Database Documentation

## Overview

The backend uses `SQLModel` on top of SQLAlchemy to define its database models and connection handling. The application creates an engine from `settings.database_url`, enables connection pre-ping for stale connection protection, and uses a small connection pool for concurrent requests. On startup, the app creates missing tables and then runs Alembic migrations up to `head` so the schema stays aligned with the code.

## Connection and Session Handling

Database access is centralized in `app/db.py`.

- `engine = create_engine(...)` creates the shared database engine.
- `create_db_and_table()` calls `SQLModel.metadata.create_all(engine)` to create missing tables.
- `get_session()` is the FastAPI dependency that opens a session, yields it to the request handler, commits on success, and rolls back on any exception.
- `SessionDep` is a reusable type alias for injecting a session into route handlers.

The lifecycle hook in `app/main.py` initializes the database first, then applies Alembic migrations from `migrations/` using `alembic.ini` at the project root.

## Tables

### `user`

Stores application users.

Columns:
- `id`: primary key
- `name`: indexed string
- `email`: unique indexed email address
- `hashed_password`: nullable password hash
- `is_google_account`: boolean flag for Google-authenticated users, defaults to `false`

Notes:
- The email field is unique.
- A user can own expenses, belong to groups, and appear in splits and settlements.

### `group`

Stores expense-sharing groups.

Columns:
- `id`: primary key
- `name`: indexed string

Notes:
- Groups have many members, expenses, and settlements.
- Deleting a group cascades to related group memberships, expenses, and settlements.

### `groupmember`

Join table for the many-to-many relationship between users and groups.

Columns:
- `id`: primary key
- `group_id`: foreign key to `group.id`, `ON DELETE CASCADE`
- `user_id`: foreign key to `user.id`, `ON DELETE CASCADE`

Notes:
- This table is the membership link between users and groups.
- Deleting either side removes the membership row automatically.

### `expenses`

Stores a single expense record inside a group.

Columns:
- `id`: primary key
- `group_id`: foreign key to `group.id`, `ON DELETE CASCADE`
- `paid_by_user_id`: foreign key to `user.id`, `ON DELETE RESTRICT`
- `title`: indexed string
- `total_amount`: non-negative float
- `created_at`: timestamp set at creation time

Notes:
- A group can have many expenses.
- The paying user cannot be deleted while referenced by an expense because of `RESTRICT`.
- Each expense can have many splits.

### `expensesplits`

Stores how an expense is divided among users.

Columns:
- `id`: primary key
- `expense_id`: foreign key to `expenses.id`, `ON DELETE CASCADE`
- `user_id`: foreign key to `user.id`, `ON DELETE CASCADE`
- `amount_owed`: float
- `amount_paid`: float

Notes:
- Deleting an expense removes all of its splits.
- Deleting a user removes their split records.

### `settlement`

Stores settlement records between users inside a group.

Columns:
- `id`: primary key
- `group_id`: foreign key to `group.id`, `ON DELETE CASCADE`
- `from_user_id`: foreign key to `user.id`, `ON DELETE RESTRICT`
- `to_user_id`: foreign key to `user.id`, `ON DELETE RESTRICT`
- `status`: stored as a string, values defined by `SettlementStatus`
- `amount`: float
- `settled_at`: timestamp set at creation time

Notes:
- Group deletion cascades to settlements.
- The source and target users are protected from deletion while referenced by a settlement.

## Relationships

The ORM relationships defined in `app/models.py` are:

- `User` to `Expenses`: one user can pay many expenses.
- `User` to `Group`: many-to-many through `groupmember`.
- `User` to `ExpenseSplits`: one user can appear in many splits.
- `Group` to `Expenses`: one group can contain many expenses.
- `Group` to `Settlement`: one group can contain many settlements.
- `Expenses` to `ExpenseSplits`: one expense can contain many splits.
- `GroupMember` connects one user to one group.

## Enums and Validation

The schema layer defines the following settlement statuses:

- `pending`
- `completed`
- `cancelled`

Expense creation also supports split methods:

- `equal`
- `exact`
- `percentage`

If `split_method` is `exact` or `percentage`, the API requires `split_participants`.

## Migrations

Alembic migrations live under `backend/migrations/`.

- The initial schema revision is `0001_initial_schema`.
- The migration creates tables only when they do not already exist.
- Indexes are created for `user.email`, `user.name`, `group.name`, and `expenses.title`.

## Practical Notes

- `SQLModel.metadata.create_all(engine)` is used as a safety net, but Alembic remains the source of truth for schema evolution.
- The session dependency commits after the request finishes, so route handlers should raise exceptions normally when a transaction must be rolled back.
- Foreign key delete behavior is intentionally mixed: grouping data cascades when removed, while user references in payments and settlements are restricted to avoid accidental data loss.
