import sqlite3

conn = sqlite3.connect("./resources/jobs_d1.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT COUNT(*) AS non_empty_tech_stack
    FROM jobs
    WHERE tech_stack IS NOT NULL
""")

result = cursor.fetchone()
print(f"Number of jobs with non-empty tech stack: {result[0]}")

conn.close()
