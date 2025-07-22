"""
Word Usage Rule for words starting with 'S'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class SWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'S'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_s'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)
        sents = list(doc.sents)

        # This rule was previously updated with advanced logic for 'setup', 'shutdown', etc.
        # That logic is preserved here.
        for i, sent in enumerate(sents):
            for token in sent:
                if token.lemma_.lower() == "setup" and token.pos_ == "VERB":
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i, # FIX: Added the missing sentence_index
                        message="Incorrect verb form: 'setup' should be 'set up'.",
                        suggestions=["Use 'set up' (two words) for the verb form."],
                        severity='high',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
                if token.lemma_.lower() == "shutdown" and token.pos_ == "VERB":
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i, # FIX: Added the missing sentence_index
                        message="Incorrect verb form: 'shutdown' should be 'shut down'.",
                        suggestions=["Use 'shut down' (two words) for the verb form."],
                        severity='medium',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))

        # General word map
        word_map = {
            "sanity check": {"suggestion": "Avoid this term. Use 'validation', 'check', or 'review'.", "severity": "high"},
            "screen shot": {"suggestion": "Use 'screenshot' (one word).", "severity": "low"},
            "second name": {"suggestion": "Use the globally recognized term 'surname'.", "severity": "medium"},
            "secure": {"suggestion": "Avoid making absolute claims. Use 'security-enhanced' or describe the specific feature.", "severity": "high"},
            "segregate": {"suggestion": "Use 'separate'.", "severity": "high"},
            "server-side": {"suggestion": "Write as 'serverside' (one word).", "severity": "low"},
            "shall": {"suggestion": "Avoid. Use 'must' for requirements or 'will' for future tense.", "severity": "medium"},
            "ship": {"suggestion": "Avoid. Use 'release' or 'make available'.", "severity": "medium"},
            "should": {"suggestion": "Avoid for mandatory actions. Use 'must' or the imperative.", "severity": "medium"},
            "slave": {"suggestion": "Use inclusive language. Use 'secondary', 'replica', 'agent', or 'worker'.", "severity": "high"},
            "stand-alone": {"suggestion": "Write as 'standalone' (one word).", "severity": "low"},
            "suite": {"suggestion": "Avoid for groups of unrelated products. Use 'family' or 'set'.", "severity": "medium"},
            "sunset": {"suggestion": "Avoid jargon. Use 'discontinue' or 'withdraw from service'.", "severity": "medium"},
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
