"""
Missing Actor Detector (Refactored to use Shared Passive Voice Analyzer)

Detects passive voice sentences without clear actors, creating ambiguity
about who or what performs the action.

This refactored version uses the centralized PassiveVoiceAnalyzer to eliminate
code duplication while focusing specifically on missing actor detection logic.
"""

from typing import List, Dict, Any, Optional, Set
import sys
import os

# Add the rules directory to the path for importing the shared analyzer
sys.path.append(os.path.join(os.path.dirname(__file__), '../../rules/language_and_grammar'))

from ..base_ambiguity_rule import AmbiguityDetector
from ..types import (
    AmbiguityType, AmbiguityCategory, AmbiguitySeverity,
    AmbiguityContext, AmbiguityEvidence, AmbiguityDetection,
    ResolutionStrategy, AmbiguityConfig
)

try:
    from passive_voice_analyzer import PassiveVoiceAnalyzer, ContextType, PassiveConstruction
except ImportError:
    # Fallback import path
    try:
        from rules.language_and_grammar.passive_voice_analyzer import PassiveVoiceAnalyzer, ContextType, PassiveConstruction
    except ImportError:
        PassiveVoiceAnalyzer = None
        ContextType = None
        PassiveConstruction = None


class MissingActorDetector(AmbiguityDetector):
    """
    Detects passive voice constructions without clear actors using shared analysis.
    
    This detector focuses specifically on identifying missing actors in passive
    constructions detected by the shared PassiveVoiceAnalyzer.
    """
    
    def __init__(self, config: AmbiguityConfig, parent_rule=None):
        super().__init__(config, parent_rule)
        
        # Initialize shared passive voice analyzer
        if PassiveVoiceAnalyzer:
            self.passive_analyzer = PassiveVoiceAnalyzer()
        else:
            self.passive_analyzer = None
            
        self.confidence_threshold = 0.7
        
        # Clear actors that, when present, reduce ambiguity
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
        Detect missing actors in passive voice sentences using shared analyzer.
        
        Args:
            context: Sentence context for analysis
            nlp: SpaCy nlp object
            
        Returns:
            List of ambiguity detections for missing actors
        """
        if not self.enabled or not self.passive_analyzer:
            return []
        
        detections = []
        
        try:
            # Parse the sentence
            doc = nlp(context.sentence)
            
            # Use shared analyzer to find passive constructions
            passive_constructions = self.passive_analyzer.find_passive_constructions(doc)
            
            # Focus on missing actor analysis for each passive construction
            for construction in passive_constructions:
                if self._is_missing_actor(construction, doc, context):
                    detection = self._create_detection(construction, doc, context)
                    if detection:
                        detections.append(detection)
        
        except Exception as e:
            # Log error but don't fail
            print(f"Error in missing actor detection: {e}")
        
        return detections
    
    def _is_missing_actor(self, construction: PassiveConstruction, doc, context: AmbiguityContext) -> bool:
        """
        Check if the passive construction lacks a clear actor.
        This is the core logic that was NOT duplicated - it's unique to missing actor detection.
        """
        
        # If construction already has clear actor (detected by shared analyzer), not missing
        if construction.has_clear_actor:
            return False
        
        # If construction has by-phrase, actor is explicit
        if construction.has_by_phrase:
            return False
        
        # Check for clear actor in the sentence (our specific logic)
        if self._has_clear_actor_in_sentence(doc):
            return False
        
        # Check for clear actor in context (our specific logic)
        if self._has_clear_actor_in_context(context):
            return False
        
        # Check if this is a technical context where actor is important (our specific logic)
        if self._is_technical_context_for_actor(construction, doc):
            return True
        
        # Check confidence based on our specific missing actor patterns
        confidence = self._calculate_missing_actor_confidence(construction, doc, context)
        return confidence >= self.confidence_threshold
    
    def _has_clear_actor_in_sentence(self, doc) -> bool:
        """Check if sentence has a clear actor using our specific actor list."""
        for token in doc:
            if token.lemma_.lower() in self.clear_actors:
                # Check if this token is in a subject position
                if token.dep_ in ['nsubj', 'nsubjpass']:
                    return True
        return False
    
    def _has_clear_actor_in_context(self, context: AmbiguityContext) -> bool:
        """Check if clear actor is established in preceding context."""
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
    
    def _is_technical_context_for_actor(self, construction: PassiveConstruction, doc) -> bool:
        """
        Check if this is a technical context where missing actor is problematic.
        Uses our specific technical context criteria.
        """
        # Check if the main verb is in our technical contexts
        if construction.main_verb and construction.main_verb.lemma_.lower() in self.technical_contexts:
            return True
        
        # Check for technical sentence patterns that need clear actors
        technical_sentence_patterns = {
            'must be', 'should be', 'needs to be', 'is required to be'
        }
        sentence_text = doc.text.lower()
        if any(pattern in sentence_text for pattern in technical_sentence_patterns):
            return True
        
        return False
    
    def _calculate_missing_actor_confidence(self, construction: PassiveConstruction, doc, context: AmbiguityContext) -> float:
        """
        Calculate confidence score specifically for missing actor detection.
        This uses criteria specific to actor identification, not general passive voice.
        """
        confidence = 0.5  # Base confidence
        
        # Increase confidence for technical contexts (our specific criteria)
        if self._is_technical_context_for_actor(construction, doc):
            confidence += 0.2
        
        # Increase confidence for imperative-style sentences needing clear actors
        if self._is_imperative_needing_actor(doc):
            confidence += 0.15
        
        # Increase confidence for short, unclear sentences
        if len(doc) < 8:
            confidence += 0.1
        
        # Decrease confidence if there are implicit actor clues
        if self._has_implicit_actor_clues(doc, context):
            confidence -= 0.2
        
        # Increase confidence if in instructional context (needs clear actors)
        if construction.context_type == ContextType.INSTRUCTIONAL:
            confidence += 0.15
        
        # Decrease confidence if in descriptive context (actors less critical)
        if construction.context_type == ContextType.DESCRIPTIVE:
            confidence -= 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def _is_imperative_needing_actor(self, doc) -> bool:
        """Check if sentence gives instructions but lacks clear actor."""
        # Look for imperative patterns that typically need actors
        imperative_needing_actors = {
            'configure', 'set', 'create', 'install', 'run', 'execute',
            'update', 'modify', 'delete', 'generate'
        }
        
        for token in doc:
            if token.lemma_.lower() in imperative_needing_actors:
                return True
        
        return False
    
    def _has_implicit_actor_clues(self, doc, context: AmbiguityContext) -> bool:
        """Check for implicit clues about the actor that reduce ambiguity."""
        # Check for pronouns that might refer to established actors
        referential_pronouns = {'it', 'this', 'that', 'they'}
        
        for token in doc:
            if token.lemma_.lower() in referential_pronouns:
                return True
        
        # Check for possessive forms that might indicate actor
        for token in doc:
            if token.pos_ == 'PRON' and 'Poss=Yes' in str(token.morph):
                return True
        
        # Check for institutional context (where "the system" is implied)
        institutional_indicators = {'automatically', 'by default', 'typically', 'normally'}
        sentence_words = [token.lemma_.lower() for token in doc]
        if any(indicator in sentence_words for indicator in institutional_indicators):
            return True
        
        return False
    
    def _create_detection(self, construction: PassiveConstruction, doc, context: AmbiguityContext) -> Optional[AmbiguityDetection]:
        """Create ambiguity detection for missing actor using shared construction data."""
        try:
            # Extract evidence using shared construction data
            tokens = [construction.main_verb.text]
            if construction.auxiliary:
                tokens.append(construction.auxiliary.text)
            if construction.passive_subject:
                tokens.append(construction.passive_subject.text)
            
            linguistic_pattern = f"missing_actor_{construction.construction_type.value}"
            
            # Use construction's span information (from shared analyzer)
            span_start = construction.span_start
            span_end = construction.span_end
            flagged_text = construction.flagged_text
            
            # Calculate our specific missing actor confidence
            confidence = self._calculate_missing_actor_confidence(construction, doc, context)
            
            # Create evidence
            evidence = AmbiguityEvidence(
                tokens=tokens,
                linguistic_pattern=linguistic_pattern,
                confidence=confidence,
                spacy_features={
                    'construction_type': construction.construction_type.value,
                    'main_verb': construction.main_verb.lemma_ if construction.main_verb else None,
                    'auxiliary': construction.auxiliary.lemma_ if construction.auxiliary else None,
                    'context_type': construction.context_type.value if construction.context_type else None,
                    'has_by_phrase': construction.has_by_phrase,
                    'technical_context': self._is_technical_context_for_actor(construction, doc)
                }
            )
            
            # Determine resolution strategies specific to missing actors
            resolution_strategies = [
                ResolutionStrategy.IDENTIFY_ACTOR,
                ResolutionStrategy.RESTRUCTURE_SENTENCE
            ]
            
            # Add context-specific strategies
            if construction.context_type == ContextType.INSTRUCTIONAL:
                resolution_strategies.append(ResolutionStrategy.SPECIFY_REFERENCE)
            
            # Generate AI instructions specific to missing actors
            ai_instructions = self._generate_missing_actor_instructions(construction, doc, context)
            
            # Create detection with proper span information
            detection = AmbiguityDetection(
                ambiguity_type=AmbiguityType.MISSING_ACTOR,
                category=self.config.get_category(AmbiguityType.MISSING_ACTOR),
                severity=self.config.get_severity(AmbiguityType.MISSING_ACTOR),
                context=context,
                evidence=evidence,
                resolution_strategies=resolution_strategies,
                ai_instructions=ai_instructions,
                examples=self._generate_missing_actor_examples(construction, doc),
                span=(span_start, span_end) if span_start is not None else None,
                flagged_text=flagged_text if flagged_text else None
            )
            
            return detection
            
        except Exception as e:
            print(f"Error creating missing actor detection: {e}")
            return None
    
    def _generate_missing_actor_instructions(self, construction: PassiveConstruction, doc, context: AmbiguityContext) -> List[str]:
        """Generate specific AI instructions for resolving missing actor (not general passive voice)."""
        instructions = []
        
        # Base instruction specific to missing actors
        instructions.append(
            "This sentence uses passive voice without specifying who or what performs the action. "
            "You MUST identify and specify the actor to eliminate ambiguity."
        )
        
        # Context-specific instructions for missing actors
        if construction.context_type == ContextType.INSTRUCTIONAL:
            instructions.append(
                "Since this is an instruction, clearly specify whether the user, administrator, "
                "or system should perform the action. Use imperative mood when addressing the user."
            )
        elif construction.context_type == ContextType.DESCRIPTIVE:
            instructions.append(
                "Since this describes system behavior, specify which component, service, "
                "or process performs the action (e.g., 'The system generates...', 'The API provides...')."
            )
        
        # Technical context instructions
        if self._is_technical_context_for_actor(construction, doc):
            instructions.append(
                "In technical documentation, ambiguous actors can lead to implementation errors. "
                "Be specific about whether it's automated (system) or manual (user) action."
            )
        
        # Specific verb-based examples
        if construction.main_verb:
            verb_lemma = construction.main_verb.lemma_.lower()
            if verb_lemma in self.technical_contexts:
                instructions.append(
                    f"Example: Instead of 'This is {verb_lemma}d', write 'The system {verb_lemma}s this' "
                    f"or 'You {verb_lemma} this' (depending on who actually performs the action)."
                )
        
        return instructions
    
    def _generate_missing_actor_examples(self, construction: PassiveConstruction, doc) -> List[str]:
        """Generate examples specific to missing actor resolution (not general passive voice)."""
        examples = []
        
        # Get the main verb for examples
        if construction.main_verb:
            verb_lemma = construction.main_verb.lemma_.lower()
            
            # Generate before/after examples focused on actor identification
            if verb_lemma in self.technical_contexts:
                examples.extend([
                    f"BEFORE: This is {verb_lemma}d. (WHO does the {verb_lemma}ing?)",
                    f"AFTER: The system {verb_lemma}s this. (system = actor)",
                    f"AFTER: You {verb_lemma} this. (user = actor)"
                ])
            else:
                examples.extend([
                    f"BEFORE: The file is {verb_lemma}d. (WHO {verb_lemma}s it?)",
                    f"AFTER: The application {verb_lemma}s the file. (application = actor)",
                    f"AFTER: The user {verb_lemma}s the file. (user = actor)"
                ])
        
        # General missing actor examples
        if not examples:
            examples.extend([
                "BEFORE: This is to be generated. (WHO generates it?)",
                "AFTER: The system generates this. (system = actor)",
                "AFTER: You generate this. (user = actor)",
                "Focus on: WHO or WHAT performs the action?"
            ])
        
        return examples 