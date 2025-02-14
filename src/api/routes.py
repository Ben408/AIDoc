"""
API routes for the documentation system.
"""
from typing import Dict, Any, Optional
import logging
from functools import wraps
from datetime import datetime

from flask import Flask, request, jsonify
from jose import jwt
from werkzeug.exceptions import HTTPException

from ..agents.orchestration import OrchestrationAgent
from ..utils.redis_client import RedisClient
from config import settings

logger = logging.getLogger(__name__)
app = Flask(__name__)
orchestrator: OrchestrationAgent = None
redis_client: RedisClient = None

def require_auth(f):
    """Authentication middleware."""
    @wraps(f)
    async def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid authorization token"}), 401
            
        try:
            token = auth_header.split(' ')[1]
            jwt.decode(
                token, 
                settings.JWT_SECRET, 
                algorithms=["HS256"]
            )
        except Exception as e:
            return jsonify({"error": "Invalid token"}), 401
            
        return await f(*args, **kwargs)
    return decorated

def rate_limit(f):
    """Rate limiting middleware."""
    @wraps(f)
    async def decorated(*args, **kwargs):
        client_ip = request.remote_addr
        key = f"rate_limit:api:{client_ip}"
        
        try:
            count = await redis_client.get(key) or 0
            if int(count) >= settings.API_RATE_LIMIT:
                return jsonify({"error": "Rate limit exceeded"}), 429
                
            await redis_client.set(
                key,
                int(count) + 1,
                expiry=settings.API_RATE_LIMIT_WINDOW
            )
            
        except Exception as e:
            logger.error(f"Rate limiting error: {str(e)}")
            # Continue processing if rate limiting fails
            
        return await f(*args, **kwargs)
    return decorated

@app.route("/api/query", methods=["POST"])
@require_auth
@rate_limit
async def handle_query():
    """Handle documentation queries."""
    start_time = datetime.now()
    
    try:
        data = request.get_json()
        if not data or "query" not in data:
            return jsonify({"error": "Missing query parameter"}), 400
            
        response = await orchestrator.process_request("query", data)
        
        await _log_request(
            "query", 
            data, 
            start_time, 
            status="success"
        )
        return jsonify(response)
        
    except Exception as e:
        await _log_request(
            "query", 
            request.get_json(), 
            start_time,
            status="error",
            error=str(e)
        )
        return handle_error(e)

@app.route("/api/draft", methods=["POST"])
@require_auth
@rate_limit
async def handle_draft_request():
    """Handle documentation draft requests."""
    start_time = datetime.now()
    
    try:
        data = request.get_json()
        if not data or "content" not in data:
            return jsonify({"error": "Missing content parameter"}), 400
            
        response = await orchestrator.process_request("draft", data)
        
        await _log_request(
            "draft", 
            data, 
            start_time, 
            status="success"
        )
        return jsonify(response)
        
    except Exception as e:
        await _log_request(
            "draft", 
            request.get_json(), 
            start_time,
            status="error",
            error=str(e)
        )
        return handle_error(e)

@app.route("/api/review", methods=["POST"])
@require_auth
@rate_limit
async def handle_review_request():
    """Handle documentation review requests."""
    start_time = datetime.now()
    
    try:
        data = request.get_json()
        if not data or "content" not in data:
            return jsonify({"error": "Missing content parameter"}), 400
            
        response = await orchestrator.process_request("review", data)
        
        await _log_request(
            "review", 
            data, 
            start_time, 
            status="success"
        )
        return jsonify(response)
        
    except Exception as e:
        await _log_request(
            "review", 
            request.get_json(), 
            start_time,
            status="error",
            error=str(e)
        )
        return handle_error(e)

def handle_error(error: Exception) -> tuple:
    """Handle and format error responses."""
    if isinstance(error, HTTPException):
        return jsonify({"error": error.description}), error.code
        
    logger.error(f"Unexpected error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

async def _log_request(
    request_type: str,
    data: Dict[str, Any],
    start_time: datetime,
    status: str,
    error: Optional[str] = None
) -> None:
    """Log API request details."""
    duration = (datetime.now() - start_time).total_seconds()
    log_data = {
        "request_type": request_type,
        "duration": duration,
        "status": status,
        "client_ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent")
    }
    
    if error:
        log_data["error"] = error
        logger.error("API request failed", extra=log_data)
    else:
        logger.info("API request successful", extra=log_data)

def init_app(
    orchestration_agent: OrchestrationAgent,
    redis_client_instance: RedisClient
) -> Flask:
    """
    Initialize the Flask application with required dependencies.
    
    Args:
        orchestration_agent (OrchestrationAgent): Configured orchestration agent
        redis_client_instance (RedisClient): Configured Redis client
        
    Returns:
        Flask: Configured Flask application
    """
    global orchestrator, redis_client
    orchestrator = orchestration_agent
    redis_client = redis_client_instance
    return app 