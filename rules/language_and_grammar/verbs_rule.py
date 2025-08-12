"""
Verbs Rule (Refactored to use Shared Passive Voice Analyzer)
Based on IBM Style Guide topics: "Verbs: Tense", "Verbs: Voice"

This refactored version uses the centralized PassiveVoiceAnalyzer to eliminate
code duplication while maintaining sophisticated context-aware suggestions.
"""
from typing import List, Dict, Any, Optional

try:
    from .base_language_rule import BaseLanguageRule
except ImportError:
    # Fallback for direct execution
    try:
        from base_language_rule import BaseLanguageRule
    except ImportError:
        # Define a minimal BaseLanguageRule for testing
        class BaseLanguageRule:
            def __init__(self):
                pass
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

try:
    from .passive_voice_analyzer import PassiveVoiceAnalyzer, ContextType, PassiveConstruction
except ImportError:
    # Fallback for direct execution
    try:
        from passive_voice_analyzer import PassiveVoiceAnalyzer, ContextType, PassiveConstruction
    except ImportError:
        PassiveVoiceAnalyzer = None
        ContextType = None
        PassiveConstruction = None

try:
    from spacy.tokens import Doc, Token
except ImportError:
    Doc = None
    Token = None

class VerbsRule(BaseLanguageRule):
    """
    Checks for verb-related style issues using centralized passive voice analysis.
    Provides context-aware suggestions for descriptive vs instructional text.
    """
    
    def __init__(self):
        super().__init__()
        if PassiveVoiceAnalyzer:
            self.passive_analyzer = PassiveVoiceAnalyzer()
        else:
            self.passive_analyzer = None
    
    def _get_rule_type(self) -> str:
        return 'verbs'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp or not self.passive_analyzer:
            return errors

        for i, sent_text in enumerate(sentences):
            if not sent_text.strip():
                continue
            
            doc = nlp(sent_text)
            
            # --- PASSIVE VOICE ANALYSIS (evidence-based using shared analyzer) ---
            passive_constructions = self.passive_analyzer.find_passive_constructions(doc)
            
            for construction in passive_constructions:
                # Calculate evidence score using enhanced analyzer with full context
                evidence_score = self.passive_analyzer.calculate_passive_voice_evidence(
                    construction, doc, text, context
                )
                
                # Only create error if evidence suggests it's worth flagging
                if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                    # Generate context-aware suggestions
                    suggestions = self._generate_context_aware_suggestions(construction, doc, sent_text)
                    message = self._get_contextual_passive_voice_message(construction, evidence_score)
                    
                    errors.append(self._create_error(
                        sentence=sent_text,
                        sentence_index=i,
                        message=message,
                        suggestions=suggestions,
                        severity='medium',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,  # Your nuanced assessment
                        span=(construction.span_start, construction.span_end),
                        flagged_text=construction.flagged_text
                    ))

            # --- FUTURE TENSE CHECK ('will') ---
            for token in doc:
                if token.lemma_.lower() == "will" and token.tag_ == "MD":
                    head_verb = token.head
                    if head_verb.pos_ == "VERB":
                        evidence_score = self._calculate_future_tense_evidence(
                            token, head_verb, doc, sent_text, text, context or {}
                        )
                        if evidence_score > 0.1:
                            flagged_text = f"{token.text} {head_verb.text}"
                            span_start = token.idx
                            span_end = head_verb.idx + len(head_verb.text)
                            errors.append(self._create_error(
                                sentence=sent_text,
                                sentence_index=i,
                                message=self._get_contextual_future_tense_message(flagged_text, evidence_score, context or {}),
                                suggestions=self._generate_smart_future_tense_suggestions(head_verb, evidence_score, context or {}),
                                severity='low' if evidence_score < 0.6 else 'medium',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=(span_start, span_end),
                                flagged_text=flagged_text
                            ))

            # --- PAST TENSE CHECK (with temporal context awareness) ---
            root_verb = self._find_root_token(doc)
            if (root_verb and root_verb.pos_ == 'VERB' and 'Tense=Past' in str(root_verb.morph)
                and not self._is_passive_construction(root_verb, doc)):

                evidence_score_past = self._calculate_past_tense_evidence(
                    root_verb, doc, sent_text, text, context or {}
                )

                if evidence_score_past > 0.1:
                    flagged_text = root_verb.text
                    span_start = root_verb.idx
                    span_end = span_start + len(flagged_text)
                    errors.append(self._create_error(
                        sentence=sent_text,
                        sentence_index=i,
                        message=self._get_contextual_past_tense_message(flagged_text, evidence_score_past, context or {}),
                        suggestions=self._generate_smart_past_tense_suggestions(root_verb, evidence_score_past, context or {}),
                        severity='low',
                        text=text,
                        context=context,
                        evidence_score=evidence_score_past,
                        span=(span_start, span_end),
                        flagged_text=flagged_text
                    ))
        
        return errors

    def _generate_context_aware_suggestions(self, construction, doc: Doc, sentence: str) -> List[str]:
        """Generate intelligent suggestions based on context classification."""
        suggestions = []
        
        try:
            # Use the analyzer's context classification
            context_type = construction.context_type
            base_verb = construction.main_verb.lemma_
            passive_subject = construction.passive_subject
            
            # Find agent in by-phrase
            agent = self._find_agent_in_by_phrase(doc, construction.main_verb)
            
            # Check for negative context
            is_negative = self._has_negative_context(doc, construction.main_verb)
            
            if is_negative:
                # Handle negative constructions
                antonym = self._get_positive_alternative(base_verb, doc)
                if antonym:
                    if context_type == ContextType.DESCRIPTIVE:
                        suggestions.append(f"Rewrite positively: 'The system {antonym}s {passive_subject.text.lower()}' (use descriptive active voice)")
                    else:
                        suggestions.append(f"Rewrite positively: 'You must {antonym} {passive_subject.text.lower()}' (use positive action)")
                else:
                    suggestions.append(f"Rewrite as requirement: 'You must ensure {passive_subject.text.lower()} is {self._get_past_participle(base_verb)}' (specify the requirement)")
            
            elif context_type == ContextType.DESCRIPTIVE:
                # Generate descriptive suggestions
                self._add_descriptive_suggestions(suggestions, base_verb, passive_subject, agent, doc)
            
            elif context_type == ContextType.INSTRUCTIONAL:
                # Generate instructional suggestions
                self._add_instructional_suggestions(suggestions, base_verb, passive_subject, agent)
            
            else:
                # Uncertain context - provide both options
                suggestions.append(f"For descriptions: 'The system {self._conjugate_verb(base_verb, 'system')} {passive_subject.text.lower()}'")
                suggestions.append(f"For instructions: '{base_verb.capitalize()} the {passive_subject.text.lower()}'")
            
            # Add agent-based suggestion if available
            if agent and len(suggestions) < 2:
                verb_form = self._conjugate_verb(base_verb, agent)
                suggestions.append(f"Make the agent active: '{agent.capitalize()} {verb_form} {passive_subject.text.lower()}'")
            
            # Fallback
            if not suggestions:
                suggestions.append("Rewrite in active voice by identifying who or what performs the action")
                
        except Exception as e:
            suggestions = ["Rewrite in active voice by identifying who or what performs the action"]
        
        return suggestions[:3]

    def _add_descriptive_suggestions(self, suggestions: List[str], base_verb: str, 
                                   passive_subject: Token, agent: str, doc: Doc) -> None:
        """Add suggestions appropriate for descriptive context."""
        
        # Get appropriate actors for descriptive active voice
        descriptive_actors = self._get_descriptive_actors(base_verb, passive_subject, doc)
        
        for actor in descriptive_actors:
            # Check for same-root awkwardness and use alternative verb if needed
            final_verb = self._get_stylistically_appropriate_verb(base_verb, actor)
            verb_form = self._conjugate_verb(final_verb, actor)
            
            if passive_subject and passive_subject.text.lower() in ['it', 'this', 'that']:
                suggestions.append(f"Use descriptive active voice: '{actor.capitalize()} {verb_form} {passive_subject.text.lower()}'")
            else:
                suggestions.append(f"Use descriptive active voice: '{actor.capitalize()} {verb_form} the {passive_subject.text.lower()}'")
            
            if len(suggestions) >= 2:
                break
        
        # Fallback descriptive suggestion
        if not suggestions:
            if base_verb in ['document', 'describe', 'specify', 'define']:
                # Avoid same-root awkwardness in fallback too
                fallback_verb = self._get_stylistically_appropriate_verb(base_verb, 'the documentation')
                suggestions.append(f"Use descriptive active voice: 'The documentation {self._conjugate_verb(fallback_verb, 'documentation')} {passive_subject.text.lower()}'")
            else:
                suggestions.append(f"Use descriptive active voice: 'The system {self._conjugate_verb(base_verb, 'system')} {passive_subject.text.lower()}'")

    def _get_stylistically_appropriate_verb(self, base_verb: str, actor: str) -> str:
        """
        Return a stylistically appropriate verb, avoiding same-root awkwardness.
        
        E.g., avoid "documentation documents" -> use "documentation describes"
        """
        # Extract the root noun from the actor
        actor_root = actor.replace('the ', '').replace('a ', '').replace('an ', '')
        
        # Check if actor root and verb lemma are too similar (same-root awkwardness)
        if self._is_same_root_awkward(actor_root, base_verb):
            # Use alternative verbs for common cases (avoid multi-word verbs for now)
            verb_alternatives = {
                'document': 'describe',
                'describe': 'detail', 
                'specify': 'define',
                'define': 'outline',
                'configure': 'establish',
                'manage': 'handle',
                'process': 'handle',
                'support': 'enable'
            }
            
            alternative = verb_alternatives.get(base_verb)
            if alternative:
                return alternative
        
        return base_verb
    
    def _is_same_root_awkward(self, actor_root: str, verb: str) -> bool:
        """Check if using actor + verb creates awkward same-root construction."""
        # Handle obvious cases
        same_root_pairs = {
            ('documentation', 'document'),
            ('configuration', 'configure'), 
            ('specification', 'specify'),
            ('management', 'manage'),
            ('processing', 'process'),
            ('support', 'support')
        }
        
        return (actor_root, verb) in same_root_pairs or actor_root.startswith(verb) or verb.startswith(actor_root)

    def _add_instructional_suggestions(self, suggestions: List[str], base_verb: str, 
                                     passive_subject: Token, agent: str) -> None:
        """Add suggestions appropriate for instructional context."""
        
        # Use imperative mood for instructions
        if passive_subject and passive_subject.text.lower() in ['it', 'this', 'that']:
            suggestions.append(f"Use imperative: '{base_verb.capitalize()} {passive_subject.text.lower()}' (make the user the actor)")
        else:
            suggestions.append(f"Use imperative: '{base_verb.capitalize()} the {passive_subject.text.lower()}' (make the user the actor)")
        
        # Suggest specific actors for technical instructions
        if base_verb in ['configure', 'install', 'setup', 'deploy', 'enable', 'disable']:
            suggestions.append(f"Specify the actor: 'The administrator {self._conjugate_verb(base_verb, 'administrator')} the {passive_subject.text.lower()}'")
        elif base_verb in ['test', 'verify', 'check', 'validate']:
            suggestions.append(f"Specify the actor: 'You {base_verb} the {passive_subject.text.lower()}'")

    def _get_descriptive_actors(self, base_verb: str, passive_subject: Token, doc: Doc) -> List[str]:
        """Get appropriate actors for descriptive active voice."""
        
        # Use the analyzer's verb categorization
        verb_actors = {
            'document': ['the documentation', 'the manual', 'the guide'],
            'describe': ['the documentation', 'the specification', 'the manual'],
            'specify': ['the configuration', 'the settings', 'the parameters'],
            'define': ['the system', 'the configuration', 'the specification'],
            'configure': ['the system', 'the application', 'the software'],
            'provide': ['the system', 'the platform', 'the service'],
            'support': ['the system', 'the platform', 'the framework'],
            'manage': ['the system', 'the application', 'the service']
        }
        
        actors = verb_actors.get(base_verb, ['the system', 'the application'])
        
        # Context-based refinement using spaCy analysis
        context_words = [token.lemma_.lower() for token in doc]
        
        if any(word in context_words for word in ['database', 'data', 'record']):
            if base_verb in ['store', 'save', 'retrieve']:
                actors = ['the database', 'the data store'] + actors
        
        return actors[:2]

    # Utility methods (simplified from original)
    def _find_root_token(self, doc: Doc) -> Token:
        """Find the root token of the sentence."""
        for token in doc:
            if token.dep_ == "ROOT":
                return token
        return None

    def _is_passive_construction(self, verb_token: Token, doc: Doc) -> bool:
        """Check if a verb token is part of a passive voice construction."""
        if not verb_token:
            return False
        
        # Use analyzer for consistency
        constructions = self.passive_analyzer.find_passive_constructions(doc)
        return any(c.main_verb == verb_token for c in constructions)

    def _find_agent_in_by_phrase(self, doc: Doc, main_verb: Token) -> str:
        """Find the agent in a 'by' phrase."""
        for token in doc:
            if token.lemma_ == 'by' and token.head == main_verb:
                for child in token.children:
                    if child.dep_ == 'pobj':
                        return child.text
        return None

    def _has_negative_context(self, doc: Doc, main_verb: Token) -> bool:
        """Check if the passive construction is in a negative context."""
        for token in doc:
            if token.dep_ == 'neg' or token.lemma_ in ['not', 'never', 'cannot']:
                if token.head == main_verb or token.head.head == main_verb:
                    return True
        
        sentence_text = doc.text.lower()
        negative_patterns = ['can not be', 'cannot be', 'should not be', 'must not be']
        return any(pattern in sentence_text for pattern in negative_patterns)

    def _get_positive_alternative(self, verb_lemma: str, doc: Doc) -> str:
        """Get a positive alternative for a negated verb."""
        verb_alternatives = {
            'overlook': 'address', 'ignore': 'consider', 'miss': 'include',
            'skip': 'complete', 'avoid': 'ensure', 'neglect': 'maintain'
        }
        return verb_alternatives.get(verb_lemma)

    def _get_past_participle(self, verb_lemma: str) -> str:
        """Get the past participle form of a verb."""
        irregular_participles = {
            'configure': 'configured', 'install': 'installed', 'deploy': 'deployed',
            'address': 'addressed', 'consider': 'considered', 'include': 'included'
        }
        
        if verb_lemma in irregular_participles:
            return irregular_participles[verb_lemma]
        
        # Regular formation
        if verb_lemma.endswith('e'):
            return verb_lemma + 'd'
        else:
            return verb_lemma + 'ed'

    def _conjugate_verb(self, verb_lemma: str, subject: str) -> str:
        """Enhanced verb conjugation for both singular and descriptive subjects."""
        
        if subject.startswith('the '):
            subject_noun = subject[4:]
        else:
            subject_noun = subject.lower()
        
        third_person_singular = {
            'system', 'server', 'application', 'service', 'documentation', 'manual', 
            'configuration', 'database', 'interface', 'platform', 'framework'
        }
        
        if subject_noun in third_person_singular:
            if verb_lemma.endswith('e'):
                return verb_lemma + 's'
            elif verb_lemma.endswith(('s', 'sh', 'ch', 'x', 'z')):
                return verb_lemma + 'es'
            elif verb_lemma.endswith('y') and len(verb_lemma) > 1 and verb_lemma[-2] not in 'aeiou':
                return verb_lemma[:-1] + 'ies'
            else:
                return verb_lemma + 's'
        else:
            return verb_lemma

    def _has_legitimate_temporal_context(self, doc, sentence: str) -> bool:
        """
        Detect when past tense is legitimately appropriate due to temporal context.
        
        Past tense is appropriate for:
        - Historical descriptions ("Before this update...")
        - Bug reports and issue descriptions  
        - Release notes and change descriptions
        - Temporal comparisons ("Previously...")
        """
        sentence_lower = sentence.lower()
        
        # Temporal indicators that justify past tense
        temporal_indicators = {
            # Version/update context
            'before this update', 'before the update', 'prior to this update',
            'before this release', 'before the release', 'in previous versions',
            'in earlier versions', 'previously', 'formerly', 'originally',
            
            # Issue/bug context  
            'this issue occurred', 'this condition occurred', 'this problem occurred',
            'the issue was', 'the problem was', 'the bug was', 'the error was',
            'users experienced', 'this caused', 'this resulted in',
            
            # Historical context
            'in the past', 'historically', 'before the fix', 'before the change',
            'until now', 'until this version', 'up until', 'prior to',
            
            # Specific temporal phrases
            'this condition occurred', 'the service could not', 'users could not',
            'the system was unable', 'it was not possible', 'this failed to'
        }
        
        # Check for explicit temporal indicators
        for indicator in temporal_indicators:
            if indicator in sentence_lower:
                return True
        
        # Pattern detection using spaCy for more sophisticated analysis
        temporal_patterns = self._detect_temporal_patterns(doc)
        if temporal_patterns:
            return True
        
        # Context clues from document structure (if available)
        context_clues = self._detect_release_notes_context(sentence_lower)
        if context_clues:
            return True
        
        return False
    
    def _detect_temporal_patterns(self, doc) -> bool:
        """Use spaCy to detect temporal patterns that justify past tense."""
        
        # Look for temporal prepositions at sentence start
        if len(doc) > 0:
            first_token = doc[0]
            temporal_prepositions = {'before', 'after', 'during', 'until', 'since', 'when'}
            if first_token.lemma_.lower() in temporal_prepositions:
                return True
        
        # Look for temporal nouns/phrases
        temporal_nouns = {'update', 'release', 'version', 'fix', 'change', 'modification'}
        for token in doc:
            if (token.lemma_.lower() in temporal_nouns and 
                any(child.text.lower() in {'this', 'the', 'previous', 'earlier'} 
                    for child in token.children)):
                return True
        
        # Look for modal past constructions indicating capability/possibility
        for token in doc:
            if (token.lemma_.lower() in {'could', 'would', 'might'} and 
                token.tag_ == 'MD'):
                # Check if this is describing a past limitation/capability
                head_verb = token.head
                if head_verb and head_verb.lemma_.lower() in {'reload', 'access', 'load', 'connect', 'process'}:
                    # Check for negative context
                    if any(child.lemma_.lower() == 'not' for child in token.children):
                        return True
        
        return False
    
    def _detect_release_notes_context(self, sentence_lower: str) -> bool:
        """Detect if this appears to be release notes or changelog context."""
        
        release_notes_indicators = {
            'fixed', 'resolved', 'addressed', 'corrected', 'improved',
            'enhanced', 'updated', 'modified', 'changed', 'added', 'removed',
            'introduced', 'deprecated', 'replaced', 'migrated'
        }
        
        issue_description_patterns = {
            'failed to', 'unable to', 'could not', 'did not', 'would not',
            'was not', 'were not', 'caused', 'resulted in', 'led to'
        }
        
        # Check for release notes language
        for indicator in release_notes_indicators:
            if indicator in sentence_lower:
                return True
        
        # Check for issue description patterns
        for pattern in issue_description_patterns:
            if pattern in sentence_lower:
                return True
        
        return False

    def _get_contextual_passive_voice_message(self, construction: PassiveConstruction, evidence_score: float) -> str:
        """Generate context-aware error messages for passive voice."""
        
        context_type = construction.context_type
        
        # Base message varies by evidence strength
        if evidence_score > 0.8:
            base_msg = "Sentence is in the passive voice."
        elif evidence_score > 0.5:
            base_msg = "Sentence may be in the passive voice."
        else:
            base_msg = "Sentence appears to use passive voice."
        
        # Add context-specific guidance
        if context_type == ContextType.INSTRUCTIONAL:
            return f"{base_msg} Consider using active voice for clearer instructions."
        elif context_type == ContextType.DESCRIPTIVE:
            return f"{base_msg} While acceptable for descriptions, active voice may be clearer."
        else:
            return f"{base_msg} Consider using active voice for clarity."

    # === EVIDENCE-BASED: FUTURE TENSE ===

    def _calculate_future_tense_evidence(self, will_token: Token, head_verb: Token, doc: Doc, sentence: str, text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for future tense concerns.
        
        Higher scores indicate stronger evidence that future tense should be corrected.
        Lower scores indicate acceptable usage in specific contexts.
        
        Args:
            will_token: The 'will' modal token
            head_verb: The main verb following 'will'
            doc: The sentence document
            sentence: The sentence text
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (acceptable) to 1.0 (should be corrected)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_future_tense_evidence(will_token, head_verb, doc, sentence)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this construction
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_future_tense(evidence_score, will_token, head_verb, doc, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_future_tense(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_future_tense(evidence_score, will_token, head_verb, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_future_tense(evidence_score, will_token, head_verb, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    # === FUTURE TENSE EVIDENCE METHODS ===

    def _get_base_future_tense_evidence(self, will_token: Token, head_verb: Token, doc: Doc, sentence: str) -> float:
        """Get base evidence score for future tense concerns."""
        
        # === FUTURE TENSE TYPE ANALYSIS ===
        # Different future constructions have different evidence strengths
        
        # High-priority corrections (inappropriate in instructions/procedures)
        inappropriate_contexts = {
            'will click', 'will select', 'will enter', 'will type', 'will configure',
            'will install', 'will setup', 'will run', 'will execute', 'will perform'
        }
        
        # Medium-priority corrections (better as present tense)
        better_as_present = {
            'will display', 'will show', 'will provide', 'will contain', 'will include',
            'will support', 'will enable', 'will allow', 'will require'
        }
        
        # Low-priority corrections (context-dependent)
        context_dependent = {
            'will be', 'will have', 'will become', 'will remain', 'will continue'
        }
        
        # Check construction type
        construction = f"{will_token.text.lower()} {head_verb.lemma_.lower()}"
        
        if construction in inappropriate_contexts:
            return 0.8  # High evidence for procedural/instructional contexts
        elif construction in better_as_present:
            return 0.6  # Medium evidence for descriptive contexts
        elif construction in context_dependent:
            return 0.4  # Lower evidence, context-dependent
        else:
            return 0.5  # Default evidence for future tense usage

    def _apply_linguistic_clues_future_tense(self, evidence_score: float, will_token: Token, head_verb: Token, doc: Doc, sentence: str) -> float:
        """
        Apply linguistic analysis clues for future tense detection.
        
        Analyzes SpaCy linguistic features including question forms, conditionals,
        temporal markers, and surrounding context to determine evidence strength
        for future tense corrections.
        
        Args:
            evidence_score: Current evidence score to modify
            will_token: The 'will' modal token
            head_verb: The main verb following 'will'
            doc: The sentence document
            sentence: The sentence text
            
        Returns:
            float: Modified evidence score based on linguistic analysis
        """
        
        sent_lower = sentence.lower()
        
        # === QUESTION AND CONDITIONAL FORMS ===
        # Questions and conditionals may legitimately use 'will'
        
        if sentence.strip().endswith('?'):
            evidence_score -= 0.3  # Questions often need future tense
        
        # Conditional markers
        conditional_markers = ['if ', 'whether ', 'when ', 'unless ', 'in case ']
        if any(marker in sent_lower for marker in conditional_markers):
            evidence_score -= 0.2  # Conditionals may need future tense
        
        # === TEMPORAL CONTEXT INDICATORS ===
        # Legitimate future temporal markers
        
        scheduled_indicators = [
            'tomorrow', 'next week', 'next month', 'next year', 'later',
            'upcoming', 'planned', 'scheduled', 'in the future', 'eventually',
            'soon', 'shortly', 'in time', 'by then', 'after that'
        ]
        
        if any(indicator in sent_lower for indicator in scheduled_indicators):
            evidence_score -= 0.15  # Scheduled/planned events may justify future tense
        
        # === ABILITY AND CAPABILITY CONSTRUCTIONS ===
        # "will be able to" constructions
        
        if 'will be able to' in sent_lower:
            evidence_score -= 0.2  # Capability expressions may justify future tense
        
        # Modal combinations that suggest necessity/possibility
        modal_combinations = ['will need to', 'will have to', 'will be required to']
        if any(combo in sent_lower for combo in modal_combinations):
            evidence_score -= 0.1  # Necessity expressions may be acceptable
        
        # === SURROUNDING CONTEXT ANALYSIS ===
        # Check for instruction vs. description context
        
        instruction_indicators = [
            'step', 'click', 'select', 'enter', 'type', 'configure', 'setup',
            'install', 'run', 'execute', 'perform', 'do the following'
        ]
        
        if any(indicator in sent_lower for indicator in instruction_indicators):
            evidence_score += 0.2  # Instructions should avoid future tense
        
        # === NEGATION CONTEXT ===
        # Negative constructions may be more acceptable
        
        if 'will not' in sent_lower or "won't" in sent_lower:
            evidence_score -= 0.1  # Negative futures may be acceptable for warnings
        
        # === NAMED ENTITY RECOGNITION ===
        # Named entities may affect verb usage appropriateness
        
        for token in doc:
            if hasattr(token, 'ent_type_') and token.ent_type_:
                ent_type = token.ent_type_
                
                # Organization or product entities may use different verb patterns
                if ent_type in ['ORG', 'PRODUCT', 'WORK_OF_ART']:
                    # Check if entity is related to the verb construction
                    if abs(token.i - will_token.i) <= 3:  # Within 3 tokens
                        evidence_score -= 0.1  # Entity contexts may justify future tense
                
                # Person entities may use different language patterns
                elif ent_type in ['PERSON', 'GPE']:
                    if abs(token.i - will_token.i) <= 2:  # Within 2 tokens
                        evidence_score -= 0.05  # Person/place contexts may be more flexible
                
                # Event or temporal entities may justify future constructions
                elif ent_type in ['EVENT', 'DATE', 'TIME']:
                    if abs(token.i - will_token.i) <= 4:  # Within 4 tokens
                        evidence_score -= 0.15  # Temporal entities may justify future tense
        
        # === VERB TYPE ANALYSIS ===
        # Some verbs are more problematic with 'will' than others
        
        action_verbs = {
            'click', 'select', 'enter', 'type', 'run', 'execute', 'perform',
            'configure', 'install', 'setup', 'create', 'delete', 'modify'
        }
        
        if head_verb.lemma_.lower() in action_verbs:
            evidence_score += 0.15  # Action verbs should generally be imperative
        
        state_verbs = {
            'be', 'have', 'become', 'remain', 'continue', 'appear', 'seem'
        }
        
        if head_verb.lemma_.lower() in state_verbs:
            evidence_score -= 0.1  # State verbs more acceptable with 'will'
        
        # === SENTENCE POSITION ANALYSIS ===
        # Future tense at sentence beginning is often more problematic
        
        first_two_tokens = [token.text.lower() for token in doc[:2]]
        if 'will' in first_two_tokens:
            evidence_score += 0.1  # Sentence-initial 'will' often problematic
        
        return evidence_score

    def _apply_structural_clues_future_tense(self, evidence_score: float, context: Dict[str, Any]) -> float:
        """
        Apply document structure clues for future tense detection.
        
        Analyzes document structure context including block types, heading levels,
        and other structural elements to determine appropriate evidence adjustments
        for future tense usage.
        
        Args:
            evidence_score: Current evidence score to modify
            context: Document context dictionary
            
        Returns:
            float: Modified evidence score based on structural analysis
        """
        
        block_type = context.get('block_type', 'paragraph')
        
        # === TECHNICAL DOCUMENTATION CONTEXTS ===
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.8  # Code blocks may contain future references
        elif block_type == 'inline_code':
            evidence_score -= 0.6  # Inline code may reference future behavior
        
        # === HEADING CONTEXT ===
        if block_type == 'heading':
            heading_level = context.get('block_level', 1)
            if heading_level == 1:  # H1 - Main headings
                evidence_score -= 0.2  # Main headings may describe future features
            elif heading_level == 2:  # H2 - Section headings  
                evidence_score -= 0.1  # Section headings may reference future content
            elif heading_level >= 3:  # H3+ - Subsection headings
                evidence_score -= 0.05  # Subsection headings less likely to need future
        
        # === LIST CONTEXT ===
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score += 0.1  # List items should generally be present/imperative
            
            # Nested list items may be more procedural
            if context.get('list_depth', 1) > 1:
                evidence_score += 0.05  # Nested items often procedural steps
        
        # === TABLE CONTEXT ===
        elif block_type in ['table_cell', 'table_header']:
            evidence_score += 0.05  # Tables should generally use present tense
        
        # === ADMONITION CONTEXT ===
        elif block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'TIP', 'HINT']:
                evidence_score -= 0.1  # Notes may describe future behavior
            elif admonition_type in ['WARNING', 'CAUTION', 'DANGER']:
                evidence_score -= 0.15  # Warnings may describe future consequences
            elif admonition_type in ['IMPORTANT', 'ATTENTION']:
                evidence_score -= 0.05  # Important notices may reference future
        
        # === QUOTE/CITATION CONTEXT ===
        elif block_type in ['block_quote', 'citation']:
            evidence_score -= 0.2  # Quotes may preserve original future tense
        
        # === EXAMPLE/SAMPLE CONTEXT ===
        elif block_type in ['example', 'sample']:
            evidence_score -= 0.1  # Examples may show future scenarios
        
        return evidence_score

    def _apply_semantic_clues_future_tense(self, evidence_score: float, will_token: Token, head_verb: Token, text: str, context: Dict[str, Any]) -> float:
        """
        Apply semantic and content-type clues for future tense detection.
        
        Analyzes high-level semantic context including content type, domain, audience,
        and document purpose to determine evidence strength for future tense corrections.
        
        Args:
            evidence_score: Current evidence score to modify
            will_token: The 'will' modal token
            head_verb: The main verb following 'will'
            text: Full document text
            context: Document context dictionary
            
        Returns:
            float: Modified evidence score based on semantic analysis
        """
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # === CONTENT TYPE ANALYSIS ===
        # Some content types strongly discourage future tense
        if content_type == 'procedural':
            evidence_score += 0.25  # Procedures should use imperative mood
        elif content_type == 'api':
            evidence_score += 0.2  # API docs should describe current behavior
        elif content_type == 'technical':
            evidence_score += 0.15  # Technical writing should be direct
        elif content_type == 'tutorial':
            evidence_score += 0.2  # Tutorials should be step-by-step present
        elif content_type == 'legal':
            evidence_score += 0.1  # Legal writing should be precise
        elif content_type == 'academic':
            evidence_score += 0.05  # Academic writing should be clear
        elif content_type == 'marketing':
            evidence_score -= 0.1  # Marketing may describe future benefits
        elif content_type == 'narrative':
            evidence_score -= 0.15  # Narrative may legitimately use future
        
        # === DOMAIN-SPECIFIC PATTERNS ===
        if domain in ['software', 'engineering', 'devops']:
            evidence_score += 0.1  # Technical domains prefer direct language
        elif domain in ['user-documentation', 'help']:
            evidence_score += 0.15  # User docs should be action-oriented
        elif domain in ['training', 'education']:
            evidence_score += 0.1  # Training should be direct
        elif domain in ['legal', 'compliance']:
            evidence_score += 0.05  # Legal domains prefer precision
        elif domain in ['planning', 'roadmap']:
            evidence_score -= 0.2  # Planning documents may legitimately use future
        
        # === AUDIENCE CONSIDERATIONS ===
        if audience in ['beginner', 'general', 'consumer']:
            evidence_score += 0.1  # General audiences need clear instructions
        elif audience in ['professional', 'business']:
            evidence_score += 0.05  # Professional content should be direct
        elif audience in ['developer', 'technical', 'expert']:
            evidence_score += 0.08  # Technical audiences expect direct language
        
        # === DOCUMENT PURPOSE ANALYSIS ===
        if self._is_installation_documentation(text):
            evidence_score += 0.2  # Installation docs should be step-by-step
        
        if self._is_troubleshooting_documentation(text):
            evidence_score += 0.15  # Troubleshooting should be direct
        
        if self._is_ui_documentation(text):
            evidence_score += 0.18  # UI docs should describe current behavior
        
        if self._is_release_notes_documentation(text):
            evidence_score -= 0.3  # Release notes may describe future features
        
        if self._is_roadmap_documentation(text):
            evidence_score -= 0.4  # Roadmaps legitimately use future tense
        
        if self._is_planning_documentation(text):
            evidence_score -= 0.3  # Planning docs may use future tense
        
        # === DOCUMENT LENGTH CONTEXT ===
        doc_length = len(text.split())
        if doc_length < 100:  # Short documents
            evidence_score += 0.05  # Brief content should be direct
        elif doc_length > 5000:  # Long documents
            evidence_score += 0.02  # Consistency important in long docs
        
        return evidence_score

    def _apply_feedback_clues_future_tense(self, evidence_score: float, will_token: Token, head_verb: Token, context: Dict[str, Any]) -> float:
        """
        Apply feedback patterns for future tense detection.
        
        Incorporates learned patterns from user feedback including acceptance rates,
        context-specific patterns, and correction success rates to refine evidence
        scoring for future tense corrections.
        
        Args:
            evidence_score: Current evidence score to modify
            will_token: The 'will' modal token
            head_verb: The main verb following 'will'
            context: Document context dictionary
            
        Returns:
            float: Modified evidence score based on feedback analysis
        """
        
        feedback_patterns = self._get_cached_feedback_patterns('verbs_future_tense')
        
        # === PHRASE-SPECIFIC FEEDBACK ===
        phrase = f"{will_token.text.lower()} {head_verb.lemma_.lower()}"
        
        # Check if this specific phrase is commonly accepted by users
        accepted_phrases = feedback_patterns.get('accepted_future_phrases', set())
        if phrase in accepted_phrases:
            evidence_score -= 0.3  # Users consistently accept this phrase
        
        flagged_phrases = feedback_patterns.get('flagged_future_phrases', set())
        if phrase in flagged_phrases:
            evidence_score += 0.2  # Users consistently flag this phrase
        
        # === CONTEXT-SPECIFIC FEEDBACK ===
        content_type = context.get('content_type', 'general')
        context_patterns = feedback_patterns.get(f'{content_type}_future_patterns', {})
        
        if phrase in context_patterns.get('acceptable', set()):
            evidence_score -= 0.2
        elif phrase in context_patterns.get('problematic', set()):
            evidence_score += 0.25
        
        # === VERB-SPECIFIC PATTERNS ===
        verb_lemma = head_verb.lemma_.lower()
        verb_patterns = feedback_patterns.get('verb_specific_patterns', {})
        
        if verb_lemma in verb_patterns.get('often_accepted_with_will', set()):
            evidence_score -= 0.15  # This verb often acceptable with 'will'
        elif verb_lemma in verb_patterns.get('problematic_with_will', set()):
            evidence_score += 0.2  # This verb problematic with 'will'
        
        # === CORRECTION SUCCESS PATTERNS ===
        correction_patterns = feedback_patterns.get('correction_success', {})
        correction_success = correction_patterns.get(phrase, 0.5)
        
        if correction_success > 0.8:
            evidence_score += 0.1  # Corrections highly successful
        elif correction_success < 0.3:
            evidence_score -= 0.15  # Corrections often rejected
        
        return evidence_score

    # Removed _get_cached_feedback_patterns_future_tense - using base class utility

    def _get_contextual_future_tense_message(self, flagged_text: str, ev: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error messages for future tense patterns."""
        
        content_type = context.get('content_type', 'general')
        
        if ev > 0.9:
            return f"Future tense '{flagged_text}' should be avoided in {content_type} documentation. Use present or imperative."
        elif ev > 0.7:
            return f"Consider replacing '{flagged_text}' with present tense for clearer {content_type} writing."
        elif ev > 0.5:
            return f"Present tense is preferred over '{flagged_text}' in most technical writing."
        else:
            return f"The phrase '{flagged_text}' may benefit from present tense for clarity."

    def _generate_smart_future_tense_suggestions(self, head_verb: Token, ev: float, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for future tense patterns."""
        
        base = head_verb.lemma_
        suggestions = []
        content_type = context.get('content_type', 'general')
        
        # Base suggestions based on evidence strength and context
        if ev > 0.8:
            if content_type == 'procedural':
                suggestions.append(f"Use imperative: '{base.capitalize()}' (direct instruction)")
                suggestions.append(f"Use present: 'The system {base}s' (describe current behavior)")
            elif content_type == 'api':
                suggestions.append(f"Use present: 'The method {base}s' (current API behavior)")
                suggestions.append(f"Use present: 'This {base}s the resource' (API functionality)")
            else:
                suggestions.append(f"Use present: '{base}s' (current state/behavior)")
                suggestions.append(f"Use imperative: '{base.capitalize()}' (direct action)")
        else:
            suggestions.append(f"Consider present: '{base}s'")
            suggestions.append(f"Consider imperative: '{base.capitalize()}'")
        
        # Context-specific advice
        if content_type == 'procedural':
            suggestions.append("Use imperative mood for clear step-by-step instructions.")
        elif content_type == 'api':
            suggestions.append("Describe API behavior in present tense for clarity.")
        elif content_type == 'technical':
            suggestions.append("Technical documentation should describe current system behavior.")
        elif content_type == 'tutorial':
            suggestions.append("Tutorial steps should be in imperative mood.")
        
        return suggestions[:3]

    # === EVIDENCE-BASED: PAST TENSE ===

    def _calculate_past_tense_evidence(self, root_verb: Token, doc: Doc, sentence: str, text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for past tense concerns.
        
        Higher scores indicate stronger evidence that past tense should be corrected.
        Lower scores indicate acceptable usage in specific contexts.
        
        Args:
            root_verb: The root verb token in past tense
            doc: The sentence document
            sentence: The sentence text
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (acceptable) to 1.0 (should be corrected)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_past_tense_evidence(root_verb, doc, sentence)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this construction
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_past_tense(evidence_score, root_verb, doc, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_past_tense(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_past_tense(evidence_score, root_verb, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_past_tense(evidence_score, root_verb, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    # === PAST TENSE EVIDENCE METHODS ===

    def _get_base_past_tense_evidence(self, root_verb: Token, doc: Doc, sentence: str) -> float:
        """Get base evidence score for past tense concerns."""
        
        # === PAST TENSE TYPE ANALYSIS ===
        # Different past tense contexts have different evidence strengths
        
        # High-priority corrections (inappropriate in instructions/current descriptions)
        inappropriate_past_verbs = {
            'clicked', 'selected', 'entered', 'typed', 'configured', 'installed',
            'ran', 'executed', 'performed', 'created', 'deleted', 'modified'
        }
        
        # Medium-priority corrections (better as present for current behavior)
        better_as_present = {
            'displayed', 'showed', 'provided', 'contained', 'included',
            'supported', 'enabled', 'allowed', 'required', 'returned'
        }
        
        # Low-priority corrections (often acceptable in temporal contexts)
        temporal_acceptable = {
            'was', 'were', 'had', 'became', 'remained', 'continued',
            'appeared', 'seemed', 'occurred', 'happened'
        }
        
        # Check verb type
        verb_text = root_verb.text.lower()
        verb_lemma = root_verb.lemma_.lower()
        
        if verb_text in inappropriate_past_verbs or verb_lemma in inappropriate_past_verbs:
            return 0.7  # High evidence for action verbs in past tense
        elif verb_text in better_as_present or verb_lemma in better_as_present:
            return 0.5  # Medium evidence for descriptive verbs in past tense
        elif verb_text in temporal_acceptable or verb_lemma in temporal_acceptable:
            return 0.3  # Lower evidence for state verbs in past tense
        else:
            return 0.45  # Default evidence for past tense usage

    def _apply_linguistic_clues_past_tense(self, evidence_score: float, root_verb: Token, doc: Doc, sentence: str) -> float:
        """
        Apply linguistic analysis clues for past tense detection.
        
        Analyzes SpaCy linguistic features including temporal markers, context indicators,
        and surrounding constructions to determine evidence strength for past tense corrections.
        
        Args:
            evidence_score: Current evidence score to modify
            root_verb: The root verb token in past tense
            doc: The sentence document
            sentence: The sentence text
            
        Returns:
            float: Modified evidence score based on linguistic analysis
        """
        
        sent_lower = sentence.lower()
        
        # === TEMPORAL CONTEXT INDICATORS ===
        # Strong temporal indicators that justify past tense
        
        strong_temporal_indicators = [
            'before this update', 'before the update', 'prior to this update',
            'before this release', 'before the release', 'in previous versions',
            'in earlier versions', 'previously', 'formerly', 'originally',
            'this issue occurred', 'this problem occurred', 'the bug was',
            'users experienced', 'this caused', 'this resulted in'
        ]
        
        if any(indicator in sent_lower for indicator in strong_temporal_indicators):
            evidence_score -= 0.4  # Strong justification for past tense
        
        # Weaker temporal indicators
        weak_temporal_indicators = [
            'in the past', 'historically', 'before', 'earlier', 'until now',
            'up until', 'prior to', 'when', 'while', 'during'
        ]
        
        if any(indicator in sent_lower for indicator in weak_temporal_indicators):
            evidence_score -= 0.2  # Some justification for past tense
        
        # === LEGITIMATE TEMPORAL PATTERNS ===
        # Use enhanced temporal detection
        if self._has_legitimate_temporal_context(doc, sentence):
            evidence_score -= 0.3  # Comprehensive temporal analysis
        
        # === ISSUE/BUG REPORTING CONTEXT ===
        # Past tense often appropriate for issue descriptions
        
        issue_indicators = [
            'failed to', 'unable to', 'could not', 'did not', 'would not',
            'was not', 'were not', 'error', 'issue', 'problem', 'bug'
        ]
        
        if any(indicator in sent_lower for indicator in issue_indicators):
            evidence_score -= 0.25  # Issue descriptions often need past tense
        
        # === NEGATION CONTEXT ===
        # Negative past constructions often describe problems
        
        negative_past_patterns = ['was not', 'were not', 'did not', 'could not']
        if any(pattern in sent_lower for pattern in negative_past_patterns):
            evidence_score -= 0.2  # Negative past often legitimate
        
        # === SENTENCE STRUCTURE ANALYSIS ===
        # Check for temporal subordinate clauses
        
        for token in doc:
            if token.dep_ == 'mark' and token.lemma_.lower() in ['when', 'while', 'before', 'after']:
                # Check if this introduces a temporal clause
                if token.head and 'Tense=Past' in str(token.head.morph):
                    evidence_score -= 0.15  # Temporal clauses may justify past tense
        
        # === CONDITIONAL AND HYPOTHETICAL CONSTRUCTIONS ===
        # Past tense in conditionals may be appropriate
        
        conditional_markers = ['if', 'unless', 'suppose', 'imagine', 'what if']
        if any(marker in sent_lower for marker in conditional_markers):
            evidence_score -= 0.1  # Conditionals may use past tense
        
        # === QUOTED SPEECH OR REPORTED CONTENT ===
        # Quoted content may preserve original tense
        
        if '"' in sentence or "'" in sentence:
            evidence_score -= 0.15  # Quoted content may preserve past tense
        
        # === NAMED ENTITY RECOGNITION ===
        # Named entities may affect past tense appropriateness
        
        for token in doc:
            if hasattr(token, 'ent_type_') and token.ent_type_:
                ent_type = token.ent_type_
                
                # Organization or product entities may reference historical states
                if ent_type in ['ORG', 'PRODUCT', 'WORK_OF_ART']:
                    # Check if entity is related to the past tense verb
                    if abs(token.i - root_verb.i) <= 3:  # Within 3 tokens
                        evidence_score -= 0.08  # Entity contexts may justify past tense
                
                # Person entities in past contexts often legitimate
                elif ent_type in ['PERSON', 'GPE']:
                    if abs(token.i - root_verb.i) <= 2:  # Within 2 tokens
                        evidence_score -= 0.1  # Person/place historical references
                
                # Event or temporal entities strongly justify past tense
                elif ent_type in ['EVENT', 'DATE', 'TIME']:
                    if abs(token.i - root_verb.i) <= 4:  # Within 4 tokens
                        evidence_score -= 0.2  # Temporal entities strongly justify past tense
                
                # Version or release entities may justify past tense
                elif ent_type in ['CARDINAL', 'ORDINAL']:
                    # Check if this might be a version number
                    if any(word in doc.text.lower() for word in ['version', 'release', 'update']):
                        if abs(token.i - root_verb.i) <= 3:
                            evidence_score -= 0.12  # Version contexts may justify past tense
        
        # === COMPARISON AND CONTRAST STRUCTURES ===
        # Comparing past vs. present states
        
        comparison_indicators = ['compared to', 'unlike', 'whereas', 'however', 'but now']
        if any(indicator in sent_lower for indicator in comparison_indicators):
            evidence_score -= 0.1  # Comparisons may need past tense
        
        return evidence_score

    def _apply_structural_clues_past_tense(self, evidence_score: float, context: Dict[str, Any]) -> float:
        """
        Apply document structure clues for past tense detection.
        
        Analyzes document structure context including block types, heading levels,
        and other structural elements to determine appropriate evidence adjustments
        for past tense usage.
        
        Args:
            evidence_score: Current evidence score to modify
            context: Document context dictionary
            
        Returns:
            float: Modified evidence score based on structural analysis
        """
        
        block_type = context.get('block_type', 'paragraph')
        
        # === TECHNICAL DOCUMENTATION CONTEXTS ===
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.6  # Code blocks may contain past references
        elif block_type == 'inline_code':
            evidence_score -= 0.4  # Inline code may reference past behavior
        
        # === HEADING CONTEXT ===
        if block_type == 'heading':
            heading_level = context.get('block_level', 1)
            if heading_level == 1:  # H1 - Main headings
                evidence_score += 0.1  # Main headings should generally be present
            elif heading_level == 2:  # H2 - Section headings  
                evidence_score += 0.05  # Section headings should be current
            elif heading_level >= 3:  # H3+ - Subsection headings
                evidence_score += 0.02  # Subsection headings less critical
        
        # === LIST CONTEXT ===
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score += 0.1  # List items should generally be present/imperative
            
            # Nested list items may be more procedural
            if context.get('list_depth', 1) > 1:
                evidence_score += 0.05  # Nested items often procedural steps
        
        # === TABLE CONTEXT ===
        elif block_type in ['table_cell', 'table_header']:
            evidence_score += 0.05  # Tables should generally use present tense
        
        # === ADMONITION CONTEXT ===
        elif block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'TIP', 'HINT']:
                evidence_score -= 0.05  # Notes may describe past situations
            elif admonition_type in ['WARNING', 'CAUTION', 'DANGER']:
                evidence_score -= 0.1  # Warnings may describe past problems
            elif admonition_type in ['IMPORTANT', 'ATTENTION']:
                evidence_score += 0.02  # Important notices should be current
        
        # === QUOTE/CITATION CONTEXT ===
        elif block_type in ['block_quote', 'citation']:
            evidence_score -= 0.3  # Quotes may preserve original past tense
        
        # === EXAMPLE/SAMPLE CONTEXT ===
        elif block_type in ['example', 'sample']:
            evidence_score -= 0.2  # Examples may show past scenarios
        
        # === CHANGELOG/RELEASE NOTES CONTEXT ===
        elif block_type in ['changelog', 'release_notes']:
            evidence_score -= 0.4  # Change logs legitimately use past tense
        
        return evidence_score

    def _apply_semantic_clues_past_tense(self, evidence_score: float, root_verb: Token, text: str, context: Dict[str, Any]) -> float:
        """
        Apply semantic and content-type clues for past tense detection.
        
        Analyzes high-level semantic context including content type, domain, audience,
        and document purpose to determine evidence strength for past tense corrections.
        
        Args:
            evidence_score: Current evidence score to modify
            root_verb: The root verb token in past tense
            text: Full document text
            context: Document context dictionary
            
        Returns:
            float: Modified evidence score based on semantic analysis
        """
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # === CONTENT TYPE ANALYSIS ===
        # Some content types strongly discourage past tense
        if content_type == 'procedural':
            evidence_score += 0.25  # Procedures should use present/imperative
        elif content_type == 'api':
            evidence_score += 0.2  # API docs should describe current behavior
        elif content_type == 'technical':
            evidence_score += 0.15  # Technical writing should be current
        elif content_type == 'tutorial':
            evidence_score += 0.2  # Tutorials should be step-by-step present
        elif content_type == 'legal':
            evidence_score += 0.1  # Legal writing should be precise and current
        elif content_type == 'academic':
            evidence_score += 0.05  # Academic writing should be clear
        elif content_type == 'marketing':
            evidence_score += 0.1  # Marketing should focus on current benefits
        elif content_type == 'narrative':
            evidence_score -= 0.1  # Narrative may legitimately use past tense
        
        # === CONTENT TYPES THAT ACCEPT PAST TENSE ===
        past_appropriate_types = ['release_notes', 'changelog', 'bug_report', 'issue_report']
        if content_type in past_appropriate_types:
            evidence_score -= 0.3  # These content types legitimately use past tense
        
        # === DOMAIN-SPECIFIC PATTERNS ===
        if domain in ['software', 'engineering', 'devops']:
            evidence_score += 0.1  # Technical domains prefer current descriptions
        elif domain in ['user-documentation', 'help']:
            evidence_score += 0.15  # User docs should be current and actionable
        elif domain in ['training', 'education']:
            evidence_score += 0.1  # Training should be current
        elif domain in ['legal', 'compliance']:
            evidence_score += 0.05  # Legal domains prefer current statements
        elif domain in ['support', 'troubleshooting']:
            evidence_score -= 0.1  # Support may describe past problems
        
        # === AUDIENCE CONSIDERATIONS ===
        if audience in ['beginner', 'general', 'consumer']:
            evidence_score += 0.1  # General audiences need current, clear language
        elif audience in ['professional', 'business']:
            evidence_score += 0.05  # Professional content should be current
        elif audience in ['developer', 'technical', 'expert']:
            evidence_score += 0.08  # Technical audiences expect current descriptions
        
        # === DOCUMENT PURPOSE ANALYSIS ===
        if self._is_installation_documentation(text):
            evidence_score += 0.2  # Installation docs should be current steps
        
        if self._is_troubleshooting_documentation(text):
            evidence_score -= 0.1  # Troubleshooting may describe past problems
        
        if self._is_ui_documentation(text):
            evidence_score += 0.18  # UI docs should describe current interface
        
        if self._is_release_notes_documentation(text):
            evidence_score -= 0.4  # Release notes legitimately use past tense
        
        if self._is_changelog_documentation(text):
            evidence_score -= 0.4  # Changelogs legitimately use past tense
        
        if self._is_bug_report_documentation(text):
            evidence_score -= 0.3  # Bug reports may describe past issues
        
        # === DOCUMENT LENGTH CONTEXT ===
        doc_length = len(text.split())
        if doc_length < 100:  # Short documents
            evidence_score += 0.05  # Brief content should be current
        elif doc_length > 5000:  # Long documents
            evidence_score += 0.02  # Consistency important in long docs
        
        return evidence_score

    def _apply_feedback_clues_past_tense(self, evidence_score: float, root_verb: Token, context: Dict[str, Any]) -> float:
        """
        Apply feedback patterns for past tense detection.
        
        Incorporates learned patterns from user feedback including acceptance rates,
        context-specific patterns, and correction success rates to refine evidence
        scoring for past tense corrections.
        
        Args:
            evidence_score: Current evidence score to modify
            root_verb: The root verb token in past tense
            context: Document context dictionary
            
        Returns:
            float: Modified evidence score based on feedback analysis
        """
        
        feedback_patterns = self._get_cached_feedback_patterns('verbs_past_tense')
        
        # === VERB-SPECIFIC FEEDBACK ===
        verb_lemma = root_verb.lemma_.lower()
        verb_text = root_verb.text.lower()
        
        # Check if this specific verb is commonly accepted in past tense by users
        accepted_past_verbs = feedback_patterns.get('often_accepted_past_verbs', set())
        if verb_lemma in accepted_past_verbs or verb_text in accepted_past_verbs:
            evidence_score -= 0.3  # Users consistently accept this verb in past tense
        
        flagged_past_verbs = feedback_patterns.get('often_flagged_past_verbs', set())
        if verb_lemma in flagged_past_verbs or verb_text in flagged_past_verbs:
            evidence_score += 0.2  # Users consistently flag this verb in past tense
        
        # === CONTEXT-SPECIFIC FEEDBACK ===
        content_type = context.get('content_type', 'general')
        context_patterns = feedback_patterns.get(f'{content_type}_past_patterns', {})
        
        if verb_lemma in context_patterns.get('acceptable', set()):
            evidence_score -= 0.2
        elif verb_lemma in context_patterns.get('problematic', set()):
            evidence_score += 0.25
        
        # === TEMPORAL CONTEXT FEEDBACK ===
        # Check patterns for temporal/historical contexts
        temporal_patterns = feedback_patterns.get('temporal_context_patterns', {})
        if verb_lemma in temporal_patterns.get('acceptable_in_temporal', set()):
            evidence_score -= 0.15  # This verb acceptable in temporal contexts
        
        # === CORRECTION SUCCESS PATTERNS ===
        correction_patterns = feedback_patterns.get('correction_success', {})
        correction_success = correction_patterns.get(verb_lemma, 0.5)
        
        if correction_success > 0.8:
            evidence_score += 0.1  # Corrections highly successful
        elif correction_success < 0.3:
            evidence_score -= 0.15  # Corrections often rejected
        
        return evidence_score

    # Removed _get_cached_feedback_patterns_past_tense - using base class utility

    def _get_contextual_past_tense_message(self, flagged_text: str, ev: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error messages for past tense patterns."""
        
        content_type = context.get('content_type', 'general')
        
        if ev > 0.9:
            return f"Past tense '{flagged_text}' should be avoided in {content_type} documentation. Use present tense."
        elif ev > 0.7:
            return f"Consider replacing '{flagged_text}' with present tense for clearer {content_type} writing."
        elif ev > 0.5:
            return f"Present tense is preferred over '{flagged_text}' in most technical writing."
        else:
            return f"The verb '{flagged_text}' may benefit from present tense for clarity."

    def _generate_smart_past_tense_suggestions(self, root_verb: Token, ev: float, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for past tense patterns."""
        
        base = root_verb.lemma_
        suggestions = []
        content_type = context.get('content_type', 'general')
        
        # Base suggestions based on evidence strength and context
        if ev > 0.8:
            if content_type == 'procedural':
                suggestions.append(f"Use imperative: '{base.capitalize()}' (direct instruction)")
                suggestions.append(f"Use present: 'The system {base}s' (describe current behavior)")
            elif content_type == 'api':
                suggestions.append(f"Use present: 'The method {base}s' (current API behavior)")
                suggestions.append(f"Use present: 'This {base}s the resource' (API functionality)")
            else:
                suggestions.append(f"Use present: '{base}s' (current state/behavior)")
                suggestions.append(f"Use imperative: '{base.capitalize()}' (direct action)")
        else:
            suggestions.append(f"Consider present: '{base}s'")
            suggestions.append("Consider if this describes current vs. historical behavior")
        
        # Context-specific advice
        if content_type == 'procedural':
            suggestions.append("Use imperative mood for clear step-by-step instructions.")
        elif content_type == 'api':
            suggestions.append("Describe current API behavior in present tense.")
        elif content_type == 'technical':
            suggestions.append("Technical documentation should describe current system behavior.")
        elif content_type == 'tutorial':
            suggestions.append("Tutorial steps should be in imperative mood.")
        else:
            suggestions.append("Use present tense for current behavior and instructions.")
        
        return suggestions[:3]

    # === HELPER METHODS FOR SEMANTIC ANALYSIS ===

    # Removed _is_installation_documentation - using base class utility

    # Removed _is_troubleshooting_documentation - using base class utility

    # Removed _is_user_interface_documentation - using base class utility

    def _is_release_notes_documentation(self, text: str) -> bool:
        """Check if text appears to be release notes documentation."""
        release_indicators = [
            'release notes', 'release', 'version', 'changelog', 'change log',
            'new features', 'improvements', 'bug fixes', 'fixed', 'resolved',
            'added', 'removed', 'deprecated', 'enhanced', 'updated'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in release_indicators if indicator in text_lower) >= 3

    def _is_roadmap_documentation(self, text: str) -> bool:
        """Check if text appears to be roadmap documentation."""
        roadmap_indicators = [
            'roadmap', 'future', 'planned', 'upcoming', 'next version',
            'coming soon', 'will be', 'scheduled', 'timeline', 'milestone'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in roadmap_indicators if indicator in text_lower) >= 2

    def _is_planning_documentation(self, text: str) -> bool:
        """Check if text appears to be planning documentation."""
        planning_indicators = [
            'plan', 'planning', 'strategy', 'goals', 'objectives', 'timeline',
            'schedule', 'milestone', 'deliverable', 'project', 'initiative'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in planning_indicators if indicator in text_lower) >= 3

    def _is_changelog_documentation(self, text: str) -> bool:
        """Check if text appears to be changelog documentation."""
        changelog_indicators = [
            'changelog', 'change log', 'changes', 'fixed', 'added', 'removed',
            'changed', 'deprecated', 'security', 'unreleased', 'version'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in changelog_indicators if indicator in text_lower) >= 3

    def _is_bug_report_documentation(self, text: str) -> bool:
        """Check if text appears to be bug report documentation."""
        bug_report_indicators = [
            'bug', 'issue', 'error', 'problem', 'defect', 'fault',
            'reproduce', 'steps to reproduce', 'expected', 'actual',
            'workaround', 'failed', 'not working'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in bug_report_indicators if indicator in text_lower) >= 3

    def _is_ui_documentation(self, text: str) -> bool:
        """Check if text appears to be user interface documentation."""
        ui_indicators = [
            'user interface', 'ui', 'gui', 'dialog', 'window', 'button', 'menu',
            'toolbar', 'tab', 'panel', 'form', 'field', 'dropdown', 'checkbox',
            'click', 'select', 'enter', 'type'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in ui_indicators if indicator in text_lower) >= 3

    # === Feedback patterns for verbs ===
    def _get_feedback_patterns_verbs(self) -> Dict[str, Any]:
        return {
            'accepted_future_phrases': {
                'will be removed', 'will be deprecated', 'will be available'
            },
            'flagged_future_phrases': {
                'will click', 'will go', 'will run'
            },
            'often_accepted_past_verbs': {'fixed', 'resolved', 'addressed'}
        }
