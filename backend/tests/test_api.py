import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool

import app.main as main
import app.models as models

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


def add_user(client, name, email, password):
    response = client.post(
        "/users",
        json={
            "name": name,
            "email": email,
            "password": password,
        },
    )
    assert response.status_code == 200
    return response.json()


def login(client, email, password):
    response = client.post(
        "/users/token",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def add_group(client, name, *, email, password):
    token = login(client, email, password)
    response = client.post(
        "/groups",
        json={"name": name},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    return response.json()

def add_member(client, group_id, user_id):
    response = client.post(f"/groups/{group_id}/members", json={"user_id": user_id})
    assert response.status_code == 200
    return response.json()

def add_expense(client, group_id, paid_by_user_id, title, total_amount, split_method = "equal", split_participants = None):
    response = client.post(
        f"/groups/{group_id}/expenses",
        json={
            "paid_by_user_id": paid_by_user_id,
            "title": title,
            "total_amount": total_amount,
            "split_method": split_method,
            "split_participants": split_participants
        },
    )
    assert response.status_code == 200
    return response.json()

def add_split(client, group_id, expense_id, user_id, amount_owed, amount_paid):
    response = client.post(
        f"/groups/{group_id}/expenses/{expense_id}/splits",
        json={
            "user_id": user_id,
            "amount_owed": amount_owed,
            "amount_paid": amount_paid,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_create_list_get_and_delete_user(client):
    user = add_user(client, "Alice", "alice@example.com", "secret")
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
    user = add_user(client, "Bob", "bob@example.com", "secret")
    group = add_group(client, "Trip", email="bob@example.com", password="secret")

    user_id = user["id"]
    group_id = group["id"]

    members_response = client.get(f"/groups/{group_id}/members")
    assert members_response.status_code == 200
    members = members_response.json()
    assert len(members) == 1
    assert members[0]["id"] == user_id
    assert members[0]["name"] == "Bob"

    duplicate_response = client.post(
        f"/groups/{group_id}/members",
        json={"user_id": user_id},
    )
    assert duplicate_response.status_code == 400


def test_create_expense_and_splits(client):
    user = add_user(client, "Charlie", "charlie@example.com", "secret")
    group = add_group(client, "Dinner", email="charlie@example.com", password="secret")

    user_id = user["id"]
    group_id = group["id"]

    expense = add_expense(client, group_id, user_id, "Pizza", 300.0)

    assert expense["title"] == "Pizza"
    assert expense["total_amount"] == 300.0
    assert expense["paid_by_user"]["id"] == user_id

    expense_id = expense["id"]
    split = add_split(client, group_id, expense_id, user_id, 150.0, 300.0)

    assert split["user"]["id"] == user_id
    assert split["amount_owed"] == 150.0
    assert split["amount_paid"] == 300.0

def test_calculate_balance(client):
    # Create users
    user1 = add_user(client, "Dave", "Dave@example.com", "secret")
    user2 = add_user(client, "Eve", "Eve@example.com", "secret")

    # Create group (creator is auto-added as a member)
    group = add_group(client, "Movie Night", email="Dave@example.com", password="secret")
    group_id = group["id"]

    add_member(client, group_id, user2["id"])

    # Create expense
    add_expense(client, group_id, user1["id"], "Tickets", 200.0)
    add_expense(client, group_id, user2["id"], "Popcorn", 100.0, split_method = "exact", split_participants = [
        {"user_id": user1["id"],
        "amount": 30.0},
        {"user_id": user2["id"],
        "amount": 70.0}
    ])
    add_expense(client, group_id, user1["id"], "Drinks", 50.0, split_method = "percentage", split_participants = [
        {"user_id": user1["id"],
        "percentage": 25.0},
        {"user_id": user2["id"],
        "percentage": 75.0}
    ])

    # Calculate balance
    balance_response = client.get(f"/groups/{group_id}/balances")
    assert balance_response.status_code == 200
    balances = balance_response.json()["balances"]
     
    user1_balance = next(b for b in balances if b["user_id"] == user1["id"])
    user2_balance = next(b for b in balances if b["user_id"] == user2["id"])

    assert abs(user1_balance["balance"] - 107.5) < 1e-6
    assert abs(user2_balance["balance"] + 107.5) < 1e-6 


def test_calculate_settlement(client):
    # Create users
    user1 = add_user(client, "Frank", "Frank@example.com", "secret")
    user2 = add_user(client, "Grace", "Grace@example.com", "secret")

    # Create group (creator is auto-added as a member)
    group = add_group(client, "Concert", email="Frank@example.com", password="secret")
    group_id = group["id"]

    add_member(client, group_id, user2["id"])

    # Create expenses
    add_expense(client, group_id, user1["id"], "Tickets", 300.0)
    add_expense(client, group_id, user2["id"], "Food", 150.0)

    # Calculate settlement
    settlement_response = client.get(f"/groups/{group_id}/settlements/suggested")
    assert settlement_response.status_code == 200
    settlements = settlement_response.json()["settlements"]
    assert len(settlements) == 1
    settlement = settlements[0]
    assert settlement["from_user_id"] == user2["id"]
    assert settlement["to_user_id"] == user1["id"]
    assert abs(settlement["amount"] - 75.0) < 1e-6