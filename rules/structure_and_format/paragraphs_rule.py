"""
Paragraphs Rule (Enhanced with Evidence-Based Analysis)
Based on IBM Style Guide topic: "Paragraphs"
Enhanced to follow evidence-based rule development methodology for zero false positives.
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

class ParagraphsRule(BaseStructureRule):
    """
    Checks for paragraph formatting issues using evidence-based analysis with surgical precision.
    Implements rule-specific evidence calculation for optimal false positive reduction.
    
    Violations detected:
    - Inappropriate paragraph indentation
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'paragraphs'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes paragraphs for formatting violations using evidence-based scoring.
        Each potential violation gets nuanced evidence assessment for precision.
        """
        errors = []
        if not context:
            return errors

        # This rule operates on the structural node provided by the parser.
        paragraph_node = context.get('node')
        if not paragraph_node or paragraph_node.node_type != 'paragraph':
            return errors

        # The structural parser must provide indentation information.
        # We assume the parser adds an 'indent' attribute to the node.
        indentation = getattr(paragraph_node, 'indent', 0)

        # === EVIDENCE-BASED ANALYSIS: Paragraph Indentation ===
        if indentation > 0:
            evidence_score = self._calculate_indentation_evidence(
                indentation, text, sentences, context
            )
            
            if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                errors.append(self._create_error(
                    sentence=sentences[0] if sentences else text,
                    sentence_index=0,
                    message=self._get_contextual_message('paragraph_indentation', evidence_score, context, indentation=indentation),
                    suggestions=self._generate_smart_suggestions('paragraph_indentation', evidence_score, context, indentation=indentation),
                    severity='low',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=(0, indentation),
                    flagged_text=text[:indentation] if indentation <= len(text) else text
                ))
            
        return errors

    # === EVIDENCE CALCULATION METHODS ===

    def _calculate_indentation_evidence(self, indentation: int, text: str, 
                                       sentences: List[str], context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for potential paragraph indentation violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            indentation: Amount of indentation detected
            text: Paragraph text content
            sentences: List of sentences in paragraph
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === ZERO FALSE POSITIVE GUARDS ===
        # CRITICAL: Apply rule-specific guards FIRST to eliminate common exceptions
        
        # Kill evidence immediately for contexts where this specific rule should never apply
        if not context:
            return 0.0  # No context available
        
        # Don't flag paragraphs in actual code blocks
        if self._is_paragraph_in_actual_code_block(text, context):
            return 0.0  # Code blocks have their own indentation rules
        
        # Don't flag paragraphs in quoted examples or citations
        if self._is_paragraph_in_actual_quotes(text, context):
            return 0.0  # Quoted examples are not formatting errors
        
        # Don't flag paragraphs in technical documentation contexts with approved patterns
        if self._is_paragraph_in_technical_context(text, context):
            return 0.0  # Technical docs may use different conventions
        
        # Apply inherited zero false positive guards
        violation = {'text': text, 'indentation': indentation}
        if self._apply_zero_false_positive_guards_structure(violation, context):
            return 0.0
        
        # Special guard: List items or nested content where indentation is semantic
        if self._is_semantic_indentation_context(text, context):
            return 0.0
        
        # Special guard: Poetry, dialogue, or formatted content
        if self._is_intentional_formatting_context(text, context):
            return 0.0
        
        # Special guard: Legacy document formats that traditionally use indentation
        if self._is_legacy_format_context(context):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_indentation_base_evidence_score(indentation, text, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this paragraph
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        # Check indentation amount specificity
        if indentation > 8:  # More than 2 standard tabs - very problematic
            evidence_score += 0.2
        elif indentation <= 2:  # Minor indentation - less problematic
            evidence_score -= 0.1
        
        # Check for text content patterns that suggest intentional formatting
        if self._has_structural_text_patterns(text):
            evidence_score -= 0.2  # Structured content might legitimately use indentation
        
        # Check for paragraph starting patterns
        first_sentence = sentences[0] if sentences else text
        if self._starts_with_continuation_pattern(first_sentence):
            evidence_score -= 0.1  # Might be legitimate continuation
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._adjust_evidence_for_structure_context(evidence_score, context)
        
        # Document structure analysis
        doc_type = self._detect_structure_document_type(text, context)
        if doc_type in ['technical', 'reference']:
            evidence_score -= 0.1  # Technical docs might have legitimate indentation
        elif doc_type in ['formal', 'business']:
            evidence_score += 0.1  # Formal docs should follow strict formatting
        
        # Block context analysis
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['sidebar', 'callout', 'note']:
            evidence_score -= 0.2  # Special blocks may use indentation
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        # Content type adjustments
        content_type = context.get('content_type', 'general')
        if content_type in ['formal', 'professional']:
            evidence_score += 0.1  # Formal docs should follow strict formatting
        elif content_type in ['creative', 'narrative']:
            evidence_score -= 0.2  # Creative content might use indentation stylistically
        elif content_type in ['technical', 'reference']:
            evidence_score -= 0.1  # Technical content more flexible
        
        # Document format considerations
        format_type = context.get('format', 'general')
        if format_type in ['email', 'letter']:
            evidence_score -= 0.3  # Traditional formats might use indentation
        elif format_type in ['manual', 'guide']:
            evidence_score += 0.1  # Guides should follow consistent formatting
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_indentation(evidence_score, indentation, text, context)
        
        # Paragraph indentation-specific final adjustments (moderate to avoid evidence inflation)
        evidence_score += 0.05  # IBM Style Guide is clear on no indentation
        
        return max(0.0, min(1.0, evidence_score))

    # === ENHANCED HELPER METHODS FOR 6-STEP EVIDENCE PATTERN ===
    
    def _is_paragraph_in_actual_code_block(self, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Surgical check: Is the paragraph actually within a code block?
        Only returns True for genuine code content, not incidental code references.
        """
        if not context:
            return False
        
        # Check context block type for explicit code blocks
        block_type = context.get('block_type', '')
        if block_type in ['code_block', 'literal_block', 'code_fence', 'pre_block']:
            return True
        
        # Check for code fence markers
        if text.strip().startswith('```') or text.strip().endswith('```'):
            return True
        
        # Check for substantial code patterns (not just references)
        code_patterns = [
            r'function\s+\w+\s*\(',  # Function definitions
            r'class\s+\w+\s*[:{]',   # Class definitions
            r'def\s+\w+\s*\(',       # Python function definitions
            r'var\s+\w+\s*=',        # Variable declarations
            r'const\s+\w+\s*=',      # Constant declarations
            r'let\s+\w+\s*=',        # Let declarations
            r'import\s+\w+',         # Import statements
            r'from\s+\w+\s+import',  # From imports
            r'#include\s*<',         # C/C++ includes
        ]
        
        import re
        code_pattern_count = sum(1 for pattern in code_patterns if re.search(pattern, text))
        
        # If multiple code patterns, likely actual code
        if code_pattern_count >= 2:
            return True
        
        # Check for high density of technical symbols
        technical_chars = ['{', '}', ';', '->', '=>', '&&', '||', '!=', '==', '++', '--']
        tech_char_density = sum(text.count(char) for char in technical_chars) / max(len(text), 1)
        
        if tech_char_density > 0.1:  # High density suggests code
            return True
        
        return False
    
    def _is_paragraph_in_actual_quotes(self, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Surgical check: Is the paragraph actually within quotation marks or block quotes?
        Only returns True for genuine quoted content, not incidental quote references.
        """
        if not context:
            return False
        
        # Check context block type for explicit quotes
        block_type = context.get('block_type', '')
        if block_type in ['block_quote', 'quote', 'citation', 'blockquote']:
            return True
        
        # Check for quote block markers
        stripped_text = text.strip()
        if stripped_text.startswith(('>', '> ', '>> ', '>>> ')):
            return True
        
        # Check for enclosing quotation marks (full paragraph quoted)
        if ((stripped_text.startswith(('"', '"', '"')) and stripped_text.endswith(('"', '"', '"'))) or
            (stripped_text.startswith(("'", "'", "'")) and stripped_text.endswith(("'", "'", "'")))):
            # Ensure it's not just a sentence with quotes
            if len(stripped_text) > 50:  # Substantial quoted content
                return True
        
        # Check for citation or attribution patterns (only at beginning or with clear citation context)
        citation_patterns = [
            'according to', 'as stated by', 'quoted from', 'citation:',
            'source:', 'reference:', 'excerpt from', 'from the'
        ]
        
        text_lower = text.lower()
        # Only trigger for citations at the beginning of sentences or with clear citation punctuation
        for pattern in citation_patterns:
            if pattern in text_lower:
                # Check if it's actually a citation (not just mentioning something)
                pattern_index = text_lower.find(pattern)
                if pattern_index <= 10 or text_lower[pattern_index-1:pattern_index+1] in ['. ', ': ', '- ']:
                    return True
        
        return False
    
    def _is_paragraph_in_technical_context(self, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if paragraph appears in technical documentation context with approved patterns.
        """
        if not context:
            return False
        
        # Check content type for technical context
        content_type = context.get('content_type', '')
        if content_type in ['technical', 'api', 'reference', 'developer']:
            # In technical docs, check for specific patterns that use indentation semantically
            technical_indentation_patterns = [
                'parameter:', 'returns:', 'arguments:', 'options:', 'properties:',
                'example:', 'usage:', 'syntax:', 'format:', 'structure:'
            ]
            
            text_lower = text.lower()
            if any(pattern in text_lower for pattern in technical_indentation_patterns):
                return True
        
        # Check for API documentation patterns
        api_patterns = [
            r'[A-Z_]+\s*=\s*',       # Constants
            r'@\w+\s*\(',             # Decorators/annotations
            r'\w+\.\w+\.\w+',         # Module paths
            r'HTTP\s+(GET|POST|PUT|DELETE|PATCH)',  # HTTP methods
            r'status\s+code\s+\d+',   # Status codes
        ]
        
        import re
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in api_patterns):
            return True
        
        return False
    
    def _is_semantic_indentation_context(self, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if indentation is semantic (meaningful for content structure).
        """
        if not context:
            return False
        
        # Check for list context where indentation indicates hierarchy
        block_type = context.get('block_type', '')
        if 'list' in block_type:
            list_depth = context.get('list_depth', 0)
            if list_depth > 1:
                return True
        
        # Check for outline or hierarchical content
        if text.strip().startswith(('1.', '2.', '3.', 'a.', 'b.', 'c.', 'i.', 'ii.', 'iii.')):
            return True
        
        # Check for definition lists or structured content
        if ':' in text and len(text.split(':')) == 2:
            term, definition = text.split(':', 1)
            if len(term.strip()) < 50 and len(definition.strip()) > len(term.strip()):
                return True  # Likely definition list
        
        # Check for table of contents or index patterns
        if '...' in text or '.....' in text:
            return True  # TOC dots
        
        return False
    
    def _is_intentional_formatting_context(self, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if paragraph uses intentional formatting (poetry, dialogue, addresses).
        """
        # Poetry or verse formatting
        lines = text.split('\n')
        if len(lines) > 1:
            # Check for verse patterns - short lines with rhythmic endings
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            if len(non_empty_lines) >= 2:
                # All lines should be relatively short for poetry
                if all(len(line) < 60 for line in non_empty_lines):
                    # Check for common poetry patterns
                    poetry_indicators = [
                        # Rhyming patterns
                        any(line.endswith(('red', 'blue', 'you', 'too')) for line in non_empty_lines),
                        # Rhythmic endings
                        any(line.endswith(('ing', 'ed', 'er', 'ly')) for line in non_empty_lines),
                        # Poetry content words
                        any(word in text.lower() for word in ['roses', 'violets', 'poetry', 'verse']),
                        # Multiple lines with similar length (common in poetry)
                        len(set(len(line) for line in non_empty_lines)) <= 3
                    ]
                    if any(poetry_indicators):
                        return True
        
        # Dialogue or script formatting
        if text.count(':') > 1:
            colon_density = text.count(':') / max(len(text.split()), 1)
            if colon_density > 0.2:  # High colon density suggests dialogue
                return True
        
        # Address or contact information formatting
        address_indicators = [
            'street', 'avenue', 'road', 'lane', 'drive', 'boulevard',
            'city', 'state', 'zip', 'postal', 'phone', 'email', 'fax',
            'suite', 'apt', 'apartment', 'building', 'floor'
        ]
        text_lower = text.lower()
        address_matches = sum(1 for indicator in address_indicators if indicator in text_lower)
        if address_matches >= 2:
            return True
        
        # Letter or formal document formatting
        formal_patterns = [
            'dear ', 'sincerely', 'regards', 'yours truly', 'respectfully',
            'to whom it may concern', 'best regards', 'kind regards'
        ]
        if any(pattern in text_lower for pattern in formal_patterns):
            return True
        
        return False
    
    def _is_legacy_format_context(self, context: Dict[str, Any] = None) -> bool:
        """
        Check if document is in a legacy format that traditionally uses indentation.
        """
        if not context:
            return False
        
        # Document format types that traditionally use indentation
        format_type = context.get('format', '')
        if format_type in ['letter', 'memo', 'manuscript', 'academic', 'thesis']:
            return True
        
        # Content types that might use traditional formatting
        content_type = context.get('content_type', '')
        if content_type in ['academic', 'literary', 'manuscript', 'correspondence']:
            return True
        
        # Check for document metadata indicating legacy format
        doc_style = context.get('document_style', '')
        if doc_style in ['traditional', 'classic', 'formal_letter', 'academic_paper']:
            return True
        
        return False
    
    def _get_indentation_base_evidence_score(self, indentation: int, text: str, context: Dict[str, Any] = None) -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Large indentation (>8 spaces) → 0.8 (very specific)
        - Standard indentation (4-8 spaces) → 0.7 (clear pattern)
        - Minor indentation (1-3 spaces) → 0.5 (ambiguous)
        """
        if indentation <= 0:
            return 0.0  # No indentation, no violation
        
        # Enhanced specificity analysis
        if self._is_exact_indentation_violation(indentation, text):
            return 0.8  # Very specific, clear violation
        elif self._is_pattern_indentation_violation(indentation, text):
            return 0.6  # Pattern-based, moderate specificity  
        elif self._is_minor_indentation_issue(indentation, text):
            return 0.4  # Minor issue, needs context
        else:
            return 0.3  # Possible issue, needs more evidence
    
    def _has_structural_text_patterns(self, text: str) -> bool:
        """
        Check if text has patterns suggesting structural/semantic indentation.
        """
        # Check for numbered or lettered sections
        if text.strip().startswith(('1.', '2.', '3.', 'a.', 'b.', 'c.', 'i.', 'ii.', 'A.', 'B.')):
            return True
        
        # Check for definition or glossary patterns
        if ':' in text:
            parts = text.split(':', 1)
            if len(parts) == 2 and len(parts[0].strip()) < 50:
                return True  # Likely term: definition
        
        # Check for code or technical documentation patterns
        technical_patterns = ['function', 'class', 'method', 'property', 'parameter', 'returns']
        text_lower = text.lower()
        if any(pattern in text_lower for pattern in technical_patterns):
            return True
        
        return False
    
    def _starts_with_continuation_pattern(self, sentence: str) -> bool:
        """
        Check if sentence starts with patterns suggesting continuation.
        """
        continuation_patterns = [
            'and ', 'but ', 'however ', 'therefore ', 'thus ', 'furthermore ',
            'moreover ', 'additionally ', 'also ', 'likewise ', 'similarly ',
            'in addition', 'on the other hand', 'for example', 'for instance'
        ]
        
        sentence_lower = sentence.lower().strip()
        return any(sentence_lower.startswith(pattern) for pattern in continuation_patterns)
    
    def _is_exact_indentation_violation(self, indentation: int, text: str) -> bool:
        """
        Check if indentation represents an exact formatting violation.
        """
        # Large indentation is clearly problematic
        if indentation > 8:
            return True
        
        # Standard tab indentation (4 spaces) in paragraph context
        if indentation == 4 and not self._has_structural_text_patterns(text):
            return True
        
        # Multiple of standard indentation without structural justification
        if indentation % 4 == 0 and indentation > 0 and not self._has_structural_text_patterns(text):
            return True
        
        return False
    
    def _is_pattern_indentation_violation(self, indentation: int, text: str) -> bool:
        """
        Check if indentation shows a pattern of formatting violation.
        """
        # Medium indentation (2-6 spaces) without clear purpose
        if 2 <= indentation <= 6 and not self._has_structural_text_patterns(text):
            return True
        
        # Odd number of spaces (suggesting accidental indentation)
        if indentation % 2 == 1 and indentation > 1:
            return True
        
        return False
    
    def _is_minor_indentation_issue(self, indentation: int, text: str) -> bool:
        """
        Check if indentation has minor formatting issues.
        """
        # Single space indentation (might be accidental)
        if indentation == 1:
            return True
        
        # Small indentation that might be intentional formatting
        if 2 <= indentation <= 3 and len(text.strip()) > 50:
            return True
        
        return False
    
    def _apply_feedback_clues_indentation(self, evidence_score: float, indentation: int, text: str, context: Dict[str, Any] = None) -> float:
        """
        Apply clues learned from user feedback patterns specific to paragraph indentation.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_paragraphs()
        
        # Consistently Accepted Indented Paragraphs
        paragraph_signature = self._get_paragraph_signature(text, indentation)
        if paragraph_signature in feedback_patterns.get('accepted_indented_paragraphs', set()):
            evidence_score -= 0.5  # Users consistently accept this indentation
        
        # Consistently Rejected Suggestions
        if paragraph_signature in feedback_patterns.get('rejected_indentation_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: Indentation amount acceptance rates
        indent_acceptance = feedback_patterns.get('indentation_acceptance', {})
        
        if indentation <= 2:
            acceptance_rate = indent_acceptance.get('small', 0.4)
        elif indentation <= 4:
            acceptance_rate = indent_acceptance.get('medium', 0.2)
        elif indentation <= 8:
            acceptance_rate = indent_acceptance.get('large', 0.1)
        else:
            acceptance_rate = indent_acceptance.get('very_large', 0.05)
        
        if acceptance_rate > 0.7:
            evidence_score -= 0.4  # High acceptance, likely valid in some contexts
        elif acceptance_rate < 0.2:
            evidence_score += 0.2  # Low acceptance, strong violation
        
        # Pattern: Content type specific acceptance
        content_type = context.get('content_type', 'general') if context else 'general'
        content_patterns = feedback_patterns.get(f'{content_type}_indentation_acceptance', {})
        
        indent_category = self._categorize_indentation_amount(indentation)
        acceptance_rate = content_patterns.get(indent_category, 0.3)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Accepted in this content type
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Consistently flagged in this content type
        
        # Pattern: Document format acceptance
        format_type = context.get('format', 'general') if context else 'general'
        format_patterns = feedback_patterns.get(f'{format_type}_indentation_acceptance', {})
        
        acceptance_rate = format_patterns.get(indent_category, 0.3)
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # Highly accepted in this format
        elif acceptance_rate < 0.2:
            evidence_score += 0.3  # Consistently rejected in this format
        
        # Pattern: Text length vs indentation acceptance
        text_length = len(text.split())
        length_patterns = feedback_patterns.get('text_length_indentation_acceptance', {})
        
        if text_length <= 10:
            acceptance_rate = length_patterns.get('short', 0.5)
        elif text_length <= 50:
            acceptance_rate = length_patterns.get('medium', 0.3)
        else:
            acceptance_rate = length_patterns.get('long', 0.2)
        
        if acceptance_rate > 0.6:
            evidence_score -= 0.2
        elif acceptance_rate < 0.3:
            evidence_score += 0.1
        
        return evidence_score
    
    def _get_paragraph_signature(self, text: str, indentation: int) -> str:
        """
        Generate a signature for the paragraph for feedback analysis.
        """
        # Create a simplified signature based on content patterns
        first_words = ' '.join(text.split()[:5]) if text.split() else ''
        indent_category = self._categorize_indentation_amount(indentation)
        text_length_category = 'short' if len(text.split()) <= 20 else 'medium' if len(text.split()) <= 50 else 'long'
        
        return f"{indent_category}_{text_length_category}_{hash(first_words) % 1000}"
    
    def _categorize_indentation_amount(self, indentation: int) -> str:
        """
        Categorize indentation amount for feedback analysis.
        """
        if indentation <= 2:
            return 'minimal'
        elif indentation <= 4:
            return 'standard'
        elif indentation <= 8:
            return 'large'
        else:
            return 'excessive'
    
    def _get_cached_feedback_patterns_paragraphs(self) -> Dict[str, Any]:
        """
        Load feedback patterns from cache or feedback analysis for paragraph indentation.
        """
        # This would load from feedback analysis system
        # For now, return basic patterns with some realistic examples
        return {
            'accepted_indented_paragraphs': set(),  # Specific paragraph signatures users accept
            'rejected_indentation_suggestions': set(),  # Paragraphs users don't want flagged
            'indentation_acceptance': {
                'small': 0.4,     # 1-2 spaces sometimes acceptable
                'medium': 0.2,    # 3-4 spaces rarely acceptable  
                'large': 0.1,     # 5-8 spaces almost never acceptable
                'very_large': 0.05  # >8 spaces virtually never acceptable
            },
            'formal_indentation_acceptance': {
                'minimal': 0.3,   # Formal docs less tolerant of indentation
                'standard': 0.1,  # Standard indentation rarely acceptable in formal
                'large': 0.05,    # Large indentation almost never acceptable
                'excessive': 0.01 # Excessive indentation never acceptable
            },
            'creative_indentation_acceptance': {
                'minimal': 0.6,   # Creative writing more tolerant
                'standard': 0.4,  # Standard indentation sometimes acceptable
                'large': 0.2,     # Large indentation sometimes used stylistically
                'excessive': 0.1  # Even excessive might be stylistic
            },
            'technical_indentation_acceptance': {
                'minimal': 0.5,   # Technical docs moderately tolerant
                'standard': 0.3,  # Standard indentation sometimes used for hierarchy
                'large': 0.15,    # Large indentation occasionally used
                'excessive': 0.05 # Excessive rarely justified
            },
            'letter_indentation_acceptance': {
                'minimal': 0.7,   # Letters traditionally use some indentation
                'standard': 0.8,  # Standard indentation very acceptable in letters
                'large': 0.6,     # Large indentation acceptable in formal letters
                'excessive': 0.3  # Even excessive might be traditional formatting
            },
            'email_indentation_acceptance': {
                'minimal': 0.4,   # Emails less formal than letters
                'standard': 0.6,  # Standard indentation acceptable in emails
                'large': 0.4,     # Large indentation sometimes used
                'excessive': 0.2  # Excessive might be reply formatting
            },
            'manual_indentation_acceptance': {
                'minimal': 0.2,   # Manuals should follow strict formatting
                'standard': 0.1,  # Standard indentation rarely acceptable
                'large': 0.05,    # Large indentation almost never acceptable
                'excessive': 0.01 # Excessive indentation never acceptable
            },
            'text_length_indentation_acceptance': {
                'short': 0.5,     # Short paragraphs more tolerant
                'medium': 0.3,    # Medium paragraphs standard tolerance
                'long': 0.2       # Long paragraphs less tolerant
            }
        }

    # === CONTEXTUAL MESSAGING AND SUGGESTIONS ===

    def _get_contextual_message(self, violation_type: str, evidence_score: float, 
                               context: Dict[str, Any], **kwargs) -> str:
        """Generate contextual error messages based on violation type and evidence."""
        if violation_type == 'paragraph_indentation':
            indentation = kwargs.get('indentation', 0)
            
            if evidence_score > 0.8:
                return f"Paragraph indentation of {indentation} spaces violates IBM Style Guide formatting standards."
            elif evidence_score > 0.6:
                return f"Consider removing the {indentation}-space indentation for consistency with style guidelines."
            elif evidence_score > 0.4:
                return f"This paragraph indentation ({indentation} spaces) may not follow standard formatting."
            else:
                return f"The {indentation}-space paragraph indentation could be reviewed for style consistency."
        
        return "Paragraph formatting issue detected."

    def _generate_smart_suggestions(self, violation_type: str, evidence_score: float,
                                  context: Dict[str, Any], **kwargs) -> List[str]:
        """Generate smart suggestions based on violation type and evidence confidence."""
        suggestions = []
        
        if violation_type == 'paragraph_indentation':
            indentation = kwargs.get('indentation', 0)
            
            if evidence_score > 0.8:
                # High evidence = authoritative, direct suggestions
                suggestions.append(f"Remove all {indentation} spaces from the paragraph beginning immediately.")
                suggestions.append("IBM Style Guide requires flush-left paragraph formatting.")
                suggestions.append("Consistent formatting is essential for professional documentation.")
            elif evidence_score > 0.6:
                # Medium evidence = balanced, helpful suggestions  
                suggestions.append(f"Consider removing the {indentation}-space indentation.")
                suggestions.append("Use paragraph spacing instead of indentation to separate paragraphs.")
                suggestions.append("Flush-left formatting improves readability and consistency.")
            elif evidence_score > 0.4:
                # Medium-low evidence = gentle suggestions
                suggestions.append(f"The {indentation}-space indentation might be unnecessary.")
                suggestions.append("Review if this indentation serves a specific formatting purpose.")
                suggestions.append("Consider aligning with standard paragraph formatting guidelines.")
            else:
                # Low evidence = very gentle suggestions
                suggestions.append(f"This {indentation}-space indentation may be acceptable depending on context.")
                suggestions.append("Verify if this formatting follows your document style requirements.")
                suggestions.append("Consider consistency with other paragraphs in the document.")
            
            # Context-specific suggestions
            content_type = context.get('content_type', '') if context else ''
            if content_type == 'formal' and evidence_score > 0.6:
                suggestions.append("Formal documents should follow strict formatting guidelines.")
            elif content_type == 'technical' and evidence_score > 0.5:
                suggestions.append("Technical documentation benefits from consistent formatting.")
            
            # Format-specific suggestions  
            format_type = context.get('format', '') if context else ''
            if format_type in ['letter', 'email'] and evidence_score < 0.7:
                suggestions.append("Traditional letter formats may appropriately use paragraph indentation.")
        
        return suggestions[:3]  # Limit to 3 suggestions