from datetime import datetime, timedelta
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
import random
from pydantic import EmailStr, BaseModel
from db import get_db
from models import Student


class EmailSchema(BaseModel):
    email: EmailStr


conf = ConnectionConfig(
    MAIL_USERNAME="hassansabri172@gmail.com",
    MAIL_PASSWORD="*****",
    MAIL_FROM="hassansabri172@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="Hassan Solutions",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


async def send_email(email: str,subject: str,message: str):
    email_message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=message,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(email_message)

def generate_otp() -> str:
    return f"{random.randint(100000,999999)}"


def forgot_password_service(request: EmailSchema,background_tasks: BackgroundTasks,db: Session):
    student = (db.query(Student).filter(Student.email == request.email).first())

    if not student:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    otp = generate_otp()

    student.reset_otp = otp
    student.reset_otp_expiry = datetime.now() + timedelta(minutes=10)

    db.commit()
    db.refresh(student)

    subject = "Reset Password OTP"

    message = f"""
    <h3>Password Reset</h3>
    <p>Your OTP is:</p>
    <h2>{otp}</h2>
    <p>This OTP will expire in 10 minutes.</p>
    """

    background_tasks.add_task(
        send_email,
        request.email,
        subject,
        message,
    )

    return {
        "message": "OTP sent successfully."
    }
