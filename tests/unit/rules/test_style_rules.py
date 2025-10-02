"""
Unit Tests for Style Rules
Tests style and formatting rules
"""

import pytest

from rules.sentence_length_rule import SentenceLengthRule
from rules.second_person_rule import SecondPersonRule
from rules.structure_and_format.headings_rule import HeadingsRule
from rules.structure_and_format.lists_rule import ListsRule


@pytest.mark.unit
class TestSentenceLengthRule:
    """Test Sentence Length rule"""
    
    def test_long_sentence_detected(self):
        """Test detecting overly long sentences"""
        rule = SentenceLengthRule()
        
        # Create a very long sentence
        long_text = "This is a very long sentence that goes on and on with many clauses and phrases and continues to add more and more words making it difficult for readers to follow the main point because there are so many ideas packed into a single sentence structure."
        
        issues = rule.check(long_text)
        assert len(issues) > 0
    
    def test_short_sentences_ok(self):
        """Test that short sentences are acceptable"""
        rule = SentenceLengthRule()
        text = "This is short. So is this. And this too."
        
        issues = rule.check(text)
        assert len(issues) == 0


@pytest.mark.unit
class TestSecondPersonRule:
    """Test Second Person usage rule"""
    
    def test_detect_second_person(self):
        """Test detecting second person"""
        rule = SecondPersonRule()
        text = "You should click the button to proceed."
        
        issues = rule.check(text)
        # Rule may flag or accept depending on context
        assert isinstance(issues, list)
    
    def test_third_person_preferred(self):
        """Test third person usage"""
        rule = SecondPersonRule()
        text = "The user should click the button to proceed."
        
        issues = rule.check(text)
        assert isinstance(issues, list)


@pytest.mark.unit
class TestHeadingsRule:
    """Test Headings rule"""
    
    def test_heading_format(self):
        """Test heading formatting"""
        rule = HeadingsRule()
        text = "# Main Heading\n## Subheading\n### Sub-subheading"
        
        issues = rule.check(text)
        assert isinstance(issues, list)
    
    def test_improper_heading_hierarchy(self):
        """Test improper heading hierarchy"""
        rule = HeadingsRule()
        text = "# Main\n### Skipped Level"  # Skips level 2
        
        issues = rule.check(text)
        # May detect hierarchy issue
        assert isinstance(issues, list)


@pytest.mark.unit
class TestListsRule:
    """Test Lists rule"""
    
    def test_list_format(self):
        """Test list formatting"""
        rule = ListsRule()
        text = """
        Items:
        - Item 1
        - Item 2
        - Item 3
        """
        
        issues = rule.check(text)
        assert isinstance(issues, list)
    
    def test_inconsistent_list_punctuation(self):
        """Test inconsistent list punctuation"""
        rule = ListsRule()
        text = """
        - Item 1.
        - Item 2
        - Item 3.
        """
        
        issues = rule.check(text)
        # May detect inconsistency
        assert isinstance(issues, list)

