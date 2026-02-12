from finsentiment.processors.deduplicator import Deduplicator


def test_process_removes_duplicates():
    dedup = Deduplicator(capacity=10)
    items = [
        {"source": "reuters", "title": "A", "link": "u1", "summary": "s"},
        {"source": "reuters", "title": "A", "link": "u1", "summary": "s"},
        {"source": "reuters", "title": "B", "link": "u2", "summary": "s"},
    ]

    unique = dedup.process(items)
    assert len(unique) == 2
    assert unique[0]["title"] == "A"
    assert unique[1]["title"] == "B"


def test_capacity_window_allows_reappearance_after_eviction():
    dedup = Deduplicator(capacity=2)
    a = {"source": "x", "title": "A", "link": "1", "summary": ""}
    b = {"source": "x", "title": "B", "link": "2", "summary": ""}
    c = {"source": "x", "title": "C", "link": "3", "summary": ""}

    assert dedup.is_duplicate(a) is False
    assert dedup.is_duplicate(b) is False
    assert dedup.is_duplicate(c) is False
    assert dedup.is_duplicate(a) is False
