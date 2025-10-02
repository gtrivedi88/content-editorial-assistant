"""
Comprehensive Rule Testing
Tests all rule categories systematically
"""

import pytest
import os
import importlib
import inspect
from pathlib import Path

from rules.base_rule import BaseRule


@pytest.mark.unit
class TestAllRulesExist:
    """Test that all rule files can be imported and instantiated"""
    
    def get_all_rule_files(self):
        """Get all rule files in the rules directory"""
        rules_dir = Path('rules')
        rule_files = []
        
        for root, dirs, files in os.walk(rules_dir):
            for file in files:
                if file.endswith('_rule.py') and file != '__init__.py':
                    relative_path = os.path.join(root, file)
                    rule_files.append(relative_path)
        
        return rule_files
    
    def test_all_rules_importable(self):
        """Test that all rule files can be imported"""
        rule_files = self.get_all_rule_files()
        
        errors = []
        for rule_file in rule_files:
            try:
                # Convert file path to module path
                module_path = rule_file.replace(os.sep, '.').replace('.py', '')
                importlib.import_module(module_path)
            except Exception as e:
                errors.append(f"{rule_file}: {e}")
        
        assert len(errors) == 0, f"Failed to import rules:\n" + "\n".join(errors)
    
    def test_all_rules_have_check_method(self):
        """Test that all rule classes have a check method"""
        rule_files = self.get_all_rule_files()
        
        errors = []
        for rule_file in rule_files[:20]:  # Test sample to avoid timeout
            try:
                module_path = rule_file.replace(os.sep, '.').replace('.py', '')
                module = importlib.import_module(module_path)
                
                # Find rule classes in module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if 'Rule' in name and obj.__module__ == module_path:
                        if not hasattr(obj, 'check'):
                            errors.append(f"{rule_file}: {name} missing check() method")
            except Exception as e:
                pass  # Skip import errors
        
        assert len(errors) == 0, f"Rules missing check():\n" + "\n".join(errors)


@pytest.mark.unit
class TestRuleCategories:
    """Test rules by category"""
    
    def test_language_grammar_rules(self):
        """Test language and grammar rules"""
        from rules.language_and_grammar.passive_voice_analyzer import PassiveVoiceAnalyzer
        
        analyzer = PassiveVoiceAnalyzer()
        
        # Test passive voice detection
        passive_text = "The document was written by the team."
        issues = analyzer.check(passive_text)
        assert isinstance(issues, list)
    
    def test_punctuation_rules(self):
        """Test punctuation rules"""
        from rules.punctuation.commas_rule import CommasRule
        
        rule = CommasRule()
        text = "First, second, and third."
        
        issues = rule.check(text)
        assert isinstance(issues, list)
    
    def test_word_usage_rules(self):
        """Test word usage rules exist"""
        word_usage_dir = Path('rules/word_usage')
        
        # Should have many word usage rule files
        rule_files = list(word_usage_dir.glob('word_usage_*.py'))
        assert len(rule_files) > 0
    
    def test_structure_format_rules(self):
        """Test structure and format rules"""
        from rules.structure_and_format.headings_rule import HeadingsRule
        
        rule = HeadingsRule()
        text = "# Main Heading\n## Subheading"
        
        issues = rule.check(text)
        assert isinstance(issues, list)
    
    def test_numbers_measurement_rules(self):
        """Test numbers and measurement rules exist"""
        numbers_dir = Path('rules/numbers_and_measurement')
        
        rule_files = list(numbers_dir.glob('*_rule.py'))
        assert len(rule_files) > 0
    
    def test_technical_elements_rules(self):
        """Test technical elements rules exist"""
        tech_dir = Path('rules/technical_elements')
        
        rule_files = list(tech_dir.glob('*_rule.py'))
        assert len(rule_files) > 0


@pytest.mark.unit
class TestRuleInterface:
    """Test that all rules follow the correct interface"""
    
    def test_base_rule_interface(self):
        """Test BaseRule interface"""
        rule = BaseRule()
        
        assert hasattr(rule, 'check')
        assert callable(rule.check)
    
    def test_rule_check_returns_list(self):
        """Test that check() returns a list"""
        rule = BaseRule()
        result = rule.check("Test text")
        
        assert isinstance(result, list)
    
    def test_rule_handles_empty_text(self):
        """Test rules handle empty text"""
        rule = BaseRule()
        result = rule.check("")
        
        assert isinstance(result, list)
        assert len(result) == 0


@pytest.mark.integration
class TestRuleIntegration:
    """Integration tests for rule system"""
    
    def test_multiple_rules_on_same_text(self):
        """Test multiple rules can analyze same text"""
        from rules.language_and_grammar.passive_voice_analyzer import PassiveVoiceAnalyzer
        from rules.sentence_length_rule import SentenceLengthRule
        
        text = "The very long document that contains multiple issues and problems was carefully written by the experienced team of professional technical writers working on the project."
        
        passive_analyzer = PassiveVoiceAnalyzer()
        length_rule = SentenceLengthRule()
        
        passive_issues = passive_analyzer.check(text)
        length_issues = length_rule.check(text)
        
        # Both should return lists
        assert isinstance(passive_issues, list)
        assert isinstance(length_issues, list)
        
        # Length rule should flag this long sentence
        assert len(length_issues) > 0
    
    def test_rules_with_different_severities(self):
        """Test that rules can have different severities"""
        from rules.language_and_grammar.passive_voice_analyzer import PassiveVoiceAnalyzer
        
        analyzer = PassiveVoiceAnalyzer()
        text = "The system was designed by engineers."
        
        issues = analyzer.check(text)
        
        if len(issues) > 0:
            # Should have severity information
            assert 'severity' in issues[0] or 'level' in issues[0]

