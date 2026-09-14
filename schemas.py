from dataclasses import dataclass


@dataclass
class Review:
	review_id: str
	review_text: str
	rating: int | None = None
	product: str | None = None
	date: str | None = None
