from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

OUTPUT = "hackathon_role_wise_study_guide.pdf"

roles = [
    {
        "title": "Person 1 - Product Story and Pitch Lead",
        "files": "README.md and overall project flow",
        "study": [
            "Problem: customer reviews are large, unstructured, and difficult to analyse manually.",
            "Solution: ReviewPulse converts reviews into sentiment, themes, evidence, privacy-safe text, and trends.",
            "Know the 30-second pitch and the 2-minute presentation sequence.",
            "Explain the business value: faster product decisions and early complaint detection.",
        ],
        "demo": "Open the dashboard, explain the problem, show the bundled 10K review dataset, and connect every chart to a product decision.",
        "questions": "Why is this useful? Who uses it? What decisions can a product team make from the output?",
    },
    {
        "title": "Person 2 - Streamlit Dashboard and UX Lead",
        "files": "app.py",
        "study": [
            "CSV upload and automatic column detection for review, review_text, rating, date, and app_name.",
            "Dashboard metrics: reviews analysed, positive signals, negative signals, PII protected, and validation accuracy.",
            "Sentiment landscape, theme chart, evidence expanders, mood-over-time chart, and audit table.",
            "How the dashboard calls analyze_reviews(records) and displays its result.",
        ],
        "demo": "Own the live UI walkthrough: upload a CSV, point out the charts, expand evidence, and show the audit trail.",
        "questions": "What input format is supported? Can users analyse their own data? What happens if a column is missing?",
    },
    {
        "title": "Person 3 - AI, Sentiment, and Theme Analytics Lead",
        "files": "sentiment.py, themes.py, and review_pipeline.py",
        "study": [
            "Sentiment uses an offline, explainable word lexicon. Positive and negative signal words produce a bounded score.",
            "Themes use keyword groups such as reliability, performance, usability, support, price, privacy, and features.",
            "Every classification retains the matching signal words, making the output traceable.",
            "Know the limitation: this is a hackathon model; production needs human-labelled data and a tested multilingual model.",
        ],
        "demo": "Expand an evidence item and explain exactly which words triggered the sentiment and theme classification.",
        "questions": "Is this machine learning? How is explainability achieved? How would you improve accuracy for production?",
    },
    {
        "title": "Person 4 - Privacy and Responsible AI Lead",
        "files": "pii_logic.py and the privacy parts of app.py",
        "study": [
            "PII is redacted before the text is analysed or displayed.",
            "Supported patterns: email addresses, phone numbers, card-like numbers, and URLs.",
            "Know the replacements: [EMAIL REDACTED], [PHONE REDACTED], [CARD REDACTED], and [URL REDACTED].",
            "The dashboard audit trail displays protected text, not the original sensitive values.",
        ],
        "demo": "Use a sample review containing an email or phone number and show that the displayed result is redacted.",
        "questions": "When does redaction happen? What PII is covered? What would you add for production?",
    },
    {
        "title": "Person 5 - Backend and API Integration Lead",
        "files": "main.py and review_pipeline.py",
        "study": [
            "FastAPI exposes GET /health, GET /api/clean-review, and POST /api/analyze.",
            "The API and Streamlit dashboard share the same analysis pipeline, so logic is not duplicated.",
            "Know the example JSON review object and the empty-payload validation response.",
            "Run command: uvicorn main:app --reload.",
        ],
        "demo": "Show how another frontend or service could send reviews to POST /api/analyze and receive structured results.",
        "questions": "How can this integrate with a mobile app or existing frontend? Why expose an API? How is invalid input handled?",
    },
    {
        "title": "Person 6 - Testing, Validation, and Quality Lead",
        "files": "test_pipeline.py and quality logic in review_pipeline.py",
        "study": [
            "Invalid rows are skipped and counted instead of breaking the full batch.",
            "Validation uses sentiment_label when available, otherwise a rating-derived proxy: 4-5 positive, 3 neutral, 1-2 negative.",
            "Monthly sentiment trend is generated from dated reviews.",
            "Jensen-Shannon divergence compares the first and second time periods and reports Stable or Watch.",
            "Run command: .venv/bin/pytest.",
        ],
        "demo": "Show the quality and model notes section, explain validation accuracy, and mention the difference between a proxy label and ground truth.",
        "questions": "How do you know the model is correct? What happens with bad rows? How do you detect changing customer mood?",
    },
]

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleCustom", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=27, alignment=TA_CENTER, textColor=colors.HexColor("#12304A"), spaceAfter=8))
styles.add(ParagraphStyle(name="Subtitle", parent=styles["Normal"], fontSize=10, leading=14, alignment=TA_CENTER, textColor=colors.HexColor("#48657A"), spaceAfter=16))
styles.add(ParagraphStyle(name="RoleTitle", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=colors.HexColor("#0B6174"), spaceBefore=4, spaceAfter=8))
styles.add(ParagraphStyle(name="Label", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=colors.HexColor("#12304A"), spaceBefore=5, spaceAfter=2))
styles.add(ParagraphStyle(name="BodySmall", parent=styles["Normal"], fontSize=9.5, leading=13, textColor=colors.HexColor("#243746"), spaceAfter=3))
styles.add(ParagraphStyle(name="Footer", parent=styles["Normal"], fontSize=8, alignment=TA_CENTER, textColor=colors.HexColor("#6B7C87")))


def bullet(text):
    return Paragraph("- " + text, styles["BodySmall"])


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D5E3E8"))
    canvas.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6B7C87"))
    canvas.drawCentredString(105 * mm, 8 * mm, "ReviewPulse | Hackathon Role-Wise Study Guide")
    canvas.restoreState()


doc = SimpleDocTemplate(OUTPUT, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=16 * mm, bottomMargin=20 * mm)
story = [
    Paragraph("ReviewPulse", styles["TitleCustom"]),
    Paragraph("Hackathon Role-Wise Study Guide - 6 Team Members", styles["Subtitle"]),
    Paragraph("Common pitch: ReviewPulse converts raw customer reviews into explainable product insights while protecting customer privacy.", styles["BodySmall"]),
    Spacer(1, 8),
]

for index, role in enumerate(roles):
    story.append(Paragraph(role["title"], styles["RoleTitle"]))
    story.append(Paragraph("Study files: " + role["files"], styles["BodySmall"]))
    story.append(Paragraph("What to study", styles["Label"]))
    story.extend(bullet(item) for item in role["study"])
    story.append(Paragraph("Demo responsibility", styles["Label"]))
    story.append(Paragraph(role["demo"], styles["BodySmall"]))
    story.append(Paragraph("Likely judge questions", styles["Label"]))
    story.append(Paragraph(role["questions"], styles["BodySmall"]))
    if index != len(roles) - 1:
        story.append(Spacer(1, 8))
        story.append(Table([[""]], colWidths=[174 * mm], rowHeights=[0.5 * mm], style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#D5E3E8"))])))
        story.append(Spacer(1, 6))

story.append(Spacer(1, 8))
story.append(Paragraph("Final team checklist", styles["RoleTitle"]))
for item in [
    "Everyone should know the overall pitch, privacy flow, model limitation, and how to run the project.",
    "Dashboard: streamlit run app.py",
    "API: uvicorn main:app --reload",
    "Tests: .venv/bin/pytest",
    "Do not call rating-derived labels ground truth; clearly describe them as a proxy.",
]:
    story.append(bullet(item))

doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUTPUT)
