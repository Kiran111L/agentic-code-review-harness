import os
from dataclasses import dataclass
from .schemas import RunLimits

@dataclass
class ModelConfig:
    api_key: str | None
    model: str
    base_url: str | None
    input_price: float | None
    output_price: float | None

def model_config(mode: str = "live") -> ModelConfig:
    def number(name):
        raw = os.getenv(name)
        try:
            return float(raw) if raw not in (None, "") else None
        except ValueError:
            return None

    if mode == "ollama":
        return ModelConfig(
            api_key=None,
            model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            input_price=None,
            output_price=None,
        )

    return ModelConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        base_url=os.getenv("OPENAI_BASE_URL") or None,
        input_price=number("MODEL_INPUT_USD_PER_1M"),
        output_price=number("MODEL_OUTPUT_USD_PER_1M"),
    )
