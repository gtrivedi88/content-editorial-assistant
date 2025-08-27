"""
Word Usage Rule for words starting with 'Y' (Production-Grade)
Evidence-based analysis with surgical zero false positive guards for Y-word usage detection.
Based on IBM Style Guide recommendations with production-grade evidence calculation.
Currently no Y-word patterns implemented - placeholder for future expansion.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class YWordsRule(BaseWordUsageRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect usage of specific words starting with 'Y'.
    
    Implements evidence-based analysis with:
    - Surgical zero false positive guards for Y-word usage
    - Dynamic base evidence scoring based on word specificity and context
    - Context-aware adjustments for different writing domains
    
    Features:
    - Near 100% false positive elimination through surgical guards
    - Word-specific evidence calculation for each Y-word violation
    - Evidence-aware suggestions tailored to writing context
    - Currently no patterns implemented - ready for future expansion
    
    Note: Currently no specific Y-word usage rules are implemented.
    The previous "your" rule was removed as it incorrectly flagged
    general possessive pronouns, which are acceptable according to 
    the IBM Style Guide. Possessives on abbreviations and trademarks
    are handled by the possessives_rule.py instead.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_y'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """Evidence-based analysis for Y-word usage violations."""
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Currently no Y-word patterns defined
        y_word_patterns = {}

        # Evidence-based analysis framework ready for future Y-word patterns
        for word, details in y_word_patterns.items():
            for match in re.finditer(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE):
                char_start, char_end, matched_text = match.start(), match.end(), match.group(0)
                
                token, sent, sentence_index = None, None, 0
                for i, s in enumerate(doc.sents):
                    if s.start_char <= char_start < s.end_char:
                        sent, sentence_index = s, i
                        for t in s:
                            if t.idx <= char_start < t.idx + len(t.text):
                                token = t
                                break
                        break
                
                if sent and token:
                    if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                        continue
                    
                    evidence_score = self._calculate_y_word_evidence(word, token, sent, text, context or {}, details["category"])
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message(word, evidence_score, details["category"]),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions(word, details["alternatives"], evidence_score, context or {}, details["category"]),
                            severity=details["severity"] if evidence_score < 0.7 else 'high',
                            text=text, context=context, evidence_score=evidence_score,
                            span=(char_start, char_end), flagged_text=matched_text
                        ))
        
        # No Y-word patterns currently defined - return empty errors list
        return errors

    def _calculate_y_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score for Y-word usage violations."""
        evidence_score = self._get_base_y_word_evidence_score(word, category, sentence, context)
        if evidence_score == 0.0:
            return 0.0
        
        evidence_score = self._apply_linguistic_clues_y_words(evidence_score, word, token, sentence)
        evidence_score = self._apply_structural_clues_y_words(evidence_score, context)
        evidence_score = self._apply_semantic_clues_y_words(evidence_score, word, text, context)
        evidence_score = self._apply_feedback_clues_y_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_y_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Set dynamic base evidence score based on Y-word category."""
        # Framework ready for future Y-word categories
        return 0.6

    def _apply_linguistic_clues_y_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply Y-word-specific linguistic clues."""
        # Framework ready for future Y-word linguistic analysis
        return ev

    def _apply_structural_clues_y_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for Y-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_y_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for Y-words."""
        # Framework ready for future Y-word semantic analysis
        return ev

    def _apply_feedback_clues_y_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for Y-words."""
        # Framework ready for future Y-word feedback analysis
        return ev