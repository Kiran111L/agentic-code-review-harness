import asyncio, pytest
from agent_harness.budgets import BudgetManager, BudgetExceeded
from agent_harness.schemas import RunLimits

@pytest.mark.asyncio
async def test_concurrent_budget_is_enforced():
    b = BudgetManager(RunLimits(max_interactions=1, max_model_calls=1))
    results = await asyncio.gather(b.reserve(model_call=True), b.reserve(model_call=True), return_exceptions=True)
    assert sum(isinstance(x, BudgetExceeded) for x in results) == 1
