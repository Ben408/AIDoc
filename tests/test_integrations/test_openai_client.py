"""
Tests for the OpenAI client integration.
"""
import pytest
from src.integrations.openai_client import OpenAIClient

@pytest.fixture
def openai_client():
    return OpenAIClient()

async def test_generate_completion(openai_client, mocker):
    # Arrange
    system_prompt = "You are a helpful assistant"
    user_message = "Hello"
    expected_response = "Hi there!"
    
    mock_response = mocker.Mock()
    mock_response.choices[0].message.content = expected_response
    mocker.patch('openai.ChatCompletion.acreate', return_value=mock_response)

    # Act
    response = await openai_client.generate_completion(system_prompt, user_message)

    # Assert
    assert response == expected_response 