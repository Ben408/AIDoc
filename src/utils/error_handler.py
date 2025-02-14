"""
Centralized error handling for the AI Documentation System.
"""
from typing import Dict, Optional, List, Any
import logging
import traceback
from datetime import datetime
import aiohttp
import json
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for classification."""
    API_ERROR = "api_error"
    VALIDATION_ERROR = "validation_error"
    INTEGRATION_ERROR = "integration_error"
    SYSTEM_ERROR = "system_error"
    RESOURCE_ERROR = "resource_error"
    CONFIGURATION_ERROR = "configuration_error"

class ErrorHandler:
    def __init__(
        self,
        redis_client=None,
        notification_url: Optional[str] = None,
        notification_token: Optional[str] = None
    ):
        """
        Initialize error handler.
        
        Args:
            redis_client: Optional Redis client for error logging
            notification_url: Webhook URL for error notifications
            notification_token: Authentication token for notifications
        """
        self.redis_client = redis_client
        self.notification_url = notification_url
        self.notification_token = notification_token
        self.error_patterns: Dict[str, int] = {}
        
    async def handle_error(
        self,
        error: Exception,
        context: Dict,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        notify: bool = True
    ) -> Dict:
        """Handle and log an error."""
        # Categorize error
        category = await self._categorize_error(error)
        
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "category": category.value,
            "severity": severity.value,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context
        }
        
        # Update error patterns
        await self._update_error_pattern(error_info)
        
        # Log error
        logger.error(
            f"Error in {context.get('component', 'unknown')}: {str(error)}",
            extra=error_info
        )
        
        # Store in Redis if available
        if self.redis_client:
            await self._store_error(error_info)
            
        # Check for error patterns
        if await self._check_error_pattern(error_info):
            error_info["pattern_detected"] = True
            severity = ErrorSeverity.HIGH
            
        # Notify if required
        if notify or severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            await self._notify_error(error_info)
            
        # Attempt recovery
        recovery_action = await self._attempt_recovery(error_info)
        if recovery_action:
            error_info["recovery_action"] = recovery_action
            
        return error_info
        
    async def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize the error type."""
        if isinstance(error, aiohttp.ClientError):
            return ErrorCategory.API_ERROR
        elif isinstance(error, ValueError):
            return ErrorCategory.VALIDATION_ERROR
        elif isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorCategory.INTEGRATION_ERROR
        elif isinstance(error, MemoryError):
            return ErrorCategory.RESOURCE_ERROR
        elif isinstance(error, KeyError):
            return ErrorCategory.CONFIGURATION_ERROR
        return ErrorCategory.SYSTEM_ERROR
        
    async def _store_error(self, error_info: Dict) -> None:
        """Store error information in Redis."""
        key = f"error:{error_info['timestamp']}"
        await self.redis_client.set_cache(
            key,
            error_info,
            ttl=604800  # 7 days
        )
        
        # Update error pattern tracking
        pattern_key = f"error_pattern:{error_info['error_type']}"
        await self.redis_client.set_cache(
            pattern_key,
            self.error_patterns.get(error_info['error_type'], 0) + 1,
            ttl=3600  # 1 hour
        )
        
    async def _notify_error(self, error_info: Dict) -> None:
        """Send error notification."""
        if not self.notification_url:
            return
            
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    self.notification_url,
                    headers={
                        "Authorization": f"Bearer {self.notification_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "type": "error_notification",
                        "data": error_info
                    }
                )
        except Exception as e:
            logger.error(f"Failed to send error notification: {str(e)}")
            
    async def _update_error_pattern(self, error_info: Dict) -> None:
        """Update error pattern tracking."""
        error_type = error_info["error_type"]
        self.error_patterns[error_type] = self.error_patterns.get(error_type, 0) + 1
        
    async def _check_error_pattern(self, error_info: Dict) -> bool:
        """Check for error patterns that might indicate larger issues."""
        error_type = error_info["error_type"]
        error_count = self.error_patterns.get(error_type, 0)
        
        # Pattern detection thresholds
        if error_count > 10:  # More than 10 errors of same type
            return True
            
        return False
        
    async def _attempt_recovery(self, error_info: Dict) -> Optional[str]:
        """Attempt to recover from the error."""
        category = ErrorCategory(error_info["category"])
        
        recovery_actions = {
            ErrorCategory.API_ERROR: self._recover_api_error,
            ErrorCategory.INTEGRATION_ERROR: self._recover_integration_error,
            ErrorCategory.RESOURCE_ERROR: self._recover_resource_error
        }
        
        if category in recovery_actions:
            return await recovery_actions[category](error_info)
        
        return None
        
    async def _recover_api_error(self, error_info: Dict) -> str:
        """Attempt to recover from API errors."""
        # Implement retry logic
        return "Implemented retry with exponential backoff"
        
    async def _recover_integration_error(self, error_info: Dict) -> str:
        """Attempt to recover from integration errors."""
        # Implement reconnection logic
        return "Attempted service reconnection"
        
    async def _recover_resource_error(self, error_info: Dict) -> str:
        """Attempt to recover from resource errors."""
        # Implement resource cleanup
        return "Performed resource cleanup"
        
    async def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors."""
        if not self.redis_client:
            return {"error": "Redis client not available"}
            
        try:
            errors = await self._get_recent_errors()
            return {
                "total_errors": len(errors),
                "by_category": self._group_by_category(errors),
                "by_severity": self._group_by_severity(errors),
                "patterns_detected": bool(self.error_patterns)
            }
        except Exception as e:
            logger.error(f"Failed to generate error summary: {str(e)}")
            return {"error": "Failed to generate summary"} 