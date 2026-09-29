from fastapi import FastAPI,HTTPException
from dataModel import AuthorModel,BookModel,BookOut,AuthorOut
from config import engine,session
from sqlalchemy.orm import declarative_base,relationship,joinedload
from sqlalchemy import Column,Integer,Float,String,ForeignKey


app = FastAPI()

Base = declarative_base()

class Author(Base):
    __tablename__ = "Author"
    author_id = Column(Integer,primary_key=True,index=True)
    name = Column(String , nullable=False)
    country = Column(String)
    books = relationship("Book", back_populates = "author")

class Book(Base):
    __tablename__ = "Book"
    book_id = Column(Integer, primary_key=True, index=True)
    book_title = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    publication_year = Column(Integer)
    author_id = Column(Integer, ForeignKey("Author.author_id", ondelete="RESTRICT"), nullable=False)
    author = relationship("Author", back_populates="books")

Base.metadata.create_all(bind=engine)

@app.post("/author")
def add_author(author : AuthorModel):
    db = session()

    try:
        new_author = Author(name=author.name,country=author.country)
        db.add(new_author)
        db.commit()
        db.refresh(new_author)
        return new_author
    finally:
        db.close()

@app.get("/author")
def get_author():
    db = session()
    try:
        author_list = db.query(Author).all()
        return author_list
    finally:
        db.close()

@app.post("/book")
def add_book(book : BookModel):
    db = session()

    try:
        author_by_id = (db.query(Author).filter(book.author_id==Author.author_id).first())
        if not author_by_id:
            raise HTTPException(
                status_code=404,
                detail="Author not found"
            )
        new_book = Book(book_title=book.book_title,price=book.price,publication_year=book.publication_year,author_id=book.author_id)
        db.add(new_book)
        db.commit()
        db.refresh(new_book)
        return new_book
    finally:
        db.close()

@app.get("/book")
def get_book():
    db = session()
    try:
        book_list = db.query(Book).all()
        return book_list
    finally:
        db.close()

@app.get("/book/{book_id}")
def get_book_by_id(book_id : int):
    db = session()
    try:
        book_by_id = (db.query(Book).filter(Book.book_id==book_id).first())
        if not book_by_id:
            raise HTTPException(
                status_code=404,
                detail="Book not found"
            )
        return book_by_id
    finally:
        db.close()

@app.get("/author/{author_id}")
def get_author_by_id(author_id : int):
    db = session()
    try:
        author_by_id = (db.query(Author).filter(Author.author_id==author_id).first())
        if not author_by_id:
            raise HTTPException(
                status_code=404,
                detail="Author not found"
            )
        return author_by_id
    finally:
        db.close()

@app.get("/author/{author_id}/books", response_model=AuthorOut)
def get_books_by_author(author_id: int):
    db = session()
    try:
        author = (
            db.query(Author)
            .options(joinedload(Author.books))
            .filter(Author.author_id == author_id)
            .first()
        )
        if not author:
            raise HTTPException(status_code=404, detail="Author not found")
        return author
    finally:
        db.close()

@app.delete("/author/{author_id}")
def delete_author(author_id: int):
    db = session()
    try:
        author = db.query(Author).filter(Author.author_id == author_id).first()
        if not author:
            raise HTTPException(
                status_code=404,
                detail=f"Author with id {author_id} not found"
            )

        book_count = db.query(Book).filter(Book.author_id == author_id).count()
        if book_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete author {author_id}: they still have {book_count} book(s). Delete or reassign those books first."
            )

        db.delete(author)
        db.commit()
        return {"message": f"Author {author_id} deleted"}
    finally:
        db.close()






