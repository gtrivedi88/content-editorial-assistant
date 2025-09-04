"""
Second Person Rule (Evidence-Based)
Based on IBM Style Guide topic: "Verbs: Person"
Enhanced with evidence-based rule development and sophisticated confidence scoring.

This rule is fully compatible with Level 2 Enhanced Validation, Evidence-Based 
Rule Development, and Universal Confidence Threshold architecture. It provides
sophisticated 7-factor evidence scoring for second person violations.

Architecture compliance:
- confidence.md: Universal threshold (≥0.35), normalized confidence
- evidence_based_rule_development.md: Multi-factor evidence assessment  
- level_2_implementation.adoc: Enhanced validation integration
"""
from typing import List, Dict, Any, Set, Optional
from .language_and_grammar.base_language_rule import BaseLanguageRule

class SecondPersonRule(BaseLanguageRule):
    """
    Enforces the use of second person ("you") using evidence-based analysis.
    
    This rule implements sophisticated evidence scoring that considers:
    - Linguistic context and grammatical roles
    - Document structure and content type
    - Domain-specific appropriateness
    - User intent and communication style
    - Surgical zero false positive guards
    
    Architecture compliance:
    - Universal threshold (≥0.35) for all detections
    - Multi-factor evidence assessment with 7 evidence factors
    - Enhanced validation system integration
    - Surgical zero false positive guards
    """
    
    def __init__(self):
        super().__init__()
        # The exception framework is initialized in the BaseRule constructor.
        self._initialize_person_anchors()
        
        # Evidence-based configuration
        self.confidence_threshold = 0.45  # Above universal threshold (≥0.35)
        
        # Initialize evidence scoring components
        self._initialize_evidence_patterns()
    
    def _initialize_person_anchors(self):
        """Initialize morphological and semantic anchors for person analysis."""
        self.first_person_patterns = {
            'pronoun_indicators': {
                'subject_pronouns': {'i', 'we'},
                'object_pronouns': {'me', 'us'},
                'possessive_pronouns': {'my', 'our', 'mine', 'ours'},
            }
        }
        self.third_person_substitutes = {
            'user', 'users', 'administrator', 'admin', 'developer', 
            'operator', 'customer', 'person', 'individual'
        }
    
    def _initialize_evidence_patterns(self):
        """Initialize evidence-based patterns for sophisticated scoring."""
        
        # High-impact first person patterns (definitive violations)
        self.high_impact_first_person = {
            'strong_subject': {'i'},  # "I think" - direct first person
            'strong_possessive': {'my', 'our'},  # "my opinion" - ownership
            'strong_object': {'me', 'us'}  # "contact me" - direct object
        }
        
        # Context indicators that affect evidence scoring
        self.appropriate_contexts = {
            'quotations': True,  # First person allowed in quotes
            'examples': True,    # First person allowed in example scenarios
            'testimonials': True, # First person allowed in user testimonials
            'company_statements': True  # First person allowed for company voice
        }
        
        # Document types where third-person substitutes might be appropriate
        self.substitute_appropriate_contexts = {
            'api_documentation': ['developer', 'administrator'],
            'user_guides': ['user'],
            'admin_guides': ['administrator', 'admin'],
            'technical_specs': ['operator', 'developer']
        }
        
        # Linguistic indicators that reduce evidence
        self.evidence_reducers = {
            'compound_indicators': ['interface', 'guide', 'manual', 'documentation'],
            'role_definitions': ['role', 'position', 'type', 'kind', 'category'],
            'technical_terms': ['account', 'profile', 'session', 'authentication']
        }

    def _get_rule_type(self) -> str:
        return 'second_person'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for person violations using evidence-based rule development.
        
        Implements sophisticated evidence scoring with:
        - Multi-factor evidence assessment (7 factors)
        - Surgical zero false positive guards
        - Context-aware domain validation
        - Universal threshold compliance (≥0.35)
        """
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            # Handle both string and SpaCy Doc inputs for compatibility
            if hasattr(sentence, 'text'):
                sent_text = sentence.text
                sent_doc = sentence
            else:
                sent_text = sentence
                sent_doc = self._analyze_sentence_structure(sentence, nlp)
            
            if not sent_doc:
                continue
            
            # Apply zero false positive guards first
            if self._apply_zero_false_positive_guards(sent_text, context):
                continue
            
            # Analyze first person violations with evidence scoring
            first_person_errors = self._analyze_first_person_evidence_based(
                sent_doc, sent_text, i, text=text, context=context
            )
            errors.extend(first_person_errors)
            
            # Analyze third person substitutes with evidence scoring
            substitute_errors = self._analyze_third_person_substitutes_evidence_based(
                sent_doc, sent_text, i, text=text, context=context
            )
            errors.extend(substitute_errors)

        return errors
    
    def _apply_zero_false_positive_guards(self, sentence_text: str, context: Optional[Dict[str, Any]]) -> bool:
        """
        Apply surgical zero false positive guards for second person rule.
        
        Returns True if the detection should be skipped (no second person violation risk).
        """
        if not sentence_text:
            return True
        
        document_context = context or {}
        block_type = document_context.get('block_type', '').lower()
        content_type = document_context.get('content_type', '').lower()
        
        # Guard 1: Code blocks and technical identifiers
        if block_type in ['code_block', 'literal_block', 'inline_code']:
            return True
        
        # Guard 2: Direct quotations where first person is appropriate
        sentence_lower = sentence_text.lower().strip()
        if (sentence_text.startswith('"') or sentence_text.startswith("'")) or \
           ('"' in sentence_text and sentence_text.count('"') >= 2) or \
           ("'" in sentence_text and sentence_text.count("'") >= 2):
            return True
        
        # Guard 3: Example scenarios and user testimonials
        example_indicators = ['example:', 'for example', 'e.g.', 'scenario:', 'testimonial:']
        if any(indicator in sentence_lower for indicator in example_indicators):
            return True
        
        # Guard 4: Company/organizational statements where "we" is appropriate
        company_indicators = ['company', 'organization', 'team', 'corporation', 'business']
        if any(indicator in sentence_lower for indicator in company_indicators):
            # "We" might be appropriate when talking about the company
            return True
        
        # Guard 5: Legal disclaimers and formal statements
        legal_indicators = ['disclaimer:', 'notice:', 'copyright', 'trademark', 'legal']
        if any(indicator in sentence_lower for indicator in legal_indicators):
            return True
        
        return False
    
    def _analyze_first_person_evidence_based(self, doc, sentence_text: str, sentence_index: int, 
                                           text: str = None, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Detect first-person pronouns using evidence-based analysis.
        
        Implements multi-factor evidence assessment for sophisticated confidence scoring.
        """
        errors = []
        first_person_pronouns = (
            self.first_person_patterns['pronoun_indicators']['subject_pronouns'] |
            self.first_person_patterns['pronoun_indicators']['object_pronouns'] |
            self.first_person_patterns['pronoun_indicators']['possessive_pronouns']
        )

        for token in doc:
            if token.lemma_.lower() in first_person_pronouns:
                # Calculate evidence score for this first person usage
                evidence_score = self._calculate_first_person_evidence(token, doc, sentence_text, text, context)
                
                # Only create error if evidence suggests it's worth evaluating
                if evidence_score >= self.confidence_threshold:
                    error = self._create_error(
                        sentence=sentence_text,
                        sentence_index=sentence_index,
                        message=self._get_contextual_first_person_message(token, evidence_score),
                        suggestions=self._generate_first_person_suggestions(token, evidence_score, context),
                        severity='high' if evidence_score > 0.75 else 'medium',
                        text=text,  # Level 2 ✅
                        context=context,  # Level 2 ✅
                        evidence_score=evidence_score,  # Evidence-based scoring
                        flagged_text=token.text,
                        span=(token.idx, token.idx + len(token.text))
                    )
                    errors.append(error)
        
        return errors
    
    def _analyze_third_person_substitutes_evidence_based(self, doc, sentence_text: str, sentence_index: int, 
                                                       text: str = None, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Detect third-person substitutes using evidence-based analysis.
        
        Implements multi-factor evidence assessment for sophisticated confidence scoring.
        """
        errors = []
        
        # LINGUISTIC ANCHOR: Check if 'you' is already present in the sentence
        if any(token.lemma_.lower() == 'you' for token in doc):
            return errors  # The sentence correctly uses second person

        for token in doc:
            if token.lemma_.lower() in self.third_person_substitutes:
                # Check for multi-word exceptions first
                if token.i + 1 < len(doc):
                    next_token = doc[token.i + 1]
                    two_word_phrase = f"{token.text} {next_token.text}"
                    if self._is_excepted(two_word_phrase):
                        continue

                # Check for single-word exceptions
                if self._is_excepted(token.text):
                    continue

                # Calculate evidence score for this third person substitute
                evidence_score = self._calculate_third_person_evidence(token, doc, sentence_text, text, context)
                
                # Only create error if evidence suggests it's worth evaluating
                if evidence_score >= self.confidence_threshold:
                    error = self._create_error(
                        sentence=sentence_text,
                        sentence_index=sentence_index,
                        message=self._get_contextual_third_person_message(token, evidence_score),
                        suggestions=self._generate_third_person_suggestions(token, evidence_score, context),
                        severity='medium' if evidence_score > 0.65 else 'low',
                        text=text,  # Level 2 ✅
                        context=context,  # Level 2 ✅
                        evidence_score=evidence_score,  # Evidence-based scoring
                        flagged_text=token.text,
                        span=(token.idx, token.idx + len(token.text))
                    )
                    errors.append(error)
        
        return errors
    
    def _calculate_first_person_evidence(self, token, doc, sentence_text: str, text: str, context: Dict[str, Any]) -> float:
        """
        Enhanced Level 2 evidence calculation for first person violations.
        
        Implements evidence-based rule development with:
        - Multi-factor evidence assessment
        - Context-aware domain validation 
        - Universal threshold compliance (≥0.35)
        - Specific criteria for first person vs legitimate usage
        """
        # Evidence-based base confidence (Level 2 enhancement)
        evidence_score = 0.60  # Starting point for first person violations
        
        # === NARRATIVE/BLOG CONTENT CLUE (RELAX FORMAL RULES) ===
        # Detect narrative/blog writing style and significantly reduce evidence
        if self._is_narrative_or_blog_content(text, context):
            evidence_score -= 0.45  # Major reduction for narrative/blog content
            # In narrative/blog content, first-person pronouns ("we", "our", "I") are not only 
            # acceptable but correct and expected for storytelling and personal experience
        
        # EVIDENCE FACTOR 1: Pronoun Type Assessment (High Impact)
        pronoun_lemma = token.lemma_.lower()
        if pronoun_lemma in self.high_impact_first_person['strong_subject']:
            evidence_score += 0.25  # "I" - strong first person violation
        elif pronoun_lemma in self.high_impact_first_person['strong_possessive']:
            evidence_score += 0.20  # "my", "our" - ownership implications
        elif pronoun_lemma in self.high_impact_first_person['strong_object']:
            evidence_score += 0.15  # "me", "us" - direct object reference
        
        # EVIDENCE FACTOR 2: Grammatical Role Analysis (Context Dependency)
        grammatical_modifier = 0.0
        if token.dep_ == 'nsubj':  # Nominal subject
            grammatical_modifier += 0.15  # "I think" - direct subject role
        elif token.dep_ == 'poss':  # Possessive
            grammatical_modifier += 0.10  # "my opinion" - ownership
        elif token.dep_ in ['dobj', 'iobj']:  # Object
            grammatical_modifier += 0.08  # "contact me" - object role
        
        # EVIDENCE FACTOR 3: Document Context Assessment (Domain Knowledge)
        domain_modifier = 0.0
        if context:
            content_type = context.get('content_type', '')
            if content_type == 'user_guide':
                domain_modifier += 0.12  # User guides should use "you"
            elif content_type == 'api_documentation':
                domain_modifier += 0.08  # API docs should be direct
            elif content_type == 'marketing':
                domain_modifier -= 0.05  # Marketing might use "we"
            elif content_type == 'legal':
                domain_modifier -= 0.10  # Legal docs might use formal language
        
        # EVIDENCE FACTOR 4: Sentence Position Analysis (Emphasis Assessment)
        position_modifier = 0.0
        if token.i == 0:  # Sentence start
            position_modifier += 0.10  # "I believe..." - emphatic position
        elif token.i == len(doc) - 2:  # Near sentence end (before punctuation)
            position_modifier += 0.05  # "...contact me." - concluding position
        
        # EVIDENCE FACTOR 5: Communication Intent Analysis (Purpose Assessment)
        intent_modifier = 0.0
        verb_nearby = self._find_nearby_verb(token, doc)
        if verb_nearby:
            verb_lemma = verb_nearby.lemma_.lower()
            communication_verbs = {'think', 'believe', 'recommend', 'suggest', 'prefer'}
            instruction_verbs = {'contact', 'email', 'call', 'reach'}
            
            if verb_lemma in communication_verbs:
                intent_modifier += 0.12  # "I think" - opinion expression
            elif verb_lemma in instruction_verbs:
                intent_modifier += 0.15  # "contact me" - direct instruction
        
        # EVIDENCE FACTOR 6: Contextual Appropriateness Analysis (Situational Validity)
        appropriateness_modifier = 0.0
        if self._is_in_appropriate_context(sentence_text, context):
            appropriateness_modifier -= 0.20  # Reduce evidence for appropriate contexts
        elif self._is_in_company_context(sentence_text):
            appropriateness_modifier -= 0.15  # Company statements might use "we"
        
        # EVIDENCE FACTOR 7: Formality Level Analysis (Style Consistency)
        formality_modifier = 0.0
        if self._has_formal_indicators(doc):
            formality_modifier += 0.08  # Formal docs should avoid first person
        elif self._has_conversational_indicators(doc):
            formality_modifier -= 0.05  # Conversational style might allow some first person
        
        # EVIDENCE AGGREGATION (Level 2 Multi-Factor Assessment)
        final_evidence = (evidence_score + 
                         grammatical_modifier + 
                         domain_modifier + 
                         position_modifier + 
                         intent_modifier + 
                         appropriateness_modifier + 
                         formality_modifier)
        
        # UNIVERSAL THRESHOLD COMPLIANCE (≥0.35 minimum)
        # Cap at 0.95 to leave room for uncertainty
        return min(0.95, max(0.35, final_evidence))
    
    def _calculate_third_person_evidence(self, token, doc, sentence_text: str, text: str, context: Dict[str, Any]) -> float:
        """
        Enhanced Level 2 evidence calculation for third person substitute violations.
        
        Implements evidence-based rule development with specific criteria for substitutes vs legitimate usage.
        """
        # Evidence-based base confidence (Level 2 enhancement)
        substitute_text = token.lemma_.lower()
        
        # Different base scores based on substitute type
        if substitute_text in ['user', 'users']:
            evidence_score = 0.55  # Common substitutes, moderate evidence
        elif substitute_text in ['administrator', 'admin']:
            evidence_score = 0.50  # Role-specific, might be appropriate
        elif substitute_text in ['developer', 'operator']:
            evidence_score = 0.45  # Technical roles, often appropriate
        else:
            evidence_score = 0.50  # Generic substitutes
        
        # EVIDENCE FACTOR 1: Document Type Appropriateness (Domain Knowledge)
        domain_modifier = 0.0
        if context:
            content_type = context.get('content_type', '')
            if content_type in self.substitute_appropriate_contexts:
                if substitute_text in self.substitute_appropriate_contexts[content_type]:
                    domain_modifier -= 0.15  # Appropriate for this document type
                else:
                    domain_modifier += 0.10  # Not appropriate for this document type
        
        # EVIDENCE FACTOR 2: Compound Noun Analysis (Linguistic Context)
        compound_modifier = 0.0
        if self._is_part_of_compound_noun(token):
            compound_modifier -= 0.25  # "user interface" - legitimate compound
        elif self._has_compound_indicators_nearby(token, doc):
            compound_modifier -= 0.15  # Near compound indicators
        
        # EVIDENCE FACTOR 3: Role Definition Context (Semantic Analysis)
        role_modifier = 0.0
        if self._is_in_role_definition_context(token, doc):
            role_modifier -= 0.20  # "user is a person who..." - defining role
        elif self._has_role_indicators_nearby(token, doc):
            role_modifier -= 0.10  # Near role definition language
        
        # EVIDENCE FACTOR 4: Instructional Context Analysis (Communication Purpose)
        instruction_modifier = 0.0
        if self._is_in_instructional_context(doc):
            instruction_modifier += 0.15  # Instructions should use "you"
        elif self._has_imperative_verbs_nearby(token, doc):
            instruction_modifier += 0.10  # Near imperative verbs
        
        # EVIDENCE FACTOR 5: Technical Specificity (Precision Assessment)
        technical_modifier = 0.0
        if self._has_technical_qualifiers(token, doc):
            technical_modifier -= 0.10  # "database administrator" - specific role
        elif self._is_generic_reference(token, doc):
            technical_modifier += 0.08  # Generic reference, should use "you"
        
        # EVIDENCE FACTOR 6: Frequency and Consistency (Document-wide Analysis)
        consistency_modifier = 0.0
        if text and self._has_consistent_second_person_usage(text):
            consistency_modifier += 0.12  # Document uses "you" elsewhere
        elif text and self._has_mixed_person_usage(text):
            consistency_modifier += 0.08  # Inconsistent usage
        
        # EVIDENCE FACTOR 7: Audience Directness (Communication Effectiveness)
        directness_modifier = 0.0
        if self._requires_direct_address(doc, context):
            directness_modifier += 0.10  # Context requires direct address
        
        # EVIDENCE AGGREGATION (Level 2 Multi-Factor Assessment)
        final_evidence = (evidence_score + 
                         domain_modifier + 
                         compound_modifier + 
                         role_modifier + 
                         instruction_modifier + 
                         technical_modifier + 
                         consistency_modifier + 
                         directness_modifier)
        
        # UNIVERSAL THRESHOLD COMPLIANCE (≥0.35 minimum)
        # Cap at 0.95 to leave room for uncertainty
        return min(0.95, max(0.35, final_evidence))

    def _is_narrative_or_blog_content(self, text: str, context: Dict[str, Any]) -> bool:
        """
        Detect if content is narrative/blog style using enhanced ContextAnalyzer.
        
        Looks for blog/narrative indicators like:
        - Frequent first-person pronouns ("we", "our", "I")  
        - Contractions ("we're", "it's", "wasn't")
        - Rhetorical questions
        - Informal sentence structure
        - Blog-specific phrases ("Why we switched", "Our journey")
        
        Args:
            text: The document text to analyze
            context: Document context information
            
        Returns:
            bool: True if content appears to be narrative/blog style
        """
        if not text:
            return False
            
        # Import ContextAnalyzer to leverage enhanced narrative detection
        try:
            from validation.confidence.context_analyzer import ContextAnalyzer
            analyzer = ContextAnalyzer()
            
            # Use enhanced content type detection  
            content_result = analyzer.detect_content_type(text, context)
            
            # Check if identified as narrative with reasonable confidence
            if (content_result.content_type.value == 'narrative' and 
                content_result.confidence > 0.4):
                return True
            
            # Additional check for blog-specific patterns even if not classified as narrative
            # Look for strong blog indicators in the text
            text_lower = text.lower()
            blog_strong_indicators = [
                'why we', 'how we', 'what we', 'when we', 'we switched', 
                'we decided', 'our journey', 'our experience', 'our story',
                'we learned', 'we discovered', 'we realized'
            ]
            
            strong_indicator_count = sum(1 for indicator in blog_strong_indicators 
                                       if indicator in text_lower)
            
            if strong_indicator_count >= 2:  # Multiple strong blog indicators
                return True
                
            # Check for high first-person pronoun density (blog characteristic)
            words = text_lower.split()
            if len(words) > 20:  # Only for substantial text
                first_person_count = sum(1 for word in words 
                                       if word in ['i', 'we', 'my', 'our', 'me', 'us'])
                first_person_ratio = first_person_count / len(words)
                
                # More than 3% first-person pronouns suggests blog/narrative
                if first_person_ratio > 0.03:
                    return True
                    
        except ImportError:
            # Fallback to simple pattern matching if ContextAnalyzer unavailable
            text_lower = text.lower()
            
            # Simple blog indicators
            simple_indicators = ['why we', 'we switched', 'our journey', 'we decided']
            if any(indicator in text_lower for indicator in simple_indicators):
                return True
        
        return False

    def _analyze_first_person(self, doc, sentence: str, sentence_index: int, text: str = None, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Detect first-person pronouns using morphological analysis."""
        errors = []
        first_person_pronouns = self.first_person_patterns['pronoun_indicators']['subject_pronouns'] | \
                                self.first_person_patterns['pronoun_indicators']['object_pronouns'] | \
                                self.first_person_patterns['pronoun_indicators']['possessive_pronouns']

        for token in doc:
            if token.lemma_.lower() in first_person_pronouns:
                # Add contextual checks here if needed (e.g., quotations, company names)
                if self._is_in_quotation(token) or self._is_part_of_proper_noun(token):
                    continue
                
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message=f"Avoid first-person pronoun '{token.text}'; use second person ('you') instead.",
                    suggestions=["Rewrite using 'you' to address the user directly."],
                    severity='high',
                    text=text,  # Enhanced: Pass full text for better confidence analysis
                    context=context,  # Enhanced: Pass context for domain-specific validation
                    span=(token.idx, token.idx + len(token.text)),
                    flagged_text=token.text
                ))
        return errors

    def _analyze_third_person_substitutes(self, doc, sentence: str, sentence_index: int, text: str = None, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Detect third-person substitutes using morphological analysis, now with exception checking.
        """
        errors = []
        
        # LINGUISTIC ANCHOR: Check if 'you' is already present in the sentence. If so, any third-person
        # substitute is likely defining the role of 'you' and should not be flagged.
        if any(token.lemma_.lower() == 'you' for token in doc):
            return errors # The sentence correctly uses second person.

        for token in doc:
            # Check if the token is a potential substitute (e.g., "user", "administrator")
            if token.lemma_.lower() in self.third_person_substitutes:
                
                # *** NEW EXCEPTION HANDLING LOGIC ***
                # Check for multi-word exceptions first (e.g., "user interface")
                if token.i + 1 < len(doc):
                    next_token = doc[token.i + 1]
                    two_word_phrase = f"{token.text} {next_token.text}"
                    if self._is_excepted(two_word_phrase):
                        # This is an allowed phrase like "user interface", so we skip the next token as well
                        # to avoid it being processed individually.
                        # We can simply continue here, as the loop will advance past the current token.
                        continue

                # Check for single-word exceptions (e.g., if you wanted to allow "admin" in some contexts)
                if self._is_excepted(token.text):
                    continue
                # *** END OF NEW LOGIC ***

                # If not an exception, proceed with the original logic
                if self._is_part_of_compound_noun(token):
                    continue
                
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message=f"Consider using 'you' instead of '{token.text}' for direct user engagement.",
                    suggestions=[f"Replace '{token.text}' with 'you' or rewrite the sentence to address the user directly."],
                    severity='medium',
                    text=text,  # Enhanced: Pass full text for better confidence analysis
                    context=context,  # Enhanced: Pass context for domain-specific validation
                    span=(token.idx, token.idx + len(token.text)),
                    flagged_text=token.text
                ))
        
        return errors

    # Helper methods (can be simplified or kept as is)
    def _is_part_of_compound_noun(self, token) -> bool:
        """Check if token is part of a compound noun using dependency analysis."""
        # This check is still useful for generic compounds not in the exception list.
        if token.dep_ == 'compound':
            return True
        # Check for constructions like "the user's guide"
        if token.head.dep_ == 'poss' and token.head.head.pos_ == 'NOUN':
            return True
        return False

    def _is_in_quotation(self, token) -> bool:
        # Simple check, can be made more robust if needed
        return token.sent.text.startswith('"') and token.sent.text.endswith('"')

    def _is_part_of_proper_noun(self, token) -> bool:
        # Check if the token or its head is a proper noun, indicating a name
        return token.pos_ == 'PROPN' or token.head.pos_ == 'PROPN'

    def _analyze_sentence_structure(self, sentence: str, nlp):
        """Helper to get a SpaCy doc from a sentence string."""
        if not sentence or not sentence.strip():
            return None
        try:
            return nlp(sentence)
        except Exception:
            return None
    
    # Evidence calculation helper methods
    def _find_nearby_verb(self, token, doc):
        """Find verb near the token for intent analysis."""
        # Check if token itself has a verb head
        if token.head.pos_ == 'VERB':
            return token.head
        
        # Check children for verbs
        for child in token.children:
            if child.pos_ == 'VERB':
                return child
        
        # Check nearby tokens (within 3 positions)
        start_idx = max(0, token.i - 3)
        end_idx = min(len(doc), token.i + 4)
        
        for i in range(start_idx, end_idx):
            if i != token.i and doc[i].pos_ == 'VERB':
                return doc[i]
        
        return None
    
    def _is_in_appropriate_context(self, sentence_text: str, context: Dict[str, Any]) -> bool:
        """Check if first person is appropriate in this context."""
        sentence_lower = sentence_text.lower()
        
        # Direct quotations
        if (sentence_text.startswith('"') and sentence_text.endswith('"')):
            return True
        
        # Example scenarios
        example_indicators = ['example:', 'for example', 'e.g.', 'scenario:']
        if any(indicator in sentence_lower for indicator in example_indicators):
            return True
        
        # Testimonials and user feedback
        testimonial_indicators = ['testimonial:', 'feedback:', 'review:', 'user says']
        if any(indicator in sentence_lower for indicator in testimonial_indicators):
            return True
        
        return False
    
    def _is_in_company_context(self, sentence_text: str) -> bool:
        """Check if sentence is about company/organization."""
        sentence_lower = sentence_text.lower()
        company_indicators = ['company', 'organization', 'team', 'corporation', 'business', 'enterprise']
        return any(indicator in sentence_lower for indicator in company_indicators)
    
    def _has_formal_indicators(self, doc) -> bool:
        """Check for formal language indicators."""
        formal_words = {'shall', 'must', 'therefore', 'furthermore', 'consequently', 'accordingly'}
        return any(token.lemma_.lower() in formal_words for token in doc)
    
    def _has_conversational_indicators(self, doc) -> bool:
        """Check for conversational language indicators."""
        conversational_words = {'hey', 'hi', 'well', 'okay', 'sure', 'yeah', 'cool'}
        return any(token.lemma_.lower() in conversational_words for token in doc)
    
    def _has_compound_indicators_nearby(self, token, doc) -> bool:
        """Check for compound noun indicators near the token."""
        nearby_range = 2
        start_idx = max(0, token.i - nearby_range)
        end_idx = min(len(doc), token.i + nearby_range + 1)
        
        for i in range(start_idx, end_idx):
            if i != token.i and doc[i].lemma_.lower() in self.evidence_reducers['compound_indicators']:
                return True
        
        return False
    
    def _is_in_role_definition_context(self, token, doc) -> bool:
        """Check if token is in a role definition context."""
        # Look for patterns like "user is a person who..."
        if token.i + 2 < len(doc):
            next_two = [doc[token.i + 1].lemma_.lower(), doc[token.i + 2].lemma_.lower()]
            if next_two == ['be', 'a'] or next_two == ['be', 'an']:
                return True
        
        # Look for role definition words nearby
        return self._has_role_indicators_nearby(token, doc)
    
    def _has_role_indicators_nearby(self, token, doc) -> bool:
        """Check for role definition indicators near the token."""
        nearby_range = 3
        start_idx = max(0, token.i - nearby_range)
        end_idx = min(len(doc), token.i + nearby_range + 1)
        
        for i in range(start_idx, end_idx):
            if i != token.i and doc[i].lemma_.lower() in self.evidence_reducers['role_definitions']:
                return True
        
        return False
    
    def _is_in_instructional_context(self, doc) -> bool:
        """Check if sentence is instructional."""
        instruction_verbs = {'click', 'select', 'choose', 'configure', 'set', 'install', 'run', 'execute'}
        return any(token.lemma_.lower() in instruction_verbs for token in doc)
    
    def _has_imperative_verbs_nearby(self, token, doc) -> bool:
        """Check for imperative verbs near the token."""
        imperative_verbs = {'click', 'select', 'configure', 'install', 'run', 'set', 'choose'}
        nearby_range = 3
        start_idx = max(0, token.i - nearby_range)
        end_idx = min(len(doc), token.i + nearby_range + 1)
        
        for i in range(start_idx, end_idx):
            if i != token.i and doc[i].lemma_.lower() in imperative_verbs:
                return True
        
        return False
    
    def _has_technical_qualifiers(self, token, doc) -> bool:
        """Check for technical qualifiers that make the reference specific."""
        qualifiers = ['database', 'system', 'network', 'senior', 'junior', 'lead', 'principal']
        
        # Check previous token for qualifiers
        if token.i > 0 and doc[token.i - 1].lemma_.lower() in qualifiers:
            return True
        
        # Check next token for qualifiers
        if token.i + 1 < len(doc) and doc[token.i + 1].lemma_.lower() in qualifiers:
            return True
        
        return False
    
    def _is_generic_reference(self, token, doc) -> bool:
        """Check if token is a generic reference that should use 'you'."""
        # Simple check - if it's not qualified and not in a compound, it's likely generic
        return not (self._has_technical_qualifiers(token, doc) or 
                   self._is_part_of_compound_noun(token) or
                   self._has_compound_indicators_nearby(token, doc))
    
    def _has_consistent_second_person_usage(self, text: str) -> bool:
        """Check if document consistently uses second person."""
        text_lower = text.lower()
        you_count = text_lower.count(' you ') + text_lower.count('you ') + text_lower.count(' you')
        return you_count >= 3  # Document uses "you" multiple times
    
    def _has_mixed_person_usage(self, text: str) -> bool:
        """Check if document has mixed person usage."""
        text_lower = text.lower()
        first_person_count = (text_lower.count(' i ') + text_lower.count(' we ') + 
                             text_lower.count(' my ') + text_lower.count(' our '))
        second_person_count = text_lower.count(' you ')
        third_person_count = (text_lower.count(' user ') + text_lower.count(' users ') +
                             text_lower.count(' admin ') + text_lower.count(' developer '))
        
        # Mixed if multiple person types are used
        person_types_used = sum([first_person_count > 0, second_person_count > 0, third_person_count > 0])
        return person_types_used >= 2
    
    def _requires_direct_address(self, doc, context: Dict[str, Any]) -> bool:
        """Check if context requires direct address to user."""
        if context:
            content_type = context.get('content_type', '')
            if content_type in ['user_guide', 'tutorial', 'instructions', 'how_to']:
                return True
        
        # Check for instructional language
        instruction_patterns = {'how to', 'follow these steps', 'to do this', 'perform the following'}
        doc_text = doc.text.lower()
        return any(pattern in doc_text for pattern in instruction_patterns)
    
    # Message and suggestion generation methods
    def _get_contextual_first_person_message(self, token, evidence_score: float) -> str:
        """Generate contextual message for first person violations."""
        pronoun = token.text
        
        if evidence_score > 0.85:
            return f"Avoid first-person pronoun '{pronoun}'; use second person ('you') for direct user engagement."
        elif evidence_score > 0.65:
            return f"Consider replacing '{pronoun}' with 'you' to directly address the user."
        else:
            return f"The pronoun '{pronoun}' could be replaced with 'you' for more direct communication."
    
    def _generate_first_person_suggestions(self, token, evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate evidence-aware suggestions for first person violations."""
        suggestions = []
        pronoun = token.text.lower()
        
        if evidence_score > 0.80:
            # High confidence - direct suggestions
            if pronoun in ['i', 'me']:
                suggestions.append("Replace with 'you' to address the user directly.")
                suggestions.append("Rewrite to use imperative mood: 'Click...' instead of 'I click...'")
            elif pronoun in ['we', 'us']:
                suggestions.append("Use 'you' to focus on the user's actions.")
                suggestions.append("Consider 'the system' if referring to software behavior.")
            elif pronoun in ['my', 'our']:
                suggestions.append("Replace with 'your' to address the user directly.")
                suggestions.append("Use 'the' for generic references.")
        
        elif evidence_score > 0.60:
            # Medium confidence - balanced suggestions
            suggestions.append(f"Consider replacing '{token.text}' with 'you' for better user engagement.")
            suggestions.append("Rewrite to address the user directly.")
            
        else:
            # Lower confidence - gentle suggestions
            suggestions.append(f"'{token.text}' could be replaced with 'you' for more direct communication.")
            suggestions.append("Consider if direct address would improve clarity.")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _get_contextual_third_person_message(self, token, evidence_score: float) -> str:
        """Generate contextual message for third person substitute violations."""
        substitute = token.text
        
        if evidence_score > 0.80:
            return f"Replace '{substitute}' with 'you' for direct user engagement."
        elif evidence_score > 0.60:
            return f"Consider using 'you' instead of '{substitute}' to address the user directly."
        else:
            return f"'{substitute}' could be replaced with 'you' for more personal communication."
    
    def _generate_third_person_suggestions(self, token, evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate evidence-aware suggestions for third person substitute violations."""
        suggestions = []
        substitute = token.text
        
        if evidence_score > 0.75:
            # High confidence - direct suggestions
            suggestions.append(f"Replace '{substitute}' with 'you' for direct user engagement.")
            suggestions.append("Use imperative mood to give direct instructions.")
            suggestions.append("Address the user personally rather than referring to them in third person.")
            
        elif evidence_score > 0.55:
            # Medium confidence - balanced suggestions
            suggestions.append(f"Consider replacing '{substitute}' with 'you' for better engagement.")
            suggestions.append("Direct address creates more personal communication.")
            
        else:
            # Lower confidence - gentle suggestions
            suggestions.append(f"'{substitute}' could be replaced with 'you' for more direct communication.")
            suggestions.append("Consider if direct address would improve user experience.")
        
        return suggestions[:3]  # Limit to 3 suggestions
