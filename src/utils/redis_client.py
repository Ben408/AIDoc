"""
Redis client for caching and data persistence.
"""
from typing import Optional, Any, Dict, Union
import json
import logging
from datetime import datetime, timedelta
import aioredis
import pickle

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(
        self,
        redis_url: str,
        default_ttl: int = 3600  # 1 hour default TTL
    ):
        """
        Initialize Redis client.
        
        Args:
            redis_url (str): Redis connection URL
            default_ttl (int): Default time-to-live for cached items in seconds
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self._redis: Optional[aioredis.Redis] = None
        
    async def connect(self) -> None:
        """Establish Redis connection."""
        try:
            self._redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}")
            raise
            
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            
    async def get_cache(
        self,
        key: str,
        deserialize: bool = True
    ) -> Optional[Any]:
        """
        Get cached value.
        
        Args:
            key (str): Cache key
            deserialize (bool): Whether to deserialize the value
            
        Returns:
            Optional[Any]: Cached value if exists
        """
        try:
            value = await self._redis.get(key)
            if value and deserialize:
                return json.loads(value)
            return value
        except Exception as e:
            logger.error(f"Cache retrieval failed for key {key}: {str(e)}")
            return None
            
    async def set_cache(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """
        Set cache value.
        
        Args:
            key (str): Cache key
            value (Any): Value to cache
            ttl (Optional[int]): Time-to-live in seconds
            serialize (bool): Whether to serialize the value
            
        Returns:
            bool: Success status
        """
        try:
            if serialize:
                value = json.dumps(value)
            await self._redis.set(
                key,
                value,
                ex=ttl or self.default_ttl
            )
            return True
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {str(e)}")
            return False
            
    async def cache_review_result(
        self,
        content_hash: str,
        result: Dict,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache review result.
        
        Args:
            content_hash (str): Content hash as key
            result (Dict): Review result to cache
            ttl (Optional[int]): Cache duration
            
        Returns:
            bool: Success status
        """
        key = f"review:{content_hash}"
        return await self.set_cache(key, result, ttl)
        
    async def get_review_cache(
        self,
        content_hash: str
    ) -> Optional[Dict]:
        """
        Get cached review result.
        
        Args:
            content_hash (str): Content hash
            
        Returns:
            Optional[Dict]: Cached review result if exists
        """
        key = f"review:{content_hash}"
        return await self.get_cache(key)
        
    async def cache_acrolinx_result(
        self,
        content_hash: str,
        result: Dict,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache Acrolinx check result.
        
        Args:
            content_hash (str): Content hash as key
            result (Dict): Acrolinx result to cache
            ttl (Optional[int]): Cache duration
            
        Returns:
            bool: Success status
        """
        key = f"acrolinx:{content_hash}"
        return await self.set_cache(key, result, ttl)
        
    async def get_acrolinx_cache(
        self,
        content_hash: str
    ) -> Optional[Dict]:
        """
        Get cached Acrolinx result.
        
        Args:
            content_hash (str): Content hash
            
        Returns:
            Optional[Dict]: Cached Acrolinx result if exists
        """
        key = f"acrolinx:{content_hash}"
        return await self.get_cache(key)
        
    async def cache_query_result(
        self,
        query_hash: str,
        result: Dict,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache query result.
        
        Args:
            query_hash (str): Query hash as key
            result (Dict): Query result to cache
            ttl (Optional[int]): Cache duration
            
        Returns:
            bool: Success status
        """
        key = f"query:{query_hash}"
        return await self.set_cache(key, result, ttl)
        
    async def get_query_cache(
        self,
        query_hash: str
    ) -> Optional[Dict]:
        """
        Get cached query result.
        
        Args:
            query_hash (str): Query hash
            
        Returns:
            Optional[Dict]: Cached query result if exists
        """
        key = f"query:{query_hash}"
        return await self.get_cache(key)
        
    async def clear_cache(self, pattern: str = "*") -> bool:
        """
        Clear cache entries matching pattern.
        
        Args:
            pattern (str): Pattern to match keys
            
        Returns:
            bool: Success status
        """
        try:
            cursor = 0
            while True:
                cursor, keys = await self._redis.scan(
                    cursor,
                    match=pattern
                )
                if keys:
                    await self._redis.delete(*keys)
                if cursor == 0:
                    break
            return True
        except Exception as e:
            logger.error(f"Cache clear failed: {str(e)}")
            return False 