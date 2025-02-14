"""
Query Response Agent responsible for handling user queries and coordinating responses.
"""
from typing import Dict, List, Optional, Union, Any
import logging
from datetime import datetime
import re

from ..integrations.openai_client import OpenAIClient
from ..integrations.confluence_client import ConfluenceClient
from ..utils.redis_client import RedisClient

logger = logging.getLogger(__name__)

class QueryResponseAgent:
    def __init__(
        self,
        openai_client: OpenAIClient,
        confluence_client: Optional[ConfluenceClient] = None,
        redis_client: Optional[RedisClient] = None
    ):
        self.openai_client = openai_client
        self.confluence_client = confluence_client
        self.redis_client = redis_client
        self.conversation_history: Dict[str, List[Dict]] = {}
        
    async def process_query(
        self,
        query: str,
        context: Optional[Dict] = None,
        session_id: Optional[str] = None,
        parameters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a user query and generate a response.
        
        Args:
            query (str): User's query
            context (Dict, optional): Additional context for the query
            session_id (str, optional): Session identifier for conversation tracking
            parameters (Dict, optional): Additional parameters for response generation
            
        Returns:
            Dict[str, Any]: Structured response with answer and metadata
        """
        start_time = datetime.now()
        
        try:
            # Analyze and classify the query
            query_analysis = await self._analyze_query(query)
            
            # Gather relevant context
            enhanced_context = await self._gather_context(
                query,
                query_analysis,
                context
            )
            
            # Generate the response
            response_content = await self._generate_response(
                query,
                query_analysis,
                enhanced_context,
                parameters
            )
            
            # Process and structure the response
            structured_response = await self._structure_response(
                query,
                response_content,
                enhanced_context,
                query_analysis
            )
            
            # Update conversation history
            if session_id:
                await self._update_conversation_history(
                    session_id,
                    query,
                    structured_response
                )
            
            await self._log_success(start_time, query_analysis['type'])
            return structured_response
            
        except Exception as e:
            await self._log_error(str(e), start_time)
            raise
            
    async def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze and classify the query."""
        system_prompt = """Analyze the following query and provide:
        1. Query type (how-to, conceptual, troubleshooting, reference)
        2. Technical domain
        3. Required expertise level
        4. Expected response format
        5. Key terms and concepts"""
        
        try:
            analysis_response = await self.openai_client.generate_completion(
                system_prompt=system_prompt,
                user_message=query
            )
            
            return self._parse_query_analysis(analysis_response)
            
        except Exception as e:
            logger.error(f"Query analysis failed: {str(e)}")
            return self._get_default_query_analysis()
            
    def _parse_query_analysis(self, analysis_response: str) -> Dict[str, Any]:
        """Parse the query analysis response."""
        analysis = {
            'type': 'general',
            'domain': 'general',
            'expertise_level': 'intermediate',
            'response_format': 'text',
            'key_terms': []
        }
        
        # Extract query type
        if re.search(r'how.?to|step|procedure', analysis_response, re.I):
            analysis['type'] = 'how-to'
        elif re.search(r'trouble.?shoot|error|issue|problem', analysis_response, re.I):
            analysis['type'] = 'troubleshooting'
        elif re.search(r'what.?is|explain|define', analysis_response, re.I):
            analysis['type'] = 'conceptual'
        elif re.search(r'reference|documentation|where', analysis_response, re.I):
            analysis['type'] = 'reference'
            
        # Extract technical domain
        domains = {
            'api': r'api|rest|endpoint',
            'authentication': r'auth|oauth|login',
            'database': r'database|sql|query',
            'deployment': r'deploy|kubernetes|docker',
            'security': r'security|encryption|ssl'
        }
        
        for domain, pattern in domains.items():
            if re.search(pattern, analysis_response, re.I):
                analysis['domain'] = domain
                break
                
        # Extract expertise level
        if re.search(r'basic|beginner|start', analysis_response, re.I):
            analysis['expertise_level'] = 'beginner'
        elif re.search(r'advanced|expert|complex', analysis_response, re.I):
            analysis['expertise_level'] = 'advanced'
            
        # Extract key terms
        analysis['key_terms'] = self._extract_key_terms(analysis_response)
        
        return analysis
        
    def _get_default_query_analysis(self) -> Dict[str, Any]:
        """Return default query analysis."""
        return {
            'type': 'general',
            'domain': 'general',
            'expertise_level': 'intermediate',
            'response_format': 'text',
            'key_terms': []
        }
        
    async def _gather_context(
        self,
        query: str,
        query_analysis: Dict[str, Any],
        user_context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Gather relevant context for the query."""
        context = {
            'user_provided': user_context or {},
            'documentation': [],
            'related_queries': [],
            'technical_references': []
        }
        
        try:
            # Search Confluence if available
            if self.confluence_client:
                docs = await self.confluence_client.search_content(
                    ' '.join(query_analysis['key_terms'])
                )
                context['documentation'] = docs
                
            # Get cached related queries if available
            if self.redis_client:
                related = await self.redis_client.get_related_queries(
                    query_analysis['key_terms']
                )
                context['related_queries'] = related
                
            # Add technical references based on domain
            context['technical_references'] = (
                await self._get_technical_references(query_analysis['domain'])
            )
            
        except Exception as e:
            logger.warning(f"Context gathering partial failure: {str(e)}")
            
        return context
        
    async def _generate_response(
        self,
        query: str,
        query_analysis: Dict[str, Any],
        context: Dict[str, Any],
        parameters: Optional[Dict]
    ) -> str:
        """Generate response based on query and context."""
        # Create system prompt based on query type
        system_prompt = self._create_response_prompt(query_analysis, parameters)
        
        # Prepare context message
        context_message = self._prepare_context_message(context)
        
        # Generate response
        response = await self.openai_client.generate_completion(
            system_prompt=system_prompt,
            user_message=f"{query}\n\nContext:\n{context_message}"
        )
        
        return response
        
    def _create_response_prompt(
        self,
        query_analysis: Dict[str, Any],
        parameters: Optional[Dict]
    ) -> str:
        """Create appropriate system prompt based on query type."""
        base_prompt = "You are a technical documentation expert. "
        
        type_prompts = {
            'how-to': """Provide clear, step-by-step instructions. Include:
            1. Prerequisites
            2. Step-by-step procedure
            3. Code examples where relevant
            4. Common issues and solutions""",
            
            'troubleshooting': """Provide troubleshooting guidance. Include:
            1. Problem analysis
            2. Possible causes
            3. Solution steps
            4. Prevention measures""",
            
            'conceptual': """Explain concepts clearly. Include:
            1. Clear definition
            2. Key components
            3. Real-world examples
            4. Related concepts""",
            
            'reference': """Provide reference information. Include:
            1. Relevant documentation links
            2. API details if applicable
            3. Configuration options
            4. Usage examples"""
        }
        
        prompt = base_prompt + type_prompts.get(
            query_analysis['type'],
            type_prompts['how-to']
        )
        
        if parameters and 'style_guide' in parameters:
            prompt += "\n\nFollow these style guidelines:\n"
            for rule, desc in parameters['style_guide'].items():
                prompt += f"- {rule}: {desc}\n"
                
        return prompt
        
    def _prepare_context_message(self, context: Dict[str, Any]) -> str:
        """Prepare context information for the response generation."""
        context_message = ""
        
        if context.get('documentation'):
            context_message += "Related Documentation:\n"
            for doc in context['documentation'][:3]:  # Limit to top 3
                context_message += f"- {doc['title']}: {doc.get('excerpt', '')}\n"
                
        if context.get('technical_references'):
            context_message += "\nTechnical References:\n"
            for ref in context['technical_references']:
                context_message += f"- {ref['title']}: {ref['description']}\n"
                
        if context.get('user_provided'):
            context_message += "\nAdditional Context:\n"
            for key, value in context['user_provided'].items():
                context_message += f"- {key}: {value}\n"
                
        return context_message
        
    async def _structure_response(
        self,
        query: str,
        response_content: str,
        context: Dict[str, Any],
        query_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Structure the response with metadata and references."""
        return {
            'query': query,
            'response': response_content,
            'metadata': {
                'query_type': query_analysis['type'],
                'domain': query_analysis['domain'],
                'expertise_level': query_analysis['expertise_level'],
                'generated_at': datetime.now().isoformat()
            },
            'references': self._extract_references(context),
            'related_queries': context.get('related_queries', []),
            'suggestions': await self._generate_follow_up_suggestions(
                query,
                response_content,
                query_analysis
            )
        }
        
    def _extract_references(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract references from context."""
        references = []
        
        if context.get('documentation'):
            references.extend([{
                'type': 'documentation',
                'title': doc['title'],
                'url': doc.get('url', ''),
                'relevance': 'high'
            } for doc in context['documentation']])
            
        if context.get('technical_references'):
            references.extend([{
                'type': 'technical',
                'title': ref['title'],
                'url': ref.get('url', ''),
                'relevance': 'medium'
            } for ref in context['technical_references']])
            
        return references
        
    async def _generate_follow_up_suggestions(
        self,
        query: str,
        response: str,
        query_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate follow-up question suggestions."""
        system_prompt = """Based on the query and response, suggest relevant
        follow-up questions that would help deepen understanding or address
        related aspects."""
        
        try:
            suggestions_response = await self.openai_client.generate_completion(
                system_prompt=system_prompt,
                user_message=f"Query: {query}\n\nResponse: {response}"
            )
            
            return [s.strip() for s in suggestions_response.split('\n') if s.strip()]
            
        except Exception as e:
            logger.warning(f"Failed to generate suggestions: {str(e)}")
            return []
            
    async def _update_conversation_history(
        self,
        session_id: str,
        query: str,
        response: Dict[str, Any]
    ) -> None:
        """Update the conversation history."""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
            
        self.conversation_history[session_id].append({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response': response
        })
        
        # Maintain history size
        if len(self.conversation_history[session_id]) > 10:
            self.conversation_history[session_id].pop(0)
            
        # Cache in Redis if available
        if self.redis_client:
            try:
                await self.redis_client.set_conversation_history(
                    session_id,
                    self.conversation_history[session_id]
                )
            except Exception as e:
                logger.warning(f"Failed to cache conversation history: {str(e)}")
                
    async def _get_technical_references(self, domain: str) -> List[Dict[str, str]]:
        """Get technical references based on domain."""
        # This would typically fetch from a knowledge base
        # Placeholder implementation
        return []
        
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key technical terms from text."""
        # Placeholder for more sophisticated term extraction
        return list(set(re.findall(r'\b\w+\b', text.lower())))
        
    async def _log_success(self, start_time: datetime, query_type: str) -> None:
        """Log successful query processing."""
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            "Query processed successfully",
            extra={
                "query_type": query_type,
                "duration": duration,
                "status": "success"
            }
        )
        
    async def _log_error(self, error: str, start_time: datetime) -> None:
        """Log query processing error."""
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(
            "Query processing failed",
            extra={
                "error": error,
                "duration": duration,
                "status": "error"
            }
        ) 