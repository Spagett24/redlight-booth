from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import random
import sqlite3

app = FastAPI()

# Serve static files (images)
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
# Helper: load HTML file
# -----------------------------
def load_html(file_name: str):
    with open(f"templates/{file_name}", encoding="utf-8") as f:
        return f.read()

# -----------------------------
# Landing page
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(load_html("index.html"))

# -----------------------------
# Request code
# -----------------------------
@app.post("/request_code", response_class=HTMLResponse)
def request_code(email: str = Form(...)):
    code = str(random.randint(100000, 999999))
    pending_codes[email] = code

    print(f"Verification code for {email}: {code}")

    html = load_html("verify.html")
    html = html.replace("{{ email }}", email)
    html = html.replace("{{ error }}", "")

    return HTMLResponse(html)

# -----------------------------
# Verify code
# -----------------------------
@app.post("/verify_code", response_class=HTMLResponse)
def verify_code(email: str = Form(...), code: str = Form(...)):

    stored = pending_codes.get(email)

    if stored and stored == code:
        cursor.execute(
            "INSERT INTO booth_sessions (email, used) VALUES (?, 0)",
            (email,)
        )
        conn.commit()

        del pending_codes[email]

        return HTMLResponse(load_html("success.html"))

    # invalid code
    html = load_html("verify.html")
    html = html.replace("{{ email }}", email)
    html = html.replace("{{ error }}", "Invalid code. Try again.")

    return HTMLResponse(html)

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