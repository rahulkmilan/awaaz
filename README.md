# 🔊 Awaaz — Your Voice. Actually Heard.

> AI-powered government complaint filing platform for India.  
> Describe your problem in plain language → get a legally sound complaint drafted, the right authority identified, and a step-by-step filing guide.

[![Live Demo](https://img.shields.io/badge/Live-awaaz--32mv.onrender.com-10b981?style=for-the-badge&logo=render&logoColor=white)](https://awaaz-32mv.onrender.com)

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/AI-Groq%20Llama%203.3-orange?logo=meta&logoColor=white)](https://groq.com)
[![Tests](https://github.com/rahulkmilan/awaaz/actions/workflows/tests.yml/badge.svg)](https://github.com/rahulkmilan/awaaz/actions/workflows/tests.yml)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## The Problem

Filing a government complaint in India is **broken**.

- **68% of cybercrime victims never report** — because the process is too painful
- **Only 1.4–2.9% of complaints become FIRs** — the system fails citizens daily
- Government portals like `cybercrime.gov.in` suffer from random logouts, confusing forms, and zero guidance
- Citizens don't know **where** to file, **what** to write, or **what rights** they have

## The Solution

**Awaaz** is TurboTax for government complaints.

1. **Describe** your problem in plain language (any language, any complexity)
2. **AI analyzes** your situation and identifies the correct authority
3. **Get** a formal complaint letter, step-by-step filing guide, evidence checklist, and your legal rights
4. **File** it yourself using our guided process — or call the helpline number we provide

No lawyer needed. No legal jargon. Just justice.

---

## Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI-Powered Drafting** | Llama 3.3 70B via Groq generates custom complaint letters tailored to your situation |
| 🏛️ **Smart Categorization** | Auto-detects complaint type: cybercrime, consumer, municipal, police, RERA, RTI, railways |
| 📋 **Filing Guides** | Step-by-step instructions with direct portal links and helpline numbers |
| 📎 **Evidence Checklists** | Category-specific lists of what evidence to gather before filing |
| ⚖️ **Legal Rights** | Relevant Indian law sections (IT Act, CrPC, Consumer Protection Act) so you know your rights |
| 🔒 **Tracking IDs** | Every complaint gets a unique ID (AWZ-2026-XXXXXX) for your records |
| 📄 **PDF Export** | Download a formal, printable complaint letter as PDF |
| 💬 **WhatsApp Sharing** | Share complaint summary via WhatsApp with one click |
| 🎤 **Voice Input** | Speak your complaint — Web Speech API transcribes it |
| 📝 **Quick Templates** | Pre-written templates for common issues (UPI fraud, potholes, etc.) |
| 🌐 **Multi-Language** | Draft complaints in English, Hindi, Malayalam, Tamil, Telugu, or Kannada |
| 📊 **Dashboard** | Track all filed complaints with search and category filtering |
| 🛡️ **Rate Limited** | API rate limiting protects the free AI tier from abuse |
| 📱 **Mobile Responsive** | Works on any device — phone, tablet, or desktop |
| ⚡ **Blazing Fast** | AI responses in under 2 seconds thanks to Groq inference |
| 💰 **100% Free AI** | No API costs — Groq's free tier handles 14,400 requests/day |

## Supported Complaint Categories

| Category | Authority | Helpline |
|----------|-----------|----------|
| 🛡️ Cybercrime | National Cyber Crime Reporting Portal | 1930 |
| 🛒 Consumer | National Consumer Helpline / e-Jagriti | 1800-11-4000 |
| 🏛️ Municipal | Kochi Corporation / CPGRAMS | 0484-2205553 |
| 🚔 Police / FIR | Kerala Police | 100 / 112 |
| 🏠 Real Estate (RERA) | Kerala RERA | 0471-2579700 |
| 📋 RTI | RTI Online Portal | 011-24622461 |
| 🚂 Railways | RailMadad | 139 |

---

## Tech Stack

- **Backend:** Python 3.12 + FastAPI
- **AI Engine:** Groq (Llama 3.3 70B Versatile) — free tier
- **Database:** SQLite (local) / PostgreSQL (production via `DATABASE_URL`)
- **Frontend:** Vanilla HTML/CSS/JS — dark premium theme
- **Styling:** Custom CSS with glassmorphism, gradients, micro-animations
- **Testing:** pytest + httpx
- **Deployment:** Render (Infrastructure-as-Code via `render.yaml`)

---

## Quick Start

### Prerequisites

- Python 3.10+
- A free [Groq API key](https://console.groq.com/keys)

### Setup

```bash
# Clone the repo
git clone https://github.com/rahulkmilan/awaaz.git
cd awaaz

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
echo "GROQ_API_KEY=your_groq_api_key_here" > .env

# Run the server
python -m uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000** in your browser.

### Without AI (Demo Mode)

The app works without an API key too — it uses keyword-based categorization and template-based drafting. Just skip the `.env` step.

### Running Tests

```bash
pip install pytest httpx
pytest tests/ -v
```

### Live Demo

**[https://awaaz-32mv.onrender.com](https://awaaz-32mv.onrender.com)**

---

## Project Structure

```
awaaz/
├── main.py              # FastAPI app — routes, middleware, PDF export
├── ai_engine.py         # AI categorization, drafting & guidance engine
├── database.py          # Database setup (SQLite local / PostgreSQL prod)
├── models.py            # Data models (Complaint, Evidence)
├── requirements.txt     # Python dependencies
├── render.yaml          # Render deployment config (IaC)
├── Procfile             # Process file for Render
├── .env                 # API keys (not committed to git)
├── .gitignore           # Git ignore rules
├── templates/
│   └── index.html       # Frontend SPA (landing + form + results + dashboard)
├── static/
│   ├── css/
│   │   └── style.css    # Design system — dark theme, animations
│   └── js/
│       └── app.js       # Frontend logic — form handling, rendering
└── tests/
    └── test_api.py      # API & engine tests (pytest)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Landing page |
| `POST` | `/api/complaints` | Submit a complaint for AI analysis (rate limited: 10/min) |
| `GET` | `/api/complaints` | List all complaints |
| `GET` | `/api/complaints/{tracking_id}` | Get complaint by tracking ID |
| `PATCH` | `/api/complaints/{tracking_id}/status` | Update complaint status |
| `GET` | `/api/complaints/{tracking_id}/pdf` | Download complaint as PDF |
| `GET` | `/api/complaints/{tracking_id}/whatsapp` | Get WhatsApp share URL |
| `GET` | `/api/stats` | Platform statistics |
| `GET` | `/api/health` | Health check |

### Example Request

```bash
curl -X POST https://awaaz-32mv.onrender.com/api/complaints \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Someone called pretending to be from SBI and stole Rs 15000 via UPI",
    "user_name": "Rahul",
    "user_city": "Kochi"
  }'
```

---

## Roadmap

- [x] AI complaint categorization and drafting (Groq Llama 3.3)
- [x] 7 complaint categories with filing guides
- [x] Evidence checklists and legal rights
- [x] SQLite database with tracking IDs
- [x] PDF export of complaints
- [x] WhatsApp sharing
- [x] Complaint status tracking dashboard
- [x] Voice-to-text input (Web Speech API)
- [x] Pre-written complaint templates
- [x] Multi-language support (Hindi, Malayalam, Tamil, Telugu, Kannada)
- [x] Advanced search & filter on dashboard
- [x] Rate limiting (slowapi)
- [x] Input sanitization & error resilience
- [x] Automated tests (pytest)
- [x] PostgreSQL support for production
- [x] Infrastructure-as-Code (render.yaml)
- [ ] Phone OTP authentication
- [ ] Complaint edit/refine flow
- [ ] Auto-escalation if no response in 30 days
- [ ] Evidence file upload
- [ ] Integration with CPGRAMS API

## Contributing

Contributions welcome! This is a civic tech project — if you want to help Indian citizens access justice, open a PR.

## License

MIT License — use it, fork it, build on it.

---

<p align="center">
  Built with conviction in <strong>Kochi</strong> 🇮🇳<br>
  Because every citizen deserves to be heard.
</p>
