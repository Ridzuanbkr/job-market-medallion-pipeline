import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
# Fix line 5: Change to load_dotenv
from dotenv import load_dotenv

# Fix line 8: Change to load_dotenv()
load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="src/templates")

BACKEND_URL = os.getenv("backend_url", "http://localhost:8001")

from fastapi.responses import RedirectResponse

@app.get("/")
async def root_redirect():
    # 🚀 Instantly forward anyone clicking the base terminal link to your dashboard
    return RedirectResponse(url="/Dashboard")

# Keep all your previous code imports/setup exactly the same
@app.get("/Dashboard", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse(
        request, 
        "Dashboard.html", 
        {"backend_url": BACKEND_URL}
    )
    
@app.get("/chat_page", response_class=HTMLResponse)
async def read_chat(request: Request):
    return templates.TemplateResponse(
        request, 
        "chat_page.html", # Double-check if your filename starts with a capital 'C' locally!
        {"backend_url": BACKEND_URL}
    )
    