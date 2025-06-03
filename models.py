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
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    row = cursor.fetchone()
    cursor.close()
    if row:
        return User(*row)
    return None

def get_user_by_id(mysql, user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    if row:
        return User(*row)
    return None

def create_user(mysql, username, email, password):
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
                   (username, email, password, 'user'))
    mysql.connection.commit()
    cursor.close()
