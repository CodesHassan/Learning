import os
import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, BackgroundTasks
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from db import get_db
from models import Student
from schemas import StudentCreate, StudentLogin
from email_helper import send_email
from verifyToken import verify_token

password_hash = PasswordHash.recommended()


def get_password_hash(password: str):
    return password_hash.hash(password)


def verify_password(password: str, hashed: str):
    return password_hash.verify(password, hashed)


def register(std: StudentCreate, background_tasks: BackgroundTasks, db: Session):
    if db.query(Student).filter_by(email=std.email).first():
        raise HTTPException(400, "User already exists")

    student = Student(
        email=std.email,
        name=std.name,
        age=std.age,
        weight=std.weight,
        hash_password=get_password_hash(std.password),
    )

    db.add(student)
    db.commit()
    db.refresh(student)

    background_tasks.add_task(
        send_email,
        student.email,
        "Registration Successful",
        f"<h2>Welcome {student.name}</h2><p>Your account has been created successfully.</p>",
    )

    return student


def login(std: StudentLogin, db: Session):
    student = db.query(Student).filter_by(email=std.email).first()

    if not student or not verify_password(std.password, student.hash_password):
        raise HTTPException(401, "Invalid email or password")

    token = jwt.encode(
        {
            "_id": student.id,
            "email": student.email,
            "exp": datetime.now()
            + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))),
        },
        os.getenv("SECRET_KEY"),
        algorithm=os.getenv("ALGORITHM"),
    )

    return {"access_token": token, "token_type": "bearer"}


def is_auth(
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    student = db.query(Student).filter_by(
        id=payload["_id"],
        email=payload["email"],
    ).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return student