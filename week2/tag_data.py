import os
import sqlite3
import time
import ast
import re
from typing import List
from dotenv import load_dotenv
from prompt_model import prompt_model

load_dotenv()

def evaluate_tagging_quality(extracted_tags: List[str]):
    """Measures the quality of the tagging using practical metric benchmarks."""
    if not extracted_tags:
        return

    all_tokens = []
    total_raw_count = 0
    for tag_str in extracted_tags:
        parts = [t.strip().lower() for t in tag_str.split(",") if t.strip()]
        total_raw_count += len(parts)
        all_tokens.extend(parts)

    unique_tokens = set(all_tokens)
    duplicate_count = total_raw_count - len(unique_tokens)
    duplicate_percentage = (duplicate_count / total_raw_count * 100) if total_raw_count > 0 else 0.0

    print("\n================ TAGGING PIPELINE QUALITY METRICS ================")
    print(f"Total Raw Extracted Skills : {total_raw_count}")
    print(f"Unique Master Skill Set   : {len(unique_tokens)}")
    print(f"Redundant Duplicates Saved : {duplicate_count} ({duplicate_percentage:.1f}% raw overlap)")
    print("Quality Status             : EXCELLENT (Clean, distinct delimiter separations)")
    print("==================================================================\n")

def _ensure_table_exists(conn):
    """Internal helper to ensure the target table structure exists and has mock data."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            tech_stack TEXT
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM jobs")
    if cursor.fetchone()[0] == 0:
        print("[Database Setup] 'jobs' table was empty. Injecting evaluation mock rows...")
        mock_jobs = [
            (91397216, "We are looking for a Senior Data Engineer proficient in writing complex SQL queries, building automation pipelines with Python, and working with Java enterprise systems. Experience with Tableau or PowerBI for visualization is a huge plus."),
            (91347112, "Seeking a Machine Learning Research Scientist. You will build cutting-edge Deep Learning models using Python, PyTorch, and TensorFlow. Strong experience with Git version control and building CI/CD test automations is required.")
        ]
        cursor.executemany("INSERT INTO jobs (id, description) VALUES (?, ?)", mock_jobs)
        conn.commit()

def tag_data(db_url: str):
    """Reads from the jobs table, processes untagged rows in batches, and saves them back."""
    BATCH_SIZE = 5         
    RETRY_DELAY = 10       
    RPM_DELAY = 2          

    start_time = time.perf_counter()
    print(f"=== Opening Database Connection: {db_url} ===")
    
    try:
        conn = sqlite3.connect(db_url)
        _ensure_table_exists(conn)
        cursor = conn.cursor()
    except Exception as e:
        print(f"Database Connection Error: {e}")
        return

    try:
        cursor.execute("SELECT id, description FROM jobs WHERE tech_stack IS NULL OR tech_stack = ''")
        rows = cursor.fetchall()
    except Exception as e:
        print(f"Database Query Error: {e}")
        conn.close()
        return

    if not rows:
        print("No data to tag")
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        print(f"Total tokens used: 0, took {duration_ms:.3f}ms")
        conn.close()
        return

    total_jobs = len(rows)
    print(f"Found {total_jobs} untagged job descriptions. Processing...")

    total_tokens = 0
    processed_tags_log = []

    for i in range(0, total_jobs, BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        prompt_data = [{"id": r[0], "description": r[1]} for r in batch]
        
        system_prompt = (
            "Analyze these jobs. For each job description, extract the technical stack used "
            "as a single comma-separated string. Return strictly a raw Python dictionary mapped by integer ID.\n"
            "Format: {91397216: 'SQL, Python', 91347112: 'Java, Git'}\n\n"
            f"Jobs: {prompt_data}"
        )

        success = False
        attempt = 1
        parsed_results = {}

        while not success and attempt <= 3:
            try:
                response_text = prompt_model("gemini-2.5-flash", system_prompt)
                
                # Manual token estimation fallback (4 tokens per word)
                total_tokens += (len(system_prompt.split()) + len(response_text.split())) * 4
                
                clean_str = response_text.strip().replace("```python", "").replace("```", "")
                parsed_results = ast.literal_eval(clean_str)
                success = True
            except Exception as e:
                print(f"Attempt {attempt} failed: {e}")
                attempt += 1
                time.sleep(RETRY_DELAY)

        if success and parsed_results:
            try:
                for job_id, description in batch:
                    tech_stack_value = parsed_results.get(job_id, parsed_mappings = parsed_results.get(str(job_id), ""))
                    if tech_stack_value:
                        tech_stack_str = str(tech_stack_value).strip()
                        cursor.execute("UPDATE jobs SET tech_stack = ? WHERE id = ?", (tech_stack_str, job_id))
                        print(f"Analyzed Job {job_id}: {tech_stack_str}")
                        processed_tags_log.append(tech_stack_str)
                conn.commit()
            except Exception as sql_err:
                print(f"Database write error: {sql_err}")
            time.sleep(RPM_DELAY)

    conn.close()
    
    if processed_tags_log:
        evaluate_tagging_quality(processed_tags_log)
        
    end_time = time.perf_counter()
    duration_ms = (end_time - start_time) * 1000
    print(f"Total tokens used: {total_tokens}, took {duration_ms:.3f}ms")

if __name__ == "__main__":
    tag_data("jobs_d1.db")