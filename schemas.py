from pydantic import BaseModel, Field, EmailStr

class StudentCreate(BaseModel):
    email: EmailStr
    name: str = Field(...,min_length=2,max_length=100)
    age: int | None = Field(default=None,ge=1,le=120)
    weight: float | None = Field(default=None,gt=0)
    password: str = Field(...,min_length=5,max_length=100)

class StudentLogin(BaseModel):
    email: EmailStr
    password: str = Field(...,min_length=5,max_length=100)

class StudentUpdate(BaseModel):
    name: str | None = Field(default=None,min_length=2,max_length=100)
    age: int | None = Field(default=None,ge=1,le=120)
    weight: float | None = Field(default=None,gt=0)

class StudentResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    age: int | None
    weight: float | None
    model_config = {
        "from_attributes": True
    }