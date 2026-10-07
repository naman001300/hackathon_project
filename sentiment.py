"""Local Hugging Face sentiment analysis for customer reviews."""
from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
import re

from themes import detect_themes


# This is a three-way (positive / neutral / negative) classifier.  Keep the
# legacy name below because older API consumers import it directly.
SENTIMENT_MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
GPT_MODEL_NAME = SENTIMENT_MODEL_NAME
REQUEST_BATCH_SIZE = 32
MIN_CONFIDENCE = 0.58
MIN_MARGIN = 0.18
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
        return pipeline(
            "text-classification",
            model=SENTIMENT_MODEL_NAME,
            tokenizer=SENTIMENT_MODEL_NAME,
            device=-1,
        )
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


def _prediction_details(prediction: object) -> tuple[str, float, dict[str, float], float]:
    """Turn the model's full score vector into an auditable sentiment result."""
    rows = prediction if isinstance(prediction, list) else [prediction]
    distribution = {label: 0.0 for label in ("positive", "neutral", "negative")}
    for row in rows:
        if not isinstance(row, dict):
            continue
        label = _normalise_label(str(row.get("label", "neutral")))
        distribution[label] = max(distribution[label], float(row.get("score", 0.0)))

    ranked = sorted(distribution.items(), key=lambda item: item[1], reverse=True)
    label, score = ranked[0]
    margin = score - ranked[1][1]
    return label, round(score, 4), {key: round(value, 4) for key, value in distribution.items()}, round(margin, 4)


def classify_reviews(texts: list[str], progress_callback: Callable[[int, int], None] | None = None) -> list[dict]:
    """Classify reviews with a trained Hugging Face RoBERTa model, locally on this machine."""
    classifier = _sentiment_pipeline()
    results = []
    for start in range(0, len(texts), REQUEST_BATCH_SIZE):
        batch = texts[start:start + REQUEST_BATCH_SIZE]
        try:
            # Asking for every class is essential: a top-label score alone
            # cannot reveal an ambiguous positive-vs-negative prediction.
            predictions = classifier(batch, truncation=True, max_length=512, batch_size=16, top_k=None)
        except Exception as error:
            raise ModelLoadError(f"Hugging Face sentiment analysis failed: {error}") from error
        for text, prediction in zip(batch, predictions):
            sentiment, sentiment_score, distribution, margin = _prediction_details(prediction)
            needs_review = sentiment_score < MIN_CONFIDENCE or margin < MIN_MARGIN
            sentiment_signals = ["RoBERTa full probability distribution"]
            if sentiment_score < MIN_CONFIDENCE:
                sentiment_signals.append("Low model confidence")
            if margin < MIN_MARGIN:
                sentiment_signals.append("Close competing sentiment scores")
            sarcasm, sarcasm_score, sarcasm_signals = _sarcasm_evidence(text)
            results.append({
                "sentiment": sentiment,
                "sentiment_score": sentiment_score,
                "sentiment_distribution": distribution,
                "sentiment_margin": margin,
                "needs_review": needs_review,
                "sentiment_signals": sentiment_signals,
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
