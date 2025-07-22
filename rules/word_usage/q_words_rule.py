"""
Word Usage Rule for words starting with 'Q'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class QWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'Q'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_q'

    def analyze(self, text: str, sentences: List[str], spacy_doc=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not spacy_doc:
            return errors
        doc = spacy_doc

        # Context-aware check for 'quote' as a noun
        for token in doc:
            if token.lemma_.lower() == "quote" and token.pos_ == "NOUN":
                sent = token.sent
                errors.append(self._create_error(
                    sentence=sent.text,
                    message="Do not use 'quote' as a noun.",
                    suggestions=["Use 'quotation'. 'Quote' is a verb."],
                    severity='medium',
                    span=(token.idx, token.idx + len(token.text)),
                    flagged_text=token.text
                ))

        # General word map
        word_map = {
            "Q&A": {"suggestion": "Write as 'Q&A' to mean 'question and answer'.", "severity": "low"},
            "quantum safe": {"suggestion": "Use 'quantum-safe' (hyphenated) as an adjective before a noun.", "severity": "low"},
            "quiesce": {"suggestion": "This is a valid technical term, but ensure it is used correctly (can be transitive or intransitive).", "severity": "low"},
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
