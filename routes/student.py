from flask import Blueprint, render_template
from flask_login import login_required

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('student/dashboard.html')
