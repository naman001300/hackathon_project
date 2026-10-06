from unittest.mock import patch

from review_pipeline import analyze_reviews
from sentiment import GPT_MODEL_NAME, classify_reviews
from streamlit.testing.v1 import AppTest


def _labels(texts, progress_callback=None):
    rows = []
    for index, text in enumerate(texts):
        negative = any(word in text.lower() for word in ("broken", "crash", "slow", "bad"))
        rows.append({"id": index, "sentiment": "negative" if negative else "positive", "sentiment_score": .95, "sarcasm": "not_sarcastic", "sarcasm_score": .9})
    if progress_callback:
        progress_callback(len(texts), len(texts))
    return rows


def test_local_classifier_returns_labels_for_every_review():
    result = classify_reviews(["I love this app", "The login is broken and slow"])
    assert result[0]["sentiment"] == "positive"
    assert result[1]["sentiment"] == "negative"
    assert GPT_MODEL_NAME == "local-review-classifier-v1"


def test_detects_expectation_reversal_and_uninstall_sarcasm():
    review = "Downloaded this app expecting convenience. Got confusion, crashes, endless loading, and emotional damage instead. At this point, the uninstall button is the most reliable feature."
    result = classify_reviews([review])[0]
    assert result["sentiment"] == "negative"
    assert result["sarcasm"] == "sarcastic"
    assert result["sarcasm_score"] >= .9


def test_app_defaults_home_without_analysis_data():
    app = AppTest.from_file("app.py", default_timeout=30).run()
    assert not app.exception
    assert app.segmented_control[0].value == "Home"
    assert not app.metric
    assert not app.text_area
    assert not app.file_uploader


def test_app_analyzes_multiple_pasted_reviews():
    with patch("review_pipeline.classify_reviews", side_effect=_labels):
        app = AppTest.from_file("app.py", default_timeout=30).run()
        app.segmented_control[0].set_value("Analyze").run()
        app.text_area[0].set_value("The app is brilliant and easy to use.\n\nThis app is broken and painfully slow.")
        app.button(key="FormSubmitter:paste_reviews_form-Analyze pasted reviews").click().run()
    assert not app.exception
    assert any("2 reviews processed" in item.value for item in app.markdown)


def test_pipeline_redacts_and_tracks_evidence():
    with patch("review_pipeline.classify_reviews", side_effect=_labels):
        result = analyze_reviews([{"review_id": "a", "review_text": "The app crashes. Contact me at jo@example.com or 9876543210", "rating": 1, "date": "2026-01-01"}])
    assert result["total_reviews"] == 1
    assert result["quality"]["pii_redacted_count"] == 1
    assert "EMAIL REDACTED" in result["reviews"][0]["text"]
    assert "reliability" in result["reviews"][0]["themes"]


def test_pipeline_rejects_bad_rows_and_exposes_drift():
    progress = []
    with patch("review_pipeline.classify_reviews", side_effect=_labels):
        result = analyze_reviews(
            [{"review_text": "great app", "rating": 5, "date": "2026-01-02"}, {"review_text": "broken app", "rating": 1, "date": "2026-02-02"}, {"review_text": "bad rating", "rating": 7}],
            progress_callback=lambda phase, completed, total: progress.append((phase, completed, total)),
        )
    assert result["quality"]["invalid_rows"] == 1
    assert result["drift"]["score"] is not None
    assert result["validation"]["labelled_sample_size"] == 2
    assert progress == [("gpt", 0, 2), ("gpt", 2, 2)]
