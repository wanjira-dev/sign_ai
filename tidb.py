import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import bcrypt
import json # Converts list to JSON strings for storage

load_dotenv()

DB_HOST = os.getenv("TIDB_HOST")
DB_PORT = int(os.getenv("TIDB_PORT", 4000))
DB_USER = os.getenv("TIDB_USER")
DB_PASSWORD = os.getenv("TIDB_PASSWORD")
DB_NAME = os.getenv("TIDB_DB_NAME")
DB_SSL_CA = os.getenv("TIDB_SSL_CA")

def get_db_connection():
    """Establishes and returns a connection to the TiDB database.
    Connects to the server first and creates the database if it does not exist,
    then connects the database
    """
    try:
        # Build connection arguments dynamically
        conn_args = {
            'host': DB_HOST,
            'port': DB_PORT,
            'user': DB_USER,
            'password': DB_PASSWORD
        }
        if DB_SSL_CA:
            conn_args['ssl_ca'] = DB_SSL_CA
            conn_args['ssl_verify_cert'] = True
        
        connection = mysql.connector.connect(**conn_args)
        
        if connection.is_connected():
            print("Successfully connected to TiDB server.")
            cursor = connection.cursor()
            
            # Create the DB if it does not exist
            print(f"Ensuring database '{DB_NAME}' exists...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            print(f"Database '{DB_NAME}' is ready")
            
            # Switch to desired database
            connection.database = DB_NAME
            
            print(f" Successfully connected to database '{DB_NAME}'")
            cursor.close()
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
    if not connection or not connection.is_connected():
        print("Cannot set up database: No valid connection.")
        return
    
    cursor = connection.cursor()
    try:
        # Table 1: Users Table - Stores user registration data
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT AUTO_RANDOM PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(100) NOT NULL,
            gender VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP   
        );            
        """)
        
        # Table 2: Vector Table - Storing learned sign language embeddings
        # VECTOR (128) - Stores 128-dimensional vector from our custom NN
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sign_vectors (
            id BIGINT AUTO_RANDOM PRIMARY KEY,
            label VARCHAR(50) NOT NULL,
            embedding VECTOR(128),
            user_id BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("Table 'sign_vectors' verified.")
        
        # Create vector index
        try:
            print("Ensuring vector index exists on 'sign_vectors' table...")
            cursor.execute("""
            CREATE INDEX embedding_index ON sign_vectors (embedding) USING ANN(ENG=COS);
            """)
            print("Vector index created or already exists.")
            
        except mysql.connector.Error as e:
            if e.errno ==1061:
                print("Vector index already exists, skipping creation.")
            else:
                raise e
            
        connection.commit()
        print("Database tables (users, sign_vectors, prediction_logs, model_feedback) verified/created")
    except Error as e:
        print(f"Error creating tables: {e}")
    finally:
        cursor.close()
        

# Vector Database Functions
def add_sign_vector(connection, label, vector, user_id=None):
    """
    Ingests a new sign into the vector database.
    Populates knowledge base of signs.
    """
    cursor = connection.cursor()
    try:
        # Vector is in string format
        vector_str = json.dumps(vector)
        sql = "INSERT INTO sign_vectors (label, embedding, user_id) VALUES (%s, %s, %s)"
        cursor.execute(sql, (label, vector_str, user_id))
        connection.commit()
        print(f"Successfully added vector for sign: '{label}'")
        return True
    except Error as e:
        print(f"Error adding sign vector: {e}")
        return False
    finally:
        cursor.close()
        
def find_similar_signs(connection, query_vector, top_k=1):
    """
    Performs a vector similarity search (ANN_SEARCH) to find the closest matching sign.
    """
    cursor = connection.cursor(dictionary=True)
    try:
        vector_str = json.dumps(query_vector)
        # ANN_SEARCH finds the Approximate Nearest Neighbors using Cosine similarity
        sql = """
        SELECT id, label, ANN_SEARCH(embedding, %s) as similarity
        FROM sign_vectors
        ORDER BY similarity DESC
        LIMIT %s
        """
        cursor.execute(sql, (vector_str, top_k))
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Error during vector search: {e}")
        return []
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
        