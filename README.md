# ReviewPulse - Q17 Feedback & Review Analyzer

An offline, privacy-first dashboard for turning thousands of customer reviews into product insight.

## What it demonstrates

- Batch CSV analysis with automatic support for common review-app export columns (`review`, `rating`, `date`, `app_name`) or the simple `review_text` schema.
- Explainable sentiment and theme detection, with each theme linked to redacted source verbatims and matching terms.
- PII redaction for email addresses, phone numbers, card-like values, and URLs before reviews are displayed or analysed.
- Model validation against an optional `sentiment_label` column (or a clearly labelled rating-derived proxy), plus monthly sentiment drift monitoring.
- A FastAPI endpoint for integrating the same analysis in another frontend.

## Run the dashboard

```bash
python3 -m pip install -r requirements.txt
streamlit run app.py
```

It opens with the bundled 10,000-review demo dataset. Upload any CSV to analyse your own data.

## API

```bash
uvicorn main:app --reload
```

- `GET /health`
- `GET /api/clean-review?review_text=...`
- `POST /api/analyze` with a JSON array of review objects.

Example object: `{"review_id": "r-1", "review_text": "The app crashes", "rating": 1, "date": "2026-01-01"}`.

## Quality note

The included lexicon model is deliberately offline and explainable for a hackathon demo. For production, validate against a human-labelled sample and replace or augment it with a tested multilingual model.
