# ⚖️ AI-Powered Multi-Agent Legal Contract Assistant

An **AI-driven legal contract analysis system** that uses **multi-agent orchestration** and **Retrieval-Augmented Generation (RAG)** to parse, analyze, and summarize contracts automatically.  

This project is designed to **help legal professionals, startups, and businesses** quickly extract insights, identify risks, and understand contracts without reading every clause manually.  

---

## 🚀 Features
- **Multi-Agent Orchestration**: Specialized agents for parsing, retrieval, analysis, summarization, and compliance checks.  
- **RAG-Powered Q&A**: Retrieve relevant clauses and provide accurate, context-aware answers.  
- **Automated Clause Extraction**: Identify parties, obligations, dates, penalties, and compliance issues.  
- **Risk Assessment**: Highlight potential red flags in contracts.  
- **Actionable Insights**: Generate a structured JSON report with strengths, risks, and recommendations.  
- **Web Interface**: Upload contracts and view results through an interactive React frontend.  

---

## 🛠 Tech Stack
- **Backend**: Python, Flask (REST API)  
- **Frontend**: React.js  
- **AI Frameworks**: LangChain, LangGraph  
- **Vector Database**: ChromaDB  
- **LLM Integration**: Gemini / OpenAI (configurable)  
- **Other Tools**: Docker, Git, Pandas  

---

## 🧩 Multi-Agent Architecture
- **📄 Document Parser Agent**: Extracts raw text and segments clauses.  
- **🔍 Retrieval Agent**: Uses ChromaDB to fetch relevant chunks for queries.  
- **⚖️ Analysis Agent**: Evaluates contract terms, obligations, and risks.  
- **🧾 Summarizer Agent**: Generates human-readable summaries + JSON reports.  
- **❓ Q&A Agent**: Answers user-specific legal questions.  
- **📑 Compliance Agent**: Flags missing or risky clauses against predefined standards.  

---

## 📊 Workflow
1. User uploads a contract via the **React frontend**.  
2. **Flask backend** receives file → runs preprocessing → sends data to LangChain.  
3. Text is chunked, embedded, and stored in **ChromaDB**.  
4. **Orchestrator** assigns tasks to agents (parser, retriever, analyzer, summarizer).  
5. Results are combined into:  
   - A **summary report**  
   - **Red-flag highlights**  
   - A **structured JSON output**  
6. Frontend displays results with **highlighted clauses and explanations**.  

---

## ⚙️ Installation & Setup
Clone the repository:
```bash
git clone https://github.com/ADI-KRISH/Legal-Document-Reviewer-and-Analysis-Platform.git
cd Legal-Document-Reviewer-and-Analysis-Platform
