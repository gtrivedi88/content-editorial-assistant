"""
Inclusive Language Rule
Based on IBM Style Guide topic: "Inclusive language"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class InclusiveLanguageRule(BaseLanguageRule):
    """
    Checks for non-inclusive terms and suggests modern, neutral alternatives
    as specified by the IBM Style Guide.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'inclusive_language'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for specific non-inclusive terms.
        """
        errors = []
        
        # Linguistic Anchor: A dictionary of non-inclusive terms and their
        # preferred replacements. This dictionary is the single source of truth
        # for this rule, making it easy to update and scale.
        non_inclusive_terms = {
            "whitelist": "allowlist",
            "blacklist": "blocklist",
            "master": "primary, main, or controller",
            "slave": "secondary, replica, or agent",
            "man-hours": "person-hours or work-hours",
            "man hours": "person-hours or work-hours",
            "manned": "staffed, operated, or crewed",
            "sanity check": "coherence check, confirmation, or validation",
        }

        for i, sentence in enumerate(sentences):
            # We check the lowercase version of the sentence for a broader match.
            sentence_lower = sentence.lower()
            for term, replacement in non_inclusive_terms.items():
                # The use of spaces around the term ensures we match whole words only,
                # preventing false positives on words that might contain the term
                # (e.g., "mastery" would not be flagged).
                if f" {term} " in f" {sentence_lower} ":
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Consider replacing the non-inclusive term '{term}'.",
                        suggestions=[f"Use a more inclusive alternative, such as '{replacement}'."],
                        severity='medium'
                    ))
        return errors
