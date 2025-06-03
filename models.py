from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, id, username, email, password, role='user'):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.role = role


def get_user_by_email(mysql, email):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, username, email, password, role FROM users WHERE email = %s", (email,))
    row = cursor.fetchone()
    cursor.close()
    if row:
        return User(*row)
    return None


def get_user_by_id(mysql, user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, username, email, password, role FROM users WHERE id = %s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    if row:
        return User(*row)
    return None


def create_user(mysql, username, email, hashed_password):
    cursor = mysql.connection.cursor()
    # Паролата вече е хеширана
    cursor.execute(
        "INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
        (username, email, hashed_password, 'user')
    )
    mysql.connection.commit()
    cursor.close()


# ─── STUDENTS ─────────────────────────────────────────────────────────────────────────────────────────────

def get_all_students(mysql):
    cursor = mysql.connection.cursor()
    # Обграждаме колоната class в обратно кавички
    cursor.execute("SELECT id, first_name, last_name, `class`, date_of_birth FROM students")
    rows = cursor.fetchall()
    cursor.close()
    students = []
    for row in rows:
        # row = (id, first_name, last_name, class, date_of_birth)
        students.append({
            'id': row[0],
            'first_name': row[1],
            'last_name': row[2],
            'class': row[3],
            'date_of_birth': row[4]
        })
    return students


def student_exists(mysql, student_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT 1 FROM students WHERE id = %s", (student_id,))
    exists = cursor.fetchone() is not None
    cursor.close()
    return exists


def get_student_by_id(mysql, student_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, first_name, last_name, `class`, date_of_birth FROM students WHERE id = %s", (student_id,))
    row = cursor.fetchone()
    cursor.close()
    if row:
        return {
            'id': row[0],
            'first_name': row[1],
            'last_name': row[2],
            'class': row[3],
            'date_of_birth': row[4]
        }
    return None


def insert_student_record(mysql, first_name, last_name, cls, date_of_birth):
    cursor = mysql.connection.cursor()
    # Обвиваме class в обратно кавички
    cursor.execute(
        "INSERT INTO students (first_name, last_name, `class`, date_of_birth) VALUES (%s, %s, %s, %s)",
        (first_name, last_name, cls, date_of_birth)
    )
    mysql.connection.commit()
    cursor.close()


def update_student(mysql, student_id, first_name, last_name, cls, date_of_birth):
    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE students SET first_name = %s, last_name = %s, `class` = %s, date_of_birth = %s WHERE id = %s",
        (first_name, last_name, cls, date_of_birth, student_id)
    )
    mysql.connection.commit()
    cursor.close()


def delete_student_by_id(mysql, student_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
    mysql.connection.commit()
    cursor.close()


# ─── GRADES ──────────────────────────────────────────────────────────────────────────────────────────────

def get_grades_by_student(mysql, student_id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT g.id, g.subject, g.grade, g.date_given, u.username "
        "FROM grades g JOIN users u ON g.teacher_id = u.id "
        "WHERE g.student_id = %s "
        "ORDER BY g.date_given DESC",
        (student_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    grades = []
    for row in rows:
        # row = (id, subject, grade, date_given, teacher_username)
        grades.append({
            'id': row[0],
            'subject': row[1],
            'grade': row[2],
            'date_given': row[3],
            'teacher': row[4]
        })
    return grades


def get_all_grades(mysql):
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT g.id, g.student_id, s.first_name, s.last_name, g.subject, g.grade, g.date_given, u.username "
        "FROM grades g "
        "JOIN students s ON g.student_id = s.id "
        "JOIN users u ON g.teacher_id = u.id "
        "ORDER BY g.date_given DESC"
    )
    rows = cursor.fetchall()
    cursor.close()
    grades = []
    for row in rows:
        # row = (id, student_id, first_name, last_name, subject, grade, date_given, teacher_username)
        grades.append({
            'id': row[0],
            'student_id': row[1],
            'student_name': f"{row[2]} {row[3]}",
            'subject': row[4],
            'grade': row[5],
            'date_given': row[6],
            'teacher': row[7]
        })
    return grades


def get_grade_by_id(mysql, grade_id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT id, student_id, subject, grade, date_given FROM grades WHERE id = %s",
        (grade_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    if row:
        return {
            'id': row[0],
            'student_id': row[1],
            'subject': row[2],
            'grade': row[3],
            'date_given': row[4]
        }
    return None


def add_grade_record(mysql, student_id, subject, grade, date_given, teacher_id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        "INSERT INTO grades (student_id, subject, grade, date_given, teacher_id) VALUES (%s, %s, %s, %s, %s)",
        (student_id, subject, grade, date_given, teacher_id)
    )
    mysql.connection.commit()
    cursor.close()


def update_grade_record(mysql, grade_id, student_id, subject, grade, date_given, teacher_id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE grades SET student_id = %s, subject = %s, grade = %s, date_given = %s, teacher_id = %s WHERE id = %s",
        (student_id, subject, grade, date_given, teacher_id, grade_id)
    )
    mysql.connection.commit()
    cursor.close()


def delete_grade_by_id(mysql, grade_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM grades WHERE id = %s", (grade_id,))
    mysql.connection.commit()
    cursor.close()


# ─── ABSENCES ────────────────────────────────────────────────────────────────────────────────────────────

def get_all_absences(mysql):
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT a.id, a.student_id, s.first_name, s.last_name, a.date_absent, a.is_justified, u.username "
        "FROM absences a "
        "JOIN students s ON a.student_id = s.id "
        "JOIN users u ON a.teacher_id = u.id "
        "ORDER BY a.date_absent DESC"
    )
    rows = cursor.fetchall()
    cursor.close()
    absences = []
    for row in rows:
        # row = (id, student_id, first_name, last_name, date_absent, is_justified, teacher_username)
        absences.append({
            'id': row[0],
            'student_id': row[1],
            'student_name': f"{row[2]} {row[3]}",
            'date_absent': row[4],
            'is_justified': bool(row[5]),
            'teacher': row[6]
        })
    return absences


def get_absence_by_id(mysql, absence_id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT id, student_id, date_absent, is_justified, teacher_id FROM absences WHERE id = %s",
        (absence_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    if row:
        return {
            'id': row[0],
            'student_id': row[1],
            'date_absent': row[2],
            'is_justified': bool(row[3]),
            'teacher_id': row[4]
        }
    return None


def add_absence_record(mysql, student_id, date_absent, is_justified, teacher_id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        "INSERT INTO absences (student_id, date_absent, is_justified, teacher_id) VALUES (%s, %s, %s, %s)",
        (student_id, date_absent, is_justified, teacher_id)
    )
    mysql.connection.commit()
    cursor.close()


def update_absence_record(mysql, absence_id, student_id, date_absent, is_justified, teacher_id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE absences SET student_id = %s, date_absent = %s, is_justified = %s, teacher_id = %s WHERE id = %s",
        (student_id, date_absent, is_justified, teacher_id, absence_id)
    )
    mysql.connection.commit()
    cursor.close()


def delete_absence_by_id(mysql, absence_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM absences WHERE id = %s", (absence_id,))
    mysql.connection.commit()
    cursor.close()
