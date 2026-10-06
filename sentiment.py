"""Transformer-only sentiment and sarcasm classification."""
from __future__ import annotations

from collections.abc import Callable
from threading import Lock
from typing import Any

SENTIMENT_MODEL_NAME = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"
SARCASM_MODEL_NAME = "helinivan/english-sarcasm-detector"

_SENTIMENT_PIPELINE: Any | None = None
_SARCASM_PIPELINE: Any | None = None
_PIPELINE_LOAD_LOCK = Lock()
# Free Streamlit Cloud runs on CPU. Larger batches reduce Python/pipeline overhead
# dramatically while 128 tokens comfortably covers normal customer reviews.
CLASSIFY_CHUNK_SIZE = 512
INFERENCE_BATCH_SIZE = 64
MAX_INPUT_TOKENS = 128


class ModelLoadError(RuntimeError):
    """Raised when a required Hugging Face model cannot be made available."""


def _load_pipeline(model_name: str):
    """Load a classifier once per process, including during concurrent uploads."""
    global _SENTIMENT_PIPELINE, _SARCASM_PIPELINE
    cached = _SENTIMENT_PIPELINE if model_name == SENTIMENT_MODEL_NAME else _SARCASM_PIPELINE
    if cached is not None:
        return cached

    # Streamlit can process uploads in separate sessions at the same time. Without
    # this guard both sessions may try to download/load the same large weights,
    # which can exhaust memory or leave an upload apparently stuck.
    with _PIPELINE_LOAD_LOCK:
        cached = _SENTIMENT_PIPELINE if model_name == SENTIMENT_MODEL_NAME else _SARCASM_PIPELINE
        if cached is not None:
            return cached

        try:
            import truststore

            truststore.inject_into_ssl()
            from transformers import pipeline

            cached = pipeline(
                "text-classification",
                model=model_name,
                tokenizer=model_name,
                truncation=True,
            )
        except Exception as error:
            raise ModelLoadError(
                f"Could not load {model_name}. Check the internet connection, "
                "Hugging Face access, and available disk space."
            ) from error

        if model_name == SENTIMENT_MODEL_NAME:
            _SENTIMENT_PIPELINE = cached
        else:
            _SARCASM_PIPELINE = cached
    return cached


def _classify_batch(
    texts: list[str],
    model_name: str,
    kind: str,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[dict]:
    if not texts:
        return []

    classifier = _load_pipeline(model_name)
    results = []
    for start in range(0, len(texts), CLASSIFY_CHUNK_SIZE):
        batch = texts[start:start + CLASSIFY_CHUNK_SIZE]
        predictions = classifier(
            batch,
            batch_size=INFERENCE_BATCH_SIZE,
            truncation=True,
            max_length=MAX_INPUT_TOKENS,
        )
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
        if progress_callback is not None:
            progress_callback(len(results), len(texts))
    return results


def classify_sentiments(
    texts: list[str],
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[dict]:
    """Classify a batch of texts as positive or negative with DistilBERT."""
    return _classify_batch(texts, SENTIMENT_MODEL_NAME, "sentiment", progress_callback)


def classify_sarcasms(
    texts: list[str],
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[dict]:
    """Classify a batch of English texts for sarcasm with a fine-tuned BERT model."""
    return _classify_batch(texts, SARCASM_MODEL_NAME, "sarcasm", progress_callback)


def classify_sentiment(text: str) -> dict:
    """Classify one text with DistilBERT."""
    return classify_sentiments([text])[0]


def classify_sarcasm(text: str) -> dict:
    """Classify one text with the sarcasm transformer."""
    return classify_sarcasms([text])[0]
