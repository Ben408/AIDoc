"""
Integration tests for agent interactions and workflows.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.agents.review import ReviewAgent
from src.agents.drafting import DraftingAgent
from src.agents.query_response import QueryResponseAgent
from src.agents.orchestration import OrchestrationAgent
from src.integrations.openai_client import OpenAIClient
from src.integrations.jira_client import JiraClient
from src.integrations.confluence_client import ConfluenceClient
from src.utils.redis_client import RedisClient

@pytest.fixture
def openai_client():
    return Mock(spec=OpenAIClient)

@pytest.fixture
def jira_client():
    return Mock(spec=JiraClient)

@pytest.fixture
def confluence_client():
    return Mock(spec=ConfluenceClient)

@pytest.fixture
def redis_client():
    return Mock(spec=RedisClient)

@pytest.fixture
def review_agent(openai_client):
    return ReviewAgent(openai_client)

@pytest.fixture
def drafting_agent(openai_client, jira_client, confluence_client):
    return DraftingAgent(openai_client, jira_client, confluence_client)

@pytest.fixture
def query_agent(openai_client, confluence_client, redis_client):
    return QueryResponseAgent(openai_client, confluence_client, redis_client)

@pytest.fixture
def orchestrator(query_agent, drafting_agent, review_agent, redis_client):
    return OrchestrationAgent(query_agent, drafting_agent, review_agent, redis_client)

class TestAgentIntegration:
    async def test_draft_and_review_workflow(
        self,
        orchestrator,
        openai_client,
        jira_client,
        confluence_client
    ):
        """Test the complete draft creation and review workflow."""
        # Arrange
        draft_request = {
            'title': 'API Authentication Guide',
            'doc_type': 'technical_guide',
            'requirements': ['Explain OAuth2 flow', 'Include code examples'],
            'jira_keys': ['AUTH-123']
        }
        
        jira_client.get_issues.return_value = [{
            'key': 'AUTH-123',
            'summary': 'Implement OAuth2',
            'description': 'Implementation details'
        }]
        
        draft_content = """# API Authentication Guide
        
        ## Overview
        This guide explains OAuth2 authentication implementation.
        
        ## Steps
        1. Configure OAuth2
        2. Implement endpoints
        
        ## Code Examples
        ```python
        # Example implementation
        ```
        """
        
        review_feedback = """
        TECHNICAL_ACCURACY:
        - Implementation steps are correct
        - Add error handling examples
        
        STYLE_AND_CLARITY:
        - Clear and well-structured
        - Consider adding diagrams
        """
        
        openai_client.generate_completion.side_effect = [
            draft_content,    # For draft generation
            review_feedback,  # For review
        ]
        
        # Act
        # 1. Generate draft
        draft_result = await orchestrator.process_request(
            'draft',
            draft_request
        )
        
        # 2. Review the draft
        review_result = await orchestrator.process_request(
            'review',
            {'content': draft_result['content']}
        )
        
        # Assert
        assert 'content' in draft_result
        assert 'API Authentication Guide' in draft_result['content']
        assert 'metadata' in draft_result
        
        assert 'feedback' in review_result
        assert 'technical_issues' in review_result['feedback']
        assert 'style_issues' in review_result['feedback']
        
    async def test_query_and_draft_workflow(
        self,
        orchestrator,
        openai_client,
        confluence_client
    ):
        """Test the workflow from user query to draft generation."""
        # Arrange
        query = "How do I document our API authentication process?"
        
        query_response = """You should create a technical guide covering:
        1. OAuth2 implementation
        2. Authentication flows
        3. Code examples"""
        
        draft_content = """# API Authentication Documentation Guide
        
        ## Required Sections
        1. Overview
        2. Implementation Steps
        3. Code Examples
        4. Troubleshooting
        """
        
        openai_client.generate_completion.side_effect = [
            query_response,  # For query analysis
            draft_content,   # For draft generation
        ]
        
        confluence_client.search_content.return_value = [{
            'title': 'Existing Auth Docs',
            'excerpt': 'Previous documentation on authentication'
        }]
        
        # Act
        # 1. Process initial query
        query_result = await orchestrator.process_request(
            'query',
            {'query': query}
        )
        
        # 2. Generate draft based on query response
        draft_request = {
            'title': 'API Authentication Documentation',
            'requirements': query_result['response'].split('\n'),
            'doc_type': 'technical_guide'
        }
        
        draft_result = await orchestrator.process_request(
            'draft',
            draft_request
        )
        
        # Assert
        assert 'response' in query_result
        assert 'OAuth2' in query_result['response']
        
        assert 'content' in draft_result
        assert 'API Authentication' in draft_result['content']
        assert 'Required Sections' in draft_result['content']
        
    async def test_complete_documentation_workflow(
        self,
        orchestrator,
        openai_client,
        jira_client,
        confluence_client,
        redis_client
    ):
        """Test the complete documentation workflow from query to final review."""
        # Arrange
        initial_query = "We need documentation for our new OAuth2 implementation"
        
        query_analysis = """
        Type: documentation_request
        Domain: authentication
        Expertise: intermediate
        """
        
        draft_outline = """
        Suggested documentation structure:
        1. Overview
        2. Implementation Guide
        3. Examples
        4. Security Considerations
        """
        
        draft_content = """# OAuth2 Implementation Guide
        
        ## Overview
        This guide covers our OAuth2 implementation.
        
        ## Implementation Steps
        1. Configure OAuth2
        2. Set up endpoints
        
        ## Examples
        ```python
        # Example code
        ```
        
        ## Security
        Security best practices...
        """
        
        review_feedback = """
        TECHNICAL_ACCURACY:
        - Implementation steps are accurate
        - Add more security details
        
        STYLE_AND_CLARITY:
        - Well-structured
        - Add troubleshooting section
        """
        
        openai_client.generate_completion.side_effect = [
            query_analysis,    # Query analysis
            draft_outline,     # Initial outline
            draft_content,     # Draft generation
            review_feedback    # Review feedback
        ]
        
        # Act
        # 1. Initial query processing
        query_result = await orchestrator.process_request(
            'query',
            {'query': initial_query}
        )
        
        # 2. Draft generation
        draft_result = await orchestrator.process_request(
            'draft',
            {
                'title': 'OAuth2 Implementation Guide',
                'requirements': draft_outline.split('\n'),
                'doc_type': 'technical_guide'
            }
        )
        
        # 3. Review
        review_result = await orchestrator.process_request(
            'review',
            {'content': draft_result['content']}
        )
        
        # Assert
        # Query phase
        assert 'response' in query_result
        assert query_result['metadata']['query_type'] == 'documentation_request'
        
        # Draft phase
        assert 'content' in draft_result
        assert 'OAuth2' in draft_result['content']
        assert 'Implementation Steps' in draft_result['content']
        assert 'Examples' in draft_result['content']
        
        # Review phase
        assert 'feedback' in review_result
        assert 'technical_issues' in review_result['feedback']
        assert 'style_issues' in review_result['feedback']
        
    async def test_error_handling_across_agents(
        self,
        orchestrator,
        openai_client,
        jira_client
    ):
        """Test error handling and recovery across agent interactions."""
        # Arrange
        draft_request = {
            'title': 'Test Guide',
            'requirements': ['Test requirement'],
            'jira_keys': ['TEST-123']
        }
        
        # Simulate JIRA error but successful draft generation
        jira_client.get_issues.side_effect = Exception("JIRA API Error")
        openai_client.generate_completion.return_value = "# Test Content"
        
        # Act
        draft_result = await orchestrator.process_request(
            'draft',
            draft_request
        )
        
        # Assert
        assert 'content' in draft_result
        assert 'metadata' in draft_result
        assert draft_result['metadata'].get('jira_error') is not None
        
    @patch('logging.Logger.info')
    async def test_performance_monitoring(
        self,
        mock_logger,
        orchestrator,
        openai_client
    ):
        """Test performance monitoring across agent interactions."""
        # Arrange
        query = "Test query"
        openai_client.generate_completion.return_value = "Test response"
        
        # Act
        await orchestrator.process_request(
            'query',
            {'query': query}
        )
        
        # Assert
        mock_logger.assert_called()
        log_calls = mock_logger.call_args_list
        
        # Verify timing logs
        timing_logs = [
            call for call in log_calls 
            if 'duration' in call[1]['extra']
        ]
        assert len(timing_logs) > 0 