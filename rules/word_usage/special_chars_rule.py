"""
Word Usage Rule for special characters and numbers (Production-Grade)
Evidence-based analysis with surgical zero false positive guards for special character usage detection.
Based on IBM Style Guide recommendations with production-grade evidence calculation.
Preserves sophisticated Matcher integration for hash character detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
    from spacy.matcher import Matcher
except ImportError:
    Doc = None
    Matcher = None

class SpecialCharsRule(BaseWordUsageRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect usage of special characters and numbers.
    
    Implements evidence-based analysis with:
    - Surgical zero false positive guards for special character usage
    - Dynamic base evidence scoring based on usage specificity and context
    - Context-aware adjustments for different writing domains
    - PRESERVED: Advanced Matcher integration for hash character detection
    
    Features:
    - Near 100% false positive elimination through surgical guards
    - Usage-specific evidence calculation for each special character violation
    - Evidence-aware suggestions tailored to writing context
    - Sophisticated pattern matching for fiscal periods and symbols
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_special'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """Evidence-based analysis for special character usage violations."""
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define comprehensive special character and number patterns
        special_patterns = {
            # Time and availability formats
            "24/7": {"alternatives": ["24x7", "24 hours a day", "always available"], "category": "time_format", "severity": "medium"},
            "7x24": {"alternatives": ["24x7", "24 hours a day"], "category": "time_format", "severity": "medium"},
            "24x7x365": {"alternatives": ["24x7", "continuous operation"], "category": "time_format", "severity": "medium"},
            
            # Fiscal period standardization (H to Q format)
            "H1": {"alternatives": ["1H", "first half"], "category": "fiscal_period", "severity": "medium"},
            "H2": {"alternatives": ["2H", "second half"], "category": "fiscal_period", "severity": "medium"},
            "Q1": {"alternatives": ["1Q", "first quarter"], "category": "fiscal_period", "severity": "medium"},
            "Q2": {"alternatives": ["2Q", "second quarter"], "category": "fiscal_period", "severity": "medium"},
            "Q3": {"alternatives": ["3Q", "third quarter"], "category": "fiscal_period", "severity": "medium"},
            "Q4": {"alternatives": ["4Q", "fourth quarter"], "category": "fiscal_period", "severity": "medium"},
            
            # Symbol and character usage  
            "%": {"alternatives": ["percent"], "category": "symbol_usage", "severity": "low"},
            "&": {"alternatives": ["and"], "category": "symbol_usage", "severity": "medium"},
            "@": {"alternatives": ["at"], "category": "symbol_usage", "severity": "medium"},
            
            # Number format issues
            "1st": {"alternatives": ["first"], "category": "ordinal_format", "severity": "low"},
            "2nd": {"alternatives": ["second"], "category": "ordinal_format", "severity": "low"},
            "3rd": {"alternatives": ["third"], "category": "ordinal_format", "severity": "low"},
            "4th": {"alternatives": ["fourth"], "category": "ordinal_format", "severity": "low"},
            
            # Mathematical operators in text
            "=": {"alternatives": ["equals", "is"], "category": "math_operator", "severity": "medium"},
            "+": {"alternatives": ["plus", "and"], "category": "math_operator", "severity": "medium"},
            "-": {"alternatives": ["minus", "to"], "category": "math_operator", "severity": "low"},
            
            # Currency symbols
            "$": {"alternatives": ["dollar", "USD"], "category": "currency_symbol", "severity": "medium"},
            "€": {"alternatives": ["euro"], "category": "currency_symbol", "severity": "medium"},
            "£": {"alternatives": ["pound"], "category": "currency_symbol", "severity": "medium"},
            
            # Special notation and marks
            "™": {"alternatives": ["trademark"], "category": "legal_symbol", "severity": "low"},
            "®": {"alternatives": ["registered"], "category": "legal_symbol", "severity": "low"},
            "©": {"alternatives": ["copyright"], "category": "legal_symbol", "severity": "low"},
            
            # Acceptable usage patterns (should not be flagged in most contexts)
            "*": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},  # Asterisk for notes/bullets
            ".": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},  # Period
            ",": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},  # Comma
        }

        # Evidence-based analysis for special character patterns
        # Track matched spans to avoid overlaps
        matched_spans = []
        
        # Process patterns by priority (most specific first)
        for pattern, details in special_patterns.items():
            # Skip acceptable usage patterns
            if details["category"] == "acceptable_usage":
                continue
                
            # Use appropriate regex pattern based on character type
            if len(pattern) == 1 and not pattern.isalnum():
                # Single special character - use more flexible matching
                regex_pattern = re.escape(pattern)
            else:
                # Multi-character patterns - use word boundaries
                regex_pattern = r'\b' + re.escape(pattern) + r'\b'
            
            for match in re.finditer(regex_pattern, text, re.IGNORECASE):
                char_start, char_end, matched_text = match.start(), match.end(), match.group(0)
                
                # Check for overlaps with already matched spans
                overlap = any(char_start < end and char_end > start for start, end in matched_spans)
                if overlap:
                    continue
                
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
                    # Apply surgical guards but allow time format patterns to override file path filtering
                    if self._should_filter_special_char(pattern, token, context or {}):
                        continue
                    
                    evidence_score = self._calculate_special_evidence(pattern, token, sent, text, context or {}, details["category"])
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message(pattern, evidence_score, details["category"]),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions(pattern, details["alternatives"], evidence_score, context or {}, details["category"]),
                            severity=details["severity"] if evidence_score < 0.7 else 'high',
                            text=text, context=context, evidence_score=evidence_score,
                            span=(char_start, char_end), flagged_text=matched_text
                        ))
                        # Add to matched spans to prevent overlaps
                        matched_spans.append((char_start, char_end))

        # PRESERVE EXISTING ADVANCED FUNCTIONALITY: spaCy Matcher for hash character detection
        if Matcher is not None:
            if not hasattr(self, '_hash_matcher'):
                self._hash_matcher = Matcher(nlp.vocab)
                hash_pattern = [{"TEXT": "#"}]
                self._hash_matcher.add("HASH_CHAR", [hash_pattern])

            hash_matches = self._hash_matcher(doc)
            for match_id, start, end in hash_matches:
                span = doc[start:end]
                
                # Check for overlaps with already matched spans
                char_start, char_end = span.start_char, span.end_char
                overlap = any(char_start < end_pos and char_end > start_pos for start_pos, end_pos in matched_spans)
                if overlap:
                    continue
                
                sent = span.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                # Apply surgical guards for hash detection
                if self._should_filter_special_char("#", span[0], context or {}):
                    continue
                
                evidence_score = self._calculate_special_evidence("#", span[0], sent, text, context or {}, "symbol_usage")
                
                if evidence_score > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text, sentence_index=sentence_index,
                        message=self._generate_evidence_aware_word_usage_message("#", evidence_score, "symbol_usage"),
                        suggestions=self._generate_evidence_aware_word_usage_suggestions("#", ["number sign", "hash sign"], evidence_score, context or {}, "symbol_usage"),
                        severity='low' if evidence_score < 0.7 else 'medium',
                        text=text, context=context, evidence_score=evidence_score,
                        span=(char_start, char_end), flagged_text=span.text
                    ))
                    # Add to matched spans to prevent overlaps
                    matched_spans.append((char_start, char_end))
        
        return errors

    def _calculate_special_evidence(self, pattern: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for special character usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on character category and usage context
        - Context-aware adjustments for different writing domains and audiences
        - Linguistic, structural, semantic, and feedback pattern analysis
        - Special handling for fiscal periods, time formats, symbols, and mathematical operators
        
        Args:
            pattern: The special character or pattern being analyzed
            token: SpaCy token object
            sentence: Sentence containing the character
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Character category (fiscal_period, time_format, symbol_usage, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_special_evidence_score(pattern, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this character
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_special(evidence_score, pattern, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_special(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_special(evidence_score, pattern, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_special(evidence_score, pattern, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _should_filter_special_char(self, pattern: str, token, context: Dict[str, Any]) -> bool:
        """
        Apply surgical guards for special characters with overrides for valid patterns.
        Allows time format patterns to bypass file path filtering and legal symbols to override entity filtering.
        """
        pattern_lower = pattern.lower()
        
        # Override file path filtering for known time format patterns
        if pattern_lower in ['24/7', '7x24', '24x7x365']:
            # Apply all guards except file path filtering
            return self._apply_surgical_guards_except_file_paths(token, context)
        
        # Override entity filtering for patterns that should be flagged regardless of entity status
        if pattern_lower in ['™', '®', '©', 'q1', 'q2', 'q3', 'q4', 'h1', 'h2']:
            # Apply all guards except entity filtering for legal symbols and fiscal periods
            return self._apply_surgical_guards_except_entities(token, context)
        
        # For all other patterns, apply standard surgical guards
        return self._apply_surgical_zero_false_positive_guards_word_usage(token, context)
    
    def _apply_surgical_guards_except_file_paths(self, token, context: Dict[str, Any]) -> bool:
        """
        Apply surgical guards but skip file path filtering for time formats.
        """
        # === GUARD 1: CODE AND TECHNICAL CONTEXT ===
        if self._is_in_code_or_technical_context_words(token, context):
            return True
            
        # === GUARD 2: QUOTED CONTENT ===
        if self._is_in_quoted_context_words(token, context):
            return True
            
        # === GUARD 3: TECHNICAL SPECIFICATIONS ===
        if self._is_technical_specification_words(token, context):
            return True
            
        # === GUARD 4: DOMAIN-APPROPRIATE LANGUAGE ===
        if self._is_domain_appropriate_word_usage(token, context):
            return True
            
        # === GUARD 5: PROPER NOUNS AND ENTITY FILTERING ===
        if hasattr(token, 'ent_type_') and token.ent_type_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT']:
            return True
            
        # === SKIP GUARD 6: URLs and FILE PATHS ===
        # Allow time formats like "24/7" to pass through
        
        # === GUARD 7: FOREIGN LANGUAGE ===
        if hasattr(token, 'lang_') and token.lang_ != 'en':
            return True
            
        return False  # No guards triggered - process this character
    
    def _apply_surgical_guards_except_entities(self, token, context: Dict[str, Any]) -> bool:
        """
        Apply surgical guards but skip entity filtering for legal symbols.
        """
        # === GUARD 1: CODE AND TECHNICAL CONTEXT ===
        if self._is_in_code_or_technical_context_words(token, context):
            return True
            
        # === GUARD 2: QUOTED CONTENT ===
        if self._is_in_quoted_context_words(token, context):
            return True
            
        # === GUARD 3: TECHNICAL SPECIFICATIONS ===
        if self._is_technical_specification_words(token, context):
            return True
            
        # === GUARD 4: DOMAIN-APPROPRIATE LANGUAGE ===
        if self._is_domain_appropriate_word_usage(token, context):
            return True
            
        # === SKIP GUARD 5: ENTITY FILTERING ===
        # Allow legal symbols to pass through even if tagged as entities
        
        # === GUARD 6: URLs, FILE PATHS, AND IDENTIFIERS ===
        if hasattr(token, 'like_url') and token.like_url:
            return True
        if hasattr(token, 'text'):
            text = token.text
            if (text.startswith('http') or 
                text.startswith('www.') or
                text.startswith('ftp://') or
                ('/' in text and len(text) > 3) or
                ('\\' in text and len(text) > 3)):
                return True
        
        # === GUARD 7: FOREIGN LANGUAGE ===
        if hasattr(token, 'lang_') and token.lang_ != 'en':
            return True
            
        return False  # No guards triggered - process this character
    
    def _get_base_special_evidence_score(self, pattern: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on special character category and usage specificity.
        Higher priority categories get higher base scores for surgical precision.
        """
        pattern_lower = pattern.lower()
        
        # Critical financial/corporate formatting standards
        if category == 'fiscal_period':
            if pattern_lower in ['h1', 'h2']:
                return 0.75  # Half-year formatting needs consistency
            elif pattern_lower in ['q1', 'q2', 'q3', 'q4']:
                return 0.7   # Quarter formatting needs consistency
            else:
                return 0.65  # Other fiscal periods
        
        # Time and availability format issues
        elif category == 'time_format':
            if pattern_lower == '24/7':
                return 0.65  # Common time format needing clarity
            elif pattern_lower in ['7x24', '24x7x365']:
                return 0.6   # Alternative time formats
            else:
                return 0.55  # Other time formats
        
        # Symbol usage and terminology precision
        elif category == 'symbol_usage':
            if pattern_lower in ['&', '@']:
                return 0.6   # Commonly misused symbols in formal text
            elif pattern_lower in ['%', '#']:
                return 0.5   # Context-dependent symbols
            else:
                return 0.45  # Other symbols
        
        # Mathematical operators in prose
        elif category == 'math_operator':
            if pattern_lower in ['=', '+']:
                return 0.6   # Mathematical symbols in text
            elif pattern_lower == '-':
                return 0.4   # Dash usage context-dependent
            else:
                return 0.5   # Other math operators
        
        # Currency symbols needing clarity
        elif category == 'currency_symbol':
            if pattern_lower in ['$', '€', '£']:
                return 0.65  # Currency symbols benefit from text alternatives
            else:
                return 0.6   # Other currency symbols
        
        # Legal symbols and marks
        elif category == 'legal_symbol':
            if pattern_lower in ['™', '®', '©']:
                return 0.4   # Legal symbols often acceptable but benefit from expansion
            else:
                return 0.45  # Other legal symbols
        
        # Ordinal format consistency
        elif category == 'ordinal_format':
            if pattern_lower in ['1st', '2nd', '3rd']:
                return 0.5   # Common ordinals benefit from word form
            elif pattern_lower == '4th':
                return 0.45  # Fourth less commonly written as word
            else:
                return 0.4   # Other ordinals
        
        return 0.5  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_special(self, ev: float, pattern: str, token, sentence) -> float:
        """Apply special character-specific linguistic clues using SpaCy analysis."""
        sent_text = sentence.text.lower()
        pattern_lower = pattern.lower()
        
        # === FISCAL PERIOD CLUES ===
        if pattern_lower in ['h1', 'h2', 'q1', 'q2', 'q3', 'q4']:
            # Financial context indicators
            if any(indicator in sent_text for indicator in ['quarter', 'fiscal', 'financial', 'earnings']):
                ev += 0.2  # Financial context needs standard formatting
            elif any(indicator in sent_text for indicator in ['revenue', 'profit', 'results', 'performance']):
                ev += 0.15  # Business results context
            elif any(indicator in sent_text for indicator in ['report', 'guidance', 'outlook']):
                ev += 0.1  # Reporting context benefits from clarity
        
        # === TIME FORMAT CLUES ===
        if pattern_lower in ['24/7', '7x24', '24x7x365']:
            # Service availability context
            if any(indicator in sent_text for indicator in ['service', 'support', 'available', 'operation']):
                ev += 0.15  # Service context benefits from clear formatting
            elif any(indicator in sent_text for indicator in ['monitor', 'maintenance', 'coverage']):
                ev += 0.1  # Operations context
        
        # === SYMBOL USAGE CLUES ===
        if pattern_lower == '#':
            # Context suggesting need for clarification
            if any(indicator in sent_text for indicator in ['hashtag', 'social', 'number', 'pound']):
                ev += 0.15  # Ambiguous usage needs clarification
            elif any(indicator in sent_text for indicator in ['tag', 'reference', 'id']):
                ev += 0.1  # Reference context may benefit from clarity
        
        if pattern_lower == '&':
            # Formal writing context
            if any(indicator in sent_text for indicator in ['and', 'plus', 'with', 'along']):
                ev += 0.1  # Formal context benefits from "and"
        
        if pattern_lower == '@':
            # Email or location context
            if any(indicator in sent_text for indicator in ['email', 'address', 'contact', 'location']):
                ev += 0.15  # Non-email context benefits from "at"
        
        # === MATHEMATICAL OPERATOR CLUES ===
        if pattern_lower in ['=', '+', '-']:
            # Mathematical or equation context
            if any(indicator in sent_text for indicator in ['equals', 'plus', 'minus', 'add', 'subtract']):
                ev += 0.1  # Mathematical context may benefit from words
            elif any(indicator in sent_text for indicator in ['formula', 'equation', 'calculation']):
                ev -= 0.1  # Mathematical context may allow symbols
        
        # === CURRENCY CLUES ===
        if pattern_lower in ['$', '€', '£']:
            # Financial amount context
            if any(indicator in sent_text for indicator in ['price', 'cost', 'amount', 'value', 'fee']):
                ev += 0.1  # Financial context may benefit from word form
            elif any(indicator in sent_text for indicator in ['dollar', 'euro', 'pound', 'currency']):
                ev += 0.05  # Currency context
        
        # === ORDINAL FORMAT CLUES ===
        if pattern_lower in ['1st', '2nd', '3rd', '4th']:
            # Ordinal usage context
            if any(indicator in sent_text for indicator in ['step', 'phase', 'stage', 'level']):
                ev += 0.1  # Procedural context benefits from word form
            elif any(indicator in sent_text for indicator in ['first', 'second', 'third', 'fourth']):
                ev += 0.05  # Word form context
        
        return ev

    def _apply_structural_clues_special(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for special characters."""
        block_type = context.get('block_type', 'paragraph')
        
        if block_type in ['step', 'procedure']:
            ev += 0.1  # Procedural content benefits from clear, readable formats
        elif block_type == 'heading':
            ev += 0.05  # Headings benefit from professional appearance
        elif block_type in ['admonition', 'callout']:
            ev += 0.1  # Important callouts need clear formatting
        elif block_type in ['table_cell', 'table_header']:
            ev -= 0.1  # Tables may allow more compact formats
        elif block_type in ['code_block', 'inline_code']:
            ev -= 0.3  # Code contexts may require specific symbols
        
        return ev

    def _apply_semantic_clues_special(self, ev: float, pattern: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for special characters."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        pattern_lower = pattern.lower()
        
        # Content type adjustments
        if content_type == 'financial':
            if pattern_lower in ['h1', 'h2', 'q1', 'q2', 'q3', 'q4']:
                ev += 0.3  # Financial content needs standard fiscal formatting
            elif pattern_lower in ['$', '€', '£']:
                ev += 0.2  # Financial content may benefit from currency clarity
        
        elif content_type == 'customer_facing':
            if pattern_lower in ['24/7', '7x24', '24x7x365']:
                ev += 0.2  # Customer content benefits from clear time expressions
            elif pattern_lower in ['&', '@', '%']:
                ev += 0.15  # Customer content benefits from readable symbols
            elif pattern_lower in ['1st', '2nd', '3rd', '4th']:
                ev += 0.1  # Customer instructions benefit from word forms
        
        elif content_type == 'technical':
            if pattern_lower in ['#', '&', '@']:
                ev += 0.1  # Technical docs benefit from precise terminology
            elif pattern_lower in ['=', '+', '-']:
                ev -= 0.1  # Technical content may allow mathematical operators
            
            # Additional reduction for expert/developer technical audience
            if audience in ['expert', 'developer']:
                ev -= 0.6  # Expert/developer technical audience understands symbols better
        
        elif content_type == 'legal':
            if pattern_lower in ['&', '$', '€', '£']:
                ev += 0.2  # Legal content requires precision and clarity
            elif pattern_lower in ['™', '®', '©']:
                ev -= 0.1  # Legal symbols may be acceptable in legal context
        
        elif content_type == 'marketing':
            if pattern_lower in ['&', '@', '#']:
                ev += 0.15  # Marketing content benefits from readable text
            elif pattern_lower in ['$', '€', '£']:
                ev += 0.1  # Marketing may benefit from clear pricing
        
        # Audience adjustments
        if audience == 'external':
            if pattern_lower in ['h1', 'h2', 'q1', 'q2', 'q3', 'q4']:
                ev += 0.25  # External audiences need standard formatting
            elif pattern_lower in ['&', '@', '%']:
                ev += 0.2  # External audiences benefit from readable symbols
        
        elif audience == 'global':
            if pattern_lower in ['24/7', '7x24']:
                ev += 0.2  # Global audiences benefit from clear expressions
            elif pattern_lower in ['$', '€', '£']:
                ev += 0.15  # Global audiences need currency clarity
        
        elif audience == 'beginner':
            if pattern_lower in ['&', '@', '#', '%']:
                ev += 0.2  # Beginners benefit from word forms over symbols
            elif pattern_lower in ['=', '+', '-']:
                ev += 0.15  # Beginners benefit from word descriptions
        
        elif audience in ['expert', 'developer']:
            if pattern_lower in ['=', '+', '-']:
                ev -= 0.3  # Experts/developers may understand mathematical notation
            elif pattern_lower in ['#', '&', '@']:
                ev -= 0.2  # Experts/developers may understand common symbols
        
        return ev

    def _apply_feedback_clues_special(self, ev: float, pattern: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for special characters."""
        patterns = self._get_cached_feedback_patterns_special()
        pattern_lower = pattern.lower()
        
        # Consistently flagged terms
        if pattern_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        
        # Consistently accepted terms
        if pattern_lower in patterns.get('accepted_terms', set()):
            ev -= 0.3
        
        # Context-specific patterns
        content_type = context.get('content_type', 'general')
        context_patterns = patterns.get(f'{content_type}_patterns', {})
        
        if pattern_lower in context_patterns.get('flagged', set()):
            ev += 0.1
        elif pattern_lower in context_patterns.get('accepted', set()):
            ev -= 0.15
        
        return ev

    def _get_cached_feedback_patterns_special(self) -> Dict[str, Any]:
        """Get cached feedback patterns for special characters."""
        return {
            'often_flagged_terms': {'h1', 'h2', 'q1', 'q2', 'q3', 'q4', '24/7', '&', '@', '$'},
            'accepted_terms': {'%'},  # Commonly acceptable special characters (context-dependent ones moved to specific patterns)
            'financial_patterns': {
                'flagged': {'h1', 'h2', 'q1', 'q2', 'q3', 'q4', '$', '€', '£'},  # Financial needs clarity
                'accepted': {'%', '™', '®'}  # Some symbols acceptable in financial context
            },
            'customer_facing_patterns': {
                'flagged': {'24/7', '7x24', '&', '@', '#', '=', '+', '™', '®', '©'},  # Customer content needs clarity and expansion
                'accepted': {'%'}  # Percentage acceptable for customers
            },
            'technical_patterns': {
                'flagged': {'&', '@', '#'},  # Technical docs need precise terminology
                'accepted': {'=', '+', '-', '%', '™', '®', '©'}  # Technical symbols acceptable
            },
            'legal_patterns': {
                'flagged': {'&', '$', '€', '£', '#', '@'},  # Legal content requires precision
                'accepted': {'™', '®', '©', '%'}  # Legal symbols acceptable in legal context
            },
            'marketing_patterns': {
                'flagged': {'&', '@', '#', '=', '+'},  # Marketing needs readable text
                'accepted': {'%', '™', '®', '©', '$', '€', '£'}  # Some symbols acceptable in marketing
            },
            'general_patterns': {
                'flagged': {'24/7', 'h1', 'h2', 'q1', 'q2', 'q3', 'q4', '&', '@'},  # General content avoids complex symbols
                'accepted': {'%', '™', '®', '©'}  # Generally acceptable symbols
            }
        }