import sqlite3
import json
import hashlib
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "clinical.db")


# ───────── INIT DB ─────────
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Create table if not exists (new schema with phone)
    c.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        patient_id TEXT PRIMARY KEY,
        name TEXT,
        phone TEXT UNIQUE
    )
    """)

    # Safe migration: if old 'aadhar' column exists, rename it to 'phone'
    c.execute("PRAGMA table_info(patients)")
    cols = [row[1] for row in c.fetchall()]
    if "aadhar" in cols and "phone" not in cols:
        c.execute("ALTER TABLE patients RENAME COLUMN aadhar TO phone")

    # Safe migration: add 'pat_name' and 'pat_phone' display columns to visits if missing
    c.execute("PRAGMA table_info(visits)")
    visit_cols = [row[1] for row in c.fetchall()]

    c.execute("""
    CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT,
        visit_number INTEGER,
        visit_date TEXT,
        doctor_name TEXT,
        symptoms TEXT,
        diagnosis TEXT,
        medication TEXT,
        raw_notes TEXT,
        pat_name TEXT DEFAULT 'N/A',
        pat_phone TEXT DEFAULT 'N/A'
    )
    """)

    # If visits table already existed without pat_name/pat_phone, add them
    if "pat_name" not in visit_cols:
        c.execute("ALTER TABLE visits ADD COLUMN pat_name TEXT DEFAULT 'N/A'")
    if "pat_phone" not in visit_cols:
        c.execute("ALTER TABLE visits ADD COLUMN pat_phone TEXT DEFAULT 'N/A'")

    conn.commit()
    conn.close()


# ───────── CREATE PATIENT ─────────
def create_patient(name, phone):
    pid = "PAT" + hashlib.md5((name + phone).encode()).hexdigest()[:6].upper()

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT patient_id FROM patients WHERE phone=?", (phone,))
    row = c.fetchone()

    if row:
        conn.close()
        return row[0], True

    c.execute("INSERT INTO patients VALUES (?,?,?)", (pid, name, phone))
    conn.commit()
    conn.close()

    return pid, False


# ───────── GET PATIENT BY ID ─────────
def get_patient(pid):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT * FROM patients WHERE patient_id=?", (pid,))
    row = c.fetchone()

    conn.close()
    return row


# ───────── GET PATIENT BY NAME + PHONE ─────────
def get_patient_by_details(name, phone):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute(
        "SELECT patient_id FROM patients WHERE name=? AND phone=?",
        (name, phone)
    )

    row = c.fetchone()
    conn.close()

    return row[0] if row else None


# ───────── SAVE VISIT ─────────
def save_visit(pid, visit_no, data, raw_note, pat_name="N/A", pat_phone="N/A"):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("DELETE FROM visits WHERE patient_id=? AND visit_number=?", (pid, visit_no))

    c.execute("""
    INSERT INTO visits (
        patient_id, visit_number, visit_date, doctor_name,
        symptoms, diagnosis, medication, raw_notes, pat_name, pat_phone
    ) VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        pid,
        visit_no,
        data["visit_date"],
        data["doctor_name"],
        json.dumps(data["symptoms"]),
        data["diagnosis"],
        json.dumps(data["medication"]),
        raw_note,
        pat_name,
        pat_phone
    ))

    conn.commit()
    conn.close()


# ───────── GET VISITS ─────────
def get_visits(pid):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM visits WHERE patient_id=? ORDER BY visit_number", (pid,))
    rows = c.fetchall()

    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        d["symptoms"] = json.loads(d["symptoms"]) if d["symptoms"] else []
        d["medication"] = json.loads(d["medication"]) if d["medication"] else []
        d.setdefault("pat_name", "N/A")
        d.setdefault("pat_phone", "N/A")
        result.append(d)

    return result