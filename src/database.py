import sqlite3
from pathlib import Path


def load_gold_database(cleaned_jobs: list[dict], db_name: str = "jobs.db") -> int:
    """
    Creates a SQLite database and inserts the cleaned job data.
    Ensures idempotency by overwriting existing records with the same source_id.
    """
    db_path = Path(db_name)

    # Connect to SQLite (it create the jobs.db automatically if missing)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1.Create the single table with the exact schema requested
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            source_id TEXT PRIMARY KEY,
            job_title TEXT,
            company TEXT,
            description TEXT,
            tech_stack TEXT
        )
    """
    )

    # 2.Insert the data safely using 'INSERT OR REPLACE' This maintain Idempotency
    inserted_count = 0
    for job in cleaned_jobs:
        cursor.execute(
            """
            INSERT OR REPLACE INTO jobs
            (source_id, job_title, company, description, tech_stack)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                job["source_id"],
                job["job_title"],
                job["company"],
                job["description"],
                job["tech_stack"],
            ),
        )
        inserted_count += 1

    conn.commit()
    conn.close()

    print(f"Database Sync Complete. {inserted_count} rows written to '{db_name}'.")
    return inserted_count
