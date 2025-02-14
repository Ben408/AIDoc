"""
Tests for the Flare content structure analyzer.
"""
import pytest
from pathlib import Path
import shutil
import tempfile
from typing import Generator, Optional

from src.flare_integration.analyzer import FlareContentAnalyzer

@pytest.fixture
def temp_content_dir() -> Generator[Path, None, None]:
    """Create a temporary directory with sample documentation content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        content_dir = Path(temp_dir)
        
        # Create sample documentation structure
        (content_dir / "guides").mkdir()
        (content_dir / "api").mkdir()
        (content_dir / "references").mkdir()
        
        # Create sample content files
        create_sample_content(content_dir)
        
        yield content_dir

def create_sample_content(content_dir: Path) -> None:
    """Create sample documentation files for testing."""
    # Guide example
    guide_content = """
    <html>
    <head>
        <meta name="author" content="Test Author">
        <meta name="keywords" content="test, guide, documentation">
    </head>
    <body>
        <h1>Getting Started Guide</h1>
        <h2>Prerequisites</h2>
        <p>Before you begin, ensure you have:</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
        
        <h2>Installation</h2>
        <div class="note">
            Important: Follow these steps carefully.
        </div>
        
        <pre><code>
        # Example code
        pip install package
        </code></pre>
        
        <h2>Configuration</h2>
        <table>
            <tr><th>Setting</th><th>Description</th></tr>
            <tr><td>Port</td><td>Default port number</td></tr>
        </table>
    </body>
    </html>
    """
    
    (content_dir / "guides" / "getting_started.htm").write_text(guide_content)
    
    # API reference example
    api_content = """
    <html>
    <head>
        <meta name="version" content="1.0">
        <meta name="api-version" content="v1">
    </head>
    <body>
        <h1>API Reference</h1>
        <h2>Endpoints</h2>
        <h3>GET /users</h3>
        <pre><code>
        GET /api/v1/users
        </code></pre>
        
        <div class="warning">
            Authentication required
        </div>
        
        <table>
            <tr><th>Parameter</th><th>Type</th><th>Description</th></tr>
            <tr><td>page</td><td>integer</td><td>Page number</td></tr>
        </table>
    </body>
    </html>
    """
    
    (content_dir / "api" / "users.htm").write_text(api_content)

@pytest.fixture
def analyzer(temp_content_dir) -> FlareContentAnalyzer:
    return FlareContentAnalyzer(str(temp_content_dir))

class TestFlareContentAnalyzer:
    async def test_analyze_guide_structure(self, analyzer):
        """Test analysis of guide content structure."""
        # Act
        structure = await analyzer.analyze_content_structure('guide')
        
        # Assert
        heading_patterns = structure['heading_patterns']
        assert 'levels' in heading_patterns
        assert '1' in heading_patterns['levels']  # h1 exists
        assert '2' in heading_patterns['levels']  # h2 exists
        assert 'Getting Started Guide' in heading_patterns['common_titles']
        
        content_blocks = structure['content_blocks']
        assert len(content_blocks['code_blocks']) > 0
        assert len(content_blocks['note_blocks']) > 0
        assert len(content_blocks['table_patterns']) > 0
        
    async def test_analyze_api_structure(self, analyzer):
        """Test analysis of API documentation structure."""
        # Act
        structure = await analyzer.analyze_content_structure('api')
        
        # Assert
        metadata = structure['metadata']
        assert 'api-version' in metadata['common_tags']
        assert 'version' in metadata['common_tags']
        
        content_blocks = structure['content_blocks']
        assert any('GET /api/v1/users' in block for block in content_blocks['code_blocks'])
        assert len(content_blocks['warning_blocks']) > 0
        
    async def test_analyze_multiple_files(self, analyzer):
        """Test analysis across multiple content files."""
        # Act
        structure = await analyzer.analyze_content_structure(
            'guide',
            ['guides/getting_started.htm']
        )
        
        # Assert
        common_elements = structure['common_elements']
        assert 'note' in common_elements['common_classes']
        assert len(structure['heading_patterns']['hierarchy']) > 0
        
    def test_heading_hierarchy_extraction(self, analyzer):
        """Test extraction of heading hierarchy."""
        content = """
        <h1>Main Title</h1>
        <h2>Subtitle 1</h2>
        <h3>Section 1.1</h3>
        <h2>Subtitle 2</h2>
        """
        
        # Act
        hierarchy = analyzer._extract_heading_hierarchy(content)
        
        # Assert
        assert len(hierarchy) == 4
        assert hierarchy[0]['level'] == 1
        assert hierarchy[0]['title'] == 'Main Title'
        assert hierarchy[2]['level'] == 3
        
    def test_metadata_extraction(self, analyzer):
        """Test extraction of metadata properties."""
        meta_tags = [
            '<meta name="author" content="Test">',
            '<meta name="version" content="1.0">',
            '<meta name="keywords" content="test">'
        ]
        
        # Act
        properties = analyzer._extract_meta_properties(meta_tags)
        
        # Assert
        assert 'author' in properties
        assert 'version' in properties
        assert 'keywords' in properties

class TestFlareContentAnalyzerWithRealContent:
    """Tests using real documentation content from local repository."""
    
    @pytest.fixture
    def real_content_analyzer(self) -> Optional[FlareContentAnalyzer]:
        """
        Create analyzer instance pointing to real documentation.
        Returns None if documentation path doesn't exist.
        """
        # Update this path to match your local documentation location
        doc_path = Path(r"C:\Users\bjcor\Desktop\Sage Local\Documentation")  # Updated path
        if doc_path.exists():
            return FlareContentAnalyzer(str(doc_path))
        return None
    
    @pytest.mark.skipif(
        not Path("../documentation").exists(),
        reason="Local documentation not found"
    )
    async def test_analyze_real_content(self, real_content_analyzer):
        """Test analysis of real documentation content."""
        if not real_content_analyzer:
            pytest.skip("Documentation path not found")
            
        # Act
        structure = await real_content_analyzer.analyze_content_structure('guide')
        
        # Assert
        assert structure is not None
        assert 'heading_patterns' in structure
        assert 'content_blocks' in structure
        assert 'metadata' in structure
        
        # Log analysis results for review
        logging.info("Content Analysis Results:", extra={
            'structure': structure
        })
        
    @pytest.mark.skipif(
        not Path("../documentation").exists(),
        reason="Local documentation not found"
    )
    async def test_analyze_content_patterns(self, real_content_analyzer):
        """Test analysis of content patterns in real documentation."""
        if not real_content_analyzer:
            pytest.skip("Documentation path not found")
            
        # Analyze different content types
        guide_structure = await real_content_analyzer.analyze_content_structure('guide')
        api_structure = await real_content_analyzer.analyze_content_structure('api')
        
        # Compare patterns
        assert guide_structure['heading_patterns'] != api_structure['heading_patterns']
        assert guide_structure['content_blocks'] != api_structure['content_blocks'] 