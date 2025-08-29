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
        """
        Evidence-based analysis for Q-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define Q-word patterns with evidence categories
        q_word_patterns = {
            "Q&A": {"alternatives": ["Q&A", "question and answer"], "category": "format_consistency", "severity": "low"},
            "quantum safe": {"alternatives": ["quantum-safe"], "category": "hyphenation", "severity": "low"},
            "quiesce": {"alternatives": ["pause", "temporarily stop"], "category": "technical_jargon", "severity": "medium"},
            "quote": {"alternatives": ["quotation"], "category": "noun_misuse", "severity": "medium"},
            "quick": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "quality": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "question": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
        }

        # Evidence-based analysis for Q-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches (including advanced POS analysis for 'quote')
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Special handling for 'quote' - only flag when used as noun
            if token_lemma == "quote" and token.pos_ == "NOUN":
                matched_pattern = "quote"
            # Check other single words (excluding multi-word patterns) - case-insensitive
            elif token_lemma != "quote":  # Skip quote for regular processing since we handle it specially above
                for pattern in q_word_patterns:
                    if ' ' not in pattern:  # Single word pattern
                        if (token_lemma == pattern.lower() or 
                            token_text == pattern.lower() or
                            token.text == pattern):  # Handle case-sensitive patterns like "Q&A"
                            matched_pattern = pattern
                            break
            
            if matched_pattern:
                details = q_word_patterns[matched_pattern]
                
                # Skip acceptable usage patterns
                if details["category"] == "acceptable_usage":
                    continue
                
                # Apply surgical guards
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue
                
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_q_word_evidence(
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

        # 2. Multi-word phrase detection for Q-words
        multi_word_patterns = {pattern: details for pattern, details in q_word_patterns.items() if ' ' in pattern and details["category"] != "acceptable_usage"}
        
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
                
                evidence_score = self._calculate_q_word_evidence(
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

    def _calculate_q_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for Q-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and violation type
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        - Special POS analysis preservation for 'quote' noun detection
        
        Args:
            word: The Q-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (noun_misuse, technical_jargon, hyphenation, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_q_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_q_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_q_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_q_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_q_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_q_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on Q-word category and violation specificity.
        Higher priority categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # Very high-risk grammatical and clarity issues
        if category == 'noun_misuse':
            if word_lower == 'quote':
                return 0.75  # Grammatical precision critical for professional content
            else:
                return 0.75  # Other noun misuse issues
        
        # High-risk technical jargon and clarity issues
        elif category == 'technical_jargon':
            if word_lower == 'quiesce':
                return 0.65  # Technical jargon clarity for broader audiences
            else:
                return 0.65  # Other technical jargon issues
        
        # Medium-risk formatting and consistency issues
        elif category in ['hyphenation', 'format_consistency']:
            if word_lower == 'quantum safe':
                return 0.55  # Hyphenation consistency for technical terms
            elif word_lower == 'q&a':
                return 0.45  # Format consistency context-dependent
            else:
                return 0.5  # Other formatting issues
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_q_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply Q-word-specific linguistic clues using SpaCy analysis."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # === NOUN MISUSE CLUES ===
        if word_lower == 'quote':
            # Context suggests quotation usage (surrounding words indicating reported speech)
            if any(indicator in sent_text for indicator in ['said', 'stated', 'mentioned', 'according to']):
                ev += 0.2  # Strong context suggests quotation usage
            elif any(indicator in sent_text for indicator in ['from', 'by', 'attributed']):
                ev += 0.15  # Attribution context suggests quotation
            # Check grammatical context using POS tags
            if hasattr(token, 'head') and token.head.pos_ in ['VERB']:
                if token.head.lemma_.lower() in ['give', 'provide', 'request', 'generate']:
                    ev += 0.1  # Verbal context suggests quotation usage
        
        # === TECHNICAL JARGON CLUES ===
        if word_lower == 'quiesce':
            # User-facing content needs simpler language
            if any(indicator in sent_text for indicator in ['user', 'customer', 'documentation', 'guide']):
                ev += 0.15  # User-facing content needs accessible language
            elif any(indicator in sent_text for indicator in ['instruction', 'tutorial', 'help', 'manual']):
                ev += 0.1  # Instructional context benefits from clear language
            # Technical operations context
            elif any(indicator in sent_text for indicator in ['system', 'process', 'service', 'operation']):
                ev += 0.05  # Technical context but still benefits from clarity
        
        # === HYPHENATION CLUES ===
        if word_lower == 'quantum safe':
            # Technical security context needs precise hyphenation
            if any(indicator in sent_text for indicator in ['security', 'encryption', 'cryptography', 'algorithm']):
                ev += 0.15  # Security context needs precise technical terminology
            elif any(indicator in sent_text for indicator in ['protocol', 'standard', 'implementation', 'solution']):
                ev += 0.1  # Technical implementation context benefits from consistency
        
        # === FORMAT CONSISTENCY CLUES ===
        if word_lower in ['q&a', 'q and a']:
            # Format consistency in documentation
            if any(indicator in sent_text for indicator in ['section', 'document', 'page', 'chapter']):
                ev += 0.1  # Documentation context benefits from standard formatting
            elif any(indicator in sent_text for indicator in ['frequently', 'common', 'typical']):
                ev += 0.05  # FAQ context benefits from consistent format
        
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
        patterns = self._get_cached_feedback_patterns_q_words()
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
            ev -= 0.35  # Strong reduction for context-appropriate terms to go below rule threshold
        
        return ev

    def _get_cached_feedback_patterns_q_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for Q-words."""
        return {
            'often_flagged_terms': {'quote', 'quiesce', 'quantum safe'},
            'accepted_terms': {'q&a', 'quick', 'quality', 'question'},  # Generally acceptable terms
            'technical_patterns': {
                'flagged': {'quote', 'quiesce'},  # Technical docs need precision
                'accepted': {'q&a', 'quantum safe', 'quality', 'question'}  # Technical terms acceptable
            },
            'customer_facing_patterns': {
                'flagged': {'quiesce', 'quantum safe'},  # Customer content needs accessible language
                'accepted': {'q&a', 'quote', 'question', 'quality'}  # Customer-friendly terms
            },
            'security_patterns': {
                'flagged': {'quantum safe', 'quote'},  # Security docs need precise terminology
                'accepted': {'q&a', 'quality', 'question'}  # Security context terms
            },
            'documentation_patterns': {
                'flagged': {'quiesce', 'quote'},  # Documentation needs clear language
                'accepted': {'q&a', 'question', 'quality'}  # Documentation-friendly terms
            },
            'formal_patterns': {
                'flagged': {'q&a', 'quote'},  # Formal writing prefers standard forms
                'accepted': {'question', 'quality', 'quantum safe'}  # Formal terms acceptable
            },
            'general_patterns': {
                'flagged': {'quiesce', 'quantum safe'},  # General content prefers accessible language
                'accepted': {'q&a', 'quote', 'question', 'quality'}  # Common terms acceptable
            }
        }