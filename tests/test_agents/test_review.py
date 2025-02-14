"""
Tests for the Review Agent implementation.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.agents.review import ReviewAgent
from src.integrations.openai_client import OpenAIClient

@pytest.fixture
def openai_client():
    return Mock(spec=OpenAIClient)

@pytest.fixture
def review_agent(openai_client):
    return ReviewAgent(openai_client)

@pytest.fixture
def sample_content():
    return """
    This is a sample documentation section. It contains multiple sentences
    with varying lengths and complexity. Some technical terms like API,
    REST endpoints, and authentication tokens are included. The documentation
    aims to be clear and concise while maintaining technical accuracy.
    """

@pytest.fixture
def sample_review_response():
    return """
    TECHNICAL_ACCURACY:
    - Technical terms are used correctly
    - Authentication process needs more detail
    
    STYLE_AND_CLARITY:
    - Writing is clear and concise
    - Consider breaking down longer sentences
    
    STRUCTURE_AND_ORGANIZATION:
    - Good logical flow
    - Add section headers for better organization
    
    COMPLETENESS:
    - Missing error handling examples
    - Need more code samples
    
    ACTIONABLE_SUGGESTIONS:
    - Add authentication flow diagram
    - Include error response examples
    """

class TestReviewAgent:
    async def test_review_content_success(self, review_agent, openai_client, sample_content, sample_review_response):
        # Arrange
        openai_client.generate_completion.return_value = sample_review_response
        
        # Act
        result = await review_agent.review_content(sample_content)
        
        # Assert
        assert isinstance(result, dict)
        assert 'technical_issues' in result
        assert 'style_issues' in result
        assert 'structure_issues' in result
        assert 'completeness_issues' in result
        assert 'suggestions' in result
        assert 'metrics' in result
        
        # Verify OpenAI client was called correctly
        openai_client.generate_completion.assert_called_once()
        
    async def test_review_content_with_style_guide(self, review_agent, openai_client):
        # Arrange
        style_guide = {
            "tone": "technical but approachable",
            "formatting": "use markdown for code blocks"
        }
        
        # Act
        await review_agent.review_content("Sample content", style_guide)
        
        # Assert
        call_args = openai_client.generate_completion.call_args[1]
        assert "STYLE GUIDE RULES:" in call_args['system_prompt']
        assert "technical but approachable" in call_args['system_prompt']
        
    async def test_parse_feedback_structure(self, review_agent, sample_review_response):
        # Act
        feedback = review_agent._parse_feedback(sample_review_response)
        
        # Assert
        assert len(feedback['technical_issues']) > 0
        assert len(feedback['style_issues']) > 0
        assert len(feedback['structure_issues']) > 0
        assert len(feedback['completeness_issues']) > 0
        assert len(feedback['suggestions']) > 0
        
        # Verify specific content
        assert any('authentication' in issue for issue in feedback['technical_issues'])
        assert any('section headers' in issue for issue in feedback['structure_issues'])
        
    def test_calculate_metrics(self, review_agent, sample_content):
        # Act
        metrics = review_agent._calculate_metrics(sample_content)
        
        # Assert
        assert metrics['word_count'] > 0
        assert metrics['sentence_count'] > 0
        assert metrics['avg_words_per_sentence'] > 0
        assert 'complexity_indicators' in metrics
        assert 'readability_score' in metrics
        
    def test_calculate_readability(self, review_agent):
        # Arrange
        simple_text = "The cat sat on the mat."
        complex_text = "The implementation of asynchronous microservices architecture requires careful consideration of distributed system patterns."
        
        # Act
        simple_score = review_agent._calculate_readability(simple_text)
        complex_score = review_agent._calculate_readability(complex_text)
        
        # Assert
        assert simple_score < complex_score  # Complex text should have higher grade level
        
    def test_count_syllables(self, review_agent):
        # Arrange
        test_cases = {
            "cat": 1,
            "python": 2,
            "documentation": 5,
            "api": 3,
            "microservice": 4
        }
        
        # Act & Assert
        for word, expected_count in test_cases.items():
            assert abs(review_agent._count_syllables(word) - expected_count) <= 1
            
    async def test_review_content_error_handling(self, review_agent, openai_client):
        # Arrange
        openai_client.generate_completion.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await review_agent.review_content("Sample content")
        assert "API Error" in str(exc_info.value)
        
    @patch('logging.Logger.info')
    async def test_logging_success(self, mock_logger, review_agent, openai_client, sample_review_response):
        # Arrange
        openai_client.generate_completion.return_value = sample_review_response
        
        # Act
        await review_agent.review_content("Sample content")
        
        # Assert
        mock_logger.assert_called_once()
        log_args = mock_logger.call_args[1]
        assert 'duration' in log_args['extra']
        assert log_args['extra']['status'] == 'success'
        
    @patch('logging.Logger.error')
    async def test_logging_error(self, mock_logger, review_agent, openai_client):
        # Arrange
        openai_client.generate_completion.side_effect = Exception("Test Error")
        
        # Act
        with pytest.raises(Exception):
            await review_agent.review_content("Sample content")
        
        # Assert
        mock_logger.assert_called_once()
        log_args = mock_logger.call_args[1]
        assert 'error' in log_args['extra']
        assert log_args['extra']['status'] == 'error'
        
    def test_empty_content_handling(self, review_agent):
        # Act
        metrics = review_agent._calculate_metrics("")
        
        # Assert
        assert metrics['word_count'] == 0
        assert metrics['sentence_count'] == 1  # Split on '.' returns ['']
        assert metrics['avg_words_per_sentence'] == 0
        
    def test_single_word_content(self, review_agent):
        # Act
        metrics = review_agent._calculate_metrics("Test")
        
        # Assert
        assert metrics['word_count'] == 1
        assert metrics['sentence_count'] == 1
        assert metrics['avg_words_per_sentence'] == 1 