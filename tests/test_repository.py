import pytest
from unittest.mock import AsyncMock, MagicMock
from ai_service.db.repositories import AIRepository


@pytest.mark.asyncio
async def test_update_student_performance():
    mock_session = AsyncMock()
    repo = AIRepository(db=mock_session)

    await repo.update_student_performance("user123", "Math", True)

    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_cached_response():
    mock_session = AsyncMock()
    repo = AIRepository(db=mock_session)

    mock_result = MagicMock()
    mock_result.scalar.return_value = {"cached": True}
    mock_session.execute.return_value = mock_result

    res = await repo.get_cached_response("test text")
    assert res == {"cached": True}


@pytest.mark.asyncio
async def test_save_to_cache():
    mock_session = AsyncMock()
    repo = AIRepository(db=mock_session)

    await repo.save_to_cache("test text", {"data": 1})

    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
