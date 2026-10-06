# ReviewPulse - Q17 Feedback & Review Analyzer

An AI-powered, upload-only dashboard for turning customer reviews into product insight.

## What it demonstrates

- Batch CSV analysis with automatic support for common review-app export columns (`review`, `rating`, `date`, `app_name`) or the simple `review_text` schema.
- Manual analysis by pasting one review or multiple reviews separated by a blank line; ratings are optional for pasted reviews.
- Fast local sentiment and sarcasm classification; no model downloads, API key, or external service is required.
- Explainable theme detection, with each theme linked to redacted source verbatims and matching terms.
- PII redaction for email addresses, phone numbers, card-like values, and URLs before reviews are displayed or analysed.
- Model validation against an optional `sentiment_label` column (or a clearly labelled rating-derived proxy), plus monthly sentiment drift monitoring.
- A FastAPI endpoint for integrating the same analysis in another frontend.

## Run the dashboard

```bash
python3 -m pip install -r requirements.txt
streamlit run app.py
```

The app waits for pasted review text or a CSV/Excel upload and does not automatically load `reviews_clean.csv`. Reviews are PII-redacted, then classified locally in batches. No API key, model download, billing setup, or external network request is needed.

## API

```bash
uvicorn main:app --reload
```

- `GET /health`
- `GET /api/clean-review?review_text=...`
- `POST /api/analyze` with a JSON array of review objects.

Example object: `{"review_id": "r-1", "review_text": "The app crashes", "rating": 1, "date": "2026-01-01"}`.

## Model limitations

The local classifier uses sentiment and sarcasm signals designed for English customer reviews. Predictions should be validated on a representative, human-labelled review set before production use.
