import json
import os
import re

FILE = "memory_db.json"


# ---------------- LOAD ----------------
def load_memory():
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


# ---------------- TEXT NORMALIZATION ----------------
def normalize(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', '', text)
    return text


def similarity(a, b):
    a_words = set(normalize(a).split())
    b_words = set(normalize(b).split())
    if not a_words or not b_words:
        return 0
    return len(a_words & b_words) / len(a_words | b_words)


# ---------------- SAVE ----------------
# CHANGE: Stores structured knowledge object — not raw summary text.
#
# Schema:
#   {
#     "question": "…",
#     "knowledge": {
#       "facts":      [ {"fact":…, "source":…, "confidence":…} ],
#       "confidence": "high|medium|low"   ← overall confidence tier
#     },
#     "verdict":  "…",
#     "sources":  [url, …]
#   }
#
# "summary" alias kept so old memory records still display
# correctly in the frontend (backward compatible).
def save_memory(question, knowledge, verdict, sources=None):
    """
    Args:
        question  : str — the research question
        knowledge : dict — {"facts": [...], "confidence": "…"}
                    OR a plain str (legacy) for backward compat
        verdict   : str — final decision agent output
        sources   : list of URL strings
    """
    memory = load_memory()

    # Accept both old str summaries and new structured knowledge dicts
    if isinstance(knowledge, str):
        knowledge_obj = {"facts": [], "confidence": "unknown", "raw": knowledge}
        summary_text  = knowledge
    else:
        knowledge_obj = knowledge
        # Build a readable summary from facts for backward compat
        facts = knowledge.get("facts", [])
        summary_text = "\n".join(f"• {f['fact']}" for f in facts[:6]) or "No facts extracted."

    memory.append({
        "question":  question,
        "knowledge": knowledge_obj,          # structured — new format
        "summary":   summary_text,           # flat text  — legacy compat
        "verdict":   verdict,
        "sources":   sources or []
    })

    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)


# ---------------- RETRIEVE ----------------
# CHANGE: Raises similarity threshold to 0.65 (was 0.55).
# Also requires >= 2 verified sources before trusting the cache.
# This prevents low-quality single-source memories from
# short-circuiting a new research session.
def retrieve_memory(question, min_similarity=0.65, min_sources=2):
    """
    Returns cached memory entries only when:
      - Jaccard similarity with question > 0.65
      - At least `min_sources` source URLs were stored

    Returns up to the 2 most recent qualifying entries.
    """
    memory = load_memory()
    results = []

    for item in memory:
        score      = similarity(question, item["question"])
        num_sources = len(item.get("sources", []))

        if score > min_similarity and num_sources >= min_sources:
            results.append(item)

    return results[-2:]