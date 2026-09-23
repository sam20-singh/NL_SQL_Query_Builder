import requests
import sqlite3

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen2.5:7b",
        "prompt": """
You are a SQL assistant.

Database table:
employees

Columns:
id - employee ID
name - employee name
department - employee department
salary - employee salary

Convert this request into SQL:
Show employees whose salary is greater than 50000
""",
        "stream": False
    }
)

print(response.json()["response"])



connection = sqlite3.connect("database.db")
cursor = connection.cursor()

cursor.execute("SELECT * FROM employees WHERE salary > 50000")

rows = cursor.fetchall()

for row in rows:
    print(row)