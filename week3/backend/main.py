import os
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
import asyncio

# Load environment variables (like GEMINI_API_KEY) from your .env file
load_dotenv()

app = FastAPI()

# Enable CORS so your frontend can talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# CONFIGURATIONS & INITIALIZATIONS
# -------------------------------------------------------------
# Path to the Week 1 database file copied inside your backend data folder
DB_PATH = os.getenv("DB_PATH", "src/week_2/jobs.db")

# Initialize the Gemini client (it automatically picks up GEMINI_API_KEY from os.environ)
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("WARNING: GEMINI_API_KEY is not set in the environment variables!")

client = genai.Client(api_key=API_KEY)

class ChatPayload(BaseModel):
    message: str
    pdf_context: str = ""


# -------------------------------------------------------------
# 1. AI CHATBOX ENDPOINT (GEMINI)
# -------------------------------------------------------------
@app.post("/api/chat")
async def chat_endpoint(payload: ChatPayload):
    # Combine the user prompt with the extracted PDF resume context
    full_prompt = payload.message
    if payload.pdf_context:
        full_prompt = f"Resume Context:\n{payload.pdf_context}\n\nUser Question: {payload.message}"
        
    # 🚀 Robust Retry Configuration
    max_retries = 10
    delay = 0.5  # Start with a 0.5-second wait
    
    for attempt in range(max_retries):
        try:
            response = await client.aio.models.generate_content(
                model='gemini-3-flash-preview',
                contents=full_prompt,
            )
            return {"response": response.text}
        
        except Exception as e:
            # If it's a server traffic spike error (503), wait and retry
            if "503" in str(e) and attempt < max_retries - 1:
                print(f"Server busy (503). Retrying in {delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)
                delay *= 2  # Double the wait time for the next try
                continue
            
            # If it's any other error or we ran out of retries, log and fail gracefully
            print(f"CRITICAL CHAT ERROR: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Gemini API Error: {str(e)}")

    # 🚀 FALLBACK: If it somehow exits the loop without returning or raising an error
    raise HTTPException(status_code=500, detail="Gemini API failed after maximum retry attempts.")

# -------------------------------------------------------------
# 2. BONUS DASHBOARD DATABASE SEARCH ENDPOINT
# -------------------------------------------------------------
@app.get("/api/search")
async def search_database(q: str):
    if not os.path.exists(DB_PATH):
        return {"results": []}
        
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Returns rows as dictionary items so JSON understands them
        cursor = conn.cursor()
        
        # NOTE: Make sure your table name and columns exist in your Week 1 DB!
        # Change 'jobs', 'title', and 'description' below if your week 1 names are different.
        query = f"SELECT * FROM jobs WHERE job_title LIKE ? OR description LIKE ? LIMIT 100"
        cursor.execute(query, (f"%{q}%", f"%{q}%"))
        
        rows = cursor.fetchall()
        conn.close()
        
        return {"results": [dict(row) for row in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))