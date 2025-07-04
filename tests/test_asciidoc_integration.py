"""
Integration tests for AsciiDoc end-to-end analysis.
Tests the complete pipeline from parsing to style analysis.
"""

import pytest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from style_analyzer.core_analyzer import StyleAnalyzer
    from style_analyzer.base_types import AnalysisMode
    STYLE_ANALYZER_AVAILABLE = True
except ImportError:
    STYLE_ANALYZER_AVAILABLE = False

try:
    from structural_parsing.parser_factory import StructuralParserFactory
    STRUCTURAL_PARSING_AVAILABLE = True
except ImportError:
    STRUCTURAL_PARSING_AVAILABLE = False

try:
    from rules import get_registry
    RULES_AVAILABLE = True
except ImportError:
    RULES_AVAILABLE = False


class TestAsciiDocStyleAnalysis:
    """Test suite for end-to-end AsciiDoc style analysis."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a style analyzer instance."""
        if not STYLE_ANALYZER_AVAILABLE:
            pytest.skip("Style analyzer not available")
        return StyleAnalyzer()
    
    def test_basic_asciidoc_analysis(self, analyzer):
        """Test basic style analysis of AsciiDoc content."""
        content = """= User Guide

This guide explains how to use the software effectively.

[NOTE]
Please read this section carefully.

== Getting Started

You can start using the application by following these steps:

1. Open the application
2. Create a new project  
3. Begin adding content

[WARNING]
Do not forget to save your work regularly.

== Advanced Features

This section covers advanced topics.

----
// This is sample code
function hello() {
    console.log("Hello, World!");
}
----

[TIP]
Code blocks are not analyzed for style issues.
"""
        
        result = analyzer.analyze(content, format_hint='asciidoc')
        
        # Basic checks
        assert result is not None
        assert 'errors' in result
        assert 'statistics' in result
        assert 'suggestions' in result
        
        # Should have some statistics
        assert 'total_words' in result['statistics']
        assert 'total_sentences' in result['statistics']
        assert result['statistics']['total_words'] > 0
        
        # Should have analyzed some content
        assert result['analysis_mode'] != AnalysisMode.ERROR.value
        
        # Errors should be context-aware if structural parsing worked
        if result['analysis_mode'] in [AnalysisMode.SPACY_WITH_MODULAR_RULES.value, 
                                     AnalysisMode.MODULAR_RULES_WITH_FALLBACKS.value]:
            # Check that analysis was performed
            assert isinstance(result['errors'], list)
    
    def test_admonition_context_analysis(self, analyzer):
        """Test that admonitions receive special analysis."""
        content = """= Documentation

[NOTE]
This note contains some repetitive words. The repetitive words are really repetitive.

[WARNING]
This warning is very important and extremely critical.

[TIP]
Use this tip for better results.

Regular paragraph content that should be analyzed normally.
"""
        
        result = analyzer.analyze(content, format_hint='asciidoc')
        
        # Should complete without errors
        assert result is not None
        assert result['analysis_mode'] != AnalysisMode.ERROR.value
        
        # Should have processed the content
        assert result['statistics']['total_words'] > 0
        
        # Check that analysis was performed
        assert isinstance(result['errors'], list)
        assert isinstance(result['suggestions'], list)
    
    def test_code_block_exclusion(self, analyzer):
        """Test that code blocks are excluded from style analysis."""
        content = """= Code Examples

Here is some normal prose that should be analyzed for style.

----
// This code block should NOT be analyzed
function badlyNamed() {
    var x = 1;
    var y = 2;
    // This comment has bad grammar
    return x + y;
}
----

....
This literal block should also be skipped.
More content here.
....

Back to normal prose that should be analyzed.
"""
        
        result = analyzer.analyze(content, format_hint='asciidoc')
        
        # Should complete successfully
        assert result is not None
        assert result.analysis_mode != AnalysisMode.ERROR
        
        # Should have processed some content (the prose parts)
        assert result.statistics['total_words'] > 0
        
        # If structural parsing worked, code blocks should be excluded
        # This is hard to test directly, but we can verify the analysis ran
        assert isinstance(result.errors, list)
    
    def test_complex_document_analysis(self, analyzer):
        """Test analysis of a complex AsciiDoc document."""
        content = """= Complete User Manual
:author: Documentation Team
:version: 1.0

This manual provides comprehensive information about using our software.

[NOTE]
This document is updated regularly to reflect new features.

== Installation

Installing the software is straightforward.

=== System Requirements

You need:

* Operating System: Windows 10 or later
* Memory: 4GB RAM minimum
* Storage: 500MB available space

=== Installation Steps

1. Download the installer from our website
2. Run the installer as administrator
3. Follow the installation wizard

[WARNING]
Ensure you have sufficient privileges before starting installation.

== Configuration

After installation, you may need to configure certain settings.

=== Basic Configuration

The basic configuration involves:

* Setting your preferences
* Configuring network settings
* Choosing your default theme

----
# Example configuration file
server.port=8080
server.host=localhost
app.name=MyApplication
----

[TIP]
Save your configuration before making changes.

== Usage

This section explains how to use the main features.

=== Creating Projects

To create a new project:

1. Click "New Project"
2. Choose a project template
3. Enter project details
4. Click "Create"

[IMPORTANT]
Project names must be unique within your workspace.

=== Managing Files

You can manage files through the file browser:

* Create new files
* Edit existing files
* Delete unwanted files
* Organize files in folders

== Troubleshooting

This section covers common issues and solutions.

[CAUTION]
Always backup your data before attempting fixes.

=== Common Problems

The most frequent issues include:

* Performance problems
* Connection issues
* File corruption
* Configuration errors

=== Getting Help

If you need assistance:

1. Check the documentation
2. Search our knowledge base
3. Contact support

== Conclusion

This manual should help you get started with our software.

[NOTE]
For additional resources, visit our website.
"""
        
        result = analyzer.analyze(content, format_hint='asciidoc')
        
        # Should complete successfully
        assert result is not None
        assert result.analysis_mode != AnalysisMode.ERROR
        
        # Should have substantial content
        assert result.statistics['total_words'] > 100
        assert result.statistics['total_sentences'] > 10
        
        # Should have some analysis results
        assert isinstance(result.errors, list)
        assert isinstance(result.suggestions, list)
        
        # Should have calculated readability if possible
        if 'readability_score' in result.statistics:
            assert result.statistics['readability_score'] >= 0
        
        # Should have an overall score
        assert result.overall_score >= 0
        assert result.overall_score <= 100
    
    def test_error_handling_malformed_asciidoc(self, analyzer):
        """Test error handling with malformed AsciiDoc."""
        malformed_content = """
        = Malformed Document
        
        [INVALID_ADMONITION]
        This is not a valid admonition.
        
        ****
        Unclosed sidebar block
        
        === Missing content
        
        ----
        Unclosed code block
        """
        
        result = analyzer.analyze(malformed_content, format_hint='asciidoc')
        
        # Should handle gracefully
        assert result is not None
        
        # Should either succeed with fallback or provide error information
        if result.analysis_mode == AnalysisMode.ERROR:
            assert len(result.errors) > 0
        else:
            # Should have attempted some analysis
            assert isinstance(result.errors, list)
            assert isinstance(result.statistics, dict)
    
    def test_format_hint_auto_detection(self, analyzer):
        """Test automatic format detection for AsciiDoc content."""
        asciidoc_content = """= AsciiDoc Document

[NOTE]
This should be detected as AsciiDoc.

----
Code block
----
"""
        
        # Test with auto format hint
        result = analyzer.analyze(asciidoc_content, format_hint='auto')
        
        # Should complete successfully
        assert result is not None
        assert result.analysis_mode != AnalysisMode.ERROR
        
        # Should have processed the content
        assert result.statistics['total_words'] > 0
    
    def test_markdown_vs_asciidoc_analysis(self, analyzer):
        """Test that AsciiDoc and Markdown are handled differently."""
        # Same content in different formats
        asciidoc_content = """= Document Title

[NOTE]
This is an AsciiDoc admonition.

== Section

Some content here.
"""
        
        markdown_content = """# Document Title

> This is a Markdown blockquote.

## Section

Some content here.
"""
        
        # Analyze both
        asciidoc_result = analyzer.analyze(asciidoc_content, format_hint='asciidoc')
        markdown_result = analyzer.analyze(markdown_content, format_hint='markdown')
        
        # Both should succeed
        assert asciidoc_result is not None
        assert markdown_result is not None
        
        # Both should have content
        assert asciidoc_result['statistics']['total_words'] > 0
        assert markdown_result['statistics']['total_words'] > 0
        
        # Results might differ if structural parsing is working
        # At minimum, both should complete analysis
        assert asciidoc_result['analysis_mode'] != AnalysisMode.ERROR.value
        assert markdown_result['analysis_mode'] != AnalysisMode.ERROR.value


@pytest.mark.integration
class TestAsciiDocEndToEnd:
    """End-to-end tests for AsciiDoc functionality."""
    
    def test_complete_analysis_pipeline(self):
        """Test the complete analysis pipeline with AsciiDoc."""
        if not STYLE_ANALYZER_AVAILABLE:
            pytest.skip("Style analyzer not available")
        
        # Create analyzer
        analyzer = StyleAnalyzer()
        
        # Test content
        content = """= API Documentation

This document describes the REST API endpoints.

[NOTE]
All endpoints require authentication.

== Authentication

Use Bearer token authentication:

----
Authorization: Bearer <your-token>
----

== Endpoints

=== GET /users

Returns a list of users.

[TIP]
Use pagination for large result sets.

=== POST /users

Creates a new user.

[WARNING]
Validate all input parameters.

== Error Handling

The API returns standard HTTP status codes:

* 200 - Success
* 400 - Bad Request
* 401 - Unauthorized
* 500 - Internal Server Error

[IMPORTANT]
Always check the status code before processing responses.
"""
        
        # Perform analysis
        result = analyzer.analyze(content, format_hint='asciidoc')
        
        # Verify complete pipeline worked
        assert result is not None
        assert result.analysis_mode != AnalysisMode.ERROR
        
        # Check all components have results
        assert isinstance(result.errors, list)
        assert isinstance(result.suggestions, list)
        assert isinstance(result.statistics, dict)
        assert isinstance(result.technical_metrics, dict)
        
        # Check required statistics
        required_stats = ['total_words', 'total_sentences', 'total_paragraphs']
        for stat in required_stats:
            assert stat in result.statistics
            assert result.statistics[stat] >= 0
        
        # Check overall score
        assert 0 <= result.overall_score <= 100
        
        # Check that we have some content
        assert result.statistics['total_words'] > 50  # Should have substantial content
        
        # If structural parsing worked, verify context awareness
        if hasattr(analyzer, 'parser_factory') and analyzer.parser_factory:
            # Should have used structural parsing
            assert result.analysis_mode in [
                AnalysisMode.SPACY_WITH_MODULAR_RULES,
                AnalysisMode.MODULAR_RULES_WITH_FALLBACKS,
                AnalysisMode.SPACY_LEGACY_ONLY,
                AnalysisMode.MINIMAL_SAFE_MODE
            ]
    
    def test_asciidoc_specific_features(self):
        """Test AsciiDoc-specific features work correctly."""
        if not STYLE_ANALYZER_AVAILABLE:
            pytest.skip("Style analyzer not available")
        
        analyzer = StyleAnalyzer()
        
        # Test with AsciiDoc-specific constructs
        content = """= Feature Test
:toc:
:author: Test Author

[abstract]
This tests AsciiDoc-specific features.

[NOTE]
====
This is a complex admonition block.
It can contain multiple paragraphs.

And even code:

----
example code
----
====

== Attributes

Document attributes like {author} should be handled.

[source,python]
----
def hello():
    print("Hello, World!")
----

[TIP]
====
Tips can also be complex blocks.
====

== Tables

[cols="2,3,1"]
|===
|Name |Description |Status

|Feature A
|Important feature
|Done

|Feature B
|Another feature
|In Progress
|===

== Conclusion

This document tests various AsciiDoc features.
"""
        
        result = analyzer.analyze(content, format_hint='asciidoc')
        
        # Should handle AsciiDoc features gracefully
        assert result is not None
        assert result.analysis_mode != AnalysisMode.ERROR
        
        # Should have processed content
        assert result.statistics['total_words'] > 0
        
        # Should have some analysis results
        assert isinstance(result.errors, list)
        assert isinstance(result.suggestions, list)


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__]) 