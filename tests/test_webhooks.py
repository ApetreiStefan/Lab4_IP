import pytest
import respx
import httpx
from httpx import Response
import json


@pytest.mark.asyncio
@respx.mock
async def test_send_results_to_java_success():
    target_url = "https://java-server.com/api/callback"
    mock_data = {"status": "completed", "score": 80}

    route = respx.post(target_url).mock(return_value=Response(200))

    async with httpx.AsyncClient() as client:
        response = await client.post(target_url, json=mock_data)

    assert response.status_code == 200
    assert route.called
    sent_data = json.loads(route.calls.last.request.content)
    assert sent_data == mock_data
