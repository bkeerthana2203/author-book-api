from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import declarative_base, relationship, joinedload, Session
from sqlalchemy import Column, Integer, Float, String, ForeignKey
import jwt

from dataModel import (
    AuthorModel, BookModel, BookOut, AuthorOut,
    UserCreate, UserResponse, LoginRequest,
)
from config import engine, session
from security import (
    hash_password, verify_password, create_access_token,
    SECRET_KEY, ALGORITHM,
)

app = FastAPI()

Base = declarative_base()


# ---------- Models ----------

class Author(Base):
    __tablename__ = "Author"
    author_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    country = Column(String)
    books = relationship("Book", back_populates="author")


class Book(Base):
    __tablename__ = "Book"
    book_id = Column(Integer, primary_key=True, index=True)
    book_title = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    publication_year = Column(Integer)
    author_id = Column(Integer, ForeignKey("Author.author_id", ondelete="RESTRICT"), nullable=False)
    author = relationship("Author", back_populates="books")
    owner_id = Column(Integer, ForeignKey("UserLogin.user_id"), nullable=False)


class User(Base):
    __tablename__ = "UserLogin"
    user_id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)


Base.metadata.create_all(bind=engine)


# ---------- Dependencies ----------

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()


bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    credentials_error = HTTPException(
        status_code=401,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        data = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(data["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise credentials_error

    db_user = db.query(User).filter(User.user_id == user_id).first()
    if not db_user:
        raise credentials_error

    return db_user


# ---------- Auth routes ----------

@app.post("/register", response_model=UserResponse, status_code=201)
def user_register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="The entered email already exists. Create a new email",
        )

    new_user = User(email=user.email, hashed_password=hash_password(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login")
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == credentials.email).first()

    if not db_user or not verify_password(credentials.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(db_user.user_id)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


# ---------- Author routes ----------

@app.post("/author", status_code=201)
def add_author(
    author: AuthorModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_author = Author(name=author.name, country=author.country)
    db.add(new_author)
    db.commit()
    db.refresh(new_author)
    return new_author


@app.get("/author")
def get_author(db: Session = Depends(get_db)):
    return db.query(Author).all()


@app.get("/author/{author_id}")
def get_author_by_id(author_id: int, db: Session = Depends(get_db)):
    author = db.query(Author).filter(Author.author_id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author


@app.get("/author/{author_id}/books", response_model=AuthorOut)
def get_books_by_author(author_id: int, db: Session = Depends(get_db)):
    author = (
        db.query(Author)
        .options(joinedload(Author.books))
        .filter(Author.author_id == author_id)
        .first()
    )
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author


@app.put("/author/{author_id}")
def update_author(
    author_id: int,
    author: AuthorModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_author = db.query(Author).filter(Author.author_id == author_id).first()
    if not db_author:
        raise HTTPException(status_code=404, detail="Author not found")

    db_author.name = author.name
    db_author.country = author.country
    db.commit()
    db.refresh(db_author)
    return db_author


@app.delete("/author/{author_id}")
def delete_author(
    author_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    author = db.query(Author).filter(Author.author_id == author_id).first()
    if not author:
        raise HTTPException(
            status_code=404,
            detail=f"Author with id {author_id} not found",
        )

    book_count = db.query(Book).filter(Book.author_id == author_id).count()
    if book_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete author {author_id}: they still have {book_count} book(s). Delete or reassign those books first.",
        )

    db.delete(author)
    db.commit()
    return {"message": f"Author {author_id} deleted"}


# ---------- Book routes ----------

@app.post("/book", response_model=BookOut, status_code=201)
def add_book(
    book: BookModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    author = db.query(Author).filter(Author.author_id == book.author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    new_book = Book(
        book_title=book.book_title,
        price=book.price,
        publication_year=book.publication_year,
        author_id=book.author_id,
        owner_id=current_user.user_id,
    )
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book


@app.get("/my-books", response_model=list[BookOut])
def my_books(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Book).filter(Book.owner_id == current_user.user_id).all()


@app.get("/book")
def get_book(db: Session = Depends(get_db)):
    return db.query(Book).all()


@app.get("/book/{book_id}")
def get_book_by_id(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.put("/book/{book_id}", response_model=BookOut)
def update_book(
    book_id: int,
    book: BookModel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_book = db.query(Book).filter(Book.book_id == book_id).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    if db_book.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not your book")

    author = db.query(Author).filter(Author.author_id == book.author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    db_book.book_title = book.book_title
    db_book.price = book.price
    db_book.publication_year = book.publication_year
    db_book.author_id = book.author_id
    db.commit()
    db.refresh(db_book)
    return db_book


@app.delete("/book/{book_id}")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = db.query(Book).filter(Book.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.owner_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not your book")

    db.delete(book)
    db.commit()
    return {"detail": "Book deleted"}