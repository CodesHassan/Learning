import os, jwt, uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Request, Response
from sqlalchemy.orm import Session
from models import Student, RefreshToken
from controller import verify_password, get_password_hash

def create_access_token(payload):
    return jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))

def create_refresh_token(payload):
    return jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))


def login(std, request: Request, response: Response, db):

    student = db.query(Student).filter_by(email=std.email).first()

    if not student or not verify_password(std.password, student.hash_password):
        raise HTTPException(401, "Invalid email or password")

    session_id = str(uuid.uuid4())

    access_token = create_access_token({
        "_id": student.id,
        "email": student.email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    })

    refresh_token = create_refresh_token({
        "_id": student.id,
        "email": student.email,
        "session_id": session_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    })

    db.add(RefreshToken(
        session_id=session_id,
        user_id=student.id,
        token_hash=get_password_hash(refresh_token),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    ))

    db.commit()

    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=604800
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }



import jwt
from datetime import datetime, timedelta, timezone

def refresh(request: Request, response: Response, db):

    token = request.cookies.get("refresh_token")

    if not token:
        raise HTTPException(401, "Refresh token missing")

    try:
        payload = jwt.decode(
            token,
            os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("ALGORITHM")]
        )
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid refresh token")

    refresh = db.query(RefreshToken).filter_by(
        session_id=payload["session_id"]
    ).first()

    if not refresh:
        raise HTTPException(401, "Session not found")

    if not verify_password(token, refresh.token_hash):
        raise HTTPException(401, "Invalid refresh token")

    if refresh.expires_at < datetime.now(timezone.utc):
        db.delete(refresh)
        db.commit()
        raise HTTPException(401, "Refresh token expired")

    student = db.query(Student).filter_by(id=payload["_id"]).first()

    access_token = create_access_token({
        "_id": student.id,
        "email": student.email,
        "exp": datetime.now(timezone.utc) + timedelta(
            minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
        )
    })

    new_refresh_token = create_refresh_token({
        "_id": student.id,
        "email": student.email,
        "session_id": refresh.session_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    })

    refresh.token_hash = get_password_hash(new_refresh_token)
    refresh.expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    db.commit()

    response.set_cookie(
        "refresh_token",
        new_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=604800
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


from fastapi import Request, Response, HTTPException

def logout(request: Request, response: Response, db):

    token = request.cookies.get("refresh_token")

    if not token:
        raise HTTPException(401, "Refresh token missing")

    try:
        payload = jwt.decode(
            token,
            os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("ALGORITHM")]
        )
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid refresh token")

    refresh = db.query(RefreshToken).filter_by(
        session_id=payload["session_id"]
    ).first()

    if refresh:
        db.delete(refresh)
        db.commit()

    response.delete_cookie("refresh_token")

    return {"message": "Logout successful"}



def logout_all(user: Student, response: Response, db: Session):

    db.query(RefreshToken).filter_by(
        user_id=user.id
    ).delete()

    db.commit()

    response.delete_cookie("refresh_token")

    return {"message": "Logged out from all devices"}