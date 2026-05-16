"""
Tests for Awaaz — API endpoints and AI engine logic.

Run with: pytest tests/ -v
"""

import re
import pytest
from fastapi.testclient import TestClient

from main import app
from ai_engine import generate_tracking_id, _categorize_demo, process_complaint


client = TestClient(app)


# ─── Health Endpoint ──────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_returns_200(self):
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_reports_healthy(self):
        data = response = client.get("/api/health").json()
        assert data["status"] == "healthy"
        assert data["service"] == "Awaaz"
        assert data["ai_mode"] in ("live", "demo")


# ─── Complaint Creation ──────────────────────────────────────────────────────

class TestComplaintCreation:
    def test_create_complaint_happy_path(self):
        """Full complaint creation using demo mode."""
        response = client.post("/api/complaints", json={
            "description": "Someone called pretending to be from SBI bank and stole Rs 15000 via UPI transfer",
            "user_name": "Test User",
            "user_city": "Kochi"
        })
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "tracking_id" in data
        assert data["tracking_id"].startswith("AWZ-")
        assert "category" in data
        assert "draft" in data
        assert "summary" in data
        assert "authority" in data
        assert "authority_portal" in data
        assert "filing_guide" in data
        assert "evidence_checklist" in data

    def test_create_complaint_rejects_short_input(self):
        """Input less than 10 characters should be rejected."""
        response = client.post("/api/complaints", json={
            "description": "hi"
        })
        assert response.status_code == 400

    def test_create_complaint_rejects_empty_input(self):
        """Empty input should be rejected."""
        response = client.post("/api/complaints", json={
            "description": ""
        })
        assert response.status_code == 400

    def test_complaint_appears_in_list(self):
        """Created complaint should show up in the list endpoint."""
        # Create a complaint first
        create_resp = client.post("/api/complaints", json={
            "description": "I ordered a laptop from Flipkart but received an empty box. Seller not responding.",
        })
        tracking_id = create_resp.json()["tracking_id"]

        # Check it appears in the list
        list_resp = client.get("/api/complaints")
        assert list_resp.status_code == 200
        complaints = list_resp.json()["complaints"]
        tracking_ids = [c["tracking_id"] for c in complaints]
        assert tracking_id in tracking_ids


# ─── Complaint Retrieval ─────────────────────────────────────────────────────

class TestComplaintRetrieval:
    def test_get_complaint_by_tracking_id(self):
        """Retrieve a specific complaint by its tracking ID."""
        # Create first
        create_resp = client.post("/api/complaints", json={
            "description": "There is a dangerous pothole on MG Road near Ernakulam junction",
        })
        tracking_id = create_resp.json()["tracking_id"]

        # Fetch it
        get_resp = client.get(f"/api/complaints/{tracking_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["tracking_id"] == tracking_id
        assert data["category"] == "municipal"

    def test_get_nonexistent_complaint_returns_404(self):
        response = client.get("/api/complaints/AWZ-0000-INVALID")
        assert response.status_code == 404


# ─── PDF Export ───────────────────────────────────────────────────────────────

class TestPDFExport:
    def test_pdf_export_returns_pdf(self):
        """PDF export should return valid PDF content."""
        # Create a complaint
        create_resp = client.post("/api/complaints", json={
            "description": "Someone hacked my Instagram account and is blackmailing me",
        })
        tracking_id = create_resp.json()["tracking_id"]

        # Download PDF
        pdf_resp = client.get(f"/api/complaints/{tracking_id}/pdf")
        assert pdf_resp.status_code == 200
        assert pdf_resp.headers["content-type"] == "application/pdf"
        # PDF files start with %PDF
        assert pdf_resp.content[:5] == b"%PDF-"

    def test_pdf_nonexistent_complaint_returns_404(self):
        response = client.get("/api/complaints/AWZ-0000-INVALID/pdf")
        assert response.status_code == 404


# ─── Tracking ID Format ──────────────────────────────────────────────────────

class TestTrackingID:
    def test_tracking_id_format(self):
        """Tracking IDs must match AWZ-YYYY-XXXXXX pattern."""
        for _ in range(10):
            tid = generate_tracking_id()
            assert re.match(r"^AWZ-\d{4}-[A-Z0-9]{6}$", tid), f"Invalid tracking ID: {tid}"

    def test_tracking_ids_are_unique(self):
        """Generated tracking IDs should be unique."""
        ids = {generate_tracking_id() for _ in range(100)}
        assert len(ids) == 100  # All unique


# ─── Demo Categorization ─────────────────────────────────────────────────────

class TestDemoCategorization:
    """Verify the keyword-based demo categorizer assigns correct categories."""

    def test_upi_fraud_categorized_as_cybercrime(self):
        result = _categorize_demo("Someone stole my money via UPI fraud, Rs 25000 gone from GPay")
        assert result["category"] == "cybercrime"

    def test_pothole_categorized_as_municipal(self):
        result = _categorize_demo("There is a massive pothole on the road near my house")
        assert result["category"] == "municipal"

    def test_refund_categorized_as_consumer(self):
        result = _categorize_demo("Flipkart refused to give me a refund for defective product")
        assert result["category"] == "consumer"

    def test_train_categorized_as_railways(self):
        result = _categorize_demo("The train coach was filthy and the IRCTC food was terrible")
        assert result["category"] == "railways"

    def test_builder_categorized_as_rera(self):
        result = _categorize_demo("My builder has delayed flat possession by 2 years, apartment not ready")
        assert result["category"] == "rera"

    def test_theft_categorized_as_police(self):
        result = _categorize_demo("My phone was stolen at the bus station, theft and robbery")
        assert result["category"] == "police"

    def test_rti_categorized_correctly(self):
        result = _categorize_demo("I want to file an RTI request for right to information about government documents and records")
        assert result["category"] == "rti"


# ─── Stats Endpoint ──────────────────────────────────────────────────────────

class TestStats:
    def test_stats_returns_valid_data(self):
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_complaints" in data
        assert "by_category" in data
        assert isinstance(data["total_complaints"], int)


# ─── WhatsApp Share ───────────────────────────────────────────────────────────

class TestWhatsAppShare:
    def test_whatsapp_share_returns_url(self):
        # Create a complaint
        create_resp = client.post("/api/complaints", json={
            "description": "Water supply has been cut off in my area for 3 days, drainage is broken",
        })
        tracking_id = create_resp.json()["tracking_id"]

        # Get WhatsApp URL
        wa_resp = client.get(f"/api/complaints/{tracking_id}/whatsapp")
        assert wa_resp.status_code == 200
        data = wa_resp.json()
        assert "whatsapp_url" in data
        assert data["whatsapp_url"].startswith("https://wa.me/")
