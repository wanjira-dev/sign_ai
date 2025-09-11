import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

print("Attempting to load .env file....")
load_dotenv()
print(".env file loaded")

# Reading credentials
DB_HOST = os.getenv("TIDB_HOST")
DB_PORT = os.getenv("TIDB_PORT")
DB_USER = os.getenv("TIDB_USER")
DB_PASSWORD = os.getenv("TIDB_PASSWORD")
DB_NAME = os.getenv("TIDB_NAME")
DB_SSL_CA = os.getenv("TIDB_SSL_CA")

print("\n--- Verifying credentials (from .env) ---")
print(f"Host: {DB_HOST}")
print(f"Port: {DB_PORT}")
print(f"User: {DB_USER}")
print(f"Password Loaded: {'Yes' if DB_PASSWORD else 'No'}")
print(f"Database Name: {DB_NAME}")
print(f"SSL CA Path: {DB_SSL_CA}")
print("------------------------------\n")

def test_connection():
    """Attempts to connect to the TiDB database and prints the result."""
    
    # Check if essential variables are loaded
    if not all([DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_SSL_CA]):
        print(" Critical error: Not all required environment variables are loaded.")
        print("Please check your .env file's name, location, and content.")
        return

    try:
        print("Attempting to connect to TiDB Cloud...")
        conn_args = {
            'host': DB_HOST,
            'port': int(DB_PORT),
            'user': DB_USER,
            'password': DB_PASSWORD,
            'ssl_ca': DB_SSL_CA,
            'ssl_verify_cert': True,
            'connection_timeout': 15
        }
        
        connection = mysql.connector.connect(**conn_args)
        
        if connection.is_connected():
            print("\n SUCCESS! Connection to TiDB Cloud was successful")
            db_info = connection.get_server_info()
            print(f"Connected to Server Version: {db_info}\n")
            
            # simple query
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            record = cursor.fetchone()
            print(f"You're connected to database: {record}")
            connection.close()
    
    except Error as e:
        print("\n Failed to connect to TiDB Cloud.")
        print("This is the error you need to analyse:")
        print(f"\n---> Error: {e}\n")
        
if __name__ == "__main__":
    test_connection()