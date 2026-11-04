import os 
from dotenv import load_dotenv
import psycopg2
from mcp.server.fastmcp import FastMCP

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

mcp = FastMCP("Bank Data MCP Server")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME, 
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode="require"
    )
@mcp.tool()
def list_tables():
    """return the names of the tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = []
        for row in cursor.fetchall():
            tables.append(row[0])
        return tables 
    finally:
        cursor.close()
        conn.close()

@mcp.tool()
def describe_table (table_name):
    """return name and type of info shown in a  table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try: 
        cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s;", (table_name,))
        columns = []
        for row in cursor.fetchall():
            columns.append(row)

        return columns
    finally:
        cursor.close()
        conn.close()

@mcp.tool()
def run_query (query: str):
    """run given query on database"""
    print("AGENT IS RUNNING QUERY:", query)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        answer = []
        for row in cursor.fetchall():
            answer.append(row)
        print("QUERY RESULT:", answer)
        return answer
    except Exception as e:
        return f"Query failed: {e}. use describe_table to check column names and try again."
    finally:
        cursor.close()
        conn.close()

@mcp.tool()
def get_unique_values(table_name: str, column_name: str):
    """Return up to 10 unique values from a specific column to understand the exact spelling and case."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # שימוש בפורמט בטוח כדי למנוע שגיאות תחביר
        cursor.execute(f'SELECT DISTINCT "{column_name}" FROM "{table_name}" LIMIT 10;')
        values = [row[0] for row in cursor.fetchall()]
        return values
    except Exception as e:
        return f"Failed to get unique values: {e}"
    finally:
        cursor.close()
        conn.close()




