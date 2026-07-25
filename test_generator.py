import pytest
from shorts_generator.highlights import (
    _sanitize_highlights,
    _coerce_float,
    _coerce_int,
    dedupe_highlights,
    build_transcript_text,
)

def test_coerce_float():
    assert _coerce_float("123.4") == 123.4
    assert _coerce_float(5) == 5.0
    assert _coerce_float("abc", default=2.5) == 2.5

def test_coerce_int():
    assert _coerce_int("123") == 123
    assert _coerce_int(5.5) == 5
    assert _coerce_int("abc", default=10) == 10

def test_sanitize_highlights():
    raw_highlights = [
        {
            "title": "Test Highlight",
            "start_time": "10.0",
            "end_time": "25.0",
            "score": "85",
            "hook_sentence": "Hook",
            "virality_reason": "Reason",
        },
        {
            "title": "Invalid Highlight",
            "start_time": "40.0",
            "end_time": "30.0",  # start_time > end_time
            "score": "50",
        },
    ]
    cleaned = _sanitize_highlights(raw_highlights, duration=100)
    assert len(cleaned) == 1
    assert cleaned[0]["title"] == "Test Highlight"
    assert cleaned[0]["start_time"] == 10.0
    assert cleaned[0]["end_time"] == 25.0
    assert cleaned[0]["score"] == 85

def test_dedupe_highlights():
    # Highlight 2 overlaps significantly with Highlight 1 but has a lower score
    highlights = [
        {
            "title": "Highlight 1 (high score)",
            "start_time": 10.0,
            "end_time": 30.0,
            "score": 90,
        },
        {
            "title": "Highlight 2 (overlaps H1, lower score)",
            "start_time": 15.0,
            "end_time": 25.0,
            "score": 75,
        },
        {
            "title": "Highlight 3 (no overlap)",
            "start_time": 50.0,
            "end_time": 70.0,
            "score": 80,
        },
    ]

    deduped = dedupe_highlights(highlights)
    assert len(deduped) == 2
    titles = [h["title"] for h in deduped]
    assert "Highlight 1 (high score)" in titles
    assert "Highlight 3 (no overlap)" in titles
    assert "Highlight 2 (overlaps H1, lower score)" not in titles

def test_build_transcript_text():
    transcript = {
        "segments": [
            {"start": 0.0, "end": 2.0, "text": "Hello world"},
            {"start": 2.5, "end": 5.0, "text": "This is a test"},
        ]
    }
    text = build_transcript_text(transcript)
    assert "[0.0s] Hello world" in text
    assert "[2.5s] This is a test" in text
