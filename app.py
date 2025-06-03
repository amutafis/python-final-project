from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mysqldb import MySQL
from models import User, get_user_by_email, get_user_by_id, create_user

app = Flask(__name__)
app.secret_key = 'verysecretadminteacherkey123'  # shh

# Конфигурация на връзката с MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'AlekFM6644'     # shh
app.config['MYSQL_DB'] = 'diary'

mysql = MySQL(app)

# Flask-Login конфигурация
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(mysql, user_id)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        create_user(mysql, username, email, password)
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        selected_role = request.form['role']

        user = get_user_by_email(mysql, email)
        if user and user.password == password and user.role == selected_role:
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('grades'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        return "Нямате достъп до тази страница.", 403
    return render_template('dashboard.html')

# ----------------------------------------
# Маршрути за ученици (admin CRUD)
# ----------------------------------------

@app.route('/students')
@login_required
def list_students():
    if current_user.role != 'admin':
        return "Нямате достъп.", 403
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, first_name, last_name, class, date_of_birth FROM students")
    students = cursor.fetchall()
    cursor.close()
    return render_template('students.html', students=students)

@app.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if current_user.role != 'admin':
        return "Нямате достъп.", 403
    if request.method == 'POST':
        first = request.form['first_name']
        last = request.form['last_name']
        cls = request.form['class']
        dob = request.form['date_of_birth']  # формат: YYYY-MM-DD или празно
        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO students (first_name, last_name, class, date_of_birth) VALUES (%s, %s, %s, %s)",
            (first, last, cls, dob)
        )
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('list_students'))
    return render_template('add_student.html')

@app.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    if current_user.role != 'admin':
        return "Нямате достъп.", 403
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        first = request.form['first_name']
        last = request.form['last_name']
        cls = request.form['class']
        dob = request.form['date_of_birth']
        cursor.execute(
            "UPDATE students SET first_name=%s, last_name=%s, class=%s, date_of_birth=%s WHERE id=%s",
            (first, last, cls, dob, student_id)
        )
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('list_students'))
    cursor.execute(
        "SELECT id, first_name, last_name, class, date_of_birth FROM students WHERE id=%s",
        (student_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    if row:
        student = {
            'id': row[0],
            'first_name': row[1],
            'last_name': row[2],
            'class': row[3],
            'date_of_birth': row[4]
        }
        return render_template('edit_student.html', student=student)
    return "Учeникът не е намерен.", 404

@app.route('/students/delete/<int:student_id>')
@login_required
def delete_student(student_id):
    if current_user.role != 'admin':
        return "Нямате достъп.", 403
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('list_students'))

# ----------------------------------------
# Маршрути за оценки (admin CRUD + студент view)
# ----------------------------------------

@app.route('/grades')
@login_required
def grades():
    # страницата за учениците (role='user')
    if current_user.role != 'user':
        return "Нямате достъп до тази страница.", 403
    # Извличаме само оценките на логнатия ученик
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT subject, grade, date_given FROM grades WHERE student_id = %s",
        (current_user.id,)
    )
    user_grades = cursor.fetchall()
    cursor.close()
    return render_template('grades.html', grades=user_grades)

@app.route('/grades/manage')
@login_required
def manage_grades():
    if current_user.role != 'admin':
        return "Нямате достъп.", 403
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT g.id, s.first_name, s.last_name, g.subject, g.grade, g.date_given
        FROM grades g
        JOIN students s ON g.student_id = s.id
    """)
    grades = cursor.fetchall()
    cursor.close()
    return render_template('grades_manage.html', grades=grades)

@app.route('/grades/add', methods=['GET', 'POST'])
@login_required
def add_grade():
    if current_user.role != 'admin':
        return "Нямате достъп.", 403
    cursor = mysql.connection.cursor()
    # Списък с всички ученици за dropdown
    cursor.execute("SELECT id, first_name, last_name FROM students")
    students = cursor.fetchall()
    if request.method == 'POST':
        student_id = request.form['student_id']
        subject = request.form['subject']
        value = request.form['grade']
        dateg = request.form['date_given']
        teacher = current_user.id
        cursor.execute(
            "INSERT INTO grades (student_id, subject, grade, teacher_id, date_given) VALUES (%s, %s, %s, %s, %s)",
            (student_id, subject, value, teacher, dateg)
        )
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('manage_grades'))
    cursor.close()
    return render_template('add_grade.html', students=students)

@app.route('/grades/edit/<int:grade_id>', methods=['GET', 'POST'])
@login_required
def edit_grade(grade_id):
    if current_user.role != 'admin':
        return "Нямате достъп.", 403
    cursor = mysql.connection.cursor()
    # Списък с всички ученици за dropdown
    cursor.execute("SELECT id, first_name, last_name FROM students")
    students = cursor.fetchall()
    if request.method == 'POST':
        student_id = request.form['student_id']
        subject = request.form['subject']
        value = request.form['grade']
        dateg = request.form['date_given']
        cursor.execute(
            "UPDATE grades SET student_id=%s, subject=%s, grade=%s, date_given=%s WHERE id=%s",
            (student_id, subject, value, dateg, grade_id)
        )
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('manage_grades'))
    cursor.execute(
        "SELECT id, student_id, subject, grade, date_given FROM grades WHERE id=%s",
        (grade_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    if row:
        grade = {
            'id': row[0],
            'student_id': row[1],
            'subject': row[2],
            'grade': row[3],
            'date_given': row[4]
        }
        return render_template('edit_grade.html', grade=grade, students=students)
    return "Оценката не е намерена.", 404

@app.route('/grades/delete/<int:grade_id>')
@login_required
def delete_grade(grade_id):
    if current_user.role != 'admin':
        return "Нямате достъп.", 403
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM grades WHERE id = %s", (grade_id,))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('manage_grades'))

@app.route('/absences/manage')
@login_required
def manage_absences():
    if current_user.role != 'admin':
        return "Нямате достъп.", 403
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT a.id, s.first_name, s.last_name, a.date_absent, a.is_justified
        FROM absences a
        JOIN students s ON a.student_id = s.id
    """)
    absences = cursor.fetchall()
    cursor.close()
    return render_template('absences_manage.html', absences=absences)

@app.route('/absences/add', methods=['GET', 'POST'])
@login_required
def add_absence():
    if current_user.role != 'admin':
        return "Нямате достъп.", 403
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, first_name, last_name FROM students")
    students = cursor.fetchall()
    if request.method == 'POST':
        student_id = request.form['student_id']
        date_abs = request.form['date_absent']
        justified = bool(request.form.get('is_justified'))
        teacher = current_user.id
        cursor.execute(
            "INSERT INTO absences (student_id, date_absent, is_justified, teacher_id) VALUES (%s, %s, %s, %s)",
            (student_id, date_abs, justified, teacher)
        )
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('manage_absences'))
    cursor.close()
    return render_template('add_absence.html', students=students)

@app.route('/absences/edit/<int:absence_id>', methods=['GET', 'POST'])
@login_required
def edit_absence(absence_id):
    if current_user.role != 'admin':
        return "Нямате достъп.", 403
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, first_name, last_name FROM students")
    students = cursor.fetchall()
    if request.method == 'POST':
        student_id = request.form['student_id']
        date_abs = request.form['date_absent']
        justified = bool(request.form.get('is_justified'))
        cursor.execute(
            "UPDATE absences SET student_id=%s, date_absent=%s, is_justified=%s WHERE id=%s",
            (student_id, date_abs, justified, absence_id)
        )
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('manage_absences'))
    cursor.execute(
        "SELECT id, student_id, date_absent, is_justified FROM absences WHERE id=%s",
        (absence_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    if row:
        absence = {
            'id': row[0],
            'student_id': row[1],
            'date_absent': row[2].isoformat(),  # за HTML date input
            'is_justified': row[3]
        }
        return render_template('edit_absence.html', absence=absence, students=students)
    return "Отсъствието не е намерено.", 404

@app.route('/absences/delete/<int:absence_id>')
@login_required
def delete_absence(absence_id):
    if current_user.role != 'admin':
        return "Нямате достъп.", 403
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM absences WHERE id = %s", (absence_id,))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('manage_absences'))

if __name__ == '__main__':
    app.run(debug=True)
