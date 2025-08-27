"""
Word Usage Rule for words starting with 'Q' (Production-Grade)
Evidence-based analysis with surgical zero false positive guards for Q-word usage detection.
Based on IBM Style Guide recommendations with production-grade evidence calculation.
Preserves sophisticated POS analysis for 'quote' noun detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class QWordsRule(BaseWordUsageRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect usage of specific words starting with 'Q'.
    
    Implements evidence-based analysis with:
    - Surgical zero false positive guards for Q-word usage
    - Dynamic base evidence scoring based on word specificity and context
    - Context-aware adjustments for different writing domains
    - PRESERVED: Advanced POS analysis for 'quote' noun detection
    
    Features:
    - Near 100% false positive elimination through surgical guards
    - Word-specific evidence calculation for each Q-word violation
    - Evidence-aware suggestions tailored to writing context
    - Sophisticated grammatical analysis for quote vs quotation
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_q'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """Evidence-based analysis for Q-word usage violations."""
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        q_word_patterns = {
            "Q&A": {"alternatives": ["Q&A"], "category": "format_consistency", "severity": "low"},
            "quantum safe": {"alternatives": ["quantum-safe"], "category": "hyphenation", "severity": "low"},
            "quiesce": {"alternatives": ["pause", "temporarily stop"], "category": "technical_jargon", "severity": "low"},
        }

        # Evidence-based analysis for standard Q-word patterns
        for word, details in q_word_patterns.items():
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
                    
                    evidence_score = self._calculate_q_word_evidence(word, token, sent, text, context or {}, details["category"])
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message(word, evidence_score, details["category"]),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions(word, details["alternatives"], evidence_score, context or {}, details["category"]),
                            severity=details["severity"] if evidence_score < 0.7 else 'high',
                            text=text, context=context, evidence_score=evidence_score,
                            span=(char_start, char_end), flagged_text=matched_text
                        ))

        # PRESERVE EXISTING ADVANCED FUNCTIONALITY: Context-aware POS analysis for 'quote' as noun
        # This sophisticated linguistic analysis distinguishes "quote" as noun vs verb through grammar
        for token in doc:
            if token.lemma_.lower() == "quote" and token.pos_ == "NOUN":
                sent = token.sent
                
                # Get sentence index
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                # Apply surgical guards for POS detection
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue
                
                evidence_score = self._calculate_q_word_evidence("quote", token, sent, text, context or {}, "noun_misuse")
                
                if evidence_score > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text, sentence_index=sentence_index,
                        message=self._generate_evidence_aware_word_usage_message("quote", evidence_score, "noun_misuse"),
                        suggestions=self._generate_evidence_aware_word_usage_suggestions("quote", ["quotation"], evidence_score, context or {}, "noun_misuse"),
                        severity='medium' if evidence_score < 0.7 else 'high',
                        text=text, context=context, evidence_score=evidence_score,
                        span=(token.idx, token.idx + len(token.text)), flagged_text=token.text
                    ))
        
        return errors

    def _calculate_q_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score for Q-word usage violations."""
        evidence_score = self._get_base_q_word_evidence_score(word, category, sentence, context)
        if evidence_score == 0.0:
            return 0.0
        
        evidence_score = self._apply_linguistic_clues_q_words(evidence_score, word, token, sentence)
        evidence_score = self._apply_structural_clues_q_words(evidence_score, context)
        evidence_score = self._apply_semantic_clues_q_words(evidence_score, word, text, context)
        evidence_score = self._apply_feedback_clues_q_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_q_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Set dynamic base evidence score based on Q-word category."""
        if category == 'noun_misuse':
            return 0.75  # "quote" as noun - grammatical precision
        elif category == 'technical_jargon':
            return 0.6  # "quiesce" - clarity for broader audiences
        elif category in ['hyphenation', 'format_consistency']:
            return 0.5  # "quantum-safe", "Q&A" - style consistency
        return 0.6

    def _apply_linguistic_clues_q_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply Q-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        if word_lower == 'quote' and any(indicator in sent_text for indicator in ['said', 'stated', 'mentioned']):
            ev += 0.15  # Context suggests quotation usage
        
        if word_lower == 'quiesce' and any(indicator in sent_text for indicator in ['user', 'customer', 'documentation']):
            ev += 0.1  # User-facing content needs simpler language
        
        if word_lower == 'quantum safe' and any(indicator in sent_text for indicator in ['security', 'encryption', 'cryptography']):
            ev += 0.1  # Technical security context needs precise hyphenation
        
        return ev

    def _apply_structural_clues_q_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for Q-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_q_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for Q-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'customer_facing' and word_lower == 'quiesce':
            ev += 0.2  # Customer content needs accessible language
        elif content_type == 'technical' and word_lower == 'quote':
            ev += 0.1  # Technical docs benefit from precise terminology
        elif content_type == 'security' and word_lower == 'quantum safe':
            ev += 0.15  # Security docs need precise technical terminology
        
        if audience == 'external' and word_lower == 'quiesce':
            ev += 0.2  # External audiences need simpler language
        elif audience == 'global' and word_lower == 'quote':
            ev += 0.1  # Global audiences benefit from standard forms
        
        return ev

    def _apply_feedback_clues_q_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for Q-words."""
        patterns = {'often_flagged_terms': {'quote', 'quiesce'}, 'accepted_terms': {'q&a'}}
        word_lower = word.lower()
        
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        elif word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.2  # "Q&A" is standard format
        
        return ev