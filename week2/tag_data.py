import sqlite3
import time
import ast
from pathlib import Path
from dotenv import load_dotenv
from prompt_model import prompt_model

# Load environment variables
load_dotenv()

def tag_data(db_filename: str):
    """
    Reads from the original jobs table using 'source_id', processes untagged rows 
    in batches using Gemini, and updates the original tech_stack column in-place.
    Uses pathlib to dynamically target files inside the 'resources' directory.
    """
    BATCH_SIZE = 5         
    RETRY_DELAY = 10       
    RPM_DELAY = 6          

    # Using pathlib to build an absolute path to /resources/jobs_d1.db
    script_dir = Path(__file__).resolve().parent
    db_url = script_dir / "resources" / db_filename

    print("=== Checking Database Path ===", flush=True)
    print(f"Looking for database at: {db_url}", flush=True)

    # Explicitly verify the file exists before letting SQLite touch it
    if not db_url.exists():
        print(f"[Database Error] CRITICAL: Could not find '{db_filename}' at {db_url}!", flush=True)
        print("Please ensure your 'resources' folder and the database file exist alongside this script.", flush=True)
        return

    print("=== Opening Database Connection ===", flush=True)
    try:
        conn = sqlite3.connect(db_url)
        cursor = conn.cursor()
        
        # Double check that the expected table actually exists inside the found file
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
        if not cursor.fetchone():
            print("[Database Error] The file exists, but it does not contain a 'jobs' table!", flush=True)
            conn.close()
            return
            
    except Exception as e:
        print(f"Database Connection Error: {e}", flush=True)
        return

    # Fetch rows using 'source_id' instead of 'id' to match your original table
    try:
        cursor.execute("SELECT source_id, description FROM jobs WHERE tech_stack IS NULL OR tech_stack = ''")
        rows = cursor.fetchall()
    except Exception as e:
        print(f"Database Query Error: {e}", flush=True)
        conn.close()
        return

    if not rows:
        print("No missing tech_stack profiles found. Original database is fully updated!", flush=True)
        conn.close()
        return

    total_jobs = len(rows)
    print(f"Found {total_jobs} untagged job descriptions. Processing in batches of {BATCH_SIZE}...", flush=True)

    for i in range(0, total_jobs, BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        batch_index = i // BATCH_SIZE
        
        # Mapping using source_id to match original schema
        prompt_data = [{"source_id": r[0], "description": r[1]} for r in batch]
        
        system_prompt = (
            "You are a tech stack extraction engine. Analyze the following list of jobs. "
            "For each job description, extract the technical stack used (e.g., programming languages, frameworks, databases, tools) "
            "as a single comma-separated string. "
            "Return your output strictly as a Python dictionary where keys are the job source_ids (strings) and values are the tech stack strings.\n"
            "Example Output Format: {'91397216': 'SQL, Python, Java', '91347112': 'Java, PyTorch, Git'}\n"
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
                print(f"[Batch {batch_index}] Attempt {attempt} failed: {e}", flush=True)
                attempt += 1
                time.sleep(RETRY_DELAY)

        if success and parsed_results:
            try:
                for source_id, description in batch:
                    # Robust lookup check (checks string key first, then integer key, then defaults to empty string)
                    tech_stack_value = parsed_results.get(str(source_id), parsed_results.get(int(source_id) if str(source_id).isdigit() else source_id, ""))
                    
                    # Logic Fix: Safe fallback assignment so empty values update the table and clear the backlog
                    if tech_stack_value and str(tech_stack_value).strip():
                        tech_stack_str = str(tech_stack_value).strip()
                    else:
                        tech_stack_str = "None (No tech keywords found)"
                    
                    # This now executes outside of the limiting wrapper check
                    cursor.execute("UPDATE jobs SET tech_stack = ? WHERE source_id = ?", (tech_stack_str, source_id))
                    print(f"Analyzed Job {source_id}: {tech_stack_str}", flush=True)
                
                conn.commit()
                print(f"[Batch {batch_index}] Saved to original database successfully.\n", flush=True)
                
            except Exception as sql_err:
                print(f"Database write error encountered during batch update processing: {sql_err}", flush=True)
            
            time.sleep(RPM_DELAY)
        else:
            print(f"[Batch {batch_index}] Skipping batch permanently after exceeding maximum failure limits.", flush=True)

    conn.close()
    print("\n=== Data Tagging Complete ===", flush=True)

if __name__ == "__main__":
    tag_data("jobs_d1.db")