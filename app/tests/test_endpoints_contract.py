from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import app.api.dependencies as deps


def _obj(**kwargs):
    return SimpleNamespace(**kwargs)


def _iso_now():
    return datetime.now(timezone.utc).isoformat()


def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_muscles(client):
    class Service:
        async def get_muscles(self):
            return [{"id": str(uuid4()), "name": "Chest", "pic": "/uploads/muscles/chest.png"}]

    client.app.dependency_overrides[deps.get_muscle_service] = lambda: Service()
    response = client.get("/muscles")
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Chest"


def test_create_muscle(client):
    class Service:
        async def create_muscle(self, _):
            return {"id": str(uuid4()), "name": "Back", "pic": "back.png"}

    client.app.dependency_overrides[deps.get_muscle_service] = lambda: Service()
    response = client.post("/muscles", json={"name": "Back", "pic": "back.png"})
    assert response.status_code == 201


def test_get_exercises(client):
    class Service:
        async def list_exercises(self):
            return [
                {
                    "id": str(uuid4()),
                    "name": "Bench Press",
                    "pic": "/uploads/exercises/bench.png",
                    "tips": "keep elbows tucked",
                    "equipment": "barbell",
                    "favourite": False,
                    "primary_muscle": "Chest",
                    "secondary_muscles": ["Triceps"],
                }
            ]

    client.app.dependency_overrides[deps.get_exercise_service] = lambda: Service()
    response = client.get("/exercises")
    assert response.status_code == 200


def test_get_exercises_by_muscle(client):
    class Service:
        async def list_exercises_by_muscle(self, *_):
            return [
                {
                    "id": str(uuid4()),
                    "name": "Push Up",
                    "pic": "/uploads/exercises/pushup.png",
                    "tips": "core tight",
                    "equipment": "bodyweight",
                    "favourite": True,
                    "primary_muscle": "Chest",
                    "secondary_muscles": ["Triceps"],
                }
            ]

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_exercise_service] = lambda: Service()
    response = client.get(f"/exercises/by-muscle/{uuid4()}")
    assert response.status_code == 200


def test_create_exercise(client):
    class Service:
        async def create_exercise(self, _):
            return {
                "id": str(uuid4()),
                "name": "Incline Bench",
                "pic": "incline.png",
                "tips": "slow eccentric",
                "equipment": "barbell",
                "favourite": False,
                "primary_muscle": "Chest",
                "secondary_muscles": ["Triceps"],
            }

    client.app.dependency_overrides[deps.get_exercise_service] = lambda: Service()
    response = client.post(
        "/exercises",
        json={
            "name": "Incline Bench",
            "pic": "incline.png",
            "tips": "slow eccentric",
            "equipment": "barbell",
            "favourite": False,
            "muscle_id": str(uuid4()),
            "secondary_muscles": [str(uuid4())],
        },
    )
    assert response.status_code == 201


def test_create_exercises_bulk(client):
    class Service:
        async def create_bulk(self, _):
            return [
                {
                    "id": str(uuid4()),
                    "name": "Row",
                    "pic": "row.png",
                    "tips": "brace",
                    "equipment": "barbell",
                    "favourite": False,
                    "primary_muscle": "Back",
                    "secondary_muscles": ["Biceps"],
                }
            ]

    client.app.dependency_overrides[deps.get_exercise_service] = lambda: Service()
    response = client.post(
        "/exercises/bulk",
        json={
            "exercises": [
                {
                    "name": "Row",
                    "pic": "row.png",
                    "tips": "brace",
                    "equipment": "barbell",
                    "favourite": False,
                    "muscle_id": str(uuid4()),
                    "secondary_muscles": [str(uuid4())],
                }
            ]
        },
    )
    assert response.status_code == 201


def test_get_splits(client):
    class Service:
        async def get_splits(self, _):
            return [
                {
                    "id": str(uuid4()),
                    "name": "Push",
                    "pic": "push.png",
                    "description": "Chest / Shoulders",
                    "muscles": [
                        {
                            "id": str(uuid4()),
                            "name": "Chest",
                            "pic": "/uploads/muscles/chest.png",
                            "nr_of_exercises": 5,
                            "nr_of_exercises_done_today": 2,
                        }
                    ],
                }
            ]

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_split_service] = lambda: Service()
    response = client.get("/splits")
    assert response.status_code == 200


def test_create_split(client):
    class Service:
        async def create_split(self, *_):
            return {
                "id": str(uuid4()),
                "name": "Leg Day",
                "pic": "legday.png",
                "description": "Legs",
                "muscles": [{"id": str(uuid4()), "name": "Legs", "pic": "legs.png", "nr_of_exercises": 6}],
            }

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_split_service] = lambda: Service()
    response = client.post(
        "/splits",
        json={"name": "Leg Day", "pic": "legday.png", "muscles": [{"muscle_id": str(uuid4()), "nr_of_exercises": 6}]},
    )
    assert response.status_code == 201


def test_delete_split(client):
    class Service:
        async def delete_split(self, *_):
            return None

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_split_service] = lambda: Service()
    response = client.delete(f"/splits/{uuid4()}")
    assert response.status_code == 204


def test_get_todays_workouts(client):
    class Service:
        async def get_todays_workouts(self, _):
            return [{"id": str(uuid4()), "exercise_id": str(uuid4()), "reps": [10], "weights": [50], "date": _iso_now()}]

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_workout_service] = lambda: Service()
    response = client.get("/workouts/today")
    assert response.status_code == 200


def test_get_workouts_by_exercise(client):
    class Service:
        async def get_workouts_for_exercise(self, *_):
            return [{"id": str(uuid4()), "exercise_id": str(uuid4()), "reps": [12], "weights": [30], "date": _iso_now()}]

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_workout_service] = lambda: Service()
    response = client.get(f"/workouts/by-exercise?exercise_id={uuid4()}")
    assert response.status_code == 200


def test_log_workout(client):
    class Service:
        async def log_workout(self, *_):
            return {"message": "Workout logged successfully", "workout_id": str(uuid4())}

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_workout_service] = lambda: Service()
    response = client.post("/log-workout", json={"exercise_id": str(uuid4()), "reps": [10], "weights": [50.0]})
    assert response.status_code == 201


def test_get_workouts(client):
    class Service:
        async def get_workouts(self, _):
            return [{"id": str(uuid4()), "exercise_id": str(uuid4()), "reps": [10], "weights": [45], "date": _iso_now()}]

    client.app.dependency_overrides[deps.get_workout_service] = lambda: Service()
    response = client.get("/workouts")
    assert response.status_code == 200


def test_create_workout(client):
    class Service:
        async def create_workout(self, *_):
            return {"id": str(uuid4()), "exercise_id": str(uuid4()), "reps": [8], "weights": [100], "date": _iso_now()}

    client.app.dependency_overrides[deps.get_workout_service] = lambda: Service()
    response = client.post("/workouts", json={"exercise_id": str(uuid4()), "reps": [8], "weights": [100]})
    assert response.status_code == 201


def test_delete_workout(client):
    class Service:
        async def delete_workout(self, *_):
            return None

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_workout_service] = lambda: Service()
    response = client.delete(f"/workouts?workout_id={uuid4()}")
    assert response.status_code == 204


def test_get_workout_sessions(client):
    class Service:
        async def get_workout_sessions(self, _):
            return [{"id": str(uuid4()), "date": _iso_now(), "split_id": str(uuid4()), "muscles": []}]

    client.app.dependency_overrides[deps.get_workout_session_service] = lambda: Service()
    response = client.get("/workout_sessions")
    assert response.status_code == 200


def test_create_workout_session(client):
    class Service:
        async def create_workout_session(self, _, data):
            return {"id": str(uuid4()), "date": _iso_now(), "split_id": str(data.split_id), "muscles": data.muscles}

    client.app.dependency_overrides[deps.get_workout_session_service] = lambda: Service()
    response = client.post(
        "/workout_sessions",
        json={"split_id": str(uuid4()), "muscles": [{"muscle_id": str(uuid4()), "nr_of_exercises": 3}]},
    )
    assert response.status_code == 201


def test_auth_signup(client):
    class Service:
        async def signup(self, *_):
            return {"id": str(uuid4()), "email": "a@b.com", "name": "Alice"}

    client.app.dependency_overrides[deps.get_auth_service] = lambda: Service()
    response = client.post("/auth/signup", json={"email": "a@b.com", "password": "secret123", "name": "Alice"})
    assert response.status_code == 201


def test_auth_login(client):
    class Service:
        async def login(self, *_):
            return {"access_token": "access", "refresh_token": "refresh", "token_type": "bearer"}

    client.app.dependency_overrides[deps.get_auth_service] = lambda: Service()
    response = client.post("/auth/login", json={"email": "a@b.com", "password": "secret123"})
    assert response.status_code == 200


def test_auth_refresh(client):
    class Service:
        async def refresh_tokens(self, _):
            return {"access_token": "new-access", "refresh_token": "new-refresh", "token_type": "bearer"}

    client.app.dependency_overrides[deps.get_auth_service] = lambda: Service()
    response = client.post("/auth/refresh", json={"refresh_token": "refresh-token-1"})
    assert response.status_code == 200


def test_auth_me(client):
    class Service:
        async def me(self, _):
            return {"id": str(uuid4()), "email": "a@b.com", "name": "Alice"}

    client.app.dependency_overrides[deps.get_auth_service] = lambda: Service()
    response = client.get("/auth/me", headers={"Authorization": "Bearer token-1"})
    assert response.status_code == 200


def test_auth_logout(client):
    class Service:
        async def logout(self, *_):
            return {"message": "User logged out successfully"}

    client.app.dependency_overrides[deps.get_auth_service] = lambda: Service()
    response = client.post("/auth/logout", headers={"Authorization": "Bearer token-1"})
    assert response.status_code == 200


def test_upload_qr(client):
    class Service:
        async def upload_qr(self, *_):
            return {"success": True, "message": "QR code uploaded successfully", "qr_code_url": "https://example.com/qr.png"}

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_qr_service] = lambda: Service()
    response = client.post("/users/upload-qr", files={"file": ("qr.png", b"png", "image/png")})
    assert response.status_code == 200


def test_get_qr(client):
    class Service:
        async def get_qr(self, _):
            return {"qr_code_url": "https://example.com/qr.png"}

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_qr_service] = lambda: Service()
    response = client.get("/users/get-qr")
    assert response.status_code == 200


def test_delete_qr(client):
    class Service:
        async def delete_qr(self, _):
            return {"success": True, "message": "QR code deleted successfully"}

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_qr_service] = lambda: Service()
    response = client.delete("/users/delete-qr")
    assert response.status_code == 200


def test_add_favorite(client):
    class Service:
        async def add_favorite(self, *_):
            return [
                {
                    "id": str(uuid4()),
                    "name": "Curl",
                    "pic": "/uploads/exercises/curl.png",
                    "tips": "full ROM",
                    "equipment": "dumbbell",
                    "favourite": True,
                    "primary_muscle": "Biceps",
                    "secondary_muscles": [],
                }
            ]

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_favorite_service] = lambda: Service()
    response = client.post(f"/favorites/add?exercise_id={uuid4()}")
    assert response.status_code == 200


def test_remove_favorite(client):
    class Service:
        async def remove_favorite(self, *_):
            return [
                {
                    "id": str(uuid4()),
                    "name": "Curl",
                    "pic": "/uploads/exercises/curl.png",
                    "tips": "full ROM",
                    "equipment": "dumbbell",
                    "favourite": False,
                    "primary_muscle": "Biceps",
                    "secondary_muscles": [],
                }
            ]

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_favorite_service] = lambda: Service()
    response = client.delete(f"/favorites/remove?exercise_id={uuid4()}")
    assert response.status_code == 200


def test_get_favorites(client):
    class Service:
        async def get_favorites(self, _):
            return {"favorite_exercises": [str(uuid4())]}

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_favorite_service] = lambda: Service()
    response = client.get("/favorites")
    assert response.status_code == 200
