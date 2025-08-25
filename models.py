from extensions import db
from flask_login import UserMixin
from datetime import datetime

# ==========================
# ✅ USER MODEL
# ==========================
class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'teacher'

    # Relationships
    classes_taught = db.relationship("Class", backref="teacher", lazy=True)
    test_attempts = db.relationship("TestAttempt", backref="student", lazy=True)
    assignment_submissions = db.relationship("AssignmentSubmission", backref="student", lazy=True)
    enrolled_classes = db.relationship("StudentClass", back_populates="student", lazy=True)

    def __repr__(self):
        return f"<User {self.name} ({self.role})>"


# ==========================
# ✅ CLASS MODEL
# ==========================
class Class(db.Model):
    __tablename__ = "class"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    join_code = db.Column(db.String(10), unique=True, nullable=False)

    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Relationships
    students = db.relationship("StudentClass", back_populates="class_obj", lazy=True, cascade="all, delete-orphan")
    chapters = db.relationship("Chapter", backref="class_obj", lazy=True, cascade="all, delete-orphan")
    assignments = db.relationship("Assignment", backref="class_obj", lazy=True, cascade="all, delete-orphan")

    @property
    def enrolled_users(self):
        """Return a list of User objects enrolled in this class"""
        return [sc.student for sc in self.students]

    def __repr__(self):
        return f"<Class {self.name} | Teacher ID {self.teacher_id}>"


# ✅ Many-to-Many for Students in a Class
class StudentClass(db.Model):
    __tablename__ = "student_class"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("class.id"), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)  # ✅ WHEN student joined

    # ✅ FIX: Add relationships for easy access
    student = db.relationship("User", back_populates="enrolled_classes", lazy=True)
    class_obj = db.relationship("Class", back_populates="students", lazy=True)

    def __repr__(self):
        return f"<StudentClass student={self.student_id} class={self.class_id}>"


# ==========================
# ✅ CHAPTER MODEL
# ==========================
class Chapter(db.Model):
    __tablename__ = "chapter"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("class.id"), nullable=False)

    tests = db.relationship("Test", backref="chapter", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Chapter {self.name} in Class {self.class_id}>"


# ==========================
# ✅ TEST MODEL (TIME-BOUND)
# ==========================
class Test(db.Model):
    __tablename__ = "test"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey("chapter.id"), nullable=False)

    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, default=30)  # ✅ Added test duration
    max_score = db.Column(db.Integer, default=100)

    # Relationships
    questions = db.relationship("Question", backref="test", lazy=True, cascade="all, delete-orphan")
    attempts = db.relationship("TestAttempt", backref="test", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Test {self.name} | Chapter {self.chapter_id}>"


# ✅ STUDENT ATTEMPTS WITH ANALYTICS
class TestAttempt(db.Model):
    __tablename__ = "test_attempt"

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("test.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    score = db.Column(db.Float, default=0.0)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ Analytics fields
    total_questions = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    wrong_answers = db.Column(db.Integer, default=0)
    time_taken = db.Column(db.Integer, default=0)  # ✅ seconds taken to complete

    topic_performance = db.Column(db.JSON, nullable=True)  
    # Example: {"Strong": ["Topic A"], "Weak": ["Topic B"]}

    answers = db.relationship("StudentAnswer", backref="attempt", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Attempt student={self.student_id} test={self.test_id} score={self.score}>"


# ✅ PER-QUESTION ANSWERS FOR DETAILED ANALYSIS
class StudentAnswer(db.Model):
    __tablename__ = "student_answer"

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("test_attempt.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)

    selected_option = db.Column(db.String(1), nullable=True)  # "A", "B", "C", "D"
    is_correct = db.Column(db.Boolean, default=False)
    time_spent = db.Column(db.Integer, default=0)  # seconds spent on question

    def __repr__(self):
        return f"<StudentAnswer question={self.question_id} correct={self.is_correct}>"


# ✅ QUESTIONS WITH TOPICS & DIFFICULTY
class Question(db.Model):
    __tablename__ = "question"

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("test.id"), nullable=False)

    text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)  # "A", "B", "C", or "D"
    marks = db.Column(db.Integer, default=1)

    # ✅ Future fields for analytics
    topic = db.Column(db.String(100), nullable=True)         # e.g. "Computer Vision Basics"
    difficulty = db.Column(db.String(20), nullable=True)     # e.g. "Easy", "Medium", "Hard"

    def __repr__(self):
        return f"<Question {self.text[:20]}...>"


# ==========================
# ✅ ASSIGNMENTS
# ==========================
class Assignment(db.Model):
    __tablename__ = "assignment"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)

    class_id = db.Column(db.Integer, db.ForeignKey("class.id"), nullable=False)

    # Submissions
    submissions = db.relationship("AssignmentSubmission", backref="assignment", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Assignment {self.title}>"


class AssignmentSubmission(db.Model):
    __tablename__ = "assignment_submission"

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey("assignment.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Float, default=0.0)
    feedback = db.Column(db.Text, nullable=True)
    improvement_score = db.Column(db.Float, default=0.0)  # ✅ Track post-followup improvement

    def __repr__(self):
        return f"<AssignmentSubmission student={self.student_id} assignment={self.assignment_id}>"


# ==========================
# ✅ STUDENT ANALYTICS (AGGREGATED)
# ==========================
class StudentAnalytics(db.Model):
    __tablename__ = "student_analytics"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("class.id"), nullable=False)

    overall_score = db.Column(db.Float, default=0.0)
    weak_topics = db.Column(db.JSON, nullable=True)    # e.g. ["Math Basics", "Image Filters"]
    strong_topics = db.Column(db.JSON, nullable=True)  # e.g. ["CNNs", "Object Detection"]

    # ✅ Progress tracking over time
    history = db.Column(db.JSON, nullable=True)  
    # Example: [{"date": "2025-07-01", "score": 65}, {"date": "2025-07-15", "score": 75}]

    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Analytics student={self.student_id} class={self.class_id}>"
