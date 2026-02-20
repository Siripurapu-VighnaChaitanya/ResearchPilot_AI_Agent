import json
from agents import planner_agent, researcher_agent, analyst_agent, decision_agent
from memory import retrieve_memory, save_memory


def _facts_to_display(facts, query=""):
    """
    Converts a list of {"fact","source","confidence"} dicts into a
    clean human-readable bullet string for the UI stream.
    Never exposes raw JSON to the frontend.
    """
    if not facts:
        return "⚠ No validated evidence found for this query."

    lines = []
    if query:
        lines.append(f"**Query:** {query}\n")

    for i, f in enumerate(facts, 1):
        confidence_icon = {"high": "✓", "medium": "~", "low": "?"}.get(
            f.get("confidence", "low"), "~"
        )
        lines.append(f"{confidence_icon} {f.get('fact', '')}")

    # Collect unique sources for a compact reference line
    sources = list(dict.fromkeys(
        f.get("source", "") for f in facts if f.get("source")
    ))
    if sources:
        refs = "  ".join(f"[{i+1}] {s}" for i, s in enumerate(sources[:3]))
        lines.append(f"\n_Sources: {refs}_")

    return "\n".join(lines)


def run_research_pipeline_stream(question):

    # ============================================================
    # MEMORY RETRIEVAL
    # CHANGE: threshold raised to 0.65 AND requires >= 2 sources.
    # Memory items now carry structured "knowledge" objects.
    # ============================================================
    past = retrieve_memory(question)

    if past:
        yield {"stage": "memory", "content": "Found related verified research. Reusing validated knowledge."}

        # Rebuild flat fact list from cached knowledge objects
        cached_facts = []
        cached_sources = []
        for p in past:
            knowledge = p.get("knowledge", {})
            if isinstance(knowledge, dict):
                cached_facts.extend(knowledge.get("facts", []))
            cached_sources.extend(p.get("sources", []))

        cached_sources = list(dict.fromkeys(cached_sources))  # deduplicate

        # Run analyst on cached facts
        analysis = analyst_agent(question, cached_facts)
        yield {"stage": "analysis", "content": analysis["human_summary"]}

        verdict = decision_agent(question, analysis, sources=cached_sources)
        yield {"stage": "decision", "content": verdict}
        return


    # ============================================================
    # PLANNING — structured JSON query objects
    # CHANGE: planner now returns [{"query":…,"goal":…}] list
    # ============================================================
    yield {"stage": "planning", "content": "Formulating research queries..."}

    query_objects = planner_agent(question)

    # Display the plan as human-readable text (not raw JSON)
    plan_display = "\n".join(
        f"{i+1}. {q.get('query', q) if isinstance(q, dict) else q}"
        for i, q in enumerate(query_objects)
    )
    yield {"stage": "planning", "content": f"**Research Plan:**\n{plan_display}"}


    # ============================================================
    # RESEARCH — structured fact collection
    # CHANGE: researcher_agent returns {"facts":[…],"sources":[…]}
    # All facts are accumulated as flat list for the analyst.
    # ============================================================
    all_facts   = []   # flat list of {"fact","source","confidence"} dicts
    all_sources = []   # unique source URLs across all queries

    for query_obj in query_objects[:3]:
        result = researcher_agent(query_obj)

        task_facts   = result.get("facts", [])
        task_sources = result.get("sources", [])
        query_str    = result.get("query", query_obj.get("query", "") if isinstance(query_obj, dict) else "")

        # Accumulate facts and sources
        all_facts.extend(task_facts)
        for s in task_sources:
            if s and s not in all_sources:
                all_sources.append(s)

        # Stream human-readable evidence bullets (never raw JSON)
        yield {
            "stage":   "research",
            "content": _facts_to_display(task_facts, query=query_str)
        }


    # ============================================================
    # ANALYSIS — cross-source synthesis
    # CHANGE: analyst receives flat fact list (structured JSON),
    # returns {key_points, uncertain_points, contradictions}.
    # human_summary is what we stream to the UI.
    # ============================================================
    analysis = analyst_agent(question, all_facts)
    yield {"stage": "analysis", "content": analysis["human_summary"]}


    # ============================================================
    # DECISION — evidence-tier verdict
    # CHANGE: decision_agent receives the structured analysis dict
    # and full source list to compute correct confidence tier.
    # ============================================================
    verdict = decision_agent(question, analysis, sources=all_sources)
    yield {"stage": "decision", "content": verdict}


    # ============================================================
    # SAVE MEMORY — structured knowledge object
    # CHANGE: stores {facts, confidence} dict, not a raw summary.
    # ============================================================
    # Determine overall confidence tier based on source count
    n = len(all_sources)
    if n >= 3:
        overall_confidence = "high"
    elif n == 2:
        overall_confidence = "medium"
    else:
        overall_confidence = "low"

    knowledge_obj = {
        "facts":      all_facts,
        "confidence": overall_confidence
    }

    save_memory(question, knowledge_obj, verdict, sources=all_sources)