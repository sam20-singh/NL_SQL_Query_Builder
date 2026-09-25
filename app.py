from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import sqlite3
import re


app = FastAPI()


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
        "message": "NL → SQL Query Builder API is running"
    }


# ==========================================
# GET DATABASE SCHEMA
# ==========================================

def get_database_schema(cursor):

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
    """)

    tables = cursor.fetchall()

    schema_parts = []

    allowed_tables = {}


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


        allowed_tables[
            table_name.upper()
        ] = [
            column.upper()
            for column in column_names
        ]


        schema_parts.append(
            f"Table: {table_name}\n"
            f"Columns: {', '.join(column_names)}"
        )


    schema = "\n\n".join(
        schema_parts
    )


    return schema, allowed_tables


# ==========================================
# EXTRACT TABLES FROM SQL
# ==========================================

def extract_tables(sql):

    tables = []


    patterns = [

        r"\bFROM\s+([A-Za-z_][A-Za-z0-9_]*)",

        r"\bJOIN\s+([A-Za-z_][A-Za-z0-9_]*)"

    ]


    for pattern in patterns:

        matches = re.findall(
            pattern,
            sql,
            re.IGNORECASE
        )


        for table in matches:

            table_upper = table.upper()


            if table_upper not in tables:

                tables.append(
                    table_upper
                )


    return tables


# ==========================================
# VALIDATE TABLES
# ==========================================

def validate_tables(sql, allowed_tables):

    tables_used = extract_tables(sql)


    if not tables_used:

        return (
            False,
            "No valid table was found in the generated SQL."
        )


    for table in tables_used:

        if table not in allowed_tables:

            return (
                False,
                f"Table '{table}' does not exist in the database."
            )


    return True, ""


# ==========================================
# VALIDATE SQL
# ==========================================

def validate_sql(sql, allowed_tables):

    sql_upper = sql.upper().strip()


    # --------------------------------------
    # SELECT ONLY
    # --------------------------------------

    if not sql_upper.startswith("SELECT"):

        return (
            False,
            "Only SELECT queries are allowed."
        )


    # --------------------------------------
    # MULTIPLE STATEMENTS
    # --------------------------------------

    if ";" in sql_upper[:-1]:

        return (
            False,
            "Multiple SQL statements are not allowed."
        )


    # --------------------------------------
    # SQL COMMENTS
    # --------------------------------------

    if "--" in sql_upper:

        return (
            False,
            "SQL comments are not allowed."
        )


    if "/*" in sql_upper or "*/" in sql_upper:

        return (
            False,
            "SQL comments are not allowed."
        )


    # --------------------------------------
    # DANGEROUS SQL OPERATIONS
    # --------------------------------------

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

        pattern = rf"\b{keyword}\b"


        if re.search(
            pattern,
            sql_upper
        ):

            return (
                False,
                f"Blocked dangerous SQL operation: {keyword}"
            )


    # --------------------------------------
    # TABLE VALIDATION
    # --------------------------------------

    valid, error_message = validate_tables(
        sql,
        allowed_tables
    )


    if not valid:

        return (
            False,
            error_message
        )


    return True, ""


# ==========================================
# QUERY ENDPOINT
# ==========================================

@app.post("/query")
def query(request: QueryRequest):

    question = request.question.strip()


    # --------------------------------------
    # EMPTY QUESTION
    # --------------------------------------

    if not question:

        return {
            "error": "Please enter a question."
        }


    # --------------------------------------
    # CONNECT DATABASE
    # --------------------------------------

    connection = sqlite3.connect(
        "database.db"
    )

    cursor = connection.cursor()


    try:

        # ==================================
        # GET DATABASE SCHEMA
        # ==================================

        schema, allowed_tables = (
            get_database_schema(cursor)
        )


        print("\n==============================")

        print("DATABASE SCHEMA")

        print("==============================")

        print(schema)


        # ==================================
        # SEND QUESTION TO QWEN
        # ==================================

        try:

            response = requests.post(

                "http://localhost:11434/api/generate",

                json={

                    "model": "qwen2.5:7b",

                    "prompt": f"""
You are an expert SQLite SQL query generator.

Your job is to convert the user's natural-language
question into ONE SQL SELECT query.

DATABASE SCHEMA:

{schema}

RULES:

1. Return ONLY the SQL query.
2. Do not return explanations.
3. Do not return Markdown.
4. Only generate SELECT queries.
5. Never generate INSERT.
6. Never generate UPDATE.
7. Never generate DELETE.
8. Never generate DROP.
9. Never generate ALTER.
10. Never generate CREATE.
11. Never generate PRAGMA.
12. Use SQLite syntax.
13. Use only tables and columns shown in the schema.
14. Use JOIN when multiple tables are required.
15. Use GROUP BY for grouped calculations.
16. Use ORDER BY when sorting is requested.
17. Use LIMIT when the user asks for the highest,
    lowest, first, last, top, or a limited number of rows.
18. Do not invent tables.
19. Do not invent columns.
20. Return exactly one SQL query.

USER QUESTION:

{question}

Return ONLY the SQL query.
""",

                    "stream": False

                },

                timeout=120
            )


        except requests.exceptions.RequestException:

            return {
                "error":
                    "AI service is unavailable. "
                    "Make sure Ollama is running."
            }


        # ==================================
        # OLLAMA RESPONSE CHECK
        # ==================================

        if response.status_code != 200:

            return {
                "error":
                    "Qwen returned an error."
            }


        ai_data = response.json()


        ai_response = ai_data.get(
            "response",
            ""
        ).strip()


        if not ai_response:

            return {
                "error":
                    "Qwen did not generate a SQL query."
            }


        print("\n==============================")

        print("QWEN RESPONSE")

        print("==============================")

        print(ai_response)


        # ==================================
        # EXTRACT SQL
        # ==================================

        if "```sql" in ai_response.lower():

            sql = re.split(
                r"```sql",
                ai_response,
                flags=re.IGNORECASE
            )[1]

            sql = sql.split(
                "```"
            )[0].strip()


        elif "```" in ai_response:

            sql = ai_response.split(
                "```"
            )[1].strip()


        else:

            sql = ai_response.strip()


        # Remove final semicolon
        sql = sql.rstrip(";").strip()


        print("\n==============================")

        print("GENERATED SQL")

        print("==============================")

        print(sql)


        # ==================================
        # VALIDATE SQL
        # ==================================

        valid, error_message = validate_sql(
            sql,
            allowed_tables
        )


        if not valid:

            return {
                "error": error_message,
                "sql": sql
            }


        # ==================================
        # EXECUTE SQL
        # ==================================

        try:

            cursor.execute(sql)

            rows = cursor.fetchall()


            # Get actual column names

            columns = []


            if cursor.description:

                for column in cursor.description:

                    columns.append(
                        column[0]
                    )


        except sqlite3.Error as error:

            return {
                "error":
                    f"SQL execution failed: {error}",

                "sql": sql
            }


        # ==================================
        # RETURN DATA
        # ==================================

        return {

            "question": question,

            "sql": sql,

            "columns": columns,

            "results": rows

        }


    finally:

        connection.close()