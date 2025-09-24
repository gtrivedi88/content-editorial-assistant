"""
Conjunctions Rule - Evidence-Based Analysis
Based on IBM Style Guide topic: "Conjunctions"
"""
from typing import List, Dict, Any, Optional, Set, Tuple
try:
    from .base_language_rule import BaseLanguageRule
    from .services.language_vocabulary_service import LanguageVocabularyService
except ImportError:
    # Fallback for direct imports or when module structure is problematic
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from language_and_grammar.base_language_rule import BaseLanguageRule
    from language_and_grammar.services.language_vocabulary_service import LanguageVocabularyService

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
        self.vocabulary_service = LanguageVocabularyService()

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
        Parallel structure analysis using direct grammatical tag comparison.

        """
        errors = []
        
        # Find all coordination groups in the sentence
        coordinated_groups = self._find_coordinated_elements_simple(sent)
        
        for group in coordinated_groups:
            if len(group) >= 2:
                parallel_error = self._check_parallel_tags(group, sent, sentence_index, text, context)
                if parallel_error:
                    errors.append(parallel_error)
        
        return errors

    def _find_coordinated_elements_simple(self, sent: 'Span') -> List[List['Token']]:
        """
        Robust coordination detection using direct conj relationships.

        """
        groups = []
        processed_tokens = set()
        
        # Find all tokens with conj dependency (they are coordinated with their head)
        for token in sent:
            if token.dep_ == 'conj' and token not in processed_tokens:
                # Start a new coordination group
                group = [token.head, token]  # Head and the conjunct
                processed_tokens.add(token)
                processed_tokens.add(token.head)
                
                # Find all other tokens coordinated with the same head
                for other_token in sent:
                    if (other_token.dep_ == 'conj' and 
                        other_token.head == token.head and 
                        other_token not in processed_tokens):
                        group.append(other_token)
                        processed_tokens.add(other_token)
                
                if len(group) >= 2:
                    groups.append(group)
        
        return groups

    
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
    
    
    def _check_parallel_tags(self, elements: List['Token'], sent: 'Span', sentence_index: int, text: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Simple, robust parallel structure check using grammatical tags.
        
        Compares token.tag_ for each coordinated element:
        - VBG (creating) vs NN (analysis) vs TO (to) + VB (generate) = violation
        - VBG vs VBG vs VBG = parallel ✓
        """
        
        if len(elements) < 2:
            return None
        
        # Get grammatical patterns for each element
        element_patterns = []
        element_texts = []
        
        for element in elements:
            # Get the grammatical pattern for this element
            pattern = self._get_grammatical_pattern(element, sent)
            element_patterns.append(pattern)
            
            # Get clean text representation
            element_text = self._get_element_text(element, sent)
            element_texts.append(element_text)
        
        # Check for consistency in grammatical patterns
        unique_patterns = set(element_patterns)
        if len(unique_patterns) > 1:
            # Calculate evidence score based on pattern mismatch severity
            evidence_score = self._calculate_tag_mismatch_evidence(element_patterns, context)
            
            if evidence_score > 0.5:  # Simple threshold
                message = self._create_parallel_structure_message(element_texts, element_patterns)
                suggestions = self._create_parallel_structure_suggestions(element_patterns)
                
                return self._create_error(
                    sentence=sent.text,
                    sentence_index=sentence_index,
                    message=message,
                    suggestions=suggestions,
                    severity=self._determine_severity_from_evidence(evidence_score),
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=(elements[0].idx, elements[-1].idx + len(elements[-1].text)),
                    flagged_text=', '.join(element_texts),
                    subtype='parallel_structure_tag_mismatch'
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


    def _get_grammatical_pattern(self, token: 'Token', sent) -> str:
        """
        Get the grammatical pattern for a coordinated element.
        
        Returns simple patterns like:
        - VBG (gerund: "creating")
        - NN (noun: "analysis")  
        - TO+VB (infinitive: "to generate")
        - NNS (plural noun: "users")
        """
        
        # Handle infinitives: TO + VB
        if token.tag_ == 'VB' and token.i > 0:
            # Handle both Doc and Span objects
            if hasattr(sent, 'start'):  # It's a Span
                start_offset = sent.start
            else:  # It's a Doc
                start_offset = 0
            
            prev_idx = token.i - start_offset - 1
            if prev_idx >= 0:
                prev_token = sent[prev_idx]
                if prev_token and prev_token.text.lower() == 'to' and prev_token.pos_ == 'PART':
                    return 'TO+VB'  # infinitive
        
        # Handle prepositional phrases: starts with preposition
        if token.pos_ == 'ADP':
            return 'PREP'  # prepositional phrase
        
        # Direct tag mapping for most cases
        tag_mappings = {
            'VBG': 'VBG',  # gerund or present participle  
            'NN': 'NN',    # singular noun
            'NNS': 'NNS',  # plural noun
            'VB': 'VB',    # base verb
            'VBD': 'VBD',  # past tense verb
            'VBN': 'VBN',  # past participle
            'VBP': 'VBP',  # present verb
            'VBZ': 'VBZ',  # 3rd person singular present
            'JJ': 'JJ',    # adjective
            'RB': 'RB',    # adverb
        }
        
        return tag_mappings.get(token.tag_, token.tag_)

    def _get_element_text(self, token: 'Token', sent) -> str:
        """
        Get clean text representation of a coordinated element.
        
        For infinitives, includes "to": "to generate"
        For others, just the token: "creating", "analysis"
        """
        
        # Handle infinitives: include the "to"
        if token.tag_ == 'VB' and token.i > 0:
            # Handle both Doc and Span objects
            if hasattr(sent, 'start'):  # It's a Span
                start_offset = sent.start
            else:  # It's a Doc
                start_offset = 0
            
            prev_idx = token.i - start_offset - 1
            if prev_idx >= 0:
                prev_token = sent[prev_idx]
                if prev_token and prev_token.text.lower() == 'to' and prev_token.pos_ == 'PART':
                    return f"to {token.text}"
        
        # For compound nouns, include the modifier
        if token.dep_ in ['compound', 'amod'] and token.head:
            return f"{token.text} {token.head.text}"
        
        # For most cases, just the token text
        return token.text

    def _calculate_tag_mismatch_evidence(self, patterns: List[str], context: Dict[str, Any]) -> float:
        """
        Calculate evidence score for tag mismatches.
        
        Simple scoring based on how severe the mismatch is:
        - Mixed verb forms (VBG vs TO+VB) = high evidence
        - Mixed noun/verb forms = high evidence  
        - Similar forms = lower evidence
        """
        
        unique_patterns = set(patterns)
        base_evidence = 0.7  # Start with high evidence for any mismatch
        
        # Increase evidence for severe mismatches
        has_verbs = any(p in ['VBG', 'VB', 'VBD', 'VBN', 'VBP', 'VBZ', 'TO+VB'] for p in unique_patterns)
        has_nouns = any(p in ['NN', 'NNS'] for p in unique_patterns)
        has_prep = any(p == 'PREP' for p in unique_patterns)
        
        if has_verbs and has_nouns:
            base_evidence = 0.9  # Very clear violation
        elif has_prep and (has_verbs or has_nouns):
            base_evidence = 0.8  # Clear structural mismatch
        elif 'TO+VB' in unique_patterns and 'VBG' in unique_patterns:
            base_evidence = 0.85  # Classic gerund/infinitive mismatch
        
        # Context adjustments
        content_type = context.get('content_type', 'general')
        if content_type in ['technical', 'academic', 'formal']:
            base_evidence += 0.1
        
        return min(base_evidence, 1.0)

    def _create_parallel_structure_message(self, element_texts: List[str], patterns: List[str]) -> str:
        """Create a clear, helpful error message."""
        
        pattern_descriptions = {
            'VBG': 'gerund (-ing verb)',
            'NN': 'noun',
            'NNS': 'plural noun', 
            'TO+VB': 'infinitive (to + verb)',
            'PREP': 'prepositional phrase',
            'JJ': 'adjective',
            'VB': 'base verb'
        }
        
        # Create element descriptions
        elements_desc = []
        for text, pattern in zip(element_texts, patterns):
            desc = pattern_descriptions.get(pattern, pattern)
            elements_desc.append(f"'{text}' ({desc})")
        
        return f"Non-parallel structure: {', '.join(elements_desc)}. Use consistent grammatical forms."

    def _create_parallel_structure_suggestions(self, patterns: List[str]) -> List[str]:
        """Create helpful suggestions for fixing parallel structure."""
        
        unique_patterns = set(patterns)
        suggestions = []
        
        if 'VBG' in unique_patterns and 'TO+VB' in unique_patterns:
            suggestions.extend([
                "Convert all to gerunds: 'creating datasets, analyzing data, generating reports'",
                "Convert all to infinitives: 'to create datasets, to analyze data, to generate reports'"
            ])
        elif 'VBG' in unique_patterns and 'NN' in unique_patterns:
            suggestions.extend([
                "Convert all to gerunds: 'creating datasets, analyzing data, monitoring systems'",
                "Convert all to nouns: 'dataset creation, data analysis, system monitoring'"
            ])
        elif 'PREP' in unique_patterns:
            suggestions.append("Use consistent prepositional structure or remove prepositions")
        else:
            suggestions.append("Ensure all coordinated elements use the same grammatical form")
        
        return suggestions[:3]  # Return top 3

    def _get_conjunctions_patterns(self) -> Dict[str, Any]:
        """Get conjunctions patterns from YAML vocabulary service."""
        return self.vocabulary_service._load_yaml_file("conjunctions_patterns.yaml")