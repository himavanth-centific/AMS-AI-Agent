import pyodbc
import pandas as pd

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "Server=localhost;"
    "Database=ALIPSDevelopment2;"
    "UID=sa;"
    "PWD=Password@123;"
    "TrustServerCertificate=yes;"
)

def execute_mssql_query(sql_query):
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        df = pd.read_sql(sql_query, conn)
        conn.close()
        
        if df.empty:
            return "Query executed successfully, but returned no results."
        
        return df.to_html(classes='table table-striped', index=False)
    except Exception as e:
        return f"Database Error: {str(e)}"

def load_schema():
    try:
        with open("schema.txt", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "Error: schema.txt not found."