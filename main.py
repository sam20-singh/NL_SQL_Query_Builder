from fastapi import FastAPI
from pydantic import BaseModel
import requests
import sqlite3

app = FastAPI()


class QueryRequest(BaseModel):
    question: str


@app.get("/")
def home():
    return {
        "message": "NL SQL Query Builder API is running"
    }


@app.post("/query")
def query(request: QueryRequest):

    # Connect to SQLite database
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # Find all tables
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
    """)

    tables = cursor.fetchall()

    allowed_tables = []

    for table in tables:
        allowed_tables.append(table[0].upper())

    print("Allowed tables:", allowed_tables)

    # Build dynamic database schema
    schema_parts = []

    for table in tables:
        table_name = table[0]

        cursor.execute(f"PRAGMA table_info({table_name})")

        columns = cursor.fetchall()

        column_names = []

        for column in columns:
            column_names.append(column[1])

        table_schema = (
            f"Table: {table_name}\n"
            f"Columns: {', '.join(column_names)}"
        )

        schema_parts.append(table_schema)

    schema = "\n\n".join(schema_parts)

    print("Schema:")
    print(schema)

    # Ask Qwen to generate SQL
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:7b",
                "prompt": f"""
You are a SQL assistant.

Here is the actual database schema:

{schema}

Convert the user's request into a SQL SELECT query.

Rules:
- Only generate SELECT queries.
- You may use JOIN when the user's request requires data from multiple tables.
- Use only tables and columns that exist in the schema.
- Return only the SQL query.

User request:
{request.question}

Return only the SQL query.
""",
                "stream": False
            }
        )

    except requests.exceptions.RequestException:
        connection.close()

        return {
            "error": "AI service is unavailable. Make sure Ollama is running."
        }

    # Get AI response
    ai_response = response.json()["response"]

    # Extract SQL from Markdown code block
    if "```sql" in ai_response:
        sql = ai_response.split("```sql")[1].split("```")[0].strip()
    else:
        sql = ai_response.strip()

    print("Generated SQL:", sql)

    # Convert SQL to uppercase for validation
    sql_upper = sql.upper().strip()

    # Only SELECT queries are allowed
    if not sql_upper.startswith("SELECT"):
        connection.close()

        return {
            "error": "Unsafe SQL query blocked"
        }

    # Prevent multiple SQL statements
    if ";" in sql_upper[:-1]:
        connection.close()

        return {
            "error": "Multiple SQL statements are not allowed"
        }

    # Prevent SQL comments
    if "--" in sql_upper or "/*" in sql_upper or "*/" in sql_upper:
        connection.close()

        return {
            "error": "SQL comments are not allowed"
        }

    # Check whether the SQL uses an allowed table
    table_found = False

    for table in allowed_tables:
        if f"FROM {table}" in sql_upper:
            table_found = True
            break

    if not table_found:
        connection.close()

        return {
            "error": "SQL query uses an unknown table"
        }

    # Execute SQL
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()

    except Exception as error:
        connection.close()

        return {
            "error": str(error)
        }

    # Close database
    connection.close()

    # Return result
    return {
        "sql": sql,
        "results": rows
    }