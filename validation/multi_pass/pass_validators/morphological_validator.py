"""
MorphologicalValidator Class
Concrete implementation of BasePassValidator for morphological and syntactic validation.
Uses NLP analysis to validate errors based on linguistic structure.
"""

import time
import spacy
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass
from collections import defaultdict

from ..base_validator import (
    BasePassValidator, ValidationDecision, ValidationConfidence,
    ValidationEvidence, ValidationResult, ValidationContext
)


@dataclass
class POSAnalysis:
    """Part-of-speech analysis results."""
    
    token: str                    # The analyzed token
    pos: str                      # Part-of-speech tag
    tag: str                      # Fine-grained POS tag
    lemma: str                    # Lemmatized form
    confidence: float             # Confidence in POS assignment
    context_pos: List[str]        # POS tags of surrounding context
    morphological_features: Dict[str, str]  # Morphological features


@dataclass
class DependencyAnalysis:
    """Dependency parsing analysis results."""
    
    token: str                    # The analyzed token
    dependency_relation: str      # Dependency relation (e.g., 'nsubj', 'dobj')
    head: str                     # Head token
    head_pos: str                 # Head token POS
    children: List[str]           # Child tokens
    sentence_position: float      # Position in sentence (0-1)
    dependency_distance: int      # Distance from head
    syntactic_role: str           # Semantic role description


@dataclass
class MorphologicalAmbiguity:
    """Morphological ambiguity detection results."""
    
    token: str                    # The ambiguous token
    possible_interpretations: List[Tuple[str, float]]  # (interpretation, confidence)
    ambiguity_type: str           # Type of ambiguity (e.g., 'pos', 'lemma', 'meaning')
    resolution_confidence: float  # Confidence in resolution
    context_clues: List[str]      # Context that helps resolve ambiguity


class MorphologicalValidator(BasePassValidator):
    """
    Morphological and syntactic validator using NLP analysis.
    
    This validator focuses on:
    - POS tagging validation for grammatical correctness
    - Dependency parsing for syntactic structure validation
    - Morphological ambiguity detection and resolution
    - Cross-model linguistic verification
    
    It integrates with SpaCy for advanced NLP analysis and provides
    evidence-based validation decisions with detailed linguistic reasoning.
    """
    
    def __init__(self, 
                 spacy_model: str = "en_core_web_sm",
                 enable_dependency_parsing: bool = True,
                 enable_ambiguity_detection: bool = True,
                 cache_nlp_results: bool = True,
                 min_confidence_threshold: float = 0.6):
        """
        Initialize the morphological validator.
        
        Args:
            spacy_model: SpaCy model to use for NLP analysis
            enable_dependency_parsing: Whether to perform dependency analysis
            enable_ambiguity_detection: Whether to detect morphological ambiguities
            cache_nlp_results: Whether to cache NLP analysis results
            min_confidence_threshold: Minimum confidence for decisive decisions
        """
        super().__init__(
            validator_name="morphological_validator",
            min_confidence_threshold=min_confidence_threshold
        )
        
        # Configuration
        self.spacy_model_name = spacy_model
        self.enable_dependency_parsing = enable_dependency_parsing
        self.enable_ambiguity_detection = enable_ambiguity_detection
        self.cache_nlp_results = cache_nlp_results
        
        # Load SpaCy model
        try:
            self.nlp = spacy.load(spacy_model)
            print(f"✓ Loaded SpaCy model: {spacy_model}")
        except OSError:
            # Fallback to smaller model or raise error
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print(f"⚠️ Fallback: Loaded en_core_web_sm instead of {spacy_model}")
            except OSError:
                raise RuntimeError(f"Could not load SpaCy model {spacy_model} or fallback model")
        
        # NLP analysis cache
        self._nlp_cache: Dict[str, Any] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Morphological patterns and rules
        self._initialize_morphological_patterns()
        
        # Performance tracking
        self._analysis_times = {
            'pos_analysis': [],
            'dependency_analysis': [],
            'ambiguity_detection': []
        }
    
    def _initialize_morphological_patterns(self):
        """Initialize morphological patterns and validation rules."""
        
        # Common grammatical error patterns
        self.grammar_patterns = {
            'subject_verb_agreement': {
                'singular_subjects': {'he', 'she', 'it', 'this', 'that'},
                'plural_subjects': {'they', 'these', 'those', 'we'},
                'singular_verbs': {'is', 'was', 'has', 'does'},
                'plural_verbs': {'are', 'were', 'have', 'do'}
            },
            'possessive_vs_contraction': {
                'possessive_pronouns': {'its', 'yours', 'theirs', 'hers', 'ours'},
                'contractions': {"it's", "you're", "they're", "she's", "we're"}
            },
            'article_noun_agreement': {
                'definite': 'the',
                'indefinite_vowel': 'an',
                'indefinite_consonant': 'a'
            }
        }
        
        # POS tag hierarchies for validation
        self.pos_hierarchies = {
            'noun_tags': {'NN', 'NNS', 'NNP', 'NNPS'},
            'verb_tags': {'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'},
            'adjective_tags': {'JJ', 'JJR', 'JJS'},
            'adverb_tags': {'RB', 'RBR', 'RBS'},
            'pronoun_tags': {'PRP', 'PRP$', 'WP', 'WP$'},
            'determiner_tags': {'DT', 'WDT', 'PDT'}
        }
        
        # Dependency relation validations
        self.dependency_validations = {
            'subject_relations': {'nsubj', 'nsubjpass', 'csubj', 'csubjpass'},
            'object_relations': {'dobj', 'iobj', 'pobj'},
            'modifier_relations': {'amod', 'advmod', 'nmod', 'nummod'},
            'clause_relations': {'ccomp', 'xcomp', 'advcl', 'acl'}
        }
        
        # Morphological ambiguity patterns
        self.ambiguity_patterns = {
            'homonyms': {
                'bank': [('financial_institution', 0.6), ('river_side', 0.4)],
                'bark': [('dog_sound', 0.7), ('tree_covering', 0.3)],
                'bear': [('animal', 0.5), ('carry', 0.5)],
                'lead': [('guide', 0.6), ('metal', 0.4)]
            },
            'pos_ambiguous': {
                'run': [('verb', 0.8), ('noun', 0.2)],
                'light': [('adjective', 0.6), ('noun', 0.3), ('verb', 0.1)],
                'fast': [('adjective', 0.7), ('adverb', 0.3)],
                'well': [('adverb', 0.6), ('noun', 0.3), ('adjective', 0.1)]
            }
        }
    
    def _validate_error(self, context: ValidationContext) -> ValidationResult:
        """
        Validate an error using morphological and syntactic analysis.
        
        Args:
            context: Validation context containing error and metadata
            
        Returns:
            ValidationResult with morphological analysis and decision
        """
        start_time = time.time()
        
        try:
            # Perform NLP analysis
            doc = self._analyze_text(context.text)
            
            # Find the error token and its context
            error_token, error_context = self._locate_error_in_doc(doc, context.error_position, context.error_text)
            
            if error_token is None:
                return self._create_uncertain_result(
                    context, 
                    "Could not locate error token in NLP analysis",
                    time.time() - start_time
                )
            
            # Perform morphological analyses
            evidence = []
            
            # 1. POS tagging validation
            pos_analysis = self._analyze_pos_tagging(error_token, error_context, context)
            if pos_analysis:
                evidence.append(self._create_pos_evidence(pos_analysis, context))
            
            # 2. Dependency parsing validation
            if self.enable_dependency_parsing:
                dep_analysis = self._analyze_dependency_structure(error_token, error_context, context)
                if dep_analysis:
                    evidence.append(self._create_dependency_evidence(dep_analysis, context))
            
            # 3. Morphological ambiguity detection
            if self.enable_ambiguity_detection:
                ambiguity_analysis = self._detect_morphological_ambiguity(error_token, error_context, context)
                if ambiguity_analysis:
                    evidence.append(self._create_ambiguity_evidence(ambiguity_analysis, context))
            
            # 4. Cross-model linguistic verification
            cross_model_evidence = self._perform_cross_model_verification(error_token, error_context, context)
            if cross_model_evidence:
                evidence.append(cross_model_evidence)
            
            # Make validation decision based on evidence
            decision, confidence_score, reasoning = self._make_morphological_decision(evidence, context)
            
            return ValidationResult(
                validator_name=self.validator_name,
                decision=decision,
                confidence=self._convert_confidence_to_level(confidence_score),
                confidence_score=confidence_score,
                evidence=evidence,
                reasoning=reasoning,
                error_text=context.error_text,
                error_position=context.error_position,
                rule_type=context.rule_type,
                rule_name=context.rule_name,
                validation_time=time.time() - start_time,
                metadata={
                    'error_token_pos': error_token.pos_,
                    'error_token_tag': error_token.tag_,
                    'error_token_dep': error_token.dep_,
                    'sentence_length': len(error_token.sent),
                    'analysis_types_used': [e.evidence_type for e in evidence],
                    'spacy_model': self.spacy_model_name
                }
            )
            
        except Exception as e:
            return self._create_error_result(context, str(e), time.time() - start_time)
    
    def _analyze_text(self, text: str):
        """Analyze text with SpaCy, using cache if enabled."""
        if self.cache_nlp_results and text in self._nlp_cache:
            self._cache_hits += 1
            return self._nlp_cache[text]
        
        self._cache_misses += 1
        doc = self.nlp(text)
        
        if self.cache_nlp_results:
            self._nlp_cache[text] = doc
        
        return doc
    
    def _locate_error_in_doc(self, doc, error_position: int, error_text: str):
        """Locate the error token in the SpaCy document."""
        # Find token that contains or is closest to the error position
        best_token = None
        min_distance = float('inf')
        
        for token in doc:
            # Check if token contains the error position
            if token.idx <= error_position <= token.idx + len(token.text):
                best_token = token
                break
            
            # Track closest token as fallback
            distance = min(abs(token.idx - error_position), 
                          abs(token.idx + len(token.text) - error_position))
            if distance < min_distance:
                min_distance = distance
                best_token = token
        
        if best_token is None:
            return None, None
        
        # Get surrounding context (3 tokens before and after)
        sent = best_token.sent
        token_idx = best_token.i - sent.start
        context_start = max(0, token_idx - 3)
        context_end = min(len(sent), token_idx + 4)
        context_tokens = sent[context_start:context_end]
        
        return best_token, context_tokens
    
    def _analyze_pos_tagging(self, token, context_tokens, validation_context: ValidationContext) -> Optional[POSAnalysis]:
        """Analyze POS tagging for validation."""
        start_time = time.time()
        
        try:
            # Extract morphological features
            morph_features = {}
            if token.morph:
                for feature in str(token.morph).split('|'):
                    if '=' in feature:
                        key, value = feature.split('=', 1)
                        morph_features[key] = value
            
            # Analyze context POS
            context_pos = [t.pos_ for t in context_tokens]
            
            # Calculate POS confidence based on context consistency
            pos_confidence = self._calculate_pos_confidence(token, context_tokens, validation_context)
            
            analysis = POSAnalysis(
                token=token.text,
                pos=token.pos_,
                tag=token.tag_,
                lemma=token.lemma_,
                confidence=pos_confidence,
                context_pos=context_pos,
                morphological_features=morph_features
            )
            
            self._analysis_times['pos_analysis'].append(time.time() - start_time)
            return analysis
            
        except Exception:
            return None
    
    def _analyze_dependency_structure(self, token, context_tokens, validation_context: ValidationContext) -> Optional[DependencyAnalysis]:
        """Analyze dependency structure for validation."""
        start_time = time.time()
        
        try:
            # Get dependency information
            head = token.head
            children = list(token.children)
            
            # Calculate sentence position
            sent = token.sent
            sentence_position = (token.i - sent.start) / len(sent)
            
            # Calculate dependency distance
            dependency_distance = abs(token.i - head.i)
            
            # Determine syntactic role
            syntactic_role = self._determine_syntactic_role(token)
            
            analysis = DependencyAnalysis(
                token=token.text,
                dependency_relation=token.dep_,
                head=head.text,
                head_pos=head.pos_,
                children=[child.text for child in children],
                sentence_position=sentence_position,
                dependency_distance=dependency_distance,
                syntactic_role=syntactic_role
            )
            
            self._analysis_times['dependency_analysis'].append(time.time() - start_time)
            return analysis
            
        except Exception:
            return None
    
    def _detect_morphological_ambiguity(self, token, context_tokens, validation_context: ValidationContext) -> Optional[MorphologicalAmbiguity]:
        """Detect and analyze morphological ambiguities."""
        start_time = time.time()
        
        try:
            token_lower = token.text.lower()
            possible_interpretations = []
            ambiguity_type = "none"
            context_clues = []
            
            # Check for known ambiguous words
            if token_lower in self.ambiguity_patterns['homonyms']:
                possible_interpretations = self.ambiguity_patterns['homonyms'][token_lower]
                ambiguity_type = "semantic"
                context_clues = self._extract_semantic_context_clues(token, context_tokens)
                
            elif token_lower in self.ambiguity_patterns['pos_ambiguous']:
                possible_interpretations = self.ambiguity_patterns['pos_ambiguous'][token_lower]
                ambiguity_type = "pos"
                context_clues = self._extract_pos_context_clues(token, context_tokens)
            
            # If ambiguity detected, calculate resolution confidence
            if possible_interpretations:
                resolution_confidence = self._calculate_ambiguity_resolution_confidence(
                    token, context_tokens, possible_interpretations, context_clues
                )
                
                analysis = MorphologicalAmbiguity(
                    token=token.text,
                    possible_interpretations=possible_interpretations,
                    ambiguity_type=ambiguity_type,
                    resolution_confidence=resolution_confidence,
                    context_clues=context_clues
                )
                
                self._analysis_times['ambiguity_detection'].append(time.time() - start_time)
                return analysis
            
            return None
            
        except Exception:
            return None
    
    def _perform_cross_model_verification(self, token, context_tokens, validation_context: ValidationContext) -> Optional[ValidationEvidence]:
        """Perform cross-model linguistic verification."""
        try:
            # For now, implement basic verification using multiple analysis approaches
            # In a full implementation, this might use multiple NLP models
            
            # Verify POS consistency across different analysis methods
            pos_consistency = self._verify_pos_consistency(token, context_tokens)
            
            # Verify morphological consistency
            morph_consistency = self._verify_morphological_consistency(token, validation_context)
            
            # Calculate overall cross-model confidence
            cross_model_confidence = (pos_consistency + morph_consistency) / 2
            
            if cross_model_confidence > 0.3:  # Only create evidence if meaningful
                return ValidationEvidence(
                    evidence_type="cross_model_verification",
                    confidence=cross_model_confidence,
                    description=f"Cross-model verification shows {cross_model_confidence:.2f} consistency",
                    source_data={
                        'pos_consistency': pos_consistency,
                        'morphological_consistency': morph_consistency,
                        'verification_methods': ['pos_analysis', 'morphological_analysis']
                    }
                )
            
            return None
            
        except Exception:
            return None
    
    def _calculate_pos_confidence(self, token, context_tokens, validation_context: ValidationContext) -> float:
        """Calculate confidence in POS tagging decision."""
        confidence = 0.5  # Base confidence
        
        # Factor 1: Rule type relevance
        if validation_context.rule_type == "grammar":
            confidence += 0.2  # Grammar rules benefit from POS analysis
        elif validation_context.rule_type == "style":
            confidence += 0.1  # Style rules moderately benefit
        
        # Factor 2: POS tag certainty (based on SpaCy's internal consistency)
        if token.pos_ in ['NOUN', 'VERB', 'ADJ']:
            confidence += 0.15  # Major POS categories are more reliable
        
        # Factor 3: Context consistency
        expected_context = self._get_expected_pos_context(token.pos_)
        actual_context = [t.pos_ for t in context_tokens if t != token]
        context_match = len(set(expected_context) & set(actual_context)) / max(1, len(expected_context))
        confidence += context_match * 0.15
        
        return min(1.0, confidence)
    
    def _determine_syntactic_role(self, token) -> str:
        """Determine the syntactic role of a token."""
        dep = token.dep_
        
        role_mapping = {
            'nsubj': 'subject',
            'nsubjpass': 'passive_subject',
            'dobj': 'direct_object',
            'iobj': 'indirect_object',
            'pobj': 'prepositional_object',
            'amod': 'adjective_modifier',
            'advmod': 'adverb_modifier',
            'det': 'determiner',
            'aux': 'auxiliary',
            'cop': 'copula',
            'cc': 'coordinating_conjunction',
            'prep': 'preposition'
        }
        
        return role_mapping.get(dep, f"other_{dep}")
    
    def _extract_semantic_context_clues(self, token, context_tokens) -> List[str]:
        """Extract context clues for semantic disambiguation."""
        clues = []
        
        # Look for domain-specific words
        for context_token in context_tokens:
            if context_token != token:
                # Financial context for 'bank'
                if context_token.lemma_ in ['money', 'account', 'financial', 'deposit', 'loan']:
                    clues.append(f"financial_context:{context_token.text}")
                # Nature context for 'bank' or 'bark'
                elif context_token.lemma_ in ['river', 'water', 'tree', 'dog', 'animal']:
                    clues.append(f"nature_context:{context_token.text}")
        
        return clues
    
    def _extract_pos_context_clues(self, token, context_tokens) -> List[str]:
        """Extract context clues for POS disambiguation."""
        clues = []
        
        for i, context_token in enumerate(context_tokens):
            if context_token != token:
                # Check for determiners before the token (suggests noun)
                if i < len(context_tokens) - 1 and context_tokens[i + 1] == token and context_token.pos_ == 'DET':
                    clues.append(f"determiner_before:{context_token.text}")
                # Check for auxiliaries before the token (suggests verb)
                elif i < len(context_tokens) - 1 and context_tokens[i + 1] == token and context_token.pos_ == 'AUX':
                    clues.append(f"auxiliary_before:{context_token.text}")
        
        return clues
    
    def _calculate_ambiguity_resolution_confidence(self, token, context_tokens, 
                                                 possible_interpretations, context_clues) -> float:
        """Calculate confidence in ambiguity resolution."""
        base_confidence = 0.3
        
        # More context clues = higher confidence
        clue_boost = min(0.4, len(context_clues) * 0.1)
        
        # Stronger interpretation dominance = higher confidence
        if possible_interpretations:
            max_interp_conf = max(conf for _, conf in possible_interpretations)
            dominance_boost = (max_interp_conf - 0.5) * 0.3 if max_interp_conf > 0.5 else 0
        else:
            dominance_boost = 0
        
        return min(1.0, base_confidence + clue_boost + dominance_boost)
    
    def _verify_pos_consistency(self, token, context_tokens) -> float:
        """Verify POS consistency using rule-based analysis."""
        # Simple heuristic: check if POS fits syntactic expectations
        pos = token.pos_
        
        # Check surrounding context for consistency
        prev_token = None
        next_token = None
        
        for i, t in enumerate(context_tokens):
            if t == token:
                if i > 0:
                    prev_token = context_tokens[i - 1]
                if i < len(context_tokens) - 1:
                    next_token = context_tokens[i + 1]
                break
        
        consistency = 0.5  # Base consistency
        
        # Rule-based consistency checks
        if pos == 'NOUN':
            # Nouns often follow determiners or adjectives
            if prev_token and prev_token.pos_ in ['DET', 'ADJ']:
                consistency += 0.3
            # Nouns often precede verbs in subject position
            if next_token and next_token.pos_ == 'VERB':
                consistency += 0.2
        
        elif pos == 'VERB':
            # Verbs often follow subjects (nouns/pronouns)
            if prev_token and prev_token.pos_ in ['NOUN', 'PRON']:
                consistency += 0.3
        
        return min(1.0, consistency)
    
    def _verify_morphological_consistency(self, token, validation_context: ValidationContext) -> float:
        """Verify morphological consistency with validation context."""
        consistency = 0.5  # Base consistency
        
        # Check if morphological analysis supports the error type
        if validation_context.rule_type == "grammar":
            # Grammar rules should have strong morphological signals
            if token.pos_ in ['VERB', 'NOUN', 'PRON']:
                consistency += 0.3
        
        elif validation_context.rule_type == "style":
            # Style rules have moderate morphological relevance
            if token.pos_ in ['ADV', 'ADJ']:
                consistency += 0.2
        
        # Check for morphological features that support validation
        if token.morph:
            consistency += 0.1  # Having morphological features is good
        
        return min(1.0, consistency)
    
    def _get_expected_pos_context(self, pos: str) -> List[str]:
        """Get expected POS context for a given POS tag."""
        context_expectations = {
            'NOUN': ['DET', 'ADJ', 'VERB'],
            'VERB': ['NOUN', 'PRON', 'AUX', 'ADV'],
            'ADJ': ['NOUN', 'ADV', 'VERB'],
            'ADV': ['VERB', 'ADJ'],
            'PRON': ['VERB', 'AUX'],
            'DET': ['NOUN', 'ADJ']
        }
        
        return context_expectations.get(pos, [])
    
    def _create_pos_evidence(self, analysis: POSAnalysis, context: ValidationContext) -> ValidationEvidence:
        """Create validation evidence from POS analysis."""
        return ValidationEvidence(
            evidence_type="pos_tagging",
            confidence=analysis.confidence,
            description=f"POS analysis: '{analysis.token}' tagged as {analysis.pos} ({analysis.tag}) with lemma '{analysis.lemma}'",
            source_data={
                'token': analysis.token,
                'pos': analysis.pos,
                'tag': analysis.tag,
                'lemma': analysis.lemma,
                'context_pos': analysis.context_pos,
                'morphological_features': analysis.morphological_features
            }
        )
    
    def _create_dependency_evidence(self, analysis: DependencyAnalysis, context: ValidationContext) -> ValidationEvidence:
        """Create validation evidence from dependency analysis."""
        return ValidationEvidence(
            evidence_type="dependency_parsing",
            confidence=self._calculate_dependency_confidence(analysis, context),
            description=f"Dependency analysis: '{analysis.token}' has {analysis.dependency_relation} relation to '{analysis.head}' ({analysis.syntactic_role})",
            source_data={
                'token': analysis.token,
                'dependency_relation': analysis.dependency_relation,
                'head': analysis.head,
                'head_pos': analysis.head_pos,
                'children': analysis.children,
                'sentence_position': analysis.sentence_position,
                'dependency_distance': analysis.dependency_distance,
                'syntactic_role': analysis.syntactic_role
            }
        )
    
    def _create_ambiguity_evidence(self, analysis: MorphologicalAmbiguity, context: ValidationContext) -> ValidationEvidence:
        """Create validation evidence from ambiguity analysis."""
        return ValidationEvidence(
            evidence_type="morphological_ambiguity",
            confidence=analysis.resolution_confidence,
            description=f"Ambiguity analysis: '{analysis.token}' has {analysis.ambiguity_type} ambiguity with {len(analysis.possible_interpretations)} interpretations",
            source_data={
                'token': analysis.token,
                'possible_interpretations': analysis.possible_interpretations,
                'ambiguity_type': analysis.ambiguity_type,
                'resolution_confidence': analysis.resolution_confidence,
                'context_clues': analysis.context_clues
            }
        )
    
    def _calculate_dependency_confidence(self, analysis: DependencyAnalysis, context: ValidationContext) -> float:
        """Calculate confidence in dependency analysis."""
        confidence = 0.5  # Base confidence
        
        # Factor 1: Rule type relevance
        if context.rule_type == "grammar":
            confidence += 0.2  # Grammar rules benefit strongly from dependency analysis
        
        # Factor 2: Syntactic role clarity
        if analysis.syntactic_role in ['subject', 'direct_object', 'adjective_modifier']:
            confidence += 0.15  # Clear syntactic roles are more reliable
        
        # Factor 3: Dependency distance (closer = more reliable)
        distance_factor = max(0, 0.15 - (analysis.dependency_distance * 0.02))
        confidence += distance_factor
        
        # Factor 4: Sentence position (middle positions often more stable)
        position_factor = 0.1 * (1 - abs(analysis.sentence_position - 0.5) * 2)
        confidence += position_factor
        
        return min(1.0, confidence)
    
    def _make_morphological_decision(self, evidence: List[ValidationEvidence], 
                                   context: ValidationContext) -> Tuple[ValidationDecision, float, str]:
        """Make validation decision based on morphological evidence."""
        if not evidence:
            return ValidationDecision.UNCERTAIN, 0.3, "No morphological evidence available for validation"
        
        # Calculate weighted average confidence
        total_weight = sum(e.confidence * e.weight for e in evidence)
        total_weights = sum(e.weight for e in evidence)
        avg_confidence = total_weight / total_weights if total_weights > 0 else 0.3
        
        # Analyze evidence types
        evidence_types = [e.evidence_type for e in evidence]
        
        # Decision logic based on evidence and rule type
        if context.rule_type == "grammar":
            # Grammar rules: Strong morphological evidence suggests acceptance
            if avg_confidence >= 0.7 and any(et in ['pos_tagging', 'dependency_parsing'] for et in evidence_types):
                decision = ValidationDecision.ACCEPT
                reasoning = f"Strong morphological evidence ({avg_confidence:.2f}) supports grammar validation"
                
            elif avg_confidence < 0.4:
                decision = ValidationDecision.REJECT
                reasoning = f"Weak morphological evidence ({avg_confidence:.2f}) suggests grammar rule may not apply"
                
            else:
                decision = ValidationDecision.UNCERTAIN
                reasoning = f"Moderate morphological evidence ({avg_confidence:.2f}) - grammar validation uncertain"
        
        elif context.rule_type == "style":
            # Style rules: Morphological evidence is supportive but not decisive
            if avg_confidence >= 0.6:
                decision = ValidationDecision.ACCEPT
                reasoning = f"Morphological analysis ({avg_confidence:.2f}) supports style rule applicability"
                
            else:
                decision = ValidationDecision.UNCERTAIN
                reasoning = f"Limited morphological relevance ({avg_confidence:.2f}) for style validation"
        
        else:
            # Other rule types: Conservative approach
            if avg_confidence >= 0.8:
                decision = ValidationDecision.ACCEPT
                reasoning = f"Very strong morphological evidence ({avg_confidence:.2f}) supports validation"
                
            elif avg_confidence < 0.3:
                decision = ValidationDecision.REJECT
                reasoning = f"Very weak morphological evidence ({avg_confidence:.2f}) suggests rule not applicable"
                
            else:
                decision = ValidationDecision.UNCERTAIN
                reasoning = f"Morphological evidence ({avg_confidence:.2f}) inconclusive for {context.rule_type} rule"
        
        return decision, avg_confidence, reasoning
    
    def _create_uncertain_result(self, context: ValidationContext, reason: str, validation_time: float) -> ValidationResult:
        """Create an uncertain validation result."""
        return ValidationResult(
            validator_name=self.validator_name,
            decision=ValidationDecision.UNCERTAIN,
            confidence=ValidationConfidence.LOW,
            confidence_score=0.3,
            evidence=[ValidationEvidence(
                evidence_type="error",
                confidence=0.0,
                description=reason,
                source_data={"error_type": "analysis_failure"}
            )],
            reasoning=f"Morphological validation uncertain: {reason}",
            error_text=context.error_text,
            error_position=context.error_position,
            rule_type=context.rule_type,
            rule_name=context.rule_name,
            validation_time=validation_time,
            metadata={"validation_failure": True}
        )
    
    def _create_error_result(self, context: ValidationContext, error_msg: str, validation_time: float) -> ValidationResult:
        """Create an error validation result."""
        return ValidationResult(
            validator_name=self.validator_name,
            decision=ValidationDecision.UNCERTAIN,
            confidence=ValidationConfidence.LOW,
            confidence_score=0.0,
            evidence=[ValidationEvidence(
                evidence_type="error",
                confidence=0.0,
                description=f"Validation error: {error_msg}",
                source_data={"error_message": error_msg}
            )],
            reasoning=f"Morphological validation failed due to error: {error_msg}",
            error_text=context.error_text,
            error_position=context.error_position,
            rule_type=context.rule_type,
            rule_name=context.rule_name,
            validation_time=validation_time,
            metadata={"validation_error": True}
        )
    
    def get_validator_info(self) -> Dict[str, Any]:
        """Get comprehensive information about this validator."""
        return {
            "name": self.validator_name,
            "type": "morphological_validator",
            "version": "1.0.0",
            "description": "Validates errors using morphological and syntactic NLP analysis",
            "capabilities": [
                "pos_tagging",
                "dependency_parsing",
                "morphological_ambiguity_detection",
                "cross_model_verification",
                "syntactic_structure_analysis"
            ],
            "specialties": [
                "grammar_validation",
                "syntactic_correctness",
                "morphological_consistency",
                "linguistic_structure_analysis"
            ],
            "configuration": {
                "spacy_model": self.spacy_model_name,
                "dependency_parsing_enabled": self.enable_dependency_parsing,
                "ambiguity_detection_enabled": self.enable_ambiguity_detection,
                "nlp_caching_enabled": self.cache_nlp_results,
                "min_confidence_threshold": self.min_confidence_threshold
            },
            "performance_characteristics": {
                "best_for_rule_types": ["grammar", "syntax"],
                "moderate_for_rule_types": ["style", "punctuation"],
                "limited_for_rule_types": ["terminology", "formatting"],
                "avg_processing_time_ms": self._get_average_processing_time(),
                "cache_hit_rate": self._get_cache_hit_rate()
            },
            "linguistic_patterns": {
                "grammar_patterns_count": len(self.grammar_patterns),
                "pos_hierarchies_count": len(self.pos_hierarchies),
                "dependency_validations_count": len(self.dependency_validations),
                "ambiguity_patterns_count": len(self.ambiguity_patterns)
            }
        }
    
    def _get_average_processing_time(self) -> float:
        """Get average processing time across all analysis types."""
        all_times = []
        for analysis_type, times in self._analysis_times.items():
            all_times.extend(times)
        
        return (sum(all_times) / len(all_times) * 1000) if all_times else 0.0
    
    def _get_cache_hit_rate(self) -> float:
        """Get NLP cache hit rate."""
        total = self._cache_hits + self._cache_misses
        return self._cache_hits / total if total > 0 else 0.0
    
    def clear_caches(self) -> None:
        """Clear all caches."""
        self._nlp_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Clear performance tracking
        for analysis_type in self._analysis_times:
            self._analysis_times[analysis_type].clear()
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get detailed analysis statistics."""
        return {
            "nlp_cache": {
                "cached_texts": len(self._nlp_cache),
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "hit_rate": self._get_cache_hit_rate()
            },
            "analysis_performance": {
                analysis_type: {
                    "total_analyses": len(times),
                    "average_time_ms": (sum(times) / len(times) * 1000) if times else 0.0,
                    "min_time_ms": (min(times) * 1000) if times else 0.0,
                    "max_time_ms": (max(times) * 1000) if times else 0.0
                }
                for analysis_type, times in self._analysis_times.items()
            },
            "configuration_status": {
                "spacy_model_loaded": self.nlp is not None,
                "dependency_parsing": self.enable_dependency_parsing,
                "ambiguity_detection": self.enable_ambiguity_detection,
                "nlp_caching": self.cache_nlp_results
            }
        }