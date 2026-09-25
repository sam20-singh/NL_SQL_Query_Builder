from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from pathlib import Path
import os
import re
import sqlite3


# ==========================================
# APPLICATION
# ==========================================

app = FastAPI()


# ==========================================
# GROQ CLIENT
# ==========================================

api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    raise RuntimeError(
        "GROQ_API_KEY environment variable is not set."
    )

client = Groq(
    api_key=api_key
)


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ==========================================
# DATABASE PATH
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = BASE_DIR / "database.db"


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
# DATABASE CONNECTION
# ==========================================

def get_database_connection():

    database_uri = (
        f"file:{DATABASE_PATH}?mode=ro"
    )

    return sqlite3.connect(
        database_uri,
        uri=True
    )


# ==========================================
# SQL AUTHORISER
# ==========================================

def sql_authorizer(
    action,
    arg1,
    arg2,
    database_name,
    trigger_name
):

    blocked_actions = {

        sqlite3.SQLITE_INSERT,
        sqlite3.SQLITE_UPDATE,
        sqlite3.SQLITE_DELETE,

        sqlite3.SQLITE_CREATE_INDEX,
        sqlite3.SQLITE_CREATE_TABLE,
        sqlite3.SQLITE_CREATE_TEMP_INDEX,
        sqlite3.SQLITE_CREATE_TEMP_TABLE,
        sqlite3.SQLITE_CREATE_TEMP_TRIGGER,
        sqlite3.SQLITE_CREATE_TEMP_VIEW,
        sqlite3.SQLITE_CREATE_TRIGGER,
        sqlite3.SQLITE_CREATE_VIEW,

        sqlite3.SQLITE_DROP_INDEX,
        sqlite3.SQLITE_DROP_TABLE,
        sqlite3.SQLITE_DROP_TEMP_INDEX,
        sqlite3.SQLITE_DROP_TEMP_TABLE,
        sqlite3.SQLITE_DROP_TEMP_TRIGGER,
        sqlite3.SQLITE_DROP_TEMP_VIEW,
        sqlite3.SQLITE_DROP_TRIGGER,
        sqlite3.SQLITE_DROP_VIEW,

        sqlite3.SQLITE_ATTACH,
        sqlite3.SQLITE_DETACH,

        sqlite3.SQLITE_ALTER_TABLE,
        sqlite3.SQLITE_REINDEX,
        sqlite3.SQLITE_ANALYZE,
        sqlite3.SQLITE_PRAGMA
    }

    if action in blocked_actions:

        return sqlite3.SQLITE_DENY

    return sqlite3.SQLITE_OK


# ==========================================
# EXTRACT SQL FROM AI RESPONSE
# ==========================================

def extract_sql(ai_response):

    ai_response = ai_response.strip()


    if "```sql" in ai_response:

        sql = (
            ai_response
            .split("```sql", 1)[1]
            .split("```", 1)[0]
            .strip()
        )

    elif "```" in ai_response:

        sql = (
            ai_response
            .split("```", 1)[1]
            .split("```", 1)[0]
            .strip()
        )

    else:

        sql = ai_response


    return sql.strip()


# ==========================================
# SQL VALIDATION
# ==========================================

def validate_sql(sql):

    sql = sql.strip()


    # ------------------------------------------
    # CHECK EMPTY SQL
    # ------------------------------------------

    if not sql:

        return (
            "AI returned an empty SQL query."
        )


    # ------------------------------------------
    # SELECT ONLY
    # ------------------------------------------

    if not re.match(
        r"^SELECT\b",
        sql,
        re.IGNORECASE
    ):

        return (
            "Only SELECT queries are allowed."
        )


    # ------------------------------------------
    # BLOCK MULTIPLE STATEMENTS
    # ------------------------------------------

    if ";" in sql[:-1]:

        return (
            "Multiple SQL statements are not allowed."
        )


    # ------------------------------------------
    # REMOVE TRAILING SEMICOLON
    # ------------------------------------------

    if sql.endswith(";"):

        sql = sql[:-1].strip()


    # ------------------------------------------
    # BLOCK SQL COMMENTS
    # ------------------------------------------

    if (
        "--" in sql
        or "/*" in sql
        or "*/" in sql
    ):

        return (
            "SQL comments are not allowed."
        )


    return None


# ==========================================
# QUERY ENDPOINT
# ==========================================

@app.post("/query")
def query(request: QueryRequest):

    connection = None


    try:

        # ==========================================
        # CONNECT TO DATABASE
        # ==========================================

        connection = get_database_connection()

        cursor = connection.cursor()


        # ==========================================
        # GET DATABASE TABLES
        # ==========================================

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
        """)

        tables = cursor.fetchall()


        # ==========================================
        # BUILD DATABASE SCHEMA
        # ==========================================

        schema_parts = []


        for table in tables:

            table_name = table[0]


            cursor.execute(
                f'PRAGMA table_info("{table_name}")'
            )


            columns = cursor.fetchall()


            column_names = []


            for column in columns:

                column_names.append(
                    column[1]
                )


            table_schema = (
                f"Table: {table_name}\n"
                f"Columns: {', '.join(column_names)}"
            )


            schema_parts.append(
                table_schema
            )


        schema = "\n\n".join(
            schema_parts
        )


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

- Generate only SELECT queries.
- You may use JOIN when the request requires data from multiple tables.
- Use only tables and columns that exist in the schema.
- Do not create tables.
- Do not modify the database.
- Do not use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA, ATTACH, or DETACH.
- Return only the SQL query.
"""
                    },

                    {
                        "role": "user",

                        "content": request.question
                    }

                ]
            )


        except Exception:

            return {
                "error": "AI service is unavailable."
            }


        # ==========================================
        # GET AI RESPONSE
        # ==========================================

        ai_response = (
            response
            .choices[0]
            .message
            .content
        )


        if not ai_response:

            return {
                "error": "AI returned an empty response."
            }


        # ==========================================
        # EXTRACT SQL
        # ==========================================

        sql = extract_sql(
            ai_response
        )


        # ==========================================
        # VALIDATE SQL
        # ==========================================

        validation_error = validate_sql(
            sql
        )


        if validation_error:

            return {
                "error": validation_error
            }


        # ==========================================
        # ENABLE SQL AUTHORISER
        # ==========================================

        connection.set_authorizer(
            sql_authorizer
        )


        # ==========================================
        # EXECUTE SQL
        # ==========================================

        try:

            cursor.execute(sql)

            rows = cursor.fetchall()


            # --------------------------------------
            # GET COLUMN NAMES
            # --------------------------------------

            columns = []


            if cursor.description:

                for column in cursor.description:

                    columns.append(
                        column[0]
                    )


        except sqlite3.Error as error:

            return {
                "error": (
                    f"SQL execution failed: {error}"
                )
            }


        # ==========================================
        # RETURN RESULTS
        # ==========================================

        return {

            "sql": sql,

            "columns": columns,

            "results": rows
        }


    except Exception:

        return {
            "error": (
                "An unexpected server error occurred."
            )
        }


    finally:

        if connection:

            connection.close()