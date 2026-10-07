from pydantic import BaseModel,Field,ConfigDict,EmailStr

class AuthorModel(BaseModel):
    name : str = Field(min_length = 3,max_length=20)
    country : str 

class BookModel(BaseModel):
    book_title  : str
    price : float 
    author_id : int
    publication_year : int 
    

class BookOut(BaseModel):
    book_id: int
    book_title: str
    price: float
    publication_year: int
    owner_id : int
    model_config = ConfigDict(from_attributes=True)

class AuthorOut(BaseModel):
    author_id: int
    name: str
    country: str | None = None
    books: list[BookOut] = []
    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    email : EmailStr
    password : str = Field(min_length=8,max_length=128)

class UserResponse(BaseModel):
    user_id : int
    email : str
    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
