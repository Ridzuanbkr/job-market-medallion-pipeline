import sys
from src.extract import ingest_all_mhtml
from src.process import process_all_html
from src.loader import load_all_jsons
from src.profiler import run_data_profile


def show_usage():
    print("Usage: python main.py [ingest|process|load|profile|all]")
    sys.exit(1)


def execute_pipeline(command):
    """Helper map to handle standalone execution blocks cleanly."""
    print("====================================================")
    print(f"--- Pipeline Command Triggered: [{command.upper()}] ---")
    print("====================================================")
    
    if command == "ingest":
        try:
            print("\n[Executing] Step 1: Decoding MHTML to data/1_bronze...\n")
            raw_files = ingest_all_mhtml()
            extracted_count = len(raw_files)
            print(f"\n✅ 📊 Bronze Summary:\n")
            print(f"Total: 100 | Extracted: {extracted_count} | Failed: {100 - extracted_count}")
        except Exception as e:
            print(f"❌ Ingestion Critical Fault: {e}")
            sys.exit(1)

    elif command == "process":
        try:
            print("\n[Executing] Step 2: Cleaning & validating data to data/2_silver...\n")
            process_all_html()
        except Exception as e:
            print(f"❌ Processing Critical Fault: {e}")
            sys.exit(1)

    elif command == "load":
        try:
            print("\n[Executing] Step 3: Storing Silver data into Gold SQLite DB...\n")
            # Connect the outputs directly to the execution function parameters
            load_all_jsons()
        except Exception as e:
            print(f"❌ Loading Critical Fault: {e}")
            sys.exit(1)

    elif command == "profile":
        try:
            print("\n[Executing] Step 4: Generating Data Quality Audit Report...\n")
            run_data_profile(db_path="data/3_gold/jobs.db")
        except Exception as e:
            print(f"❌ Profiling Critical Fault: {e}")
            sys.exit(1)


def main():
    if len(sys.argv) < 2:
        show_usage()

    target_command = sys.argv[1].lower()

    valid_commands = ["ingest", "process", "load", "profile", "all"]
    if target_command not in valid_commands:
        show_usage()

    if target_command == "all":
        print("🌀 Starting Full End-to-End ETL Pipeline In Order...")
        execute_pipeline("ingest")
        execute_pipeline("process")
        execute_pipeline("load")
        execute_pipeline("profile")
        print("\n🏆 End-to-End ETL Pipeline successfully finished running!")
    else:
        execute_pipeline(target_command)


if __name__ == "__main__":
    main()