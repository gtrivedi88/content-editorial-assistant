"""
Word Usage Rule for words starting with 'W'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re
try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class WWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'W'.
    The check for the pronoun 'we' has been moved to the second_person_rule
    to avoid redundant error reporting.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_w'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
            
        doc = nlp(text)

        # Linguistic Anchor: Use dependency parsing for 'while' to check if it's used for contrast.
        for sent in doc.sents:
            for token in sent:
                if token.lemma_.lower() == "while" and token.dep_ == "mark":
                    # If the main clause contains a word of contrast, it's likely a style violation.
                    contrast_words = {"but", "however", "still", "yet"}
                    if any(t.lemma_ in contrast_words for t in token.head.children):
                        errors.append(self._create_error(
                            sentence=sent.text,
                            message="Use 'while' only to refer to time. For contrast, use 'although' or 'whereas'.",
                            suggestions=["Replace 'while' with 'although' when indicating contrast."],
                            severity='medium',
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))

        # General word map for other 'W' words
        word_map = {
            "w/": {"suggestion": "Spell out 'with'.", "severity": "medium"},
            "war room": {"suggestion": "Avoid military metaphors. Use 'command center' or 'operations center'.", "severity": "high"},
            "web site": {"suggestion": "Use 'website' (one word).", "severity": "low"},
            "whitelist": {"suggestion": "Use inclusive language. Use 'allowlist'.", "severity": "high"},
            "Wi-Fi": {"suggestion": "Use 'Wi-Fi' for the certified technology and 'wifi' for a generic wireless connection.", "severity": "low"},
            "work station": {"suggestion": "Use 'workstation' (one word).", "severity": "low"},
            "world-wide": {"suggestion": "Use 'worldwide' (one word).", "severity": "low"},
        }

        for i, sentence in enumerate(sentences):
            for word, details in word_map.items():
                for match in re.finditer(r'\\b' + re.escape(word) + r'\\b', sentence, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Review usage of the term '{word}'.",
                        suggestions=[details['suggestion']],
                        severity=details['severity'],
                        span=match.span(),
                        flagged_text=match.group(0)
                    ))
        return errors
