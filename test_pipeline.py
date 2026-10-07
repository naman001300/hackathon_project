from unittest.mock import patch

from review_pipeline import analyze_reviews
from sentiment import _prediction_details, classify_reviews
from streamlit.testing.v1 import AppTest


def _labels(texts, progress_callback=None):
    rows = []
    for index, text in enumerate(texts):
        negative = any(word in text.lower() for word in ("broken", "crash", "slow", "bad"))
        rows.append({"id": index, "sentiment": "negative" if negative else "positive", "sentiment_score": .95, "sarcasm": "not_sarcastic", "sarcasm_score": .9})
    if progress_callback:
        progress_callback(len(texts), len(texts))
    return rows


def test_full_probability_vector_keeps_ambiguous_predictions_auditable():
    label, score, distribution, margin = _prediction_details([
        {"label": "LABEL_0", "score": .41},
        {"label": "LABEL_1", "score": .18},
        {"label": "LABEL_2", "score": .41},
    ])
    assert label == "positive"
    assert score == .41
    assert distribution == {"positive": .41, "neutral": .18, "negative": .41}
    assert margin == 0


def test_classifier_flags_close_model_scores_for_human_review():
    with patch("sentiment._sentiment_pipeline", return_value=lambda *_args, **_kwargs: [[
        {"label": "LABEL_0", "score": .45},
        {"label": "LABEL_1", "score": .12},
        {"label": "LABEL_2", "score": .43},
    ]]):
        result = classify_reviews(["I guess it is okay."])[0]
    assert result["sentiment"] == "negative"
    assert result["needs_review"] is True
    assert "Close competing sentiment scores" in result["sentiment_signals"]


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
    assert "other" in result["reviews"][0]["themes"]


def test_pipeline_keeps_sarcastic_reviews_in_dedicated_evidence():
    with patch("review_pipeline.classify_reviews", return_value=[{
        "sentiment": "negative", "sentiment_score": .95,
        "sarcasm": "sarcastic", "sarcasm_score": .96,
        "sarcasm_signals": ["Expectation reversal"], "themes": ["reliability"],
    }]):
        result = analyze_reviews([{"review_id": "sarcasm-1", "review_text": "Great, I expected it to work but it crashes.", "rating": 1}])
    assert result["sarcasm_examples"][0]["review_id"] == "sarcasm-1"
    assert result["sarcasm_examples"][0]["signals"] == ["Expectation reversal"]


def test_pipeline_flags_rating_model_conflict_without_overwriting_the_model():
    with patch("review_pipeline.classify_reviews", return_value=[{
        "sentiment": "positive", "sentiment_score": .91,
        "sentiment_distribution": {"positive": .91, "neutral": .06, "negative": .03},
        "sentiment_margin": .85, "needs_review": False,
        "sentiment_signals": ["RoBERTa full probability distribution"],
        "sarcasm": "not_sarcastic", "sarcasm_score": .08, "sarcasm_signals": [], "themes": ["other"],
    }]):
        result = analyze_reviews([{"review_text": "Amazing", "rating": 1}])
    review = result["reviews"][0]
    assert review["sentiment"] == "positive"
    assert review["needs_review"] is True
    assert "Rating/model conflict (1-star suggests negative)" in review["sentiment_signals"]


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
