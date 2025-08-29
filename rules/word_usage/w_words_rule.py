"""
Word Usage Rule for words starting with 'W' (Production-Grade)
Evidence-based analysis with surgical zero false positive guards for W-word usage detection.
Based on IBM Style Guide recommendations with production-grade evidence calculation.
Preserves sophisticated morphological analysis for 'while' semantic detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class WWordsRule(BaseWordUsageRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect usage of specific words starting with 'W'.
    
    Implements evidence-based analysis with:
    - Surgical zero false positive guards for W-word usage
    - Dynamic base evidence scoring based on word specificity and context
    - Context-aware adjustments for different writing domains
    - PRESERVED: Advanced morphological analysis for 'while' semantic detection
    
    Features:
    - Near 100% false positive elimination through surgical guards
    - Word-specific evidence calculation for each W-word violation
    - Evidence-aware suggestions tailored to writing context
    - Sophisticated dependency parsing and morphology for 'while' context
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_w'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for W-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        
        PRESERVES: Advanced morphological analysis for 'while' semantic detection.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define W-word patterns with evidence categories
        w_word_patterns = {
            "w/": {"alternatives": ["with"], "category": "abbreviation", "severity": "medium"},
            "war room": {"alternatives": ["command center", "operations center"], "category": "inclusive_language", "severity": "high"},
            "web site": {"alternatives": ["website"], "category": "spacing", "severity": "low"},
            "whitelist": {"alternatives": ["allowlist"], "category": "inclusive_language", "severity": "high"},
            "Wi-Fi": {"alternatives": ["Wi-Fi (certified)", "wifi (generic)"], "category": "technical_precision", "severity": "low"},
            "work station": {"alternatives": ["workstation"], "category": "spacing", "severity": "low"},
            "world-wide": {"alternatives": ["worldwide"], "category": "hyphenation", "severity": "low"},
            "while": {"alternatives": ["although", "whereas"], "category": "semantic_precision", "severity": "medium"},
            "with": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "website": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "workstation": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "worldwide": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
        }

        # Evidence-based analysis for W-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches (excluding the advanced "while" analysis)
        for token in doc:
            # Skip "while" - it gets special advanced processing below
            if token.lemma_.lower() == "while":
                continue
                
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Check single words (excluding multi-word patterns)
            for pattern in w_word_patterns:
                if ' ' not in pattern and pattern != "world-wide":  # Single word pattern (exclude hyphenated "world-wide")
                    # Case-sensitive check for patterns like "Wi-Fi"
                    if pattern == "Wi-Fi" and token.text == "Wi-Fi":
                        matched_pattern = pattern
                        break
                    # Special handling for "w/" which may have different tokenization
                    elif pattern == "w/" and (token.text == "w/" or 
                                              (token.text.lower() == "w" and token.nbor(1).text == "/" if token.i < len(doc) - 1 else False)):
                        matched_pattern = pattern
                        break
                    # Case-insensitive check for other patterns
                    elif pattern not in ["Wi-Fi", "w/"] and (token_lemma == pattern.lower() or token_text == pattern.lower()):
                        matched_pattern = pattern
                        break
            
            if matched_pattern:
                details = w_word_patterns[matched_pattern]
                
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
                
                evidence_score = self._calculate_w_word_evidence(
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

        # 2. Multi-word phrase detection for W-words
        multi_word_patterns = {pattern: details for pattern, details in w_word_patterns.items() if ' ' in pattern and details["category"] != "acceptable_usage"}
        
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
                
                evidence_score = self._calculate_w_word_evidence(
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

        # 2b. Special handling for hyphenated words like "world-wide"
        # SpaCy often tokenizes "world-wide" as ["world", "-", "wide"]
        for i, token in enumerate(doc):
            if (token.text.lower() == "world" and 
                i + 2 < len(doc) and 
                doc[i + 1].text == "-" and 
                doc[i + 2].text.lower() == "wide"):
                
                # Found "world-wide" pattern
                pattern = "world-wide"
                details = w_word_patterns[pattern]
                
                # Apply surgical guards
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue
                
                sent = token.sent
                sentence_index = 0
                for j, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = j
                        break
                
                evidence_score = self._calculate_w_word_evidence(
                    pattern, token, sent, text, context or {}, details["category"]
                )
                
                if evidence_score > 0.1:
                    # Calculate span for the full "world-wide" phrase
                    start_char = token.idx
                    end_char = doc[i + 2].idx + len(doc[i + 2].text)
                    flagged_text = text[start_char:end_char]
                    
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



        # 3. PRESERVE EXISTING ADVANCED FUNCTIONALITY: Enhanced context-aware morphological analysis for 'while'
        # This sophisticated linguistic analysis uses dependency parsing and morphology to determine semantic usage
        for token in doc:
            if token.lemma_.lower() == "while":
                sent = token.sent
                sent_text = sent.text.lower()
                
                # Get the sentence index by finding the sentence in the doc.sents
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                # Apply surgical guards for dependency detection
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue
                
                # Enhanced heuristics to determine temporal vs contrast usage
                is_temporal = False
                is_contrast = False
                
                # Check for temporal indicators
                temporal_indicators = ['accessing', 'configuring', 'maintaining', 'running', 'processing', 'loading', 'waiting']
                if any(indicator in sent_text for indicator in temporal_indicators):
                    is_temporal = True
                
                # Check for contrast indicators
                contrast_indicators = ['different', 'prefer', 'however', 'but', 'instead', 'although', 'whereas', 'comparison']
                if any(indicator in sent_text for indicator in contrast_indicators):
                    is_contrast = True
                
                # Advanced dependency analysis
                if hasattr(token, 'head') and token.head:
                    # Look for progressive verbs (temporal usage)
                    for child in token.head.children:
                        if child.pos_ == "VERB" and ("ing" in str(child.morph) or child.tag_ == "VBG"):
                            is_temporal = True
                        # Look for comparative structures (contrast usage)
                        elif child.dep_ in ["acomp", "attr"] or child.pos_ == "ADJ":
                            is_contrast = True
                
                # Only flag if it's clearly contrast usage and not temporal
                if is_contrast and not is_temporal:
                    evidence_score = self._calculate_w_word_evidence("while", token, sent, text, context or {}, "semantic_precision")
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message("while", evidence_score, "semantic_precision"),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions("while", ["although", "whereas"], evidence_score, context or {}, "semantic_precision"),
                            severity='medium' if evidence_score < 0.7 else 'high',
                            text=text, context=context, evidence_score=evidence_score,
                            span=(token.idx, token.idx + len(token.text)), flagged_text="while"  # Normalize to lowercase for consistency
                        ))
        
        return errors

    def _calculate_w_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for W-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and violation type
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        - Special handling for inclusive language and semantic precision
        
        Args:
            word: The W-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (inclusive_language, abbreviation, semantic_precision, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_w_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_w_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_w_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_w_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_w_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_w_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on W-word category and violation specificity.
        Higher priority categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # Very high-risk inclusive language issues
        if category == 'inclusive_language':
            if word_lower == 'whitelist':
                return 0.85  # Critical inclusive terminology replacement
            elif word_lower == 'war room':
                return 0.8  # Military terminology in business contexts
            else:
                return 0.85  # Other inclusive language issues
        
        # High-risk clarity and precision issues
        elif category in ['abbreviation', 'semantic_precision']:
            if word_lower == 'while':
                return 0.7  # Semantic precision important for clarity
            elif word_lower == 'w/':
                return 0.75  # Abbreviation professionalism
            else:
                return 0.75  # Other clarity issues
        
        # Medium-risk technical precision issues
        elif category == 'technical_precision':
            if word_lower == 'wi-fi':
                return 0.55  # Technical accuracy context-dependent
            else:
                return 0.6  # Other technical precision issues
        
        # Lower risk consistency issues
        elif category in ['spacing', 'hyphenation']:
            if word_lower == 'web site':
                return 0.5  # Spacing consistency
            elif word_lower == 'work station':
                return 0.45  # Spacing consistency
            elif word_lower == 'world-wide':
                return 0.4  # Hyphenation consistency
            else:
                return 0.5  # Other consistency issues
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_w_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply W-word-specific linguistic clues using SpaCy analysis."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # === INCLUSIVE LANGUAGE CLUES ===
        if word_lower in ['war room', 'whitelist']:
            # Team/customer context needs inclusive language
            if any(indicator in sent_text for indicator in ['team', 'customer', 'global', 'international']):
                ev += 0.3  # Strong need for inclusive language in team/customer contexts
            elif any(indicator in sent_text for indicator in ['business', 'strategy', 'meeting', 'collaboration']):
                ev += 0.25  # Business contexts benefit from inclusive terminology
            elif any(indicator in sent_text for indicator in ['external', 'public', 'community']):
                ev += 0.35  # Public-facing content especially needs inclusive language
            elif any(indicator in sent_text for indicator in ['security', 'access', 'control', 'permission']):
                ev += 0.2  # Security contexts should use modern inclusive terminology
        
        # === SEMANTIC PRECISION CLUES ===
        if word_lower == 'while':
            # Context analysis for temporal vs contrast usage
            if any(indicator in sent_text for indicator in ['contrast', 'however', 'although', 'but', 'whereas']):
                ev += 0.25  # Strong contrast context suggests non-temporal usage
            elif any(indicator in sent_text for indicator in ['difference', 'comparison', 'unlike', 'instead']):
                ev += 0.2  # Comparison context suggests contrast rather than time
            elif any(indicator in sent_text for indicator in ['simultaneously', 'same time', 'concurrent']):
                ev -= 0.1  # Temporal indicators suggest correct usage
            # Check grammatical context using dependency parsing
            if hasattr(token, 'head') and token.head.pos_ in ['VERB']:
                if any(child.pos_ == 'VERB' for child in token.head.children):
                    ev += 0.1  # Multiple verbs suggest contrast rather than time
        
        # === ABBREVIATION CLARITY CLUES ===
        if word_lower == 'w/':
            # Formal context needs spelled-out words
            if any(indicator in sent_text for indicator in ['documentation', 'formal', 'technical', 'professional']):
                ev += 0.2  # Formal contexts need professional language
            elif any(indicator in sent_text for indicator in ['customer', 'client', 'external', 'public']):
                ev += 0.15  # Customer-facing content benefits from clarity
            elif any(indicator in sent_text for indicator in ['international', 'global', 'worldwide']):
                ev += 0.1  # International contexts benefit from spelled-out words
        
        # === TECHNICAL PRECISION CLUES ===
        if word_lower == 'wi-fi':
            # Technical context needs precision
            if any(indicator in sent_text for indicator in ['certified', 'standard', 'specification', 'protocol']):
                ev += 0.15  # Technical standards context needs precision
            elif any(indicator in sent_text for indicator in ['generic', 'wireless', 'network', 'connectivity']):
                ev -= 0.1  # Generic wireless context may allow casual usage
            elif any(indicator in sent_text for indicator in ['brand', 'trademark', 'alliance']):
                ev += 0.1  # Brand/trademark context benefits from accuracy
        
        # === SPACING AND HYPHENATION CLUES ===
        if word_lower == 'web site':
            # Web context analysis
            if any(indicator in sent_text for indicator in ['modern', 'current', 'standard', 'convention']):
                ev += 0.1  # Modern web standards prefer "website"
            elif any(indicator in sent_text for indicator in ['url', 'domain', 'online', 'internet']):
                ev += 0.05  # Web contexts benefit from standard terminology
        
        if word_lower == 'work station':
            # Computing context analysis
            if any(indicator in sent_text for indicator in ['computer', 'desktop', 'hardware', 'system']):
                ev += 0.1  # Computing contexts prefer "workstation"
            elif any(indicator in sent_text for indicator in ['technical', 'specification', 'manual']):
                ev += 0.05  # Technical documentation benefits from standard terms
        
        if word_lower == 'world-wide':
            # Global context analysis
            if any(indicator in sent_text for indicator in ['web', 'internet', 'global', 'international']):
                ev += 0.1  # Web/global contexts prefer "worldwide"
            elif any(indicator in sent_text for indicator in ['modern', 'current', 'standard']):
                ev += 0.05  # Modern usage prefers un-hyphenated form
        
        return ev

    def _apply_structural_clues_w_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for W-words."""
        block_type = context.get('block_type', 'paragraph')
        
        if block_type in ['step', 'procedure']:
            ev += 0.1  # Procedural content benefits from clear, inclusive language
        elif block_type == 'heading':
            ev -= 0.1  # Headings may be more informal
        elif block_type in ['admonition', 'callout']:
            ev += 0.05  # Important callouts benefit from precise language
        elif block_type in ['table_cell', 'table_header']:
            ev -= 0.05  # Tables may use abbreviated forms
        
        return ev

    def _apply_semantic_clues_w_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for W-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        # Content type adjustments
        if content_type == 'customer_facing':
            if word_lower in ['war room', 'whitelist']:
                ev += 0.35  # Customer content must use inclusive language
            elif word_lower == 'w/':
                ev += 0.25  # Customer content needs professional clarity
            elif word_lower in ['web site', 'work station']:
                ev += 0.15  # Customer content benefits from modern terminology
        
        elif content_type == 'international':
            if word_lower in ['war room', 'whitelist']:
                ev += 0.3  # International content requires inclusive language
            elif word_lower == 'w/':
                ev += 0.2  # International content needs spelled-out clarity
            elif word_lower == 'while':
                ev += 0.1  # International content benefits from precise semantic usage
        
        elif content_type == 'technical':
            if word_lower in ['w/', 'wi-fi']:
                ev += 0.15  # Technical docs need precision and professionalism
            elif word_lower in ['web site', 'work station', 'world-wide']:
                ev += 0.1  # Technical docs benefit from standard terminology
        
        elif content_type == 'legal':
            if word_lower in ['war room', 'whitelist']:
                ev += 0.4  # Legal content must use inclusive, professional language
            elif word_lower == 'while':
                ev += 0.2  # Legal content needs semantic precision
            elif word_lower == 'w/':
                ev += 0.3  # Legal content requires formal language
        
        elif content_type == 'ui_documentation':
            if word_lower in ['web site', 'work station']:
                ev += 0.2  # UI docs benefit from modern, standard terminology
            elif word_lower == 'wi-fi':
                ev += 0.1  # UI docs benefit from technical accuracy
        
        # Audience adjustments
        if audience == 'external':
            if word_lower in ['war room', 'whitelist']:
                ev += 0.35  # External audiences need inclusive terminology
            elif word_lower == 'w/':
                ev += 0.2  # External audiences benefit from professional clarity
        
        elif audience == 'global':
            if word_lower in ['war room', 'whitelist']:
                ev += 0.25  # Global audiences need inclusive language
            elif word_lower in ['w/', 'while']:
                ev += 0.15  # Global audiences need clear, precise language
            elif word_lower in ['web site', 'work station', 'world-wide']:
                ev += 0.1  # Global audiences benefit from standard terminology
        
        elif audience == 'beginner':
            if word_lower in ['w/', 'while']:
                ev += 0.1  # Beginners benefit from clear, unambiguous language
            elif word_lower == 'wi-fi':
                ev -= 0.05  # Beginners may accept common casual terms
        
        return ev

    def _apply_feedback_clues_w_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for W-words."""
        patterns = self._get_cached_feedback_patterns_w_words()
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

    def _get_cached_feedback_patterns_w_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for W-words."""
        return {
            'often_flagged_terms': {'war room', 'whitelist', 'w/', 'web site', 'work station'},
            'accepted_terms': {'with', 'website', 'workstation', 'worldwide'},  # Correct forms
            'customer_facing_patterns': {
                'flagged': {'war room', 'whitelist', 'w/', 'web site'},  # Customer content needs inclusive, professional language
                'accepted': {'website', 'with', 'workstation'}  # Modern, clear terms
            },
            'international_patterns': {
                'flagged': {'war room', 'whitelist', 'w/', 'while'},  # International content needs inclusive, clear language
                'accepted': {'with', 'website', 'worldwide'}  # Clear, standard terms
            },
            'technical_patterns': {
                'flagged': {'w/', 'web site', 'work station', 'world-wide'},  # Technical docs need standard terminology
                'accepted': {'wi-fi', 'website', 'workstation', 'worldwide'}  # Technical terms and standard forms
            },
            'legal_patterns': {
                'flagged': {'war room', 'whitelist', 'w/', 'while'},  # Legal content needs precise, inclusive language
                'accepted': {'with', 'whereas', 'although'}  # Formal, precise terms
            },
            'ui_documentation_patterns': {
                'flagged': {'web site', 'work station', 'w/'},  # UI docs need modern terminology
                'accepted': {'website', 'workstation', 'wi-fi'}  # Modern UI/tech terms
            },
            'general_patterns': {
                'flagged': {'war room', 'whitelist', 'w/'},  # General content avoids exclusive/unclear language
                'accepted': {'with', 'website', 'workstation', 'worldwide'}  # Clear, modern terms
            }
        }