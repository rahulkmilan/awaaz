"""
AI Engine for Awaaz — Complaint Categorization, Drafting & Guidance.

Includes a DEMO mode that works without an API key (for testing/demos),
and a LIVE mode that uses Groq (FREE, blazing fast, no credit card needed).

Set GROQ_API_KEY env variable to enable live mode.
Get your free key at: https://console.groq.com/keys
"""

import os
import json
import random
import string
from datetime import datetime

# Try to import Groq — free tier, 14,400 requests/day
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


def generate_tracking_id():
    """Generate a unique tracking ID like AWZ-2026-XXXX."""
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choices(chars, k=6))
    return f"AWZ-{datetime.now().year}-{suffix}"


# ─── Authority Database ──────────────────────────────────────────────────────

AUTHORITIES = {
    "cybercrime": {
        "name": "National Cyber Crime Reporting Portal",
        "portal": "https://cybercrime.gov.in",
        "helpline": "1930",
        "email": "cybercrime@nic.in",
        "filing_guide": [
            "Go to https://cybercrime.gov.in and click 'File a Complaint'",
            "Select 'Report Other Cyber Crime' or 'Report Women/Child Related Crime' based on your case",
            "Register with your mobile number and verify via OTP",
            "Select the category that best matches your complaint (Financial Fraud, Social Media, etc.)",
            "Fill in the incident details — use the AI-drafted complaint below for the description field",
            "Upload all evidence (screenshots, bank statements, chat logs)",
            "Note down the acknowledgement number — save it!",
            "If the portal has login issues: Try using Chrome/Edge, clear cookies, or try early morning (lower traffic)",
            "ALTERNATIVE: Call 1930 (National Cyber Crime Helpline) and file verbally — they MUST register your complaint",
            "IMPORTANT: For financial fraud, call 1930 within 24 hours for best chance of freezing the scammer's account"
        ]
    },
    "consumer": {
        "name": "National Consumer Helpline / e-Jagriti",
        "portal": "https://consumerhelpline.gov.in",
        "helpline": "1800-11-4000",
        "email": "nch@nic.in",
        "filing_guide": [
            "Go to https://consumerhelpline.gov.in or https://edaakhil.nic.in",
            "Register with your email and mobile number",
            "Click 'File a Complaint' and select the relevant category",
            "Enter the company/seller details and describe your issue",
            "Upload proof of purchase, payment receipts, and communication records",
            "For complaints > ₹50 lakhs: File in State Consumer Commission",
            "For complaints ≤ ₹50 lakhs: File in District Consumer Forum",
            "ALTERNATIVE: Call 1800-11-4000 (toll-free) to file verbally",
            "Keep all original bills and receipts — you'll need them",
            "Consumer cases typically resolve in 3-6 months"
        ]
    },
    "municipal": {
        "name": "Kochi Municipal Corporation / CPGRAMS",
        "portal": "https://pgportal.gov.in",
        "helpline": "0484-2205553",
        "email": "kochicorporation@gmail.com",
        "filing_guide": [
            "For Kochi municipal issues: Visit https://cochinmunicipalcorporation.kerala.gov.in",
            "For central government issues: Visit https://pgportal.gov.in (CPGRAMS)",
            "Register with your Aadhaar or mobile number",
            "Select the relevant department (Roads, Water, Sanitation, etc.)",
            "Describe the issue with specific location details",
            "Upload photos of the problem (pothole, garbage, broken infrastructure)",
            "Include GPS coordinates or Google Maps pin for exact location",
            "ALTERNATIVE: Use the Nava Kerala app for Kerala state complaints",
            "Follow up if no response within 30 days — file escalation on CPGRAMS",
            "Tag your ward councillor on social media for faster response"
        ]
    },
    "rti": {
        "name": "RTI Online Portal",
        "portal": "https://rtionline.gov.in",
        "helpline": "011-24622461",
        "email": "rtionline-dopt@nic.in",
        "filing_guide": [
            "Go to https://rtionline.gov.in",
            "Click 'Submit Request' and register",
            "Select the Central Public Authority you're requesting information from",
            "Write your RTI request clearly — ask specific questions, not vague ones",
            "Pay the ₹10 fee online",
            "You should receive a response within 30 days",
            "If no response: File First Appeal to the First Appellate Authority",
            "If still no response: File Second Appeal to the Central Information Commission",
            "For state government RTIs: Use the respective state RTI portal",
            "Keep your RTI registration number safe — you'll need it for appeals"
        ]
    },
    "police": {
        "name": "Kerala Police / Local Police Station",
        "portal": "https://keralapolice.gov.in",
        "helpline": "100 / 112",
        "email": "dgp@keralapolice.gov.in",
        "filing_guide": [
            "For emergencies: Call 100 or 112 immediately",
            "For non-emergency FIR: Visit your nearest police station",
            "Police CANNOT refuse to register an FIR — this is your legal right under Section 154 CrPC",
            "If police refuse: Send your complaint by registered post to the SP/Commissioner",
            "You can also file an e-FIR at https://eservices.keralapolice.gov.in",
            "Get a copy of the FIR — it's your legal right",
            "Note the FIR number and investigating officer's name",
            "For women's safety: Call 181 (Women Helpline) or 1091",
            "IMPORTANT: If police refuse to register FIR, you can approach the Magistrate directly under Section 156(3) CrPC",
            "Keep copies of all evidence before handing originals to police"
        ]
    },
    "rera": {
        "name": "Kerala RERA (Real Estate Regulatory Authority)",
        "portal": "https://rera.kerala.gov.in",
        "helpline": "0471-2579700",
        "email": "krera@kerala.gov.in",
        "filing_guide": [
            "Go to https://rera.kerala.gov.in",
            "Check if the project is RERA registered (search by project name)",
            "Click 'File a Complaint' and register",
            "Provide builder/developer details and RERA registration number",
            "Describe the issue (delayed possession, deviation from plan, quality issues)",
            "Upload sale agreement, payment receipts, builder communication",
            "RERA complaints must be filed within 1 year of possession or defect discovery",
            "Filing fee: ₹1,000 for individual complaints",
            "Hearings are typically scheduled within 60 days",
            "If not satisfied with RERA order: Appeal to RERA Appellate Tribunal within 60 days"
        ]
    },
    "railways": {
        "name": "RailMadad — Indian Railways Grievance Portal",
        "portal": "https://railmadad.indianrailways.gov.in",
        "helpline": "139",
        "email": "railmadad@rb.railnet.gov.in",
        "filing_guide": [
            "Go to https://railmadad.indianrailways.gov.in or download RailMadad app",
            "Register with your mobile number",
            "Select complaint category (Cleanliness, Catering, Staff behavior, etc.)",
            "Enter your PNR/ticket number and train details",
            "Describe the issue and upload photos if applicable",
            "ALTERNATIVE: Call 139 for immediate assistance during journey",
            "Tweet to @RailMinIndia or @IRCTCofficial for quick response",
            "Complaints during journey are typically acknowledged within 1 hour",
            "For refund issues: File separately on IRCTC website",
            "Keep your PNR and complaint reference number"
        ]
    }
}


# ─── Demo Mode Responses ─────────────────────────────────────────────────────

def _categorize_demo(description: str) -> dict:
    """
    Categorize a complaint using keyword matching (demo mode).
    In production, this is handled by GPT.
    """
    desc_lower = description.lower()
    
    # Cybercrime keywords
    cyber_keywords = [
        "scam", "fraud", "hack", "phishing", "upi", "otp", "online fraud",
        "cyber", "fake", "sextortion", "blackmail", "identity theft",
        "bank fraud", "credit card", "debit card", "money transfer",
        "fake website", "fake app", "whatsapp scam", "instagram scam",
        "loan app", "crypto scam", "bitcoin", "ransomware", "malware",
        "account hacked", "password", "data breach", "stolen money",
        "gpay", "phonepe", "paytm", "money lost", "transferred money"
    ]
    
    # Consumer keywords
    consumer_keywords = [
        "refund", "product", "defective", "warranty", "seller", "amazon",
        "flipkart", "delivery", "damaged", "wrong product", "overcharged",
        "service", "repair", "replacement", "consumer", "purchase",
        "billing", "subscription", "cancel", "return", "e-commerce"
    ]
    
    # Municipal keywords
    municipal_keywords = [
        "pothole", "garbage", "water supply", "road", "street light",
        "drainage", "sewer", "park", "footpath", "construction",
        "noise", "pollution", "encroachment", "illegal", "building",
        "property tax", "corporation", "municipality", "ward"
    ]
    
    # RTI keywords
    rti_keywords = [
        "information", "rti", "right to information", "government data",
        "transparency", "public authority", "documents", "records"
    ]
    
    # Police keywords
    police_keywords = [
        "theft", "robbery", "assault", "harassment", "stalking",
        "threat", "violence", "abuse", "missing", "accident",
        "fir", "police", "crime", "kidnapping", "murder"
    ]
    
    # RERA keywords
    rera_keywords = [
        "builder", "flat", "apartment", "real estate", "property",
        "possession", "construction delay", "rera", "developer",
        "housing", "plot", "land"
    ]
    
    # Railway keywords
    railway_keywords = [
        "train", "railway", "irctc", "ticket", "pnr", "coach",
        "platform", "station", "rail", "berth", "pantry"
    ]
    
    # Score each category
    scores = {
        "cybercrime": sum(1 for kw in cyber_keywords if kw in desc_lower),
        "consumer": sum(1 for kw in consumer_keywords if kw in desc_lower),
        "municipal": sum(1 for kw in municipal_keywords if kw in desc_lower),
        "rti": sum(1 for kw in rti_keywords if kw in desc_lower),
        "police": sum(1 for kw in police_keywords if kw in desc_lower),
        "rera": sum(1 for kw in rera_keywords if kw in desc_lower),
        "railways": sum(1 for kw in railway_keywords if kw in desc_lower),
    }
    
    best_category = max(scores, key=scores.get)
    confidence = min(scores[best_category] * 25, 95) if scores[best_category] > 0 else 30
    
    if scores[best_category] == 0:
        best_category = "cybercrime"  # Default for demo
        confidence = 60
    
    return {
        "category": best_category,
        "confidence": confidence,
        "subcategory": _get_subcategory(best_category, desc_lower)
    }


def _get_subcategory(category: str, desc_lower: str) -> str:
    """Get a more specific subcategory."""
    subcategories = {
        "cybercrime": {
            "upi fraud": ["upi", "gpay", "phonepe", "paytm", "money transfer"],
            "phishing": ["phishing", "fake email", "fake website", "link"],
            "social media fraud": ["instagram", "facebook", "whatsapp", "telegram"],
            "banking fraud": ["bank", "credit card", "debit card", "account"],
            "online shopping fraud": ["shopping", "order", "fake seller"],
            "sextortion": ["sextortion", "blackmail", "nude", "photos"],
            "loan app harassment": ["loan app", "lending", "interest", "threatening"],
        },
        "consumer": {
            "product defect": ["defective", "broken", "damaged", "quality"],
            "refund not received": ["refund", "money back", "return"],
            "misleading advertisement": ["advertisement", "misleading", "fake claims"],
            "service complaint": ["service", "repair", "maintenance"],
        }
    }
    
    for subcategory, keywords in subcategories.get(category, {}).items():
        if any(kw in desc_lower for kw in keywords):
            return subcategory
    
    return "general"


def _draft_complaint_demo(description: str, category: str, subcategory: str) -> dict:
    """
    Generate a formal complaint draft in demo mode.
    Uses templates — in production, GPT writes custom drafts.
    """
    today = datetime.now().strftime("%d/%m/%Y")
    
    # Generate a formal complaint based on the description
    draft = f"""FORMAL COMPLAINT

Date: {today}
Complaint Category: {category.upper().replace('_', ' ')}
Sub-category: {subcategory.replace('_', ' ').title()}

To,
The {AUTHORITIES.get(category, AUTHORITIES['cybercrime'])['name']}

Subject: Formal Complaint Regarding {subcategory.replace('_', ' ').title()}

Respected Sir/Madam,

I am writing to formally register a complaint regarding the following incident:

{description}

I request you to kindly:
1. Register this complaint and provide an acknowledgement number
2. Investigate the matter thoroughly
3. Take appropriate action against the offender(s)
4. Keep me informed about the progress of the investigation

I am attaching all relevant evidence to support my complaint. I am willing to provide any additional information or documentation that may be required during the investigation.

I trust that your esteemed authority will take prompt action on this matter. The delay in action may cause further harm/loss to me and potentially to other citizens.

I request that this complaint be treated as urgent and action be initiated at the earliest.

Thanking you,
[Your Full Name]
[Your Address]
[Your Phone Number]
[Your Email Address]

Enclosures:
- Screenshots/evidence (as applicable)
- ID proof (Aadhaar/PAN)
- Transaction records (if financial fraud)"""

    # Generate evidence checklist based on category
    evidence_checklists = {
        "cybercrime": [
            "📱 Screenshots of the scam/fraud (messages, calls, emails)",
            "🏦 Bank/UPI transaction statements showing the fraudulent transfer",
            "📋 Transaction reference numbers and timestamps",
            "👤 Scammer's details (phone number, UPI ID, email, social media profile)",
            "💬 Chat logs/call recordings with the scammer",
            "🌐 URLs of fake websites or apps involved",
            "🪪 Your ID proof (Aadhaar/PAN card)",
            "📄 FIR copy (if already filed with police)"
        ],
        "consumer": [
            "🧾 Purchase receipt/invoice/order confirmation",
            "📱 Screenshots of the product listing vs what you received",
            "💬 Communication with seller/company (emails, chats)",
            "📦 Photos of defective/damaged product",
            "📋 Warranty card (if applicable)",
            "🏦 Payment proof (bank statement, UPI receipt)",
            "📄 Company's refund/return policy screenshot",
            "🪪 Your ID proof"
        ],
        "municipal": [
            "📸 Photos of the issue (pothole, garbage, etc.)",
            "📍 Exact location with GPS coordinates or Google Maps link",
            "📅 Dates when the issue was first noticed",
            "👥 Names of other affected residents (if any)",
            "📞 Records of previous complaints to the corporation",
            "📰 Any media coverage of the issue"
        ],
        "police": [
            "📝 Detailed written description of the incident",
            "📅 Date, time, and exact location of the incident",
            "👤 Description/details of the accused (if known)",
            "👥 Witness details and contact information",
            "📸 Photos/videos of evidence or injuries",
            "🏥 Medical reports (if applicable)",
            "🪪 Your ID proof"
        ]
    }
    
    legal_rights = {
        "cybercrime": [
            "⚖️ Under IT Act 2000, cybercrimes are punishable with imprisonment up to 3 years and fine up to ₹5 lakhs",
            "⚖️ Section 66C: Identity theft — up to 3 years imprisonment",
            "⚖️ Section 66D: Cheating by impersonation using computer — up to 3 years imprisonment",
            "⚖️ You can file a Zero FIR at ANY police station — they cannot refuse",
            "⚖️ Call 1930 within 24 hours of financial fraud for best chance of recovering money",
            "⚖️ Banks must reverse unauthorized transactions if reported within 3 working days (RBI circular)"
        ],
        "consumer": [
            "⚖️ Consumer Protection Act 2019 protects your rights as a consumer",
            "⚖️ You can claim compensation for deficiency in service or defective goods",
            "⚖️ E-commerce companies must resolve complaints within 1 month",
            "⚖️ No lawyer needed for consumer forum — you can argue your own case",
            "⚖️ Court fee is minimal: ₹100-500 for District Forum",
            "⚖️ You can claim compensation for mental harassment and time wasted"
        ],
        "municipal": [
            "⚖️ Article 21: Right to clean environment is a fundamental right",
            "⚖️ Municipal authorities are legally obligated to maintain roads and drainage",
            "⚖️ You can file PIL if the issue affects a larger population",
            "⚖️ CPGRAMS complaints MUST be resolved within 60 days"
        ],
        "police": [
            "⚖️ Police CANNOT refuse to register an FIR — Section 154 CrPC",
            "⚖️ If refused: Send complaint by registered post to SP/Commissioner",
            "⚖️ If still refused: Approach Magistrate under Section 156(3) CrPC",
            "⚖️ You have the right to a copy of the FIR — free of charge",
            "⚖️ Women can file complaints online or at home — police must visit"
        ]
    }
    
    authority = AUTHORITIES.get(category, AUTHORITIES["cybercrime"])
    
    return {
        "draft": draft,
        "summary": f"Your complaint has been categorized as a {category.replace('_', ' ')} issue ({subcategory.replace('_', ' ')}). The relevant authority is {authority['name']}.",
        "authority": authority["name"],
        "authority_portal": authority["portal"],
        "authority_helpline": authority["helpline"],
        "authority_email": authority.get("email", ""),
        "filing_guide": authority["filing_guide"],
        "evidence_checklist": evidence_checklists.get(category, evidence_checklists.get("police", [])),
        "legal_rights": legal_rights.get(category, legal_rights.get("police", []))
    }


# ─── Live Mode (Groq — FREE, blazing fast) ────────────────────────────────────

def _process_with_groq(description: str) -> dict:
    """
    Process complaint using Groq (Llama 3.3 70B) for production-quality results.
    FREE tier: 14,400 requests/day. Responses in <1 second.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    
    client = Groq(api_key=api_key)
    
    system_prompt = """You are Awaaz, an AI legal assistant specializing in Indian government complaint filing.

Your job is to:
1. Categorize the user's complaint into the correct authority
2. Draft a formal, legally effective complaint letter
3. Provide a step-by-step filing guide
4. List required evidence
5. Explain the user's legal rights

Categories: cybercrime, consumer, municipal, rti, police, rera, railways, tax, labour, other

Respond ONLY with valid JSON (no markdown, no code fences) with these exact fields:
{
  "category": "string (one of the categories above)",
  "subcategory": "string (specific type within category)",
  "confidence": 85,
  "draft": "string (formal complaint letter, ready to submit, include today's date)",
  "summary": "string (one-paragraph summary of the situation and recommended action)",
  "authority": "string (full name of authority to file with)",
  "authority_portal": "string (website URL)",
  "authority_helpline": "string (phone number)",
  "filing_guide": ["step 1", "step 2", "..."],
  "evidence_checklist": ["item with emoji prefix", "..."],
  "legal_rights": ["right with law section reference", "..."]
}

Be specific to Indian law. Mention exact sections of relevant acts (IT Act, CrPC, Consumer Protection Act, etc.).
Be empathetic but professional. Draft the complaint in a formal tone that government officials will take seriously.
Include specific details from the user's description in the complaint draft."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"I need to file a complaint. Here's my situation:\n\n{description}"}
            ],
            temperature=0.3,
            max_tokens=3000,
            response_format={"type": "json_object"},
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"Groq API error: {e}")
        return None


# ─── Main Public API ─────────────────────────────────────────────────────────

def process_complaint(description: str) -> dict:
    """
    Process a complaint description and return categorization, draft, and guidance.
    Uses Groq (free) if API key is available, falls back to demo mode.
    """
    tracking_id = generate_tracking_id()
    
    # Try Groq live mode first (FREE)
    if GROQ_AVAILABLE and os.getenv("GROQ_API_KEY"):
        result = _process_with_groq(description)
        if result:
            result["tracking_id"] = tracking_id
            result["mode"] = "ai"
            return result
    
    # Fall back to demo mode
    categorization = _categorize_demo(description)
    complaint_data = _draft_complaint_demo(
        description,
        categorization["category"],
        categorization["subcategory"]
    )
    
    return {
        "tracking_id": tracking_id,
        "category": categorization["category"],
        "subcategory": categorization["subcategory"],
        "confidence": categorization["confidence"],
        "mode": "demo",
        **complaint_data
    }

