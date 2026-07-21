import os, jwt, hashlib
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Request, Response
from sqlalchemy.orm import Session
from controller import verify_password
from models import Student, RefreshToken
from schemas import StudentLogin


def create_access_token(payload):
    return jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))

def create_refresh_token(payload):
    return jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))


def login(std: StudentLogin, request: Request, response: Response, db: Session):
    student = db.query(Student).filter_by(email=std.email).first()
    if not student or not verify_password(std.password, student.hash_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token({"_id": student.id, "email": student.email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))})

    refresh_token = create_refresh_token({"_id": student.id, "email": student.email,
        "exp": datetime.now(timezone.utc) + timedelta(days=2)})

    db.add(RefreshToken(
        user_id=student.id,
        token_hash=hashlib.sha256(refresh_token.encode()).hexdigest(),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        expires_at=datetime.now(timezone.utc) + timedelta(days = 2)
    ))
    db.commit()

    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800)
    return {"access_token": access_token, "token_type": "bearer"}


def refresh(request: Request, response: Response, db: Session):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    refresh = db.query(RefreshToken).filter_by(
        token_hash=hashlib.sha256(token.encode()).hexdigest()
    ).first()

    if not refresh or refresh.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
    student = db.query(Student).filter_by(id=payload["_id"]).first()

    access_token = create_access_token({"_id": student.id, "email": student.email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))})

    new_refresh_token = create_refresh_token({"_id": student.id, "email": student.email,
        "exp": datetime.now(timezone.utc) + timedelta(days = 2)})

    refresh.token_hash = hashlib.sha256(new_refresh_token.encode()).hexdigest()
    refresh.expires_at = datetime.now(timezone.utc) + timedelta(days = 2)
    db.commit()

    response.set_cookie("refresh_token", new_refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800)
    return {"access_token": access_token, "token_type": "bearer"}