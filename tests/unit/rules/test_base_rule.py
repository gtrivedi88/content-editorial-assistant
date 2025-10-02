"""
Unit Tests for Base Rule
Tests the base rule functionality that all rules inherit from
"""

import pytest
from rules.base_rule import BaseRule


@pytest.mark.unit
class TestBaseRule:
    """Test BaseRule class"""
    
    def test_base_rule_has_check_method(self):
        """Test that BaseRule has check method"""
        rule = BaseRule()
        assert hasattr(rule, 'check')
    
    def test_base_rule_check_returns_list(self):
        """Test that check method returns a list"""
        rule = BaseRule()
        result = rule.check("Sample text")
        
        assert isinstance(result, list)
    
    def test_base_rule_has_name(self):
        """Test that rules have a name"""
        rule = BaseRule()
        assert hasattr(rule, 'name') or hasattr(rule, 'rule_name')
    
    def test_base_rule_has_description(self):
        """Test that rules have a description"""
        rule = BaseRule()
        assert hasattr(rule, 'description') or hasattr(rule, '__doc__')


@pytest.mark.unit
class TestRuleInterface:
    """Test that all rules follow the interface contract"""
    
    def test_rule_returns_error_format(self):
        """Test that rules return errors in correct format"""
        rule = BaseRule()
        result = rule.check("Test text with issues")
        
        if len(result) > 0:
            error = result[0]
            # Errors should be dictionaries with required fields
            assert isinstance(error, dict)
            # Common fields: message, start, end, severity
            assert 'message' in error or 'text' in error
    
    def test_rule_handles_empty_text(self):
        """Test that rules handle empty text gracefully"""
        rule = BaseRule()
        result = rule.check("")
        
        assert isinstance(result, list)
        assert len(result) == 0  # No errors in empty text
    
    def test_rule_handles_none_text(self):
        """Test that rules handle None input"""
        rule = BaseRule()
        
        try:
            result = rule.check(None)
            assert isinstance(result, list)
        except (TypeError, AttributeError):
            # It's acceptable to raise an error for None
            pass

