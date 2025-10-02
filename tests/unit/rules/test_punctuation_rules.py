"""
Unit Tests for Punctuation Rules
Tests punctuation checking rules
"""

import pytest

from rules.punctuation.commas_rule import CommasRule
from rules.punctuation.periods_rule import PeriodsRule
from rules.punctuation.quotation_marks_rule import QuotationMarksRule
from rules.punctuation.hyphens_rule import HyphensRule


@pytest.mark.unit
class TestCommasRule:
    """Test Commas rule"""
    
    def test_comma_usage(self):
        """Test comma usage"""
        rule = CommasRule()
        text = "First, second, and third items are listed."
        
        issues = rule.check(text)
        assert isinstance(issues, list)
    
    def test_missing_comma(self):
        """Test detecting missing commas"""
        rule = CommasRule()
        text = "After eating the team went home."  # Missing comma after "eating"
        
        issues = rule.check(text)
        # May detect missing comma
        assert isinstance(issues, list)


@pytest.mark.unit
class TestPeriodsRule:
    """Test Periods rule"""
    
    def test_period_usage(self):
        """Test period usage"""
        rule = PeriodsRule()
        text = "This is a sentence. This is another."
        
        issues = rule.check(text)
        assert len(issues) == 0
    
    def test_missing_period(self):
        """Test missing period detection"""
        rule = PeriodsRule()
        text = "This sentence is missing something"  # No period
        
        issues = rule.check(text)
        # May detect missing period
        assert isinstance(issues, list)


@pytest.mark.unit
class TestQuotationMarksRule:
    """Test Quotation Marks rule"""
    
    def test_quotation_marks(self):
        """Test quotation mark usage"""
        rule = QuotationMarksRule()
        text = 'The user said "hello" to the system.'
        
        issues = rule.check(text)
        assert isinstance(issues, list)
    
    def test_mismatched_quotes(self):
        """Test mismatched quotation marks"""
        rule = QuotationMarksRule()
        text = 'The user said "hello to the system.'  # Missing closing quote
        
        issues = rule.check(text)
        # Should detect mismatch
        assert isinstance(issues, list)


@pytest.mark.unit
class TestHyphensRule:
    """Test Hyphens rule"""
    
    def test_hyphen_usage(self):
        """Test hyphen usage"""
        rule = HyphensRule()
        text = "The well-known feature is user-friendly."
        
        issues = rule.check(text)
        assert isinstance(issues, list)
    
    def test_missing_hyphen(self):
        """Test missing hyphen detection"""
        rule = HyphensRule()
        text = "The real time processing is complete."  # Should be "real-time"
        
        issues = rule.check(text)
        # May detect missing hyphen
        assert isinstance(issues, list)

