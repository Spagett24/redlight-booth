from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import random
import sqlite3

# Create / connect database
conn = sqlite3.connect("booth.db", check_same_thread=False)
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS booth_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used INTEGER DEFAULT 0
)
""")

conn.commit()

app = FastAPI()

# -----------------------------
# Temporary in-memory storage
# -----------------------------
pending_codes = {}
authorized = False


# -----------------------------
# Landing page (QR opens this)
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head>
            <title>Red Light Booth</title>
        </head>

        <body style="font-family: Arial; text-align:center; margin-top:100px;">

            <h1>Red Light Therapy Booth</h1>

            <p>Enter your email to receive a verification code.</p>

            <form action="/request_code" method="post">
                <input type="email" name="email" placeholder="Enter email" required style="padding:10px; width:250px;">
                <br><br>
                <button type="submit" style="padding:10px 20px;">Send Code</button>
            </form>

        </body>
    </html>
    """


# -----------------------------
# Generate verification code
# -----------------------------
@app.post("/request_code", response_class=HTMLResponse)
def request_code(email: str = Form(...)):
    code = str(random.randint(100000, 999999))
    pending_codes[email] = code

    print(f"Verification code for {email}: {code}")

    return f"""
    <html>
        <body style="font-family: Arial; text-align:center; margin-top:100px;">

            <h2>Check your email</h2>

            <p>Enter the verification code.</p>

            <form action="/verify_code" method="post">
                <input type="hidden" name="email" value="{email}">
                <input type="text" name="code" placeholder="Enter code" required style="padding:10px;">
                <br><br>
                <button type="submit" style="padding:10px 20px;">Verify</button>
            </form>

        </body>
    </html>
    """

# -----------------------------
# Verify code
# -----------------------------
@app.post("/verify_code", response_class=HTMLResponse)
def verify_code(email: str = Form(...), code: str = Form(...)):

    stored = pending_codes.get(email)

    if stored and stored == code:

        # create booth session
        cursor.execute(
            "INSERT INTO booth_sessions (email, used) VALUES (?, 0)",
            (email,)
        )
        conn.commit()

        del pending_codes[email]

        return """
        <html>
            <body style="font-family: Arial; text-align:center; margin-top:100px;">
                <h2>Verification successful</h2>
                <p>You may now enter the booth.</p>
            </body>
        </html>
        """

    return """
    <html>
        <body style="font-family: Arial; text-align:center; margin-top:100px;">
            <h2>Invalid code</h2>
            <p>Please try again.</p>
        </body>
    </html>
    """



# -----------------------------
# Raspberry Pi polling endpoint
# -----------------------------
@app.get("/booth_status")
def booth_status():

    # find first unused session
    cursor.execute(
        """
        SELECT id FROM booth_sessions
        WHERE used = 0
        AND verified_at >= datetime('now', '-6 minutes')
        ORDER BY verified_at
        LIMIT 1
        """
    )
    row = cursor.fetchone()

    if row:
        session_id = row[0]

        # mark it used so it cannot trigger again
        cursor.execute(
            "UPDATE booth_sessions SET used = 1 WHERE id = ?",
            (session_id,)
        )
        conn.commit()

        return {"activate": True}

    return {"activate": False}
