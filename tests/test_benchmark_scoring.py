from agent_harness.scoring import score_findings


def test_all_ground_truth_issues_found():
    expected = [
        {"id": "T1-1", "category": "correctness", "file": "app.py"},
    ]
    accepted = [
        {"category": "correctness", "file_path": "app.py"},
    ]

    result = score_findings(expected, accepted)

    assert result["true_positives"] == 1
    assert result["false_positives"] == 0
    assert result["false_negatives"] == 0
    assert result["precision"] == 1.0
    assert result["recall"] == 1.0
    assert result["f1"] == 1.0


def test_missing_ground_truth_issue():
    expected = [
        {"id": "T1-1", "category": "correctness", "file": "app.py"},
    ]

    result = score_findings(expected, [])

    assert result["true_positives"] == 0
    assert result["false_negatives"] == 1
    assert result["recall"] == 0.0


def test_duplicate_matches_do_not_inflate_true_positives():
    expected = [
        {"id": "T1-1", "category": "correctness", "file": "app.py"},
    ]
    accepted = [
        {"category": "correctness", "file_path": "app.py"},
        {"category": "correctness", "file_path": "src/app.py"},
    ]

    result = score_findings(expected, accepted)

    assert result["true_positives"] == 1
    assert result["false_positives"] == 1
    assert result["false_negatives"] == 0
    assert result["precision"] == 0.5


def test_unmatched_finding_is_false_positive():
    expected = [
        {"id": "T1-1", "category": "correctness", "file": "app.py"},
    ]
    accepted = [
        {"category": "security", "file_path": "app.py"},
    ]

    result = score_findings(expected, accepted)

    assert result["true_positives"] == 0
    assert result["false_positives"] == 1
    assert result["false_negatives"] == 1
