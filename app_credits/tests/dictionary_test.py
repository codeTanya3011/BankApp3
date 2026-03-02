import pytest
from httpx import AsyncClient
from decimal import Decimal


@pytest.mark.asyncio
async def test_dictionaries_integrity(ac: AsyncClient):
    response = await ac.get("/plans/performance?check_date=2021-03-01")
    assert response.status_code == 200
    data = response.json()

    for item in data:
        assert len(item["category"]) > 0
        assert isinstance(item["fact_sum"], (int, float, Decimal))
        assert isinstance(item["plan_sum"], (int, float, Decimal))

        assert item["plan_sum"] >= 0, f"План для {item['category']} негативний!"
        #перевірка зв'язків та типів даних

