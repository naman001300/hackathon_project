"""Azure OpenAI-powered review classification."""
from __future__ import annotations

import json
import os
from collections.abc import Callable


AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
GPT_MODEL_NAME = AZURE_OPENAI_DEPLOYMENT or "azure-openai-unconfigured"
REQUEST_BATCH_SIZE = 25

_THEMES = {"reliability", "performance", "features", "usability", "support", "price", "privacy", "other"}


class ModelLoadError(RuntimeError):
    """Raised when Azure OpenAI cannot be used for review analysis."""


def _client():
    if not all((AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT)):
        raise ModelLoadError(
            "Azure OpenAI is not configured. Set AZURE_OPENAI_ENDPOINT, "
            "AZURE_OPENAI_API_KEY, and AZURE_OPENAI_DEPLOYMENT."
        )
    try:
        from openai import AzureOpenAI
    except ImportError as error:
        raise ModelLoadError("The OpenAI SDK is missing. Run: python3 -m pip install -r requirements.txt") from error
    return AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )


def _prompt(texts: list[str]) -> str:
    reviews = [{"index": index, "review": text} for index, text in enumerate(texts)]
    return f"""Classify each customer review. Return JSON only, following this exact shape:
{{"results":[{{"index":0,"sentiment":"positive|neutral|negative","sentiment_score":0.0,"sarcasm":"sarcastic|not_sarcastic","sarcasm_score":0.0,"themes":["reliability"]}}]}}

Rules:
- sentiment_score and sarcasm_score must be numbers from 0 to 1.
- Choose one or more themes only from: reliability, performance, features, usability, support, price, privacy, other.
- Use contextual meaning, not merely keywords. Detect sarcasm when the wording implies the opposite of its literal praise.
- Preserve the input index and return exactly one result per review.

Reviews:
{json.dumps(reviews, ensure_ascii=False)}"""


def _normalise(item: dict, index: int) -> dict:
    sentiment = str(item.get("sentiment", "neutral")).lower()
    sarcasm = str(item.get("sarcasm", "not_sarcastic")).lower()
    themes = item.get("themes", ["other"])
    if not isinstance(themes, list):
        themes = ["other"]
    clean_themes = [str(theme).lower() for theme in themes if str(theme).lower() in _THEMES] or ["other"]
    try:
        sentiment_score = min(1.0, max(0.0, float(item.get("sentiment_score", 0.5))))
        sarcasm_score = min(1.0, max(0.0, float(item.get("sarcasm_score", 0.0))))
    except (TypeError, ValueError):
        sentiment_score, sarcasm_score = 0.5, 0.0
    return {
        "index": index,
        "sentiment": sentiment if sentiment in {"positive", "neutral", "negative"} else "neutral",
        "sentiment_score": round(sentiment_score, 4),
        "sarcasm": sarcasm if sarcasm in {"sarcastic", "not_sarcastic"} else "not_sarcastic",
        "sarcasm_score": round(sarcasm_score, 4),
        "themes": list(dict.fromkeys(clean_themes)),
    }


def _classify_batch(client, texts: list[str]) -> list[dict]:
    try:
        completion = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a precise customer-review analytics model. Return valid JSON only."},
                {"role": "user", "content": _prompt(texts)},
            ],
        )
        payload = json.loads(completion.choices[0].message.content or "{}")
        rows = payload.get("results", [])
    except Exception as error:
        raise ModelLoadError(f"Azure OpenAI analysis failed: {error}") from error
    if not isinstance(rows, list):
        raise ModelLoadError("Azure OpenAI returned an invalid analysis response.")
    by_index = {item.get("index"): item for item in rows if isinstance(item, dict) and isinstance(item.get("index"), int)}
    if any(index not in by_index for index in range(len(texts))):
        raise ModelLoadError("Azure OpenAI response was incomplete; no reviews were saved.")
    return [_normalise(by_index[index], index) for index in range(len(texts))]


def classify_reviews(texts: list[str], progress_callback: Callable[[int, int], None] | None = None) -> list[dict]:
    """Classify redacted reviews through the configured Azure OpenAI deployment."""
    client = _client()
    results: list[dict] = []
    for start in range(0, len(texts), REQUEST_BATCH_SIZE):
        results.extend(_classify_batch(client, texts[start:start + REQUEST_BATCH_SIZE]))
        if progress_callback:
            progress_callback(len(results), len(texts))
    return results


def classify_sentiments(texts: list[str], progress_callback: Callable[[int, int], None] | None = None) -> list[dict]:
    return [{"label": item["sentiment"], "score": item["sentiment_score"], "signals": ["Azure OpenAI contextual classification"], "model": GPT_MODEL_NAME, "model_status": "azure_openai", "model_used": GPT_MODEL_NAME} for item in classify_reviews(texts, progress_callback)]


def classify_sarcasms(texts: list[str], progress_callback: Callable[[int, int], None] | None = None) -> list[dict]:
    return [{"label": item["sarcasm"], "score": item["sarcasm_score"], "signals": ["Azure OpenAI contextual classification"], "model": GPT_MODEL_NAME, "model_status": "azure_openai", "model_used": GPT_MODEL_NAME} for item in classify_reviews(texts, progress_callback)]


def classify_sentiment(text: str) -> dict:
    return classify_sentiments([text])[0]


def classify_sarcasm(text: str) -> dict:
    return classify_sarcasms([text])[0]
