import hashlib

def generate_patient_id(aadhar):
    return hashlib.md5(aadhar.encode()).hexdigest()[:10]

# ───────── SYNONYM MAP ─────────
# Medical shortforms / variations → standard word
SYNONYMS = {
    "bp"                  : "blood pressure",
    "htn"                 : "hypertension",
    "high blood pressure" : "hypertension",
    "sob"                 : "shortness of breath",
    "breathlessness"      : "shortness of breath",
    "breathless"          : "shortness of breath",
    "high temp"           : "fever",
    "high temperature"    : "fever",
    "pyrexia"             : "fever",
    "cold"                : "cough",
    "runny nose"          : "rhinitis",
    "body ache"           : "body pain",
    "bodyache"            : "body pain",
    "loose motions"       : "diarrhea",
    "loose stools"        : "diarrhea",
    "heart attack"        : "myocardial infarction",
    "mi"                  : "myocardial infarction",
    "sugar"               : "diabetes",
    "blood sugar"         : "diabetes",
    "fits"                : "seizure",
    "convulsions"         : "seizure",
    "chest tightness"     : "chest pain",
    "chest discomfort"    : "chest pain",
    "dizzy"               : "dizziness",
    "lightheaded"         : "dizziness",
    "throwing up"         : "vomiting",
    "puking"              : "vomiting",
    "tiredness"           : "fatigue",
    "weakness"            : "fatigue",
    "low energy"          : "fatigue",
}
 
# ───────── ALLERGY GROUPS ─────────
# If patient is allergic to key → all values are also dangerous
ALLERGY_GROUPS = {
    "penicillin"    : ["amoxicillin", "ampicillin", "cloxacillin", "flucloxacillin"],
    "sulfa"         : ["sulfamethoxazole", "cotrimoxazole", "trimethoprim"],
    "aspirin"       : ["ibuprofen", "naproxen", "diclofenac"],
    "codeine"       : ["morphine", "tramadol", "oxycodone"],
    "erythromycin"  : ["azithromycin", "clarithromycin"],
}
 
# ───────── SYMPTOM-MEDICATION MISMATCH ─────────
# Serious symptoms that should NOT be treated with only mild meds
SERIOUS_SYMPTOMS = [
    "chest pain",
    "shortness of breath",
    "seizure",
    "myocardial infarction",
    "stroke",
    "unconscious",
    "paralysis",
    "severe headache",
]
 
MILD_MEDS = [
    "paracetamol",
    "cetirizine",
    "antacid",
    "cough syrup",
    "vitamin c",
    "ors",
]
 
 
# ───────── NORMALIZE FUNCTION ─────────
def normalize(text):
    """Lowercase and replace known synonyms with standard terms."""
    text = text.lower().strip()
    for variant, standard in SYNONYMS.items():
        if variant in text:
            text = text.replace(variant, standard)
    return text
 
 
def normalize_list(items):
    """Normalize a list of symptoms or medications."""
    return [normalize(i) for i in items]