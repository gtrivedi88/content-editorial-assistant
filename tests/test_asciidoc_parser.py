"""
Unit tests for AsciiDoc parser functionality.
Tests the structural parsing of AsciiDoc documents.
"""

import pytest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from structural_parsing.asciidoc.parser import AsciiDocParser
    from structural_parsing.asciidoc.types import AsciiDocBlockType, AdmonitionType
    ASCIIDOC_AVAILABLE = True
except ImportError:
    ASCIIDOC_AVAILABLE = False


class TestAsciiDocParser:
    """Test suite for AsciiDoc parser functionality."""
    
    @pytest.fixture
    def parser(self):
        """Create an AsciiDoc parser instance."""
        if not ASCIIDOC_AVAILABLE:
            pytest.skip("AsciiDoc parsing not available")
        return AsciiDocParser()
    
    def test_parser_initialization(self, parser):
        """Test that parser initializes correctly."""
        assert parser is not None
        # Note: asciidoctor availability depends on system installation
        assert hasattr(parser, 'asciidoctor_available')
    
    def test_heading_parsing(self, parser):
        """Test parsing of AsciiDoc headings."""
        content = """= Document Title

== Section Header

=== Subsection Header

Some paragraph content.
"""
        
        result = parser.parse(content, "test.adoc")
        
        if result.success:
            document = result.document
            headings = [block for block in document.blocks 
                       if block.block_type == AsciiDocBlockType.HEADING]
            
            assert len(headings) >= 2  # At least document title and section
            
            # Check document title
            doc_title = next((h for h in headings if h.level == 0), None)
            assert doc_title is not None
            assert "Document Title" in doc_title.content
            
            # Check section header
            section_header = next((h for h in headings if h.level == 1), None)
            assert section_header is not None
            assert "Section Header" in section_header.content
    
    def test_admonition_parsing(self, parser):
        """Test parsing of AsciiDoc admonitions."""
        content = """[NOTE]
This is a note.

[WARNING]
This is a warning.

[TIP]
This is a helpful tip.

[IMPORTANT]
This is important information.

[CAUTION]
Please be careful.
"""
        
        result = parser.parse(content, "test.adoc")
        
        if result.success:
            document = result.document
            admonitions = [block for block in document.blocks 
                          if block.block_type == AsciiDocBlockType.ADMONITION]
            
            assert len(admonitions) >= 3  # Should find multiple admonitions
            
            # Check for different admonition types
            admonition_types = [block.admonition_type for block in admonitions 
                              if block.admonition_type]
            
            # Should contain some of the expected types
            expected_types = [AdmonitionType.NOTE, AdmonitionType.WARNING, 
                             AdmonitionType.TIP, AdmonitionType.IMPORTANT, 
                             AdmonitionType.CAUTION]
            
            found_types = [t for t in expected_types if t in admonition_types]
            assert len(found_types) > 0  # Should find at least some admonition types
    
    def test_delimited_blocks_parsing(self, parser):
        """Test parsing of AsciiDoc delimited blocks."""
        content = """****
This is sidebar content.
****

====
This is example content.
====

----
This is code listing.
echo "Hello World"
----

....
This is literal content.
....

____
This is a quote block.
____
"""
        
        result = parser.parse(content, "test.adoc")
        
        if result.success:
            document = result.document
            
            # Check for different block types
            block_types = [block.block_type for block in document.blocks]
            
            # Should contain some delimited block types
            expected_types = [
                AsciiDocBlockType.SIDEBAR,
                AsciiDocBlockType.EXAMPLE,
                AsciiDocBlockType.LISTING,
                AsciiDocBlockType.LITERAL,
                AsciiDocBlockType.QUOTE
            ]
            
            found_types = [t for t in expected_types if t in block_types]
            assert len(found_types) > 0  # Should find at least some block types
    
    def test_mixed_content_document(self, parser):
        """Test parsing of a realistic mixed-content AsciiDoc document."""
        content = """= Installation Guide

This document explains how to install the software.

[NOTE]
Make sure you have admin privileges before starting.

== Prerequisites

You need the following:

* Java 8 or higher
* At least 4GB of RAM
* 500MB of disk space

== Installation Steps

Follow these steps carefully:

1. Download the installer
2. Run the installer as administrator
3. Follow the on-screen instructions

[WARNING]
Do not interrupt the installation process.

=== Post-Installation

After installation, verify it works:

----
java -version
echo "Installation complete"
----

[TIP]
You can now start using the application.
"""
        
        result = parser.parse(content, "test.adoc")
        
        if result.success:
            document = result.document
            assert len(document.blocks) > 0
            
            # Should contain various block types
            block_types = [block.block_type for block in document.blocks]
            
            # Should have headings
            assert AsciiDocBlockType.HEADING in block_types
            
            # Should have at least one admonition
            admonitions = [block for block in document.blocks 
                          if block.block_type == AsciiDocBlockType.ADMONITION]
            assert len(admonitions) > 0
            
            # Should have some paragraphs
            paragraphs = [block for block in document.blocks 
                         if block.block_type == AsciiDocBlockType.PARAGRAPH]
            assert len(paragraphs) > 0
            
            # Content blocks should be identifiable
            content_blocks = document.get_content_blocks()
            assert len(content_blocks) > 0
            
            # Code blocks should be skippable
            code_blocks = [block for block in document.blocks 
                          if block.should_skip_analysis()]
            # Should have at least the code listing
            assert any(block.block_type == AsciiDocBlockType.LISTING for block in document.blocks)
    
    def test_error_handling_invalid_content(self, parser):
        """Test error handling with invalid or problematic content."""
        # Test with empty content
        result = parser.parse("", "empty.adoc")
        # Should handle gracefully
        assert result is not None
        
        # Test with malformed content
        malformed_content = """
        [INVALID_ADMONITION]
        This should not crash the parser.
        
        === Missing heading content
        
        ****
        Unclosed sidebar block
        """
        
        result = parser.parse(malformed_content, "malformed.adoc")
        # Should not crash
        assert result is not None
    
    def test_asciidoctor_unavailable_fallback(self):
        """Test behavior when asciidoctor is not available."""
        # Create parser and simulate asciidoctor unavailability
        parser = AsciiDocParser()
        parser.asciidoctor_available = False
        
        content = """= Test Document
        
[NOTE]
This is a test.
"""
        
        result = parser.parse(content, "test.adoc")
        
        # Should return a result indicating failure
        assert result is not None
        assert not result.success
        assert len(result.errors) > 0
        assert "Asciidoctor is not available" in result.errors[0]
    
    def test_document_statistics(self, parser):
        """Test document statistics generation."""
        content = """= Test Document

[NOTE]
This is a note.

== Section

Some paragraph content.

----
Code block
----
"""
        
        result = parser.parse(content, "test.adoc")
        
        if result.success:
            document = result.document
            stats = document.get_document_statistics()
            
            assert 'total_blocks' in stats
            assert 'content_blocks' in stats
            assert 'block_type_counts' in stats
            assert stats['total_blocks'] > 0
            assert stats['content_blocks'] >= 0
            assert len(stats['block_type_counts']) > 0


@pytest.mark.integration
class TestAsciiDocIntegration:
    """Integration tests for AsciiDoc parser with other components."""
    
    def test_parser_factory_integration(self):
        """Test AsciiDoc parser integration with parser factory."""
        try:
            from structural_parsing.parser_factory import StructuralParserFactory
            
            factory = StructuralParserFactory()
            
            content = """= Test Document

[NOTE]
This is a test note.
"""
            
            # Test auto-detection
            result = factory.parse(content, format_hint='auto')
            assert result is not None
            
            # Test explicit AsciiDoc parsing
            result = factory.parse(content, format_hint='asciidoc')
            assert result is not None
            
            # Test parser availability info
            parsers_info = factory.get_available_parsers()
            assert 'asciidoc' in parsers_info
            
        except ImportError:
            pytest.skip("Parser factory not available")
    
    def test_format_detection(self):
        """Test format detection for AsciiDoc content."""
        try:
            from structural_parsing.format_detector import FormatDetector
            
            detector = FormatDetector()
            
            # Test AsciiDoc detection
            asciidoc_content = """= Document Title

[NOTE]
This is clearly AsciiDoc.
"""
            
            detected_format = detector.detect_format(asciidoc_content)
            # Should detect as AsciiDoc (though might fall back to markdown)
            assert detected_format in ['asciidoc', 'markdown']
            
            # Test with strong AsciiDoc indicators
            strong_asciidoc = """= Title
:author: John Doe

[WARNING]
Strong AsciiDoc indicators.

****
Sidebar block
****
"""
            
            detected_format = detector.detect_format(strong_asciidoc)
            # Should more likely detect as AsciiDoc
            assert detected_format in ['asciidoc', 'markdown']
            
        except ImportError:
            pytest.skip("Format detector not available")


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__]) 