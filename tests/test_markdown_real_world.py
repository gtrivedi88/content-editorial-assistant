"""
Real-world markdown document testing.

Tests the parser against actual markdown files of varying complexity.
"""

import unittest
import os
from pathlib import Path

from structural_parsing import StructuralParserFactory
from structural_parsing.markdown.types import MarkdownBlockType


class TestMarkdownRealWorldDocuments(unittest.TestCase):
    """Test parsing of real-world markdown documents."""

    def setUp(self):
        self.factory = StructuralParserFactory()
        self.test_docs_dir = Path(__file__).parent / "test_markdown_documents"

    def load_test_document(self, filename: str) -> str:
        """Load a test document from the test documents directory."""
        file_path = self.test_docs_dir / filename
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_simple_document(self):
        """Test parsing of simple markdown document."""
        content = self.load_test_document("simple.md")
        result = self.factory.parse(content, filename="simple.md")
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertGreater(len(result.document.blocks), 5)
        
        # Verify we have expected block types
        block_types = [block.block_type for block in result.document.blocks]
        
        # Should have headings
        self.assertIn(MarkdownBlockType.HEADING, block_types)
        # Should have paragraphs
        self.assertIn(MarkdownBlockType.PARAGRAPH, block_types)
        # Should have lists
        self.assertIn(MarkdownBlockType.UNORDERED_LIST, block_types)
        # Should have code blocks
        self.assertIn(MarkdownBlockType.CODE_BLOCK, block_types)
        # Should have blockquotes
        self.assertIn(MarkdownBlockType.BLOCKQUOTE, block_types)

    def test_complex_document(self):
        """Test parsing of complex markdown document with advanced features."""
        content = self.load_test_document("complex.md")
        result = self.factory.parse(content, filename="complex.md")
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertGreater(len(result.document.blocks), 20)
        
        # Verify we have expected block types for complex document
        block_types = [block.block_type for block in result.document.blocks]
        
        # Should have various block types
        expected_types = [
            MarkdownBlockType.HEADING,
            MarkdownBlockType.PARAGRAPH,
            MarkdownBlockType.UNORDERED_LIST,
            MarkdownBlockType.CODE_BLOCK,
            MarkdownBlockType.BLOCKQUOTE,
        ]
        
        for expected_type in expected_types:
            self.assertIn(expected_type, block_types, 
                         f"Expected {expected_type} not found in block types")

    def test_edge_cases_document(self):
        """Test parsing of document with edge cases and potential problems."""
        content = self.load_test_document("edge_cases.md")
        result = self.factory.parse(content, filename="edge_cases.md")
        
        # Should parse successfully even with edge cases
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertGreater(len(result.document.blocks), 1)

    def test_real_world_document(self):
        """Test parsing of realistic documentation-style markdown."""
        content = self.load_test_document("real_world.md")
        result = self.factory.parse(content, filename="real_world.md")
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertGreater(len(result.document.blocks), 50)


class TestMarkdownPerformance(unittest.TestCase):
    """Performance tests for markdown parser."""

    def setUp(self):
        self.factory = StructuralParserFactory()

    def test_large_document_performance(self):
        """Test performance with large documents."""
        import time
        
        # Create a large document
        large_content = []
        for i in range(1000):
            large_content.append(f"## Section {i}")
            large_content.append(f"This is paragraph {i} with some content.")
            large_content.append("")
            large_content.append("- List item 1")
            large_content.append("- List item 2") 
            large_content.append("- List item 3")
            large_content.append("")
            if i % 10 == 0:
                large_content.append("```python")
                large_content.append(f"def function_{i}():")
                large_content.append(f'    return "Function {i}"')
                large_content.append("```")
                large_content.append("")
        
        content = "\n".join(large_content)
        
        # Measure parse time
        start_time = time.time()
        result = self.factory.parse(content, filename="large_test.md")
        end_time = time.time()
        
        parse_time = end_time - start_time
        
        # Should parse successfully
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertGreater(len(result.document.blocks), 1000)
        
        # Performance assertion (should parse in reasonable time)
        # This is lenient - adjust based on your requirements
        self.assertLess(parse_time, 10.0, 
                       f"Parsing took too long: {parse_time:.2f}s")
        
        print(f"Large document ({len(content)} chars) parsed in {parse_time:.3f}s")


if __name__ == '__main__':
    unittest.main()
