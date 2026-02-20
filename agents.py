import os
import re
import json
from groq import Groq
from dotenv import load_dotenv
from tools import search_and_extract

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL  = "llama-3.1-8b-instant"


# ============================================================
# HELPERS
# ============================================================
def _safe_json(text, fallback):
    """
    Parse JSON from LLM output, stripping markdown fences if present.
    Returns fallback value on any parse error.
    """
    try:
        text = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.MULTILINE)
        text = re.sub(r'\s*```$', '', text.strip(), flags=re.MULTILINE)
        return json.loads(text)
    except Exception:
        return fallback


# ============================================================
# PLANNER AGENT
#
# CHANGE: Now outputs structured JSON instead of plain text.
# Each query object has:
#   "query" — the specific factual question to research
#   "goal"  — what evidence the researcher should find
#
# The pipeline iterates this list, one researcher call per item.
# ============================================================
def planner_agent(question):
    prompt = f"""You are a research director. Break the following question into exactly 3 focused research queries.

Each query must:
- Be a specific, self-contained factual question (not a topic overview)
- Directly contribute evidence to answer the main question
- Avoid generic tasks like "define X", "overview of Y", "explain the history of Z"

Respond ONLY with a valid JSON array — no explanation, no markdown.

Format:
[
  {{"query": "<specific factual question>", "goal": "<what evidence this query should find>"}},
  {{"query": "...", "goal": "..."}},
  {{"query": "...", "goal": "..."}}
]

MAIN QUESTION: {question}
"""
    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    raw = r.choices[0].message.content

    # Parse JSON; fall back to a single generic query so pipeline never crashes
    queries = _safe_json(raw, fallback=None)
    if not isinstance(queries, list) or len(queries) == 0:
        # Graceful degradation: split by newline and wrap as query objects
        lines = [l.strip() for l in raw.splitlines() if len(l.strip()) > 5][:3]
        queries = [{"query": l, "goal": "find relevant evidence"} for l in lines]

    return queries          # list of {"query":…, "goal":…}


# ============================================================
# RESEARCHER AGENT — TWO-STEP EVIDENCE PIPELINE
#
# CHANGE: Accepts a query object dict (not a plain string).
# Delegates ALL web fetching + relevance scoring + fact
# extraction to tools.search_and_extract(), which:
#   1. Fetches 7 DuckDuckGo results
#   2. Jaccard pre-filters to top 5
#   3. LLM scores each paragraph 0-5 (rejects < 3)
#   4. LLM extracts structured facts as JSON
#
# Returns {"facts": [...], "sources": [...]}
# Never returns raw web text.
# ============================================================
def researcher_agent(query_obj):
    """
    Args:
        query_obj: {"query": str, "goal": str}

    Returns:
        {"facts": [{"fact":…,"source":…,"confidence":…}], "sources": [url,…]}
    """
    query = query_obj.get("query", "") if isinstance(query_obj, dict) else str(query_obj)

    result = search_and_extract(query)

    facts   = result.get("facts", [])
    sources = result.get("sources", [])

    # If extraction yielded nothing, return empty structure (never raw text)
    if not facts:
        return {
            "facts": [],
            "sources": sources,
            "query": query
        }

    return {
        "facts":   facts,
        "sources": sources,
        "query":   query
    }


# ============================================================
# ANALYST AGENT — CROSS-SOURCE SYNTHESIS
#
# CHANGE: Accepts a list of fact dicts (structured JSON),
# NOT a blob of text. Performs:
#   - Combine agreeing facts → key_points
#   - Detect contradictions  → contradictions
#   - Flag unsupported claims → uncertain_points
#
# Returns parsed JSON dict so downstream code can read it
# programmatically. Also returns a human_summary string for
# streaming to the UI.
# ============================================================
def analyst_agent(question, all_facts):
    """
    Args:
        question : the original user question
        all_facts: flat list of {"fact":…,"source":…,"confidence":…} dicts

    Returns:
        {
          "key_points":    [str, …],
          "uncertain_points": [str, …],
          "contradictions": [str, …],
          "human_summary": str   # formatted text for UI stream
        }
    """
    if not all_facts:
        return {
            "key_points": [],
            "uncertain_points": ["No validated evidence was collected."],
            "contradictions": [],
            "human_summary": "⚠ Insufficient evidence to perform analysis."
        }

    # Serialize facts for the LLM context
    facts_json = json.dumps(all_facts, indent=2)

    prompt = f"""You are a senior intelligence analyst. Perform CROSS-SOURCE SYNTHESIS on the evidence below.

MAIN QUESTION: {question}

EXTRACTED FACTS (JSON):
{facts_json}

YOUR TASK:
Analyze the facts across all sources and produce structured intelligence.

1. key_points      — facts that multiple sources AGREE on (or one high-confidence fact with no contradiction). State as conclusions, not raw facts.
2. uncertain_points — facts mentioned by only one low-confidence source, or that need more evidence.
3. contradictions  — cases where sources DISAGREE. State both sides and which is more credible.

Rules:
- Do NOT invent facts not present in the input.
- Do NOT summarize. REASON across facts.
- key_points must be conclusions/inferences, not restatements.
- Each entry max 2 sentences.
- Return ONLY valid JSON — no markdown, no explanation.

Format:
{{
  "key_points": ["<conclusion>", "..."],
  "uncertain_points": ["<uncertain claim>", "..."],
  "contradictions": ["<source A says X, source B says Y; X is more credible because…>", "..."]
}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    raw = response.choices[0].message.content
    parsed = _safe_json(raw, fallback={
        "key_points": [],
        "uncertain_points": ["Analysis parsing failed."],
        "contradictions": []
    })

    # Build a clean human-readable summary for the UI stream
    lines = ["**Intelligence Insights**\n"]

    if parsed.get("key_points"):
        lines.append("**Key Conclusions:**")
        for kp in parsed["key_points"]:
            lines.append(f"• {kp}")

    if parsed.get("contradictions"):
        lines.append("\n**Contradictions Detected:**")
        for c in parsed["contradictions"]:
            lines.append(f"⚠ {c}")

    if parsed.get("uncertain_points"):
        lines.append("\n**Uncertain / Needs More Evidence:**")
        for u in parsed["uncertain_points"]:
            lines.append(f"? {u}")

    parsed["human_summary"] = "\n".join(lines)
    return parsed


# ============================================================
# DECISION AGENT — EVIDENCE-TIER CONFIDENCE
#
# CHANGE: Confidence is determined by INDEPENDENT SOURCE COUNT:
#   0-1 sources → 40%  → cautious / "insufficient data" verdict
#   2   sources → 60%  → mixed, caveated verdict
#   3+  sources → 80-95% → assertive verdict
#
# High-confidence sources boost score; low-confidence cap it.
# Verdict tone changes with confidence tier.
# ============================================================
def decision_agent(question, analysis_result, sources=None):
    """
    Args:
        question        : original user question
        analysis_result : dict from analyst_agent (with key_points etc.)
        sources         : list of unique source URLs

    Returns:
        str — formatted verdict for UI
    """
    sources = sources or []
    n_sources = len(set(sources))

    # Source-count confidence tiers (per spec)
    if n_sources == 0:
        confidence_pct = 0
        tier = "insufficient"
    elif n_sources == 1:
        confidence_pct = 40
        tier = "weak"
    elif n_sources == 2:
        confidence_pct = 60
        tier = "mixed"
    else:
        # 3+ sources: scale 80-95 based on count
        confidence_pct = min(80 + (n_sources - 3) * 5, 95)
        tier = "strong"

    # Further adjust based on analyst output quality
    key_points      = analysis_result.get("key_points", [])
    contradictions  = analysis_result.get("contradictions", [])
    uncertain       = analysis_result.get("uncertain_points", [])

    if contradictions and tier == "strong":
        confidence_pct = max(confidence_pct - 15, 60)
    if not key_points:
        confidence_pct = min(confidence_pct, 40)
        tier = "insufficient"

    citation_line = (
        f"Supported by {n_sources} independent source{'s' if n_sources != 1 else ''}."
    )

    # Tier-specific verdict instruction
    tier_instructions = {
        "insufficient": "State that the evidence is INSUFFICIENT to draw a reliable conclusion. Explain what additional information would be needed.",
        "weak":         "Give a CAUTIOUS answer. Make clear this is based on limited evidence. Avoid definitive claims.",
        "mixed":        "Give a NUANCED answer. Acknowledge uncertainty where it exists. State which conclusion is better supported.",
        "strong":       "Give a DIRECT, ASSERTIVE answer. Commit to a verdict. The evidence is sufficient.",
    }

    # Format key points for LLM context
    insights_text = "\n".join(f"- {kp}" for kp in key_points) or "No key conclusions found."
    contradictions_text = "\n".join(f"- {c}" for c in contradictions) or "None"

    prompt = f"""You are a senior policy advisor delivering a final research briefing.
Evidence quality: {tier.upper()} ({n_sources} independent source{'s' if n_sources != 1 else ''})
Instruction: {tier_instructions[tier]}

QUESTION: {question}

KEY CONCLUSIONS FROM ANALYSIS:
{insights_text}

CONTRADICTIONS:
{contradictions_text}

RESPOND IN THIS EXACT FORMAT (no extra sections):

Final Verdict: <Direct answer, adjusted for evidence strength. Max 2 sentences.>

Reasoning: <Why this verdict follows from the analysis. Reference specific conclusions. Max 3 sentences. Do NOT repeat the verdict.>

Confidence: {confidence_pct}%

{citation_line}
"""

    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    verdict_text = r.choices[0].message.content.strip()

    # Guarantee citation line is always present
    if citation_line not in verdict_text:
        verdict_text = verdict_text.rstrip() + f"\n{citation_line}"

    return verdict_text