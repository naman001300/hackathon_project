import re
THEME_KEYWORDS = {
	"reliability": {"crash", "crashes", "crashed", "broken", "bug", "bugs", "working", "works", "stürzt", "funktioniert", "hängen"},
	"performance": {"slow", "delay", "loading", "lag", "fast", "schnell", "lange"},
	"features": {"feature", "features", "wish", "update", "status", "message", "messages", "video", "voice", "photo", "emoji", "notification", "funktion"},
	"usability": {"confusing", "easy", "difficult", "interface", "app", "settings", "design", "klein", "einfach"},
	"support": {"support", "agent", "help", "complaint", "service", "response", "hilfe"},
	"price": {"price", "cost", "expensive", "cheap", "discount", "pay", "paid", "kosten", "geld", "kostenpflichtig"},
	"privacy": {"privacy", "password", "secret", "spionage", "data", "daten", "security"},
}


def detect_themes(text: str) -> dict[str, list[str]]:
	"""Return themes and terms that caused each assignment."""
	words = set(re.findall(r"[\w']+", text.lower()))
	matches = {theme: sorted(words & keywords) for theme, keywords in THEME_KEYWORDS.items() if words & keywords}
	return matches or {"other": []}
