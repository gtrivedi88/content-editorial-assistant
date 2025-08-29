"""
Word Usage Rule for words starting with 'X' (Production-Grade)
Evidence-based analysis with surgical zero false positive guards for X-word usage detection.
Based on IBM Style Guide recommendations with production-grade evidence calculation.
Preserves case-sensitive pattern detection for technical terms.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class XWordsRule(BaseWordUsageRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect usage of specific words starting with 'X'.
    
    Implements evidence-based analysis with:
    - Surgical zero false positive guards for X-word usage
    - Dynamic base evidence scoring based on word specificity and context
    - Context-aware adjustments for different writing domains
    - PRESERVED: Case-sensitive pattern detection for technical terms
    
    Features:
    - Near 100% false positive elimination through surgical guards
    - Word-specific evidence calculation for each X-word violation
    - Evidence-aware suggestions tailored to writing context
    - Case-sensitive technical term detection
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_x'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for X-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        
        PRESERVES: Case-sensitive pattern detection for technical terms.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define X-word patterns with evidence categories
        x_word_patterns = {
            # Technical abbreviations requiring clarification
            "XSA": {"alternatives": ["extended subarea addressing"], "category": "technical_abbreviation", "severity": "medium"},
            "XML": {"alternatives": ["eXtensible Markup Language"], "category": "technical_abbreviation", "severity": "low"},
            "XDR": {"alternatives": ["external data representation"], "category": "technical_abbreviation", "severity": "medium"},
            "XSLT": {"alternatives": ["XSL Transformations"], "category": "technical_abbreviation", "severity": "medium"},
            
            # Capitalization consistency
            "xterm": {"alternatives": ["XTerm"], "category": "capitalization", "severity": "low"},
            "xerox": {"alternatives": ["photocopy"], "category": "trademark_generic", "severity": "medium"},
            
            # Technical precision - note: case-sensitive phrase matching may be challenging
            # "X Window System": {"alternatives": ["X11", "X Window System"], "category": "technical_precision", "severity": "low"},
            "x86": {"alternatives": ["x86"], "category": "acceptable_usage", "severity": "none"},
            "x64": {"alternatives": ["x64"], "category": "acceptable_usage", "severity": "none"},
            
            # Correct forms (should not be flagged)
            "XTerm": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "X11": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "XPath": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "XQuery": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
        }

        # Evidence-based analysis for X-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches (case-sensitive for technical terms)
        for token in doc:
            # Check if token matches any of our target words
            token_text = token.text
            token_text_lower = token.text.lower()
            matched_pattern = None
            
            # Check single words (excluding multi-word patterns)
            for pattern in x_word_patterns:
                if ' ' not in pattern:  # Single word pattern
                    # Case-sensitive check for technical terms and abbreviations
                    if pattern.isupper() or pattern in ["xterm", "xerox"]:
                        if token_text == pattern:
                            matched_pattern = pattern
                            break
                    # Case-insensitive check for other patterns
                    else:
                        if token_text_lower == pattern.lower():
                            matched_pattern = pattern
                            break
            
            if matched_pattern:
                details = x_word_patterns[matched_pattern]
                
                # Skip acceptable usage patterns
                if details["category"] == "acceptable_usage":
                    continue
                
                # Apply surgical guards with entity override for technical abbreviations
                if self._is_target_x_word_override(matched_pattern, token, context or {}):
                    # Allow through if this is an entity-only filtering scenario for target X-words
                    pass  # Continue to evidence calculation
                elif self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue
                
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_x_word_evidence(
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

        # 2. Multi-word phrase detection for X-words
        multi_word_patterns = {pattern: details for pattern, details in x_word_patterns.items() if ' ' in pattern and details["category"] != "acceptable_usage"}
        
        if multi_word_patterns:
            phrase_matches = self._find_multi_word_phrases_with_lemma(doc, list(multi_word_patterns.keys()), case_sensitive=True)
            
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
                
                evidence_score = self._calculate_x_word_evidence(
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

    def _calculate_x_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for X-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and violation type
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        - Special handling for technical abbreviations and trademark terms
        
        Args:
            word: The X-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (technical_abbreviation, capitalization, trademark_generic, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_x_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_x_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_x_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_x_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_x_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_x_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on X-word category and violation specificity.
        Higher priority categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # High-risk technical abbreviations requiring clarification
        if category == 'technical_abbreviation':
            if word_lower in ['xsa', 'xdr', 'xslt']:
                return 0.75  # Specialized technical abbreviations need clarification
            elif word_lower == 'xml':
                return 0.6  # XML is more widely known
            else:
                return 0.7  # Other technical abbreviations
        
        # Trademark and generic use issues
        elif category == 'trademark_generic':
            if word_lower == 'xerox':
                return 0.8  # Trademark genericization needs attention
            else:
                return 0.75  # Other trademark issues
        
        # Capitalization consistency issues
        elif category == 'capitalization':
            if word_lower == 'xterm':
                return 0.5  # Capitalization consistency
            else:
                return 0.55  # Other capitalization issues
        
        # Technical precision issues
        elif category == 'technical_precision':
            return 0.4  # Lower priority for precision issues
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_x_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply X-word-specific linguistic clues using SpaCy analysis."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # === TECHNICAL ABBREVIATION CLUES ===
        if word_lower in ['xsa', 'xdr', 'xslt', 'xml']:
            # User-facing content needs clear terminology
            if any(indicator in sent_text for indicator in ['documentation', 'user', 'customer', 'guide', 'tutorial']):
                ev += 0.2  # User-facing content needs spelled-out terms
            elif any(indicator in sent_text for indicator in ['international', 'global', 'external']):
                ev += 0.15  # International content benefits from clarity
            elif any(indicator in sent_text for indicator in ['technical', 'specification', 'protocol']):
                ev -= 0.05  # Technical specs may allow abbreviations
        
        # === TRADEMARK CLUES ===
        if word_lower == 'xerox':
            # Generic usage context
            if any(indicator in sent_text for indicator in ['copy', 'photocopy', 'duplicate', 'scan']):
                ev += 0.25  # Generic usage needs correction
            elif any(indicator in sent_text for indicator in ['machine', 'device', 'equipment']):
                ev += 0.2  # Equipment context often generic usage
            elif any(indicator in sent_text for indicator in ['brand', 'company', 'corporation']):
                ev -= 0.3  # Proper brand usage acceptable
        
        # === CAPITALIZATION CLUES ===
        if word_lower == 'xterm':
            # Application context
            if any(indicator in sent_text for indicator in ['terminal', 'application', 'program', 'software']):
                ev += 0.15  # Application context needs consistent capitalization
            elif any(indicator in sent_text for indicator in ['command', 'run', 'execute', 'launch']):
                ev += 0.1  # Command context benefits from proper naming
        
        # === TECHNICAL PRECISION CLUES ===
        if 'x window system' in word_lower:
            # System/technical context
            if any(indicator in sent_text for indicator in ['system', 'display', 'graphics', 'server']):
                ev += 0.1  # Technical system context benefits from precision
        
        return ev

    def _apply_structural_clues_x_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for X-words."""
        block_type = context.get('block_type', 'paragraph')
        
        if block_type in ['step', 'procedure']:
            ev += 0.1  # Procedural content benefits from clear terminology
        elif block_type == 'heading':
            ev -= 0.1  # Headings may use abbreviated forms
        elif block_type in ['admonition', 'callout']:
            ev += 0.05  # Important callouts benefit from clear language
        elif block_type in ['table_cell', 'table_header']:
            ev -= 0.05  # Tables may use abbreviated forms
        
        return ev

    def _apply_semantic_clues_x_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for X-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        # Content type adjustments
        if content_type == 'customer_facing':
            if word_lower in ['xsa', 'xdr', 'xslt', 'xerox']:
                ev += 0.3  # Customer content needs clear, accessible language
            elif word_lower in ['xml', 'xterm']:
                ev += 0.15  # Even common terms benefit from clarity
        
        elif content_type == 'international':
            if word_lower in ['xsa', 'xdr', 'xslt', 'xerox']:
                ev += 0.25  # International content needs universal clarity
            elif word_lower in ['xml', 'xterm']:
                ev += 0.1  # Common terms still benefit from international clarity
        
        elif content_type == 'technical':
            if word_lower in ['xsa', 'xdr', 'xslt']:
                ev += 0.1  # Technical docs benefit from consistency
            elif word_lower in ['xml', 'xterm']:
                ev -= 0.05  # Common technical terms more acceptable
        
        elif content_type == 'legal':
            if word_lower == 'xerox':
                ev += 0.4  # Legal content must use proper generic terms
            elif word_lower in ['xsa', 'xdr', 'xslt']:
                ev += 0.2  # Legal docs need precise terminology
        
        elif content_type == 'ui_documentation':
            if word_lower == 'xterm':
                ev += 0.2  # UI docs benefit from consistent application naming
            elif word_lower in ['xml', 'xslt']:
                ev += 0.1  # UI context benefits from clarity
        
        # Audience adjustments
        if audience == 'external':
            if word_lower in ['xsa', 'xdr', 'xslt', 'xerox']:
                ev += 0.25  # External audiences need clear terminology
            elif word_lower in ['xml', 'xterm']:
                ev += 0.1  # Even known terms benefit from external clarity
        
        elif audience == 'global':
            if word_lower in ['xsa', 'xdr', 'xslt', 'xerox']:
                ev += 0.2  # Global audiences need universal language
            elif word_lower in ['xml', 'xterm']:
                ev += 0.05  # Global context benefits from consistency
        
        elif audience == 'beginner':
            if word_lower in ['xsa', 'xdr', 'xslt', 'xml']:
                ev += 0.15  # Beginners need spelled-out technical terms
            elif word_lower in ['xerox', 'xterm']:
                ev += 0.1  # Beginners benefit from clear terminology
        
        return ev

    def _apply_feedback_clues_x_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for X-words."""
        patterns = self._get_cached_feedback_patterns_x_words()
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

    def _get_cached_feedback_patterns_x_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for X-words."""
        return {
            'often_flagged_terms': {'xsa', 'xdr', 'xslt', 'xerox', 'xterm'},
            'accepted_terms': {'xml', 'xpath', 'xquery', 'x11', 'x86', 'x64'},  # Widely accepted technical terms
            'customer_facing_patterns': {
                'flagged': {'xsa', 'xdr', 'xslt', 'xerox', 'xterm'},  # Customer content needs clear language
                'accepted': {'xml', 'x11'}  # Some technical terms acceptable in customer context
            },
            'international_patterns': {
                'flagged': {'xsa', 'xdr', 'xslt', 'xerox'},  # International content needs universal clarity
                'accepted': {'xml', 'xpath', 'x86', 'x64'}  # Universal technical terms
            },
            'technical_patterns': {
                'flagged': {'xerox', 'xterm'},  # Technical docs need consistent terminology
                'accepted': {'xsa', 'xml', 'xdr', 'xslt', 'xpath', 'xquery', 'x11', 'x86', 'x64'}  # Technical terms acceptable
            },
            'legal_patterns': {
                'flagged': {'xerox', 'xsa', 'xdr'},  # Legal docs need precise language
                'accepted': {'xml', 'xslt', 'xpath'}  # Standard technical terms
            },
            'ui_documentation_patterns': {
                'flagged': {'xterm', 'xerox'},  # UI docs need consistent naming
                'accepted': {'xml', 'xslt', 'x11'}  # UI-related technical terms
            },
            'general_patterns': {
                'flagged': {'xsa', 'xerox', 'xterm'},  # General content avoids technical jargon
                'accepted': {'xml', 'x86', 'x64'}  # Common technical terms
            }
        }

    def _is_target_x_word_override(self, word: str, token, context: Dict[str, Any]) -> bool:
        """
        Smart Entity Override System for X-words.
        
        Allows specific X-word technical abbreviations to be flagged even when SpaCy 
        incorrectly tags them as entities, but only if they're not in higher-priority 
        filtered contexts (quotes, code, organization names, etc.).
        
        Returns True if this word should override entity filtering.
        """
        word_lower = word.lower()
        
        # Only apply entity override for X-words that are commonly misidentified as entities
        target_words = {'xsa', 'xdr', 'xml', 'xslt', 'xerox'}
        if word_lower not in target_words:
            return False
        
        # Check if token has entity type that would be filtered
        if not (hasattr(token, 'ent_type_') and token.ent_type_ in ['ORG', 'GPE', 'PERSON', 'PRODUCT', 'EVENT']):
            return False  # No entity filtering to override
        
        # Check if it's being filtered ONLY due to entity type, not other higher-priority guards
        if self._is_entity_only_filtering_x_words(token, context):
            return True  # Override entity filtering
        
        return False  # Other guards take priority
    
    def _is_entity_only_filtering_x_words(self, token, context: Dict[str, Any]) -> bool:
        """
        Check if the token would be filtered ONLY due to entity type, 
        not due to other higher-priority guards.
        
        Returns True if filtering is only due to entity type.
        """
        # === CHECK FOR HIGHER-PRIORITY GUARDS ===
        
        # GUARD 1: Code blocks and technical contexts
        if self._is_in_code_or_technical_context_words(token, context):
            return False  # Code filtering takes priority
        
        # GUARD 2: Quoted content
        if self._is_in_quoted_context_words(token, context):
            return False  # Quote filtering takes priority
        
        # GUARD 4: Technical specifications (allow override for some X-words)
        # Note: Technical specs may use abbreviations appropriately
        if self._is_technical_specification_words(token, context):
            # For X-words, technical specification context reduces evidence rather than filtering completely
            # Only filter if this is clearly a technical specification document
            content_type = context.get('content_type', '')
            audience = context.get('audience', '')
            if content_type == 'technical' and audience == 'expert':
                return False  # Technical spec filtering takes priority for expert technical content
            # Otherwise, allow override but evidence calculation will handle context
        
        # GUARD 5: Domain-appropriate usage
        if self._is_domain_appropriate_word_usage(token, context):
            return False  # Domain filtering takes priority
        
        # GUARD 6: URLs and file paths
        if hasattr(token, 'like_url') and token.like_url:
            return False  # URL filtering takes priority
        if hasattr(token, 'text'):
            text = token.text
            if (text.startswith('http') or 
                text.startswith('www.') or
                text.startswith('ftp://') or
                ('/' in text and len(text) > 3) or
                ('\\' in text and len(text) > 3)):
                return False  # Path filtering takes priority
        
        # GUARD 7: Foreign language
        if hasattr(token, 'lang_') and token.lang_ != 'en':
            return False  # Language filtering takes priority
        
        # If we get here, the only filtering would be due to entity type
        return True