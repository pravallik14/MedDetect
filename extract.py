import os
import io
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


# ───────── READ FILE CONTENT ─────────
def read_file(uploaded_file):
    """
    Accepts a Streamlit UploadedFile object.
    Supports .txt and .pdf
    Returns plain text string.
    """
    filename = uploaded_file.name.lower()

    if filename.endswith(".txt"):
        return uploaded_file.read().decode("utf-8", errors="ignore")

    elif filename.endswith(".pdf"):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(uploaded_file.read()))
            text   = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text.strip()
        except Exception as e:
            return f"PDF read error: {e}"

    else:
        return uploaded_file.read().decode("utf-8", errors="ignore")


# ───────── PROMPT ─────────
def build_prompt(note: str) -> str:
    return f"""
You are a strict medical JSON extraction system.

RULES:
- Return ONLY JSON
- No explanation
- No markdown
- No null values
- If missing → empty string "" or []

Clinical Note:
{note}

Output:
{{
  "visit_date": "",
  "doctor_name": "",
  "symptoms": [],
  "diagnosis": "",
  "medication": []
}}
"""


# ───────── SAFE JSON PARSE ─────────
def safe_json(text):
    try:
        return json.loads(text)
    except:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return None


# ───────── REGEX FALLBACK ─────────
def regex_fallback(note):
    note_lower = note.lower()

    date_patterns = [
        r"\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b",
        r"\b[A-Za-z]+\s+\d{1,2},\s*\d{4}\b",
        r"\b\d{2}/\d{2}/\d{4}\b"
    ]

    visit_date = ""
    for p in date_patterns:
        m = re.search(p, note)
        if m:
            visit_date = m.group()
            break

    doctor      = re.search(r"(dr\.?\s*[a-z]+)", note, re.IGNORECASE)
    doctor_name = doctor.group() if doctor else ""

    symptoms_list = ["fever", "cough", "pain", "nausea", "vomiting",
                     "fatigue", "headache", "dizziness", "chest pain",
                     "shortness of breath", "chills", "rash", "diarrhea"]
    symptoms = [s for s in symptoms_list if s in note_lower]

    diag      = re.search(r"diagnosis[:\-]\s*(.*)", note, re.IGNORECASE)
    diagnosis = diag.group(1).strip() if diag else ""

    meds      = ["paracetamol", "aspirin", "metformin", "azithromycin",
                 "cetirizine", "ibuprofen", "amoxicillin"]
    medication = [m for m in meds if m in note_lower]

    return {
        "visit_date" : visit_date,
        "doctor_name": doctor_name,
        "symptoms"   : symptoms,
        "diagnosis"  : diagnosis,
        "medication" : medication
    }


# ───────── MAIN EXTRACT ─────────
def extract_from_note(note: str):
    try:
        prompt   = build_prompt(note)
        response = client.chat.completions.create(
            model    = "llama-3.3-70b-versatile",
            messages = [{"role": "user", "content": prompt}],
            temperature = 0.1,
            max_tokens  = 400
        )

        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()

        data = safe_json(raw)
        if not data:
            return regex_fallback(note)

        for k in ["visit_date", "doctor_name", "symptoms", "diagnosis", "medication"]:
            if k not in data or data[k] is None:
                data[k] = "" if k not in ["symptoms", "medication"] else []

        return data

    except:
        return regex_fallback(note)