import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_functional.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


class TestRootEndpoint:
    def test_root_returns_welcome(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Welcome to TaskFlow API"
        assert "docs" in data


class TestCreateTask:
    def test_create_task_success(self, client):
        payload = {
            "title": "Test Task",
            "description": "A functional test task",
            "status": "pending",
            "priority": "high",
        }
        response = client.post("/tasks/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["description"] == "A functional test task"
        assert data["status"] == "pending"
        assert data["priority"] == "high"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_task_with_defaults(self, client):
        response = client.post("/tasks/", json={"title": "Minimal"})
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["priority"] == "medium"

    def test_create_duplicate_titles_allowed(self, client):
        payload = {"title": "Duplicate"}
        resp1 = client.post("/tasks/", json=payload)
        resp2 = client.post("/tasks/", json=payload)
        assert resp1.status_code == 201
        assert resp2.status_code == 201
        assert resp1.json()["id"] != resp2.json()["id"]


class TestListTasks:
    def test_list_tasks_empty(self, client):
        response = client.get("/tasks/")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_tasks_returns_created(self, client):
        client.post("/tasks/", json={"title": "Task 1"})
        client.post("/tasks/", json={"title": "Task 2"})

        response = client.get("/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_tasks_pagination(self, client):
        for i in range(15):
            client.post("/tasks/", json={"title": f"Task {i}"})

        response = client.get("/tasks/?skip=5&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_list_tasks_filter_by_status(self, client):
        client.post("/tasks/", json={"title": "T1", "status": "pending"})
        client.post("/tasks/", json={"title": "T2", "status": "completed"})

        response = client.get("/tasks/?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "pending"

    def test_list_tasks_filter_by_priority(self, client):
        client.post("/tasks/", json={"title": "T1", "priority": "high"})
        client.post("/tasks/", json={"title": "T2", "priority": "low"})

        response = client.get("/tasks/?priority=high")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["priority"] == "high"

    def test_bulk_create_and_list(self, client):
        for i in range(15):
            client.post("/tasks/", json={"title": f"Bulk Task {i}"})

        response = client.get("/tasks/")
        assert response.status_code == 200
        assert len(response.json()) == 15


class TestGetTask:
    def test_get_task_success(self, client):
        create_resp = client.post("/tasks/", json={"title": "Find Me"})
        task_id = create_resp.json()["id"]

        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Find Me"

    def test_get_task_not_found(self, client):
        response = client.get("/tasks/99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"


class TestUpdateTask:
    def test_update_task_success(self, client):
        create_resp = client.post("/tasks/", json={"title": "Original"})
        task_id = create_resp.json()["id"]

        response = client.put(
            f"/tasks/{task_id}", json={"title": "Updated", "status": "completed"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"
        assert data["status"] == "completed"

    def test_update_task_not_found(self, client):
        response = client.put("/tasks/99999", json={"title": "Ghost"})
        assert response.status_code == 404

    def test_update_task_partial(self, client):
        create_resp = client.post(
            "/tasks/",
            json={"title": "Partial", "description": "Original desc", "priority": "low"},
        )
        task_id = create_resp.json()["id"]

        response = client.put(f"/tasks/{task_id}", json={"priority": "high"})
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == "high"
        assert data["title"] == "Partial"
        assert data["description"] == "Original desc"


class TestDeleteTask:
    def test_delete_task_success(self, client):
        create_resp = client.post("/tasks/", json={"title": "Delete Me"})
        task_id = create_resp.json()["id"]

        response = client.delete(f"/tasks/{task_id}")
        assert response.status_code == 204

        get_resp = client.get(f"/tasks/{task_id}")
        assert get_resp.status_code == 404

    def test_delete_task_not_found(self, client):
        response = client.delete("/tasks/99999")
        assert response.status_code == 404


class TestMetricsEndpoint:
    def test_metrics_returns_dict(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_metrics_tracks_requests(self, client):
        client.post("/tasks/", json={"title": "Tracked"})
        client.post("/tasks/", json={"title": "Tracked 2"})

        response = client.get("/metrics")
        assert response.status_code == 200
        metrics = response.json()
        assert len(metrics) > 0
