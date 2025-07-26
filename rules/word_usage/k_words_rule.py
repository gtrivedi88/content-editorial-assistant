"""
Word Usage Rule for 'key'
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

class KWordsRule(BaseWordUsageRule):
    """
    Checks for potentially incorrect usage of the word 'key'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_k'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        for i, sent_text in enumerate(sentences):
            doc = nlp(sent_text)
            for token in doc:
                # PRIORITY 1 FIX: Use Part-of-Speech (POS) tagging to be context-aware.
                # The rule now only flags 'key' if spaCy identifies it as a VERB.
                # This correctly distinguishes "key in your password" (verb) from
                # "key feature" (adjective/noun), eliminating the false positive.
                if token.lemma_.lower() == 'key' and token.pos_ == 'VERB':
                    errors.append(self._create_error(
                        sentence=sent_text,
                        sentence_index=i,
                        message="Review usage of the term 'key'.",
                        suggestions=["Do not use 'key' as a verb. Use 'type' or 'press'."],
                        severity='medium',
                        flagged_text=token.text
                    ))
        return errors
