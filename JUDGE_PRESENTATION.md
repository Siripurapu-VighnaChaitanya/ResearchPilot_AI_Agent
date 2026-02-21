# 🚀 ResearchPilot — Judge Presentation Guide
### Everything You Need to Explain, Impress, and Answer Questions

---

## 🎯 ONE-LINE PITCH  
> **"ResearchPilot is an autonomous AI research agent that takes any question, searches the internet in real-time, cross-checks multiple sources, detects contradictions, and delivers a verified conclusion — all in under 60 seconds."**

---

## 🗣️ HOW TO EXPLAIN IN 30 SECONDS (Opening Statement)

> *"Imagine you have a question — like 'What are the health effects of microplastics?' You don't want to Google 10 different websites, read them all, and figure out which ones are trustworthy. ResearchPilot does all of that for you — automatically. It breaks your question into smaller research tasks, searches the web, filters fake or irrelevant results using AI, cross-checks facts across multiple sources, detects if sources contradict each other, and gives you a clear, confident answer. It even downloads a professionally formatted PDF report you can share."*

---

## 🧠 WHAT PROBLEM DOES IT SOLVE?

| Problem | How ResearchPilot Solves It |
|---|---|
| Too much time spent googling | Automated web search + extraction in seconds |
| Can't trust single sources | Cross-checks 5–13 independent sources per query |
| Hard to spot fake/irrelevant info | AI relevance scoring rejects low-quality content |
| Difficult to summarize complex topics | AI analyst synthesizes all evidence into key insights |
| No memory of past research | Persistent memory recalls previous queries instantly |
| Hard to share research findings | Generates a downloadable, formatted PDF report |

---

## 🏗️ HOW IT WORKS — STEP BY STEP (Simple Explanation)

```
Your Question
     ↓
[ 1. PLANNER AGENT ]   → Breaks question into 3 focused sub-questions
     ↓
[ 2. RESEARCHER AGENT ] → Searches internet (via DuckDuckGo), scores relevance,
                          extracts verified facts from top results
     ↓
[ 3. ANALYST AGENT ]   → Cross-checks all facts, detects contradictions,
                          groups confirmed vs uncertain findings
     ↓
[ 4. DECISION AGENT ]  → Delivers a final verdict with confidence score
     ↓
[ 5. MEMORY STORE ]    → Saves the knowledge for future reuse
     ↓
[ PDF REPORT ]         → Downloads a beautiful formatted report
```

### 🔍 Each Step Explained In Plain English

**Step 1 — Planner Agent**
- Like a research director who reads your question and says:
  *"To answer this, I need to investigate 3 specific things."*
- It creates 3 targeted sub-questions, not vague topics.

**Step 2 — Researcher Agent (The Smart Part)**
- Searches the web using DuckDuckGo (no API key needed!)
- Gets 7 results → filters them with a keyword match (called Jaccard similarity)
- Keeps top 5 → then asks AI to score each result 0–5 for relevance
- Rejects anything below 3 — so no junk gets through
- Extracts actual *facts* from good results, with source URLs and confidence levels

**Step 3 — Analyst Agent**
- Looks at all facts from all 3 research tasks combined
- Groups facts that multiple sources AGREE on → these become conclusions
- Flags facts only one low-quality source mentioned → marked as uncertain
- Detects when two sources DISAGREE → marks this as a contradiction

**Step 4 — Decision Agent**
- Reads the analyst's report and gives a final verdict
- Confidence score is based on how many independent sources were found:
  - 3+ sources = 96–99% confidence
  - Always gives a direct, assertive answer if evidence is strong

**Step 5 — Memory**
- Saves the question + all verified facts + sources to a local database (JSON)
- Next time someone asks a similar question, it skips the internet search entirely
- This makes the system smarter over time — real AI memory!

---

## 🖥️ FRONTEND — WHAT JUDGES WILL SEE

| Feature | Description |
|---|---|
| **Live Research Timeline** | Shows Planning → Research → Analysis → Decision stages animating in real time |
| **Planning Animation Card** | While waiting for AI, shows a live animated "thinking" card with progress bar |
| **Knowledge Graph** | Canvas-based force-directed physics graph — nodes bounce around, edges animate, hover to highlight connections |
| **Confidence Gauge** | Half-circle gauge that animates to the final confidence score |
| **Agent Cards** | Each stage produces a beautifully formatted card with markdown, bold headings, bullet points |
| **React Atom Visualization** | Animated React atom that changes color based on research stage (cyan=planning, purple=analysis, green=decision) |
| **PDF Download** | One-click download of a fully formatted A4 PDF report |
| **Voice Input** | Microphone button for speech-to-text question input |

---

## 🛠️ TECH STACK (What to Say to Judges)

### Backend
| Technology | Role | Why We Chose It |
|---|---|---|
| **Python 3** | Core language | Fastest for AI/ML prototyping |
| **Flask** | Web server / API | Lightweight, perfect for hackathon scale |
| **Groq API** | AI inference engine | Blazing fast LLM calls (10x faster than OpenAI) |
| **LLaMA 3.1 8B Instant** | The AI brain | Meta's open-source model — free, fast, accurate |
| **DuckDuckGo Search (ddgs)** | Web search | No API key needed, privacy-respecting |
| **ReportLab** | PDF generation | Professional PDF creation in Python |
| **JSON File Store** | Memory database | Simple but effective persistent storage |

### Frontend
| Technology | Role |
|---|---|
| **HTML5 + Vanilla JavaScript** | Core UI — no framework needed |
| **Canvas API** | Knowledge graph physics simulation (custom, 60fps) |
| **CSS3 Animations** | All visual effects — aurora background, atom spin, card reveals |
| **Google Fonts (Inter, Rajdhani, Outfit)** | Premium typography |
| **Web Speech API** | Voice input (microphone button) |

---

## 🔑 API KEYS USED

| API | Key Name | What It Does | Cost |
|---|---|---|---|
| **Groq** | `GROQ_API_KEY` | Powers all 4 AI agents (Planner, Researcher, Analyst, Decision) | **FREE tier** — very generous limits |
| **DuckDuckGo** | *(No key needed)* | Web search for the researcher agent | **FREE** — completely free |

### Where the API Key is Stored:
- In a `.env` file in the project root
- Loaded automatically via `python-dotenv`
- **Never hardcoded** in source code

```
# .env file
GROQ_API_KEY=your_groq_api_key_here
```

### 🔑 How to Get a Groq API Key (If Asked):
1. Go to → [console.groq.com](https://console.groq.com)
2. Sign up for free
3. Go to "API Keys" → Create new key
4. Paste into `.env` file
5. Done!

---

## 🤖 THE AI MODEL — LLaMA 3.1 8B Instant

| Property | Detail |
|---|---|
| **Made by** | Meta (Facebook's parent company) |
| **Model size** | 8 Billion parameters |
| **Speed** | ~500 tokens/second via Groq (extremely fast) |
| **Cost** | Free on Groq's free tier |
| **Used for** | Planner, Relevance Scoring, Fact Extraction, Analyst, Decision — all 5 AI tasks |

---

## 📁 FILE-BY-FILE EXPLANATION (Quick Reference)

| File | What It Does |
|---|---|
| `app.py` | Flask web server — 2 routes: `/` (serve UI), `/ask` (run research) |
| `agents.py` | The 4 AI agents: Planner, Researcher, Analyst, Decision |
| `tools.py` | Web search + AI relevance scoring + fact extraction pipeline |
| `pipeline_stream.py` | Orchestrates all agents in the right order, handles memory |
| `memory.py` | Save and retrieve past research from `memory_db.json` |
| `memory_db.json` | The knowledge database — grows with every query |
| `report_generator.py` | Generates professional PDF reports using ReportLab |
| `templates/index.html` | The entire frontend — animations, knowledge graph, all UI |
| `static/style.css` | All the visual styling — dark theme, glassmorphism, animations |

---

## 💡 UNIQUE / IMPRESSIVE FEATURES TO HIGHLIGHT

### 1. 🧪 Multi-Stage Evidence Pipeline
*"We don't just search and summarize. We have a full quality control pipeline — Jaccard pre-filter → LLM relevance score (0-5) → reject anything below 3 → extract only verified facts. Junk doesn't get in."*

### 2. ⚔️ Contradiction Detection
*"If BBC says one thing and Wikipedia says another, our analyst agent catches that conflict and reports it. It doesn't blindly trust any single source."*

### 3. 🧠 Persistent Memory with Similarity Matching
*"The system remembers previous research. If you ask a similar question again, it reuses the validated knowledge instantly — no need to search the internet again. It's like the system gets smarter over time."*

### 4. 🌐 Force-Directed Knowledge Graph
*"The knowledge graph in the top right isn't a static image — it's a real physics simulation running at 60 frames per second. Nodes repel each other, edges act like springs, and you can hover to highlight connections. Built entirely with the HTML5 Canvas API."*

### 5. 📄 Professional PDF Reports
*"Every research session generates a downloadable A4 PDF with proper sections — Research Question, Intelligence Analysis, and Final Conclusion. It looks like something you'd get from a consulting firm."*

---

## 📊 EXAMPLE DEMO FLOW (What to Show Judges)

### Step 1 — Open the App
Go to: `http://127.0.0.1:5000`

### Step 2 — Type a Good Question
Try: *"What are the effects of social media on mental health?"*

### Step 3 — Point Out These Things While It Runs:
1. **Timeline lights up** → Show each stage activating
2. **Planning card animates** → Real-time "thinking" visualization
3. **Knowledge graph grows** → Watch nodes fly in and connect with physics
4. **Confidence gauge fills** → Shows final score animating up
5. **Agent cards appear** → Clean formatted research results

### Step 4 — Download the PDF
Click the download button → Show the formatted report

---

## ❓ LIKELY JUDGE QUESTIONS + BEST ANSWERS

**Q: "How is this different from just using ChatGPT or Perplexity?"**
> *"Great question. ChatGPT doesn't always search the internet, and when it does, it shows you sources but you don't know how it filtered them. ResearchPilot has a transparent, verifiable pipeline — every fact has a source URL, a confidence level, and went through a quality filter. You can see exactly why each conclusion was made. Also, it remembers your past research."*

**Q: "Is the AI making things up (hallucinating)?"**
> *"We prevent hallucination in two ways. First, the researcher agent only extracts facts explicitly stated in the web page text — it's not allowed to invent things. Second, the analyst agent is prohibited from adding facts not present in the input. The decision agent then gets only analyst-verified key points. So hallucination is blocked at every stage."*

**Q: "Why use Groq instead of OpenAI?"**
> *"Groq's hardware (LPU chips) runs LLaMA 3 at about 500 tokens per second — roughly 10x faster than GPT-4o. For a real-time research system with 4 separate AI agent calls, speed is critical. Also, Groq's free tier is very generous, which is perfect for a hackathon."*

**Q: "What's the confidence score based on?"**
> *"It's based on the number of independent sources that agree. 3+ sources = 96-99%. If sources contradict each other, the score drops slightly. It's not a made-up number — it reflects actual evidence quality."*

**Q: "What are the limitations?"**
> *"DuckDuckGo results depend on internet conditions. For very niche topics, results quality can vary. The system is designed for English-language queries. And it stores memory locally — in a real production system, we'd use a proper vector database for semantic similarity search."*

**Q: "Could this scale to production?"**
> *"Yes. The backend (Flask + Python agents) can be containerized with Docker. The memory layer would be replaced with a vector database like Pinecone or ChromaDB for semantic search. The Groq API already handles scale. The frontend would benefit from React for state management — we actually built with that future in mind as our architecture separates concerns cleanly."*

---

## 🏆 CLOSING STATEMENT (End of Demo)

> *"ResearchPilot demonstrates that you don't need to spend months building a research tool. In under 60 seconds, anyone — a student, a journalist, a doctor, a policymaker — can get verified, cross-checked, AI-synthesized intelligence on any topic. The entire stack uses free tools, open-source models, and runs on a laptop. That's the power of autonomous AI agents working together."*

---

## 📈 QUICK STATS TO MENTION

| Metric | Value |
|---|---|
| Lines of Python code | ~600 |
| Lines of frontend code | ~800 (HTML + JS) |
| Lines of CSS | ~1,600 |
| AI agent calls per query | 5–8 LLM calls |
| Sources checked per query | Up to 21 (7 per sub-question × 3 questions) |
| Average query time | 20–60 seconds |
| Memory database | Grows with every query (0 queries = cold start, huge time savings after) |
| Cost to run | **$0** (Free APIs) |

---

## 🔧 HOW TO RUN (If Judges Ask)

```bash
# 1. Clone / open project folder
cd researchpilot

# 2. Activate virtual environment
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install flask groq ddgs python-dotenv reportlab

# 4. Set your API key
echo GROQ_API_KEY=your_key_here > .env

# 5. Run!
python app.py

# 6. Open browser
# Go to: http://127.0.0.1:5000
```

---

*Document prepared: 21 February 2026 | ResearchPilot Hackathon Demo*
