import pytest
from pydantic import ValidationError
from agent_harness.schemas import Finding, FindingCategory, Severity, Role

def test_finding_rejects_bad_confidence():
    with pytest.raises(ValidationError):
        Finding(finding_id="x", category=FindingCategory.security, severity=Severity.high, title="bad issue",
          file_path="x.py", start_line=1, end_line=1, evidence="x", explanation="some explanation",
          recommended_fix="fix it", confidence=2, specialist=Role.security)
