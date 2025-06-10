import os
from datetime import datetime
from flask import Flask, request, redirect, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mysqldb import MySQL

from models import (
    User, get_user_by_email, get_user_by_id, create_user,
    get_all_students, get_student_by_id, update_student, delete_student_by_id,
    get_grades_by_student, get_all_grades, get_grade_by_id, add_grade_record,
    update_grade_record, delete_grade_by_id, get_all_absences, get_absence_by_id,
    add_absence_record, update_absence_record, delete_absence_by_id, insert_student_record,
    student_exists
)

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'AlekFM6644'
app.config['MYSQL_DB'] = 'diary'
mysql = MySQL(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

app.debug = True

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(mysql, user_id)

@app.route('/')
def index():
    return 'Добре дошъл в електронния дневник!'

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    data = request.form
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()

    if not username or not email or not password:
        return 'Липсва информация.', 400

    try:
        create_user(mysql, username, email, password)
    except Exception as e:
        return f'Грешка при регистрация: {str(e)}', 500

    return 'Успешна регистрация.'

@app.route('/login', methods=['POST'])
def login():
    data = request.form
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role')

    if role not in ('user', 'admin'):
        return 'Невалидна роля.', 400

    user = get_user_by_email(mysql, email)
    if user and user.password == password and user.role == role:
        login_user(user)
        return f'Успешен вход като {role}.'
    return 'Грешен имейл, парола или роля.', 401

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return 'Излязохте успешно.'

@app.route('/students', methods=['GET'])
@login_required
def students():
    if current_user.role != 'admin':
        return 'Забранен достъп.', 403
    try:
        students = get_all_students(mysql)
        return jsonify(students)
    except Exception as e:
        return str(e), 500

@app.route('/students/add', methods=['POST'])
@login_required
def add_student():
    if current_user.role != 'admin':
        return 'Забранен достъп.', 403
    data = request.form
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    cls = data.get('class', '').strip()
    dob_str = data.get('date_of_birth', '').strip()
    dob = None
    if dob_str:
        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except:
            return 'Невалидна дата.', 400
    try:
        insert_student_record(mysql, first_name, last_name, cls, dob)
        return 'Ученикът е добавен.'
    except Exception as e:
        return str(e), 500

@app.route('/grades', methods=['GET'])
@login_required
def grades():
    if current_user.role != 'user':
        return 'Забранен достъп.', 403
    try:
        grades = get_grades_by_student(mysql, current_user.id)
        return jsonify(grades)
    except Exception as e:
        return str(e), 500

@app.route('/grades/manage', methods=['GET'])
@login_required
def grades_manage():
    if current_user.role != 'admin':
        return 'Забранен достъп.', 403
    try:
        grades = get_all_grades(mysql)
        return jsonify(grades)
    except Exception as e:
        return str(e), 500

@app.route('/grades/add', methods=['POST'])
@login_required
def add_grade():
    if current_user.role != 'admin':
        return 'Забранен достъп.', 403
    data = request.form
    sid = int(data.get('student_id'))
    subject = data.get('subject', '')
    grade = data.get('grade', '')
    date_given = datetime.strptime(data.get('date_given'), '%Y-%m-%d').date()
    if not student_exists(mysql, sid):
        return 'Ученикът не съществува.', 400
    try:
        add_grade_record(mysql, sid, subject, grade, date_given, current_user.id)
        return 'Оценката е добавена.'
    except Exception as e:
        return str(e), 500

@app.route('/absences', methods=['GET'])
@login_required
def absences():
    if current_user.role != 'user':
        return 'Забранен достъп.', 403
    try:
        absences = get_all_absences(mysql)
        filtered = [a for a in absences if a['student_id'] == current_user.id]
        return jsonify(filtered)
    except Exception as e:
        return str(e), 500

@app.route('/absences/manage', methods=['GET'])
@login_required
def absences_manage():
    if current_user.role != 'admin':
        return 'Забранен достъп.', 403
    try:
        absences = get_all_absences(mysql)
        return jsonify(absences)
    except Exception as e:
        return str(e), 500

@app.route('/absences/add', methods=['POST'])
@login_required
def add_absence():
    if current_user.role != 'admin':
        return 'Забранен достъп.', 403
    data = request.form
    sid = int(data.get('student_id'))
    date = datetime.strptime(data.get('date_absent'), '%Y-%m-%d').date()
    justified = data.get('is_justified') == 'on'
    try:
        add_absence_record(mysql, sid, date, justified, current_user.id)
        return 'Отсъствието е добавено.'
    except Exception as e:
        return str(e), 500

@app.route('/students/edit/<int:student_id>', methods=['POST'])
@login_required
def edit_student(student_id):
    if current_user.role != 'admin':
        return 'Забранен достъп.', 403
    data = request.form
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    cls = data.get('class', '').strip()
    dob_str = data.get('date_of_birth', '').strip()
    dob = None
    if dob_str:
        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except:
            return 'Невалидна дата.', 400
    try:
        update_student(mysql, student_id, first_name, last_name, cls, dob)
        return 'Ученикът е обновен.'
    except Exception as e:
        return str(e), 500

@app.route('/students/delete/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    if current_user.role != 'admin':
        return 'Забранен достъп.', 403
    try:
        delete_student_by_id(mysql, student_id)
        return 'Ученикът е изтрит.'
    except Exception as e:
        return str(e), 500

@app.route('/grades/edit/<int:grade_id>', methods=['POST'])
@login_required
def edit_grade(grade_id):
    if current_user.role != 'admin':
        return 'Забранен достъп.', 403
    data = request.form
    sid = int(data.get('student_id'))
    subject = data.get('subject', '').strip()
    grade_val = data.get('grade', '').strip()
    date_given = datetime.strptime(data.get('date_given'), '%Y-%m-%d').date()
    if not student_exists(mysql, sid):
        return 'Ученикът не съществува.', 400
    try:
        update_grade_record(mysql, grade_id, sid, subject, grade_val, date_given, current_user.id)
        return 'Оценката е обновена.'
    except Exception as e:
        return str(e), 500

@app.route('/grades/delete/<int:grade_id>', methods=['POST'])
@login_required
def delete_grade(grade_id):
    if current_user.role != 'admin':
        return 'Забранен достъп.', 403
    try:
        delete_grade_by_id(mysql, grade_id)
        return 'Оценката е изтрита.'
    except Exception as e:
        return str(e), 500

@app.route('/absences/edit/<int:absence_id>', methods=['POST'])
@login_required
def edit_absence(absence_id):
    if current_user.role != 'admin':
        return 'Забранен достъп.', 403
    data = request.form
    sid = int(data.get('student_id'))
    date_absent = datetime.strptime(data.get('date_absent'), '%Y-%m-%d').date()
    justified = data.get('is_justified') == 'on'
    if not student_exists(mysql, sid):
        return 'Ученикът не съществува.', 400
    try:
        update_absence_record(mysql, absence_id, sid, date_absent, justified, current_user.id)
        return 'Отсъствието е обновено.'
    except Exception as e:
        return str(e), 500

@app.route('/absences/delete/<int:absence_id>', methods=['POST'])
@login_required
def delete_absence(absence_id):
    if current_user.role != 'admin':
        return 'Забранен достъп.', 403
    try:
        delete_absence_by_id(mysql, absence_id)
        return 'Отсъствието е изтрито.'
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=app.debug)
