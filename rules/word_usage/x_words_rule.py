"""
Word Usage Rule for words starting with 'X' (Production-Grade)
Evidence-based analysis with surgical zero false positive guards for X-word usage detection.
Based on IBM Style Guide recommendations with production-grade evidence calculation.
Preserves case-sensitive pattern detection for technical terms.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class XWordsRule(BaseWordUsageRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect usage of specific words starting with 'X'.
    
    Implements evidence-based analysis with:
    - Surgical zero false positive guards for X-word usage
    - Dynamic base evidence scoring based on word specificity and context
    - Context-aware adjustments for different writing domains
    - PRESERVED: Case-sensitive pattern detection for technical terms
    
    Features:
    - Near 100% false positive elimination through surgical guards
    - Word-specific evidence calculation for each X-word violation
    - Evidence-aware suggestions tailored to writing context
    - Case-sensitive technical term detection
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_x'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """Evidence-based analysis for X-word usage violations."""
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Case-sensitive patterns for technical terms
        x_word_patterns = {
            "XSA": {"alternatives": ["extended subarea addressing"], "category": "technical_abbreviation", "severity": "medium"},
            "xterm": {"alternatives": ["xterm"], "category": "capitalization", "severity": "low"},
        }

        for word, details in x_word_patterns.items():
            # Use case-sensitive matching for technical terms
            for match in re.finditer(r'\b' + re.escape(word) + r'\b', text):
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
                    
                    evidence_score = self._calculate_x_word_evidence(word, token, sent, text, context or {}, details["category"])
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message(word, evidence_score, details["category"]),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions(word, details["alternatives"], evidence_score, context or {}, details["category"]),
                            severity=details["severity"] if evidence_score < 0.7 else 'high',
                            text=text, context=context, evidence_score=evidence_score,
                            span=(char_start, char_end), flagged_text=matched_text
                        ))
        return errors

    def _calculate_x_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score for X-word usage violations."""
        evidence_score = self._get_base_x_word_evidence_score(word, category, sentence, context)
        if evidence_score == 0.0:
            return 0.0
        
        evidence_score = self._apply_linguistic_clues_x_words(evidence_score, word, token, sentence)
        evidence_score = self._apply_structural_clues_x_words(evidence_score, context)
        evidence_score = self._apply_semantic_clues_x_words(evidence_score, word, text, context)
        evidence_score = self._apply_feedback_clues_x_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_x_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Set dynamic base evidence score based on X-word category."""
        if category == 'technical_abbreviation':
            return 0.7  # "XSA" - clarity for broader audiences
        elif category == 'capitalization':
            return 0.5  # "xterm" - consistency
        return 0.6

    def _apply_linguistic_clues_x_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply X-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        if word_lower == 'xsa' and any(indicator in sent_text for indicator in ['documentation', 'user', 'customer']):
            ev += 0.15  # User-facing content needs clear terminology
        
        if word_lower == 'xterm' and any(indicator in sent_text for indicator in ['terminal', 'application', 'program']):
            ev += 0.1  # Application context needs consistent capitalization
        
        return ev

    def _apply_structural_clues_x_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for X-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_x_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for X-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'customer_facing' and word_lower == 'xsa':
            ev += 0.2  # Customer content needs clear, spelled-out terms
        elif content_type == 'technical' and word_lower in ['xsa', 'xterm']:
            ev += 0.1  # Technical docs benefit from consistency
        
        if audience == 'external' and word_lower == 'xsa':
            ev += 0.2  # External audiences need clear terminology
        elif audience == 'global' and word_lower == 'xsa':
            ev += 0.15  # Global audiences benefit from spelled-out terms
        
        return ev

    def _apply_feedback_clues_x_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for X-words."""
        patterns = {'often_flagged_terms': {'xsa'}, 'accepted_terms': {'xterm'}}
        word_lower = word.lower()
        
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        elif word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.1  # "xterm" is more widely accepted
        
        return ev