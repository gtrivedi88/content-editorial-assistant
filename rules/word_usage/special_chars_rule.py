"""
Word Usage Rule for special characters and numbers (Production-Grade)
Evidence-based analysis with surgical zero false positive guards for special character usage detection.
Based on IBM Style Guide recommendations with production-grade evidence calculation.
Preserves sophisticated Matcher integration for hash character detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
    from spacy.matcher import Matcher
except ImportError:
    Doc = None
    Matcher = None

class SpecialCharsRule(BaseWordUsageRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect usage of special characters and numbers.
    
    Implements evidence-based analysis with:
    - Surgical zero false positive guards for special character usage
    - Dynamic base evidence scoring based on usage specificity and context
    - Context-aware adjustments for different writing domains
    - PRESERVED: Advanced Matcher integration for hash character detection
    
    Features:
    - Near 100% false positive elimination through surgical guards
    - Usage-specific evidence calculation for each special character violation
    - Evidence-aware suggestions tailored to writing context
    - Sophisticated pattern matching for fiscal periods and symbols
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_special'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """Evidence-based analysis for special character usage violations."""
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define special character and number patterns
        special_patterns = {
            "24/7": {"alternatives": ["24x7", "24 hours a day"], "category": "time_format", "severity": "medium"},
            "H1": {"alternatives": ["1H"], "category": "fiscal_period", "severity": "medium"},
            "H2": {"alternatives": ["2H"], "category": "fiscal_period", "severity": "medium"},
            "Q1": {"alternatives": ["1Q"], "category": "fiscal_period", "severity": "medium"},
            "Q2": {"alternatives": ["2Q"], "category": "fiscal_period", "severity": "medium"},
            "Q3": {"alternatives": ["3Q"], "category": "fiscal_period", "severity": "medium"},
            "Q4": {"alternatives": ["4Q"], "category": "fiscal_period", "severity": "medium"},
        }

        # Evidence-based analysis for standard special character patterns
        for pattern, details in special_patterns.items():
            for match in re.finditer(r'\b' + re.escape(pattern) + r'\b', text, re.IGNORECASE):
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
                    
                    evidence_score = self._calculate_special_evidence(pattern, token, sent, text, context or {}, details["category"])
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message(pattern, evidence_score, details["category"]),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions(pattern, details["alternatives"], evidence_score, context or {}, details["category"]),
                            severity=details["severity"] if evidence_score < 0.7 else 'high',
                            text=text, context=context, evidence_score=evidence_score,
                            span=(char_start, char_end), flagged_text=matched_text
                        ))

        # PRESERVE EXISTING ADVANCED FUNCTIONALITY: spaCy Matcher for hash character detection
        if Matcher is not None:
            if not hasattr(self, '_hash_matcher'):
                self._hash_matcher = Matcher(nlp.vocab)
                hash_pattern = [{"TEXT": "#"}]
                self._hash_matcher.add("HASH_CHAR", [hash_pattern])

            hash_matches = self._hash_matcher(doc)
            for match_id, start, end in hash_matches:
                span = doc[start:end]
                sent = span.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                # Apply surgical guards for hash detection
                if self._apply_surgical_zero_false_positive_guards_word_usage(span[0], context or {}):
                    continue
                
                evidence_score = self._calculate_special_evidence("#", span[0], sent, text, context or {}, "symbol_usage")
                
                if evidence_score > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text, sentence_index=sentence_index,
                        message=self._generate_evidence_aware_word_usage_message("#", evidence_score, "symbol_usage"),
                        suggestions=self._generate_evidence_aware_word_usage_suggestions("#", ["number sign", "hash sign"], evidence_score, context or {}, "symbol_usage"),
                        severity='low' if evidence_score < 0.7 else 'medium',
                        text=text, context=context, evidence_score=evidence_score,
                        span=(span.start_char, span.end_char), flagged_text=span.text
                    ))
        
        return errors

    def _calculate_special_evidence(self, pattern: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score for special character usage violations."""
        evidence_score = self._get_base_special_evidence_score(pattern, category, sentence, context)
        if evidence_score == 0.0:
            return 0.0
        
        evidence_score = self._apply_linguistic_clues_special(evidence_score, pattern, token, sentence)
        evidence_score = self._apply_structural_clues_special(evidence_score, context)
        evidence_score = self._apply_semantic_clues_special(evidence_score, pattern, text, context)
        evidence_score = self._apply_feedback_clues_special(evidence_score, pattern, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_special_evidence_score(self, pattern: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Set dynamic base evidence score based on special character category."""
        if category == 'fiscal_period':
            return 0.7  # "H1", "Q1" etc. - corporate formatting standards
        elif category == 'time_format':
            return 0.6  # "24/7" - clarity and format preference
        elif category == 'symbol_usage':
            return 0.5  # "#" - terminology precision
        return 0.6

    def _apply_linguistic_clues_special(self, ev: float, pattern: str, token, sentence) -> float:
        """Apply special character-specific linguistic clues."""
        sent_text = sentence.text.lower()
        pattern_lower = pattern.lower()
        
        if pattern_lower in ['h1', 'h2', 'q1', 'q2', 'q3', 'q4'] and any(indicator in sent_text for indicator in ['quarter', 'fiscal', 'financial']):
            ev += 0.15  # Fiscal context needs standard formatting
        
        if pattern_lower == '24/7' and any(indicator in sent_text for indicator in ['service', 'support', 'available']):
            ev += 0.1  # Service context benefits from clear formatting
        
        if pattern_lower == '#' and any(indicator in sent_text for indicator in ['hashtag', 'social', 'number']):
            ev += 0.1  # Context suggests need for clarification
        
        return ev

    def _apply_structural_clues_special(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for special characters."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_special(self, ev: float, pattern: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for special characters."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        pattern_lower = pattern.lower()
        
        if content_type == 'financial' and pattern_lower in ['h1', 'h2', 'q1', 'q2', 'q3', 'q4']:
            ev += 0.2  # Financial content needs standard fiscal formatting
        elif content_type == 'customer_facing' and pattern_lower == '24/7':
            ev += 0.15  # Customer content benefits from clear time expressions
        elif content_type == 'technical' and pattern_lower == '#':
            ev += 0.1  # Technical docs benefit from precise terminology
        
        if audience == 'external' and pattern_lower in ['h1', 'h2', 'q1', 'q2', 'q3', 'q4']:
            ev += 0.2  # External audiences need standard formatting
        elif audience == 'global' and pattern_lower == '24/7':
            ev += 0.15  # Global audiences benefit from clear expressions
        
        return ev

    def _apply_feedback_clues_special(self, ev: float, pattern: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for special characters."""
        patterns = {'often_flagged_terms': {'h1', 'h2', 'q1', 'q2', 'q3', 'q4', '24/7'}, 'accepted_terms': set()}
        pattern_lower = pattern.lower()
        
        if pattern_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        elif pattern_lower in patterns.get('accepted_terms', set()):
            ev -= 0.2
        
        return ev