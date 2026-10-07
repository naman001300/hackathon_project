"""Local Hugging Face sentiment analysis for customer reviews."""
from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
import re

from themes import detect_themes


GPT_MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
REQUEST_BATCH_SIZE = 32
SARCASM_MARKERS = {"as if", "brilliantly broken", "congratulations", "emotional damage", "fantastic job", "great job", "just what i needed", "love that", "nice job", "obviously", "perfectly useless", "what a joke", "wow"}
EXPECTATION_WORDS = {"expected", "expecting", "thought", "hoped"}
REVERSAL_WORDS = {"but", "got", "instead", "rather"}
WORD = re.compile(r"[a-z]+(?:'[a-z]+)?")


class ModelLoadError(RuntimeError):
    """Raised when the local Hugging Face model cannot be loaded."""


@lru_cache(maxsize=1)
def _sentiment_pipeline():
    """Load the trained model once; the first analysis downloads it from Hugging Face."""
    try:
        from transformers import pipeline
        return pipeline("text-classification", model=GPT_MODEL_NAME, tokenizer=GPT_MODEL_NAME, device=-1)
    except Exception as error:
        raise ModelLoadError(
            "Could not load the Hugging Face sentiment model. Ensure internet access for the first download "
            "and run: python3 -m pip install -r requirements.txt"
        ) from error


def _sarcasm_evidence(text: str) -> tuple[str, float, list[str]]:
    """Classify sarcasm and preserve the rule(s) that triggered the label."""
    lowered = text.lower()
    words = set(WORD.findall(lowered))
    matched_markers = sorted(marker for marker in SARCASM_MARKERS if marker in lowered)
    marker_match = bool(matched_markers)
    expectation_reversal = bool(words & EXPECTATION_WORDS) and bool(words & REVERSAL_WORDS)
    destructive_praise = bool({"uninstall", "delete", "remove"} & words) and bool({"best", "only", "reliable", "feature"} & words)
    sarcastic = marker_match or expectation_reversal or destructive_praise
    score = .96 if sarcastic and (expectation_reversal or destructive_praise) else .88 if sarcastic else .08
    signals = [f'Marker: "{marker}"' for marker in matched_markers]
    if expectation_reversal:
        signals.append("Expectation reversal")
    if destructive_praise:
        signals.append("Destructive praise")
    return ("sarcastic" if sarcastic else "not_sarcastic", score, signals)


def _sarcasm(text: str) -> tuple[str, float]:
    """Backward-compatible compact sarcasm result."""
    label, score, _ = _sarcasm_evidence(text)
    return label, score


def _normalise_label(label: str) -> str:
    value = label.lower().strip()
    if value in {"negative", "label_0"}: return "negative"
    if value in {"neutral", "label_1"}: return "neutral"
    if value in {"positive", "label_2"}: return "positive"
    return "neutral"


def classify_reviews(texts: list[str], progress_callback: Callable[[int, int], None] | None = None) -> list[dict]:
    """Classify reviews with a trained Hugging Face RoBERTa model, locally on this machine."""
    classifier = _sentiment_pipeline()
    results = []
    for start in range(0, len(texts), REQUEST_BATCH_SIZE):
        batch = texts[start:start + REQUEST_BATCH_SIZE]
        try:
            predictions = classifier(batch, truncation=True, max_length=512, batch_size=16)
        except Exception as error:
            raise ModelLoadError(f"Hugging Face sentiment analysis failed: {error}") from error
        for text, prediction in zip(batch, predictions):
            sarcasm, sarcasm_score, sarcasm_signals = _sarcasm_evidence(text)
            results.append({
                "sentiment": _normalise_label(str(prediction.get("label", "neutral"))),
                "sentiment_score": round(float(prediction.get("score", .5)), 4),
                "sarcasm": sarcasm,
                "sarcasm_score": sarcasm_score,
                "sarcasm_signals": sarcasm_signals,
                "themes": list(detect_themes(text)),
            })
        if progress_callback:
            progress_callback(len(results), len(texts))
    return results


def classify_sentiments(texts: list[str], progress_callback: Callable[[int, int], None] | None = None) -> list[dict]:
    return [{"label": item["sentiment"], "score": item["sentiment_score"], "signals": ["Hugging Face RoBERTa"], "model": GPT_MODEL_NAME, "model_status": "local_huggingface", "model_used": GPT_MODEL_NAME} for item in classify_reviews(texts, progress_callback)]


def classify_sarcasms(texts: list[str], progress_callback: Callable[[int, int], None] | None = None) -> list[dict]:
    return [{"label": item["sarcasm"], "score": item["sarcasm_score"], "signals": ["Sarcasm heuristic"], "model": GPT_MODEL_NAME, "model_status": "local_huggingface", "model_used": GPT_MODEL_NAME} for item in classify_reviews(texts, progress_callback)]


def classify_sentiment(text: str) -> dict:
    return classify_sentiments([text])[0]


def classify_sarcasm(text: str) -> dict:
    return classify_sarcasms([text])[0]
