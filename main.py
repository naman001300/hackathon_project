from fastapi import FastAPI
from pii_logic import redact_pii

app = FastAPI()

@app.get("/api/clean-review")
def clean_dummy_review(review_text: str):
    # Jo text aayega, wo tere PII filter mein jayega
    safe_text = redact_pii(review_text)
    
    return {
        "original_review": review_text,
        "cleaned_review": safe_text
    }

