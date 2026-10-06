from review_pipeline import analyze_reviews
from sentiment import classify_sentiment, classify_sarcasm


def test_sentiment_uses_bert_classifier_when_available():
    result = classify_sentiment("I love this app")
    assert result["model"] == "distilbert-base-uncased-finetuned-sentiment"
    assert result["model_status"] in {"online", "unavailable"}
    assert result["score"] >= 0.0
    assert result["score"] <= 1.0


def test_sarcasm_is_detected_with_bert_or_fallback():
    sarcastic = classify_sarcasm("Great, another update that makes everything worse")
    assert sarcastic["label"] == "sarcastic"
    assert sarcastic["model"] == "cardiffnlp/twitter-roberta-base-sarcasm"
    assert sarcastic["model_status"] in {"online", "fallback"}
    assert 0.0 <= sarcastic["score"] <= 1.0

    neutral = classify_sarcasm("The update made everything worse")
    assert neutral["label"] == "not_sarcastic"


def test_pipeline_redacts_and_tracks_evidence():
    result = analyze_reviews([{"review_id": "a", "review_text": "The app crashes. Contact me at jo@example.com or 9876543210", "rating": 1, "date": "2026-01-01"}])
    assert result["total_reviews"] == 1
    assert result["quality"]["pii_redacted_count"] == 1
    assert "EMAIL REDACTED" in result["reviews"][0]["text"]
    assert "reliability" in result["reviews"][0]["themes"]

def test_pipeline_rejects_bad_rows_and_exposes_drift():
    result = analyze_reviews([
        {"review_text": "great app", "rating": 5, "date": "2026-01-02"},
        {"review_text": "broken app", "rating": 1, "date": "2026-02-02"},
        {"review_text": "bad rating", "rating": 7},
    ])
    assert result["quality"]["invalid_rows"] == 1
    assert result["drift"]["score"] is not None
    assert result["validation"]["labelled_sample_size"] == 2
