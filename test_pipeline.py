from review_pipeline import analyze_reviews
from sentiment import classify_sentiment, classify_sarcasm
from streamlit.testing.v1 import AppTest


def test_sentiment_uses_distilbert():
    result = classify_sentiment("I love this app")
    assert result["model"] == "distilbert/distilbert-base-uncased-finetuned-sst-2-english"
    assert result["model_used"] == result["model"]
    assert result["model_status"] == "online"
    assert result["label"] == "positive"
    assert result["score"] >= 0.0
    assert result["score"] <= 1.0
    assert classify_sentiment("Amazing, helpful, and wonderful")["label"] == "positive"
    assert classify_sentiment("Broken, slow, and terrible")["label"] == "negative"


def test_sarcasm_uses_english_bert_classifier():
    sarcastic = classify_sarcasm("CIA Realizes It's Been Using Black Highlighters All These Years.")
    assert sarcastic["label"] == "sarcastic"
    assert sarcastic["model"] == "helinivan/english-sarcasm-detector"
    assert sarcastic["model_used"] == sarcastic["model"]
    assert sarcastic["model_status"] == "online"
    assert 0.0 <= sarcastic["score"] <= 1.0

    neutral = classify_sarcasm("The app works well and is easy to use.")
    assert neutral["label"] == "not_sarcastic"


def test_app_defaults_home_without_analysis_data():
    app = AppTest.from_file("app.py", default_timeout=30).run()
    assert not app.exception
    assert app.segmented_control[0].value == "Home"
    assert not app.metric
    assert not app.text_area
    assert not app.file_uploader
    assert app.button[0].label == "Analyze reviews"

    app.segmented_control[0].set_value("Dashboard").run()
    assert not app.exception
    assert not app.metric
    assert any("No review analysis yet" in item.value for item in app.markdown)
    assert app.button[0].label == "Go to Analyze"


def test_app_analyzes_multiple_pasted_reviews():
    app = AppTest.from_file("app.py", default_timeout=120).run()
    app.segmented_control[0].set_value("Analyze").run()
    app.text_area[0].set_value("The app is brilliant and easy to use.\n\nThis app is broken and painfully slow.")
    app.button(key="FormSubmitter:paste_reviews_form-Analyze pasted reviews").click().run()

    assert not app.exception
    assert any("2 reviews processed" in item.value for item in app.markdown)

    app.segmented_control[0].set_value("Dashboard").run()
    assert not app.exception
    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["Reviews analyzed"] == "2"
    assert metrics["Positive"] == "1"
    assert metrics["Negative"] == "1"

    app.segmented_control[0].set_value("Trust").run()
    assert not app.exception
    assert len(app.dataframe) == 1

    app.segmented_control[0].set_value("Drift").run()
    assert not app.exception
    assert any("Add dates to the reviews" in item.value for item in app.info)


def test_pipeline_redacts_and_tracks_evidence():
    result = analyze_reviews([{"review_id": "a", "review_text": "The app crashes. Contact me at jo@example.com or 9876543210", "rating": 1, "date": "2026-01-01"}])
    assert result["total_reviews"] == 1
    assert result["quality"]["pii_redacted_count"] == 1
    assert "EMAIL REDACTED" in result["reviews"][0]["text"]
    assert "reliability" in result["reviews"][0]["themes"]

def test_pipeline_rejects_bad_rows_and_exposes_drift():
    progress = []
    result = analyze_reviews(
        [
            {"review_text": "great app", "rating": 5, "date": "2026-01-02"},
            {"review_text": "broken app", "rating": 1, "date": "2026-02-02"},
            {"review_text": "bad rating", "rating": 7},
        ],
        progress_callback=lambda phase, completed, total: progress.append((phase, completed, total)),
    )
    assert result["quality"]["invalid_rows"] == 1
    assert result["drift"]["score"] is not None
    assert result["validation"]["labelled_sample_size"] == 2
    assert progress == [
        ("sentiment", 0, 2),
        ("sentiment", 2, 2),
        ("sarcasm", 0, 2),
        ("sarcasm", 2, 2),
    ]
