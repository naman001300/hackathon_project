from fastapi import FastAPI, HTTPException
from pii_logic import redact_pii
from review_pipeline import analyze_reviews

app = FastAPI(title="ReviewPulse API", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/clean-review")
def clean_review(review_text: str):
    return {"original_review": review_text, "cleaned_review": redact_pii(review_text)}

@app.post("/api/analyze")
def analyze(payload: list[dict]):
    if not payload:
        raise HTTPException(status_code=400, detail="Provide at least one review.")
    return analyze_reviews(payload)
