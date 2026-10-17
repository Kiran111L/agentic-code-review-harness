import pytest
from pathlib import Path
from agent_harness.tools import ToolRegistry

def test_evidence_validation(tmp_path):
    root = tmp_path / "p"; root.mkdir()
    (root / "a.py").write_text("x = eval(user_input)\n")
    tools = ToolRegistry(str(root))
    good = {"file_path":"a.py","start_line":1,"end_line":1,"evidence":"x = eval(user_input)"}
    bad = {"file_path":"a.py","start_line":1,"end_line":1,"evidence":"safe operation"}
    assert tools.call("checker","validate_finding",{"finding":good})["valid"]
    assert not tools.call("checker","validate_finding",{"finding":bad})["valid"]


def _make_finding():
    from agent_harness.schemas import Finding, FindingCategory, Role, Severity

    return Finding(
        finding_id="finding-empty-list",
        category=FindingCategory.correctness,
        severity=Severity.high,
        title="Empty list raises IndexError",
        file_path="a.py",
        start_line=2,
        end_line=2,
        evidence="return items[0]",
        explanation="An empty list raises IndexError when indexed.",
        recommended_fix="Check whether the list is empty first.",
        confidence=0.95,
        specialist=Role.bug,
    )


class _FakeBudget:
    async def reserve(self, **kwargs):
        pass


class _FakeTrace:
    def emit(self, *args, **kwargs):
        pass


class _FakeTools:
    def call(self, *args, **kwargs):
        return {"valid": True, "reason": "Evidence matches source."}


class _FakeModel:
    def __init__(self, response):
        self.response = response

    async def complete_json(self, *args, **kwargs):
        self.last_prompt = args[1] if len(args) > 1 else kwargs.get("prompt", "")
        return self.response


@pytest.mark.asyncio
async def test_checker_accepts_explicit_justified_decision():
    from agent_harness.checker import check_findings

    finding = _make_finding()
    model = _FakeModel({
        "decisions": [{
            "finding_id": finding.finding_id,
            "decision": "accept",
            "reason": "Indexing an empty list raises IndexError.",
        }]
    })

    accepted, rejected, error = await check_findings(
        [finding], model, _FakeTools(), _FakeBudget(), _FakeTrace()
    )

    assert error is None
    assert len(accepted) == 1
    assert rejected == []
    assert accepted[0].checker_status == "accepted"


@pytest.mark.asyncio
async def test_checker_rejects_explicit_rejection():
    from agent_harness.checker import check_findings

    finding = _make_finding()
    model = _FakeModel({
        "decisions": [{
            "finding_id": finding.finding_id,
            "decision": "reject",
            "reason": "The explanation is not supported.",
        }]
    })

    accepted, rejected, error = await check_findings(
        [finding], model, _FakeTools(), _FakeBudget(), _FakeTrace()
    )

    assert error is None
    assert accepted == []
    assert len(rejected) == 1
    assert rejected[0]["reason"] == "The explanation is not supported."


@pytest.mark.asyncio
async def test_checker_does_not_accept_missing_decision():
    from agent_harness.checker import check_findings

    finding = _make_finding()
    model = _FakeModel({"decisions": []})

    accepted, rejected, error = await check_findings(
        [finding], model, _FakeTools(), _FakeBudget(), _FakeTrace()
    )

    assert error is None
    assert accepted == []
    assert len(rejected) == 1
    assert finding.checker_status == "unverified"
    assert "Missing" in rejected[0]["reason"]


@pytest.mark.asyncio
async def test_checker_prompt_requires_source_grounded_reasoning():
    from agent_harness.checker import check_findings

    finding = _make_finding()
    model = _FakeModel({
        "decisions": [{
            "finding_id": finding.finding_id,
            "decision": "accept",
            "reason": "The explanation matches the source.",
        }]
    })

    await check_findings(
        [finding], model, _FakeTools(), _FakeBudget(), _FakeTrace()
    )

    assert "Independently reason about the source" in model.last_prompt
    assert "raises IndexError" in model.last_prompt
