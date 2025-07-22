from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)  # plain for now
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'teacher'

    # Relationships
    classes_taught = db.relationship("Class", backref="teacher", lazy=True)  # only for teachers
    test_attempts = db.relationship("TestAttempt", backref="student", lazy=True)  # only for students

    def __repr__(self):
        return f"<User {self.name} ({self.role})>"


class Class(db.Model):
    __tablename__ = "class"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    join_code = db.Column(db.String(10), unique=True, nullable=False)

    # Foreign key
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Relationships
    students = db.relationship("StudentClass", backref="class_obj", lazy=True, cascade="all, delete-orphan")
    chapters = db.relationship("Chapter", backref="class_obj", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Class {self.name} | Teacher ID {self.teacher_id}>"


class StudentClass(db.Model):
    __tablename__ = "student_class"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("class.id"), nullable=False)

    def __repr__(self):
        return f"<StudentClass student={self.student_id} class={self.class_id}>"


class Chapter(db.Model):
    __tablename__ = "chapter"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("class.id"), nullable=False)

    # Relationship
    tests = db.relationship("Test", backref="chapter", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Chapter {self.name} in Class {self.class_id}>"


class Test(db.Model):
    __tablename__ = "test"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey("chapter.id"), nullable=False)

    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    max_score = db.Column(db.Integer, default=100)

    # Relationship
    attempts = db.relationship("TestAttempt", backref="test", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Test {self.name} | Chapter {self.chapter_id}>"


class TestAttempt(db.Model):
    __tablename__ = "test_attempt"

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("test.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    score = db.Column(db.Float, default=0.0)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Attempt student={self.student_id} test={self.test_id} score={self.score}>"
