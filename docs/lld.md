# Low-Level Design (LLD)

## TaskFlow API — Detailed Design and Data Models

**Version:** 1.0.0
**Date:** 2025-03-24
**Author:** TaskFlow Engineering Team

---

## Table of Contents

1. [Class Diagrams](#1-class-diagrams)
2. [Function Signatures](#2-function-signatures)
3. [Database Schema](#3-database-schema)
4. [Telemetry Middleware Design](#4-telemetry-middleware-design)
5. [Error Handling Strategy](#5-error-handling-strategy)
6. [Logging Approach](#6-logging-approach)

---

## 1. Class Diagrams

### 1.1 SQLAlchemy Model — Task

```
┌──────────────────────────────────────────────────┐
│                    Task (Model)                   │
│──────────────────────────────────────────────────│
│  __tablename__ = "tasks"                         │
│──────────────────────────────────────────────────│
│  + id          : Integer    [PK, AUTO_INCREMENT] │
│  + title       : String(255)  [NOT NULL]         │
│  + description : String(1000) [NULLABLE]         │
│  + status      : String(20)   [NOT NULL]         │
│  + priority    : String(10)   [NOT NULL]         │
│  + created_at  : DateTime     [AUTO]             │
│  + updated_at  : DateTime     [AUTO]             │
└──────────────────────────────────────────────────┘
```

### 1.2 Pydantic Schemas

```
┌──────────────────────────────────────────┐
│           TaskCreate (BaseModel)         │
│──────────────────────────────────────────│
│  + title       : str   [required, 1-255]│
│  + description : Optional[str] [max 1000│
│  + status      : Optional[str] [enum]   │
│  + priority    : Optional[str] [enum]   │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│           TaskUpdate (BaseModel)         │
│──────────────────────────────────────────│
│  + title       : Optional[str]          │
│  + description : Optional[str]          │
│  + status      : Optional[str]          │
│  + priority    : Optional[str]          │
│──────────────────────────────────────────│
│  All fields optional for partial update  │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│          TaskResponse (BaseModel)        │
│──────────────────────────────────────────│
│  + id          : int                     │
│  + title       : str                     │
│  + description : Optional[str]           │
│  + status      : str                     │
│  + priority    : str                     │
│  + created_at  : datetime                │
│  + updated_at  : datetime                │
│──────────────────────────────────────────│
│  Config: from_attributes = True          │
└──────────────────────────────────────────┘
```

### 1.3 TelemetryMiddleware Class

```
┌────────────────────────────────────────────────────────┐
│        TelemetryMiddleware (BaseHTTPMiddleware)         │
│────────────────────────────────────────────────────────│
│  Inherits: starlette.middleware.base.BaseHTTPMiddleware │
│────────────────────────────────────────────────────────│
│  + dispatch(request, call_next) -> Response             │
│────────────────────────────────────────────────────────│
│  Module-level:                                         │
│  + metrics_store : dict                                │
│  + get_metrics() -> dict                               │
└────────────────────────────────────────────────────────┘

metrics_store structure:
{
    "endpoints": {
        "<METHOD> <PATH>": {
            "request_count": int,
            "total_response_time": float,
            "error_count": int,
            "status_codes": { "<code>": int }
        }
    }
}
```

### 1.4 CRUD Module Functions

```
┌───────────────────────────────────────────────────────────────┐
│                      crud (module)                             │
│───────────────────────────────────────────────────────────────│
│  + create_task(db: Session, task: TaskCreate) -> Task         │
│  + get_task(db: Session, task_id: int) -> Task | None         │
│  + get_tasks(db, skip, limit, status, priority) -> list[Task] │
│  + update_task(db: Session, task_id: int, task: TaskUpdate)   │
│      -> Task | None                                           │
│  + delete_task(db: Session, task_id: int) -> bool             │
└───────────────────────────────────────────────────────────────┘
```

### 1.5 Database Module

```
┌───────────────────────────────────────────────────────┐
│                  database (module)                     │
│───────────────────────────────────────────────────────│
│  + SQLALCHEMY_DATABASE_URL : str                      │
│  + engine : Engine                                    │
│  + SessionLocal : sessionmaker                        │
│  + Base : DeclarativeBase                             │
│  + get_db() -> Generator[Session, None, None]         │
└───────────────────────────────────────────────────────┘
```

---

## 2. Function Signatures

### 2.1 CRUD Functions (app/crud.py)

#### `create_task`
```python
def create_task(db: Session, task: TaskCreate) -> Task:
    """
    Create a new task in the database.

    Args:
        db: Active SQLAlchemy session.
        task: Validated TaskCreate schema with title, description, status, priority.

    Returns:
        The newly created Task ORM instance with auto-generated id and timestamps.

    Side Effects:
        Commits a new row to the tasks table.
    """
```

#### `get_task`
```python
def get_task(db: Session, task_id: int) -> Task | None:
    """
    Retrieve a single task by its primary key.

    Args:
        db: Active SQLAlchemy session.
        task_id: Integer primary key of the task.

    Returns:
        Task instance if found, None otherwise.
    """
```

#### `get_tasks`
```python
def get_tasks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    priority: str | None = None,
) -> list[Task]:
    """
    Retrieve a paginated, optionally filtered list of tasks.

    Args:
        db: Active SQLAlchemy session.
        skip: Number of records to skip (offset).
        limit: Maximum number of records to return.
        status: Optional filter — only return tasks with this status.
        priority: Optional filter — only return tasks with this priority.

    Returns:
        List of Task instances matching the criteria.
    """
```

#### `update_task`
```python
def update_task(db: Session, task_id: int, task: TaskUpdate) -> Task | None:
    """
    Partially update an existing task.

    Args:
        db: Active SQLAlchemy session.
        task_id: Integer primary key of the task to update.
        task: TaskUpdate schema with optional fields to change.

    Returns:
        Updated Task instance if found, None if task does not exist.

    Behavior:
        Only fields explicitly set in the TaskUpdate are modified.
        Uses model_dump(exclude_unset=True) to determine which fields to update.
    """
```

#### `delete_task`
```python
def delete_task(db: Session, task_id: int) -> bool:
    """
    Delete a task by its primary key.

    Args:
        db: Active SQLAlchemy session.
        task_id: Integer primary key of the task to delete.

    Returns:
        True if the task was found and deleted, False otherwise.
    """
```

### 2.2 Database Functions (app/database.py)

#### `get_db`
```python
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a SQLAlchemy session.

    Yields:
        A SQLAlchemy Session instance.

    Cleanup:
        Session is closed in the finally block regardless of success or failure.
    """
```

### 2.3 Telemetry Functions (app/telemetry.py)

#### `TelemetryMiddleware.dispatch`
```python
async def dispatch(self, request: Request, call_next) -> Response:
    """
    Intercept each request, measure timing, and record metrics.

    Args:
        request: The incoming HTTP request.
        call_next: Callable to pass the request to the next middleware/handler.

    Returns:
        The HTTP response from the downstream handler.

    Side Effects:
        Updates metrics_store with request count, timing, status code, and error info.
    """
```

#### `get_metrics`
```python
def get_metrics() -> dict:
    """
    Compute and return a summary of all collected telemetry data.

    Returns:
        Dictionary keyed by endpoint string (e.g. "GET /tasks/"), each containing:
        - request_count: Total requests received
        - average_response_time: Mean response time in seconds
        - error_count: Number of 4xx/5xx responses
        - error_rate: Ratio of errors to total requests
        - status_codes: Distribution of HTTP status codes
    """
```

### 2.4 Router Functions (app/routers/tasks.py)

```python
@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate, db: Session = Depends(get_db)) -> TaskResponse:
    ...

@router.get("/", response_model=list[TaskResponse])
def list_tasks(skip, limit, status, priority, db) -> list[TaskResponse]:
    ...

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)) -> TaskResponse:
    ...

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)) -> TaskResponse:
    ...

@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)) -> None:
    ...
```

---

## 3. Database Schema

### 3.1 Table DDL

```sql
CREATE TABLE tasks (
    id          INTEGER     PRIMARY KEY AUTOINCREMENT,
    title       VARCHAR(255)  NOT NULL,
    description VARCHAR(1000) DEFAULT '',
    status      VARCHAR(20)   NOT NULL DEFAULT 'pending',
    priority    VARCHAR(10)   NOT NULL DEFAULT 'medium',
    created_at  DATETIME      DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME      DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_tasks_id ON tasks (id);
```

### 3.2 Field Constraints

| Field         | SQL Type       | Nullable | Default             | Index    |
|---------------|---------------|----------|---------------------|----------|
| `id`          | INTEGER        | NO       | AUTO_INCREMENT      | PRIMARY  |
| `title`       | VARCHAR(255)   | NO       | —                   | —        |
| `description` | VARCHAR(1000)  | YES      | `''`                | —        |
| `status`      | VARCHAR(20)    | NO       | `'pending'`         | —        |
| `priority`    | VARCHAR(10)    | NO       | `'medium'`          | —        |
| `created_at`  | DATETIME       | YES      | `CURRENT_TIMESTAMP` | —        |
| `updated_at`  | DATETIME       | YES      | `CURRENT_TIMESTAMP` | —        |

### 3.3 Sample Data

| id | title              | description        | status      | priority | created_at          | updated_at          |
|----|--------------------|--------------------|-------------|----------|---------------------|---------------------|
| 1  | Setup CI pipeline  | Configure GitHub…  | completed   | high     | 2025-03-24 10:00:00 | 2025-03-24 14:30:00 |
| 2  | Write unit tests   | Cover CRUD ops     | in-progress | medium   | 2025-03-24 11:00:00 | 2025-03-24 11:00:00 |
| 3  | Update README      |                    | pending     | low      | 2025-03-24 12:00:00 | 2025-03-24 12:00:00 |

---

## 4. Telemetry Middleware Design

### 4.1 Data Flow

```
Request In ──► TelemetryMiddleware.dispatch()
                │
                ├── Record start_time = time.time()
                ├── Build endpoint key = "{METHOD} {PATH}"
                │
                ├── call_next(request) ──► Handler ──► Response
                │
                ├── Record duration = time.time() - start_time
                ├── Update metrics_store[endpoint]:
                │     ├── request_count += 1
                │     ├── total_response_time += duration
                │     ├── status_codes[status_code] += 1
                │     └── if status >= 400: error_count += 1
                │
                └── Return Response
```

### 4.2 In-Memory Storage Structure

The `metrics_store` is a module-level dictionary using `defaultdict` for automatic
initialization of new endpoint entries:

```python
metrics_store = {
    "endpoints": defaultdict(lambda: {
        "request_count": 0,
        "total_response_time": 0.0,
        "error_count": 0,
        "status_codes": defaultdict(int),
    })
}
```

### 4.3 Metrics Aggregation

When `get_metrics()` is called, it iterates over all endpoints and computes:

- **average_response_time**: `total_response_time / request_count`
- **error_rate**: `error_count / request_count`
- **status_codes**: Converted from `defaultdict` to regular `dict` for JSON serialization.

### 4.4 Thread Safety Considerations

Since FastAPI runs request handlers in a thread pool (for synchronous endpoints), the
in-memory `metrics_store` could face race conditions under high concurrency. For the MVP,
this is an accepted limitation. A production system would use:
- `threading.Lock` for critical sections, or
- An atomic counter library, or
- An external metrics store (Redis, Prometheus).

---

## 5. Error Handling Strategy

### 5.1 HTTP Error Responses

| Status Code | Condition                          | Detail Message             |
|-------------|-------------------------------------|----------------------------|
| `404`       | Task not found by ID               | `"Task not found"`         |
| `422`       | Request validation failure          | Auto-generated by Pydantic |
| `400`       | Malformed request body             | Auto-generated by FastAPI  |
| `500`       | Unhandled server error             | Internal Server Error      |

### 5.2 Error Response Format

FastAPI automatically returns validation errors in a structured format:

```json
{
    "detail": [
        {
            "type": "string_too_short",
            "loc": ["body", "title"],
            "msg": "String should have at least 1 character",
            "input": "",
            "ctx": {"min_length": 1}
        }
    ]
}
```

### 5.3 Exception Handling in Routers

```python
# Pattern for all "get by ID" and "update/delete by ID" endpoints
task = crud.get_task(db=db, task_id=task_id)
if task is None:
    raise HTTPException(status_code=404, detail="Task not found")
return task
```

### 5.4 Telemetry Error Recording

The telemetry middleware tracks errors at two levels:

1. **Handled exceptions** (4xx responses): Recorded via status code inspection after
   `call_next()` returns.
2. **Unhandled exceptions** (500 responses): Caught in the middleware's try/except block,
   metrics are updated, then the exception is re-raised for FastAPI's default handler.

---

## 6. Logging Approach

### 6.1 Configuration

The application uses Python's built-in `logging` module with a structured format:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)
```

### 6.2 Log Levels

| Level    | Usage                                                      |
|----------|------------------------------------------------------------|
| `DEBUG`  | Detailed diagnostic info (query parameters, ORM queries)   |
| `INFO`   | Normal operations (server start, request handled)          |
| `WARNING`| Recoverable issues (deprecated usage, high latency)        |
| `ERROR`  | Failed operations (unhandled exceptions, DB errors)        |

### 6.3 Log Points

| Component          | Event                          | Level   |
|--------------------|--------------------------------|---------|
| `app.main`         | Application startup            | INFO    |
| `app.routers.tasks`| Task created / updated / deleted | INFO  |
| `app.routers.tasks`| Task not found                 | WARNING |
| `app.crud`         | Database query executed        | DEBUG   |
| `app.telemetry`    | Metrics endpoint accessed      | DEBUG   |
| `app.telemetry`    | Unhandled exception caught     | ERROR   |

### 6.4 Sample Log Output

```
2025-03-24 10:30:15 | INFO     | app.main | TaskFlow API starting on 0.0.0.0:8000
2025-03-24 10:30:16 | INFO     | app.routers.tasks | Task created: id=1, title="Setup CI"
2025-03-24 10:30:17 | WARNING  | app.routers.tasks | Task not found: id=999
2025-03-24 10:30:18 | DEBUG    | app.crud | Query: SELECT * FROM tasks WHERE id = 1
```

---

*End of Low-Level Design Document*
