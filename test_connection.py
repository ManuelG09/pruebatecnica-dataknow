import pyodbc
from dotenv import load_dotenv
import os

load_dotenv()

conn_str = (
    f"DRIVER={os.getenv('DB_DRIVER')};"
    f"SERVER={os.getenv('DB_SERVER')};"
    f"DATABASE={os.getenv('DB_NAME')};"
    f"UID={os.getenv('DB_USER')};"
    f"PWD={os.getenv('DB_PASSWORD')};"
    f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
)

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    print("Conexión exitosa:", cursor.fetchone())
    conn.close()
except Exception as e:
    print("Error de conexión:", e)