# Software Requirements Specification (SRS)

## TaskFlow API — Task Management REST API

**Version:** 1.0.0
**Date:** 2025-03-24
**Author:** TaskFlow Engineering Team

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Problem Statement](#2-problem-statement)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Assumptions and Constraints](#5-assumptions-and-constraints)
6. [Out of Scope](#6-out-of-scope)

---

## 1. Introduction

TaskFlow API is a production-grade task management REST API built with **FastAPI**. It provides
a robust backend for creating, reading, updating, and deleting tasks while offering built-in
observability through telemetry middleware and a real-time analytics dashboard.

The system is designed to serve as a lightweight yet fully-featured task management backend
suitable for small-to-medium teams, personal productivity tools, or as a microservice within
a larger project management ecosystem.

### 1.1 Purpose

This document defines the complete set of functional and non-functional requirements for the
TaskFlow API system. It serves as the authoritative reference for design, implementation,
testing, and validation activities throughout the software development lifecycle.

### 1.2 Scope

The TaskFlow API encompasses:

- A RESTful HTTP API for task CRUD operations
- Request/response validation via Pydantic models
- Persistent storage using SQLite via SQLAlchemy ORM
- Telemetry middleware capturing per-endpoint performance metrics
- A `/metrics` endpoint exposing collected telemetry data
- A Streamlit-based dashboard consuming the metrics endpoint

### 1.3 Definitions and Acronyms

| Term       | Definition                                                 |
|------------|------------------------------------------------------------|
| CRUD       | Create, Read, Update, Delete                               |
| ORM        | Object-Relational Mapping                                  |
| REST       | Representational State Transfer                            |
| SRS        | Software Requirements Specification                        |
| API        | Application Programming Interface                          |
| MVP        | Minimum Viable Product                                     |
| p95        | 95th percentile latency                                    |
| Telemetry  | Automated collection of performance and usage metrics      |

---

## 2. Problem Statement

Development teams and individuals need a **lightweight, fast, and observable** task management
API that can be deployed quickly without heavy infrastructure dependencies. Existing solutions
are either too complex (Jira, Asana APIs) or lack built-in observability features.

### 2.1 Key Pain Points

1. **Heavyweight solutions**: Enterprise task management APIs require complex setup, databases,
   and infrastructure that are overkill for small teams.
2. **Lack of observability**: Most lightweight task APIs do not ship with built-in telemetry,
   making it difficult to monitor performance and usage patterns.
3. **Slow iteration cycles**: Teams need an API that can be set up in minutes, not hours,
   with auto-generated documentation and validation.
4. **No visibility into API health**: Without metrics, teams cannot proactively identify
   performance bottlenecks or error-prone endpoints.

### 2.2 Target Users

- Small development teams needing a quick task-tracking backend
- Individual developers building productivity tools
- Teams evaluating API design patterns with observability best practices
- Educators and students studying production-grade API development

---

## 3. Functional Requirements

### FR-001: Create a New Task

| Field       | Detail                                                           |
|-------------|------------------------------------------------------------------|
| **ID**      | FR-001                                                           |
| **Title**   | Create a new task                                                |
| **Description** | The system shall allow users to create a new task by providing a title, optional description, status, and priority. |
| **Input**   | `title` (required, string, 1-255 chars), `description` (optional, string, max 1000 chars), `status` (optional, enum: pending/in-progress/completed, default: pending), `priority` (optional, enum: low/medium/high, default: medium) |
| **Output**  | Created task object with auto-generated `id`, `created_at`, and `updated_at` timestamps |
| **HTTP**    | `POST /tasks/` → `201 Created`                                  |

### FR-002: Retrieve a Single Task by ID

| Field       | Detail                                                           |
|-------------|------------------------------------------------------------------|
| **ID**      | FR-002                                                           |
| **Title**   | Retrieve a single task by ID                                     |
| **Description** | The system shall return a single task when queried by its unique integer ID. |
| **Input**   | `task_id` (path parameter, integer)                              |
| **Output**  | Task object if found; `404 Not Found` if no task exists with the given ID |
| **HTTP**    | `GET /tasks/{task_id}` → `200 OK` or `404 Not Found`            |

### FR-003: List All Tasks with Pagination

| Field       | Detail                                                           |
|-------------|------------------------------------------------------------------|
| **ID**      | FR-003                                                           |
| **Title**   | List all tasks with pagination support                           |
| **Description** | The system shall return a paginated list of all tasks. Pagination is controlled via `skip` and `limit` query parameters. |
| **Input**   | `skip` (optional, integer, default: 0, min: 0), `limit` (optional, integer, default: 100, min: 1, max: 100) |
| **Output**  | Array of task objects                                            |
| **HTTP**    | `GET /tasks/` → `200 OK`                                        |

### FR-004: Update an Existing Task

| Field       | Detail                                                           |
|-------------|------------------------------------------------------------------|
| **ID**      | FR-004                                                           |
| **Title**   | Update an existing task (partial updates)                        |
| **Description** | The system shall allow partial updates to an existing task. Only provided fields are updated; omitted fields remain unchanged. |
| **Input**   | `task_id` (path parameter), plus any combination of `title`, `description`, `status`, `priority` |
| **Output**  | Updated task object; `404 Not Found` if task does not exist      |
| **HTTP**    | `PUT /tasks/{task_id}` → `200 OK` or `404 Not Found`            |

### FR-005: Delete a Task by ID

| Field       | Detail                                                           |
|-------------|------------------------------------------------------------------|
| **ID**      | FR-005                                                           |
| **Title**   | Delete a task by ID                                              |
| **Description** | The system shall permanently remove a task identified by its unique ID. |
| **Input**   | `task_id` (path parameter, integer)                              |
| **Output**  | `204 No Content` on success; `404 Not Found` if task does not exist |
| **HTTP**    | `DELETE /tasks/{task_id}` → `204 No Content` or `404 Not Found`  |

### FR-006: Filter Tasks by Status

| Field       | Detail                                                           |
|-------------|------------------------------------------------------------------|
| **ID**      | FR-006                                                           |
| **Title**   | Filter tasks by status                                           |
| **Description** | The system shall support filtering the task list by status value via a query parameter. |
| **Input**   | `status` query parameter (enum: pending/in-progress/completed)   |
| **Output**  | Array of tasks matching the specified status                     |
| **HTTP**    | `GET /tasks/?status=pending` → `200 OK`                         |

### FR-007: Filter Tasks by Priority

| Field       | Detail                                                           |
|-------------|------------------------------------------------------------------|
| **ID**      | FR-007                                                           |
| **Title**   | Filter tasks by priority                                         |
| **Description** | The system shall support filtering the task list by priority level via a query parameter. |
| **Input**   | `priority` query parameter (enum: low/medium/high)               |
| **Output**  | Array of tasks matching the specified priority                   |
| **HTTP**    | `GET /tasks/?priority=high` → `200 OK`                          |

### FR-008: Track Request Count per Endpoint

| Field       | Detail                                                           |
|-------------|------------------------------------------------------------------|
| **ID**      | FR-008                                                           |
| **Title**   | Track request count per endpoint (telemetry)                     |
| **Description** | The system shall automatically count the number of HTTP requests received by each API endpoint and store these counts in memory. |
| **Input**   | Automatic — intercepted via middleware                           |
| **Output**  | Per-endpoint request count accessible via the metrics endpoint   |

### FR-009: Track Response Time and Error Rate

| Field       | Detail                                                           |
|-------------|------------------------------------------------------------------|
| **ID**      | FR-009                                                           |
| **Title**   | Track response time and error rate per endpoint                  |
| **Description** | The system shall measure the wall-clock response time for each request and track the count and rate of error responses (HTTP 4xx/5xx) per endpoint. |
| **Input**   | Automatic — intercepted via middleware                           |
| **Output**  | Average response time, error count, and error rate per endpoint  |

### FR-010: Expose Metrics Endpoint

| Field       | Detail                                                           |
|-------------|------------------------------------------------------------------|
| **ID**      | FR-010                                                           |
| **Title**   | Expose `/metrics` endpoint with JSON telemetry data              |
| **Description** | The system shall provide a dedicated `/metrics` HTTP endpoint that returns all collected telemetry data in JSON format, including per-endpoint request counts, average response times, error counts, error rates, and status code distributions. |
| **Input**   | None                                                             |
| **Output**  | JSON object keyed by endpoint string                             |
| **HTTP**    | `GET /metrics` → `200 OK`                                       |

---

## 4. Non-Functional Requirements

### 4.1 Performance

| Metric               | Target                              |
|----------------------|--------------------------------------|
| p95 response time    | < 200ms for all CRUD endpoints       |
| Throughput           | ≥ 50 requests/second sustained       |
| Database query time  | < 50ms per query                     |
| Startup time         | < 5 seconds                          |

### 4.2 Scalability

- The system shall support at least **100 concurrent users** without degradation.
- The SQLite database shall handle up to **100,000 tasks** without significant performance loss.
- The telemetry middleware shall introduce no more than **5ms overhead** per request.

### 4.3 Reliability

- **Uptime target**: 99.9% availability for single-instance deployments.
- The system shall handle malformed requests gracefully, returning appropriate HTTP error codes.
- Database transactions shall be atomic — partial writes must not corrupt data.

### 4.4 Maintainability

- Code shall follow PEP 8 style guidelines.
- All modules shall include type hints for function signatures.
- Test coverage shall be maintained at **80% or higher**.
- The project shall include comprehensive documentation (SRS, HLD, LLD, Test Plan).

### 4.5 Security

- Input validation shall prevent SQL injection via parameterized queries (SQLAlchemy ORM).
- Pydantic models shall enforce strict input validation with field length limits and regex patterns.
- CORS middleware shall be configurable for production deployments.

---

## 5. Assumptions and Constraints

### 5.1 Assumptions

1. **SQLite** is used as the database for simplicity and zero-configuration setup.
2. The API will be deployed as a **single-instance** application (no horizontal scaling).
3. **No authentication or authorization** is required for the MVP phase.
4. All telemetry data is stored **in-memory** and resets on application restart.
5. The Streamlit dashboard runs as a **separate process** alongside the API.
6. Python 3.11 or higher is available in the deployment environment.

### 5.2 Constraints

1. SQLite does not support concurrent writes — write operations are serialized.
2. In-memory telemetry data is lost on application restart.
3. The system is designed for single-instance deployment only.
4. File-based SQLite database limits maximum concurrent connections.
5. No real-time push notifications (polling-based dashboard only).

---

## 6. Out of Scope

The following features are explicitly excluded from the current release:

1. **User Authentication and Authorization** — No login, API keys, or JWT tokens.
2. **Multi-Tenancy** — All tasks exist in a single namespace with no user isolation.
3. **File Attachments** — Tasks do not support file uploads or binary data.
4. **Real-Time WebSocket Updates** — The dashboard uses HTTP polling, not WebSocket push.
5. **Email Notifications** — No notification system for task state changes.
6. **Task Dependencies** — No support for task-to-task relationships or dependency graphs.
7. **Audit Logging** — No persistent log of who changed what and when.
8. **Rate Limiting** — No built-in request throttling or abuse prevention.
9. **Database Migration Tool** — Schema changes require manual intervention (no Alembic).
10. **Containerization** — No Docker/Kubernetes manifests in the MVP.

---

*End of Software Requirements Specification*
