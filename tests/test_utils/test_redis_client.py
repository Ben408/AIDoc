"""
Tests for Redis client implementation.
"""
import pytest
from unittest.mock import Mock, patch
import json
from datetime import datetime

from src.utils.redis_client import RedisClient

@pytest.fixture
async def redis_client():
    client = RedisClient("redis://localhost:6379")
    await client.connect()
    yield client
    await client.disconnect()

@pytest.fixture
def sample_review_result():
    return {
        "quality_score": 85,
        "issues": [
            {
                "type": "style",
                "message": "Consider active voice"
            }
        ],
        "timestamp": datetime.now().isoformat()
    }

@pytest.fixture
def sample_acrolinx_result():
    return {
        "quality_score": 90,
        "issues": [],
        "guidance": {
            "goals": ["clarity"]
        }
    }

class TestRedisClient:
    async def test_cache_review_result(
        self,
        redis_client,
        sample_review_result
    ):
        # Arrange
        content_hash = "test123"
        
        # Act
        success = await redis_client.cache_review_result(
            content_hash,
            sample_review_result
        )
        cached = await redis_client.get_review_cache(content_hash)
        
        # Assert
        assert success is True
        assert cached["quality_score"] == 85
        assert len(cached["issues"]) == 1
        
    async def test_cache_acrolinx_result(
        self,
        redis_client,
        sample_acrolinx_result
    ):
        # Arrange
        content_hash = "test456"
        
        # Act
        success = await redis_client.cache_acrolinx_result(
            content_hash,
            sample_acrolinx_result
        )
        cached = await redis_client.get_acrolinx_cache(content_hash)
        
        # Assert
        assert success is True
        assert cached["quality_score"] == 90
        assert "clarity" in cached["guidance"]["goals"]
        
    async def test_cache_expiration(self, redis_client):
        # Arrange
        key = "test789"
        value = {"test": "data"}
        ttl = 1  # 1 second
        
        # Act
        await redis_client.set_cache(key, value, ttl)
        import asyncio
        await asyncio.sleep(1.1)  # Wait for expiration
        cached = await redis_client.get_cache(key)
        
        # Assert
        assert cached is None
        
    async def test_clear_cache(
        self,
        redis_client,
        sample_review_result,
        sample_acrolinx_result
    ):
        # Arrange
        await redis_client.cache_review_result("test1", sample_review_result)
        await redis_client.cache_acrolinx_result("test2", sample_acrolinx_result)
        
        # Act
        success = await redis_client.clear_cache()
        
        # Assert
        assert success is True
        assert await redis_client.get_review_cache("test1") is None
        assert await redis_client.get_acrolinx_cache("test2") is None
        
    async def test_error_handling(self, redis_client):
        # Arrange
        redis_client._redis = None  # Simulate disconnection
        
        # Act & Assert
        with pytest.raises(Exception):
            await redis_client.get_cache("test") 