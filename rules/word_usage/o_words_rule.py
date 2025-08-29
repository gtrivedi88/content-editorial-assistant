"""
Word Usage Rule for words starting with 'O'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class OWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'O'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_o'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for O-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define O-word patterns with evidence categories
        o_word_patterns = {
            "off of": {"alternatives": ["off", "from"], "category": "redundant_preposition", "severity": "medium"},
            "off-line": {"alternatives": ["offline"], "category": "hyphenation", "severity": "low"},
            "OK": {"alternatives": ["OK (UI only)", "acceptable"], "category": "context_specific", "severity": "medium"},
            "on-boarding": {"alternatives": ["onboarding"], "category": "hyphenation", "severity": "low"},
            "on premise": {"alternatives": ["on-premises", "on premises"], "category": "hyphenation", "severity": "medium"},
            "on the fly": {"alternatives": ["dynamically", "during processing"], "category": "jargon", "severity": "medium"},
            "orientate": {"alternatives": ["orient"], "category": "word_choice", "severity": "low"},
            "our": {"alternatives": ["the", "this"], "category": "perspective", "severity": "medium"},
            "out-of-the-box": {"alternatives": ["out of the box"], "category": "hyphenation", "severity": "low"},
            "online": {"alternatives": ["on the web"], "category": "acceptable_usage", "severity": "none"},
            "optional": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "over": {"alternatives": ["more than"], "category": "preposition_clarity", "severity": "low"},
        }

        # Evidence-based analysis for O-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Check single words (excluding multi-word patterns) - case-insensitive
            for pattern in o_word_patterns:
                if ' ' not in pattern:  # Single word pattern
                    if (token_lemma == pattern.lower() or 
                        token_text == pattern.lower() or
                        token.text == pattern):  # Handle case-sensitive patterns like "OK"
                        matched_pattern = pattern
                        break
            
            if matched_pattern:
                details = o_word_patterns[matched_pattern]
                
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
                
                evidence_score = self._calculate_o_word_evidence(
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

        # 2. Multi-word phrase detection for O-words
        multi_word_patterns = {pattern: details for pattern, details in o_word_patterns.items() if ' ' in pattern and details["category"] != "acceptable_usage"}
        
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
                
                evidence_score = self._calculate_o_word_evidence(
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

        # 3. Special handling for hyphenated patterns
        hyphenated_patterns = ['off-line', 'on-boarding', 'out-of-the-box']
        
        for pattern in hyphenated_patterns:
            if pattern in o_word_patterns:
                details = o_word_patterns[pattern]
                
                # Find hyphenated versions in text
                for i in range(len(doc)):
                    tokens_found = []
                    current_pos = i
                    
                    # Check for pattern like "off", "-", "line"
                    if pattern == 'off-line' and current_pos + 2 < len(doc):
                        if (doc[current_pos].text.lower() == 'off' and
                            doc[current_pos + 1].text == '-' and
                            doc[current_pos + 2].text.lower() == 'line'):
                            tokens_found = [doc[current_pos], doc[current_pos + 1], doc[current_pos + 2]]
                    
                    elif pattern == 'on-boarding' and current_pos + 2 < len(doc):
                        if (doc[current_pos].text.lower() == 'on' and
                            doc[current_pos + 1].text == '-' and
                            doc[current_pos + 2].text.lower() == 'boarding'):
                            tokens_found = [doc[current_pos], doc[current_pos + 1], doc[current_pos + 2]]
                    
                    elif pattern == 'out-of-the-box' and current_pos + 6 < len(doc):
                        if (doc[current_pos].text.lower() == 'out' and
                            doc[current_pos + 1].text == '-' and
                            doc[current_pos + 2].text.lower() == 'of' and
                            doc[current_pos + 3].text == '-' and
                            doc[current_pos + 4].text.lower() == 'the' and
                            doc[current_pos + 5].text == '-' and
                            doc[current_pos + 6].text.lower() == 'box'):
                            tokens_found = doc[current_pos:current_pos + 7]
                    
                    if tokens_found:
                        # Apply surgical guards on the first token
                        if self._apply_surgical_zero_false_positive_guards_word_usage(tokens_found[0], context or {}):
                            continue
                        
                        sent = tokens_found[0].sent
                        sentence_index = 0
                        for j, s in enumerate(doc.sents):
                            if s == sent:
                                sentence_index = j
                                break
                        
                        evidence_score = self._calculate_o_word_evidence(
                            pattern, tokens_found[0], sent, text, context or {}, details["category"]
                        )
                        
                        if evidence_score > 0.1:
                            start_char = tokens_found[0].idx
                            end_char = tokens_found[-1].idx + len(tokens_found[-1].text)
                            flagged_text = ''.join([t.text_with_ws for t in tokens_found]).strip()
                            
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=sentence_index,
                                message=self._generate_evidence_aware_word_usage_message(pattern, evidence_score, details["category"]),
                                suggestions=self._generate_evidence_aware_word_usage_suggestions(pattern, details["alternatives"], evidence_score, context or {}, details["category"]),
                                severity=details["severity"] if evidence_score < 0.7 else 'high',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=(start_char, end_char),
                                flagged_text=flagged_text
                            ))
        
        return errors

    def _calculate_o_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for O-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and violation type
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        
        Args:
            word: The O-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (redundant_preposition, jargon, perspective, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_o_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_o_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_o_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_o_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_o_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_o_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on O-word category and violation specificity.
        Higher priority categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # Very high-risk clarity and professionalism issues
        if category in ['redundant_preposition', 'jargon', 'perspective']:
            if word_lower == 'our':
                return 0.8  # Perspective issues critical for professional content
            elif word_lower == 'off of':
                return 0.75  # Redundant prepositions affect clarity
            elif word_lower == 'on the fly':
                return 0.7  # Jargon clarity for global audiences
            else:
                return 0.75  # Other clarity issues
        
        # High-risk context and consistency issues
        elif category in ['context_specific', 'hyphenation']:
            if word_lower == 'ok':
                return 0.6  # Context-dependent appropriateness
            elif word_lower in ['on premise', 'on-boarding']:
                return 0.65  # Hyphenation consistency important
            elif word_lower in ['off-line', 'out-of-the-box']:
                return 0.55  # Lower priority hyphenation
            else:
                return 0.6  # Other consistency issues
        
        # Medium-risk correctness and clarity issues
        elif category in ['word_choice', 'preposition_clarity']:
            if word_lower == 'orientate':
                return 0.5  # Word choice correctness
            elif word_lower == 'over':
                return 0.45  # Preposition clarity context-dependent
            else:
                return 0.5  # Other correctness issues
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_o_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply O-word-specific linguistic clues using SpaCy analysis."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # === PERSPECTIVE CLUES ===
        if word_lower == 'our':
            # Technical and professional contexts avoid first-person
            if any(indicator in sent_text for indicator in ['documentation', 'technical', 'guide', 'manual']):
                ev += 0.2  # Technical content should avoid first-person pronouns
            elif any(indicator in sent_text for indicator in ['procedure', 'instruction', 'step', 'process']):
                ev += 0.15  # Procedural content benefits from objective language
        
        # === JARGON CLUES ===
        if word_lower == 'on the fly':
            # Technical contexts need precise language
            if any(indicator in sent_text for indicator in ['process', 'generate', 'create', 'compute']):
                ev += 0.15  # Technical context needs precise language
            elif any(indicator in sent_text for indicator in ['dynamic', 'runtime', 'real-time']):
                ev += 0.1  # Performance context benefits from clarity
        
        # === CONTEXT-SPECIFIC CLUES ===
        if word_lower == 'ok':
            # UI context makes "OK" appropriate
            if any(indicator in sent_text for indicator in ['button', 'dialog', 'interface', 'click']):
                ev -= 0.3  # UI context makes "OK" appropriate
            elif any(indicator in sent_text for indicator in ['acceptable', 'valid', 'correct']):
                ev -= 0.2  # General acceptance context
        
        # === REDUNDANT PREPOSITION CLUES ===
        if word_lower == 'off of':
            # Action contexts benefit from precise prepositions
            if any(indicator in sent_text for indicator in ['remove', 'take', 'get', 'pull']):
                ev += 0.15  # Action context benefits from precise prepositions
            elif any(indicator in sent_text for indicator in ['download', 'copy', 'extract']):
                ev += 0.1  # Transfer context benefits from clarity
        
        # === HYPHENATION CLUES ===
        if word_lower in ['on premise', 'on-boarding', 'off-line', 'out-of-the-box']:
            # Technical documentation contexts
            if any(indicator in sent_text for indicator in ['deployment', 'installation', 'setup', 'configuration']):
                ev += 0.1  # Technical contexts prefer standard forms
        
        # === WORD CHOICE CLUES ===
        if word_lower == 'orientate':
            # Professional contexts prefer standard forms
            if any(indicator in sent_text for indicator in ['training', 'introduction', 'guide', 'familiarize']):
                ev += 0.1  # Professional context prefers "orient"
        
        # === PREPOSITION CLARITY CLUES ===
        if word_lower == 'over':
            # Numerical contexts benefit from precise prepositions
            if any(indicator in sent_text for indicator in ['than', 'number', 'count', 'amount']):
                ev += 0.1  # Numerical context benefits from "more than"
        
        return ev

    def _apply_structural_clues_o_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for O-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_o_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for O-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'technical' and word_lower in ['our', 'on the fly']:
            ev += 0.15  # Technical docs need objective, precise language
        elif content_type == 'tutorial' and word_lower in ['our', 'off of']:
            ev += 0.1  # Tutorials benefit from clear, professional language
        elif content_type == 'ui_documentation' and word_lower == 'ok':
            ev -= 0.2  # UI docs appropriately use "OK" for interface elements
        
        if audience == 'external' and word_lower == 'our':
            ev += 0.2  # External audiences need objective language
        elif audience == 'global' and word_lower == 'on the fly':
            ev += 0.15  # Global audiences need clear, non-idiomatic language
        
        return ev

    def _apply_feedback_clues_o_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for O-words."""
        patterns = self._get_cached_feedback_patterns_o_words()
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

    def _get_cached_feedback_patterns_o_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for O-words."""
        return {
            'often_flagged_terms': {'our', 'on the fly', 'off of', 'orientate', 'on premise'},
            'accepted_terms': set(),  # Context-dependent acceptance
            'technical_patterns': {
                'flagged': {'our', 'on the fly', 'off of', 'on premise', 'on-boarding'},  # Technical docs need precision
                'accepted': {'ok', 'over', 'orientate'}  # Technical terms sometimes acceptable
            },
            'ui_documentation_patterns': {
                'flagged': {'our', 'on the fly', 'off of'},  # UI docs need clear language
                'accepted': {'ok', 'on-boarding', 'online'}  # UI-specific terms
            },
            'tutorial_patterns': {
                'flagged': {'our', 'on the fly', 'off of', 'orientate'},  # Tutorials need clear instructions
                'accepted': {'ok', 'online', 'over'}  # Tutorial-friendly terms
            },
            'customer_facing_patterns': {
                'flagged': {'our', 'on the fly', 'off of', 'orientate', 'on premise'},  # Customer content needs clarity
                'accepted': {'ok', 'online', 'over'}  # Customer-friendly terms
            },
            'procedure_patterns': {
                'flagged': {'our', 'on the fly', 'off of'},  # Procedures need clear language
                'accepted': {'ok', 'on-boarding', 'online', 'over'}  # Procedural terms acceptable
            },
            'formal_patterns': {
                'flagged': {'our', 'on the fly', 'off of', 'ok', 'OK'},  # Formal writing prefers professional language
                'accepted': {'orientate', 'online', 'over'}  # Formal terms acceptable
            },
            'general_patterns': {
                'flagged': {'our', 'on the fly', 'off of'},  # General content prefers clear language
                'accepted': {'ok', 'online', 'over', 'orientate'}  # Common terms acceptable
            }
        }