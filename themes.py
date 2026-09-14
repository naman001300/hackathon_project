THEME_KEYWORDS = {
	"delivery": {"delivery", "shipping", "late", "arrived", "courier"},
	"payment": {"payment", "card", "transaction", "refund", "checkout"},
	"quality": {"quality", "broken", "defect", "damaged", "poor"},
	"support": {"support", "agent", "help", "complaint", "service"},
	"price": {"price", "cost", "expensive", "cheap", "discount"},
	"usability": {"confusing", "easy", "difficult", "interface", "app"},
}


def detect_themes(text: str) -> list[str]:
	words = {word.strip(".,!?;:()[]{}\"").lower() for word in text.split()}
	detected = [
		theme for theme, keywords in THEME_KEYWORDS.items() if words & keywords
	]
	return detected or ["other"]
