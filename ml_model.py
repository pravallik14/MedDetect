import os
import json
import pickle
import numpy as np
import pandas as pd
import scipy.sparse as sp
from groq import Groq
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
from utils import normalize_list

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


# ═══════════════════════════════════════════
# LAYER 1 — RULE BASED
# ═══════════════════════════════════════════

RULES = [
    {"symptoms": {"fever", "cough", "cold"},                    "disease": "Influenza (Flu)"},
    {"symptoms": {"fever", "cough"},                            "disease": "Influenza (Flu)"},
    {"symptoms": {"fever", "runny nose", "sore throat"},        "disease": "Common Cold"},
    {"symptoms": {"fever", "rash", "joint pain"},               "disease": "Dengue"},
    {"symptoms": {"fever", "rash", "body pain"},                "disease": "Dengue"},
    {"symptoms": {"fever", "joint pain", "fatigue"},            "disease": "Dengue"},
    {"symptoms": {"chest pain", "sweating"},                    "disease": "Coronary Artery Disease"},
    {"symptoms": {"chest pain", "shortness of breath"},         "disease": "Pulmonary Embolism"},
    {"symptoms": {"chest pain", "dizziness"},                   "disease": "Coronary Artery Disease"},
    {"symptoms": {"frequent urination", "fatigue"},             "disease": "Diabetes Mellitus"},
    {"symptoms": {"frequent urination", "weight loss"},         "disease": "Diabetes Mellitus"},
    {"symptoms": {"fatigue", "blurred vision"},                 "disease": "Diabetes Mellitus"},
    {"symptoms": {"headache", "nausea", "vomiting"},            "disease": "Migraine"},
    {"symptoms": {"severe headache", "light sensitivity"},      "disease": "Migraine"},
    {"symptoms": {"fever", "abdominal pain", "diarrhea"},       "disease": "Typhoid Fever"},
    {"symptoms": {"fever", "weakness", "loss of appetite"},     "disease": "Typhoid Fever"},
    {"symptoms": {"cough", "fever", "chest pain"},              "disease": "Pneumonia"},
    {"symptoms": {"cough", "shortness of breath", "fever"},     "disease": "Pneumonia"},
    {"symptoms": {"fever", "chills", "sweating"},               "disease": "Malaria"},
    {"symptoms": {"fever", "chills", "headache"},               "disease": "Malaria"},
    {"symptoms": {"nausea", "vomiting", "diarrhea"},            "disease": "Gastroenteritis"},
    {"symptoms": {"vomiting", "diarrhea", "abdominal pain"},    "disease": "Gastroenteritis"},
    {"symptoms": {"headache", "dizziness", "blood pressure"},   "disease": "Hypertension"},
    {"symptoms": {"seizure", "unconscious"},                    "disease": "Epilepsy"},
    {"symptoms": {"fatigue", "pallor", "dizziness"},            "disease": "Anemia"},
    {"symptoms": {"burning urination", "frequent urination"},   "disease": "Urinary Tract Infection"},
    {"symptoms": {"wheezing", "shortness of breath"},           "disease": "Asthma"},
    {"symptoms": {"cough", "wheezing", "chest tightness"},      "disease": "Asthma"},
]


def _rule_predict(symptoms_normalized):
    sym_set    = set(symptoms_normalized)
    best       = None
    best_score = 0

    for rule in RULES:
        overlap  = len(rule["symptoms"].intersection(sym_set))
        coverage = overlap / len(rule["symptoms"])

        if overlap >= 2 and coverage == 1.0 and overlap > best_score:
            best_score = overlap
            best       = rule["disease"]

    return best


# ═══════════════════════════════════════════
# LAYER 2 — SIMILARITY (dataset powered)
# ═══════════════════════════════════════════

_BASE = os.path.dirname(os.path.abspath(__file__))

def _load_similarity_model():
    vec_path     = os.path.join(_BASE, "symptom_vectorizer.pkl")
    vectors_path = os.path.join(_BASE, "disease_vectors.npz")
    names_path   = os.path.join(_BASE, "disease_names.csv")

    if not all(os.path.exists(p) for p in [vec_path, vectors_path, names_path]):
        return None, None, None

    with open(vec_path, "rb") as f:
        vec = pickle.load(f)

    disease_vectors = sp.load_npz(vectors_path)
    disease_names   = pd.read_csv(names_path)["Disease"].tolist()

    return vec, disease_vectors, disease_names


_vec, _disease_vectors, _disease_names = _load_similarity_model()


def _similarity_predict(symptoms_normalized):
    if _vec is None:
        return None, 0.0

    query     = " ".join(symptoms_normalized)
    query_vec = _vec.transform([query])
    sims      = cosine_similarity(query_vec, _disease_vectors).flatten()
    top_idx   = int(sims.argmax())
    score     = float(sims[top_idx])

    return _disease_names[top_idx], score


# ═══════════════════════════════════════════
# LAYER 3 — GROQ FALLBACK
# ═══════════════════════════════════════════

def _groq_predict(symptoms_normalized):
    prompt = f"""
You are a medical diagnosis assistant.
Given these symptoms: {', '.join(symptoms_normalized)}

Reply ONLY with a JSON object like this:
{{"disease": "Disease Name"}}

No explanation. No markdown. Just JSON.
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=50,
        )
        raw  = response.choices[0].message.content.strip()
        raw  = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        return data.get("disease", "Unknown")
    except:
        return "Unknown"


# ═══════════════════════════════════════════
# MAIN — called by app.py
# ═══════════════════════════════════════════

def predict_disease(symptoms: list):
    """
    Input  : raw symptom list from visit  e.g. ["fever", "cough"]
    Output : {
        "disease"    : "Influenza (Flu)",
        "layer"      : "Rules" | "Similarity" | "Groq",
        "confidence" : "high" | "medium" | "low",
        "score"      : 0.87   (only for Similarity layer, else None)
    }
    """
    if not symptoms:
        return {"disease": "Unknown", "layer": "None", "confidence": "low", "score": None}

    normalized = normalize_list(symptoms)

    # Layer 1
    result = _rule_predict(normalized)
    if result:
        return {"disease": result, "layer": "Rules", "confidence": "high", "score": None}

    # Layer 2
    disease, score = _similarity_predict(normalized)
    if disease and score >= 0.15:
        confidence = "high" if score >= 0.35 else "medium" if score >= 0.20 else "low"
        return {"disease": disease, "layer": "Similarity", "confidence": confidence, "score": round(score, 2)}

    # Layer 3
    groq_disease = _groq_predict(normalized)
    return {"disease": groq_disease, "layer": "Groq", "confidence": "low", "score": None}