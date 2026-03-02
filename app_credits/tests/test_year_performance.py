import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_year_performance_structure(ac: AsyncClient):
    year = 2022
    response = await ac.get(f"/plans/year_performance?year={year}")

    assert response.status_code == 200
    data = response.json()

    assert len(data) <= 12
    if len(data) > 0:
        assert "issued_fact_sum" in data[0]
        assert "payments_fact_sum" in data[0]


@pytest.mark.asyncio
async def test_year_performance_all_columns_present(ac: AsyncClient):
    response = await ac.get("/plans/year_performance?year=2022")
    assert response.status_code == 200

    data = response.json()
    if len(data) > 0:
        month_data = data[0]
        required_fields = [
            "issued_plan_sum", "issued_fact_sum", "issued_percent",
            "payments_plan_sum", "payments_fact_sum", "payments_percent"
        ]
        for field in required_fields:
            assert field in month_data, f"Поле {field} відсутнє у відповіді"


@pytest.mark.asyncio
async def test_year_performance_invalid_year(ac: AsyncClient):
    response = await ac.get("/plans/year_performance?year=9999")
    assert response.status_code == 200

    data = response.json()

    if len(data) > 0:
        assert data[0]["issued_percent"] == 0
