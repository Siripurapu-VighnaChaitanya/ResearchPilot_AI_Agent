import time
from agents import planner_agent, researcher_agent, analyst_agent

question = input("Enter question: ")

plan = planner_agent(question)

print("\n🧠 Planning research...\n")

tasks = [t for t in plan.split("\n") if len(t.strip()) > 15]

all_research = ""

for t in tasks[:4]:   # limit tasks for demo speed
    print(f"🔎 Researching: {t}")
    time.sleep(2)
    result = researcher_agent(t)
    all_research += result + "\n"

print("\n📊 Analyzing findings...\n")

summary = analyst_agent(question, all_research)

print("\n📊 Intelligence Summary:\n")
print(summary)

print("\n🧠 Making final decision...\n")

from agents import decision_agent
decision = decision_agent(question, summary)

print("\n=== FINAL AI VERDICT ===\n")
print(decision)