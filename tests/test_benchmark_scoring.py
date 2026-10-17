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


def test_matches_same_issue_when_category_differs():
    expected = [{
        "category": "correctness",
        "file": "app.py",
        "description": "Empty list causes IndexError in first_item",
    }]
    accepted = [{
        "category": "maintainability",
        "file_path": "src/app.py",
        "title": "Potential edge case not handled",
        "explanation": "Empty input could lead to IndexError.",
        "evidence": "return items[0]",
    }]

    result = score_findings(expected, accepted)

    assert result["true_positives"] == 1
    assert result["false_positives"] == 0
    assert result["false_negatives"] == 0


def test_same_file_and_category_do_not_match_unrelated_issue():
    expected = [{
        "category": "correctness",
        "file": "app.py",
        "description": "Empty list causes IndexError in first_item",
    }]
    accepted = [{
        "category": "correctness",
        "file_path": "app.py",
        "title": "Function has no documentation",
        "explanation": "The public API needs a docstring.",
        "evidence": "def first_item(items):",
    }]

    result = score_findings(expected, accepted)

    assert result["true_positives"] == 0
    assert result["false_positives"] == 1
    assert result["false_negatives"] == 1
