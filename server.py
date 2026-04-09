from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import random
import sqlite3

app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")
# -----------------------------
# Database setup
# -----------------------------
conn = sqlite3.connect("booth.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS booth_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used INTEGER DEFAULT 0
)
""")
conn.commit()

# -----------------------------
# In-memory codes
# -----------------------------
pending_codes = {}

# -----------------------------
# Landing page
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# -----------------------------
# Request code
# -----------------------------
@app.post("/request_code", response_class=HTMLResponse)
def request_code(request: Request, email: str = Form(...)):
    code = str(random.randint(100000, 999999))
    pending_codes[email] = code

    print(f"Verification code for {email}: {code}")

    return templates.TemplateResponse(
        "verify.html",
        {
            "request": request,
            "email": email,
            "error": None
        }
    )

# -----------------------------
# Verify code
# -----------------------------
@app.post("/verify_code", response_class=HTMLResponse)
def verify_code(request: Request, email: str = Form(...), code: str = Form(...)):

    stored = pending_codes.get(email)

    if stored and stored == code:
        # create booth session
        cursor.execute(
            "INSERT INTO booth_sessions (email, used) VALUES (?, 0)",
            (email,)
        )
        conn.commit()

        del pending_codes[email]

        return templates.TemplateResponse(
            "success.html",
            {"request": request}
        )

    # INVALID CODE PATH (fixed)
    return templates.TemplateResponse(
        "verify.html",
        {
            "request": request,
            "email": email,
            "error": "Invalid code. Try again."
        }
    )

# -----------------------------
# Raspberry Pi polling
# -----------------------------
@app.get("/booth_status")
def booth_status():

    cursor.execute(
        """
        SELECT id FROM booth_sessions
        WHERE used = 0
        AND verified_at >= datetime('now', '-30 seconds')
        ORDER BY verified_at
        LIMIT 1
        """
    )
    row = cursor.fetchone()

    if row:
        session_id = row[0]

        cursor.execute(
            "UPDATE booth_sessions SET used = 1 WHERE id = ?",
            (session_id,)
        )
        conn.commit()

        return {"activate": True}

    return {"activate": False}