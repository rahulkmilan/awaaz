"""
Test configuration — ensures database tables exist before tests run.
"""

from database import init_db

# Create all tables before any test runs
init_db()
