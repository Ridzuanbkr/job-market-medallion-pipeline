import json
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, ValidationError


# Mandatory Pydantic Data Contract
class JobListing(BaseModel):
    source_id: str = Field(..., min_length=1)
    job_title: str = Field(..., min_length=1)
    company: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)


def extract_source_id_from_url(soup: BeautifulSoup) -> str | None:
    """Finds og:url and extracts the last segment of the path."""
    meta_url = soup.find("meta", property="og:url")
    if meta_url and meta_url.get("content"):
        url_str = meta_url["content"].strip().rstrip("/")
        return url_str.split("/")[-1]
    return None


def extract_field_by_automation_value(soup: BeautifulSoup, target_value: str) -> str | None:
    """Finds text inside elements matching a specific data-automation value."""
    element = soup.find(attrs={"data-automation": target_value})
    if element:
        return element.get_text(strip=True)
    return None


def process_all_html(input_dir: str = "data/1_bronze", output_dir: str = "data/2_silver") -> list[Path]:
    """Cleans HTML data, validates structure, and outputs a formatted log."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not output_path.exists():
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

            # Extract fields dynamically using your exact data-automation keys!
            source_id = extract_source_id_from_url(soup) or file_path.stem
            job_title = extract_field_by_automation_value(soup, "job-detail-title")
            company = extract_field_by_automation_value(soup, "advertiser-name")

            # Clean description text safely without fused words
            clean_description = soup.get_text(separator=" ", strip=True)
            clean_description = re.sub(r"\s+", " ", clean_description).strip()

            try:
                validated_job = JobListing(
                    source_id=str(source_id) if source_id else None,
                    job_title=str(job_title) if job_title else None,
                    company=str(company) if company else None,
                    description=str(clean_description) if clean_description else None,
                )

                # Save file tracking idempotency rules
                destination = output_path / f"{validated_job.source_id}.json"
                with open(destination, "w", encoding="utf-8") as out_f:
                    json.dump(validated_job.model_dump(), out_f, ensure_ascii=False, indent=2)

                print(f"✅ Processed: {file_path.name}")
                saved_json_files.append(destination)

            except ValidationError as err:
                skipped_count += 1
                missing_field = err.errors()[0]["loc"][0]
                print(f"⚠️ Missing {missing_field} in: {file_path.name}")
            except Exception:
                skipped_count += 1
                print(f"⚠️ Missing unknown data structural contract in: {file_path.name}")

    # Output Summary block layout
    print("\n📊 Silver Summary:")
    print(f"Total: {total_count} | Processed: {len(saved_json_files)} | Skipped: {skipped_count}")

    return saved_json_files


if __name__ == "__main__":
    src = sys.argv[2] if len(sys.argv) > 2 else "data/1_bronze"
    dest = sys.argv[3] if len(sys.argv) > 3 else "data/2_silver"
    process_all_html(src, dest)