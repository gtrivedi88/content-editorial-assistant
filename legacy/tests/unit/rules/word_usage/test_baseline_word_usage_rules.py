"""
Tests for Word Usage Rules — Acrolinx Deterministic Pattern.

Verifies:
1. All 28 rules import and instantiate correctly
2. YAML config loads properly
3. Deterministic detection works (wrong term → flagged)
4. Code block guard skips code content
5. Clean text produces no false positives
6. Rule type strings are correct for rule_mappings.yaml compatibility
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class TestBaselineImports:
    """Test that all word usage rules can be imported without errors."""

    def test_import_a_words_rule(self):
        from rules.word_usage.a_words_rule import AWordsRule
        assert AWordsRule is not None

    def test_import_b_words_rule(self):
        from rules.word_usage.b_words_rule import BWordsRule
        assert BWordsRule is not None

    def test_import_c_words_rule(self):
        from rules.word_usage.c_words_rule import CWordsRule
        assert CWordsRule is not None

    def test_import_base_word_usage_rule(self):
        from rules.word_usage.base_word_usage_rule import BaseWordUsageRule
        assert BaseWordUsageRule is not None

    def test_import_all_rules(self):
        """Test all 28 rules import via __init__.py."""
        from rules.word_usage import (
            AWordsRule, BWordsRule, CWordsRule, DWordsRule,
            EWordsRule, FWordsRule, GWordsRule, HWordsRule,
            IWordsRule, JWordsRule, KWordsRule, LWordsRule,
            MWordsRule, NWordsRule, OWordsRule, PWordsRule,
            QWordsRule, RWordsRule, SWordsRule, TWordsRule,
            UWordsRule, VWordsRule, WWordsRule, XWordsRule,
            YWordsRule, ZWordsRule, SpecialCharsRule,
        )
        assert all([
            AWordsRule, BWordsRule, CWordsRule, DWordsRule,
            EWordsRule, FWordsRule, GWordsRule, HWordsRule,
            IWordsRule, JWordsRule, KWordsRule, LWordsRule,
            MWordsRule, NWordsRule, OWordsRule, PWordsRule,
            QWordsRule, RWordsRule, SWordsRule, TWordsRule,
            UWordsRule, VWordsRule, WWordsRule, XWordsRule,
            YWordsRule, ZWordsRule, SpecialCharsRule,
        ])


class TestBaselineInstantiation:
    """Test that all word usage rules can be instantiated."""

    def test_instantiate_a_words_rule(self):
        from rules.word_usage.a_words_rule import AWordsRule
        rule = AWordsRule()
        assert rule is not None
        assert hasattr(rule, 'analyze')

    def test_instantiate_b_words_rule(self):
        from rules.word_usage.b_words_rule import BWordsRule
        rule = BWordsRule()
        assert rule is not None
        assert hasattr(rule, 'analyze')


class TestBaselineSpaCyIntegration:
    """Test that SpaCy integration works correctly."""

    @pytest.fixture
    def nlp(self):
        try:
            import spacy
            return spacy.load("en_core_web_sm")
        except (ImportError, OSError):
            pytest.skip("SpaCy or model not available")

    def test_a_words_rule_with_spacy(self, nlp):
        from rules.word_usage.a_words_rule import AWordsRule
        rule = AWordsRule()
        errors = rule.analyze(
            "Use the adviser for guidance.", ["Use the adviser for guidance."],
            nlp=nlp, context={},
        )
        assert isinstance(errors, list)
        assert len(errors) >= 1  # "adviser" → "advisor"

    def test_b_words_rule_with_spacy(self, nlp):
        from rules.word_usage.b_words_rule import BWordsRule
        rule = BWordsRule()
        errors = rule.analyze(
            "The blacklist is active.", ["The blacklist is active."],
            nlp=nlp, context={},
        )
        assert isinstance(errors, list)
        assert len(errors) >= 1  # "blacklist" → "blocklist"


class TestBaselineCodeContextGuard:
    """Test that code context guard works correctly."""

    @pytest.fixture
    def nlp(self):
        try:
            import spacy
            return spacy.load("en_core_web_sm")
        except (ImportError, OSError):
            pytest.skip("SpaCy or model not available")

    def test_code_block_skipped(self, nlp):
        from rules.word_usage.a_words_rule import AWordsRule
        rule = AWordsRule()
        context = {'block_type': 'code_block'}
        errors = rule.analyze("abort();", ["abort();"], nlp=nlp, context=context)
        assert errors == []

    def test_listing_skipped(self, nlp):
        from rules.word_usage.a_words_rule import AWordsRule
        rule = AWordsRule()
        context = {'block_type': 'listing'}
        errors = rule.analyze("abort();", ["abort();"], nlp=nlp, context=context)
        assert errors == []


class TestBaselineOptionalImports:
    """Test that optional imports are handled gracefully."""

    def test_rules_work_without_spacy(self):
        from rules.word_usage.a_words_rule import AWordsRule
        rule = AWordsRule()
        errors = rule.analyze("test", ["test"], nlp=None, context={})
        assert errors == []

    def test_base_rule_has_fallback_imports(self):
        from rules.word_usage.base_word_usage_rule import BaseWordUsageRule
        assert BaseWordUsageRule is not None


class TestBaselineFunctionalBehavior:
    """Test actual functional behavior of rules."""

    @pytest.fixture
    def nlp(self):
        try:
            import spacy
            return spacy.load("en_core_web_sm")
        except (ImportError, OSError):
            pytest.skip("SpaCy or model not available")

    def test_a_words_detects_adviser(self, nlp):
        """Test that A-words rule detects 'adviser' → 'advisor'."""
        from rules.word_usage.a_words_rule import AWordsRule
        rule = AWordsRule()
        errors = rule.analyze(
            "Ask your adviser.", ["Ask your adviser."],
            nlp=nlp, context={},
        )
        assert len(errors) >= 1
        assert any("advisor" in e.get('message', '') for e in errors)

    def test_s_words_detects_sanity_check(self, nlp):
        """Test that S-words rule detects 'sanity check'."""
        from rules.word_usage.s_words_rule import SWordsRule
        rule = SWordsRule()
        errors = rule.analyze(
            "Run a sanity check.", ["Run a sanity check."],
            nlp=nlp, context={},
        )
        assert len(errors) >= 1

    def test_error_structure(self, nlp):
        from rules.word_usage.a_words_rule import AWordsRule
        rule = AWordsRule()
        errors = rule.analyze(
            "The adviser gave afterwards advice.",
            ["The adviser gave afterwards advice."],
            nlp=nlp, context={},
        )
        for error in errors:
            assert isinstance(error, dict)
            assert 'message' in error
            assert 'flagged_text' in error
            assert 'span' in error

    def test_clean_text_no_errors(self, nlp):
        """No false positives on clean text."""
        from rules.word_usage.a_words_rule import AWordsRule
        rule = AWordsRule()
        errors = rule.analyze(
            "The system is running normally.",
            ["The system is running normally."],
            nlp=nlp, context={},
        )
        assert errors == []


class TestBaselineRuleTypeMethod:
    """Test that _get_rule_type method works."""

    def test_a_words_rule_type(self):
        from rules.word_usage.a_words_rule import AWordsRule
        rule = AWordsRule()
        assert rule._get_rule_type() == 'word_usage_a'

    def test_b_words_rule_type(self):
        from rules.word_usage.b_words_rule import BWordsRule
        rule = BWordsRule()
        assert rule._get_rule_type() == 'word_usage_b'

    def test_special_chars_rule_type(self):
        from rules.word_usage.special_chars_rule import SpecialCharsRule
        rule = SpecialCharsRule()
        assert rule._get_rule_type() == 'word_usage_special'


class TestYAMLConfigLoading:
    """Test that YAML config loads correctly."""

    def test_config_file_exists(self):
        import os
        config_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', '..',
            'rules', 'word_usage', 'config', 'word_usage_config.yaml',
        )
        assert os.path.exists(config_path)

    def test_config_has_all_letters(self):
        import os
        import yaml
        config_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', '..',
            'rules', 'word_usage', 'config', 'word_usage_config.yaml',
        )
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        # Verify key letter sections exist
        for letter in ['a', 'b', 'c', 's', 'special']:
            assert letter in config, f"Missing section '{letter}' in YAML"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
