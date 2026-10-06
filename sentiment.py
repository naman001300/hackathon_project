"""Transformer-only sentiment and sarcasm classification."""
from __future__ import annotations

from typing import Any

SENTIMENT_MODEL_NAME = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"
SARCASM_MODEL_NAME = "helinivan/english-sarcasm-detector"

_SENTIMENT_PIPELINE: Any | None = None
_SARCASM_PIPELINE: Any | None = None


def _load_pipeline(model_name: str):
    """Load and cache a public Hugging Face classifier using system certificates."""
    global _SENTIMENT_PIPELINE, _SARCASM_PIPELINE
    cached = _SENTIMENT_PIPELINE if model_name == SENTIMENT_MODEL_NAME else _SARCASM_PIPELINE
    if cached is None:
        import truststore

        truststore.inject_into_ssl()
        from transformers import pipeline

        cached = pipeline(
            "text-classification",
            model=model_name,
            tokenizer=model_name,
            truncation=True,
        )
        if model_name == SENTIMENT_MODEL_NAME:
            _SENTIMENT_PIPELINE = cached
        else:
            _SARCASM_PIPELINE = cached
    return cached


def _classify_batch(texts: list[str], model_name: str, kind: str) -> list[dict]:
    if not texts:
        return []

    classifier = _load_pipeline(model_name)
    predictions = classifier(texts, batch_size=16, truncation=True)
    results = []
    for prediction in predictions:
        item = prediction[0] if isinstance(prediction, list) else prediction
        raw_label = str(item["label"]).upper()
        confidence = round(float(item["score"]), 4)

        if kind == "sentiment":
            if raw_label not in {"POSITIVE", "NEGATIVE"}:
                raise ValueError(f"Unexpected sentiment label from {model_name}: {raw_label}")
            label = raw_label.lower()
        else:
            if raw_label not in {"LABEL_0", "LABEL_1"}:
                raise ValueError(f"Unexpected sarcasm label from {model_name}: {raw_label}")
            label = "sarcastic" if raw_label == "LABEL_1" else "not_sarcastic"

        results.append({
            "label": label,
            "score": confidence,
            "signals": [raw_label] if kind == "sentiment" else [],
            "model": model_name,
            "model_status": "online",
            "model_used": model_name,
        })
    return results


def classify_sentiments(texts: list[str]) -> list[dict]:
    """Classify a batch of texts as positive or negative with DistilBERT."""
    return _classify_batch(texts, SENTIMENT_MODEL_NAME, "sentiment")


def classify_sarcasms(texts: list[str]) -> list[dict]:
    """Classify a batch of English texts for sarcasm with a fine-tuned BERT model."""
    return _classify_batch(texts, SARCASM_MODEL_NAME, "sarcasm")


def classify_sentiment(text: str) -> dict:
    """Classify one text with DistilBERT."""
    return classify_sentiments([text])[0]


def classify_sarcasm(text: str) -> dict:
    """Classify one text with the sarcasm transformer."""
    return classify_sarcasms([text])[0]