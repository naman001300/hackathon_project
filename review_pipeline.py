"""Privacy-first batch review analytics used by the Streamlit dashboard and API."""
from collections import Counter, defaultdict
from collections.abc import Callable
from datetime import datetime
import math
from typing import Any
from pii_logic import redact_pii
from sentiment import GPT_MODEL_NAME, classify_reviews

SENTIMENTS = ("positive", "neutral", "negative")

def _normalise_date(value: Any) -> str | None:
    if value is None or str(value).strip() == "": return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y %H:%M", "%d-%m-%Y", "%m/%d/%Y"):
        try: return datetime.strptime(str(value).strip(), fmt).strftime("%Y-%m")
        except ValueError: pass
    return None

def _rating(value: Any) -> int | None:
    if value is None or str(value).strip() == "": return None
    try: value = int(float(value))
    except (TypeError, ValueError): return -1
    return value if 1 <= value <= 5 else -1

def _expected_label(rating: int | None) -> str | None:
    return "positive" if rating and rating >= 4 else "negative" if rating and rating <= 2 else "neutral" if rating else None

def _distribution(counts: Counter) -> dict[str, float]:
    total = sum(counts.values())
    return {label: round(counts.get(label, 0) / total, 3) if total else 0.0 for label in SENTIMENTS}

def _js_divergence(first: Counter, second: Counter) -> float:
    p, q = _distribution(first), _distribution(second)
    mid = {key: (p[key] + q[key]) / 2 for key in SENTIMENTS}
    def kl(source): return sum(value * math.log2(value / mid[key]) for key, value in source.items() if value)
    return round((kl(p) + kl(q)) / 2, 3)

def analyze_reviews(
    reviews: list[dict],
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> dict:
    """Create dashboard-ready analysis, keeping every output traceable to its source review."""
    prepared, invalid_rows, pii_redacted = [], 0, 0
    examples, sarcasm_examples, by_month = defaultdict(list), [], defaultdict(Counter)
    labelled_total = labelled_correct = 0
    for index, review in enumerate(reviews, 1):
        review_id = str(review.get("review_id") or index).strip()
        raw = str(review.get("review_text") or "").strip()
        rating = _rating(review.get("rating"))
        if not raw or rating == -1:
            invalid_rows += 1; continue
        text = redact_pii(raw)
        pii_redacted += text != raw
        expected = str(review.get("sentiment_label") or "").lower().strip() or _expected_label(rating)
        prepared.append({
            "review_id": review_id,
            "text": text,
            "rating": rating,
            "product": review.get("product"),
            "date": _normalise_date(review.get("date")),
            "expected": expected,
        })

    texts = [review["text"] for review in prepared]
    if progress_callback is not None:
        progress_callback("gpt", 0, len(texts))
    classifications = classify_reviews(
        texts,
        progress_callback=(
            lambda completed, total: progress_callback("gpt", completed, total)
            if progress_callback is not None
            else None
        ),
    )
    analyzed = []

    for review, classification in zip(prepared, classifications):
        review_id, text = review["review_id"], review["text"]
        matches = {theme: ["Hugging Face RoBERTa / theme match"] for theme in classification.get("themes", ["other"])}
        month, rating = review["date"], review["rating"]
        expected = review["expected"]
        sentiment_signals = list(classification.get("sentiment_signals", ["RoBERTa sentiment classifier"]))
        needs_review = bool(classification.get("needs_review", False))
        # A star rating is not used to overwrite the model.  It is useful
        # evidence, though: a disagreement deserves a human look rather than
        # being quietly presented as a certain AI verdict.
        rating_sentiment = _expected_label(rating)
        if rating_sentiment and rating_sentiment != classification["sentiment"]:
            needs_review = True
            sentiment_signals.append(f"Rating/model conflict ({rating}-star suggests {rating_sentiment})")
        if expected in SENTIMENTS:
            labelled_total += 1; labelled_correct += classification["sentiment"] == expected
        sarcasm_signals = classification.get("sarcasm_signals", [])
        item = {"review_id": review_id, "text": text, "sentiment": classification["sentiment"], "sentiment_score": classification["sentiment_score"], "sentiment_distribution": classification.get("sentiment_distribution", {}), "sentiment_margin": classification.get("sentiment_margin"), "needs_review": needs_review, "sentiment_signals": sentiment_signals, "sarcasm": classification["sarcasm"], "sarcasm_score": classification["sarcasm_score"], "sarcasm_signals": sarcasm_signals, "themes": list(matches), "theme_signals": matches, "rating": rating, "product": review["product"], "date": month, "model": GPT_MODEL_NAME}
        analyzed.append(item)
        if month: by_month[month][classification["sentiment"]] += 1
        for theme, signals in matches.items(): examples[theme].append({"review_id": review_id, "text": text, "signals": signals, "sentiment": classification["sentiment"], "sarcasm": classification["sarcasm"]})
        if classification["sarcasm"] == "sarcastic":
            sarcasm_examples.append({"review_id": review_id, "text": text, "signals": sarcasm_signals, "sentiment": classification["sentiment"], "sarcasm": classification["sarcasm"], "sarcasm_score": classification["sarcasm_score"]})
    counts, months = Counter(row["sentiment"] for row in analyzed), sorted(by_month)
    trend = [{"month": month, **{label: by_month[month].get(label, 0) for label in SENTIMENTS}} for month in months]
    midpoint = max(1, len(months) // 2); baseline, recent = Counter(), Counter()
    for month in months[:midpoint]: baseline.update(by_month[month])
    for month in months[midpoint:]: recent.update(by_month[month])
    drift = _js_divergence(baseline, recent) if len(months) > 1 else None
    return {"total_reviews": len(analyzed), "sentiment_summary": _distribution(counts), "sentiment_counts": {label: counts.get(label, 0) for label in SENTIMENTS}, "themes": [{"name": theme, "count": len(rows), "examples": rows[:3]} for theme, rows in sorted(examples.items(), key=lambda pair: (-len(pair[1]), pair[0]))], "sarcasm_examples": sarcasm_examples[:3], "reviews": analyzed, "trend": trend, "validation": {"labelled_sample_size": labelled_total, "accuracy": round(labelled_correct / labelled_total, 3) if labelled_total else None, "correct": labelled_correct}, "drift": {"score": drift, "status": "Not enough dated reviews" if drift is None else "Watch" if drift >= 0.1 else "Stable", "baseline": _distribution(baseline), "recent": _distribution(recent)}, "quality": {"valid_rows": len(analyzed), "invalid_rows": invalid_rows, "pii_redacted_count": pii_redacted, "needs_human_review": sum(row["needs_review"] for row in analyzed)}}
