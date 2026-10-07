# Author & Book API

A REST API built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL** for managing authors and books. It includes **JWT authentication**, argon2 password hashing, and per-user ownership, so users can only modify the books they created.

## Features

- User registration and login with **JWT authentication**
- Passwords hashed with **argon2** (never stored in plain text)
- Per-user book ownership: users can only update or delete their own books
- Full CRUD for authors and books, with relationships and nested responses
- Safe deletes: an author who still has books can't be deleted (409 Conflict)
- Request validation with Pydantic (email format, password length, field types)
- Consistent error handling: 401, 403, 404, and 409 used for their proper meanings
- Interactive API docs at `/docs` (Swagger UI)

## Tech stack

| Area | Tools |
|---|---|
| Framework | FastAPI, Uvicorn |
| Validation | Pydantic |
| Database | PostgreSQL, SQLAlchemy |
| Authentication | PyJWT, pwdlib (argon2) |
| Configuration | python-dotenv |

## Project structure

```
.
├── main.py            # App, models, dependencies, and routes
├── dataModel.py       # Pydantic request and response schemas
├── config.py          # Database engine and session setup
├── security.py        # Password hashing and JWT creation
├── requirements.txt   # Python dependencies
├── .env.example       # Template for required environment variables
└── README.md
```

## Getting started

### Prerequisites

- Python 3.10 or newer
- A running PostgreSQL server

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/bkeerthana2203/author-book-api.git
   cd <your-repo>
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv

   # Windows (PowerShell)
   venv\Scripts\Activate.ps1

   # macOS / Linux
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create your `.env` file**

   Copy `.env.example` to `.env` and fill in your values (see the next section).

5. **Create the database**

   Create an empty PostgreSQL database matching the name in your `DATABASE_URL`. The tables are created automatically when the app starts.

6. **Run the server**

   ```bash
   uvicorn main:app --reload
   ```

7. **Open the docs**

   Go to <http://127.0.0.1:8000/docs>.

### Environment variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string, e.g. `postgresql+psycopg://user:password@localhost:5432/dbname` |
| `SECRET_KEY` | Secret used to sign JWTs. Keep it private. |

Generate a strong secret key with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

The `postgresql+psycopg://` prefix selects the `psycopg` (v3) driver, which is the default for current SQLAlchemy versions.

## Authentication flow

1. **Register:** `POST /register` with an email and password. The password is hashed with argon2 before it is stored.
2. **Log in:** `POST /login` with the same credentials. The response contains an `access_token`.
3. **Authorize:** in `/docs`, click **Authorize** and paste the token (without the word `Bearer`). Outside `/docs`, send it as a header:

   ```
   Authorization: Bearer <access_token>
   ```

4. **Use protected endpoints.** The server verifies the token's signature and expiry on every request and identifies the user from it. Tokens expire after **30 minutes**.

### Example requests

```bash
# Register
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "strongpassword"}'

# Log in
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "strongpassword"}'

# Create a book (replace TOKEN)
curl -X POST http://127.0.0.1:8000/book \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"book_title": "Example Book", "price": 9.99, "publication_year": 2024, "author_id": 1}'
```

## API endpoints

### Authentication

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/register` | No | Create an account (409 if the email already exists) |
| POST | `/login` | No | Get a JWT access token (401 on invalid credentials) |
| GET | `/me` | Yes | Current user's profile |

### Authors

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/author` | No | List all authors |
| GET | `/author/{id}` | No | Get one author (404 if missing) |
| GET | `/author/{id}/books` | No | Get an author with their books |
| POST | `/author` | Yes | Create an author |
| PUT | `/author/{id}` | Yes | Update an author |
| DELETE | `/author/{id}` | Yes | Delete an author (409 if they still have books) |

### Books

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/book` | No | List all books |
| GET | `/book/{id}` | No | Get one book (404 if missing) |
| GET | `/my-books` | Yes | List books owned by the current user |
| POST | `/book` | Yes | Create a book (owner is set from the token) |
| PUT | `/book/{id}` | Yes (owner) | Update your own book (403 if it isn't yours) |
| DELETE | `/book/{id}` | Yes (owner) | Delete your own book (403 if it isn't yours) |

### Status codes used

| Code | Meaning in this API |
|---|---|
| 201 | Resource created |
| 401 | Missing, invalid, or expired token, or wrong login credentials |
| 403 | Authenticated, but the resource belongs to someone else |
| 404 | Resource not found |
| 409 | Conflict (duplicate email, or deleting an author who still has books) |
| 422 | Request body failed validation |

## Design notes

- **Passwords:** hashed with argon2 through `pwdlib`. Each hash includes a random salt, so identical passwords produce different hashes.
- **JWT contents:** the payload holds only the user id (`sub`) and an expiry (`exp`). JWTs are signed, not encrypted, so nothing sensitive goes inside.
- **Ownership:** the book owner is always taken from the verified token, never from the request body, so a client can't create or claim records under another user's name.
- **No account enumeration:** login returns the same 401 message for an unknown email and a wrong password.
- **Database sessions:** provided through a `get_db` dependency, so every request opens and closes its own session.

## Security notes

- `SECRET_KEY` lives in `.env`, which is git-ignored. Never commit it.
- If the key ever leaks, generate a new one. All existing tokens become invalid and users must log in again.
- Use HTTPS in any real deployment so tokens can't be intercepted in transit.

## Known limitations

- Authors have no owner, so any logged-in user can edit or delete any author. Roles (for example, admin only) or an `owner_id` on `Author` would fix this.
- No refresh tokens, so users log in again after 30 minutes.
- No way to revoke a token before it expires.
- No automated tests.
- Tables are created with `create_all`, with no migration tool such as Alembic.

## Roadmap

- [ ] Switch login to `OAuth2PasswordRequestForm` so the **Authorize** button accepts a username and password
- [ ] Add refresh tokens
- [ ] Add roles and permissions
- [ ] Add pagination and filtering to list endpoints
- [ ] Add automated tests with `pytest`
- [ ] Add database migrations with Alembic
- [ ] Containerize with Docker
