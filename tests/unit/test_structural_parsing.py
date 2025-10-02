"""
Unit Tests for Structural Parsing Module
Tests format detection, parser factory, and parser implementations
"""

import pytest
from unittest.mock import Mock

from structural_parsing.format_detector import FormatDetector
from structural_parsing.parser_factory import StructuralParserFactory


@pytest.mark.unit
class TestFormatDetector:
    """Test FormatDetector class"""
    
    def test_detect_asciidoc(self):
        """Test detecting AsciiDoc format"""
        detector = FormatDetector()
        
        content = """
= Document Title
:author: John Doe

== Section
Content here.
"""
        
        format_type = detector.detect(content)
        assert format_type == 'asciidoc'
    
    def test_detect_markdown(self):
        """Test detecting Markdown format"""
        detector = FormatDetector()
        
        content = """
# Document Title

## Section
Content here.
"""
        
        format_type = detector.detect(content)
        assert format_type == 'markdown'
    
    def test_detect_dita(self):
        """Test detecting DITA format"""
        detector = FormatDetector()
        
        content = """<?xml version="1.0"?>
<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="test">
  <title>Test</title>
</concept>"""
        
        format_type = detector.detect(content)
        assert format_type == 'dita'
    
    def test_detect_plaintext(self):
        """Test detecting plaintext format"""
        detector = FormatDetector()
        
        content = "This is just plain text without any markup."
        
        format_type = detector.detect(content)
        assert format_type == 'plaintext'
    
    def test_detect_with_filename_hint(self):
        """Test format detection with filename hint"""
        detector = FormatDetector()
        
        # Markdown file
        format_type = detector.detect("# Title", filename="document.md")
        assert format_type == 'markdown'
        
        # AsciiDoc file
        format_type = detector.detect("= Title", filename="document.adoc")
        assert format_type == 'asciidoc'
        
        # DITA file
        format_type = detector.detect("<concept>", filename="topic.dita")
        assert format_type == 'dita'


@pytest.mark.unit
class TestStructuralParserFactory:
    """Test StructuralParserFactory class"""
    
    def test_factory_initialization(self):
        """Test parser factory initializes"""
        factory = StructuralParserFactory()
        assert factory is not None
    
    def test_get_parser_for_markdown(self):
        """Test getting markdown parser"""
        factory = StructuralParserFactory()
        
        parser = factory.get_parser('markdown')
        assert parser is not None
        assert hasattr(parser, 'parse')
    
    def test_get_parser_for_asciidoc(self):
        """Test getting AsciiDoc parser"""
        factory = StructuralParserFactory()
        
        parser = factory.get_parser('asciidoc')
        assert parser is not None
        assert hasattr(parser, 'parse')
    
    def test_get_parser_for_dita(self):
        """Test getting DITA parser"""
        factory = StructuralParserFactory()
        
        parser = factory.get_parser('dita')
        assert parser is not None
        assert hasattr(parser, 'parse')
    
    def test_get_parser_for_plaintext(self):
        """Test getting plaintext parser"""
        factory = StructuralParserFactory()
        
        parser = factory.get_parser('plaintext')
        assert parser is not None
        assert hasattr(parser, 'parse')
    
    def test_parse_with_auto_detection(self):
        """Test parsing with automatic format detection"""
        factory = StructuralParserFactory()
        
        markdown_content = "# Title\n\nParagraph."
        result = factory.parse(markdown_content)
        
        assert result is not None
        assert result.success
        assert result.document is not None
    
    def test_parse_with_explicit_format(self):
        """Test parsing with explicitly specified format"""
        factory = StructuralParserFactory()
        
        content = "# Title\n\nParagraph."
        result = factory.parse(content, format_type='markdown')
        
        assert result is not None
        assert result.success
    
    def test_parse_with_filename_hint(self):
        """Test parsing with filename hint"""
        factory = StructuralParserFactory()
        
        content = "# Title"
        result = factory.parse(content, filename='document.md')
        
        assert result is not None
        assert result.success


@pytest.mark.integration
class TestParserIntegration:
    """Integration tests for parser system"""
    
    def test_markdown_full_workflow(self):
        """Test complete markdown parsing workflow"""
        factory = StructuralParserFactory()
        
        content = """
# Main Title

## Section 1

This is a paragraph with some **bold** text.

- Item 1
- Item 2
- Item 3

## Section 2

Another paragraph here.

```python
def example():
    return "code"
```
"""
        
        result = factory.parse(content, format_type='markdown')
        
        assert result.success
        assert len(result.document.blocks) > 5
        
        # Should have headings, paragraphs, lists, code blocks
        block_types = [block.block_type for block in result.document.blocks]
        assert 'heading' in str(block_types).lower()
    
    def test_asciidoc_full_workflow(self):
        """Test complete AsciiDoc parsing workflow"""
        factory = StructuralParserFactory()
        
        content = """
= Document Title

== Section 1

This is a paragraph.

* Item 1
* Item 2

== Section 2

Another paragraph.
"""
        
        result = factory.parse(content, format_type='asciidoc')
        
        assert result.success
        assert len(result.document.blocks) > 3
    
    def test_plaintext_full_workflow(self):
        """Test complete plaintext parsing workflow"""
        factory = StructuralParserFactory()
        
        content = """
This is a plain text document.

It has multiple paragraphs.

Each separated by blank lines.
"""
        
        result = factory.parse(content, format_type='plaintext')
        
        assert result.success
        assert len(result.document.blocks) > 0
    
    def test_format_auto_detection_workflow(self):
        """Test automatic format detection in full workflow"""
        factory = StructuralParserFactory()
        
        # Test with different formats
        test_cases = [
            ("# Markdown Title\n\nContent", 'markdown'),
            ("= AsciiDoc Title\n\nContent", 'asciidoc'),
            ("Plain text content", 'plaintext'),
        ]
        
        for content, expected_format in test_cases:
            result = factory.parse(content)
            assert result.success, f"Failed to parse {expected_format}"

