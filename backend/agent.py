"""
LangGraph based AI Agent for Customer Complaint Intake.
Nodes:
  1. extract   -> Extract structured fields from raw text
  2. risk      -> AI Risk Classification
  3. summary   -> Complaint Summary
  4. capa      -> CAPA Recommendation
  5. completeness -> Completeness Checker
  6. root_cause -> Root Cause Recommendation
"""

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import json
import os
from dotenv import load_dotenv

load_dotenv()

# ---------------- State ----------------
class ComplaintState(TypedDict):
    raw_text: str
    extracted: dict
    risk_classification: str
    ai_summary: str
    capa_recommendation: str
    completeness_score: float
    completeness_feedback: str
    root_cause: str
    error: str | None


# ---------------- LLM ----------------
def get_llm(model: str = "llama-3.1-8b-instant"):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment")
    return ChatGroq(
        model=model,
        api_key=api_key,
        temperature=0.1,
        max_tokens=2048,
    )


# ---------------- Helper ----------------
def safe_json_parse(text: str) -> dict:
    """Extract JSON from LLM response even if it has extra text."""
    text = text.strip()
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Find first { ... }
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return {}


# ---------------- Nodes ----------------
def extract_node(state: ComplaintState) -> dict:
    """Extract structured complaint fields from raw text."""
    llm = get_llm("llama-3.1-8b-instant")

    system_prompt = """You are an expert pharmaceutical Quality Management System (QMS) assistant.
Your job is to extract structured information from customer complaint documents (emails, PDFs, text).

Return ONLY a valid JSON object with these exact keys (use null if not found):
{
  "customer_name": "string or null",
  "complaint_source": "string or null (Email / Phone / Letter / Portal etc.)",
  "product_name": "string or null",
  "product_strength": "string or null (e.g. 500mg, 10mg/ml)",
  "batch_lot_number": "string or null",
  "manufacturing_date": "string or null (YYYY-MM-DD or as written)",
  "expiry_date": "string or null",
  "quantity_affected": "string or null",
  "complaint_type": "string or null (Quality / Packaging / Efficacy / Adverse Event / Other)",
  "complaint_date": "string or null",
  "detailed_description": "string or null (full complaint narrative)",
  "initial_severity": "string or null (Critical / Major / Minor)",
  "priority": "string or null (High / Medium / Low)"
}

Rules:
- Be accurate. Do not invent data.
- If a field is missing, put null.
- detailed_description should capture the core complaint story.
- Return pure JSON only, no markdown, no explanation.
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Complaint document content:\n\n{state['raw_text'][:8000]}")
    ]

    try:
        response = llm.invoke(messages)
        data = safe_json_parse(response.content)
        return {"extracted": data, "error": None}
    except Exception as e:
        return {"extracted": {}, "error": f"Extraction failed: {str(e)}"}


def risk_node(state: ComplaintState) -> dict:
    """Classify risk level for the complaint."""
    llm = get_llm("llama-3.1-8b-instant")
    extracted = state.get("extracted", {})

    prompt = f"""You are a pharmaceutical QMS risk assessor.
Based on the extracted complaint data below, classify the overall RISK.

Extracted Data:
{json.dumps(extracted, indent=2)}

Return ONLY a JSON object:
{{
  "risk_classification": "Critical | Major | Minor",
  "justification": "one short sentence"
}}

Guidelines:
- Critical: Patient safety risk, sterility failure, wrong drug, severe adverse event
- Major: Significant quality issue, labeling error, potency problem
- Minor: Cosmetic, packaging appearance, minor documentation issues
"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        data = safe_json_parse(response.content)
        risk = data.get("risk_classification", "Major")
        return {"risk_classification": risk}
    except Exception as e:
        return {"risk_classification": "Major", "error": str(e)}

def summary_node(state: ComplaintState) -> dict:
    """Generate a short professional summary."""
    llm = get_llm("llama-3.1-8b-instant")
    extracted = state.get("extracted", {})

    prompt = f"""Summarize this pharmaceutical customer complaint in 2-3 professional sentences for a QMS record.

Data:
{json.dumps(extracted, indent=2)}

Return ONLY the summary text, no JSON, no prefix.
"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return {"ai_summary": response.content.strip()}
    except Exception as e:
        print(f"SUMMARY ERROR: {e}")   # yeh terminal mein dikhega
        return {"ai_summary": f"Summary failed: {str(e)}"}

def capa_node(state: ComplaintState) -> dict:
    llm = get_llm("llama-3.1-8b-instant")
    extracted = state.get("extracted", {})
    risk = state.get("risk_classification", "Major")

    prompt = f"""You are a pharmaceutical CAPA expert.
Suggest practical Corrective and Preventive Actions for this complaint.

Complaint Data:
{json.dumps(extracted, indent=2)}
Risk Level: {risk}

Return a short structured recommendation (3-5 bullet points).
Keep it realistic. Return plain text only.
"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return {"capa_recommendation": response.content.strip()}
    except Exception as e:
        print(f"CAPA ERROR: {e}")
        return {"capa_recommendation": f"CAPA failed: {str(e)}"}


def completeness_node(state: ComplaintState) -> dict:
    """Check how complete the extracted complaint is."""
    extracted = state.get("extracted", {})
    required = [
        "customer_name", "product_name", "batch_lot_number",
        "detailed_description", "complaint_type", "complaint_date"
    ]
    present = sum(1 for k in required if extracted.get(k))
    score = round((present / len(required)) * 100, 1)

    missing = [k for k in required if not extracted.get(k)]
    feedback = "All key fields present." if not missing else f"Missing: {', '.join(missing)}"

    return {
        "completeness_score": score,
        "completeness_feedback": feedback
    }


def root_cause_node(state: ComplaintState) -> dict:
    llm = get_llm("llama-3.1-8b-instant")
    extracted = state.get("extracted", {})

    prompt = f"""Based on this pharmaceutical complaint, list 2-3 most likely root causes.

Data:
{json.dumps(extracted, indent=2)}

Return a short bullet list only.
"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return {"root_cause": response.content.strip()}
    except Exception as e:
        print(f"ROOT CAUSE ERROR: {e}")
        return {"root_cause": f"Root cause failed: {str(e)}"}

# ---------------- Graph ----------------
def build_graph():
    workflow = StateGraph(ComplaintState)

    workflow.add_node("extract", extract_node)
    workflow.add_node("risk", risk_node)
    workflow.add_node("summary", summary_node)
    workflow.add_node("capa", capa_node)
    workflow.add_node("completeness", completeness_node)
    workflow.add_node("root_cause", root_cause_node)

    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "risk")
    workflow.add_edge("risk", "summary")
    workflow.add_edge("summary", "capa")
    workflow.add_edge("capa", "completeness")
    workflow.add_edge("completeness", "root_cause")
    workflow.add_edge("root_cause", END)

    return workflow.compile()


# Compiled graph (lazy)
_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


async def run_complaint_agent(raw_text: str) -> dict:
    """Main entry point used by FastAPI."""
    graph = get_graph()
    initial_state: ComplaintState = {
        "raw_text": raw_text,
        "extracted": {},
        "risk_classification": "",
        "ai_summary": "",
        "capa_recommendation": "",
        "completeness_score": 0.0,
        "completeness_feedback": "",
        "root_cause": "",
        "error": None,
    }
    result = await graph.ainvoke(initial_state)
    return result
