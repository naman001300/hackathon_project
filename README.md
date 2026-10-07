# ReviewPulse - Q17 Feedback & Review Analyzer

An AI-powered, upload-only dashboard for turning customer reviews into product insight.

## What it demonstrates

- Batch CSV analysis with automatic support for common review-app export columns (`review`, `rating`, `date`, `app_name`) or the simple `review_text` schema.
- Manual analysis by pasting one review or multiple reviews separated by a blank line; ratings are optional for pasted reviews.
- Azure OpenAI-powered sentiment, sarcasm, and theme classification using a deployed chat model such as GPT-4o mini.
- Explainable theme detection, with each theme linked to redacted source verbatims and model provenance.
- PII redaction for email addresses, phone numbers, card-like values, and URLs before reviews are displayed or analysed.
- Model validation against an optional `sentiment_label` column (or a clearly labelled rating-derived proxy), plus monthly sentiment drift monitoring.
- A FastAPI endpoint for integrating the same analysis in another frontend.

## Run the dashboard

```bash
python3 -m pip install -r requirements.txt
streamlit run app.py
```

The app waits for pasted review text or a CSV/Excel upload and does not automatically load `reviews_clean.csv`. Reviews are PII-redacted before they are sent to Azure OpenAI, then classified in batches.

## Azure OpenAI setup

Deploy a chat model (recommended: `gpt-4o-mini`) in Azure OpenAI, then set these environment variables before starting Streamlit or FastAPI:

```bash
export AZURE_OPENAI_ENDPOINT="https://YOUR-RESOURCE.openai.azure.com"
export AZURE_OPENAI_API_KEY="YOUR_KEY"
export AZURE_OPENAI_DEPLOYMENT="YOUR_DEPLOYMENT_NAME"
# Optional; defaults to 2024-10-21
export AZURE_OPENAI_API_VERSION="2024-10-21"
```

Never commit an API key. Copy `.env.example` for a local reference only; load the values in your shell or secret manager.

## API

```bash
uvicorn main:app --reload
```

- `GET /health`
- `GET /api/clean-review?review_text=...`
- `POST /api/analyze` with a JSON array of review objects.

Example object: `{"review_id": "r-1", "review_text": "The app crashes", "rating": 1, "date": "2026-01-01"}`.

## Model limitations

The Azure OpenAI classifier uses contextual review analysis. Predictions should be validated on a representative, human-labelled review set before production use.
