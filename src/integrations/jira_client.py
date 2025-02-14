"""
JIRA API client for retrieving and updating JIRA issues.
"""
from typing import Dict, Any, List
from atlassian import Jira
from config import settings

class JiraClient:
    def __init__(self):
        self.client = Jira(
            url=settings.JIRA_URL,
            username=settings.JIRA_USERNAME,
            password=settings.JIRA_API_TOKEN
        )

    async def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Retrieve a JIRA issue by its key.
        
        Args:
            issue_key (str): JIRA issue key (e.g., "PROJ-123")
            
        Returns:
            Dict[str, Any]: Issue data
        """
        return self.client.issue(issue_key)

    async def search_issues(self, jql: str) -> List[Dict[str, Any]]:
        """
        Search for JIRA issues using JQL.
        
        Args:
            jql (str): JQL query string
            
        Returns:
            List[Dict[str, Any]]: List of matching issues
        """
        return self.client.jql(jql) 