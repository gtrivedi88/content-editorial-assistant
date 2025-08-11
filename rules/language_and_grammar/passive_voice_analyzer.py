"""
Shared Passive Voice Analysis Module - Pure Linguistic Approach
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
    
    # Evidence-based scoring
    evidence_score: float = 0.0
    
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
            'product', 'solution', 'package', 'library', 'plugin', 'extension',
            # Configuration and data entities  
            'parameter', 'variable', 'property', 'attribute', 'setting', 'option',
            'configuration', 'config', 'field', 'value', 'flag', 'switch',
            'policy', 'rule', 'constraint', 'limit', 'threshold', 'timeout'
        }
        
        self.characteristic_verbs = {
            'configure', 'design', 'build', 'implement', 'create', 'develop',
            'provide', 'support', 'enable', 'offer', 'document', 'describe',
            'guarantee', 'optimize', 'secure', 'protect', 'validate',
            # Technical configuration and implementation verbs
            'hardcode', 'encode', 'embed', 'preset', 'predefine', 'initialize',
            'install', 'deploy', 'setup', 'establish', 'register', 'bind',
            'allocate', 'assign', 'specify', 'define', 'declare', 'map',
            'route', 'redirect', 'forward', 'expose', 'publish', 'mount'
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
        
        # CRITICAL: Check for change announcements first - these should NOT be descriptive
        # even if they use present tense auxiliary
        if self._is_change_announcement(construction, doc):
            return False
        
        # Present tense auxiliary = descriptive (but only if not a change announcement)
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
    
    def _is_change_announcement(self, construction: PassiveConstruction, doc: Doc) -> bool:
        """
        Linguistic analysis to detect change announcements using morphological features,
        dependency parsing, and semantic patterns rather than hard-coded word lists.
        
        Uses linguistic anchors:
        1. Perfective aspect vs. imperfective aspect analysis
        2. Temporal modifier attachment patterns  
        3. Discourse deixis analysis
        4. Argument structure and semantic role patterns
        """
        
        # LINGUISTIC ANCHOR 1: Perfective vs. Imperfective Aspect Analysis
        if self._has_perfective_completion_markers(construction, doc):
            return True
        
        # LINGUISTIC ANCHOR 2: Temporal Deixis with Release Semantics
        if self._has_temporal_release_deixis(construction, doc):
            return True
        
        # LINGUISTIC ANCHOR 3: Accomplishment vs. State Aspectual Class
        if self._is_accomplishment_predicate(construction, doc):
            # Accomplishments in passive voice often indicate announcements
            # unless they have habitual/generic markers
            if not self._has_habitual_generic_markers(doc):
                return True
        
        # LINGUISTIC ANCHOR 4: Discourse Demonstrative with Change Semantics
        if self._has_change_oriented_discourse_deixis(construction, doc):
            return True
        
        return False
    
    def _has_perfective_completion_markers(self, construction: PassiveConstruction, doc: Doc) -> bool:
        """
        LINGUISTIC ANCHOR 1: Detect perfective aspect markers indicating completed actions.
        Uses morphological analysis and dependency parsing to identify completion semantics.
        """
        main_verb = construction.main_verb
        
        # Check for temporal prepositional phrases indicating completion/result
        for token in doc:
            if token.dep_ == 'prep' and token.head == main_verb:
                # "fixed in version X" - completion in specific context
                if token.lemma_ in ['in', 'with'] and token.head.tag_ == 'VBN':
                    for child in token.children:
                        if child.pos_ in ['NOUN', 'PROPN']:
                            # Check if the noun has release/version semantics using morphology
                            if self._has_release_semantics(child):
                                return True
        
        # Check for resultative constructions and perfective particles
        for child in main_verb.children:
            if child.dep_ == 'advmod' and child.lemma_ in ['now', 'finally', 'completely']:
                return True
        
        return False
    
    def _has_temporal_release_deixis(self, construction: PassiveConstruction, doc: Doc) -> bool:
        """
        LINGUISTIC ANCHOR 2: Detect temporal deixis with release semantics.
        Analyzes demonstrative + temporal noun patterns using dependency parsing.
        """
        for token in doc:
            # Look for demonstrative determiners with temporal nouns
            if token.dep_ == 'det' and token.lemma_ == 'this':
                temporal_head = token.head
                if temporal_head.pos_ == 'NOUN':
                    # Check if this is in a prepositional phrase indicating temporal context
                    if temporal_head.dep_ == 'pobj':
                        prep = temporal_head.head
                        if prep.pos_ == 'ADP' and prep.lemma_ in ['with', 'in']:
                            # "with this update", "in this release" - temporal deixis
                            if self._has_release_semantics(temporal_head):
                                return True
            
            # Look for "following" + plural noun constructions
            if token.lemma_ == 'following' and token.pos_ == 'ADJ':
                if token.head.pos_ == 'NOUN' and 'Number=Plur' in token.head.morph:
                    return True
        
        return False
    
    def _is_accomplishment_predicate(self, construction: PassiveConstruction, doc: Doc) -> bool:
        """
        LINGUISTIC ANCHOR 3: Analyze aspectual class using morphological features.
        Distinguishes accomplishment verbs (telic) from state verbs (atelic).
        
        Key distinction:
        - Accomplishments: bounded events with endpoints (fix, add, resolve)
        - States: unbounded capabilities/processes (validate, encrypt, configure)
        """
        main_verb = construction.main_verb
        
        # Use morphological analysis to detect telicity markers
        if 'VerbForm=Part' in main_verb.morph and main_verb.tag_ == 'VBN':
            
            # EXCLUSION: Process/capability descriptions with temporal/manner modifiers
            if self._has_process_capability_markers(main_verb, doc):
                return False
            
            # INCLUSION: Look for bounded completion semantics
            if self._has_bounded_completion_semantics(main_verb, construction, doc):
                return True
        
        return False
    
    def _has_process_capability_markers(self, main_verb: Token, doc: Doc) -> bool:
        """
        Detect linguistic markers indicating ongoing processes/capabilities rather than events.
        Uses morphological analysis to identify stative/process semantics.
        """
        # Check for temporal/manner adverbials indicating ongoing processes
        for child in main_verb.children:
            if child.dep_ == 'advmod':
                # Process adverbials: during, before, while, automatically
                if child.lemma_ in ['automatically', 'continuously', 'typically']:
                    return True
            
            # Temporal prepositional phrases indicating process context
            if child.dep_ == 'prep' and child.lemma_ in ['during', 'before', 'while']:
                return True
        
        # Check for generic present tense auxiliary WITH additional capability markers
        aux = self._find_auxiliary(main_verb)
        if aux and 'Tense=Pres' in aux.morph:
            # Present tense alone is not sufficient - need additional capability markers
            has_capability_indicators = False
            
            # Look for manner/process adverbials that indicate ongoing capability
            for token in doc:
                if token.dep_ == 'advmod' and token.lemma_ in ['automatically', 'typically', 'usually']:
                    has_capability_indicators = True
                    break
                # Look for temporal process contexts
                if token.dep_ == 'prep' and token.lemma_ in ['during', 'while', 'before']:
                    has_capability_indicators = True
                    break
            
            # Only classify as process capability if there are explicit capability indicators
            if has_capability_indicators:
                return True
        
        return False
    
    def _has_bounded_completion_semantics(self, main_verb: Token, construction: PassiveConstruction, doc: Doc) -> bool:
        """
        Detect linguistic markers indicating bounded completion events.
        Uses morphological and dependency analysis to identify telic accomplishments.
        """
        # Check for resultative/completion modifiers
        for child in main_verb.children:
            if child.dep_ == 'advmod' and child.lemma_ in ['successfully', 'completely', 'finally']:
                return True
        
        # Check for bounded quantification of the theme/patient
        if construction.passive_subject:
            subject = construction.passive_subject
            
            # Plural countable nouns often indicate bounded accomplishments
            if 'Number=Plur' in subject.morph and subject.pos_ == 'NOUN':
                # Check if it's a concrete countable entity (not mass noun)
                if not subject.lemma_ in ['data', 'information', 'content']:
                    return True
            
            # Definite descriptions with specific reference
            for child in subject.children:
                if child.dep_ == 'det' and child.lemma_ in ['these', 'those']:
                    return True  # Anaphoric definites suggest specific accomplishments
        
        # Check for perfective temporal anchoring
        for token in doc:
            if token.dep_ == 'prep' and token.head == main_verb:
                if token.lemma_ in ['in', 'with']:
                    for child in token.children:
                        # Version/release contexts indicate bounded accomplishments
                        if self._has_release_semantics(child):
                            return True
        
        return False
    
    def _has_habitual_generic_markers(self, doc: Doc) -> bool:
        """
        LINGUISTIC ANCHOR 4: Detect habitual/generic aspect markers.
        Uses morphological analysis to identify ongoing/habitual interpretations.
        """
        for token in doc:
            # Habitual/frequency adverbials
            if token.dep_ == 'advmod' and token.lemma_ in ['regularly', 'automatically', 'typically', 'usually', 'always']:
                return True
            
            # Generic temporal expressions
            if token.dep_ == 'npadvmod' and 'regularly' in token.lemma_:
                return True
                
            # Present habitual markers
            if token.pos_ == 'AUX' and 'Tense=Pres' in token.morph:
                # Check for generic interpretation markers
                for sibling in token.head.children:
                    if sibling.dep_ == 'advmod' and sibling.lemma_ in ['automatically', 'typically']:
                        return True
        
        return False
    
    def _has_change_oriented_discourse_deixis(self, construction: PassiveConstruction, doc: Doc) -> bool:
        """
        LINGUISTIC ANCHOR 5: Detect discourse deixis with change orientation.
        Analyzes anaphoric patterns and demonstrative reference.
        """
        # Look for sentence-initial demonstratives with change-oriented predicates
        for i, token in enumerate(doc):
            if i == 0 and token.lemma_ == 'the' and token.dep_ == 'det':
                # "The following X are ..." - discourse deixis to upcoming list
                if token.head.lemma_ == 'following':
                    return True
            
            # Demonstrative pronouns referring to document sections
            if token.lemma_ == 'this' and token.dep_ == 'det':
                head = token.head
                if head.pos_ == 'NOUN':
                    # Check morphological features for document structure reference
                    # This uses dependency parsing rather than word lists
                    if head.dep_ == 'nsubjpass' and construction.passive_subject == head:
                        # "This [noun] is fixed" where noun is the passive subject
                        return True
        
        return False
    
    def _has_release_semantics(self, token: Token) -> bool:
        """
        Helper: Check if a token has release/version semantics using morphological analysis.
        Uses spaCy's semantic features rather than hard-coded lists.
        """
        # Use morphological patterns and context rather than word lists
        lemma = token.lemma_.lower()
        
        # Check for version number patterns using dependency children
        for child in token.children:
            if child.like_num or child.pos_ == 'NUM':
                return True  # "version 1.0", "release 2"
        
        # Check for compound constructions indicating releases
        if token.dep_ == 'compound':
            head = token.head
            if head.pos_ == 'NOUN':
                return True  # Part of compound like "version number"
        
        # Use morphological features - proper nouns often indicate releases
        if token.pos_ == 'PROPN':
            return True  # Product names, version names
        
        # Semantic patterns based on word formation
        if lemma.endswith('ing') and token.pos_ == 'NOUN':
            return False  # Process nouns, less likely to be releases
        
        return lemma in ['version', 'release', 'update', 'patch']  # Minimal core semantic set
    
    # NOTE: PhraseMatcher example for complex multi-token patterns if needed:
    # 
    # from spacy.matcher import PhraseMatcher
    # 
    # def _has_complex_release_patterns(self, doc: Doc) -> bool:
    #     """Example: Use PhraseMatcher for complex multi-token patterns."""
    #     matcher = PhraseMatcher(doc.vocab, attr="LOWER")
    #     patterns = [nlp("following issues"), nlp("security vulnerabilities")]
    #     matcher.add("RELEASE_PATTERNS", patterns)
    #     matches = matcher(doc)
    #     return len(matches) > 0
    #
    # This approach maintains pure linguistic analysis while handling
    # complex patterns that exceed simple dependency parsing.
    
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
                
                # Calculate evidence score (will be overridden when called from rules with full context)
                # This provides a default evidence score based on sentence-level analysis
                construction.evidence_score = self.calculate_passive_voice_evidence(construction, doc)
                
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
    
    # === EVIDENCE-BASED CALCULATION METHODS ===
    
    def calculate_passive_voice_evidence(self, construction: PassiveConstruction, doc: Doc, 
                                       full_text: str = "", context: Dict[str, Any] = None) -> float:
        """
        Calculate evidence score (0.0-1.0) for passive voice concerns.
        
        Higher scores indicate stronger evidence that passive voice should be flagged.
        Lower scores indicate acceptable usage in specific contexts.
        
        Args:
            construction: PassiveConstruction with linguistic analysis
            doc: SpaCy document for the sentence
            full_text: Full document text for broader context analysis
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (acceptable) to 1.0 (should be flagged)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_passive_voice_evidence(construction, doc)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this construction
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_passive(evidence_score, construction, doc)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_passive(evidence_score, construction, context or {})
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_passive(evidence_score, construction, full_text, context or {})
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_passive(evidence_score, construction, context or {})
        
        # Store evidence score in construction for reference
        construction.evidence_score = max(0.0, min(1.0, evidence_score))
        
        return construction.evidence_score

    def _get_base_passive_voice_evidence(self, construction: PassiveConstruction, doc: Doc) -> float:
        """Get base evidence score based on passive construction characteristics."""
        
        # === DESCRIPTIVE CONTEXT ANALYSIS ===
        # The analyzer already has sophisticated context classification
        context_type = construction.context_type
        
        if context_type == ContextType.DESCRIPTIVE:
            # Descriptive passive voice often acceptable in technical documentation
            base_evidence = 0.3  # Low base evidence for descriptive contexts
        elif context_type == ContextType.INSTRUCTIONAL:
            # Instructional passive voice often problematic
            base_evidence = 0.8  # High base evidence for instructional contexts
        else:
            # Uncertain contexts get moderate evidence
            base_evidence = 0.6  # Moderate base evidence for uncertain contexts
        
        # === CONSTRUCTION QUALITY ANALYSIS ===
        # Factor in the existing linguistic analysis
        
        # Clear agent (by-phrase) reduces evidence - intentional passive
        if construction.has_by_phrase:
            base_evidence -= 0.2  # Intentional passive with clear agent
        
        # Change announcements often legitimate passive usage
        if self._is_change_announcement(construction, doc):
            base_evidence -= 0.3  # Change announcements often use passive appropriately
        
        # Strong passive evidence increases base score
        if self._has_strong_passive_evidence(construction, doc):
            base_evidence += 0.1  # Clear passive construction
        
        # System functionality descriptions are often acceptable
        if self._is_system_functionality_description(construction, doc):
            base_evidence -= 0.2  # System descriptions often use legitimate passive
        
        return max(0.0, min(1.0, base_evidence))

    def _apply_linguistic_clues_passive(self, evidence_score: float, construction: PassiveConstruction, doc: Doc) -> float:
        """Apply linguistic analysis clues for passive voice detection."""
        
        main_verb = construction.main_verb
        
        # === VERB SEMANTIC ANALYSIS ===
        # State-oriented verbs are often legitimate in passive
        if main_verb.lemma_ in self.state_oriented_verbs:
            evidence_score -= 0.3  # State verbs often acceptable in passive
        
        # Characteristic verbs in technical contexts often legitimate
        if main_verb.lemma_ in self.characteristic_verbs:
            evidence_score -= 0.2  # Technical implementation verbs
        
        # === AUXILIARY VERB ANALYSIS ===
        if construction.auxiliary:
            aux = construction.auxiliary
            
            # Present tense auxiliary suggests ongoing/descriptive state
            if aux.tag_ in ['VBZ', 'VBP']:  # is/are configured
                evidence_score -= 0.2  # Present tense often descriptive
            
            # Past tense auxiliary suggests completed action (more problematic)
            elif aux.tag_ in ['VBD']:  # was/were configured
                evidence_score += 0.1  # Past tense completion often inappropriate
            
            # Modal auxiliaries suggest capability/requirement
            elif aux.lemma_ in self.capability_modals:
                evidence_score -= 0.3  # "can be configured" - capability description
            elif aux.lemma_ in self.requirement_modals:
                evidence_score += 0.2  # "must be configured" - instruction context
        
        # === SUBJECT ANALYSIS ===
        if construction.passive_subject:
            subject = construction.passive_subject
            
            # Technical entity subjects often legitimate
            if subject.text.lower() in self.technical_entities:
                evidence_score -= 0.2  # "The system is configured" - technical description
            
            # Personal pronouns as subjects less appropriate in passive
            if subject.pos_ == 'PRON' and subject.lemma_ in ['you', 'they', 'we']:
                evidence_score += 0.2  # "You are configured" - awkward passive
            
            # Generic/indefinite subjects suggest weak agency
            if subject.lemma_ in ['it', 'this', 'that']:
                evidence_score += 0.1  # Vague passive subjects
        
        # === AGENT ANALYSIS ===
        # Clear actor availability (implicit agent)
        if construction.has_clear_actor:
            evidence_score += 0.1  # Clear agent available - could be active
        
        # === NAMED ENTITY RECOGNITION ===
        # Named entities may affect passive voice appropriateness
        if construction.passive_subject and hasattr(construction.passive_subject, 'ent_type_'):
            if construction.passive_subject.ent_type_:
                ent_type = construction.passive_subject.ent_type_
                # Organizations and products often legitimate passive subjects
                if ent_type in ['ORG', 'PRODUCT', 'FAC']:
                    evidence_score -= 0.1  # Organizations often configured/managed passively
                # Personal entities less appropriate as passive subjects
                elif ent_type == 'PERSON':
                    evidence_score += 0.2  # People should be active agents
                # Technical entities often legitimate passive subjects
                elif ent_type in ['GPE', 'EVENT']:
                    evidence_score -= 0.05  # Geographic/event entities
        
        # Check for named entities in the broader sentence context
        for token in doc:
            if hasattr(token, 'ent_type_') and token.ent_type_:
                ent_type = token.ent_type_
                # Technical product entities suggest technical documentation
                if ent_type in ['PRODUCT', 'ORG', 'FAC']:
                    evidence_score -= 0.02  # Technical context allows more passive voice
                # Money/quantity entities suggest formal documentation
                elif ent_type in ['MONEY', 'QUANTITY', 'PERCENT']:
                    evidence_score -= 0.01  # Financial/quantitative contexts
        
        # === SENTENCE COMPLEXITY ===
        sentence_length = len([token for token in doc if not token.is_punct])
        if sentence_length > 15:
            evidence_score -= 0.1  # Complex sentences may need passive for clarity
        elif sentence_length < 6:
            evidence_score += 0.1  # Simple sentences often better in active
        
        return max(0.0, min(1.0, evidence_score))

    def _apply_structural_clues_passive(self, evidence_score: float, construction: PassiveConstruction, context: Dict[str, Any]) -> float:
        """Apply document structure-based clues for passive voice detection."""
        
        block_type = context.get('block_type', 'paragraph')
        
        # === TECHNICAL DOCUMENTATION CONTEXTS ===
        # Technical contexts often legitimately use passive voice
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.4  # Code documentation often uses passive appropriately
        elif block_type == 'inline_code':
            evidence_score -= 0.3  # Inline code descriptions
        
        # === PROCEDURAL CONTEXTS ===
        # Lists and procedures vary in passive voice appropriateness
        if block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.1  # Lists may document configurations passively
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.2  # Tables often describe states passively
        
        # === HEADING CONTEXTS ===
        # Headings should generally be clear and active
        if block_type in ['heading', 'title']:
            evidence_score += 0.2  # Headings better in active voice
        
        # === ADMONITION CONTEXTS ===
        # Warnings and notes vary by type
        if block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'TIP']:
                evidence_score -= 0.1  # Notes may describe states passively
            elif admonition_type in ['WARNING', 'CAUTION', 'IMPORTANT']:
                evidence_score += 0.1  # Warnings should be clear and direct
        
        # === EXAMPLE CONTEXTS ===
        # Examples and samples often show passive configurations
        if block_type in ['example', 'sample']:
            evidence_score -= 0.3  # Examples may show passive configurations
        elif block_type in ['block_quote', 'citation']:
            evidence_score -= 0.2  # Quoted material may preserve passive voice
        
        return max(0.0, min(1.0, evidence_score))

    def _apply_semantic_clues_passive(self, evidence_score: float, construction: PassiveConstruction, 
                                    full_text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for passive voice detection."""
        
        content_type = context.get('content_type', 'general')
        
        # === CONTENT TYPE ANALYSIS ===
        # Different content types have different passive voice expectations
        if content_type == 'technical':
            evidence_score -= 0.2  # Technical documentation often uses passive appropriately
        elif content_type == 'api':
            evidence_score -= 0.3  # API documentation often describes passive configurations
        elif content_type == 'academic':
            evidence_score -= 0.1  # Academic writing sometimes uses passive appropriately
        elif content_type == 'legal':
            evidence_score -= 0.2  # Legal writing often uses passive for objectivity
        elif content_type == 'marketing':
            evidence_score += 0.2  # Marketing should be active and engaging
        elif content_type == 'narrative':
            evidence_score += 0.1  # Narrative writing often better in active voice
        elif content_type == 'procedural':
            evidence_score += 0.2  # Procedures should be clear and direct
        
        # === DOMAIN-SPECIFIC PATTERNS ===
        domain = context.get('domain', 'general')
        if domain in ['software', 'engineering', 'devops']:
            evidence_score -= 0.2  # Technical domains often use passive for system descriptions
        elif domain in ['configuration', 'setup', 'installation']:
            evidence_score -= 0.1  # Configuration domains may use passive
        elif domain in ['tutorial', 'documentation']:
            evidence_score += 0.1  # Educational content should be clear and direct
        elif domain in ['user-guide', 'manual']:
            evidence_score += 0.2  # User guides should be action-oriented
        
        # === AUDIENCE CONSIDERATIONS ===
        audience = context.get('audience', 'general')
        if audience in ['developer', 'technical', 'expert']:
            evidence_score -= 0.1  # Technical audiences understand passive technical descriptions
        elif audience in ['beginner', 'general', 'user']:
            evidence_score += 0.2  # General audiences need clear, active instructions
        elif audience in ['administrator', 'maintainer']:
            evidence_score -= 0.1  # Admin audiences understand system descriptions
        
        # === DOCUMENT PURPOSE ANALYSIS ===
        # Analyze document purpose from content patterns
        if self._is_configuration_documentation(full_text):
            evidence_score -= 0.2  # Configuration docs often describe passive states
        
        if self._is_troubleshooting_documentation(full_text):
            evidence_score += 0.1  # Troubleshooting should be action-oriented
        
        if self._is_user_instruction_content(full_text):
            evidence_score += 0.3  # User instructions should be active and clear
        
        # === PASSIVE VOICE DENSITY ===
        # High passive voice density in document suggests systematic usage
        if self._has_high_passive_voice_density(full_text):
            evidence_score -= 0.1  # Systematic passive usage may be intentional
        
        return max(0.0, min(1.0, evidence_score))

    def _apply_feedback_clues_passive(self, evidence_score: float, construction: PassiveConstruction, context: Dict[str, Any]) -> float:
        """Apply feedback patterns for passive voice detection."""
        
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_passive()
        
        # === VERB-SPECIFIC FEEDBACK ===
        verb_lemma = construction.main_verb.lemma_
        
        # Check if this verb is commonly accepted in passive voice
        accepted_passive_verbs = feedback_patterns.get('accepted_passive_verbs', set())
        if verb_lemma in accepted_passive_verbs:
            evidence_score -= 0.3  # Users consistently accept this verb in passive
        
        flagged_passive_verbs = feedback_patterns.get('flagged_passive_verbs', set())
        if verb_lemma in flagged_passive_verbs:
            evidence_score += 0.3  # Users consistently flag this verb in passive
        
        # === CONTEXT-SPECIFIC FEEDBACK ===
        content_type = context.get('content_type', 'general')
        context_patterns = feedback_patterns.get(f'{content_type}_passive_patterns', {})
        
        # Construction type feedback
        construction_key = f"{construction.context_type.value}_{verb_lemma}"
        if construction_key in context_patterns.get('acceptable', set()):
            evidence_score -= 0.2  # Users accept this construction in this context
        elif construction_key in context_patterns.get('problematic', set()):
            evidence_score += 0.2  # Users flag this construction in this context
        
        # === CHANGE ANNOUNCEMENT FEEDBACK ===
        # Special handling for change announcements
        if self._is_change_announcement(construction, construction.main_verb.doc):
            change_acceptance = feedback_patterns.get('change_announcement_acceptance', 0.7)
            if change_acceptance > 0.8:
                evidence_score -= 0.2  # Users accept passive in change announcements
            elif change_acceptance < 0.3:
                evidence_score += 0.2  # Users prefer active in change announcements
        
        # === TECHNICAL ENTITY + PASSIVE FEEDBACK ===
        if (construction.passive_subject and 
            construction.passive_subject.text.lower() in self.technical_entities):
            tech_passive_acceptance = feedback_patterns.get('technical_entity_passive_acceptance', 0.6)
            if tech_passive_acceptance > 0.7:
                evidence_score -= 0.2  # Users accept technical entity passive constructions
            elif tech_passive_acceptance < 0.4:
                evidence_score += 0.1  # Users prefer active for technical entities
        
        # === AUXILIARY VERB FEEDBACK ===
        if construction.auxiliary:
            aux_patterns = feedback_patterns.get('auxiliary_patterns', {})
            aux_acceptance = aux_patterns.get(construction.auxiliary.lemma_, 0.5)
            
            if aux_acceptance > 0.7:
                evidence_score -= 0.1  # This auxiliary commonly accepted in passive
            elif aux_acceptance < 0.3:
                evidence_score += 0.1  # This auxiliary commonly flagged in passive
        
        return max(0.0, min(1.0, evidence_score))

    # === HELPER METHODS FOR SEMANTIC ANALYSIS ===

    def _is_configuration_documentation(self, text: str) -> bool:
        """Check if text appears to be configuration documentation."""
        config_indicators = [
            'configuration', 'configure', 'config', 'setting', 'parameter',
            'option', 'property', 'attribute', 'variable', 'flag', 'switch',
            'default', 'preset', 'initialize', 'setup', 'install'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in config_indicators if indicator in text_lower) >= 3

    def _is_troubleshooting_documentation(self, text: str) -> bool:
        """Check if text appears to be troubleshooting documentation."""
        troubleshooting_indicators = [
            'troubleshoot', 'troubleshooting', 'problem', 'issue', 'error',
            'fix', 'resolve', 'solution', 'debug', 'diagnose', 'repair',
            'restore', 'recover', 'failure', 'broken', 'not working'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in troubleshooting_indicators if indicator in text_lower) >= 2

    def _is_user_instruction_content(self, text: str) -> bool:
        """Check if text appears to be user instruction content."""
        instruction_indicators = [
            'follow', 'complete', 'perform', 'execute', 'run', 'start',
            'stop', 'create', 'add', 'remove', 'delete', 'modify', 'update',
            'step', 'procedure', 'instruction', 'guide', 'how to', 'tutorial'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in instruction_indicators if indicator in text_lower) >= 3

    def _has_high_passive_voice_density(self, text: str) -> bool:
        """Check if document has high density of passive voice constructions."""
        # This is a simplified heuristic - in production, would use full analysis
        passive_indicators = ['is configured', 'are set', 'was implemented', 'were created', 'been established']
        text_lower = text.lower()
        
        passive_count = sum(1 for indicator in passive_indicators if indicator in text_lower)
        word_count = len(text.split())
        
        # Consider high density if > 2% of content has passive indicators
        return passive_count > 0 and (passive_count / max(word_count, 1)) > 0.02

    def _is_api_documentation_context(self, text: str, context: dict) -> bool:
        """
        Detect if content is API reference documentation.
        
        API docs often use passive voice to describe system behaviors,
        configurations, and capabilities in an objective manner.
        
        Args:
            text: Document text
            context: Document context
            
        Returns:
            bool: True if API documentation context detected
        """
        api_indicators = {
            'api', 'endpoint', 'method', 'request', 'response', 'parameter',
            'authentication', 'authorization', 'header', 'payload', 'json',
            'rest', 'restful', 'http', 'https', 'get', 'post', 'put', 'delete',
            'webhook', 'callback', 'token', 'key', 'secret', 'client'
        }
        
        text_lower = text.lower()
        domain = context.get('domain', '')
        content_type = context.get('content_type', '')
        
        # Direct text indicators
        api_score = sum(1 for indicator in api_indicators if indicator in text_lower)
        
        # Context-based indicators
        if domain in {'api', 'web-service', 'microservice', 'rest', 'graphql'}:
            api_score += 2
        
        if content_type in {'api', 'reference', 'specification', 'openapi'}:
            api_score += 2
        
        # Check for API-specific patterns
        api_patterns = [
            'api endpoint', 'http method', 'request parameter', 'response body',
            'authentication header', 'authorization token', 'json payload',
            'api call', 'api response', 'rest api', 'web service'
        ]
        
        pattern_matches = sum(1 for pattern in api_patterns if pattern in text_lower)
        api_score += pattern_matches
        
        # Threshold for API context detection
        return api_score >= 3

    def _is_architecture_documentation_context(self, text: str, context: dict) -> bool:
        """
        Detect if content is architecture or design documentation.
        
        Architecture docs often use passive voice to describe how systems
        are structured, connected, and configured.
        
        Args:
            text: Document text
            context: Document context
            
        Returns:
            bool: True if architecture documentation context detected
        """
        architecture_indicators = {
            'architecture', 'design', 'pattern', 'component', 'module', 'service',
            'microservice', 'infrastructure', 'deployment', 'topology', 'layer',
            'tier', 'distributed', 'scalable', 'fault-tolerant', 'high-availability',
            'load-balancer', 'database', 'cache', 'queue', 'message', 'event'
        }
        
        text_lower = text.lower()
        domain = context.get('domain', '')
        content_type = context.get('content_type', '')
        
        # Direct text indicators
        arch_score = sum(1 for indicator in architecture_indicators if indicator in text_lower)
        
        # Context-based indicators
        if domain in {'architecture', 'design', 'infrastructure', 'platform', 'system'}:
            arch_score += 2
        
        if content_type in {'architecture', 'design', 'specification', 'blueprint'}:
            arch_score += 2
        
        # Check for architecture-specific patterns
        architecture_patterns = [
            'system architecture', 'service architecture', 'application architecture',
            'data flow', 'message flow', 'component interaction', 'service communication',
            'distributed system', 'microservice pattern', 'design pattern'
        ]
        
        pattern_matches = sum(1 for pattern in architecture_patterns if pattern in text_lower)
        arch_score += pattern_matches
        
        # Threshold for architecture context detection
        return arch_score >= 3

    # === CONTEXT-AWARE MESSAGING AND SUGGESTIONS ===

    def get_contextual_passive_voice_message(self, construction: PassiveConstruction, evidence_score: float, context: dict = None) -> str:
        """
        Generate context-aware error messages for passive voice constructions.
        
        Tailors the message based on evidence strength, document context, and writing style
        to provide meaningful feedback that respects the writing situation.
        
        Args:
            construction: PassiveConstruction with linguistic analysis
            evidence_score: Calculated evidence score for this construction
            context: Document context for message customization
            
        Returns:
            str: Contextual error message
        """
        content_type = context.get('content_type', 'general') if context else 'general'
        audience = context.get('audience', 'general') if context else 'general'
        verb = construction.main_verb.lemma_
        
        if evidence_score > 0.8:
            if content_type in ['procedural', 'tutorial']:
                return f"Passive voice found: '{verb}'. Instructions should be clear and direct - consider using active voice."
            elif audience in ['beginner', 'general']:
                return f"Passive voice detected: '{verb}'. Active voice is clearer for readers."
            else:
                return f"Passive voice construction: '{verb}'. Consider using active voice for clarity."
        elif evidence_score > 0.5:
            if content_type in ['technical', 'api']:
                return f"Passive voice usage: '{verb}'. Verify this aligns with your documentation style."
            elif construction.context_type == ContextType.INSTRUCTIONAL:
                return f"Passive voice in instruction: '{verb}'. Consider if active voice would be clearer."
            else:
                return f"Passive voice noted: '{verb}'. Consider whether active voice would improve clarity."
        else:
            if content_type in ['technical', 'api']:
                return f"Passive voice: '{verb}'. May be appropriate for technical descriptions."
            elif construction.context_type == ContextType.DESCRIPTIVE:
                return f"Descriptive passive voice: '{verb}'. This may be acceptable for system descriptions."
            else:
                return f"Passive voice usage: '{verb}'. Verify appropriateness for your context."

    def generate_smart_passive_voice_suggestions(self, construction: PassiveConstruction, evidence_score: float, context: dict = None) -> List[str]:
        """
        Generate context-aware suggestions for passive voice constructions.
        
        Provides actionable suggestions that consider document type, audience,
        and specific passive voice patterns found in the sentence.
        
        Args:
            construction: PassiveConstruction with linguistic analysis
            evidence_score: Calculated evidence score for this construction
            context: Document context for suggestion customization
            
        Returns:
            List[str]: Context-appropriate suggestions for improvement
        """
        suggestions = []
        content_type = context.get('content_type', 'general') if context else 'general'
        audience = context.get('audience', 'general') if context else 'general'
        verb = construction.main_verb.lemma_
        
        # High evidence cases need clear corrections
        if evidence_score > 0.7:
            if content_type in ['procedural', 'tutorial']:
                suggestions.append(f"Rewrite in active voice: 'You {verb}...' or 'To {verb}...'")
                suggestions.append("Use imperative mood for clear instructions.")
            elif audience in ['beginner', 'general']:
                suggestions.append("Identify who performs the action and make them the subject.")
                suggestions.append("Use active voice to make instructions clearer for readers.")
            else:
                suggestions.append("Convert to active voice by identifying the actor.")
                suggestions.append("Consider restructuring to emphasize the action performer.")
        else:
            suggestions.append("Consider whether active voice would improve clarity.")
        
        # Context-specific advice
        if content_type == 'technical' and construction.context_type == ContextType.DESCRIPTIVE:
            suggestions.append("Passive voice may be acceptable for technical system descriptions.")
        elif content_type == 'api':
            suggestions.append("For API docs, consider if this describes system behavior (passive OK) or user actions (active better).")
        elif content_type == 'procedural':
            suggestions.append("Instructions should be direct: use active voice or imperative mood.")
        elif construction.has_by_phrase:
            suggestions.append("The by-phrase suggests intentional passive voice - verify if appropriate.")
        elif self._is_change_announcement(construction, construction.main_verb.doc):
            suggestions.append("Change announcements may appropriately use passive voice.")
        
        # Audience-specific advice
        if audience in ['beginner', 'general']:
            suggestions.append("Active voice is generally clearer for general audiences.")
        elif audience in ['technical', 'developer']:
            suggestions.append("Technical audiences may accept passive voice for system descriptions.")
        
        # Evidence-based advice
        if evidence_score < 0.3:
            suggestions.append("This passive voice usage may be appropriate in your context.")
        elif evidence_score > 0.8:
            suggestions.append("Strong recommendation to use active voice here.")
        
        # Construction-specific suggestions
        if construction.context_type == ContextType.INSTRUCTIONAL:
            suggestions.append("Instructions are clearer when they specify who should perform actions.")
        elif construction.context_type == ContextType.DESCRIPTIVE:
            suggestions.append("Descriptive content may appropriately use passive voice.")
        
        # Limit to most relevant suggestions
        return suggestions[:3]

    def _get_cached_feedback_patterns_passive(self):
        """Load feedback patterns from cache or feedback analysis for passive voice."""
        # This would load from feedback analysis system
        # For now, return patterns based on common passive voice usage
        return {
            'accepted_passive_verbs': {
                # Verbs users often accept in passive voice (technical contexts)
                'configure', 'implement', 'design', 'build', 'create', 'develop',
                'install', 'deploy', 'setup', 'establish', 'define', 'specify',
                'validate', 'verify', 'test', 'document', 'describe', 'support'
            },
            'flagged_passive_verbs': {
                # Verbs users consistently want to be active
                'perform', 'execute', 'run', 'start', 'stop', 'complete',
                'follow', 'use', 'apply', 'ensure', 'check', 'verify'
            },
            'technical_passive_patterns': {
                'acceptable': {
                    # Context-specific patterns users accept
                    'descriptive_configure', 'descriptive_implement', 'descriptive_design',
                    'descriptive_build', 'descriptive_create', 'descriptive_install'
                },
                'problematic': {
                    # Context-specific patterns users flag
                    'instructional_perform', 'instructional_execute', 'instructional_run',
                    'instructional_follow', 'instructional_complete'
                }
            },
            'api_passive_patterns': {
                'acceptable': {
                    'descriptive_configure', 'descriptive_implement', 'descriptive_support',
                    'descriptive_provide', 'descriptive_enable', 'descriptive_validate'
                },
                'problematic': {
                    'instructional_use', 'instructional_call', 'instructional_send',
                    'instructional_request', 'instructional_access'
                }
            },
            'procedural_passive_patterns': {
                'acceptable': set(),  # Very few passive constructions acceptable in procedures
                'problematic': {
                    'instructional_perform', 'instructional_execute', 'instructional_complete',
                    'instructional_follow', 'instructional_run', 'instructional_start',
                    'instructional_configure', 'instructional_setup', 'instructional_install'
                }
            },
            'change_announcement_acceptance': 0.8,  # High acceptance for passive in change announcements
            'technical_entity_passive_acceptance': 0.7,  # Good acceptance for technical entity passive
            'auxiliary_patterns': {
                # Acceptance rates for different auxiliary verbs in passive
                'is': 0.8, 'are': 0.8,      # High acceptance for present tense descriptive
                'was': 0.4, 'were': 0.4,    # Lower acceptance for past tense
                'been': 0.5,                # Moderate acceptance for perfect aspect
                'being': 0.3,               # Lower acceptance for progressive
                'can': 0.7, 'may': 0.7,     # High acceptance for capability modals
                'must': 0.3, 'should': 0.3  # Lower acceptance for requirement modals
            }
        } 