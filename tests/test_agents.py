import pytest
from agent_harness.harness import run_review

@pytest.mark.asyncio
async def test_mock_end_to_end(tmp_path):
    project=tmp_path/"p"; project.mkdir()
    (project/"app.py").write_text("def f():\n    return 1\n")
    report, paths=await run_review("review",str(project),mode="mock",output_dir=str(tmp_path/"runs"))
    assert report.status.value == "completed"
    assert len(report.agent_results)==3
    assert all(p.exists() for p in map(__import__("pathlib").Path, paths.values()))

@pytest.mark.asyncio
async def test_failed_specialist_produces_partial_report(tmp_path):
    project=tmp_path/"p"; project.mkdir()
    (project/"app.py").write_text("def f():\n    return 1\n")
    report, paths=await run_review("review",str(project),mode="mock",output_dir=str(tmp_path/"runs"),fail_roles={"security"})
    security = next(r for r in report.agent_results if r.role.value == "security")
    assert security.status.value == "failed"
    assert report.status.value == "partial"


def test_finding_from_dict_normalizes_aliases():
    from agent_harness.agents import finding_from_dict
    from agent_harness.schemas import Role

    raw = {
        "type": "bug",
        "title": "File handle leak",
        "path": "app.py",
        "line": 2,
        "snippet": 'handle = open(path, "r")',
        "description": "The file handle may remain open after an exception.",
        "fix": "Use a with statement to manage the file handle.",
        "severity": "moderate",
        "confidence": 0.8,
    }

    finding = finding_from_dict(raw, Role.baseline)

    assert finding.category.value == "correctness"
    assert finding.file_path == "app.py"
    assert finding.start_line == 2
    assert finding.end_line == 2
    assert finding.evidence == raw["snippet"]
    assert finding.recommended_fix == raw["fix"]


def test_finding_from_dict_rejects_missing_required_fields():
    from pydantic import ValidationError
    from agent_harness.agents import finding_from_dict
    from agent_harness.schemas import Role

    with pytest.raises(ValidationError):
        finding_from_dict(
            {"category": "security", "title": "Missing source details"},
            Role.baseline,
        )


@pytest.mark.asyncio
async def test_duplicate_findings_across_categories_are_removed(tmp_path, monkeypatch):
    import agent_harness.harness as harness_module
    from agent_harness.schemas import AgentResult, Finding, Role, Status

    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text(
        "def first_item(items):\n"
        "    return items[0]\n"
    )

    async def fake_specialist(role, task_id, desc, tools, model, budget, trace, limits):
        findings = []
        if role in {Role.bug, Role.security}:
            category = (
                "correctness" if role == Role.bug else "security"
            )
            findings = [
                Finding(
                    finding_id=f"finding-{role.value}",
                    category=category,
                    severity="high",
                    title="Empty input raises IndexError",
                    file_path="app.py",
                    start_line=2,
                    end_line=2,
                    evidence="return items[0]",
                    explanation="An empty list raises IndexError when indexed.",
                    recommended_fix="Check for an empty list before indexing.",
                    confidence=0.9,
                    specialist=role,
                )
            ]

        return AgentResult(
            role=role,
            task_id=task_id,
            status=Status.completed,
            findings=findings,
        )

    async def fake_checker(findings, *args, **kwargs):
        assert len(findings) == 1
        return findings, [], None

    monkeypatch.setattr(harness_module, "specialist", fake_specialist)
    monkeypatch.setattr(harness_module, "check_findings", fake_checker)

    report, _ = await harness_module.run_review(
        "Check duplicate detection",
        str(project),
        mode="mock",
        output_dir=str(tmp_path / "runs"),
    )

    assert len(report.accepted_findings) == 1
    assert len(report.rejected_findings) == 1
    assert "Duplicate finding removed" in report.rejected_findings[0]["reason"]


def test_finding_from_dict_rejects_missing_evidence_and_fix():
    from pydantic import ValidationError
    from agent_harness.agents import finding_from_dict
    from agent_harness.schemas import Role

    raw = {
        "type": "security",
        "title": "Unsafe use of eval",
        "path": "app.py",
        "line": 3,
        "description": "Untrusted input may execute arbitrary code.",
    }

    with pytest.raises(ValidationError):
        finding_from_dict(raw, Role.baseline)
