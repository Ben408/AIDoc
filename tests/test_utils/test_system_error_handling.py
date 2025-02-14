"""
System-wide error handling tests for the AI Documentation System.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import logging
from datetime import datetime

from src.utils.error_handler import ErrorHandler, ErrorSeverity, ErrorCategory
from src.agents.orchestration import OrchestrationAgent
from src.utils.performance_monitor import PerformanceMonitor
from src.utils.documentation_generator import DocumentationGenerator

@pytest.fixture
async def system_components():
    """Setup complete system with all components."""
    # Mock Redis client
    redis_client = Mock()
    redis_client.set_cache = AsyncMock()
    redis_client.get_cache = AsyncMock()
    
    # Initialize components
    error_handler = ErrorHandler(
        redis_client=redis_client,
        notification_url="https://test.notifications.com/webhook"
    )
    
    performance_monitor = PerformanceMonitor(redis_client)
    
    doc_generator = DocumentationGenerator("test_output")
    
    orchestrator = OrchestrationAgent(
        Mock(),  # query_agent
        Mock(),  # drafting_agent
        Mock(),  # review_agent
        redis_client
    )
    
    return {
        "redis_client": redis_client,
        "error_handler": error_handler,
        "performance_monitor": performance_monitor,
        "doc_generator": doc_generator,
        "orchestrator": orchestrator
    }

class TestSystemErrorHandling:
    async def test_system_startup_errors(self, system_components):
        """Test error handling during system startup."""
        # Arrange
        redis_client = system_components["redis_client"]
        error_handler = system_components["error_handler"]
        
        # Simulate Redis connection failure
        redis_client.connect = AsyncMock(
            side_effect=ConnectionError("Redis connection failed")
        )
        
        # Act
        startup_errors = []
        try:
            await redis_client.connect()
        except Exception as e:
            error_result = await error_handler.handle_error(
                e,
                {
                    "component": "system",
                    "operation": "startup",
                    "stage": "redis_connection"
                },
                severity=ErrorSeverity.CRITICAL
            )
            startup_errors.append(error_result)
            
        # Assert
        assert len(startup_errors) == 1
        assert startup_errors[0]["severity"] == ErrorSeverity.CRITICAL.value
        assert "redis connection" in str(startup_errors[0]["message"]).lower()
        
    async def test_concurrent_error_handling(self, system_components):
        """Test handling of concurrent errors across system."""
        # Arrange
        error_handler = system_components["error_handler"]
        orchestrator = system_components["orchestrator"]
        
        # Simulate multiple concurrent operations
        async def simulate_concurrent_operations():
            operations = [
                ("review", "<p>Test content</p>"),
                ("draft", {"topic": "API Guide"}),
                ("query", "How to authenticate?")
            ]
            
            errors = []
            for op_type, data in operations:
                try:
                    await orchestrator.process_request(op_type, {"data": data})
                except Exception as e:
                    error_result = await error_handler.handle_error(
                        e,
                        {
                            "component": "orchestrator",
                            "operation": op_type,
                            "data": str(data)[:50]
                        }
                    )
                    errors.append(error_result)
            return errors
            
        # Act
        errors = await simulate_concurrent_operations()
        
        # Assert
        assert len(errors) > 0
        assert len(set(e["timestamp"] for e in errors)) == len(errors)
        
    async def test_cascading_system_failures(self, system_components):
        """Test handling of cascading system failures."""
        # Arrange
        error_handler = system_components["error_handler"]
        performance_monitor = system_components["performance_monitor"]
        doc_generator = system_components["doc_generator"]
        
        # Simulate resource exhaustion cascade
        async def simulate_cascade():
            cascade_errors = []
            
            # Stage 1: Resource error
            try:
                raise MemoryError("System memory exhausted")
            except Exception as e:
                error1 = await error_handler.handle_error(
                    e,
                    {"component": "system", "operation": "resource_management"}
                )
                cascade_errors.append(error1)
                
                # Stage 2: Performance degradation
                try:
                    await performance_monitor.start_operation(
                        "test_op",
                        "performance_check"
                    )
                except Exception as e2:
                    error2 = await error_handler.handle_error(
                        e2,
                        {"component": "performance_monitor"}
                    )
                    cascade_errors.append(error2)
                    
                    # Stage 3: Documentation generation failure
                    try:
                        await doc_generator.generate_api_documentation()
                    except Exception as e3:
                        error3 = await error_handler.handle_error(
                            e3,
                            {"component": "doc_generator"}
                        )
                        cascade_errors.append(error3)
                        
            return cascade_errors
            
        # Act
        cascade_results = await simulate_cascade()
        
        # Assert
        assert len(cascade_results) == 3
        assert any(
            "memory" in str(e["message"]).lower() for e in cascade_results
        )
        assert any(
            ErrorCategory.RESOURCE_ERROR.value == e["category"] 
            for e in cascade_results
        )
        
    @patch('logging.Logger.error')
    async def test_system_recovery_procedures(
        self,
        mock_logger,
        system_components
    ):
        """Test system-wide recovery procedures."""
        # Arrange
        error_handler = system_components["error_handler"]
        redis_client = system_components["redis_client"]
        
        # Simulate recoverable system error
        redis_client.connect.side_effect = [
            ConnectionError("Initial connection failed"),
            None  # Second attempt succeeds
        ]
        
        # Act
        recovery_attempts = []
        try:
            await redis_client.connect()
        except Exception as e:
            error_result = await error_handler.handle_error(
                e,
                {"component": "system", "operation": "redis_connection"}
            )
            
            if "recovery_action" in error_result:
                try:
                    # Attempt recovery
                    await redis_client.connect()
                    recovery_attempts.append({"status": "success"})
                except Exception as e2:
                    recovery_attempts.append({"status": "failed"})
                    
        # Assert
        assert len(recovery_attempts) == 1
        assert recovery_attempts[0]["status"] == "success"
        assert mock_logger.call_count >= 1 