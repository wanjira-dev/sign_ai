import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv()

DB_HOST = os.getenv("TIDB_HOST")
DB_PORT = int(os.getenv("TIDB_PORT", 4000))
DB_USER = os.getenv("TIDB_USER")
DB_PASSWORD = os.getenv("TIDB_PASSWORD")
DB_NAME = os.getenv("TIDB_DB_NAME")
DB_SSL_CA = os.getenv("TIDB_SSL_CA")

def get_db_connection():
    """Establishes and returns a connection to the TiDB database."""
    try:
        # Build connection arguments dynamically
        conn_args = {
            'host': DB_HOST,
            'port': DB_PORT,
            'user': DB_USER,
            'password': DB_PASSWORD,
            'database': DB_NAME
        }
        if DB_SSL_CA:
            conn_args['ssl_ca'] = DB_SSL_CA
            conn_args['ssl_verify_cert'] = True
        
        connection = mysql.connector.connect(**conn_args)
        
        if connection.is_connected():
            print("Successfully connected to TiDB database.")
            return connection
        
    except Error as e:
        print(f"Error connection to TiDB: {e}")
        
        if "TiDB_HOST" not in os.environ:
            print("Make sure .env file is created and `load_dotenv()` is called.")
            
        return None
    
def setup_database(connection):
    """
    Creates/verifies all necessary tables: users, prediction_logs, and model_feedback. This new structure links log to registered users. 
    """
    cursor = connection.cursor()
    try:
        # Table 1: Users (New) - Stores user registration data
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT AUTO_RANDOM PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(100) NOT NULL,
            gender VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   
        );            
        """)
        
        # Table 2: Prediction Logs (Updated) - Now linked to the users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_logs (
            id BIGINT AUTO_RANDOM PRIMARY KEY,
            session_id VARCHAR(255) NOT NULL,
            user_id BIGINT,
            timestamp TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP(3),
            predicted_sign CHAR(1) NOT NULL,
            confidence_score FLOAT NOT NULL,
            model_version VARCHAR(50) DEFAULT 'v1.0-64x64',
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );            
        """)
        
        # Table 3: Model Feedback (Unchanged) - Inherits user link via prediction_logs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_feedback (
            id BIGINT AUTO_RANDOM PRIMARY KEY,
            log_id BIGINT,
            timestamp TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP(3),
            correct_sign CHAR(1) NOT NULL,
            is_processed BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (log_id) REFERENCES prediction_logs(id) ON DELETE CASCADE
        );     
        """)
        connection.commit()
        print("Database tables (users, prediction_logs, model_feedback) verified/created")
    except Error as e:
        print(f"Error creating tables: {e}")
    finally:
        cursor.close()
        
# User Management Functions
def register_user(connection, username, password, gender):
    """Registers a new user with a securely hashed password."""
    if not connection or not connection.is_connected():
        return False
    
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    cursor = connection.cursor()
    try:
        sql = "INSERT INTO users (username, password_hash, gender) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, hashed_password.decode('utf-8'), gender))
        connection.commit()
        print(f"User '{username}' registered successfully.")
        return True
    except mysql.connector.IntegrityError:
        # This error occurs if the username is already taken
        print(f"Registration failed: Username '{username}' already exists.")
        return False
    except Error as e:
        print(f"Error during registration: {e}")
        return False
    finally:
        cursor.close()
        
def login_user(connection, username, password):
    """Logs in a user by verifying their username and password hash."""
    if not connection or not connection.is_connected():
        return None
    cursor = connection.cursor(dictionary=True)
    # Fetch results as dictionaries
    try:
        sql = "SELECT id, username, password_hash, gender FROM users WHERE username = %s"
        cursor.execute(sql, (username,))
        user_record = cursor.fetchone()
        
        if user_record:
            # Check if the provided password matches the stored hash
            password_valid = bcrypt.checkpw(password.encode('utf-8'), user_record['password_hash'].encode('utf-8'))
            if password_valid:
                print(f"User '{username}' logged in successfully.")
                # Return a dictionary of user details
                return {
                    "user_id": user_record['id'],
                    "username": user_record['username'],
                    "gender": user_record['gender']
                }
                
        print(f"Login failed: Invalid username or password for '{username}'.")
        return None
    except Error as e:
        print(f"Error during login: {e}")
        return None
    finally:
        cursor.close()
        
# Logging Functions
def log_prediction(connection, session_id, prediction, confidence, user_id=None):
    """
    Logs a prediction. Now accepts an optional user_id logged_in users.
    """
    if not connection or not connection.is_connected():
        return None
    
    cursor = connection.cursor()
    try:
        sql = "INSERT INTO prediction_logs (session_id, user_id, predicted_sign, confidence_score) VALUES (%s, %s, %s, %s)"
        values = (session_id, user_id, prediction, confidence)
        cursor.execute(sql, values)
        connection.commit()
        last_id = cursor.lastrowid
        print(f"Log successful: Sign '{prediction}' by user_id '{user_id}'. Log ID: {last_id}")
        return last_id
    except Error as e:
        print(f"Error logging prediction: {e}")
        return None
    finally:
        cursor.close()
        
def log_feedback(connection, log_id, correct_sign):
    """Logs user_provided feedback for an incorrect prediction"""
    if not connection or not connection.is_connected():
        return
    cursor = connection.cursor()
    try:
        sql = "INSERT INTO model_feedback (log_id, correct_sign) VALUES (%s, %s)"
        values = (log_id, correct_sign)
        cursor.execute(sql, values)
        connection.commmit()
        print(f"Feedback successful: Log ID {log_id} corrected to '{correct_sign}'.")
        
    except Error as e:
        print(F"Error loading feedback: {e}")
    finally:
        cursor.close()