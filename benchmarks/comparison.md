# Benchmark comparison

Results are scored against samples/ground_truth.json. Only accepted findings count as detections. Matching uses category and file basename, so these are approximate benchmark metrics, not proof of semantic correctness. Unlisted legitimate issues may be counted as false positives.

| Task | Approach | Status | Accepted | TP | FP | FN | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| task_1 | multi_agent | completed | 1 | 1 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| task_1 | single_agent_baseline | completed | 1 | 1 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| task_2 | multi_agent | completed | 1 | 1 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| task_2 | single_agent_baseline | completed | 1 | 1 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| task_3 | multi_agent | completed | 1 | 1 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| task_3 | single_agent_baseline | completed | 1 | 1 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |

## Interpretation

- TP: accepted finding matched an expected issue.
- FP: accepted finding did not match an unmatched expected issue.
- FN: expected issue not detected by an accepted finding.
- Precision = TP / (TP + FP); recall = TP / (TP + FN).
- F1 is the harmonic mean of precision and recall.
- Mock-mode results test workflow mechanics, not model quality.
