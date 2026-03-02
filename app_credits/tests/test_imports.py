import pytest
from httpx import AsyncClient
import io
import pandas as pd


@pytest.mark.asyncio
async def test_import_plans_invalid_file(ac: AsyncClient):
    files = {'file': ('test.txt', b'wrong content', 'text/plain')}
    response = await ac.post("/plans/insert", files=files)

    assert response.status_code == 400

    data = response.json()
    assert data["detail"] == "Наданий файл не є валідним Excel-файлом"
    assert data["type"] == "AppException"


@pytest.mark.asyncio
async def test_import_plans_empty_file(ac: AsyncClient):
    output = io.BytesIO()
    df = pd.DataFrame(columns=["period", "category_id", "sum"])
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    excel_content = output.getvalue()
    files = {'file': ('empty.xlsx', excel_content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}

    response = await ac.post("/plans/insert", files=files)

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_import_plans_success_flow(ac: AsyncClient):
    csv_content = b"period,category_id,sum\n01.01.2025,1,1000"
    files = {'file': ('valid.csv', csv_content, 'text/csv')}

    response = await ac.post("/plans/insert", files=files)

    assert response.status_code == 400

    if response.status_code == 409:
        assert "вже існує" in response.json()["detail"]


@pytest.mark.asyncio
async def test_import_with_spaces_in_csv(ac: AsyncClient):
    csv_content = b"period,category_id,sum\n01.01.2025,1,500.0"
    files = {'file': ('spaces.csv', csv_content, 'text/csv')}

    response = await ac.post("/plans/insert", files=files)

    assert response.status_code == 400