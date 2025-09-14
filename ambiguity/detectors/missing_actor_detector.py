"""
Missing Actor Detector

Detects passive voice sentences without clear actors, creating ambiguity
about who or what performs the action.
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

class ContextType:
    """Context types for passive voice usage."""
    DESCRIPTIVE = "descriptive"
    INSTRUCTIONAL = "instructional"
    UNCERTAIN = "uncertain"

class PassiveConstruction:
    """Lightweight passive construction representation for ambiguity detection."""
    def __init__(self, main_verb=None, auxiliary=None, passive_subject=None, 
                 has_by_phrase=False, has_clear_actor=False, context_type=None,
                 span_start=None, span_end=None, flagged_text=None, construction_type=None):
        self.main_verb = main_verb
        self.auxiliary = auxiliary
        self.passive_subject = passive_subject
        self.has_by_phrase = has_by_phrase
        self.has_clear_actor = has_clear_actor
        self.context_type = context_type
        self.span_start = span_start
        self.span_end = span_end
        self.flagged_text = flagged_text
        self.construction_type = construction_type

class LightweightPassiveAnalyzer:
    """Lightweight passive voice analyzer specifically for ambiguity detection."""
    
    def find_passive_constructions(self, doc):
        """Find passive constructions in the document for ambiguity analysis."""
        constructions = []
        seen_constructions = set()  # Track unique constructions to prevent duplicates
        
        # Look for passive voice patterns in the sentence
        for token in doc:
            # Pattern 1: Auxiliary passive (is/was + past participle)
            if token.dep_ == 'auxpass':
                # Find the past participle
                main_verb = None
                for child in token.head.children:
                    if child.tag_ == 'VBN':
                        main_verb = child
                        break
                
                if main_verb:
                    # Create unique identifier for this construction
                    construction_id = (main_verb.idx, token.idx, main_verb.lemma_, token.lemma_)
                    if construction_id not in seen_constructions:
                        construction = self._create_construction(token, main_verb, doc)
                        if construction:
                            constructions.append(construction)
                            seen_constructions.add(construction_id)
            
            # Pattern 2: "be" + past participle (broader detection)
            elif (token.lemma_ == 'be' and 
                  any(child.tag_ == 'VBN' for child in token.children)):
                
                for child in token.children:
                    if child.tag_ == 'VBN':
                        # Create unique identifier for this construction
                        construction_id = (child.idx, token.idx, child.lemma_, token.lemma_)
                        if construction_id not in seen_constructions:
                            construction = self._create_construction(token, child, doc)
                            if construction:
                                constructions.append(construction)
                                seen_constructions.add(construction_id)
            
            # Pattern 3: Direct past participle with auxiliary (like "This is clicked")
            elif token.tag_ == 'VBN':
                # Look for auxiliary in the sentence
                auxiliary = None
                for t in doc:
                    if (t.lemma_ in ['be', 'get', 'become'] and 
                        t.head == token or token.head == t):
                        auxiliary = t
                        break
                
                if auxiliary:
                    # Create unique identifier for this construction
                    construction_id = (token.idx, auxiliary.idx, token.lemma_, auxiliary.lemma_)
                    if construction_id not in seen_constructions:
                        construction = self._create_construction(auxiliary, token, doc)
                        if construction:
                            constructions.append(construction)
                            seen_constructions.add(construction_id)
        
        return constructions
    
    def _create_construction(self, auxiliary, main_verb, doc):
        """Create a PassiveConstruction object."""
        # Check for by-phrase
        has_by_phrase = any(
            child.lemma_ == 'by' and child.dep_ == 'agent'
            for child in main_verb.children
        )
        
        # Check for clear actor (by-phrase or explicit agent)
        has_clear_actor = has_by_phrase or any(
            child.dep_ == 'agent' for child in main_verb.children
        )
        
        # Determine context type
        context_type = self._determine_context_type(doc.text)
        
        return PassiveConstruction(
            main_verb=main_verb,
            auxiliary=auxiliary,
            passive_subject=None,
            has_by_phrase=has_by_phrase,
            has_clear_actor=has_clear_actor,
            context_type=context_type,
            span_start=main_verb.idx,
            span_end=main_verb.idx + len(main_verb.text),
            flagged_text=main_verb.text,
            construction_type="passive"
        )
    
    def _determine_context_type(self, text):
        """Determine the context type of the text."""
        text_lower = text.lower()
        
        # Instructional indicators
        if any(word in text_lower for word in ['click', 'select', 'choose', 'configure', 'set']):
            return ContextType.INSTRUCTIONAL
        
        # Descriptive indicators
        if any(word in text_lower for word in ['is', 'are', 'was', 'were', 'describes', 'represents']):
            return ContextType.DESCRIPTIVE
            
        return ContextType.UNCERTAIN


class MissingActorDetector(AmbiguityDetector):
    """
    Detects passive voice constructions without clear actors using self-contained analysis.
    
    This detector is fully compatible with Level 2 Enhanced Validation, Evidence-Based 
    Rule Development, and Universal Confidence Threshold architecture. It provides
    sophisticated 7-factor evidence scoring for ambiguous actor detection.
    
    Architecture compliance:
    - confidence.md: Universal threshold (≥0.35), normalized confidence
    - evidence_based_rule_development.md: Multi-factor evidence assessment  
    - level_2_implementation.adoc: Enhanced validation integration
    """
    
    def __init__(self, config: AmbiguityConfig, parent_rule=None):
        super().__init__(config, parent_rule)
        
        # Initialize self-contained lightweight passive voice analyzer for ambiguity detection
        self.passive_analyzer = LightweightPassiveAnalyzer()
            
        self.confidence_threshold = 0.55  # Adjusted for evidence-based detection
        
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
        Detect missing actors in passive voice sentences using self-contained analysis.
        
        Args:
            context: Sentence context for analysis
            nlp: SpaCy nlp object
            
        Returns:
            List of ambiguity detections for missing actors
        """
        if not self.enabled:
            return []
        
        detections = []
        
        try:
            # Parse the sentence
            doc = nlp(context.sentence)
            
            # Use self-contained analyzer to find passive constructions
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
        Enhanced Level 2 confidence calculation for missing actor detection.
        
        Implements evidence-based rule development with:
        - Multi-factor evidence assessment
        - Context-aware domain validation 
        - Universal threshold compliance (≥0.35)
        - Specific criteria for actor identification vs general passive voice
        """
        # Evidence-based base confidence (Level 2 enhancement)
        confidence = 0.50  # Starting point for missing actor scenarios
        
        # EVIDENCE FACTOR 1: Technical Context Assessment (High Impact)
        if self._is_technical_context_for_actor(construction, doc):
            confidence += 0.25  # Strong evidence - technical docs need clear actors
        
        # EVIDENCE FACTOR 2: Imperative Context (Critical for UI/Instructions)
        if self._is_imperative_needing_actor(doc):
            confidence += 0.20  # High evidence - imperative without actor is problematic
        
        # EVIDENCE FACTOR 3: Sentence Complexity Analysis (Length vs Clarity)
        sentence_complexity_modifier = 0.0
        if len(doc) < 6:  # Very short sentences like "This is clicked"
            sentence_complexity_modifier += 0.15  # High evidence - brevity increases ambiguity
        elif len(doc) < 10:  # Medium length
            sentence_complexity_modifier += 0.08  # Medium evidence
        
        # EVIDENCE FACTOR 4: Context Type Specificity (Domain Knowledge)
        context_type_modifier = 0.0
        if construction.context_type == ContextType.INSTRUCTIONAL:
            context_type_modifier += 0.18  # Strong evidence - instructions need clear actors
        elif construction.context_type == ContextType.DESCRIPTIVE:
            context_type_modifier -= 0.05  # Weak evidence - descriptions more forgiving
        
        # EVIDENCE FACTOR 5: Implicit Actor Analysis (Contextual Clues)
        implicit_actor_modifier = 0.0
        if self._has_implicit_actor_clues(doc, context):
            implicit_actor_modifier -= 0.15  # Counter-evidence - implicit actors reduce concern
        
        # EVIDENCE FACTOR 6: Linguistic Pattern Strength
        linguistic_evidence = 0.0
        sentence_text = doc.text.lower()
        
        # Strong passive indicators without clear subjects
        strong_passive_patterns = ['this is', 'that is', 'it is', 'they are', 'these are']
        if any(pattern in sentence_text for pattern in strong_passive_patterns):
            linguistic_evidence += 0.12  # Strong linguistic evidence
        
        # Generic subject pronouns (ambiguity red flags)
        if sentence_text.startswith(('this ', 'that ', 'it ')):
            linguistic_evidence += 0.08  # Medium linguistic evidence
        
        # EVIDENCE FACTOR 7: Domain-Specific Validation (Context Awareness)
        domain_modifier = 0.0
        if context and hasattr(context, 'document_context'):
            doc_context = context.document_context or {}
            domain = doc_context.get('domain', '')
            
            if domain == 'ui':  # User interface documentation
                domain_modifier += 0.10  # Clear actors critical for UI
            elif domain == 'api':  # API documentation  
                domain_modifier += 0.05  # Some ambiguity acceptable in API docs
            elif domain == 'legal':  # Legal documentation
                domain_modifier -= 0.05  # Passive voice common in legal text
        
        # EVIDENCE AGGREGATION (Level 2 Multi-Factor Assessment)
        final_confidence = (confidence + 
                          sentence_complexity_modifier + 
                          context_type_modifier + 
                          implicit_actor_modifier + 
                          linguistic_evidence + 
                          domain_modifier)
        
        # UNIVERSAL THRESHOLD COMPLIANCE (≥0.35 minimum)
        # Cap at 0.95 to leave room for uncertainty
        return min(0.95, max(0.35, final_confidence))
    
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
            
            linguistic_pattern = f"missing_actor_{construction.construction_type}"
            
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
                    'construction_type': construction.construction_type,
                    'main_verb': construction.main_verb.lemma_ if construction.main_verb else None,
                    'auxiliary': construction.auxiliary.lemma_ if construction.auxiliary else None,
                    'context_type': construction.context_type,
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