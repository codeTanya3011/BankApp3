import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_performance_calculation(ac: AsyncClient):
    check_date = "2021-03-01"
    response = await ac.get(f"/plans/performance?check_date={check_date}")

    assert response.status_code == 200
    data = response.json()

    if data:
        categories = [item["category"].lower() for item in data]
        assert any("видача" in cat or "збір" in cat for cat in categories)


@pytest.mark.asyncio
async def test_performance_zero_plan(ac: AsyncClient):
    check_date = "2030-01-01"
    response = await ac.get(f"/plans/performance?check_date={check_date}")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_performance_dates_sorting(ac: AsyncClient):
    test_date = "2021-03-01"
    response = await ac.get(f"/plans/performance?check_date={test_date}")

    assert response.status_code == 200
    data = response.json()
    for item in data:

        assert item["period"].startswith("2021-03")


@pytest.mark.asyncio
async def test_performance_math_accuracy(ac: AsyncClient):
    setup_res = await ac.post("/plans/setup-database")
    assert setup_res.status_code == 200, f"Setup failed: {setup_res.json()}"

    check_date = "2021-03-01"
    response = await ac.get(f"/plans/performance?check_date={check_date}")

    assert response.status_code == 200
    data = response.json()

    assert len(data) > 0, f"Порожній список для {check_date}. Перевір, чи заповнена база."

    target_category = "збір"
    item = next((i for i in data if target_category in i["category"].lower()), None)

    assert item is not None, f"Категорія '{target_category}' не знайдена. Доступні: {[i['category'] for i in data]}"

    plan_sum = float(item["plan_sum"])
    fact_sum = float(item["fact_sum"])
    performance_percent = float(item["performance_percent"])

    if plan_sum > 0:
        expected_percent = round((fact_sum / plan_sum) * 100, 2)
    else:
        expected_percent = 0.0

    assert performance_percent == pytest.approx(expected_percent, abs=0.01), \
        f"Математика підвела: очікували {expected_percent}, отримали {performance_percent}"