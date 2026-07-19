from datetime import datetime

from fastapi import BackgroundTasks, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from controller import get_password_hash
from email_helper import send_email
from models import Student


class ChangePasswordSchema(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


def change_password(
    request: ChangePasswordSchema,
    background_tasks: BackgroundTasks,
    db: Session,
):
    student = (
        db.query(Student)
        .filter(Student.email == request.email)
        .first()
    )

    if not student:
        raise HTTPException(404, "User not found")

    if student.reset_otp is None:
        raise HTTPException(400, "No active OTP found")

    if student.reset_otp != request.otp:
        raise HTTPException(400, "Invalid OTP")

    if (
        student.reset_otp_expiry is None
        or datetime.now() > student.reset_otp_expiry
    ):
        student.reset_otp = None
        student.reset_otp_expiry = None
        db.commit()
        raise HTTPException(400, "OTP expired")

    student.hash_password = get_password_hash(request.new_password)
    student.reset_otp = None
    student.reset_otp_expiry = None

    db.commit()

    background_tasks.add_task(
        send_email,
        request.email,
        "Password Changed Successfully",
        """
        <h2>Password Changed</h2>
        <p>Your password has been changed successfully.</p>
        """,
    )

    return {"message": "Password changed successfully."}