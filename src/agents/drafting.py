"""
Drafting Agent responsible for creating documentation content.
"""
from typing import Dict, List, Optional, Union
import logging
from datetime import datetime
import re

from ..integrations.openai_client import OpenAIClient
from ..integrations.jira_client import JiraClient
from ..integrations.confluence_client import ConfluenceClient

logger = logging.getLogger(__name__)

class DraftingAgent:
    def __init__(
        self,
        openai_client: OpenAIClient,
        jira_client: Optional[JiraClient] = None,
        confluence_client: Optional[ConfluenceClient] = None
    ):
        self.openai_client = openai_client
        self.jira_client = jira_client
        self.confluence_client = confluence_client
        
    async def create_draft(
        self,
        content_request: Dict[str, Union[str, Dict]],
        parameters: Optional[Dict] = None
    ) -> Dict:
        """
        Create documentation draft based on provided content request and parameters.
        
        Args:
            content_request (Dict): Content requirements and context
            parameters (Dict, optional): Additional parameters for draft generation
            
        Returns:
            Dict: Generated draft with metadata and analysis
        """
        start_time = datetime.now()
        
        try:
            # Gather context from external sources
            context = await self._gather_context(content_request)
            
            # Generate the draft
            draft_content = await self._generate_draft(content_request, context, parameters)
            
            # Analyze the generated content
            analysis = self._analyze_draft(draft_content)
            
            # Structure the response
            response = {
                'content': draft_content,
                'metadata': self._generate_metadata(content_request, context),
                'analysis': analysis,
                'suggestions': await self._generate_suggestions(draft_content),
                'references': self._extract_references(context)
            }
            
            await self._log_success(start_time)
            return response
            
        except Exception as e:
            await self._log_error(str(e), start_time)
            raise
            
    async def _gather_context(self, content_request: Dict) -> Dict:
        """Gather relevant context from various sources."""
        context = {}
        
        try:
            # Gather JIRA information if available
            if self.jira_client and 'jira_keys' in content_request:
                context['jira'] = await self.jira_client.get_issues(
                    content_request['jira_keys']
                )
                
            # Gather Confluence information if available
            if self.confluence_client and 'confluence_ids' in content_request:
                context['confluence'] = await self.confluence_client.get_pages(
                    content_request['confluence_ids']
                )
                
            # Add any provided technical specifications
            if 'specifications' in content_request:
                context['specifications'] = content_request['specifications']
                
        except Exception as e:
            logger.warning(f"Error gathering context: {str(e)}")
            # Continue with partial context
            
        return context
        
    async def _generate_draft(
        self,
        content_request: Dict,
        context: Dict,
        parameters: Optional[Dict]
    ) -> str:
        """Generate the documentation draft."""
        # Prepare the system prompt
        system_prompt = self._create_system_prompt(content_request, parameters)
        
        # Prepare the content request with context
        content_prompt = self._create_content_prompt(content_request, context)
        
        # Generate the draft
        draft = await self.openai_client.generate_completion(
            system_prompt=system_prompt,
            user_message=content_prompt
        )
        
        return draft
        
    def _create_system_prompt(
        self,
        content_request: Dict,
        parameters: Optional[Dict]
    ) -> str:
        """Create the system prompt for draft generation."""
        base_prompt = """You are an expert technical writer specializing in clear,
        accurate, and well-structured documentation. Generate documentation that is:
        
        1. Clear and concise
        2. Technically accurate
        3. Well-structured
        4. Appropriately detailed
        5. Consistent in style and tone
        
        Follow these guidelines:
        - Use active voice
        - Include relevant examples
        - Structure content logically
        - Include necessary cross-references
        - Maintain technical accuracy"""
        
        if parameters and 'style_guide' in parameters:
            base_prompt += "\n\nStyle Guide Requirements:\n"
            for rule, description in parameters['style_guide'].items():
                base_prompt += f"- {rule}: {description}\n"
                
        if 'doc_type' in content_request:
            base_prompt += f"\n\nDocument Type: {content_request['doc_type']}"
            
        return base_prompt
        
    def _create_content_prompt(self, content_request: Dict, context: Dict) -> str:
        """Create the content generation prompt with context."""
        prompt = f"Generate documentation for: {content_request.get('title', 'Untitled')}\n\n"
        
        if 'requirements' in content_request:
            prompt += "Requirements:\n"
            for req in content_request['requirements']:
                prompt += f"- {req}\n"
                
        if context:
            prompt += "\nContext Information:\n"
            if 'jira' in context:
                prompt += "JIRA Issues:\n"
                for issue in context['jira']:
                    prompt += f"- {issue['key']}: {issue['summary']}\n"
                    
            if 'confluence' in context:
                prompt += "Related Documentation:\n"
                for page in context['confluence']:
                    prompt += f"- {page['title']}\n"
                    
            if 'specifications' in context:
                prompt += "Technical Specifications:\n"
                for spec in context['specifications']:
                    prompt += f"- {spec}\n"
                    
        return prompt
        
    def _analyze_draft(self, content: str) -> Dict:
        """Analyze the generated draft content."""
        analysis = {
            'structure': self._analyze_structure(content),
            'readability': self._analyze_readability(content),
            'technical_elements': self._analyze_technical_elements(content),
            'completeness': self._analyze_completeness(content)
        }
        return analysis
        
    def _analyze_structure(self, content: str) -> Dict:
        """Analyze the content structure."""
        sections = content.split('\n\n')
        headings = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
        
        return {
            'section_count': len(sections),
            'heading_count': len(headings),
            'heading_hierarchy': self._analyze_heading_hierarchy(headings),
            'avg_section_length': sum(len(s) for s in sections) / len(sections)
        }
        
    def _analyze_heading_hierarchy(self, headings: List[str]) -> Dict:
        """Analyze the heading hierarchy."""
        levels = {}
        for heading in headings:
            level = len(re.match(r'^#+', heading).group())
            levels[level] = levels.get(level, 0) + 1
            
        return {
            'levels': levels,
            'max_depth': max(levels.keys()) if levels else 0,
            'is_sequential': self._check_heading_sequence(levels)
        }
        
    def _check_heading_sequence(self, levels: Dict) -> bool:
        """Check if heading levels are sequential."""
        if not levels:
            return True
        sequence = sorted(levels.keys())
        return sequence == list(range(min(sequence), max(sequence) + 1))
        
    def _analyze_readability(self, content: str) -> Dict:
        """Analyze content readability."""
        sentences = content.split('.')
        words = content.split()
        
        return {
            'avg_sentence_length': len(words) / len(sentences),
            'long_sentences': sum(1 for s in sentences if len(s.split()) > 25),
            'complex_words': sum(1 for w in words if len(w) > 12),
            'readability_score': self._calculate_readability_score(content)
        }
        
    def _calculate_readability_score(self, content: str) -> float:
        """Calculate readability score (Flesch-Kincaid)."""
        # Implementation similar to ReviewAgent
        return 0.0  # Placeholder
        
    def _analyze_technical_elements(self, content: str) -> Dict:
        """Analyze technical elements in the content."""
        return {
            'code_blocks': len(re.findall(r'```[\s\S]*?```', content)),
            'api_references': len(re.findall(r'API|REST|endpoint', content, re.I)),
            'technical_terms': self._extract_technical_terms(content),
            'links': len(re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content))
        }
        
    def _extract_technical_terms(self, content: str) -> List[str]:
        """Extract technical terms from content."""
        # Placeholder for technical term extraction
        return []
        
    def _analyze_completeness(self, content: str) -> Dict:
        """Analyze content completeness."""
        required_sections = {
            'overview': bool(re.search(r'overview|introduction', content, re.I)),
            'prerequisites': bool(re.search(r'prerequisites|requirements', content, re.I)),
            'steps': bool(re.search(r'steps|procedure|how to', content, re.I)),
            'examples': bool(re.search(r'example|sample', content, re.I)),
            'references': bool(re.search(r'references|see also', content, re.I))
        }
        
        return {
            'has_required_sections': required_sections,
            'completeness_score': sum(required_sections.values()) / len(required_sections)
        }
        
    async def _generate_suggestions(self, content: str) -> List[str]:
        """Generate improvement suggestions for the draft."""
        system_prompt = """Analyze the documentation and provide specific,
        actionable suggestions for improvement. Focus on:
        1. Technical accuracy
        2. Clarity and readability
        3. Structure and organization
        4. Completeness
        5. Examples and illustrations"""
        
        try:
            suggestions_response = await self.openai_client.generate_completion(
                system_prompt=system_prompt,
                user_message=content
            )
            return [s.strip() for s in suggestions_response.split('\n') if s.strip()]
        except Exception as e:
            logger.warning(f"Error generating suggestions: {str(e)}")
            return []
            
    def _generate_metadata(self, content_request: Dict, context: Dict) -> Dict:
        """Generate metadata for the draft."""
        return {
            'generated_at': datetime.now().isoformat(),
            'doc_type': content_request.get('doc_type', 'general'),
            'related_issues': [i['key'] for i in context.get('jira', [])],
            'related_pages': [p['id'] for p in context.get('confluence', [])]
        }
        
    def _extract_references(self, context: Dict) -> List[Dict]:
        """Extract references from context."""
        references = []
        
        if 'jira' in context:
            references.extend([{
                'type': 'jira',
                'key': issue['key'],
                'title': issue['summary'],
                'url': issue.get('url', '')
            } for issue in context['jira']])
            
        if 'confluence' in context:
            references.extend([{
                'type': 'confluence',
                'id': page['id'],
                'title': page['title'],
                'url': page.get('url', '')
            } for page in context['confluence']])
            
        return references
        
    async def _log_success(self, start_time: datetime) -> None:
        """Log successful draft generation."""
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            "Draft generation completed successfully",
            extra={
                "duration": duration,
                "status": "success"
            }
        )
        
    async def _log_error(self, error: str, start_time: datetime) -> None:
        """Log draft generation error."""
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(
            "Draft generation failed",
            extra={
                "error": error,
                "duration": duration,
                "status": "error"
            }
        ) 