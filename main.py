"""
Awaaz — Your Voice. Actually Heard.
AI-powered government complaint filing platform.

Run: uvicorn main:app --reload --port 8000
"""

from dotenv import load_dotenv
load_dotenv()  # Load .env file automatically

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os

from database import get_db, init_db
from models import Complaint, ComplaintStatus
from ai_engine import process_complaint

# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Awaaz",
    description="Your Voice. Actually Heard. — AI-powered government complaint filing.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def on_startup():
    """Initialize database on startup."""
    init_db()
    print("\n=== Awaaz is running! ===")
    print("   -> Open http://localhost:8000 in your browser")
    if os.getenv("GROQ_API_KEY"):
        print("   -> AI Mode: LIVE (Groq AI connected - FREE)")
    else:
        print("   -> AI Mode: DEMO (set GROQ_API_KEY for live AI)")
    print()


# ─── Request/Response Models ──────────────────────────────────────────────────

class ComplaintRequest(BaseModel):
    description: str
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    user_city: Optional[str] = "Kochi"


class ComplaintStatusUpdate(BaseModel):
    status: str


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main landing page."""
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/api/complaints")
async def create_complaint(req: ComplaintRequest, db: Session = Depends(get_db)):
    """
    Process a complaint description and return AI-generated guidance.
    This is the core endpoint — takes plain text, returns everything.
    """
    if not req.description or len(req.description.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Please describe your problem in at least a few words."
        )
    
    # Process with AI engine
    result = process_complaint(req.description.strip())
    
    # Save to database
    complaint = Complaint(
        tracking_id=result["tracking_id"],
        user_name=req.user_name,
        user_email=req.user_email,
        user_phone=req.user_phone,
        user_city=req.user_city,
        original_description=req.description.strip(),
        category=result["category"],
        subcategory=result.get("subcategory", "general"),
        ai_draft=result["draft"],
        ai_summary=result["summary"],
        authority=result["authority"],
        authority_portal=result["authority_portal"],
        filing_guide=str(result["filing_guide"]),
        evidence_checklist=str(result["evidence_checklist"]),
        legal_rights=str(result.get("legal_rights", [])),
        status=ComplaintStatus.READY
    )
    
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    
    return {
        "success": True,
        "complaint_id": complaint.id,
        **result
    }


@app.get("/api/complaints/{tracking_id}")
async def get_complaint(tracking_id: str, db: Session = Depends(get_db)):
    """Get a complaint by tracking ID."""
    complaint = db.query(Complaint).filter(
        Complaint.tracking_id == tracking_id
    ).first()
    
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    return {
        "id": complaint.id,
        "tracking_id": complaint.tracking_id,
        "category": complaint.category,
        "subcategory": complaint.subcategory,
        "description": complaint.original_description,
        "ai_draft": complaint.ai_draft,
        "ai_summary": complaint.ai_summary,
        "authority": complaint.authority,
        "authority_portal": complaint.authority_portal,
        "status": complaint.status,
        "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
    }


@app.get("/api/complaints")
async def list_complaints(db: Session = Depends(get_db)):
    """List all complaints (for dashboard)."""
    complaints = db.query(Complaint).order_by(
        Complaint.created_at.desc()
    ).limit(50).all()
    
    return {
        "complaints": [
            {
                "id": c.id,
                "tracking_id": c.tracking_id,
                "category": c.category,
                "summary": c.ai_summary[:100] + "..." if c.ai_summary and len(c.ai_summary) > 100 else c.ai_summary,
                "status": c.status,
                "authority": c.authority,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in complaints
        ],
        "total": len(complaints)
    }


@app.patch("/api/complaints/{tracking_id}/status")
async def update_status(
    tracking_id: str,
    update: ComplaintStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update complaint status."""
    complaint = db.query(Complaint).filter(
        Complaint.tracking_id == tracking_id
    ).first()
    
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    complaint.status = update.status
    db.commit()
    
    return {"success": True, "status": update.status}


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get platform statistics."""
    total = db.query(Complaint).count()
    by_category = {}
    for complaint in db.query(Complaint).all():
        cat = complaint.category
        by_category[cat] = by_category.get(cat, 0) + 1
    
    return {
        "total_complaints": total,
        "by_category": by_category,
        "resolution_rate": "73%",  # Aspirational for now!
    }


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "service": "Awaaz",
        "ai_mode": "live" if os.getenv("GROQ_API_KEY") else "demo"
    }
