"""
Tests for the Performance Monitor system.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import time
from datetime import datetime

from src.utils.performance_monitor import PerformanceMonitor

@pytest.fixture
def redis_client():
    client = Mock()
    client.set_cache = AsyncMock()
    client.get_cache = AsyncMock()
    return client

@pytest.fixture
def performance_monitor(redis_client):
    return PerformanceMonitor(redis_client)

class TestPerformanceMonitor:
    async def test_start_operation_tracking(self, performance_monitor):
        """Test starting operation tracking."""
        # Arrange
        operation_id = "test_op_1"
        operation_type = "content_review"
        
        # Act
        await performance_monitor.start_operation(operation_id, operation_type)
        
        # Assert
        metrics = performance_monitor.metrics[operation_id]
        assert metrics["type"] == operation_type
        assert isinstance(metrics["start_time"], datetime)
        assert "memory_start" in metrics
        assert "cpu_start" in metrics
        
    async def test_end_operation_metrics(self, performance_monitor):
        """Test operation completion metrics."""
        # Arrange
        operation_id = "test_op_2"
        await performance_monitor.start_operation(operation_id, "content_draft")
        
        # Add small delay to simulate work
        await asyncio.sleep(0.1)
        
        # Act
        result = await performance_monitor.end_operation(operation_id)
        
        # Assert
        assert result["duration"] > 0
        assert result["memory_end"] > 0
        assert result["cpu_end"] >= 0
        assert result["status"] == "success"
        
    async def test_redis_metrics_storage(
        self,
        performance_monitor,
        redis_client
    ):
        """Test metrics storage in Redis."""
        # Arrange
        operation_id = "test_op_3"
        
        # Act
        await performance_monitor.start_operation(operation_id, "query")
        metrics = await performance_monitor.end_operation(operation_id)
        
        # Assert
        redis_client.set_cache.assert_called_once()
        call_args = redis_client.set_cache.call_args[0]
        assert f"metrics:{operation_id}" in call_args[0]
        assert isinstance(call_args[1], dict)
        
    @patch('psutil.Process')
    async def test_resource_monitoring(self, mock_process, performance_monitor):
        """Test system resource monitoring."""
        # Arrange
        mock_process.return_value.memory_info.return_value.rss = 1000000
        mock_process.return_value.cpu_percent.return_value = 5.0
        
        # Act
        await performance_monitor.start_operation("test_op_4", "review")
        metrics = await performance_monitor.end_operation("test_op_4")
        
        # Assert
        assert metrics["memory_start"] == 1000000
        assert metrics["cpu_start"] == 5.0
        
    async def test_multiple_operations(self, performance_monitor):
        """Test handling multiple concurrent operations."""
        # Arrange
        operations = [
            ("op1", "review"),
            ("op2", "draft"),
            ("op3", "query")
        ]
        
        # Act
        for op_id, op_type in operations:
            await performance_monitor.start_operation(op_id, op_type)
            
        results = []
        for op_id, _ in operations:
            result = await performance_monitor.end_operation(op_id)
            results.append(result)
            
        # Assert
        assert len(results) == 3
        assert all(r["status"] == "success" for r in results)
        
    async def test_error_handling(self, performance_monitor):
        """Test handling of monitoring errors."""
        # Act & Assert
        with pytest.raises(ValueError):
            await performance_monitor.end_operation("nonexistent_op")
            
    async def test_long_running_operation(self, performance_monitor):
        """Test monitoring of long-running operations."""
        # Arrange
        operation_id = "long_op"
        
        # Act
        await performance_monitor.start_operation(operation_id, "long_process")
        await asyncio.sleep(1.1)  # Simulate long operation
        result = await performance_monitor.end_operation(operation_id)
        
        # Assert
        assert result["duration"] >= 1.0 