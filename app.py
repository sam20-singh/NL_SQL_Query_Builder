from fastapi import FastAPI
from pydantic import BaseModel
import requests
import sqlite3

app = FastAPI()


class QueryRequest(BaseModel):
    question: str


@app.get("/")
def home():
    return {"message": "NL SQL Query Builder API is running"}


@app.post("/query")
def query(request: QueryRequest):

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:7b",
            "prompt": f"""
You are a SQL assistant.

Database table:
employees

Columns:
id - employee ID
name - employee name
department - employee department
salary - employee salary

Convert this request into SQL:

{request.question}
""",
            "stream": False
        }
    )


    ai_response = response.json()["response"]

    if "```sql" in ai_response:
        sql = ai_response.split("```sql")[1].split("```")[0].strip()
    else:
        sql = ai_response.strip()

    sql_upper = sql.upper().strip()

    if not sql_upper.startswith("SELECT"):
        return {
            "error": "Unsafe SQL query blocked"
        }

    if ";" in sql_upper[:-1]:
        return {
            "error": "Multiple SQL statements are not allowed"
        }

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    try:
        cursor.execute(sql)
        rows = cursor.fetchall()

    except Exception as error:
        return {
            "error": str(error)
        }

    connection.close()

    return {
        "sql": sql,
        "results": rows
    }