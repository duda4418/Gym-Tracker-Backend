from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import app.api.dependencies as deps


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _session(session_id, **overrides):
    data = {
        "id": session_id,
        "split_id": None,
        "started_at": _now(),
        "completed_at": None,
        "notes": None,
        "exercises": [],
    }
    data.update(overrides)
    return data


def test_workout_session_lifecycle_routes(client):
    session_id = uuid4()

    class Service:
        async def create_session(self, user_id, data):
            assert user_id == "user-1"
            return _session(session_id, split_id=data.split_id)

        async def list_sessions(self, user_id, limit, before):
            assert (user_id, limit, before) == ("user-1", 20, None)
            return [_session(session_id, completed_at=_now())]

        async def get_session(self, user_id, requested_id):
            assert (user_id, requested_id) == ("user-1", session_id)
            return _session(session_id)

        async def update_session(self, user_id, requested_id, data):
            assert (user_id, requested_id) == ("user-1", session_id)
            return _session(session_id, notes=data.notes)

        async def delete_session(self, user_id, requested_id):
            assert (user_id, requested_id) == ("user-1", session_id)

    client.app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(id="user-1")
    client.app.dependency_overrides[deps.get_workout_service] = lambda: Service()

    create_response = client.post("/workouts", json={"split_id": None})
    assert create_response.status_code == 201
    assert create_response.json()["id"] == str(session_id)

    list_response = client.get("/workouts?limit=20")
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == str(session_id)

    detail_response = client.get(f"/workouts/{session_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["exercises"] == []

    update_response = client.patch(f"/workouts/{session_id}", json={"notes": "felt strong"})
    assert update_response.status_code == 200
    assert update_response.json()["notes"] == "felt strong"

    delete_response = client.delete(f"/workouts/{session_id}")
    assert delete_response.status_code == 204


def test_workout_exercise_and_set_routes(client):
    session_id = uuid4()
    exercise_id = uuid4()
    workout_exercise_id = uuid4()
    set_id = uuid4()

    class Service:
        async def add_exercise(self, user_id, requested_session_id, data):
            assert (user_id, requested_session_id) == ("user-1", session_id)
            return {
                "id": workout_exercise_id,
                "exercise_id": data.exercise_id,
                "order_index": data.order_index,
                "superset_group_id": None,
                "sets": [],
            }

        async def remove_exercise(self, user_id, requested_session_id, requested_exercise_id):
            assert (user_id, requested_session_id, requested_exercise_id) == (
                "user-1",
                session_id,
                workout_exercise_id,
            )

        async def create_set(self, user_id, requested_exercise_id, data):
            assert (user_id, requested_exercise_id) == ("user-1", workout_exercise_id)
            return {
                "id": set_id,
                **data.model_dump(),
                "completed_at": _now(),
            }

        async def update_set(self, user_id, requested_set_id, data):
            assert (user_id, requested_set_id) == ("user-1", set_id)
            return {
                "id": set_id,
                "set_number": 1,
                "set_type": "standard",
                "target_weight": None,
                "target_reps": None,
                "target_rir": None,
                "actual_weight": data.actual_weight,
                "actual_reps": 8,
                "actual_rir": 2,
                "completed": True,
                "completed_at": _now(),
            }

        async def delete_set(self, user_id, requested_set_id):
            assert (user_id, requested_set_id) == ("user-1", set_id)

    client.app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(id="user-1")
    client.app.dependency_overrides[deps.get_workout_service] = lambda: Service()

    exercise_response = client.post(
        f"/workouts/{session_id}/exercises",
        json={"exercise_id": str(exercise_id), "order_index": 0},
    )
    assert exercise_response.status_code == 201
    assert exercise_response.json()["id"] == str(workout_exercise_id)

    set_response = client.post(
        f"/workout-exercises/{workout_exercise_id}/sets",
        json={
            "set_number": 1,
            "set_type": "standard",
            "actual_weight": 80,
            "actual_reps": 8,
            "actual_rir": 2,
            "completed": True,
        },
    )
    assert set_response.status_code == 201
    assert set_response.json()["id"] == str(set_id)

    update_response = client.patch(f"/sets/{set_id}", json={"actual_weight": 82.5})
    assert update_response.status_code == 200
    assert update_response.json()["actual_weight"] == 82.5

    delete_set_response = client.delete(f"/sets/{set_id}")
    assert delete_set_response.status_code == 204

    delete_exercise_response = client.delete(
        f"/workouts/{session_id}/exercises/{workout_exercise_id}"
    )
    assert delete_exercise_response.status_code == 204