"""
Tests for the Documentation Generator system.
"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import json

from src.utils.documentation_generator import DocumentationGenerator

@pytest.fixture
def temp_output_dir(tmp_path):
    return str(tmp_path / "docs")

@pytest.fixture
def doc_generator(temp_output_dir):
    return DocumentationGenerator(temp_output_dir)

class TestDocumentationGenerator:
    async def test_generate_api_documentation(self, doc_generator):
        """Test API documentation generation."""
        # Act
        output_file = await doc_generator.generate_api_documentation()
        
        # Assert
        assert output_file.exists()
        content = output_file.read_text()
        assert "AI Documentation System API" in content
        assert "endpoints" in content.lower()
        assert "models" in content.lower()
        
    async def test_generate_user_guide(self, doc_generator):
        """Test user guide generation."""
        # Act
        output_file = await doc_generator.generate_user_guide()
        
        # Assert
        assert output_file.exists()
        content = output_file.read_text()
        assert "User Guide" in content
        assert "Getting Started" in content
        
    async def test_generate_developer_guide(self, doc_generator):
        """Test developer documentation generation."""
        # Act
        output_file = await doc_generator.generate_developer_guide()
        
        # Assert
        assert output_file.exists()
        content = output_file.read_text()
        assert "Developer Guide" in content
        assert "Architecture" in content
        
    async def test_markdown_formatting(self, doc_generator):
        """Test markdown formatting of documentation."""
        # Arrange
        test_content = {
            "title": "Test Document",
            "sections": [
                {
                    "title": "Section 1",
                    "content": "Test content"
                }
            ]
        }
        
        # Act
        output_file = Path(doc_generator.output_path) / "test.md"
        await doc_generator._write_markdown(output_file, test_content)
        
        # Assert
        content = output_file.read_text()
        assert "# Test Document" in content
        assert "## Section 1" in content
        
    async def test_endpoint_collection(self, doc_generator):
        """Test API endpoint documentation collection."""
        # Act
        endpoints = await doc_generator._collect_endpoints()
        
        # Assert
        assert isinstance(endpoints, list)
        assert any(e["name"] == "review" for e in endpoints)
        assert any(e["name"] == "draft" for e in endpoints)
        assert any(e["name"] == "query" for e in endpoints)
        
    async def test_model_collection(self, doc_generator):
        """Test data model documentation collection."""
        # Act
        models = await doc_generator._collect_models()
        
        # Assert
        assert isinstance(models, list)
        assert any(m["name"] == "ReviewResult" for m in models)
        assert any(m["name"] == "DraftRequest" for m in models)
        
    async def test_example_collection(self, doc_generator):
        """Test API example collection."""
        # Act
        examples = await doc_generator._collect_examples()
        
        # Assert
        assert isinstance(examples, list)
        assert len(examples) > 0
        assert all(
            isinstance(e["code"], str) for e in examples
        ) 