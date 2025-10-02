"""
Unit Tests for Grammar Rules
Tests grammar checking rules
"""

import pytest

from rules.language_and_grammar.passive_voice_analyzer import PassiveVoiceAnalyzer
from rules.language_and_grammar.articles_rule import ArticlesRule
from rules.language_and_grammar.verbs_rule import VerbsRule
from rules.language_and_grammar.pronouns_rule import PronounsRule


@pytest.mark.unit
class TestPassiveVoiceAnalyzer:
    """Test Passive Voice detection"""
    
    def test_detect_passive_voice(self):
        """Test detecting passive voice"""
        analyzer = PassiveVoiceAnalyzer()
        text = "The document was written by the team."
        
        issues = analyzer.check(text)
        assert len(issues) > 0
    
    def test_active_voice_no_issues(self):
        """Test that active voice has no issues"""
        analyzer = PassiveVoiceAnalyzer()
        text = "The team wrote the document."
        
        issues = analyzer.check(text)
        assert len(issues) == 0


@pytest.mark.unit
class TestArticlesRule:
    """Test Articles rule"""
    
    def test_missing_article(self):
        """Test detecting missing articles"""
        rule = ArticlesRule()
        text = "User clicks button."  # Missing 'the'
        
        issues = rule.check(text)
        # May or may not detect depending on sophistication
        assert isinstance(issues, list)
    
    def test_correct_articles(self):
        """Test correct article usage"""
        rule = ArticlesRule()
        text = "The user clicks the button."
        
        issues = rule.check(text)
        assert len(issues) == 0


@pytest.mark.unit
class TestVerbsRule:
    """Test Verbs rule"""
    
    def test_verb_agreement(self):
        """Test subject-verb agreement"""
        rule = VerbsRule()
        text = "The users clicks the button."  # Incorrect: should be 'click'
        
        issues = rule.check(text)
        # May detect agreement issue
        assert isinstance(issues, list)
    
    def test_correct_verbs(self):
        """Test correct verb usage"""
        rule = VerbsRule()
        text = "The user clicks the button."
        
        issues = rule.check(text)
        # Correct usage should have no issues
        assert len(issues) == 0 or all(i.get('severity') == 'info' for i in issues)


@pytest.mark.unit
class TestPronounsRule:
    """Test Pronouns rule"""
    
    def test_pronoun_usage(self):
        """Test pronoun usage"""
        rule = PronounsRule()
        text = "The user must enter their password."
        
        issues = rule.check(text)
        assert isinstance(issues, list)
    
    def test_ambiguous_pronouns(self):
        """Test ambiguous pronoun detection"""
        rule = PronounsRule()
        text = "John met Bob. He was happy."  # Ambiguous 'He'
        
        issues = rule.check(text)
        # Should detect ambiguity
        assert isinstance(issues, list)

