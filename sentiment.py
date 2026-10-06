"""GPT-powered review sentiment and sarcasm classification."""
from __future__ import annotations

import json
import os
from collections.abc import Callable
from typing import Any

GPT_MODEL_NAME = os.getenv("OPENAI_REVIEW_MODEL", "gpt-4.1-mini")
REQUEST_BATCH_SIZE = 200


class ModelLoadError(RuntimeError):
    """Raised when the OpenAI-powered review analysis cannot be run."""


RESULT_SCHEMA = {"type": "object", "properties": {"results": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "integer"}, "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative"]}, "sentiment_score": {"type": "number"}, "sarcasm": {"type": "string", "enum": ["sarcastic", "not_sarcastic"]}, "sarcasm_score": {"type": "number"}}, "required": ["id", "sentiment", "sentiment_score", "sarcasm", "sarcasm_score"], "additionalProperties": False}}}, "required": ["results"], "additionalProperties": False}


def _api_key() -> str | None:
    if key := os.getenv("OPENAI_API_KEY"):
        return key
    try:
        import streamlit as st
        return st.secrets.get("OPENAI_API_KEY")
    except Exception:
        return None


def _client():
    key = _api_key()
    if not key:
        raise ModelLoadError("OPENAI_API_KEY is missing. Add it to Streamlit Cloud App settings → Secrets, or set it in your local environment.")
    try:
        from openai import OpenAI
        return OpenAI(api_key=key)
    except Exception as error:
        raise ModelLoadError("The OpenAI SDK could not be initialized.") from error


def _classify_request(client: Any, batch: list[tuple[int, str]]) -> list[dict]:
    try:
        response = client.responses.create(
            model=GPT_MODEL_NAME,
            instructions=("Classify each customer review independently. Sentiment is the overall customer attitude: positive, neutral, or negative. Sarcasm means irony or mocking language; ordinary criticism is not sarcasm. Scores are confidence values from 0 to 1. Return one result for every supplied id."),
            input=json.dumps({"reviews": [{"id": index, "text": text} for index, text in batch]}),
            text={"format": {"type": "json_schema", "name": "review_classifications", "strict": True, "schema": RESULT_SCHEMA}},
        )
        results = json.loads(response.output_text)["results"]
    except Exception as error:
        raise ModelLoadError("OpenAI could not classify the uploaded reviews. Check the API key, billing, and rate limits.") from error
    if len(results) != len(batch) or {item.get("id") for item in results} != {index for index, _ in batch}:
        raise ModelLoadError("OpenAI returned an incomplete review-classification batch. Please retry the upload.")
    return results


def classify_reviews(texts: list[str], progress_callback: Callable[[int, int], None] | None = None) -> list[dict]:
    """Classify sentiment and sarcasm together, minimizing API calls and latency."""
    if not texts:
        return []
    client, classified = _client(), {}
    for start in range(0, len(texts), REQUEST_BATCH_SIZE):
        batch = list(enumerate(texts[start:start + REQUEST_BATCH_SIZE], start))
        for item in _classify_request(client, batch):
            item["sentiment_score"] = round(min(1.0, max(0.0, float(item["sentiment_score"]))), 4)
            item["sarcasm_score"] = round(min(1.0, max(0.0, float(item["sarcasm_score"]))), 4)
            classified[item["id"]] = item
        if progress_callback:
            progress_callback(min(start + len(batch), len(texts)), len(texts))
    return [classified[index] for index in range(len(texts))]


def classify_sentiments(texts: list[str], progress_callback: Callable[[int, int], None] | None = None) -> list[dict]:
    return [{"label": item["sentiment"], "score": item["sentiment_score"], "signals": ["GPT classification"], "model": GPT_MODEL_NAME, "model_status": "online", "model_used": GPT_MODEL_NAME} for item in classify_reviews(texts, progress_callback)]


def classify_sarcasms(texts: list[str], progress_callback: Callable[[int, int], None] | None = None) -> list[dict]:
    return [{"label": item["sarcasm"], "score": item["sarcasm_score"], "signals": [], "model": GPT_MODEL_NAME, "model_status": "online", "model_used": GPT_MODEL_NAME} for item in classify_reviews(texts, progress_callback)]


def classify_sentiment(text: str) -> dict:
    return classify_sentiments([text])[0]


def classify_sarcasm(text: str) -> dict:
    return classify_sarcasms([text])[0]
