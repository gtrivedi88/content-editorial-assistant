"""
Word Usage Rule for words starting with 'C'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class CWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'C'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_c'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with C-word patterns."""
        # Define word details for 'C' words (extracted from original word map)
        word_details = {
            "cancelation": {"suggestion": "Use 'cancellation'.", "severity": "low"},
            "can not": {"suggestion": "Use 'cannot'.", "severity": "high"},
            "canned": {"suggestion": "Avoid jargon. Use 'predefined' or 'preconfigured'.", "severity": "medium"},
            "catalogue": {"suggestion": "Use 'catalog'.", "severity": "low"},
            "checkbox": {"suggestion": "Use 'check box'.", "severity": "low"},
            "check out": {"suggestion": "Use 'check out' (verb) and 'checkout' (noun/adjective).", "severity": "low"},
            "choose": {"suggestion": "For UI elements, use a more specific verb like 'select' or 'click'.", "severity": "medium"},
            "class path": {"suggestion": "Use 'classpath' only as a variable, otherwise 'class path'.", "severity": "low"},
            "clean up": {"suggestion": "Use 'clean up' (verb) and 'cleanup' (noun).", "severity": "low"},
            "client-server": {"suggestion": "Use 'client/server'.", "severity": "low"},
            "combo box": {"suggestion": "Do not use. In instructions, use the name of the field.", "severity": "medium"},
            "comprise": {"suggestion": "The whole comprises the parts. The parts compose the whole. Avoid 'is comprised of'.", "severity": "medium"},
            "congratulations": {"suggestion": "Avoid in technical information. State the accomplishment directly.", "severity": "medium"},
            "counterclockwise": {"suggestion": "Use 'counterclockwise', not 'anticlockwise'.", "severity": "low"},
            "crash": {"suggestion": "Use a more specific term like 'fail' or 'stop unexpectedly'.", "severity": "medium"},
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

        # PRESERVE EXISTING FUNCTIONALITY: Advanced phrasal verb detection
        # This sophisticated linguistic analysis is kept unchanged for maximum accuracy
        phrasal_verb_violations = self._detect_phrasal_verbs_with_unnecessary_prepositions(doc)
        
        # Process phrasal verb violations found by linguistic analysis
        for violation in phrasal_verb_violations:
            # Find which sentence this violation belongs to
            sentence_index = 0
            sentence_text = ""
            for i, sent in enumerate(doc.sents):
                if sent.start_char <= violation['start_char'] < sent.end_char:
                    sentence_index = i
                    sentence_text = sent.text
                    break
            
            # Only process violations that start with 'C' (since this is c_words_rule)
            if violation['verb_token'].text.lower().startswith('c'):
                errors.append(self._create_error(
                    sentence=sentence_text,
                    sentence_index=sentence_index,
                    message=f"Review usage of the phrase '{violation['phrase']}'.",
                    suggestions=[violation['suggestion']],
                    severity='high',
                    text=text,  # Enhanced: Pass full text for better confidence analysis
                    context=context,  # Enhanced: Pass context for domain-specific validation
                    span=(violation['start_char'], violation['end_char']),
                    flagged_text=violation['phrase']
                ))

        # NEW ENHANCED APPROACH: Use base class PhraseMatcher for single word detection
        word_usage_errors = self._find_word_usage_errors(doc, "Review usage of the term")
        errors.extend(word_usage_errors)
                    
        return errors
