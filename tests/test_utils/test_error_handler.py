"""
Tests for the Error Handler system.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from datetime import datetime

from src.utils.error_handler import (
    ErrorHandler,
    ErrorSeverity,
    ErrorCategory
)

@pytest.fixture
def redis_client():
    client = Mock()
    client.set_cache = AsyncMock()
    client.get_cache = AsyncMock()
    return client

@pytest.fixture
def error_handler(redis_client):
    return ErrorHandler(
        redis_client=redis_client,
        notification_url="https://api.notifications.test/webhook",
        notification_token="test-token"
    )

@pytest.fixture
def sample_error_context():
    return {
        "component": "review_agent",
        "operation": "content_review",
        "user_id": "test-user",
        "content_id": "doc-123"
    }

class TestErrorHandler:
    async def test_handle_error_basic(self, error_handler, sample_error_context):
        """Test basic error handling functionality."""
        # Arrange
        test_error = ValueError("Invalid input")
        
        # Act
        result = await error_handler.handle_error(
            test_error,
            sample_error_context,
            severity=ErrorSeverity.MEDIUM
        )
        
        # Assert
        assert result["error_type"] == "ValueError"
        assert result["category"] == ErrorCategory.VALIDATION_ERROR.value
        assert result["severity"] == ErrorSeverity.MEDIUM.value
        assert "timestamp" in result
        assert "traceback" in result
        
    async def test_error_categorization(self, error_handler):
        """Test error categorization logic."""
        # Arrange
        test_cases = [
            (ValueError("test"), ErrorCategory.VALIDATION_ERROR),
            (ConnectionError(), ErrorCategory.INTEGRATION_ERROR),
            (MemoryError(), ErrorCategory.RESOURCE_ERROR),
            (KeyError(), ErrorCategory.CONFIGURATION_ERROR),
            (Exception("unknown"), ErrorCategory.SYSTEM_ERROR)
        ]
        
        # Act & Assert
        for error, expected_category in test_cases:
            category = await error_handler._categorize_error(error)
            assert category == expected_category
            
    async def test_error_pattern_detection(
        self,
        error_handler,
        sample_error_context
    ):
        """Test error pattern detection."""
        # Arrange
        test_error = ValueError("Repeated error")
        
        # Act - Simulate multiple errors
        for _ in range(11):  # Exceed pattern threshold
            await error_handler.handle_error(
                test_error,
                sample_error_context
            )
            
        result = await error_handler.handle_error(
            test_error,
            sample_error_context
        )
        
        # Assert
        assert result.get("pattern_detected") is True
        assert error_handler.error_patterns["ValueError"] > 10
        
    @patch("aiohttp.ClientSession.post")
    async def test_error_notification(
        self,
        mock_post,
        error_handler,
        sample_error_context
    ):
        """Test error notification system."""
        # Arrange
        test_error = Exception("Critical error")
        mock_post.return_value.__aenter__.return_value.status = 200
        
        # Act
        await error_handler.handle_error(
            test_error,
            sample_error_context,
            severity=ErrorSeverity.CRITICAL
        )
        
        # Assert
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert "Authorization" in call_kwargs["headers"]
        assert "error_notification" in call_kwargs["json"]["type"]
        
    async def test_error_recovery_attempt(
        self,
        error_handler,
        sample_error_context
    ):
        """Test error recovery mechanisms."""
        # Arrange
        test_error = ConnectionError("Connection lost")
        
        # Act
        result = await error_handler.handle_error(
            test_error,
            sample_error_context
        )
        
        # Assert
        assert "recovery_action" in result
        assert "reconnection" in result["recovery_action"].lower()
        
    async def test_redis_storage(
        self,
        error_handler,
        redis_client,
        sample_error_context
    ):
        """Test error storage in Redis."""
        # Arrange
        test_error = ValueError("Test storage")
        
        # Act
        await error_handler.handle_error(
            test_error,
            sample_error_context
        )
        
        # Assert
        redis_client.set_cache.assert_called()
        call_args = redis_client.set_cache.call_args[0]
        assert "error:" in call_args[0]
        assert "ValueError" in str(call_args[1])
        
    async def test_error_summary_generation(
        self,
        error_handler,
        redis_client
    ):
        """Test error summary generation."""
        # Arrange
        redis_client.get_cache.return_value = [
            {
                "error_type": "ValueError",
                "category": ErrorCategory.VALIDATION_ERROR.value,
                "severity": ErrorSeverity.MEDIUM.value
            },
            {
                "error_type": "ConnectionError",
                "category": ErrorCategory.INTEGRATION_ERROR.value,
                "severity": ErrorSeverity.HIGH.value
            }
        ]
        
        # Act
        summary = await error_handler.get_error_summary()
        
        # Assert
        assert summary["total_errors"] == 2
        assert ErrorCategory.VALIDATION_ERROR.value in str(summary["by_category"])
        assert ErrorSeverity.HIGH.value in str(summary["by_severity"])
        
    @pytest.mark.parametrize("severity", [
        ErrorSeverity.LOW,
        ErrorSeverity.MEDIUM,
        ErrorSeverity.HIGH,
        ErrorSeverity.CRITICAL
    ])
    async def test_severity_handling(
        self,
        error_handler,
        sample_error_context,
        severity
    ):
        """Test handling of different error severities."""
        # Arrange
        test_error = Exception(f"Test {severity.value} severity")
        
        # Act
        result = await error_handler.handle_error(
            test_error,
            sample_error_context,
            severity=severity
        )
        
        # Assert
        assert result["severity"] == severity.value
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            assert "notification" in str(result).lower() 