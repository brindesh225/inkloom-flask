from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import json
import re
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
DB_PATH = Path(__file__).with_name("inkloom.db")

SAMPLE_RULES = [
    ("Tone", "Avoid exaggerated or guaranteed claims such as 'best ever', '100% guaranteed', or 'perfect for everyone'.", "Use clear, honest, helpful language."),
    ("Terminology", "Use 'customers' or 'everyone' rather than 'guys' when addressing an audience.", "Choose inclusive, audience-appropriate terminology."),
    ("Claims", "Claims such as 'risk-free', 'guaranteed to work', or absolute performance promises may need approved evidence.", "Use precise wording and provide approved evidence for factual claims."),
    ("Style", "Avoid writing an entire message in ALL CAPS.", "Use sentence case so content is easier to read."),
    ("Accessibility", "Avoid repeated exclamation marks and excessive punctuation.", "Use calm, readable punctuation.")
]

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draft TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Needs review',
            issues TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")

def check_text(draft):
    lower = draft.lower()
    issues = []

    checks = [
        (["best ever", "world's best", "world’s best", "perfect for everyone", "the greatest ever"],
         "Tone", "Potentially exaggerated wording", "This wording makes a broad or superlative promise that may not fit the sample brand guidance.",
         "Use a specific, supportable description of the product or benefit.", "Medium"),
        (["guys"],
         "Terminology", "Audience terminology may not match the guideline", "The sample guideline prefers inclusive audience terminology instead of “guys”.",
         "Replace “guys” with “customers”, “everyone”, or the audience's preferred term.", "Low"),
        (["100% guaranteed", "guaranteed to work", "risk-free", "zero risk", "no risk"],
         "Claims", "Strong promise needs evidence or review", "This wording sounds like a guarantee. The checker cannot verify whether the promise is true; a reviewer should check approved evidence.",
         "Remove the guarantee or attach approved evidence and use precise wording.", "High"),
    ]

    for phrases, category, title, reason, suggestion, severity in checks:
        if any(p in lower for p in phrases):
            issues.append({
                "category": category, "title": title, "reason": reason,
                "suggestion": suggestion, "severity": severity,
                "matched_text": next((p for p in phrases if p in lower), "")
            })

    # Flag full-message all caps (ignoring spaces and punctuation).
    letters = [c for c in draft if c.isalpha()]
    if len(letters) >= 5 and all(c.isupper() for c in letters):
        issues.append({
            "category": "Style", "title": "All-caps writing detected",
            "reason": "A message written entirely in capital letters can feel loud and may be harder to scan.",
            "suggestion": "Rewrite the draft in normal sentence case.", "severity": "Low",
            "matched_text": "ALL CAPS"
        })

    if re.search(r"!{2,}", draft):
        issues.append({
            "category": "Accessibility / Style", "title": "Repeated exclamation marks",
            "reason": "Repeated punctuation can make content feel overly promotional and less readable.",
            "suggestion": "Use one punctuation mark and let the message carry the emphasis.", "severity": "Low",
            "matched_text": "!!"
        })

    # Numeric or absolute claims are flagged for verification, not declared false.
    claim_patterns = [
        r"\b\d+\s?%\b", r"\b\d+x\b", r"\bguarantee(?:d|s)?\b",
        r"\balways\b", r"\bnever\b", r"\bfastest\b", r"\bnumber one\b", r"\b#1\b"
    ]
    has_claim_pattern = any(re.search(pattern, lower) for pattern in claim_patterns)
    claim_already_flagged = any(issue["category"] == "Claims" for issue in issues)
    if has_claim_pattern and not claim_already_flagged:
        issues.append({
            "category": "Claims", "title": "Claim may need a source",
            "reason": "The draft contains a numeric, absolute, or performance-style claim. This prototype cannot check the claim against a source, so treat it as needing human verification—not as false.",
            "suggestion": "Ask the content owner for an approved source, or soften the wording until it can be verified.",
            "severity": "Review", "matched_text": "claim requiring verification"
        })

    return issues

@app.route("/", methods=["GET"])
def index():
    with connect() as conn:
        reviews = conn.execute("SELECT * FROM reviews ORDER BY id DESC LIMIT 8").fetchall()
        total = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        flagged = conn.execute("SELECT COUNT(*) FROM reviews WHERE status = 'Needs review'").fetchone()[0]
    return render_template("index.html", reviews=reviews, total=total, flagged=flagged)

@app.route("/review", methods=["POST"])
def review():
    draft = request.form.get("draft", "").strip()
    if not draft:
        return redirect(url_for("index"))
    issues = check_text(draft)
    status = "Needs review" if issues else "Ready for review"
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO reviews (draft, status, issues, created_at) VALUES (?, ?, ?, ?)",
            (draft, status, json.dumps(issues), datetime.now().strftime("%d %b %Y, %I:%M %p"))
        )
        review_id = cur.lastrowid
    return redirect(url_for("result", review_id=review_id))

@app.route("/result/<int:review_id>")
def result(review_id):
    with connect() as conn:
        item = conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
    if item is None:
        return redirect(url_for("index"))
    return render_template("result.html", item=item, issues=json.loads(item["issues"]))

@app.route("/status/<int:review_id>", methods=["POST"])
def status(review_id):
    new_status = request.form.get("status", "Needs review")
    allowed = {"Approved", "Needs Changes", "Rejected", "Ready for review", "Needs review"}
    if new_status not in allowed:
        new_status = "Needs review"
    with connect() as conn:
        conn.execute("UPDATE reviews SET status = ? WHERE id = ?", (new_status, review_id))
    return redirect(url_for("result", review_id=review_id))

@app.route("/guidelines")
def guidelines():
    return render_template("guidelines.html", rules=SAMPLE_RULES)

@app.route("/history")
def history():
    with connect() as conn:
        reviews = conn.execute("SELECT * FROM reviews ORDER BY id DESC").fetchall()
    return render_template("history.html", reviews=reviews)

init_db()

if __name__ == "__main__":
    # Debug is convenient for local demos only. Do not use it for public deployment.
    app.run(debug=True)
