# TaskFlow API

```
 _____         _    _____ _                 _    ____ ___
|_   _|_ _ ___| | _|  ___| | _____      __/ \  |  _ \_ _|
  | |/ _` / __| |/ / |_  | |/ _ \ \ /\ / / _ \ | |_) | |
  | | (_| \__ \   <|  _| | | (_) \ V  V / ___ \|  __/| |
  |_|\__,_|___/_|\_\_|   |_|\___/ \_/\_/_/   \_\_|  |___|

  Production-Grade Task Management REST API
```

![CI](https://github.com/DhanikulaBalaji/TaskFlow-API/actions/workflows/ci.yml/badge.svg)

---

## Problem Statement

Development teams need a **lightweight, fast, and observable** task management API that can be
deployed without heavy infrastructure. Existing solutions either lack built-in observability
or require complex setup processes that slow down development workflows.

## Solution Overview

TaskFlow API is a **production-grade REST API** built with FastAPI that provides:

- Full CRUD operations for task management
- Built-in telemetry middleware tracking per-endpoint performance metrics
- Real-time Streamlit dashboard for monitoring API health
- Comprehensive test suite with 80%+ code coverage
- Auto-generated interactive API documentation (Swagger UI)

---

## Architecture

```
┌──────────────┐     HTTP     ┌──────────────────────────────────┐
│   Clients    │ ──────────── │         FastAPI Application       │
│  (Browser,   │              │  ┌────────────────────────────┐  │
│   curl,      │              │  │   Telemetry Middleware      │  │
│   Postman)   │              │  └─────────────┬──────────────┘  │
└──────────────┘              │  ┌─────────────▼──────────────┐  │
                              │  │      API Routers           │  │
                              │  │  POST/GET/PUT/DELETE /tasks │  │
                              │  └─────────────┬──────────────┘  │
                              │  ┌─────────────▼──────────────┐  │
                              │  │    CRUD Service Layer       │  │
                              │  └─────────────┬──────────────┘  │
                              │  ┌─────────────▼──────────────┐  │
                              │  │  SQLAlchemy ORM + SQLite    │  │
                              │  └────────────────────────────┘  │
                              └──────────────────────────────────┘

┌──────────────────────────────────┐
│     Streamlit Dashboard          │
│   (polls GET /metrics endpoint)  │
└──────────────────────────────────┘
```

---

## Tech Stack

| Tool           | Purpose                                    |
|----------------|--------------------------------------------|
| FastAPI        | High-performance async web framework       |
| SQLAlchemy     | ORM for database operations                |
| SQLite         | Lightweight file-based database            |
| Pydantic       | Request/response validation                |
| Uvicorn        | ASGI server                                |
| Streamlit      | Real-time metrics dashboard                |
| Plotly         | Interactive charts and visualizations      |
| pytest         | Testing framework                          |
| pytest-cov     | Code coverage reporting                    |
| httpx          | HTTP client for functional tests           |
| GitHub Actions | Continuous Integration pipeline            |

---

## Folder Structure

```
taskflow-api/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI pipeline
├── app/
│   ├── __init__.py
│   ├── crud.py                 # CRUD service layer
│   ├── database.py             # Database engine and session
│   ├── main.py                 # FastAPI application entry point
│   ├── models.py               # SQLAlchemy ORM models
│   ├── schemas.py              # Pydantic validation schemas
│   ├── telemetry.py            # Telemetry middleware
│   └── routers/
│       ├── __init__.py
│       └── tasks.py            # Task API endpoints
├── dashboard/
│   └── dashboard.py            # Streamlit analytics dashboard
├── docs/
│   ├── requirements.md         # Software Requirements Specification
│   ├── design.md               # High-Level Design document
│   ├── lld.md                  # Low-Level Design document
│   └── test-plan.md            # Formal Test Plan
├── tests/
│   ├── __init__.py
│   ├── test_unit.py            # Unit tests for CRUD operations
│   ├── test_functional.py      # Functional API endpoint tests
│   └── test_edge_cases.py      # Edge case and boundary tests
├── CHANGELOG.md
├── README.md
└── requirements.txt
```

---

## Setup Instructions

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### 1. Clone the Repository

```bash
git clone https://github.com/DhanikulaBalaji/TaskFlow-API.git
cd TaskFlow-API
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the API Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 4. Run the Dashboard (Optional)

```bash
streamlit run dashboard/dashboard.py
```

### 5. Run Tests

```bash
pytest -v
```

With coverage:

```bash
pytest --cov=app --cov-report=term-missing -v
```

---

## API Documentation

### Endpoints

| Method   | Endpoint          | Description                        | Request Body      | Response           |
|----------|-------------------|------------------------------------|--------------------|--------------------|
| `GET`    | `/`               | Root welcome message               | —                  | Welcome JSON       |
| `POST`   | `/tasks/`         | Create a new task                  | `TaskCreate` JSON  | `TaskResponse` 201 |
| `GET`    | `/tasks/`         | List all tasks (paginated)         | —                  | `TaskResponse[]`   |
| `GET`    | `/tasks/{id}`     | Get a single task by ID            | —                  | `TaskResponse`     |
| `PUT`    | `/tasks/{id}`     | Update a task (partial)            | `TaskUpdate` JSON  | `TaskResponse`     |
| `DELETE` | `/tasks/{id}`     | Delete a task                      | —                  | 204 No Content     |
| `GET`    | `/metrics`        | Get telemetry metrics              | —                  | Metrics JSON       |

### Create Task (Request Body)

```json
{
    "title": "Implement feature X",
    "description": "Build the new feature with full test coverage",
    "status": "pending",
    "priority": "high"
}
```

**Fields:**
- `title` (required): 1-255 characters
- `description` (optional): Up to 1000 characters, defaults to `""`
- `status` (optional): `pending` | `in-progress` | `completed`, defaults to `pending`
- `priority` (optional): `low` | `medium` | `high`, defaults to `medium`

### Update Task (Request Body)

All fields are optional. Only provided fields are updated.

```json
{
    "status": "completed"
}
```

### Query Parameters for GET /tasks/

| Parameter  | Type    | Default | Description                |
|------------|---------|---------|----------------------------|
| `skip`     | integer | 0       | Number of records to skip  |
| `limit`    | integer | 100     | Max records to return (1-100) |
| `status`   | string  | —       | Filter by status           |
| `priority` | string  | —       | Filter by priority         |

---

## Telemetry & Metrics

TaskFlow API includes built-in telemetry middleware that automatically tracks:

- **Request count** per endpoint
- **Average response time** per endpoint
- **Error count and error rate** per endpoint
- **HTTP status code distribution**

Access metrics via `GET /metrics`:

```json
{
    "POST /tasks/": {
        "request_count": 42,
        "average_response_time": 0.0087,
        "error_count": 3,
        "error_rate": 0.0714,
        "status_codes": {"201": 39, "422": 3}
    }
}
```

The Streamlit dashboard (`dashboard/dashboard.py`) provides visual charts for these metrics.

---

## Testing

The project includes three test suites:

| Suite                 | File                       | Coverage Area                    |
|-----------------------|----------------------------|----------------------------------|
| Unit Tests            | `tests/test_unit.py`       | CRUD service layer functions     |
| Functional Tests      | `tests/test_functional.py` | API endpoints via HTTP           |
| Edge Case Tests       | `tests/test_edge_cases.py` | Invalid inputs and boundaries    |

### Run All Tests

```bash
pytest -v
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=term-missing -v
```

### Coverage Target

Minimum **80%** code coverage enforced in CI.

---

## License

This project is provided for educational and demonstration purposes.

---

*Built with FastAPI, SQLAlchemy, and Streamlit.*
