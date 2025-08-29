"""
Word Usage Rule for words starting with 'Z' (Production-Grade)
Evidence-based analysis with surgical zero false positive guards for Z-word usage detection.
Based on IBM Style Guide recommendations with production-grade evidence calculation.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ZWordsRule(BaseWordUsageRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect usage of specific words starting with 'Z'.
    
    Implements evidence-based analysis with:
    - Surgical zero false positive guards for Z-word usage
    - Dynamic base evidence scoring based on word specificity and context
    - Context-aware adjustments for different writing domains
    
    Features:
    - Near 100% false positive elimination through surgical guards
    - Word-specific evidence calculation for each Z-word violation
    - Evidence-aware suggestions tailored to writing context
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_z'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for Z-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define Z-word patterns with evidence categories
        z_word_patterns = {
            # Verb form precision
            "zero out": {"alternatives": ["zero", "clear", "reset"], "category": "verb_form", "severity": "low"},
            
            # Environmental claims requiring substantiation
            "zero emissions": {"alternatives": ["(avoid unsubstantiated claims)", "reduced emissions", "low emissions"], "category": "environmental_claim", "severity": "high"},
            "zero carbon": {"alternatives": ["(avoid unsubstantiated claims)", "reduced carbon", "low carbon"], "category": "environmental_claim", "severity": "high"},
            "zero waste": {"alternatives": ["(avoid unsubstantiated claims)", "reduced waste", "minimal waste"], "category": "environmental_claim", "severity": "high"},
            
            # Trademark and generic terminology
            "zip": {"alternatives": ["compress", "archive", "package"], "category": "trademark", "severity": "high"},
            "ZIP file": {"alternatives": ["compressed file", "archive file"], "category": "trademark", "severity": "medium"},
            
            # Format consistency and hyphenation
            "zero-trust": {"alternatives": ["zero trust"], "category": "hyphenation", "severity": "low"},
            "zero-day": {"alternatives": ["zero day"], "category": "hyphenation", "severity": "low"},
            
            # Correct forms (should not be flagged in most contexts)
            "zero trust": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "zero day": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "zone": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "zoom": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
        }

        # Evidence-based analysis for Z-words using lemma-based matching and phrase detection
        
        # Track matched spans to avoid overlaps between single-word and multi-word patterns
        matched_spans = []
        
        # 1. Multi-word phrase detection for Z-words (process first to avoid conflicts)
        multi_word_patterns = {pattern: details for pattern, details in z_word_patterns.items() if (' ' in pattern or '-' in pattern) and details["category"] != "acceptable_usage"}
        
        if multi_word_patterns:
            # Sort patterns by length (longest first) to avoid overlapping matches
            sorted_patterns = sorted(multi_word_patterns.items(), key=lambda x: len(x[0]), reverse=True)
            
            # Use case-insensitive regex-based detection for multi-word Z phrases since lemma matching may fail
            for pattern, details in sorted_patterns:
                for match in re.finditer(r'\b' + re.escape(pattern) + r'\b', text, re.IGNORECASE):
                    char_start, char_end, matched_text = match.start(), match.end(), match.group(0)
                    
                    # Check for overlaps with already matched spans
                    overlap = any(char_start < end and char_end > start for start, end in matched_spans)
                    if overlap:
                        continue
                    
                    # Find the sentence and first token
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
                        # Apply surgical guards on the first token
                        if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                            continue
                        
                        evidence_score = self._calculate_z_word_evidence(
                            pattern, token, sent, text, context or {}, details["category"]
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
                                span=(char_start, char_end),
                                flagged_text=matched_text
                            ))
                            # Add to matched spans to prevent overlaps
                            matched_spans.append((char_start, char_end))
        
        # 2. Single-word matches
        for token in doc:
            token_text = token.text.lower()
            token_lemma = token.lemma_.lower()
            matched_pattern = None
            
            # Check single words (excluding multi-word patterns)
            for pattern in z_word_patterns:
                if ' ' not in pattern and '-' not in pattern:  # Single word pattern
                    # Exact text match or exact lemma match for single words
                    if pattern.lower() == token_text or pattern.lower() == token_lemma:
                        matched_pattern = pattern
                        break
            
            if matched_pattern:
                details = z_word_patterns[matched_pattern]
                
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
                
                # Check for overlap with already matched spans
                token_start, token_end = token.idx, token.idx + len(token.text)
                overlap = any(token_start < end and token_end > start for start, end in matched_spans)
                if overlap:
                    continue
                
                evidence_score = self._calculate_z_word_evidence(
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
                        span=(token_start, token_end),
                        flagged_text=token.text
                    ))
                    # Add to matched spans to prevent overlaps
                    matched_spans.append((token_start, token_end))
        
        return errors

    def _calculate_z_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for Z-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and violation type
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        - Special handling for environmental claims, trademark issues, and verb forms
        
        Args:
            word: The Z-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (environmental_claim, trademark, verb_form, hyphenation)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_z_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_z_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_z_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_z_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_z_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_z_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on Z-word category and violation specificity.
        Higher priority categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # Critical environmental claims requiring substantiation
        if category == 'environmental_claim':
            if word_lower in ['zero emissions', 'zero carbon']:
                return 0.9  # Unsubstantiated environmental claims are critical
            elif word_lower == 'zero waste':
                return 0.85  # Waste claims also critical but slightly less than emissions
            else:
                return 0.8  # Other environmental claims
        
        # Trademark and generic terminology issues
        elif category == 'trademark':
            if word_lower == 'zip':
                return 0.8  # Trademark genericization needs attention
            elif word_lower == 'zip file':
                return 0.75  # File context trademark issue
            else:
                return 0.7  # Other trademark issues
        
        # Verb form and precision issues
        elif category == 'verb_form':
            if word_lower == 'zero out':
                return 0.6  # Verb form style improvement
            else:
                return 0.55  # Other verb form issues
        
        # Hyphenation and format consistency
        elif category == 'hyphenation':
            if word_lower in ['zero-trust', 'zero-day']:
                return 0.5  # Format consistency for established terms
            else:
                return 0.45  # Other hyphenation issues
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_z_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply Z-word-specific linguistic clues using SpaCy analysis."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # === ENVIRONMENTAL CLAIMS CLUES ===
        if word_lower in ['zero emissions', 'zero carbon', 'zero waste']:
            # Marketing or promotional context
            if any(indicator in sent_text for indicator in ['achieve', 'reach', 'attain', 'deliver', 'promise']):
                ev += 0.3  # Achievement claims need substantiation
            elif any(indicator in sent_text for indicator in ['commitment', 'goal', 'target', 'plan']):
                ev += 0.2  # Future goals are less critical than current claims
            elif any(indicator in sent_text for indicator in ['working toward', 'striving for', 'aiming for']):
                ev -= 0.1  # Process language is more acceptable
            elif any(indicator in sent_text for indicator in ['environmental', 'sustainable', 'green', 'climate']):
                ev += 0.25  # Environmental context requires careful claims
        
        # === TRADEMARK CLUES ===
        if word_lower in ['zip', 'zip file']:
            # File operation context
            if any(indicator in sent_text for indicator in ['file', 'compress', 'archive', 'extract', 'decompress']):
                ev += 0.25  # File operation context needs generic terminology
            elif any(indicator in sent_text for indicator in ['format', 'type', 'extension']):
                ev += 0.2  # File format context benefits from generic terms
            elif any(indicator in sent_text for indicator in ['software', 'application', 'tool']):
                ev += 0.15  # Software context may use generic terms
        
        # === VERB FORM CLUES ===
        if word_lower == 'zero out':
            # Data operation context
            if any(indicator in sent_text for indicator in ['data', 'field', 'value', 'variable', 'register']):
                ev += 0.15  # Data context benefits from concise language
            elif any(indicator in sent_text for indicator in ['reset', 'clear', 'initialize']):
                ev += 0.1  # Similar operation context suggests precision need
        
        # === HYPHENATION CLUES ===
        if word_lower in ['zero-trust', 'zero-day']:
            # Security/technical context
            if any(indicator in sent_text for indicator in ['security', 'architecture', 'model', 'approach']):
                ev += 0.1  # Technical context benefits from standard formatting
            elif any(indicator in sent_text for indicator in ['vulnerability', 'exploit', 'attack']):
                ev += 0.1  # Security context needs consistent terminology
        
        return ev

    def _apply_structural_clues_z_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for Z-words."""
        block_type = context.get('block_type', 'paragraph')
        
        if block_type in ['step', 'procedure']:
            ev += 0.1  # Procedural content benefits from clear, precise language
        elif block_type == 'heading':
            ev += 0.05  # Headings benefit from professional terminology
        elif block_type in ['admonition', 'callout']:
            ev += 0.15  # Important callouts need accurate language
        elif block_type in ['table_cell', 'table_header']:
            ev += 0.05  # Tables benefit from concise professional language
        
        return ev

    def _apply_semantic_clues_z_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for Z-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        # Content type adjustments
        if content_type == 'marketing':
            if word_lower in ['zero emissions', 'zero carbon', 'zero waste']:
                ev += 0.4  # Marketing content must avoid unsubstantiated environmental claims
            elif word_lower in ['zip', 'zip file']:
                ev += 0.2  # Marketing content should use generic terminology
        
        elif content_type == 'legal':
            if word_lower in ['zero emissions', 'zero carbon', 'zero waste']:
                ev += 0.5  # Legal content requires substantiated claims
            elif word_lower in ['zip', 'zip file']:
                ev += 0.3  # Legal content needs trademark compliance
        
        elif content_type == 'customer_facing':
            if word_lower in ['zero emissions', 'zero carbon', 'zero waste']:
                ev += 0.3  # Customer content needs accurate claims
            elif word_lower in ['zip', 'zip file']:
                ev += 0.25  # Customer content benefits from generic terms
            elif word_lower == 'zero out':
                ev += 0.1  # Customer content benefits from clear language
        
        elif content_type == 'technical':
            if word_lower in ['zip', 'zip file']:
                ev += 0.2  # Technical docs benefit from generic terminology
            elif word_lower == 'zero out':
                ev += 0.05  # Technical context may allow concise terms
            elif word_lower in ['zero-trust', 'zero-day']:
                ev += 0.1  # Technical docs benefit from standard formatting
        
        elif content_type == 'environmental':
            if word_lower in ['zero emissions', 'zero carbon', 'zero waste']:
                ev += 0.6  # Environmental content must be extremely careful with claims
        
        # Audience adjustments
        if audience == 'external':
            if word_lower in ['zero emissions', 'zero carbon', 'zero waste']:
                ev += 0.3  # External audiences need substantiated claims
            elif word_lower in ['zip', 'zip file']:
                ev += 0.2  # External audiences benefit from generic terms
        
        elif audience == 'global':
            if word_lower in ['zip', 'zip file']:
                ev += 0.25  # Global audiences need universal terminology
            elif word_lower in ['zero emissions', 'zero carbon', 'zero waste']:
                ev += 0.2  # Global audiences need verified claims
        
        elif audience == 'regulatory':
            if word_lower in ['zero emissions', 'zero carbon', 'zero waste']:
                ev += 0.5  # Regulatory audiences require substantiated claims
        
        return ev

    def _apply_feedback_clues_z_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for Z-words."""
        patterns = self._get_cached_feedback_patterns_z_words()
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

    def _get_cached_feedback_patterns_z_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for Z-words."""
        return {
            'often_flagged_terms': {'zero emissions', 'zero carbon', 'zero waste', 'zip', 'zero out'},
            'accepted_terms': {'zero trust', 'zero day', 'zone', 'zoom'},  # Widely accepted Z terms
            'marketing_patterns': {
                'flagged': {'zero emissions', 'zero carbon', 'zero waste', 'zip'},  # Marketing needs verified claims
                'accepted': {'zone', 'zoom'}  # Some Z terms acceptable in marketing
            },
            'legal_patterns': {
                'flagged': {'zero emissions', 'zero carbon', 'zero waste', 'zip', 'zip file'},  # Legal needs accuracy
                'accepted': {'zero trust', 'zone'}  # Standard legal terms
            },
            'customer_facing_patterns': {
                'flagged': {'zero emissions', 'zero carbon', 'zero waste', 'zip', 'zero out'},  # Customer content needs clarity
                'accepted': {'zero trust', 'zero day', 'zone', 'zoom'}  # Customer-appropriate terms
            },
            'technical_patterns': {
                'flagged': {'zip', 'zero-trust', 'zero-day'},  # Technical docs need standard formatting
                'accepted': {'zero trust', 'zero day', 'zero out', 'zone', 'zoom'}  # Technical terms acceptable
            },
            'environmental_patterns': {
                'flagged': {'zero emissions', 'zero carbon', 'zero waste'},  # Environmental content needs verified claims
                'accepted': {'zone'}  # Environmental zones acceptable
            },
            'general_patterns': {
                'flagged': {'zero emissions', 'zero carbon', 'zip'},  # General content avoids questionable claims
                'accepted': {'zero trust', 'zero day', 'zone', 'zoom'}  # Common Z terms acceptable
            }
        }