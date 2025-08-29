"""
Word Usage Rule for words starting with 'U' (Production-Grade)
Evidence-based analysis with surgical zero false positive guards for U-word usage detection.
Based on IBM Style Guide recommendations with production-grade evidence calculation.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class UWordsRule(BaseWordUsageRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect usage of specific words starting with 'U'.
    
    Implements evidence-based analysis with:
    - Surgical zero false positive guards for U-word usage
    - Dynamic base evidence scoring based on word specificity and context
    - Context-aware adjustments for different writing domains
    
    Features:
    - Near 100% false positive elimination through surgical guards
    - Word-specific evidence calculation for each U-word violation
    - Evidence-aware suggestions tailored to writing context
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_u'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for U-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define U-word patterns with evidence categories
        u_word_patterns = {
            "un-": {"alternatives": ["un- (no hyphen)"], "category": "prefix_usage", "severity": "low"},
            "underbar": {"alternatives": ["underscore"], "category": "terminology", "severity": "medium"},
            "unselect": {"alternatives": ["clear", "deselect"], "category": "word_choice", "severity": "medium"},
            "up-to-date": {"alternatives": ["up to date"], "category": "hyphenation", "severity": "low"},
            "user-friendly": {"alternatives": ["(describe specific benefits)"], "category": "subjective_claim", "severity": "high"},
            "user name": {"alternatives": ["username"], "category": "spacing", "severity": "low"},
            "utilize": {"alternatives": ["use"], "category": "word_choice", "severity": "medium"},
            "update": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "user": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "under": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "unique": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
        }

        # Evidence-based analysis for U-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Check single words (excluding multi-word patterns) - case-insensitive
            for pattern in u_word_patterns:
                if ' ' not in pattern and '-' not in pattern:  # Single word pattern (no hyphens/spaces)
                    if (token_lemma == pattern.lower() or 
                        token_text == pattern.lower()):
                        matched_pattern = pattern
                        break
            
            if matched_pattern:
                details = u_word_patterns[matched_pattern]
                
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
                
                evidence_score = self._calculate_u_word_evidence(
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

        # 2. Multi-word phrase detection for U-words (including hyphenated words)
        multi_word_patterns = {pattern: details for pattern, details in u_word_patterns.items() if (' ' in pattern or '-' in pattern) and details["category"] != "acceptable_usage"}
        
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
                
                evidence_score = self._calculate_u_word_evidence(
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

        # 3. Special handling for "un-" prefix patterns
        # Look for words that start with "un-" and might be incorrectly hyphenated
        import re as regex_module
        for match in regex_module.finditer(r'\bun-\w+', text):
            char_start, char_end = match.start(), match.end()
            matched_text = match.group(0)

            # Find the corresponding token
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
                # Apply surgical guards
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue

                evidence_score = self._calculate_u_word_evidence("un-", token, sent, text, context or {}, "prefix_usage")

                if evidence_score > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_index,
                        message=self._generate_evidence_aware_word_usage_message("un-", evidence_score, "prefix_usage"),
                        suggestions=self._generate_evidence_aware_word_usage_suggestions("un-", ["un- (no hyphen)"], evidence_score, context or {}, "prefix_usage"),
                        severity='low' if evidence_score < 0.7 else 'medium',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(char_start, char_start + 3),  # Just the "un-" part
                        flagged_text="un-"
                    ))

        # 4. Special handling for hyphenated U-words
        # Handle patterns like "up-to-date", "user-friendly" that are tokenized as ["word", "-", "word"]
        hyphenated_patterns = {
            'up-to-date': {'alternatives': ['up to date'], 'category': 'hyphenation', 'severity': 'low'},
            'user-friendly': {'alternatives': ['(describe specific benefits)'], 'category': 'subjective_claim', 'severity': 'high'}
        }
        
        for i in range(len(doc) - 2):
            token1 = doc[i]
            hyphen = doc[i + 1]
            
            if hyphen.text == '-':
                # For multi-word hyphenated patterns like "up-to-date"
                if i + 4 < len(doc):
                    token2 = doc[i + 2]
                    hyphen2 = doc[i + 3]
                    token3 = doc[i + 4]
                    
                    if hyphen2.text == '-':
                        combined_text = f"{token1.text.lower()}-{token2.text.lower()}-{token3.text.lower()}"
                        
                        if combined_text in hyphenated_patterns:
                            details = hyphenated_patterns[combined_text]
                            
                            # Apply surgical guards on the first token
                            if self._apply_surgical_zero_false_positive_guards_word_usage(token1, context or {}):
                                continue
                            
                            sent = token1.sent
                            sentence_index = 0
                            for j, s in enumerate(doc.sents):
                                if s == sent:
                                    sentence_index = j
                                    break
                            
                            evidence_score = self._calculate_u_word_evidence(
                                combined_text, token1, sent, text, context or {}, details["category"]
                            )
                            
                            if evidence_score > 0.1:
                                errors.append(self._create_error(
                                    sentence=sent.text,
                                    sentence_index=sentence_index,
                                    message=self._generate_evidence_aware_word_usage_message(combined_text, evidence_score, details["category"]),
                                    suggestions=self._generate_evidence_aware_word_usage_suggestions(combined_text, details["alternatives"], evidence_score, context or {}, details["category"]),
                                    severity=details["severity"] if evidence_score < 0.7 else 'high',
                                    text=text,
                                    context=context,
                                    evidence_score=evidence_score,
                                    span=(token1.idx, token3.idx + len(token3.text)),
                                    flagged_text=f"{token1.text}-{token2.text}-{token3.text}"
                                ))
                
                # For two-word hyphenated patterns like "user-friendly"
                if i + 2 < len(doc):
                    token2 = doc[i + 2]
                    combined_text = f"{token1.text.lower()}-{token2.text.lower()}"
                    
                    if combined_text in hyphenated_patterns:
                        details = hyphenated_patterns[combined_text]
                        
                        # Apply surgical guards on the first token
                        if self._apply_surgical_zero_false_positive_guards_word_usage(token1, context or {}):
                            continue
                        
                        sent = token1.sent
                        sentence_index = 0
                        for j, s in enumerate(doc.sents):
                            if s == sent:
                                sentence_index = j
                                break
                        
                        evidence_score = self._calculate_u_word_evidence(
                            combined_text, token1, sent, text, context or {}, details["category"]
                        )
                        
                        if evidence_score > 0.1:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=sentence_index,
                                message=self._generate_evidence_aware_word_usage_message(combined_text, evidence_score, details["category"]),
                                suggestions=self._generate_evidence_aware_word_usage_suggestions(combined_text, details["alternatives"], evidence_score, context or {}, details["category"]),
                                severity=details["severity"] if evidence_score < 0.7 else 'high',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=(token1.idx, token2.idx + len(token2.text)),
                                flagged_text=f"{token1.text}-{token2.text}"
                            ))
        
        return errors

    def _calculate_u_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for U-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and violation type
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        - Special handling for subjective claims and terminology precision
        
        Args:
            word: The U-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (subjective_claim, terminology, word_choice, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_u_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_u_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_u_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_u_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_u_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_u_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on U-word category and violation specificity.
        Higher priority categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # Very high-risk subjective claims
        if category == 'subjective_claim':
            if word_lower == 'user-friendly':
                return 0.8  # Critical subjective marketing language
            else:
                return 0.8  # Other subjective claims
        
        # High-risk terminology and word choice issues
        elif category in ['terminology', 'word_choice']:
            if word_lower == 'utilize':
                return 0.7  # Formal language clarity important
            elif word_lower == 'underbar':
                return 0.75  # Technical terminology precision
            elif word_lower == 'unselect':
                return 0.65  # UI terminology clarity
            else:
                return 0.7  # Other precision issues
        
        # Lower-risk consistency issues
        elif category in ['spacing', 'hyphenation', 'prefix_usage']:
            if word_lower == 'user name':
                return 0.5  # Spacing consistency
            elif word_lower == 'up-to-date':
                return 0.45  # Hyphenation consistency context-dependent
            elif word_lower == 'un-':
                return 0.4  # Prefix hyphenation context-dependent
            else:
                return 0.5  # Other consistency issues
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_u_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply U-word-specific linguistic clues using SpaCy analysis."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # === SUBJECTIVE CLAIM CLUES ===
        if word_lower == 'user-friendly':
            # Interface context needs objective descriptions
            if any(indicator in sent_text for indicator in ['interface', 'design', 'feature', 'ui']):
                ev += 0.25  # Strong need for objective language in interface contexts
            elif any(indicator in sent_text for indicator in ['customer', 'client', 'user', 'audience']):
                ev += 0.2  # Customer contexts benefit from specific descriptions
            elif any(indicator in sent_text for indicator in ['easy', 'simple', 'intuitive', 'convenient']):
                ev += 0.15  # Other subjective terms compound the issue
            elif any(indicator in sent_text for indicator in ['marketing', 'promotion', 'advertising']):
                ev += 0.3  # Marketing contexts especially need objective language
        
        # === WORD CHOICE CLUES ===
        if word_lower == 'utilize':
            # Formal context benefits from simpler language
            if any(indicator in sent_text for indicator in ['documentation', 'formal', 'technical', 'procedure']):
                ev += 0.2  # Formal contexts benefit from plain language
            elif any(indicator in sent_text for indicator in ['customer', 'user', 'guide', 'instruction']):
                ev += 0.15  # User-facing content benefits from simple language
            elif any(indicator in sent_text for indicator in ['international', 'global', 'worldwide']):
                ev += 0.1  # International contexts benefit from common words
            # Check grammatical context for overformality
            if hasattr(token, 'head') and token.head.pos_ in ['AUX', 'VERB']:
                if token.head.lemma_.lower() in ['should', 'must', 'can', 'will']:
                    ev += 0.05  # Modal context suggests simpler alternatives work
        
        # === TERMINOLOGY CLUES ===
        if word_lower == 'underbar':
            # Technical context needs standard terminology
            if any(indicator in sent_text for indicator in ['character', 'symbol', 'programming', 'code']):
                ev += 0.15  # Programming contexts use "underscore" as standard
            elif any(indicator in sent_text for indicator in ['documentation', 'guide', 'tutorial']):
                ev += 0.1  # Documentation benefits from standard terminology
            elif any(indicator in sent_text for indicator in ['user', 'beginner', 'learn']):
                ev += 0.05  # User education benefits from standard terms
        
        if word_lower == 'unselect':
            # UI context benefits from standard terms
            if any(indicator in sent_text for indicator in ['checkbox', 'option', 'ui', 'interface']):
                ev += 0.15  # UI contexts have established terminology
            elif any(indicator in sent_text for indicator in ['deselect', 'clear', 'remove']):
                ev += 0.1  # Standard alternatives present in context
            elif any(indicator in sent_text for indicator in ['user', 'click', 'tap']):
                ev += 0.05  # User action contexts benefit from standard terms
        
        # === PREFIX USAGE CLUES ===
        if word_lower == 'un-':
            # Prefix hyphenation context
            if any(indicator in sent_text for indicator in ['prefix', 'compound', 'word']):
                ev += 0.1  # Linguistic contexts discuss proper prefix usage
            elif any(indicator in sent_text for indicator in ['style', 'format', 'writing']):
                ev += 0.05  # Style guides discuss hyphenation rules
        
        # === SPACING AND HYPHENATION CLUES ===
        if word_lower == 'user name':
            # Spacing consistency
            if any(indicator in sent_text for indicator in ['field', 'form', 'input', 'login']):
                ev += 0.1  # Form contexts benefit from consistent terminology
            elif any(indicator in sent_text for indicator in ['system', 'account', 'profile']):
                ev += 0.05  # System contexts use standard terms
        
        if word_lower == 'up-to-date':
            # Hyphenation context-dependency
            if any(indicator in sent_text for indicator in ['information', 'data', 'content', 'version']):
                ev += 0.05  # Content freshness contexts may vary in hyphenation preference
            elif any(indicator in sent_text for indicator in ['current', 'latest', 'recent']):
                ev += 0.02  # Temporal contexts may have style preferences
        
        return ev

    def _apply_structural_clues_u_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for U-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_u_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for U-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'customer_facing' and word_lower == 'user-friendly':
            ev += 0.3  # Customer content needs objective descriptions
        elif content_type == 'technical' and word_lower in ['underbar', 'utilize']:
            ev += 0.15  # Technical docs benefit from precise, simple language
        elif content_type == 'tutorial' and word_lower in ['unselect', 'utilize']:
            ev += 0.1  # Tutorials benefit from clear, standard terminology
        
        if audience == 'external' and word_lower == 'user-friendly':
            ev += 0.2  # External audiences need objective language
        elif audience == 'global' and word_lower == 'utilize':
            ev += 0.15  # Global audiences benefit from simpler language
        
        return ev

    def _apply_feedback_clues_u_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for U-words."""
        patterns = self._get_cached_feedback_patterns_u_words()
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

    def _get_cached_feedback_patterns_u_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for U-words."""
        return {
            'often_flagged_terms': {'user-friendly', 'utilize', 'underbar', 'unselect'},
            'accepted_terms': {'update', 'user', 'under', 'unique', 'up'},  # Generally acceptable terms
            'technical_patterns': {
                'flagged': {'user-friendly', 'utilize'},  # Technical docs need objective, simple language
                'accepted': {'underbar', 'unselect', 'user', 'update', 'unique'}  # Technical terms acceptable in context
            },
            'customer_facing_patterns': {
                'flagged': {'user-friendly', 'utilize', 'underbar', 'unselect'},  # Customer content needs clear language
                'accepted': {'user', 'update', 'unique', 'under'}  # Customer-friendly terms
            },
            'ui_documentation_patterns': {
                'flagged': {'user-friendly', 'unselect', 'underbar'},  # UI docs need standard terminology
                'accepted': {'user', 'update', 'unique', 'utilize'}  # UI context terms
            },
            'formal_patterns': {
                'flagged': {'user-friendly', 'unselect'},  # Formal writing avoids subjective and non-standard terms
                'accepted': {'utilize', 'unique', 'update', 'user'}  # Formal terms acceptable
            },
            'marketing_patterns': {
                'flagged': {'user-friendly', 'utilize'},  # Marketing needs objective, accessible language
                'accepted': {'user', 'update', 'unique', 'under'}  # Marketing-friendly terms
            },
            'tutorial_patterns': {
                'flagged': {'utilize', 'underbar', 'unselect'},  # Tutorials need clear, standard language
                'accepted': {'user', 'update', 'unique', 'under'}  # Tutorial-friendly terms
            },
            'general_patterns': {
                'flagged': {'user-friendly', 'utilize', 'underbar'},  # General content prefers clear language
                'accepted': {'user', 'update', 'unique', 'under', 'unselect'}  # Common terms acceptable
            }
        }