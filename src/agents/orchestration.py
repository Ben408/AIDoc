"""
Orchestration Agent for AI Documentation System

This agent coordinates workflows between different specialized agents (Query, Draft, Review)
and manages the overall documentation generation process.

Key Features:
- Complete content workflow orchestration (new content, updates, reviews)
- Integration with external data sources (JIRA, Confluence)
- Quality assurance and metrics tracking
- Performance monitoring and error handling
- Caching and optimization

Workflow Types:
1. New Content Generation
   - Context retrieval
   - Content drafting
   - Quality review
   - Performance tracking

2. Content Updates
   - Original content retrieval
   - Context gathering
   - Update generation
   - Quality verification

3. Content Review
   - Content analysis
   - Style checking
   - Quality metrics
   - Improvement suggestions

Usage Example:
    orchestrator = OrchestrationAgent(
        query_agent=query_agent,
        drafting_agent=drafting_agent,
        review_agent=review_agent,
        redis_client=redis_client,
        error_handler=error_handler,
        performance_monitor=performance_monitor
    )

    # Start a new content workflow
    result = await orchestrator.orchestrate_content_workflow(
        workflow_type="new_content",
        content_data={
            "topic": "API Documentation",
            "template": "api_template"
        },
        context={
            "jira_ids": ["PROJ-123", "PROJ-124"],
            "confluence_ids": ["PAGE-456"]
        }
    )
"""
from typing import Dict, Optional, Any
import logging
from datetime import datetime
import asyncio

from .review import ReviewAgent
from .drafting import DraftingAgent
from .query_response import QueryResponseAgent
from .acrolinx_agent import AcrolinxAgent
from ..utils.redis_client import RedisClient
from ..utils.error_handler import ErrorHandler, ErrorSeverity
from ..utils.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)

class OrchestrationAgent:
    def __init__(
        self,
        query_agent: QueryResponseAgent,
        drafting_agent: DraftingAgent,
        review_agent: ReviewAgent,
        redis_client: RedisClient,
        error_handler: Optional[ErrorHandler] = None,
        performance_monitor: Optional[PerformanceMonitor] = None
    ):
        """
        Initialize the Orchestration Agent.

        Args:
            query_agent: Agent for handling user queries and responses
            drafting_agent: Agent for content generation and updates
            review_agent: Agent for content review and quality checks
            redis_client: Redis client for caching and data storage
            error_handler: Optional error handling system
            performance_monitor: Optional performance monitoring system
        """
        self.query_agent = query_agent
        self.drafting_agent = drafting_agent
        self.review_agent = review_agent
        self.redis_client = redis_client
        self.error_handler = error_handler
        self.performance_monitor = performance_monitor
        
    async def process_request(
        self,
        request_type: str,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process incoming requests and route to appropriate agent.
        
        Args:
            request_type: Type of request (review, draft, query)
            request_data: Request parameters and data
            
        Returns:
            Dict containing operation results
        """
        operation_id = f"{request_type}_{datetime.now().isoformat()}"
        
        try:
            if self.performance_monitor:
                await self.performance_monitor.start_operation(
                    operation_id,
                    request_type
                )
                
            # Check cache first
            cache_key = await self._generate_cache_key(request_type, request_data)
            cached_result = await self.redis_client.get_cache(cache_key)
            if cached_result:
                return cached_result
                
            # Process request based on type
            result = await self._route_request(request_type, request_data)
            
            # Cache successful results
            await self.redis_client.set_cache(cache_key, result)
            
            if self.performance_monitor:
                await self.performance_monitor.end_operation(
                    operation_id,
                    status="success"
                )
                
            return result
            
        except Exception as e:
            if self.error_handler:
                await self.error_handler.handle_error(
                    e,
                    context={
                        "component": "orchestration",
                        "request_type": request_type,
                        "operation_id": operation_id
                    },
                    severity=ErrorSeverity.HIGH
                )
                
            if self.performance_monitor:
                await self.performance_monitor.end_operation(
                    operation_id,
                    status="error"
                )
                
            raise
            
    async def _route_request(
        self,
        request_type: str,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route request to appropriate agent."""
        if request_type == "review":
            return await self.review_agent.review_content(
                request_data["content"],
                content_type=request_data.get("content_type", "text/html"),
                reference=request_data.get("reference")
            )
            
        elif request_type == "draft":
            return await self.drafting_agent.create_draft(
                request_data["topic"],
                context=request_data.get("context"),
                template=request_data.get("template")
            )
            
        elif request_type == "query":
            return await self.query_agent.process_query(
                request_data["query"],
                context=request_data.get("context"),
                session_id=request_data.get("session_id")
            )
            
        else:
            raise ValueError(f"Unknown request type: {request_type}")
            
    async def _generate_cache_key(
        self,
        request_type: str,
        request_data: Dict[str, Any]
    ) -> str:
        """Generate cache key for request."""
        # Remove volatile fields from cache key generation
        cache_data = request_data.copy()
        cache_data.pop("session_id", None)
        cache_data.pop("reference", None)
        
        key_parts = [
            request_type,
            str(hash(frozenset(cache_data.items())))
        ]
        return ":".join(key_parts)
        
    async def get_system_status(self) -> Dict[str, Any]:
        """Get system status including performance metrics."""
        status = {
            "agents": {
                "review": self.review_agent.is_available(),
                "draft": self.drafting_agent.is_available(),
                "query": self.query_agent.is_available()
            },
            "cache": await self.redis_client.ping()
        }
        
        if self.performance_monitor:
            status["performance"] = await self.performance_monitor.get_metrics_summary()
            
        return status 

    async def orchestrate_content_workflow(
        self,
        workflow_type: str,
        content_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate a complete content workflow.

        This method manages the entire process from data retrieval to final review,
        coordinating between different specialized agents.

        Args:
            workflow_type: Type of workflow ("new_content", "update", "review")
            content_data: Dictionary containing content and metadata
                - For new_content: {"topic": str, "template": str}
                - For update: {"content": str, "updates": Dict}
                - For review: {"content": str}
            context: Optional additional context
                - jira_ids: List of JIRA ticket IDs
                - confluence_ids: List of Confluence page IDs
                - additional_context: Any other context

        Returns:
            Dictionary containing:
                - workflow_type: Type of workflow completed
                - content: Generated or reviewed content
                - quality_metrics: Quality assessment results
                - metadata: Workflow metadata and context information

        Raises:
            ValueError: If workflow_type is unknown
            Exception: For any other errors during processing
        """
        operation_id = f"workflow_{datetime.now().isoformat()}"
        
        try:
            if self.performance_monitor:
                await self.performance_monitor.start_operation(
                    operation_id,
                    f"workflow_{workflow_type}"
                )
                
            # Step 1: Data Retrieval
            retrieval_data = await self._retrieve_context_data(
                content_data,
                context
            )
            
            # Step 2: Content Processing
            if workflow_type == "new_content":
                result = await self.drafting_agent.create_draft(
                    content_data["topic"],
                    context=retrieval_data
                )
            elif workflow_type == "update":
                result = await self.drafting_agent.update_content(
                    content_data["content"],
                    updates=content_data["updates"],
                    context=retrieval_data
                )
            elif workflow_type == "review":
                result = await self.review_agent.review_content(
                    content_data["content"],
                    context=retrieval_data
                )
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")
                
            # Step 3: Quality Check
            quality_result = await self._check_content_quality(result)
            
            # Step 4: Store Results
            workflow_result = {
                "workflow_type": workflow_type,
                "content": result,
                "quality_metrics": quality_result,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "context_used": retrieval_data.get("sources", [])
                }
            }
            
            if self.performance_monitor:
                await self.performance_monitor.end_operation(
                    operation_id,
                    status="success"
                )
                
            return workflow_result
            
        except Exception as e:
            if self.error_handler:
                await self.error_handler.handle_error(
                    e,
                    context={
                        "component": "orchestration",
                        "workflow_type": workflow_type,
                        "operation_id": operation_id
                    }
                )
            raise
            
    async def _retrieve_context_data(
        self,
        content_data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Retrieve context data from various sources.

        Gathers relevant information from JIRA, Confluence, and other sources
        to provide context for content generation or review.

        Args:
            content_data: Content-related data
            context: Additional context information

        Returns:
            Dictionary containing:
                - sources: List of data sources and their content
                - original_context: Original context provided
        """
        sources = []
        
        # Get JIRA data if needed
        if context and context.get("jira_ids"):
            jira_data = await self._fetch_jira_data(context["jira_ids"])
            sources.append({"type": "jira", "data": jira_data})
            
        # Get Confluence data if needed
        if context and context.get("confluence_ids"):
            confluence_data = await self._fetch_confluence_data(
                context["confluence_ids"]
            )
            sources.append({"type": "confluence", "data": confluence_data})
            
        return {
            "sources": sources,
            "original_context": context
        }
        
    async def _check_content_quality(
        self,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive quality checks on content.

        Evaluates content quality using multiple metrics including
        readability, consistency, and completeness.

        Args:
            content: Content to be evaluated

        Returns:
            Dictionary containing quality metrics:
                - quality_score: Overall quality score
                - readability_score: Content readability assessment
                - consistency_score: Style consistency check
                - completeness_score: Content completeness evaluation
                - suggestions: List of improvement suggestions
        """
        quality_result = await self.review_agent.check_quality(content)
        
        # Add quality metrics
        quality_result.update({
            "readability_score": await self._calculate_readability(content),
            "consistency_score": await self._check_style_consistency(content),
            "completeness_score": await self._check_completeness(content)
        })
        
        return quality_result
        
    async def get_workflow_status(
        self,
        workflow_id: str
    ) -> Dict[str, Any]:
        """
        Retrieve status and metrics for a specific workflow.

        Args:
            workflow_id: Unique identifier for the workflow

        Returns:
            Dictionary containing:
                - status: Current workflow status
                - performance: Performance metrics if available
                - error: Error message if workflow not found

        Raises:
            Exception: If error occurs during status retrieval
        """
        try:
            status = await self.redis_client.get_cache(f"workflow:{workflow_id}")
            if not status:
                return {"error": "Workflow not found"}
                
            # Add performance metrics if available
            if self.performance_monitor:
                metrics = await self.performance_monitor.get_metrics_summary(
                    f"workflow_{workflow_id}"
                )
                status["performance"] = metrics
                
            return status
            
        except Exception as e:
            if self.error_handler:
                await self.error_handler.handle_error(
                    e,
                    context={
                        "component": "orchestration",
                        "operation": "get_status",
                        "workflow_id": workflow_id
                    }
                )
            raise 