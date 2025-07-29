"""
Shared Passive Voice Analysis Module

Centralizes passive voice detection logic to eliminate duplication between
verbs_rule.py and missing_actor_detector.py while maintaining sophisticated
linguistic analysis using spaCy features.

This module provides production-quality passive voice detection with:
- spaCy-based morphological analysis
- Sophisticated validation to eliminate false positives
- Context-aware classification (descriptive vs instructional)
- Extensible architecture for future enhancements
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from spacy.tokens import Doc, Token
except ImportError:
    Doc = None
    Token = None


class PassiveVoiceType(Enum):
    """Types of passive voice constructions."""
    SPACY_DETECTED = "spacy_detected"      # Detected by spaCy dependency parsing
    PATTERN_MATCHED = "pattern_matched"    # Detected by pattern matching
    MODAL_PASSIVE = "modal_passive"        # Modal + passive construction


class ContextType(Enum):
    """Context types for passive voice usage."""
    DESCRIPTIVE = "descriptive"            # Describes system characteristics
    INSTRUCTIONAL = "instructional"        # Gives instructions/requirements
    UNCERTAIN = "uncertain"                # Ambiguous context


@dataclass
class PassiveConstruction:
    """Represents a passive voice construction with full linguistic analysis."""
    
    # Core tokens
    main_verb: Token                       # Past participle (VBN)
    auxiliary: Optional[Token] = None      # Auxiliary verb (be, etc.)
    passive_subject: Optional[Token] = None # nsubjpass token
    
    # Construction details
    construction_type: PassiveVoiceType = PassiveVoiceType.SPACY_DETECTED
    all_tokens: List[Token] = None
    
    # Linguistic analysis
    has_by_phrase: bool = False
    has_clear_actor: bool = False
    context_type: ContextType = ContextType.UNCERTAIN
    confidence: float = 0.0
    
    # Span information for error reporting
    span_start: Optional[int] = None
    span_end: Optional[int] = None
    flagged_text: str = ""
    
    def __post_init__(self):
        if self.all_tokens is None:
            self.all_tokens = []
        if self.span_start is None and self.main_verb:
            self.span_start = self.main_verb.idx
            self.span_end = self.span_start + len(self.main_verb.text)
            self.flagged_text = self.main_verb.text


class PassiveVoiceAnalyzer:
    """
    Production-quality passive voice analyzer using spaCy linguistic features.
    
    Provides centralized passive voice detection and analysis to eliminate
    duplication between grammar rules and ambiguity detectors.
    """
    
    def __init__(self):
        # Linguistic feature sets for semantic categorization
        self.state_oriented_verbs = {
            'done', 'finished', 'ready', 'prepared', 'set', 'fixed', 'broken', 
            'closed', 'open', 'available', 'busy', 'free', 'connected', 'offline'
        }
        
        self.capability_modals = {'can', 'may', 'could', 'might'}
        self.requirement_modals = {'must', 'should', 'need', 'have to', 'ought'}
        
        self.technical_entities = {
            'system', 'platform', 'api', 'service', 'application', 'software', 
            'tool', 'framework', 'component', 'module', 'database', 'server', 
            'network', 'interface', 'feature', 'functionality', 'capability',
            'product', 'solution', 'package', 'library', 'plugin', 'extension'
        }
        
        self.characteristic_verbs = {
            'configure', 'design', 'build', 'implement', 'create', 'develop',
            'provide', 'support', 'enable', 'offer', 'document', 'describe',
            'guarantee', 'optimize', 'secure', 'protect', 'validate'
        }
        
        self.imperative_indicators = {
            'must', 'should', 'need', 'require', 'ensure', 'make sure'
        }
    
    def find_passive_constructions(self, doc: Doc) -> List[PassiveConstruction]:
        """
        Find all valid passive voice constructions in a document.
        
        Uses spaCy dependency parsing with sophisticated validation to eliminate
        false positives from predicate adjective constructions.
        """
        constructions = []
        
        for token in doc:
            # Method 1: spaCy dependency-based detection
            if token.dep_ in ('nsubjpass', 'auxpass'):
                construction = self._analyze_spacy_passive(token, doc)
                if construction and self._is_true_passive_voice(construction, doc):
                    constructions.append(construction)
            
            # Method 2: Pattern-based detection for "to be + VBN"
            elif (token.lemma_ in {'be', 'is', 'are', 'was', 'were', 'being', 'been'} 
                  and token.pos_ in ['AUX', 'VERB']):
                construction = self._analyze_pattern_passive(token, doc)
                if construction and self._is_true_passive_voice(construction, doc):
                    constructions.append(construction)
        
        # Post-process to remove duplicates and enhance analysis
        return self._deduplicate_and_enhance(constructions, doc)
    
    def _analyze_spacy_passive(self, token: Token, doc: Doc) -> Optional[PassiveConstruction]:
        """Analyze spaCy-detected passive construction."""
        try:
            if token.dep_ == 'nsubjpass':
                # Passive subject found
                main_verb = token.head
                auxiliary = self._find_auxiliary(main_verb)
                
                return PassiveConstruction(
                    main_verb=main_verb,
                    auxiliary=auxiliary,
                    passive_subject=token,
                    construction_type=PassiveVoiceType.SPACY_DETECTED,
                    all_tokens=[token, main_verb] + ([auxiliary] if auxiliary else [])
                )
            
            elif token.dep_ == 'auxpass':
                # Auxiliary passive found
                main_verb = token.head
                passive_subject = self._find_passive_subject(main_verb, doc)
                
                return PassiveConstruction(
                    main_verb=main_verb,
                    auxiliary=token,
                    passive_subject=passive_subject,
                    construction_type=PassiveVoiceType.SPACY_DETECTED,
                    all_tokens=[token, main_verb] + ([passive_subject] if passive_subject else [])
                )
        
        except Exception:
            pass
        
        return None
    
    def _analyze_pattern_passive(self, aux_token: Token, doc: Doc) -> Optional[PassiveConstruction]:
        """Analyze pattern-matched passive construction."""
        try:
            # Look for past participle following auxiliary
            past_participle = self._find_past_participle_after(aux_token)
            if not past_participle:
                return None
            
            # Find passive subject
            passive_subject = self._find_passive_subject(past_participle, doc)
            
            return PassiveConstruction(
                main_verb=past_participle,
                auxiliary=aux_token,
                passive_subject=passive_subject,
                construction_type=PassiveVoiceType.PATTERN_MATCHED,
                all_tokens=[aux_token, past_participle] + ([passive_subject] if passive_subject else [])
            )
        
        except Exception:
            pass
        
        return None
    
    def _is_true_passive_voice(self, construction: PassiveConstruction, doc: Doc) -> bool:
        """
        Sophisticated validation to distinguish true passive voice from
        predicate adjective constructions that spaCy mislabels.
        """
        main_verb = construction.main_verb
        
        # Must be past participle (VBN) to be passive
        if main_verb.tag_ != 'VBN':
            return False
        
        # Check 1: Explicit agent (by-phrase) = definitely passive
        if self._has_by_phrase(main_verb, doc):
            construction.has_by_phrase = True
            return True
        
        # Check 2: Exclude adverbial clauses (common false positives)
        if main_verb.dep_ == 'advcl':
            return False
        
        # Check 3: State-oriented verbs need stronger evidence
        if main_verb.lemma_ in self.state_oriented_verbs:
            return self._has_strong_passive_evidence(construction, doc)
        
        # Check 4: System functionality descriptions may be legitimate passive
        if self._is_system_functionality_description(construction, doc):
            # Still passive, but mark as descriptive context
            construction.context_type = ContextType.DESCRIPTIVE
            return True
        
        # Check 5: Root verbs with clear passive structure
        if main_verb.dep_ == 'ROOT':
            return not self._is_predicate_adjective_pattern(construction, doc)
        
        # Check 6: Complex sentence structures
        return self._analyze_complex_structure(construction, doc)
    
    def classify_context(self, construction: PassiveConstruction, doc: Doc) -> ContextType:
        """
        Classify whether passive voice appears in descriptive or instructional context.
        This is crucial for generating appropriate suggestions.
        """
        # Priority 1: Requirement modals = instructional
        if any(token.lemma_ in self.requirement_modals and token.pos_ == 'AUX' 
               for token in doc):
            return ContextType.INSTRUCTIONAL
        
        # Priority 2: Imperative indicators = instructional (only for verbs, not nouns)
        if any(token.lemma_.lower() in self.imperative_indicators and token.pos_ in ['AUX', 'VERB'] 
               for token in doc):
            return ContextType.INSTRUCTIONAL
        
        # Descriptive indicators
        if self._has_descriptive_patterns(construction, doc):
            return ContextType.DESCRIPTIVE
        
        return ContextType.UNCERTAIN
    
    def _has_descriptive_patterns(self, construction: PassiveConstruction, doc: Doc) -> bool:
        """Check for patterns indicating descriptive context."""
        
        # Present tense auxiliary = descriptive
        if construction.auxiliary and construction.auxiliary.tag_ in ['VBZ', 'VBP']:
            return True
        
        # Technical entity subjects = often descriptive
        if (construction.passive_subject and 
            construction.passive_subject.text.lower() in self.technical_entities):
            return True
        
        # Capability modals = descriptive
        if any(token.lemma_ in self.capability_modals and token.pos_ == 'AUX' 
               for token in doc):
            return True
        
        # Characteristic verbs = often descriptive
        if construction.main_verb.lemma_ in self.characteristic_verbs:
            return True
        
        return False
    
    def _find_auxiliary(self, main_verb: Token) -> Optional[Token]:
        """Find auxiliary verb for passive construction."""
        for child in main_verb.children:
            if child.dep_ == 'auxpass':
                return child
        return None
    
    def _find_passive_subject(self, main_verb: Token, doc: Doc) -> Optional[Token]:
        """Find passive subject (nsubjpass) for main verb."""
        for token in doc:
            if token.dep_ == 'nsubjpass' and token.head == main_verb:
                return token
        return None
    
    def _find_past_participle_after(self, aux_token: Token) -> Optional[Token]:
        """Find past participle following auxiliary."""
        doc = aux_token.doc
        
        # Check children first
        for child in aux_token.children:
            if child.tag_ == 'VBN':
                return child
        
        # Check following tokens
        for i in range(aux_token.i + 1, min(aux_token.i + 4, len(doc))):
            if doc[i].tag_ == 'VBN':
                return doc[i]
        
        return None
    
    def _has_by_phrase(self, main_verb: Token, doc: Doc) -> bool:
        """Check for explicit agent in by-phrase."""
        for token in doc:
            if (token.lemma_ == 'by' and 
                token.head == main_verb and 
                any(child.dep_ == 'pobj' for child in token.children)):
                return True
        return False
    
    def _has_strong_passive_evidence(self, construction: PassiveConstruction, doc: Doc) -> bool:
        """Check for strong evidence of passive voice for ambiguous cases."""
        
        # Evidence 1: By-phrase
        if construction.has_by_phrase:
            return True
        
        # Evidence 2: Past tense auxiliary suggests completed action
        if (construction.auxiliary and 
            construction.auxiliary.lemma_ in ['was', 'were', 'been']):
            return True
        
        # Evidence 3: Temporal indicators suggest action occurred
        temporal_words = ['yesterday', 'recently', 'just', 'already', 'earlier']
        sentence_words = [token.lemma_.lower() for token in doc]
        if any(word in sentence_words for word in temporal_words):
            return True
        
        return False
    
    def _is_system_functionality_description(self, construction: PassiveConstruction, doc: Doc) -> bool:
        """Check if passive describes system functionality (legitimate descriptive use)."""
        
        # Check for capability modals
        if any(token.lemma_ in self.capability_modals and token.pos_ == 'AUX' 
               for token in doc):
            return True
        
        # Check for technical subject + characteristic verb
        if (construction.passive_subject and 
            construction.passive_subject.text.lower() in self.technical_entities and
            construction.main_verb.lemma_ in self.characteristic_verbs):
            return True
        
        return False
    
    def _is_predicate_adjective_pattern(self, construction: PassiveConstruction, doc: Doc) -> bool:
        """Check if this is predicate adjective rather than passive voice."""
        
        if not construction.auxiliary or construction.auxiliary.lemma_ != 'be':
            return False
        
        # Check semantic context for state description
        state_words = ['when', 'after', 'once', 'ready', 'available', 'complete']
        sentence_words = [token.lemma_.lower() for token in doc]
        
        return any(word in sentence_words for word in state_words)
    
    def _analyze_complex_structure(self, construction: PassiveConstruction, doc: Doc) -> bool:
        """Analyze complex sentence structures for passive voice validation."""
        
        main_verb = construction.main_verb
        
        # Complement clauses likely to be passive
        if main_verb.dep_ in ['ccomp', 'xcomp']:
            return True
        
        # Coordinated structures
        if main_verb.dep_ == 'conj':
            return True
        
        # Default conservative approach
        return True
    
    def _deduplicate_and_enhance(self, constructions: List[PassiveConstruction], doc: Doc) -> List[PassiveConstruction]:
        """Remove duplicates and enhance constructions with full analysis."""
        
        # Simple deduplication by main verb position
        seen_positions = set()
        unique_constructions = []
        
        for construction in constructions:
            pos = construction.main_verb.i
            if pos not in seen_positions:
                seen_positions.add(pos)
                
                # Enhance with full analysis
                construction.context_type = self.classify_context(construction, doc)
                construction.confidence = self._calculate_confidence(construction, doc)
                construction.has_clear_actor = self._has_clear_actor(construction, doc)
                
                unique_constructions.append(construction)
        
        return unique_constructions
    
    def _calculate_confidence(self, construction: PassiveConstruction, doc: Doc) -> float:
        """Calculate confidence score for passive voice detection."""
        confidence = 0.7  # Base confidence
        
        # Strong indicators
        if construction.has_by_phrase:
            confidence += 0.2
        if construction.construction_type == PassiveVoiceType.SPACY_DETECTED:
            confidence += 0.1
        
        # Reduce for ambiguous patterns
        if construction.main_verb.lemma_ in self.state_oriented_verbs:
            confidence -= 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def _has_clear_actor(self, construction: PassiveConstruction, doc: Doc) -> bool:
        """Check if construction has a clear actor."""
        
        # By-phrase provides clear actor
        if construction.has_by_phrase:
            return True
        
        # Check for clear actor words in sentence
        clear_actors = {'system', 'user', 'administrator', 'you', 'we', 'they'}
        sentence_words = [token.lemma_.lower() for token in doc]
        
        return any(actor in sentence_words for actor in clear_actors) 