from decimal import Decimal
from typing import NamedTuple


class ModelPrice(NamedTuple):
    prompt_price_per_1k: Decimal
    completion_price_per_1k: Decimal


# USD per 1,000 tokens. Update as providers change pricing; an unlisted model
# is priced at $0 (see cost_service.calculate_run_cost) rather than raising,
# so ingestion never fails just because a new model isn't in this table yet.
MODEL_PRICING: dict[str, ModelPrice] = {
    "gpt-4o": ModelPrice(Decimal("0.0025"), Decimal("0.01")),
    "gpt-4o-mini": ModelPrice(Decimal("0.00015"), Decimal("0.0006")),
    "claude-sonnet-5": ModelPrice(Decimal("0.003"), Decimal("0.015")),
    "claude-haiku-4-5": ModelPrice(Decimal("0.0008"), Decimal("0.004")),
    "claude-opus-4-8": ModelPrice(Decimal("0.015"), Decimal("0.075")),
}


def price_for_model(model: str) -> ModelPrice | None:
    return MODEL_PRICING.get(model)
