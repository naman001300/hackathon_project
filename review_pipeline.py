from collections import Counter

from pii_logic import redact_pii
from sentiment import classify_sentiment
from themes import detect_themes


def analyze_reviews(reviews: list[dict]) -> dict:
	"""Convert raw review dictionaries into dashboard-ready analysis."""
	analyzed_reviews = []
	invalid_rows = 0
	pii_redacted_count = 0

	for review in reviews:
		review_id = str(review.get("review_id", "")).strip()
		review_text = str(review.get("review_text", "")).strip()
		rating = review.get("rating")

		if not review_id or not review_text:
			invalid_rows += 1
			continue
		if rating is not None and not 1 <= int(rating) <= 5:
			invalid_rows += 1
			continue

		cleaned_text = redact_pii(review_text)
		if cleaned_text != review_text:
			pii_redacted_count += 1

		sentiment = classify_sentiment(cleaned_text)
		themes = detect_themes(cleaned_text)
		analyzed_reviews.append(
			{
				"review_id": review_id,
				"text": cleaned_text,
				"sentiment": sentiment["label"],
				"sentiment_score": sentiment["score"],
				"themes": themes,
				"product": review.get("product"),
				"date": review.get("date"),
			}
		)

	theme_examples = {}
	for review in analyzed_reviews:
		for theme in review["themes"]:
			theme_examples.setdefault(theme, []).append(
				{"review_id": review["review_id"], "text": review["text"]}
			)

	sentiment_counts = Counter(review["sentiment"] for review in analyzed_reviews)
	themes = [
		{
			"name": theme,
			"count": len(examples),
			"examples": examples[:3],
		}
		for theme, examples in sorted(
			theme_examples.items(), key=lambda item: len(item[1]), reverse=True
		)
	]

	return {
		"total_reviews": len(analyzed_reviews),
		"sentiment_summary": {
			"positive": sentiment_counts.get("positive", 0),
			"neutral": sentiment_counts.get("neutral", 0),
			"negative": sentiment_counts.get("negative", 0),
		},
		"themes": themes,
		"reviews": analyzed_reviews,
		"quality": {
			"valid_rows": len(analyzed_reviews),
			"invalid_rows": invalid_rows,
			"pii_redacted_count": pii_redacted_count,
		},
	}
