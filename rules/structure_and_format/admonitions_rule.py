"""
Admonitions Rule (Enhanced with Evidence-Based Analysis)
Based on IBM Style Guide topic: "Notes"
Enhanced to follow evidence-based rule development methodology for zero false positives.
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class AdmonitionsRule(BaseStructureRule):
    """
    Checks for style issues within admonition blocks using evidence-based analysis with surgical precision.
    Implements rule-specific evidence calculation for optimal false positive reduction.
    
    Violations detected:
    - Invalid admonition labels not in approved list
    - Incomplete sentences within admonitions
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'admonitions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes admonitions for style violations using evidence-based scoring.
        Each potential violation gets nuanced evidence assessment for precision.
        """
        errors = []
        if not nlp or not context or context.get('block_type') != 'admonition':
            return errors

        admonition_kind = context.get('kind', '').upper()
        
        # Linguistic Anchor: A set of approved labels from the IBM Style Guide.
        approved_labels = {
            'NOTE', 'IMPORTANT', 'RESTRICTION', 'TIP', 'ATTENTION', 
            'CAUTION', 'DANGER', 'REQUIREMENT', 'EXCEPTION', 'FAST PATH', 'REMEMBER'
        }

        # === EVIDENCE-BASED ANALYSIS 1: Invalid Labels ===
        if admonition_kind not in approved_labels:
            evidence_score = self._calculate_invalid_label_evidence(
                admonition_kind, approved_labels, text, context
            )
            
            if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                errors.append(self._create_error(
                    sentence=text,
                    sentence_index=0,
                    message=self._get_contextual_message('invalid_label', evidence_score, context, kind=admonition_kind),
                    suggestions=self._generate_smart_suggestions('invalid_label', evidence_score, context, kind=admonition_kind),
                    severity='medium',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=(0, len(admonition_kind) + 2),
                    flagged_text=f"[{admonition_kind}]"
                ))

        # === EVIDENCE-BASED ANALYSIS 2: Incomplete Sentences ===
        doc = nlp(text)
        if not self._is_complete_sentence(doc):
            evidence_score = self._calculate_incomplete_sentence_evidence(
                text, doc, context
            )
            
            if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                errors.append(self._create_error(
                    sentence=text,
                    sentence_index=0,
                    message=self._get_contextual_message('incomplete_sentence', evidence_score, context),
                    suggestions=self._generate_smart_suggestions('incomplete_sentence', evidence_score, context),
                    severity='low',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=(0, len(text)),
                    flagged_text=text
                ))

        return errors

    # === EVIDENCE CALCULATION METHODS ===

    def _calculate_invalid_label_evidence(self, admonition_kind: str, approved_labels: set, 
                                        text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for potential invalid admonition label violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            admonition_kind: The detected admonition label
            approved_labels: Set of approved IBM Style Guide labels
            text: Admonition text content
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === ZERO FALSE POSITIVE GUARDS ===
        # CRITICAL: Apply rule-specific guards FIRST to eliminate common exceptions
        
        # Kill evidence immediately for contexts where this specific rule should never apply
        if context and context.get('block_type') not in ['admonition', 'note', 'callout']:
            return 0.0  # Only apply to admonition-type blocks
        
        # Don't flag admonitions in quoted examples
        if self._is_admonition_in_actual_quotes(admonition_kind, text, context):
            return 0.0  # Quoted examples are not admonition errors
        
        # Don't flag admonitions in technical documentation contexts with approved custom types
        if self._is_admonition_in_technical_context(admonition_kind, text, context):
            return 0.0  # Technical docs may use different conventions
        
        # Don't flag admonitions in citation or reference context
        if self._is_admonition_in_citation_context(admonition_kind, text, context):
            return 0.0  # Academic papers, documentation references, etc.
        
        # Apply inherited zero false positive guards
        violation = {'text': admonition_kind, 'sentence': text}
        if self._apply_zero_false_positive_guards_structure(violation, context):
            return 0.0
        
        # Special guard: Custom admonition types in specific domains
        if self._is_legitimate_custom_admonition(admonition_kind, context):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_admonition_label_base_evidence_score(admonition_kind, approved_labels, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this admonition
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        # Check if it's a close match to approved labels
        for approved in approved_labels:
            if admonition_kind.lower() in approved.lower() or approved.lower() in admonition_kind.lower():
                evidence_score -= 0.2  # Might be slight variation
                break
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._adjust_evidence_for_structure_context(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        # Content type adjustments
        content_type = context.get('content_type', 'general')
        if content_type in ['technical', 'api']:
            evidence_score -= 0.1  # Technical docs might have custom labels
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_admonitions(evidence_score, admonition_kind, context)
        
        # Admonition-specific final adjustments (moderate to avoid evidence inflation)
        evidence_score += 0.1  # Label consistency is important but context-dependent
        
        return max(0.0, min(1.0, evidence_score))

    def _calculate_incomplete_sentence_evidence(self, text: str, doc: 'Doc', 
                                              context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for potential incomplete sentence violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            text: Admonition text content
            doc: SpaCy document
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === ZERO FALSE POSITIVE GUARDS ===
        # CRITICAL: Apply rule-specific guards FIRST to eliminate common exceptions
        
        # Kill evidence immediately for contexts where this specific rule should never apply
        if context and context.get('block_type') not in ['admonition', 'note', 'callout']:
            return 0.0  # Only apply to admonition-type blocks
        
        # Don't flag fragments in quoted examples
        if self._is_sentence_in_actual_quotes(text, context):
            return 0.0  # Quoted examples are not sentence structure errors
        
        # Don't flag fragments in technical reference contexts
        if self._is_sentence_in_technical_context(text, doc, context):
            return 0.0  # Technical docs may use different conventions
        
        # Don't flag fragments in citation or reference context
        if self._is_sentence_in_citation_context(text, context):
            return 0.0  # Academic papers, documentation references, etc.
        
        # Apply inherited zero false positive guards
        violation = {'text': text, 'sentence': text}
        if self._apply_zero_false_positive_guards_structure(violation, context):
            return 0.0
        
        # Special guard: Short technical terms or references
        if self._is_legitimate_fragment(text, doc, context):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_incomplete_sentence_base_evidence_score(text, doc, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this sentence
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        # Very short text might be acceptable
        if len(text.split()) <= 3:
            evidence_score -= 0.3
        
        # Check for technical patterns that might be acceptable
        if self._has_technical_reference_pattern(text):
            evidence_score -= 0.2
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._adjust_evidence_for_structure_context(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        # Content type adjustments
        content_type = context.get('content_type', 'general')
        if content_type in ['reference', 'api']:
            evidence_score -= 0.2  # Reference docs might have fragments
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_sentences(evidence_score, text, context)
        
        # Incomplete sentence-specific final adjustments (moderate to avoid evidence inflation)
        evidence_score += 0.05  # Sentence completeness is important but context-dependent
        
        return max(0.0, min(1.0, evidence_score))

    # === HELPER METHODS ===

    def _is_complete_sentence(self, doc: Doc) -> bool:
        """
        Uses dependency parsing to check if the text forms a complete sentence.
        Enhanced to properly detect imperative sentences.
        """
        if not doc or len(doc) < 1:
            return False
        
        # Single word is generally not a complete sentence
        if len([token for token in doc if token.pos_ not in ['PUNCT', 'SPACE']]) < 2:
            return False
            
        has_root = any(token.dep_ == 'ROOT' for token in doc)
        if not has_root:
            return False
        
        # Find the root verb
        root_token = next((token for token in doc if token.dep_ == 'ROOT'), None)
        if not root_token:
            return False
        
        # Check for explicit subject
        has_subject = any(token.dep_ in ('nsubj', 'nsubjpass', 'csubj') for token in doc)
        
        # Check for imperative sentences (commands)
        # Imperative sentences have a root verb without an explicit subject
        is_imperative = (root_token.pos_ == 'VERB' and 
                        not has_subject and
                        root_token.tag_ in ['VB', 'VBP'])  # Base form or present tense
        
        # Check for other sentence patterns
        # Sentences with "there" as existential subject
        has_existential = any(token.dep_ == 'expl' for token in doc)
        
        return has_subject or is_imperative or has_existential

    def _is_legitimate_custom_admonition(self, admonition_kind: str, context: Dict[str, Any]) -> bool:
        """Check if custom admonition type is legitimate in this context."""
        # Some technical documentation might have domain-specific admonitions
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        
        # Technical domains might have specialized admonitions
        if content_type == 'technical' and admonition_kind.upper() in ['SECURITY', 'PERFORMANCE', 'COMPATIBILITY']:
            return True
        
        # Software documentation might have specialized types
        if domain == 'software' and admonition_kind.upper() in ['DEPRECATED', 'EXPERIMENTAL', 'BETA']:
            return True
        
        return False

    def _is_legitimate_fragment(self, text: str, doc: 'Doc', context: Dict[str, Any]) -> bool:
        """Check if text fragment is legitimate in admonition context."""
        # Technical references might be acceptable
        if re.search(r'\b(API|SDK|URL|URI|HTTP|HTTPS)\b', text, re.IGNORECASE):
            return True
        
        # Version numbers or identifiers
        if re.search(r'v?\d+\.\d+|[A-Z]{2,}\d+', text):
            return True
        
        # Single technical terms in reference context
        content_type = context.get('content_type', 'general')
        if content_type == 'reference' and len(text.split()) <= 2:
            return True
        
        return False

    def _has_technical_reference_pattern(self, text: str) -> bool:
        """Check if text has patterns suggesting technical reference."""
        patterns = [
            r'\b\w+\(\)',  # Function calls
            r'\b[A-Z_]{3,}',  # Constants
            r'\b\w+\.[a-z]+',  # File extensions or properties
            r'<\w+>',  # XML/HTML tags or placeholders
        ]
        
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        
        return False

    # === CONTEXTUAL MESSAGING AND SUGGESTIONS ===

    def _get_contextual_message(self, violation_type: str, evidence_score: float, 
                               context: Dict[str, Any], **kwargs) -> str:
        """Generate contextual error messages based on violation type and evidence."""
        if violation_type == 'invalid_label':
            kind = kwargs.get('kind', 'UNKNOWN')
            if evidence_score > 0.8:
                return f"Invalid admonition label '[{kind}]' violates IBM Style Guide standards."
            elif evidence_score > 0.6:
                return f"Consider using an approved admonition label instead of '[{kind}]'."
            else:
                return f"The admonition label '[{kind}]' may not be standard."
        
        elif violation_type == 'incomplete_sentence':
            if evidence_score > 0.8:
                return "Admonition content must be a complete sentence for clarity."
            elif evidence_score > 0.6:
                return "Consider expanding this admonition into a complete sentence."
            else:
                return "This admonition content could be more complete."
        
        return "Admonition formatting issue detected."

    def _generate_smart_suggestions(self, violation_type: str, evidence_score: float,
                                  context: Dict[str, Any], **kwargs) -> List[str]:
        """Generate smart suggestions based on violation type and evidence confidence."""
        suggestions = []
        
        if violation_type == 'invalid_label':
            kind = kwargs.get('kind', 'UNKNOWN')
            suggestions.append("Use one of the approved IBM Style Guide labels: NOTE, IMPORTANT, TIP, CAUTION, etc.")
            
            # Suggest closest matches
            approved_labels = {
                'NOTE', 'IMPORTANT', 'RESTRICTION', 'TIP', 'ATTENTION', 
                'CAUTION', 'DANGER', 'REQUIREMENT', 'EXCEPTION', 'FAST PATH', 'REMEMBER'
            }
            
            closest_matches = [label for label in approved_labels 
                             if kind.lower() in label.lower() or label.lower() in kind.lower()]
            if closest_matches:
                suggestions.append(f"Consider using '{closest_matches[0]}' instead of '{kind}'.")
            
            if evidence_score > 0.7:
                suggestions.append("Consistent admonition labels improve document professionalism.")
        
        elif violation_type == 'incomplete_sentence':
            suggestions.append("Ensure the admonition content forms a complete, standalone sentence.")
            suggestions.append("Add a subject and verb to create a complete thought.")
            
            if evidence_score > 0.7:
                suggestions.append("Complete sentences in admonitions improve clarity and comprehension.")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    # === ENHANCED HELPER METHODS FOR 6-STEP EVIDENCE PATTERN ===
    
    def _is_admonition_in_actual_quotes(self, admonition_kind: str, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Surgical check: Is the admonition actually within quotation marks?
        Only returns True for genuine quoted content, not incidental apostrophes.
        """
        if not text:
            return False
        
        # Look for quote pairs that actually enclose the admonition
        import re
        
        # Find all potential quote pairs
        quote_patterns = [
            (r'"([^"]*)"', '"'),  # Double quotes
            (r"'([^']*)'", "'"),  # Single quotes
            (r'`([^`]*)`', '`')   # Backticks
        ]
        
        for pattern, quote_char in quote_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                quoted_content = match.group(1)
                if admonition_kind.lower() in quoted_content.lower():
                    return True
        
        return False
    
    def _is_admonition_in_technical_context(self, admonition_kind: str, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if admonition appears in technical documentation context with approved custom types.
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for technical documentation indicators
        technical_indicators = [
            'api documentation', 'technical specification', 'developer guide',
            'software documentation', 'system documentation', 'installation guide',
            'configuration guide', 'troubleshooting guide', 'reference manual'
        ]
        
        for indicator in technical_indicators:
            if indicator in text_lower:
                # Allow some technical-specific admonitions in strong technical contexts
                if admonition_kind.upper() in ['SECURITY', 'PERFORMANCE', 'COMPATIBILITY', 'DEPRECATED']:
                    return True
        
        # Check content type for technical context
        content_type = context.get('content_type', '') if context else ''
        if content_type == 'technical':
            # Common technical admonitions that might be acceptable
            if admonition_kind.upper() in ['WARNING', 'ERROR', 'INFO', 'DEBUG', 'TRACE']:
                return True
        
        return False
    
    def _is_admonition_in_citation_context(self, admonition_kind: str, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if admonition appears in citation or reference context.
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for citation indicators
        citation_indicators = [
            'according to', 'as stated in', 'reference:', 'cited in',
            'documentation shows', 'manual states', 'guide recommends',
            'specification defines', 'standard requires'
        ]
        
        for indicator in citation_indicators:
            if indicator in text_lower:
                return True
        
        # Check for reference formatting patterns
        if any(pattern in text_lower for pattern in ['see also', 'refer to', 'as described']):
            return True
        
        return False
    
    def _is_sentence_in_actual_quotes(self, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Surgical check: Is the sentence fragment actually within quotation marks?
        Only returns True for genuine quoted content, not incidental apostrophes.
        """
        if not text:
            return False
        
        # Look for quote pairs that actually enclose the sentence
        import re
        
        # Find all potential quote pairs in surrounding context
        quote_patterns = [
            (r'"([^"]*)"', '"'),  # Double quotes
            (r"'([^']*)'", "'"),  # Single quotes
            (r'`([^`]*)`', '`')   # Backticks
        ]
        
        for pattern, quote_char in quote_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                quoted_content = match.group(1)
                # If the text is mostly within quotes, consider it quoted
                if len(quoted_content.strip()) > len(text.strip()) * 0.7:
                    return True
        
        return False
    
    def _is_sentence_in_technical_context(self, text: str, doc: 'Doc', context: Dict[str, Any] = None) -> bool:
        """
        Check if sentence fragment appears in technical reference context.
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for technical reference indicators
        technical_patterns = [
            r'\b(api|sdk|cli|gui|ui|url|uri|http|https)\b',
            r'\b(json|xml|yaml|csv|sql|html|css|js)\b',
            r'\b(get|post|put|delete|patch)\b',  # HTTP methods
            r'\b(200|404|500|401|403)\b',  # HTTP status codes
            r'v?\d+\.\d+(\.\d+)?',  # Version numbers
            r'\b[A-Z_]{3,}\b',  # Constants
            r'\w+\(\)',  # Function calls
            r'<\w+>',  # XML/HTML tags or placeholders
        ]
        
        for pattern in technical_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Check content type for technical context
        content_type = context.get('content_type', '') if context else ''
        if content_type in ['technical', 'api', 'reference']:
            # Very short fragments in technical docs might be acceptable
            if len(text.split()) <= 3:
                return True
        
        return False
    
    def _is_sentence_in_citation_context(self, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if sentence fragment appears in citation or reference context.
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for citation indicators
        citation_indicators = [
            'source:', 'reference:', 'see:', 'note:', 'example:',
            'figure:', 'table:', 'section:', 'chapter:', 'page:'
        ]
        
        for indicator in citation_indicators:
            if indicator in text_lower:
                return True
        
        # Check for reference patterns
        if any(pattern in text_lower for pattern in ['see section', 'refer to', 'as shown']):
            return True
        
        return False
    
    def _get_admonition_label_base_evidence_score(self, admonition_kind: str, approved_labels: set, context: Dict[str, Any] = None) -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Completely unknown labels → 0.7 (very specific)
        - Close matches to approved → 0.5 (moderate specificity)
        - Technical domain variations → 0.4 (needs context analysis)
        """
        if not admonition_kind:
            return 0.0
        
        # Enhanced specificity analysis
        if self._is_exact_admonition_violation(admonition_kind, approved_labels):
            return 0.7  # Very specific, clear violation (reduced from 0.9)
        elif self._is_pattern_admonition_violation(admonition_kind, approved_labels):
            return 0.5  # Pattern-based, moderate specificity
        elif self._is_minor_admonition_issue(admonition_kind, approved_labels):
            return 0.4  # Minor issue, needs context
        else:
            return 0.3  # Possible issue, needs more evidence
    
    def _get_incomplete_sentence_base_evidence_score(self, text: str, doc: 'Doc', context: Dict[str, Any] = None) -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Clear sentence fragments → 0.6 (moderate specificity)
        - Technical terms/identifiers → 0.3 (needs context analysis)
        - Very short phrases → 0.4 (needs more evidence)
        """
        if not text or not doc:
            return 0.0
        
        # Enhanced specificity analysis
        if self._is_exact_sentence_violation(text, doc):
            return 0.6  # Moderate specificity - sentence structure issues
        elif self._is_pattern_sentence_violation(text, doc):
            return 0.4  # Pattern-based, needs context
        elif self._is_minor_sentence_issue(text, doc):
            return 0.3  # Minor issue, needs context
        else:
            return 0.2  # Possible issue, needs more evidence
    
    def _is_exact_admonition_violation(self, admonition_kind: str, approved_labels: set) -> bool:
        """
        Check if admonition represents an exact label violation.
        """
        # Completely unknown labels that are not close to any approved label
        kind_lower = admonition_kind.lower()
        
        # Check if it's completely different from all approved labels
        for approved in approved_labels:
            approved_lower = approved.lower()
            # If there's any similarity, it's not an exact violation
            if (kind_lower in approved_lower or approved_lower in kind_lower or
                abs(len(kind_lower) - len(approved_lower)) <= 2):
                return False
        
        return True
    
    def _is_pattern_admonition_violation(self, admonition_kind: str, approved_labels: set) -> bool:
        """
        Check if admonition shows a pattern of label violation.
        """
        kind_lower = admonition_kind.lower()
        
        # Check for close matches that might be variations
        for approved in approved_labels:
            approved_lower = approved.lower()
            if kind_lower in approved_lower or approved_lower in kind_lower:
                return True
        
        return False
    
    def _is_minor_admonition_issue(self, admonition_kind: str, approved_labels: set) -> bool:
        """
        Check if admonition has minor label issues.
        """
        # Very similar length or structure to approved labels
        kind_len = len(admonition_kind)
        
        for approved in approved_labels:
            if abs(kind_len - len(approved)) <= 2:
                return True
        
        return False
    
    def _is_exact_sentence_violation(self, text: str, doc: 'Doc') -> bool:
        """
        Check if text represents an exact sentence structure violation.
        """
        # Clear indicators of incomplete sentences
        text_lower = text.lower().strip()
        
        # Very short fragments without proper structure
        if len(text.split()) <= 2 and not text_lower.endswith('.'):
            return True
        
        # Missing essential sentence components
        if not self._is_complete_sentence(doc):
            # But has some sentence-like structure
            if len(text.split()) >= 4:
                return True
        
        return False
    
    def _is_pattern_sentence_violation(self, text: str, doc: 'Doc') -> bool:
        """
        Check if text shows a pattern of sentence structure violation.
        """
        # Moderate length but incomplete structure
        word_count = len(text.split())
        
        if 3 <= word_count <= 6:
            if not self._is_complete_sentence(doc):
                return True
        
        return False
    
    def _is_minor_sentence_issue(self, text: str, doc: 'Doc') -> bool:
        """
        Check if text has minor sentence structure issues.
        """
        # Longer text that might be acceptable fragments
        if len(text.split()) >= 7:
            if not self._is_complete_sentence(doc):
                return True
        
        return False
    
    def _apply_feedback_clues_admonitions(self, evidence_score: float, admonition_kind: str, context: Dict[str, Any] = None) -> float:
        """
        Apply clues learned from user feedback patterns specific to admonition labels.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_admonitions()
        
        kind_lower = admonition_kind.lower()
        
        # Consistently Accepted Admonition Labels
        if kind_lower in feedback_patterns.get('accepted_admonition_labels', set()):
            evidence_score -= 0.5  # Users consistently accept this label
        
        # Consistently Rejected Suggestions
        if kind_lower in feedback_patterns.get('rejected_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: Admonition label acceptance rates
        label_acceptance = feedback_patterns.get('admonition_label_acceptance', {})
        acceptance_rate = label_acceptance.get(kind_lower, 0.5)
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # High acceptance, likely valid in some contexts
        elif acceptance_rate < 0.2:
            evidence_score += 0.2  # Low acceptance, strong violation
        
        # Pattern: Admonition labels in different content types
        content_type = context.get('content_type', 'general') if context else 'general'
        content_patterns = feedback_patterns.get(f'{content_type}_admonition_acceptance', {})
        
        acceptance_rate = content_patterns.get(kind_lower, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Accepted in this content type
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Consistently flagged in this content type
        
        # Pattern: Context-specific acceptance
        block_type = context.get('block_type', 'paragraph') if context else 'paragraph'
        context_patterns = feedback_patterns.get(f'{block_type}_admonition_patterns', {})
        
        if kind_lower in context_patterns.get('accepted', set()):
            evidence_score -= 0.2
        elif kind_lower in context_patterns.get('flagged', set()):
            evidence_score += 0.2
        
        # Pattern: Frequency-based adjustment for admonition labels
        term_frequency = feedback_patterns.get('admonition_label_frequencies', {}).get(kind_lower, 0)
        if term_frequency > 10:  # Commonly seen label
            acceptance_rate = feedback_patterns.get('admonition_label_acceptance', {}).get(kind_lower, 0.5)
            if acceptance_rate > 0.7:
                evidence_score -= 0.3  # Frequently accepted
            elif acceptance_rate < 0.3:
                evidence_score += 0.2  # Frequently rejected
        
        return evidence_score
    
    def _apply_feedback_clues_sentences(self, evidence_score: float, text: str, context: Dict[str, Any] = None) -> float:
        """
        Apply clues learned from user feedback patterns specific to sentence structure.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_sentences()
        
        text_lower = text.lower().strip()
        
        # Consistently Accepted Sentence Fragments
        if text_lower in feedback_patterns.get('accepted_sentence_fragments', set()):
            evidence_score -= 0.5  # Users consistently accept this fragment
        
        # Consistently Rejected Suggestions
        if text_lower in feedback_patterns.get('rejected_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: Fragment type acceptance rates
        fragment_patterns = feedback_patterns.get('fragment_type_acceptance', {})
        
        # Classify fragment type
        fragment_type = self._classify_fragment_type(text)
        acceptance_rate = fragment_patterns.get(fragment_type, 0.5)
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # High acceptance for this fragment type
        elif acceptance_rate < 0.2:
            evidence_score += 0.2  # Low acceptance, strong violation
        
        # Pattern: Sentence fragments in different content types
        content_type = context.get('content_type', 'general') if context else 'general'
        content_patterns = feedback_patterns.get(f'{content_type}_fragment_acceptance', {})
        
        acceptance_rate = content_patterns.get(fragment_type, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Accepted in this content type
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Consistently flagged in this content type
        
        # Pattern: Length-based acceptance
        word_count = len(text.split())
        length_patterns = feedback_patterns.get('fragment_length_acceptance', {})
        
        if word_count <= 3:
            acceptance_rate = length_patterns.get('short', 0.6)
        elif word_count <= 6:
            acceptance_rate = length_patterns.get('medium', 0.4)
        else:
            acceptance_rate = length_patterns.get('long', 0.2)
        
        if acceptance_rate > 0.7:
            evidence_score -= 0.2
        elif acceptance_rate < 0.3:
            evidence_score += 0.1
        
        return evidence_score
    
    def _classify_fragment_type(self, text: str) -> str:
        """
        Classify the type of sentence fragment for feedback analysis.
        """
        text_lower = text.lower()
        
        # Technical reference patterns
        if self._has_technical_reference_pattern(text):
            return 'technical_reference'
        
        # Version or identifier patterns
        if re.search(r'v?\d+\.\d+|[A-Z]{2,}\d+', text):
            return 'version_identifier'
        
        # Short command or function
        if re.search(r'\w+\(\)|[A-Z_]{3,}', text):
            return 'command_function'
        
        # Single word or very short
        if len(text.split()) <= 2:
            return 'single_term'
        
        # Medium length phrase
        if len(text.split()) <= 5:
            return 'short_phrase'
        
        # Longer incomplete sentence
        return 'incomplete_sentence'
    
    def _get_cached_feedback_patterns_admonitions(self) -> Dict[str, Any]:
        """
        Load feedback patterns from cache or feedback analysis for admonition labels.
        """
        # This would load from feedback analysis system
        # For now, return basic patterns with some realistic examples
        return {
            'accepted_admonition_labels': {'info', 'warning', 'error', 'success'},  # Common in technical docs
            'rejected_suggestions': set(),  # Labels users don't want flagged
            'admonition_label_acceptance': {
                'info': 0.7,          # Often acceptable in technical contexts
                'warning': 0.8,       # Very acceptable
                'error': 0.8,         # Very acceptable
                'success': 0.7,       # Often acceptable
                'debug': 0.6,         # Moderately acceptable in technical contexts
                'trace': 0.5,         # Sometimes acceptable
                'alert': 0.4,         # Less preferred
                'notice': 0.6,        # Moderately acceptable
                'hint': 0.5,          # Sometimes acceptable
                'example': 0.4,       # Less preferred as admonition
                'deprecated': 0.9     # Very acceptable in technical contexts
            },
            'technical_admonition_acceptance': {
                'info': 0.9,          # Very acceptable in technical writing
                'warning': 0.9,       # Very acceptable in technical writing
                'error': 0.9,         # Very acceptable in technical writing
                'debug': 0.8,         # Acceptable in technical writing
                'trace': 0.7,         # Acceptable in technical writing
                'deprecated': 0.95,   # Very acceptable in technical writing
                'security': 0.8,      # Acceptable in technical writing
                'performance': 0.8,   # Acceptable in technical writing
                'compatibility': 0.8  # Acceptable in technical writing
            },
            'business_admonition_acceptance': {
                'info': 0.6,          # Moderately acceptable in business writing
                'warning': 0.7,       # Acceptable in business writing
                'success': 0.8,       # Very acceptable in business writing
                'alert': 0.5,         # Sometimes acceptable in business writing
                'notice': 0.7,        # Acceptable in business writing
                'hint': 0.6           # Moderately acceptable in business writing
            },
            'documentation_admonition_acceptance': {
                'info': 0.8,          # Very acceptable in documentation
                'warning': 0.9,       # Very acceptable in documentation
                'example': 0.6,       # Moderately acceptable in documentation
                'hint': 0.7,          # Acceptable in documentation
                'notice': 0.8         # Very acceptable in documentation
            },
            'admonition_label_frequencies': {
                'info': 200,          # Very common label
                'warning': 180,       # Very common label
                'note': 250,          # Most common approved label
                'tip': 150,           # Common approved label
                'caution': 120,       # Common approved label
                'important': 140,     # Common approved label
                'error': 100,         # Common in technical contexts
                'success': 80,        # Common in business contexts
                'debug': 60,          # Less common, technical contexts
                'deprecated': 40      # Less common, technical contexts
            },
            'admonition_admonition_patterns': {
                'accepted': {'info', 'warning', 'success'},
                'flagged': {'alert', 'notice', 'example'}
            },
            'note_admonition_patterns': {
                'accepted': {'info', 'hint', 'notice'},  # More acceptable in note contexts
                'flagged': {'error', 'debug'}
            },
            'callout_admonition_patterns': {
                'accepted': {'info', 'warning', 'tip', 'hint'},  # More acceptable in callouts
                'flagged': {'error', 'debug', 'trace'}
            }
        }
    
    def _get_cached_feedback_patterns_sentences(self) -> Dict[str, Any]:
        """
        Load feedback patterns from cache or feedback analysis for sentence structure.
        """
        # This would load from feedback analysis system
        # For now, return basic patterns with some realistic examples
        return {
            'accepted_sentence_fragments': {
                'api endpoint', 'http status code', 'json response', 'xml format',
                'database connection', 'user interface', 'command line', 'configuration file'
            },
            'rejected_suggestions': set(),  # Fragments users don't want flagged
            'fragment_type_acceptance': {
                'technical_reference': 0.9,    # Very acceptable
                'version_identifier': 0.95,    # Very acceptable
                'command_function': 0.9,       # Very acceptable
                'single_term': 0.7,            # Often acceptable
                'short_phrase': 0.5,           # Sometimes acceptable
                'incomplete_sentence': 0.2     # Usually should be flagged
            },
            'technical_fragment_acceptance': {
                'technical_reference': 0.95,   # Very acceptable in technical writing
                'version_identifier': 0.98,    # Very acceptable in technical writing
                'command_function': 0.95,      # Very acceptable in technical writing
                'single_term': 0.8,            # Often acceptable in technical writing
                'short_phrase': 0.7,           # Often acceptable in technical writing
                'incomplete_sentence': 0.3     # Sometimes acceptable in technical writing
            },
            'business_fragment_acceptance': {
                'technical_reference': 0.6,    # Sometimes acceptable in business writing
                'version_identifier': 0.7,     # Often acceptable in business writing
                'command_function': 0.5,       # Sometimes acceptable in business writing
                'single_term': 0.5,            # Sometimes acceptable in business writing
                'short_phrase': 0.3,           # Less acceptable in business writing
                'incomplete_sentence': 0.1     # Usually should be flagged in business writing
            },
            'reference_fragment_acceptance': {
                'technical_reference': 0.98,   # Very acceptable in reference writing
                'version_identifier': 0.98,    # Very acceptable in reference writing
                'command_function': 0.95,      # Very acceptable in reference writing
                'single_term': 0.9,            # Very acceptable in reference writing
                'short_phrase': 0.8,           # Very acceptable in reference writing
                'incomplete_sentence': 0.5     # Sometimes acceptable in reference writing
            },
            'fragment_length_acceptance': {
                'short': 0.8,                  # 1-3 words often acceptable
                'medium': 0.5,                 # 4-6 words sometimes acceptable
                'long': 0.2                    # 7+ words usually should be complete
            }
        }
