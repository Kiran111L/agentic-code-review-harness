import pytest
from agent_harness.models import MockModel, ModelError

@pytest.mark.asyncio
async def test_injected_failure_is_real_exception():
    model = MockModel(fail_roles={"security"})
    with pytest.raises(ModelError, match="Injected mock failure"):
        await model.complete_json("security", "system", "user")

@pytest.mark.asyncio
async def test_live_mode_requires_approval(tmp_path):
    from agent_harness.harness import run_review
    with pytest.raises(PermissionError, match="requires --approve-paid-calls"):
        await run_review("review", str(tmp_path), mode="live", approve_paid_calls=False)
