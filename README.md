# Inkloom AI — Round 3 Updated Prototype

A Flask-based, text-only brand-governance demo for the CodeAxis Hackathon. It compares draft text with fictional sample rules, explains potential findings, and lets a human reviewer record the next step.

## What's included
- Updated responsive workspace UI with sample-draft buttons and character counter
- Rule-based checks for exaggerated wording, terminology, all-caps writing, repeated punctuation, and claims that may need evidence
- Findings include category, explanation, suggested next step, and attention level
- Human decision controls: Approved, Needs Changes, Rejected
- SQLite-backed review history
- Sample brand rules page and explicit prototype limitations

## Run locally
Requires Python 3.10+.

```bash
python -m venv .venv
# Linux / macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

## Suggested demo
1. Click **Potential issues** or use the default draft.
2. Click **Run brand check**.
3. Walk through the finding category, explanation, and suggested next step.
4. Explain that a claim needing evidence is flagged for review, not declared false.
5. Choose **Request changes** or **Approve** and show the updated status.
6. Open **Review history** and **Brand rules**.

## Important limitations
- This is deterministic rule-based checking, not a full AI model or reliable fact-checker.
- A rule match is a potential issue; false positives and missed issues are possible.
- Claims flagged for evidence have not been verified against an external source.
- The prototype uses fictional sample rules and has no login, role-based permissions, or external AI service.
- Do not submit confidential company content.
- For public deployment, disable Flask debug mode and review privacy, security, and hosting requirements.
