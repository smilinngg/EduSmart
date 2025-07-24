from flask import Blueprint, render_template, request, redirect, url_for, flash
# from flask_login import login_required, current_user   # 🔒 Temporarily disabled until auth is ready
from extensions import db
from models import Class, Chapter, Test, Question, TestAttempt, User, StudentClass

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")

# ✅ TEMP fake teacher ID
FAKE_TEACHER_ID = 1


@teacher_bp.route("/dashboard")
# @login_required   # 🔒 Will enable after login is ready
def dashboard():
    classes = Class.query.filter_by(teacher_id=FAKE_TEACHER_ID).all()
    return render_template("teacher/dashboard.html", classes=classes)


# ✅ Create Classroom
@teacher_bp.route("/class/create", methods=["GET", "POST"])
# @login_required
def create_class():
    if request.method == "POST":
        class_name = request.form.get("name")
        join_code = request.form.get("join_code")

        new_class = Class(name=class_name, join_code=join_code, teacher_id=FAKE_TEACHER_ID)
        db.session.add(new_class)
        db.session.commit()

        flash("✅ Classroom created successfully!", "success")
        return redirect(url_for("teacher.dashboard"))

    return render_template("teacher/create_class.html")


# ✅ View Class with Chapters, Tests & Analytics
@teacher_bp.route("/class/<int:class_id>")
# @login_required
def view_class(class_id):
    class_obj = Class.query.get_or_404(class_id)
    enrolled_students = [sc.student for sc in class_obj.students]

    # ✅ Compute analytics for each chapter & test
    for chapter in class_obj.chapters:
        chapter_analytics = get_chapter_analytics(chapter.id)
        chapter.avg_score = chapter_analytics["avg"]
        chapter.lowest_test_name = chapter_analytics["lowest_test"]

        for test in chapter.tests:
            t_analytics = get_test_analytics(test.id)
            test.avg_score = t_analytics["avg"]
            test.highest_score = t_analytics["highest"]
            test.lowest_score = t_analytics["lowest"]

    return render_template(
        "teacher/view_class.html",
        class_obj=class_obj,
        enrolled_students=enrolled_students
    )


# ✅ Create Chapter
@teacher_bp.route("/class/<int:class_id>/create_chapter", methods=["GET", "POST"])
# @login_required
def create_chapter(class_id):
    class_obj = Class.query.get_or_404(class_id)

    if request.method == "POST":
        chapter_name = request.form.get("name")
        new_chapter = Chapter(name=chapter_name, class_id=class_id)
        db.session.add(new_chapter)
        db.session.commit()

        flash("✅ Chapter created!", "success")
        return redirect(url_for("teacher.view_class", class_id=class_id))

    return render_template("teacher/create_chapter.html", class_obj=class_obj)


# ✅ Create Test inside a Chapter
@teacher_bp.route("/chapter/<int:chapter_id>/create_test", methods=["GET", "POST"])
# @login_required
def create_test(chapter_id):
    chapter_obj = Chapter.query.get_or_404(chapter_id)

    if request.method == "POST":
        test_name = request.form.get("name")
        new_test = Test(name=test_name, chapter_id=chapter_id)
        db.session.add(new_test)
        db.session.commit()

        flash("✅ Test created! Now add questions.", "success")
        return redirect(url_for("teacher.manage_test", test_id=new_test.id))

    return render_template("teacher/create_test.html", chapter_obj=chapter_obj)


@teacher_bp.route("/test/<int:test_id>/manage", methods=["GET", "POST"])
# @login_required
def manage_test(test_id):
    test_obj = Test.query.get_or_404(test_id)
    questions = Question.query.filter_by(test_id=test_id).all()

    current_total_marks = sum(q.marks for q in questions if hasattr(q, "marks") and q.marks)

    if request.method == "POST":
        q_text = request.form.get("question_text")
        opt_a = request.form.get("option_a")
        opt_b = request.form.get("option_b")
        opt_c = request.form.get("option_c")
        opt_d = request.form.get("option_d")
        correct_opt = request.form.get("correct_option")
        marks = int(request.form.get("marks") or 1)

        if current_total_marks + marks > test_obj.max_score:
            flash(f"❌ Cannot add question! Total marks would exceed max score ({test_obj.max_score}).", "danger")
            return redirect(url_for("teacher.manage_test", test_id=test_id))

        new_q = Question(
            test_id=test_id,
            text=q_text,
            option_a=opt_a,
            option_b=opt_b,
            option_c=opt_c,
            option_d=opt_d,
            correct_option=correct_opt,
            marks=marks
        )

        db.session.add(new_q)
        db.session.commit()

        flash("✅ Question added successfully!", "success")
        return redirect(url_for("teacher.manage_test", test_id=test_id))

    return render_template(
        "teacher/manage_test.html",
        test_obj=test_obj,
        questions=questions,
        current_total_marks=current_total_marks
    )


# ✅ Delete Question
@teacher_bp.route("/question/<int:question_id>/delete", methods=["POST"])
# @login_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    test_id = question.test_id

    db.session.delete(question)
    db.session.commit()

    flash("❌ Question deleted!", "danger")
    return redirect(url_for("teacher.manage_test", test_id=test_id))


# ✅ Edit Question
@teacher_bp.route("/question/<int:question_id>/edit", methods=["POST"])
# @login_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)

    question.text = request.form.get("edit_text")
    question.option_a = request.form.get("edit_option_a")
    question.option_b = request.form.get("edit_option_b")
    question.option_c = request.form.get("edit_option_c")
    question.option_d = request.form.get("edit_option_d")
    question.correct_option = request.form.get("edit_correct_option")

    db.session.commit()
    flash("✅ Question updated!", "success")
    return redirect(url_for("teacher.manage_test", test_id=question.test_id))


@teacher_bp.route("/test/<int:test_id>/delete", methods=["POST"])
# @login_required
def delete_test(test_id):
    test = Test.query.get_or_404(test_id)
    class_id = test.chapter.class_id  # get before deleting

    db.session.delete(test)
    db.session.commit()

    flash("✅ Test deleted successfully!", "success")
    return redirect(url_for("teacher.view_class", class_id=class_id))


# ✅ View all students in a class with analytics
@teacher_bp.route("/class/<int:class_id>/students")
# @login_required
def class_students(class_id):
    class_obj = Class.query.get_or_404(class_id)

    students = (
        db.session.query(User)
        .join(StudentClass)
        .filter(StudentClass.class_id == class_id, User.role == "student")
        .all()
    )

    student_analytics = []
    for student in students:
        attempts = (
            db.session.query(TestAttempt)
            .join(Test)
            .join(Chapter)
            .filter(
                TestAttempt.student_id == student.id,
                Chapter.class_id == class_id
            )
            .all()
        )

        total_attempts = len(attempts)
        total_score = sum(a.score for a in attempts)
        avg_score = round(total_score / total_attempts, 2) if total_attempts else 0

        weak_topics = []
        strong_topics = []

        for attempt in attempts:
            percentage = (attempt.score / attempt.test.max_score) * 100 if attempt.test.max_score else 0
            if percentage < 50:
                weak_topics.append(attempt.test.name)
            elif percentage >= 80:
                strong_topics.append(attempt.test.name)

        student_analytics.append({
            "student": student,
            "total_attempts": total_attempts,
            "avg_score": avg_score,
            "weak_topics": weak_topics,
            "strong_topics": strong_topics
        })

    return render_template(
        "teacher/class_students.html",
        class_obj=class_obj,
        student_analytics=student_analytics
    )


# ✅ Analytics helpers
def get_test_analytics(test_id):
    attempts = TestAttempt.query.filter_by(test_id=test_id).all()
    if not attempts:
        return {"avg": None, "highest": None, "lowest": None, "count": 0}

    scores = [a.score for a in attempts]
    return {
        "avg": round(sum(scores) / len(scores), 2),
        "highest": max(scores),
        "lowest": min(scores),
        "count": len(scores)
    }


def get_chapter_analytics(chapter_id):
    tests = Test.query.filter_by(chapter_id=chapter_id).all()
    if not tests:
        return {"avg": None, "lowest_test": None, "total_tests": 0}

    all_scores = []
    test_scores = {}
    for test in tests:
        t_analytics = get_test_analytics(test.id)
        if t_analytics["avg"] is not None:
            all_scores.append(t_analytics["avg"])
            test_scores[test.name] = t_analytics["avg"]

    if not all_scores:
        return {"avg": None, "lowest_test": None, "total_tests": len(tests)}

    lowest_test = min(test_scores, key=test_scores.get)

    return {
        "avg": round(sum(all_scores) / len(all_scores), 2),
        "lowest_test": lowest_test,
        "total_tests": len(tests)
    }
