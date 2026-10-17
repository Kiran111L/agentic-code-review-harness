import asyncio, time

class BudgetExceeded(RuntimeError):
    pass

class BudgetManager:
    def __init__(self, limits):
        self.limits = limits
        self.started = time.monotonic()
        self.interactions = 0
        self.model_calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.lock = asyncio.Lock()

    async def reserve(self, *, model_call=False, input_tokens=0, output_tokens=0):
        async with self.lock:
            if time.monotonic() - self.started >= self.limits.max_wall_seconds:
                raise BudgetExceeded("Run wall-clock budget exhausted")
            if self.interactions + 1 > self.limits.max_interactions:
                raise BudgetExceeded("Run interaction budget exhausted")
            if model_call and self.model_calls + 1 > self.limits.max_model_calls:
                raise BudgetExceeded("Run model-call budget exhausted")
            if self.input_tokens + input_tokens > self.limits.max_input_tokens:
                raise BudgetExceeded("Run input-token budget exhausted")
            if self.output_tokens + output_tokens > self.limits.max_output_tokens:
                raise BudgetExceeded("Run output-token budget exhausted")
            self.interactions += 1
            if model_call:
                self.model_calls += 1
            self.input_tokens += input_tokens
            self.output_tokens += output_tokens

    def elapsed(self):
        return time.monotonic() - self.started
