# Full-Stack Containerized AI Chat Application

## 1. Project Overview
The goal of this project is to build, integrate, and containerize a high-performance, full-stack conversational web application. The ecosystem splits the application logic into decoupled frontend and backend layers, orchestrated seamlessly via Docker. 

The application enables users to query a relational job vacancy database from a central dashboard and engage in an automated context-aware chat interface. The chat engine processes raw text inputs combined with parsed PDF documentation, parsing data structures asynchronously through the Google Gemini AI API framework utilizing dynamic request retries.

---

## 2. Setup Instructions

### Prerequisites
Ensure your local host machine has the following modern toolchains installed:
* **Docker Desktop** (Engine v20.10+ with Compose V2 support)
* **Python 3.14+** (Optional: Only required for local development outside containers)
* **uv** (Optional: Modern ultra-fast Python package installer for manual execution)

### Environment Variable Configurations
The application reads secrets and structural endpoints locally via standard environment configuration matrices. 

1. Locate the `backend/` directory and clone the template structure:
   ```bash
   cp backend/.env.example backend/.env

2. Open your newly created backend/.env file and append your dedicated Google AI Studio API credentials:

GEMINI_API_KEY=AIzaSyYourActualSecureGeminiKeyGoesHere
DB_PATH=src/week_2/jobs.db
⚠️ Security Warning: The .env configurations are explicitly blocked via .gitignore to guarantee local API tokens are never checked into public version control histories.

Manual Local Dependencies Installation (Alternative Setup)
If running components natively on your host machine without containers, install the locked project workspace trees using uv:

# Inside /backend or /frontend
uv sync

## 3. Usage
Launching the Application Ecosystem
Execute the full initialization pipeline directly from your PowerShell or bash terminal console root folder:

# 1. Clean drop stale environment profiles
docker compose down

# 2. Build and launch the container ecosystem cleanly
docker compose up --build

Accessing the Interfaces
Once Docker completes compilation, custom terminal echo filters output direct clickable localhost routes:
* Frontend Web Dashboard: Ctrl + Click -> http://localhost:8501/Dashboard
* Backend Auto-Generated API Docs: Ctrl + Click -> http://localhost:8001/docs#/

User Workflow Strategy
1. Database Search: Navigate to the Dashboard page, type a query parameter (e.g., Data), and verify that real relational rows fetch and map dynamically to the UI tables.
2. AI Chat Engine: Open the Chat tab. Paste context payload markers or select sample criteria, input custom textual prompt instructions, and hit send. The AI bot will stream a compiled response based on internal reasoning.

## 4. API & Function Reference
Backend Router (backend/main.py)
    POST /api/chat
        * Description: Receives user data payload targets, attaches conditional metadata structures, and initiates async calls to Gemini models.
        * Payload (ChatPayload):
        {
         "message": "Is this background suited for Data Science positions?",
            "pdf_context": "Parsed text array content extracted from resume document string..."
        }

        * Response Format:
        {
        "response": "Based on the provided resume context, the candidate possesses strong competencies in..."
        }

    GET /api/search
        * Description: Reads incoming parameter string queries and executes wildcard filters against local indexed database rows.

Frontend Web Layer (frontend/src/)
* src/app.py: Manages underlying routing matrices for Jinja template processing engine. It serves views like /Dashboard and /chat_page, redirecting base root index connections safely to the interactive view layouts.
* JavaScript Engine (chat.js / Frontend Fetch Scripts): Manages interactive elements without page reloads. Captures form submission event payloads, dispatches fetch() methods asynchronously targeting backend microservice boundaries, tracks active UI status states, and prints markup arrays on success.

Cross-Container Networking Topology
Both services link directly via a virtual isolated bridge framework defined as app-network. The Frontend safely addresses the private backend backend cluster container through internal domain lookups via standard Docker DNS aliases: http://backend:8000.

## 5. Data & Assumptions
Data Architecture Specifications
Communication between the decoupled client engine and the server interface relies exclusively on standard JSON structural payloads.

Core Architectural Assumptions
* Input Parameters: Text extracted from uploaded files must be passed to the payload wrapper as pre-formatted UTF-8 raw strings.
* Payload Boundary Restrictions: Prompts conform directly to baseline tokens allocated for gemini-2.5-flash-lite. High-frequency payloads are throttled gracefully using an exponential backoff retry loop (max 10 execution attempts).
* Simplifications: Database interactions remain entirely read-only to ensure baseline atomic stability during deployment.

System Data Flow Pipeline
[User Browser] -> Click Event -> JS Async Fetch -> [Frontend Port 8501 Container]
                                                          |
                                                    (Docker Network)
                                                          v
[Gemini AI Engine] <- Async SDK Hook <- [Backend Port 8000 Container Proxy]

## 6. Testing Framework
Backend Endpoint Validation
Verify operational efficiency by mocking raw HTTP inputs via PowerShell or cURL terminals directly against the running service interface:

Invoke-RestMethod -Uri "http://localhost:8001/api/search?q=Data" -Method Get

Full-Stack Network Integration Verification
Check active routing pathways inside running container instances by reading isolated container log streams:

docker compose logs -f backend

Expected trace lines signaling healthy client-to-server operations: INFO: 172.18.0.1 - "POST /api/chat HTTP/1.1" 200 OK

## 7. Limitations & Constraints
* Session Persistence Constraints: The chat system runs as a stateless processing interface. Refreshing the browser clear-wipes current contextual transaction history tables because active sessions do not write to persistent user state stores.
* Authentication Constraints: Access boundaries are wide open. The deployment configuration lacks route guards, validation middleware tokens, or credential handshakes.
* PDF File Handling Limits: The application assumes the text layer can be cleanly extracted and handles parsing memory management entirely client-side. Large scannable image blobs can exhaust standard execution buffers.

## 8. Architecture Reflection
Design Choices
Splitting the system into an isolated Microservices Architecture via distinct frontend and backend servers enforces clean separations of concern. The frontend deals strictly with presentation layers and state presentation engines, while the heavy processing loads, database clients, and API SDK wrappers remain isolated behind the backend domain. Containerizing with Docker eliminates standard "works on my machine" environmental discrepancies.

Architectural Trade-offs
Simplicity vs. Scope: Priority was placed on ultra-fast environment setups (using uv configurations over bulky legacy setup tools) and complete container orchestration readiness via a single command, choosing to defer production features like distributed authentication frameworks or multi-region database replication structures.

Future System Improvements
Given additional development timeline scopes, the application would adapt the following improvements:
1. Dynamic State Stores: Migrate stateless endpoints toward real relational user history tables managed inside an independent PostgreSQL database container instance.
2. Advanced Presentation Frameworks: Replace Jinja HTML routing structures entirely with modular single-page UI architectures like React or Vue, communicating asynchronously through standard secure JWT authentication layers.