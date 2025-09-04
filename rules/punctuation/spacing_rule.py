"""
Spacing Rule - Evidence-Based Analysis
"""
from typing import List, Dict, Any, Optional
import re
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens import Doc, Token, Span
except ImportError:
    Doc = None
    Token = None
    Span = None

class SpacingRule(BasePunctuationRule):
    """
    Checks for spacing violations using evidence-based analysis:
    - Double spaces between words
    - Missing spaces after punctuation
    - Trailing and leading spaces
    - Mixed tab/space indentation
    - Inconsistent spacing around punctuation
    Enhanced with dependency parsing and contextual awareness.
    """
    def __init__(self):
        """Initialize the rule with spacing patterns."""
        super().__init__()
        self._initialize_spacing_patterns()
    
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'spacing'
    
    def _initialize_spacing_patterns(self):
        """Initialize spacing detection patterns."""
        self.spacing_patterns = {
            'double_spaces': re.compile(r'(\S)\s{2,}(\S)'),  # Multiple spaces between non-whitespace
            'trailing_spaces': re.compile(r'\s+$', re.MULTILINE),  # Spaces at end of lines
            'leading_spaces': re.compile(r'^\s+(\S)', re.MULTILINE),  # Leading spaces (not indentation)
            'missing_space_after_period': re.compile(r'\.(\w)'),  # Period directly followed by word
            'missing_space_after_comma': re.compile(r',(\w)'),  # Comma directly followed by word
            'missing_space_after_colon': re.compile(r':(\w)'),  # Colon directly followed by word
            'space_before_punctuation': re.compile(r'\s+([,.;:!?])'),  # Space before punctuation
            'mixed_indentation': re.compile(r'^(\t+ +| +\t+)', re.MULTILINE),  # Mixed tabs and spaces
            'odd_indentation': re.compile(r'^( {1}[^ ]| {3}[^ ]| {5}[^ ]| {7}[^ ])', re.MULTILINE),  # Odd spaces
            'excessive_indentation': re.compile(r'^( {9,})(\S)', re.MULTILINE)  # Too many spaces
        }
    
    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for spacing violations:
        - Multiple spaces between words
        - Missing spaces after punctuation
        - Trailing/leading whitespace issues
        - Indentation problems
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        
        # Fallback analysis when nlp is not available
        if not nlp:
            return self._fallback_spacing_analysis(text, sentences, context, errors)

        try:
            doc = nlp(text)
            
            # PRIORITY: Use regex patterns for reliable spacing detection
            # These patterns are more reliable for spacing issues than token-based analysis
            errors.extend(self._analyze_spacing_with_patterns(text, context))
            
            # Additional spaCy-based analysis for complex cases
            for i, sent in enumerate(doc.sents):
                errors.extend(self._analyze_sentence_spacing_advanced(sent, i, text, context))
            
        except Exception as e:
            # Graceful degradation for SpaCy errors
            return self._fallback_spacing_analysis(text, sentences, context, errors)
        
        return errors

    def _fallback_spacing_analysis(self, text: str, sentences: List[str], context: Dict[str, Any], errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback spacing analysis without spaCy."""
        # Apply basic context guards
        if self._should_skip_fallback_analysis(context):
            return errors
        
        # Check for spacing violations using regex patterns
        for pattern_name, pattern in self.spacing_patterns.items():
            for match in pattern.finditer(text):
                # Calculate basic evidence score
                evidence_score = self._calculate_fallback_evidence(pattern_name, match, text, context)
                
                if evidence_score > 0.1:
                    error = self._create_spacing_error(
                        pattern_name, match, text, 0, evidence_score, context
                    )
                    if error:
                        errors.append(error)
        
        return errors
    
    def _should_skip_fallback_analysis(self, context: Dict[str, Any]) -> bool:
        """Check if fallback analysis should be skipped for this context."""
        content_type = context.get('content_type', 'general')
        block_type = context.get('block_type', 'paragraph')
        
        # Skip code blocks and technical contexts
        if content_type in ['code', 'technical_code'] or block_type in ['code_block', 'inline_code', 'literal_block']:
            return True
        
        # Skip tables where spacing might be intentional
        if block_type in ['table_cell', 'table_header', 'table']:
            return True
        
        # Skip quoted content where original spacing should be preserved
        if block_type in ['quote', 'blockquote', 'citation']:
            return True
        
        return False

    def _analyze_spacing_with_patterns(self, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze spacing using regex patterns - reliable for most spacing issues."""
        errors = []
        
        # Skip if context suggests we shouldn't analyze
        if self._should_skip_fallback_analysis(context):
            return errors
        
        # Use the same patterns as fallback analysis
        for pattern_name, pattern in self.spacing_patterns.items():
            for match in pattern.finditer(text):
                # Calculate evidence score
                evidence_score = self._calculate_fallback_evidence(pattern_name, match, text, context)
                
                if evidence_score > 0.1:
                    error = self._create_spacing_error(
                        pattern_name, match, text, 0, evidence_score, context
                    )
                    if error:
                        errors.append(error)
        
        return errors

    def _analyze_sentence_spacing_advanced(self, sent: 'Span', sentence_idx: int, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Advanced spaCy-based spacing analysis for complex cases."""
        errors = []
        
        # For now, this is a placeholder for future advanced analysis
        # The regex patterns handle most spacing issues effectively
        
        return errors
    
    def _analyze_sentence_spacing(self, sent: 'Span', sentence_idx: int, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze spacing within a sentence using spaCy tokens."""
        errors = []
        
        for i, token in enumerate(sent):
            # Check for double spaces between tokens
            if i > 0:
                prev_token = sent[i-1]
                space_between = token.idx - (prev_token.idx + len(prev_token.text))
                
                if space_between > 1:
                    evidence_score = self._calculate_double_space_evidence(prev_token, token, sent, text, context)
                    
                    if evidence_score > 0.1:
                        error = self._create_error(
                            sentence=sent.text,
                            sentence_index=sentence_idx,
                            message=self._get_contextual_spacing_message('double_spaces', evidence_score, context),
                            suggestions=self._generate_smart_spacing_suggestions('double_spaces', evidence_score, context),
                            severity='low' if evidence_score < 0.6 else 'medium',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(prev_token.idx + len(prev_token.text), token.idx),
                            flagged_text=text[prev_token.idx + len(prev_token.text):token.idx],
                            violation_type='double_spaces'
                        )
                        errors.append(error)
            
            # Check for missing spaces after punctuation
            if token.text in '.,:' and i < len(sent) - 1:
                next_token = sent[i+1]
                space_after = next_token.idx - (token.idx + len(token.text))
                
                if space_after == 0:  # No space after punctuation
                    evidence_score = self._calculate_missing_space_evidence(token, next_token, sent, text, context)
                    
                    if evidence_score > 0.1:
                        pattern_name = f'missing_space_after_{self._get_punctuation_name(token.text)}'
                        error = self._create_error(
                            sentence=sent.text,
                            sentence_index=sentence_idx,
                            message=self._get_contextual_spacing_message(pattern_name, evidence_score, context),
                            suggestions=self._generate_smart_spacing_suggestions(pattern_name, evidence_score, context),
                            severity='medium',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(token.idx, next_token.idx),
                            flagged_text=token.text + next_token.text,
                            violation_type=pattern_name
                        )
                        errors.append(error)
        
        return errors
    
    def _analyze_document_spacing(self, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze document-level spacing issues like trailing spaces and indentation."""
        errors = []
        
        # Check trailing spaces
        for match in self.spacing_patterns['trailing_spaces'].finditer(text):
            if match.group().strip():  # Only flag non-empty trailing spaces
                evidence_score = self._calculate_trailing_space_evidence(match, text, context)
                
                if evidence_score > 0.1:
                    error = self._create_spacing_error('trailing_spaces', match, text, 0, evidence_score, context)
                    if error:
                        errors.append(error)
        
        # Check mixed indentation only if context suggests it's important
        if context.get('block_type') not in ['code_block', 'literal_block']:
            for match in self.spacing_patterns['mixed_indentation'].finditer(text):
                evidence_score = self._calculate_indentation_evidence(match, text, context)
                
                if evidence_score > 0.1:
                    error = self._create_spacing_error('mixed_indentation', match, text, 0, evidence_score, context)
                    if error:
                        errors.append(error)
        
        return errors

    # === EVIDENCE CALCULATION ===

    def _calculate_double_space_evidence(self, prev_token: 'Token', token: 'Token', sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence for double space violations."""
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        if self._apply_zero_false_positive_guards_punctuation(prev_token, context):
            return 0.0
        
        # Tables and formatted content may intentionally use multiple spaces
        if context.get('block_type') in ['table_cell', 'table_header', 'table']:
            return 0.0
        
        # Code blocks use their own spacing rules
        if context.get('block_type') in ['code_block', 'inline_code', 'literal_block']:
            return 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = 0.8  # Strong evidence for double spaces
        
        # === STEP 2: LINGUISTIC CLUES ===
        evidence_score = self._apply_common_linguistic_clues_punctuation(evidence_score, prev_token, sent)
        
        # === STEP 3: STRUCTURAL CLUES ===
        evidence_score = self._apply_common_structural_clues_punctuation(evidence_score, prev_token, context)
        
        # === STEP 4: SEMANTIC CLUES ===
        evidence_score = self._apply_common_semantic_clues_punctuation(evidence_score, prev_token, context)
        
        # === STEP 5: SPACING-SPECIFIC CLUES ===
        # Check if this might be intentional alignment
        if self._is_intentional_alignment(prev_token, token, text):
            evidence_score -= 0.4
        
        return max(0.0, min(1.0, evidence_score))
    
    def _calculate_missing_space_evidence(self, punct_token: 'Token', next_token: 'Token', sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence for missing space after punctuation."""
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        if self._apply_zero_false_positive_guards_punctuation(punct_token, context):
            return 0.0
        
        # URLs and file paths have their own punctuation rules
        if hasattr(next_token, 'like_url') and next_token.like_url:
            return 0.0
        
        # Technical identifiers may not need spaces
        if self._is_technical_identifier_context(punct_token, next_token):
            return 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = 0.9  # Very strong evidence for missing space after punctuation
        
        # === STEP 2: LINGUISTIC CLUES ===
        evidence_score = self._apply_common_linguistic_clues_punctuation(evidence_score, punct_token, sent)
        
        # === STEP 3: STRUCTURAL CLUES ===
        evidence_score = self._apply_common_structural_clues_punctuation(evidence_score, punct_token, context)
        
        # === STEP 4: SEMANTIC CLUES ===
        evidence_score = self._apply_common_semantic_clues_punctuation(evidence_score, punct_token, context)
        
        # === STEP 5: PUNCTUATION-SPECIFIC CLUES ===
        # Periods in abbreviations are different
        if punct_token.text == '.' and self._is_abbreviation_context(punct_token, next_token):
            evidence_score -= 0.6
        
        # Colons in time format or ratios are different
        if punct_token.text == ':' and self._is_time_or_ratio_context(punct_token, next_token):
            evidence_score -= 0.7
        
        return max(0.0, min(1.0, evidence_score))
    
    def _calculate_trailing_space_evidence(self, match, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence for trailing space violations."""
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        if context.get('block_type') in ['code_block', 'literal_block', 'inline_code']:
            return 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = 0.6  # Medium evidence for trailing spaces
        
        # === STEP 2: CONTEXT CLUES ===
        # Markdown may use trailing spaces for line breaks
        if context.get('format') == 'markdown' and len(match.group()) == 2:
            evidence_score -= 0.4
        
        # More trailing spaces = stronger evidence
        space_count = len(match.group())
        if space_count > 3:
            evidence_score += 0.2
        
        return max(0.0, min(1.0, evidence_score))
    
    def _calculate_indentation_evidence(self, match, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence for indentation violations."""
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        if context.get('block_type') in ['code_block', 'literal_block']:
            return 0.0
        
        # Lists may have varied indentation
        if context.get('block_type') in ['ordered_list_item', 'unordered_list_item']:
            return 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = 0.7  # Good evidence for indentation problems
        
        # === STEP 2: CONTEXT CLUES ===
        # Poetry and creative content may use intentional indentation
        if context.get('content_type') in ['creative', 'poetry', 'verse']:
            evidence_score -= 0.5
        
        return max(0.0, min(1.0, evidence_score))
    
    def _calculate_fallback_evidence(self, pattern_name: str, match, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence for fallback analysis without spaCy."""
        base_scores = {
            'double_spaces': 0.8,
            'trailing_spaces': 0.6,
            'missing_space_after_period': 0.9,
            'missing_space_after_comma': 0.9,
            'missing_space_after_colon': 0.8,
            'space_before_punctuation': 0.7,
            'mixed_indentation': 0.7,
            'odd_indentation': 0.5,
            'excessive_indentation': 0.6
        }
        
        evidence_score = base_scores.get(pattern_name, 0.5)
        
        # Apply basic context adjustments
        content_type = context.get('content_type', 'general')
        if content_type in ['creative', 'poetry']:
            evidence_score -= 0.3
        elif content_type == 'technical':
            evidence_score += 0.1
        
        return max(0.0, min(1.0, evidence_score))

    # === HELPER METHODS ===
    
    def _is_intentional_alignment(self, prev_token: 'Token', token: 'Token', text: str) -> bool:
        """Check if multiple spaces might be for intentional alignment."""
        # Look for patterns that suggest alignment (tables, forms)
        line_start = text.rfind('\n', 0, prev_token.idx)
        line_end = text.find('\n', token.idx)
        if line_end == -1:
            line_end = len(text)
        
        line_text = text[line_start+1:line_end]
        
        # Count alignment patterns
        space_groups = re.findall(r'\s{2,}', line_text)
        if len(space_groups) > 2:  # Multiple alignment groups suggest intentional formatting
            return True
        
        return False
    
    def _is_technical_identifier_context(self, punct_token: 'Token', next_token: 'Token') -> bool:
        """Check if punctuation is part of a technical identifier."""
        if punct_token.text == '.' and hasattr(next_token, 'text'):
            # Version numbers like "1.0"
            if next_token.text.isdigit():
                return True
            # File extensions like ".py"
            if next_token.text.lower() in ['py', 'js', 'html', 'css', 'json', 'xml', 'yml', 'yaml']:
                return True
        
        if punct_token.text == ':' and hasattr(next_token, 'text'):
            # Port numbers like ":8080"
            if next_token.text.isdigit():
                return True
        
        return False
    
    def _is_abbreviation_context(self, punct_token: 'Token', next_token: 'Token') -> bool:
        """Check if period is part of an abbreviation."""
        if not hasattr(next_token, 'text'):
            return False
        
        # Common abbreviation patterns
        if next_token.text.isupper() and len(next_token.text) <= 3:
            return True
        
        return False
    
    def _is_time_or_ratio_context(self, punct_token: 'Token', next_token: 'Token') -> bool:
        """Check if colon is part of time or ratio."""
        if not hasattr(next_token, 'text'):
            return False
        
        # Time format like "12:30"
        if next_token.text.isdigit() and len(next_token.text) == 2:
            return True
        
        return False
    
    def _get_punctuation_name(self, punct: str) -> str:
        """Get name for punctuation mark."""
        names = {'.': 'period', ',': 'comma', ':': 'colon'}
        return names.get(punct, 'punctuation')
    
    def _create_spacing_error(self, pattern_name: str, match, text: str, sentence_idx: int, evidence_score: float, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create error for spacing violation."""
        if evidence_score <= 0.1:
            return None
        
        flagged_text = match.group()
        
        return self._create_error(
            sentence=self._get_sentence_for_match(match, text),
            sentence_index=sentence_idx,
            message=self._get_contextual_spacing_message(pattern_name, evidence_score, context),
            suggestions=self._generate_smart_spacing_suggestions(pattern_name, evidence_score, context),
            severity='low' if evidence_score < 0.6 else ('medium' if evidence_score < 0.8 else 'high'),
            text=text,
            context=context,
            evidence_score=evidence_score,
            span=(match.start(), match.end()),
            flagged_text=flagged_text,
            violation_type=pattern_name
        )
    
    def _get_sentence_for_match(self, match, text: str) -> str:
        """Extract sentence containing the match."""
        # Find sentence boundaries around the match
        start = max(0, text.rfind('.', 0, match.start()) + 1)
        end = text.find('.', match.end())
        if end == -1:
            end = len(text)
        
        return text[start:end].strip()

    # === SMART MESSAGING ===

    def _get_contextual_spacing_message(self, pattern_name: str, evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for spacing violations."""
        confidence_phrase = "clearly has" if evidence_score > 0.8 else ("likely has" if evidence_score > 0.6 else "may have")
        
        messages = {
            'double_spaces': f"This text {confidence_phrase} multiple consecutive spaces between words.",
            'trailing_spaces': f"This line {confidence_phrase} unnecessary spaces at the end.",
            'missing_space_after_period': f"This sentence {confidence_phrase} a missing space after a period.",
            'missing_space_after_comma': f"This text {confidence_phrase} a missing space after a comma.",
            'missing_space_after_colon': f"This text {confidence_phrase} a missing space after a colon.",
            'space_before_punctuation': f"This text {confidence_phrase} unnecessary spaces before punctuation.",
            'mixed_indentation': f"This content {confidence_phrase} mixed tabs and spaces for indentation.",
            'odd_indentation': f"This content {confidence_phrase} unusual indentation spacing.",
            'excessive_indentation': f"This content {confidence_phrase} excessive indentation."
        }
        
        return messages.get(pattern_name, f"This text {confidence_phrase} a spacing issue.")

    def _generate_smart_spacing_suggestions(self, pattern_name: str, evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for spacing violations."""
        suggestions = []
        
        suggestion_map = {
            'double_spaces': [
                "Replace multiple spaces with a single space.",
                "Use find and replace to fix multiple consecutive spaces.",
                "Ensure only one space between words."
            ],
            'trailing_spaces': [
                "Remove spaces at the end of the line.",
                "Trim whitespace from line endings.",
                "Configure your editor to show/remove trailing spaces."
            ],
            'missing_space_after_period': [
                "Add a space after the period.",
                "Ensure proper spacing between sentences.",
                "Use 'period space' pattern for sentence separation."
            ],
            'missing_space_after_comma': [
                "Add a space after the comma.",
                "Follow standard comma spacing rules.",
                "Use 'comma space' pattern in lists and clauses."
            ],
            'missing_space_after_colon': [
                "Add a space after the colon.",
                "Follow standard colon spacing conventions.",
                "Use proper spacing for clarity."
            ],
            'space_before_punctuation': [
                "Remove the space before punctuation.",
                "Punctuation should directly follow the word.",
                "Avoid spaces before commas, periods, and other punctuation."
            ],
            'mixed_indentation': [
                "Use consistent indentation (either tabs or spaces).",
                "Configure your editor for consistent indentation.",
                "Convert tabs to spaces or vice versa."
            ],
            'odd_indentation': [
                "Use standard indentation (2, 4, or 8 spaces).",
                "Align content properly with standard spacing.",
                "Consider using consistent indentation levels."
            ],
            'excessive_indentation': [
                "Reduce excessive indentation.",
                "Use appropriate indentation levels.",
                "Consider document structure and nesting."
            ]
        }
        
        base_suggestions = suggestion_map.get(pattern_name, ["Fix the spacing issue."])
        suggestions.extend(base_suggestions[:2])  # Take first 2 suggestions
        
        # Add confidence-specific suggestions
        if evidence_score > 0.8:
            suggestions.append("This spacing issue should be corrected for proper formatting.")
        elif evidence_score > 0.6:
            suggestions.append("Consider fixing this spacing for better readability.")
        
        # Add context-specific suggestions
        content_type = context.get('content_type', 'general')
        if content_type == 'technical' and pattern_name in ['mixed_indentation', 'odd_indentation']:
            suggestions.append("Technical documentation requires consistent formatting.")
        
        return suggestions[:3]  # Limit to 3 suggestions
