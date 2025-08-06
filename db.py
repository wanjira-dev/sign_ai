# db.py
import mysql.connector


def connect_db():
    return mysql.connector.connect(
        host="gateway01.eu-central-1.prod.aws.tidbcloud.com",
        user="2BLUt2oE6PhmNWv.root",
        password="ZZlmbebBqt5velrx",
        database="test"
    )

def init_db():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE,
            password VARCHAR(255),
            gender ENUM('male', 'female')
        )
    """)
    conn.commit()
    conn.close()

def register_user(username, password, gender):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, gender) VALUES (%s, %s, %s)", (username, password, gender))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT gender FROM users WHERE username=%s AND password=%s", (username, password))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None
