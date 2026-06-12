# 📋 Job Market Data Engineering Pipeline (Medallion Architecture)

## 📖 Project Description
This project implements a fully automated, local **Medallion Architecture** data pipeline designed to ingest, clean, validate, and profile job listing data. Moving from raw multi-part archive assets to structured relational tables, the pipeline organizes data through progressive stages: **Bronze** (raw extraction), **Silver** (cleaned and schema-validated JSONs via Pydantic data contracts), and **Gold** (analytical relational storage in SQLite).

---

## ⚙️ Setup Instructions

### 1. Prerequisites
Ensure you have the following installed on your local operating system:
* **Python**: Version `3.10` or higher
* **Package Manager**: [uv](https://github.com/astral-sh/uv) (An ultra-fast Python package installer and resolver)

### 2. Dependency Installation
This project leverages `uv` to maintain reproducible environments. Clone the repository, navigate to the root directory, and initialize the environment by running:

```powershell
# Create a virtual environment and install all necessary dependencies
uv venv
uv pip install beautifulsoup4 pydantic

Environment & Workspace Layout
No external API keys or secret environment variables are required for this local-first execution. However, the pipeline strictly expects a unified storage layout. The program automatically builds this infrastructure if missing, but ensure your starting raw archives are placed as follows:

📁 data/
└── 📁 0_source/      <-- Place your raw seed .mhtml files here

USAGE

The pipeline is coordinated through a central orchestration file (main.py) exposed via clean command aliases. Run these from your terminal/PowerShell:

Individual Step Execution
1.Ingest Layer (Bronze): Parses and decodes raw .mhtml files into flat raw HTML.

python main.py ingest

2.Process Layer (Silver): Extracted elements are cleaned using BeautifulSoup and structured using a strict Pydantic Data Contract. Missing or corrupt profiles are skipped.

python main.py process

3.Load Layer (Gold): Safely map validated files into a structured relational storage layer.

python main.py load

4.Profile Layer (QA): Inspects structural integrity and calculates high-level metrics.

python main.py profile

Full End-to-End Execution
To trigger the complete pipeline sequentially (Ingest -> Process -> Load -> Profile), use the macro orchestration command:

python main.py all

Expected Output Example (Data Quality Report)

--- 🔍 DATA QUALITY REPORT ---
📈 Total Records: 92
❓ Missing Values -> job_title: 0, company: 0, description: 0
📝 Avg Description Length: 5832 chars
⚠️ Shortest Description: 4 chars
   ↳ source_id: 91647393 | job_title: Seed
🚨 Longest Description: 10890 chars
   ↳ source_id: 91450819 | job_title: Data Engineer

TECHNICAL REFLECTIONS
Day 1: The Extractor (Medallion & Lakehouses)
Why is it useful to keep the original raw HTML files instead of directly inserting processed data into the database? What problems become easier to debug or recover from?

Answer: Storing raw data un-mutated in the Bronze layer implements an "immutable ledger" pattern critical to modern Lakehouses. If downstream transformation requirements change—such as wanting to extract a new metadata attribute previously ignored—having the original HTML eliminates the need to re-fetch files from the web source. It simplifies debugging by decoupling data collection failures (network, missing source files) from parsing failures (HTML layout updates), allowing engineers to safely re-run parsing logic on historical data without data loss.

Day 2: Treatment Plant (ETL vs ELT & Scale)
Why do cloud systems prefer loading raw data first before cleaning it (ELT)? What problems happen when processing files sequentially, and how does distributed processing help?

Answer: Cloud architectures lean heavily on ELT because compute power and storage can scale independently. Ingesting raw assets immediately maximizes data collection velocities without creating processing bottlenecks. Processing files sequentially (one-by-one) introduces major performance bottlenecks as file counts grow, as compute cores spend idle periods waiting for disk I/O. Distributed systems (like Apache Spark) break datasets into concurrent, parallel chunks across a cluster, allowing tens of thousands of files to be cleaned simultaneously, ensuring pipeline completion time scales linearly with hardware rather than quadratically with data size.

Day 3: The Blueprint & The Vault (Storage & Contracts)
What should happen if an important field like job_title disappears? Why fail early instead of silently inserting nulls into DB? How does INSERT OR IGNORE help prevent duplicate records?

Answer: If a structural element like job_title disappears, the pipeline must proactively trip a circuit breaker or quarantine the record using strict Pydantic data contracts. Failing early guards downstream analytics and dashboards from producing corrupt metrics or throwing untraceable runtime exceptions. Enforcing identity constraints via INSERT OR IGNORE or INSERT OR REPLACE ensures idempotency; it allows the system to re-ingest data packages multiple times while safely discarding duplicate source_id keys, preventing artificial inflation of analytical row counts.

Day 4: The QA Inspector & Orchestrator (Orchestration & DAGs)
What happens if processor.py crashes halfway? How are automated orchestration tools more reliable than manual retries with Python scripts?

Answer: If processor.py crashes mid-execution, a manual script leaves the environment in an unknown, partially updated state, risking data fragmentation or missing blocks. Automated orchestrators solve this by organizing steps into directed acyclic graphs (DAGs) that track execution states. If a failure strikes, the orchestrator handles atomic rollbacks, manages sophisticated backoff retries, sends real-time alerting to engineering teams, and cleanly resumes exactly from the point of failure without repeating successfully completed upstream operations.
