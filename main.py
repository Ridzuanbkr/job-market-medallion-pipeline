import sys
from src.extract import ingest_all_mhtml
from src.process import process_all_html
from src.loader import load_all_jsons
from src.profiler import run_data_profile


def show_usage():
    print("Usage: python main.py [ingest|process|load|profile|all]")
    sys.exit(1)


def execute_pipeline(command):
    print("====================================================")
    print(f"--- Pipeline Command Triggered: [{command.upper()}] ---")
    print("====================================================")
    
    if command == "ingest":
        try:
            ingest_all_mhtml()
        except Exception as e:
            print(f"❌ Ingestion Fault: {e}")
            sys.exit(1)

    elif command == "process":
        try:
            process_all_html()
        except Exception as e:
            print(f"❌ Processing Fault: {e}")
            sys.exit(1)

    elif command == "load":
        try:
            load_all_jsons()
        except Exception as e:
            print(f"❌ Loading Fault: {e}")
            sys.exit(1)

    elif command == "profile":
        try:
            run_data_profile(db_path="data/3_gold/jobs.db")
        except Exception as e:
            print(f"❌ Profiling Fault: {e}")
            sys.exit(1)


def main():
    if len(sys.argv) < 2:
        show_usage()

    target_command = sys.argv[1].lower()
    if target_command not in ["ingest", "process", "load", "profile", "all"]:
        show_usage()

    if target_command == "all":
        execute_pipeline("ingest")
        execute_pipeline("process")
        execute_pipeline("load")
        execute_pipeline("profile")
        print("\n🏆 Pipeline successfully finished running!")
    else:
        execute_pipeline(target_command)


if __name__ == "__main__":
    main()