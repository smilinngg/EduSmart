# routes/student.py

from flask import Blueprint, render_template, request, redirect, flash, url_for
from models import db, Class, StudentClass, Test, Question, TestAttempt
from datetime import datetime
import json  # ✅ to parse options if stored as JSON

student_bp = Blueprint("student", __name__, url_prefix="/student")


# ================================
# ✅ STUDENT DASHBOARD
# ================================
@student_bp.route("/dashboard")
def dashboard():
    dummy_student_id = 1  

    enrolled_classes = (
        db.session.query(Class)
        .join(StudentClass, StudentClass.class_id == Class.id)
        .filter(StudentClass.student_id == dummy_student_id)
        .all()
    )
    return render_template("student/dashboard.html", classes=enrolled_classes)


# ================================
# ✅ JOIN CLASS BY CODE
# ================================
@student_bp.route("/join_class", methods=["POST"])
def join_class():
    dummy_student_id = 1  

    join_code = request.form.get("join_code").strip()
    class_obj = Class.query.filter_by(join_code=join_code).first()

    if not class_obj:
        flash("Invalid join code", "danger")
        return redirect(url_for("student.dashboard"))

    already_joined = StudentClass.query.filter_by(
        student_id=dummy_student_id, class_id=class_obj.id
    ).first()

    if already_joined:
        flash(f"You are already enrolled in {class_obj.name}", "info")
    else:
        new_enrollment = StudentClass(student_id=dummy_student_id, class_id=class_obj.id)
        db.session.add(new_enrollment)
        db.session.commit()
        flash(f"Successfully joined {class_obj.name}", "success")

    return redirect(url_for("student.dashboard"))


# ================================
# ✅ CLASS DETAILS VIEW
# ================================
@student_bp.route("/class/<int:class_id>")
def class_detail(class_id):
    class_obj = Class.query.get_or_404(class_id)

    dummy_student_id = 1  

    is_enrolled = StudentClass.query.filter_by(
        student_id=dummy_student_id, class_id=class_id
    ).first()
    if not is_enrolled:
        flash("You are not enrolled in this class", "danger")
        return redirect(url_for("student.dashboard"))

    chapters = class_obj.chapters
    assignments = class_obj.assignments

    return render_template(
        "student/class_detail.html",
        class_obj=class_obj,
        chapters=chapters,
        assignments=assignments,
    )


# ================================
# ✅ TEST FLOW
# ================================
@student_bp.route("/start_test/<int:test_id>/<int:question_index>", methods=["GET", "POST"])
def start_test(test_id, question_index=0):
    """Show one question at a time with proper navigation + options."""

    test = Test.query.get_or_404(test_id)

    # ✅ 1. Check time validity
    now = datetime.utcnow()
    if test.start_time and now < test.start_time:
        flash("This test has not started yet!", "warning")
        return redirect(url_for("student.class_detail", class_id=test.chapter.class_id))
    if test.end_time and now > test.end_time:
        flash("This test is already closed!", "danger")
        return redirect(url_for("student.class_detail", class_id=test.chapter.class_id))

    # ✅ 2. Get all questions
    questions = test.questions
    total_questions = len(questions)

    if total_questions == 0:
        flash("No questions available for this test!", "info")
        return redirect(url_for("student.class_detail", class_id=test.chapter.class_id))

    # ✅ 3. Validate index
    if question_index < 0 or question_index >= total_questions:
        flash("Invalid question index", "danger")
        return redirect(url_for("student.start_test", test_id=test_id, question_index=0))

    current_question = questions[question_index]

    # ✅ Build options list from available fields
    options_list = []
    if hasattr(current_question, "option_a") and current_question.option_a:
        options_list.append(current_question.option_a)
    if hasattr(current_question, "option_b") and current_question.option_b:
        options_list.append(current_question.option_b)
    if hasattr(current_question, "option_c") and current_question.option_c:
        options_list.append(current_question.option_c)
    if hasattr(current_question, "option_d") and current_question.option_d:
        options_list.append(current_question.option_d)

    # ✅ 4. Handle submission
    if request.method == "POST":
        selected_option = request.form.get("selected_option")

        if selected_option:
            flash(f"You selected {selected_option} for Q{question_index+1}", "info")

        # Move to next question
        if question_index + 1 < total_questions:
            return redirect(url_for("student.start_test", test_id=test_id, question_index=question_index + 1))
        else:
            flash("🎉 You finished the test! (Submit feature coming soon)", "success")
            return redirect(url_for("student.dashboard"))

    # ✅ 5. Render the question page
    return render_template(
        "student/start_test.html",
        test=test,
        current_question=current_question,
        current_index=question_index,
        total_questions=total_questions,
        options_list=options_list
    )
