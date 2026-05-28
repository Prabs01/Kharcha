import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool

import main
import models

@pytest.fixture()
def client():
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # attach test engine
    models.engine = test_engine
    models.engine = test_engine

    # recreate tables
    SQLModel.metadata.create_all(test_engine)

    # override dependency
    def override_get_session():
        with Session(test_engine) as session:
            yield session

    main.app.dependency_overrides[models.get_session] = override_get_session

    with TestClient(main.app) as test_client:
        yield test_client

    # cleanup
    main.app.dependency_overrides.clear()


def test_root_route(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "welcome"}


def test_create_list_get_and_delete_user(client):
    create_response = client.post(
        "/users",
        json={
            "name": "Alice",
            "email": "alice@example.com",
            "password": "secret",
        },
    )

    assert create_response.status_code == 200
    user = create_response.json()
    assert user["name"] == "Alice"
    assert user["email"] == "alice@example.com"
    assert "password" not in user

    list_response = client.get("/users")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    user_id = user["id"]
    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == user_id

    delete_response = client.delete(f"/users/{user_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"ok": True}

    missing_response = client.get(f"/users/{user_id}")
    assert missing_response.status_code == 404


def test_create_group_and_add_member(client):
    user_response = client.post(
        "/users",
        json={
            "name": "Bob",
            "email": "bob@example.com",
            "password": "secret",
        },
    )
    group_response = client.post("/groups", json={"name": "Trip"})

    assert user_response.status_code == 200
    assert group_response.status_code == 200

    user_id = user_response.json()["id"]
    group_id = group_response.json()["id"]

    member_response = client.post(f"/groups/{group_id}/members", json={"user_id": user_id})

    assert member_response.status_code == 200
    member = member_response.json()
    assert member["id"] > 0
    assert member["user"]["id"] == user_id
    assert member["user"]["name"] == "Bob"


def test_create_expense_and_splits(client):
    user_response = client.post(
        "/users",
        json={
            "name": "Charlie",
            "email": "charlie@example.com",
            "password": "secret",
        },
    )
    group_response = client.post("/groups", json={"name": "Dinner"})

    assert user_response.status_code == 200
    assert group_response.status_code == 200

    user_id = user_response.json()["id"]
    group_id = group_response.json()["id"]

    member_response = client.post(f"/groups/{group_id}/members", json={"user_id": user_id})

    assert member_response.status_code == 200
    member = member_response.json()
    assert member["id"] > 0
    assert member["user"]["id"] == user_id
    assert member["user"]["name"] == "Charlie"

    expense_response = client.post(
        f"/groups/{group_id}/expenses",
        json={
            "paid_by_user_id": user_id, 
            "title": "Pizza",
            "total_amount": 300.0,
        },
    )

    assert expense_response.status_code == 200
    expense = expense_response.json()
    assert expense["title"] == "Pizza"
    assert expense["total_amount"] == 300.0
    assert expense["paid_by_user"]["id"] == user_id

    expense_id = expense["id"]
    split_response = client.post(
        f"/groups/{group_id}/expenses/{expense_id}/splits",
        json={
            "user_id": user_id,
            "amount_owed": 150.0,
            "amount_paid": 300.0,
        },
    )
    assert split_response.status_code == 200
    split = split_response.json()
    assert split["user"]["id"] == user_id
    assert split["amount_owed"] == 150.0
    assert split["amount_paid"] == 300.0

