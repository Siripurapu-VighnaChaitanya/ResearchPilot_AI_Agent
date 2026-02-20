import os
import re
import json
import time
from ddgs import DDGS
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
_MODEL  = "llama-3.1-8b-instant"

# ============================================================
# FAST PRE-FILTER  (keyword Jaccard — no LLM call)
# Runs BEFORE the expensive LLM relevance scorer to discard
# obviously off-topic results cheaply.
# ============================================================
_STOPWORDS = {
    "a","an","the","is","are","was","were","be","been","being",
    "have","has","had","do","does","did","will","would","could",
    "should","may","might","to","of","in","on","at","for","with",
    "by","from","and","or","but","not","this","that","it","its",
    "as","if","what","how","its","we","they","their","our",
}

def _tokens(text):
    words = re.findall(r'\b[a-z]{2,}\b', text.lower())
    return set(w for w in words if w not in _STOPWORDS)

def _jaccard(a_tokens, b_text):
    b = _tokens(b_text)
    if not a_tokens or not b:
        return 0.0
    return len(a_tokens & b) / len(a_tokens | b)


# ============================================================
# RELEVANCE SCORER  (LLM-graded 0-5 per paragraph)
#
# Scores: 0 = unrelated, 1 = weak, 2 = mentions keyword,
#         3 = partially relevant, 4 = relevant,
#         5 = directly answers the query.
# Reject everything < 3.
# ============================================================
def _score_relevance(paragraph, query):
    """
    Calls LLM to score relevance of a web paragraph to the query.
    Returns integer 0-5.  Falls back to 0 on parse error.
    """
    prompt = f"""Rate how relevant this text is to the research query.
Respond with a SINGLE INTEGER from 0 to 5 only. No explanation.

0 = completely unrelated
1 = weak relation
2 = mentions the keyword but off-topic
3 = partially relevant
4 = relevant and useful
5 = directly answers the query

QUERY: {query}

TEXT: {paragraph[:600]}
"""
    try:
        r = _client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0,
        )
        raw = r.choices[0].message.content.strip()
        # Extract first digit found
        m = re.search(r'[0-5]', raw)
        return int(m.group()) if m else 0
    except Exception:
        return 0


# ============================================================
# FACT EXTRACTOR  (structured JSON per relevant source)
#
# Extracts verifiable facts with source URL and confidence.
# Returns {"facts": [{"fact":…,"source":…,"confidence":…}]}
# Falls back to empty list on JSON parse error.
# ============================================================
def _extract_facts(text, url, query):
    """
    Given a relevant paragraph and its source URL, asks the LLM
    to extract structured facts as JSON objects.
    """
    prompt = f"""You are a scientific fact extractor.

QUERY: {query}
SOURCE URL: {url}

TEXT:
{text[:800]}

Extract verifiable facts from this text that are relevant to the query.
Return ONLY a valid JSON object — nothing else.

Format:
{{
  "facts": [
    {{"fact": "<one clear factual statement>", "source": "{url}", "confidence": "<high|medium|low>"}}
  ]
}}

Rules:
- Max 3 facts per source.
- Only include facts DIRECTLY relevant to the query.
- "confidence" is high if the text explicitly states it, medium if implied, low if uncertain.
- If no relevant facts exist, return {{"facts": []}}
- Return ONLY the JSON. Do NOT add explanation or markdown.
"""
    try:
        r = _client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw = r.choices[0].message.content.strip()
        # Strip markdown code fences if present
        raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
        raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)
        return json.loads(raw).get("facts", [])
    except Exception:
        return []


# ============================================================
# MAIN PIPELINE ENTRY
# search_and_extract() — replaces old search_web()
#
# Flow:
#   1. DuckDuckGo text search (up to 7 results)
#   2. Jaccard pre-filter  (cheap, no LLM)
#   3. LLM relevance score (0-5, reject < 3)
#   4. LLM fact extraction (structured JSON)
#   5. Return merged facts + source URLs
# ============================================================
def search_and_extract(query, retries=3):
    """
    Full evidence pipeline for a single research query.

    Returns:
        {
          "facts":   [ {"fact":…, "source":…, "confidence":…} ],
          "sources": [ url, … ]   # unique source URLs
        }
    """
    raw_results = []

    for attempt in range(retries):
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=7):
                    raw_results.append({
                        "title": r.get("title", ""),
                        "body":  r.get("body", ""),
                        "url":   r.get("href", "")
                    })
            if raw_results:
                break
        except Exception:
            time.sleep(2)

    if not raw_results:
        return {"facts": [], "sources": []}

    # ---- Step 2: Jaccard pre-filter (fast, no LLM) ----
    query_tokens = _tokens(query)
    prescored = []
    for r in raw_results:
        combined = f"{r['title']} {r['body']}"
        j = _jaccard(query_tokens, combined)
        prescored.append((j, r))

    # Sort descending; keep top 5 for LLM scoring
    prescored.sort(key=lambda x: x[0], reverse=True)
    candidates = [r for _, r in prescored[:5]]

    # ---- Step 3: LLM relevance scoring (reject < 3) ----
    relevant = []
    for r in candidates:
        score = _score_relevance(r["body"], query)
        if score >= 3:
            relevant.append(r)

    # Graceful fallback: if nothing passes LLM filter, use top-2 Jaccard hits
    if not relevant:
        relevant = [r for _, r in prescored[:2]]

    # ---- Step 4: Structured fact extraction ----
    all_facts = []
    all_sources = []

    for r in relevant:
        facts = _extract_facts(r["body"], r["url"], query)
        all_facts.extend(facts)
        if r["url"] and r["url"] not in all_sources:
            all_sources.append(r["url"])

    return {
        "facts":   all_facts,
        "sources": all_sources
    }


# ============================================================
# KEPT for backward compatibility — used by filter_relevant_results
# callers elsewhere (does not break existing imports).
# ============================================================
def search_web(query, retries=3):
    """Legacy wrapper — returns structured result list."""
    for attempt in range(retries):
        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=7):
                    results.append({
                        "title": r.get("title", ""),
                        "body":  r.get("body", ""),
                        "url":   r.get("href", "")
                    })
            if results:
                return {"results": results, "sources": [r["url"] for r in results]}
        except Exception:
            time.sleep(2)
    return {"results": [], "sources": []}


def filter_relevant_results(results, task, threshold=0.10, top_k=3):
    """Legacy keyword filter — kept so old import paths still work."""
    task_tokens = _tokens(task)
    scored = [(
        _jaccard(task_tokens, f"{r['title']} {r['body']}"), r
    ) for r in results]
    scored.sort(key=lambda x: x[0], reverse=True)
    passing = [(s, r) for s, r in scored if s >= threshold]
    pool = passing if passing else scored
    return [r for _, r in pool[:top_k]]