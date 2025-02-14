"""
Tests for the Acrolinx integration agent.
"""
import pytest
from unittest.mock import Mock, patch
import aiohttp
import json
from datetime import datetime

from src.agents.acrolinx_agent import AcrolinxAgent

@pytest.fixture
def acrolinx_config():
    return {
        "api_url": "https://test.acrolinx.cloud",
        "api_token": "test-token-123",
        "guidance_profile": "technical-content"
    }

@pytest.fixture
def acrolinx_agent(acrolinx_config):
    return AcrolinxAgent(**acrolinx_config)

@pytest.fixture
def sample_content():
    return """
    <h1>API Authentication Guide</h1>
    <p>This guide explains the authentication process for our API.</p>
    <div class="note">
        Important: Secure your API keys properly.
    </div>
    """

@pytest.fixture
def mock_check_response():
    return {
        "id": "check-123",
        "status": "done",
        "quality": {
            "score": 85,
            "status": "green"
        },
        "issues": [
            {
                "issueType": "spelling",
                "category": "correctness",
                "severity": "error",
                "message": "Possible spelling mistake",
                "suggestions": ["authentication"],
                "positionalInformation": {
                    "start": 10,
                    "end": 25
                }
            },
            {
                "issueType": "style",
                "category": "clarity",
                "severity": "warning",
                "message": "Consider using active voice",
                "suggestions": ["We explain"],
                "positionalInformation": {
                    "start": 45,
                    "end": 60
                }
            }
        ],
        "guidance": {
            "goals": ["clarity", "consistency"],
            "guidelines": ["Use active voice", "Keep sentences short"],
            "recommendations": ["Consider restructuring long sentences"]
        },
        "termHarvesting": {
            "terms": ["API", "authentication"],
            "suggestions": ["Consider adding to terminology database"]
        }
    }

class TestAcrolinxAgent:
    async def test_check_content_success(
        self,
        acrolinx_agent,
        sample_content,
        mock_check_response
    ):
        """Test successful content check submission and processing."""
        with patch("aiohttp.ClientSession") as mock_session:
            # Mock the POST request for check submission
            mock_post = Mock()
            mock_post.__aenter__.return_value.json.return_value = {
                "id": "check-123"
            }
            
            # Mock the GET request for check results
            mock_get = Mock()
            mock_get.__aenter__.return_value.json.return_value = mock_check_response
            
            mock_session.return_value.__aenter__.return_value.post = Mock(
                return_value=mock_post
            )
            mock_session.return_value.__aenter__.return_value.get = Mock(
                return_value=mock_get
            )
            
            # Act
            result = await acrolinx_agent.check_content(
                sample_content,
                content_type="text/html",
                content_reference="test-doc-1"
            )
            
            # Assert
            assert result["quality_score"] == 85
            assert len(result["issues"]) == 2
            assert "guidance" in result
            assert "terminology" in result
            assert result["metadata"]["guidance_profile"] == "technical-content"
            
    async def test_process_issues(self, acrolinx_agent, mock_check_response):
        """Test processing of content issues."""
        # Act
        processed_issues = acrolinx_agent._process_issues(
            mock_check_response["issues"]
        )
        
        # Assert
        assert len(processed_issues) == 2
        assert processed_issues[0]["type"] == "spelling"
        assert processed_issues[1]["type"] == "style"
        assert "suggestions" in processed_issues[0]
        assert "position" in processed_issues[0]
        
    async def test_process_guidance(self, acrolinx_agent, mock_check_response):
        """Test processing of guidance information."""
        # Act
        guidance = acrolinx_agent._process_guidance(
            mock_check_response["guidance"]
        )
        
        # Assert
        assert "goals" in guidance
        assert "guidelines" in guidance
        assert "recommendations" in guidance
        assert "clarity" in guidance["goals"]
        
    async def test_error_handling(self, acrolinx_agent, sample_content):
        """Test error handling during content check."""
        with patch("aiohttp.ClientSession") as mock_session:
            # Mock API error
            mock_session.return_value.__aenter__.return_value.post.side_effect = \
                aiohttp.ClientError("API Error")
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await acrolinx_agent.check_content(sample_content)
            assert "API Error" in str(exc_info.value)
            
    async def test_timeout_handling(
        self,
        acrolinx_agent,
        sample_content,
        mock_check_response
    ):
        """Test handling of timeout during result polling."""
        with patch("aiohttp.ClientSession") as mock_session:
            # Mock initial check submission
            mock_post = Mock()
            mock_post.__aenter__.return_value.json.return_value = {
                "id": "check-123"
            }
            
            # Mock polling timeout
            mock_get = Mock()
            mock_get.__aenter__.return_value.json.return_value = {
                "id": "check-123",
                "status": "processing"
            }
            
            mock_session.return_value.__aenter__.return_value.post = Mock(
                return_value=mock_post
            )
            mock_session.return_value.__aenter__.return_value.get = Mock(
                return_value=mock_get
            )
            
            # Act & Assert
            with pytest.raises(TimeoutError) as exc_info:
                await acrolinx_agent.check_content(
                    sample_content,
                    content_type="text/html"
                )
            assert "timed out" in str(exc_info.value).lower()
            
    async def test_guidance_profiles(self, acrolinx_agent):
        """Test fetching guidance profiles."""
        mock_profiles = {
            "profiles": [
                {"id": "technical", "name": "Technical Content"},
                {"id": "marketing", "name": "Marketing Content"}
            ]
        }
        
        with patch("aiohttp.ClientSession") as mock_session:
            mock_get = Mock()
            mock_get.__aenter__.return_value.json.return_value = mock_profiles
            
            mock_session.return_value.__aenter__.return_value.get = Mock(
                return_value=mock_get
            )
            
            # Act
            profiles = await acrolinx_agent.get_guidance_profiles()
            
            # Assert
            assert len(profiles) == 2
            assert profiles[0]["id"] == "technical"
            assert profiles[1]["name"] == "Marketing Content"
            
    @patch('logging.Logger.error')
    async def test_error_logging(
        self,
        mock_logger,
        acrolinx_agent,
        sample_content
    ):
        """Test error logging during content check."""
        with patch("aiohttp.ClientSession") as mock_session:
            # Mock API error
            mock_session.return_value.__aenter__.return_value.post.side_effect = \
                Exception("Test Error")
            
            # Act & Assert
            with pytest.raises(Exception):
                await acrolinx_agent.check_content(sample_content)
            
            mock_logger.assert_called_once()
            assert "Test Error" in mock_logger.call_args[0][0] 