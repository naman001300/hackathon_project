"""Transformer-based sentiment and sarcasm classification with safe fallbacks."""
from __future__ import annotations

import re
from typing import Any

SENTIMENT_MODEL_NAME = "distilbert-base-uncased-finetuned-sentiment"
SARCASM_MODEL_NAME = "cardiffnlp/twitter-roberta-base-sarcasm"

_SENTIMENT_PIPELINE: Any | None = None
_SARCASM_PIPELINE: Any | None = None

_IRONIC_PATTERN = re.compile(
    r"\b(?:great|awesome|fantastic|love|excellent|amazing|perfect|brilliant|nice|wonderful)\b"
    r".*\b(?:but|however|still|yet|though|unless|except|really|totally|absolutely|another)\b"
    r".*\b(?:bad|broken|slow|terrible|awful|worse|hate|crash|bug|delay|problem|useless|worse)\b"
    r"|\b(?:yeah|sure|great|nice|fantastic|amazing)\b.*\b(?:not|never|no|doesn't|doesnt)\b"
    r"|\b(?:great|love|amazing)\b.*\b(?:update|feature|improvement)\b.*\b(?:worse|breaks|fails|crashes|slow)\b",
    re.IGNORECASE,
)


def _load_pipeline(model_name: str, task: str):
    """Load a Hugging Face pipeline lazily."""
    pipeline = _SENTIMENT_PIPELINE if model_name == SENTIMENT_MODEL_NAME else _SARCASM_PIPELINE
    if pipeline is None:
        try:
            from transformers import pipeline as build_pipeline

            pipeline = build_pipeline(task, model=model_name, tokenizer=model_name, truncation=True)
        except Exception:
            pipeline = False
        if model_name == SENTIMENT_MODEL_NAME:
            globals()["_SENTIMENT_PIPELINE"] = pipeline
        else:
            globals()["_SARCASM_PIPELINE"] = pipeline
    return pipeline


def classify_sentiment(text: str) -> dict:
    """Return BERT sentiment, or a conservative fallback when the model is unavailable."""
    pipeline = _load_pipeline(SENTIMENT_MODEL_NAME, "text-classification")

    if pipeline is False:
        return {
            "label": "neutral",
            "score": 0.0,
            "signals": [],
            "model": SENTIMENT_MODEL_NAME,
            "model_status": "unavailable",
        }

    result = pipeline(text)[0]
    label = "positive" if result["label"] == "POSITIVE" else "negative"
    score = float(result["score"])

    if label == "positive":
        score = score if score > 0.5 else 0.5
    else:
        score = 1.0 - score if score < 0.5 else 0.5

    return {
        "label": label,
        "score": round(score, 2),
        "signals": [result["label"]],
        "model": SENTIMENT_MODEL_NAME,
        "model_status": "online",
    }


def classify_sarcasm(text: str) -> dict:
    """Detect sarcasm with a dedicated RoBERTa model when available, or with a local fallback."""
    pipeline = _load_pipeline(SARCASM_MODEL_NAME, "text-classification")

    if pipeline is False:
        score = 0.9 if _IRONIC_PATTERN.search(text) else 0.1
        label = "sarcastic" if score > 0.5 else "not_sarcastic"
        return {
            "label": label,
            "score": round(score, 2),
            "model": SARCASM_MODEL_NAME,
            "model_status": "fallback",
        }

    result = pipeline(text)[0]
    is_sarcastic = result["label"] == "LABEL_1"
    score = float(result["score"])

    if not is_sarcastic:
        score = 1.0 - score

    return {
        "label": "sarcastic" if is_sarcastic else "not_sarcastic",
        "score": round(score, 2),
        "model": SARCASM_MODEL_NAME,
        "model_status": "online",
    }
