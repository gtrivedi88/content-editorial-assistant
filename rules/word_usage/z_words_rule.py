"""
Word Usage Rule for words starting with 'Z' (Production-Grade)
Evidence-based analysis with surgical zero false positive guards for Z-word usage detection.
Based on IBM Style Guide recommendations with production-grade evidence calculation.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ZWordsRule(BaseWordUsageRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect usage of specific words starting with 'Z'.
    
    Implements evidence-based analysis with:
    - Surgical zero false positive guards for Z-word usage
    - Dynamic base evidence scoring based on word specificity and context
    - Context-aware adjustments for different writing domains
    
    Features:
    - Near 100% false positive elimination through surgical guards
    - Word-specific evidence calculation for each Z-word violation
    - Evidence-aware suggestions tailored to writing context
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_z'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """Evidence-based analysis for Z-word usage violations."""
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        z_word_patterns = {
            "zero out": {"alternatives": ["zero"], "category": "verb_form", "severity": "low"},
            "zero emissions": {"alternatives": ["(avoid unsubstantiated claims)"], "category": "environmental_claim", "severity": "high"},
            "zero trust": {"alternatives": ["zero trust"], "category": "format_consistency", "severity": "low"},
            "zip": {"alternatives": ["compress"], "category": "trademark", "severity": "high"},
        }

        for word, details in z_word_patterns.items():
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
                    
                    evidence_score = self._calculate_z_word_evidence(word, token, sent, text, context or {}, details["category"])
                    
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

    def _calculate_z_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score for Z-word usage violations."""
        evidence_score = self._get_base_z_word_evidence_score(word, category, sentence, context)
        if evidence_score == 0.0:
            return 0.0
        
        evidence_score = self._apply_linguistic_clues_z_words(evidence_score, word, token, sentence)
        evidence_score = self._apply_structural_clues_z_words(evidence_score, context)
        evidence_score = self._apply_semantic_clues_z_words(evidence_score, word, text, context)
        evidence_score = self._apply_feedback_clues_z_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_z_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Set dynamic base evidence score based on Z-word category."""
        if category in ['environmental_claim', 'trademark']:
            return 0.9  # "zero emissions", "zip" - legal and accuracy critical
        elif category == 'verb_form':
            return 0.6  # "zero out" - style improvement
        elif category == 'format_consistency':
            return 0.5  # "zero trust" - format consistency
        return 0.6

    def _apply_linguistic_clues_z_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply Z-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        if word_lower == 'zero emissions' and any(indicator in sent_text for indicator in ['environmental', 'green', 'sustainable']):
            ev += 0.3  # Environmental context needs substantiated claims
        
        if word_lower == 'zip' and any(indicator in sent_text for indicator in ['file', 'compress', 'archive']):
            ev += 0.2  # File context needs generic terminology
        
        if word_lower == 'zero out' and any(indicator in sent_text for indicator in ['data', 'field', 'value']):
            ev += 0.1  # Data context benefits from concise language
        
        return ev

    def _apply_structural_clues_z_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for Z-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_z_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for Z-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'marketing' and word_lower == 'zero emissions':
            ev += 0.4  # Marketing content must avoid unsubstantiated claims
        elif content_type == 'legal' and word_lower in ['zero emissions', 'zip']:
            ev += 0.3  # Legal content requires accuracy and trademark compliance
        elif content_type == 'technical' and word_lower in ['zip', 'zero out']:
            ev += 0.15  # Technical docs benefit from precise terminology
        
        if audience == 'external' and word_lower in ['zero emissions', 'zip']:
            ev += 0.2  # External audiences need accurate, legally compliant language
        elif audience == 'global' and word_lower == 'zip':
            ev += 0.15  # Global audiences need generic, non-trademark terms
        
        return ev

    def _apply_feedback_clues_z_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for Z-words."""
        patterns = {'often_flagged_terms': {'zero emissions', 'zip'}, 'accepted_terms': {'zero trust'}}
        word_lower = word.lower()
        
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        elif word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.2  # "zero trust" is acceptable as two words
        
        return ev