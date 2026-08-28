"""
Seeds the database with demo content on a fresh deploy.

The reports analyzed here (Renault's DEU 2024 and Stellantis's Expanded
Sustainability Statement 2024) are both public disclosures, so keeping their
analysis results around is fine, it just saves a visitor from having to
upload their own report to see the app do something. The stored analysis
and comparison text was generated once, for real, by the app itself, this
just replays that result into a fresh database instead of paying for a new
LLM call on every cold start.

Render's free plan has no persistent disk, so the SQLite file starts empty
on every deploy. This runs once at startup and is a no-op if the reports
table already has data.
"""

import json
import os

from database import get_db_connection
from utils import hash_password

SEED_FILE = os.path.join(os.path.dirname(__file__), "seed_demo_data.json")
DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "Demo1234!"


def seed_demo_data():
    if not os.path.exists(SEED_FILE):
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM reports")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    with open(SEED_FILE, "r", encoding="utf-8") as f:
        seed = json.load(f)

    try:
        cursor.execute(
            "INSERT INTO users (id, first_name, last_name, email, hashed_password) VALUES (1, ?, ?, ?, ?)",
            ("Demo", "Account", DEMO_EMAIL, hash_password(DEMO_PASSWORD)),
        )

        for r in seed["reports"]:
            cursor.execute(
                "INSERT INTO reports (id, user_id, filename, filepath, extracted_text, extracted_tables, upload_date) "
                "VALUES (?, 1, ?, ?, ?, ?, ?)",
                (r["id"], r["filename"], r["filepath"], r["extracted_text"], r["extracted_tables"], r["upload_date"]),
            )

        for a in seed["advanced_analyses"]:
            cursor.execute(
                "INSERT INTO advanced_analyses (id, report_id, user_id, analysis_text, scores_json, analysis_date, model_used, tokens_used) "
                "VALUES (?, ?, 1, ?, ?, ?, ?, ?)",
                (a["id"], a["report_id"], a["analysis_text"], a["scores_json"], a["analysis_date"], a["model_used"], a["tokens_used"]),
            )

        for c in seed["ai_comparisons"]:
            cursor.execute(
                "INSERT INTO ai_comparisons (id, user_id, report1_id, report2_id, comparison_text, scores_json, comparison_date, model_used, tokens_used) "
                "VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?)",
                (c["id"], c["report1_id"], c["report2_id"], c["comparison_text"], c["scores_json"], c["comparison_date"], c["model_used"], c["tokens_used"]),
            )

        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Demo seed failed: {e}")
        return

    conn.close()
    print(f"Seeded demo data: {len(seed['reports'])} reports, {len(seed['advanced_analyses'])} analyses, {len(seed['ai_comparisons'])} comparisons")
    print(f"Demo login: {DEMO_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    seed_demo_data()
