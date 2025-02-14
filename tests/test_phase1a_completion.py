"""
System-wide tests to verify Phase 1A completion requirements.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import logging
from datetime import datetime

from src.agents.orchestration import OrchestrationAgent
from src.agents.review import ReviewAgent
from src.agents.drafting import DraftingAgent
from src.agents.query_response import QueryResponseAgent
from src.utils.error_handler import ErrorHandler
from src.utils.performance_monitor import PerformanceMonitor
from src.utils.documentation_generator import DocumentationGenerator

@pytest.fixture
async def system_components():
    """Setup complete system with all Phase 1A components."""
    redis_client = Mock()
    error_handler = ErrorHandler(redis_client)
    performance_monitor = PerformanceMonitor(redis_client)
    
    query_agent = QueryResponseAgent(redis_client)
    drafting_agent = DraftingAgent(redis_client)
    review_agent = ReviewAgent(redis_client)
    
    orchestrator = OrchestrationAgent(
        query_agent,
        drafting_agent,
        review_agent,
        redis_client,
        error_handler,
        performance_monitor
    )
    
    return {
        "orchestrator": orchestrator,
        "query_agent": query_agent,
        "drafting_agent": drafting_agent,
        "review_agent": review_agent,
        "error_handler": error_handler,
        "performance_monitor": performance_monitor,
        "redis_client": redis_client
    }

class TestPhase1ACompletion:
    """Verify all Phase 1A requirements are met."""
    
    async def test_complete_documentation_workflow(self, system_components):
        """Test end-to-end documentation workflow."""
        orchestrator = system_components["orchestrator"]
        
        # Test new content workflow
        content_result = await orchestrator.orchestrate_content_workflow(
            workflow_type="new_content",
            content_data={
                "topic": "API Authentication",
                "template": "api_docs"
            },
            context={
                "jira_ids": ["AUTH-123"],
                "confluence_ids": ["DOC-456"]
            }
        )
        
        assert "content" in content_result
        assert "quality_metrics" in content_result
        assert content_result["workflow_type"] == "new_content"
        
    async def test_retrieval_integration(self, system_components):
        """Test JIRA and Confluence data retrieval."""
        orchestrator = system_components["orchestrator"]
        
        context_data = await orchestrator._retrieve_context_data(
            content_data={},
            context={
                "jira_ids": ["PROJ-123"],
                "confluence_ids": ["PAGE-456"]
            }
        )
        
        assert "sources" in context_data
        assert any(s["type"] == "jira" for s in context_data["sources"])
        assert any(s["type"] == "confluence" for s in context_data["sources"])
        
    async def test_error_handling_integration(self, system_components):
        """Test error handling across system."""
        error_handler = system_components["error_handler"]
        
        error_result = await error_handler.handle_error(
            Exception("Test error"),
            context={
                "component": "test",
                "operation": "phase1a_verification"
            }
        )
        
        assert "error_id" in error_result
        assert "timestamp" in error_result
        
    async def test_performance_monitoring(self, system_components):
        """Test performance monitoring integration."""
        monitor = system_components["performance_monitor"]
        
        await monitor.start_operation("test_op", "verification")
        metrics = await monitor.end_operation("test_op")
        
        assert "duration" in metrics
        assert "memory_used" in metrics
        assert "cpu_average" in metrics
        
    async def test_content_quality_checks(self, system_components):
        """Test content quality verification."""
        review_agent = system_components["review_agent"]
        
        quality_result = await review_agent.check_quality({
            "content": "Test API documentation content",
            "type": "api_docs"
        })
        
        assert "quality_score" in quality_result
        assert "readability_score" in quality_result
        assert "consistency_score" in quality_result
        
    async def test_caching_mechanism(self, system_components):
        """Test Redis caching integration."""
        redis_client = system_components["redis_client"]
        
        # Test cache operations
        await redis_client.set_cache("test_key", {"data": "test"})
        cached_data = await redis_client.get_cache("test_key")
        
        assert cached_data is not None
        assert "data" in cached_data 