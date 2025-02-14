"""
Confluence API client for retrieving and updating documentation.
"""
from typing import Dict, Any, List
from atlassian import Confluence
from config import settings

class ConfluenceClient:
    def __init__(self):
        self.client = Confluence(
            url=settings.CONFLUENCE_URL,
            username=settings.CONFLUENCE_USERNAME,
            password=settings.CONFLUENCE_API_TOKEN
        )

    async def get_page(self, page_id: str) -> Dict[str, Any]:
        """
        Retrieve a Confluence page by its ID.
        
        Args:
            page_id (str): Confluence page ID
            
        Returns:
            Dict[str, Any]: Page content and metadata
        """
        return self.client.get_page_by_id(page_id, expand='body.storage')

    async def search_content(self, query: str) -> List[Dict[str, Any]]:
        """
        Search Confluence content.
        
        Args:
            query (str): Search query string
            
        Returns:
            List[Dict[str, Any]]: List of matching content
        """
        return self.client.cql(query) 