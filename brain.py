import os
from groq import Groq
from dotenv import load_dotenv
from tools import search_web

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

while True:
    question = input("Ask ResearchPilot > ")

    # Step 1: search internet
    web_info = search_web(question)

    prompt = f"""
You are ResearchPilot, an autonomous research system.

Carefully read the web research data and produce a factual answer.
If information exists — summarize it.
If partial — reason logically.
Never say 'no information' unless truly empty.

WEB RESEARCH:
{web_info}

USER QUESTION:
{question}

Give a clear, confident explanation.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    print("\nResearchPilot:", response.choices[0].message.content, "\n")