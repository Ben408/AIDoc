"""
Tests for the Query Response Agent implementation.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.agents.query_response import QueryResponseAgent
from src.integrations.openai_client import OpenAIClient
from src.integrations.confluence_client import ConfluenceClient
from src.utils.redis_client import RedisClient

@pytest.fixture
def openai_client():
    return Mock(spec=OpenAIClient)

@pytest.fixture
def confluence_client():
    return Mock(spec=ConfluenceClient)

@pytest.fixture
def redis_client():
    return Mock(spec=RedisClient)

@pytest.fixture
def query_agent(openai_client, confluence_client, redis_client):
    return QueryResponseAgent(openai_client, confluence_client, redis_client)

@pytest.fixture
def sample_query():
    return "How do I implement OAuth2 authentication in the API?"

@pytest.fixture
def sample_context():
    return {
        'documentation': [
            {
                'title': 'OAuth2 Implementation Guide',
                'url': 'https://docs.example.com/oauth2',
                'excerpt': 'Step-by-step guide for OAuth2 implementation'
            }
        ],
        'technical_references': [
            {
                'title': 'OAuth2 Specification',
                'description': 'Official OAuth2 protocol specification',
                'url': 'https://oauth.net/2/'
            }
        ],
        'user_provided': {
            'framework': 'Django',
            'version': '3.2'
        }
    }

@pytest.fixture
def sample_query_analysis():
    return {
        'type': 'how-to',
        'domain': 'authentication',
        'expertise_level': 'intermediate',
        'response_format': 'text',
        'key_terms': ['oauth2', 'authentication', 'api']
    }

@pytest.fixture
def sample_response_content():
    return """To implement OAuth2 authentication:

1. Install required packages
2. Configure OAuth2 settings
3. Implement authentication endpoints
4. Add middleware

Example code:

python
from oauth2_provider.views import TokenView


For more details, see the documentation."""

class TestQueryResponseAgent:
    async def test_process_query_success(
        self,
        query_agent,
        openai_client,
        sample_query,
        sample_response_content
    ):
        # Arrange
        openai_client.generate_completion.return_value = sample_response_content
        
        # Act
        result = await query_agent.process_query(sample_query)
        
        # Assert
        assert isinstance(result, dict)
        assert 'query' in result
        assert 'response' in result
        assert 'metadata' in result
        assert 'references' in result
        assert 'suggestions' in result
        
    async def test_analyze_query(self, query_agent, openai_client, sample_query):
        # Arrange
        analysis_response = """
        Type: how-to
        Domain: authentication
        Expertise: intermediate
        Format: structured
        Terms: oauth2, authentication, api
        """
        openai_client.generate_completion.return_value = analysis_response
        
        # Act
        analysis = await query_agent._analyze_query(sample_query)
        
        # Assert
        assert isinstance(analysis, dict)
        assert 'type' in analysis
        assert 'domain' in analysis
        assert 'expertise_level' in analysis
        assert 'key_terms' in analysis
        
    def test_parse_query_analysis(self, query_agent):
        # Arrange
        analysis_text = """
        This is a how-to query about API authentication.
        It requires advanced expertise.
        Key terms: oauth, token, authentication.
        """
        
        # Act
        result = query_agent._parse_query_analysis(analysis_text)
        
        # Assert
        assert result['type'] == 'how-to'
        assert result['domain'] == 'authentication'
        assert result['expertise_level'] == 'advanced'
        assert len(result['key_terms']) > 0
        
    async def test_gather_context(
        self,
        query_agent,
        confluence_client,
        sample_query,
        sample_query_analysis
    ):
        # Arrange
        confluence_client.search_content.return_value = [
            {'title': 'OAuth2 Guide', 'excerpt': 'Guide content'}
        ]
        
        # Act
        context = await query_agent._gather_context(
            sample_query,
            sample_query_analysis,
            {'framework': 'Django'}
        )
        
        # Assert
        assert 'documentation' in context
        assert 'user_provided' in context
        assert 'technical_references' in context
        assert context['user_provided']['framework'] == 'Django'
        
    def test_create_response_prompt(
        self,
        query_agent,
        sample_query_analysis,
        sample_context
    ):
        # Arrange
        parameters = {'style_guide': {'tone': 'technical'}}
        
        # Act
        prompt = query_agent._create_response_prompt(
            sample_query_analysis,
            sample_context,
            parameters
        )
        
        # Assert
        assert 'how-to' in prompt.lower()
        assert 'style guidelines' in prompt.lower()
        assert 'technical' in prompt.lower()
        
    def test_prepare_context_message(self, query_agent, sample_context):
        # Act
        context_message = query_agent._prepare_context_message(sample_context)
        
        # Assert
        assert 'Related Documentation:' in context_message
        assert 'Technical References:' in context_message
        assert 'Additional Context:' in context_message
        assert 'OAuth2' in context_message
        
    async def test_structure_response(
        self,
        query_agent,
        sample_query,
        sample_response_content,
        sample_context,
        sample_query_analysis
    ):
        # Act
        response = await query_agent._structure_response(
            sample_query,
            sample_response_content,
            sample_context,
            sample_query_analysis
        )
        
        # Assert
        assert response['query'] == sample_query
        assert response['response'] == sample_response_content
        assert 'metadata' in response
        assert 'references' in response
        assert 'suggestions' in response
        
    def test_extract_references(self, query_agent, sample_context):
        # Act
        references = query_agent._extract_references(sample_context)
        
        # Assert
        assert len(references) > 0
        assert references[0]['type'] in ['documentation', 'technical']
        assert 'title' in references[0]
        assert 'url' in references[0]
        assert 'relevance' in references[0]
        
    async def test_generate_follow_up_suggestions(
        self,
        query_agent,
        openai_client,
        sample_query,
        sample_response_content,
        sample_query_analysis
    ):
        # Arrange
        suggestions = [
            "How do I handle OAuth2 token refresh?",
            "What are the best security practices for OAuth2?"
        ]
        openai_client.generate_completion.return_value = "\n".join(suggestions)
        
        # Act
        result = await query_agent._generate_follow_up_suggestions(
            sample_query,
            sample_response_content,
            sample_query_analysis
        )
        
        # Assert
        assert len(result) > 0
        assert all(isinstance(s, str) for s in result)
        assert "OAuth2" in " ".join(result)
        
    async def test_conversation_history_management(
        self,
        query_agent,
        redis_client,
        sample_query,
        sample_response_content
    ):
        # Arrange
        session_id = "test_session"
        response = {
            'query': sample_query,
            'response': sample_response_content,
            'metadata': {}
        }
        
        # Act
        await query_agent._update_conversation_history(
            session_id,
            sample_query,
            response
        )
        
        # Assert
        assert session_id in query_agent.conversation_history
        assert len(query_agent.conversation_history[session_id]) == 1
        assert query_agent.conversation_history[session_id][0]['query'] == sample_query
        
    async def test_error_handling(self, query_agent, openai_client, sample_query):
        # Arrange
        openai_client.generate_completion.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await query_agent.process_query(sample_query)
        assert "API Error" in str(exc_info.value)
        
    @patch('logging.Logger.info')
    async def test_logging_success(
        self,
        mock_logger,
        query_agent,
        openai_client,
        sample_query,
        sample_response_content
    ):
        # Arrange
        openai_client.generate_completion.return_value = sample_response_content
        
        # Act
        await query_agent.process_query(sample_query)
        
        # Assert
        mock_logger.assert_called()
        log_args = mock_logger.call_args[1]
        assert 'duration' in log_args['extra']
        assert log_args['extra']['status'] == 'success'
        
    @patch('logging.Logger.error')
    async def test_logging_error(
        self,
        mock_logger,
        query_agent,
        openai_client,
        sample_query
    ):
        # Arrange
        openai_client.generate_completion.side_effect = Exception("Test Error")
        
        # Act & Assert
        with pytest.raises(Exception):
            await query_agent.process_query(sample_query)
        
        mock_logger.assert_called_once()
        log_args = mock_logger.call_args[1]
        assert 'error' in log_args['extra']
        assert log_args['extra']['status'] == 'error'