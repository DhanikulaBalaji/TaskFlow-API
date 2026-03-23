import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Task
from app.schemas import TaskCreate, TaskUpdate
from app import crud

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_taskflow.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestCreateTask:
    def test_create_task_with_valid_data(self, db_session):
        task_data = TaskCreate(
            title="Test Task",
            description="A test task description",
            status="pending",
            priority="high",
        )
        task = crud.create_task(db=db_session, task=task_data)

        assert task.id is not None
        assert task.id > 0
        assert task.title == "Test Task"
        assert task.description == "A test task description"
        assert task.status == "pending"
        assert task.priority == "high"

    def test_create_task_with_defaults(self, db_session):
        task_data = TaskCreate(title="Minimal Task")
        task = crud.create_task(db=db_session, task=task_data)

        assert task.title == "Minimal Task"
        assert task.description == ""
        assert task.status == "pending"
        assert task.priority == "medium"

    def test_create_task_timestamps_are_set(self, db_session):
        task_data = TaskCreate(title="Timestamp Task")
        task = crud.create_task(db=db_session, task=task_data)

        assert task.created_at is not None
        assert task.updated_at is not None

    def test_create_multiple_tasks_unique_ids(self, db_session):
        task1 = crud.create_task(db=db_session, task=TaskCreate(title="Task 1"))
        task2 = crud.create_task(db=db_session, task=TaskCreate(title="Task 2"))
        task3 = crud.create_task(db=db_session, task=TaskCreate(title="Task 3"))

        assert task1.id != task2.id
        assert task2.id != task3.id
        assert task1.id != task3.id


class TestGetTask:
    def test_get_task_existing(self, db_session):
        created = crud.create_task(
            db=db_session, task=TaskCreate(title="Find Me")
        )
        found = crud.get_task(db=db_session, task_id=created.id)

        assert found is not None
        assert found.id == created.id
        assert found.title == "Find Me"

    def test_get_task_non_existing(self, db_session):
        result = crud.get_task(db=db_session, task_id=99999)
        assert result is None

    def test_get_task_returns_all_fields(self, db_session):
        task_data = TaskCreate(
            title="Full Task",
            description="Full description",
            status="in-progress",
            priority="low",
        )
        created = crud.create_task(db=db_session, task=task_data)
        found = crud.get_task(db=db_session, task_id=created.id)

        assert found.title == "Full Task"
        assert found.description == "Full description"
        assert found.status == "in-progress"
        assert found.priority == "low"


class TestGetTasks:
    def test_get_tasks_empty_database(self, db_session):
        tasks = crud.get_tasks(db=db_session)
        assert tasks == []

    def test_get_tasks_returns_all(self, db_session):
        for i in range(5):
            crud.create_task(
                db=db_session, task=TaskCreate(title=f"Task {i}")
            )

        tasks = crud.get_tasks(db=db_session)
        assert len(tasks) == 5

    def test_get_tasks_pagination_skip(self, db_session):
        for i in range(10):
            crud.create_task(
                db=db_session, task=TaskCreate(title=f"Task {i}")
            )

        tasks = crud.get_tasks(db=db_session, skip=5)
        assert len(tasks) == 5

    def test_get_tasks_pagination_limit(self, db_session):
        for i in range(10):
            crud.create_task(
                db=db_session, task=TaskCreate(title=f"Task {i}")
            )

        tasks = crud.get_tasks(db=db_session, limit=3)
        assert len(tasks) == 3

    def test_get_tasks_pagination_skip_and_limit(self, db_session):
        for i in range(10):
            crud.create_task(
                db=db_session, task=TaskCreate(title=f"Task {i}")
            )

        tasks = crud.get_tasks(db=db_session, skip=2, limit=3)
        assert len(tasks) == 3

    def test_get_tasks_filter_by_status(self, db_session):
        crud.create_task(
            db=db_session, task=TaskCreate(title="T1", status="pending")
        )
        crud.create_task(
            db=db_session, task=TaskCreate(title="T2", status="completed")
        )
        crud.create_task(
            db=db_session, task=TaskCreate(title="T3", status="pending")
        )

        tasks = crud.get_tasks(db=db_session, status="pending")
        assert len(tasks) == 2
        assert all(t.status == "pending" for t in tasks)

    def test_get_tasks_filter_by_priority(self, db_session):
        crud.create_task(
            db=db_session, task=TaskCreate(title="T1", priority="high")
        )
        crud.create_task(
            db=db_session, task=TaskCreate(title="T2", priority="low")
        )
        crud.create_task(
            db=db_session, task=TaskCreate(title="T3", priority="high")
        )

        tasks = crud.get_tasks(db=db_session, priority="high")
        assert len(tasks) == 2
        assert all(t.priority == "high" for t in tasks)

    def test_get_tasks_filter_status_and_priority(self, db_session):
        crud.create_task(
            db=db_session,
            task=TaskCreate(title="T1", status="pending", priority="high"),
        )
        crud.create_task(
            db=db_session,
            task=TaskCreate(title="T2", status="completed", priority="high"),
        )
        crud.create_task(
            db=db_session,
            task=TaskCreate(title="T3", status="pending", priority="low"),
        )

        tasks = crud.get_tasks(db=db_session, status="pending", priority="high")
        assert len(tasks) == 1
        assert tasks[0].title == "T1"


class TestUpdateTask:
    def test_update_task_partial_title(self, db_session):
        created = crud.create_task(
            db=db_session, task=TaskCreate(title="Original", priority="low")
        )
        updated = crud.update_task(
            db=db_session,
            task_id=created.id,
            task=TaskUpdate(title="Updated"),
        )

        assert updated is not None
        assert updated.title == "Updated"
        assert updated.priority == "low"

    def test_update_task_partial_status(self, db_session):
        created = crud.create_task(
            db=db_session, task=TaskCreate(title="Task", status="pending")
        )
        updated = crud.update_task(
            db=db_session,
            task_id=created.id,
            task=TaskUpdate(status="completed"),
        )

        assert updated is not None
        assert updated.status == "completed"
        assert updated.title == "Task"

    def test_update_task_multiple_fields(self, db_session):
        created = crud.create_task(
            db=db_session,
            task=TaskCreate(title="Old", description="Old desc", priority="low"),
        )
        updated = crud.update_task(
            db=db_session,
            task_id=created.id,
            task=TaskUpdate(title="New", description="New desc", priority="high"),
        )

        assert updated.title == "New"
        assert updated.description == "New desc"
        assert updated.priority == "high"

    def test_update_task_non_existing(self, db_session):
        result = crud.update_task(
            db=db_session,
            task_id=99999,
            task=TaskUpdate(title="Ghost"),
        )
        assert result is None

    def test_update_task_no_fields(self, db_session):
        created = crud.create_task(
            db=db_session, task=TaskCreate(title="Unchanged")
        )
        updated = crud.update_task(
            db=db_session,
            task_id=created.id,
            task=TaskUpdate(),
        )

        assert updated is not None
        assert updated.title == "Unchanged"


class TestDeleteTask:
    def test_delete_task_existing(self, db_session):
        created = crud.create_task(
            db=db_session, task=TaskCreate(title="Delete Me")
        )
        result = crud.delete_task(db=db_session, task_id=created.id)
        assert result is True

        found = crud.get_task(db=db_session, task_id=created.id)
        assert found is None

    def test_delete_task_non_existing(self, db_session):
        result = crud.delete_task(db=db_session, task_id=99999)
        assert result is False

    def test_delete_does_not_affect_other_tasks(self, db_session):
        task1 = crud.create_task(
            db=db_session, task=TaskCreate(title="Keep Me")
        )
        task2 = crud.create_task(
            db=db_session, task=TaskCreate(title="Delete Me")
        )

        crud.delete_task(db=db_session, task_id=task2.id)

        remaining = crud.get_tasks(db=db_session)
        assert len(remaining) == 1
        assert remaining[0].id == task1.id
