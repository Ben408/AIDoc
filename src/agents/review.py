"""
Review Agent responsible for reviewing and suggesting improvements to documentation.
"""
from typing import Dict, List, Optional
import logging
from datetime import datetime

from ..integrations.openai_client import OpenAIClient
from config import settings
from .acrolinx_agent import AcrolinxAgent

logger = logging.getLogger(__name__)

class ReviewAgent:
    def __init__(
        self,
        openai_client: OpenAIClient,
        acrolinx_agent: Optional[AcrolinxAgent] = None
    ):
        self.openai_client = openai_client
        self.acrolinx_agent = acrolinx_agent
        
    async def review_content(
        self, 
        content: str,
        style_guide: Optional[Dict] = None,
        **kwargs
    ) -> Dict:
        """
        Review documentation content and provide structured feedback.
        
        Args:
            content (str): The documentation content to review
            style_guide (Dict, optional): Custom style guide parameters
            **kwargs: Additional keyword arguments
            
        Returns:
            Dict: Structured feedback including suggestions, style issues,
                 technical issues, and metrics
        """
        start_time = datetime.now()
        
        try:
            # Prepare the system prompt with style guide
            system_prompt = self._create_system_prompt(style_guide)
            
            # Get the AI review
            ai_review = await self.openai_client.generate_completion(
                system_prompt=system_prompt,
                user_message=content
            )
            
            # Parse the structured feedback
            ai_feedback = self._parse_feedback(ai_review)
            
            # Calculate content metrics
            ai_metrics = self._calculate_metrics(content)
            ai_feedback['metrics'] = ai_metrics
            
            results = {
                "ai_review": ai_feedback,
                "acrolinx_review": None
            }
            
            if self.acrolinx_agent:
                results["acrolinx_review"] = await self.acrolinx_agent.check_content(
                    content,
                    content_type="text/html",
                    content_reference=kwargs.get("reference")
                )
            
            await self._log_success(start_time)
            return await self._combine_reviews(results)
            
        except Exception as e:
            await self._log_error(str(e), start_time)
            raise
            
    def _create_system_prompt(self, style_guide: Optional[Dict] = None) -> str:
        """Create the system prompt for the review."""
        base_prompt = """You are an expert documentation reviewer. Analyze the provided content and provide structured feedback in the following format:

TECHNICAL_ACCURACY:
- List any technical inaccuracies or unclear explanations
- Suggest specific improvements

STYLE_AND_CLARITY:
- Identify style issues (consistency, tone, etc.)
- Note any clarity or readability concerns
- Suggest improvements

STRUCTURE_AND_ORGANIZATION:
- Evaluate the logical flow and organization
- Identify any missing sections or context
- Suggest structural improvements

COMPLETENESS:
- Identify missing information
- Note areas that need more detail
- Suggest additional content

ACTIONABLE_SUGGESTIONS:
- Provide specific, actionable improvements
- Include example revisions where helpful"""

        if style_guide:
            style_rules = "\n\nSTYLE GUIDE RULES:\n"
            for rule, description in style_guide.items():
                style_rules += f"- {rule}: {description}\n"
            base_prompt += style_rules
            
        return base_prompt
        
    def _parse_feedback(self, review_response: str) -> Dict:
        """Parse the AI review response into structured feedback."""
        sections = {
            'technical_issues': [],
            'style_issues': [],
            'structure_issues': [],
            'completeness_issues': [],
            'suggestions': []
        }
        
        current_section = None
        
        for line in review_response.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Identify sections
            if line.endswith(':'):
                section_name = line[:-1].lower()
                if 'technical' in section_name:
                    current_section = 'technical_issues'
                elif 'style' in section_name:
                    current_section = 'style_issues'
                elif 'structure' in section_name:
                    current_section = 'structure_issues'
                elif 'complete' in section_name:
                    current_section = 'completeness_issues'
                elif 'action' in section_name:
                    current_section = 'suggestions'
                continue
                
            # Add content to current section
            if current_section and line.startswith('-'):
                sections[current_section].append(line[1:].strip())
                
        return sections
        
    def _calculate_metrics(self, content: str) -> Dict:
        """Calculate various metrics for the content."""
        words = content.split()
        sentences = content.split('.')
        
        metrics = {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'avg_words_per_sentence': len(words) / max(len(sentences), 1),
            'complexity_indicators': {
                'long_sentences': sum(1 for s in sentences if len(s.split()) > 25),
                'complex_words': sum(1 for w in words if len(w) > 12),
            }
        }
        
        # Calculate readability score (simplified Flesch-Kincaid)
        metrics['readability_score'] = self._calculate_readability(content)
        
        return metrics
        
    def _calculate_readability(self, content: str) -> float:
        """Calculate a readability score for the content."""
        words = content.split()
        sentences = content.split('.')
        syllables = sum(self._count_syllables(word) for word in words)
        
        # Flesch-Kincaid Grade Level formula
        if len(sentences) > 0 and len(words) > 0:
            score = 0.39 * (len(words) / len(sentences))
            score += 11.8 * (syllables / len(words))
            score -= 15.59
            return round(score, 2)
        return 0.0
        
    def _count_syllables(self, word: str) -> int:
        """Estimate the number of syllables in a word."""
        word = word.lower()
        count = 0
        vowels = 'aeiouy'
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                count += 1
            previous_was_vowel = is_vowel
            
        if word.endswith('e'):
            count -= 1
        if count == 0:
            count = 1
            
        return count
        
    async def _log_success(self, start_time: datetime) -> None:
        """Log successful review completion."""
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            "Content review completed successfully",
            extra={
                "duration": duration,
                "status": "success"
            }
        )
        
    async def _log_error(self, error: str, start_time: datetime) -> None:
        """Log review error."""
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(
            "Content review failed",
            extra={
                "error": error,
                "duration": duration,
                "status": "error"
            }
        )
        
    async def _combine_reviews(self, reviews: Dict) -> Dict:
        """Combine AI and Acrolinx review results."""
        combined = {
            "quality_score": None,
            "issues": [],
            "suggestions": [],
            "metadata": {}
        }
        
        # Add AI review results
        if reviews["ai_review"]:
            combined["issues"].extend(reviews["ai_review"].get("issues", []))
            combined["suggestions"].extend(
                reviews["ai_review"].get("suggestions", [])
            )
            
        # Add Acrolinx results if available
        if reviews["acrolinx_review"]:
            acrolinx = reviews["acrolinx_review"]
            combined["quality_score"] = acrolinx.get("quality_score")
            combined["issues"].extend(acrolinx.get("issues", []))
            combined["metadata"]["acrolinx"] = acrolinx.get("metadata")
            
        return combined 