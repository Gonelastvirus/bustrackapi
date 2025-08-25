from functools import wraps
from flask import session, request, redirect, url_for, flash

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please log in as admin to access this page.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'student_id' not in session:
            flash('Please log in as student to access this page.', 'error')
            return redirect(url_for('student_login'))
        return f(*args, **kwargs)
    return decorated_function

def logout_admin():
    session.pop('admin_id', None)
    session.pop('admin_username', None)

def logout_student():
    session.pop('student_id', None)
    session.pop('student_username', None)
    session.pop('student_name', None)
