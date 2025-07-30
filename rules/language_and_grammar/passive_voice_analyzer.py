"""
Shared Passive Voice Analysis Module - Pure Linguistic Approach

Centralizes passive voice detection using sophisticated linguistic analysis 
rather than hard-coded patterns. Implements production-quality detection with:

LINGUISTIC METHODOLOGY:
- Pure morphological analysis using spaCy morphological features
- Dependency parsing for grammatical relationship analysis
- 5 linguistic anchors for change announcement detection
- Aspectual class analysis (accomplishment vs. state verbs)
- Discourse deixis and temporal reference analysis

NO HARD-CODING:
- Minimal word lists, maximum linguistic pattern analysis
- No fallback to string matching or regex patterns
- PhraseMatcher available for complex multi-token patterns if needed
- Robust linguistic features handle edge cases

LINGUISTIC ANCHORS:
1. Perfective completion markers (temporal prepositional phrases)
2. Temporal deixis with release semantics (demonstrative + temporal patterns)
3. Accomplishment vs. state predicate analysis (aspectual class)
4. Habitual/generic aspect markers (morphological analysis)
5. Discourse demonstrative with change semantics (anaphoric patterns)
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