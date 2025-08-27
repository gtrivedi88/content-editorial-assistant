"""
Word Usage Rule for words starting with 'M'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection combined with context-aware analysis.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class MWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'M'.
    Enhanced with spaCy PhraseMatcher for efficient detection combined with context-aware analysis.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_m'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """Evidence-based analysis for M-word usage violations."""
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        m_word_patterns = {
            "man-hour": {"alternatives": ["person hour", "labor hour"], "category": "inclusive_language", "severity": "high"},
            "man day": {"alternatives": ["person day"], "category": "inclusive_language", "severity": "high"},
            "master": {"alternatives": ["primary", "main", "controller"], "category": "inclusive_language", "severity": "high"},
            "may": {"alternatives": ["can", "might"], "category": "word_distinction", "severity": "medium"},
            "menu bar": {"alternatives": ["menubar"], "category": "spacing", "severity": "low"},
            "meta data": {"alternatives": ["metadata"], "category": "spacing", "severity": "low"},
            "methodology": {"alternatives": ["method"], "category": "word_choice", "severity": "low"},
            "migrate": {"alternatives": ["move", "transfer"], "category": "technical_precision", "severity": "medium"},
        }

        # Evidence-based analysis for M-word patterns
        for word, details in m_word_patterns.items():
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
                    
                    # PRESERVE EXISTING ADVANCED FUNCTIONALITY: Context-aware filtering for 'master'
                    # Apply sophisticated contextual logic - only flag 'master' when 'slave' is present
                    if word.lower() == 'master':
                        error_sentence = sent.text.lower()
                        if 'slave' not in error_sentence:
                            continue  # Skip 'master' if 'slave' is not in the same sentence (avoid false positives)
                    
                    evidence_score = self._calculate_m_word_evidence(word, token, sent, text, context or {}, details["category"])
                    
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

    def _calculate_m_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score for M-word usage violations."""
        evidence_score = self._get_base_m_word_evidence_score(word, category, sentence, context)
        if evidence_score == 0.0:
            return 0.0
        
        evidence_score = self._apply_linguistic_clues_m_words(evidence_score, word, token, sentence)
        evidence_score = self._apply_structural_clues_m_words(evidence_score, context)
        evidence_score = self._apply_semantic_clues_m_words(evidence_score, word, text, context)
        evidence_score = self._apply_feedback_clues_m_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_m_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Set dynamic base evidence score based on M-word category."""
        if category == 'inclusive_language':
            return 0.9  # "man-hour", "man day", "master/slave" - critical for inclusive content
        elif category in ['technical_precision', 'word_distinction']:
            return 0.7  # "migrate", "may" - precision and clarity
        elif category in ['spacing', 'word_choice']:
            return 0.5  # "menu bar", "meta data", "methodology" - consistency
        return 0.6

    def _apply_linguistic_clues_m_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply M-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        if word_lower in ['man-hour', 'man day'] and any(indicator in sent_text for indicator in ['estimate', 'project', 'resource']):
            ev += 0.2  # Project context needs inclusive language
        
        if word_lower == 'master' and any(indicator in sent_text for indicator in ['slave', 'primary', 'secondary']):
            ev += 0.25  # Master/slave terminology needs inclusive alternatives
        
        if word_lower == 'migrate' and any(indicator in sent_text for indicator in ['upgrade', 'port', 'version']):
            ev += 0.15  # Technical context needs precise terminology
        
        if word_lower == 'may' and any(indicator in sent_text for indicator in ['permission', 'ability', 'possibility']):
            ev += 0.1  # Context clarifies whether "can" or "might" is better
        
        return ev

    def _apply_structural_clues_m_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for M-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_m_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for M-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'customer_facing' and word_lower in ['man-hour', 'man day', 'master']:
            ev += 0.3  # Customer content must use inclusive language
        elif content_type == 'technical' and word_lower in ['migrate', 'master']:
            ev += 0.2  # Technical docs need precise, inclusive terminology
        elif content_type == 'international' and word_lower in ['man-hour', 'man day']:
            ev += 0.25  # International content requires inclusive language
        
        if audience == 'global' and word_lower in ['man-hour', 'man day', 'master']:
            ev += 0.2  # Global audiences need inclusive terminology
        elif audience == 'external' and word_lower in ['man-hour', 'man day']:
            ev += 0.25  # External audiences need inclusive language
        
        return ev

    def _apply_feedback_clues_m_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for M-words."""
        patterns = {'often_flagged_terms': {'man-hour', 'man day', 'master', 'migrate'}, 'accepted_terms': set()}
        word_lower = word.lower()
        
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        elif word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.2
        
        return ev