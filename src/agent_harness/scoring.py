import re
from pathlib import Path


STOPWORDS = {
    "the", "a", "an", "and", "or", "in", "on", "to", "of",
    "for", "is", "are", "be", "with", "when", "may", "can",
    "could", "does", "not", "this", "that", "it", "from",
    "function", "potential", "issue", "code", "use",
}

DISTINCTIVE_TERMS = {
    "indexerror", "eval", "injection", "sql", "xss",
    "traceback", "deadlock", "overflow", "underflow",
}


def _file_name(path):
    return Path(str(path or "").replace("\\", "/")).name


def _text(item, expected=False):
    """Build searchable text from the issue description and finding."""
    fields = (
        ("description", "category", "file")
        if expected
        else ("title", "explanation", "evidence", "recommended_fix")
    )
    return " ".join(str(item.get(key, "")) for key in fields).lower()


def _tokens(text):
    return {
        token for token in re.findall(r"[a-z][a-z0-9_]*", text.lower())
        if len(token) > 2 and token not in STOPWORDS
    }


def _is_match(truth, finding):
    truth_file = _file_name(truth.get("file", truth.get("file_path", "")))
    finding_file = _file_name(
        finding.get("file_path", finding.get("file", ""))
    )

    if not truth_file or truth_file != finding_file:
        return False

    expected_text = _text(truth, expected=True)
    finding_text = _text(finding)

    expected_tokens = _tokens(expected_text)
    finding_tokens = _tokens(finding_text)
    overlap = expected_tokens & finding_tokens

    # Preserve compatibility with minimal test fixtures that have no
    # descriptions or issue-specific text.
    if not expected_tokens or not finding_tokens:
        return truth.get("category") == finding.get("category")

    # Exact category is supporting evidence, not proof that two issues
    # are the same. Require issue-specific textual overlap.
    if len(overlap) >= 2:
        return True

    return bool(overlap & DISTINCTIVE_TERMS)


def score_findings(expected, accepted):
    """
    Approximate scoring using filename and issue-text overlap.

    Each expected issue can match at most one accepted finding.
    This lexical matcher is not a substitute for human semantic review.
    Unmatched accepted findings count as false positives.
    """
    unmatched_expected = list(expected)
    true_positives = 0
    false_positives = 0

    for finding in accepted:
        match_index = next(
            (
                i for i, truth in enumerate(unmatched_expected)
                if _is_match(truth, finding)
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
