from types import SimpleNamespace
from uuid import uuid4

import app.api.dependencies as deps


def test_exercise_filter_history_and_last_set_routes(client):
    muscle_id = uuid4()
    exercise_id = uuid4()

    class ExerciseService:
        async def list_exercises_by_muscle(self, requested_muscle_id, user_id):
            assert (requested_muscle_id, user_id) == (muscle_id, "user-1")
            return []

    class WorkoutService:
        async def get_exercise_history(self, user_id, requested_exercise_id, limit, before):
            assert (user_id, requested_exercise_id, limit, before) == (
                "user-1",
                exercise_id,
                10,
                None,
            )
            return []

        async def get_last_set(self, user_id, requested_exercise_id):
            assert (user_id, requested_exercise_id) == ("user-1", exercise_id)
            return None

    client.app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(id="user-1")
    client.app.dependency_overrides[deps.get_exercise_service] = lambda: ExerciseService()
    client.app.dependency_overrides[deps.get_workout_service] = lambda: WorkoutService()

    assert client.get(f"/exercises?muscle_id={muscle_id}").status_code == 200
    assert client.get(f"/exercises/{exercise_id}/history?limit=10").status_code == 200
    assert client.get(f"/exercises/{exercise_id}/last-set").status_code == 204


def test_favorite_body_and_path_routes(client):
    exercise_id = uuid4()

    class Service:
        async def add_favorite(self, user_id, requested_exercise_id):
            assert (user_id, requested_exercise_id) == ("user-1", exercise_id)

        async def remove_favorite(self, user_id, requested_exercise_id):
            assert (user_id, requested_exercise_id) == ("user-1", exercise_id)

    client.app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(id="user-1")
    client.app.dependency_overrides[deps.get_favorite_service] = lambda: Service()

    assert client.post("/favorites", json={"exercise_id": str(exercise_id)}).status_code == 204
    assert client.delete(f"/favorites/{exercise_id}").status_code == 204


def test_split_detail_and_update_routes(client):
    split_id = uuid4()
    muscle_id = uuid4()
    split = {
        "id": split_id,
        "name": "Push Day",
        "pic": None,
        "muscles": [{"muscle_id": muscle_id, "nr_of_exercises": 3}],
    }

    class Service:
        async def get_split(self, user_id, requested_split_id):
            assert (user_id, requested_split_id) == ("user-1", split_id)
            return split

        async def update_split(self, user_id, requested_split_id, data):
            assert (user_id, requested_split_id, data.name) == ("user-1", split_id, "Push Day")
            return split

    client.app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(id="user-1")
    client.app.dependency_overrides[deps.get_split_service] = lambda: Service()

    assert client.get(f"/splits/{split_id}").json() == {
        "id": str(split_id),
        "name": "Push Day",
        "pic": None,
        "muscles": [{"muscle_id": str(muscle_id), "nr_of_exercises": 3}],
    }
    update_response = client.put(
        f"/splits/{split_id}",
        json={
            "name": "Push Day",
            "pic": None,
            "muscles": [{"muscle_id": str(muscle_id), "nr_of_exercises": 3}],
        },
    )
    assert update_response.status_code == 200


def test_signup_and_login_return_access_token_with_user(client):
    user_id = uuid4()
    auth_response = {
        "access_token": "access-token",
        "user": {"id": user_id, "email": "athlete@example.com"},
    }

    class Service:
        async def signup(self, email, password):
            assert (email, password) == ("athlete@example.com", "secret123")
            return auth_response

        async def login(self, email, password):
            assert (email, password) == ("athlete@example.com", "secret123")
            return auth_response

    client.app.dependency_overrides[deps.get_auth_service] = lambda: Service()

    signup_response = client.post(
        "/auth/signup",
        json={"email": "athlete@example.com", "password": "secret123"},
    )
    assert signup_response.status_code == 201
    assert signup_response.json()["user"]["id"] == str(user_id)

    login_response = client.post(
        "/auth/login",
        json={"email": "athlete@example.com", "password": "secret123"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["access_token"] == "access-token"


def test_validation_errors_use_standard_error_envelope(client):
    response = client.post("/workouts", json={"split_id": "not-a-uuid"})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["message"]