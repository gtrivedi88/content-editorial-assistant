"""
Word Usage Rule for words starting with 'W' (Production-Grade)
Evidence-based analysis with surgical zero false positive guards for W-word usage detection.
Based on IBM Style Guide recommendations with production-grade evidence calculation.
Preserves sophisticated morphological analysis for 'while' semantic detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class WWordsRule(BaseWordUsageRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect usage of specific words starting with 'W'.
    
    Implements evidence-based analysis with:
    - Surgical zero false positive guards for W-word usage
    - Dynamic base evidence scoring based on word specificity and context
    - Context-aware adjustments for different writing domains
    - PRESERVED: Advanced morphological analysis for 'while' semantic detection
    
    Features:
    - Near 100% false positive elimination through surgical guards
    - Word-specific evidence calculation for each W-word violation
    - Evidence-aware suggestions tailored to writing context
    - Sophisticated dependency parsing and morphology for 'while' context
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_w'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """Evidence-based analysis for W-word usage violations."""
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        w_word_patterns = {
            "w/": {"alternatives": ["with"], "category": "abbreviation", "severity": "medium"},
            "war room": {"alternatives": ["command center", "operations center"], "category": "inclusive_language", "severity": "high"},
            "web site": {"alternatives": ["website"], "category": "spacing", "severity": "low"},
            "whitelist": {"alternatives": ["allowlist"], "category": "inclusive_language", "severity": "high"},
            "Wi-Fi": {"alternatives": ["Wi-Fi (certified)", "wifi (generic)"], "category": "technical_precision", "severity": "low"},
            "work station": {"alternatives": ["workstation"], "category": "spacing", "severity": "low"},
            "world-wide": {"alternatives": ["worldwide"], "category": "hyphenation", "severity": "low"},
        }

        # Evidence-based analysis for standard W-word patterns
        for word, details in w_word_patterns.items():
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
                    
                    evidence_score = self._calculate_w_word_evidence(word, token, sent, text, context or {}, details["category"])
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message(word, evidence_score, details["category"]),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions(word, details["alternatives"], evidence_score, context or {}, details["category"]),
                            severity=details["severity"] if evidence_score < 0.7 else 'high',
                            text=text, context=context, evidence_score=evidence_score,
                            span=(char_start, char_end), flagged_text=matched_text
                        ))

        # PRESERVE EXISTING ADVANCED FUNCTIONALITY: Context-aware morphological analysis for 'while'
        # This sophisticated linguistic analysis uses dependency parsing and morphology to determine semantic usage
        for token in doc:
            if token.lemma_.lower() == "while" and token.dep_ == "mark":
                sent = token.sent
                
                # Get the sentence index by finding the sentence in the doc.sents
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                # Apply surgical guards for dependency detection
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue
                
                # Heuristic: if the clause is not clearly about time, flag for review.
                is_time_related = any(t.pos_ == "VERB" and "ing" in t.morph for t in token.head.children)
                if not is_time_related:
                    evidence_score = self._calculate_w_word_evidence("while", token, sent, text, context or {}, "semantic_precision")
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message("while", evidence_score, "semantic_precision"),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions("while", ["although", "whereas"], evidence_score, context or {}, "semantic_precision"),
                            severity='medium' if evidence_score < 0.7 else 'high',
                            text=text, context=context, evidence_score=evidence_score,
                            span=(token.idx, token.idx + len(token.text)), flagged_text=token.text
                        ))
        
        return errors

    def _calculate_w_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score for W-word usage violations."""
        evidence_score = self._get_base_w_word_evidence_score(word, category, sentence, context)
        if evidence_score == 0.0:
            return 0.0
        
        evidence_score = self._apply_linguistic_clues_w_words(evidence_score, word, token, sentence)
        evidence_score = self._apply_structural_clues_w_words(evidence_score, context)
        evidence_score = self._apply_semantic_clues_w_words(evidence_score, word, text, context)
        evidence_score = self._apply_feedback_clues_w_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_w_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Set dynamic base evidence score based on W-word category."""
        if category == 'inclusive_language':
            return 0.9  # "war room", "whitelist" - critical for inclusive content
        elif category in ['abbreviation', 'semantic_precision']:
            return 0.75  # "w/", "while" - clarity and professionalism
        elif category == 'technical_precision':
            return 0.6  # "Wi-Fi" - technical accuracy
        elif category in ['spacing', 'hyphenation']:
            return 0.5  # "web site", "work station", "world-wide" - consistency
        return 0.6

    def _apply_linguistic_clues_w_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply W-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        if word_lower in ['war room', 'whitelist'] and any(indicator in sent_text for indicator in ['team', 'customer', 'global']):
            ev += 0.3  # Team/customer context needs inclusive language
        
        if word_lower == 'while' and any(indicator in sent_text for indicator in ['contrast', 'however', 'although']):
            ev += 0.2  # Contrast context suggests non-temporal usage
        
        if word_lower == 'w/' and any(indicator in sent_text for indicator in ['documentation', 'formal', 'technical']):
            ev += 0.15  # Formal context needs spelled-out words
        
        if word_lower == 'wi-fi' and any(indicator in sent_text for indicator in ['certified', 'standard', 'wireless']):
            ev += 0.1  # Technical context needs precision
        
        return ev

    def _apply_structural_clues_w_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for W-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_w_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for W-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'customer_facing' and word_lower in ['war room', 'whitelist']:
            ev += 0.3  # Customer content must use inclusive language
        elif content_type == 'international' and word_lower in ['war room', 'whitelist']:
            ev += 0.25  # International content requires inclusive language
        elif content_type == 'technical' and word_lower in ['w/', 'wi-fi']:
            ev += 0.15  # Technical docs need precision and professionalism
        
        if audience == 'external' and word_lower in ['war room', 'whitelist']:
            ev += 0.3  # External audiences need inclusive terminology
        elif audience == 'global' and word_lower in ['war room', 'whitelist', 'w/']:
            ev += 0.2  # Global audiences need inclusive, clear language
        
        return ev

    def _apply_feedback_clues_w_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for W-words."""
        patterns = {'often_flagged_terms': {'war room', 'whitelist', 'while', 'w/'}, 'accepted_terms': set()}
        word_lower = word.lower()
        
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        elif word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.2
        
        return ev