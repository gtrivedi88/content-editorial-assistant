"""
Word Usage Rule for words starting with 'C'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class CWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'C'.
    Uses linguistic anchors for automatic detection without hard-coded phrases.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_c'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
            
        doc = nlp(text)

        # LINGUISTIC ANCHOR APPROACH: Automatically detect phrasal verb issues
        phrasal_verb_violations = self._detect_phrasal_verbs_with_unnecessary_prepositions(doc)
        
        # Convert sentences to list for indexing
        sentences_list = list(doc.sents)
        
        # Process phrasal verb violations found by linguistic analysis
        for violation in phrasal_verb_violations:
            # Find which sentence this violation belongs to
            sentence_index = 0
            sentence_text = ""
            for i, sent in enumerate(sentences_list):
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
                    span=(violation['start_char'], violation['end_char']),
                    flagged_text=violation['phrase']
                ))

        # Single word map for exact matching (keep existing functionality)
        single_word_map = {
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

        # Handle single words with regex (existing logic)
        for i, sent in enumerate(sentences_list):
            for word, details in single_word_map.items():
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
