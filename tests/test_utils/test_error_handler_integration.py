"""
Integration tests for Error Handler with system components.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import logging
from datetime import datetime

from src.utils.error_handler import ErrorHandler, ErrorSeverity, ErrorCategory
from src.agents.review import ReviewAgent
from src.agents.drafting import DraftingAgent
from src.agents.acrolinx_agent import AcrolinxAgent
from src.utils.redis_client import RedisClient

@pytest.fixture
async def integrated_system():
    """Setup integrated test system with all components."""
    redis_client = Mock(spec=RedisClient)
    redis_client.set_cache = AsyncMock()
    redis_client.get_cache = AsyncMock()
    
    error_handler = ErrorHandler(
        redis_client=redis_client,
        notification_url="https://test.notifications.com/webhook",
        notification_token="test-token"
    )
    
    openai_client = Mock()
    acrolinx_agent = Mock(spec=AcrolinxAgent)
    review_agent = ReviewAgent(openai_client, acrolinx_agent)
    drafting_agent = DraftingAgent(openai_client)
    
    return {
        "redis_client": redis_client,
        "error_handler": error_handler,
        "review_agent": review_agent,
        "drafting_agent": drafting_agent,
        "acrolinx_agent": acrolinx_agent
    }

class TestErrorHandlerIntegration:
    async def test_review_agent_error_handling(self, integrated_system):
        """Test error handling during review process."""
        # Arrange
        review_agent = integrated_system["review_agent"]
        error_handler = integrated_system["error_handler"]
        acrolinx_agent = integrated_system["acrolinx_agent"]
        
        # Simulate Acrolinx error
        acrolinx_agent.check_content.side_effect = ConnectionError(
            "Acrolinx service unavailable"
        )
        
        # Act
        try:
            await review_agent.review_content("<p>Test content</p>")
        except Exception as e:
            error_result = await error_handler.handle_error(
                e,
                {
                    "component": "review_agent",
                    "operation": "content_review",
                    "content_length": 19
                }
            )
            
        # Assert
        assert error_result["category"] == ErrorCategory.INTEGRATION_ERROR.value
        assert "Acrolinx" in str(error_result["message"])
        
    async def test_drafting_agent_error_handling(self, integrated_system):
        """Test error handling during content drafting."""
        # Arrange
        drafting_agent = integrated_system["drafting_agent"]
        error_handler = integrated_system["error_handler"]
        
        # Simulate OpenAI API error
        drafting_agent.openai_client.generate_completion.side_effect = \
            Exception("API rate limit exceeded")
            
        # Act
        try:
            await drafting_agent.create_draft({
                "topic": "API Authentication",
                "context": {"audience": "developers"}
            })
        except Exception as e:
            error_result = await error_handler.handle_error(
                e,
                {
                    "component": "drafting_agent",
                    "operation": "content_generation",
                    "topic": "API Authentication"
                },
                severity=ErrorSeverity.HIGH
            )
            
        # Assert
        assert error_result["severity"] == ErrorSeverity.HIGH.value
        assert "rate limit" in str(error_result["message"]).lower()
        
    async def test_cascading_error_handling(self, integrated_system):
        """Test handling of cascading errors across components."""
        # Arrange
        review_agent = integrated_system["review_agent"]
        error_handler = integrated_system["error_handler"]
        redis_client = integrated_system["redis_client"]
        
        # Simulate cascading failures
        redis_client.set_cache.side_effect = ConnectionError("Redis unavailable")
        review_agent.acrolinx_agent.check_content.side_effect = \
            TimeoutError("Acrolinx timeout")
            
        # Act
        errors = []
        try:
            await review_agent.review_content("<p>Test content</p>")
        except Exception as e:
            # Handle primary error
            error_result = await error_handler.handle_error(
                e,
                {"component": "review_agent", "operation": "content_review"}
            )
            errors.append(error_result)
            
            # Handle secondary error (Redis)
            try:
                await error_handler._store_error(error_result)
            except Exception as redis_error:
                redis_error_result = await error_handler.handle_error(
                    redis_error,
                    {"component": "redis_client", "operation": "error_storage"}
                )
                errors.append(redis_error_result)
                
        # Assert
        assert len(errors) == 2
        assert any(
            "timeout" in str(e["message"]).lower() for e in errors
        )  # Acrolinx error
        assert any(
            "redis" in str(e["message"]).lower() for e in errors
        )  # Redis error
        
    @patch('logging.Logger.error')
    async def test_error_logging_integration(
        self,
        mock_logger,
        integrated_system
    ):
        """Test error logging across integrated components."""
        # Arrange
        error_handler = integrated_system["error_handler"]
        redis_client = integrated_system["redis_client"]
        
        # Simulate various errors
        errors = [
            ValueError("Validation failed"),
            ConnectionError("Service unavailable"),
            TimeoutError("Operation timed out")
        ]
        
        # Act
        for error in errors:
            await error_handler.handle_error(
                error,
                {"component": "test", "operation": "integration_test"}
            )
            
        # Assert
        assert mock_logger.call_count == len(errors)
        assert redis_client.set_cache.call_count == len(errors)
        
    async def test_recovery_integration(self, integrated_system):
        """Test error recovery across integrated components."""
        # Arrange
        error_handler = integrated_system["error_handler"]
        review_agent = integrated_system["review_agent"]
        
        # Simulate recoverable error
        review_agent.acrolinx_agent.check_content.side_effect = [
            ConnectionError("First attempt failed"),  # First attempt fails
            {"quality_score": 85}  # Second attempt succeeds
        ]
        
        # Act
        try:
            await review_agent.review_content("<p>Test content</p>")
        except Exception as e:
            error_result = await error_handler.handle_error(
                e,
                {"component": "review_agent", "operation": "content_review"}
            )
            
            if "recovery_action" in error_result:
                # Retry the operation
                result = await review_agent.review_content("<p>Test content</p>")
                
        # Assert
        assert "recovery_action" in error_result
        assert result["acrolinx_review"]["quality_score"] == 85 