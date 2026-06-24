## ⚙️ Backend `README.md`
Create a file named **`README.md`** inside your **`backend`** directory:

```markdown
# Full-Stack Job Dashboard - Backend API

This is the central engine and data API processing system. It interfaces directly with local relational database systems and coordinates asynchronous communication protocols with Google Gemini AI models.

## 🛠️ Tech Stack
* **Framework:** FastAPI (Python 3.12-slim)
* **AI Integration:** Google GenAI SDK (`gemini-2.5-flash-lite`)
* **Database Engine:** SQLite3
* **Package Manager:** `uv` by Astral

## 📋 Required Configurations (`.env`)
The service depends heavily on specific container variables to talk to the AI API. Create a `.env` file inside this folder mirroring the structure below:

```text
GEMINI_API_KEY=your_actual_studio_api_key_here
DB_PATH=data/3_gold/jobs.db

📂 Core API Routing Endpoints
* POST /api/chat: Processes raw user context, injects parsed documentation frameworks, and runs exponential backoff logic against Gemini's streaming frameworks.
* GET /api/search: Performs relational database querying via standard text filter constraints.

🚀 Independent Local Development
# Synchronize environment libraries
uv sync
# Launch the standalone service API 
uv run uvicorn main:app --host 127.0.0.1 --port 8000