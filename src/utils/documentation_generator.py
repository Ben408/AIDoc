"""
Documentation generator for the AI Documentation System.
"""
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
import json
import inspect
import importlib
import pkgutil
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentationGenerator:
    def __init__(self, output_path: str):
        """
        Initialize documentation generator.
        
        Args:
            output_path (str): Path for generated documentation
        """
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
    async def generate_api_documentation(self) -> Path:
        """Generate API documentation."""
        api_doc = {
            "title": "AI Documentation System API",
            "version": "1.0.0",
            "endpoints": await self._collect_endpoints(),
            "models": await self._collect_models(),
            "examples": await self._collect_examples()
        }
        
        output_file = self.output_path / "api_documentation.md"
        await self._write_markdown(output_file, api_doc)
        return output_file
        
    async def generate_user_guide(self) -> Path:
        """Generate user guide."""
        user_guide = {
            "title": "AI Documentation System User Guide",
            "sections": [
                await self._generate_overview(),
                await self._generate_getting_started(),
                await self._generate_features(),
                await self._generate_workflows(),
                await self._generate_configuration(),
                await self._generate_troubleshooting()
            ]
        }
        
        output_file = self.output_path / "user_guide.md"
        await self._write_markdown(output_file, user_guide)
        return output_file
        
    async def generate_developer_guide(self) -> Path:
        """Generate developer documentation."""
        dev_guide = {
            "title": "AI Documentation System Developer Guide",
            "sections": [
                await self._generate_architecture(),
                await self._generate_setup_guide(),
                await self._generate_contribution_guide(),
                await self._generate_testing_guide(),
                await self._generate_deployment_guide()
            ]
        }
        
        output_file = self.output_path / "developer_guide.md"
        await self._write_markdown(output_file, dev_guide)
        return output_file
        
    async def _collect_endpoints(self) -> List[Dict[str, Any]]:
        """Collect API endpoint documentation."""
        endpoints = []
        
        # Collect from agents
        agent_endpoints = {
            "review": {
                "path": "/api/review",
                "method": "POST",
                "description": "Submit content for review",
                "parameters": {
                    "content": "Content to review",
                    "content_type": "Type of content (html, markdown, text)",
                    "reference": "Optional reference ID"
                },
                "returns": "Review results including AI and Acrolinx feedback"
            },
            "draft": {
                "path": "/api/draft",
                "method": "POST",
                "description": "Generate content draft",
                "parameters": {
                    "topic": "Topic to generate content for",
                    "context": "Additional context",
                    "template": "Optional template to follow"
                },
                "returns": "Generated content draft"
            },
            "query": {
                "path": "/api/query",
                "method": "POST",
                "description": "Query documentation",
                "parameters": {
                    "query": "Query text",
                    "context": "Optional context",
                    "session_id": "Optional session ID"
                },
                "returns": "Query response"
            }
        }
        
        endpoints.extend([
            {
                "name": name,
                "details": details
            } for name, details in agent_endpoints.items()
        ])
        
        return endpoints
        
    async def _collect_models(self) -> List[Dict[str, Any]]:
        """Collect data model documentation."""
        models = []
        
        # Core models
        models.extend([
            {
                "name": "ReviewResult",
                "fields": {
                    "quality_score": "float: Overall quality score",
                    "issues": "List[Dict]: Identified issues",
                    "suggestions": "List[str]: Improvement suggestions",
                    "metadata": "Dict: Additional metadata"
                }
            },
            {
                "name": "DraftRequest",
                "fields": {
                    "topic": "str: Content topic",
                    "context": "Dict: Additional context",
                    "template": "Optional[str]: Template name"
                }
            },
            {
                "name": "QueryRequest",
                "fields": {
                    "query": "str: Query text",
                    "context": "Optional[Dict]: Query context",
                    "session_id": "Optional[str]: Session identifier"
                }
            }
        ])
        
        return models
        
    async def _collect_examples(self) -> List[Dict[str, Any]]:
        """Collect API usage examples."""
        return [
            {
                "title": "Submit content for review",
                "description": "Example of submitting content for AI and Acrolinx review",
                "code": """
                import requests

                response = requests.post(
                    "http://api/review",
                    json={
                        "content": "<h1>API Guide</h1>...",
                        "content_type": "text/html",
                        "reference": "doc-123"
                    }
                )
                result = response.json()
                """
            },
            {
                "title": "Generate content draft",
                "description": "Example of requesting a content draft",
                "code": """
                import requests

                response = requests.post(
                    "http://api/draft",
                    json={
                        "topic": "API Authentication",
                        "context": {
                            "audience": "developers",
                            "level": "intermediate"
                        }
                    }
                )
                draft = response.json()
                """
            }
        ]
        
    async def _generate_overview(self) -> Dict[str, Any]:
        """Generate system overview documentation."""
        return {
            "title": "System Overview",
            "sections": [
                {
                    "title": "Introduction",
                    "content": "The AI Documentation System provides intelligent documentation assistance through AI-powered content generation, review, and querying capabilities."
                },
                {
                    "title": "Key Features",
                    "content": [
                        "AI-powered content review",
                        "Automated content generation",
                        "Intelligent documentation querying",
                        "Acrolinx integration",
                        "Performance monitoring",
                        "Error handling"
                    ]
                },
                {
                    "title": "System Architecture",
                    "content": "The system consists of multiple specialized agents working together to provide comprehensive documentation assistance."
                }
            ]
        }
        
    async def _generate_getting_started(self) -> Dict[str, Any]:
        """Generate getting started guide."""
        return {
            "title": "Getting Started",
            "sections": [
                {
                    "title": "Prerequisites",
                    "content": [
                        "Python 3.8+",
                        "Docker and Docker Compose",
                        "OpenAI API key",
                        "Acrolinx credentials",
                        "Redis server"
                    ]
                },
                {
                    "title": "Installation",
                    "content": """
                    1. Clone the repository
                    2. Copy .env.example to .env
                    3. Configure environment variables
                    4. Run docker-compose up
                    """
                },
                {
                    "title": "First Steps",
                    "content": "Guide to initial system usage and configuration"
                }
            ]
        }
        
    async def _generate_features(self) -> Dict[str, Any]:
        """Generate features documentation."""
        return {
            "title": "Features",
            "sections": [
                {
                    "title": "AI-Powered Review",
                    "content": [
                        "Content quality analysis",
                        "Style consistency checks",
                        "Grammar and spelling verification",
                        "Readability scoring"
                    ]
                },
                {
                    "title": "Content Generation",
                    "content": [
                        "Context-aware drafting",
                        "Template-based generation",
                        "Style matching",
                        "Automated formatting"
                    ]
                },
                {
                    "title": "Documentation Query",
                    "content": [
                        "Natural language queries",
                        "Context-aware responses",
                        "Cross-reference support",
                        "Historical query tracking"
                    ]
                }
            ]
        }
        
    async def _generate_workflows(self) -> Dict[str, Any]:
        """Generate workflows documentation."""
        return {
            "title": "Workflows",
            "sections": [
                {
                    "title": "Content Review Process",
                    "content": """
                    1. Submit content for review
                    2. AI analysis performed
                    3. Acrolinx quality check
                    4. Results aggregation
                    5. Suggestions provided
                    """
                },
                {
                    "title": "Content Generation",
                    "content": """
                    1. Define content requirements
                    2. Provide context and templates
                    3. Generate initial draft
                    4. Review and refine
                    5. Finalize content
                    """
                }
            ]
        }
        
    async def _generate_configuration(self) -> Dict[str, Any]:
        """Generate configuration documentation."""
        return {
            "title": "Configuration",
            "sections": [
                {
                    "title": "Environment Variables",
                    "content": [
                        "OPENAI_API_KEY - OpenAI API key",
                        "ACROLINX_API_TOKEN - Acrolinx API token",
                        "REDIS_URL - Redis connection URL",
                        "LOG_LEVEL - Logging level configuration"
                    ]
                },
                {
                    "title": "Performance Settings",
                    "content": [
                        "CACHE_TTL - Cache time-to-live",
                        "MAX_RETRIES - Maximum retry attempts",
                        "TIMEOUT - Operation timeout",
                        "BATCH_SIZE - Processing batch size"
                    ]
                }
            ]
        }
        
    async def _generate_troubleshooting(self) -> Dict[str, Any]:
        """Generate troubleshooting documentation."""
        return {
            "title": "Troubleshooting",
            "sections": [
                {
                    "title": "Common Issues",
                    "content": [
                        "API connection failures",
                        "Cache inconsistencies",
                        "Performance degradation",
                        "Integration errors"
                    ]
                },
                {
                    "title": "Solutions",
                    "content": [
                        "Verify API credentials",
                        "Clear cache and retry",
                        "Check system resources",
                        "Review error logs"
                    ]
                }
            ]
        }
        
    async def _generate_architecture(self) -> Dict[str, Any]:
        """Generate architecture documentation."""
        return {
            "title": "System Architecture",
            "sections": [
                {
                    "title": "Components",
                    "content": [
                        "Core Agents - Review, Draft, Query",
                        "Integration Services - Acrolinx, OpenAI",
                        "Support Systems - Cache, Error Handler",
                        "Monitoring - Performance, Logging"
                    ]
                },
                {
                    "title": "Data Flow",
                    "content": """
                    1. Request Processing
                    2. Agent Orchestration
                    3. External Integration
                    4. Result Aggregation
                    5. Response Generation
                    """
                }
            ]
        }
        
    async def _generate_setup_guide(self) -> Dict[str, Any]:
        """Generate setup guide documentation."""
        return {
            "title": "Setup Guide",
            "sections": [
                {
                    "title": "Installation",
                    "content": """
                    1. System Requirements
                    2. Dependencies Installation
                    3. Configuration Setup
                    4. Integration Configuration
                    5. Verification Steps
                    """
                },
                {
                    "title": "First Steps",
                    "content": [
                        "Basic configuration",
                        "API key setup",
                        "Integration testing",
                        "Initial validation"
                    ]
                }
            ]
        }
        
    async def _write_markdown(self, file_path: Path, content: Dict) -> None:
        """Write content to markdown file."""
        def dict_to_markdown(data: Dict, level: int = 1) -> str:
            markdown = []
            
            # Add title
            if "title" in data:
                markdown.append(f"{'#' * level} {data['title']}\n")
            
            # Handle sections
            if "sections" in data:
                for section in data["sections"]:
                    markdown.append(dict_to_markdown(section, level + 1))
            
            # Handle content
            if "content" in data:
                if isinstance(data["content"], list):
                    for item in data["content"]:
                        markdown.append(f"- {item}")
                else:
                    markdown.append(data["content"])
            
            return "\n".join(markdown)
        
        markdown_content = dict_to_markdown(content)
        file_path.write_text(markdown_content) 