"""
Tests for API routes.
"""
import pytest
from src.api.routes import init_app

@pytest.fixture
def client(mocker):
    # Mock orchestration agent
    mock_orchestrator = mocker.Mock()
    app = init_app(mock_orchestrator)
    app.config['TESTING'] = True
    return app.test_client()

async def test_handle_query(client, mocker):
    # Arrange
    test_query = {"query": "How do I document an API?"}
    expected_response = {"response": "Here's how to document an API..."}

    # Act
    response = await client.post('/api/query', json=test_query)

    # Assert
    assert response.status_code == 200
    assert response.json == expected_response 