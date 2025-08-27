"""
Word Usage Rule for words starting with 'C'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
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
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_c'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for C-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define C-word patterns with evidence categories
        c_word_patterns = {
            "cancelation": {"alternatives": ["cancellation"], "category": "spelling", "severity": "low"},
            "can not": {"alternatives": ["cannot"], "category": "spacing", "severity": "high"},
            "canned": {"alternatives": ["predefined", "preconfigured"], "category": "jargon", "severity": "medium"},
            "catalogue": {"alternatives": ["catalog"], "category": "spelling", "severity": "low"},
            "checkbox": {"alternatives": ["check box"], "category": "spacing", "severity": "low"},
            "check out": {"alternatives": ["check out (verb)", "checkout (noun)"], "category": "form_usage", "severity": "low"},
            "click on": {"alternatives": ["click"], "category": "redundant_preposition", "severity": "medium"},
            "comprise": {"alternatives": ["include", "contain"], "category": "word_choice", "severity": "medium"},
            "copy and paste": {"alternatives": ["copy", "paste"], "category": "action_clarity", "severity": "low"},
            "currently": {"alternatives": ["now"], "category": "word_choice", "severity": "low"},
        }

        # Evidence-based analysis for C-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Check exact lemma matches first (single words)
            if token_lemma in c_word_patterns and ' ' not in token_lemma:
                matched_pattern = token_lemma
            # Also check for exact text matches (single words)
            elif token_text in c_word_patterns and ' ' not in token_text:
                matched_pattern = token_text
            
            if matched_pattern:
                details = c_word_patterns[matched_pattern]
                
                # Apply surgical guards
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue
                
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_c_word_evidence(
                    matched_pattern, token, sent, text, context or {}, details["category"]
                )
                
                if evidence_score > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_index,
                        message=self._generate_evidence_aware_word_usage_message(matched_pattern, evidence_score, details["category"]),
                        suggestions=self._generate_evidence_aware_word_usage_suggestions(matched_pattern, details["alternatives"], evidence_score, context or {}, details["category"]),
                        severity=details["severity"] if evidence_score < 0.7 else 'high',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
        
        # 2. Multi-word phrase detection
        multi_word_patterns = {pattern: details for pattern, details in c_word_patterns.items() if ' ' in pattern}
        
        if multi_word_patterns:
            phrase_matches = self._find_multi_word_phrases_with_lemma(doc, list(multi_word_patterns.keys()), case_sensitive=False)
            
            for match in phrase_matches:
                pattern = match['phrase']
                details = multi_word_patterns[pattern]
                
                # Apply surgical guards on the first token
                if self._apply_surgical_zero_false_positive_guards_word_usage(match['start_token'], context or {}):
                    continue
                
                sent = match['start_token'].sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_c_word_evidence(
                    pattern, match['start_token'], sent, text, context or {}, details["category"]
                )
                
                if evidence_score > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_index,
                        message=self._generate_evidence_aware_word_usage_message(pattern, evidence_score, details["category"]),
                        suggestions=self._generate_evidence_aware_word_usage_suggestions(pattern, details["alternatives"], evidence_score, context or {}, details["category"]),
                        severity=details["severity"] if evidence_score < 0.7 else 'high',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(match['start_char'], match['end_char']),
                        flagged_text=match['actual_text']
                    ))
        
        return errors

    def _calculate_c_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score for C-word usage violations."""
        evidence_score = self._get_base_c_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0
        
        evidence_score = self._apply_linguistic_clues_c_words(evidence_score, word, token, sentence)
        evidence_score = self._apply_structural_clues_c_words(evidence_score, context)
        evidence_score = self._apply_semantic_clues_c_words(evidence_score, word, text, context)
        evidence_score = self._apply_feedback_clues_c_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_c_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Set dynamic base evidence score based on C-word category."""
        if category == 'spacing':
            return 0.9  # "can not" vs "cannot", "checkbox" vs "check box"
        elif category == 'redundant_preposition':
            return 0.8  # "click on" - clear redundancy
        elif category == 'jargon':
            return 0.75  # "canned" - technical jargon
        elif category in ['word_choice', 'action_clarity']:
            return 0.65  # "comprise", "copy and paste"
        elif category in ['spelling', 'form_usage']:
            return 0.5  # "catalogue"/"catalog", "check out" forms
        return 0.6

    def _apply_linguistic_clues_c_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply C-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # UI interaction context
        ui_indicators = ['button', 'link', 'menu', 'icon']
        if any(ui in sent_text for ui in ui_indicators):
            if word_lower == 'click on':
                ev += 0.15  # "Click on" particularly problematic in UI
        
        # Technical jargon context
        if word_lower == 'canned':
            technical_indicators = ['solution', 'response', 'data']
            if any(tech in sent_text for tech in technical_indicators):
                ev += 0.1
        
        return ev

    def _apply_structural_clues_c_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for C-words."""
        block_type = context.get('block_type', 'paragraph')
        
        if block_type in ['step', 'procedure']:
            ev += 0.1  # Procedural content needs precision
        elif block_type == 'heading':
            ev -= 0.1  # Headings more flexible
        
        return ev

    def _apply_semantic_clues_c_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for C-words."""
        content_type = context.get('content_type', 'general')
        word_lower = word.lower()
        
        if content_type == 'tutorial':
            if word_lower in ['click on', 'copy and paste']:
                ev += 0.15  # Tutorials need clear actions
        elif content_type == 'technical':
            if word_lower == 'canned':
                ev += 0.1  # Technical docs avoid jargon
        
        return ev

    def _apply_feedback_clues_c_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for C-words."""
        patterns = {'often_flagged_terms': {'can not', 'click on', 'canned'}, 'accepted_terms': set()}
        word_lower = word.lower()
        
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        elif word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.2
        
        return ev