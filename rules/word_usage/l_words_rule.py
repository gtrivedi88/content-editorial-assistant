"""
Word Usage Rule for words starting with 'L'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection combined with advanced morphological analysis.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class LWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'L'.
    Enhanced with spaCy PhraseMatcher for efficient detection combined with advanced morphological analysis.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_l'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for L-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define L-word patterns with evidence categories
        l_word_patterns = {
            "land and expand": {"alternatives": ["expansion strategy"], "category": "inclusive_language", "severity": "high"},
            "last name": {"alternatives": ["surname"], "category": "inclusive_language", "severity": "medium"},
            "leverage": {"alternatives": ["use"], "category": "jargon", "severity": "medium"},
            "licence": {"alternatives": ["license"], "category": "spelling", "severity": "low"},
            "log on to": {"alternatives": ["log on to"], "category": "correct_form", "severity": "low"},
            "log off of": {"alternatives": ["log off from"], "category": "preposition_usage", "severity": "medium"},
            "look and feel": {"alternatives": ["appearance", "user interface"], "category": "vague_language", "severity": "medium"},
            "lowercase": {"alternatives": ["lowercase"], "category": "spacing", "severity": "low"},
            "life cycle": {"alternatives": ["lifecycle"], "category": "spacing", "severity": "low"},
            "log in": {"alternatives": ["log in"], "category": "correct_form", "severity": "low"},
            "log out": {"alternatives": ["log out"], "category": "correct_form", "severity": "low"},
        }

        # Evidence-based analysis for L-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Check single words (excluding multi-word patterns)
            if (token_lemma in l_word_patterns and ' ' not in token_lemma):
                matched_pattern = token_lemma
            elif (token_text in l_word_patterns and ' ' not in token_text):
                matched_pattern = token_text
            
            if matched_pattern:
                details = l_word_patterns[matched_pattern]
                
                # Apply surgical guards
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue
                
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_l_word_evidence(
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

        # 2. Multi-word phrase detection for L-words
        multi_word_patterns = {pattern: details for pattern, details in l_word_patterns.items() if ' ' in pattern}
        
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
                
                evidence_score = self._calculate_l_word_evidence(
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

    def _calculate_l_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for L-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and violation type
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        
        Args:
            word: The L-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (inclusive_language, jargon, spelling, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_l_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_l_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_l_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_l_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_l_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_l_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on L-word category and violation specificity.
        Higher priority categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # Very high-risk inclusive language issues
        if category == 'inclusive_language':
            if word_lower == 'land and expand':
                return 0.9  # Potentially exclusionary business terminology
            elif word_lower == 'last name':
                return 0.8  # Important for global accessibility
            else:
                return 0.85  # Other inclusive language issues
        
        # High-risk jargon and vague language
        elif category in ['jargon', 'vague_language']:
            if word_lower == 'leverage':
                return 0.8  # Overused business jargon
            elif word_lower == 'look and feel':
                return 0.75  # Vague UI terminology
            else:
                return 0.75  # Other jargon/vague language issues
        
        # Medium-risk grammatical issues
        elif category == 'preposition_usage':
            return 0.65  # "log off of" - grammatical precision needed
        
        # Lower risk consistency issues
        elif category in ['spelling', 'spacing']:
            if word_lower == 'licence':
                return 0.6  # Regional spelling variant
            elif word_lower in ['life cycle', 'lowercase']:
                return 0.5  # Spacing/formatting consistency
            else:
                return 0.55  # Other spelling/spacing issues
        
        # Special handling for correct forms
        elif category == 'correct_form':
            if word_lower in ['log on to', 'log in', 'log out']:
                return 0.0  # These are correct forms, should not be flagged
            else:
                return 0.5  # Other form issues
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_l_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply L-word-specific linguistic clues using SpaCy analysis."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # === INCLUSIVE LANGUAGE CLUES ===
        if word_lower == 'land and expand':
            # Business strategy context increases importance of inclusive language
            if any(indicator in sent_text for indicator in ['strategy', 'business', 'growth', 'customer', 'market']):
                ev += 0.2  # Business context needs inclusive terminology
            elif any(indicator in sent_text for indicator in ['team', 'organization', 'company']):
                ev += 0.15  # Organizational context also important
        
        if word_lower == 'last name':
            # User-facing and international contexts increase importance
            if any(indicator in sent_text for indicator in ['global', 'international', 'form', 'user', 'customer']):
                ev += 0.2  # User-facing content needs inclusive language
            elif any(indicator in sent_text for indicator in ['registration', 'profile', 'account', 'signup']):
                ev += 0.15  # Form contexts especially important
        
        # === JARGON AND VAGUE LANGUAGE CLUES ===
        if word_lower == 'leverage':
            # Technical and international contexts need clearer language
            if any(indicator in sent_text for indicator in ['documentation', 'technical', 'international', 'tutorial']):
                ev += 0.2  # Technical/international context needs clear language
            elif any(indicator in sent_text for indicator in ['user', 'customer', 'help']):
                ev += 0.15  # User-facing content needs clarity
        
        if word_lower == 'look and feel':
            # UI/design contexts need specific terminology
            if any(indicator in sent_text for indicator in ['ui', 'interface', 'design', 'user experience', 'ux']):
                ev += 0.15  # UI context needs specific terminology
            elif any(indicator in sent_text for indicator in ['application', 'website', 'platform']):
                ev += 0.1  # Application context benefits from precision
        
        # === PREPOSITION AND GRAMMAR CLUES ===
        if word_lower == 'log off of':
            # Check grammatical context
            if token.dep_ in ['prep', 'pcomp']:  # Prepositional phrase context
                ev += 0.1  # Grammatical precision important in prepositional phrases
        
        # === SPELLING AND CONSISTENCY CLUES ===
        if word_lower == 'licence':
            # Regional context analysis
            if any(indicator in sent_text for indicator in ['american', 'us', 'software', 'license']):
                ev += 0.15  # American English context prefers "license"
        
        if word_lower == 'life cycle':
            # Technical contexts often prefer compound form
            if any(indicator in sent_text for indicator in ['software', 'development', 'product', 'system']):
                ev += 0.1  # Technical contexts prefer "lifecycle"
        
        return ev

    def _apply_structural_clues_l_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for L-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_l_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for L-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'customer_facing' and word_lower in ['land and expand', 'leverage']:
            ev += 0.25  # Customer content needs professional, clear language
        elif content_type == 'international' and word_lower in ['last name', 'leverage']:
            ev += 0.2  # International content needs inclusive, clear language
        elif content_type == 'ui_documentation' and word_lower == 'look and feel':
            ev += 0.15  # UI docs need specific terminology
        
        if audience == 'global' and word_lower in ['last name', 'leverage']:
            ev += 0.15  # Global audiences need inclusive, clear language
        elif audience == 'external' and word_lower == 'land and expand':
            ev += 0.3  # External audiences need inclusive terminology
        
        return ev

    def _apply_feedback_clues_l_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for L-words."""
        patterns = self._get_cached_feedback_patterns_l_words()
        word_lower = word.lower()
        
        # Consistently flagged terms
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        
        # Consistently accepted terms
        if word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.3
        
        # Context-specific patterns
        content_type = context.get('content_type', 'general')
        context_patterns = patterns.get(f'{content_type}_patterns', {})
        
        if word_lower in context_patterns.get('flagged', set()):
            ev += 0.1
        elif word_lower in context_patterns.get('accepted', set()):
            ev -= 0.15
        
        return ev

    def _get_cached_feedback_patterns_l_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for L-words."""
        return {
            'often_flagged_terms': {'land and expand', 'leverage', 'last name', 'look and feel', 'log off of'},
            'accepted_terms': {'log on to', 'log in', 'log out'},  # Correct forms
            'technical_patterns': {
                'flagged': {'leverage', 'look and feel', 'life cycle'},  # Technical docs need precision
                'accepted': {'licence', 'log in', 'log out'}  # Technical terms sometimes acceptable
            },
            'customer_facing_patterns': {
                'flagged': {'land and expand', 'leverage', 'last name', 'look and feel'},  # Customer content needs clarity
                'accepted': {'log on to', 'log in'}  # Standard login terminology
            },
            'international_patterns': {
                'flagged': {'last name', 'leverage', 'land and expand'},  # International content needs inclusive language
                'accepted': {'licence', 'log on to'}  # Regional variations acceptable
            },
            'ui_documentation_patterns': {
                'flagged': {'look and feel', 'leverage'},  # UI docs need specific terminology
                'accepted': {'log in', 'log out', 'lowercase'}  # UI elements acceptable
            },
            'formal_patterns': {
                'flagged': {'leverage', 'land and expand', 'look and feel'},  # Formal writing avoids jargon
                'accepted': {'log on to', 'log off of'}  # Formal preposition usage
            },
            'general_patterns': {
                'flagged': {'leverage', 'look and feel'},  # General content avoids vague language
                'accepted': {'log in', 'log out', 'lowercase'}  # Common terms acceptable
            }
        }