"""
Lists Rule (Enhanced with Evidence-Based Analysis)
Based on IBM Style Guide topic: "Lists"
Enhanced to follow evidence-based rule development methodology for zero false positives.
"""
from typing import List, Dict, Any, Optional
from .base_structure_rule import BaseStructureRule
import re

try:
    from spacy.tokens import Doc, Token
except ImportError:
    Doc = None
    Token = None

class ListsRule(BaseStructureRule):
    """
    Checks for style issues in lists using evidence-based analysis with surgical precision.
    Implements rule-specific evidence calculation for optimal false positive reduction.
    
    Violations detected:
    - Lack of parallel structure across list items
    - Inconsistent grammatical patterns
    """
    
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'lists'

    def _get_grammatical_form(self, doc: Doc) -> str:
        """
        Analyzes a SpaCy doc object and determines its grammatical form using morphological analysis.
        """
        if not doc or len(doc) == 0:
            return "EMPTY"

        # Enhanced linguistic anchors for different grammatical forms
        first_token = doc[0]
        
        # Imperative verbs (base form)
        if first_token.pos_ == 'VERB' and first_token.tag_ == 'VB':
            return "Imperative Phrase"
        
        # Gerund phrases
        if first_token.pos_ == 'VERB' and first_token.tag_ == 'VBG':
            return "Gerund Phrase"
        
        # Complete sentences (have subject and predicate)
        has_subject = any(token.dep_ in ('nsubj', 'nsubjpass') for token in doc)
        has_verb = any(token.pos_ == 'VERB' for token in doc)
        if has_subject and has_verb:
            return "Complete Sentence"
        
        # Noun phrases
        if first_token.pos_ in ['NOUN', 'PROPN']:
            return "Noun Phrase"
        
        # Adjective phrases
        if first_token.pos_ == 'ADJ':
            return "Adjective Phrase"
        
        # Prepositional phrases
        if first_token.pos_ == 'ADP':
            return "Prepositional Phrase"
        
        # Default to fragment
        return "Fragment"

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes lists for style violations using evidence-based scoring.
        Each potential violation gets nuanced evidence assessment for precision.
        """
        errors = []
        if not nlp or len(sentences) < 2:
            return []

        # Skip if explicitly excluded
        if context and context.get('exclude_list_rules'):
            return []

        # === EVIDENCE-BASED ANALYSIS: Parallel Structure ===
        parallel_issues = self._detect_parallel_structure_violations(sentences, nlp)
        if parallel_issues:
            evidence_score = self._calculate_parallel_structure_evidence(
                sentences, parallel_issues, nlp, text, context
            )
            
            if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                # Use the first non-parallel item for error reporting
                first_violation = parallel_issues[0]
                
                errors.append(self._create_error(
                    sentence=first_violation['text'],
                    sentence_index=first_violation['index'],
                    message=self._get_contextual_message('parallel_structure', evidence_score, context, parallel_issues=parallel_issues),
                    suggestions=self._generate_smart_suggestions('parallel_structure', evidence_score, context, parallel_issues=parallel_issues),
                    severity='medium',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=(0, len(first_violation['text'])),
                    flagged_text=first_violation['text']
                ))
        
        return errors

    # === EVIDENCE CALCULATION METHODS ===

    def _calculate_parallel_structure_evidence(self, sentences: List[str], parallel_issues: List[Dict[str, Any]], 
                                              nlp, text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for potential parallel structure violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            sentences: All list items
            parallel_issues: Detected parallelism violations
            nlp: SpaCy language model
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === ZERO FALSE POSITIVE GUARDS ===
        # CRITICAL: Apply rule-specific guards FIRST to eliminate common exceptions
        
        # Kill evidence immediately for contexts where this specific rule should never apply
        if not context:
            return 0.0  # No context available
        
        # Don't flag lists in quoted examples
        if self._is_list_in_actual_quotes(sentences, text, context):
            return 0.0  # Quoted examples are not list structure errors
        
        # Don't flag lists in technical documentation contexts with approved patterns
        if self._is_list_in_technical_context(sentences, text, context):
            return 0.0  # Technical docs may use different conventions
        
        # Don't flag lists in citation or reference context
        if self._is_list_in_citation_context(sentences, text, context):
            return 0.0  # Academic papers, documentation references, etc.
        
        # Apply inherited zero false positive guards
        for sentence in sentences:
            violation = {'sentence': sentence, 'text': sentence}
            if self._apply_zero_false_positive_guards_structure(violation, context):
                return 0.0
        
        # Special guard: Technical lists often have mixed structures legitimately
        if self._is_technical_mixed_list(sentences, context):
            return 0.0
        
        # Special guard: Very short lists (2 items) are more flexible
        if len(sentences) <= 2:
            return 0.0
        
        # Special guard: Lists with intentional variation (e.g., Q&A format)
        if self._has_intentional_structure_variation(sentences, nlp, context):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_parallel_structure_base_evidence_score(sentences, parallel_issues, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this list
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        # Check consistency of the predominant pattern
        all_forms = []
        for sentence in sentences:
            doc = nlp(sentence)
            if doc:
                all_forms.append(self._get_grammatical_form(doc))
        
        if all_forms:
            # Find most common form
            form_counts = {}
            for form in all_forms:
                form_counts[form] = form_counts.get(form, 0) + 1
            
            most_common_form = max(form_counts, key=form_counts.get)
            most_common_count = form_counts[most_common_form]
            
            # If most items follow one pattern, violations are more significant
            pattern_dominance = most_common_count / len(all_forms)
            if pattern_dominance >= 0.7:  # 70% or more follow one pattern
                evidence_score += 0.2
        
        # Check grammatical complexity - simple structures need more consistency
        simple_forms = ['Noun Phrase', 'Adjective Phrase', 'Fragment']
        if most_common_form in simple_forms:
            evidence_score += 0.1  # Simple lists should be very consistent
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._adjust_evidence_for_structure_context(evidence_score, context)
        
        # List depth adjustments
        list_depth = context.get('list_depth', 1) if context else 1
        if list_depth > 1:
            evidence_score -= 0.1  # Nested lists might be more flexible
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        # Content type adjustments
        content_type = context.get('content_type', 'general') if context else 'general'
        
        if content_type == 'procedural':
            evidence_score += 0.2  # Procedural lists need strong consistency
        elif content_type == 'technical':
            evidence_score -= 0.1  # Technical lists might legitimately vary
        elif content_type == 'marketing':
            evidence_score += 0.1  # Marketing lists should be polished
        
        # Audience adjustments
        audience = context.get('audience', 'general') if context else 'general'
        if audience in ['beginner', 'general']:
            evidence_score += 0.1  # General audiences benefit from consistency
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_parallel_structure(evidence_score, sentences, parallel_issues, context)
        
        # Parallel structure-specific final adjustments (moderate to avoid evidence inflation)
        evidence_score += 0.05  # Parallel structure is important for readability but context-dependent
        
        return max(0.0, min(1.0, evidence_score))

    # === HELPER METHODS FOR VIOLATION DETECTION ===

    def _detect_parallel_structure_violations(self, sentences: List[str], nlp) -> List[Dict[str, Any]]:
        """Detect parallel structure violations across list items."""
        if len(sentences) < 2:
            return []
        
        # Analyze grammatical form of each item
        forms_and_sentences = []
        for i, sentence in enumerate(sentences):
            doc = nlp(sentence.strip())
            if doc:
                form = self._get_grammatical_form(doc)
                forms_and_sentences.append({
                    'index': i,
                    'text': sentence,
                    'form': form,
                    'doc': doc
                })
        
        if len(forms_and_sentences) < 2:
            return []
        
        # Find the predominant pattern (most common form)
        form_counts = {}
        for item in forms_and_sentences:
            form = item['form']
            form_counts[form] = form_counts.get(form, 0) + 1
        
        # Determine expected pattern (most common)
        expected_form = max(form_counts, key=form_counts.get)
        expected_count = form_counts[expected_form]
        
        # Only flag violations if there's a clear predominant pattern
        if expected_count < len(forms_and_sentences) * 0.5:  # Less than 50% follow the same pattern
            return []  # No clear pattern, so no violations
        
        # Find violations (items that don't match the predominant pattern)
        violations = []
        for item in forms_and_sentences:
            if item['form'] != expected_form:
                violations.append({
                    'index': item['index'],
                    'text': item['text'],
                    'actual_form': item['form'],
                    'expected_form': expected_form
                })
        
        return violations

    def _is_technical_mixed_list(self, sentences: List[str], context: Dict[str, Any]) -> bool:
        """Check if this is a technical list that legitimately has mixed structures."""
        if not context:
            return False
        
        content_type = context.get('content_type', 'general')
        if content_type not in ['technical', 'api', 'reference', 'code']:
            return False
        
        # Check for technical indicators that suggest legitimate mixed structure
        technical_patterns = [
            r'\b\w+\(\)',  # Functions with parentheses
            r'\b[A-Z_]{2,}',  # Constants or environment variables
            r'\b\w+\.\w+',  # Object.property patterns
            r'<\w+>',  # XML/HTML tags or placeholders
            r'--\w+',  # Command line flags
            r'/\w+/',  # Paths or regex patterns
        ]
        
        technical_count = 0
        for sentence in sentences:
            for pattern in technical_patterns:
                if re.search(pattern, sentence):
                    technical_count += 1
                    break
        
        # If most items have technical patterns, mixed structure might be legitimate
        return technical_count >= len(sentences) * 0.6

    def _has_intentional_structure_variation(self, sentences: List[str], nlp, context: Dict[str, Any]) -> bool:
        """Check if structure variation is intentional (e.g., Q&A, definition lists)."""
        if len(sentences) < 2:
            return False
        
        # Check for Q&A patterns
        question_count = sum(1 for s in sentences if s.strip().endswith('?'))
        if question_count >= len(sentences) * 0.3:  # 30% or more are questions
            return True
        
        # Check for definition list patterns (term: definition)
        colon_count = sum(1 for s in sentences if ':' in s and s.index(':') < len(s) * 0.5)
        if colon_count >= len(sentences) * 0.5:  # 50% or more have early colons
            return True
        
        # Check for alternating pattern (e.g., genuine problem/solution pairs)
        if len(sentences) >= 4:
            # Only consider alternating patterns if they have semantic meaning indicators
            semantic_indicators = [
                ('problem', 'solution'), ('question', 'answer'), ('issue', 'resolution'),
                ('challenge', 'approach'), ('symptom', 'treatment')
            ]
            
            # Check if content suggests intentional alternating structure
            text_lower = ' '.join(sentences).lower()
            has_semantic_alternation = any(
                ind1 in text_lower and ind2 in text_lower 
                for ind1, ind2 in semantic_indicators
            )
            
            if has_semantic_alternation:
                # Analyze first few items for alternating patterns
                forms = []
                for sentence in sentences[:4]:
                    doc = nlp(sentence.strip())
                    if doc:
                        forms.append(self._get_grammatical_form(doc))
                
                # Check if forms alternate in a pattern with semantic justification
                if len(forms) >= 4 and forms[0] == forms[2] and forms[1] == forms[3] and forms[0] != forms[1]:
                    return True
        
        return False

    # === CONTEXTUAL MESSAGING AND SUGGESTIONS ===

    def _get_contextual_message(self, violation_type: str, evidence_score: float, 
                               context: Dict[str, Any], **kwargs) -> str:
        """Generate contextual error messages based on violation type and evidence."""
        if violation_type == 'parallel_structure':
            parallel_issues = kwargs.get('parallel_issues', [])
            
            if evidence_score > 0.8:
                return "List items must use parallel grammatical structure for clarity and consistency."
            elif evidence_score > 0.6:
                return "Consider revising list items to follow a consistent grammatical pattern."
            else:
                return "List items could benefit from more consistent grammatical structure."
        
        return "List formatting issue detected."

    def _generate_smart_suggestions(self, violation_type: str, evidence_score: float,
                                  context: Dict[str, Any], **kwargs) -> List[str]:
        """Generate smart suggestions based on violation type and evidence confidence."""
        suggestions = []
        
        if violation_type == 'parallel_structure':
            parallel_issues = kwargs.get('parallel_issues', [])
            
            if parallel_issues:
                expected_form = parallel_issues[0].get('expected_form', 'consistent structure')
                
                if expected_form == 'Imperative Phrase':
                    suggestions.append("Start each list item with an action verb (e.g., 'Configure', 'Install', 'Run').")
                elif expected_form == 'Noun Phrase':
                    suggestions.append("Use noun phrases for all list items (e.g., 'Database configuration', 'User settings').")
                elif expected_form == 'Complete Sentence':
                    suggestions.append("Write each list item as a complete sentence with subject and verb.")
                elif expected_form == 'Gerund Phrase':
                    suggestions.append("Start each list item with an -ing verb form (e.g., 'Configuring', 'Installing').")
                else:
                    suggestions.append(f"Rewrite all list items to follow the '{expected_form}' pattern.")
                
                # Count of violations for context
                violation_count = len(parallel_issues)
                if violation_count == 1:
                    suggestions.append("Revise the inconsistent item to match the pattern of other list items.")
                else:
                    suggestions.append(f"Revise {violation_count} items to match the predominant pattern.")
                
                if evidence_score > 0.7:
                    suggestions.append("Parallel structure improves readability and comprehension for all audiences.")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    # === ENHANCED HELPER METHODS FOR 6-STEP EVIDENCE PATTERN ===
    
    def _is_list_in_actual_quotes(self, sentences: List[str], text: str, context: Dict[str, Any] = None) -> bool:
        """
        Surgical check: Is the list actually within quotation marks?
        Only returns True for genuine quoted content, not incidental apostrophes.
        """
        if not text or not sentences:
            return False
        
        # Look for quote pairs that actually enclose the list
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
                # If any list item is mostly within quotes, consider it quoted
                for sentence in sentences:
                    if sentence.strip() and sentence.strip() in quoted_content:
                        return True
        
        return False
    
    def _is_list_in_technical_context(self, sentences: List[str], text: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if list appears in technical documentation context with approved patterns.
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
                # Allow some technical-specific list patterns in strong technical contexts
                if self._is_technical_list_pattern(sentences):
                    return True
        
        # Check content type for technical context
        content_type = context.get('content_type', '') if context else ''
        if content_type == 'technical':
            # Common technical list patterns that might be acceptable
            if self._is_technical_list_pattern(sentences):
                return True
        
        return False
    
    def _is_list_in_citation_context(self, sentences: List[str], text: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if list appears in citation or reference context.
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
    
    def _is_technical_list_pattern(self, sentences: List[str]) -> bool:
        """
        Check if list follows a technical pattern that might be acceptable.
        """
        if not sentences:
            return False
        
        # Technical list patterns that might be acceptable without strict parallelism
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
        
        import re
        technical_count = 0
        for sentence in sentences:
            for pattern in technical_patterns:
                if re.search(pattern, sentence.lower()):
                    technical_count += 1
                    break
        
        # If most items have technical patterns, mixed structure might be acceptable
        return technical_count >= len(sentences) * 0.6
    
    def _get_parallel_structure_base_evidence_score(self, sentences: List[str], parallel_issues: List[Dict[str, Any]], context: Dict[str, Any] = None) -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Clear parallel violations with strong pattern → 0.8 (very specific)
        - Mixed structure violations → 0.6 (moderate specificity)
        - Minor structure inconsistencies → 0.4 (needs context analysis)
        """
        if not parallel_issues or len(sentences) < 3:
            return 0.0
        
        # Enhanced specificity analysis
        if self._is_exact_parallel_violation(sentences, parallel_issues):
            return 0.8  # Very specific, clear violation
        elif self._is_pattern_parallel_violation(sentences, parallel_issues):
            return 0.6  # Pattern-based, moderate specificity
        elif self._is_minor_parallel_issue(sentences, parallel_issues):
            return 0.4  # Minor issue, needs context
        else:
            return 0.3  # Possible issue, needs more evidence
    
    def _is_exact_parallel_violation(self, sentences: List[str], parallel_issues: List[Dict[str, Any]]) -> bool:
        """
        Check if list represents an exact parallel structure violation.
        """
        if not parallel_issues:
            return False
        
        # High violation ratio indicates clear parallel structure problem
        violation_ratio = len(parallel_issues) / len(sentences)
        if violation_ratio > 0.5:  # More than half the items violate pattern
            return True
        
        # Strong pattern dominance with clear violations
        if len(sentences) >= 4 and violation_ratio >= 0.3:
            return True
        
        return False
    
    def _is_pattern_parallel_violation(self, sentences: List[str], parallel_issues: List[Dict[str, Any]]) -> bool:
        """
        Check if list shows a pattern of parallel structure violation.
        """
        if not parallel_issues:
            return False
        
        # Moderate violation ratio with clear expected pattern
        violation_ratio = len(parallel_issues) / len(sentences)
        if 0.2 <= violation_ratio <= 0.5:
            return True
        
        # Few violations but very clear expected pattern
        if len(parallel_issues) <= 2 and len(sentences) >= 5:
            return True
        
        return False
    
    def _is_minor_parallel_issue(self, sentences: List[str], parallel_issues: List[Dict[str, Any]]) -> bool:
        """
        Check if list has minor parallel structure issues.
        """
        if not parallel_issues:
            return False
        
        # Small number of violations in longer lists
        violation_ratio = len(parallel_issues) / len(sentences)
        if violation_ratio < 0.2 and len(sentences) >= 5:
            return True
        
        # Single violation in medium lists
        if len(parallel_issues) == 1 and 3 <= len(sentences) <= 6:
            return True
        
        return False
    
    def _apply_feedback_clues_parallel_structure(self, evidence_score: float, sentences: List[str], parallel_issues: List[Dict[str, Any]], context: Dict[str, Any] = None) -> float:
        """
        Apply clues learned from user feedback patterns specific to list parallel structure.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_lists()
        
        # Classify list type
        list_type = self._classify_list_type(sentences, context)
        
        # Consistently Accepted List Patterns
        list_signature = self._get_list_signature(sentences, parallel_issues)
        if list_signature in feedback_patterns.get('accepted_list_patterns', set()):
            evidence_score -= 0.5  # Users consistently accept this list structure
        
        # Consistently Rejected Suggestions
        if list_signature in feedback_patterns.get('rejected_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: List type-specific acceptance rates
        list_patterns = feedback_patterns.get('list_structure_acceptance', {})
        acceptance_rate = list_patterns.get(list_type, 0.5)
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # High acceptance for this list type
        elif acceptance_rate < 0.2:
            evidence_score += 0.2  # Low acceptance, strong violation
        
        # Pattern: Context-specific list acceptance
        content_type = context.get('content_type', 'general') if context else 'general'
        content_patterns = feedback_patterns.get(f'{content_type}_list_acceptance', {})
        
        acceptance_rate = content_patterns.get(list_type, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Accepted in this content type
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Consistently flagged in this content type
        
        # Pattern: List length-based acceptance
        list_length = len(sentences)
        length_patterns = feedback_patterns.get('list_length_acceptance', {})
        
        if list_length <= 3:
            acceptance_rate = length_patterns.get('short', 0.7)  # Short lists more flexible
        elif list_length <= 7:
            acceptance_rate = length_patterns.get('medium', 0.4)
        else:
            acceptance_rate = length_patterns.get('long', 0.2)  # Long lists need consistency
        
        if acceptance_rate > 0.7:
            evidence_score -= 0.2
        elif acceptance_rate < 0.3:
            evidence_score += 0.1
        
        # Pattern: Violation ratio-based adjustment
        violation_ratio = len(parallel_issues) / len(sentences) if parallel_issues else 0
        ratio_patterns = feedback_patterns.get('violation_ratio_acceptance', {})
        
        if violation_ratio <= 0.2:
            acceptance_rate = ratio_patterns.get('low', 0.8)  # Few violations often acceptable
        elif violation_ratio <= 0.5:
            acceptance_rate = ratio_patterns.get('medium', 0.4)
        else:
            acceptance_rate = ratio_patterns.get('high', 0.1)  # Many violations clearly problematic
        
        if acceptance_rate > 0.7:
            evidence_score -= 0.3
        elif acceptance_rate < 0.3:
            evidence_score += 0.2
        
        return evidence_score
    
    def _classify_list_type(self, sentences: List[str], context: Dict[str, Any] = None) -> str:
        """
        Classify the type of list for feedback analysis.
        """
        if not sentences:
            return 'empty'
        
        # Analyze predominant grammatical form
        forms = []
        for sentence in sentences[:3]:  # Sample first few items
            if hasattr(self, '_nlp') and self._nlp:
                doc = self._nlp(sentence)
                if doc:
                    forms.append(self._get_grammatical_form(doc))
        
        if not forms:
            return 'unknown'
        
        # Get most common form
        form_counts = {}
        for form in forms:
            form_counts[form] = form_counts.get(form, 0) + 1
        
        most_common_form = max(form_counts, key=form_counts.get)
        
        # Map to feedback categories
        if most_common_form == 'Imperative Phrase':
            return 'procedural'
        elif most_common_form == 'Noun Phrase':
            return 'descriptive'
        elif most_common_form == 'Complete Sentence':
            return 'explanatory'
        elif most_common_form == 'Gerund Phrase':
            return 'action_oriented'
        elif most_common_form in ['Adjective Phrase', 'Fragment']:
            return 'simple'
        else:
            return 'mixed'
    
    def _get_list_signature(self, sentences: List[str], parallel_issues: List[Dict[str, Any]]) -> str:
        """
        Generate a signature for the list structure for feedback analysis.
        """
        if not sentences:
            return 'empty'
        
        # Create a signature based on structure
        length = len(sentences)
        violation_count = len(parallel_issues) if parallel_issues else 0
        violation_ratio = violation_count / length if length > 0 else 0
        
        # Classify signature
        if violation_ratio == 0:
            return f'parallel_{length}_items'
        elif violation_ratio <= 0.2:
            return f'mostly_parallel_{length}_items'
        elif violation_ratio <= 0.5:
            return f'mixed_structure_{length}_items'
        else:
            return f'inconsistent_{length}_items'
    
    def _get_cached_feedback_patterns_lists(self) -> Dict[str, Any]:
        """
        Load feedback patterns from cache or feedback analysis for list structures.
        """
        # This would load from feedback analysis system
        # For now, return basic patterns with some realistic examples
        return {
            'accepted_list_patterns': {
                'parallel_3_items', 'parallel_4_items', 'parallel_5_items',
                'mostly_parallel_4_items', 'mostly_parallel_5_items'
            },
            'rejected_suggestions': set(),  # List patterns users don't want flagged
            'list_structure_acceptance': {
                'procedural': 0.2,          # Procedural lists need strict parallelism
                'descriptive': 0.4,         # Descriptive lists moderately need parallelism
                'explanatory': 0.6,         # Explanatory lists sometimes need parallelism
                'action_oriented': 0.3,     # Action lists need good parallelism
                'simple': 0.5,              # Simple lists moderately need parallelism
                'mixed': 0.8                # Mixed lists often acceptable as-is
            },
            'procedural_list_acceptance': {
                'procedural': 0.1,          # Very important in procedural content
                'descriptive': 0.3,         # Important in procedural content
                'explanatory': 0.4,         # Somewhat important in procedural content
                'action_oriented': 0.2,     # Very important in procedural content
                'simple': 0.4,              # Somewhat important in procedural content
                'mixed': 0.7                # Sometimes acceptable in procedural content
            },
            'technical_list_acceptance': {
                'procedural': 0.4,          # Sometimes acceptable in technical docs
                'descriptive': 0.6,         # Often acceptable in technical docs
                'explanatory': 0.7,         # Often acceptable in technical docs
                'action_oriented': 0.5,     # Sometimes acceptable in technical docs
                'simple': 0.7,              # Often acceptable in technical docs
                'mixed': 0.9                # Very acceptable in technical docs
            },
            'marketing_list_acceptance': {
                'procedural': 0.2,          # Important in marketing content
                'descriptive': 0.3,         # Important in marketing content
                'explanatory': 0.4,         # Somewhat important in marketing content
                'action_oriented': 0.2,     # Important in marketing content
                'simple': 0.3,              # Important in marketing content
                'mixed': 0.6                # Sometimes acceptable in marketing content
            },
            'reference_list_acceptance': {
                'procedural': 0.3,          # Somewhat important in reference docs
                'descriptive': 0.5,         # Moderately important in reference docs
                'explanatory': 0.6,         # Often acceptable in reference docs
                'action_oriented': 0.4,     # Somewhat important in reference docs
                'simple': 0.6,              # Often acceptable in reference docs
                'mixed': 0.8                # Very acceptable in reference docs
            },
            'list_length_acceptance': {
                'short': 0.7,               # 3 items or fewer, more flexible
                'medium': 0.4,              # 4-7 items, moderate requirements
                'long': 0.2                 # 8+ items, strict requirements
            },
            'violation_ratio_acceptance': {
                'low': 0.8,                 # ≤20% violations often acceptable
                'medium': 0.4,              # 21-50% violations moderately acceptable
                'high': 0.1                 # >50% violations rarely acceptable
            }
        }
