"""
Word Usage Rule for words starting with 'R'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection combined with advanced morphological analysis.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class RWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'R'.
    Enhanced with spaCy PhraseMatcher for efficient detection combined with advanced morphological analysis.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_r'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with R-word patterns."""
        # Define word details for 'R' words (advanced morphological analysis handled separately)
        word_details = {
            "read-only": {"suggestion": "Write as 'read-only' (hyphenated).", "severity": "low"},
            "re-": {"suggestion": "Most words with the 're-' prefix are not hyphenated (e.g., 'reenter', 'reorder').", "severity": "low"},
            "Redbook": {"suggestion": "The correct term is 'IBM Redbooks publication'.", "severity": "high"},
            "refer to": {"suggestion": "For cross-references, prefer 'see'.", "severity": "low"},
            "respective": {"suggestion": "Avoid. Rewrite the sentence to be more direct.", "severity": "medium"},
            "roadmap": {"suggestion": "Write as 'roadmap' (one word).", "severity": "low"},
            "roll back": {"suggestion": "Use 'roll back' (verb) and 'rollback' (noun/adjective).", "severity": "low"},
            "run time": {"suggestion": "Use 'runtime' (one word) as an adjective, and 'run time' (two words) as a noun.", "severity": "low"},
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

        # PRESERVE EXISTING ADVANCED FUNCTIONALITY: Context-aware dependency parsing for 'real time' 
        # This sophisticated linguistic analysis checks for adjectival modification patterns
        for token in doc:
            # Linguistic Anchor: Check for 'real time' used as an adjective through dependency analysis
            if token.lemma_ == "real" and token.i + 1 < len(doc) and doc[token.i + 1].lemma_ == "time":
                if doc[token.i + 1].dep_ == "amod" or token.dep_ == "amod":
                    sent = token.sent
                    next_token = doc[token.i + 1]
                    
                    # Get sentence index
                    sentence_index = 0
                    for i, s in enumerate(doc.sents):
                        if s == sent:
                            sentence_index = i
                            break
                    
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_index,
                        message="Incorrect adjective form: 'real time' should be 'real-time'.",
                        suggestions=["Use 'real-time' (hyphenated) as an adjective before a noun."],
                        severity='medium',
                        text=text,  # Enhanced: Pass full text for better confidence analysis
                        context=context,  # Enhanced: Pass context for domain-specific validation
                        span=(token.idx, next_token.idx + len(next_token.text)),
                        flagged_text=f"{token.text} {next_token.text}"
                    ))

        # NEW ENHANCED APPROACH: Use base class PhraseMatcher for simple word patterns
        word_usage_errors = self._find_word_usage_errors(doc, "Review usage of the term")
        errors.extend(word_usage_errors)
        
        return errors
