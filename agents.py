import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def planner_agent(question):
    prompt = f"""
You are the PLANNER agent in an autonomous research system.

Your job:
Break the user's question into clear research sub-questions
that other agents can investigate.

USER QUESTION:
{question}

Return 4 to 6 specific research tasks.
Be precise and analytical.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

from tools import search_web

def researcher_agent(task):
    web_data = search_web(task)

    prompt = f"""
You are the RESEARCHER agent.

If web data is missing or limited, still reason logically using general knowledge.

TASK:
{task}

WEB DATA:
{web_data}

Return key findings in bullet points.
Be practical and informative.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

def analyst_agent(question, research_text):
    prompt = f"""
You are the ANALYST agent.

Your job:
Read the research findings and produce a concise intelligence summary.

RULES:
- Max 8 bullet points
- Clear insights only
- No long paragraphs
- Focus on conclusions

QUESTION:
{question}

RESEARCH DATA:
{research_text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

def decision_agent(question, analysis):
    prompt = f"""
You are the CHIEF DECISION AGENT.

Based on the analysis, produce a final judgment.

OUTPUT FORMAT:
Final Verdict: (1-2 sentences clear answer)
Reasoning: (short explanation)
Confidence: (0-100%)

QUESTION:
{question}

ANALYSIS:
{analysis}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content