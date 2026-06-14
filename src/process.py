import json
import re
import sys
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


# 3. DATA PROCESSING: Extract specific fields from HTML attributes
def extract_source_id_from_url(soup: BeautifulSoup) -> str | None:
    meta_url = soup.find("meta", property="og:url")
    if meta_url and meta_url.get("content"):
        url_str = meta_url["content"].strip().rstrip("/")
        if url_str:
            return url_str.split("/")[-1]
    return None


def extract_field_by_automation_value(soup: BeautifulSoup, target_value: str) -> str | None:
    element = soup.find(attrs={"data-automation": target_value})
    if element:
        text = element.get_text(strip=True)
        return text if text else None
    return None


def extract_clean_job_description(soup: BeautifulSoup, job_title: str | None) -> str:
    """2. DATA CLEANING: Removes HTML artifacts, normalizes text, and purges

    website navigation headers and footers using a global sentence blocklist.
    Focuses exclusively on jobAdDetails.
    """
    # STRIP JOBDESCRIPTION: Focus only on jobAdDetails container attribute
    desc_container = soup.find(attrs={"data-automation": "jobAdDetails"})
    
    if desc_container:
        # Prevent fused words using a space separator layout
        raw_text = desc_container.get_text(separator=" ", strip=True)
    else:
        # Fallback to body text if container element isn't found to avoid empty data breaks
        body = soup.find("body") or soup
        raw_text = body.get_text(separator=" ", strip=True)

    # Normalize multiple whitespace blocks
    raw_text = re.sub(r"\s+", " ", raw_text).strip()

    if not raw_text:
        return ""

    # Safely divide text into sentences based on punctuation markers
    sentences = re.split(r'(?<=[.!?])\s+', raw_text)
    short_desc_parts = []
    
    # --- GLOBAL BLOCKLIST ENGINE ---
    navigation_blocklist = [
        "skip to content", "open app", "sign in", "job search", 
        "people search", "career advice", "employer site", "companies community",
        "malaysia australia hong kong indonesia", "new zealand philippines singapore thailand"
    ]
    
    # Priority keywords matching your business logic rules
    priority_keywords = ["responsibilities", "requirements", "develop", "design", "experience", "skills"]
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        
        # 1. Skip sentence completely if it matches ANY layout clutter in our navigation blocklist
        if any(clutter in sentence_lower for clutter in navigation_blocklist):
            continue
            
        # 2. Keep sentence if it hits a core keyword or to populate an initial contextual summary window
        if any(kw in sentence_lower for kw in priority_keywords) or len(short_desc_parts) < 4:
            short_desc_parts.append(sentence)
            
    # Combine back into a concise block, keeping up to 6 key highlight sentences max
    clean_description = " ".join(short_desc_parts[:6]).strip()
    return clean_description


def process_all_html(input_dir: str = "data/1_bronze", output_dir: str = "data/2_silver") -> list[Path]:
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

            source_id = extract_source_id_from_url(soup)
            job_title = extract_field_by_automation_value(soup, "job-detail-title")
            company = extract_field_by_automation_value(soup, "advertiser-name")
            
            # FIXED: Correctly pass text extraction through the sentence cleaner engine 
            clean_description = extract_field_by_automation_value(soup, "jobAdDetails")

            try:
                # Validation assertions to confirm fields match required string types
                if not source_id or not job_title or not company or not clean_description:
                    raise ValueError("Missing data contract attributes.")

                validated_job = JobListing(
                    source_id=str(source_id),
                    job_title=str(job_title),
                    company=str(company),
                    description=str(clean_description),
                )

                # Output file name uses the clean job title format
                safe_title = sanitize_filename(validated_job.job_title)
                destination = output_path / f"{safe_title}.json"
                
                with open(destination, "w", encoding="utf-8") as out_f:
                    json.dump(validated_job.model_dump(), out_f, ensure_ascii=False, indent=2)

                print(f"✅ Processed: {file_path.name}")
                saved_json_files.append(destination)

            except ValueError as ve:
                skipped_count += 1
                field_name = str(ve).split()[-1] if "attributes" not in str(ve) else "data"
                print(f"⚠️ Missing {field_name} in: {file_path.name}")
                
            except (TypeError, Exception):
                skipped_count += 1
                print(f"⚠️ Missing unknown data structural contract in: {file_path.name}")

    print("\n📊 Silver Summary:")
    print(f"Total: {total_count} | Processed: {len(saved_json_files)} | Skipped: {skipped_count}")

    return saved_json_files


if __name__ == "__main__":
    src = sys.argv[2] if len(sys.argv) > 2 else "data/1_bronze"
    dest = sys.argv[3] if len(sys.argv) > 3 else "data/2_silver"
    process_all_html(src, dest)