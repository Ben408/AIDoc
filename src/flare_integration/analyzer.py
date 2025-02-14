"""
Flare content structure analyzer for maintaining consistency across documentation.
"""
from typing import Dict, List, Optional
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

class FlareContentAnalyzer:
    def __init__(self, content_root: str):
        """
        Initialize the Flare content analyzer.
        
        Args:
            content_root (str): Path to the root of Flare content files
        """
        self.content_root = Path(content_root)
        self.structure_cache: Dict[str, Dict] = {}
        
    async def analyze_content_structure(
        self,
        content_type: str,
        reference_files: Optional[List[str]] = None
    ) -> Dict:
        """
        Analyze existing content structure for consistency.
        
        Args:
            content_type (str): Type of content (guide, reference, api, etc.)
            reference_files (List[str], optional): Specific files to analyze
            
        Returns:
            Dict: Content structure analysis
        """
        try:
            # Get relevant content files
            files = await self._get_reference_files(content_type, reference_files)
            
            # Analyze structure patterns
            structure = {
                'heading_patterns': self._analyze_headings(files),
                'content_blocks': self._analyze_content_blocks(files),
                'navigation': self._analyze_navigation(files),
                'metadata': self._analyze_metadata(files),
                'common_elements': self._identify_common_elements(files)
            }
            
            # Cache the analysis
            self.structure_cache[content_type] = structure
            
            return structure
            
        except Exception as e:
            logger.error(f"Content analysis failed: {str(e)}")
            raise
            
    async def _get_reference_files(
        self,
        content_type: str,
        reference_files: Optional[List[str]] = None
    ) -> List[Path]:
        """Get relevant content files for analysis."""
        if reference_files:
            return [self.content_root / f for f in reference_files]
            
        # Find similar content files based on type
        pattern = self._get_content_pattern(content_type)
        return list(self.content_root.glob(pattern))
        
    def _get_content_pattern(self, content_type: str) -> str:
        """Get glob pattern for content type."""
        patterns = {
            'guide': '**/guides/*.htm',
            'reference': '**/references/*.htm',
            'api': '**/api/*.htm',
            'tutorial': '**/tutorials/*.htm'
        }
        return patterns.get(content_type, '**/*.htm')
        
    def _analyze_headings(self, files: List[Path]) -> Dict:
        """Analyze heading patterns and hierarchy."""
        heading_patterns = {
            'levels': {},
            'common_titles': set(),
            'hierarchy': []
        }
        
        for file in files:
            content = file.read_text(encoding='utf-8')
            
            # Extract headings
            headings = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', content)
            
            # Analyze heading levels
            levels = re.findall(r'<h([1-6])[^>]*>', content)
            for level in levels:
                heading_patterns['levels'][level] = heading_patterns['levels'].get(level, 0) + 1
                
            # Track common titles
            heading_patterns['common_titles'].update(headings)
            
            # Analyze hierarchy
            hierarchy = self._extract_heading_hierarchy(content)
            heading_patterns['hierarchy'].append(hierarchy)
            
        return heading_patterns
        
    def _analyze_content_blocks(self, files: List[Path]) -> Dict:
        """Analyze common content block patterns."""
        blocks = {
            'code_blocks': [],
            'note_blocks': [],
            'warning_blocks': [],
            'table_patterns': [],
            'list_patterns': []
        }
        
        for file in files:
            content = file.read_text(encoding='utf-8')
            
            # Analyze code blocks
            code_blocks = re.findall(r'<pre[^>]*>(.*?)</pre>', content, re.DOTALL)
            blocks['code_blocks'].extend(self._analyze_code_patterns(code_blocks))
            
            # Analyze note patterns
            notes = re.findall(r'<div[^>]*class="[^"]*note[^"]*"[^>]*>(.*?)</div>', content, re.DOTALL)
            blocks['note_blocks'].extend(self._analyze_note_patterns(notes))
            
            # Analyze table patterns
            tables = re.findall(r'<table[^>]*>(.*?)</table>', content, re.DOTALL)
            blocks['table_patterns'].extend(self._analyze_table_patterns(tables))
            
        return blocks
        
    def _analyze_navigation(self, files: List[Path]) -> Dict:
        """Analyze navigation patterns and relationships."""
        navigation = {
            'hierarchy': {},
            'relationships': {},
            'breadcrumbs': set()
        }
        
        for file in files:
            content = file.read_text(encoding='utf-8')
            
            # Extract navigation elements
            nav_elements = re.findall(r'<nav[^>]*>(.*?)</nav>', content, re.DOTALL)
            
            # Analyze breadcrumbs
            breadcrumbs = re.findall(r'<div[^>]*class="[^"]*breadcrumb[^"]*"[^>]*>(.*?)</div>', content)
            navigation['breadcrumbs'].update(breadcrumbs)
            
            # Build relationship map
            self._build_navigation_relationships(content, navigation['relationships'])
            
        return navigation
        
    def _analyze_metadata(self, files: List[Path]) -> Dict:
        """Analyze metadata patterns."""
        metadata = {
            'common_tags': set(),
            'properties': set(),
            'relationships': {}
        }
        
        for file in files:
            content = file.read_text(encoding='utf-8')
            
            # Extract metadata
            meta_tags = re.findall(r'<meta[^>]*>', content)
            metadata['common_tags'].update(self._extract_meta_properties(meta_tags))
            
        return metadata
        
    def _identify_common_elements(self, files: List[Path]) -> Dict:
        """Identify common structural elements."""
        elements = {
            'header_patterns': set(),
            'footer_patterns': set(),
            'sidebar_patterns': set(),
            'common_classes': set()
        }
        
        for file in files:
            content = file.read_text(encoding='utf-8')
            
            # Extract common elements
            headers = re.findall(r'<header[^>]*>(.*?)</header>', content, re.DOTALL)
            elements['header_patterns'].update(headers)
            
            # Extract common classes
            classes = re.findall(r'class="([^"]*)"', content)
            elements['common_classes'].update(classes)
            
        return elements
        
    def _extract_heading_hierarchy(self, content: str) -> List[Dict]:
        """Extract heading hierarchy from content."""
        hierarchy = []
        current_level = 0
        
        for match in re.finditer(r'<h([1-6])[^>]*>(.*?)</h\1>', content):
            level = int(match.group(1))
            title = match.group(2)
            
            if level > current_level:
                hierarchy.append({'level': level, 'title': title, 'children': []})
            else:
                hierarchy.append({'level': level, 'title': title})
                
            current_level = level
            
        return hierarchy
        
    def _extract_meta_properties(self, meta_tags: List[str]) -> set:
        """Extract properties from meta tags."""
        properties = set()
        
        for tag in meta_tags:
            name = re.search(r'name="([^"]*)"', tag)
            if name:
                properties.add(name.group(1))
                
        return properties 