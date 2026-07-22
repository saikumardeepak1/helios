import uuid
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pricing import price_for_model
from app.models import CostRecord, Span


def compute_cost(model: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
    price = price_for_model(model)
    if price is None:
        return Decimal("0")

    prompt_cost = (Decimal(prompt_tokens) / Decimal(1000)) * price.prompt_price_per_1k
    completion_cost = (Decimal(completion_tokens) / Decimal(1000)) * price.completion_price_per_1k
    return prompt_cost + completion_cost


async def calculate_run_cost(db: AsyncSession, run_id: uuid.UUID) -> list[CostRecord]:
    spans = (
        (await db.execute(select(Span).where(Span.run_id == run_id, Span.model.is_not(None))))
        .scalars()
        .all()
    )

    tokens_by_model: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for span in spans:
        assert span.model is not None
        tokens_by_model[span.model][0] += span.prompt_tokens
        tokens_by_model[span.model][1] += span.completion_tokens

    await db.execute(delete(CostRecord).where(CostRecord.run_id == run_id))

    records = []
    for model, (prompt_tokens, completion_tokens) in tokens_by_model.items():
        record = CostRecord(
            run_id=run_id,
            model=model,
            cost_usd=compute_cost(model, prompt_tokens, completion_tokens),
        )
        db.add(record)
        records.append(record)

    await db.commit()
    return records
