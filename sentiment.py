"""Small, explainable lexicon sentiment model suitable for an offline demo."""
import re

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
	"satisfied", "awesome", "best", "brilliant", "super", "wonderful", "easy", "cool", "genial", "toll", "spitze", "zufrieden",
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
	"unhelpful", "bug", "bugs", "crash", "crashes", "crashed", "useless", "nervig", "fehler", "problem", "probleme", "stürzt", "schlecht",
}


def classify_sentiment(text: str) -> dict:
	"""Return a label, bounded score, and matched words for transparent review."""
	words = re.findall(r"[\w']+", text.lower())
	positive = sorted(set(words) & POSITIVE_WORDS)
	negative = sorted(set(words) & NEGATIVE_WORDS)
	positive_count, negative_count = len(positive), len(negative)
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
		"score": round(score, 2), "signals": positive + negative,
	}
