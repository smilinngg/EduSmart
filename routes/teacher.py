from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Class, Chapter, Test, Question

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")

# ✅ TEMP fake teacher ID
FAKE_TEACHER_ID = 1


@teacher_bp.route("/dashboard")
def dashboard():
    classes = Class.query.filter_by(teacher_id=FAKE_TEACHER_ID).all()
    return render_template("teacher/dashboard.html", classes=classes)


# ✅ Create Classroom
@teacher_bp.route("/class/create", methods=["GET", "POST"])
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


# ✅ View Class & Chapters
@teacher_bp.route("/class/<int:class_id>")
def view_class(class_id):
    class_obj = Class.query.get_or_404(class_id)
    return render_template("teacher/view_class.html", class_obj=class_obj)


# ✅ Create Chapter
@teacher_bp.route("/class/<int:class_id>/create_chapter", methods=["GET", "POST"])
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
def manage_test(test_id):
    test_obj = Test.query.get_or_404(test_id)
    questions = Question.query.filter_by(test_id=test_id).all()

    # Calculate current total marks
    current_total_marks = sum(q.marks for q in questions if hasattr(q, "marks") and q.marks)

    if request.method == "POST":
        q_text = request.form.get("question_text")
        opt_a = request.form.get("option_a")
        opt_b = request.form.get("option_b")
        opt_c = request.form.get("option_c")
        opt_d = request.form.get("option_d")
        correct_opt = request.form.get("correct_option")
        marks = int(request.form.get("marks") or 1)

        # ✅ Validate total marks <= test.max_score
        if current_total_marks + marks > test_obj.max_score:
            flash(f"Cannot add question! Total marks would exceed max score ({test_obj.max_score}).", "danger")
            return redirect(url_for("teacher.manage_test", test_id=test_id))

        new_q = Question(
            test_id=test_id,
            text=q_text,
            option_a=opt_a,
            option_b=opt_b,
            option_c=opt_c,
            option_d=opt_d,
            correct_option=correct_opt,
        )
        # ✅ Add marks field if not already in model
        new_q.marks = marks  

        db.session.add(new_q)
        db.session.commit()

        flash("Question added successfully!", "success")
        return redirect(url_for("teacher.manage_test", test_id=test_id))

    return render_template(
        "teacher/manage_test.html",
        test_obj=test_obj,
        questions=questions,
        current_total_marks=current_total_marks
    )



# ✅ Delete Question
@teacher_bp.route("/question/<int:question_id>/delete", methods=["POST"])
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    test_id = question.test_id

    db.session.delete(question)
    db.session.commit()

    flash("❌ Question deleted!", "danger")
    return redirect(url_for("teacher.manage_test", test_id=test_id))


# ✅ Edit Question
@teacher_bp.route("/question/<int:question_id>/edit", methods=["POST"])
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
def delete_test(test_id):
    test = Test.query.get_or_404(test_id)
    
    # ✅ Get class_id BEFORE deletion
    class_id = test.chapter.class_id  

    db.session.delete(test)
    db.session.commit()

    flash("✅ Test deleted successfully!", "success")
    return redirect(url_for("teacher.view_class", class_id=class_id))


