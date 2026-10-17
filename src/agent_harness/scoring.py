from pathlib import Path


def _file_name(path):
    return Path(str(path).replace("\\", "/")).name


def score_findings(expected, accepted):
    """
    Score accepted findings against labeled ground truth.

    Matching rule: category + file basename.
    Each expected issue can match at most one accepted finding.
    Unmatched accepted findings count as false positives under
    this benchmark's closed-world labeling assumption.
    """
    unmatched_expected = list(expected)
    true_positives = 0
    false_positives = 0

    for finding in accepted:
        category = finding.get("category")
        file_name = _file_name(
            finding.get("file_path", finding.get("file", ""))
        )

        match_index = next(
            (
                i for i, truth in enumerate(unmatched_expected)
                if truth.get("category") == category
                and _file_name(truth.get("file", "")) == file_name
            ),
            None,
        )

        if match_index is None:
            false_positives += 1
        else:
            true_positives += 1
            unmatched_expected.pop(match_index)

    false_negatives = len(unmatched_expected)

    precision = (
        true_positives / (true_positives + false_positives)
        if true_positives + false_positives else 0.0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if true_positives + false_negatives else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }
