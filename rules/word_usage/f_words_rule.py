"""
Word Usage Rule for words starting with 'F'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class FWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'F'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_f'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for F-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define F-word patterns with evidence categories
        f_word_patterns = {
            "failback": {"alternatives": ["failback (noun)", "fail back (verb)"], "category": "form_usage", "severity": "low"},
            "failover": {"alternatives": ["failover (noun)", "fail over (verb)"], "category": "form_usage", "severity": "low"},
            "fallback": {"alternatives": ["fallback (noun)", "fall back (verb)"], "category": "form_usage", "severity": "low"},
            "farther": {"alternatives": ["farther (distance)", "further (degree)"], "category": "word_distinction", "severity": "medium"},
            "Fiber Channel": {"alternatives": ["Fibre Channel"], "category": "technical_standard", "severity": "high"},
            "filename": {"alternatives": ["file name"], "category": "context_specific", "severity": "low"},
            "fill out": {"alternatives": ["complete", "specify", "enter"], "category": "action_clarity", "severity": "medium"},
            "fine tune": {"alternatives": ["fine-tune (adjective)", "fine tune (verb)"], "category": "hyphenation", "severity": "low"},
            "fire up": {"alternatives": ["start"], "category": "jargon", "severity": "medium"},
            "first name": {"alternatives": ["given name"], "category": "inclusive_language", "severity": "medium"},
            "fixpack": {"alternatives": ["fix pack"], "category": "spacing", "severity": "low"},
        }

        # Evidence-based analysis for F-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Check exact lemma matches first (single words)
            if token_lemma in f_word_patterns and ' ' not in token_lemma:
                matched_pattern = token_lemma
            # Also check for exact text matches (single words)
            elif token_text in f_word_patterns and ' ' not in token_text:
                matched_pattern = token_text
            
            if matched_pattern:
                details = f_word_patterns[matched_pattern]
                
                # Apply surgical guards
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue
                
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_f_word_evidence(
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
        
        # 2. Multi-word phrase detection for F-words
        multi_word_patterns = {pattern: details for pattern, details in f_word_patterns.items() if ' ' in pattern}
        
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
                
                evidence_score = self._calculate_f_word_evidence(
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

    def _calculate_f_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for F-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and context
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        
        Args:
            word: The F-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (technical_standard, inclusive_language, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_f_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_f_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_f_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_f_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_f_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_f_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on F-word category and violation specificity.
        Higher risk categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # Very high-risk technical standards
        if category == 'technical_standard':
            return 0.95  # "Fiber Channel" vs "Fibre Channel" - precise technical terminology required
        
        # High-risk inclusive language issues
        elif category == 'inclusive_language':
            return 0.85  # "first name" vs "given name" - global inclusivity critical
        
        # Medium-high risk clarity and professionalism
        elif category in ['jargon', 'action_clarity']:
            return 0.75  # "fire up", "fill out" - professional clarity needed
        
        # Medium risk semantic distinctions
        elif category == 'word_distinction':
            return 0.7  # "farther" vs "further" - semantic precision important
        
        # Lower risk formatting and usage preferences
        elif category in ['form_usage', 'hyphenation', 'spacing']:
            if word_lower in ['failback', 'failover', 'fallback']:
                return 0.6  # Technical terms have specific forms
            else:
                return 0.5  # "fine-tune", "fix pack" - formatting preferences
        
        # Context-dependent issues
        elif category == 'context_specific':
            return 0.4  # "filename" - depends on context and style guide
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_f_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply F-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # Technical context affects certain words
        if word_lower in ['fiber channel', 'fibre channel']:
            tech_indicators = ['network', 'storage', 'protocol', 'connection']
            if any(tech in sent_text for tech in tech_indicators):
                ev += 0.15  # Technical contexts need standard terminology
        
        # Action context affects verb choices
        if word_lower in ['fill out', 'fire up']:
            action_indicators = ['form', 'application', 'system', 'process']
            if any(action in sent_text for action in action_indicators):
                ev += 0.1  # Actions need clarity
        
        # International context affects naming conventions
        if word_lower == 'first name':
            international_indicators = ['global', 'international', 'worldwide', 'region']
            if any(intl in sent_text for intl in international_indicators):
                ev += 0.15  # International contexts need inclusive language
        
        return ev

    def _apply_structural_clues_f_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for F-words."""
        block_type = context.get('block_type', 'paragraph')
        
        if block_type in ['step', 'procedure']:
            ev += 0.1  # Procedural content needs precision
        elif block_type == 'heading':
            ev -= 0.1  # Headings more flexible
        
        return ev

    def _apply_semantic_clues_f_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for F-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'tutorial':
            if word_lower in ['fill out', 'fire up']:
                ev += 0.15  # Tutorials need clear, professional language
        elif content_type == 'technical':
            if word_lower in ['fiber channel', 'filename']:
                ev += 0.1  # Technical docs need standard terminology
        elif content_type == 'international':
            if word_lower == 'first name':
                ev += 0.2  # International content requires inclusive language
        
        if audience == 'global':
            if word_lower == 'first name':
                ev += 0.15  # Global audiences need inclusive terminology
        
        return ev

    def _apply_feedback_clues_f_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for F-words."""
        patterns = self._get_cached_feedback_patterns_f_words()
        word_lower = word.lower()
        
        # Consistently flagged terms
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        
        # Consistently accepted terms
        if word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.2
        
        # Context-specific patterns
        content_type = context.get('content_type', 'general')
        context_patterns = patterns.get(f'{content_type}_patterns', {})
        
        if word_lower in context_patterns.get('flagged', set()):
            ev += 0.1
        elif word_lower in context_patterns.get('accepted', set()):
            ev -= 0.1
        
        return ev

    def _get_cached_feedback_patterns_f_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for F-words."""
        return {
            'often_flagged_terms': {'first name', 'fire up', 'fill out', 'fiber channel'},
            'accepted_terms': set(),
            'technical_patterns': {
                'flagged': {'fiber channel', 'filename'},
                'accepted': {'failover', 'fallback'}  # In system administration contexts
            },
            'international_patterns': {
                'flagged': {'first name'},
                'accepted': set()
            },
            'tutorial_patterns': {
                'flagged': {'fire up', 'fill out'},
                'accepted': set()
            },
            'procedure_patterns': {
                'flagged': {'fine tune'},  # Should be "fine-tune"
                'accepted': {'fix pack'}  # In some contexts
            }
        }