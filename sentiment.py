"""Fast, local review classification with no model download or API key."""
from __future__ import annotations

from collections.abc import Callable
import re


GPT_MODEL_NAME = "local-review-classifier-v1"
REQUEST_BATCH_SIZE = 1000

POSITIVE = {"amazing", "awesome", "best", "brilliant", "easy", "excellent", "fast", "good", "great", "helpful", "improve", "improved", "love", "loved", "nice", "perfect", "recommend", "smooth", "useful", "wonderful"}
NEGATIVE = {"annoying", "awful", "bad", "broken", "bug", "bugs", "can't", "cannot", "crash", "crashes", "crashing", "disappointing", "error", "fail", "failed", "freezes", "hate", "issue", "lag", "poor", "problem", "refund", "scam", "slow", "terrible", "useless", "worse", "worst"}
SARCASM_MARKERS = {"as if", "brilliantly broken", "congratulations", "emotional damage", "fantastic job", "great job", "just what i needed", "love that", "nice job", "obviously", "perfectly useless", "what a joke", "wow"}
EXPECTATION_WORDS = {"expected", "expecting", "thought", "hoped"}
REVERSAL_WORDS = {"but", "got", "instead", "rather"}
WORD = re.compile(r"[a-z]+(?:'[a-z]+)?")


class ModelLoadError(RuntimeError):
    """Compatibility error type for the app's analysis boundary."""


def _classify(text: str) -> dict:
    lowered = text.lower()
    words = WORD.findall(lowered)
    positive = sum(word in POSITIVE for word in words)
    negative = sum(word in NEGATIVE for word in words)
    # Negation reverses the closest positive word in common review phrasing.
    negative += sum(1 for index, word in enumerate(words[:-1]) if word in {"not", "never", "no"} and words[index + 1] in POSITIVE)
    if positive > negative:
        sentiment, confidence = "positive", min(.99, .55 + .1 * (positive - negative))
    elif negative > positive:
        sentiment, confidence = "negative", min(.99, .55 + .1 * (negative - positive))
    else:
        sentiment, confidence = "neutral", .5

    marker_match = any(marker in lowered for marker in SARCASM_MARKERS)
    expectation_reversal = bool(set(words) & EXPECTATION_WORDS) and bool(set(words) & REVERSAL_WORDS) and negative > 0
    # Praise for a destructive action is a common review-sarcasm construction:
    # "the uninstall button is the most reliable feature."
    destructive_praise = bool({"uninstall", "delete", "remove"} & set(words)) and bool({"best", "only", "reliable", "feature"} & set(words))
    sarcastic = marker_match or expectation_reversal or destructive_praise
    sarcasm_score = .96 if sarcastic and (expectation_reversal or destructive_praise) else .88 if sarcastic else .08
    return {"sentiment": sentiment, "sentiment_score": round(confidence, 4), "sarcasm": "sarcastic" if sarcastic else "not_sarcastic", "sarcasm_score": sarcasm_score}


def classify_reviews(texts: list[str], progress_callback: Callable[[int, int], None] | None = None) -> list[dict]:
    """Classify reviews locally in bounded chunks so large uploads stay responsive."""
    results = []
    for start in range(0, len(texts), REQUEST_BATCH_SIZE):
        results.extend(_classify(text) for text in texts[start:start + REQUEST_BATCH_SIZE])
        if progress_callback:
            progress_callback(len(results), len(texts))
    return results


def classify_sentiments(texts: list[str], progress_callback: Callable[[int, int], None] | None = None) -> list[dict]:
    return [{"label": item["sentiment"], "score": item["sentiment_score"], "signals": ["local classification"], "model": GPT_MODEL_NAME, "model_status": "local", "model_used": GPT_MODEL_NAME} for item in classify_reviews(texts, progress_callback)]


def classify_sarcasms(texts: list[str], progress_callback: Callable[[int, int], None] | None = None) -> list[dict]:
    return [{"label": item["sarcasm"], "score": item["sarcasm_score"], "signals": [], "model": GPT_MODEL_NAME, "model_status": "local", "model_used": GPT_MODEL_NAME} for item in classify_reviews(texts, progress_callback)]


def classify_sentiment(text: str) -> dict:
    return classify_sentiments([text])[0]


def classify_sarcasm(text: str) -> dict:
    return classify_sarcasms([text])[0]
