import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager, login_user, login_required, logout_user, current_user
)
from flask_mysqldb import MySQL
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash

from models import (
    User, get_user_by_email, get_user_by_id, create_user,
    get_all_students, get_student_by_id, insert_student_record,
    update_student, delete_student_by_id,
    get_grades_by_student, get_all_grades, get_grade_by_id,
    add_grade_record, update_grade_record, delete_grade_by_id,
    get_all_absences, get_absence_by_id, add_absence_record,
    update_absence_record, delete_absence_by_id,
    student_exists
)

# ─── Конфигурация и инциализация ─────────────────────────────────────────────────────────────────────────

app = Flask(__name__)

# --- CSRF защита (Flask-WTF) ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change_me_to_some_random_value')
csrf = CSRFProtect(app)

# --- MySQL настройки (вече имаш работеща БД 'diary') ---
app.config['MYSQL_HOST']     = 'localhost'
app.config['MYSQL_PORT']     = 3306
app.config['MYSQL_USER']     = 'root'
app.config['MYSQL_PASSWORD'] = 'AlekFM6644'
app.config['MYSQL_DB']       = 'diary'
mysql = MySQL(app)

# --- Flask-Login ---
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# debug=False по подразбиране (production)
app.debug = False


@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(mysql, user_id)


# ─── РУТИНИ (routes) ──────────────────────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        # Валидация: задължителни полета
        if not username or not email or not password:
            flash("Моля, попълнете всички полета.", 'error')
            return render_template('signup.html')

        # Хешираме паролата
        hashed_pw = generate_password_hash(password)

        # Опит за вкарване в БД (проверка за дублиран имейл)
        try:
            create_user(mysql, username, email, hashed_pw)
        except mysql.connection.IntegrityError:
            flash("Имейлът вече е регистриран.", 'error')
            return render_template('signup.html')
        except Exception as e:
            flash(f"Възникна грешка: {str(e)}", 'error')
            return render_template('signup.html')

        flash("Успешна регистрация. Можете да влезете.", 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        selected_role = request.form.get('role')

        # Валидация: роля трябва да бъде 'user' или 'admin'
        if selected_role not in ('user', 'admin'):
            flash("Моля, изберете роля (User или Admin).", 'error')
            return render_template('login.html')

        user = get_user_by_email(mysql, email)
        if user:
            # Сравняваме хеширани пароли
            if check_password_hash(user.password, password):
                if user.role == selected_role:
                    login_user(user)
                    flash(f"Успешен вход като {selected_role}.", 'success')
                    if selected_role == 'admin':
                        return redirect(url_for('dashboard'))
                    return redirect(url_for('index'))
                else:
                    flash("Нямате разрешение за тази роля.", 'error')
            else:
                flash("Грешна парола.", 'error')
        else:
            flash("Потребителят не е намерен.", 'error')

        return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Излязохте успешно.", 'info')
    return redirect(url_for('login'))


# ─── Администраторски изгледи ────────────────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash("Нямате достъп до администраторския панел.", 'error')
        return redirect(url_for('index'))
    return render_template('dashboard.html')


@app.route('/students')
@login_required
def students():
    if current_user.role != 'admin':
        flash("Нямате достъп до тази страница.", 'error')
        return redirect(url_for('index'))

    try:
        students = get_all_students(mysql)
    except Exception as e:
        flash(f"Не можа да се извлече списъкът с ученици: {str(e)}", 'error')
        students = []

    return render_template('students.html', students=students)


@app.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if current_user.role != 'admin':
        flash("Нямате достъп до тази страница.", 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        cls = request.form.get('class', '').strip()
        dob_str = request.form.get('date_of_birth', '').strip()

        # Валидация: задължителни полета
        if not first_name or not last_name or not cls:
            flash("Първо име, Фамилия и Клас са задължителни.", 'error')
            return render_template('add_student.html')

        # Валидация на дата (може да е празно → None)
        dob = None
        if dob_str:
            try:
                dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash("Невалиден формат на дата (трябва YYYY-MM-DD).", 'error')
                return render_template('add_student.html')

        try:
            insert_student_record(mysql, first_name, last_name, cls, dob)
            flash("Ученикът беше добавен успешно.", 'success')
        except mysql.connection.Error as e:
            mysql.connection.rollback()
            flash(f"Грешка при добавяне на ученик: {str(e)}", 'error')
            return render_template('add_student.html')
        except Exception as e:
            flash(f"Непредвидена грешка: {str(e)}", 'error')
            return render_template('add_student.html')

        return redirect(url_for('students'))

    return render_template('add_student.html')


@app.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    if current_user.role != 'admin':
        flash("Нямате достъп до тази страница.", 'error')
        return redirect(url_for('index'))

    student = get_student_by_id(mysql, student_id)
    if not student:
        flash("Ученикът не е намерен.", 'error')
        return redirect(url_for('students'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        cls = request.form.get('class', '').strip()
        dob_str = request.form.get('date_of_birth', '').strip()

        if not first_name or not last_name or not cls:
            flash("Първо име, Фамилия и Клас са задължителни.", 'error')
            return render_template('edit_student.html', student=student)

        dob = None
        if dob_str:
            try:
                dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash("Невалиден формат на дата (трябва YYYY-MM-DD).", 'error')
                return render_template('edit_student.html', student=student)

        try:
            update_student(mysql, student_id, first_name, last_name, cls, dob)
            flash("Ученикът беше редактиран успешно.", 'success')
        except mysql.connection.Error as e:
            mysql.connection.rollback()
            flash(f"Грешка при редактиране на ученик: {str(e)}", 'error')
            return render_template('edit_student.html', student=student)
        except Exception as e:
            flash(f"Непредвидена грешка: {str(e)}", 'error')
            return render_template('edit_student.html', student=student)

        return redirect(url_for('students'))

    return render_template('edit_student.html', student=student)


@app.route('/students/delete/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    if current_user.role != 'admin':
        flash("Нямате достъп до тази операция.", 'error')
        return redirect(url_for('index'))

    try:
        delete_student_by_id(mysql, student_id)
        flash("Ученикът беше изтрит.", 'success')
    except mysql.connection.Error as e:
        mysql.connection.rollback()
        flash(f"Грешка при изтриване на ученик: {str(e)}", 'error')
    except Exception as e:
        flash(f"Непредвидена грешка: {str(e)}", 'error')
    return redirect(url_for('students'))


# ─── ОЦЕНКИ ───────────────────────────────────────────────────────────────────────────────────────────────

@app.route('/grades')
@login_required
def grades():
    if current_user.role != 'user':
        flash("Нямате достъп до тази страница.", 'error')
        return redirect(url_for('index'))

    try:
        user_grades = get_grades_by_student(mysql, current_user.id)
    except Exception as e:
        flash(f"Грешка при извличане на оценки: {str(e)}", 'error')
        user_grades = []

    return render_template('grades.html', grades=user_grades)


@app.route('/grades/manage')
@login_required
def grades_manage():
    if current_user.role != 'admin':
        flash("Нямате достъп до тази страница.", 'error')
        return redirect(url_for('index'))

    try:
        grades_list = get_all_grades(mysql)
    except Exception as e:
        flash(f"Грешка при извличане на всички оценки: {str(e)}", 'error')
        grades_list = []

    return render_template('grades_manage.html', grades=grades_list)


@app.route('/grades/add', methods=['GET', 'POST'])
@login_required
def add_grade():
    if current_user.role != 'admin':
        flash("Нямате достъп до тази страница.", 'error')
        return redirect(url_for('index'))

    students = get_all_students(mysql)

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        subject = request.form.get('subject', '').strip()
        grade_val = request.form.get('grade', '').strip()
        dateg = request.form.get('date_given', '').strip()

        # Валидация: всички полета задължителни
        if not student_id or not subject or not grade_val or not dateg:
            flash("Всички полета са задължителни.", 'error')
            return render_template('add_grade.html', students=students)

        try:
            sid = int(student_id)
        except ValueError:
            flash("Невалиден ученик.", 'error')
            return render_template('add_grade.html', students=students)

        if not student_exists(mysql, sid):
            flash("Избраният ученик не съществува.", 'error')
            return render_template('add_grade.html', students=students)

        try:
            date_given = datetime.strptime(dateg, '%Y-%m-%d').date()
        except ValueError:
            flash("Невалиден формат на дата (трябва YYYY-MM-DD).", 'error')
            return render_template('add_grade.html', students=students)

        try:
            add_grade_record(mysql, sid, subject, grade_val, date_given, current_user.id)
            flash("Оценката беше добавена успешно.", 'success')
        except mysql.connection.Error as e:
            mysql.connection.rollback()
            flash(f"Грешка при добавяне на оценка: {str(e)}", 'error')
            return render_template('add_grade.html', students=students)
        except Exception as e:
            flash(f"Непредвидена грешка: {str(e)}", 'error')
            return render_template('add_grade.html', students=students)

        return redirect(url_for('grades_manage'))

    return render_template('add_grade.html', students=students)


@app.route('/grades/edit/<int:grade_id>', methods=['GET', 'POST'])
@login_required
def edit_grade(grade_id):
    if current_user.role != 'admin':
        flash("Нямате достъп до тази страница.", 'error')
        return redirect(url_for('index'))

    grade = get_grade_by_id(mysql, grade_id)
    if not grade:
        flash("Оценката не е намерена.", 'error')
        return redirect(url_for('grades_manage'))

    students = get_all_students(mysql)

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        subject = request.form.get('subject', '').strip()
        grade_val = request.form.get('grade', '').strip()
        dateg = request.form.get('date_given', '').strip()

        if not student_id or not subject or not grade_val or not dateg:
            flash("Всички полета са задължителни.", 'error')
            return render_template('edit_grade.html', grade=grade, students=students)

        try:
            sid = int(student_id)
        except ValueError:
            flash("Невалиден ученик.", 'error')
            return render_template('edit_grade.html', grade=grade, students=students)

        if not student_exists(mysql, sid):
            flash("Избраният ученик не съществува.", 'error')
            return render_template('edit_grade.html', grade=grade, students=students)

        try:
            date_given = datetime.strptime(dateg, '%Y-%m-%d').date()
        except ValueError:
            flash("Невалиден формат на дата (трябва YYYY-MM-DD).", 'error')
            return render_template('edit_grade.html', grade=grade, students=students)

        try:
            update_grade_record(mysql, grade_id, sid, subject, grade_val, date_given, current_user.id)
            flash("Оценката беше редактирана успешно.", 'success')
        except mysql.connection.Error as e:
            mysql.connection.rollback()
            flash(f"Грешка при редактиране на оценка: {str(e)}", 'error')
            return render_template('edit_grade.html', grade=grade, students=students)
        except Exception as e:
            flash(f"Непредвидена грешка: {str(e)}", 'error')
            return render_template('edit_grade.html', grade=grade, students=students)

        return redirect(url_for('grades_manage'))

    return render_template('edit_grade.html', grade=grade, students=students)


@app.route('/grades/delete/<int:grade_id>', methods=['POST'])
@login_required
def delete_grade(grade_id):
    if current_user.role != 'admin':
        flash("Нямате достъп до тази операция.", 'error')
        return redirect(url_for('index'))

    try:
        delete_grade_by_id(mysql, grade_id)
        flash("Оценката беше изтрита.", 'success')
    except mysql.connection.Error as e:
        mysql.connection.rollback()
        flash(f"Грешка при изтриване на оценка: {str(e)}", 'error')
    except Exception as e:
        flash(f"Непредвидена грешка: {str(e)}", 'error')
    return redirect(url_for('grades_manage'))


# ─── ОТСЪСТВИЯ ────────────────────────────────────────────────────────────────────────────────────────────

@app.route('/absences')
@login_required
def absences():
    if current_user.role != 'user':
        flash("Нямате достъп до тази страница.", 'error')
        return redirect(url_for('index'))

    try:
        absences_list = get_all_absences(mysql)
        # филтрираме само за текущия ученик
        absences_list = [a for a in absences_list if a['student_id'] == current_user.id]
    except Exception as e:
        flash(f"Грешка при извличане на отсъствия: {str(e)}", 'error')
        absences_list = []

    return render_template('absences.html', absences=absences_list)


@app.route('/absences/manage')
@login_required
def absences_manage():
    if current_user.role != 'admin':
        flash("Нямате достъп до тази страница.", 'error')
        return redirect(url_for('index'))

    try:
        absences_list = get_all_absences(mysql)
    except Exception as e:
        flash(f"Грешка при извличане на всички отсъствия: {str(e)}", 'error')
        absences_list = []

    return render_template('absences_manage.html', absences=absences_list)


@app.route('/absences/add', methods=['GET', 'POST'])
@login_required
def add_absence():
    if current_user.role != 'admin':
        flash("Нямате достъп до тази страница.", 'error')
        return redirect(url_for('index'))

    students = get_all_students(mysql)

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        date_abs = request.form.get('date_absent', '').strip()
        justified = request.form.get('is_justified') == 'on'

        if not student_id or not date_abs:
            flash("Всички полета са задължителни.", 'error')
            return render_template('add_absence.html', students=students)

        try:
            sid = int(student_id)
        except ValueError:
            flash("Невалиден ученик.", 'error')
            return render_template('add_absence.html', students=students)

        if not student_exists(mysql, sid):
            flash("Избраният ученик не съществува.", 'error')
            return render_template('add_absence.html', students=students)

        try:
            date_absent = datetime.strptime(date_abs, '%Y-%m-%d').date()
        except ValueError:
            flash("Невалиден формат на дата (трябва YYYY-MM-DD).", 'error')
            return render_template('add_absence.html', students=students)

        try:
            add_absence_record(mysql, sid, date_absent, justified, current_user.id)
            flash("Отсъствието беше добавено успешно.", 'success')
        except mysql.connection.Error as e:
            mysql.connection.rollback()
            flash(f"Грешка при добавяне на отсъствие: {str(e)}", 'error')
            return render_template('add_absence.html', students=students)
        except Exception as e:
            flash(f"Непредвидена грешка: {str(e)}", 'error')
            return render_template('add_absence.html', students=students)

        return redirect(url_for('absences_manage'))

    return render_template('add_absence.html', students=students)


@app.route('/absences/edit/<int:absence_id>', methods=['GET', 'POST'])
@login_required
def edit_absence(absence_id):
    if current_user.role != 'admin':
        flash("Нямате достъп до тази страница.", 'error')
        return redirect(url_for('index'))

    absence = get_absence_by_id(mysql, absence_id)
    if not absence:
        flash("Отсъствието не е намерено.", 'error')
        return redirect(url_for('absences_manage'))

    students = get_all_students(mysql)

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        date_abs = request.form.get('date_absent', '').strip()
        justified = request.form.get('is_justified') == 'on'

        if not student_id or not date_abs:
            flash("Всички полета са задължителни.", 'error')
            return render_template('edit_absence.html', absence=absence, students=students)

        try:
            sid = int(student_id)
        except ValueError:
            flash("Невалиден ученик.", 'error')
            return render_template('edit_absence.html', absence=absence, students=students)

        if not student_exists(mysql, sid):
            flash("Избраният ученик не съществува.", 'error')
            return render_template('edit_absence.html', absence=absence, students=students)

        try:
            date_absent = datetime.strptime(date_abs, '%Y-%m-%d').date()
        except ValueError:
            flash("Невалиден формат на дата (трябва YYYY-MM-DD).", 'error')
            return render_template('edit_absence.html', absence=absence, students=students)

        try:
            # При редакция записваме current_user.id като teacher_id
            update_absence_record(mysql, absence_id, sid, date_absent, justified, current_user.id)
            flash("Отсъствието беше редактирано успешно.", 'success')
        except mysql.connection.Error as e:
            mysql.connection.rollback()
            flash(f"Грешка при редактиране на отсъствие: {str(e)}", 'error')
            return render_template('edit_absence.html', absence=absence, students=students)
        except Exception as e:
            flash(f"Непредвидена грешка: {str(e)}", 'error')
            return render_template('edit_absence.html', absence=absence, students=students)

        return redirect(url_for('absences_manage'))

    return render_template('edit_absence.html', absence=absence, students=students)


@app.route('/absences/delete/<int:absence_id>', methods=['POST'])
@login_required
def delete_absence(absence_id):
    if current_user.role != 'admin':
        flash("Нямате достъп до тази операция.", 'error')
        return redirect(url_for('index'))

    try:
        delete_absence_by_id(mysql, absence_id)
        flash("Отсъствието беше изтрито.", 'success')
    except mysql.connection.Error as e:
        mysql.connection.rollback()
        flash(f"Грешка при изтриване на отсъствие: {str(e)}", 'error')
    except Exception as e:
        flash(f"Непредвидена грешка: {str(e)}", 'error')
    return redirect(url_for('absences_manage'))


# ─── Приложението стартира ─────────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # debug=False вече, не показваме подробни грешки на потребителя
    app.run(host='0.0.0.0', port=5000, debug=app.debug)
