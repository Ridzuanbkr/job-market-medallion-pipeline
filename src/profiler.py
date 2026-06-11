import os
import sqlite3
from pathlib import Path

def run_data_profile(db_path):
    """
    Audits the jobs database and prints a structured Data Quality Report.
    Handles missing database files gracefully without crashing.
    """
    db_file = Path(db_path)
    
    # Program Idempotency: Check if database exists
    if not db_file.exists():
        print(f"❌ Database not found at {db_path}")
        return

    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()

    try:
        # 1. Total records
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_records = cursor.fetchone()[0]

        if total_records == 0:
            print("--- 🔍 DATA QUALITY REPORT ---")
            print("📈 Total Records: 0 (Database is empty)")
            return

        # 2. Null or Empty values count
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN job_title IS NULL OR job_title = '' THEN 1 ELSE 0 END),
                SUM(CASE WHEN company IS NULL OR company = '' THEN 1 ELSE 0 END),
                SUM(CASE WHEN description IS NULL OR description = '' THEN 1 ELSE 0 END)
            FROM jobs
        """)
        null_title, null_company, null_desc = cursor.fetchone()
        # Fallback to 0 if SUM returns None on empty datasets
        null_title = null_title or 0
        null_company = null_company or 0
        null_desc = null_desc or 0

        # 3. Average description length
        cursor.execute("SELECT CAST(AVG(LENGTH(description)) AS INT) FROM jobs")
        avg_desc_len = cursor.fetchone()[0] or 0

        # 4. Shortest description details
        cursor.execute("""
            SELECT LENGTH(description) as len, source_id, job_title 
            FROM jobs 
            WHERE description IS NOT NULL AND description != ''
            ORDER BY len ASC 
            LIMIT 1
        """)
        min_row = cursor.fetchone()
        min_len, min_sid, min_title = min_row if min_row else (0, "N/A", "N/A")

        # 5. Longest description details
        cursor.execute("""
            SELECT LENGTH(description) as len, source_id, job_title 
            FROM jobs 
            WHERE description IS NOT NULL AND description != ''
            ORDER BY len DESC 
            LIMIT 1
        """)
        max_row = cursor.fetchone()
        max_len, max_sid, max_title = max_row if max_row else (0, "N/A", "N/A")

        # Exact required output format layout
        print("--- 🔍 DATA QUALITY REPORT ---")
        print(f"📈 Total Records: {total_records}")
        print(f"❓ Missing Values -> job_title: {null_title}, company: {null_company}, description: {null_desc}")
        print(f"📝 Avg Description Length: {avg_desc_len} chars")
        print(f"⚠️ Shortest Description: {min_len} chars")
        print(f"   ↳ source_id: {min_sid} | job_title: {min_title}")
        print(f"🚨 Longest Description: {max_len} chars")
        print(f"   ↳ source_id: {max_sid} | job_title: {max_title}")

    except Exception as e:
        print(f"❌ Profiling Execution Error: {e}")
    finally:
        connection.close()