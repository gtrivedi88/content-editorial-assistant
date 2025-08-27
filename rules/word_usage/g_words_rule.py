"""
Word Usage Rule for words starting with 'G'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class GWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'G'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_g'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for G-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define G-word patterns with evidence categories
        g_word_patterns = {
            "gage": {"alternatives": ["gauge"], "category": "spelling", "severity": "low"},
            "genai": {"alternatives": ["gen AI", "generative AI"], "category": "capitalization", "severity": "medium"},
            "geo": {"alternatives": ["geographical area", "location"], "category": "abbreviation", "severity": "medium"},
            "given name": {"alternatives": ["given name (preferred)"], "category": "inclusive_language", "severity": "low"},
            "g11n": {"alternatives": ["globalization"], "category": "abbreviation", "severity": "medium"},
            "go-live": {"alternatives": ["go live"], "category": "hyphenation", "severity": "low"},
            "go live": {"alternatives": ["go live (preferred)", "launch"], "category": "preferred_form", "severity": "low"},
        }

        # Evidence-based analysis for G-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Check exact lemma matches first (single words)
            if token_lemma in g_word_patterns and ' ' not in token_lemma:
                matched_pattern = token_lemma
            # Also check for exact text matches (single words)  
            elif token_text in g_word_patterns and ' ' not in token_text:
                matched_pattern = token_text
            
            if matched_pattern:
                details = g_word_patterns[matched_pattern]
                
                # Apply surgical guards with exception for abbreviations we want to flag
                should_skip = self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {})
                
                # Override guard for specific abbreviations - we want to flag these
                if should_skip and matched_pattern in ['geo', 'g11n', 'genai']:
                    # Check if this is actually our target abbreviation, not a legitimate entity
                    if self._is_target_abbreviation_g_words(token, matched_pattern):
                        should_skip = False
                
                if should_skip:
                    continue
                
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_g_word_evidence(
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
        
        # 2. Hyphenated word detection for G-words
        hyphenated_patterns = ['go-live']  # Words that get tokenized as [word, "-", word]
        for i in range(len(doc) - 2):
            if (i < len(doc) - 2 and 
                doc[i + 1].text == "-" and
                doc[i].text.lower() + "-" + doc[i + 2].text.lower() in hyphenated_patterns):
                
                hyphenated_word = doc[i].text.lower() + "-" + doc[i + 2].text.lower()
                if hyphenated_word in g_word_patterns:
                    details = g_word_patterns[hyphenated_word]
                    
                    # Apply surgical guards on the first token
                    if self._apply_surgical_zero_false_positive_guards_word_usage(doc[i], context or {}):
                        continue
                    
                    sent = doc[i].sent
                    sentence_index = 0
                    for j, s in enumerate(doc.sents):
                        if s == sent:
                            sentence_index = j
                            break
                    
                    evidence_score = self._calculate_g_word_evidence(
                        hyphenated_word, doc[i], sent, text, context or {}, details["category"]
                    )
                    
                    if evidence_score > 0.1:
                        start_char = doc[i].idx
                        end_char = doc[i + 2].idx + len(doc[i + 2].text)
                        flagged_text = doc[i].text + "-" + doc[i + 2].text
                        
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message(hyphenated_word, evidence_score, details["category"]),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions(hyphenated_word, details["alternatives"], evidence_score, context or {}, details["category"]),
                            severity=details["severity"] if evidence_score < 0.7 else 'high',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(start_char, end_char),
                            flagged_text=flagged_text
                        ))

        # 3. Multi-word phrase detection for G-words
        multi_word_patterns = {pattern: details for pattern, details in g_word_patterns.items() if ' ' in pattern}
        
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
                
                evidence_score = self._calculate_g_word_evidence(
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

    def _calculate_g_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for G-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and context
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        
        Args:
            word: The G-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (spelling, abbreviation, capitalization, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_g_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_g_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_g_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_g_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_g_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_g_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on G-word category and violation specificity.
        Higher risk categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # High-risk unclear abbreviations
        if category == 'abbreviation':
            if word_lower == 'g11n':
                return 0.85  # Very unclear abbreviation, high priority
            elif word_lower == 'geo':
                return 0.75  # Unclear in customer content, context-dependent
            else:
                return 0.8  # Other abbreviations
        
        # Medium-high risk capitalization issues
        elif category == 'capitalization':
            return 0.75  # "genai" vs "gen AI" - standardization needed
        
        # Medium risk spelling corrections
        elif category == 'spelling':
            return 0.7  # "gage" vs "gauge" - clear spelling correction
        
        # Lower risk hyphenation preferences
        elif category == 'hyphenation':
            return 0.5  # "go-live" vs "go live" - style preference
        
        # Context-dependent preferred forms
        elif category == 'preferred_form':
            if word_lower == 'go live':
                return 0.05  # Very low evidence - "go live" is actually preferred
            else:
                return 0.4  # Other forms may need consideration
        
        # Special case: "given name" is actually preferred for inclusivity
        elif category == 'inclusive_language':
            if word_lower == 'given name':
                return 0.2  # Very low evidence since this is the preferred term
            else:
                return 0.8  # Other inclusive language issues are important
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_g_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply G-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        if word_lower == 'geo' and any(indicator in sent_text for indicator in ['customer', 'user', 'interface']):
            ev += 0.15  # Customer-facing content should avoid abbreviations
        
        if word_lower == 'genai' and any(indicator in sent_text for indicator in ['artificial', 'intelligence', 'machine']):
            ev += 0.1  # AI context needs standard capitalization
        
        return ev

    def _apply_structural_clues_g_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for G-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_g_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for G-words."""
        content_type = context.get('content_type', 'general')
        word_lower = word.lower()
        
        if content_type == 'customer_facing' and word_lower in ['geo', 'g11n']:
            ev += 0.2  # Customer content should avoid abbreviations
        elif content_type == 'international' and word_lower == 'given name':
            ev -= 0.2  # "given name" is appropriate for international content
        
        return ev

    def _apply_feedback_clues_g_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for G-words."""
        patterns = self._get_cached_feedback_patterns_g_words()
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

    def _is_target_abbreviation_g_words(self, token, pattern: str) -> bool:
        """
        Check if a token flagged by entity recognition is actually our target abbreviation.
        """
        # For "geo" - if it's tagged as PRODUCT but is clearly the location abbreviation
        if pattern == 'geo':
            if token.text.lower() == 'geo':
                # Check if it's used in location context, not as a product name
                sent_text = token.sent.text.lower()
                location_indicators = ['location', 'area', 'region', 'position', 'coordinates']
                if any(indicator in sent_text for indicator in location_indicators):
                    return True
        
        # For "g11n" - this should be flagged if it's the abbreviation
        elif pattern == 'g11n':
            if token.text.lower() == 'g11n':
                return True
        
        # For "genai" - this should be flagged for capitalization
        elif pattern == 'genai':
            if token.text.lower() == 'genai':
                return True
        
        return False

    def _get_cached_feedback_patterns_g_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for G-words."""
        return {
            'often_flagged_terms': {'geo', 'genai', 'g11n', 'gage'},
            'accepted_terms': {'given name'},  # This is the preferred inclusive term
            'customer_facing_patterns': {
                'flagged': {'geo', 'g11n'},  # Avoid abbreviations in customer content
                'accepted': {'given name'}
            },
            'technical_patterns': {
                'flagged': {'genai', 'gage'},
                'accepted': {'go live'}  # In deployment contexts
            },
            'international_patterns': {
                'flagged': set(),
                'accepted': {'given name'}  # Preferred for global inclusivity
            },
            'procedure_patterns': {
                'flagged': {'go-live'},  # Prefer "go live" without hyphen
                'accepted': {'go live'}
            }
        }