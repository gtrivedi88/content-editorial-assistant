"""
Indentation Rule - Evidence-Based Analysis
Based on Editorial Enhancement Plan Phase 2

"""
from typing import List, Dict, Any, Optional, Tuple
import re
from .base_structure_rule import BaseStructureRule

try:
    from spacy.tokens import Doc, Token, Span
except ImportError:
    Doc = None
    Token = None
    Span = None

class IndentationRule(BaseStructureRule):
    """
    Checks for indentation violations using evidence-based analysis:
    - Mixed tabs and spaces within same document
    - Odd or inconsistent indentation levels
    - Excessive indentation depth
    - Accidental single space indentation
    - Context-aware validation for different content types
    Enhanced with spaCy morphological analysis and contextual awareness.
    """
    def __init__(self):
        """Initialize the rule with indentation patterns."""
        super().__init__()
        self._initialize_indentation_patterns()
    
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'indentation'
    
    def _initialize_indentation_patterns(self):
        """Initialize indentation detection patterns."""
        self.indentation_patterns = {
            # Mixed tabs and spaces in the same line
            'mixed_indentation': re.compile(r'^(\t+ +| +\t+)', re.MULTILINE),
            
            # Odd number of spaces (not 2, 4, 8)  
            'odd_indentation': re.compile(r'^( {1}[^ ]| {3}[^ ]| {5}[^ ]| {7}[^ ])', re.MULTILINE),
            
            # Excessive indentation (more than 8 spaces or 2 tabs)
            'excessive_indentation': re.compile(r'^( {9,}|\t{3,})(\S)', re.MULTILINE),
            
            # Accidental single space before capital letter (likely not intentional indentation)
            'accidental_single_space': re.compile(r'^( {1})([A-Z][a-z])', re.MULTILINE),
            
            # Inconsistent indentation levels within similar structures
            'inconsistent_indentation': re.compile(r'(^[ \t]+)(.+)', re.MULTILINE),
            
            # Zero-width or unusual whitespace characters
            'unusual_whitespace': re.compile(r'^[\u00A0\u1680\u2000-\u200B\u202F\u205F\u3000\uFEFF]+', re.MULTILINE)
        }
        
        # Standard indentation levels (in spaces)
        self.standard_indentations = [2, 4, 8]
    
    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for indentation violations:
        - Mixed tabs and spaces
        - Incorrect indentation levels
        - Accidental or inconsistent indentation
        - Context-aware validation
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        
        # Skip analysis for contexts where indentation is not relevant or controlled elsewhere
        if not self._should_analyze_indentation(context):
            return errors
        
        # Fallback analysis when nlp is not available
        if not nlp:
            return self._fallback_indentation_analysis(text, sentences, context)

        try:
            doc = nlp(text)
            
            # Pattern-based analysis (most reliable for indentation)
            errors.extend(self._analyze_indentation_patterns(text, context))
            
            # Additional spaCy-based analysis for document structure context
            errors.extend(self._analyze_document_indentation_structure(doc, text, context))
            
        except Exception as e:
            # Graceful degradation for SpaCy errors
            return self._fallback_indentation_analysis(text, sentences, context)
        
        return errors
    
    def _should_analyze_indentation(self, context: Dict[str, Any]) -> bool:
        """Check if indentation analysis is appropriate for this context."""
        block_type = context.get('block_type', 'paragraph')
        content_type = context.get('content_type', 'general')
        
        # Skip code blocks - they have their own indentation rules
        if block_type in ['code_block', 'inline_code', 'literal_block']:
            return False
        
        # Skip contexts where indentation is not meaningful
        if block_type in ['table_cell', 'table_header']:
            return False
            
        # Skip creative content where indentation might be intentional
        if content_type in ['creative', 'poetry', 'verse']:
            return False
        
        return True
    
    def _fallback_indentation_analysis(self, text: str, sentences: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback indentation analysis without spaCy."""
        errors = []
        
        # Use pattern-based analysis
        errors.extend(self._analyze_indentation_patterns(text, context))
        
        return errors
    
    def _analyze_indentation_patterns(self, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze indentation using regex patterns."""
        errors = []
        
        # Analyze each pattern type
        for pattern_name, pattern in self.indentation_patterns.items():
            errors.extend(self._analyze_single_indentation_pattern(pattern_name, pattern, text, context))
        
        # Additional analysis for inconsistent indentation levels
        errors.extend(self._analyze_indentation_consistency(text, context))
        
        return errors
    
    def _analyze_single_indentation_pattern(self, pattern_name: str, pattern: re.Pattern, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze a single indentation pattern."""
        errors = []
        
        for match in pattern.finditer(text):
            evidence_score = self._calculate_indentation_evidence(pattern_name, match, text, context)
            
            if evidence_score > 0.1:
                error = self._create_error(
                    sentence=self._get_line_for_match(match, text),
                    sentence_index=self._get_line_number_for_match(match, text),
                    message=self._get_contextual_indentation_message(pattern_name, evidence_score, context),
                    suggestions=self._generate_smart_indentation_suggestions(pattern_name, evidence_score, context),
                    severity=self._get_indentation_severity(pattern_name, evidence_score),
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=(match.start(), match.end()),
                    flagged_text=match.group(),
                    violation_type=f'indentation_{pattern_name}',
                    pattern_name=pattern_name
                )
                errors.append(error)
        
        return errors
    
    def _analyze_indentation_consistency(self, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze indentation consistency across the document."""
        errors = []
        
        lines = text.split('\n')
        indentation_levels = []
        
        # Collect all indentation patterns
        for i, line in enumerate(lines):
            if line.strip():  # Skip empty lines
                indent_match = re.match(r'^([ \t]*)', line)
                if indent_match:
                    indent = indent_match.group(1)
                    if indent:  # Only collect non-zero indentations
                        indentation_levels.append((i, indent, line))
        
        # Check for consistency issues
        if len(indentation_levels) > 1:
            inconsistency_evidence = self._calculate_consistency_evidence(indentation_levels, context)
            
            if inconsistency_evidence > 0.1:
                # Create error for the most problematic line
                line_num, indent, line = self._find_most_problematic_indentation(indentation_levels)
                
                error = self._create_error(
                    sentence=line.strip(),
                    sentence_index=line_num,
                    message=self._get_contextual_indentation_message('inconsistent_indentation', inconsistency_evidence, context),
                    suggestions=self._generate_smart_indentation_suggestions('inconsistent_indentation', inconsistency_evidence, context),
                    severity=self._get_indentation_severity('inconsistent_indentation', inconsistency_evidence),
                    text=text,
                    context=context,
                    evidence_score=inconsistency_evidence,
                    span=(0, len(indent)),
                    flagged_text=indent,
                    violation_type='indentation_inconsistent_indentation',
                    pattern_name='inconsistent_indentation',
                    indentation_analysis={'total_patterns': len(set(indent for _, indent, _ in indentation_levels))}
                )
                errors.append(error)
        
        return errors
    
    def _analyze_document_indentation_structure(self, doc: 'Doc', text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Additional spaCy-based analysis for document structure indentation."""
        errors = []
        
        # For now, this is a placeholder for advanced structural analysis
        # The pattern-based analysis handles most indentation issues effectively
        
        return errors

    # === EVIDENCE CALCULATION ===
    
    def _calculate_indentation_evidence(self, pattern_name: str, match: re.Match, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence for indentation violations."""
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        if self._apply_zero_false_positive_guards_structure({'text': match.group()}, context):
            return 0.0
        
        # Don't flag indentation in quoted examples
        line = self._get_line_for_match(match, text)
        if self._is_in_quoted_example({'sentence': line}, context):
            return 0.0
        
        # Don't flag indentation in tables or formatted content
        if self._is_formatted_content(match, text, context):
            return 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        base_scores = {
            'mixed_indentation': 0.9,        # Very strong evidence - clearly wrong
            'odd_indentation': 0.6,          # Medium evidence - could be intentional
            'excessive_indentation': 0.7,    # Good evidence - likely problematic
            'accidental_single_space': 0.8,  # Strong evidence - usually unintentional
            'inconsistent_indentation': 0.5, # Medium evidence - depends on context
            'unusual_whitespace': 0.9        # Very strong evidence - often invisible issues
        }
        
        evidence_score = base_scores.get(pattern_name, 0.5)
        
        # === STEP 2: PATTERN-SPECIFIC ADJUSTMENTS ===
        if pattern_name == 'mixed_indentation':
            # Mixed tabs and spaces is almost always an error
            evidence_score = 0.9
            
        elif pattern_name == 'odd_indentation':
            # Check if it could be intentional (e.g., poetry, special formatting)
            if context.get('content_type') in ['formal', 'technical']:
                evidence_score += 0.2  # More strict for formal content
            elif context.get('block_type') in ['heading', 'list_item']:
                evidence_score -= 0.3  # More permissive for certain blocks
                
        elif pattern_name == 'accidental_single_space':
            # Single space before capital letter is usually accidental
            indent_text = match.group(1) if match.groups() else match.group()
            if len(indent_text) == 1 and indent_text == ' ':
                evidence_score = 0.9  # Very likely accidental
                
        elif pattern_name == 'excessive_indentation':
            # Very deep indentation might be intentional in some contexts
            indent_depth = len(match.group(1)) if match.groups() else 0
            if indent_depth > 16:  # Extremely deep
                evidence_score += 0.1
            elif indent_depth <= 12:  # Moderately deep
                evidence_score -= 0.2
        
        # === STEP 3: CONTEXT CLUES ===
        evidence_score = self._adjust_evidence_for_structure_context(evidence_score, context)
        
        # === STEP 4: DOCUMENT QUALITY INDICATORS ===
        content_type = context.get('content_type', 'general')
        if content_type == 'technical':
            evidence_score += 0.1  # Technical docs need consistent indentation
        elif content_type == 'formal':
            evidence_score += 0.1  # Formal docs need proper indentation
        
        return max(0.0, min(1.0, evidence_score))
    
    def _calculate_consistency_evidence(self, indentation_levels: List[Tuple[int, str, str]], context: Dict[str, Any]) -> float:
        """Calculate evidence for indentation consistency violations."""
        if len(indentation_levels) <= 1:
            return 0.0
        
        # Analyze the variety of indentation patterns
        indent_patterns = set(indent for _, indent, _ in indentation_levels)
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        if len(indent_patterns) == 1:
            return 0.0  # All indentations are consistent
        
        evidence_score = 0.3  # Base evidence for inconsistency
        
        # === STEP 2: PATTERN ANALYSIS ===
        # Check for mixed tabs and spaces
        has_tabs = any('\t' in indent for indent in indent_patterns)
        has_spaces = any(' ' in indent for indent in indent_patterns)
        
        if has_tabs and has_spaces:
            evidence_score += 0.4  # Strong evidence for mixed indentation
        
        # Check for varied space counts
        space_counts = set()
        for indent in indent_patterns:
            if not '\t' in indent:  # Only count space-based indentations
                space_counts.add(len(indent))
        
        if len(space_counts) > 2:  # More than 2 different space counts
            evidence_score += 0.3
        
        # === STEP 3: CONTEXT ADJUSTMENTS ===
        # Lists may legitimately have varied indentation
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['ordered_list', 'unordered_list', 'dlist']:
            evidence_score -= 0.2
        
        # Technical content should be more consistent
        content_type = context.get('content_type', 'general')
        if content_type == 'technical':
            evidence_score += 0.1
        
        return max(0.0, min(1.0, evidence_score))
    
    # === HELPER METHODS ===
    
    def _is_formatted_content(self, match: re.Match, text: str, context: Dict[str, Any]) -> bool:
        """Check if indentation is part of intentional formatting."""
        line = self._get_line_for_match(match, text)
        
        # Check for table-like formatting
        if '|' in line and line.count('|') >= 2:
            return True
        
        # Check for form-like formatting  
        if ':' in line and len(line.split(':')) == 2:
            return True
        
        # Check for ASCII art or diagrams
        special_chars = set('┌┐└┘├┤┬┴┼═║╔╗╚╝╠╣╦╩╬─│+*#')
        if any(char in special_chars for char in line):
            return True
        
        return False
    
    def _get_line_for_match(self, match: re.Match, text: str) -> str:
        """Get the full line containing the match."""
        start_pos = match.start()
        
        # Find the beginning of the line
        line_start = text.rfind('\n', 0, start_pos)
        if line_start == -1:
            line_start = 0
        else:
            line_start += 1
        
        # Find the end of the line
        line_end = text.find('\n', start_pos)
        if line_end == -1:
            line_end = len(text)
        
        return text[line_start:line_end]
    
    def _get_line_number_for_match(self, match: re.Match, text: str) -> int:
        """Get the line number for the match."""
        return text[:match.start()].count('\n')
    
    def _find_most_problematic_indentation(self, indentation_levels: List[Tuple[int, str, str]]) -> Tuple[int, str, str]:
        """Find the most problematic indentation line for error reporting."""
        # Return the first line with mixed indentation, or the first unusual indentation
        for line_num, indent, line in indentation_levels:
            # Check for mixed tabs and spaces
            if '\t' in indent and ' ' in indent:
                return line_num, indent, line
        
        # Return the first odd indentation
        for line_num, indent, line in indentation_levels:
            if not '\t' in indent:  # Space-based indentation
                space_count = len(indent)
                if space_count not in self.standard_indentations and space_count not in [0, 1]:
                    return line_num, indent, line
        
        # Return the first line as fallback
        return indentation_levels[0]
    
    def _get_indentation_severity(self, pattern_name: str, evidence_score: float) -> str:
        """Determine severity based on pattern and evidence."""
        # Mixed indentation is always medium to high severity
        if pattern_name == 'mixed_indentation':
            return 'medium' if evidence_score < 0.8 else 'high'
        
        # Most other issues are low to medium severity
        if evidence_score > 0.8:
            return 'medium'
        elif evidence_score > 0.6:
            return 'low'
        else:
            return 'low'

    # === SMART MESSAGING ===

    def _get_contextual_indentation_message(self, pattern_name: str, evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for indentation violations."""
        confidence_phrase = "clearly has" if evidence_score > 0.8 else ("likely has" if evidence_score > 0.6 else "may have")
        
        messages = {
            'mixed_indentation': f"This content {confidence_phrase} mixed tabs and spaces for indentation.",
            'odd_indentation': f"This line {confidence_phrase} unusual indentation spacing.",
            'excessive_indentation': f"This content {confidence_phrase} excessive indentation depth.",
            'accidental_single_space': f"This line {confidence_phrase} an accidental space at the beginning.",
            'inconsistent_indentation': f"This document {confidence_phrase} inconsistent indentation patterns.",
            'unusual_whitespace': f"This line {confidence_phrase} unusual or invisible whitespace characters."
        }
        
        return messages.get(pattern_name, f"This content {confidence_phrase} an indentation issue.")

    def _generate_smart_indentation_suggestions(self, pattern_name: str, evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for indentation violations."""
        suggestions = []
        
        suggestion_map = {
            'mixed_indentation': [
                "Use consistent indentation (either tabs or spaces, not both).",
                "Configure your editor to show whitespace characters.",
                "Consider using spaces for better compatibility across editors."
            ],
            'odd_indentation': [
                "Use standard indentation levels (2, 4, or 8 spaces).",
                "Align content with standard spacing patterns.",
                "Check if this indentation is intentional for your document type."
            ],
            'excessive_indentation': [
                "Reduce indentation depth for better readability.",
                "Consider restructuring deeply nested content.",
                "Use standard indentation increments."
            ],
            'accidental_single_space': [
                "Remove the accidental space at the beginning of the line.",
                "Check for unintentional leading whitespace.",
                "Use proper indentation if nesting is intended."
            ],
            'inconsistent_indentation': [
                "Use consistent indentation throughout the document.",
                "Choose either tabs or spaces and use consistently.",
                "Configure your editor for consistent indentation."
            ],
            'unusual_whitespace': [
                "Replace unusual whitespace with standard spaces or tabs.",
                "Check for invisible Unicode characters.",
                "Use your editor's 'Show All Characters' feature to identify issues."
            ]
        }
        
        base_suggestions = suggestion_map.get(pattern_name, ["Fix the indentation issue."])
        suggestions.extend(base_suggestions[:2])  # Take first 2 suggestions
        
        # Add confidence-specific suggestions
        if evidence_score > 0.8:
            suggestions.append("This indentation issue should be corrected for document consistency.")
        elif evidence_score > 0.6:
            suggestions.append("Consider fixing this indentation for better formatting.")
        
        # Add context-specific suggestions
        content_type = context.get('content_type', 'general')
        if content_type == 'technical':
            suggestions.append("Technical documentation benefits from consistent indentation.")
        elif content_type == 'formal':
            suggestions.append("Formal documents require proper indentation formatting.")
        
        return suggestions[:3]  # Limit to 3 suggestions
