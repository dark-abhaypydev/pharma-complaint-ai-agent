# AIVOA – AI-Powered Customer Complaint Management System

**Round 1 Assignment – AI Product Engineer (Intern)**

AI-powered Customer Complaint Intake module for Pharmaceutical Quality Management System (QMS) – API & FDF manufacturing.

## Features

### Core
- **AI Complaint Intake Assistant** – Upload PDF / DOCX / TXT / Email or paste text
- **LangGraph multi-node agent**:
  1. Field Extraction (structured JSON)
  2. AI Risk Classification (Critical / Major / Minor)
  3. Complaint Summary
  4. CAPA Recommendation
  5. Completeness Checker
  6. Root Cause Suggestions
- Auto-fill of Log Customer Complaint form
- Save complaints to database

### Tech Stack (Mandatory)
| Layer     | Technology                  |
|-----------|-----------------------------|
| Frontend  | React 18 + Redux Toolkit    |
| Backend   | Python FastAPI              |
| AI Agent  | LangGraph                   |
| LLM       | Groq (`gemma2-9b-it`)       |
| Database  | SQLite (easy) / Postgres    |
| Font      | Google Inter                |

## Project Structure

```
aivoa-complaint-system/
├── backend/
│   ├── main.py          # FastAPI app + endpoints
│   ├── agent.py         # LangGraph workflow (6 nodes)
│   ├── database.py      # SQLAlchemy models
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── App.jsx      # Main UI (form + AI panel)
│   │   ├── store/       # Redux
│   │   └── services/    # API calls
│   ├── package.json
│   └── vite.config.js
├── samples/
│   └── sample_complaint.txt
└── README.md
```

## Setup & Run

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env
cp .env.example .env
# Edit .env and put your Groq API key:
# GROQ_API_KEY=gsk_xxxxxxxx

uvicorn main:app --reload --port 8000
```

Get free Groq key: https://console.groq.com

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### 3. Test with sample

- Open the app
- Click “or click to browse” and select `samples/sample_complaint.txt`
- Or paste the content of the sample file
- Watch AI extract fields + risk + CAPA etc.

## API Endpoints

| Method | Endpoint              | Description                     |
|--------|-----------------------|---------------------------------|
| POST   | /api/extract          | File or text → full AI pipeline |
| POST   | /api/complaints       | Save complaint                  |
| GET    | /api/complaints       | List complaints                 |
| GET    | /api/complaints/{id}  | Get one complaint               |
| GET    | /docs                 | Swagger UI                      |

## LangGraph Workflow

```
User Input (PDF/Text)
        ↓
   [extract]  → structured fields (JSON)
        ↓
   [risk]     → Critical / Major / Minor
        ↓
   [summary]  → 2-3 sentence summary
        ↓
   [capa]     → CAPA recommendations
        ↓
   [completeness] → score + missing fields
        ↓
   [root_cause] → possible root causes
        ↓
   Response → Frontend form + AI Insights panel
```

## Demo Video Script (for submission)

**Video 1 – Working Demo (3-5 min)**
1. Open app
2. Upload sample_complaint.txt / paste text
3. Show progress + auto-fill of form
4. Show AI Insights (Risk, Summary, CAPA, Completeness, Root Cause)
5. Edit any field manually
6. Save Complaint → success

**Video 2 – Code Walkthrough (5-7 min)**
1. Frontend: App.jsx → Redux store → api.js call
2. Backend: main.py `/api/extract` endpoint
3. agent.py → StateGraph nodes & edges
4. How extracted JSON populates the form
5. How Risk + CAPA appear in AI panel

## Notes for Interview

- UI was generated with AI assistance; core logic (LangGraph agent, prompts, FastAPI, Redux flow) was understood and adapted.
- Production OCR not implemented (as allowed).
- SQLite used for zero-config; switch to Postgres by changing `DATABASE_URL`.

## Author

Built for AIVOA Round 1 – AI Product Engineer Internship.
```
## Author

Abhay Singh
GitHub: https://github.com/dark-abhaypydev
Built for AIVOA Round 1 – AI Product Engineer Internship.
