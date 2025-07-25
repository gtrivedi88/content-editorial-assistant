"""
Word Usage Rule for words starting with 'L'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class LWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'L'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_l'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        # ENTERPRISE CONTEXT INTELLIGENCE: Check if word usage rules should apply
        content_classification = self._get_content_classification(text, context, nlp)
        should_apply = self._should_apply_rule(self._get_rule_category(), content_classification)
        
        if not should_apply:
            return errors  # Skip for technical labels, navigation items, etc.

        # Special morphological check for compound word patterns that should be one word
        for i, sent in enumerate(doc.sents):
            # LINGUISTIC ANCHOR: Use SpaCy to detect "life cycle" (two words) that should be "lifecycle"
            for token in sent:
                if token.lemma_.lower() == "life" and token.i + 1 < len(doc):
                    next_token = doc[token.i + 1]
                    if next_token.lemma_.lower() == "cycle":
                        # Check if they form a compound that should be one word
                        if token.dep_ == "compound" or next_token.dep_ == "compound":
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message="Review usage of the term 'life cycle'.",
                                suggestions=["Write as 'lifecycle' (one word)."],
                                severity='low',
                                span=(token.idx, next_token.idx + len(next_token.text)),
                                flagged_text=f"{token.text} {next_token.text}"
                            ))

        word_map = {
            "land and expand": {"suggestion": "Avoid this term due to colonial connotations. Use 'expansion strategy'.", "severity": "high"},
            "last name": {"suggestion": "Use the globally recognized term 'surname'.", "severity": "medium"},
            "leverage": {"suggestion": "Avoid in technical content; it does not translate well. Use 'use'.", "severity": "medium"},
            "licence": {"suggestion": "Use the spelling 'license'.", "severity": "low"},
            # REMOVED: "lifecycle" entry - now handled by morphological analysis above
            "log on to": {"suggestion": "This is the correct form. Avoid 'log onto'.", "severity": "low"},
            "log off of": {"suggestion": "Use 'log off from'.", "severity": "medium"},
            "look and feel": {"suggestion": "Avoid this phrase. Be more specific about the UI characteristics.", "severity": "medium"},
            "lowercase": {"suggestion": "Write as 'lowercase' (one word).", "severity": "low"},
        }

        for i, sent in enumerate(doc.sents):
            for word, details in word_map.items():
                for match in re.finditer(r'\b' + re.escape(word) + r'\b', sent.text, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Review usage of the term '{match.group()}'.",
                        suggestions=[details['suggestion']],
                        severity=details['severity'],
                        span=(sent.start_char + match.start(), sent.start_char + match.end()),
                        flagged_text=match.group(0)
                    ))
        return errors
