from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def restore_participants():
    original_participants = {
        name: deepcopy(activity["participants"])
        for name, activity in activities.items()
    }

    yield

    for name, participants in original_participants.items():
        activities[name]["participants"] = participants


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert set(data["Chess Club"]) == {
        "description",
        "schedule",
        "max_participants",
        "participants",
    }
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_registers_student(client):
    email = "new-student@mergington.edu"

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for Chess Club"
    }
    assert email in activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_student(client):
    email = "new-student@mergington.edu"

    first_response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )
    second_response = client.post(
        "/activities/Chess Club/signup",
        params={"email": email},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert activities["Chess Club"]["participants"].count(email) == 1


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "new-student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_student(client):
    email = "new-student@mergington.edu"
    activities["Chess Club"]["participants"].append(email)

    response = client.delete(f"/activities/Chess Club/participants/{email}")

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from Chess Club"
    }
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/participants/student@mergington.edu"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_unknown_student(client):
    response = client.delete(
        "/activities/Chess Club/participants/unknown@mergington.edu"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
