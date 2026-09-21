import sqlite3
import request

connection = sqlite3.connect("database.db")

cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    name TEXT,
    department TEXT,
    salary INTEGER
)
""")
connection = sqlite3.connect("database.db")

cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    name TEXT,
    department TEXT,
    salary INTEGER
)
""")

connection.commit()
#salary=int(input("Enter your salary :"))

#cursor.execute("INSERT INTO employees (id, name, department, salary) VALUES (1, 'Arun', 'IT', 60000)")
#cursor.execute("INSERT INTO employees (id, name, department, salary) VALUES (2, 'John', 'HR', 50000)")
#cursor.execute("INSERT INTO employees (id, name, department, salary) VALUES (3, 'Alice', 'Finance', 70000)")
cursor.execute("SELECT department, COUNT(*) FROM employees GROUP BY department")
connection.commit()

print("Employee added!")

#cursor.execute("SELECT * FROM employees WHERE department = 'IT'")
#cursor.execute("SELECT * FROM employees ORDER BY salary DESC LIMIT 1")
rows = cursor.fetchall()

for row in rows:
    print(row)
#print("Employee added!")
response = requests.post(
    url,
    json={"question": "Show IT employees"}
)


connection.commit()


##print("Employees table created!")