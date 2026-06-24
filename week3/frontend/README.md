# Full-Stack Job Dashboard - Frontend

This is the web-server user interface for the application stack. It uses **FastAPI** to server pages, **Jinja2** for HTML dynamic layouts, and requests asynchronous updates from the separate backend container.

## 🛠️ Tech Stack
* **Framework:** FastAPI (Python 3.12-slim)
* **Package Manager:** `uv` by Astral (configured via `pyproject.toml`)
* **Templating Engine:** Jinja2 Template Framework
* **Containerization:** Docker

## 📂 Project Structure
* `src/app.py`: Core FastAPI file managing dashboard views, web page layouts, and client requests.
* `src/templates/`: Folder containing raw interface markup files (`Dashboard.html`, `chat_page.html`).

## 🚀 Independent Local Development
If running outside of Docker Compose for styling tests, ensure you have `uv` installed locally:

```bash
# Install local locked dependencies
uv sync

# Fire up the application layout locally on Port 8501
uv run uvicorn src.app:app --host 127.0.0.1 --port 8501