import pyodbc

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "Server=localhost;Database=ALIPSDevelopment2;"
    "UID=sa;PWD=Password@123;TrustServerCertificate=yes;"
)

try:
    conn = pyodbc.connect(conn_str)
    print("✅ Connection Successful!")
    conn.close()
except Exception as e:
    print(f"❌ Connection Failed: {e}")