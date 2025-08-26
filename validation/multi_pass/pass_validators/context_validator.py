"""
ContextValidator Class
Concrete implementation of BasePassValidator for contextual and discourse validation.
Uses discourse analysis to validate errors based on contextual appropriateness and coherence.
"""

import time
import spacy
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass
from collections import defaultdict, Counter
import re

from ..base_validator import (
    BasePassValidator, ValidationDecision, ValidationConfidence,
    ValidationEvidence, ValidationResult, ValidationContext
)


@dataclass
class CoreferenceValidation:
    """Coreference validation results."""
    
    token: str                       # The analyzed token
    is_pronoun: bool                 # Whether token is a pronoun
    antecedent_found: bool           # Whether clear antecedent exists
    antecedent_text: Optional[str]   # Text of the antecedent if found
    antecedent_distance: int         # Distance to antecedent in tokens
    resolution_confidence: float     # Confidence in coreference resolution
    ambiguity_detected: bool         # Whether ambiguous references exist
    context_clarity: float           # Overall clarity of reference context


@dataclass
class DiscourseFlowAnalysis:
    """Discourse flow and coherence analysis results."""
    
    sentence_count: int              # Number of sentences in context
    transition_markers: List[str]    # Discourse markers found
    coherence_score: float           # Overall discourse coherence (0-1)
    flow_disruption: bool            # Whether flow is disrupted
    topic_consistency: float         # Topic consistency across sentences
    logical_progression: float       # Logical flow score
    discourse_structure: str         # Type of discourse structure
    context_window_used: int         # Size of context analyzed


@dataclass
class SemanticConsistencyCheck:
    """Semantic consistency validation results."""
    
    semantic_field: str              # Primary semantic field of context
    consistency_score: float         # Semantic consistency (0-1)
    conflicting_terms: List[str]     # Terms that conflict semantically
    domain_coherence: float          # Domain-specific coherence
    register_consistency: float      # Consistency of language register
    terminology_alignment: float     # Alignment with expected terminology
    semantic_anomalies: List[str]    # Detected semantic anomalies


@dataclass
class ContextualAppropriateness:
    """Contextual appropriateness assessment results."""
    
    formality_level: str             # Detected formality level
    audience_appropriateness: float  # Appropriateness for target audience
    style_consistency: float         # Consistency with surrounding style
    tone_alignment: float            # Alignment with expected tone
    register_appropriateness: float  # Register appropriateness score
    context_mismatch: bool           # Whether context mismatch detected
    appropriateness_factors: List[str] # Factors affecting appropriateness


class ContextValidator(BasePassValidator):
    """
    Contextual and discourse validator for multi-pass validation.
    
    This validator focuses on:
    - Coreference validation and pronoun resolution
    - Discourse flow and coherence checking
    - Semantic consistency within context
    - Contextual appropriateness assessment
    
    It leverages NLP analysis to understand context and provides
    evidence-based validation decisions for context-sensitive rules.
    """
    
    def __init__(self, 
                 spacy_model: str = "en_core_web_sm",
                 context_window_size: int = 3,
                 enable_coreference_analysis: bool = True,
                 enable_discourse_analysis: bool = True,
                 enable_semantic_consistency: bool = True,
                 cache_analysis_results: bool = True,
                 min_confidence_threshold: float = 0.55):
        """
        Initialize the context validator.
        
        Args:
            spacy_model: SpaCy model to use for NLP analysis
            context_window_size: Number of sentences to analyze for context
            enable_coreference_analysis: Whether to perform coreference validation
            enable_discourse_analysis: Whether to analyze discourse flow
            enable_semantic_consistency: Whether to check semantic consistency
            cache_analysis_results: Whether to cache analysis results
            min_confidence_threshold: Minimum confidence for decisive decisions
        """
        super().__init__(
            validator_name="context_validator",
            min_confidence_threshold=min_confidence_threshold
        )
        
        # Configuration
        self.spacy_model_name = spacy_model
        self.context_window_size = context_window_size
        self.enable_coreference_analysis = enable_coreference_analysis
        self.enable_discourse_analysis = enable_discourse_analysis
        self.enable_semantic_consistency = enable_semantic_consistency
        self.cache_analysis_results = cache_analysis_results
        
        # Load SpaCy model
        try:
            self.nlp = spacy.load(spacy_model)
            print(f"✓ Loaded SpaCy model: {spacy_model}")
        except OSError:
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print(f"⚠️ Fallback: Loaded en_core_web_sm instead of {spacy_model}")
            except OSError:
                raise RuntimeError(f"Could not load SpaCy model {spacy_model} or fallback model")
        
        # Analysis cache
        self._analysis_cache: Dict[str, Any] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Initialize contextual patterns and validation rules
        self._initialize_contextual_patterns()
        
        # Performance tracking
        self._analysis_times = {
            'coreference_validation': [],
            'discourse_analysis': [],
            'semantic_consistency': [],
            'appropriateness_assessment': []
        }
    
    def _initialize_contextual_patterns(self):
        """Initialize contextual patterns and validation rules."""
        
        # Pronoun categories for coreference analysis
        self.pronoun_categories = {
            'personal_pronouns': {'I', 'you', 'he', 'she', 'it', 'we', 'they'},
            'possessive_pronouns': {'my', 'your', 'his', 'her', 'its', 'our', 'their'},
            'reflexive_pronouns': {'myself', 'yourself', 'himself', 'herself', 'itself', 'ourselves', 'themselves'},
            'demonstrative_pronouns': {'this', 'that', 'these', 'those'},
            'relative_pronouns': {'who', 'whom', 'whose', 'which', 'that'},
            'indefinite_pronouns': {'someone', 'something', 'anyone', 'anything', 'everyone', 'everything'}
        }
        
        # Discourse markers for flow analysis
        self.discourse_markers = {
            'addition': {'furthermore', 'moreover', 'additionally', 'also', 'besides', 'in addition'},
            'contrast': {'however', 'nevertheless', 'nonetheless', 'but', 'yet', 'although', 'though'},
            'cause_effect': {'therefore', 'consequently', 'thus', 'hence', 'as a result', 'because'},
            'sequence': {'first', 'second', 'third', 'next', 'then', 'finally', 'meanwhile'},
            'example': {'for example', 'for instance', 'such as', 'namely', 'specifically'},
            'conclusion': {'in conclusion', 'to summarize', 'in summary', 'overall', 'finally'}
        }
        
        # Semantic field indicators
        self.semantic_fields = {
            'technical': {
                'keywords': {'system', 'function', 'process', 'implementation', 'algorithm', 'data', 'code'},
                'register': 'formal',
                'terminology_precision': 'high'
            },
            'business': {
                'keywords': {'strategy', 'management', 'revenue', 'customer', 'market', 'business', 'company'},
                'register': 'formal',
                'terminology_precision': 'medium'
            },
            'academic': {
                'keywords': {'research', 'study', 'analysis', 'theory', 'methodology', 'findings', 'conclusion'},
                'register': 'formal',
                'terminology_precision': 'high'
            },
            'narrative': {
                'keywords': {'story', 'character', 'plot', 'scene', 'dialogue', 'narrative', 'experience'},
                'register': 'varied',
                'terminology_precision': 'low'
            },
            'instructional': {
                'keywords': {'step', 'procedure', 'guide', 'tutorial', 'instruction', 'method', 'process'},
                'register': 'clear',
                'terminology_precision': 'medium'
            }
        }
        
        # Formality indicators
        self.formality_indicators = {
            'formal': {
                'vocabulary': {'utilize', 'demonstrate', 'facilitate', 'implement', 'establish', 'consequently'},
                'structures': ['passive_voice', 'complex_sentences', 'nominalization'],
                'avoid': ['contractions', 'colloquialisms', 'informal_pronouns']
            },
            'informal': {
                'vocabulary': {'use', 'show', 'help', 'do', 'set up', 'so'},
                'structures': ['active_voice', 'simple_sentences', 'direct_address'],
                'allow': ['contractions', 'colloquialisms', 'casual_pronouns']
            }
        }
        
        # Context appropriateness patterns
        self.appropriateness_patterns = {
            'style_consistency': {
                'technical_formal': ['precise', 'systematic', 'documented', 'implemented'],
                'technical_informal': ['simple', 'easy', 'straightforward', 'basic'],
                'narrative_descriptive': ['vivid', 'engaging', 'compelling', 'detailed'],
                'instructional_clear': ['clear', 'step-by-step', 'specific', 'actionable']
            }
        }
    
    def _validate_error(self, context: ValidationContext) -> ValidationResult:
        """
        Validate an error using contextual and discourse analysis.
        
        Args:
            context: Validation context containing error and metadata
            
        Returns:
            ValidationResult with contextual analysis and decision
        """
        start_time = time.time()
        
        try:
            # Analyze text with NLP
            doc = self._analyze_text_with_context(context.text)
            
            # Find error location and extract context
            error_context = self._extract_contextual_information(doc, context.error_position, context.error_text)
            
            if not error_context:
                return self._create_uncertain_result(
                    context,
                    "Could not extract sufficient contextual information",
                    time.time() - start_time
                )
            
            # Perform contextual analyses
            evidence = []
            
            # VALIDATION UPGRADE STEP 2: Negative-evidence guards (first check)
            negative_evidence = self._detect_negative_context_evidence(error_context, context)
            if negative_evidence:
                cumulative_negative_confidence = sum(ne.confidence for ne in negative_evidence)
                if cumulative_negative_confidence >= 0.85:
                    # Strong negative evidence triggers early REJECT to save time and prevent false positives
                    return ValidationResult(
                        validator_name=self.validator_name,
                        decision=ValidationDecision.REJECT,
                        confidence=ValidationConfidence.HIGH,
                        confidence_score=cumulative_negative_confidence,
                        evidence=negative_evidence,
                        reasoning=f"Strong negative evidence detected: {[ne.description for ne in negative_evidence]}",
                        error_text=context.error_text,
                        error_position=context.error_position,
                        rule_type=context.rule_type,
                        rule_name=context.rule_name,
                        validation_time=time.time() - start_time,
                        metadata={
                            "negative_evidence_triggered": True,
                            "cumulative_negative_confidence": cumulative_negative_confidence,
                            "negative_evidence_types": [ne.evidence_type for ne in negative_evidence]
                        }
                    )
                else:
                    # Add moderate negative evidence to consideration
                    evidence.extend(negative_evidence)
            
            # 1. Coreference validation
            if self.enable_coreference_analysis:
                coreference_analysis = self._analyze_coreference(error_context, context)
                if coreference_analysis:
                    evidence.append(self._create_coreference_evidence(coreference_analysis, context))
            
            # 2. Discourse flow analysis
            if self.enable_discourse_analysis:
                discourse_analysis = self._analyze_discourse_flow(error_context, context)
                if discourse_analysis:
                    evidence.append(self._create_discourse_evidence(discourse_analysis, context))
            
            # 3. Semantic consistency checking
            if self.enable_semantic_consistency:
                semantic_analysis = self._analyze_semantic_consistency(error_context, context)
                if semantic_analysis:
                    evidence.append(self._create_semantic_evidence(semantic_analysis, context))
            
            # 4. Contextual appropriateness assessment
            appropriateness_analysis = self._assess_contextual_appropriateness(error_context, context)
            if appropriateness_analysis:
                evidence.append(self._create_appropriateness_evidence(appropriateness_analysis, context))
            
            # Make validation decision based on evidence
            decision, confidence_score, reasoning = self._make_contextual_decision(evidence, context)
            
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
                    'context_window_size': self.context_window_size,
                    'sentence_count': len(list(doc.sents)),
                    'analysis_types_used': [e.evidence_type for e in evidence],
                    'spacy_model': self.spacy_model_name,
                    'contextual_features_detected': len(evidence)
                }
            )
            
        except Exception as e:
            return self._create_error_result(context, str(e), time.time() - start_time)
    
    def _detect_negative_context_evidence(self, error_context: Dict[str, Any], validation_context: ValidationContext) -> List[ValidationEvidence]:
        """
        VALIDATION UPGRADE STEP 2: Detect negative context evidence that can veto shortcuts and reduce FPs.
        
        Scans for:
        - Quotation context (balanced quotes around span)
        - Legacy/migration markers: legacy, deprecated, migrating, previously called, historically
        - Code indicators: inline backticks, code fences near error
        
        Args:
            error_context: Context information around the error
            validation_context: Full validation context
            
        Returns:
            List of ValidationEvidence with negative_context type
        """
        negative_evidence = []
        
        # Get sentence around error position
        error_sentence = validation_context.text
        error_position = validation_context.error_position
        error_text = validation_context.error_text
        
        # Extract context window around error
        context_start = max(0, error_position - 100)  # 100 chars before
        context_end = min(len(error_sentence), error_position + len(error_text) + 100)  # 100 chars after
        context_window = error_sentence[context_start:context_end]
        
        # 1. QUOTATION CONTEXT DETECTION
        quotes_evidence = self._detect_quotation_context(context_window, error_position - context_start, error_text)
        if quotes_evidence:
            negative_evidence.append(quotes_evidence)
        
        # 2. LEGACY/MIGRATION MARKERS DETECTION
        legacy_evidence = self._detect_legacy_migration_markers(context_window, error_text)
        if legacy_evidence:
            negative_evidence.append(legacy_evidence)
        
        # 3. CODE INDICATORS DETECTION
        code_evidence = self._detect_code_indicators(context_window, error_position - context_start, error_text)
        if code_evidence:
            negative_evidence.append(code_evidence)
        
        return negative_evidence
    
    def _detect_quotation_context(self, context_window: str, relative_error_pos: int, error_text: str) -> Optional[ValidationEvidence]:
        """Detect if error is within quoted content."""
        # Check for balanced quotes around error
        quote_chars = ['"', "'", '`']
        
        for quote_char in quote_chars:
            quote_positions = [i for i, char in enumerate(context_window) if char == quote_char]
            
            if len(quote_positions) >= 2:
                # Find quotes that bracket the error
                for i in range(0, len(quote_positions) - 1, 2):
                    start_quote = quote_positions[i]
                    end_quote = quote_positions[i + 1]
                    
                    if start_quote <= relative_error_pos <= end_quote:
                        return ValidationEvidence(
                            evidence_type="negative_context",
                            confidence=0.9,  # High confidence for quoted content
                            description=f"Error '{error_text}' appears within quoted content ({quote_char}...{quote_char})",
                            metadata={
                                "quote_type": quote_char,
                                "quoted_content": context_window[start_quote:end_quote + 1],
                                "negative_evidence_subtype": "quotation_context"
                            }
                        )
        
        return None
    
    def _detect_legacy_migration_markers(self, context_window: str, error_text: str) -> Optional[ValidationEvidence]:
        """Detect legacy/migration disclaimer markers."""
        legacy_markers = [
            'legacy', 'deprecated', 'migrating', 'previously called', 'historically',
            'obsolete', 'outdated', 'former', 'old version', 'superseded',
            'replaced by', 'no longer', 'discontinued', 'phased out'
        ]
        
        context_lower = context_window.lower()
        
        for marker in legacy_markers:
            if marker in context_lower:
                # Check proximity to error (within 50 characters)
                marker_pos = context_lower.find(marker)
                error_pos = context_lower.find(error_text.lower())
                
                if error_pos != -1 and abs(marker_pos - error_pos) <= 50:
                    return ValidationEvidence(
                        evidence_type="negative_context",
                        confidence=0.8,  # High confidence for legacy markers
                        description=f"Error '{error_text}' appears near legacy/migration marker: '{marker}'",
                        metadata={
                            "legacy_marker": marker,
                            "marker_position": marker_pos,
                            "proximity_to_error": abs(marker_pos - error_pos),
                            "negative_evidence_subtype": "legacy_migration_markers"
                        }
                    )
        
        return None
    
    def _detect_code_indicators(self, context_window: str, relative_error_pos: int, error_text: str) -> Optional[ValidationEvidence]:
        """Detect code indicators like inline backticks or code fences."""
        # 1. INLINE CODE DETECTION (single backticks)
        if '`' in context_window:
            backtick_positions = [i for i, char in enumerate(context_window) if char == '`']
            
            # Check for balanced backticks around error
            for i in range(0, len(backtick_positions) - 1, 2):
                start_tick = backtick_positions[i]
                end_tick = backtick_positions[i + 1]
                
                if start_tick <= relative_error_pos <= end_tick:
                    return ValidationEvidence(
                        evidence_type="negative_context",
                        confidence=0.95,  # Very high confidence for inline code
                        description=f"Error '{error_text}' appears within inline code (`...`)",
                        metadata={
                            "code_content": context_window[start_tick:end_tick + 1],
                            "negative_evidence_subtype": "inline_code"
                        }
                    )
        
        # 2. CODE FENCE DETECTION (triple backticks)
        if '```' in context_window:
            fence_start = context_window.find('```')
            fence_end = context_window.find('```', fence_start + 3)
            
            if fence_start != -1 and fence_end != -1 and fence_start <= relative_error_pos <= fence_end:
                return ValidationEvidence(
                    evidence_type="negative_context",
                    confidence=1.0,  # Maximum confidence for code blocks
                    description=f"Error '{error_text}' appears within code block (```...```)",
                    metadata={
                        "code_block": context_window[fence_start:fence_end + 3],
                        "negative_evidence_subtype": "code_fence"
                    }
                )
        
        # 3. TECHNICAL SYNTAX INDICATORS
        technical_indicators = ['</', '/>', '{{', '}}', '${', '}', 'function(', '=>', '==', '!=']
        
        for indicator in technical_indicators:
            if indicator in context_window:
                indicator_pos = context_window.find(indicator)
                if abs(indicator_pos - relative_error_pos) <= 20:  # Very close proximity
                    return ValidationEvidence(
                        evidence_type="negative_context",
                        confidence=0.7,  # Moderate confidence for technical syntax
                        description=f"Error '{error_text}' appears near technical syntax: '{indicator}'",
                        metadata={
                            "technical_indicator": indicator,
                            "proximity_to_error": abs(indicator_pos - relative_error_pos),
                            "negative_evidence_subtype": "technical_syntax"
                        }
                    )
        
        return None
    
    def _analyze_text_with_context(self, text: str):
        """Analyze text with SpaCy, using cache if enabled."""
        if self.cache_analysis_results and text in self._analysis_cache:
            self._cache_hits += 1
            return self._analysis_cache[text]
        
        self._cache_misses += 1
        doc = self.nlp(text)
        
        if self.cache_analysis_results:
            self._analysis_cache[text] = doc
        
        return doc
    
    def _extract_contextual_information(self, doc, error_position: int, error_text: str) -> Optional[Dict[str, Any]]:
        """Extract contextual information around the error."""
        # Find the sentence containing the error
        error_sent = None
        for sent in doc.sents:
            if sent.start_char <= error_position <= sent.end_char:
                error_sent = sent
                break
        
        if not error_sent:
            return None
        
        # Get surrounding sentences for context
        sentences = list(doc.sents)
        error_sent_idx = sentences.index(error_sent)
        
        context_start = max(0, error_sent_idx - self.context_window_size)
        context_end = min(len(sentences), error_sent_idx + self.context_window_size + 1)
        
        context_sentences = sentences[context_start:context_end]
        
        # Find the error token
        error_token = None
        for token in error_sent:
            if token.idx <= error_position <= token.idx + len(token.text):
                error_token = token
                break
        
        return {
            'error_sentence': error_sent,
            'error_token': error_token,
            'context_sentences': context_sentences,
            'preceding_sentences': sentences[context_start:error_sent_idx],
            'following_sentences': sentences[error_sent_idx + 1:context_end],
            'full_doc': doc
        }
    
    def _analyze_coreference(self, error_context: Dict[str, Any], validation_context: ValidationContext) -> Optional[CoreferenceValidation]:
        """Analyze coreference and pronoun resolution."""
        start_time = time.time()
        
        try:
            error_token = error_context.get('error_token')
            if not error_token:
                return None
            
            token_text = error_token.text.lower()
            
            # Check if token is a pronoun
            is_pronoun = self._is_pronoun(token_text)
            
            if is_pronoun:
                # Analyze coreference for pronouns
                antecedent_info = self._find_antecedent(error_token, error_context)
                
                analysis = CoreferenceValidation(
                    token=error_token.text,
                    is_pronoun=True,
                    antecedent_found=antecedent_info['found'],
                    antecedent_text=antecedent_info.get('text'),
                    antecedent_distance=antecedent_info.get('distance', -1),
                    resolution_confidence=antecedent_info.get('confidence', 0.0),
                    ambiguity_detected=antecedent_info.get('ambiguous', False),
                    context_clarity=self._assess_context_clarity(error_context)
                )
                
            else:
                # For non-pronouns, check if they're clear references
                clarity_score = self._assess_reference_clarity(error_token, error_context)
                
                analysis = CoreferenceValidation(
                    token=error_token.text,
                    is_pronoun=False,
                    antecedent_found=True,  # Non-pronouns are self-referential
                    antecedent_text=error_token.text,
                    antecedent_distance=0,
                    resolution_confidence=clarity_score,
                    ambiguity_detected=clarity_score < 0.7,
                    context_clarity=clarity_score
                )
            
            self._analysis_times['coreference_validation'].append(time.time() - start_time)
            return analysis
            
        except Exception:
            return None
    
    def _analyze_discourse_flow(self, error_context: Dict[str, Any], validation_context: ValidationContext) -> Optional[DiscourseFlowAnalysis]:
        """Analyze discourse flow and coherence."""
        start_time = time.time()
        
        try:
            context_sentences = error_context.get('context_sentences', [])
            
            if len(context_sentences) < 2:
                return None
            
            # Find discourse markers
            transition_markers = self._find_discourse_markers(context_sentences)
            
            # Assess coherence
            coherence_score = self._assess_discourse_coherence(context_sentences)
            
            # Check for flow disruption
            flow_disruption = self._detect_flow_disruption(context_sentences, validation_context)
            
            # Assess topic consistency
            topic_consistency = self._assess_topic_consistency(context_sentences)
            
            # Evaluate logical progression
            logical_progression = self._assess_logical_progression(context_sentences)
            
            # Determine discourse structure
            discourse_structure = self._identify_discourse_structure(context_sentences, transition_markers)
            
            analysis = DiscourseFlowAnalysis(
                sentence_count=len(context_sentences),
                transition_markers=transition_markers,
                coherence_score=coherence_score,
                flow_disruption=flow_disruption,
                topic_consistency=topic_consistency,
                logical_progression=logical_progression,
                discourse_structure=discourse_structure,
                context_window_used=len(context_sentences)
            )
            
            self._analysis_times['discourse_analysis'].append(time.time() - start_time)
            return analysis
            
        except Exception:
            return None
    
    def _analyze_semantic_consistency(self, error_context: Dict[str, Any], validation_context: ValidationContext) -> Optional[SemanticConsistencyCheck]:
        """Analyze semantic consistency within context."""
        start_time = time.time()
        
        try:
            context_sentences = error_context.get('context_sentences', [])
            error_token = error_context.get('error_token')
            
            # Identify primary semantic field
            semantic_field = self._identify_semantic_field(context_sentences)
            
            # Check semantic consistency
            consistency_score = self._assess_semantic_consistency(context_sentences, semantic_field)
            
            # Find conflicting terms
            conflicting_terms = self._find_semantic_conflicts(context_sentences, semantic_field)
            
            # Assess domain coherence
            domain_coherence = self._assess_domain_coherence(context_sentences, validation_context)
            
            # Check register consistency
            register_consistency = self._assess_register_consistency(context_sentences)
            
            # Evaluate terminology alignment
            terminology_alignment = self._assess_terminology_alignment(context_sentences, semantic_field)
            
            # Detect semantic anomalies
            semantic_anomalies = self._detect_semantic_anomalies(context_sentences, error_token)
            
            analysis = SemanticConsistencyCheck(
                semantic_field=semantic_field,
                consistency_score=consistency_score,
                conflicting_terms=conflicting_terms,
                domain_coherence=domain_coherence,
                register_consistency=register_consistency,
                terminology_alignment=terminology_alignment,
                semantic_anomalies=semantic_anomalies
            )
            
            self._analysis_times['semantic_consistency'].append(time.time() - start_time)
            return analysis
            
        except Exception:
            return None
    
    def _assess_contextual_appropriateness(self, error_context: Dict[str, Any], validation_context: ValidationContext) -> Optional[ContextualAppropriateness]:
        """Assess contextual appropriateness of language choices."""
        start_time = time.time()
        
        try:
            context_sentences = error_context.get('context_sentences', [])
            error_token = error_context.get('error_token')
            
            # Detect formality level
            formality_level = self._detect_formality_level(context_sentences)
            
            # Assess audience appropriateness
            audience_appropriateness = self._assess_audience_appropriateness(context_sentences, validation_context)
            
            # Check style consistency
            style_consistency = self._assess_style_consistency(context_sentences, validation_context)
            
            # Evaluate tone alignment
            tone_alignment = self._assess_tone_alignment(context_sentences, validation_context)
            
            # Check register appropriateness
            register_appropriateness = self._assess_register_appropriateness(context_sentences, validation_context)
            
            # Detect context mismatch
            context_mismatch = self._detect_context_mismatch(context_sentences, error_token, validation_context)
            
            # Identify appropriateness factors
            appropriateness_factors = self._identify_appropriateness_factors(context_sentences, validation_context)
            
            analysis = ContextualAppropriateness(
                formality_level=formality_level,
                audience_appropriateness=audience_appropriateness,
                style_consistency=style_consistency,
                tone_alignment=tone_alignment,
                register_appropriateness=register_appropriateness,
                context_mismatch=context_mismatch,
                appropriateness_factors=appropriateness_factors
            )
            
            self._analysis_times['appropriateness_assessment'].append(time.time() - start_time)
            return analysis
            
        except Exception:
            return None
    
    # Helper methods for coreference analysis
    def _is_pronoun(self, token_text: str) -> bool:
        """Check if a token is a pronoun."""
        token_lower = token_text.lower()
        for category, pronouns in self.pronoun_categories.items():
            if token_lower in pronouns:
                return True
        return False
    
    def _find_antecedent(self, pronoun_token, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Find the antecedent for a pronoun."""
        context_sentences = error_context.get('context_sentences', [])
        
        # Simple heuristic: look for nouns in preceding context
        antecedent_candidates = []
        
        for sent in context_sentences:
            if sent.start < pronoun_token.idx:  # Only consider preceding text
                for token in sent:
                    if token.pos_ in ['NOUN', 'PROPN'] and token.text.lower() not in self.pronoun_categories.get('personal_pronouns', set()):
                        distance = pronoun_token.i - token.i
                        antecedent_candidates.append({
                            'token': token,
                            'text': token.text,
                            'distance': distance,
                            'confidence': max(0.1, 1.0 - (distance * 0.1))  # Closer = higher confidence
                        })
        
        if antecedent_candidates:
            # Select the closest high-confidence candidate
            best_candidate = max(antecedent_candidates, key=lambda x: x['confidence'])
            return {
                'found': True,
                'text': best_candidate['text'],
                'distance': best_candidate['distance'],
                'confidence': best_candidate['confidence'],
                'ambiguous': len([c for c in antecedent_candidates if c['confidence'] > 0.5]) > 1
            }
        
        return {'found': False, 'confidence': 0.0, 'ambiguous': False}
    
    def _assess_context_clarity(self, error_context: Dict[str, Any]) -> float:
        """Assess the overall clarity of the context."""
        context_sentences = error_context.get('context_sentences', [])
        
        if not context_sentences:
            return 0.0
        
        clarity_factors = []
        
        # Factor 1: Sentence length (moderate length = clearer)
        avg_length = sum(len(sent.text.split()) for sent in context_sentences) / len(context_sentences)
        length_clarity = max(0.0, 1.0 - abs(avg_length - 15) / 20)  # Optimal around 15 words
        clarity_factors.append(length_clarity)
        
        # Factor 2: Pronoun density (fewer pronouns = clearer)
        total_tokens = sum(len(sent) for sent in context_sentences)
        pronoun_count = sum(1 for sent in context_sentences for token in sent if self._is_pronoun(token.text))
        pronoun_density = pronoun_count / max(1, total_tokens)
        pronoun_clarity = max(0.0, 1.0 - pronoun_density * 5)  # Penalize high pronoun density
        clarity_factors.append(pronoun_clarity)
        
        # Factor 3: Discourse markers (more markers = clearer structure)
        marker_count = len(self._find_discourse_markers(context_sentences))
        marker_clarity = min(1.0, marker_count * 0.3)
        clarity_factors.append(marker_clarity)
        
        return sum(clarity_factors) / len(clarity_factors)
    
    def _assess_reference_clarity(self, token, error_context: Dict[str, Any]) -> float:
        """Assess the clarity of a non-pronoun reference."""
        # For non-pronouns, assess how specific and clear they are
        
        clarity_score = 0.5  # Base clarity
        
        # Factor 1: Token specificity (longer, more specific terms are clearer)
        if len(token.text) > 8:
            clarity_score += 0.2
        elif len(token.text) < 4:
            clarity_score -= 0.1
        
        # Factor 2: POS tag (proper nouns are very clear)
        if token.pos_ == 'PROPN':
            clarity_score += 0.3
        elif token.pos_ == 'NOUN':
            clarity_score += 0.1
        
        # Factor 3: Context support (if term appears multiple times, it's established)
        context_sentences = error_context.get('context_sentences', [])
        term_frequency = sum(1 for sent in context_sentences for t in sent if t.lemma_ == token.lemma_)
        if term_frequency > 2:
            clarity_score += 0.2
        
        return min(1.0, max(0.0, clarity_score))
    
    # Helper methods for discourse analysis
    def _find_discourse_markers(self, context_sentences) -> List[str]:
        """Find discourse markers in the context."""
        markers_found = []
        
        for sent in context_sentences:
            sent_text = sent.text.lower()
            for category, markers in self.discourse_markers.items():
                for marker in markers:
                    if marker in sent_text:
                        markers_found.append(marker)
        
        return list(set(markers_found))  # Remove duplicates
    
    def _assess_discourse_coherence(self, context_sentences) -> float:
        """Assess overall discourse coherence."""
        if len(context_sentences) < 2:
            return 1.0
        
        coherence_factors = []
        
        # Factor 1: Lexical cohesion (shared vocabulary)
        all_lemmas = []
        for sent in context_sentences:
            sent_lemmas = [token.lemma_.lower() for token in sent if token.pos_ in ['NOUN', 'VERB', 'ADJ']]
            all_lemmas.extend(sent_lemmas)
        
        if len(all_lemmas) > 0:
            unique_lemmas = len(set(all_lemmas))
            lexical_cohesion = 1.0 - (unique_lemmas / len(all_lemmas))
            coherence_factors.append(lexical_cohesion)
        
        # Factor 2: Structural consistency
        sentence_lengths = [len(sent) for sent in context_sentences]
        if sentence_lengths:
            length_variance = sum((l - sum(sentence_lengths) / len(sentence_lengths))**2 for l in sentence_lengths) / len(sentence_lengths)
            structure_consistency = max(0.0, 1.0 - length_variance / 100)
            coherence_factors.append(structure_consistency)
        
        return sum(coherence_factors) / len(coherence_factors) if coherence_factors else 0.5
    
    def _detect_flow_disruption(self, context_sentences, validation_context: ValidationContext) -> bool:
        """Detect if there's a flow disruption in the discourse."""
        if len(context_sentences) < 3:
            return False
        
        # Check for abrupt topic changes
        sentence_topics = []
        for sent in context_sentences:
            # Simple topic representation using main nouns
            main_nouns = [token.lemma_.lower() for token in sent if token.pos_ in ['NOUN', 'PROPN']]
            sentence_topics.append(set(main_nouns))
        
        # Check for sudden topic shifts
        for i in range(1, len(sentence_topics)):
            overlap = len(sentence_topics[i] & sentence_topics[i-1])
            total_unique = len(sentence_topics[i] | sentence_topics[i-1])
            
            if total_unique > 0 and overlap / total_unique < 0.2:  # Less than 20% overlap
                return True
        
        return False
    
    def _assess_topic_consistency(self, context_sentences) -> float:
        """Assess topic consistency across sentences."""
        if len(context_sentences) < 2:
            return 1.0
        
        # Extract main topics from each sentence
        sentence_topics = []
        for sent in context_sentences:
            topics = [token.lemma_.lower() for token in sent if token.pos_ in ['NOUN', 'PROPN', 'VERB']]
            sentence_topics.append(set(topics))
        
        # Calculate average pairwise topic overlap
        total_overlap = 0
        comparisons = 0
        
        for i in range(len(sentence_topics)):
            for j in range(i + 1, len(sentence_topics)):
                overlap = len(sentence_topics[i] & sentence_topics[j])
                total_unique = len(sentence_topics[i] | sentence_topics[j])
                
                if total_unique > 0:
                    total_overlap += overlap / total_unique
                    comparisons += 1
        
        return total_overlap / comparisons if comparisons > 0 else 0.5
    
    def _assess_logical_progression(self, context_sentences) -> float:
        """Assess logical progression in the discourse."""
        if len(context_sentences) < 2:
            return 1.0
        
        progression_score = 0.5  # Base score
        
        # Look for logical connectors
        logical_connectors = self._find_discourse_markers(context_sentences)
        if logical_connectors:
            progression_score += min(0.3, len(logical_connectors) * 0.1)
        
        # Check for consistent verb tenses
        tenses = []
        for sent in context_sentences:
            sent_tenses = [token.morph.get('Tense', [''])[0] for token in sent if token.pos_ == 'VERB']
            tenses.extend([t for t in sent_tenses if t])
        
        if tenses:
            most_common_tense = Counter(tenses).most_common(1)[0][1]
            tense_consistency = most_common_tense / len(tenses)
            progression_score += tense_consistency * 0.2
        
        return min(1.0, progression_score)
    
    def _identify_discourse_structure(self, context_sentences, transition_markers: List[str]) -> str:
        """Identify the type of discourse structure."""
        if not transition_markers:
            return "simple_sequence"
        
        # Categorize the markers found
        marker_categories = defaultdict(int)
        for marker in transition_markers:
            for category, markers in self.discourse_markers.items():
                if marker in markers:
                    marker_categories[category] += 1
        
        if not marker_categories:
            return "simple_sequence"
        
        # Determine structure based on dominant marker types
        dominant_category = max(marker_categories.items(), key=lambda x: x[1])[0]
        
        structure_mapping = {
            'addition': 'enumerative',
            'contrast': 'comparative',
            'cause_effect': 'causal',
            'sequence': 'temporal',
            'example': 'explanatory',
            'conclusion': 'argumentative'
        }
        
        return structure_mapping.get(dominant_category, 'mixed_structure')
    
    # Helper methods for semantic consistency
    def _identify_semantic_field(self, context_sentences) -> str:
        """Identify the primary semantic field of the context."""
        # Count keywords from each semantic field
        field_scores = defaultdict(int)
        
        for sent in context_sentences:
            sent_text = sent.text.lower()
            for field, field_data in self.semantic_fields.items():
                for keyword in field_data['keywords']:
                    if keyword in sent_text:
                        field_scores[field] += 1
        
        if field_scores:
            return max(field_scores.items(), key=lambda x: x[1])[0]
        
        return "general"
    
    def _assess_semantic_consistency(self, context_sentences, semantic_field: str) -> float:
        """Assess semantic consistency within the identified field."""
        if semantic_field == "general":
            return 0.7  # Neutral score for general content
        
        field_data = self.semantic_fields.get(semantic_field, {})
        field_keywords = field_data.get('keywords', set())
        
        # Count field-relevant terms
        total_content_words = 0
        field_relevant_words = 0
        
        for sent in context_sentences:
            for token in sent:
                if token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV']:
                    total_content_words += 1
                    if token.lemma_.lower() in field_keywords:
                        field_relevant_words += 1
        
        if total_content_words == 0:
            return 0.5
        
        consistency_ratio = field_relevant_words / total_content_words
        return min(1.0, consistency_ratio * 3)  # Scale to reasonable range
    
    def _find_semantic_conflicts(self, context_sentences, semantic_field: str) -> List[str]:
        """Find terms that conflict with the expected semantic field."""
        conflicts = []
        
        if semantic_field == "general":
            return conflicts
        
        # Check for terms from conflicting semantic fields
        for sent in context_sentences:
            sent_text = sent.text.lower()
            for other_field, field_data in self.semantic_fields.items():
                if other_field != semantic_field:
                    for keyword in field_data['keywords']:
                        if keyword in sent_text and keyword not in conflicts:
                            conflicts.append(keyword)
        
        return conflicts
    
    def _assess_domain_coherence(self, context_sentences, validation_context: ValidationContext) -> float:
        """Assess coherence within the expected domain."""
        # Use domain from validation context if available
        expected_domain = validation_context.domain or validation_context.content_type
        
        if not expected_domain:
            return 0.7  # Neutral if no expected domain
        
        # Simple domain matching based on vocabulary
        domain_terms = {
            'technical': {'API', 'system', 'function', 'code', 'implementation', 'algorithm'},
            'business': {'customer', 'revenue', 'strategy', 'market', 'business'},
            'academic': {'research', 'study', 'analysis', 'methodology', 'findings'}
        }
        
        relevant_terms = domain_terms.get(expected_domain, set())
        
        if not relevant_terms:
            return 0.7
        
        # Count domain-relevant terms
        found_terms = 0
        total_sentences = len(context_sentences)
        
        for sent in context_sentences:
            sent_text = sent.text
            for term in relevant_terms:
                if term.lower() in sent_text.lower():
                    found_terms += 1
                    break  # Only count once per sentence
        
        return min(1.0, found_terms / max(1, total_sentences))
    
    def _assess_register_consistency(self, context_sentences) -> float:
        """Assess consistency of language register."""
        # Detect formality indicators
        formal_indicators = 0
        informal_indicators = 0
        total_sentences = len(context_sentences)
        
        for sent in context_sentences:
            sent_text = sent.text.lower()
            
            # Check for formal vocabulary
            for word in self.formality_indicators['formal']['vocabulary']:
                if word in sent_text:
                    formal_indicators += 1
                    break
            
            # Check for informal vocabulary
            for word in self.formality_indicators['informal']['vocabulary']:
                if word in sent_text:
                    informal_indicators += 1
                    break
        
        # Calculate consistency (low variance = high consistency)
        if formal_indicators + informal_indicators == 0:
            return 0.7  # Neutral if no clear indicators
        
        total_indicators = formal_indicators + informal_indicators
        formal_ratio = formal_indicators / total_indicators
        
        # High consistency if strongly formal or informal
        if formal_ratio > 0.8 or formal_ratio < 0.2:
            return 0.9
        elif formal_ratio > 0.6 or formal_ratio < 0.4:
            return 0.7
        else:
            return 0.4  # Mixed register = lower consistency
    
    def _assess_terminology_alignment(self, context_sentences, semantic_field: str) -> float:
        """Assess alignment with expected terminology for the semantic field."""
        if semantic_field == "general":
            return 0.8
        
        field_data = self.semantic_fields.get(semantic_field, {})
        expected_precision = field_data.get('terminology_precision', 'medium')
        
        # Count precise vs vague terms
        precise_terms = 0
        vague_terms = 0
        
        for sent in context_sentences:
            for token in sent:
                if token.pos_ in ['NOUN', 'VERB', 'ADJ']:
                    if len(token.text) > 6 and not token.is_stop:  # Longer words tend to be more precise
                        precise_terms += 1
                    elif len(token.text) < 4 and token.pos_ in ['ADJ', 'ADV']:  # Short modifiers can be vague
                        vague_terms += 1
        
        if precise_terms + vague_terms == 0:
            return 0.7
        
        precision_ratio = precise_terms / (precise_terms + vague_terms)
        
        # Adjust based on expected precision for the field
        if expected_precision == 'high':
            return precision_ratio
        elif expected_precision == 'medium':
            return min(1.0, precision_ratio + 0.3)
        else:  # low precision expected
            return min(1.0, precision_ratio + 0.5)
    
    def _detect_semantic_anomalies(self, context_sentences, error_token) -> List[str]:
        """Detect semantic anomalies in the context."""
        anomalies = []
        
        if not error_token:
            return anomalies
        
        # Simple anomaly detection: words that don't fit the general context
        context_lemmas = []
        for sent in context_sentences:
            for token in sent:
                if token.pos_ in ['NOUN', 'VERB', 'ADJ'] and token != error_token:
                    context_lemmas.append(token.lemma_.lower())
        
        # If error token seems unrelated to context (very simple heuristic)
        error_lemma = error_token.lemma_.lower()
        if error_lemma not in context_lemmas and len(context_lemmas) > 5:
            # Check if error token is very different from context
            if not any(self._are_semantically_related(error_lemma, lemma) for lemma in context_lemmas[:5]):
                anomalies.append(error_token.text)
        
        return anomalies
    
    def _are_semantically_related(self, word1: str, word2: str) -> bool:
        """Simple semantic relatedness check."""
        # Very basic heuristic: share prefixes or are in same semantic category
        if len(word1) > 3 and len(word2) > 3:
            if word1[:3] == word2[:3] or word1[-3:] == word2[-3:]:
                return True
        
        # Check if both are in same semantic field
        for field_data in self.semantic_fields.values():
            keywords = field_data['keywords']
            if word1 in keywords and word2 in keywords:
                return True
        
        return False
    
    # Helper methods for appropriateness assessment
    def _detect_formality_level(self, context_sentences) -> str:
        """Detect the formality level of the context."""
        formal_score = 0
        informal_score = 0
        
        for sent in context_sentences:
            sent_text = sent.text.lower()
            
            # Check formal vocabulary
            for word in self.formality_indicators['formal']['vocabulary']:
                if word in sent_text:
                    formal_score += 1
            
            # Check informal vocabulary
            for word in self.formality_indicators['informal']['vocabulary']:
                if word in sent_text:
                    informal_score += 1
            
            # Check for contractions (informal)
            if "'" in sent.text:
                informal_score += 1
        
        if formal_score > informal_score * 1.5:
            return "formal"
        elif informal_score > formal_score * 1.5:
            return "informal"
        else:
            return "neutral"
    
    def _assess_audience_appropriateness(self, context_sentences, validation_context: ValidationContext) -> float:
        """Assess appropriateness for the target audience."""
        # Use content type as audience indicator
        content_type = validation_context.content_type
        
        if not content_type:
            return 0.7
        
        formality_level = self._detect_formality_level(context_sentences)
        
        # Map content types to expected formality
        expected_formality = {
            'technical': 'formal',
            'business': 'formal',
            'academic': 'formal',
            'narrative': 'neutral',
            'instructional': 'neutral'
        }
        
        expected = expected_formality.get(content_type, 'neutral')
        
        if expected == formality_level:
            return 0.9
        elif expected == 'neutral' or formality_level == 'neutral':
            return 0.7
        else:
            return 0.4
    
    def _assess_style_consistency(self, context_sentences, validation_context: ValidationContext) -> float:
        """Assess consistency with expected style."""
        # Basic style consistency check
        sentence_lengths = [len(sent.text.split()) for sent in context_sentences]
        
        if not sentence_lengths:
            return 0.7
        
        avg_length = sum(sentence_lengths) / len(sentence_lengths)
        length_variance = sum((l - avg_length)**2 for l in sentence_lengths) / len(sentence_lengths)
        
        # Lower variance = higher consistency
        consistency_score = max(0.0, 1.0 - length_variance / 100)
        
        return min(1.0, consistency_score + 0.3)  # Boost baseline
    
    def _assess_tone_alignment(self, context_sentences, validation_context: ValidationContext) -> float:
        """Assess alignment with expected tone."""
        # Simple tone assessment based on word choice
        positive_words = {'good', 'excellent', 'effective', 'successful', 'beneficial', 'optimal'}
        negative_words = {'bad', 'poor', 'ineffective', 'failed', 'problematic', 'suboptimal'}
        neutral_words = {'standard', 'typical', 'regular', 'normal', 'average', 'common'}
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for sent in context_sentences:
            sent_text = sent.text.lower()
            
            for word in positive_words:
                if word in sent_text:
                    positive_count += 1
            
            for word in negative_words:
                if word in sent_text:
                    negative_count += 1
            
            for word in neutral_words:
                if word in sent_text:
                    neutral_count += 1
        
        total_tone_words = positive_count + negative_count + neutral_count
        
        if total_tone_words == 0:
            return 0.7  # Neutral if no tone indicators
        
        # Consistent tone is good
        dominant_tone_count = max(positive_count, negative_count, neutral_count)
        tone_consistency = dominant_tone_count / total_tone_words
        
        return min(1.0, tone_consistency + 0.2)
    
    def _assess_register_appropriateness(self, context_sentences, validation_context: ValidationContext) -> float:
        """Assess appropriateness of language register."""
        rule_type = validation_context.rule_type
        content_type = validation_context.content_type
        
        formality_level = self._detect_formality_level(context_sentences)
        
        # Different rule types may expect different registers
        if rule_type in ['grammar', 'punctuation']:
            # Grammar and punctuation rules generally favor formal register
            if formality_level == 'formal':
                return 0.9
            elif formality_level == 'neutral':
                return 0.7
            else:
                return 0.5
        
        elif rule_type == 'style':
            # Style rules depend more on content type
            if content_type in ['technical', 'business', 'academic'] and formality_level == 'formal':
                return 0.9
            elif content_type in ['narrative', 'instructional'] and formality_level in ['neutral', 'informal']:
                return 0.9
            else:
                return 0.6
        
        return 0.7  # Default neutral score
    
    def _detect_context_mismatch(self, context_sentences, error_token, validation_context: ValidationContext) -> bool:
        """Detect if there's a context mismatch."""
        if not error_token:
            return False
        
        # Check for obvious mismatches
        rule_type = validation_context.rule_type
        content_type = validation_context.content_type
        
        # Very simple mismatch detection
        error_text = error_token.text.lower()
        
        # Technical content with very informal language
        if content_type == 'technical' and error_text in ['awesome', 'cool', 'super']:
            return True
        
        # Formal content with very informal abbreviations
        if rule_type == 'grammar' and error_text in ['u', 'ur', 'plz', 'thx']:
            return True
        
        return False
    
    def _identify_appropriateness_factors(self, context_sentences, validation_context: ValidationContext) -> List[str]:
        """Identify factors affecting appropriateness."""
        factors = []
        
        # Formality mismatch
        formality = self._detect_formality_level(context_sentences)
        content_type = validation_context.content_type
        
        if content_type == 'technical' and formality != 'formal':
            factors.append('formality_mismatch')
        
        # Length consistency
        sentence_lengths = [len(sent.text.split()) for sent in context_sentences]
        if sentence_lengths:
            avg_length = sum(sentence_lengths) / len(sentence_lengths)
            if avg_length > 25:
                factors.append('overly_complex_sentences')
            elif avg_length < 5:
                factors.append('overly_simple_sentences')
        
        # Discourse structure
        markers = self._find_discourse_markers(context_sentences)
        if len(markers) == 0 and len(context_sentences) > 3:
            factors.append('lacks_discourse_markers')
        
        return factors
    
    # Evidence creation methods
    def _create_coreference_evidence(self, analysis: CoreferenceValidation, context: ValidationContext) -> ValidationEvidence:
        """Create validation evidence from coreference analysis."""
        confidence = analysis.resolution_confidence * analysis.context_clarity
        
        description = f"Coreference analysis: '{analysis.token}' "
        if analysis.is_pronoun:
            if analysis.antecedent_found:
                description += f"resolves to '{analysis.antecedent_text}' (distance: {analysis.antecedent_distance})"
            else:
                description += "has unclear reference"
        else:
            description += f"is clear reference (clarity: {analysis.context_clarity:.2f})"
        
        if analysis.ambiguity_detected:
            description += " [ambiguous]"
        
        return ValidationEvidence(
            evidence_type="coreference_validation",
            confidence=confidence,
            description=description,
            source_data={
                'token': analysis.token,
                'is_pronoun': analysis.is_pronoun,
                'antecedent_found': analysis.antecedent_found,
                'antecedent_text': analysis.antecedent_text,
                'antecedent_distance': analysis.antecedent_distance,
                'resolution_confidence': analysis.resolution_confidence,
                'context_clarity': analysis.context_clarity,
                'ambiguity_detected': analysis.ambiguity_detected
            }
        )
    
    def _create_discourse_evidence(self, analysis: DiscourseFlowAnalysis, context: ValidationContext) -> ValidationEvidence:
        """Create validation evidence from discourse analysis."""
        confidence = (analysis.coherence_score + analysis.topic_consistency + analysis.logical_progression) / 3
        
        description = f"Discourse analysis: {analysis.sentence_count} sentences, "
        description += f"coherence {analysis.coherence_score:.2f}, "
        description += f"structure: {analysis.discourse_structure}"
        
        if analysis.flow_disruption:
            description += " [flow disrupted]"
        
        if analysis.transition_markers:
            description += f", markers: {', '.join(analysis.transition_markers[:3])}"
        
        return ValidationEvidence(
            evidence_type="discourse_flow",
            confidence=confidence,
            description=description,
            source_data={
                'sentence_count': analysis.sentence_count,
                'transition_markers': analysis.transition_markers,
                'coherence_score': analysis.coherence_score,
                'flow_disruption': analysis.flow_disruption,
                'topic_consistency': analysis.topic_consistency,
                'logical_progression': analysis.logical_progression,
                'discourse_structure': analysis.discourse_structure
            }
        )
    
    def _create_semantic_evidence(self, analysis: SemanticConsistencyCheck, context: ValidationContext) -> ValidationEvidence:
        """Create validation evidence from semantic analysis."""
        confidence = (analysis.consistency_score + analysis.domain_coherence + analysis.register_consistency) / 3
        
        description = f"Semantic analysis: {analysis.semantic_field} field, "
        description += f"consistency {analysis.consistency_score:.2f}"
        
        if analysis.conflicting_terms:
            description += f", conflicts: {', '.join(analysis.conflicting_terms[:3])}"
        
        if analysis.semantic_anomalies:
            description += f" [anomalies detected]"
        
        return ValidationEvidence(
            evidence_type="semantic_consistency",
            confidence=confidence,
            description=description,
            source_data={
                'semantic_field': analysis.semantic_field,
                'consistency_score': analysis.consistency_score,
                'conflicting_terms': analysis.conflicting_terms,
                'domain_coherence': analysis.domain_coherence,
                'register_consistency': analysis.register_consistency,
                'terminology_alignment': analysis.terminology_alignment,
                'semantic_anomalies': analysis.semantic_anomalies
            }
        )
    
    def _create_appropriateness_evidence(self, analysis: ContextualAppropriateness, context: ValidationContext) -> ValidationEvidence:
        """Create validation evidence from appropriateness analysis."""
        confidence = (analysis.audience_appropriateness + analysis.style_consistency + 
                     analysis.tone_alignment + analysis.register_appropriateness) / 4
        
        description = f"Appropriateness analysis: {analysis.formality_level} formality, "
        description += f"audience fit {analysis.audience_appropriateness:.2f}"
        
        if analysis.context_mismatch:
            description += " [context mismatch]"
        
        if analysis.appropriateness_factors:
            description += f", factors: {', '.join(analysis.appropriateness_factors[:2])}"
        
        return ValidationEvidence(
            evidence_type="contextual_appropriateness",
            confidence=confidence,
            description=description,
            source_data={
                'formality_level': analysis.formality_level,
                'audience_appropriateness': analysis.audience_appropriateness,
                'style_consistency': analysis.style_consistency,
                'tone_alignment': analysis.tone_alignment,
                'register_appropriateness': analysis.register_appropriateness,
                'context_mismatch': analysis.context_mismatch,
                'appropriateness_factors': analysis.appropriateness_factors
            }
        )
    
    def _make_contextual_decision(self, evidence: List[ValidationEvidence], 
                                 context: ValidationContext) -> Tuple[ValidationDecision, float, str]:
        """Make validation decision based on contextual evidence."""
        if not evidence:
            return ValidationDecision.UNCERTAIN, 0.3, "No contextual evidence available for validation"
        
        # Calculate weighted average confidence
        total_weight = sum(e.confidence * e.weight for e in evidence)
        total_weights = sum(e.weight for e in evidence)
        avg_confidence = total_weight / total_weights if total_weights > 0 else 0.3
        
        # Analyze evidence types
        evidence_types = [e.evidence_type for e in evidence]
        
        # Decision logic based on evidence and rule type
        if context.rule_type in ["style", "tone"]:
            # Style and tone rules benefit strongly from contextual analysis
            if avg_confidence >= 0.7 and any(et in ['contextual_appropriateness', 'discourse_flow'] for et in evidence_types):
                decision = ValidationDecision.ACCEPT
                reasoning = f"Strong contextual evidence ({avg_confidence:.2f}) supports style/tone validation"
                
            elif avg_confidence < 0.4:
                decision = ValidationDecision.REJECT
                reasoning = f"Weak contextual evidence ({avg_confidence:.2f}) suggests style/tone rule may not apply"
                
            else:
                decision = ValidationDecision.UNCERTAIN
                reasoning = f"Moderate contextual evidence ({avg_confidence:.2f}) - style/tone validation uncertain"
        
        elif context.rule_type == "grammar":
            # Grammar rules have moderate benefit from contextual analysis
            if avg_confidence >= 0.8 and any(et in ['coreference_validation', 'discourse_flow'] for et in evidence_types):
                decision = ValidationDecision.ACCEPT
                reasoning = f"Strong contextual support ({avg_confidence:.2f}) reinforces grammar validation"
                
            elif avg_confidence < 0.3:
                decision = ValidationDecision.REJECT
                reasoning = f"Poor contextual fit ({avg_confidence:.2f}) suggests grammar rule may not apply"
                
            else:
                decision = ValidationDecision.UNCERTAIN
                reasoning = f"Contextual analysis ({avg_confidence:.2f}) provides moderate support for grammar rule"
        
        elif context.rule_type == "terminology":
            # Terminology rules benefit from semantic consistency
            if avg_confidence >= 0.6 and any(et in ['semantic_consistency', 'contextual_appropriateness'] for et in evidence_types):
                decision = ValidationDecision.ACCEPT
                reasoning = f"Contextual analysis ({avg_confidence:.2f}) supports terminology validation"
                
            else:
                decision = ValidationDecision.UNCERTAIN
                reasoning = f"Limited contextual relevance ({avg_confidence:.2f}) for terminology validation"
        
        else:
            # Other rule types: conservative approach
            if avg_confidence >= 0.8:
                decision = ValidationDecision.ACCEPT
                reasoning = f"Very strong contextual evidence ({avg_confidence:.2f}) supports validation"
                
            elif avg_confidence < 0.3:
                decision = ValidationDecision.REJECT
                reasoning = f"Very weak contextual evidence ({avg_confidence:.2f}) suggests rule not applicable"
                
            else:
                decision = ValidationDecision.UNCERTAIN
                reasoning = f"Contextual evidence ({avg_confidence:.2f}) inconclusive for {context.rule_type} rule"
        
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
            reasoning=f"Contextual validation uncertain: {reason}",
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
            reasoning=f"Contextual validation failed due to error: {error_msg}",
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
            "type": "context_validator",
            "version": "1.0.0",
            "description": "Validates errors using contextual and discourse analysis",
            "capabilities": [
                "coreference_validation",
                "discourse_flow_analysis",
                "semantic_consistency_checking",
                "contextual_appropriateness_assessment",
                "register_analysis"
            ],
            "specialties": [
                "style_validation",
                "tone_consistency", 
                "discourse_coherence",
                "contextual_appropriateness",
                "coreference_resolution"
            ],
            "configuration": {
                "spacy_model": self.spacy_model_name,
                "context_window_size": self.context_window_size,
                "coreference_analysis_enabled": self.enable_coreference_analysis,
                "discourse_analysis_enabled": self.enable_discourse_analysis,
                "semantic_consistency_enabled": self.enable_semantic_consistency,
                "analysis_caching_enabled": self.cache_analysis_results,
                "min_confidence_threshold": self.min_confidence_threshold
            },
            "performance_characteristics": {
                "best_for_rule_types": ["style", "tone", "discourse"],
                "moderate_for_rule_types": ["grammar", "terminology"],
                "limited_for_rule_types": ["punctuation", "formatting"],
                "avg_processing_time_ms": self._get_average_processing_time(),
                "cache_hit_rate": self._get_cache_hit_rate()
            },
            "linguistic_features": {
                "pronoun_categories_count": len(self.pronoun_categories),
                "discourse_markers_count": sum(len(markers) for markers in self.discourse_markers.values()),
                "semantic_fields_count": len(self.semantic_fields),
                "formality_indicators_count": len(self.formality_indicators)
            }
        }
    
    def _get_average_processing_time(self) -> float:
        """Get average processing time across all analysis types."""
        all_times = []
        for analysis_type, times in self._analysis_times.items():
            all_times.extend(times)
        
        return (sum(all_times) / len(all_times) * 1000) if all_times else 0.0
    
    def _get_cache_hit_rate(self) -> float:
        """Get analysis cache hit rate."""
        total = self._cache_hits + self._cache_misses
        return self._cache_hits / total if total > 0 else 0.0
    
    def clear_caches(self) -> None:
        """Clear all caches."""
        self._analysis_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Clear performance tracking
        for analysis_type in self._analysis_times:
            self._analysis_times[analysis_type].clear()
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get detailed analysis statistics."""
        return {
            "analysis_cache": {
                "cached_analyses": len(self._analysis_cache),
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
                "coreference_analysis": self.enable_coreference_analysis,
                "discourse_analysis": self.enable_discourse_analysis,
                "semantic_consistency": self.enable_semantic_consistency,
                "analysis_caching": self.cache_analysis_results
            }
        }