"""
Word Usage Rule for words starting with 'Q'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection combined with advanced POS analysis.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class QWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'Q'.
    Enhanced with spaCy PhraseMatcher for efficient detection combined with advanced POS analysis.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_q'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with Q-word patterns."""
        # Define word details for 'Q' words (advanced POS analysis handled separately)
        word_details = {
            "Q&A": {"suggestion": "Write as 'Q&A' to mean 'question and answer'.", "severity": "low"},
            "quantum safe": {"suggestion": "Use 'quantum-safe' (hyphenated) as an adjective before a noun.", "severity": "low"},
            "quiesce": {"suggestion": "This is a valid technical term, but ensure it is used correctly (can be transitive or intransitive).", "severity": "low"},
        }
        
        # Use base class method to setup patterns
        self._setup_word_patterns(nlp, word_details)

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)
        
        # Ensure patterns are initialized
        self._ensure_patterns_ready(nlp)

        # PRESERVE EXISTING ADVANCED FUNCTIONALITY: Context-aware POS analysis for 'quote' as noun
        # This sophisticated linguistic analysis distinguishes "quote" as noun vs verb through grammar
        for token in doc:
            if token.lemma_.lower() == "quote" and token.pos_ == "NOUN":
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
                    message="Do not use 'quote' as a noun.",
                    suggestions=["Use 'quotation'. 'Quote' is a verb."],
                    severity='medium',
                    span=(token.idx, token.idx + len(token.text)),
                    flagged_text=token.text
                ))

        # NEW ENHANCED APPROACH: Use base class PhraseMatcher for simple word patterns
        word_usage_errors = self._find_word_usage_errors(doc, "Review usage of the term")
        errors.extend(word_usage_errors)
        
        return errors
