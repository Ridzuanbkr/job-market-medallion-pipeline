import os
import sqlite3
import time
import ast
from dotenv import load_dotenv
from prompt_model import prompt_model

# Load environment variables
load_dotenv()

def _ensure_table_exists(conn):
    """Internal helper to ensure the target table structure matches criteria."""
    cursor = conn.cursor()
    # Create table if missing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            tech_stack TEXT
        )
    """)
    
    # Check if it has rows, insert realistic evaluation mock logs if empty
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
    """
    Reads from the jobs table in a SQLite DB, processes untagged rows in batches
    using an LLM to extract tech stacks, and saves them back to the database.
    """
    BATCH_SIZE = 5         
    RETRY_DELAY = 10       
    RPM_DELAY = 6          

    print(f"=== Opening Database Connection: {db_url} ===")
    
    try:
        conn = sqlite3.connect(db_url)
        # Run our safety structure setup check
        _ensure_table_exists(conn)
        cursor = conn.cursor()
    except Exception as e:
        print(f"Database Connection Error: {e}")
        return

    # Fetch all rows where tech_stack is missing or empty
    try:
        cursor.execute("SELECT id, description FROM jobs WHERE tech_stack IS NULL OR tech_stack = ''")
        rows = cursor.fetchall()
    except Exception as e:
        print(f"Database Query Error: {e}")
        conn.close()
        return

    if not rows:
        print("No missing tech_stack profiles found. Database is fully updated!")
        conn.close()
        return

    total_jobs = len(rows)
    print(f"Found {total_jobs} untagged job descriptions. Processing in batches of {BATCH_SIZE}...")

    # Process records in explicit batches
    for i in range(0, total_jobs, BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        batch_index = i // BATCH_SIZE
        
        prompt_data = [{"id": r[0], "description": r[1]} for r in batch]
        
        system_prompt = (
            "You are a tech stack extraction engine. Analyze the following list of jobs. "
            "For each job description, extract the technical stack used (e.g., programming languages, frameworks, databases, tools) "
            "as a single comma-separated string. "
            "Return your output strictly as a Python dictionary where keys are the job IDs (integers) and values are the tech stack strings.\n"
            "Example Output Format: {91397216: 'SQL, Python, Java', 91347112: 'Java, PyTorch, Git'}\n"
            "Do not include code blocks, markdown wrapper ticks, or conversational text. Return only the dictionary literal.\n\n"
            f"Jobs to process: {prompt_data}"
        )

        success = False
        attempt = 1
        parsed_results = {}

        while not success and attempt <= 3:
            try:
                response_text = prompt_model("gemini-2.5-flash", system_prompt)
                
                clean_str = response_text.strip().replace("```python", "").replace("```", "")
                parsed_results = ast.literal_eval(clean_str)
                
                if len(parsed_results) != len(batch):
                    raise ValueError("Mismatch between batch size and response size.")
                
                success = True
                
            except Exception as e:
                print(f"[Batch {batch_index}] Attempt {attempt} failed: {e}")
                attempt += 1
                time.sleep(RETRY_DELAY)

        if success and parsed_results:
            try:
                for job_id, description in batch:
                    tech_stack_value = parsed_results.get(job_id, parsed_results.get(str(job_id), ""))
                    
                    if tech_stack_value:
                        tech_stack_str = str(tech_stack_value).strip()
                        cursor.execute("UPDATE jobs SET tech_stack = ? WHERE id = ?", (tech_stack_str, job_id))
                        print(f"Analyzed Job {job_id}: {tech_stack_str}")
                
                conn.commit()
                
            except Exception as sql_err:
                print(f"Database write error encountered during batch update processing: {sql_err}")
            
            time.sleep(RPM_DELAY)
        else:
            print(f"[Batch {batch_index}] Skipping batch permanently after exceeding maximum failure limits.")

    conn.close()
    print("\n=== Data Tagging Complete ===")

if __name__ == "__main__":
    tag_data("jobs_d1.db")