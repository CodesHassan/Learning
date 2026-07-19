from fastapi import FastAPI, Depends, BackgroundTasks, Request, Query
from sqlalchemy.orm import Session
import time

import CRUD, controller, models, schemas
from db import Base, engine, get_db
from verifyToken import verify_token
from rate_limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler
from email_helper import EmailSchema, forgot_password_service
from ChangePswd import ChangePasswordSchema, change_password
from controller import is_auth as get_current_user

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.middleware("http")
async def request_log(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    print(time.time() - start)
    return response


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.post("/register", response_model=schemas.StudentResponse)
def register(std: schemas.StudentCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return controller.register(std, background_tasks, db)


@app.post("/login")
def login(std: schemas.StudentLogin, db: Session = Depends(get_db)):
    return controller.login(std, db)


@app.post("/forgot-password")
def forgot_password(request: EmailSchema, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return forgot_password_service(request, background_tasks, db)


@app.put("/change-password")
def change_password_endpoint(request: ChangePasswordSchema, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return change_password(request, background_tasks, db)


@app.get("/students/", response_model=list[schemas.StudentResponse])
def get_all_students(db: Session = Depends(get_db), user: models.Student = Depends(get_current_user)):
    return CRUD.get_all(db, user)


@app.get("/student/{id}", response_model=schemas.StudentResponse)
@limiter.limit("2/minute")
def get_student_by_id(request: Request, id: int, db: Session = Depends(get_db), user: models.Student = Depends(get_current_user)):
    return CRUD.get_data_by_id(id, db, user)


@app.put("/edit-student", response_model=schemas.StudentResponse)
def edit_student(std: schemas.StudentUpdate, db: Session = Depends(get_db), user: models.Student = Depends(get_current_user)):
    return CRUD.update_data_by_email(db, std, user)


@app.delete("/students/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db), user: models.Student = Depends(get_current_user)):
    return CRUD.delete_student(db, student_id, user)


@app.get("/sorted_students", response_model=list[schemas.StudentResponse])
def sorted_students(
    sort_by: str = Query("age", pattern="^(age|weight)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    user: models.Student = Depends(get_current_user),
):
    return CRUD.get_students(db, sort_by, order, user)