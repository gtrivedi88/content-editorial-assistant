"""Tests for false-positive guards on deterministic rules.

Validates that specific guard conditions in 10 rules correctly suppress
false positives for legitimate text patterns, while still detecting real
issues. Uses a real SpaCy ``en_core_web_md`` model for rules that require
dependency parsing or POS tagging.

Guards tested:
  Phase 1: VerbsRule, ClaimsRule, ToneRule, AccessibilityRule
  Phase 2: RepeatedWordsRule, NumeralsVsWordsRule
  Phase 3: OxfordCommaRule, CommasRule, UsingRule, ConversationalStyleRule
"""

import logging
from typing import Any, Dict, List

import pytest
import spacy

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Module-scoped SpaCy fixture — loaded once, reused across all tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def nlp() -> spacy.language.Language:
    """Load the en_core_web_md SpaCy model for rules that need NLP.

    Returns:
        A loaded SpaCy Language pipeline.
    """
    return spacy.load("en_core_web_md")


# ===================================================================
# Phase 1 — VerbsRule, ClaimsRule, ToneRule, AccessibilityRule
# ===================================================================


class TestVerbsRuleFPGuards:
    """False-positive guards for the VerbsRule passive-voice detector."""

    def test_state_of_being_deploy_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'is deployed' should not be flagged — 'deploy' is a state-of-being lemma."""
        from rules.language_and_grammar.verbs_rule import VerbsRule

        rule = VerbsRule()
        text = "The application is deployed on the cluster."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        passive_issues = [e for e in result if "passive" in e.get("message", "").lower()]
        assert passive_issues == [], (
            f"'is deployed' is a state-of-being pattern and should not be flagged: {passive_issues}"
        )

    def test_state_of_being_configure_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'is configured' should not be flagged — 'configure' is a state-of-being lemma."""
        from rules.language_and_grammar.verbs_rule import VerbsRule

        rule = VerbsRule()
        text = "The service is configured to use TLS."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        passive_issues = [e for e in result if "passive" in e.get("message", "").lower()]
        assert passive_issues == [], (
            f"'is configured' is a state-of-being pattern and should not be flagged: {passive_issues}"
        )

    def test_state_of_being_store_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'is stored' should not be flagged — 'store' is a state-of-being lemma."""
        from rules.language_and_grammar.verbs_rule import VerbsRule

        rule = VerbsRule()
        text = "The data is stored in the database."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        passive_issues = [e for e in result if "passive" in e.get("message", "").lower()]
        assert passive_issues == [], (
            f"'is stored' is a state-of-being pattern and should not be flagged: {passive_issues}"
        )

    def test_real_passive_still_flagged(self, nlp: spacy.language.Language) -> None:
        """'was deleted by the admin' should still be flagged — 'delete' is not excepted."""
        from rules.language_and_grammar.verbs_rule import VerbsRule

        rule = VerbsRule()
        text = "The file was deleted by the admin."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        passive_issues = [e for e in result if "passive" in e.get("message", "").lower()]
        assert len(passive_issues) >= 1, (
            "'was deleted by the admin' is real passive voice and should be flagged"
        )


class TestClaimsRuleFPGuards:
    """False-positive guards for the ClaimsRule unsubstantiated-claim detector."""

    def test_secure_shell_compound_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'Secure Shell' is a technical compound and should not trigger the 'secure' claim."""
        from rules.legal_information.claims_rule import ClaimsRule

        rule = ClaimsRule()
        text = "Connect to the server using Secure Shell."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        secure_issues = [
            e for e in result
            if "secure" in e.get("flagged_text", "").lower()
        ]
        assert secure_issues == [], (
            f"'Secure Shell' is a technical compound and should not be flagged: {secure_issues}"
        )

    def test_modal_qualifier_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'can improve performance' has a modal qualifier before any claim word."""
        from rules.legal_information.claims_rule import ClaimsRule

        rule = ClaimsRule()
        text = "Caching can improve performance."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        assert result == [], (
            f"Modal qualifier 'can' should suppress claim detection: {result}"
        )

    def test_attribution_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'according to the guide, the product is best' has an attribution marker."""
        from rules.legal_information.claims_rule import ClaimsRule

        rule = ClaimsRule()
        text = "According to the guide, the product is best in its category."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        best_issues = [
            e for e in result
            if "best" in e.get("flagged_text", "").lower()
        ]
        assert best_issues == [], (
            f"Attribution marker 'According to' should suppress claim detection: {best_issues}"
        )

    def test_unqualified_superlative_still_flagged(self, nlp: spacy.language.Language) -> None:
        """'Our product is always the best' has no modal, no attribution, no compound."""
        from rules.legal_information.claims_rule import ClaimsRule

        rule = ClaimsRule()
        text = "Our product is always the best."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        assert len(result) >= 1, (
            "'Our product is always the best' contains unqualified claims "
            "and should be flagged"
        )


class TestToneRuleFPGuards:
    """False-positive guards for the ToneRule jargon/buzzword detector."""

    def test_quoted_leverage_not_flagged(self, nlp: spacy.language.Language) -> None:
        """Text inside quotes like 'leverage' should not be flagged."""
        from rules.audience_and_medium.tone_rule import ToneRule

        rule = ToneRule()
        text = "Use the term 'leverage' carefully in technical writing."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        leverage_issues = [
            e for e in result
            if "leverage" in e.get("flagged_text", "").lower()
        ]
        assert leverage_issues == [], (
            f"'leverage' inside quotes should not be flagged: {leverage_issues}"
        )

    def test_unquoted_leverage_still_flagged(self, nlp: spacy.language.Language) -> None:
        """Unquoted 'leverage' in prose should still be flagged as business jargon."""
        from rules.audience_and_medium.tone_rule import ToneRule

        rule = ToneRule()
        text = "You can leverage this feature to improve performance."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        leverage_issues = [
            e for e in result
            if "leverage" in e.get("flagged_text", "").lower()
        ]
        assert len(leverage_issues) >= 1, (
            "Unquoted 'leverage' is business jargon and should be flagged"
        )


class TestAccessibilityRuleFPGuards:
    """False-positive guards for the AccessibilityRule all-caps detector."""

    def test_rhel_acronym_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'RHEL' is a known acronym and should not be flagged as all-caps."""
        from rules.audience_and_medium.accessibility_rule import AccessibilityRule

        rule = AccessibilityRule()
        text = "Install RHEL on the target machine."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        caps_issues = [
            e for e in result
            if "RHEL" in e.get("flagged_text", "")
        ]
        assert caps_issues == [], (
            f"'RHEL' is a known acronym and should not be flagged: {caps_issues}"
        )

    def test_openshift_acronym_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'OPENSHIFT' is a known acronym and should not be flagged as all-caps."""
        from rules.audience_and_medium.accessibility_rule import AccessibilityRule

        rule = AccessibilityRule()
        text = "Deploy the application on OPENSHIFT."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        caps_issues = [
            e for e in result
            if "OPENSHIFT" in e.get("flagged_text", "")
        ]
        assert caps_issues == [], (
            f"'OPENSHIFT' is a known acronym and should not be flagged: {caps_issues}"
        )


# ===================================================================
# Phase 2 — RepeatedWordsRule, NumeralsVsWordsRule
# ===================================================================


class TestRepeatedWordsRuleFPGuards:
    """False-positive guards for the RepeatedWordsRule duplicate detector."""

    def test_step_by_step_not_flagged(self) -> None:
        """'step by step' is a compound repeat pattern and should not be flagged."""
        from rules.language_and_grammar.repeated_words_rule import RepeatedWordsRule

        rule = RepeatedWordsRule()
        text = "Follow the step by step instructions."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        step_issues = [
            e for e in result
            if "step" in e.get("flagged_text", "").lower()
        ]
        assert step_issues == [], (
            f"'step by step' is an idiomatic compound and should not be flagged: {step_issues}"
        )

    def test_end_to_end_not_flagged(self) -> None:
        """'end to end' is a compound repeat pattern and should not be flagged."""
        from rules.language_and_grammar.repeated_words_rule import RepeatedWordsRule

        rule = RepeatedWordsRule()
        text = "Run the end to end tests before deploying."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        end_issues = [
            e for e in result
            if "end" in e.get("flagged_text", "").lower()
        ]
        assert end_issues == [], (
            f"'end to end' is an idiomatic compound and should not be flagged: {end_issues}"
        )

    def test_actual_duplicate_still_flagged(self) -> None:
        """'document document' is a real repeated word and should be flagged."""
        from rules.language_and_grammar.repeated_words_rule import RepeatedWordsRule

        rule = RepeatedWordsRule()
        # Note: 'the' is in _ALLOWED_REPEATS so we use a word not in that set.
        text = "Review document document before submitting."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        assert len(result) >= 1, (
            "'document document' is a real repeated word and should be flagged"
        )


class TestNumeralsVsWordsRuleFPGuards:
    """False-positive guards for the NumeralsVsWordsRule sentence-start detector."""

    def test_measurement_at_start_not_flagged(self) -> None:
        """'2 GB of memory is required' should not be flagged — has measurement unit."""
        from rules.numbers_and_measurement.numerals_vs_words_rule import NumeralsVsWordsRule

        rule = NumeralsVsWordsRule()
        text = "2 GB of memory is required."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        assert result == [], (
            f"'2 GB' has a measurement unit and should not be flagged: {result}"
        )

    def test_version_like_number_not_flagged(self) -> None:
        """'3.14 is the value' should not be flagged — version-like decimal."""
        from rules.numbers_and_measurement.numerals_vs_words_rule import NumeralsVsWordsRule

        rule = NumeralsVsWordsRule()
        text = "3.14 is the value of pi."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        assert result == [], (
            f"'3.14' looks like a version number and should not be flagged: {result}"
        )

    def test_bare_numeral_at_start_still_flagged(self) -> None:
        """'5 servers are available' should be flagged — bare numeral at sentence start."""
        from rules.numbers_and_measurement.numerals_vs_words_rule import NumeralsVsWordsRule

        rule = NumeralsVsWordsRule()
        text = "5 servers are available in the cluster."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        assert len(result) >= 1, (
            "'5 servers' starts with a bare numeral and should be flagged"
        )


# ===================================================================
# Phase 3 — OxfordCommaRule, CommasRule, UsingRule,
#            ConversationalStyleRule
# ===================================================================


class TestOxfordCommaRuleFPGuards:
    """False-positive guards for the OxfordCommaRule serial-comma detector."""

    def test_heading_block_type_not_flagged(self) -> None:
        """Headings should not be checked for Oxford comma."""
        from rules.punctuation.oxford_comma_rule import OxfordCommaRule

        rule = OxfordCommaRule()
        text = "Installing, configuring and deploying the application."
        sentences = [text]
        context: Dict[str, Any] = {"block_type": "heading"}

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, context=context,
        )

        assert result == [], (
            f"Headings should not be checked for Oxford comma: {result}"
        )

    def test_paragraph_without_oxford_comma_still_flagged(self) -> None:
        """Lists in paragraphs missing the Oxford comma should still be flagged."""
        from rules.punctuation.oxford_comma_rule import OxfordCommaRule

        rule = OxfordCommaRule()
        text = "Install servers, databases and applications."
        sentences = [text]
        context: Dict[str, Any] = {"block_type": "paragraph"}

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, context=context,
        )

        assert len(result) >= 1, (
            "Missing Oxford comma in a paragraph should be flagged"
        )


class TestCommasRuleFPGuards:
    """False-positive guards for the CommasRule 'then' clause detector."""

    def test_if_then_conditional_not_flagged(self) -> None:
        """'If you configured... then restart' should not be flagged — if...then pattern."""
        from rules.punctuation.commas_rule import CommasRule

        rule = CommasRule()
        text = "If you configured the storage backend then restart the service."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        then_issues = [
            e for e in result
            if "then" in e.get("flagged_text", "").lower()
        ]
        assert then_issues == [], (
            f"'If...then' conditional pattern should not be flagged: {then_issues}"
        )

    def test_when_then_conditional_not_flagged(self) -> None:
        """'When the process completes then exit' should not be flagged — when...then."""
        from rules.punctuation.commas_rule import CommasRule

        rule = CommasRule()
        text = "When the process completes then exit the terminal."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        then_issues = [
            e for e in result
            if "then" in e.get("flagged_text", "").lower()
        ]
        assert then_issues == [], (
            f"'When...then' conditional pattern should not be flagged: {then_issues}"
        )

    def test_bare_then_clause_still_flagged(self) -> None:
        """'Start the server then run the tests' should be flagged — no if/when/after."""
        from rules.punctuation.commas_rule import CommasRule

        rule = CommasRule()
        text = "Start the server then run the tests."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        then_issues = [
            e for e in result
            if "then" in e.get("flagged_text", "").lower()
        ]
        assert len(then_issues) >= 1, (
            "'Start the server then run the tests' has bare 'then' and should be flagged"
        )


class TestUsingRuleFPGuards:
    """False-positive guards for the UsingRule 'noun using' detector."""

    def test_idiomatic_tool_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'Install the package using rpm' should not be flagged — 'rpm' is idiomatic."""
        from rules.language_and_grammar.using_rule import UsingRule

        rule = UsingRule()
        text = "Install the package using rpm."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        using_issues = [
            e for e in result
            if "using" in e.get("flagged_text", "").lower()
        ]
        assert using_issues == [], (
            f"'using rpm' is idiomatic tool usage and should not be flagged: {using_issues}"
        )

    def test_heading_block_type_not_flagged(self, nlp: spacy.language.Language) -> None:
        """Headings should not be checked for 'using' clarity."""
        from rules.language_and_grammar.using_rule import UsingRule

        rule = UsingRule()
        text = "Deploying applications using containers."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]
        context: Dict[str, Any] = {"block_type": "heading"}

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, context=context, spacy_doc=doc,
        )

        assert result == [], (
            f"Headings should not be checked for 'using' clarity: {result}"
        )


class TestConversationalStyleRuleFPGuards:
    """False-positive guards for the ConversationalStyleRule formality detector."""

    def test_reference_content_type_returns_empty(
        self, nlp: spacy.language.Language,
    ) -> None:
        """Reference content type uses formal language by design — should return []."""
        from rules.audience_and_medium.conversational_style_rule import ConversationalStyleRule

        rule = ConversationalStyleRule()
        text = "Utilize the API to obtain the desired output."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]
        context: Dict[str, Any] = {"content_type": "reference"}

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, context=context, spacy_doc=doc,
        )

        assert result == [], (
            f"Reference content type should suppress conversational style checks: {result}"
        )

    def test_non_reference_content_type_still_flagged(
        self, nlp: spacy.language.Language,
    ) -> None:
        """Non-reference content should still flag 'utilize' as overly formal."""
        from rules.audience_and_medium.conversational_style_rule import ConversationalStyleRule

        rule = ConversationalStyleRule()
        text = "Utilize the API to obtain the desired output."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]
        context: Dict[str, Any] = {"content_type": "concept"}

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, context=context, spacy_doc=doc,
        )

        # 'utilize' is mapped to 'use' in conversational_vocabularies.yaml,
        # so it should be flagged for non-reference content types.
        utilize_issues = [
            e for e in result
            if "utilize" in e.get("flagged_text", "").lower()
        ]
        assert len(utilize_issues) >= 1, (
            "'utilize' is overly formal for non-reference content and should be flagged"
        )


# ===================================================================
# Phase 10 — HighlightingRule bold+code detection
# ===================================================================


class TestHighlightingRuleBoldCode:
    """Check 3: bold wrapping inline code detection."""

    def test_bold_wrapping_code_flagged(self, nlp: spacy.language.Language) -> None:
        """Bold-wrapped inline code should be flagged."""
        from rules.structure_and_format.highlighting_rule import HighlightingRule

        rule = HighlightingRule()
        # In content coordinates, bold/italic markers are stripped.
        # The rule relies on bold_code_ranges from context.
        text = "Run curl to fetch the endpoint."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]
        context: Dict[str, Any] = {
            "block_type": "paragraph",
            "bold_code_ranges": [(4, 8, "bold", "curl")],
        }

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, context=context, spacy_doc=doc,
        )

        bold_issues = [
            e for e in result
            if "bold" in e.get("message", "").lower()
            and "inline code" in e.get("message", "").lower()
        ]
        assert len(bold_issues) == 1, (
            f"Bold-wrapped inline code should be flagged: {bold_issues}"
        )

    def test_plain_backtick_code_not_flagged(self, nlp: spacy.language.Language) -> None:
        """Plain backtick code (no bold/italic) should NOT be flagged by Check 3."""
        from rules.structure_and_format.highlighting_rule import HighlightingRule

        rule = HighlightingRule()
        text = "Run curl to fetch the endpoint."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]
        context: Dict[str, Any] = {
            "block_type": "paragraph",
            "bold_code_ranges": [],  # No bold wrapping
        }

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, context=context, spacy_doc=doc,
        )

        bold_issues = [
            e for e in result
            if "inline code" in e.get("message", "").lower()
        ]
        assert bold_issues == [], (
            f"Plain backtick code should not be flagged by Check 3: {bold_issues}"
        )

    def test_bold_non_code_not_flagged_by_check3(self, nlp: spacy.language.Language) -> None:
        """Bold around non-code text should NOT trigger Check 3."""
        from rules.structure_and_format.highlighting_rule import HighlightingRule

        rule = HighlightingRule()
        text = "This is important for security."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]
        context: Dict[str, Any] = {
            "block_type": "paragraph",
            "bold_code_ranges": [],  # No bold-wrapped code
        }

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, context=context, spacy_doc=doc,
        )

        bold_code_issues = [
            e for e in result
            if "inline code" in e.get("message", "").lower()
        ]
        assert bold_code_issues == [], (
            f"Bold around non-code should not trigger Check 3: {bold_code_issues}"
        )


# ===================================================================
# CEA Perfection Plan — Rule coverage tests
# ===================================================================


class TestAnthropomorphismCoverage:
    """Verify anthropomorphism rule catches verbs removed from safe_technical_verbs."""

    def test_system_passes_flagged(self, nlp: spacy.language.Language) -> None:
        """'The system passes the request' should be flagged as anthropomorphism."""
        from rules.language_and_grammar.anthropomorphism_rule import AnthropomorphismRule

        rule = AnthropomorphismRule()
        text = "The system passes the request to the backend."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        anthro_issues = [
            e for e in result
            if "anthropomorphism" in e.get("message", "").lower()
            or "cannot" in e.get("message", "").lower()
        ]
        assert len(anthro_issues) >= 1, (
            "'The system passes' is anthropomorphic and should be flagged"
        )

    def test_system_decides_flagged(self, nlp: spacy.language.Language) -> None:
        """'The system decides the routing path' should be flagged."""
        from rules.language_and_grammar.anthropomorphism_rule import AnthropomorphismRule

        rule = AnthropomorphismRule()
        text = "The system decides the routing path."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        assert len(result) >= 1, (
            "'The system decides' is anthropomorphic and should be flagged"
        )

    def test_safe_verb_provide_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'The system provides access' uses a safe technical verb — not flagged."""
        from rules.language_and_grammar.anthropomorphism_rule import AnthropomorphismRule

        rule = AnthropomorphismRule()
        text = "The system provides access to the dashboard."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        assert result == [], (
            f"'provides' is a safe technical verb and should not be flagged: {result}"
        )


class TestPassiveVoiceCoverage:
    """Verify passive voice rule catches verbs removed from _STATE_OF_BEING_LEMMAS."""

    def test_are_listed_flagged_in_procedure(self, nlp: spacy.language.Language) -> None:
        """'are listed' should be flagged in procedure content type."""
        from rules.language_and_grammar.verbs_rule import VerbsRule

        rule = VerbsRule()
        text = "The options are listed in the table below."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]
        context: Dict[str, Any] = {"content_type": "procedure"}

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, context=context, spacy_doc=doc,
        )

        passive_issues = [e for e in result if "passive" in e.get("message", "").lower()]
        assert len(passive_issues) >= 1, (
            "'are listed' should be flagged as passive voice in procedure context"
        )

    def test_are_listed_not_flagged_in_reference(self, nlp: spacy.language.Language) -> None:
        """'are listed' should NOT be flagged in reference content type."""
        from rules.language_and_grammar.verbs_rule import VerbsRule

        rule = VerbsRule()
        text = "The options are listed in the table below."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]
        context: Dict[str, Any] = {"content_type": "reference"}

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, context=context, spacy_doc=doc,
        )

        passive_issues = [e for e in result if "passive" in e.get("message", "").lower()]
        assert passive_issues == [], (
            f"'are listed' should be acceptable in reference context: {passive_issues}"
        )

    def test_is_installed_still_exempt(self, nlp: spacy.language.Language) -> None:
        """'is installed' should still be exempt — 'install' remains in _STATE_OF_BEING_LEMMAS."""
        from rules.language_and_grammar.verbs_rule import VerbsRule

        rule = VerbsRule()
        text = "Red Hat OpenShift is installed on the cluster."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        passive_issues = [e for e in result if "passive" in e.get("message", "").lower()]
        assert passive_issues == [], (
            f"'is installed' is a state-of-being pattern and should not be flagged: {passive_issues}"
        )


class TestSpatialReferenceCoverage:
    """Verify spatial reference rule catches positional references no longer exempted."""

    def test_see_above_flagged(self) -> None:
        """'see above' should now be flagged as a positional reference."""
        from rules.structure_and_format.self_referential_text_rule import SelfReferentialTextRule

        rule = SelfReferentialTextRule()
        text = "For more details, see above."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        above_issues = [
            e for e in result
            if "above" in e.get("flagged_text", "").lower()
        ]
        assert len(above_issues) >= 1, (
            "'see above' is a positional reference and should be flagged"
        )

    def test_described_above_flagged(self) -> None:
        """'described above' should now be flagged as a positional reference."""
        from rules.structure_and_format.self_referential_text_rule import SelfReferentialTextRule

        rule = SelfReferentialTextRule()
        text = "See the configuration described above."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        above_issues = [
            e for e in result
            if "above" in e.get("flagged_text", "").lower()
        ]
        assert len(above_issues) >= 1, (
            "'described above' is a positional reference and should be flagged"
        )

    def test_degrees_above_zero_not_flagged(self) -> None:
        """'20 degrees above zero' should NOT be flagged — non-positional context."""
        from rules.structure_and_format.self_referential_text_rule import SelfReferentialTextRule

        rule = SelfReferentialTextRule()
        text = "The temperature rose to 20 degrees above zero."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        above_issues = [
            e for e in result
            if "above" in e.get("flagged_text", "").lower()
        ]
        assert above_issues == [], (
            f"'degrees above zero' is non-positional and should not be flagged: {above_issues}"
        )

    def test_see_below_flagged(self) -> None:
        """'see below' should now be flagged as a positional reference."""
        from rules.structure_and_format.self_referential_text_rule import SelfReferentialTextRule

        rule = SelfReferentialTextRule()
        text = "See the instructions below."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        below_issues = [
            e for e in result
            if "below" in e.get("flagged_text", "").lower()
        ]
        assert len(below_issues) >= 1, (
            "'see below' is a positional reference and should be flagged"
        )


# ===================================================================
# DoNotUseTermsRule — suggestion coverage (Fix 1)
# ===================================================================


class TestDoNotUseTermsSuggestions:
    """Verify do_not_use_terms_rule generates suggestions for all terms."""

    def test_kerberize_has_change_suggestions(self, nlp: spacy.language.Language) -> None:
        """'kerberize' should produce Change-style suggestions with alternatives."""
        from rules.word_usage.do_not_use_terms_rule import DoNotUseTermsRule

        rule = DoNotUseTermsRule()
        text = "You must kerberize the application."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        assert len(result) >= 1, "'kerberize' should be flagged"
        suggestions = result[0].get("suggestions", [])
        assert len(suggestions) >= 1, "'kerberize' should have suggestions"
        assert any("Kerberos-aware" in s for s in suggestions), (
            f"Suggestions should include 'Kerberos-aware': {suggestions}"
        )

    def test_please_has_instruction_suggestion(self, nlp: spacy.language.Language) -> None:
        """'please' has no alternatives and should get an instruction-style suggestion."""
        from rules.word_usage.do_not_use_terms_rule import DoNotUseTermsRule

        rule = DoNotUseTermsRule()
        text = "Please restart the service."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        assert len(result) >= 1, "'please' should be flagged"
        suggestions = result[0].get("suggestions", [])
        assert len(suggestions) >= 1, "'please' should have at least one suggestion"
        assert suggestions[0].startswith("Rewrite"), (
            f"'please' should get instruction-style suggestion: {suggestions}"
        )

    def test_resides_case_matching(self, nlp: spacy.language.Language) -> None:
        """'Resides' at sentence start should produce case-matched suggestions."""
        from rules.word_usage.do_not_use_terms_rule import DoNotUseTermsRule

        rule = DoNotUseTermsRule()
        text = "Resides in the default namespace."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        assert len(result) >= 1, "'Resides' should be flagged"
        suggestions = result[0].get("suggestions", [])
        # The replacement 'is in' should be case-matched to 'Is in'
        assert any("Is in" in s for s in suggestions), (
            f"Case matching should capitalize 'is in' to 'Is in': {suggestions}"
        )

    def test_quiescent_has_alternatives(self, nlp: spacy.language.Language) -> None:
        """'quiescent' should produce suggestions with alternatives."""
        from rules.word_usage.do_not_use_terms_rule import DoNotUseTermsRule

        rule = DoNotUseTermsRule()
        text = "The system is quiescent."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        assert len(result) >= 1, "'quiescent' should be flagged"
        suggestions = result[0].get("suggestions", [])
        assert len(suggestions) == 2, (
            f"'quiescent' should have 2 alternatives (inactive, safe): {suggestions}"
        )
        assert any("inactive" in s for s in suggestions)
        assert any("safe" in s for s in suggestions)


# ===================================================================
# Phase 12 — AsciiDoc markup cleanup (preprocessor FP guards)
# ===================================================================


class TestAsciidocMarkupCleanup:
    """Verify preprocessor strips AsciiDoc directives that cause false positives."""

    def test_attribute_unset_stripped(self) -> None:
        """':!ibi:' attribute unset should be stripped — no exclamation FP."""
        from app.services.analysis.preprocessor import _clean_markup
        cleaned = _clean_markup("Some text.\n:!ibi:\nMore text.")
        assert "!" not in cleaned

    def test_single_line_comment_stripped(self) -> None:
        """'// comment' should be stripped — no slashes FP."""
        from app.services.analysis.preprocessor import _clean_markup
        cleaned = _clean_markup(
            "Some text.\n// * edge_computing/upgrade/cnf.adoc\nMore text."
        )
        assert "edge_computing" not in cleaned

    def test_indented_comment_stripped(self) -> None:
        """'  // comment' with leading whitespace should also be stripped."""
        from app.services.analysis.preprocessor import _clean_markup
        cleaned = _clean_markup("Some text.\n  // indented comment\nMore text.")
        assert "indented comment" not in cleaned

    def test_ifdef_stripped(self) -> None:
        """'ifdef::ibu[]' should be stripped — no spacing FP."""
        from app.services.analysis.preprocessor import _clean_markup
        cleaned = _clean_markup("Some text.\nifdef::ibu[]\nMore text.")
        assert "ifdef" not in cleaned

    def test_endif_stripped(self) -> None:
        """'endif::[]' should be stripped."""
        from app.services.analysis.preprocessor import _clean_markup
        cleaned = _clean_markup("Some text.\nendif::[]\nMore text.")
        assert "endif" not in cleaned

    def test_ifeval_stripped(self) -> None:
        """'ifeval::' should be stripped."""
        from app.services.analysis.preprocessor import _clean_markup
        cleaned = _clean_markup(
            'Some text.\nifeval::["{context}" == "value"]\nMore text.'
        )
        assert "ifeval" not in cleaned

    def test_content_inside_ifdef_preserved(self) -> None:
        """Content between ifdef/endif should NOT be stripped."""
        from app.services.analysis.preprocessor import _clean_markup
        cleaned = _clean_markup(
            "ifdef::ibu[]\nThis is real prose.\nendif::[]"
        )
        assert "This is real prose." in cleaned

    def test_block_comment_still_stripped(self) -> None:
        """Block comments (////) should still be stripped (regression)."""
        from app.services.analysis.preprocessor import _clean_markup
        cleaned = _clean_markup("Text.\n////\nBlock comment\n////\nMore.")
        assert "Block comment" not in cleaned

    def test_angle_bracket_variable_replaced(self) -> None:
        """'<root_disk>' should be replaced with 'placeholder'."""
        from app.services.analysis.preprocessor import _clean_markup
        cleaned = _clean_markup("Specify the <root_disk> value.")
        assert "<root_disk>" not in cleaned
        assert "placeholder" in cleaned


# ===================================================================
# Phase 13 — Punctuation URL guard
# ===================================================================


class TestPunctuationUrlGuard:
    """Verify punctuation rule skips symbols inside URLs."""

    def test_hash_in_url_not_flagged(self) -> None:
        """'#' in a URL fragment should not be flagged."""
        from rules.punctuation.punctuation_and_symbols_rule import (
            PunctuationAndSymbolsRule,
        )

        rule = PunctuationAndSymbolsRule()
        text = "See https://example.com/docs#section for details."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        hash_issues = [e for e in result if e.get("flagged_text") == "#"]
        assert hash_issues == [], (
            f"'#' inside a URL should not be flagged: {hash_issues}"
        )

    def test_standalone_hash_still_flagged(self) -> None:
        """'#' used as a symbol in prose should still be flagged."""
        from rules.punctuation.punctuation_and_symbols_rule import (
            PunctuationAndSymbolsRule,
        )

        rule = PunctuationAndSymbolsRule()
        text = "Enter the # symbol to start."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        hash_issues = [e for e in result if e.get("flagged_text") == "#"]
        assert len(hash_issues) >= 1, (
            "Standalone '#' in prose should be flagged"
        )


# ===================================================================
# Phase 14 — Lists rule inline code guard
# ===================================================================


class TestListsInlineCodeGuard:
    """Verify lists rule skips capitalization on backtick-wrapped items."""

    def test_backtick_wrapped_placeholder_not_flagged(self) -> None:
        """Lowercase first letter inside inline code should not be flagged.

        Simulates per-block analysis where parser strips backticks from
        content but provides inline_code_ranges via context.
        """
        from rules.structure_and_format.lists_rule import ListsRule

        rule = ListsRule()
        # After parser stripping: backticks removed, content is plain text
        text = "root_disk value"
        sentences = [text]
        context: Dict[str, Any] = {
            "block_type": "list_item_unordered",
            # Range covers "root_disk" (positions 0-8) in content coords
            "inline_code_ranges": [(0, 9)],
        }

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, context=context,
        )

        cap_issues = [
            e for e in result
            if "Capitalize" in e.get("message", "")
        ]
        assert cap_issues == [], (
            f"Backtick-wrapped content should not be flagged: {cap_issues}"
        )

    def test_regular_lowercase_still_flagged(self) -> None:
        """Lowercase first word without code context should be flagged.

        Uses a 2-char word to avoid the command-token guard (>2 chars).
        """
        from rules.structure_and_format.lists_rule import ListsRule

        rule = ListsRule()
        # "an" is 2 chars — won't match _COMMAND_TOKEN_RE (requires >2)
        text = "an important step"
        sentences = [text]
        context: Dict[str, Any] = {
            "block_type": "list_item_unordered",
            "inline_code_ranges": [],
        }

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, context=context,
        )

        cap_issues = [
            e for e in result
            if "Capitalize" in e.get("message", "")
        ]
        assert len(cap_issues) >= 1, (
            "Regular lowercase list item should be flagged"
        )


# ===================================================================
# ConjunctionsRule — while temporal vs contrastive detection
# ===================================================================


class TestConjunctionsWhileFPGuards:
    """False-positive guards for the ConjunctionsRule while-check.

    The rule must only flag 'while' when positive contrastive evidence
    exists.  Temporal and ambiguous uses must NOT be flagged — ambiguous
    cases are deferred to the LLM granular pass.
    """

    # ---- Temporal uses — must NOT be flagged ----------------------------

    def test_while_with_create_not_flagged(
        self, nlp: spacy.language.Language,
    ) -> None:
        """'while you create the bridge' is temporal (concurrent action)."""
        from rules.language_and_grammar.conjunctions_rule import (
            ConjunctionsRule,
        )

        rule = ConjunctionsRule()
        text = (
            "You can either create these devices while you create the "
            "bridge or you can create them in advance."
        )
        doc = nlp(text)
        errors: List[Dict[str, Any]] = rule.analyze(
            text, [text], nlp=nlp, spacy_doc=doc,
        )
        while_errors = [
            e for e in errors if "although" in e.get("message", "").lower()
        ]
        assert len(while_errors) == 0, (
            "Temporal 'while' in 'either…while…or' must not be flagged"
        )

    def test_while_progressive_aspect_not_flagged(
        self, nlp: spacy.language.Language,
    ) -> None:
        """Progressive-aspect verb in the while-clause is temporal."""
        from rules.language_and_grammar.conjunctions_rule import (
            ConjunctionsRule,
        )

        rule = ConjunctionsRule()
        text = "You can review logs while the system is rebooting."
        doc = nlp(text)
        errors: List[Dict[str, Any]] = rule.analyze(
            text, [text], nlp=nlp, spacy_doc=doc,
        )
        while_errors = [
            e for e in errors if "although" in e.get("message", "").lower()
        ]
        assert len(while_errors) == 0, (
            "Progressive 'while…is rebooting' must not be flagged"
        )

    def test_while_either_or_not_flagged(
        self, nlp: spacy.language.Language,
    ) -> None:
        """'either…while' structure implies choice-of-timing, not contrast."""
        from rules.language_and_grammar.conjunctions_rule import (
            ConjunctionsRule,
        )

        rule = ConjunctionsRule()
        text = (
            "You can either configure the network while you set up "
            "the host or do it afterward."
        )
        doc = nlp(text)
        errors: List[Dict[str, Any]] = rule.analyze(
            text, [text], nlp=nlp, spacy_doc=doc,
        )
        while_errors = [
            e for e in errors if "although" in e.get("message", "").lower()
        ]
        assert len(while_errors) == 0, (
            "'either…while' temporal pattern must not be flagged"
        )

    def test_while_action_verb_ambiguous_not_flagged(
        self, nlp: spacy.language.Language,
    ) -> None:
        """Ambiguous 'while' with action verb — deferred to LLM."""
        from rules.language_and_grammar.conjunctions_rule import (
            ConjunctionsRule,
        )

        rule = ConjunctionsRule()
        text = (
            "While the API supports JSON, the system also accepts XML."
        )
        doc = nlp(text)
        errors: List[Dict[str, Any]] = rule.analyze(
            text, [text], nlp=nlp, spacy_doc=doc,
        )
        while_errors = [
            e for e in errors if "although" in e.get("message", "").lower()
        ]
        assert len(while_errors) == 0, (
            "Ambiguous 'while' with action verb must not be flagged — "
            "LLM handles these"
        )

    # ---- Contrastive uses — MUST be flagged -----------------------------

    def test_while_linking_verb_flagged(
        self, nlp: spacy.language.Language,
    ) -> None:
        """'While X is simple, Y has drawbacks' — copular head → contrastive."""
        from rules.language_and_grammar.conjunctions_rule import (
            ConjunctionsRule,
        )

        rule = ConjunctionsRule()
        text = (
            "While this approach is simpler, it has significant drawbacks."
        )
        doc = nlp(text)
        errors: List[Dict[str, Any]] = rule.analyze(
            text, [text], nlp=nlp, spacy_doc=doc,
        )
        while_errors = [
            e for e in errors if "although" in e.get("message", "").lower()
        ]
        assert len(while_errors) >= 1, (
            "Contrastive 'while' with linking verb must be flagged"
        )

    def test_while_comparative_adjective_flagged(
        self, nlp: spacy.language.Language,
    ) -> None:
        """Comparative adjective in while-clause signals contrast."""
        from rules.language_and_grammar.conjunctions_rule import (
            ConjunctionsRule,
        )

        rule = ConjunctionsRule()
        text = (
            "While containers are more portable, VMs provide better isolation."
        )
        doc = nlp(text)
        errors: List[Dict[str, Any]] = rule.analyze(
            text, [text], nlp=nlp, spacy_doc=doc,
        )
        while_errors = [
            e for e in errors if "although" in e.get("message", "").lower()
        ]
        assert len(while_errors) >= 1, (
            "Contrastive 'while' with comparative must be flagged"
        )

    def test_while_contrastive_adverb_flagged(
        self, nlp: spacy.language.Language,
    ) -> None:
        """Contrastive adverb ('however', 'instead') in main clause."""
        from rules.language_and_grammar.conjunctions_rule import (
            ConjunctionsRule,
        )

        rule = ConjunctionsRule()
        text = (
            "While the feature works, it is nevertheless too slow."
        )
        doc = nlp(text)
        errors: List[Dict[str, Any]] = rule.analyze(
            text, [text], nlp=nlp, spacy_doc=doc,
        )
        while_errors = [
            e for e in errors if "although" in e.get("message", "").lower()
        ]
        assert len(while_errors) >= 1, (
            "Contrastive 'while' with 'nevertheless' in main clause "
            "must be flagged"
        )

    def test_while_seems_flagged(
        self, nlp: spacy.language.Language,
    ) -> None:
        """'While X seems Y' — linking verb 'seems' → contrastive."""
        from rules.language_and_grammar.conjunctions_rule import (
            ConjunctionsRule,
        )

        rule = ConjunctionsRule()
        text = (
            "While this method seems adequate, it fails under load."
        )
        doc = nlp(text)
        errors: List[Dict[str, Any]] = rule.analyze(
            text, [text], nlp=nlp, spacy_doc=doc,
        )
        while_errors = [
            e for e in errors if "although" in e.get("message", "").lower()
        ]
        assert len(while_errors) >= 1, (
            "Contrastive 'while' with 'seems' must be flagged"
        )

    # ---- Suggestion quality ---------------------------------------------

    def test_while_suggestion_is_direct_replacement(
        self, nlp: spacy.language.Language,
    ) -> None:
        """Suggestion must be 'although', not an instruction string."""
        from rules.language_and_grammar.conjunctions_rule import (
            ConjunctionsRule,
        )

        rule = ConjunctionsRule()
        text = (
            "While this approach is simpler, it has significant drawbacks."
        )
        doc = nlp(text)
        errors: List[Dict[str, Any]] = rule.analyze(
            text, [text], nlp=nlp, spacy_doc=doc,
        )
        while_errors = [
            e for e in errors if "although" in e.get("message", "").lower()
        ]
        assert len(while_errors) >= 1
        suggestions = while_errors[0].get("suggestions", [])
        assert "although" in suggestions, (
            "Suggestion must be a direct replacement, not an instruction"
        )
