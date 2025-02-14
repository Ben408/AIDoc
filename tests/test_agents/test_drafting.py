"""
Tests for the Drafting Agent implementation.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.agents.drafting import DraftingAgent
from src.integrations.openai_client import OpenAIClient
from src.integrations.jira_client import JiraClient
from src.integrations.confluence_client import ConfluenceClient

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
def drafting_agent(openai_client, jira_client, confluence_client):
    return DraftingAgent(openai_client, jira_client, confluence_client)

@pytest.fixture
def sample_content_request():
    return {
        'title': 'API Authentication Guide',
        'doc_type': 'technical_guide',
        'requirements': [
            'Explain authentication process',
            'Include code examples',
            'Cover error scenarios'
        ],
        'jira_keys': ['AUTH-123', 'AUTH-124'],
        'confluence_ids': ['12345', '12346']
    }

@pytest.fixture
def sample_context():
    return {
        'jira': [
            {
                'key': 'AUTH-123',
                'summary': 'Implement OAuth2 flow',
                'url': 'https://jira.example.com/AUTH-123'
            }
        ],
        'confluence': [
            {
                'id': '12345',
                'title': 'Authentication Overview',
                'url': 'https://confluence.example.com/12345'
            }
        ],
        'specifications': [
            'OAuth2 implementation details',
            'Rate limiting specifications'
        ]
    }

@pytest.fixture
def sample_generated_content():
    return """# API Authentication Guide

## Overview
This guide explains the authentication process for our API.

## Prerequisites
- Basic understanding of OAuth2
- API credentials

## Authentication Flow
1. Obtain credentials
2. Request access token
3. Use token in requests

## Code Examples
# python
import requests
def get_token():
# Implementation
pass

## Error Handling
Common error scenarios and solutions.

## References
See also: Authentication Overview
"""

class TestDraftingAgent:
    async def test_create_draft_success(
        self,
        drafting_agent,
        openai_client,
        jira_client,
        confluence_client,
        sample_content_request,
        sample_generated_content
    ):
        # Arrange
        openai_client.generate_completion.return_value = sample_generated_content
        jira_client.get_issues.return_value = [{'key': 'AUTH-123', 'summary': 'Test'}]
        confluence_client.get_pages.return_value = [{'id': '12345', 'title': 'Test'}]
        
        # Act
        result = await drafting_agent.create_draft(sample_content_request)
        
        # Assert
        assert isinstance(result, dict)
        assert 'content' in result
        assert 'metadata' in result
        assert 'analysis' in result
        assert 'suggestions' in result
        assert 'references' in result
        
    async def test_gather_context_integration(
        self,
        drafting_agent,
        jira_client,
        confluence_client,
        sample_content_request
    ):
        # Arrange
        jira_client.get_issues.return_value = [{'key': 'AUTH-123', 'summary': 'Test'}]
        confluence_client.get_pages.return_value = [{'id': '12345', 'title': 'Test'}]
        
        # Act
        context = await drafting_agent._gather_context(sample_content_request)
        
        # Assert
        assert 'jira' in context
        assert 'confluence' in context
        jira_client.get_issues.assert_called_once_with(['AUTH-123', 'AUTH-124'])
        confluence_client.get_pages.assert_called_once_with(['12345', '12346'])
        
    def test_create_system_prompt(self, drafting_agent, sample_content_request):
        # Arrange
        parameters = {
            'style_guide': {
                'tone': 'technical',
                'format': 'markdown'
            }
        }
        
        # Act
        prompt = drafting_agent._create_system_prompt(sample_content_request, parameters)
        
        # Assert
        assert 'technical writer' in prompt.lower()
        assert 'style guide requirements' in prompt.lower()
        assert 'technical_guide' in prompt.lower()
        
    def test_create_content_prompt(
        self,
        drafting_agent,
        sample_content_request,
        sample_context
    ):
        # Act
        prompt = drafting_agent._create_content_prompt(
            sample_content_request,
            sample_context
        )
        
        # Assert
        assert 'API Authentication Guide' in prompt
        assert 'Requirements:' in prompt
        assert 'JIRA Issues:' in prompt
        assert 'Related Documentation:' in prompt
        assert 'Technical Specifications:' in prompt
        
    def test_analyze_draft_structure(self, drafting_agent, sample_generated_content):
        # Act
        analysis = drafting_agent._analyze_draft(sample_generated_content)
        
        # Assert
        assert 'structure' in analysis
        assert 'readability' in analysis
        assert 'technical_elements' in analysis
        assert 'completeness' in analysis
        
        structure = analysis['structure']
        assert structure['section_count'] > 0
        assert structure['heading_count'] > 0
        
    def test_analyze_heading_hierarchy(self, drafting_agent):
        # Arrange
        headings = ['# Main', '## Sub1', '## Sub2', '### SubSub1']
        
        # Act
        hierarchy = drafting_agent._analyze_heading_hierarchy(headings)
        
        # Assert
        assert hierarchy['max_depth'] == 3
        assert hierarchy['is_sequential'] == True
        assert 1 in hierarchy['levels']
        assert 2 in hierarchy['levels']
        
    def test_analyze_technical_elements(self, drafting_agent, sample_generated_content):
        # Act
        elements = drafting_agent._analyze_technical_elements(sample_generated_content)
        
        # Assert
        assert elements['code_blocks'] > 0
        assert elements['api_references'] > 0
        assert 'technical_terms' in elements
        assert 'links' in elements
        
    def test_analyze_completeness(self, drafting_agent, sample_generated_content):
        # Act
        completeness = drafting_agent._analyze_completeness(sample_generated_content)
        
        # Assert
        assert 'has_required_sections' in completeness
        assert 'completeness_score' in completeness
        assert completeness['has_required_sections']['overview'] == True
        assert 0 <= completeness['completeness_score'] <= 1
        
    def test_generate_metadata(
        self,
        drafting_agent,
        sample_content_request,
        sample_context
    ):
        # Act
        metadata = drafting_agent._generate_metadata(
            sample_content_request,
            sample_context
        )
        
        # Assert
        assert 'generated_at' in metadata
        assert metadata['doc_type'] == 'technical_guide'
        assert len(metadata['related_issues']) > 0
        assert len(metadata['related_pages']) > 0
        
    def test_extract_references(self, drafting_agent, sample_context):
        # Act
        references = drafting_agent._extract_references(sample_context)
        
        # Assert
        assert len(references) > 0
        assert references[0]['type'] in ['jira', 'confluence']
        assert 'title' in references[0]
        assert 'url' in references[0]
        
    async def test_error_handling_jira_failure(
        self,
        drafting_agent,
        jira_client,
        sample_content_request
    ):
        # Arrange
        jira_client.get_issues.side_effect = Exception("JIRA API Error")
        
        # Act
        context = await drafting_agent._gather_context(sample_content_request)
        
        # Assert
        assert 'jira' not in context
        assert 'confluence' in context  # Other sources should still work
        
    @patch('logging.Logger.info')
    async def test_logging_success(
        self,
        mock_logger,
        drafting_agent,
        openai_client,
        sample_content_request,
        sample_generated_content
    ):
        # Arrange
        openai_client.generate_completion.return_value = sample_generated_content
        
        # Act
        await drafting_agent.create_draft(sample_content_request)
        
        # Assert
        mock_logger.assert_called_once()
        log_args = mock_logger.call_args[1]
        assert 'duration' in log_args['extra']
        assert log_args['extra']['status'] == 'success'
        
    @patch('logging.Logger.error')
    async def test_logging_error(
        self,
        mock_logger,
        drafting_agent,
        openai_client,
        sample_content_request
    ):
        # Arrange
        openai_client.generate_completion.side_effect = Exception("Test Error")
        
        # Act & Assert
        with pytest.raises(Exception):
            await drafting_agent.create_draft(sample_content_request)
        
        mock_logger.assert_called_once()
        log_args = mock_logger.call_args[1]
        assert 'error' in log_args['extra']
        assert log_args['extra']['status'] == 'error'