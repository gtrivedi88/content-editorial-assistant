"""
Procedures Rule (Enhanced with Evidence-Based Analysis)
Based on IBM Style Guide topic: "Procedures"
Enhanced to follow evidence-based rule development methodology for zero false positives.
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ProceduresRule(BaseStructureRule):
    """
    Checks that steps within a Procedure topic begin with an imperative verb using evidence-based analysis.
    Implements rule-specific evidence calculation for optimal false positive reduction.
    
    Violations detected:
    - Steps that don't begin with strong, imperative verbs in procedural content
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'procedures'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes procedural steps for violations using evidence-based scoring.
        Each potential violation gets nuanced evidence assessment for precision.
        """
        errors = []
        if not nlp or not context:
            return errors

        # CONTEXT CHECK: Only run this rule inside a Procedure topic.
        if context.get('topic_type') != 'Procedure':
            return errors

        if context.get('block_type') not in ['list_item_ordered', 'list_item_unordered', 'list_item']:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            if not doc:
                continue

            if not self._is_valid_procedural_step(doc):
                evidence_score = self._calculate_procedural_step_evidence(
                    sentence, doc, text, context
                )
                
                if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=self._get_contextual_message('invalid_procedural_step', evidence_score, context, sentence=sentence),
                        suggestions=self._generate_smart_suggestions('invalid_procedural_step', evidence_score, context, sentence=sentence, doc=doc),
                        severity='medium',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(0, len(sentence)),
                        flagged_text=sentence
                    ))
        return errors

    # === EVIDENCE CALCULATION METHODS ===

    def _calculate_procedural_step_evidence(self, sentence: str, doc: 'Doc', 
                                          text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for potential procedural step violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            sentence: The step sentence
            doc: SpaCy document of the sentence
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === ZERO FALSE POSITIVE GUARDS ===
        # CRITICAL: Apply rule-specific guards FIRST to eliminate common exceptions
        
        # Kill evidence immediately for contexts where this specific rule should never apply
        if not context or context.get('topic_type') != 'Procedure':
            return 0.0  # Only apply to procedure topics
        
        # Don't flag steps in actual quoted examples or citations
        if self._is_step_in_actual_quotes(sentence, context):
            return 0.0  # Quoted examples are not procedural errors
        
        # Don't flag steps in technical documentation contexts with approved patterns
        if self._is_step_in_technical_context(sentence, doc, context):
            return 0.0  # Technical docs may use different conventions
        
        # Don't flag steps in reference or citation context
        if self._is_step_in_citation_context(sentence, context):
            return 0.0  # Academic papers, documentation references, etc.
        
        # Apply inherited zero false positive guards
        violation = {'text': sentence, 'sentence': sentence}
        if self._apply_zero_false_positive_guards_structure(violation, context):
            return 0.0
        
        # Special guard: Optional or conditional steps
        if self._is_optional_or_conditional_step(sentence, doc):
            return 0.0
        
        # Special guard: Explanatory or result steps
        if self._is_explanatory_step(sentence, doc):
            return 0.0
        
        # Special guard: Reference or navigation steps
        if self._is_reference_step(sentence):
            return 0.0
        
        # Special guard: Introductory or concluding steps
        if self._is_introductory_or_concluding_step(sentence, context):
            return 0.0
        
        # Special guard: Meta-instructional steps (about the procedure itself)
        if self._is_meta_instructional_step(sentence, doc):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_procedural_step_base_evidence_score(sentence, doc, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this step
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        if doc and len(doc) > 0:
            first_token = doc[0]
            
            # Check what type of non-imperative structure we have
            if first_token.pos_ == 'NOUN':
                evidence_score += 0.2  # Noun starts are less procedural
            elif first_token.pos_ == 'VERB' and first_token.tag_ in ['VBG', 'VBD', 'VBN']:
                evidence_score += 0.3  # Wrong verb forms are clear violations
            elif first_token.pos_ == 'DET':  # "The", "A", etc.
                evidence_score += 0.1  # Descriptive rather than instructional
            elif first_token.pos_ == 'PRON':  # "You", "We", etc.
                evidence_score += 0.1  # Personal pronouns suggest non-imperative
            
            # Check sentence structure complexity
            has_subject = any(token.dep_ in ('nsubj', 'nsubjpass') for token in doc)
            if has_subject:
                evidence_score -= 0.1  # Complete sentences might be acceptable in some contexts
            
            # Check for passive voice indicators
            if self._has_passive_voice_indicators(doc):
                evidence_score += 0.2  # Passive voice is non-imperative
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._adjust_evidence_for_structure_context(evidence_score, context)
        
        # Check procedure complexity and step position
        step_number = context.get('step_number', 1)
        total_steps = context.get('total_steps', 1)
        
        if step_number == 1:
            evidence_score += 0.1  # First steps should especially be clear imperatives
        elif step_number == total_steps:
            evidence_score -= 0.05  # Last steps might be summaries or conclusions
        
        # Check list context
        list_depth = context.get('list_depth', 1)
        if list_depth > 1:
            evidence_score -= 0.1  # Nested lists might be more flexible
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        # Content type adjustments
        content_type = context.get('content_type', 'general')
        if content_type in ['tutorial', 'user_guide']:
            evidence_score += 0.15  # User-facing procedures should be very clear
        elif content_type in ['technical', 'reference']:
            evidence_score -= 0.1  # Technical procedures might be more flexible
        elif content_type in ['academic', 'formal']:
            evidence_score -= 0.05  # Academic procedures might use different styles
        
        # Audience considerations
        audience = context.get('audience', 'general')
        if audience in ['beginner', 'general']:
            evidence_score += 0.1  # Beginners need clear imperative steps
        elif audience in ['expert', 'developer']:
            evidence_score -= 0.05  # Experts might understand non-imperative instructions
        
        # Domain considerations
        domain = context.get('domain', 'general')
        if domain in ['software', 'technical']:
            evidence_score -= 0.05  # Technical domains might be more flexible
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_procedural_steps(evidence_score, sentence, doc, context)
        
        # Procedural step-specific final adjustments (moderate to avoid evidence inflation)
        evidence_score += 0.05  # IBM Style Guide is clear on imperative steps
        
        return max(0.0, min(1.0, evidence_score))

    # === ENHANCED HELPER METHODS FOR 6-STEP EVIDENCE PATTERN ===
    
    def _is_step_in_actual_quotes(self, sentence: str, context: Dict[str, Any] = None) -> bool:
        """
        Surgical check: Is the step actually within quotation marks?
        Only returns True for genuine quoted content, not incidental quote references.
        """
        if not sentence:
            return False
        
        # Look for quote pairs that actually enclose the step
        import re
        
        # Find all potential quote pairs
        quote_patterns = [
            (r'"([^"]*)"', '"'),  # Double quotes
            (r"'([^']*)'", "'"),  # Single quotes
            (r'`([^`]*)`', '`')   # Backticks
        ]
        
        for pattern, quote_char in quote_patterns:
            matches = re.finditer(pattern, sentence)
            for match in matches:
                quoted_content = match.group(1)
                # If substantial portion of step is quoted, consider it quoted
                if len(quoted_content.strip()) > len(sentence.strip()) * 0.7:
                    return True
        
        return False
    
    def _is_step_in_technical_context(self, sentence: str, doc: 'Doc', context: Dict[str, Any] = None) -> bool:
        """
        Check if step appears in technical documentation context with approved patterns.
        """
        if not sentence or not context:
            return False
        
        # Check content type for technical context
        content_type = context.get('content_type', '')
        if content_type in ['technical', 'api', 'reference', 'developer']:
            # In technical docs, check for specific patterns that might use non-imperative forms
            technical_step_patterns = [
                'function:', 'method:', 'api call:', 'request:', 'response:',
                'parameter:', 'returns:', 'output:', 'result:', 'example:'
            ]
            
            sentence_lower = sentence.lower()
            if any(pattern in sentence_lower for pattern in technical_step_patterns):
                return True
        
        # Check for code or API documentation patterns
        api_patterns = [
            r'[A-Z_]+\s*=\s*',       # Constants
            r'\w+\(\)\s*',            # Function calls
            r'HTTP\s+(GET|POST|PUT|DELETE|PATCH)',  # HTTP methods
            r'status\s+code\s+\d+',   # Status codes
            r'curl\s+-X',             # cURL commands
        ]
        
        import re
        if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in api_patterns):
            return True
        
        return False
    
    def _is_step_in_citation_context(self, sentence: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if step appears in citation or reference context.
        """
        if not sentence:
            return False
        
        sentence_lower = sentence.lower()
        
        # Check for citation indicators
        citation_indicators = [
            'according to', 'as stated in', 'reference:', 'cited in',
            'documentation shows', 'manual states', 'guide recommends',
            'specification defines', 'standard requires'
        ]
        
        for indicator in citation_indicators:
            if indicator in sentence_lower:
                return True
        
        # Check for reference formatting patterns
        if any(pattern in sentence_lower for pattern in ['see also', 'refer to', 'as described']):
            return True
        
        return False
    
    def _is_optional_or_conditional_step(self, sentence: str, doc: 'Doc') -> bool:
        """Check if step is optional or conditional."""
        sentence_lower = sentence.lower()
        
        # Optional indicators
        optional_indicators = ['optional', 'optionally', 'if needed', 'if desired', 'as needed', 'alternatively']
        if any(indicator in sentence_lower for indicator in optional_indicators):
            return True
        
        # Conditional indicators (only at the beginning)
        if doc and len(doc) > 0:
            first_token = doc[0]
            if first_token.lemma_.lower() in ['if', 'unless', 'should', 'might', 'may']:
                return True
            # "When" only if it's truly conditional (starts the sentence)
            if first_token.lemma_.lower() == 'when' and first_token.i == 0:
                return True
        
        # Check for conditional phrase patterns (only at beginning)
        conditional_patterns = [
            r'^if\s+\w+', r'^when\s+\w+', r'^unless\s+\w+',
            r'^should\s+you', r'^may\s+want', r'^might\s+need'
        ]
        
        import re
        if any(re.search(pattern, sentence_lower) for pattern in conditional_patterns):
            return True
        
        return False

    def _is_explanatory_step(self, sentence: str, doc: 'Doc') -> bool:
        """Check if step is explanatory rather than instructional."""
        sentence_lower = sentence.lower()
        
        # Explanatory indicators
        explanatory_indicators = [
            'this will', 'this should', 'you will see', 'the system will', 'note that',
            'this action', 'this causes', 'this enables', 'this displays', 'this shows'
        ]
        if any(indicator in sentence_lower for indicator in explanatory_indicators):
            return True
        
        # Result indicators
        result_indicators = ['result:', 'outcome:', 'expected:', 'you should see', 'output:', 'response:']
        if any(indicator in sentence_lower for indicator in result_indicators):
            return True
        
        # Explanation patterns
        explanation_patterns = [
            r'\bthis\s+will\s+\w+', r'\bthe\s+system\s+will\s+\w+',
            r'\byou\s+should\s+see', r'\bthis\s+causes\s+\w+'
        ]
        
        import re
        if any(re.search(pattern, sentence_lower) for pattern in explanation_patterns):
            return True
        
        return False

    def _is_reference_step(self, sentence: str) -> bool:
        """Check if step is a reference or navigation instruction."""
        sentence_lower = sentence.lower()
        
        # Reference indicators
        reference_indicators = [
            'see also', 'refer to', 'for more information', 'additional details',
            'more details', 'further information', 'see section', 'see chapter'
        ]
        if any(indicator in sentence_lower for indicator in reference_indicators):
            return True
        
        # Navigation indicators that are references, not actions
        navigation_indicators = [
            'go to section', 'navigate to chapter', 'return to step',
            'see figure', 'see table', 'see appendix'
        ]
        if any(indicator in sentence_lower for indicator in navigation_indicators):
            return True
        
        return False
    
    def _is_introductory_or_concluding_step(self, sentence: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if step is introductory or concluding rather than procedural.
        """
        sentence_lower = sentence.lower()
        
        # Introductory indicators
        intro_indicators = [
            'before you begin', 'prerequisites', 'overview', 'introduction',
            'this procedure', 'the following steps', 'these instructions'
        ]
        if any(indicator in sentence_lower for indicator in intro_indicators):
            return True
        
        # Concluding indicators
        conclusion_indicators = [
            'completion', 'finished', 'done', 'summary', 'conclusion',
            'you have completed', 'the procedure is complete', 'next steps'
        ]
        if any(indicator in sentence_lower for indicator in conclusion_indicators):
            return True
        
        # Check position in procedure
        if context:
            step_number = context.get('step_number', 1)
            total_steps = context.get('total_steps', 1)
            
            # First step might be introductory
            if step_number == 1 and any(word in sentence_lower for word in ['overview', 'introduction', 'begin']):
                return True
            
            # Last step might be concluding
            if step_number == total_steps and any(word in sentence_lower for word in ['complete', 'finished', 'done']):
                return True
        
        return False
    
    def _is_meta_instructional_step(self, sentence: str, doc: 'Doc') -> bool:
        """
        Check if step is meta-instructional (about the procedure itself) rather than task-specific.
        """
        sentence_lower = sentence.lower()
        
        # Meta-instruction indicators
        meta_indicators = [
            'follow these steps', 'complete the following', 'perform these actions',
            'the steps below', 'this procedure', 'these instructions',
            'the following procedure', 'to complete this task'
        ]
        if any(indicator in sentence_lower for indicator in meta_indicators):
            return True
        
        # Self-referential patterns
        self_ref_patterns = [
            r'\bthese\s+steps\b', r'\bthis\s+procedure\b',
            r'\bthe\s+following\s+instructions\b', r'\bthe\s+above\s+steps\b'
        ]
        
        import re
        if any(re.search(pattern, sentence_lower) for pattern in self_ref_patterns):
            return True
        
        return False
    
    def _has_passive_voice_indicators(self, doc: 'Doc') -> bool:
        """
        Check if the sentence uses passive voice construction.
        """
        if not doc:
            return False
        
        # Look for auxiliary verbs + past participles
        for i, token in enumerate(doc):
            if token.lemma_.lower() in ['be', 'get'] and token.pos_ == 'AUX':
                # Check if followed by past participle
                if i + 1 < len(doc):
                    next_token = doc[i + 1]
                    if next_token.tag_ == 'VBN':  # Past participle
                        return True
        
        # Check for passive voice patterns
        passive_patterns = [
            'is selected', 'are configured', 'will be displayed',
            'has been created', 'should be entered', 'can be found'
        ]
        
        sentence_text = doc.text.lower()
        return any(pattern in sentence_text for pattern in passive_patterns)
    
    def _get_procedural_step_base_evidence_score(self, sentence: str, doc: 'Doc', context: Dict[str, Any] = None) -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Clear passive voice → 0.8 (very specific)
        - Wrong verb form → 0.7 (clear pattern)
        - Noun starting → 0.6 (moderate violation)
        - Determiner starting → 0.4 (minor issue)
        """
        if not doc or len(doc) == 0:
            return 0.0
        
        # Enhanced specificity analysis
        if self._is_exact_procedural_violation(sentence, doc):
            return 0.8  # Very specific, clear violation
        elif self._is_pattern_procedural_violation(sentence, doc):
            return 0.6  # Pattern-based, moderate specificity
        elif self._is_minor_procedural_issue(sentence, doc):
            return 0.4  # Minor issue, needs context
        else:
            return 0.3  # Possible issue, needs more evidence
    
    def _is_exact_procedural_violation(self, sentence: str, doc: 'Doc') -> bool:
        """
        Check if sentence represents an exact procedural violation.
        """
        if not doc or len(doc) == 0:
            return False
        
        first_token = doc[0]
        
        # Clear passive voice constructions
        if self._has_passive_voice_indicators(doc):
            return True
        
        # Wrong verb forms (gerund, past tense, past participle)
        if first_token.pos_ == 'VERB' and first_token.tag_ in ['VBG', 'VBD', 'VBN']:
            return True
        
        # Personal pronouns starting sentences (non-imperative)
        if first_token.pos_ == 'PRON' and first_token.text.lower() in ['you', 'we', 'i', 'they']:
            return True
        
        return False
    
    def _is_pattern_procedural_violation(self, sentence: str, doc: 'Doc') -> bool:
        """
        Check if sentence shows a pattern of procedural violation.
        """
        if not doc or len(doc) == 0:
            return False
        
        first_token = doc[0]
        
        # Noun starts (descriptive rather than imperative)
        if first_token.pos_ == 'NOUN':
            return True
        
        # Determiner starts ("The", "A", etc.)
        if first_token.pos_ == 'DET':
            return True
        
        # Non-imperative verb constructions
        if first_token.pos_ == 'VERB' and first_token.dep_ != 'ROOT':
            return True
        
        return False
    
    def _is_minor_procedural_issue(self, sentence: str, doc: 'Doc') -> bool:
        """
        Check if sentence has minor procedural issues.
        """
        if not doc or len(doc) == 0:
            return False
        
        # Sentences with explicit subjects (might be acceptable in some contexts)
        has_subject = any(token.dep_ in ('nsubj', 'nsubjpass') for token in doc)
        if has_subject:
            return True
        
        # Questions (might be acceptable for troubleshooting steps)
        if sentence.strip().endswith('?'):
            return True
        
        return False
    
    def _apply_feedback_clues_procedural_steps(self, evidence_score: float, sentence: str, doc: 'Doc', context: Dict[str, Any] = None) -> float:
        """
        Apply clues learned from user feedback patterns specific to procedural steps.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_procedures()
        
        # Consistently Accepted Non-Imperative Steps
        step_signature = self._get_step_signature(sentence, doc)
        if step_signature in feedback_patterns.get('accepted_non_imperative_steps', set()):
            evidence_score -= 0.5  # Users consistently accept this non-imperative form
        
        # Consistently Rejected Suggestions
        if step_signature in feedback_patterns.get('rejected_imperative_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: Step structure acceptance rates
        step_type = self._classify_step_structure(sentence, doc)
        step_acceptance = feedback_patterns.get('step_structure_acceptance', {})
        acceptance_rate = step_acceptance.get(step_type, 0.5)
        
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # High acceptance, likely valid in some contexts
        elif acceptance_rate < 0.2:
            evidence_score += 0.2  # Low acceptance, strong violation
        
        # Pattern: Content type specific acceptance
        content_type = context.get('content_type', 'general') if context else 'general'
        content_patterns = feedback_patterns.get(f'{content_type}_step_acceptance', {})
        
        acceptance_rate = content_patterns.get(step_type, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Accepted in this content type
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Consistently flagged in this content type
        
        # Pattern: Audience-specific acceptance
        audience = context.get('audience', 'general') if context else 'general'
        audience_patterns = feedback_patterns.get(f'{audience}_step_acceptance', {})
        
        acceptance_rate = audience_patterns.get(step_type, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.2  # Accepted for this audience
        elif acceptance_rate < 0.3:
            evidence_score += 0.1  # Consistently flagged for this audience
        
        # Pattern: Step position acceptance
        step_number = context.get('step_number', 1) if context else 1
        position_patterns = feedback_patterns.get('step_position_acceptance', {})
        
        if step_number == 1:
            acceptance_rate = position_patterns.get('first', 0.3)
        elif step_number <= 3:
            acceptance_rate = position_patterns.get('early', 0.4)
        else:
            acceptance_rate = position_patterns.get('middle_late', 0.5)
        
        if acceptance_rate > 0.6:
            evidence_score -= 0.2
        elif acceptance_rate < 0.3:
            evidence_score += 0.1
        
        return evidence_score
    
    def _get_step_signature(self, sentence: str, doc: 'Doc') -> str:
        """
        Generate a signature for the step for feedback analysis.
        """
        if not doc or len(doc) == 0:
            return 'empty'
        
        # Create a simplified signature based on grammatical structure
        first_token = doc[0]
        pos_pattern = first_token.pos_
        tag_pattern = first_token.tag_
        
        # Add structure indicators
        has_subject = any(token.dep_ in ('nsubj', 'nsubjpass') for token in doc)
        has_passive = self._has_passive_voice_indicators(doc)
        
        structure_flags = []
        if has_subject:
            structure_flags.append('subj')
        if has_passive:
            structure_flags.append('pass')
        
        structure_str = '_'.join(structure_flags) if structure_flags else 'none'
        
        return f"{pos_pattern}_{tag_pattern}_{structure_str}_{hash(sentence.lower()) % 1000}"
    
    def _classify_step_structure(self, sentence: str, doc: 'Doc') -> str:
        """
        Classify the grammatical structure of the step for feedback analysis.
        """
        if not doc or len(doc) == 0:
            return 'empty'
        
        first_token = doc[0]
        
        # Classify based on starting pattern
        if first_token.pos_ == 'VERB' and first_token.dep_ == 'ROOT':
            if first_token.tag_ == 'VB':
                return 'imperative_verb'
            elif first_token.tag_ == 'VBG':
                return 'gerund_start'
            elif first_token.tag_ in ['VBD', 'VBN']:
                return 'past_verb_start'
            else:
                return 'other_verb_start'
        elif first_token.pos_ == 'NOUN':
            return 'noun_start'
        elif first_token.pos_ == 'DET':
            return 'determiner_start'
        elif first_token.pos_ == 'PRON':
            return 'pronoun_start'
        elif first_token.pos_ == 'ADV':
            return 'adverb_start'
        else:
            return 'other_start'
    
    def _get_cached_feedback_patterns_procedures(self) -> Dict[str, Any]:
        """
        Load feedback patterns from cache or feedback analysis for procedural steps.
        """
        # This would load from feedback analysis system
        # For now, return basic patterns with some realistic examples
        return {
            'accepted_non_imperative_steps': set(),  # Specific step signatures users accept
            'rejected_imperative_suggestions': set(),  # Steps users don't want flagged
            'step_structure_acceptance': {
                'imperative_verb': 0.95,      # Imperative verbs almost always acceptable
                'noun_start': 0.2,            # Noun starts rarely acceptable
                'determiner_start': 0.15,     # Determiner starts rarely acceptable
                'pronoun_start': 0.1,         # Pronoun starts rarely acceptable
                'gerund_start': 0.3,          # Gerund starts sometimes acceptable
                'past_verb_start': 0.1,       # Past tense starts rarely acceptable
                'adverb_start': 0.4,          # Adverb starts sometimes acceptable
                'other_start': 0.5            # Other starts moderate acceptance
            },
            'tutorial_step_acceptance': {
                'imperative_verb': 0.98,      # Tutorials need very clear imperatives
                'noun_start': 0.1,            # Noun starts almost never acceptable
                'determiner_start': 0.1,      # Determiner starts almost never acceptable
                'pronoun_start': 0.05,        # Pronoun starts almost never acceptable
                'gerund_start': 0.2,          # Gerund starts rarely acceptable
                'adverb_start': 0.3           # Adverb starts sometimes acceptable
            },
            'technical_step_acceptance': {
                'imperative_verb': 0.9,       # Technical docs more flexible
                'noun_start': 0.4,            # Noun starts more acceptable
                'determiner_start': 0.3,      # Determiner starts more acceptable
                'pronoun_start': 0.2,         # Pronoun starts sometimes acceptable
                'gerund_start': 0.5,          # Gerund starts often acceptable
                'adverb_start': 0.6           # Adverb starts often acceptable
            },
            'reference_step_acceptance': {
                'imperative_verb': 0.85,      # Reference docs even more flexible
                'noun_start': 0.6,            # Noun starts often acceptable
                'determiner_start': 0.5,      # Determiner starts often acceptable
                'pronoun_start': 0.4,         # Pronoun starts sometimes acceptable
                'gerund_start': 0.7,          # Gerund starts very acceptable
                'adverb_start': 0.7           # Adverb starts very acceptable
            },
            'beginner_step_acceptance': {
                'imperative_verb': 0.98,      # Beginners need very clear imperatives
                'noun_start': 0.1,            # Noun starts almost never acceptable
                'determiner_start': 0.1,      # Determiner starts almost never acceptable
                'pronoun_start': 0.05,        # Pronoun starts almost never acceptable
                'gerund_start': 0.2,          # Gerund starts rarely acceptable
                'adverb_start': 0.3           # Adverb starts sometimes acceptable
            },
            'expert_step_acceptance': {
                'imperative_verb': 0.85,      # Experts more tolerant
                'noun_start': 0.5,            # Noun starts acceptable
                'determiner_start': 0.4,      # Determiner starts acceptable
                'pronoun_start': 0.3,         # Pronoun starts sometimes acceptable
                'gerund_start': 0.6,          # Gerund starts often acceptable
                'adverb_start': 0.6           # Adverb starts often acceptable
            },
            'step_position_acceptance': {
                'first': 0.2,                # First steps should be very clear
                'early': 0.3,                # Early steps should be clear
                'middle_late': 0.4            # Later steps more flexible
            }
        }
    
    def _is_valid_procedural_step(self, doc: Doc) -> bool:
        """
        Checks if a sentence is a valid procedural step.
        """
        if not doc:
            return False
            
        first_token = doc[0]

        # Linguistic Anchor: Allow optional or conditional steps.
        if first_token.text.lower() == 'optional' or first_token.lemma_.lower() == 'if':
            return True

        # Linguistic Anchor: The step should start with an imperative verb (ROOT verb).
        is_imperative = (first_token.pos_ == 'VERB' and first_token.dep_ == 'ROOT')

        return is_imperative

    # === CONTEXTUAL MESSAGING AND SUGGESTIONS ===

    def _get_contextual_message(self, violation_type: str, evidence_score: float, 
                               context: Dict[str, Any], **kwargs) -> str:
        """Generate contextual error messages based on violation type and evidence."""
        if violation_type == 'invalid_procedural_step':
            sentence = kwargs.get('sentence', '')
            
            if evidence_score > 0.8:
                return f"Procedural steps must begin with a strong, imperative verb. Rewrite '{sentence[:50]}...' to start with an action."
            elif evidence_score > 0.6:
                return f"Consider rewriting this step to start with an action verb for clarity and directness."
            elif evidence_score > 0.4:
                return f"This step could be more direct and action-oriented for better user guidance."
            else:
                return f"Review if this step follows imperative style guidelines for procedural content."
        
        return "Procedural step formatting issue detected."

    def _generate_smart_suggestions(self, violation_type: str, evidence_score: float,
                                  context: Dict[str, Any], **kwargs) -> List[str]:
        """Generate smart suggestions based on violation type and evidence confidence."""
        suggestions = []
        
        if violation_type == 'invalid_procedural_step':
            sentence = kwargs.get('sentence', '')
            doc = kwargs.get('doc')
            
            if evidence_score > 0.8:
                # High evidence = authoritative, direct suggestions
                if doc and len(doc) > 0:
                    first_token = doc[0]
                    if first_token.pos_ == 'NOUN':
                        suggestions.append("Replace noun start with imperative verb: 'Click the button' not 'The button should be clicked'.")
                    elif first_token.pos_ == 'VERB' and first_token.tag_ == 'VBG':
                        suggestions.append(f"Change '{first_token.text}' to base verb form for clear imperative.")
                    elif first_token.pos_ == 'DET':
                        suggestions.append("Remove article and start with action verb for imperative style.")
                    elif first_token.pos_ == 'PRON':
                        suggestions.append("Remove pronoun and start with direct command verb.")
                    else:
                        suggestions.append("Rewrite to start with strong imperative verb (Click, Enter, Select, Configure).")
                suggestions.append("IBM Style Guide requires imperative verbs for procedural steps.")
                suggestions.append("Clear commands improve user task completion rates significantly.")
            elif evidence_score > 0.6:
                # Medium evidence = balanced, helpful suggestions  
                if doc and len(doc) > 0:
                    first_token = doc[0]
                    if first_token.pos_ == 'NOUN':
                        suggestions.append("Consider starting with action verb instead of noun for clarity.")
                    elif first_token.pos_ == 'VERB' and first_token.tag_ == 'VBG':
                        suggestions.append("Use base verb form instead of -ing form for imperative style.")
                    elif first_token.pos_ == 'DET':
                        suggestions.append("Start with action verb rather than article for direct instruction.")
                    else:
                        suggestions.append("Rewrite to begin with command verb for clearer guidance.")
                suggestions.append("Direct imperative language helps users understand required actions.")
                suggestions.append("Action-oriented steps reduce user confusion and errors.")
            elif evidence_score > 0.4:
                # Medium-low evidence = gentle suggestions
                suggestions.append("Consider if this step could be more action-oriented and direct.")
                suggestions.append("Review if imperative verb form would improve clarity.")
                suggestions.append("Evaluate whether users can easily identify the required action.")
            else:
                # Low evidence = very gentle suggestions
                suggestions.append("This step may be acceptable depending on procedural context.")
                suggestions.append("Consider consistency with other procedural steps in the document.")
                suggestions.append("Review if the current phrasing aligns with your style guidelines.")
            
            # Context-specific suggestions
            content_type = context.get('content_type', '') if context else ''
            if content_type == 'tutorial' and evidence_score > 0.5:
                suggestions.append("Tutorial steps especially benefit from clear imperative verbs.")
            elif content_type == 'technical' and evidence_score > 0.6:
                suggestions.append("Technical procedures should use consistent imperative style.")
            
            # Audience-specific suggestions
            audience = context.get('audience', '') if context else ''
            if audience in ['beginner', 'general'] and evidence_score > 0.5:
                suggestions.append("Beginner users need very clear, direct action instructions.")
        
        return suggestions[:3]  # Limit to 3 suggestions