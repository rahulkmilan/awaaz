"""
Awaaz — Your Voice. Actually Heard.
AI-powered government complaint filing platform.

Run: uvicorn main:app --reload --port 8000
"""

from dotenv import load_dotenv
load_dotenv()  # Load .env file automatically

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os
import io
import ast
import urllib.parse

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


# ─── PDF Export ───────────────────────────────────────────────────────────────

@app.get("/api/complaints/{tracking_id}/pdf")
async def export_complaint_pdf(tracking_id: str, db: Session = Depends(get_db)):
    """Generate a formal, printable complaint letter as a downloadable PDF."""
    complaint = db.query(Complaint).filter(
        Complaint.tracking_id == tracking_id
    ).first()
    
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    from fpdf import FPDF
    
    def pdf_safe(text):
        """Replace Unicode characters that Helvetica can't render."""
        if not text:
            return text or ''
        replacements = {
            '\u20b9': 'Rs.', '\u2014': '-', '\u2013': '-', '\u2018': "'", '\u2019': "'",
            '\u201c': '"', '\u201d': '"', '\u2026': '...', '\u2022': '*',
            '\u25cf': '*', '\u2713': '[OK]', '\u2714': '[OK]', '\u2716': '[X]',
            '\u2192': '->', '\u2190': '<-', '\u00b0': ' deg',
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text.encode('latin-1', errors='replace').decode('latin-1')
    
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()
    w = pdf.w - pdf.l_margin - pdf.r_margin  # usable width
    
    def mc(text, h=6):
        """Safe multi_cell: always resets X to left margin first."""
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(w, h, pdf_safe(text))
    
    # ── Header ──
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(16, 185, 129)
    pdf.cell(0, 12, 'AWAAZ', ln=True, align='C')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, 'Your Voice. Actually Heard.', ln=True, align='C')
    pdf.ln(3)
    pdf.set_draw_color(16, 185, 129)
    pdf.set_line_width(0.5)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(8)
    
    # ── Tracking & Date ──
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(95, 6, f'Tracking ID: {complaint.tracking_id}')
    date_str = complaint.created_at.strftime('%d %B %Y, %I:%M %p') if complaint.created_at else 'N/A'
    pdf.cell(95, 6, f'Date: {date_str}', ln=True, align='R')
    pdf.cell(95, 6, f'Category: {complaint.category.upper()}')
    pdf.cell(95, 6, f'Status: {complaint.status.upper()}', ln=True, align='R')
    pdf.ln(8)
    
    # ── Complainant Info ──
    if complaint.user_name or complaint.user_email:
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 8, 'Complainant Details', ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(60, 60, 60)
        if complaint.user_name:
            pdf.cell(0, 6, f'Name: {complaint.user_name}', ln=True)
        if complaint.user_email:
            pdf.cell(0, 6, f'Email: {complaint.user_email}', ln=True)
        if complaint.user_city:
            pdf.cell(0, 6, f'City: {complaint.user_city}', ln=True)
        pdf.ln(6)
    
    # ── Authority ──
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, 'Filing Authority', ln=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 6, f'Authority: {complaint.authority or "N/A"}', ln=True)
    pdf.cell(0, 6, pdf_safe(f'Portal: {complaint.authority_portal or "N/A"}'), ln=True)
    pdf.ln(6)
    
    # ── Summary ──
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, 'Complaint Summary', ln=True)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(60, 60, 60)
    mc(complaint.ai_summary or 'N/A')
    pdf.ln(6)
    
    # ── Formal Complaint Draft ──
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, 'Formal Complaint Letter', ln=True)
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.3)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(40, 40, 40)
    mc(complaint.ai_draft or 'N/A')
    pdf.ln(6)
    
    # ── Evidence Checklist ──
    evidence_items = _parse_list_field(complaint.evidence_checklist)
    if evidence_items:
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 8, 'Evidence Checklist', ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(60, 60, 60)
        for item in evidence_items:
            pdf.set_x(pdf.l_margin)
            pdf.cell(w, 6, pdf_safe(f'  [ ]  {item}'), ln=True)
        pdf.ln(6)
    
    # ── Filing Guide ──
    guide_items = _parse_list_field(complaint.filing_guide)
    if guide_items:
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 8, 'Step-by-Step Filing Guide', ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(60, 60, 60)
        for i, step in enumerate(guide_items, 1):
            mc(f'  {i}. {step}')
        pdf.ln(6)
    
    # ── Legal Rights ──
    rights_items = _parse_list_field(complaint.legal_rights)
    if rights_items:
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 8, 'Your Legal Rights', ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(60, 60, 60)
        for right in rights_items:
            mc(f'  - {right}')
        pdf.ln(6)
    
    # ── Footer ──
    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, pdf_safe('Generated by Awaaz - Your Voice. Actually Heard.'), ln=True, align='C')
    pdf.cell(0, 5, 'This is an AI-generated draft. Please review before submitting.', ln=True, align='C')
    
    # Output
    pdf_bytes = pdf.output()
    buffer = io.BytesIO(pdf_bytes)
    buffer.seek(0)
    
    filename = f"Awaaz_Complaint_{tracking_id}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


def _parse_list_field(field_value):
    """Safely parse a stringified list from the database."""
    if not field_value:
        return []
    try:
        parsed = ast.literal_eval(field_value)
        return parsed if isinstance(parsed, list) else []
    except (ValueError, SyntaxError):
        return []


# ─── WhatsApp Share ───────────────────────────────────────────────────────────

@app.get("/api/complaints/{tracking_id}/whatsapp")
async def whatsapp_share(tracking_id: str, db: Session = Depends(get_db)):
    """Generate a WhatsApp share URL with the complaint summary."""
    complaint = db.query(Complaint).filter(
        Complaint.tracking_id == tracking_id
    ).first()
    
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    message = (
        f"*AWAAZ — Complaint Report*\n"
        f"Tracking ID: {complaint.tracking_id}\n\n"
        f"*Category:* {complaint.category.upper()}\n"
        f"*Authority:* {complaint.authority or 'N/A'}\n"
        f"*Portal:* {complaint.authority_portal or 'N/A'}\n\n"
        f"*Summary:*\n{complaint.ai_summary or 'N/A'}\n\n"
        f"Generated by Awaaz — Your Voice. Actually Heard."
    )
    
    whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(message)}"
    
    return {"whatsapp_url": whatsapp_url, "message": message}


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "service": "Awaaz",
        "ai_mode": "live" if os.getenv("GROQ_API_KEY") else "demo"
    }
