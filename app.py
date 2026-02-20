from flask import Flask, request, jsonify
from flask import render_template
from agents import planner_agent, researcher_agent, analyst_agent, decision_agent
import time

app = Flask(__name__)

def run_research_pipeline(question):
    steps = []

    # 1 Planning
    steps.append({"stage": "planning", "content": "Breaking down the problem..."})
    plan = planner_agent(question)

    tasks = [t for t in plan.split("\n") if len(t.strip()) > 15][:3]

    research_data = ""

    # 2 Research
    for t in tasks:
        steps.append({"stage": "research", "content": t})
        time.sleep(1)
        research_data += researcher_agent(t) + "\n"

    # 3 Analysis
    steps.append({"stage": "analysis", "content": "Analyzing findings..."})
    summary = analyst_agent(question, research_data)

    # 4 Decision
    steps.append({"stage": "decision", "content": "Making final decision..."})
    verdict = decision_agent(question, summary)

    return steps, summary, verdict

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question")

    steps, summary, verdict = run_research_pipeline(question)

    return jsonify({
        "steps": steps,
        "summary": summary,
        "verdict": verdict
    })


if __name__ == "__main__":
    app.run(debug=True)