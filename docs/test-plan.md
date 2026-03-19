# Test Plan

## TaskFlow API — Formal Test Plan

**Version:** 1.0.0
**Date:** 2025-03-24
**Author:** TaskFlow Engineering Team

---

## Table of Contents

1. [Test Objectives](#1-test-objectives)
2. [Test Scope](#2-test-scope)
3. [Test Types](#3-test-types)
4. [Test Cases](#4-test-cases)
5. [Code Coverage Target](#5-code-coverage-target)
6. [Test Environment](#6-test-environment)

---

## 1. Test Objectives

The test suite for TaskFlow API aims to:

1. **Validate all CRUD operations** — Ensure tasks can be created, read, updated, and deleted
   correctly through both the service layer and API endpoints.
2. **Verify telemetry accuracy** — Confirm that the telemetry middleware accurately tracks
   request counts, response times, error counts, and status code distributions.
3. **Ensure API contract compliance** — Validate that all endpoints return the correct HTTP
   status codes, response formats, and error messages as defined in the API contract.
4. **Test edge cases and error handling** — Verify graceful handling of invalid inputs,
   missing resources, boundary values, and special characters.
5. **Measure code coverage** — Achieve and maintain a minimum of 80% code coverage across
   the entire `app/` package.

---

## 2. Test Scope

### 2.1 In Scope

| Area                     | Description                                               |
|--------------------------|-----------------------------------------------------------|
| Service layer (CRUD)     | All functions in `app/crud.py`                            |
| API endpoints            | All routes in `app/routers/tasks.py` and `app/main.py`   |
| Data validation          | Pydantic schema validation for create and update          |
| Telemetry middleware     | Request counting, timing, error tracking                  |
| Metrics endpoint         | `/metrics` response format and accuracy                   |
| Error handling           | 404, 422, and edge case responses                         |
| Database operations      | SQLAlchemy model creation, queries, updates, deletes      |

### 2.2 Out of Scope

| Area                     | Reason                                                    |
|--------------------------|-----------------------------------------------------------|
| Streamlit dashboard      | Requires browser rendering; tested manually                |
| Production database      | Tests use isolated in-memory or temporary SQLite databases |
| Performance/load testing | Requires dedicated tooling (locust, k6); deferred         |
| Security testing         | No auth in MVP; deferred to future phase                  |

---

## 3. Test Types

### 3.1 Unit Tests (`tests/test_unit.py`)

**Purpose:** Test individual service layer functions in isolation.

- Direct calls to `app/crud.py` functions with a test database session.
- Verify return types, default values, and data integrity.
- No HTTP layer involved — pure function testing.

**Fixtures:**
- `test_db`: Creates an in-memory SQLite database with the schema applied.
- `db_session`: Provides a scoped session for each test, rolled back after use.

### 3.2 Functional Tests (`tests/test_functional.py`)

**Purpose:** Test the complete API endpoint behavior via HTTP.

- Uses FastAPI's `TestClient` (backed by httpx) to send real HTTP requests.
- Overrides the `get_db` dependency to use a test database.
- Validates HTTP status codes, response bodies, and headers.

**Fixtures:**
- `client`: A configured `TestClient` instance with dependency overrides.

### 3.3 Edge Case Tests (`tests/test_edge_cases.py`)

**Purpose:** Verify the system handles unusual and invalid inputs gracefully.

- Boundary value testing (empty strings, maximum lengths, zero/negative IDs).
- Invalid enum values for status and priority fields.
- Non-existent resource operations (404 scenarios).
- Special characters and Unicode in text fields.

---

## 4. Test Cases

### 4.1 Test Cases Table (TC-001 to TC-020)

| Test ID | Description                           | Input                                                       | Expected Output                              | Type       |
|---------|---------------------------------------|-------------------------------------------------------------|----------------------------------------------|------------|
| TC-001  | Create task with valid data           | `{"title": "Test Task", "description": "A test", "status": "pending", "priority": "high"}` | 201 Created, task object with generated ID and timestamps | Functional |
| TC-002  | Get task by valid ID                  | `GET /tasks/1`                                              | 200 OK, task object matching created task     | Functional |
| TC-003  | List all tasks                        | `GET /tasks/`                                               | 200 OK, array of task objects                | Functional |
| TC-004  | Update task with partial data         | `PUT /tasks/1 {"status": "completed"}`                      | 200 OK, task with updated status, other fields unchanged | Functional |
| TC-005  | Delete task by valid ID               | `DELETE /tasks/1`                                           | 204 No Content, empty response body          | Functional |
| TC-006  | Create task with missing title        | `POST /tasks/ {"description": "no title"}`                  | 422 Unprocessable Entity, validation error   | Edge Case  |
| TC-007  | Get non-existent task                 | `GET /tasks/99999`                                          | 404 Not Found, `"Task not found"` detail     | Edge Case  |
| TC-008  | Update non-existent task              | `PUT /tasks/99999 {"title": "New"}`                         | 404 Not Found, `"Task not found"` detail     | Edge Case  |
| TC-009  | Delete non-existent task              | `DELETE /tasks/99999`                                       | 404 Not Found, `"Task not found"` detail     | Edge Case  |
| TC-010  | Create task with empty string title   | `POST /tasks/ {"title": ""}`                                | 422 Unprocessable Entity, min_length error   | Edge Case  |
| TC-011  | Create task with very long title      | `POST /tasks/ {"title": "a" * 300}`                         | 422 Unprocessable Entity, max_length error   | Edge Case  |
| TC-012  | Create task with invalid status       | `POST /tasks/ {"title": "T", "status": "invalid"}`          | 422 Unprocessable Entity, pattern error      | Edge Case  |
| TC-013  | Pagination with skip and limit        | `GET /tasks/?skip=2&limit=3`                                | 200 OK, at most 3 tasks starting from offset 2 | Functional |
| TC-014  | Metrics endpoint returns data         | `GET /metrics`                                              | 200 OK, dictionary of endpoint metrics       | Functional |
| TC-015  | Telemetry counts requests             | Make 5 POST requests, then check `/metrics`                 | `request_count >= 5` for POST /tasks/        | Unit       |
| TC-016  | Concurrent request handling           | Send 10 requests in rapid succession                        | All succeed without data corruption          | Functional |
| TC-017  | Special characters in title           | `POST /tasks/ {"title": "Test <>&\"'!@#$%"}`               | 201 Created, title stored and returned correctly | Edge Case |
| TC-018  | Duplicate task titles allowed         | Create two tasks with identical titles                       | Both created successfully with different IDs | Functional |
| TC-019  | Bulk create and list operations       | Create 15 tasks, then list all                              | 15 tasks returned in list                    | Functional |
| TC-020  | Response time within threshold        | Measure response time for CRUD operations                    | Each operation completes in < 500ms          | Unit       |

### 4.2 Unit Test Details

| Test Function                      | CRUD Function Tested | Assertions                                     |
|------------------------------------|----------------------|------------------------------------------------|
| `test_create_task_valid`           | `create_task`        | Returns Task, ID > 0, fields match input       |
| `test_create_task_defaults`        | `create_task`        | Status = "pending", priority = "medium"        |
| `test_get_task_exists`             | `get_task`           | Returns Task with correct ID                   |
| `test_get_task_not_exists`         | `get_task`           | Returns None                                   |
| `test_get_tasks_empty`             | `get_tasks`          | Returns empty list                             |
| `test_get_tasks_pagination`        | `get_tasks`          | Respects skip and limit                        |
| `test_get_tasks_filter_status`     | `get_tasks`          | Only matching status returned                  |
| `test_get_tasks_filter_priority`   | `get_tasks`          | Only matching priority returned                |
| `test_update_task_partial`         | `update_task`        | Only specified fields changed                  |
| `test_update_task_not_exists`      | `update_task`        | Returns None                                   |
| `test_delete_task_exists`          | `delete_task`        | Returns True, task no longer in DB             |
| `test_delete_task_not_exists`      | `delete_task`        | Returns False                                  |
| `test_task_timestamps`             | `create_task`        | created_at and updated_at are set              |

---

## 5. Code Coverage Target

### 5.1 Minimum Threshold

- **Overall coverage**: ≥ **80%** of the `app/` package.
- **Critical modules** (`crud.py`, `routers/tasks.py`): ≥ **90%** coverage.
- **Telemetry module** (`telemetry.py`): ≥ **75%** coverage.

### 5.2 Coverage Tools

| Tool            | Purpose                                      |
|-----------------|----------------------------------------------|
| `pytest-cov`    | Coverage measurement and reporting           |
| `--cov=app`     | Scope coverage to the `app/` package         |
| `--cov-report`  | Generate terminal and XML coverage reports   |
| `--cov-fail-under=80` | Fail CI if coverage drops below 80%   |

### 5.3 Coverage Command

```bash
pytest --cov=app --cov-report=term-missing --cov-report=xml -v
```

---

## 6. Test Environment

### 6.1 Software Requirements

| Component      | Version       | Purpose                          |
|----------------|---------------|----------------------------------|
| Python         | 3.11+         | Runtime environment              |
| pytest         | 8.3.3         | Test runner and framework        |
| pytest-cov     | 5.0.0         | Code coverage measurement        |
| httpx          | 0.27.2        | HTTP client for functional tests |
| FastAPI        | 0.115.0       | TestClient for API testing       |
| SQLAlchemy     | 2.0.35        | Test database management         |

### 6.2 Test Database

- **Type**: SQLite in-memory (`sqlite:///:memory:`) or temporary file (`sqlite:///./test_taskflow.db`).
- **Lifecycle**: Created before each test module, destroyed after.
- **Isolation**: Each test function gets a fresh database session.
- **Schema**: Applied via `Base.metadata.create_all()` before tests run.

### 6.3 Test Execution

```bash
# Run all tests with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=term-missing -v

# Run only unit tests
pytest tests/test_unit.py -v

# Run only functional tests
pytest tests/test_functional.py -v

# Run only edge case tests
pytest tests/test_edge_cases.py -v

# Run with coverage threshold enforcement
pytest --cov=app --cov-fail-under=80
```

### 6.4 CI Integration

Tests are automatically executed in the GitHub Actions CI pipeline on every push to `main`
and every pull request. The pipeline runs tests against Python 3.11 and 3.12 on Ubuntu.

---

*End of Test Plan*
