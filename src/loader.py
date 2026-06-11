import os
import json
import sqlite3
from pathlib import Path

def load_all_jsons(input_dir, output_dir):
    """
    Initializes the SQLite database, establishes the mandatory schema,
    and idempotently loads Silver JSON data into jobs.db with strict tracking.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Program Idempotency: Create directory if it's missing
    output_path.mkdir(parents=True, exist_ok=True)
    
    db_path = output_path / "jobs.db"
    
    # Initialize connection
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    
    # Data Modeling: Create schema with tech_stack column (NULL allowed for now)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            source_id TEXT PRIMARY KEY,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            description TEXT,
            tech_stack TEXT
        )
    """)
    connection.commit()

    # Gather silver json files
    json_files = sorted(list(input_path.glob("*.json")))
    if not json_files:
        print("⚠️ No Silver JSON files found to load.")
        connection.close()
        return

    print("🥇 Gold:...")
    
    total_count = len(json_files)
    inserted_count = 0
    skipped_count = 0
    
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            source_id = data.get("source_id")
            job_title = data.get("job_title")
            company = data.get("company")
            description = data.get("description")
            
            # Check if source_id already exists to track 'Skipped' vs 'Inserted'
            cursor.execute("SELECT 1 FROM jobs WHERE source_id = ?", (source_id,))
            exists = cursor.fetchone()
            
            if exists:
                print(f"⏭️ Skipped (duplicate): {file_path.name}")
                skipped_count += 1
                continue
                
            # Data Storage & Idempotency: Use INSERT INTO with safe tracking
            cursor.execute(
                """
                INSERT INTO jobs (source_id, job_title, company, description, tech_stack)
                VALUES (?, ?, ?, ?, NULL)
                """,
                (source_id, job_title, company, description),
            )
            connection.commit()
            
            print(f"✅ Inserted: {file_path.name}")
            inserted_count += 1
            
        except Exception as e:
            print(f"❌ Failed: {file_path.name} Due to: {e}")
            
    connection.close()
    
    # Exact required summary format
    print("\n📊 Gold Summary:")
    print(f"Total: {total_count} | Inserted: {inserted_count} | Skipped: {skipped_count}")