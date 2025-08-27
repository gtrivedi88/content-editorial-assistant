"""
Word Usage Rule for words starting with 'V' (Production-Grade)
Evidence-based analysis with surgical zero false positive guards for V-word usage detection.
Based on IBM Style Guide recommendations with production-grade evidence calculation.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class VWordsRule(BaseWordUsageRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect usage of specific words starting with 'V'.
    
    Implements evidence-based analysis with:
    - Surgical zero false positive guards for V-word usage
    - Dynamic base evidence scoring based on word specificity and context
    - Context-aware adjustments for different writing domains
    
    Features:
    - Near 100% false positive elimination through surgical guards
    - Word-specific evidence calculation for each V-word violation
    - Evidence-aware suggestions tailored to writing context
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_v'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """Evidence-based analysis for V-word usage violations."""
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        v_word_patterns = {
            "vanilla": {"alternatives": ["basic", "standard", "not customized"], "category": "jargon", "severity": "medium"},
            "Velcro": {"alternatives": ["hook-and-loop fastener"], "category": "trademark", "severity": "high"},
            "verbatim": {"alternatives": ["verbatim (adjective/adverb only)"], "category": "part_of_speech", "severity": "low"},
            "versus": {"alternatives": ["versus"], "category": "abbreviation", "severity": "medium"},
            "via": {"alternatives": ["by using", "through"], "category": "context_specific", "severity": "low"},
            "vice versa": {"alternatives": ["vice versa"], "category": "format_consistency", "severity": "low"},
        }

        for word, details in v_word_patterns.items():
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
                    
                    evidence_score = self._calculate_v_word_evidence(word, token, sent, text, context or {}, details["category"])
                    
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

    def _calculate_v_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score for V-word usage violations."""
        evidence_score = self._get_base_v_word_evidence_score(word, category, sentence, context)
        if evidence_score == 0.0:
            return 0.0
        
        evidence_score = self._apply_linguistic_clues_v_words(evidence_score, word, token, sentence)
        evidence_score = self._apply_structural_clues_v_words(evidence_score, context)
        evidence_score = self._apply_semantic_clues_v_words(evidence_score, word, text, context)
        evidence_score = self._apply_feedback_clues_v_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_v_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Set dynamic base evidence score based on V-word category."""
        if category == 'trademark':
            return 0.9  # "Velcro" - legal compliance critical
        elif category in ['jargon', 'abbreviation']:
            return 0.75  # "vanilla", "versus" - professional clarity
        elif category in ['part_of_speech', 'context_specific', 'format_consistency']:
            return 0.5  # "verbatim", "via", "vice versa" - style consistency
        return 0.6

    def _apply_linguistic_clues_v_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply V-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        if word_lower == 'velcro' and any(indicator in sent_text for indicator in ['fastener', 'material', 'attach']):
            ev += 0.2  # Material context needs generic terminology
        
        if word_lower == 'vanilla' and any(indicator in sent_text for indicator in ['software', 'configuration', 'setup']):
            ev += 0.15  # Technical context needs clear language
        
        if word_lower == 'versus' and any(indicator in sent_text for indicator in ['vs.', 'v.', 'comparison']):
            ev += 0.1  # Comparison context benefits from spelled-out form
        
        if word_lower == 'via' and any(indicator in sent_text for indicator in ['network', 'routing', 'data']):
            ev -= 0.1  # Technical routing context where "via" is appropriate
        
        return ev

    def _apply_structural_clues_v_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for V-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_v_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for V-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'customer_facing' and word_lower in ['vanilla', 'velcro']:
            ev += 0.2  # Customer content needs clear, professional language
        elif content_type == 'legal' and word_lower == 'velcro':
            ev += 0.3  # Legal content must avoid trademark violations
        elif content_type == 'technical' and word_lower in ['vanilla', 'versus']:
            ev += 0.15  # Technical docs benefit from precise terminology
        
        if audience == 'external' and word_lower in ['vanilla', 'velcro']:
            ev += 0.2  # External audiences need clear, legally compliant language
        elif audience == 'global' and word_lower == 'vanilla':
            ev += 0.15  # Global audiences need clear, non-jargon language
        
        return ev

    def _apply_feedback_clues_v_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for V-words."""
        patterns = {'often_flagged_terms': {'vanilla', 'velcro', 'versus'}, 'accepted_terms': {'vice versa'}}
        word_lower = word.lower()
        
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        elif word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.2  # "vice versa" is acceptable when written correctly
        
        return ev