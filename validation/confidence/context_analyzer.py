"""
ContextAnalyzer Class
Advanced semantic and structural analysis for confidence scoring.
Complements LinguisticAnchors with coreference, sentence structure, and coherence analysis.
"""

import re
import time
import spacy
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict, Counter


@dataclass
class CoreferenceMatch:
    """Represents a coreference relationship."""
    
    pronoun: str          # The pronoun text
    pronoun_pos: int      # Position of pronoun in text
    antecedent: str       # The likely antecedent text
    antecedent_pos: int   # Position of antecedent in text
    confidence: float     # Confidence in the coreference link
    distance: int         # Distance between pronoun and antecedent (in tokens)
    relationship_type: str # Type of relationship (e.g., 'subject', 'object', 'possessive')


@dataclass
class SentenceStructure:
    """Represents sentence structure analysis."""
    
    text: str                    # Original sentence text
    start_pos: int               # Start position in document
    end_pos: int                 # End position in document
    complexity_score: float      # Structural complexity (0-1)
    dependency_depth: int        # Maximum dependency tree depth
    clause_count: int            # Number of clauses
    phrase_types: List[str]      # Types of phrases found
    discourse_markers: List[str] # Discourse connectors found
    formality_indicators: List[str] # Formal language markers
    
    # Structural features
    has_passive_voice: bool      # Contains passive voice constructions
    has_complex_noun_phrases: bool  # Contains complex NP structures
    has_subordinate_clauses: bool   # Contains subordinate clauses
    coordination_type: Optional[str] # Type of coordination if present


@dataclass
class SemanticCoherence:
    """Represents semantic coherence analysis."""
    
    coherence_score: float       # Overall coherence score (0-1)
    topic_consistency: float     # Topic drift assessment
    lexical_cohesion: float      # Lexical repetition and similarity
    reference_clarity: float     # Clarity of references
    
    # Coherence factors
    repeated_entities: List[str]    # Entities mentioned multiple times
    semantic_field_consistency: float  # Consistency of semantic fields
    discourse_flow_score: float        # Quality of discourse progression
    ambiguous_references: List[str]    # Potentially ambiguous references


@dataclass
class ContextAnalysis:
    """Complete context analysis result."""
    
    text: str                    # Original text analyzed
    error_position: int          # Character position of the error
    sentence_index: int          # Index of sentence containing error
    
    # Core analysis components
    coreference_matches: List[CoreferenceMatch]
    sentence_structures: List[SentenceStructure]
    semantic_coherence: SemanticCoherence
    
    # Confidence effects
    structural_confidence: float  # Confidence from sentence structure
    coreference_confidence: float # Confidence from coreference clarity
    coherence_confidence: float   # Confidence from semantic coherence
    discourse_confidence: float   # Confidence from discourse markers
    
    net_context_effect: float    # Combined context confidence effect
    
    # Metadata
    processing_time: float       # Time taken for analysis
    spacy_model_used: str        # SpaCy model version used
    explanation: str             # Human-readable explanation


class ContextAnalyzer:
    """
    Advanced semantic and structural analyzer for text context.
    
    Provides coreference analysis, sentence structure evaluation,
    semantic coherence checking, and discourse marker detection
    to calculate context-based confidence adjustments.
    """
    
    def __init__(self, spacy_model: str = "en_core_web_sm", cache_nlp_results: bool = True):
        """
        Initialize the ContextAnalyzer.
        
        Args:
            spacy_model: Name of the spaCy model to use
            cache_nlp_results: Whether to cache spaCy processing results
        """
        self.spacy_model = spacy_model
        self.cache_nlp_results = cache_nlp_results
        
        # Load spaCy model
        try:
            self.nlp = spacy.load(spacy_model)
            print(f"✓ Loaded spaCy model: {spacy_model}")
        except OSError:
            raise ValueError(f"SpaCy model '{spacy_model}' not found. Install with: python -m spacy download {spacy_model}")
        
        # Analysis caches
        self._nlp_cache: Dict[str, Any] = {}
        self._analysis_cache: Dict[str, ContextAnalysis] = {}
        
        # Discourse markers and patterns
        self._discourse_markers = self._load_discourse_markers()
        self._formality_patterns = self._load_formality_patterns()
        
        # Performance tracking
        self._cache_hits = 0
        self._cache_misses = 0
    
    def _load_discourse_markers(self) -> Dict[str, List[str]]:
        """Load discourse marker patterns organized by function."""
        return {
            'addition': ['furthermore', 'moreover', 'additionally', 'also', 'besides', 'in addition'],
            'contrast': ['however', 'nevertheless', 'nonetheless', 'conversely', 'on the other hand', 'whereas'],
            'causation': ['therefore', 'consequently', 'thus', 'hence', 'as a result', 'because'],
            'temporal': ['subsequently', 'previously', 'meanwhile', 'simultaneously', 'then', 'next'],
            'exemplification': ['for example', 'for instance', 'specifically', 'namely', 'in particular'],
            'conclusion': ['in conclusion', 'to summarize', 'finally', 'in summary', 'overall'],
            'emphasis': ['indeed', 'certainly', 'undoubtedly', 'clearly', 'obviously', 'definitely']
        }
    
    def _load_formality_patterns(self) -> Dict[str, List[str]]:
        """Load patterns that indicate formality levels."""
        return {
            'formal_verbs': ['utilize', 'demonstrate', 'indicate', 'establish', 'implement', 'facilitate'],
            'formal_nouns': ['methodology', 'implementation', 'consideration', 'specification', 'documentation'],
            'academic_phrases': ['it should be noted', 'it is important to', 'research indicates', 'studies show'],
            'hedging': ['may', 'might', 'could', 'potentially', 'arguably', 'presumably', 'likely'],
            'precision': ['specifically', 'precisely', 'exactly', 'particularly', 'especially']
        }
    
    def analyze_context(self, text: str, error_position: int) -> ContextAnalysis:
        """
        Perform comprehensive context analysis around an error position.
        
        Args:
            text: The full text containing the error
            error_position: Character position of the error
            
        Returns:
            Complete context analysis with confidence effects
        """
        start_time = time.time()
        
        # Check cache first
        cache_key = f"{hash(text)}:{error_position}"
        if cache_key in self._analysis_cache:
            self._cache_hits += 1
            return self._analysis_cache[cache_key]
        
        self._cache_misses += 1
        
        # Process text with spaCy
        doc = self._get_nlp_doc(text)
        
        # Find sentence containing error
        sentence_index = self._find_error_sentence(doc, error_position)
        
        # Perform core analyses
        coreference_matches = self._analyze_coreferences(doc, error_position)
        sentence_structures = self._analyze_sentence_structures(doc)
        semantic_coherence = self._analyze_semantic_coherence(doc, error_position)
        
        # Calculate confidence effects
        confidence_effects = self._calculate_confidence_effects(
            coreference_matches, sentence_structures, semantic_coherence, sentence_index
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            coreference_matches, sentence_structures, semantic_coherence, confidence_effects
        )
        
        # Create analysis result
        processing_time = time.time() - start_time
        analysis = ContextAnalysis(
            text=text,
            error_position=error_position,
            sentence_index=sentence_index,
            coreference_matches=coreference_matches,
            sentence_structures=sentence_structures,
            semantic_coherence=semantic_coherence,
            structural_confidence=confidence_effects['structural'],
            coreference_confidence=confidence_effects['coreference'],
            coherence_confidence=confidence_effects['coherence'],
            discourse_confidence=confidence_effects['discourse'],
            net_context_effect=confidence_effects['net_effect'],
            processing_time=processing_time,
            spacy_model_used=self.spacy_model,
            explanation=explanation
        )
        
        # Cache result
        self._analysis_cache[cache_key] = analysis
        
        return analysis
    
    def _get_nlp_doc(self, text: str):
        """Get spaCy doc with caching."""
        if not self.cache_nlp_results:
            return self.nlp(text)
        
        text_hash = hash(text)
        if text_hash not in self._nlp_cache:
            self._nlp_cache[text_hash] = self.nlp(text)
        
        return self._nlp_cache[text_hash]
    
    def _find_error_sentence(self, doc, error_position: int) -> int:
        """Find which sentence contains the error position."""
        for i, sent in enumerate(doc.sents):
            if sent.start_char <= error_position <= sent.end_char:
                return i
        return 0  # Default to first sentence
    
    def _analyze_coreferences(self, doc, error_position: int) -> List[CoreferenceMatch]:
        """Analyze coreference relationships in the text."""
        matches = []
        
        # Find pronouns and their potential antecedents
        pronouns = [token for token in doc if token.pos_ == 'PRON' and token.text.lower() not in ['i', 'you']]
        
        for pronoun in pronouns:
            # Look for potential antecedents (nouns and proper nouns)
            antecedents = self._find_potential_antecedents(doc, pronoun)
            
            # Score each potential antecedent
            best_antecedent = self._score_antecedents(pronoun, antecedents)
            
            if best_antecedent:
                confidence = self._calculate_coreference_confidence(pronoun, best_antecedent)
                distance = abs(pronoun.i - best_antecedent.i)
                
                match = CoreferenceMatch(
                    pronoun=pronoun.text,
                    pronoun_pos=pronoun.idx,
                    antecedent=best_antecedent.text,
                    antecedent_pos=best_antecedent.idx,
                    confidence=confidence,
                    distance=distance,
                    relationship_type=self._determine_relationship_type(pronoun, best_antecedent)
                )
                matches.append(match)
        
        return matches
    
    def _find_potential_antecedents(self, doc, pronoun) -> List:
        """Find potential antecedents for a pronoun."""
        # Look for nouns and proper nouns before the pronoun
        candidates = []
        
        for token in doc[:pronoun.i]:
            if (token.pos_ in ['NOUN', 'PROPN'] and 
                token.dep_ in ['nsubj', 'nsubjpass', 'dobj', 'pobj', 'nmod'] and
                not token.is_stop):
                candidates.append(token)
        
        # Return the most recent candidates (within reasonable distance)
        max_distance = 50  # tokens
        recent_candidates = [c for c in candidates if pronoun.i - c.i <= max_distance]
        
        return recent_candidates[-10:]  # Last 10 candidates
    
    def _score_antecedents(self, pronoun, antecedents) -> Optional:
        """Score potential antecedents and return the best one."""
        if not antecedents:
            return None
        
        scores = []
        for antecedent in antecedents:
            score = self._calculate_antecedent_score(pronoun, antecedent)
            scores.append((score, antecedent))
        
        # Return the highest scoring antecedent
        best_score, best_antecedent = max(scores, key=lambda x: x[0])
        return best_antecedent if best_score > 0.3 else None
    
    def _calculate_antecedent_score(self, pronoun, antecedent) -> float:
        """Calculate score for an antecedent candidate."""
        score = 0.5  # Base score
        
        # Distance penalty (closer is better)
        distance = pronoun.i - antecedent.i
        distance_penalty = min(distance * 0.02, 0.3)
        score -= distance_penalty
        
        # Gender/number agreement (simplified)
        if self._check_agreement(pronoun, antecedent):
            score += 0.2
        
        # Syntactic role preference
        if antecedent.dep_ in ['nsubj', 'nsubjpass']:
            score += 0.15  # Subjects are preferred antecedents
        
        # Proper noun preference
        if antecedent.pos_ == 'PROPN':
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _check_agreement(self, pronoun, antecedent) -> bool:
        """Check basic gender/number agreement (simplified)."""
        pronoun_text = pronoun.text.lower()
        
        # Simple heuristics for agreement
        if pronoun_text in ['he', 'him', 'his'] and antecedent.pos_ == 'PROPN':
            return True  # Assume proper nouns can be masculine
        if pronoun_text in ['she', 'her', 'hers'] and antecedent.pos_ == 'PROPN':
            return True  # Assume proper nouns can be feminine
        if pronoun_text in ['it', 'its'] and antecedent.pos_ == 'NOUN':
            return True  # Assume common nouns can be neuter
        if pronoun_text in ['they', 'them', 'their']:
            return True  # They can refer to anything
        
        return False  # Default to no agreement
    
    def _determine_relationship_type(self, pronoun, antecedent) -> str:
        """Determine the type of coreference relationship."""
        if pronoun.dep_ in ['nsubj', 'nsubjpass']:
            return 'subject'
        elif pronoun.dep_ in ['dobj', 'pobj']:
            return 'object'
        elif 'poss' in pronoun.tag_:
            return 'possessive'
        else:
            return 'other'
    
    def _calculate_coreference_confidence(self, pronoun, antecedent) -> float:
        """Calculate confidence in a coreference link."""
        base_confidence = 0.6
        
        # Adjust based on distance
        distance = abs(pronoun.i - antecedent.i)
        if distance <= 5:
            base_confidence += 0.2
        elif distance <= 15:
            base_confidence += 0.1
        else:
            base_confidence -= 0.1
        
        # Adjust based on agreement
        if self._check_agreement(pronoun, antecedent):
            base_confidence += 0.15
        
        return max(0.0, min(1.0, base_confidence))
    
    def _analyze_sentence_structures(self, doc) -> List[SentenceStructure]:
        """Analyze structure of each sentence."""
        structures = []
        
        for sent in doc.sents:
            structure = self._analyze_single_sentence(sent)
            structures.append(structure)
        
        return structures
    
    def _analyze_single_sentence(self, sent) -> SentenceStructure:
        """Analyze structure of a single sentence."""
        # Calculate complexity metrics
        complexity_score = self._calculate_complexity_score(sent)
        dependency_depth = self._calculate_dependency_depth(sent)
        clause_count = self._count_clauses(sent)
        phrase_types = self._identify_phrase_types(sent)
        discourse_markers = self._find_discourse_markers_in_sentence(sent)
        formality_indicators = self._find_formality_indicators(sent)
        
        # Structural features
        has_passive_voice = self._has_passive_voice(sent)
        has_complex_noun_phrases = self._has_complex_noun_phrases(sent)
        has_subordinate_clauses = self._has_subordinate_clauses(sent)
        coordination_type = self._identify_coordination_type(sent)
        
        return SentenceStructure(
            text=sent.text,
            start_pos=sent.start_char,
            end_pos=sent.end_char,
            complexity_score=complexity_score,
            dependency_depth=dependency_depth,
            clause_count=clause_count,
            phrase_types=phrase_types,
            discourse_markers=discourse_markers,
            formality_indicators=formality_indicators,
            has_passive_voice=has_passive_voice,
            has_complex_noun_phrases=has_complex_noun_phrases,
            has_subordinate_clauses=has_subordinate_clauses,
            coordination_type=coordination_type
        )
    
    def _calculate_complexity_score(self, sent) -> float:
        """Calculate sentence complexity score (0-1)."""
        factors = []
        
        # Length factor
        length_factor = min(len(sent) / 30.0, 1.0)  # Normalize to 30 tokens
        factors.append(length_factor)
        
        # Dependency depth factor
        depth = self._calculate_dependency_depth(sent)
        depth_factor = min(depth / 8.0, 1.0)  # Normalize to depth of 8
        factors.append(depth_factor)
        
        # Clause count factor
        clauses = self._count_clauses(sent)
        clause_factor = min(clauses / 4.0, 1.0)  # Normalize to 4 clauses
        factors.append(clause_factor)
        
        # Subordination factor
        subordinate_count = len([t for t in sent if t.dep_ in ['advcl', 'acl', 'relcl']])
        subordinate_factor = min(subordinate_count / 3.0, 1.0)
        factors.append(subordinate_factor)
        
        return sum(factors) / len(factors)
    
    def _calculate_dependency_depth(self, sent) -> int:
        """Calculate maximum dependency tree depth."""
        def get_depth(token, current_depth=0):
            children_depths = [get_depth(child, current_depth + 1) for child in token.children]
            return max([current_depth] + children_depths)
        
        root = None
        for token in sent:
            if token.dep_ == 'ROOT':
                root = token
                break
        
        return get_depth(root) if root else 0
    
    def _count_clauses(self, sent) -> int:
        """Count number of clauses in sentence."""
        # Count finite verbs as proxy for clauses
        finite_verbs = [t for t in sent if t.pos_ == 'VERB' and 'Fin' in t.tag_]
        return max(1, len(finite_verbs))  # At least one clause
    
    def _identify_phrase_types(self, sent) -> List[str]:
        """Identify types of phrases present."""
        phrase_types = set()
        
        for token in sent:
            # Noun phrases
            if token.pos_ == 'NOUN' and any(child.dep_ in ['det', 'amod', 'compound'] for child in token.children):
                phrase_types.add('complex_np')
            
            # Prepositional phrases
            if token.pos_ == 'ADP':
                phrase_types.add('prep_phrase')
            
            # Verbal phrases
            if token.pos_ == 'VERB' and any(child.dep_ in ['aux', 'auxpass'] for child in token.children):
                phrase_types.add('complex_vp')
            
            # Adverbial phrases
            if token.pos_ == 'ADV' and any(child.dep_ == 'advmod' for child in token.children):
                phrase_types.add('adv_phrase')
        
        return list(phrase_types)
    
    def _find_discourse_markers_in_sentence(self, sent) -> List[str]:
        """Find discourse markers in a sentence."""
        text = sent.text.lower()
        found_markers = []
        
        for category, markers in self._discourse_markers.items():
            for marker in markers:
                if marker in text:
                    found_markers.append(f"{category}:{marker}")
        
        return found_markers
    
    def _find_formality_indicators(self, sent) -> List[str]:
        """Find formality indicators in a sentence."""
        text = sent.text.lower()
        found_indicators = []
        
        for category, patterns in self._formality_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    found_indicators.append(f"{category}:{pattern}")
        
        return found_indicators
    
    def _has_passive_voice(self, sent) -> bool:
        """Check if sentence contains passive voice."""
        for token in sent:
            if token.dep_ == 'nsubjpass' or 'Pass' in token.tag_:
                return True
        return False
    
    def _has_complex_noun_phrases(self, sent) -> bool:
        """Check if sentence has complex noun phrases."""
        for token in sent:
            if token.pos_ == 'NOUN':
                modifiers = [child for child in token.children if child.dep_ in ['amod', 'compound', 'nmod']]
                if len(modifiers) >= 2:  # 2+ modifiers = complex
                    return True
        return False
    
    def _has_subordinate_clauses(self, sent) -> bool:
        """Check if sentence has subordinate clauses."""
        subordinate_deps = ['advcl', 'acl', 'relcl', 'ccomp', 'xcomp']
        return any(token.dep_ in subordinate_deps for token in sent)
    
    def _identify_coordination_type(self, sent) -> Optional[str]:
        """Identify type of coordination if present."""
        for token in sent:
            if token.dep_ == 'cc':  # Coordinating conjunction
                if token.text.lower() in ['and', 'or']:
                    return 'coordinate'
                elif token.text.lower() in ['but', 'yet', 'however']:
                    return 'adversative'
        return None
    
    def _analyze_semantic_coherence(self, doc, error_position: int) -> SemanticCoherence:
        """Analyze semantic coherence of the text."""
        # Calculate coherence metrics
        coherence_score = self._calculate_overall_coherence(doc)
        topic_consistency = self._assess_topic_consistency(doc)
        lexical_cohesion = self._calculate_lexical_cohesion(doc)
        reference_clarity = self._assess_reference_clarity(doc)
        
        # Identify coherence factors
        repeated_entities = self._find_repeated_entities(doc)
        semantic_field_consistency = self._assess_semantic_field_consistency(doc)
        discourse_flow_score = self._assess_discourse_flow(doc)
        ambiguous_references = self._find_ambiguous_references(doc)
        
        return SemanticCoherence(
            coherence_score=coherence_score,
            topic_consistency=topic_consistency,
            lexical_cohesion=lexical_cohesion,
            reference_clarity=reference_clarity,
            repeated_entities=repeated_entities,
            semantic_field_consistency=semantic_field_consistency,
            discourse_flow_score=discourse_flow_score,
            ambiguous_references=ambiguous_references
        )
    
    def _calculate_overall_coherence(self, doc) -> float:
        """Calculate overall coherence score."""
        if len(doc) == 0:
            return 0.5  # Neutral for empty text
        
        factors = []
        
        # Entity continuity
        entities = [ent.text for ent in doc.ents]
        entity_continuity = len(set(entities)) / max(len(entities), 1)
        factors.append(1.0 - entity_continuity)  # Lower diversity = higher coherence
        
        # Pronoun resolution quality
        pronouns = [t for t in doc if t.pos_ == 'PRON']
        pronoun_ratio = len(pronouns) / len(doc)
        if pronoun_ratio < 0.1:  # Too few pronouns
            factors.append(0.7)
        elif pronoun_ratio > 0.3:  # Too many pronouns
            factors.append(0.6)
        else:
            factors.append(0.9)
        
        # Discourse marker presence
        discourse_marker_count = 0
        for sent in doc.sents:
            if self._find_discourse_markers_in_sentence(sent):
                discourse_marker_count += 1
        
        discourse_factor = min(discourse_marker_count / len(list(doc.sents)), 1.0)
        factors.append(discourse_factor)
        
        return sum(factors) / len(factors)
    
    def _assess_topic_consistency(self, doc) -> float:
        """Assess consistency of topic throughout text."""
        # Simple implementation: check entity overlap between sentences
        sentences = list(doc.sents)
        if len(sentences) <= 1:
            return 1.0
        
        overlaps = []
        for i in range(len(sentences) - 1):
            sent1_entities = {ent.text.lower() for ent in sentences[i].ents}
            sent2_entities = {ent.text.lower() for ent in sentences[i + 1].ents}
            
            if sent1_entities or sent2_entities:
                overlap = len(sent1_entities & sent2_entities) / len(sent1_entities | sent2_entities)
            else:
                overlap = 0.5  # Neutral when no entities
            
            overlaps.append(overlap)
        
        return sum(overlaps) / len(overlaps) if overlaps else 0.5
    
    def _calculate_lexical_cohesion(self, doc) -> float:
        """Calculate lexical cohesion score."""
        # Count repeated content words
        content_words = [t.lemma_.lower() for t in doc if t.pos_ in ['NOUN', 'VERB', 'ADJ'] and not t.is_stop]
        word_counts = Counter(content_words)
        repeated_words = [word for word, count in word_counts.items() if count > 1]
        
        cohesion_score = len(repeated_words) / max(len(set(content_words)), 1)
        return min(cohesion_score, 1.0)
    
    def _assess_reference_clarity(self, doc) -> float:
        """Assess clarity of references."""
        pronouns = [t for t in doc if t.pos_ == 'PRON' and t.text.lower() not in ['i', 'you']]
        if not pronouns:
            return 1.0  # No pronouns to assess
        
        # Simple heuristic: pronouns should have clear antecedents nearby
        clear_references = 0
        for pronoun in pronouns:
            # Look for potential antecedents within 10 tokens
            window_start = max(0, pronoun.i - 10)
            window_tokens = doc[window_start:pronoun.i]
            antecedents = [t for t in window_tokens if t.pos_ in ['NOUN', 'PROPN']]
            
            if antecedents:
                clear_references += 1
        
        return clear_references / len(pronouns)
    
    def _find_repeated_entities(self, doc) -> List[str]:
        """Find entities mentioned multiple times."""
        entity_counts = Counter([ent.text for ent in doc.ents])
        return [entity for entity, count in entity_counts.items() if count > 1]
    
    def _assess_semantic_field_consistency(self, doc) -> float:
        """Assess consistency of semantic fields."""
        # Simple implementation: check POS tag distribution
        pos_counts = Counter([t.pos_ for t in doc if not t.is_space])
        
        if not pos_counts:
            return 0.5  # Neutral when no tokens
        
        # Calculate entropy (lower entropy = more consistent)
        import math
        total = sum(pos_counts.values())
        entropy = -sum((count/total) * math.log2(count/total) for count in pos_counts.values() if count > 0)
        
        # Normalize entropy (rough approximation)
        max_entropy = 4.0  # Approximate max for typical text
        return 1.0 - min(entropy / max_entropy, 1.0)
    
    def _assess_discourse_flow(self, doc) -> float:
        """Assess quality of discourse progression."""
        sentences = list(doc.sents)
        if len(sentences) <= 1:
            return 1.0
        
        flow_indicators = 0
        total_transitions = len(sentences) - 1
        
        for i in range(len(sentences) - 1):
            # Check for discourse markers
            if self._find_discourse_markers_in_sentence(sentences[i + 1]):
                flow_indicators += 1
            
            # Check for entity continuity
            sent1_entities = {ent.text.lower() for ent in sentences[i].ents}
            sent2_entities = {ent.text.lower() for ent in sentences[i + 1].ents}
            if sent1_entities & sent2_entities:
                flow_indicators += 0.5
        
        return min(flow_indicators / total_transitions, 1.0)
    
    def _find_ambiguous_references(self, doc) -> List[str]:
        """Find potentially ambiguous references."""
        ambiguous = []
        
        # Find pronouns with multiple potential antecedents
        pronouns = [t for t in doc if t.pos_ == 'PRON' and t.text.lower() not in ['i', 'you']]
        
        for pronoun in pronouns:
            # Look for multiple potential antecedents
            window_start = max(0, pronoun.i - 15)
            window_tokens = doc[window_start:pronoun.i]
            antecedents = [t for t in window_tokens if t.pos_ in ['NOUN', 'PROPN']]
            
            if len(antecedents) >= 3:  # Multiple potential antecedents
                ambiguous.append(f"{pronoun.text}@{pronoun.idx}")
        
        return ambiguous
    
    def _calculate_confidence_effects(self, coreference_matches: List[CoreferenceMatch], 
                                    sentence_structures: List[SentenceStructure],
                                    semantic_coherence: SemanticCoherence,
                                    sentence_index: int) -> Dict[str, float]:
        """Calculate confidence effects from context analysis."""
        
        # Structural confidence (based on sentence containing error)
        if sentence_index < len(sentence_structures):
            error_sentence = sentence_structures[sentence_index]
            structural_confidence = self._calculate_structural_confidence(error_sentence)
        else:
            structural_confidence = 0.0
        
        # Coreference confidence
        coreference_confidence = self._calculate_coreference_confidence_effect(coreference_matches)
        
        # Coherence confidence
        coherence_confidence = self._map_coherence_to_confidence(semantic_coherence)
        
        # Discourse confidence
        discourse_confidence = self._calculate_discourse_confidence(sentence_structures)
        
        # Combine effects with weighting
        net_effect = (
            structural_confidence * 0.25 +
            coreference_confidence * 0.25 +
            coherence_confidence * 0.25 +
            discourse_confidence * 0.25
        )
        
        return {
            'structural': structural_confidence,
            'coreference': coreference_confidence,
            'coherence': coherence_confidence,
            'discourse': discourse_confidence,
            'net_effect': net_effect
        }
    
    def _calculate_structural_confidence(self, sentence: SentenceStructure) -> float:
        """Calculate confidence based on sentence structure."""
        confidence = 0.0
        
        # Complexity factor (moderate complexity is good)
        if 0.3 <= sentence.complexity_score <= 0.7:
            confidence += 0.15  # Good complexity
        elif sentence.complexity_score < 0.2:
            confidence -= 0.1   # Too simple
        else:
            confidence -= 0.05  # Too complex
        
        # Formality indicators
        confidence += len(sentence.formality_indicators) * 0.02
        
        # Discourse markers
        confidence += len(sentence.discourse_markers) * 0.03
        
        # Structural features
        if sentence.has_passive_voice:
            confidence += 0.05  # Formal structure
        
        if sentence.has_subordinate_clauses and sentence.clause_count <= 3:
            confidence += 0.08  # Good subordination
        
        # Limit range
        return max(-0.2, min(0.2, confidence))
    
    def _calculate_coreference_confidence_effect(self, matches: List[CoreferenceMatch]) -> float:
        """Calculate confidence effect from coreference analysis."""
        if not matches:
            return 0.0
        
        # Average confidence of coreference links
        avg_confidence = sum(match.confidence for match in matches) / len(matches)
        
        # Convert to confidence effect
        if avg_confidence >= 0.8:
            return 0.15   # High confidence in references
        elif avg_confidence >= 0.6:
            return 0.05   # Moderate confidence
        elif avg_confidence >= 0.4:
            return -0.05  # Low confidence
        else:
            return -0.15  # Very unclear references
    
    def _map_coherence_to_confidence(self, coherence: SemanticCoherence) -> float:
        """Map semantic coherence to confidence effect."""
        effect = 0.0
        
        # Overall coherence
        if coherence.coherence_score >= 0.7:
            effect += 0.1
        elif coherence.coherence_score <= 0.3:
            effect -= 0.1
        
        # Reference clarity
        if coherence.reference_clarity >= 0.8:
            effect += 0.05
        elif coherence.reference_clarity <= 0.4:
            effect -= 0.08
        
        # Discourse flow
        if coherence.discourse_flow_score >= 0.7:
            effect += 0.05
        elif coherence.discourse_flow_score <= 0.3:
            effect -= 0.05
        
        # Ambiguous references penalty
        effect -= len(coherence.ambiguous_references) * 0.02
        
        return max(-0.2, min(0.2, effect))
    
    def _calculate_discourse_confidence(self, sentences: List[SentenceStructure]) -> float:
        """Calculate confidence from discourse analysis."""
        if not sentences:
            return 0.0
        
        # Count discourse markers
        total_markers = sum(len(sent.discourse_markers) for sent in sentences)
        marker_ratio = total_markers / len(sentences)
        
        # Optimal discourse marker density
        if 0.3 <= marker_ratio <= 0.8:
            discourse_effect = 0.1
        elif marker_ratio < 0.1:
            discourse_effect = -0.05  # Too few connectors
        else:
            discourse_effect = -0.02  # Too many connectors
        
        # Formality consistency
        total_formality = sum(len(sent.formality_indicators) for sent in sentences)
        formality_ratio = total_formality / len(sentences)
        
        if formality_ratio >= 0.5:
            discourse_effect += 0.08  # Consistent formality
        elif formality_ratio <= 0.1:
            discourse_effect -= 0.05  # Very informal
        
        return max(-0.15, min(0.15, discourse_effect))
    
    def _generate_explanation(self, coreference_matches: List[CoreferenceMatch],
                            sentence_structures: List[SentenceStructure],
                            semantic_coherence: SemanticCoherence,
                            confidence_effects: Dict[str, float]) -> str:
        """Generate human-readable explanation of context analysis."""
        parts = []
        
        # Overall effect
        net_effect = confidence_effects['net_effect']
        if net_effect > 0.05:
            parts.append(f"🔼 Context analysis increased confidence by {net_effect:+.3f}")
        elif net_effect < -0.05:
            parts.append(f"🔽 Context analysis decreased confidence by {net_effect:+.3f}")
        else:
            parts.append(f"➡️ Context analysis had minimal effect ({net_effect:+.3f})")
        
        # Structural analysis
        structural = confidence_effects['structural']
        if abs(structural) > 0.02:
            parts.append(f"\n🏗️ Sentence structure: {structural:+.3f}")
            if structural > 0:
                parts.append("   • Well-structured with appropriate complexity")
            else:
                parts.append("   • Overly complex or too simplistic structure")
        
        # Coreference analysis
        coreference = confidence_effects['coreference']
        if coreference_matches:
            parts.append(f"\n🔗 Reference clarity: {coreference:+.3f}")
            high_conf_refs = [m for m in coreference_matches if m.confidence >= 0.7]
            if high_conf_refs:
                parts.append(f"   • {len(high_conf_refs)} clear reference(s)")
            
            unclear_refs = [m for m in coreference_matches if m.confidence < 0.5]
            if unclear_refs:
                parts.append(f"   • {len(unclear_refs)} unclear reference(s)")
        
        # Coherence analysis
        coherence = confidence_effects['coherence']
        if abs(coherence) > 0.02:
            parts.append(f"\n🎯 Semantic coherence: {coherence:+.3f}")
            if semantic_coherence.coherence_score >= 0.7:
                parts.append("   • Strong topical consistency")
            if semantic_coherence.reference_clarity >= 0.8:
                parts.append("   • Clear pronoun references")
            if semantic_coherence.ambiguous_references:
                parts.append(f"   • {len(semantic_coherence.ambiguous_references)} ambiguous reference(s)")
        
        # Discourse analysis
        discourse = confidence_effects['discourse']
        if abs(discourse) > 0.02:
            parts.append(f"\n💬 Discourse flow: {discourse:+.3f}")
            total_markers = sum(len(s.discourse_markers) for s in sentence_structures)
            if total_markers >= 2:
                parts.append(f"   • {total_markers} discourse markers found")
            
            formal_indicators = sum(len(s.formality_indicators) for s in sentence_structures)
            if formal_indicators >= 2:
                parts.append(f"   • {formal_indicators} formality indicators")
        
        return '\n'.join(parts)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            'spacy_model': self.spacy_model,
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_rate': self._cache_hits / max(1, self._cache_hits + self._cache_misses),
            'nlp_results_cached': len(self._nlp_cache),
            'analysis_results_cached': len(self._analysis_cache)
        }
    
    def clear_caches(self) -> None:
        """Clear all caches."""
        self._nlp_cache.clear()
        self._analysis_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0