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
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_w'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        # Context-aware check for 'while'
        for token in doc:
            if token.lemma_.lower() == "while" and token.dep_ == "mark":
                sent = token.sent
                # Get the sentence index by finding the sentence in the doc.sents
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                # Heuristic: if the clause is not clearly about time, flag for review.
                is_time_related = any(t.pos_ == "VERB" and "ing" in t.morph for t in token.head.children)
                if not is_time_related:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_index,
                        message="Use 'while' only to refer to time. For contrast, use 'although' or 'whereas'.",
                        suggestions=["Replace 'while' with 'although' when indicating contrast."],
                        severity='medium',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))

        # General word map
        word_map = {
            "w/": {"suggestion": "Spell out 'with'.", "severity": "medium"},
            "war room": {"suggestion": "Avoid military metaphors. Use 'command center' or 'operations center'.", "severity": "high"},
            "we": {"suggestion": "Avoid first-person pronouns in technical content. This is handled by second_person_rule.", "severity": "medium"},
            "web site": {"suggestion": "Use 'website' (one word).", "severity": "low"},
            "whitelist": {"suggestion": "Use inclusive language. Use 'allowlist'.", "severity": "high"},
            "Wi-Fi": {"suggestion": "Use 'Wi-Fi' for the certified technology and 'wifi' for a generic wireless connection.", "severity": "low"},
            "work station": {"suggestion": "Use 'workstation' (one word).", "severity": "low"},
            "world-wide": {"suggestion": "Use 'worldwide' (one word).", "severity": "low"},
        }

        for i, sent in enumerate(doc.sents):
            for word, details in word_map.items():
                # The 'we' rule is handled by second_person_rule, so we skip it here to avoid duplicates.
                if word == "we":
                    continue
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
