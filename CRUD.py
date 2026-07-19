from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import Student
from schemas import StudentUpdate

ADMIN_EMAIL = "masoombacha556677@gmail.com"


def get_all(db: Session, user: Student):
    if user.email != ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Access denied")
    return db.query(Student).all()


def get_data_by_id(id: int, db: Session, user: Student):
    student = db.query(Student).filter(Student.id == id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if student.id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return student


def update_data_by_email(db: Session, data: StudentUpdate, user: Student):
    student = db.query(Student).filter(Student.id == user.id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(student, key, value)

    db.commit()
    db.refresh(student)

    return student


def delete_student(db: Session, student_id: int, user: Student):
    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if student.id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(student)
    db.commit()

    return {"message": "Student deleted successfully."}


def get_students(db: Session, sort_by: str, order: str, user: Student):
    if user.email != ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Access denied")

    column = getattr(Student, sort_by, None)

    if not column:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid order")

    return (
        db.query(Student)
        .order_by(column.desc() if order == "desc" else column.asc())
        .all()
    )