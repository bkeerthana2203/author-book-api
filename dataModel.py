from pydantic import BaseModel,Field,ConfigDict

class AuthorModel(BaseModel):
    name : str = Field(min_length = 3,max_length=20)
    country : str | None = None

class BookModel(BaseModel):
    book_title  : str
    price : float 
    author_id : int
    publication_year : int 

class BookOut(BaseModel):
    book_id: int
    book_title: str
    price: float
    publication_year: int | None = None
    model_config = ConfigDict(from_attributes=True)

class AuthorOut(BaseModel):
    author_id: int
    name: str
    country: str | None = None
    books: list[BookOut] = []
    model_config = ConfigDict(from_attributes=True)
