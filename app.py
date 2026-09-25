from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import os
import sqlite3


app = FastAPI()


# ==========================================
# GROQ CLIENT
# ==========================================

api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY environment variable is not set.")

client = Groq(
    api_key=api_key
)


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# REQUEST MODEL
# ==========================================

class QueryRequest(BaseModel):
    question: str


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():
    return {
        "message": "NL SQL Query Builder API is running"
    }


# ==========================================
# QUERY ENDPOINT
# ==========================================

@app.post("/query")
def query(request: QueryRequest):

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()


    # ==========================================
    # GET DATABASE TABLES
    # ==========================================

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
    """)

    tables = cursor.fetchall()


    # Store allowed table names
    allowed_tables = []

    for table in tables:
        allowed_tables.append(table[0].upper())




    # ==========================================
    # BUILD DATABASE SCHEMA
    # ==========================================

    schema_parts = []

    for table in tables:

        table_name = table[0]

        cursor.execute(
            f"PRAGMA table_info({table_name})"
        )

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

    


    # ==========================================
    # SEND QUESTION TO GROQ
    # ==========================================

    try:

        response = client.chat.completions.create(

            model="openai/gpt-oss-20b",

            messages=[
                {
                    "role": "system",

                    "content": f"""
You are a SQL assistant.

Here is the actual database schema:

{schema}

Convert the user's request into a SQL SELECT query.

Rules:

- Only generate SELECT queries.
- You may use JOIN when the user's request requires data from multiple tables.
- Use only tables and columns that exist in the schema.
- Do not create tables.
- Do not modify the database.
- Return only the SQL query.
"""
                },

                {
                    "role": "user",

                    "content": request.question
                }
            ]
        )

    except Exception as error:

        connection.close()


        return {
            "error": "AI service is unavailable."
        }


    # ==========================================
    # GET GROQ RESPONSE
    # ==========================================

    ai_response = response.choices[0].message.content

   


    # ==========================================
    # EXTRACT SQL
    # ==========================================

    if "```sql" in ai_response:

        sql = (
            ai_response
            .split("```sql")[1]
            .split("```")[0]
            .strip()
        )

    elif "```" in ai_response:

        sql = (
            ai_response
            .split("```")[1]
            .strip()
        )

    else:

        sql = ai_response.strip()


   


    # ==========================================
    # SQL VALIDATION
    # ==========================================

    sql_upper = sql.upper().strip()


    # ------------------------------------------
    # 1. SELECT ONLY
    # ------------------------------------------

    if not sql_upper.startswith("SELECT"):

        connection.close()

        return {
            "error": "Only SELECT queries are allowed."
        }


    # ------------------------------------------
    # 2. BLOCK DANGEROUS SQL OPERATIONS
    # ------------------------------------------

    dangerous_keywords = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "REPLACE",
        "ATTACH",
        "DETACH",
        "PRAGMA"
    ]


    for keyword in dangerous_keywords:

        if keyword in sql_upper:

            connection.close()

            return {
                "error": f"Blocked dangerous SQL operation: {keyword}"
            }


    # ------------------------------------------
    # 3. BLOCK MULTIPLE SQL STATEMENTS
    # ------------------------------------------

    if ";" in sql_upper[:-1]:

        connection.close()

        return {
            "error": "Multiple SQL statements are not allowed."
        }


    # ------------------------------------------
    # 4. BLOCK SQL COMMENTS
    # ------------------------------------------

    if (
        "--" in sql_upper
        or "/*" in sql_upper
        or "*/" in sql_upper
    ):

        connection.close()

        return {
            "error": "SQL comments are not allowed."
        }


    # ------------------------------------------
    # 5. CHECK THAT A KNOWN TABLE IS USED
    # ------------------------------------------

    table_found = False

    for table in allowed_tables:

        if f"FROM {table}" in sql_upper:

            table_found = True

            break


    if not table_found:

        connection.close()

        return {
            "error": "SQL query uses an unknown table."
        }


    # ==========================================
    # EXECUTE SQL
    # ==========================================

    try:

        cursor.execute(sql)

        rows = cursor.fetchall()


        # Get actual column names
        columns = []

        for column in cursor.description:

            columns.append(column[0])


    except Exception as error:

        connection.close()

        return {
            "error": str(error)
        }


    # ==========================================
    # CLOSE DATABASE
    # ==========================================

    connection.close()


    # ==========================================
    # RETURN RESULT TO FRONTEND
    # ==========================================

    return {
        "sql": sql,
        "columns": columns,
        "results": rows
    }