"""
OpenAI API client for AI model interactions.
"""
from typing import Dict, Any, Optional, List
import asyncio
import logging
import time
from datetime import datetime

import openai
from openai import AsyncOpenAI
from config import settings

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.fallback_model = settings.OPENAI_FALLBACK_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.rate_limit = settings.OPENAI_RATE_LIMIT
        self.request_lock = asyncio.Lock()
        self.request_times: List[float] = []
        
    async def generate_completion(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
    ) -> str:
        """
        Generate a completion using OpenAI's API with retry and fallback logic.
        
        Args:
            system_prompt (str): System message defining the AI's role
            user_message (str): User's input message
            context (Dict[str, Any], optional): Additional context
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            str: Generated completion text
        """
        start_time = datetime.now()
        
        try:
            # Check rate limiting
            async with self.request_lock:
                await self._check_rate_limit()
                
            messages = self._prepare_messages(system_prompt, user_message, context)
            
            # Try primary model with retries
            for attempt in range(max_retries):
                try:
                    response = await self._make_request(messages, self.model)
                    await self._log_success(start_time)
                    return response
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.warning(
                            f"Primary model failed, trying fallback model",
                            extra={"error": str(e)}
                        )
                        # Try fallback model
                        response = await self._make_request(
                            messages, 
                            self.fallback_model
                        )
                        await self._log_success(
                            start_time, 
                            model=self.fallback_model
                        )
                        return response
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    await asyncio.sleep(2 ** attempt)
                    
        except Exception as e:
            await self._log_error(str(e), start_time)
            raise
            
    async def _make_request(
        self, 
        messages: List[Dict[str, str]], 
        model: str
    ) -> str:
        """Make the actual API request."""
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.choices[0].message.content
        
    def _prepare_messages(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """Prepare messages for the API request."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        if context:
            context_message = f"\nAdditional context:\n{str(context)}"
            messages.append({"role": "user", "content": context_message})
            
        return messages
        
    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting."""
        current_time = time.time()
        self.request_times = [
            t for t in self.request_times 
            if current_time - t < 60
        ]  # Keep only last minute
        
        if len(self.request_times) >= self.rate_limit:
            raise Exception("Rate limit exceeded")
            
        self.request_times.append(current_time)
        
    async def _log_success(
        self, 
        start_time: datetime, 
        model: Optional[str] = None
    ) -> None:
        """Log successful API call."""
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"OpenAI API call successful",
            extra={
                "model": model or self.model,
                "duration": duration,
                "status": "success"
            }
        )
        
    async def _log_error(self, error: str, start_time: datetime) -> None:
        """Log API call error."""
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(
            f"OpenAI API call failed",
            extra={
                "error": error,
                "duration": duration,
                "status": "error"
            }
        ) 