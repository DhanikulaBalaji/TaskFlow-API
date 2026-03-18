# High-Level Design (HLD)

## TaskFlow API — Architecture and Design

**Version:** 1.0.0
**Date:** 2025-03-24
**Author:** TaskFlow Engineering Team

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Component Breakdown](#2-component-breakdown)
3. [API Contract](#3-api-contract)
4. [Data Models](#4-data-models)
5. [Tech Stack Justification](#5-tech-stack-justification)

---

## 1. System Architecture

The TaskFlow API follows a **layered architecture** pattern with clear separation of concerns.
Each layer communicates only with its immediate neighbors, ensuring loose coupling and high
cohesion.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTS                                  │
│          (Browser, curl, Postman, Frontend Apps)                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │  HTTP/REST
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FASTAPI APPLICATION                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Telemetry Middleware                          │  │
│  │   (Request counting, response timing, error tracking)     │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                              │                                  │
│  ┌───────────────────────────▼───────────────────────────────┐  │
│  │                    API Layer (Routers)                     │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │POST /task│  │GET /tasks│  │PUT /task  │  │DELETE    │  │  │
│  │  │          │  │          │  │          │  │  /task    │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │  │
│  │                    GET /metrics                            │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                              │                                  │
│  ┌───────────────────────────▼───────────────────────────────┐  │
│  │              Service Layer (CRUD Module)                   │  │
│  │   create_task | get_task | get_tasks | update | delete    │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                              │                                  │
│  ┌───────────────────────────▼───────────────────────────────┐  │
│  │                Data Layer (SQLAlchemy ORM)                 │  │
│  │   Models → Session → Engine → Connection Pool             │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                              │                                  │
└──────────────────────────────┼──────────────────────────────────┘
                               │  SQL
                               ▼
                    ┌─────────────────────┐
                    │    SQLite Database   │
                    │   (taskflow.db)      │
                    └─────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   STREAMLIT DASHBOARD                            │
│          (Separate process, polls GET /metrics)                  │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│   │ Request Count │  │ Avg Response │  │ Status Code          │  │
│   │   Bar Chart   │  │  Time Chart  │  │   Pie Chart          │  │
│   └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.1 Request Flow

1. Client sends HTTP request to FastAPI application.
2. **Telemetry Middleware** intercepts the request, records the start time.
3. **CORS Middleware** applies cross-origin headers.
4. **API Router** matches the endpoint and invokes the handler function.
5. Handler validates input via **Pydantic schemas**.
6. Handler calls the **CRUD service layer** with a database session.
7. Service layer executes **SQLAlchemy queries** against SQLite.
8. Response flows back through the middleware stack.
9. Telemetry middleware records duration, status code, and updates metrics.
10. Response is returned to the client.

---

## 2. Component Breakdown

### 2.1 API Layer (FastAPI Routers)

**Responsibility:** Accept HTTP requests, validate input, delegate to service layer, return
HTTP responses.

- Built with FastAPI's `APIRouter` for modular endpoint grouping.
- Request bodies validated automatically by Pydantic models.
- Path and query parameters validated via FastAPI's `Query` and `Path` annotations.
- Returns structured JSON responses with appropriate HTTP status codes.
- Auto-generates OpenAPI documentation at `/docs` (Swagger UI) and `/redoc`.

### 2.2 Service Layer (CRUD Module)

**Responsibility:** Implement business logic and data access patterns.

- Pure functions that accept a SQLAlchemy `Session` and schema objects.
- No HTTP-specific logic — fully decoupled from the API layer.
- Handles query construction, filtering, pagination, and partial updates.
- Returns ORM model instances or `None` for not-found cases.
- Transaction management (commit/rollback) happens within this layer.

### 2.3 Data Layer (SQLAlchemy ORM + SQLite)

**Responsibility:** Define data models, manage database connections, execute SQL.

- **SQLAlchemy ORM** provides Python-class-to-table mapping.
- **Declarative Base** used for model definitions.
- **Session management** via dependency injection (`get_db` generator).
- **SQLite** file-based database for zero-configuration persistence.
- Connection pooling configured with `check_same_thread=False` for FastAPI's
  async-compatible sync execution.

### 2.4 Telemetry Layer (Middleware)

**Responsibility:** Transparently collect performance and usage metrics.

- Implemented as Starlette `BaseHTTPMiddleware`.
- Captures: request count, total response time, error count, status code distribution.
- Stores metrics in an **in-memory dictionary** (resets on restart).
- Exposes metrics via a dedicated `GET /metrics` endpoint.
- Adds negligible overhead (< 1ms per request).

### 2.5 Dashboard (Streamlit Application)

**Responsibility:** Visualize API telemetry data in real time.

- Runs as a **separate process** (`streamlit run dashboard/dashboard.py`).
- Polls the `/metrics` endpoint via HTTP.
- Renders interactive Plotly charts: bar charts for request counts and response times,
  pie chart for status code distribution.
- Displays raw metrics in a sortable data table.
- Manual refresh button for on-demand data updates.

---

## 3. API Contract

### 3.1 Endpoints Summary

| Method   | Endpoint          | Description                          | Request Body            | Response                  | Status Codes       |
|----------|-------------------|--------------------------------------|-------------------------|---------------------------|---------------------|
| `POST`   | `/tasks/`         | Create a new task                    | `TaskCreate` JSON       | `TaskResponse` JSON       | 201, 422            |
| `GET`    | `/tasks/`         | List all tasks (with pagination)     | —                       | `TaskResponse[]` JSON     | 200                 |
| `GET`    | `/tasks/{id}`     | Retrieve a single task               | —                       | `TaskResponse` JSON       | 200, 404            |
| `PUT`    | `/tasks/{id}`     | Update an existing task              | `TaskUpdate` JSON       | `TaskResponse` JSON       | 200, 404, 422       |
| `DELETE` | `/tasks/{id}`     | Delete a task                        | —                       | —                         | 204, 404            |
| `GET`    | `/metrics`        | Get telemetry data                   | —                       | Metrics JSON object       | 200                 |
| `GET`    | `/`               | Root welcome endpoint                | —                       | Welcome JSON message      | 200                 |

### 3.2 Query Parameters for GET /tasks/

| Parameter  | Type    | Default | Constraints        | Description                    |
|------------|---------|---------|---------------------|-------------------------------|
| `skip`     | integer | 0       | >= 0                | Number of records to skip     |
| `limit`    | integer | 100     | >= 1, <= 100        | Maximum records to return     |
| `status`   | string  | null    | pending/in-progress/completed | Filter by status    |
| `priority` | string  | null    | low/medium/high     | Filter by priority            |

### 3.3 Request/Response Examples

**Create Task:**
```json
POST /tasks/
{
    "title": "Implement login page",
    "description": "Build the user login form with validation",
    "status": "pending",
    "priority": "high"
}

Response (201):
{
    "id": 1,
    "title": "Implement login page",
    "description": "Build the user login form with validation",
    "status": "pending",
    "priority": "high",
    "created_at": "2025-03-24T10:30:00",
    "updated_at": "2025-03-24T10:30:00"
}
```

**Metrics Response:**
```json
GET /metrics

Response (200):
{
    "POST /tasks/": {
        "request_count": 15,
        "average_response_time": 0.0123,
        "error_count": 2,
        "error_rate": 0.1333,
        "status_codes": {"201": 13, "422": 2}
    }
}
```

---

## 4. Data Models

### 4.1 Task Entity

| Field         | Type         | Constraints                              | Description                |
|---------------|-------------|------------------------------------------|----------------------------|
| `id`          | Integer      | Primary key, auto-increment, indexed     | Unique task identifier     |
| `title`       | String(255)  | Not null, 1-255 characters               | Task title                 |
| `description` | String(1000) | Nullable, max 1000 characters            | Optional task description  |
| `status`      | String(20)   | Not null, default "pending"              | Task status enum           |
| `priority`    | String(10)   | Not null, default "medium"               | Task priority level        |
| `created_at`  | DateTime     | Auto-set on creation                     | Creation timestamp         |
| `updated_at`  | DateTime     | Auto-set on creation and update          | Last modification timestamp|

### 4.2 Status Values

| Value          | Description                                    |
|----------------|------------------------------------------------|
| `pending`      | Task has been created but not started          |
| `in-progress`  | Task is currently being worked on              |
| `completed`    | Task has been finished                         |

### 4.3 Priority Values

| Value    | Description                               |
|----------|-------------------------------------------|
| `low`    | Non-urgent, can be deferred               |
| `medium` | Normal priority, standard queue           |
| `high`   | Urgent, should be addressed promptly      |

---

## 5. Tech Stack Justification

| Technology    | Role                | Justification                                                                                      |
|---------------|---------------------|----------------------------------------------------------------------------------------------------|
| **FastAPI**   | Web framework       | Async-capable, automatic OpenAPI docs, built-in validation, high performance (on par with Node.js) |
| **SQLAlchemy**| ORM                 | Mature, flexible ORM with support for multiple databases; easy migration to PostgreSQL later       |
| **SQLite**    | Database            | Zero-configuration, file-based, perfect for development and single-instance deployments            |
| **Pydantic**  | Data validation     | Tight integration with FastAPI, automatic request/response validation and serialization            |
| **Streamlit** | Dashboard           | Rapid prototyping of data dashboards with minimal code; built-in Plotly integration                |
| **Plotly**    | Charting            | Interactive, publication-quality charts; works seamlessly with Streamlit                           |
| **pytest**    | Testing framework   | Industry standard for Python testing; rich plugin ecosystem (cov, fixtures, parametrize)          |
| **httpx**     | HTTP test client    | Async-compatible HTTP client; integrates with FastAPI's TestClient for functional tests            |
| **Uvicorn**   | ASGI server         | Lightning-fast ASGI server; production-grade with hot reload for development                       |

### 5.1 Why Not Django REST Framework?

FastAPI was chosen over Django REST Framework for its:
- Native async support without additional configuration
- Automatic OpenAPI/Swagger documentation generation
- Pydantic-based validation (faster and more Pythonic than DRF serializers)
- Significantly lower boilerplate for simple CRUD APIs
- Better performance benchmarks for I/O-bound workloads

### 5.2 Why Not PostgreSQL?

SQLite was selected for the MVP because:
- Zero installation and configuration required
- Single-file database simplifies deployment and backups
- Sufficient performance for the target scale (< 100 concurrent users)
- Easy migration path to PostgreSQL via SQLAlchemy's dialect system

---

*End of High-Level Design Document*
