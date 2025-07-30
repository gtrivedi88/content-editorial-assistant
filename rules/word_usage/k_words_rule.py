"""
Word Usage Rule for 'key'
Enhanced with spaCy POS analysis for context-aware detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class KWordsRule(BaseWordUsageRule):
    """
    Checks for potentially incorrect usage of the word 'key'.
    Enhanced with spaCy POS analysis for context-aware detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_k'
    
    def _setup_patterns(self, nlp):
        """This rule uses advanced POS analysis instead of simple pattern matching."""
        # No PhraseMatcher patterns needed - we use sophisticated grammatical analysis
        pass

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        
        # Process full document for better spaCy analysis
        doc = nlp(text)

        # PRESERVE EXISTING ADVANCED FUNCTIONALITY: Use Part-of-Speech (POS) tagging for context-aware detection
        # This sophisticated linguistic analysis distinguishes "key in your password" (verb) from 
        # "key feature" (adjective/noun), eliminating false positives through grammar awareness
        for token in doc:
            if token.lemma_.lower() == 'key' and token.pos_ == 'VERB':
                sent = token.sent
                
                # Get sentence index
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=sentence_index,
                    message="Review usage of the term 'key'.",
                    suggestions=["Do not use 'key' as a verb. Use 'type' or 'press'."],
                    severity='medium',
                    span=(token.idx, token.idx + len(token.text)),
                    flagged_text=token.text
                ))
        
        return errors
