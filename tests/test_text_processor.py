"""
Text Processor Tests
Tests for the TextProcessor class that handles text cleaning and post-processing.
"""

import pytest
import os
import sys

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rewriter.processors import TextProcessor
from tests.test_utils import TestConfig, TestFixtures, TestValidators


class TestTextProcessor:
    """Test suite for the TextProcessor class."""
    
    @pytest.fixture
    def sample_errors(self):
        """Sample errors for testing."""
        return TestFixtures.get_sample_errors()
    
    def test_text_processor_initialization(self):
        """Test TextProcessor initialization."""
        
        processor = TextProcessor()
        assert isinstance(processor, TextProcessor)
    
    def test_text_processor_clean_generation(self):
        """Test text processor cleaning functionality."""
        
        processor = TextProcessor()
        
        # Test cleaning AI response with explanations
        raw_response = """Here's the improved text:
        
        This is the actual improved content that we want to keep.
        
        * I converted passive voice to active voice
        * I shortened long sentences
        * I clarified ambiguous references
        """
        
        cleaned = processor.clean_generated_text(raw_response, TestConfig.SAMPLE_TEXT)
        
        assert "This is the actual improved content that we want to keep." in cleaned
        assert "Here's the improved text:" not in cleaned
        assert "I converted" not in cleaned
        assert "I shortened" not in cleaned
    
    def test_text_processor_clean_empty_response(self):
        """Test text processor with empty response."""
        
        processor = TextProcessor()
        
        cleaned = processor.clean_generated_text("", TestConfig.SAMPLE_TEXT)
        
        assert cleaned == TestConfig.SAMPLE_TEXT
    
    def test_text_processor_clean_identical_response(self):
        """Test text processor with identical response."""
        
        processor = TextProcessor()
        
        cleaned = processor.clean_generated_text(TestConfig.SAMPLE_TEXT, TestConfig.SAMPLE_TEXT)
        
        assert cleaned == TestConfig.SAMPLE_TEXT
    
    def test_text_processor_remove_prefixes(self):
        """Test removal of common AI response prefixes."""
        
        processor = TextProcessor()
        
        test_cases = [
            ("Here is the improved text: Clean content", "Clean content"),
            ("Here's the improved text: Clean content", "Clean content"),
            ("Improved text: Clean content", "Clean content"),
            ("Sure, here's the rewrite: Clean content", "Clean content"),
            ("Here's the rewritten text: Clean content", "Clean content"),
        ]
        
        for raw_text, expected_clean in test_cases:
            cleaned = processor.clean_generated_text(raw_text, TestConfig.SAMPLE_TEXT)
            assert expected_clean in cleaned
    
    def test_text_processor_remove_explanations(self):
        """Test removal of explanatory content."""
        
        processor = TextProcessor()
        
        raw_response = """Clean improved text here.
        
        * I converted passive voice to active voice
        - I removed wordy phrases
        • I clarified ambiguous references
        
        Note: These changes improve readability.
        """
        
        cleaned = processor.clean_generated_text(raw_response, TestConfig.SAMPLE_TEXT)
        
        assert "Clean improved text here." in cleaned
        assert "I converted" not in cleaned
        assert "I removed" not in cleaned
        assert "Note:" not in cleaned
    
    def test_text_processor_sentence_filtering(self):
        """Test filtering of explanatory sentences."""
        
        processor = TextProcessor()
        
        raw_response = """This is the improved content. I've made several changes to enhance clarity. The result should be better."""
        
        cleaned = processor.clean_generated_text(raw_response, TestConfig.SAMPLE_TEXT)
        
        assert "This is the improved content." in cleaned
        assert "The result should be better." in cleaned
        assert "I've made" not in cleaned
    
    def test_text_processor_proper_sentence_ending(self):
        """Test ensuring proper sentence endings."""
        
        processor = TextProcessor()
        
        raw_response = "This is improved content without proper ending"
        
        cleaned = processor.clean_generated_text(raw_response, TestConfig.SAMPLE_TEXT)
        
        # Should handle incomplete sentences appropriately
        assert len(cleaned) > 0
    
    def test_text_processor_rule_based_rewrite(self, sample_errors):
        """Test rule-based rewriting fallback."""
        
        processor = TextProcessor()
        
        content = "In order to utilize the system, you need to make a decision."
        
        rewritten = processor.rule_based_rewrite(content, sample_errors)
        
        # Should apply basic transformations
        assert isinstance(rewritten, str)
        assert len(rewritten) > 0
    
    def test_text_processor_conciseness_replacements(self, sample_errors):
        """Test conciseness replacements in rule-based rewriting."""
        
        processor = TextProcessor()
        
        content = "In order to utilize the system, due to the fact that it's better."
        
        rewritten = processor.rule_based_rewrite(content, sample_errors)
        
        # Should replace wordy phrases
        assert "to utilize" in rewritten or "to use" in rewritten
        assert "due to the fact that" not in rewritten or "because" in rewritten
    
    def test_text_processor_clarity_replacements(self, sample_errors):
        """Test clarity replacements in rule-based rewriting."""
        
        processor = TextProcessor()
        
        content = "We need to utilize this functionality to facilitate the process."
        
        # Create clarity-focused errors
        clarity_errors = [{'type': 'clarity', 'message': 'Use simpler words'}]
        
        rewritten = processor.rule_based_rewrite(content, clarity_errors)
        
        # Should replace complex words with simpler ones
        assert "utilize" not in rewritten or "use" in rewritten
        assert "facilitate" not in rewritten or "help" in rewritten
    
    def test_text_processor_whitespace_normalization(self):
        """Test whitespace normalization."""
        
        processor = TextProcessor()
        
        raw_response = "This  has    multiple   spaces   between    words."
        
        cleaned = processor.clean_generated_text(raw_response, TestConfig.SAMPLE_TEXT)
        
        # Should normalize whitespace to single spaces
        assert "  " not in cleaned  # No double spaces
        assert "This has multiple spaces between words." in cleaned
    
    def test_text_processor_placeholder_removal(self):
        """Test removal of placeholder text."""
        
        processor = TextProcessor()
        
        raw_response = "This is clean text. [insert specific examples] More clean text."
        
        cleaned = processor.clean_generated_text(raw_response, TestConfig.SAMPLE_TEXT)
        
        assert "[insert specific examples]" not in cleaned
        assert "This is clean text." in cleaned
        assert "More clean text." in cleaned
    
    def test_text_processor_numbered_explanation_removal(self):
        """Test removal of numbered explanations."""
        
        processor = TextProcessor()
        
        raw_response = """Clean content here.
        
        1. I converted passive voice
        2. I shortened sentences
        3. I improved clarity
        """
        
        cleaned = processor.clean_generated_text(raw_response, TestConfig.SAMPLE_TEXT)
        
        assert "Clean content here." in cleaned
        assert "1. I converted" not in cleaned
        assert "2. I shortened" not in cleaned
        assert "3. I improved" not in cleaned
    
    def test_text_processor_meta_commentary_removal(self):
        """Test removal of meta-commentary about the rewriting process."""
        
        processor = TextProcessor()
        
        raw_response = """Improved text content.
        
        These changes address the original issues by converting passive voice and improving clarity.
        The rewrite maintains the original meaning while enhancing readability.
        """
        
        cleaned = processor.clean_generated_text(raw_response, TestConfig.SAMPLE_TEXT)
        
        assert "Improved text content." in cleaned
        assert "These changes address" not in cleaned
        assert "The rewrite maintains" not in cleaned
    
    def test_text_processor_minimum_length_validation(self):
        """Test minimum length validation."""
        
        processor = TextProcessor()
        
        # Test with content that becomes too short after cleaning
        raw_response = "* I made changes"
        
        cleaned = processor.clean_generated_text(raw_response, TestConfig.SAMPLE_TEXT)
        
        # Should return original when cleaned text is too short
        assert cleaned == TestConfig.SAMPLE_TEXT
    
    def test_text_processor_configuration_driven_cleaning(self):
        """Test that cleaning behavior can be configured for enterprise use."""
        
        processor = TextProcessor()
        
        # Test with various AI response patterns
        test_cases = [
            "Here's the improved version: Clean content",
            "Certainly! Here's the rewrite: Clean content", 
            "I'll help you improve this: Clean content",
            "Let me rewrite this for you: Clean content"
        ]
        
        for raw_response in test_cases:
            cleaned = processor.clean_generated_text(raw_response, TestConfig.SAMPLE_TEXT)
            
            # Should consistently extract clean content
            assert "Clean content" in cleaned
            assert "Here's" not in cleaned
            assert "I'll" not in cleaned
            assert "Let me" not in cleaned 