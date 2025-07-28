"""
Missing Actor Detector

Detects passive voice sentences without clear actors, creating ambiguity
about who or what performs the action.

Example: "This is to be generated" - unclear who/what generates it.
"""

from typing import List, Dict, Any, Optional, Set
import re

from ..base_ambiguity_rule import AmbiguityDetector
from ..types import (
    AmbiguityType, AmbiguityCategory, AmbiguitySeverity,
    AmbiguityContext, AmbiguityEvidence, AmbiguityDetection,
    ResolutionStrategy, AmbiguityConfig
)


class MissingActorDetector(AmbiguityDetector):
    """
    Detects passive voice constructions without clear actors.
    
    This detector identifies sentences in passive voice that don't specify
    who or what performs the action, creating ambiguity for the reader.
    """
    
    def __init__(self, config: AmbiguityConfig, parent_rule=None):
        super().__init__(config, parent_rule)
        self.confidence_threshold = 0.7
        self.passive_indicators = {'be', 'is', 'are', 'was', 'were', 'being', 'been'}
        
        # Common actors that, when present, reduce ambiguity
        self.clear_actors = {
            'system', 'user', 'application', 'program', 'software', 'server',
            'database', 'service', 'api', 'interface', 'module', 'component',
            'administrator', 'developer', 'operator', 'manager', 'you', 'we'
        }
        
        # Technical contexts where missing actors are more problematic
        self.technical_contexts = {
            'configure', 'generate', 'create', 'install', 'setup', 'deploy',
            'execute', 'run', 'start', 'stop', 'update', 'modify', 'delete',
            'process', 'handle', 'manage', 'control', 'monitor', 'validate'
        }
    
    def detect(self, context: AmbiguityContext, nlp) -> List[AmbiguityDetection]:
        """
        Detect missing actors in passive voice sentences.
        
        Args:
            context: Sentence context for analysis
            nlp: SpaCy nlp object
            
        Returns:
            List of ambiguity detections
        """
        if not self.enabled:
            return []
        
        detections = []
        
        try:
            # Parse the sentence
            doc = nlp(context.sentence)
            
            # Check for passive voice constructions
            passive_constructions = self._find_passive_constructions(doc)
            
            for construction in passive_constructions:
                # Check if this passive construction lacks a clear actor
                if self._is_missing_actor(construction, doc, context):
                    detection = self._create_detection(construction, doc, context)
                    if detection:
                        detections.append(detection)
        
        except Exception as e:
            # Log error but don't fail
            print(f"Error in missing actor detection: {e}")
        
        return detections
    
    def _find_passive_constructions(self, doc) -> List[Dict[str, Any]]:
        """
        Find TRUE passive voice constructions in the sentence.
        Uses sophisticated validation to eliminate false positives from predicate 
        adjective constructions that spaCy mislabels as passive voice.
        """
        constructions = []
        
        for token in doc:
            # Method 1: SpaCy dependency parsing for passive (with validation)
            if token.dep_ == 'auxpass' or token.dep_ == 'nsubjpass':
                # Validate that this is actually passive voice, not predicate adjective
                if self._is_true_passive_voice(token, doc):
                    construction = self._extract_passive_construction(token, doc)
                    if construction:
                        constructions.append(construction)
            
            # Method 2: Pattern matching for "to be + past participle" (with validation)
            elif (token.lemma_ in self.passive_indicators and 
                  token.pos_ in ['AUX', 'VERB']):
                # Check if followed by past participle
                past_participle = self._find_past_participle(token, doc)
                if past_participle and self._is_true_passive_pattern(token, past_participle, doc):
                    construction = {
                        'auxiliary': token,
                        'past_participle': past_participle,
                        'type': 'be_passive',
                        'tokens': [token, past_participle]
                    }
                    constructions.append(construction)
        
        return constructions

    def _is_true_passive_voice(self, passive_token, doc) -> bool:
        """
        Validates whether a token marked as passive is actually passive voice
        or just a predicate adjective construction that spaCy mislabeled.
        """
        # Find the main verb (past participle)
        if passive_token.dep_ == 'nsubjpass':
            main_verb = passive_token.head
        elif passive_token.dep_ == 'auxpass':
            main_verb = passive_token.head
        else:
            return False
        
        # Must be a past participle (VBN) to be passive
        if main_verb.tag_ != 'VBN':
            return False
        
        # Check 1: Presence of explicit agent (by-phrase)
        # If there's a "by" phrase, it's definitely passive voice
        if self._has_by_phrase_for_token(main_verb, doc):
            return True
        
        # Check 2: Exclude adverbial clauses (common source of false positives)
        # Constructions like "After you are done" are typically adverbial
        if main_verb.dep_ == 'advcl':
            # This is an adverbial clause, likely predicate adjective
            return False
        
        # Check 3: Check for semantic indicators of state vs. action
        # Some past participles are more commonly used as adjectives
        state_oriented_verbs = {
            'done', 'finished', 'ready', 'prepared', 'set', 'fixed', 'broken', 
            'closed', 'open', 'available', 'busy', 'free', 'connected', 'offline'
        }
        
        if main_verb.lemma_ in state_oriented_verbs:
            # These are commonly used as predicate adjectives
            # Only consider them passive if there's strong evidence
            return self._has_strong_passive_evidence(main_verb, doc)
        
        # Check 4: Root verbs with clear passive structure
        if main_verb.dep_ == 'ROOT':
            # Root past participles are more likely to be passive
            # But still check for predicate adjective patterns
            return not self._is_predicate_adjective_pattern(main_verb, doc)
        
        # Check 5: Complex sentence analysis
        # In complex sentences, check the overall structure
        return self._analyze_complex_sentence_structure(main_verb, doc)

    def _is_true_passive_pattern(self, aux_token, past_participle, doc) -> bool:
        """Validate that a be + past participle pattern is truly passive voice."""
        # Apply the same validation logic as for spaCy-detected patterns
        if past_participle.dep_ == 'advcl':
            return False
        
        state_oriented_verbs = {
            'done', 'finished', 'ready', 'prepared', 'set', 'fixed', 'broken', 
            'closed', 'open', 'available', 'busy', 'free', 'connected', 'offline'
        }
        
        if past_participle.lemma_ in state_oriented_verbs:
            return self._has_strong_passive_evidence(past_participle, doc)
        
        return not self._is_predicate_adjective_pattern(past_participle, doc)

    def _has_by_phrase_for_token(self, main_verb, doc) -> bool:
        """Check if there's an explicit agent introduced by 'by'."""
        for token in doc:
            if (token.lemma_ == 'by' and 
                token.head == main_verb and 
                any(child.dep_ == 'pobj' for child in token.children)):
                return True
        return False

    def _has_strong_passive_evidence(self, main_verb, doc) -> bool:
        """
        For state-oriented verbs, require stronger evidence of passive voice.
        """
        # Evidence 1: Explicit agent
        if self._has_by_phrase_for_token(main_verb, doc):
            return True
        
        # Evidence 2: Modal auxiliary suggesting action rather than state
        for child in main_verb.children:
            if child.dep_ == 'auxpass' and child.lemma_ in ['was', 'were', 'been']:
                # Past tense auxiliary suggests an action that happened
                return True
        
        # Evidence 3: Temporal indicators suggesting an action occurred
        temporal_indicators = ['yesterday', 'recently', 'just', 'already', 'earlier']
        sentence_words = [token.lemma_.lower() for token in doc]
        if any(indicator in sentence_words for indicator in temporal_indicators):
            return True
        
        return False

    def _is_predicate_adjective_pattern(self, main_verb, doc) -> bool:
        """
        Check if this follows a predicate adjective pattern rather than passive voice.
        """
        # Pattern 1: "be" + past participle without agent = often predicate adjective
        aux_verbs = [child for child in main_verb.children if child.dep_ == 'auxpass']
        if aux_verbs:
            aux = aux_verbs[0]
            if aux.lemma_ == 'be' and not self._has_by_phrase_for_token(main_verb, doc):
                # Could be predicate adjective, check semantic context
                return self._suggests_state_rather_than_action(main_verb, doc)
        
        return False

    def _suggests_state_rather_than_action(self, main_verb, doc) -> bool:
        """
        Analyze semantic context to determine if this describes a state vs. an action.
        """
        # Context words that suggest state description
        state_context_words = [
            'when', 'after', 'once', 'if', 'while', 'until', 
            'ready', 'available', 'complete', 'finished'
        ]
        
        sentence_words = [token.lemma_.lower() for token in doc]
        
        # If we're in a temporal/conditional clause, it's often describing a state
        if any(word in sentence_words for word in state_context_words[:6]):  # temporal words
            return True
        
        # If the sentence describes a current state rather than a completed action
        if any(word in sentence_words for word in state_context_words[6:]):  # state words
            return True
        
        return False

    def _analyze_complex_sentence_structure(self, main_verb, doc) -> bool:
        """
        Analyze complex sentence structures to determine true passive voice.
        """
        # For non-root verbs that aren't in adverbial clauses
        # Check if they're in complement clauses or other structures
        
        if main_verb.dep_ in ['ccomp', 'xcomp']:
            # Complement clauses - analyze based on governing verb
            return True  # More likely to be genuine passive in complement clauses
        
        if main_verb.dep_ in ['conj']:
            # Coordinated verbs - check consistency with other conjuncts
            return True  # Assume passive for coordination unless proven otherwise
        
        # Default: if we reach here and haven't ruled it out, be conservative
        return True
    
    def _extract_passive_construction(self, token, doc) -> Optional[Dict[str, Any]]:
        """Extract details of a passive construction."""
        construction = {
            'type': 'spacy_passive',
            'tokens': [token],
            'main_verb': None,
            'auxiliary': None
        }
        
        # Find the main verb and auxiliary
        if token.dep_ == 'auxpass':
            construction['auxiliary'] = token
            # Find the main verb this auxiliary modifies
            construction['main_verb'] = token.head
            construction['tokens'].append(token.head)
        elif token.dep_ == 'nsubjpass':
            # This is the passive subject, find the verb
            construction['main_verb'] = token.head
            construction['tokens'].append(token.head)
        
        return construction
    
    def _find_past_participle(self, aux_token, doc) -> Optional[Any]:
        """Find past participle following auxiliary verb."""
        # Look for past participle in children or nearby tokens
        for child in aux_token.children:
            if child.tag_ == 'VBN':  # Past participle
                return child
        
        # Look at next few tokens
        for i in range(aux_token.i + 1, min(aux_token.i + 4, len(doc))):
            if doc[i].tag_ == 'VBN':
                return doc[i]
        
        return None
    
    def _is_missing_actor(self, construction: Dict[str, Any], doc, context: AmbiguityContext) -> bool:
        """Check if the passive construction lacks a clear actor."""
        # Check for explicit "by" phrases (clear actor present)
        if self._has_by_phrase(construction, doc):
            return False
        
        # Check for clear actor in the sentence
        if self._has_clear_actor_in_sentence(doc):
            return False
        
        # Check for clear actor in context
        if self._has_clear_actor_in_context(context):
            return False
        
        # Check if this is a technical context where actor is important
        if self._is_technical_context(construction, doc):
            return True
        
        # Check confidence based on linguistic patterns
        confidence = self._calculate_confidence(construction, doc, context)
        return confidence >= self.confidence_threshold
    
    def _has_by_phrase(self, construction: Dict[str, Any], doc) -> bool:
        """Check if construction has explicit 'by' phrase indicating actor."""
        for token in doc:
            if token.lemma_ == 'by' and token.pos_ == 'ADP':
                # Check if this 'by' is connected to our passive construction
                if self._is_connected_to_construction(token, construction):
                    return True
        return False
    
    def _has_clear_actor_in_sentence(self, doc) -> bool:
        """Check if sentence has a clear actor."""
        for token in doc:
            if token.lemma_.lower() in self.clear_actors:
                # Check if this token is in a subject position
                if token.dep_ in ['nsubj', 'nsubjpass']:
                    return True
        return False
    
    def _has_clear_actor_in_context(self, context: AmbiguityContext) -> bool:
        """Check if clear actor is established in context."""
        # Check preceding sentences for actor establishment
        if context.preceding_sentences:
            for sentence in context.preceding_sentences:
                if any(actor in sentence.lower() for actor in self.clear_actors):
                    return True
        
        # Check paragraph context
        if context.paragraph_context:
            if any(actor in context.paragraph_context.lower() for actor in self.clear_actors):
                return True
        
        return False
    
    def _is_technical_context(self, construction: Dict[str, Any], doc) -> bool:
        """Check if this is a technical context where actor is important."""
        # Check if the main verb is technical
        main_verb = construction.get('main_verb')
        if main_verb and main_verb.lemma_.lower() in self.technical_contexts:
            return True
        
        # Check if past participle is technical
        past_participle = construction.get('past_participle')
        if past_participle and past_participle.lemma_.lower() in self.technical_contexts:
            return True
        
        return False
    
    def _is_connected_to_construction(self, by_token, construction: Dict[str, Any]) -> bool:
        """Check if 'by' token is connected to the passive construction."""
        construction_tokens = construction.get('tokens', [])
        
        # Simple heuristic: 'by' should be close to construction tokens
        for token in construction_tokens:
            if abs(by_token.i - token.i) <= 3:
                return True
        
        return False
    
    def _calculate_confidence(self, construction: Dict[str, Any], doc, context: AmbiguityContext) -> float:
        """Calculate confidence score for missing actor detection."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for technical contexts
        if self._is_technical_context(construction, doc):
            confidence += 0.2
        
        # Increase confidence for imperative-style sentences
        if self._is_imperative_style(doc):
            confidence += 0.15
        
        # Increase confidence for short, unclear sentences
        if len(doc) < 8:
            confidence += 0.1
        
        # Decrease confidence if there's context suggesting actor
        if self._has_implicit_actor_clues(doc, context):
            confidence -= 0.2
        
        return min(1.0, max(0.0, confidence))
    
    def _is_imperative_style(self, doc) -> bool:
        """Check if sentence appears to be giving instructions."""
        # Look for imperative patterns
        imperative_indicators = {'configure', 'set', 'create', 'install', 'run', 'execute'}
        
        for token in doc:
            if token.lemma_.lower() in imperative_indicators:
                return True
        
        return False
    
    def _has_implicit_actor_clues(self, doc, context: AmbiguityContext) -> bool:
        """Check for implicit clues about the actor."""
        # Check for pronouns that might refer to established actors
        pronouns = {'it', 'this', 'that', 'they'}
        
        for token in doc:
            if token.lemma_.lower() in pronouns:
                return True
        
        # Check for possessive forms that might indicate actor
        for token in doc:
            if token.pos_ == 'PRON' and 'Poss=Yes' in str(token.morph):
                return True
        
        return False
    
    def _create_detection(self, construction: Dict[str, Any], doc, context: AmbiguityContext) -> Optional[AmbiguityDetection]:
        """Create ambiguity detection for missing actor."""
        try:
            # Extract evidence
            tokens = [token.text for token in construction.get('tokens', [])]
            linguistic_pattern = f"passive_voice_{construction.get('type', 'unknown')}"
            
            # CRITICAL: Calculate span for consolidation
            span_start = None
            span_end = None
            flagged_text = ""
            
            construction_tokens = construction.get('tokens', [])
            if construction_tokens:
                # Use the main verb or first token for span calculation
                main_token = construction.get('main_verb') or construction_tokens[0]
                if hasattr(main_token, 'idx'):
                    span_start = main_token.idx
                    span_end = span_start + len(main_token.text)
                    flagged_text = main_token.text
            
            # Calculate confidence
            confidence = self._calculate_confidence(construction, doc, context)
            
            # Create evidence
            evidence = AmbiguityEvidence(
                tokens=tokens,
                linguistic_pattern=linguistic_pattern,
                confidence=confidence,
                spacy_features={
                    'construction_type': construction.get('type'),
                    'main_verb': getattr(construction.get('main_verb'), 'lemma_', None),
                    'auxiliary': getattr(construction.get('auxiliary'), 'lemma_', None)
                }
            )
            
            # Determine resolution strategies
            resolution_strategies = [
                ResolutionStrategy.IDENTIFY_ACTOR,
                ResolutionStrategy.RESTRUCTURE_SENTENCE
            ]
            
            # Generate AI instructions
            ai_instructions = self._generate_ai_instructions(construction, doc, context)
            
            # Create detection with span information
            detection = AmbiguityDetection(
                ambiguity_type=AmbiguityType.MISSING_ACTOR,
                category=self.config.get_category(AmbiguityType.MISSING_ACTOR),
                severity=self.config.get_severity(AmbiguityType.MISSING_ACTOR),
                context=context,
                evidence=evidence,
                resolution_strategies=resolution_strategies,
                ai_instructions=ai_instructions,
                examples=self._generate_examples(construction, doc),
                span=(span_start, span_end) if span_start is not None else None,  # CRITICAL: Include span
                flagged_text=flagged_text if flagged_text else None               # CRITICAL: Include flagged text
            )
            
            return detection
            
        except Exception as e:
            print(f"Error creating missing actor detection: {e}")
            return None
    
    def _generate_ai_instructions(self, construction: Dict[str, Any], doc, context: AmbiguityContext) -> List[str]:
        """Generate specific AI instructions for resolving missing actor."""
        instructions = []
        
        # Base instruction
        instructions.append(
            "This sentence uses passive voice without specifying who or what performs the action. "
            "You MUST identify and specify the actor."
        )
        
        # Context-specific instructions
        if self._is_technical_context(construction, doc):
            instructions.append(
                "Since this is a technical context, clearly specify whether the system, "
                "user, administrator, or other entity performs the action."
            )
        
        if self._is_imperative_style(doc):
            instructions.append(
                "This appears to be an instruction. Rewrite using imperative mood "
                "('Configure the system' rather than 'The system is configured')."
            )
        
        # Specific examples based on main verb
        main_verb = construction.get('main_verb')
        if main_verb:
            verb_lemma = main_verb.lemma_.lower()
            if verb_lemma in self.technical_contexts:
                instructions.append(
                    f"Example: Instead of 'This is {verb_lemma}d', write 'The system {verb_lemma}s this' "
                    f"or 'You {verb_lemma} this'."
                )
        
        return instructions
    
    def _generate_examples(self, construction: Dict[str, Any], doc) -> List[str]:
        """Generate examples for resolving missing actor."""
        examples = []
        
        # Get the main verb for examples
        main_verb = construction.get('main_verb')
        if main_verb:
            verb_lemma = main_verb.lemma_.lower()
            
            # Generate before/after examples
            if verb_lemma in self.technical_contexts:
                examples.extend([
                    f"BEFORE: This is {verb_lemma}d.",
                    f"AFTER: The system {verb_lemma}s this.",
                    f"AFTER: You {verb_lemma} this."
                ])
        
        # General examples
        if not examples:
            examples.extend([
                "BEFORE: This is to be generated.",
                "AFTER: The system generates this.",
                "AFTER: You generate this."
            ])
        
        return examples 