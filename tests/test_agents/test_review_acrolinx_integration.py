"""
Integration tests for Review Agent and Acrolinx Agent interaction.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.agents.review import ReviewAgent
from src.agents.acrolinx_agent import AcrolinxAgent
from src.integrations.openai_client import OpenAIClient

@pytest.fixture
def openai_client():
    return Mock(spec=OpenAIClient)

@pytest.fixture
def acrolinx_agent():
    return Mock(spec=AcrolinxAgent)

@pytest.fixture
def review_agent(openai_client, acrolinx_agent):
    return ReviewAgent(openai_client, acrolinx_agent)

@pytest.fixture
def sample_content():
    return """
    <h1>API Authentication Guide</h1>
    
    <p>This guide explains the authentication process for our API. 
    You will learn how to implement OAuth2 authentication in your applications.</p>
    
    <h2>Prerequisites</h2>
    <ul>
        <li>Basic understanding of REST APIs</li>
        <li>API credentials</li>
    </ul>
    
    <h2>Implementation Steps</h2>
    <p>Follow these steps to implement authentication:</p>
    
    <div class="note">
        Important: Keep your API keys secure and never commit them to version control.
    </div>
    """

@pytest.fixture
def mock_ai_review():
    return {
        "issues": [
            {
                "type": "technical_accuracy",
                "severity": "medium",
                "message": "Consider adding error handling examples",
                "location": "Implementation Steps section"
            },
            {
                "type": "completeness",
                "severity": "high",
                "message": "Missing security best practices section",
                "location": "document"
            }
        ],
        "suggestions": [
            "Add code examples for each step",
            "Include troubleshooting section",
            "Add security considerations"
        ],
        "metadata": {
            "review_timestamp": datetime.now().isoformat(),
            "review_type": "technical_documentation"
        }
    }

@pytest.fixture
def mock_acrolinx_review():
    return {
        "quality_score": 85,
        "issues": [
            {
                "type": "style",
                "category": "clarity",
                "severity": "warning",
                "message": "Consider using active voice",
                "suggestions": ["We explain"],
                "position": {"start": 45, "end": 60}
            },
            {
                "type": "terminology",
                "category": "consistency",
                "severity": "info",
                "message": "Use consistent terminology for 'API key'",
                "suggestions": ["API key", "API credential"],
                "position": {"start": 120, "end": 135}
            }
        ],
        "guidance": {
            "goals": ["clarity", "consistency"],
            "guidelines": ["Use active voice", "Maintain consistent terminology"],
            "recommendations": ["Consider restructuring long sentences"]
        },
        "metadata": {
            "check_id": "check-123",
            "timestamp": datetime.now().isoformat(),
            "guidance_profile": "technical-content"
        }
    }

class TestReviewAcrolinxIntegration:
    async def test_combined_review_process(
        self,
        review_agent,
        openai_client,
        acrolinx_agent,
        sample_content,
        mock_ai_review,
        mock_acrolinx_review
    ):
        """Test complete review process with both AI and Acrolinx."""
        # Arrange
        openai_client.generate_completion.return_value = json.dumps(mock_ai_review)
        acrolinx_agent.check_content.return_value = mock_acrolinx_review
        
        # Act
        result = await review_agent.review_content(
            sample_content,
            reference="test-doc-1"
        )
        
        # Assert
        assert "quality_score" in result
        assert result["quality_score"] == 85
        assert len(result["issues"]) == 4  # 2 from AI + 2 from Acrolinx
        assert any(i["type"] == "technical_accuracy" for i in result["issues"])
        assert any(i["type"] == "style" for i in result["issues"])
        assert "acrolinx" in result["metadata"]
        
    async def test_review_with_acrolinx_failure(
        self,
        review_agent,
        openai_client,
        acrolinx_agent,
        sample_content,
        mock_ai_review
    ):
        """Test review process when Acrolinx check fails."""
        # Arrange
        openai_client.generate_completion.return_value = json.dumps(mock_ai_review)
        acrolinx_agent.check_content.side_effect = Exception("Acrolinx API Error")
        
        # Act
        result = await review_agent.review_content(sample_content)
        
        # Assert
        assert result["quality_score"] is None
        assert len(result["issues"]) == 2  # Only AI review issues
        assert "acrolinx_error" in result["metadata"]
        
    async def test_review_priority_handling(
        self,
        review_agent,
        openai_client,
        acrolinx_agent,
        sample_content,
        mock_ai_review,
        mock_acrolinx_review
    ):
        """Test handling of conflicting issues from AI and Acrolinx."""
        # Arrange
        # Add conflicting suggestions
        mock_ai_review["issues"].append({
            "type": "style",
            "severity": "low",
            "message": "Different style suggestion",
            "location": "paragraph 1"
        })
        
        openai_client.generate_completion.return_value = json.dumps(mock_ai_review)
        acrolinx_agent.check_content.return_value = mock_acrolinx_review
        
        # Act
        result = await review_agent.review_content(sample_content)
        
        # Assert
        style_issues = [i for i in result["issues"] if i["type"] == "style"]
        assert len(style_issues) == 2
        assert style_issues[0]["severity"] == "warning"  # Acrolinx issue
        
    async def test_content_type_handling(
        self,
        review_agent,
        openai_client,
        acrolinx_agent,
        mock_ai_review,
        mock_acrolinx_review
    ):
        """Test review process with different content types."""
        # Arrange
        content_types = [
            ("text/html", "<p>Test content</p>"),
            ("text/markdown", "# Test content"),
            ("text/plain", "Test content")
        ]
        
        openai_client.generate_completion.return_value = json.dumps(mock_ai_review)
        acrolinx_agent.check_content.return_value = mock_acrolinx_review
        
        for content_type, content in content_types:
            # Act
            result = await review_agent.review_content(
                content,
                content_type=content_type
            )
            
            # Assert
            assert result["metadata"]["content_type"] == content_type
            acrolinx_agent.check_content.assert_called_with(
                content,
                content_type=content_type,
                content_reference=None
            )
            
    @patch('logging.Logger.info')
    async def test_review_performance_logging(
        self,
        mock_logger,
        review_agent,
        openai_client,
        acrolinx_agent,
        sample_content,
        mock_ai_review,
        mock_acrolinx_review
    ):
        """Test performance logging of combined review process."""
        # Arrange
        openai_client.generate_completion.return_value = json.dumps(mock_ai_review)
        acrolinx_agent.check_content.return_value = mock_acrolinx_review
        
        # Act
        await review_agent.review_content(sample_content)
        
        # Assert
        mock_logger.assert_called()
        log_calls = mock_logger.call_args_list
        
        # Verify timing logs
        timing_logs = [
            call for call in log_calls 
            if 'duration' in call[1]['extra']
        ]
        assert len(timing_logs) >= 2  # At least one log each for AI and Acrolinx 