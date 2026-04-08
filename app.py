import streamlit as st
from db import (
    init_db,
    create_patient,
    get_patient,
    save_visit,
    get_visits,
    get_patient_by_details
)
from extract import extract_from_note, read_file
from ml_model import predict_disease
from logic import (
    check_repeated_symptoms,
    analyze_trend,
    generate_all_alerts,
    patient_tracking
)

# ───────── PAGE CONFIG ─────────
st.set_page_config(
    page_title="MedDetect — Clinical AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ───────── GLOBAL STYLES ─────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

/* ── RESET & BASE ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0a0d12 !important;
    color: #e8eaf2 !important;
    font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse 80% 60% at 50% -10%, #0d2137 0%, #0a0d12 60%) !important;
}

/* ── HIDE STREAMLIT CHROME ── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* ── MAIN CONTENT WIDTH ── */
.block-container {
    max-width: 960px !important;
    padding: 2rem 2rem 4rem !important;
}

/* ── HERO HEADER ── */
.hero-header {
    display: flex;
    align-items: center;
    gap: 18px;
    padding: 2.8rem 0 2.2rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 2.4rem;
}
.hero-icon {
    width: 56px; height: 56px;
    background: linear-gradient(135deg, #00c6ff, #0072ff);
    border-radius: 16px;
    display: flex; align-items: center; justify-content: center;
    font-size: 26px;
    box-shadow: 0 0 32px rgba(0,114,255,0.4);
    flex-shrink: 0;
}
.hero-text h1 {
    font-family: 'Syne', sans-serif !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.5px;
    color: #ffffff !important;
    line-height: 1.1;
}
.hero-text p {
    font-size: 0.85rem;
    color: #5a6a82;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 4px;
}

/* ── SECTION LABELS ── */
.section-label {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #0072ff;
    margin-bottom: 0.9rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(0,114,255,0.3), transparent);
}

/* ── CARDS ── */
.med-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(8px);
    transition: border-color 0.2s;
}
.med-card:hover { border-color: rgba(0,114,255,0.25); }

.visit-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-left: 3px solid #0072ff;
    border-radius: 0 14px 14px 0;
    padding: 1.3rem 1.5rem;
    margin-bottom: 1rem;
}
.visit-card.current {
    border-left-color: #00d97e;
    background: rgba(0,217,126,0.03);
}

.visit-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 0.9rem;
}
.visit-num {
    font-family: 'Syne', sans-serif;
    font-size: 0.75rem;
    font-weight: 700;
    color: #0072ff;
    background: rgba(0,114,255,0.12);
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.05em;
}
.visit-num.current { color: #00d97e; background: rgba(0,217,126,0.12); }
.visit-fname {
    font-size: 0.78rem;
    color: #4a5c70;
    font-family: 'DM Mono', monospace;
}

/* ── DATA ROWS ── */
.data-row {
    display: flex;
    gap: 8px;
    align-items: flex-start;
    margin-bottom: 0.45rem;
    font-size: 0.88rem;
    line-height: 1.4;
}
.data-label {
    min-width: 110px;
    color: #3d5066;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding-top: 2px;
    flex-shrink: 0;
}
.data-value { color: #cdd5e0; }
.data-value.mono {
    font-family: 'DM Mono', monospace;
    font-size: 0.83rem;
}

/* ── TAGS ── */
.tag-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 2px; }
.tag {
    font-size: 0.75rem;
    padding: 3px 10px;
    border-radius: 20px;
    font-weight: 500;
}
.tag-symptom {
    background: rgba(255,160,50,0.1);
    color: #ffa032;
    border: 1px solid rgba(255,160,50,0.2);
}
.tag-med {
    background: rgba(80,200,255,0.1);
    color: #50c8ff;
    border: 1px solid rgba(80,200,255,0.2);
}

/* ── PREDICTION PILL ── */
.pred-box {
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(0,114,255,0.07);
    border: 1px solid rgba(0,114,255,0.2);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    margin-top: 0.9rem;
}
.pred-icon { font-size: 1.3rem; }
.pred-disease {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    color: #ffffff;
}
.pred-source {
    font-size: 0.74rem;
    color: #4a6080;
    margin-top: 1px;
}
.pred-match {
    margin-left: auto;
    font-size: 0.78rem;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 600;
}
.pred-match.ok { background: rgba(0,217,126,0.12); color: #00d97e; }
.pred-match.no { background: rgba(255,80,80,0.12); color: #ff5050; }
.pred-match.unk { background: rgba(255,255,255,0.05); color: #5a6a82; }

/* ── ALERT CARDS ── */
.alert-item {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    padding: 0.8rem 1rem;
    border-radius: 10px;
    margin-bottom: 0.5rem;
    font-size: 0.87rem;
    line-height: 1.4;
}
.alert-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 5px; }
.alert-critical { background: rgba(255,50,50,0.08); border: 1px solid rgba(255,50,50,0.2); }
.alert-critical .alert-dot { background: #ff3232; box-shadow: 0 0 8px #ff3232; }
.alert-high { background: rgba(255,140,0,0.08); border: 1px solid rgba(255,140,0,0.2); }
.alert-high .alert-dot { background: #ff8c00; }
.alert-medium { background: rgba(255,210,0,0.07); border: 1px solid rgba(255,210,0,0.15); }
.alert-medium .alert-dot { background: #ffd200; }
.alert-low { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); }
.alert-low .alert-dot { background: #5a6a82; }

.alert-group-header {
    font-family: 'Syne', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin: 1rem 0 0.4rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.alert-count {
    background: rgba(255,255,255,0.08);
    padding: 1px 8px;
    border-radius: 10px;
    font-size: 0.7rem;
    font-weight: 600;
}

/* ── STAT PILLS ── */
.stat-row {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin: 1rem 0;
}
.stat-pill {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 0.6rem 1rem;
    min-width: 120px;
}
.stat-pill-label {
    font-size: 0.7rem;
    color: #3d5066;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.stat-pill-value {
    font-family: 'Syne', sans-serif;
    font-size: 1.2rem;
    font-weight: 700;
    color: #ffffff;
    margin-top: 2px;
}

/* ── TRACKING TABLE ── */
.track-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 0.8rem;
    border-radius: 8px;
    margin-bottom: 4px;
    font-size: 0.84rem;
}
.track-row:nth-child(odd) { background: rgba(255,255,255,0.025); }

/* ── TREND BADGE ── */
.trend-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(0,114,255,0.1);
    border: 1px solid rgba(0,114,255,0.2);
    border-radius: 8px;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
    color: #90b8ff;
    margin: 0.6rem 0;
}

/* ── DIVIDER ── */
.med-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.07), transparent);
    margin: 2rem 0;
}

/* ── STREAMLIT OVERRIDES ── */
/* ── STREAMLIT INPUT FIX (SAFE FINAL) ── */

/* TARGET ALL INPUT BOXES */
input[type="text"], input[type="number"], textarea {
    background-color: #1a1f2b !important;
    color: #ffffff !important;
    border: 1px solid #3a455a !important;
    border-radius: 10px !important;
}

/* STREAMLIT TEXT INPUT (MAIN FIX) */
div[data-testid="stTextInput"] input {
    background-color: #1a1f2b !important;
    color: #ffffff !important;
    border: 1px solid #3a455a !important;
}

/* PLACEHOLDER TEXT */
input::placeholder {
    color: #888 !important;
}

/* FILE UPLOADER BOX */
section[data-testid="stFileUploader"] {
    background-color: rgba(255,255,255,0.02) !important;
    border: 1.5px dashed #3a455a !important;
}

/* FILE UPLOADER BUTTON */
section[data-testid="stFileUploader"] button {
    background-color: #1a1f2b !important;
    color: #ffffff !important;
    border: 1px solid #3a455a !important;
}

/* DROP ZONE TEXT */
section[data-testid="stFileUploader"] span {
    color: #cccccc !important;
}

.stButton > button {
    background: linear-gradient(135deg, #0072ff, #00c6ff) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    padding: 0.55rem 1.5rem !important;
    transition: opacity 0.2s, transform 0.15s !important;
    box-shadow: 0 4px 20px rgba(0,114,255,0.3) !important;
}
.stButton > button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}

.stRadio > div { gap: 6px !important; }
.stRadio > div > label {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    padding: 0.45rem 1rem !important;
    color: #c0cfe0 !important;
    font-size: 0.87rem !important;
    transition: all 0.15s !important;
    cursor: pointer !important;
}
.stRadio > div > label:has(input:checked) {
    border-color: rgba(0,114,255,0.6) !important;
    background: rgba(0,114,255,0.15) !important;
    color: #90b8ff !important;
}
.stRadio [data-testid="stMarkdownContainer"] p { font-size: 0.87rem !important; }
/* Radio group label */
.stRadio > label {
    color: #a0b4cc !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    font-weight: 500 !important;
}

.stFileUploader {
    background: rgba(255,255,255,0.02) !important;
    border: 1.5px dashed rgba(255,255,255,0.1) !important;
    border-radius: 14px !important;
    padding: 1rem !important;
    transition: border-color 0.2s !important;
}
.stFileUploader:hover { border-color: rgba(0,114,255,0.35) !important; }
.stFileUploader label { color: #4a6080 !important; font-size: 0.83rem !important; }

/* hide default streamlit alerts, we use custom */
.stAlert { display: none !important; }

/* ── CUSTOM ALERTS (replace st.warning etc) ── */
.inline-success {
    background: rgba(0,217,126,0.07);
    border: 1px solid rgba(0,217,126,0.25);
    border-radius: 10px;
    padding: 0.7rem 1rem;
    color: #00d97e;
    font-size: 0.87rem;
    margin: 0.4rem 0;
}
.inline-warn {
    background: rgba(255,160,50,0.07);
    border: 1px solid rgba(255,160,50,0.2);
    border-radius: 10px;
    padding: 0.7rem 1rem;
    color: #ffa032;
    font-size: 0.87rem;
    margin: 0.4rem 0;
}
.inline-info {
    background: rgba(0,114,255,0.07);
    border: 1px solid rgba(0,114,255,0.18);
    border-radius: 10px;
    padding: 0.7rem 1rem;
    color: #70a8ff;
    font-size: 0.87rem;
    margin: 0.4rem 0;
}
.inline-error {
    background: rgba(255,50,50,0.07);
    border: 1px solid rgba(255,50,50,0.2);
    border-radius: 10px;
    padding: 0.7rem 1rem;
    color: #ff6060;
    font-size: 0.87rem;
    margin: 0.4rem 0;
}

/* ── PATIENT ID BADGE ── */
.pid-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(0,114,255,0.1);
    border: 1px solid rgba(0,114,255,0.3);
    border-radius: 10px;
    padding: 0.5rem 1rem;
    margin-bottom: 1.5rem;
}
.pid-label {
    font-size: 0.7rem;
    color: #4a6080;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
.pid-value {
    font-family: 'Syne', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: #90b8ff;
}

/* ── FILE PREVIEW ROW ── */
.file-preview-row {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 0.6rem 1rem;
    margin-bottom: 0.4rem;
}
.file-preview-num {
    font-family: 'Syne', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    color: #0072ff;
    background: rgba(0,114,255,0.12);
    padding: 2px 8px;
    border-radius: 6px;
    flex-shrink: 0;
}
.file-preview-name {
    font-size: 0.83rem;
    color: #8a9ab2;
    font-family: monospace;
}

/* ── SYMPTOM FREQUENCY ── */
.freq-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0.6rem 0.8rem;
    border-radius: 8px;
    margin-bottom: 0.4rem;
    font-size: 0.85rem;
}
.freq-row.chronic {
    background: rgba(255,50,50,0.06);
    border: 1px solid rgba(255,50,50,0.15);
}
.freq-row.repeated {
    background: rgba(255,160,50,0.06);
    border: 1px solid rgba(255,160,50,0.15);
}
.freq-name { flex: 1; color: #cdd5e0; text-transform: capitalize; }
.freq-count {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 0.9rem;
}
.freq-row.chronic .freq-count { color: #ff5050; }
.freq-row.repeated .freq-count { color: #ffa032; }
.freq-badge {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 2px 8px;
    border-radius: 10px;
}
.freq-row.chronic .freq-badge {
    background: rgba(255,50,50,0.15);
    color: #ff5050;
}
.freq-row.repeated .freq-badge {
    background: rgba(255,160,50,0.15);
    color: #ffa032;
}

/* scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

init_db()

# ───────── HERO HEADER ─────────
st.markdown("""
<div class="hero-header">
    <div class="hero-icon">🧬</div>
    <div class="hero-text">
        <h1>MedDetect</h1>
        <p>Clinical AI System · Intelligent Visit Analysis</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ───────── HELPERS ─────────
def success_msg(msg):
    st.markdown(f'<div class="inline-success">✓ &nbsp;{msg}</div>', unsafe_allow_html=True)

def warn_msg(msg):
    st.markdown(f'<div class="inline-warn">⚠ &nbsp;{msg}</div>', unsafe_allow_html=True)

def info_msg(msg):
    st.markdown(f'<div class="inline-info">ℹ &nbsp;{msg}</div>', unsafe_allow_html=True)

def error_msg(msg):
    st.markdown(f'<div class="inline-error">✕ &nbsp;{msg}</div>', unsafe_allow_html=True)

def tags_html(items, cls):
    tags = "".join(f'<span class="tag {cls}">{t}</span>' for t in items)
    return f'<div class="tag-row">{tags}</div>'


def show_prediction(pred, doctor_diagnosis):
    disease = pred["disease"]
    layer   = pred["layer"]
    score   = pred["score"]

    if layer == "Rules":
        source = "Rules Engine"
        icon   = "⚙️"
    elif layer == "Similarity":
        pct    = int((score or 0) * 100)
        source = f"Dataset Match · {pct}% similar"
        icon   = "📊"
    elif layer == "Groq":
        source = "Groq AI · low confidence"
        icon   = "🤖"
    else:
        source = "Unknown"
        icon   = "❓"

    if disease == "Unknown" or not doctor_diagnosis:
        match_html = '<span class="pred-match unk">No data</span>'
    elif disease.lower() in doctor_diagnosis.lower() or doctor_diagnosis.lower() in disease.lower():
        match_html = '<span class="pred-match ok">✓ Matches</span>'
    else:
        match_html = f'<span class="pred-match no">✗ Mismatch</span>'

    st.markdown(f"""
    <div class="pred-box">
        <span class="pred-icon">{icon}</span>
        <div>
            <div class="pred-disease">{disease}</div>
            <div class="pred-source">AI Prediction · {source}</div>
        </div>
        {match_html}
    </div>
    """, unsafe_allow_html=True)


def render_visit(v, is_current=False):
    raw        = v.get("raw_notes") or ""
    fname_line = raw.split("\n")[0] if raw.startswith("[File:") else ""
    label      = fname_line.replace("[File:", "").replace("]", "").strip() if fname_line else ""

    card_cls = "visit-card current" if is_current else "visit-card"
    num_cls  = "visit-num current"  if is_current else "visit-num"

    fname_html = f'<span class="visit-fname">{label}</span>' if label else ""
    badge_html = '<span style="font-size:0.74rem;color:#00d97e;font-weight:600">&#x1F7E2; Current Session</span>' if is_current else ""

    # Build symptoms tags inline
    if v["symptoms"]:
        sym_tags = "".join(f'<span class="tag tag-symptom">{s}</span>' for s in v["symptoms"])
        sym_html = f'<div class="tag-row">{sym_tags}</div>'
    else:
        sym_html = '<span style="color:#3d5066;font-size:0.8rem">&#x2014;</span>'

    # Build medication tags inline
    if v["medication"]:
        med_tags = "".join(f'<span class="tag tag-med">{m}</span>' for m in v["medication"])
        med_html = f'<div class="tag-row">{med_tags}</div>'
    else:
        med_html = '<span style="color:#3d5066;font-size:0.8rem">&#x2014;</span>'

    # Build AI prediction HTML inline (so it stays inside the card visually)
    pred_html = ""
    if v["symptoms"]:
        pred = predict_disease(v["symptoms"])
        disease = pred["disease"]
        layer   = pred["layer"]
        score   = pred["score"]

        if layer == "Rules":
            source = "Rules Engine"
            icon   = "⚙️"
        elif layer == "Similarity":
            pct    = int((score or 0) * 100)
            source = f"Dataset Match · {pct}% similar"
            icon   = "📊"
        elif layer == "Groq":
            source = "Groq AI · low confidence"
            icon   = "🤖"
        else:
            source = "Unknown"
            icon   = "❓"

        doctor_diagnosis = v["diagnosis"]
        if disease == "Unknown" or not doctor_diagnosis:
            match_html = '<span class="pred-match unk">No data</span>'
        elif disease.lower() in doctor_diagnosis.lower() or doctor_diagnosis.lower() in disease.lower():
            match_html = '<span class="pred-match ok">✓ Matches</span>'
        else:
            match_html = '<span class="pred-match no">✗ Mismatch</span>'

        pred_html = (
            f'<div class="pred-box">'
            f'<span class="pred-icon">{icon}</span>'
            f'<div>'
            f'<div class="pred-disease">{disease}</div>'
            f'<div class="pred-source">AI Prediction · {source}</div>'
            f'</div>'
            f'{match_html}'
            f'</div>'
        )

    # Single complete HTML block — prediction inside the card
    html = (
        f'<div class="{card_cls}">'
        f'<div class="visit-header">'
        f'<span class="{num_cls}">Visit {v["visit_number"]}</span>'
        f'{fname_html}{badge_html}'
        f'</div>'
        f'<div class="data-row"><span class="data-label">Date</span>'
        f'<span class="data-value">{v["visit_date"] or "&#x2014;"}</span></div>'
        f'<div class="data-row"><span class="data-label">Doctor</span>'
        f'<span class="data-value">{v["doctor_name"] or "&#x2014;"}</span></div>'
        f'<div class="data-row"><span class="data-label">Diagnosis</span>'
        f'<span class="data-value">{v["diagnosis"] or "&#x2014;"}</span></div>'
        f'<div class="data-row"><span class="data-label">Symptoms</span>'
        f'<span class="data-value">{sym_html}</span></div>'
        f'<div class="data-row"><span class="data-label">Medication</span>'
        f'<span class="data-value">{med_html}</span></div>'
        f'{pred_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ───────── RESET ─────────
choice = st.radio("Patient Type", ["New Patient", "Existing Patient"], horizontal=True)

if "last_choice" not in st.session_state:
    st.session_state["last_choice"] = choice

if st.session_state["last_choice"] != choice:
    st.session_state.clear()
    st.session_state["last_choice"] = choice
    st.session_state["processed"]   = False
    st.rerun()

st.markdown('<div class="med-divider"></div>', unsafe_allow_html=True)

# ───────── NEW PATIENT ─────────
if choice == "New Patient":
    st.markdown('<div class="section-label">Register Patient</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        name   = st.text_input("Full Name")
    with col2:
        phone = st.text_input("Phone Number")

    if st.button("Generate Patient ID"):
        pid, exists = create_patient(name, phone)
        if exists:
            warn_msg(f"Patient already registered &nbsp;·&nbsp; ID: <strong>{pid}</strong>")
        else:
            success_msg(f"Patient created successfully &nbsp;·&nbsp; ID: <strong>{pid}</strong>")
        st.session_state["pid"] = pid
        st.session_state["pat_name"] = name
        st.session_state["pat_phone"] = phone

# ───────── EXISTING PATIENT ─────────
else:
    st.markdown('<div class="section-label">Find Patient</div>', unsafe_allow_html=True)
    method = st.radio("Search by", ["Patient ID", "Name + Phone"], horizontal=True)

    if method == "Patient ID":
        pid_input = st.text_input("Patient ID")
        if st.button("Load Patient"):
            if get_patient(pid_input):
                st.session_state["pid"]       = pid_input
                st.session_state["processed"] = False
                success_msg(f"Patient loaded · ID: <strong>{pid_input}</strong>")
            else:
                error_msg("Patient ID not found")
    else:
        col1, col2 = st.columns(2)
        with col1:
            name   = st.text_input("Name")
        with col2:
            phone = st.text_input("Phone Number")
        if st.button("Search Patient"):
            pid = get_patient_by_details(name, phone)
            if pid:
                success_msg(f"Patient found &nbsp;·&nbsp; ID: <strong>{pid}</strong>")
                st.session_state["pid"]       = pid
                st.session_state["processed"] = False
                st.session_state["pat_name"]  = name
                st.session_state["pat_phone"] = phone
            else:
                error_msg("No patient found with those details")

# ───────── MAIN FLOW ─────────
if "pid" in st.session_state:

    pid = st.session_state["pid"]

    st.markdown('<div class="med-divider"></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="pid-badge">
        <span class="pid-label">Active Patient</span>
        <span class="pid-value">{pid}</span>
    </div>
    """, unsafe_allow_html=True)

    all_visits = get_visits(pid)

    # ── Upload Section ──
    st.markdown('<div class="section-label">Add Visit Notes</div>', unsafe_allow_html=True)
    info_msg("Upload <strong>.txt</strong> or <strong>.pdf</strong> files — each file = one visit")

    uploaded_files = st.file_uploader(
        "Select visit note files",
        type=["txt", "pdf"],
        accept_multiple_files=True,
        help="Each file will be treated as one visit. Files are processed in upload order.",
        label_visibility="collapsed"
    )

    if uploaded_files:
        st.markdown('<div class="section-label" style="margin-top:1rem">Files Ready</div>', unsafe_allow_html=True)
        for i, f in enumerate(uploaded_files):
            st.markdown(f"""
            <div class="file-preview-row">
                <span class="file-preview-num">Visit {len(all_visits) + i + 1}</span>
                <span class="file-preview-name">{f.name}</span>
            </div>
            """, unsafe_allow_html=True)

        if st.button("⚡ Process & Save Files"):
            start   = len(all_visits)
            success = 0
            with st.spinner("Extracting clinical data..."):
                for i, uploaded_file in enumerate(uploaded_files):
                    content = read_file(uploaded_file)
                    if not content.strip():
                        warn_msg(f"`{uploaded_file.name}` is empty — skipped")
                        continue
                    data = extract_from_note(content)
                    raw_with_name = f"[File: {uploaded_file.name}]\n\n{content}"
                    save_visit(
                        pid, start + i + 1, data, raw_with_name,
                        pat_name=st.session_state.get("pat_name", "N/A"),
                        pat_phone=st.session_state.get("pat_phone", "N/A")
                    )
                    success += 1

            if success:
                success_msg(f"Saved {success} visit(s) successfully")
                st.session_state["processed"] = True
                st.rerun()

    elif not all_visits:
        info_msg("No visits yet — upload visit note files above to get started")

    all_visits = get_visits(pid)

    # Determine session visits: only files uploaded THIS interaction count as "current session"
    # If no files uploaded (existing patient just loaded), ALL visits are historical — nothing is "current session"
    if uploaded_files and st.session_state.get("processed"):
        n_new = len(uploaded_files)
        new_visits = all_visits[-n_new:] if len(all_visits) >= n_new else all_visits
        old_visits = all_visits[:-n_new] if len(all_visits) > n_new else []
    else:
        # No files uploaded this session → everything is history, nothing is "current"
        old_visits = all_visits
        new_visits = []

    # ── History ──
    if all_visits:
        st.markdown('<div class="med-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Patient History</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="stat-row">
            <div class="stat-pill">
                <div class="stat-pill-label">Total Visits</div>
                <div class="stat-pill-value">{len(all_visits)}</div>
            </div>
            <div class="stat-pill">
                <div class="stat-pill-label">Past</div>
                <div class="stat-pill-value">{len(old_visits)}</div>
            </div>
            <div class="stat-pill">
                <div class="stat-pill-label">This Session</div>
                <div class="stat-pill-value">{len(new_visits)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if old_visits:
            st.markdown('<div class="section-label" style="margin-top:1.5rem">Past Visits</div>', unsafe_allow_html=True)
            for v in old_visits:
                render_visit(v, is_current=False)

        if new_visits:
            st.markdown('<div class="section-label" style="margin-top:1.5rem">Current Session</div>', unsafe_allow_html=True)
            for v in new_visits:
                render_visit(v, is_current=True)

    # ── Analysis ──
    if st.session_state.get("processed"):

        st.markdown('<div class="med-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Visit Analysis</div>', unsafe_allow_html=True)

        repeated = check_repeated_symptoms(new_visits)
        if repeated:
            st.markdown('<div style="margin-bottom:0.6rem;font-size:0.8rem;color:#4a6080;text-transform:uppercase;letter-spacing:0.08em">Symptom Frequency</div>', unsafe_allow_html=True)
            for s, count, label in repeated:
                st.markdown(f"""
                <div class="freq-row {label}">
                    <span class="freq-name">{s}</span>
                    <span class="freq-count">{count}×</span>
                    <span class="freq-badge">{label}</span>
                </div>
                """, unsafe_allow_html=True)

        trend = analyze_trend(new_visits)
        trend_icons = {
            "Improving": "📉",
            "Worsening (new symptoms added)": "📈",
            "Persistent symptoms": "➡️",
            "Changing pattern": "🔄",
            "Not enough data": "📊"
        }
        t_icon = trend_icons.get(trend, "📊")
        st.markdown(f"""
        <div class="trend-badge">{t_icon} &nbsp; <strong>Trend:</strong> &nbsp; {trend}</div>
        """, unsafe_allow_html=True)

        # ── Alerts ──
        st.markdown('<div class="section-label" style="margin-top:1.5rem">Alerts & Flags</div>', unsafe_allow_html=True)
        alerts = generate_all_alerts(new_visits, old_visits, new_visits)

        if not alerts:
            success_msg("No alerts — all clear")
        else:
            critical = [a for a in alerts if a["level"] == "critical"]
            high     = [a for a in alerts if a["level"] == "high"]
            medium   = [a for a in alerts if a["level"] == "medium"]
            low      = [a for a in alerts if a["level"] == "low"]

            def render_alerts(items, cls, label, emoji):
                if not items:
                    return
                st.markdown(f"""
                <div class="alert-group-header" style="color:{'#ff5050' if cls=='critical' else '#ff8c00' if cls=='high' else '#ffd200' if cls=='medium' else '#5a6a82'}">
                    {emoji} {label} <span class="alert-count">{len(items)}</span>
                </div>
                """, unsafe_allow_html=True)
                for a in items:
                    st.markdown(f"""
                    <div class="alert-item alert-{cls}">
                        <span class="alert-dot"></span>
                        <span>{a['message']}</span>
                    </div>
                    """, unsafe_allow_html=True)

            render_alerts(critical, "critical", "CRITICAL", "🔴")
            render_alerts(high,     "high",     "HIGH",     "🟠")
            render_alerts(medium,   "medium",   "MEDIUM",   "🟡")
            render_alerts(low,      "low",      "LOW",      "⚪")

    # ── Tracking ──
    if st.session_state.get("processed") and old_visits:

        st.markdown('<div class="med-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Patient Tracking</div>', unsafe_allow_html=True)

        track = patient_tracking(old_visits, new_visits)

        cols = st.columns(2)
        with cols[0]:
            if track["common"]:
                st.markdown('<div style="font-size:0.75rem;color:#4a6080;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem">Recurring Symptoms</div>', unsafe_allow_html=True)
                st.markdown(tags_html(sorted(track["common"]), "tag-symptom"), unsafe_allow_html=True)
        with cols[1]:
            if track["new_only"]:
                st.markdown('<div style="font-size:0.75rem;color:#4a6080;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem">New Symptoms</div>', unsafe_allow_html=True)
                st.markdown(tags_html(sorted(track["new_only"]), "tag-med"), unsafe_allow_html=True)

        if track["visit_analysis"]:
            st.markdown('<div style="font-size:0.75rem;color:#4a6080;text-transform:uppercase;letter-spacing:0.08em;margin:1rem 0 0.5rem">Per Visit Breakdown</div>', unsafe_allow_html=True)
            for v in track["visit_analysis"]:
                new_syms  = v.get("new_symptoms", [])
                rep_syms  = v.get("repeated_symptoms", [])
                new_names = ", ".join(new_syms) if new_syms else "—"
                rep_names = ", ".join(rep_syms) if rep_syms else "—"
                st.markdown(f"""
                <div class="track-row" style="flex-direction:column;align-items:flex-start;gap:4px;padding:0.7rem 0.8rem;">
                    <div style="display:flex;align-items:center;gap:12px;width:100%">
                        <span style="color:#8a9ab2;font-weight:600;min-width:60px">Visit {v['visit']}</span>
                        <span style="color:#50c8ff;font-size:0.82rem">🆕 {v['new_count']} new</span>
                        <span style="color:#ffa032;font-size:0.82rem">🔁 {v['repeated_count']} repeated</span>
                    </div>
                    <div style="font-size:0.78rem;color:#50c8ff;padding-left:72px">New: {new_names}</div>
                    <div style="font-size:0.78rem;color:#ffa032;padding-left:72px">Repeated: {rep_names}</div>
                </div>
                """, unsafe_allow_html=True)

        if track["gap_days"] is not None:
            sign = "+" if track["gap_days"] > 0 else ""
            st.markdown(f"""
            <div style="margin-top:1rem" class="trend-badge">📅 &nbsp; Gap from last visit: &nbsp; <strong>{sign}{track['gap_days']} days</strong></div>
            """, unsafe_allow_html=True)

    st.markdown('<div style="height:3rem"></div>', unsafe_allow_html=True)