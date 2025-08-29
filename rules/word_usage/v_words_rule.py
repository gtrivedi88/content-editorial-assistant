"""
Word Usage Rule for words starting with 'V' (Production-Grade)
Evidence-based analysis with surgical zero false positive guards for V-word usage detection.
Based on IBM Style Guide recommendations with production-grade evidence calculation.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class VWordsRule(BaseWordUsageRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect usage of specific words starting with 'V'.
    
    Implements evidence-based analysis with:
    - Surgical zero false positive guards for V-word usage
    - Dynamic base evidence scoring based on word specificity and context
    - Context-aware adjustments for different writing domains
    
    Features:
    - Near 100% false positive elimination through surgical guards
    - Word-specific evidence calculation for each V-word violation
    - Evidence-aware suggestions tailored to writing context
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_v'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for V-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define V-word patterns with evidence categories
        v_word_patterns = {
            "vanilla": {"alternatives": ["basic", "standard", "not customized"], "category": "jargon", "severity": "medium"},
            "Velcro": {"alternatives": ["hook-and-loop fastener"], "category": "trademark", "severity": "high"},
            "verbatim": {"alternatives": ["verbatim (adjective/adverb only)"], "category": "part_of_speech", "severity": "low"},
            "versus": {"alternatives": ["versus"], "category": "abbreviation", "severity": "medium"},
            "via": {"alternatives": ["by using", "through"], "category": "context_specific", "severity": "low"},
            "vice versa": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "vs": {"alternatives": ["versus"], "category": "abbreviation", "severity": "medium"},
            "vs.": {"alternatives": ["versus"], "category": "abbreviation", "severity": "medium"},
            "value": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "version": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "view": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "valid": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
        }

        # Evidence-based analysis for V-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches (including case-sensitive for trademarks)
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Special handling for case-sensitive patterns like "Velcro"
            for pattern in v_word_patterns:
                if ' ' not in pattern:  # Single word pattern
                    # Case-sensitive check for trademarks
                    if pattern == "Velcro" and token.text == "Velcro":
                        matched_pattern = pattern
                        break
                    # Case-insensitive check for other patterns
                    elif pattern != "Velcro" and (token_lemma == pattern.lower() or 
                                                  token_text == pattern.lower() or
                                                  token.text == pattern):  # Handle exact case matches like "vs."
                        matched_pattern = pattern
                        break
            
            if matched_pattern:
                details = v_word_patterns[matched_pattern]
                
                # Skip acceptable usage patterns
                if details["category"] == "acceptable_usage":
                    continue
                
                # Apply surgical guards with V-word specific overrides
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    # Check for V-word entity override (e.g., "Velcro" tagged as ORG)
                    if not self._is_target_v_word_override(token, matched_pattern, context or {}):
                        continue
                
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_v_word_evidence(
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

        # 2. Multi-word phrase detection for V-words
        multi_word_patterns = {pattern: details for pattern, details in v_word_patterns.items() if ' ' in pattern and details["category"] != "acceptable_usage"}
        
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
                
                evidence_score = self._calculate_v_word_evidence(
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

    def _calculate_v_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for V-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and violation type
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        - Special handling for trademark compliance and jargon clarity
        
        Args:
            word: The V-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (trademark, jargon, abbreviation, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_v_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_v_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_v_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_v_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_v_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    def _is_target_v_word_override(self, token, pattern: str, context: Dict[str, Any]) -> bool:
        """
        Check if this V-word should override surgical guard filtering.
        
        This handles cases where legitimate V-word violations are incorrectly
        tagged as entities by SpaCy but should still be flagged.
        
        Args:
            token: SpaCy token object
            pattern: The V-word pattern being checked
            context: Document context
            
        Returns:
            bool: True if this word should override surgical filtering, False otherwise
        """
        # Only apply override for specific V-words that are often tagged as entities
        # but should still be flagged as violations
        override_words = {
            'Velcro': 'trademark',  # Often tagged as ORG but is trademark violation
        }
        
        if pattern in override_words:
            # Check if the surgical guard filtering is ONLY due to entity detection
            if self._is_entity_only_filtering_v_words(token, context):
                return True  # Override the surgical guard for legitimate violations
        
        return False  # Don't override surgical guards
    
    def _is_entity_only_filtering_v_words(self, token, context: Dict[str, Any]) -> bool:
        """
        Check if surgical guard filtering is only due to entity detection.
        
        Returns True only if the ONLY reason for filtering is entity detection,
        not other higher-priority guards like code blocks or quoted content.
        """
        # Check if higher-priority guards would filter this
        block_type = context.get('block_type', 'paragraph')
        
        # Code blocks and technical content - these guards take precedence
        if block_type in ['code_block', 'inline_code', 'literal_block']:
            return False  # Code filtering takes precedence over entity override
        
        # URL-like content - takes precedence
        if hasattr(token, 'like_url') and token.like_url:
            return False  # URL filtering takes precedence
        
        # Path-like content - takes precedence
        if hasattr(token, 'text') and ('/' in token.text or '\\' in token.text):
            return False  # Path filtering takes precedence
        
        # CRITICAL: Check for quoted content - takes precedence over entity override
        # Look for quotes around this token's position in the sentence
        sentence_text = token.sent.text
        token_start = token.idx - token.sent.start_char
        token_end = token_start + len(token.text)
        
        # Check if token is within quotes
        if self._is_token_in_quotes(sentence_text, token_start, token_end):
            return False  # Quoted content filtering takes precedence over entity override
        
        # Check if part of organization name (e.g., "Vanilla Solutions Inc.")
        # Look for organization indicators around the token
        if hasattr(token, 'ent_type_') and token.ent_type_ == 'ORG':
            # Check if surrounded by other organizational terms
            sentence_lower = sentence_text.lower()
            org_indicators = ['inc.', 'inc', 'corp.', 'corp', 'corporation', 'company', 'ltd.', 'ltd', 'llc', 'solutions']
            if any(indicator in sentence_lower for indicator in org_indicators):
                return False  # Organization name filtering takes precedence
        
        # If we get here, check if entity detection is the only reason for filtering
        if hasattr(token, 'ent_type_') and token.ent_type_ in ['PERSON', 'ORG', 'PRODUCT', 'EVENT', 'GPE']:
            return True  # Entity filtering is the only reason, allow override
        
        return False  # Some other reason for filtering
    
    def _is_token_in_quotes(self, sentence_text: str, token_start: int, token_end: int) -> bool:
        """Check if token is within quotation marks."""
        # Look for quote pairs that enclose the token
        quote_chars = ['"', "'", '"', '"', ''', ''']
        
        for quote_char in quote_chars:
            # Find all quotes of this type
            quote_positions = [i for i, char in enumerate(sentence_text) if char == quote_char]
            
            # Check if token is within any quote pair
            for i in range(0, len(quote_positions) - 1, 2):
                if i + 1 < len(quote_positions):
                    quote_start = quote_positions[i]
                    quote_end = quote_positions[i + 1]
                    
                    if quote_start < token_start and token_end <= quote_end:
                        return True
        
        return False
    
    def _get_base_v_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on V-word category and violation specificity.
        Higher priority categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # Very high-risk trademark compliance issues
        if category == 'trademark':
            if word_lower == 'velcro':
                return 0.85  # Critical trademark compliance
            else:
                return 0.85  # Other trademark issues
        
        # High-risk clarity and professional communication issues
        elif category in ['jargon', 'abbreviation']:
            if word_lower == 'vanilla':
                return 0.7  # Technical jargon clarity important
            elif word_lower in ['versus', 'vs', 'vs.']:
                return 0.65  # Abbreviation consistency context-dependent
            else:
                return 0.7  # Other clarity issues
        
        # Medium-risk style and consistency issues
        elif category in ['part_of_speech', 'context_specific', 'format_consistency']:
            if word_lower == 'verbatim':
                return 0.5  # Part of speech usage context-dependent
            elif word_lower == 'via':
                return 0.45  # Context-specific appropriateness varies
            elif word_lower == 'vice versa':
                return 0.4  # Format consistency minor issue
            else:
                return 0.5  # Other style issues
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_v_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply V-word-specific linguistic clues using SpaCy analysis."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # === TRADEMARK COMPLIANCE CLUES ===
        if word_lower == 'velcro':
            # Material context needs generic terminology for legal compliance
            if any(indicator in sent_text for indicator in ['fastener', 'material', 'attach', 'closure']):
                ev += 0.25  # Strong trademark compliance need in product contexts
            elif any(indicator in sent_text for indicator in ['product', 'brand', 'company', 'manufacturer']):
                ev += 0.3  # Product/brand contexts especially need compliance
            elif any(indicator in sent_text for indicator in ['hook', 'loop', 'fabric', 'adhesive']):
                ev += 0.2  # Related material contexts benefit from generic terms
            elif any(indicator in sent_text for indicator in ['legal', 'trademark', 'patent']):
                ev += 0.35  # Legal contexts require precise terminology
        
        # === JARGON CLARITY CLUES ===
        if word_lower == 'vanilla':
            # Technical context needs clear language
            if any(indicator in sent_text for indicator in ['software', 'configuration', 'setup', 'installation']):
                ev += 0.2  # Technical jargon in software contexts
            elif any(indicator in sent_text for indicator in ['customer', 'user', 'client', 'audience']):
                ev += 0.15  # Customer-facing content needs accessible language
            elif any(indicator in sent_text for indicator in ['basic', 'standard', 'default', 'plain']):
                ev += 0.1  # Alternative clear terms present in context
            elif any(indicator in sent_text for indicator in ['documentation', 'guide', 'tutorial']):
                ev += 0.15  # Documentation benefits from clear terminology
        
        # === ABBREVIATION CONSISTENCY CLUES ===
        if word_lower in ['versus', 'vs', 'vs.']:
            # Comparison context benefits from spelled-out form
            if any(indicator in sent_text for indicator in ['comparison', 'compare', 'contrast', 'difference']):
                ev += 0.15  # Comparison contexts benefit from full form
            elif any(indicator in sent_text for indicator in ['formal', 'documentation', 'report']):
                ev += 0.1  # Formal contexts prefer spelled-out forms
            elif any(indicator in sent_text for indicator in ['technical', 'specification', 'standard']):
                ev += 0.05  # Technical contexts may prefer consistency
            # Check grammatical context for formality level
            if hasattr(token, 'head') and token.head.pos_ in ['NOUN', 'PROPN']:
                if any(word in token.head.text.lower() for word in ['analysis', 'study', 'evaluation']):
                    ev += 0.05  # Formal analysis contexts
        
        # === CONTEXT-SPECIFIC APPROPRIATENESS CLUES ===
        if word_lower == 'via':
            # Context-specific appropriateness varies
            if any(indicator in sent_text for indicator in ['network', 'routing', 'protocol', 'connection']):
                ev -= 0.15  # Technical routing context where "via" is appropriate
            elif any(indicator in sent_text for indicator in ['email', 'phone', 'contact', 'communication']):
                ev -= 0.1  # Communication methods context where "via" is common
            elif any(indicator in sent_text for indicator in ['customer', 'user', 'public', 'general']):
                ev += 0.1  # Customer-facing content benefits from clearer prepositions
            elif any(indicator in sent_text for indicator in ['formal', 'business', 'professional']):
                ev += 0.05  # Formal contexts may prefer more explicit language
        
        # === PART OF SPEECH USAGE CLUES ===
        if word_lower == 'verbatim':
            # Part of speech usage context-dependent
            if hasattr(token, 'pos_') and token.pos_ == 'NOUN':
                ev += 0.15  # "Verbatim" as noun is often incorrect (should be adjective/adverb)
            elif any(indicator in sent_text for indicator in ['copy', 'exact', 'word for word', 'precisely']):
                ev += 0.1  # Context suggests adverbial usage preferred
            elif any(indicator in sent_text for indicator in ['quote', 'citation', 'reference']):
                ev += 0.05  # Citation contexts often misuse as noun
        
        # === FORMAT CONSISTENCY CLUES ===
        if word_lower == 'vice versa':
            # Format consistency minor issue
            if any(indicator in sent_text for indicator in ['reverse', 'opposite', 'conversely']):
                ev += 0.05  # Alternative clear terms available
            elif any(indicator in sent_text for indicator in ['formal', 'academic', 'scholarly']):
                ev += 0.02  # Formal contexts may scrutinize format
        
        return ev

    def _apply_structural_clues_v_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for V-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_v_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for V-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'customer_facing' and word_lower in ['vanilla', 'velcro']:
            ev += 0.2  # Customer content needs clear, professional language
        elif content_type == 'legal' and word_lower == 'velcro':
            ev += 0.3  # Legal content must avoid trademark violations
        elif content_type == 'technical' and word_lower in ['vanilla', 'versus']:
            ev += 0.15  # Technical docs benefit from precise terminology
        
        if audience == 'external' and word_lower in ['vanilla', 'velcro']:
            ev += 0.2  # External audiences need clear, legally compliant language
        elif audience == 'global' and word_lower == 'vanilla':
            ev += 0.15  # Global audiences need clear, non-jargon language
        
        return ev

    def _apply_feedback_clues_v_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for V-words."""
        patterns = self._get_cached_feedback_patterns_v_words()
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
            ev -= 0.25  # Strong reduction for context-appropriate terms
        
        return ev

    def _get_cached_feedback_patterns_v_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for V-words."""
        return {
            'often_flagged_terms': {'vanilla', 'velcro', 'versus', 'vs', 'vs.'},
            'accepted_terms': {'value', 'version', 'view', 'valid', 'vice versa'},  # Generally acceptable terms
            'technical_patterns': {
                'flagged': {'vanilla', 'versus'},  # Technical docs need clear, non-jargon language
                'accepted': {'via', 'value', 'version', 'view', 'valid'}  # Technical terms acceptable in context
            },
            'customer_facing_patterns': {
                'flagged': {'vanilla', 'velcro', 'versus', 'vs', 'vs.'},  # Customer content needs clear, compliant language
                'accepted': {'value', 'version', 'view', 'valid'}  # Customer-friendly terms
            },
            'legal_patterns': {
                'flagged': {'velcro', 'vanilla'},  # Legal writing avoids trademark and jargon issues
                'accepted': {'versus', 'via', 'value', 'valid'}  # Legal terms acceptable
            },
            'formal_patterns': {
                'flagged': {'vanilla', 'vs', 'vs.'},  # Formal writing avoids jargon and abbreviations
                'accepted': {'versus', 'via', 'value', 'version', 'view', 'valid'}  # Formal terms acceptable
            },
            'marketing_patterns': {
                'flagged': {'velcro', 'vanilla', 'versus'},  # Marketing needs compliant, accessible language
                'accepted': {'value', 'version', 'view', 'valid'}  # Marketing-friendly terms
            },
            'tutorial_patterns': {
                'flagged': {'vanilla', 'versus', 'vs', 'vs.'},  # Tutorials need clear, accessible language
                'accepted': {'value', 'version', 'view', 'valid', 'via'}  # Tutorial-friendly terms
            },
            'academic_patterns': {
                'flagged': {'vanilla', 'vs', 'vs.'},  # Academic writing prefers formal, spelled-out terms
                'accepted': {'versus', 'via', 'value', 'version', 'view', 'valid', 'verbatim'}  # Academic terms
            },
            'general_patterns': {
                'flagged': {'vanilla', 'velcro', 'vs', 'vs.'},  # General content prefers clear language
                'accepted': {'value', 'version', 'view', 'valid', 'versus', 'via'}  # Common terms acceptable
            }
        }