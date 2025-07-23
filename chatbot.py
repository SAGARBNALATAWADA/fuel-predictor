"""
Light‑weight offline chatbot for the Fuel‑Consumption‑Prediction project.

• Loads Q&A pairs from a local JSON file.
• Uses simple fuzzy / substring matching (difflib) – no internet, no ML model.
• Exposes `ask_bot(user_input)` which returns (answer, suggestions).

Author: Sagar • 2025
"""
from pathlib import Path
import json, re
from difflib import get_close_matches

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
# Name your file whatever you like:
KB_FILE = Path(__file__).with_name("knowledge_base_fuel_qa.json")

# Fallback canned answers if KB is missing
DEFAULT_KB = [
    {
        "question": "What is good fuel economy?",
        "answer": "Anything below 10 L/100 km (or above 23 mpg) is generally considered fuel‑efficient."
    },
    {
        "question": "How can I improve fuel consumption?",
        "answer": "Maintain steady speed, keep tyres inflated, reduce extra weight, and service your engine regularly."
    },
    {
        "question": "Which fuel type is most efficient?",
        "answer": "Diesel engines typically consume less fuel per kilometre, but emissions and maintenance differ."
    },
]

# ─────────────────────────────────────────────
# Load knowledge base
# ─────────────────────────────────────────────
if KB_FILE.exists():
    with KB_FILE.open(encoding="utf-8") as f:
        knowledge_base = json.load(f)
else:
    knowledge_base = DEFAULT_KB

# ─────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────
def _clean(text: str) -> str:
    """Lower‑case, strip punctuation/spaces for matching."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text.strip()

_questions_raw      = [item["question"] for item in knowledge_base]
_questions_cleaned  = [_clean(q)        for q in _questions_raw]

# ─────────────────────────────────────────────
# Main API
# ─────────────────────────────────────────────
def ask_bot(user_input: str):
    """
    Return a tuple (reply, suggestions)

    suggestions → up to 5 related questions the user might want next.
    """
    if not user_input:
        return ("I didn't catch that. Please type a question.", [])

    user_c = _clean(user_input)

    # ---------- 1. try fuzzy match against KB ----------
    matches = get_close_matches(user_c, _questions_cleaned, n=1, cutoff=0.6)
    if matches:
        idx = _questions_cleaned.index(matches[0])
        answer = knowledge_base[idx]["answer"]
    else:
        # ---------- 2. manual keyword fall‑backs ----------
        if any(w in user_c for w in ("hello", "hi")):
            answer = "Hello! I'm FuelBot – ask me anything about fuel efficiency."
        elif "thank" in user_c:
            answer = "You're welcome! Safe driving."
        else:
            answer = ("I'm still learning. Ask me about fuel types, "
                      "saving tips, or enter a vehicle parameter question.If you need more help mail to:support@fuelquestions.com")
    # ---------- 3. suggestions ----------
    suggestions = _get_suggestions(user_c)
    return answer, suggestions


def _get_suggestions(partial: str):
    """Return up to 5 similar questions from KB."""
    partial_c = _clean(partial)

    # Fuzzy match
    fuzz = get_close_matches(partial_c, _questions_cleaned, n=10, cutoff=0.3)
    # Sub‑string match
    subs = [q for q in _questions_raw if partial_c in _clean(q)]

    # Merge & deduplicate‑keeping original order
    seen, combined = set(), []
    for q in fuzz + subs:
        raw = _questions_raw[_questions_cleaned.index(_clean(q))] if q in fuzz else q
        if raw not in seen:
            combined.append(raw)
            seen.add(raw)
    return combined[:5]
