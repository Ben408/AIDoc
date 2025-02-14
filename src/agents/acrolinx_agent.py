"""
Acrolinx integration agent for content quality checks.
"""
from typing import Dict, List, Optional
import logging
import aiohttp
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class AcrolinxAgent:
    def __init__(
        self,
        api_url: str,
        api_token: str,
        guidance_profile: Optional[str] = None
    ):
        """
        Initialize Acrolinx agent.
        
        Args:
            api_url (str): Acrolinx API endpoint
            api_token (str): API authentication token
            guidance_profile (str, optional): Specific guidance profile to use
        """
        self.api_url = api_url
        self.api_token = api_token
        self.guidance_profile = guidance_profile
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
    async def check_content(
        self,
        content: str,
        content_type: str = "text/html",
        content_reference: Optional[str] = None
    ) -> Dict:
        """
        Submit content for Acrolinx quality check.
        
        Args:
            content (str): Content to check
            content_type (str): Content format (default: text/html)
            content_reference (str, optional): Reference ID for the content
            
        Returns:
            Dict: Acrolinx check results
        """
        try:
            # Prepare check request
            check_data = {
                "content": content,
                "contentFormat": content_type,
                "checkOptions": {
                    "guidanceProfileId": self.guidance_profile,
                    "reportTypes": [
                        "scorecard",
                        "issues",
                        "termHarvesting"
                    ]
                }
            }
            
            if content_reference:
                check_data["contentReference"] = content_reference
                
            # Submit check request
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(
                    f"{self.api_url}/api/v1/checking/checks",
                    json=check_data
                ) as response:
                    check_response = await response.json()
                    
                    # Get check ID and poll for results
                    check_id = check_response.get("id")
                    if not check_id:
                        raise ValueError("No check ID received from Acrolinx")
                        
                    return await self._poll_check_results(session, check_id)
                    
        except Exception as e:
            logger.error(f"Acrolinx check failed: {str(e)}")
            raise
            
    async def _poll_check_results(
        self,
        session: aiohttp.ClientSession,
        check_id: str,
        max_retries: int = 10,
        retry_delay: int = 2
    ) -> Dict:
        """Poll for check results."""
        import asyncio
        
        for _ in range(max_retries):
            async with session.get(
                f"{self.api_url}/api/v1/checking/checks/{check_id}"
            ) as response:
                result = await response.json()
                
                if result.get("status") == "done":
                    return await self._process_check_results(result)
                    
                await asyncio.sleep(retry_delay)
                
        raise TimeoutError("Acrolinx check timed out")
        
    async def _process_check_results(self, raw_results: Dict) -> Dict:
        """Process and structure check results."""
        return {
            "quality_score": raw_results.get("quality", {}).get("score"),
            "issues": self._process_issues(raw_results.get("issues", [])),
            "guidance": self._process_guidance(raw_results.get("guidance", {})),
            "terminology": raw_results.get("termHarvesting", {}),
            "metadata": {
                "check_id": raw_results.get("id"),
                "timestamp": datetime.now().isoformat(),
                "guidance_profile": self.guidance_profile
            }
        }
        
    def _process_issues(self, issues: List[Dict]) -> List[Dict]:
        """Process and categorize content issues."""
        processed_issues = []
        
        for issue in issues:
            processed_issues.append({
                "type": issue.get("issueType"),
                "category": issue.get("category"),
                "severity": issue.get("severity"),
                "message": issue.get("message"),
                "suggestions": issue.get("suggestions", []),
                "position": {
                    "start": issue.get("positionalInformation", {}).get("start"),
                    "end": issue.get("positionalInformation", {}).get("end")
                }
            })
            
        return processed_issues
        
    def _process_guidance(self, guidance: Dict) -> Dict:
        """Process guidance information."""
        return {
            "goals": guidance.get("goals", []),
            "guidelines": guidance.get("guidelines", []),
            "recommendations": guidance.get("recommendations", [])
        }
        
    async def get_guidance_profiles(self) -> List[Dict]:
        """Fetch available guidance profiles."""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(
                f"{self.api_url}/api/v1/guidance/profiles"
            ) as response:
                profiles = await response.json()
                return profiles.get("profiles", []) 