import json
import re
import sys
import shutil
from pathlib import Path
from bs4 import BeautifulSoup


# 1. DATA STRUCTURING: Pure-Python Data Contract mimicking Pydantic for Python 3.14
class JobListing:
    def __init__(self, source_id: str, job_title: str, company: str, description: str):
        if not all(isinstance(f, str) for f in [source_id, job_title, company, description]):
            raise TypeError("All fields must be of type string")
        
        self.source_id = source_id.strip()
        self.job_title = job_title.strip()
        self.company = company.strip()
        self.description = description.strip()

    def model_dump(self) -> dict:
        return {
            "source_id": self.source_id,
            "job_title": self.job_title,
            "company": self.company,
            "description": self.description,
        }


def sanitize_filename(name: str) -> str:
    """Removes or replaces characters that are illegal in file names."""
    clean_name = name.replace(" ", "_")
    clean_name = re.sub(r'[\\/*?:"<>|]', "", clean_name)
    return clean_name.strip("_")


def process_all_html(input_dir: str = "data/1_bronze", output_dir: str = "data/2_silver") -> list[Path]:
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Clean destination to wipe old stale file artifacts
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"❌ Error: Input directory '{input_dir}' does not exist.")
        return []

    saved_json_files = []
    total_count = 0
    skipped_count = 0

    print("🥈 Silver:...")

    for file_path in input_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == ".html":
            total_count += 1

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, "html.parser")

            # Custom extraction blocks
            source = soup.find("meta", property="og:url")
            source_id = source.get("content").split("/")[-1] if source else None

            if source_id is None or source_id == "":
                print(f"⚠️ Missing source_id in: {file_path.name}")
                skipped_count += 1
                continue

            title = soup.find("h1", attrs={"data-automation": "job-detail-title"})
            job_title = title.get_text(separator=" ", strip=True) if title else None

            if job_title is None or job_title == "":
                print(f"⚠️ Missing job_title in: {file_path.name}")
                skipped_count += 1
                continue

            company = soup.find("span", attrs={"data-automation": "advertiser-name"})
            company_name = company.get_text(separator=" ", strip=True) if company else None

            if company_name is None or company_name == "":
                print(f"⚠️ Missing company in: {file_path.name}")
                skipped_count += 1
                continue

            desc = soup.find("div", attrs={"data-automation": "jobAdDetails"})
            job_desc = desc.get_text(separator=" ", strip=True) if desc else None

            if job_desc is None or job_desc == "":
                print(f"⚠️ Missing description in: {file_path.name}")
                skipped_count += 1
                continue

            try:
                validated_job = JobListing(
                    source_id=str(source_id),
                    job_title=str(job_title),
                    company=str(company_name),
                    description=str(job_desc),
                )

                # Added source_id suffix to completely eliminate file name collisions
                safe_title = sanitize_filename(validated_job.job_title)
                destination = output_path / f"{safe_title}_{validated_job.source_id}.json"
                
                with open(destination, "w", encoding="utf-8") as out_f:
                    json.dump(validated_job.model_dump(), out_f, ensure_ascii=False, indent=2)

                print(f"✅ Processed: {file_path.name}")
                saved_json_files.append(destination)
                
            except Exception:
                skipped_count += 1
                print(f"⚠️ Missing unknown data structural contract in: {file_path.name}")

    print("\n📊 Silver Summary:")
    print(f"Total: {total_count} | Processed: {len(saved_json_files)} | Skipped: {skipped_count}")

    return saved_json_files


if __name__ == "__main__":
    src = sys.argv[2] if len(sys.argv) > 2 else "data/1_bronze"
    dest = sys.argv[3] if len(sys.argv) > 3 else "data/2_silver"
    process_all_html(src, dest)