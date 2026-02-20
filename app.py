from flask import Flask,request,jsonify,render_template
from pipeline_stream import run_research_pipeline_stream
from report_generator import generate_pdf
from flask import send_file
app=Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():

    data = request.json
    question = data.get("question")

    steps = []
    for step in run_research_pipeline_stream(question):
        steps.append(step)

    summary = steps[-2]["content"]
    verdict = steps[-1]["content"]

    # generate pdf
    pdf_path = generate_pdf(question, summary, verdict)

    return jsonify({
        "steps": steps[:-2],
        "summary": summary,
        "verdict": verdict,
        "pdf": pdf_path
    })

@app.route('/reports/<path:filename>')
def download_report(filename):
    return send_file(f"reports/{filename}", as_attachment=True)

if __name__=="__main__":
    app.run(debug=True)