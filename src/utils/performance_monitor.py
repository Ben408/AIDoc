"""
Performance monitoring for the AI Documentation System.
"""
from typing import Dict, Optional, List, Any
import logging
from datetime import datetime
import asyncio
import psutil
import json
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self, redis_client=None):
        """
        Initialize performance monitor.
        
        Args:
            redis_client: Optional Redis client for metrics storage
        """
        self.redis_client = redis_client
        self.metrics: Dict = {}
        self.thresholds = {
            "memory_warning": 85.0,  # 85% memory usage
            "cpu_warning": 75.0,     # 75% CPU usage
            "duration_warning": 10.0  # 10 seconds
        }
        
    @asynccontextmanager
    async def track(self, operation_name: str) -> None:
        """Context manager for tracking operation performance."""
        operation_id = f"{operation_name}_{datetime.now().isoformat()}"
        try:
            await self.start_operation(operation_id, operation_name)
            yield
        finally:
            await self.end_operation(operation_id)
            
    async def start_operation(
        self,
        operation_id: str,
        operation_type: str
    ) -> None:
        """Start tracking an operation."""
        self.metrics[operation_id] = {
            "type": operation_type,
            "start_time": datetime.now(),
            "memory_start": psutil.Process().memory_info().rss,
            "cpu_start": psutil.Process().cpu_percent(),
            "thread_count": psutil.Process().num_threads()
        }
        
    async def end_operation(
        self,
        operation_id: str,
        status: str = "success"
    ) -> Dict:
        """End tracking an operation and return metrics."""
        if operation_id not in self.metrics:
            raise ValueError(f"Unknown operation ID: {operation_id}")
            
        metrics = self.metrics[operation_id]
        end_time = datetime.now()
        
        metrics.update({
            "end_time": end_time,
            "duration": (end_time - metrics["start_time"]).total_seconds(),
            "memory_end": psutil.Process().memory_info().rss,
            "cpu_end": psutil.Process().cpu_percent(),
            "thread_count_end": psutil.Process().num_threads(),
            "status": status
        })
        
        # Calculate derived metrics
        metrics["memory_used"] = metrics["memory_end"] - metrics["memory_start"]
        metrics["cpu_average"] = (metrics["cpu_start"] + metrics["cpu_end"]) / 2
        
        # Check thresholds
        await self._check_thresholds(metrics)
        
        # Store metrics
        await self._store_metrics(operation_id, metrics)
        return metrics
        
    async def _check_thresholds(self, metrics: Dict) -> None:
        """Check if metrics exceed warning thresholds."""
        warnings = []
        
        if metrics["cpu_average"] > self.thresholds["cpu_warning"]:
            warnings.append(f"High CPU usage: {metrics['cpu_average']}%")
            
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > self.thresholds["memory_warning"]:
            warnings.append(f"High memory usage: {memory_percent}%")
            
        if metrics["duration"] > self.thresholds["duration_warning"]:
            warnings.append(
                f"Long operation duration: {metrics['duration']} seconds"
            )
            
        if warnings:
            logger.warning(
                f"Performance warnings for {metrics['type']}: {warnings}"
            )
            
    async def _store_metrics(
        self,
        operation_id: str,
        metrics: Dict
    ) -> None:
        """Store metrics in Redis if available."""
        if self.redis_client:
            await self.redis_client.set_cache(
                f"metrics:{operation_id}",
                metrics,
                ttl=86400  # 24 hours
            )
            
    async def get_metrics_summary(
        self,
        operation_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get summary of performance metrics."""
        if not self.redis_client:
            return {"error": "Redis client not available"}
            
        try:
            # Get all metrics for the specified type
            metrics_list = []
            async for key in self.redis_client.scan_iter("metrics:*"):
                metrics = await self.redis_client.get_cache(key)
                if metrics and (
                    not operation_type or 
                    metrics["type"] == operation_type
                ):
                    metrics_list.append(metrics)
                    
            return {
                "total_operations": len(metrics_list),
                "average_duration": self._calculate_average(
                    metrics_list,
                    "duration"
                ),
                "average_memory": self._calculate_average(
                    metrics_list,
                    "memory_used"
                ),
                "average_cpu": self._calculate_average(
                    metrics_list,
                    "cpu_average"
                ),
                "success_rate": self._calculate_success_rate(metrics_list),
                "warnings": self._collect_warnings(metrics_list)
            }
        except Exception as e:
            logger.error(f"Failed to generate metrics summary: {str(e)}")
            return {"error": "Failed to generate summary"}
            
    def _calculate_average(
        self,
        metrics_list: List[Dict],
        field: str
    ) -> float:
        """Calculate average value for a metric field."""
        values = [m[field] for m in metrics_list if field in m]
        return sum(values) / len(values) if values else 0.0
        
    def _calculate_success_rate(self, metrics_list: List[Dict]) -> float:
        """Calculate operation success rate."""
        if not metrics_list:
            return 0.0
        successes = sum(
            1 for m in metrics_list if m.get("status") == "success"
        )
        return (successes / len(metrics_list)) * 100
        
    def _collect_warnings(self, metrics_list: List[Dict]) -> List[str]:
        """Collect all warnings from metrics."""
        warnings = []
        for metrics in metrics_list:
            if metrics.get("warnings"):
                warnings.extend(metrics["warnings"])
        return warnings 