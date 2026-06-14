import json
import sqlite3
from pathlib import Path

def load_all_jsons(input_dir="data/2_silver", output_dir="data/3_gold"):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    db_path = output_path / "jobs.db"
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    
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

    json_files = sorted(list(input_path.glob("*.json")))
    if not json_files:
        print("⚠️ No Silver JSON files found to load.")
        connection.close()
        return []

    print("🥇 Gold:...")
    inserted_records = []
    skipped_count = 0
    
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            source_id = data.get("source_id")
            job_title = data.get("job_title")
            company = data.get("company")
            description = data.get("description")
            
            if not source_id or not job_title or not company:
                skipped_count += 1
                continue
                
            cursor.execute("SELECT 1 FROM jobs WHERE source_id = ?", (source_id,))
            exists = cursor.fetchone()
            
            # FIXED: Change update block behavior to skip duplicates and track metrics cleanly
            if exists:
                print(f"⏭️ Skipped (duplicate): {file_path.name}")
                skipped_count += 1
                continue
                
            cursor.execute(
                "INSERT INTO jobs (source_id, job_title, company, description, tech_stack) VALUES (?, ?, ?, ?, NULL)",
                (source_id, job_title, company, description),
            )
            connection.commit()
            print(f"✅ Inserted: {file_path.name}")
            inserted_records.append(file_path)
            
        except Exception:
            skipped_count += 1
            
    connection.close()
    
    # FIXED: Realigned logging summaries to show Total vs Inserted vs Skipped
    print("\n📊 Gold Summary:")
    print(f"Total: {len(json_files)} | Inserted: {len(inserted_records)} | Skipped: {skipped_count}")
    return inserted_records