"""
Base Structure and Format Rule (Enhanced)
Enhanced base class following evidence-based rule development standards.
Provides shared utilities for structure/format rules while enforcing rule-specific evidence calculation.
Each rule must implement its own _calculate_[RULE_TYPE]_evidence() method for optimal precision.
"""

from typing import List, Dict, Any, Optional
import re

# A generic base rule to be inherited from a central location
# in a real application. The # type: ignore comments prevent the
# static type checker from getting confused by the fallback class.
try:
    from ..base_rule import BaseRule  # type: ignore
except ImportError:
    class BaseRule:  # type: ignore
        def _get_rule_type(self) -> str:
            return 'base'
        def _create_error(self, sentence: str, sentence_index: int, message: str, 
                         suggestions: List[str], severity: str = 'medium', 
                         text: Optional[str] = None, context: Optional[Dict[str, Any]] = None,
                         **extra_data) -> Dict[str, Any]:
            """Fallback _create_error implementation when main BaseRule import fails."""
            # Create basic error structure for fallback scenarios
            error = {
                'type': getattr(self, 'rule_type', 'unknown'),
                'message': str(message),
                'suggestions': [str(s) for s in suggestions],
                'sentence': str(sentence),
                'sentence_index': int(sentence_index),
                'severity': severity,
                'enhanced_validation_available': False  # Mark as fallback
            }
            # Add any extra data
            error.update(extra_data)
            return error


class BaseStructureRule(BaseRule):
    """
    Enhanced base class for all structure and format rules.
    Provides shared utilities while enforcing rule-specific evidence calculation.
    
    IMPORTANT: Each rule must implement its own _calculate_[RULE_TYPE]_evidence()
    method rather than using centralized evidence calculation for optimal precision.
    """

    def __init__(self):
        super().__init__()
        self._initialize_structure_anchors()

    def _initialize_structure_anchors(self):
        """Initialize structural and formatting anchors for analysis."""
        
        # Document structure patterns
        self.structure_patterns = {
            'heading_indicators': {
                'markdown_style': re.compile(r'^#{1,6}\s+'),
                'asciidoc_style': re.compile(r'^=+\s+'),
                'underline_style': re.compile(r'^.+\n[-=]+\s*$', re.MULTILINE)
            },
            'list_indicators': {
                'ordered': re.compile(r'^\s*\d+\.\s+'),
                'unordered': re.compile(r'^\s*[-*+]\s+'),
                'definition': re.compile(r'^\s*\w+::\s+')
            },
            'admonition_indicators': {
                'note': re.compile(r'^\s*(NOTE|Note|note)\s*:'),
                'warning': re.compile(r'^\s*(WARNING|Warning|warning)\s*:'),
                'important': re.compile(r'^\s*(IMPORTANT|Important|important)\s*:'),
                'tip': re.compile(r'^\s*(TIP|Tip|tip)\s*:'),
                'caution': re.compile(r'^\s*(CAUTION|Caution|caution)\s*:')
            }
        }
        
        # Formatting quality indicators
        self.formatting_quality = {
            'punctuation_patterns': {
                'sentence_ending': re.compile(r'[.!?]$'),
                'proper_spacing': re.compile(r'\.\s+[A-Z]'),
                'quote_matching': re.compile(r'(["\'"])[^"\']*\1'),
                'parentheses_matching': re.compile(r'\([^)]*\)')
            },
            'capitalization_patterns': {
                'sentence_style': re.compile(r'^[A-Z][^A-Z]*$'),
                'title_case': re.compile(r'^[A-Z][a-z]*(\s+[A-Z][a-z]*)*$'),
                'all_caps': re.compile(r'^[A-Z\s]+$')
            }
        }

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        ABSTRACT: Each rule must implement its own analyze method with evidence-based scoring.
        
        Required implementation pattern:
        1. Find potential issues using rule-specific detection
        2. Calculate evidence using rule-specific _calculate_[RULE_TYPE]_evidence()
        3. Apply zero false positive guards specific to structure/format domain
        4. Use evidence-aware messaging and suggestions
        
        Returns:
            List of errors with rule-specific evidence scores
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement its own analyze() method "
            f"with rule-specific evidence calculation."
        )

    # === SHARED ZERO FALSE POSITIVE GUARDS ===

    def _apply_zero_false_positive_guards_structure(self, violation, context: Dict[str, Any]) -> bool:
        """
        Apply surgical zero false positive guards for structure/format rules.
        Returns True if evidence should be killed immediately.
        
        CRITICAL: These guards must be surgical - eliminate false positives while 
        preserving ALL legitimate violations. Individual rules should extend with 
        rule-specific guards.
        """
        if not violation:
            return True
            
        # === CODE CONTEXT GUARDS ===
        # Code blocks have different formatting rules
        if context and context.get('block_type') in ['code_block', 'inline_code', 'literal_block']:
            return True
            
        # === QUOTED CONTENT GUARDS ===
        # Don't flag formatting in quoted examples or citations
        if self._is_in_quoted_example(violation, context):
            return True
            
        # === METADATA CONTEXT GUARDS ===
        # Front matter, metadata blocks have different formatting rules
        if context and context.get('block_type') in ['metadata', 'front_matter', 'yaml_header']:
            return True
            
        # === URL AND PATH GUARDS ===
        # URLs and file paths have their own formatting rules
        if self._is_url_or_path_context(violation):
            return True
            
        # === TECHNICAL IDENTIFIER GUARDS ===
        # Version numbers, IDs, technical identifiers
        if self._is_technical_identifier(violation):
            return True
            
        # === FOREIGN LANGUAGE GUARDS ===
        # Different languages have different formatting conventions
        if self._is_foreign_language_content(violation, context):
            return True
            
        return False

    def _is_in_quoted_example(self, violation, context: Dict[str, Any]) -> bool:
        """Check if violation appears in quoted example context."""
        if not violation or not hasattr(violation, 'get'):
            return False
        
        text = violation.get('text', violation.get('sentence', ''))
        if not text:
            return False
        
        # Check for quote indicators
        quote_indicators = ['"', "'", '"', '"', '`', '```']
        for indicator in quote_indicators:
            if indicator in text:
                return True
        
        # Check context for example blocks
        if context and context.get('block_type') in ['example', 'quote', 'citation']:
            return True
        
        return False

    def _is_url_or_path_context(self, violation) -> bool:
        """Check if violation involves URLs or file paths."""
        if not violation or not hasattr(violation, 'get'):
            return False
        
        text = violation.get('text', violation.get('sentence', ''))
        if not text:
            return False
        
        # URL patterns
        url_patterns = [
            r'https?://',
            r'ftp://',
            r'www\.',
            r'\.com',
            r'\.org',
            r'\.net'
        ]
        
        # File path patterns
        path_patterns = [
            r'/[a-zA-Z0-9_/-]+',
            r'[a-zA-Z]:\\',
            r'\.[a-zA-Z]{2,4}$',
            r'~/[a-zA-Z0-9_/-]+'
        ]
        
        all_patterns = url_patterns + path_patterns
        
        for pattern in all_patterns:
            if re.search(pattern, text):
                return True
        
        return False

    def _is_technical_identifier(self, violation) -> bool:
        """Check if violation involves technical identifiers."""
        if not violation or not hasattr(violation, 'get'):
            return False
        
        text = violation.get('text', violation.get('sentence', ''))
        if not text:
            return False
        
        # Technical identifier patterns
        tech_patterns = [
            r'v\d+\.\d+',  # Version numbers
            r'\d+\.\d+\.\d+',  # Semantic versions
            r'[A-Z0-9]{8,}',  # IDs, hashes
            r'[a-f0-9]{32,}',  # Hex strings
            r'[A-Z_]{3,}_[A-Z_]{3,}',  # Constants
            r'\$[A-Z_]+',  # Environment variables
        ]
        
        for pattern in tech_patterns:
            if re.search(pattern, text):
                return True
        
        return False

    def _is_foreign_language_content(self, violation, context: Dict[str, Any]) -> bool:
        """Check if violation involves foreign language content."""
        if not context:
            return False
        
        # Check explicit language context
        if context.get('language') and context.get('language') != 'en':
            return True
        
        # Check for foreign language indicators in content type
        content_type = context.get('content_type', '')
        if content_type in ['translation', 'multilingual', 'i18n']:
            return True
        
        return False

    # === SHARED STRUCTURAL ANALYSIS UTILITIES ===

    def _analyze_document_structure(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall document structure for context-aware validation."""
        structure_analysis = {
            'total_length': len(text),
            'paragraph_count': len(text.split('\n\n')),
            'line_count': len(text.split('\n')),
            'has_headings': False,
            'has_lists': False,
            'has_code_blocks': False,
            'document_type': 'unknown'
        }
        
        # Detect headings
        for pattern in self.structure_patterns['heading_indicators'].values():
            if pattern.search(text):
                structure_analysis['has_headings'] = True
                break
        
        # Detect lists
        for pattern in self.structure_patterns['list_indicators'].values():
            if pattern.search(text):
                structure_analysis['has_lists'] = True
                break
        
        # Detect code blocks
        if '```' in text or '    ' in text:  # Code blocks or indented code
            structure_analysis['has_code_blocks'] = True
        
        # Infer document type
        if structure_analysis['has_headings'] and structure_analysis['has_lists']:
            structure_analysis['document_type'] = 'structured_document'
        elif structure_analysis['has_code_blocks']:
            structure_analysis['document_type'] = 'technical_document'
        elif structure_analysis['paragraph_count'] > 5:
            structure_analysis['document_type'] = 'narrative_document'
        else:
            structure_analysis['document_type'] = 'simple_document'
        
        return structure_analysis

    def _get_block_context_clues(self, sentence: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract block-level context clues for evidence calculation."""
        clues = {
            'block_type': context.get('block_type', 'paragraph'),
            'block_level': context.get('block_level', 1),
            'list_depth': context.get('list_depth', 0),
            'is_heading': False,
            'is_list_item': False,
            'is_admonition': False,
            'formatting_context': 'standard'
        }
        
        # Determine if this is a heading
        clues['is_heading'] = clues['block_type'] == 'heading'
        
        # Determine if this is a list item
        clues['is_list_item'] = clues['block_type'] in ['ordered_list_item', 'unordered_list_item']
        
        # Determine if this is an admonition
        clues['is_admonition'] = clues['block_type'] == 'admonition'
        
        # Determine formatting context
        if clues['is_heading']:
            clues['formatting_context'] = 'heading'
        elif clues['is_list_item']:
            clues['formatting_context'] = 'list'
        elif clues['is_admonition']:
            clues['formatting_context'] = 'admonition'
        else:
            clues['formatting_context'] = 'paragraph'
        
        return clues

    def _assess_formatting_quality(self, text: str) -> Dict[str, float]:
        """Assess overall formatting quality for context-aware evidence scoring."""
        quality_scores = {
            'punctuation_consistency': 0.0,
            'capitalization_consistency': 0.0,
            'spacing_consistency': 0.0,
            'overall_quality': 0.0
        }
        
        if not text.strip():
            return quality_scores
        
        sentences = text.split('.')
        if not sentences:
            return quality_scores
        
        # Assess punctuation consistency
        proper_endings = sum(1 for s in sentences if s.strip() and 
                           self.formatting_quality['punctuation_patterns']['sentence_ending'].search(s.strip() + '.'))
        if sentences:
            quality_scores['punctuation_consistency'] = proper_endings / len(sentences)
        
        # Assess capitalization consistency
        proper_caps = sum(1 for s in sentences if s.strip() and s.strip()[0].isupper())
        if sentences:
            quality_scores['capitalization_consistency'] = proper_caps / len(sentences)
        
        # Assess spacing consistency (simplified)
        proper_spacing_matches = len(self.formatting_quality['punctuation_patterns']['proper_spacing'].findall(text))
        sentence_count = len([s for s in sentences if s.strip()])
        if sentence_count > 1:
            quality_scores['spacing_consistency'] = min(1.0, proper_spacing_matches / (sentence_count - 1))
        
        # Calculate overall quality
        quality_scores['overall_quality'] = (
            quality_scores['punctuation_consistency'] * 0.4 +
            quality_scores['capitalization_consistency'] * 0.3 +
            quality_scores['spacing_consistency'] * 0.3
        )
        
        return quality_scores

    # === SHARED EVIDENCE CALCULATION UTILITIES ===

    def _adjust_evidence_for_structure_context(self, base_evidence: float, context: Dict[str, Any]) -> float:
        """Apply structure-specific context adjustments to evidence scores."""
        adjusted_evidence = base_evidence
        
        if not context:
            return adjusted_evidence
        
        block_type = context.get('block_type', 'paragraph')
        
        # Heading context adjustments
        if block_type == 'heading':
            heading_level = context.get('block_level', 1)
            if heading_level == 1:  # H1 - Most visible, stricter standards
                adjusted_evidence *= 1.2
            elif heading_level >= 4:  # H4+ - Less critical
                adjusted_evidence *= 0.9
        
        # List context adjustments
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            adjusted_evidence *= 0.95  # Lists slightly more permissive
            
            # Nested lists even more permissive
            list_depth = context.get('list_depth', 1)
            if list_depth > 1:
                adjusted_evidence *= 0.9
        
        # Admonition context adjustments
        elif block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['WARNING', 'CAUTION', 'DANGER']:
                adjusted_evidence *= 1.1  # Critical admonitions need good formatting
            else:
                adjusted_evidence *= 0.95  # Other admonitions slightly permissive
        
        # Table context adjustments
        elif block_type in ['table_cell', 'table_header']:
            adjusted_evidence *= 0.9  # Tables often use abbreviated formatting
        
        # Quote context adjustments
        elif block_type in ['block_quote', 'citation']:
            adjusted_evidence *= 0.8  # Quotes may preserve original formatting
        
        return max(0.0, min(1.0, adjusted_evidence))

    def _generate_structure_aware_message(self, violation_type: str, evidence_score: float, 
                                        context: Dict[str, Any], **kwargs) -> str:
        """Generate structure-aware error messages based on evidence score."""
        block_context = self._get_block_context_clues(kwargs.get('sentence', ''), context)
        
        # Base message templates
        if evidence_score > 0.8:
            confidence_phrase = "clearly needs"
        elif evidence_score > 0.6:
            confidence_phrase = "should consider"
        else:
            confidence_phrase = "might benefit from"
        
        # Context-specific messaging
        if block_context['is_heading']:
            return f"This heading {confidence_phrase} formatting improvement for {violation_type}."
        elif block_context['is_list_item']:
            return f"This list item {confidence_phrase} better {violation_type} formatting."
        elif block_context['is_admonition']:
            return f"This admonition {confidence_phrase} {violation_type} consistency."
        else:
            return f"This content {confidence_phrase} {violation_type} formatting review."

    def _generate_structure_aware_suggestions(self, violation_type: str, evidence_score: float,
                                            context: Dict[str, Any], **kwargs) -> List[str]:
        """Generate structure-aware suggestions based on evidence confidence."""
        suggestions = []
        block_context = self._get_block_context_clues(kwargs.get('sentence', ''), context)
        
        # Evidence-based suggestion confidence
        if evidence_score > 0.8:
            # High confidence suggestions
            suggestions.append(f"Fix this {violation_type} issue for proper document structure.")
            if block_context['is_heading']:
                suggestions.append("Headings should follow consistent formatting standards.")
            elif block_context['is_list_item']:
                suggestions.append("List items need consistent formatting for readability.")
        
        elif evidence_score > 0.6:
            # Medium confidence suggestions
            suggestions.append(f"Consider improving {violation_type} formatting for better presentation.")
            suggestions.append("Consistent formatting enhances document professionalism.")
        
        else:
            # Low confidence suggestions
            suggestions.append(f"This {violation_type} formatting could be optimized.")
            suggestions.append("Minor formatting improvements enhance overall quality.")
        
        # Add context-specific suggestions
        if block_context['formatting_context'] == 'heading' and evidence_score > 0.7:
            suggestions.append("Headings are highly visible and should use proper formatting.")
        elif block_context['formatting_context'] == 'list' and evidence_score > 0.6:
            suggestions.append("Consistent list formatting improves document structure.")
        
        return suggestions[:3]  # Limit to 3 suggestions

    # === SHARED CONTENT TYPE DETECTION ===

    def _detect_structure_document_type(self, text: str, context: Dict[str, Any]) -> str:
        """Detect document type for structure-aware validation."""
        if not text:
            return 'unknown'
        
        # Check explicit context
        content_type = context.get('content_type', 'general')
        if content_type != 'general':
            return content_type
        
        text_lower = text.lower()
        
        # Technical documentation indicators
        tech_indicators = ['api', 'sdk', 'configuration', 'installation', 'setup']
        if sum(1 for indicator in tech_indicators if indicator in text_lower) >= 2:
            return 'technical'
        
        # User documentation indicators
        user_indicators = ['how to', 'guide', 'tutorial', 'instructions']
        if sum(1 for indicator in user_indicators if indicator in text_lower) >= 1:
            return 'user_guide'
        
        # Reference documentation indicators
        ref_indicators = ['reference', 'specification', 'manual']
        if sum(1 for indicator in ref_indicators if indicator in text_lower) >= 1:
            return 'reference'
        
        # Procedural documentation indicators
        proc_indicators = ['step', 'procedure', 'process', 'workflow']
        if sum(1 for indicator in proc_indicators if indicator in text_lower) >= 2:
            return 'procedural'
        
        return 'general'
