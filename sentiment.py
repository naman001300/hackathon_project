POSITIVE_WORDS = {
	"amazing",
	"excellent",
	"fast",
	"good",
	"great",
	"helpful",
	"love",
	"perfect",
	"smooth",
	"satisfied",
}

NEGATIVE_WORDS = {
	"bad",
	"broken",
	"confusing",
	"delay",
	"failed",
	"late",
	"poor",
	"slow",
	"terrible",
	"unhelpful",
}


def classify_sentiment(text: str) -> dict[str, str | float]:
	"""Return a small, explainable sentiment result for one review."""
	words = {word.strip(".,!?;:()[]{}\"").lower() for word in text.split()}
	positive_count = len(words & POSITIVE_WORDS)
	negative_count = len(words & NEGATIVE_WORDS)
	score = (positive_count - negative_count) / max(
		positive_count + negative_count, 1
	)

	if score > 0:
		label = "positive"
	elif score < 0:
		label = "negative"
	else:
		label = "neutral"

	return {
		"label": label,
		"score": round(score, 2),
	}
