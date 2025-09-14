"""
Conjunctions Rule - Evidence-Based Analysis
Based on IBM Style Guide topic: "Conjunctions"
"""
from typing import List, Dict, Any, Optional, Set, Tuple
try:
    from .base_language_rule import BaseLanguageRule
except ImportError:
    # Fallback for direct imports or when module structure is problematic
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from language_and_grammar.base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc, Token, Span
except ImportError:
    Doc = None
    Token = None
    Span = None

class ConjunctionsRule(BaseLanguageRule):
    """
    Evidence-based analysis for conjunction-related issues using multi-level scoring:
    
    - MICRO-LEVEL: Linguistic analysis (POS tags, dependencies, morphology)
    - MESO-LEVEL: Structural analysis (block types, heading levels, document structure)
    - MACRO-LEVEL: Semantic analysis (content type, audience, domain)
    - FEEDBACK-LEVEL: Learning from user corrections and preferences
    """
    
    def _get_rule_type(self) -> str:
        return 'conjunctions'
    
    def __init__(self):
        """Initialize the conjunctions rule with proper base class setup."""
        super().__init__()
        self.rule_type = self._get_rule_type()

    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for conjunction usage violations using multi-level scoring.
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        
        if not nlp:
            return errors
        
        try:
            doc = nlp(text)
            for i, sent in enumerate(doc.sents):
                
                # Check coordinating conjunctions with evidence-based scoring
                coord_errors = self._analyze_coordinating_conjunctions_evidence(sent, i, text, context)
                errors.extend(coord_errors)
                
                # Check subordinating conjunctions with multi-level analysis
                subord_errors = self._analyze_subordinating_conjunctions_evidence(sent, i, text, context)
                errors.extend(subord_errors)
                
                # Check parallel structure with contextual awareness
                parallel_errors = self._analyze_parallel_structure_evidence(sent, i, text, context)
                errors.extend(parallel_errors)
                
        except Exception as e:
            # Graceful degradation with low evidence score
            errors.append(self._create_error(
                sentence=text,
                sentence_index=0,
                message=f"Conjunction analysis failed: {str(e)}",
                suggestions=["Please review conjunction usage manually."],
                severity='low',
                text=text,
                context=context,
                evidence_score=0.0  # No evidence when analysis fails
            ))
        
        return errors
    
    # === EVIDENCE-BASED ANALYSIS METHODS ===
    
    def _analyze_coordinating_conjunctions_evidence(self, sent: 'Span', sentence_index: int, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for coordinating conjunction issues.
        Uses multi-level evidence scoring for sentence-initial conjunctions.
        """
        errors = []
        coordinating_conjunctions = {'and', 'but', 'or', 'nor', 'for', 'yet', 'so'}
        
        for token in sent:
            if (token.lemma_.lower() in coordinating_conjunctions and 
                token.pos_ == 'CCONJ' and token.i == sent.start):
                
                # Multi-level evidence calculation
                evidence_score = self._calculate_sentence_initial_conjunction_evidence(token, sent, text, context)
                
                if evidence_score > 0.1:  # Threshold for reporting
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_index,
                        message=self._get_contextual_conjunction_message('sentence_initial', evidence_score, context, conjunction=token.text),
                        suggestions=self._generate_smart_conjunction_suggestions('sentence_initial', token.text, context),
                        severity=self._determine_severity_from_evidence(evidence_score),
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text,
                        subtype='sentence_initial_conjunction'
                    ))
        
        return errors
    
    def _analyze_subordinating_conjunctions_evidence(self, sent: 'Span', sentence_index: int, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for subordinating conjunction placement issues.
        NOTE: Comma-related checks are excluded to prevent duplicates with CommasRule.
        """
        errors = []
        subordinating_conjunctions = {
            'although', 'because', 'since', 'while', 'when', 'where', 'if', 'unless',
            'until', 'after', 'before', 'as', 'though', 'whereas', 'provided'
        }
        
        for token in sent:
            if (token.lemma_.lower() in subordinating_conjunctions and 
                token.pos_ == 'SCONJ' and token.i == sent.start):
                
                # Focus on conjunction placement and clause structure (not commas)
                evidence_score = self._calculate_subordinate_conjunction_structure_evidence(token, sent, text, context)
                
                if evidence_score > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_index,
                        message=self._get_contextual_conjunction_message('subordinate_structure', evidence_score, context, conjunction=token.text),
                        suggestions=self._generate_smart_conjunction_suggestions('subordinate_structure', token.text, context),
                        severity=self._determine_severity_from_evidence(evidence_score),
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text,
                        subtype='subordinate_conjunction_structure'
                    ))
        
        return errors
    
    def _analyze_parallel_structure_evidence(self, sent: 'Span', sentence_index: int, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for parallel structure violations in coordinated elements.
        """
        errors = []
        
        # Find coordinating conjunctions that join multiple elements
        for token in sent:
            if token.pos_ == 'CCONJ' and token.lemma_.lower() in ['and', 'or']:
                coordinated_elements = self._get_coordinated_elements(token, sent)
                
                if len(coordinated_elements) >= 2:
                    parallel_error = self._check_parallel_structure_evidence(coordinated_elements, sent, sentence_index, text, context)
                    if parallel_error:
                        errors.append(parallel_error)
        
        return errors
    
    # === MULTI-LEVEL EVIDENCE CALCULATION ===
    
    def _calculate_sentence_initial_conjunction_evidence(self, conjunction: 'Token', sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """
        Multi-level evidence calculation for sentence-initial conjunction issues.
        
        Uses MICRO/MESO/MACRO/FEEDBACK level analysis for comprehensive scoring.
        """
        
        # === STEP 1: BASE EVIDENCE ===
        evidence_score = self._get_base_sentence_initial_evidence(conjunction, sent)
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_sentence_initial(evidence_score, conjunction, sent, text)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_sentence_initial(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_sentence_initial(evidence_score, conjunction, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_sentence_initial(evidence_score, conjunction, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _calculate_subordinate_conjunction_structure_evidence(self, conjunction: 'Token', sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """
        Multi-level evidence calculation for subordinate conjunction structure issues.
        NOTE: Comma-related analysis is excluded to prevent duplicates.
        """
        
        # === STEP 1: BASE EVIDENCE ===
        evidence_score = self._get_base_subordinate_structure_evidence(conjunction, sent)
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_subordinate_structure(evidence_score, conjunction, sent, text)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_subordinate_structure(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_subordinate_structure(evidence_score, conjunction, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_subordinate_structure(evidence_score, conjunction, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    # === BASE EVIDENCE METHODS ===
    
    def _get_base_sentence_initial_evidence(self, conjunction: 'Token', sent: 'Span') -> float:
        """Get base evidence score for sentence-initial conjunction concerns."""
        
        # Different conjunctions have different base evidence
        conjunction_evidence = {
            'and': 0.3,  # Common and sometimes acceptable
            'but': 0.2,  # Often acceptable for contrast
            'or': 0.4,   # Less common, more problematic
            'nor': 0.6,  # Formal, often awkward at sentence start
            'for': 0.5,  # Can be confusing (preposition vs conjunction)
            'yet': 0.3,  # Similar to 'but', sometimes acceptable
            'so': 0.4    # Informal, better to restructure
        }
        
        return conjunction_evidence.get(conjunction.lemma_.lower(), 0.4)
    
    def _get_base_subordinate_structure_evidence(self, conjunction: 'Token', sent: 'Span') -> float:
        """Get base evidence score for subordinate conjunction structure concerns."""
        
        # Focus on clause complexity and structure, not commas
        main_clause_start = self._find_main_clause_start(conjunction, sent)
        if main_clause_start:
            clause_length = main_clause_start.i - conjunction.i
            
            # Very long subordinate clauses may be problematic for clarity
            if clause_length >= 10:  # Very long subordinate clause
                return 0.4
            elif clause_length >= 7:  # Moderately long subordinate clause
                return 0.2
            else:  # Short subordinate clause
                return 0.1
        
        return 0.2  # Default evidence
    
    # === LINGUISTIC CLUES (MICRO-LEVEL) ===
    
    def _apply_linguistic_clues_sentence_initial(self, evidence_score: float, conjunction: 'Token', sent: 'Span', text: str) -> float:
        """Apply linguistic analysis clues for sentence-initial conjunctions."""
        
        # Check if previous sentence exists and ends with specific patterns
        if conjunction.i > 0:
            # Check for sentence connectivity patterns
            prev_tokens = [token for token in sent.doc[:sent.start] if not token.is_space]
            if prev_tokens:
                last_prev_token = prev_tokens[-1]
                
                # Strong connection suggests conjunction is appropriate
                if last_prev_token.text in ['.', '!', '?']:
                    # Look for semantic connection indicators
                    if any(word in text.lower() for word in ['however', 'therefore', 'thus', 'consequently']):
                        evidence_score -= 0.2  # Reduce evidence if strong connective context
        
        # Check conjunction's syntactic role
        if conjunction.dep_ in ['cc', 'mark']:  # Coordinating or subordinating marker
            evidence_score += 0.1  # Slight increase for clear syntactic role
        
        return evidence_score
    
    def _apply_linguistic_clues_subordinate_structure(self, evidence_score: float, conjunction: 'Token', sent: 'Span', text: str) -> float:
        """Apply linguistic analysis clues for subordinate conjunction structure."""
        
        # Analyze the complexity of the subordinate clause
        subordinate_tokens = []
        for token in sent[conjunction.i - sent.start:]:
            if token.dep_ == 'nsubj' and token.head != conjunction:
                break  # Found main clause subject
            subordinate_tokens.append(token)
        
        # Complex subordinate clauses may need restructuring
        if len(subordinate_tokens) > 8:
            evidence_score += 0.2
        
        # Check for nested clauses within the subordinate clause
        nested_conjunctions = sum(1 for token in subordinate_tokens 
                                if token.pos_ in ['SCONJ', 'CCONJ'])
        if nested_conjunctions > 1:
            evidence_score += 0.2  # Nested complexity may impact clarity
        
        return evidence_score
    
    # === STRUCTURAL CLUES (MESO-LEVEL) ===
    
    def _apply_structural_clues_sentence_initial(self, evidence_score: float, context: Dict[str, Any]) -> float:
        """Apply document structure clues for sentence-initial conjunction detection."""
        
        block_type = context.get('block_type', 'paragraph')
        
        # === TECHNICAL DOCUMENTATION CONTEXTS ===
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.8  # Code blocks may contain conjunction examples
        elif block_type == 'inline_code':
            evidence_score -= 0.6  # Inline code may show conjunctions
        
        # === HEADING CONTEXT ===
        if block_type == 'heading':
            heading_level = context.get('block_level', 1)
            if heading_level == 1:  # H1 - Main headings
                evidence_score += 0.3  # Main headings should avoid sentence-initial conjunctions
            elif heading_level <= 3:  # H2-H3 - Section headings
                evidence_score += 0.2  # Section headings should be clear
        
        # === LIST CONTEXT ===
        if block_type in ['list_item', 'unordered_list', 'ordered_list']:
            evidence_score -= 0.2  # Lists may have more informal conjunction usage
        
        # === ADMONITION CONTEXT ===
        if block_type in ['note', 'tip', 'warning', 'caution', 'important']:
            evidence_score += 0.1  # Admonitions should be clear and direct
        
        return evidence_score
    
    def _apply_structural_clues_subordinate_structure(self, evidence_score: float, context: Dict[str, Any]) -> float:
        """Apply document structure clues for subordinate conjunction structure."""
        
        block_type = context.get('block_type', 'paragraph')
        
        # === PROCEDURAL DOCUMENTATION ===
        if block_type in ['procedure', 'step', 'instruction']:
            evidence_score += 0.2  # Procedures need clear clause structure
        
        # === FORMAL DOCUMENTATION ===
        if block_type in ['heading', 'title']:
            evidence_score += 0.1  # Formal contexts need proper structure
        
        # === TECHNICAL SPECIFICATIONS ===
        if block_type in ['specification', 'requirement']:
            evidence_score += 0.3  # Specifications must be unambiguous
        
        return evidence_score
    
    # === SEMANTIC CLUES (MACRO-LEVEL) ===
    
    def _apply_semantic_clues_sentence_initial(self, evidence_score: float, conjunction: 'Token', text: str, context: Dict[str, Any]) -> float:
        """Apply semantic analysis clues for sentence-initial conjunctions."""
        
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        
        # === CONTENT TYPE ADJUSTMENTS ===
        if content_type == 'academic':
            evidence_score += 0.4  # Academic writing should avoid sentence-initial conjunctions
        elif content_type == 'formal':
            evidence_score += 0.3  # Formal writing should be more conservative
        elif content_type == 'legal':
            evidence_score += 0.5  # Legal writing must be precise and formal
        elif content_type == 'technical':
            evidence_score += 0.2  # Technical writing should be clear but not overly formal
        elif content_type in ['conversational', 'marketing']:
            evidence_score -= 0.2  # More casual contexts are permissive
        
        # === AUDIENCE ADJUSTMENTS ===
        if audience in ['expert', 'developer']:
            evidence_score -= 0.1  # Expert audiences more forgiving
        elif audience in ['beginner', 'general']:
            evidence_score += 0.2  # General audiences need clearer language
        
        # === DOMAIN-SPECIFIC ADJUSTMENTS ===
        if self._is_procedural_documentation(text):
            evidence_score += 0.2  # Procedures should have clear sentence starts
        elif self._is_api_documentation(text):
            evidence_score += 0.1  # API docs should be clear but not overly formal
        
        return evidence_score
    
    def _apply_semantic_clues_subordinate_structure(self, evidence_score: float, conjunction: 'Token', text: str, context: Dict[str, Any]) -> float:
        """Apply semantic analysis clues for subordinate conjunction structure."""
        
        content_type = context.get('content_type', 'general')
        
        # === CONTENT TYPE ADJUSTMENTS ===
        if content_type in ['academic', 'formal', 'legal']:
            evidence_score += 0.2  # Formal contexts require clear structure
        elif content_type == 'technical':
            evidence_score += 0.1  # Technical writing should be unambiguous
        elif content_type == 'procedural':
            evidence_score += 0.3  # Procedures must have clear clause boundaries
        
        # === COMPLEXITY ANALYSIS ===
        if self._has_high_technical_density(text):
            evidence_score += 0.2  # Technical complexity requires clear structure
        
        return evidence_score
    
    # === FEEDBACK PATTERNS (LEARNING CLUES) ===
    
    def _apply_feedback_clues_sentence_initial(self, evidence_score: float, conjunction: 'Token', context: Dict[str, Any]) -> float:
        """Apply user feedback patterns for sentence-initial conjunctions."""
        
        # Get cached feedback patterns for this rule type
        feedback_patterns = self._get_cached_feedback_patterns('conjunctions')
        
        conjunction_text = conjunction.text.lower()
        
        # === ACCEPTED PATTERNS ===
        if conjunction_text in feedback_patterns.get('accepted_terms', set()):
            evidence_score -= 0.3  # User has accepted this conjunction usage
        
        # === REJECTED PATTERNS ===
        if conjunction_text in feedback_patterns.get('rejected_terms', set()):
            evidence_score += 0.3  # User has rejected similar usage
        
        # === CONTEXT-SPECIFIC PATTERNS ===
        content_type = context.get('content_type', 'general')
        context_patterns = feedback_patterns.get('context_patterns', {})
        if content_type in context_patterns:
            context_feedback = context_patterns[content_type]
            if conjunction_text in context_feedback.get('accepted', set()):
                evidence_score -= 0.2
            elif conjunction_text in context_feedback.get('rejected', set()):
                evidence_score += 0.2
        
        return evidence_score
    
    def _apply_feedback_clues_subordinate_structure(self, evidence_score: float, conjunction: 'Token', context: Dict[str, Any]) -> float:
        """Apply user feedback patterns for subordinate conjunction structure."""
        
        feedback_patterns = self._get_cached_feedback_patterns('conjunctions')
        
        # === STRUCTURE CORRECTION SUCCESS RATES ===
        correction_success = feedback_patterns.get('correction_success', {})
        structure_corrections = correction_success.get('subordinate_structure', {})
        
        conjunction_text = conjunction.text.lower()
        if conjunction_text in structure_corrections:
            success_rate = structure_corrections[conjunction_text]
            if success_rate > 0.8:  # High success rate
                evidence_score += 0.2
            elif success_rate < 0.3:  # Low success rate (many false positives)
                evidence_score -= 0.3
        
        return evidence_score
    
    # === UTILITY METHODS ===
    
    def _find_main_clause_start(self, subordinating_conj: 'Token', sent: 'Span') -> Optional['Token']:
        """Find the start of the main clause after a subordinating conjunction."""
        
        for token in sent[subordinating_conj.i - sent.start + 1:]:
            # Look for main clause subject that's not dependent on the subordinate clause
            if (token.dep_ == 'nsubj' and 
                token.head != subordinating_conj and
                not any(child.head == subordinating_conj for child in token.subtree)):
                return token
        
        return None
    
    def _get_coordinated_elements(self, conjunction: 'Token', sent: 'Span') -> List['Token']:
        """Get elements coordinated by a conjunction."""
        
        coordinated_elements = []
        
        # Find elements connected by this conjunction
        if conjunction.dep_ == 'cc':
            # Look for elements this conjunction coordinates
            head = conjunction.head
            if head:
                coordinated_elements.append(head)
                
                # Find other coordinated elements
                for child in head.head.children if head.head else []:
                    if child != head and child.dep_ == head.dep_:
                        coordinated_elements.append(child)
        
        return coordinated_elements
    
    def _check_parallel_structure_evidence(self, elements: List['Token'], sent: 'Span', sentence_index: int, text: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for parallel structure violations with evidence scoring."""
        
        if len(elements) < 2:
            return None
        
        # Analyze grammatical consistency
        pos_tags = [element.pos_ for element in elements]
        deps = [element.dep_ for element in elements]
        
        # Check for consistency in POS tags and dependencies
        pos_consistent = len(set(pos_tags)) == 1
        dep_consistent = len(set(deps)) == 1
        
        if not pos_consistent or not dep_consistent:
            # Calculate evidence for parallel structure violation
            evidence_score = 0.6  # Base evidence for inconsistency
            
            # Adjust based on context
            content_type = context.get('content_type', 'general')
            if content_type in ['academic', 'formal']:
                evidence_score += 0.2
            elif content_type == 'legal':
                evidence_score += 0.3
            
            if evidence_score > 0.1:
                element_texts = [elem.text for elem in elements]
                
                return self._create_error(
                    sentence=sent.text,
                    sentence_index=sentence_index,
                    message=self._get_contextual_conjunction_message('parallel_structure', evidence_score, context, elements=element_texts),
                    suggestions=self._generate_smart_conjunction_suggestions('parallel_structure', ', '.join(element_texts), context),
                    severity=self._determine_severity_from_evidence(evidence_score),
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=(elements[0].idx, elements[-1].idx + len(elements[-1].text)),
                    flagged_text=' '.join(element_texts),
                    subtype='parallel_structure'
                )
        
        return None
    
    def _determine_severity_from_evidence(self, evidence_score: float) -> str:
        """Determine error severity based on evidence score."""
        
        if evidence_score >= 0.7:
            return 'high'
        elif evidence_score >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _get_contextual_conjunction_message(self, violation_type: str, evidence_score: float, context: Dict[str, Any], **kwargs) -> str:
        """Generate contextual error message for conjunction violations."""
        
        content_type = context.get('content_type', 'general')
        
        if violation_type == 'sentence_initial':
            conjunction = kwargs.get('conjunction', 'conjunction')
            if evidence_score > 0.6:
                if content_type in ['academic', 'formal']:
                    return f"Avoid starting sentences with '{conjunction}' in formal writing. Consider restructuring the sentence."
                else:
                    return f"Consider avoiding '{conjunction}' at the beginning of sentences for improved clarity."
            else:
                return f"Starting sentences with '{conjunction}' may impact readability. Consider restructuring if appropriate."
                
        elif violation_type == 'subordinate_structure':
            conjunction = kwargs.get('conjunction', 'subordinate conjunction')
            return f"Consider restructuring this '{conjunction}' clause for improved clarity and readability."
            
        elif violation_type == 'parallel_structure':
            elements = kwargs.get('elements', [])
            return f"These coordinated elements may not have parallel structure: {', '.join(elements[:2])}. Ensure consistent grammatical forms."
        
        return f"Consider reviewing this {violation_type} for context appropriateness."
    
    def _generate_smart_conjunction_suggestions(self, violation_type: str, original_text: str, context: Dict[str, Any]) -> List[str]:
        """Generate smart suggestions for conjunction violations."""
        
        content_type = context.get('content_type', 'general')
        suggestions = []
        
        if violation_type == 'sentence_initial':
            suggestions.extend([
                "Combine with the previous sentence using a comma",
                "Start the sentence with a different word or phrase",
                "Restructure to put the main clause first"
            ])
            
        elif violation_type == 'subordinate_structure':
            suggestions.extend([
                "Break into shorter, clearer sentences",
                "Restructure to put the main clause first",
                "Simplify the subordinate clause structure"
            ])
            
        elif violation_type == 'parallel_structure':
            suggestions.extend([
                "Use consistent grammatical forms for coordinated elements",
                "Ensure all items in the series follow the same pattern",
                "Consider breaking into separate sentences if too complex"
            ])
        
        # Add context-specific suggestions
        if content_type == 'technical':
            suggestions.append("Ensure clarity for technical accuracy")
        elif content_type == 'procedural':
            suggestions.append("Maintain clear step-by-step flow")
        
        return suggestions[:3]  # Return top 3 suggestions