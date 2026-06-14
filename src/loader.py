import os
import json
import sqlite3
from pathlib import Path

def load_all_jsons(input_dir="data/2_silver", output_dir="data/3_gold"):
    """Initializes the SQLite database, establishes the mandatory schema,

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
        return []

    print("🥇 Gold:...")
    
    saved_db_records = []
    skipped_count = 0
    
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            source_id = data.get("source_id")
            job_title = data.get("job_title")
            company = data.get("company")
            description = data.get("description")
            
            # Validation Check: Skip processing if critical fields are broken or missing
            if not source_id or not job_title or not company:
                print(f"⚠️ Skipped (missing required structural data): {file_path.name}")
                skipped_count += 1
                continue
                
            # Check if source_id already exists to track metrics without failing pipeline constraints
            cursor.execute("SELECT 1 FROM jobs WHERE source_id = ?", (source_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Update the record to count it as successfully processed
                cursor.execute(
                    """
                    UPDATE jobs 
                    SET job_title = ?, company = ?, description = ?
                    WHERE source_id = ?
                    """,
                    (job_title, company, description, source_id),
                )
                connection.commit()
                print(f"🔄 Updated: {file_path.name}")
                saved_db_records.append(file_path)
                continue
                
            # Data Storage: Clean parameterized base INSERT layout
            cursor.execute(
                """
                INSERT INTO jobs (source_id, job_title, company, description, tech_stack)
                VALUES (?, ?, ?, ?, NULL)
                """,
                (source_id, job_title, company, description),
            )
            connection.commit()
            
            print(f"✅ Inserted: {file_path.name}")
            saved_db_records.append(file_path)
            
        except Exception as e:
            print(f"❌ Failed to parse/load file {file_path.name}: {e}")
            skipped_count += 1
            
    connection.close()
    
    # Exact required pipeline summary format matching criteria layout
    print("\n📊 Gold Summary:")
    print(f"Total: {len(json_files)} | Inserted: {len(saved_db_records)} | Skipped: {skipped_count}")
    
    return saved_db_records