from review_pipeline import analyze_reviews

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
