"""
Word Usage Rule for 'key'
Enhanced with spaCy POS analysis for context-aware detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class KWordsRule(BaseWordUsageRule):
    """
    Checks for potentially incorrect usage of the word 'key'.
    Enhanced with spaCy POS analysis for context-aware detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_k'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """Evidence-based analysis for K-word usage violations."""
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # PRESERVED ADVANCED FUNCTIONALITY: Use Part-of-Speech (POS) tagging for context-aware detection
        # This sophisticated linguistic analysis distinguishes "key in your password" (verb) from 
        # "key feature" (adjective/noun), eliminating false positives through grammar awareness
        for token in doc:
            if token.lemma_.lower() == 'key' and token.pos_ == 'VERB':
                sent = token.sent
                
                # Get sentence index
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                # Apply surgical guards
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue
                
                evidence_score = self._calculate_k_word_evidence('key', token, sent, text, context or {}, 'verb_misuse')
                
                if evidence_score > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text, sentence_index=sentence_index,
                        message=self._generate_evidence_aware_word_usage_message('key', evidence_score, 'verb_misuse'),
                        suggestions=self._generate_evidence_aware_word_usage_suggestions('key', ['type', 'press'], evidence_score, context or {}, 'verb_misuse'),
                        severity='medium' if evidence_score < 0.7 else 'high',
                        text=text, context=context, evidence_score=evidence_score,
                        span=(token.idx, token.idx + len(token.text)), flagged_text=token.text
                    ))
        
        return errors

    def _calculate_k_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score for K-word usage violations."""
        evidence_score = self._get_base_k_word_evidence_score(word, category, sentence, context)
        if evidence_score == 0.0:
            return 0.0
        
        evidence_score = self._apply_linguistic_clues_k_words(evidence_score, word, token, sentence)
        evidence_score = self._apply_structural_clues_k_words(evidence_score, context)
        evidence_score = self._apply_semantic_clues_k_words(evidence_score, word, text, context)
        evidence_score = self._apply_feedback_clues_k_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_k_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Set dynamic base evidence score based on K-word category."""
        if category == 'verb_misuse':
            return 0.8  # "key" used as verb - needs correction for clarity
        return 0.6

    def _apply_linguistic_clues_k_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply K-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        if word_lower == 'key' and any(indicator in sent_text for indicator in ['keyboard', 'button', 'password', 'command']):
            ev += 0.15  # Action context needs precise language: "press" or "type"
        
        if word_lower == 'key' and any(indicator in sent_text for indicator in ['enter', 'input', 'data']):
            ev += 0.1  # Data entry context benefits from clear action verbs
        
        return ev

    def _apply_structural_clues_k_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for K-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.15  # Procedural content needs precise action verbs
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_k_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for K-words."""
        content_type = context.get('content_type', 'general')
        word_lower = word.lower()
        
        if content_type == 'tutorial' and word_lower == 'key':
            ev += 0.2  # Tutorials need clear, unambiguous action instructions
        elif content_type == 'technical' and word_lower == 'key':
            ev += 0.15  # Technical docs benefit from precise terminology
        elif content_type == 'user_interface' and word_lower == 'key':
            ev += 0.15  # UI instructions need clear action verbs
        
        return ev

    def _apply_feedback_clues_k_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for K-words."""
        patterns = {'often_flagged_terms': {'key'}, 'accepted_terms': set()}
        word_lower = word.lower()
        
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1  # "key" as verb is commonly flagged for improvement
        elif word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.2
        
        return ev