# Ground-truth evaluation

Scores are computed by matching accepted findings to the labels in `ground_truth.json`.
Matching uses file basename, category, and a configurable line tolerance.
These labels cover only the currently known sample issues; they do not measure every possible issue.
Mock-mode results test deterministic mechanics, not real LLM quality.

| Approach | Runs scored | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| multi_agent | 3 | 2 | 2 | 1 | 0.500 | 0.667 | 0.571 |
| single_agent_baseline | 3 | 0 | 0 | 3 | 0.000 | 0.000 | 0.000 |

## Per-task results

| Task | Approach | TP | FP | FN | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| task_1 | multi_agent | 1 | 1 | 0 | 0.500 | 1.000 | 0.667 |
| task_1 | single_agent_baseline | 0 | 0 | 1 | 0.000 | 0.000 | 0.000 |
| task_2 | multi_agent | 1 | 1 | 0 | 0.500 | 1.000 | 0.667 |
| task_2 | single_agent_baseline | 0 | 0 | 1 | 0.000 | 0.000 | 0.000 |
| task_3 | multi_agent | 0 | 0 | 1 | 0.000 | 0.000 | 0.000 |
| task_3 | single_agent_baseline | 0 | 0 | 1 | 0.000 | 0.000 | 0.000 |

## Interpretation

- A true positive (TP) is an accepted finding matched to a ground-truth label.
- A false positive (FP) is an accepted finding that did not match a label.
- A false negative (FN) is a ground-truth label with no matching accepted finding.
- A score of zero can mean the approach missed all current labels; it does not prove it is generally ineffective.
- Review and expand the ground-truth labels whenever the sample code changes.
