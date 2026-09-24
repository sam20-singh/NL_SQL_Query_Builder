import sqlite3

connection = sqlite3.connect("database.db")
cursor = connection.cursor()


# Create departments table
cursor.execute("""
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY,
    department_name TEXT
)
""")


# Insert departments
cursor.execute("""
INSERT OR IGNORE INTO departments (id, department_name)
VALUES
    (1, 'IT'),
    (2, 'HR'),
    (3, 'Finance')
""")


# Check existing employees columns
cursor.execute("PRAGMA table_info(employees)")

columns = cursor.fetchall()

column_names = []

for column in columns:
    column_names.append(column[1])


# Add department_id if it does not exist
if "department_id" not in column_names:
    cursor.execute("""
    ALTER TABLE employees
    ADD COLUMN department_id INTEGER
    """)


# Connect existing employees to departments
cursor.execute("""
UPDATE employees
SET department_id = 1
WHERE department = 'IT'
""")

cursor.execute("""
UPDATE employees
SET department_id = 2
WHERE department = 'HR'
""")

cursor.execute("""
UPDATE employees
SET department_id = 3
WHERE department = 'Finance'
""")


# Save changes
connection.commit()


# Check employees
cursor.execute("""
SELECT * FROM employees
""")

employees = cursor.fetchall()

print("Employees:")
for employee in employees:
    print(employee)


# Check departments
cursor.execute("""
SELECT * FROM departments
""")

departments = cursor.fetchall()

print("\nDepartments:")
for department in departments:
    print(department)


connection.close()

print("\nDatabase setup completed")