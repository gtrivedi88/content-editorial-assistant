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
    
    def __init__(self, config: AmbiguityConfig):
        super().__init__(config)
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
        """Find passive voice constructions in the sentence."""
        constructions = []
        
        for token in doc:
            # Method 1: SpaCy dependency parsing for passive
            if token.dep_ == 'auxpass' or token.dep_ == 'nsubjpass':
                # Found passive construction
                construction = self._extract_passive_construction(token, doc)
                if construction:
                    constructions.append(construction)
            
            # Method 2: Pattern matching for "to be + past participle"
            elif (token.lemma_ in self.passive_indicators and 
                  token.pos_ in ['AUX', 'VERB']):
                # Check if followed by past participle
                past_participle = self._find_past_participle(token, doc)
                if past_participle:
                    construction = {
                        'auxiliary': token,
                        'past_participle': past_participle,
                        'type': 'be_passive',
                        'tokens': [token, past_participle]
                    }
                    constructions.append(construction)
        
        return constructions
    
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
            
            # Create detection
            detection = AmbiguityDetection(
                ambiguity_type=AmbiguityType.MISSING_ACTOR,
                category=self.config.get_category(AmbiguityType.MISSING_ACTOR),
                severity=self.config.get_severity(AmbiguityType.MISSING_ACTOR),
                context=context,
                evidence=evidence,
                resolution_strategies=resolution_strategies,
                ai_instructions=ai_instructions,
                examples=self._generate_examples(construction, doc)
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