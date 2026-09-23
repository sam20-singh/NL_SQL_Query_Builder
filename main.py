import requests
import sqlite3

user_question = input("Enter your question: ")

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

{user_question}
""",
        "stream": False
    }
)

ai_response = response.json()["response"]

if "```sql" in ai_response:
    sql = ai_response.split("```sql")[1].split("```")[0].strip()
else:
    sql = ai_response.strip()

print(sql)


sql_upper = sql.upper().strip()

if not sql_upper.startswith("SELECT"):
    print("Unsafe SQL query blocked!")
    exit()

if ";" in sql_upper[:-1]:
    print("Multiple SQL statements are not allowed!")
    exit()

print("Safe SQL query")


connection = sqlite3.connect("database.db")
cursor = connection.cursor()


try:
    cursor.execute(sql)
    rows = cursor.fetchall()

except Exception as error:
    print("SQL execution failed:", error)
    exit()

for row in rows:
    print(" | ".join(str(value) for value in row))