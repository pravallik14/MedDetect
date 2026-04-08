from collections import Counter
from datetime import datetime


# ───────── DATE ─────────
def parse_date(date_str):
    formats = ["%d/%m/%y", "%d/%m/%Y", "%B %d, %Y"]
    for f in formats:
        try:
            return datetime.strptime(date_str, f)
        except:
            continue
    return None


def sort_visits(records):
    return sorted(records, key=lambda x: parse_date(x["visit_date"]) or datetime.min)


# ───────── ALERT FORMAT ─────────
def make_alert(level, message):
    return {"level": level, "message": message}


# ───────── REPEATED SYMPTOMS ─────────
def check_repeated_symptoms(records):

    all_symptoms = []

    for r in records:
        all_symptoms.extend([s.lower() for s in r["symptoms"]])

    counts = Counter(all_symptoms)

    result = []

    for s, c in counts.items():
        if c >= 3:
            result.append((s, c, "chronic"))
        elif c == 2:
            result.append((s, c, "repeated"))

    return result


# ───────── TREND ─────────
def analyze_trend(records):

    if len(records) < 2:
        return "Not enough data"

    records = sort_visits(records)

    first = set([s.lower() for s in records[0]["symptoms"]])
    last = set([s.lower() for s in records[-1]["symptoms"]])

    new = last - first
    removed = first - last

    if first == last:
        return "Persistent symptoms"

    elif new and not removed:
        return "Worsening (new symptoms added)"

    elif removed and not new:
        return "Improving"

    else:
        return "Changing pattern"


# ───────── MAIN ALERT ENGINE ─────────
def generate_all_alerts(visits, old_visits, new_visits):

    alerts = []
    visits = sort_visits(visits)

    # ───────── VISIT COMPARISON ─────────
    for i in range(len(visits) - 1):

        v1 = visits[i]
        v2 = visits[i + 1]

        sym1 = set([s.lower() for s in v1["symptoms"]])
        sym2 = set([s.lower() for s in v2["symptoms"]])

        d1 = v1["diagnosis"].lower()
        d2 = v2["diagnosis"].lower()

        # SAME symptoms + DIFFERENT diagnosis → CONTRADICTION
        if sym1 == sym2 and d1 != d2:
            alerts.append(make_alert(
                "high",
                f"Visit {v1['visit_number']} → {v2['visit_number']}: Same symptoms but different diagnosis"
            ))

        # DIFFERENT symptoms + SAME diagnosis → suspicious
        elif sym1 != sym2 and d1 == d2:
            alerts.append(make_alert(
                "medium",
                f"Visit {v1['visit_number']} → {v2['visit_number']}: Same diagnosis despite symptom change"
            ))

        # NORMAL evolution → low (not serious)
        elif sym1 != sym2 and d1 != d2:
            alerts.append(make_alert(
                "low",
                f"Visit {v1['visit_number']} → {v2['visit_number']}: Condition evolving"
            ))

    # ───────── HISTORY ALERT (FIXED DUPLICATES) ─────────
    old_symptoms = set()

    for v in old_visits:
        old_symptoms.update([s.lower() for s in v["symptoms"]])

    seen = set()  # 🔥 prevent duplicates

    for v in new_visits:
        for s in v["symptoms"]:
            s_lower = s.lower()

            if s_lower in old_symptoms and s_lower not in seen:
                alerts.append(make_alert(
                    "medium",
                    f"{s} reappeared from past visits"
                ))
                seen.add(s_lower)

    return alerts
def patient_tracking(old_visits, new_visits):

    # collect symptoms
    old_symptoms = set()
    for v in old_visits:
        old_symptoms.update([s.lower() for s in v["symptoms"]])

    new_symptoms_all = set()
    for v in new_visits:
        new_symptoms_all.update([s.lower() for s in v["symptoms"]])

    # common & new
    common = old_symptoms.intersection(new_symptoms_all)
    new_only = new_symptoms_all - old_symptoms

    # per visit analysis
    visit_analysis = []

    for v in new_visits:
        sym = [s.lower() for s in v["symptoms"]]

        repeated = [s for s in sym if s in old_symptoms]
        new = [s for s in sym if s not in old_symptoms]

        visit_analysis.append({
            "visit": v["visit_number"],
            "new_count": len(new),
            "repeated_count": len(repeated),
            "new_symptoms": new,
            "repeated_symptoms": repeated
        })

    # date gap
    gap_days = None
    if old_visits:
        last_old = old_visits[-1]["visit_date"]
        first_new = new_visits[0]["visit_date"]

        try:
            d1 = parse_date(last_old)
            d2 = parse_date(first_new)

            if d1 and d2:
                gap_days = (d2 - d1).days
        except:
            pass

    return {
        "common": common,
        "new_only": new_only,
        "visit_analysis": visit_analysis,
        "gap_days": gap_days
    }