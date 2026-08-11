from types import SimpleNamespace
from uuid import uuid4

import app.api.dependencies as deps


def _obj(**kwargs):
    return SimpleNamespace(**kwargs)


def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_muscles(client):
    class Service:
        async def get_muscles(self):
            return [{"id": str(uuid4()), "name": "Chest", "pic": "chest.png"}]

    client.app.dependency_overrides[deps.get_muscle_service] = lambda: Service()
    response = client.get("/muscles")
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Chest"
    assert response.json()[0]["pic"] == "chest.png"


def test_create_muscle(client):
    class Service:
        async def create_muscle(self, _):
            return {"id": str(uuid4()), "name": "Back", "pic": "back.png"}

    client.app.dependency_overrides[deps.get_muscle_service] = lambda: Service()
    response = client.post("/muscles", json={"name": "Back", "pic": "back.png"})
    assert response.status_code == 201


def test_get_exercises(client):
    muscle_id = uuid4()

    class Service:
        async def list_exercises(self):
            return [
                {
                    "id": str(uuid4()),
                    "name": "Bench Press",
                    "muscle_id": str(muscle_id),
                    "pic": "/uploads/exercises/bench.png",
                    "tips": "keep elbows tucked",
                    "equipment": "barbell",
                    "rest_time": 90,
                    "favourite": False,
                    "primary_muscle": "Chest",
                    "secondary_muscles": ["Triceps"],
                }
            ]

    client.app.dependency_overrides[deps.get_exercise_service] = lambda: Service()
    response = client.get("/exercises")
    assert response.status_code == 200


def test_get_exercises_by_muscle(client):
    muscle_id = uuid4()

    class Service:
        async def list_exercises_by_muscle(self, *_):
            return [
                {
                    "id": str(uuid4()),
                    "name": "Push Up",
                    "muscle_id": str(muscle_id),
                    "pic": "/uploads/exercises/pushup.png",
                    "tips": "core tight",
                    "equipment": "bodyweight",
                    "rest_time": 90,
                    "favourite": True,
                    "primary_muscle": "Chest",
                    "secondary_muscles": ["Triceps"],
                }
            ]

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_exercise_service] = lambda: Service()
    response = client.get(f"/exercises?muscle_id={muscle_id}")
    assert response.status_code == 200


def test_create_exercise(client):
    muscle_id = uuid4()

    class Service:
        async def create_exercise(self, data):
            assert data.rest_time == 90
            return {
                "id": str(uuid4()),
                "name": "Incline Bench",
                "muscle_id": str(muscle_id),
                "pic": "incline.png",
                "tips": "slow eccentric",
                "equipment": "barbell",
                "rest_time": 90,
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
            "rest_time": 90,
            "favourite": False,
            "muscle_id": str(muscle_id),
            "secondary_muscles": [str(uuid4())],
        },
    )
    assert response.status_code == 201


def test_update_exercise(client):
    exercise_id = uuid4()
    muscle_id = uuid4()

    class Service:
        async def update_exercise(self, requested_id, data):
            assert requested_id == exercise_id
            assert data.name == "Incline Dumbbell Press"
            assert data.exercise_type == "weighted"
            assert data.rest_time == 120
            return {
                "id": str(exercise_id),
                "name": data.name,
                "muscle_id": str(muscle_id),
                "pic": None,
                "tips": None,
                "equipment": "dumbbells",
                "exercise_type": data.exercise_type,
                "rest_time": data.rest_time,
                "favourite": False,
                "primary_muscle": "Chest",
                "secondary_muscles": ["Triceps"],
            }

    client.app.dependency_overrides[deps.get_exercise_service] = lambda: Service()
    response = client.patch(
        f"/exercises/{exercise_id}",
        json={
            "name": "Incline Dumbbell Press",
            "equipment": "dumbbells",
            "exercise_type": "weighted",
            "rest_time": 120,
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Incline Dumbbell Press"
    assert response.json()["exercise_type"] == "weighted"
    assert response.json()["rest_time"] == 120


def test_create_exercises_bulk(client):
    muscle_id = uuid4()

    class Service:
        async def create_bulk(self, _):
            return [
                {
                    "id": str(uuid4()),
                    "name": "Row",
                    "muscle_id": str(muscle_id),
                    "pic": "row.png",
                    "tips": "brace",
                    "equipment": "barbell",
                    "rest_time": 90,
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
                    "rest_time": 90,
                    "favourite": False,
                    "muscle_id": str(muscle_id),
                    "secondary_muscles": [str(uuid4())],
                }
            ]
        },
    )
    assert response.status_code == 201


def test_get_splits(client):
    muscle_id = uuid4()

    class Service:
        async def get_splits(self, _):
            return [
                {
                    "id": str(uuid4()),
                    "name": "Push",
                    "pic": "push.png",
                    "muscles": [{"muscle_id": str(muscle_id), "nr_of_exercises": 5}],
                }
            ]

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_split_service] = lambda: Service()
    response = client.get("/splits")
    assert response.status_code == 200


def test_create_split(client):
    muscle_id = uuid4()

    class Service:
        async def create_split(self, *_):
            return {
                "id": str(uuid4()),
                "name": "Leg Day",
                "pic": "legday.png",
                "muscles": [{"muscle_id": str(muscle_id), "nr_of_exercises": 6}],
            }

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_split_service] = lambda: Service()
    response = client.post(
        "/splits",
        json={"name": "Leg Day", "pic": "legday.png", "muscles": [{"muscle_id": str(muscle_id), "nr_of_exercises": 6}]},
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


def test_auth_signup(client):
    user_id = uuid4()

    class Service:
        async def signup(self, *_):
            return {"access_token": "access", "user": {"id": str(user_id), "email": "a@b.com"}}

    client.app.dependency_overrides[deps.get_auth_service] = lambda: Service()
    response = client.post("/auth/signup", json={"email": "a@b.com", "password": "secret123"})
    assert response.status_code == 201


def test_auth_login(client):
    class Service:
        async def login(self, *_):
            return {"access_token": "access", "user": {"id": str(uuid4()), "email": "a@b.com"}}

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

    response = client.put("/users/upload-qr", files={"file": ("qr.png", b"png", "image/png")})
    assert response.status_code == 200


def test_get_qr(client):
    class Service:
        async def get_qr(self, _):
            return {"qr_code_url": "https://example.com/qr.png"}

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_qr_service] = lambda: Service()
    response = client.get("/users/get-qr")
    assert response.status_code == 200


def test_get_qr_image(client):
    class Service:
        async def get_qr_image(self, _):
            return b"png-data", "image/png"

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_qr_service] = lambda: Service()
    response = client.get("/users/qr-image")

    assert response.status_code == 200
    assert response.content == b"png-data"
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "private, no-store"


def test_delete_qr(client):
    class Service:
        async def delete_qr(self, _):
            return {"success": True, "message": "QR code deleted successfully"}

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_qr_service] = lambda: Service()
    response = client.delete("/users/delete-qr")
    assert response.status_code == 200


def test_upload_profile_picture(client):
    class Service:
        async def upload_profile_picture(self, *_):
            return {
                "success": True,
                "message": "Profile picture uploaded successfully",
                "profile_pic": "/users/profile-picture",
            }

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_profile_service] = lambda: Service()
    response = client.post(
        "/users/profile-picture",
        files={"file": ("profile.webp", b"webp", "image/webp")},
    )

    assert response.status_code == 200
    assert response.json()["profile_pic"] == "/users/profile-picture"

    response = client.put(
        "/users/profile-picture",
        files={"file": ("profile.webp", b"webp", "image/webp")},
    )
    assert response.status_code == 200


def test_get_profile_picture(client):
    class Service:
        async def get_profile_picture(self, _):
            return b"image-data", "image/png"

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_profile_service] = lambda: Service()
    response = client.get("/users/profile-picture")

    assert response.status_code == 200
    assert response.content == b"image-data"
    assert response.headers["content-type"] == "image/png"


def test_delete_profile_picture(client):
    class Service:
        async def delete_profile_picture(self, _):
            return {"success": True, "message": "Profile picture deleted successfully"}

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_profile_service] = lambda: Service()
    response = client.delete("/users/profile-picture")

    assert response.status_code == 200


def test_add_favorite(client):
    class Service:
        async def add_favorite(self, *_):
            return None

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_favorite_service] = lambda: Service()
    response = client.post("/favorites", json={"exercise_id": str(uuid4())})
    assert response.status_code == 204


def test_remove_favorite(client):
    class Service:
        async def remove_favorite(self, *_):
            return None

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_favorite_service] = lambda: Service()
    response = client.delete(f"/favorites/{uuid4()}")
    assert response.status_code == 204


def test_get_favorites(client):
    class Service:
        async def get_favorites(self, _):
            return {"favorite_exercises": [str(uuid4())]}

    client.app.dependency_overrides[deps.get_current_user] = lambda: _obj(id="auth-user-1")
    client.app.dependency_overrides[deps.get_favorite_service] = lambda: Service()
    response = client.get("/favorites")
    assert response.status_code == 200
