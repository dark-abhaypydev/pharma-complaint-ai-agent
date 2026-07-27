"""
AIVOA - AI Powered Customer Complaint Management System
Backend: FastAPI + LangGraph + Groq
"""

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional
import io
from pypdf import PdfReader
from docx import Document
from datetime import datetime

from database import init_db, get_db, Complaint
from agent import run_complaint_agent

app = FastAPI(
    title="AIVOA Complaint Management API",
    description="AI-powered Customer Complaint Intake for Pharmaceutical QMS",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Pydantic Schemas ----------
class ComplaintCreate(BaseModel):
    customer_name: Optional[str] = None
    complaint_source: Optional[str] = None
    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    batch_lot_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    quantity_affected: Optional[str] = None
    complaint_type: Optional[str] = None
    complaint_date: Optional[str] = None
    detailed_description: Optional[str] = None
    initial_severity: Optional[str] = None
    priority: Optional[str] = None
    risk_classification: Optional[str] = None
    ai_summary: Optional[str] = None
    capa_recommendation: Optional[str] = None
    completeness_score: Optional[float] = None
    root_cause: Optional[str] = None


class ExtractResponse(BaseModel):
    extracted: dict
    risk_classification: str
    ai_summary: str
    capa_recommendation: str
    completeness_score: float
    completeness_feedback: str
    root_cause: str
    error: Optional[str] = None


# ---------- Helpers ----------
def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    filename = filename.lower()
    if filename.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n".join(pages)
    elif filename.endswith(".docx"):
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    elif filename.endswith(".txt") or filename.endswith(".eml"):
        return file_bytes.decode("utf-8", errors="ignore")
    else:
        # try as text
        try:
            return file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, DOCX, TXT or EML.")


# ---------- Startup ----------
@app.on_event("startup")
async def startup():
    await init_db()


# ---------- Routes ----------
@app.get("/")
async def root():
    return {
        "message": "AIVOA Customer Complaint Management API",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/extract", response_model=ExtractResponse)
async def extract_complaint(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
):
    """
    Main AI Intake endpoint.
    Accepts either a file (PDF/DOCX/TXT) or plain text.
    Runs full LangGraph pipeline: Extract → Risk → Summary → CAPA → Completeness → Root Cause
    """
    raw_text = ""

    if file and file.filename:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10 MB limit
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        raw_text = extract_text_from_file(content, file.filename)
    elif text and text.strip():
        raw_text = text.strip()
    else:
        raise HTTPException(status_code=400, detail="Provide either a file or text content")

    if not raw_text or len(raw_text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Extracted text is too short or empty")

    # Run LangGraph agent
    result = await run_complaint_agent(raw_text)

    return ExtractResponse(
        extracted=result.get("extracted", {}),
        risk_classification=result.get("risk_classification", "Major"),
        ai_summary=result.get("ai_summary", ""),
        capa_recommendation=result.get("capa_recommendation", ""),
        completeness_score=result.get("completeness_score", 0.0),
        completeness_feedback=result.get("completeness_feedback", ""),
        root_cause=result.get("root_cause", ""),
        error=result.get("error"),
    )


@app.post("/api/complaints")
async def save_complaint(payload: ComplaintCreate, db: AsyncSession = Depends(get_db)):
    """Save a fully filled complaint into the database."""
    complaint = Complaint(
        customer_name=payload.customer_name,
        complaint_source=payload.complaint_source,
        product_name=payload.product_name,
        product_strength=payload.product_strength,
        batch_lot_number=payload.batch_lot_number,
        manufacturing_date=payload.manufacturing_date,
        expiry_date=payload.expiry_date,
        quantity_affected=payload.quantity_affected,
        complaint_type=payload.complaint_type,
        complaint_date=payload.complaint_date,
        detailed_description=payload.detailed_description,
        initial_severity=payload.initial_severity,
        priority=payload.priority,
        risk_classification=payload.risk_classification,
        ai_summary=payload.ai_summary,
        capa_recommendation=payload.capa_recommendation,
        completeness_score=payload.completeness_score,
        root_cause=payload.root_cause,
    )
    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)
    return {"id": complaint.id, "message": "Complaint saved successfully"}


@app.get("/api/complaints")
async def list_complaints(db: AsyncSession = Depends(get_db)):
    """List all saved complaints (latest first)."""
    result = await db.execute(select(Complaint).order_by(Complaint.created_at.desc()).limit(50))
    complaints = result.scalars().all()
    return [
        {
            "id": c.id,
            "customer_name": c.customer_name,
            "product_name": c.product_name,
            "batch_lot_number": c.batch_lot_number,
            "complaint_type": c.complaint_type,
            "risk_classification": c.risk_classification,
            "priority": c.priority,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in complaints
    ]


@app.get("/api/complaints/{complaint_id}")
async def get_complaint(complaint_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Complaint).where(Complaint.id == complaint_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {
        "id": c.id,
        "customer_name": c.customer_name,
        "complaint_source": c.complaint_source,
        "product_name": c.product_name,
        "product_strength": c.product_strength,
        "batch_lot_number": c.batch_lot_number,
        "manufacturing_date": c.manufacturing_date,
        "expiry_date": c.expiry_date,
        "quantity_affected": c.quantity_affected,
        "complaint_type": c.complaint_type,
        "complaint_date": c.complaint_date,
        "detailed_description": c.detailed_description,
        "initial_severity": c.initial_severity,
        "priority": c.priority,
        "risk_classification": c.risk_classification,
        "ai_summary": c.ai_summary,
        "capa_recommendation": c.capa_recommendation,
        "completeness_score": c.completeness_score,
        "root_cause": c.root_cause,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
