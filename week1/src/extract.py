import sys
from email import message_from_file
from pathlib import Path
import quopri


# Mandatory function name and default directory paths
def ingest_all_mhtml(
    input_dir: str = "data/0_source", output_dir: str = "data/1_bronze"
) -> list[Path]:
    """Extracts text/html payloads from .mhtml web archives, decodes

    quoted-printable encodings, and writes clean .html outputs.
    """
    source_path = Path(input_dir)
    output_path = Path(output_dir)

    # Program Idempotency: Create the 1_bronze directory if it is missing
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)

    # Program Idempotency: Gracefully exit if source directory is missing or empty
    if not source_path.exists():
        print(f"Warning: Source directory '{input_dir}' does not exist.")
        return []

    # Initialize metric counters
    total_count = 0
    extracted_count = 0
    failed_count = 0
    extracted_files = []

    print("🟫 Bronze:...")

    # Filter and loop through source files
    for file_path in source_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == ".mhtml":
            total_count += 1
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    msg = message_from_file(f)

                html_content = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/html":
                            payload = part.get_payload(decode=False)
                            if payload:
                                html_content = payload
                                break
                else:
                    if msg.get_content_type() == "text/html":
                        html_content = msg.get_payload(decode=False)

                if html_content:
                    # Decode the quoted-printable data string payload cleanly
                    decoded_bytes = quopri.decodestring(html_content.encode("utf-8"))
                    decoded_text = decoded_bytes.decode("utf-8", errors="ignore")

                    destination = output_path / f"{file_path.stem}.html"
                    with open(destination, "w", encoding="utf-8") as out_f:
                        out_f.write(decoded_text)

                    # FIXED: Aligned output print styling
                    print(f"✅ Extracted: {file_path.name}")
                    extracted_files.append(destination)
                    extracted_count += 1
                else:
                    # Handle files that successfully opened but had empty html text components
                    print(f"❌ Failed to extract {file_path.name}: No HTML payload found.")
                    failed_count += 1

            except Exception as e:
                print(f"❌ Failed to extract {file_path.name}: {e}")
                failed_count += 1

    # FIXED: Prints the exact requested output summary format layout
    print("\n📊 Bronze Summary:")
    print(f"Total: {total_count} | Extracted: {extracted_count} | Failed: {failed_count}")

    return extracted_files


if __name__ == "__main__":
    src = sys.argv[2] if len(sys.argv) > 2 else "data/0_source"
    dest = sys.argv[3] if len(sys.argv) > 3 else "data/1_bronze"
    ingest_all_mhtml(src, dest)