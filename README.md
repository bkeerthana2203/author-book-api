# Author & Book API

A REST API for managing authors and their books, built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**. Supports full CRUD operations, nested relationship data (an author's books returned in a single response), and proper validation and error handling throughout.

## Features

- Create, read, and delete authors
- Create and read books, each linked to an author via a foreign key
- Fetch a single author or book by ID, with clean `404` responses when not found
- Fetch an author **with all of their books nested in one response**, using SQLAlchemy relationships and eager loading
- Input validation on every endpoint via Pydantic — invalid data is rejected before it reaches the database
- Referential integrity enforced at the database level: a book can't be created for a nonexistent author, and an author can't be deleted while they still have books attached (`409 Conflict`, with a message explaining why)
- Environment-based configuration — no credentials committed to the repository

## Tech Stack

| | |
|---|---|
| **Framework** | FastAPI |
| **ORM** | SQLAlchemy 2.x |
| **Database** | PostgreSQL |
| **Validation** | Pydantic v2 |
| **Server** | Uvicorn |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/author` | Create a new author |
| `GET` | `/author` | List all authors |
| `GET` | `/author/{author_id}` | Get a single author by ID |
| `GET` | `/author/{author_id}/books` | Get an author with their books nested |
| `DELETE` | `/author/{author_id}` | Delete an author (blocked with `409` if they have books) |
| `POST` | `/book` | Create a new book (requires a valid `author_id`) |
| `GET` | `/book` | List all books |
| `GET` | `/book/{book_id}` | Get a single book by ID |

Full interactive documentation (test every endpoint from the browser) is available at `/docs` once the server is running.

## Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL installed and running locally

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/bkeerthana2203/author-book-api.git
   cd author-book-api
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # Mac/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create the database**

   In pgAdmin (or `psql`), create a new database:
   ```sql
   CREATE DATABASE library;
   ```

5. **Configure environment variables**

   Create a `.env` file in the project root:
   ```
   DB_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/library
   ```

6. **Run the server**
   ```bash
   uvicorn main:app --reload
   ```

   Tables are created automatically on first run. Visit `http://127.0.0.1:8000/docs` to explore and test the API.

## Design Decisions

- **Separate Pydantic schemas for input and output.** A model used to validate an incoming `POST` body is never the same class used to shape a response — this keeps client-facing validation and database structure independently adjustable.
- **Foreign key behavior set to `RESTRICT`.** Deleting an author with existing books is blocked rather than silently cascading or nulling out data, since losing book records or leaving them "orphaned" wasn't an acceptable default for this use case.
- **Eager loading (`joinedload`) for nested responses.** An author's books are fetched in the same query as the author, avoiding a `DetachedInstanceError` from lazy-loading a relationship after the database session has closed.
- **Application-level checks before database-level failures.** Rather than letting a raw database integrity error surface to the client as a `500`, the API checks preconditions (does this author exist? do they have books?) first, returning clear, specific `404`/`409` responses instead.

## What I'd Improve With More Time

- Add authentication so authors/books can be scoped to individual users
- Add `PUT`/`PATCH` endpoints for updating existing authors and books
- Replace `Base.metadata.create_all()` with Alembic migrations for safer schema changes
- Add automated tests (pytest) covering the validation and error-handling paths

## Author

Built as part of a self-directed backend development learning path, covering Python fundamentals through FastAPI, SQL, and SQLAlchemy.
