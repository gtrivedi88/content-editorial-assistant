"""
Base Rule Class - Abstract interface for all writing rules using pure SpaCy morphological analysis.
All rules must inherit from this class and implement the required methods.
Provides comprehensive linguistic analysis utilities without hardcoded patterns.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set, Tuple, Union
import re
from collections import defaultdict
import yaml
import os

# Import confidence and validation system components
try:
    from validation.confidence.confidence_calculator import ConfidenceCalculator, ConfidenceBreakdown
    from validation.multi_pass.validation_pipeline import (
        ValidationPipeline, PipelineConfiguration, PipelineResult, ConsensusStrategy
    )
    from validation.multi_pass.base_validator import ValidationContext
    from validation.confidence.rule_reliability import get_rule_reliability_coefficient
    ENHANCED_VALIDATION_AVAILABLE = True
except ImportError:
    # Fallback for environments where validation system is not available
    ConfidenceCalculator = None
    ConfidenceBreakdown = None
    ValidationPipeline = None
    PipelineConfiguration = None
    PipelineResult = None
    ValidationContext = None
    ConsensusStrategy = None
    get_rule_reliability_coefficient = None
    ENHANCED_VALIDATION_AVAILABLE = False

try:
    from spacy.matcher import Matcher, PhraseMatcher
except ImportError:
    Matcher = None
    PhraseMatcher = None

class BaseRule(ABC):
    """
    Abstract base class for all writing rules using pure SpaCy morphological analysis.
    Provides comprehensive linguistic utilities without hardcoded patterns.
    """
    
    # Class-level cache for exceptions to avoid reading the file for every rule instance.
    _exceptions = None
    
    # Class-level shared validation system components for enhanced error creation
    _confidence_calculator = None
    _validation_pipeline = None
    _validation_pipeline_config = None

    def __init__(self) -> None:
        """Initializes the rule and loads the exception configuration."""
        self.rule_type = self._get_rule_type()
        self.severity_levels = ['low', 'medium', 'high']
        
        # spaCy Matcher support for enhanced pattern matching
        self._matcher = None
        self._phrase_matcher = None
        self._patterns_initialized = False
        
        # Load exceptions once and cache them at the class level.
        if BaseRule._exceptions is None:
            self._load_exceptions()
        
        # Initialize validation system components once at class level
        if ENHANCED_VALIDATION_AVAILABLE and BaseRule._confidence_calculator is None:
            BaseRule._initialize_validation_system()
    
    @classmethod
    def _load_exceptions(cls):
        """
        Loads the exceptions.yaml file and caches it.
        This method is called only once to optimize performance.
        """
        # The path is constructed relative to this file's location.
        # It goes up one level (to the 'rules' dir) and then into a 'config' dir.
        # Assumed structure: project_root/rules/base_rule.py and project_root/config/exceptions.yaml
        path = os.path.join(os.path.dirname(__file__), '..', 'config', 'exceptions.yaml')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                cls._exceptions = yaml.safe_load(f)
                if not isinstance(cls._exceptions, dict):
                    print(f"Warning: exceptions.yaml at {path} is not a valid dictionary. Disabling exceptions.")
                    cls._exceptions = {}
        except FileNotFoundError:
            print(f"Warning: exceptions.yaml not found at {path}. No exceptions will be applied.")
            cls._exceptions = {}
        except Exception as e:
            print(f"Error loading or parsing exceptions.yaml: {e}")
            cls._exceptions = {}

    @classmethod
    def _initialize_validation_system(cls):
        """
        Initialize the enhanced validation system components once at class level.
        This includes confidence calculation and validation pipeline.
        """
        if not ENHANCED_VALIDATION_AVAILABLE:
            return
        
        try:
            # Initialize confidence calculator with default configuration
            cls._confidence_calculator = ConfidenceCalculator(
                cache_results=True,
                enable_layer_caching=True
            )
            
            # Initialize validation pipeline with optimized configuration for rule processing
            cls._validation_pipeline_config = PipelineConfiguration(
                # Enable all validators for comprehensive validation
                enable_morphological=True,
                enable_contextual=True,
                enable_domain=True,
                enable_cross_rule=True,
                
                # Optimize for rule-level validation
                consensus_strategy=ConsensusStrategy.WEIGHTED_AVERAGE if ConsensusStrategy else None,
                minimum_consensus_confidence=0.6,
                
                # Enable early termination for performance
                enable_early_termination=True,
                high_confidence_threshold=0.85,
                timeout_seconds=5.0,  # Faster timeout for rule-level validation
                
                # Error handling
                continue_on_validator_error=True,
                minimum_validator_count=2,
                
                # Performance optimization
                enable_performance_monitoring=True,
                enable_audit_trail=False  # Disable detailed audit trail for performance
            )
            
            cls._validation_pipeline = ValidationPipeline(cls._validation_pipeline_config)
            
        except Exception as e:
            print(f"Warning: Failed to initialize enhanced validation system: {e}")
            # Set to None to indicate failure and fall back to basic error creation
            cls._confidence_calculator = None
            cls._validation_pipeline = None
            cls._validation_pipeline_config = None

    def _is_excepted(self, text_span: str) -> bool:
        """
        Checks if a given text span is in the global or rule-specific exception list.
        This is the core method for preventing false positives.
        The check is case-insensitive.

        Args:
            text_span: The word or phrase to check (e.g., "user interface").

        Returns:
            True if the text_span is an exception, False otherwise.
        """
        if not self._exceptions or not text_span:
            return False

        text_span_lower = text_span.lower().strip()

        # 1. Check global exceptions
        global_exceptions = self._exceptions.get('global_exceptions', [])
        if isinstance(global_exceptions, list):
            if text_span_lower in [str(exc).lower() for exc in global_exceptions]:
                return True

        # 2. Check rule-specific exceptions
        rule_specifics = self._exceptions.get('rule_specific_exceptions', {})
        if isinstance(rule_specifics, dict):
            rule_exceptions = rule_specifics.get(self.rule_type, [])
            if isinstance(rule_exceptions, list):
                if text_span_lower in [str(exc).lower() for exc in rule_exceptions]:
                    return True

        return False

    @abstractmethod
    def _get_rule_type(self) -> str:
        """Return the rule type identifier (e.g., 'passive_voice', 'sentence_length')."""
        pass
    
    def _get_rule_reliability_coefficient(self) -> float:
        """
        Get reliability coefficient for this rule type.
        
        Returns:
            Reliability coefficient in range [0.5, 1.0] indicating typical accuracy
        """
        if ENHANCED_VALIDATION_AVAILABLE and get_rule_reliability_coefficient:
            return get_rule_reliability_coefficient(self.rule_type)
        else:
            # Fallback coefficient when validation system not available
            return 0.75
    
    @abstractmethod
    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyze text and return list of errors found.
        
        Args:
            text: Full text to analyze
            sentences: List of sentences
            nlp: SpaCy nlp object (optional)
            context: Optional context information about the block being analyzed
            
        Returns:
            List of error dictionaries.
        """
        pass
    
    # === spaCy MATCHER SUPPORT ===
    
    def _setup_patterns(self, nlp):
        """
        Override in subclasses to define spaCy Matcher patterns.
        This method should initialize self._matcher and/or self._phrase_matcher.
        
        Args:
            nlp: The spaCy nlp object for pattern compilation
        """
        pass
    
    def _ensure_patterns_ready(self, nlp):
        """
        Lazy initialization of spaCy patterns.
        Ensures patterns are compiled only once per rule instance.
        
        Args:
            nlp: The spaCy nlp object
        """
        if not self._patterns_initialized and nlp and (Matcher is not None and PhraseMatcher is not None):
            self._setup_patterns(nlp)
            self._patterns_initialized = True
    
    def _find_matcher_errors(self, doc, word_map=None, error_type_prefix="word_usage"):
        """
        Common method to process spaCy Matcher results and convert to error format.
        
        Args:
            doc: spaCy Doc object
            word_map: Optional mapping of words to error details (for word usage rules)
            error_type_prefix: Prefix for error categorization
            
        Returns:
            List of error dictionaries
        """
        errors = []
        
        # Process Matcher results
        if self._matcher:
            matches = self._matcher(doc)
            for match_id, start, end in matches:
                span = doc[start:end]
                errors.extend(self._process_match_span(span, word_map, error_type_prefix))
        
        # Process PhraseMatcher results  
        if self._phrase_matcher:
            matches = self._phrase_matcher(doc)
            for match_id, start, end in matches:
                span = doc[start:end]
                errors.extend(self._process_match_span(span, word_map, error_type_prefix))
                
        return errors
    
    def _process_match_span(self, span, word_map=None, error_type_prefix="word_usage"):
        """
        Convert a spaCy span match to error format.
        
        Args:
            span: spaCy Span object representing the match
            word_map: Optional mapping of words to error details
            error_type_prefix: Prefix for error categorization
            
        Returns:
            List containing error dictionary
        """
        matched_text = span.text.lower()
        sent = span.sent
        
        # Get sentence index
        sentence_index = 0
        for i, s in enumerate(span.doc.sents):
            if s == sent:
                sentence_index = i
                break
        
        # Default error details
        error_details = {
            "suggestion": f"Consider an alternative for '{span.text}'.",
            "severity": "medium"
        }
        
        # Use word_map if provided (for word usage rules)
        if word_map and matched_text in word_map:
            error_details = word_map[matched_text]
        
        return [self._create_error(
            sentence=sent.text,
            sentence_index=sentence_index,
            message=f"Consider an alternative for the word '{span.text}'.",
            suggestions=[error_details['suggestion']],
            severity=error_details['severity'],
            span=(span.start_char, span.end_char),
            flagged_text=span.text
        )]
    
    # === ENTERPRISE CONTEXT INTELLIGENCE ===
    
    def _get_content_classification(self, text: str, context: Optional[dict] = None, nlp=None) -> str:
        """
        Enterprise-grade content classification using pure SpaCy morphological analysis.
        Uses linguistic anchors instead of hardcoded patterns.
        
        Returns:
            - 'technical_identifier': Technical terms/identifiers (morphologically detected)
            - 'navigation_label': Concise navigation elements (syntactically detected)  
            - 'procedural_instruction': Action-oriented steps (verb-pattern detected)
            - 'data_reference': Reference values (entity/compound detected)
            - 'topic_heading': Topic titles (syntactic structure detected)
            - 'descriptive_content': Full explanatory content (complete syntax detected)
        """
        if not context:
            return 'descriptive_content'
            
        # Use SpaCy for morphological analysis if available
        if nlp:
            return self._classify_with_morphological_analysis(text, context, nlp)
        else:
            return self._classify_with_structural_context(text, context)
    
    def _classify_with_morphological_analysis(self, text: str, context: dict, nlp) -> str:
        """Classification using pure SpaCy morphological and syntactic analysis."""
        try:
            doc = nlp(text.strip())
            if not doc:
                return 'descriptive_content'
            
            # LINGUISTIC ANCHOR 1: Analyze syntactic completeness
            has_complete_syntax = self._has_complete_syntactic_structure(doc)
            
            # LINGUISTIC ANCHOR 2: Detect technical/compound terms through morphology
            is_technical_identifier = self._is_morphological_technical_term(doc)
            
            # LINGUISTIC ANCHOR 3: Detect procedural patterns through dependency analysis
            is_procedural = self._has_procedural_syntax_pattern(doc)
            
            # LINGUISTIC ANCHOR 4: Analyze named entities and references
            is_reference_entity = self._is_reference_entity_pattern(doc)
            
            # LINGUISTIC ANCHOR 5: Detect topic/heading patterns through POS structure
            is_topic_pattern = self._has_topic_heading_syntax(doc)
            
            # Classification logic based on linguistic features
            block_type = context.get('block_type', '').lower()
            
            # ENHANCED TABLE CELL CLASSIFICATION
            if block_type == 'table_cell':
                # Check if this is a table header (typically row 0 or concise labels)
                table_row_index = context.get('table_row_index', context.get('row_index', 999))
                cell_index = context.get('cell_index', 0)
                
                # Table headers are typically navigation labels (no articles needed)
                if (table_row_index == 0 or 
                    is_topic_pattern or 
                    (not has_complete_syntax and len(doc) <= 3)):  # Short phrases
                    return 'navigation_label'
                
                # Procedural instructions (imperative verbs like "Click", "Configure")
                elif is_procedural:
                    return 'procedural_instruction'
                
                # Data references (identifiers, names, technical terms)
                elif is_reference_entity or is_technical_identifier:
                    return 'data_reference'
                
                # Only complete sentences should be treated as descriptive content
                elif has_complete_syntax and len(doc) > 4:
                    return 'descriptive_content'
                
                # Default table cell content to navigation label (concise phrases)
                else:
                    return 'navigation_label'
            
            # Use morphological evidence for classification (existing logic)
            if is_technical_identifier and 'list_item' in block_type:
                return 'technical_identifier'
            elif is_procedural and block_type == 'list_item_ordered':
                return 'procedural_instruction'
            elif is_reference_entity:
                return 'data_reference'
            elif is_topic_pattern and block_type in ['heading', 'section']:
                return 'topic_heading'
            elif not has_complete_syntax and 'list_item' in block_type:
                return 'navigation_label'
            else:
                return 'descriptive_content'
                
        except Exception:
            return self._classify_with_structural_context(text, context)
    
    def _has_complete_syntactic_structure(self, doc) -> bool:
        """Use SpaCy dependency parsing to detect complete syntactic structures."""
        if not doc:
            return False
            
        # LINGUISTIC ANCHOR: Complete sentences have ROOT verbs with subjects/objects
        root_verbs = [token for token in doc if token.dep_ == 'ROOT' and token.pos_ == 'VERB']
        
        if not root_verbs:
            return False
            
        for root in root_verbs:
            # Check for subject-verb-object patterns
            has_subject = any(child.dep_ in ['nsubj', 'nsubjpass'] for child in root.children)
            has_object = any(child.dep_ in ['dobj', 'iobj', 'pobj'] for child in root.children)
            
            if has_subject or has_object:
                return True
                
        return False
    
    def _is_morphological_technical_term(self, doc) -> bool:
        """Use SpaCy morphological analysis to detect technical terminology."""
        if not doc:
            return False
            
        # LINGUISTIC ANCHOR 1: Named entities often indicate technical terms
        technical_entities = [ent for ent in doc.ents 
                            if ent.label_ in ['ORG', 'PRODUCT', 'FACILITY', 'LANGUAGE']]
        if technical_entities:
            return True
            
        # LINGUISTIC ANCHOR 2: Compound noun patterns (technical_term + technical_term)
        compounds = self._detect_compound_technical_patterns(doc)
        if compounds:
            return True
            
        # LINGUISTIC ANCHOR 3: Technical morphological patterns
        for token in doc:
            # Check for technical suffixes/morphology
            if self._has_technical_morphology(token):
                return True
                
        return False
    
    def _detect_compound_technical_patterns(self, doc) -> bool:
        """Use SpaCy dependency parsing to detect compound technical terms."""
        # LINGUISTIC ANCHOR: compound + noun patterns for technical terms
        for token in doc:
            if token.dep_ == 'compound':
                head = token.head
                # Both compound and head should be nouns for technical patterns
                if token.pos_ in ['NOUN', 'PROPN'] and head.pos_ in ['NOUN', 'PROPN']:
                    # Check if either has technical characteristics
                    if (self._has_technical_morphology(token) or 
                        self._has_technical_morphology(head)):
                        return True
        return False
    
    def _has_technical_morphology(self, token) -> bool:
        """Analyze token morphology for technical characteristics."""
        if not token:
            return False
            
        # LINGUISTIC ANCHOR 1: Technical suffixes through morphology
        technical_suffixes = ['ing', 'tion', 'sion', 'ment', 'ance', 'ence']
        if any(token.text.lower().endswith(suffix) for suffix in technical_suffixes):
            return True
            
        # LINGUISTIC ANCHOR 2: Capitalized technical patterns (not sentence start)
        if (token.is_title and token.i > 0 and 
            not token.is_sent_start and token.pos_ in ['NOUN', 'PROPN']):
            return True
            
        # LINGUISTIC ANCHOR 3: All-caps technical abbreviations
        if token.is_upper and len(token.text) >= 2 and token.pos_ in ['NOUN', 'PROPN']:
            return True
            
        return False
    
    def _has_procedural_syntax_pattern(self, doc) -> bool:
        """Use dependency parsing to detect procedural/instructional patterns."""
        if not doc:
            return False
            
        # LINGUISTIC ANCHOR: Imperative verbs at sentence start indicate procedures
        first_token = doc[0] if doc else None
        if first_token and first_token.pos_ == 'VERB':
            # Check if it's imperative mood through morphology
            if first_token.dep_ == 'ROOT':
                # Imperative verbs often have no explicit subject
                has_explicit_subject = any(child.dep_ in ['nsubj'] for child in first_token.children)
                if not has_explicit_subject:
                    return True
                    
        return False
    
    def _is_reference_entity_pattern(self, doc) -> bool:
        """Use NER and morphology to detect reference entities."""
        if not doc:
            return False
            
        # LINGUISTIC ANCHOR 1: Single named entities
        if len(doc.ents) == 1 and len(doc) <= 3:
            return True
            
        # LINGUISTIC ANCHOR 2: Single proper nouns
        proper_nouns = [token for token in doc if token.pos_ == 'PROPN']
        if len(proper_nouns) >= 1 and len(doc) <= 3:
            return True
            
        return False
    
    def _has_topic_heading_syntax(self, doc) -> bool:
        """Use syntactic analysis to detect topic/heading patterns."""
        if not doc:
            return False
            
        # LINGUISTIC ANCHOR 1: Noun phrase patterns without verbs
        has_verbs = any(token.pos_ == 'VERB' for token in doc)
        has_nouns = any(token.pos_ in ['NOUN', 'PROPN'] for token in doc)
        
        if has_nouns and not has_verbs:
            return True
            
        # LINGUISTIC ANCHOR 2: Prepositional phrase patterns (common in headings)
        has_prep_phrase = any(token.pos_ == 'ADP' for token in doc)
        if has_prep_phrase and not has_verbs and len(doc) <= 6:
            return True
            
        return False
    
    def _classify_with_structural_context(self, text: str, context: dict) -> str:
        """Fallback classification when SpaCy is not available."""
        block_type = context.get('block_type', '').lower()
        word_count = len(text.split())
        
        # Simple structural heuristics
        if 'list_item' in block_type and word_count <= 3:
            return 'navigation_label'
        elif block_type in ['heading', 'section']:
            return 'topic_heading'
        elif block_type in ['table_cell'] and word_count <= 2:
            return 'data_reference'
        else:
            return 'descriptive_content'
    
    def _should_apply_rule(self, rule_category: str, content_classification: str) -> bool:
        """
        Linguistic anchor-based rule application matrix.
        
        Args:
            rule_category: Type of rule (completeness, grammar, technical, etc.)
            content_classification: Result from morphological classification
        """
        # Rule application matrix based on linguistic content analysis
        rule_matrix = {
            'technical_identifier': {
                'completeness': False,    # Technical identifiers are complete by nature
                'length': False,          # No arbitrary length requirements
                'articles': False,        # Technical terms don't follow article rules
                'fabrication': False,     # Technical identifiers aren't fabrication risks
                'grammar': True,          # Still check basic grammar
                'technical': True,        # Emphasize technical accuracy
                'spelling': True          # Emphasize spelling
            },
            'navigation_label': {
                'completeness': False,    # Navigation labels are intentionally concise
                'length': False, 
                'articles': False,        # Labels don't need articles
                'fabrication': False,     # Navigation isn't fabrication risk
                'grammar': True,
                'technical': True,
                'spelling': True
            },
            'topic_heading': {
                'completeness': False,    # Headings are naturally incomplete sentences
                'length': False,
                'articles': False,        # Headings often omit articles 
                'fabrication': False,     # Headings aren't fabrication risks
                'grammar': True,
                'technical': True,
                'spelling': True
            },
            'data_reference': {
                'completeness': False,    # Data values are references, not sentences
                'length': False,
                'articles': False,
                'fabrication': False,     # Data references aren't fabrication risks
                'grammar': False,         # Data follows different grammar rules
                'technical': True,
                'spelling': True
            },
            'procedural_instruction': {
                'completeness': True,     # Instructions should be complete
                'length': False,          # But not artificially lengthy
                'articles': False,        # Instructions often omit articles ("Click Save")
                'fabrication': False,     # Instructions aren't fabrication risks
                'grammar': True,
                'technical': True,
                'spelling': True
            },
            'descriptive_content': {
                'completeness': True,     # Full content should be complete
                'length': True,
                'articles': True,
                'fabrication': True,      # Full content can have fabrication risks
                'grammar': True,
                'technical': True,
                'spelling': True
            }
        }
        
        return rule_matrix.get(content_classification, {}).get(rule_category, True)
    
    def _is_technical_term(self, text: str) -> bool:
        """Check if text is a technical term that should be treated specially."""
        text_lower = text.lower().strip()
        
        # Common technical patterns
        technical_patterns = [
            # Development/DevOps terms
            'deployment', 'code scanning', 'image building', 'vulnerability detection',
            'integration', 'configuration', 'authentication', 'authorization',
            # Cloud/Infrastructure
            'monitoring', 'logging', 'scaling', 'load balancing', 'backup',
            # Software patterns
            'api', 'sdk', 'cli', 'ui', 'ux', 'ci/cd', 'git', 'docker',
        ]
        
        # Check direct matches
        if text_lower in technical_patterns:
            return True
            
        # Check patterns: "word word" technical terms
        words = text_lower.split()
        if len(words) == 2:
            # Technical compound terms
            if any(word in ['code', 'image', 'data', 'security', 'network', 'system'] for word in words):
                return True
                
        return False
    
    def _get_rule_category(self) -> str:
        """Map rule types to categories for the application matrix."""
        rule_type = self._get_rule_type()
        
        category_mapping = {
            # Completeness rules
            'llm_consumability': 'completeness',
            'sentence_length': 'length',
            
            # Grammar rules  
            'articles': 'articles',
            'pronouns': 'grammar',
            'verbs': 'grammar',
            'conjunctions': 'grammar',
            
            # Technical accuracy
            'terminology': 'technical',
            'capitalization': 'technical',
            'spelling': 'spelling',
            
            # Content integrity
            'fabrication_risk': 'fabrication',
            'ambiguity': 'fabrication',
            
            # Default to grammar for unmapped rules
        }
        
        return category_mapping.get(rule_type, 'grammar')
    
    # === Core SpaCy Analysis Methods ===
    
    def _analyze_sentence_structure(self, sentence: str, nlp=None) -> Optional[object]:
        """Get SpaCy doc for a sentence with error handling."""
        if nlp and sentence.strip():
            try:
                return nlp(sentence)
            except Exception:
                return None
        return None
    
    def _get_morphological_features(self, token) -> Dict[str, Any]:
        """Extract comprehensive morphological features from SpaCy token."""
        if not token:
            return {}
        
        features = {}
        try:
            # Basic morphological information
            features['pos'] = token.pos_
            features['tag'] = token.tag_
            features['lemma'] = token.lemma_
            features['dep'] = token.dep_
            
            # Detailed morphological analysis
            if hasattr(token, 'morph') and token.morph:
                features['morph'] = dict(token.morph) if hasattr(token.morph, '__iter__') else str(token.morph)
            
            # Linguistic properties
            features['is_alpha'] = token.is_alpha
            features['is_digit'] = token.is_digit
            features['is_punct'] = token.is_punct
            features['is_space'] = token.is_space
            features['is_stop'] = token.is_stop
            features['like_num'] = token.like_num
            features['like_url'] = token.like_url
            features['like_email'] = token.like_email
            
            # Word shape and case
            features['shape'] = token.shape_
            features['is_upper'] = token.is_upper
            features['is_lower'] = token.is_lower
            features['is_title'] = token.is_title
            
        except Exception:
            # Minimal fallback
            features = {
                'pos': getattr(token, 'pos_', ''),
                'tag': getattr(token, 'tag_', ''),
                'lemma': getattr(token, 'lemma_', token.text if hasattr(token, 'text') else str(token)),
                'dep': getattr(token, 'dep_', '')
            }
        
        return features
    
    def _extract_morphological_root(self, token) -> str:
        """Extract morphological root using SpaCy's lemmatization."""
        if not token:
            return ""
        
        try:
            # Use SpaCy's lemma as the morphological root
            lemma = token.lemma_.lower().strip()
            
            # Remove common inflectional endings using morphological analysis
            if hasattr(token, 'morph') and token.morph:
                morph_dict = dict(token.morph) if hasattr(token.morph, '__iter__') else {}
                
                # If it's a verb, get the base form
                if token.pos_ == 'VERB' and 'VerbForm' in morph_dict:
                    return lemma
                
                # If it's a noun, handle plurals
                if token.pos_ in ['NOUN', 'PROPN'] and 'Number' in morph_dict:
                    return lemma
                
                # If it's an adjective, handle comparatives/superlatives
                if token.pos_ == 'ADJ' and 'Degree' in morph_dict:
                    return lemma
            
            return lemma
            
        except Exception:
            return token.text.lower() if hasattr(token, 'text') else str(token).lower()
    
    def _calculate_morphological_complexity(self, token) -> float:
        """Calculate morphological complexity score using SpaCy features."""
        if not token:
            return 0.0
        
        complexity_score = 0.0
        
        try:
            # Base complexity from POS
            pos_complexity = {
                'NOUN': 1.0, 'VERB': 1.2, 'ADJ': 1.1, 'ADV': 1.1,
                'PROPN': 0.8, 'PRON': 0.5, 'DET': 0.3, 'ADP': 0.4,
                'CONJ': 0.3, 'CCONJ': 0.3, 'SCONJ': 0.5, 'PART': 0.4,
                'INTJ': 0.2, 'SYM': 0.1, 'X': 0.1
            }
            complexity_score += pos_complexity.get(token.pos_, 0.5)
            
            # Morphological feature complexity
            if hasattr(token, 'morph') and token.morph:
                morph_features = dict(token.morph) if hasattr(token.morph, '__iter__') else {}
                complexity_score += len(morph_features) * 0.1
            
            # Word length complexity (morphological complexity often correlates with length)
            word_length = len(token.text)
            if word_length > 8:
                complexity_score += (word_length - 8) * 0.05
            
            # Derivational complexity (estimated from lemma vs text difference)
            if hasattr(token, 'lemma_') and token.lemma_ != token.text:
                complexity_score += 0.2
            
        except Exception:
            # Fallback to basic length-based complexity
            complexity_score = min(len(token.text) / 10.0, 2.0) if hasattr(token, 'text') else 0.0
        
        return min(complexity_score, 5.0)  # Cap at 5.0
    
    def _analyze_semantic_field(self, token, doc=None) -> str:
        """Determine semantic field using SpaCy's linguistic features."""
        if not token:
            return 'unknown'
        
        try:
            # Use named entity recognition for semantic classification
            if hasattr(token, 'ent_type_') and token.ent_type_:
                entity_to_field = {
                    'PERSON': 'human',
                    'ORG': 'organization',
                    'GPE': 'location',
                    'LOC': 'location',
                    'PRODUCT': 'artifact',
                    'EVENT': 'event',
                    'FAC': 'facility',
                    'MONEY': 'economic',
                    'PERCENT': 'quantitative',
                    'DATE': 'temporal',
                    'TIME': 'temporal',
                    'CARDINAL': 'quantitative',
                    'ORDINAL': 'quantitative'
                }
                return entity_to_field.get(token.ent_type_, 'entity')
            
            # Use POS and dependency for semantic field classification
            pos = token.pos_
            dep = token.dep_
            
            if pos in ['NOUN', 'PROPN']:
                if dep in ['nsubj', 'nsubjpass']:
                    return 'agent'
                elif dep in ['dobj', 'iobj']:
                    return 'patient'
                elif dep == 'pobj':
                    return 'circumstance'
                else:
                    return 'entity'
            
            elif pos == 'VERB':
                if dep == 'ROOT':
                    return 'action'
                elif dep in ['aux', 'auxpass']:
                    return 'auxiliary'
                else:
                    return 'process'
            
            elif pos in ['ADJ', 'ADV']:
                return 'property'
            
            elif pos in ['ADP', 'SCONJ', 'CCONJ']:
                return 'relation'
            
            elif pos in ['DET', 'PRON']:
                return 'reference'
            
            else:
                return 'function'
                
        except Exception:
            return 'unknown'
    
    def _estimate_syllables_morphological(self, token) -> int:
        """Estimate syllables using morphological analysis and phonological patterns."""
        if not token:
            return 0
        
        try:
            word = token.text.lower() if hasattr(token, 'text') else str(token).lower()
            
            # Use morphological structure to estimate syllables
            morphological_complexity = self._calculate_morphological_complexity(token)
            
            # Basic phonological syllable estimation
            if not word or not word.isalpha():
                return 0
            
            # Count vowel groups (basic syllable estimation)
            vowels = "aeiouy"
            syllable_count = 0
            prev_was_vowel = False
            
            for char in word:
                is_vowel = char in vowels
                if is_vowel and not prev_was_vowel:
                    syllable_count += 1
                prev_was_vowel = is_vowel
            
            # Adjust for silent 'e'
            if word.endswith('e') and syllable_count > 1:
                syllable_count -= 1
            
            # Ensure at least one syllable
            syllable_count = max(syllable_count, 1)
            
            # Adjust based on morphological complexity
            if morphological_complexity > 2.0:
                syllable_count = max(syllable_count, int(morphological_complexity))
            
            return syllable_count
            
        except Exception:
            # Ultra-simple fallback
            word = str(token) if not hasattr(token, 'text') else token.text
            return max(1, len([c for c in word.lower() if c in "aeiouy"]))
    
    def _analyze_formality_level(self, token) -> float:
        """Analyze formality level using morphological features."""
        if not token:
            return 0.5
        
        try:
            formality_score = 0.5  # Neutral baseline
            
            # Use word length as formality indicator (longer words often more formal)
            word_length = len(token.text)
            if word_length > 8:
                formality_score += 0.2
            elif word_length < 4:
                formality_score -= 0.1
            
            # Use morphological complexity
            complexity = self._calculate_morphological_complexity(token)
            formality_score += (complexity - 1.0) * 0.1
            
            # Use syllable count
            syllables = self._estimate_syllables_morphological(token)
            if syllables > 3:
                formality_score += 0.1
            elif syllables == 1:
                formality_score -= 0.05
            
            # Latinate vs Germanic origin (approximated by morphological patterns)
            if self._has_latinate_morphology(token):
                formality_score += 0.2
            elif self._has_germanic_morphology(token):
                formality_score -= 0.1
            
            return max(0.0, min(1.0, formality_score))
            
        except Exception:
            return 0.5
    
    def _has_latinate_morphology(self, token) -> bool:
        """Check for Latinate morphological patterns."""
        if not token or not hasattr(token, 'text'):
            return False
        
        try:
            text = token.text.lower()
            lemma = token.lemma_.lower() if hasattr(token, 'lemma_') else text
            
            # Latinate endings (morphological indicators)
            latinate_patterns = [
                'tion', 'sion', 'ment', 'ance', 'ence', 'ity', 'ous', 
                'ive', 'ate', 'ize', 'ify', 'able', 'ible'
            ]
            
            return any(lemma.endswith(pattern) for pattern in latinate_patterns)
            
        except Exception:
            return False
    
    def _has_germanic_morphology(self, token) -> bool:
        """Check for Germanic morphological patterns."""
        if not token or not hasattr(token, 'text'):
            return False
        
        try:
            text = token.text.lower()
            lemma = token.lemma_.lower() if hasattr(token, 'lemma_') else text
            
            # Germanic patterns (simpler morphology)
            germanic_indicators = [
                len(text) <= 4,  # Germanic words often shorter
                text == lemma,   # Less inflection
                not self._has_latinate_morphology(token)  # Not Latinate
            ]
            
            return sum(germanic_indicators) >= 2
            
        except Exception:
            return False
    
    def _analyze_word_frequency_class(self, token, doc=None) -> str:
        """Analyze frequency class using morphological and contextual features."""
        if not token:
            return 'unknown'
        
        try:
            # Use SpaCy's statistical models for frequency estimation
            if hasattr(token, 'prob') and token.prob < -10:
                return 'rare'
            elif hasattr(token, 'prob') and token.prob > -5:
                return 'common'
            
            # Use POS as frequency indicator
            common_pos = ['DET', 'ADP', 'PRON', 'CCONJ', 'AUX']
            if token.pos_ in common_pos:
                return 'very_common'
            
            # Use morphological complexity as frequency indicator
            complexity = self._calculate_morphological_complexity(token)
            if complexity > 3.0:
                return 'rare'
            elif complexity < 1.0:
                return 'common'
            
            return 'medium'
            
        except Exception:
            return 'unknown'
    
    def _find_similar_tokens_morphologically(self, target_token, doc) -> List[object]:
        """Find morphologically similar tokens in the document."""
        if not target_token or not doc:
            return []
        
        similar_tokens = []
        target_features = self._get_morphological_features(target_token)
        target_root = self._extract_morphological_root(target_token)
        
        try:
            for token in doc:
                if token == target_token:
                    continue
                
                # Compare morphological roots
                token_root = self._extract_morphological_root(token)
                if target_root and token_root and target_root == token_root:
                    similar_tokens.append(token)
                    continue
                
                # Compare morphological features
                token_features = self._get_morphological_features(token)
                similarity_score = self._calculate_morphological_similarity(target_features, token_features)
                
                if similarity_score > 0.7:  # High similarity threshold
                    similar_tokens.append(token)
        
        except Exception:
            pass
        
        return similar_tokens
    
    def _calculate_morphological_similarity(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
        """Calculate morphological similarity between two feature sets."""
        if not features1 or not features2:
            return 0.0
        
        try:
            # Key morphological features to compare
            key_features = ['pos', 'lemma', 'morph']
            total_weight = 0.0
            weighted_similarity = 0.0
            
            for feature in key_features:
                if feature in features1 and feature in features2:
                    weight = 1.0
                    if feature == 'pos':
                        weight = 2.0  # POS is very important
                    elif feature == 'lemma':
                        weight = 1.5  # Lemma is important
                    
                    if features1[feature] == features2[feature]:
                        weighted_similarity += weight
                    
                    total_weight += weight
            
            return weighted_similarity / total_weight if total_weight > 0 else 0.0
            
        except Exception:
            return 0.0
    
    # === Serialization and Error Creation Methods ===
    
    def _token_to_dict(self, token) -> Optional[Dict[str, Any]]:
        """Convert SpaCy token to JSON-serializable dictionary."""
        if token is None:
            return None
        
        try:
            token_dict = {
                'text': token.text,
                'lemma': token.lemma_,
                'pos': token.pos_,
                'tag': token.tag_,
                'dep': token.dep_,
                'idx': token.idx,
                'i': token.i
            }
            
            # Add morphological features safely
            if hasattr(token, 'morph') and token.morph:
                try:
                    token_dict['morphology'] = dict(token.morph)
                except Exception:
                    token_dict['morphology'] = str(token.morph)
            else:
                token_dict['morphology'] = {}
            
            return token_dict
            
        except Exception:
            # Minimal fallback
            return {
                'text': str(token),
                'lemma': getattr(token, 'lemma_', ''),
                'pos': getattr(token, 'pos_', ''),
                'tag': getattr(token, 'tag_', ''),
                'dep': getattr(token, 'dep_', ''),
                'idx': getattr(token, 'idx', 0),
                'i': getattr(token, 'i', 0),
                'morphology': {}
            }
    
    def _tokens_to_list(self, tokens) -> List[Dict[str, Any]]:
        """Convert list of SpaCy tokens to JSON-serializable list."""
        if not tokens:
            return []
        
        result = []
        for token in tokens:
            token_dict = self._token_to_dict(token)
            if token_dict is not None:
                result.append(token_dict)
        
        return result
    
    def _make_serializable(self, data: Any) -> Any:
        """Recursively convert data structure to be JSON serializable."""
        if data is None:
            return None
        
        # Handle SpaCy tokens
        if hasattr(data, 'text') and hasattr(data, 'lemma_'):
            return self._token_to_dict(data)
        
        # Handle SpaCy objects with iteration but not standard types
        if (hasattr(data, '__iter__') and hasattr(data, 'get') and 
            not isinstance(data, (str, dict, list, tuple))):
            try:
                return dict(data)
            except Exception:
                return str(data)
        
        # Handle dictionaries
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                try:
                    serialized_value = self._make_serializable(value)
                    result[str(key)] = serialized_value  # Ensure key is string
                except Exception:
                    result[str(key)] = str(value)
            return result
        
        # Handle lists
        if isinstance(data, list):
            return [self._make_serializable(item) for item in data]
        
        # Handle tuples
        if isinstance(data, tuple):
            return [self._make_serializable(item) for item in data]  # Convert to list
        
        # Handle sets
        if isinstance(data, set):
            return [self._make_serializable(item) for item in data]
        
        # Handle primitive types
        if isinstance(data, (str, int, float, bool)):
            return data
        
        # Convert unknown types to string
        try:
            return str(data)
        except Exception:
            return None
    
    def _create_error(self, sentence: str, sentence_index: int, message: str, 
                     suggestions: List[str], severity: str = 'medium', 
                     text: Optional[str] = None, context: Optional[Dict[str, Any]] = None,
                     **extra_data) -> Dict[str, Any]:
        """
        Create standardized error dictionary with enhanced validation system integration.
        
        Args:
            sentence: The sentence containing the error
            sentence_index: Index of the sentence
            message: Error message
            suggestions: List of suggestions for fixing the error
            severity: Error severity level ('low', 'medium', 'high')
            text: Full text context (for enhanced validation)
            context: Additional context information
            **extra_data: Additional error data to include
            
        Returns:
            Enhanced error dictionary with confidence scores and validation results
        """
        if severity not in self.severity_levels:
            severity = 'medium'
        
        # Create base error structure (backward compatible)
        error = {
            'type': self.rule_type,
            'message': str(message),
            'suggestions': [str(s) for s in suggestions],
            'sentence': str(sentence),
            'sentence_index': int(sentence_index),
            'severity': severity
        }
        
        # Enhanced validation integration (if available)
        if ENHANCED_VALIDATION_AVAILABLE and self._confidence_calculator and self._validation_pipeline:
            try:
                enhanced_fields = self._calculate_enhanced_error_fields(
                    sentence, message, text, context, extra_data
                )
                error.update(enhanced_fields)
            except Exception as e:
                # Log warning but don't fail - maintain backward compatibility
                print(f"Warning: Enhanced validation failed for rule {self.rule_type}: {e}")
                # Add basic enhanced fields as fallback
                error.update({
                    'confidence_score': 0.5,  # Default confidence
                    'confidence_breakdown': None,
                    'validation_result': None,
                    'enhanced_validation_available': False,
                    'validation_error': str(e)
                })
        else:
            # Mark that enhanced validation is not available
            error['enhanced_validation_available'] = False
        
        # Add extra data with safe serialization
        for key, value in extra_data.items():
            try:
                error[str(key)] = self._make_serializable(value)
            except Exception as e:
                error[str(key)] = f"<serialization_error: {str(e)}>"
        
        return error
    
    def _calculate_enhanced_error_fields(self, sentence: str, message: str, 
                                       text: Optional[str], context: Optional[Dict[str, Any]],
                                       extra_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate enhanced error fields using confidence calculator and validation pipeline.
        
        Args:
            sentence: The sentence containing the error
            message: Error message
            text: Full text context
            context: Additional context information
            extra_data: Extra error data
            
        Returns:
            Dictionary with enhanced error fields
        """
        enhanced_fields = {
            'enhanced_validation_available': True,
            'confidence_score': 0.5,  # Default fallback
            'confidence_breakdown': None,
            'validation_result': None
        }
        
        # Use full text if available, otherwise fall back to sentence
        analysis_text = text or sentence
        
        # Extract error position and text from extra data if available
        error_position = extra_data.get('span', [0, 0])[0] if extra_data.get('span') else 0
        error_text = extra_data.get('flagged_text', '') or extra_data.get('error_text', '')
        
        # Get content metadata
        content_type = None
        domain = None
        if context:
            content_type = context.get('content_type') or context.get('block_type')
            domain = context.get('domain')
        
        # 1. Calculate normalized confidence score (replaces legacy confidence calculation)
        try:
            # Use the new normalized confidence calculation with provenance
            normalized_confidence, confidence_breakdown = self._confidence_calculator.calculate_normalized_confidence(
                text=analysis_text,
                error_position=error_position,
                rule_type=self.rule_type,
                content_type=content_type,
                rule_reliability=self._get_rule_reliability_coefficient(),
                base_confidence=0.5,
                evidence_score=extra_data.get('evidence_score'),
                return_breakdown=True
            )
            
            enhanced_fields['confidence_score'] = normalized_confidence
            
            # Include provenance for explainability (Upgrade 3)
            if hasattr(confidence_breakdown, 'confidence_provenance'):
                enhanced_fields['confidence_provenance'] = self._make_serializable(confidence_breakdown.confidence_provenance)
            
            # Also provide detailed breakdown for debugging/analysis
            enhanced_fields['confidence_breakdown'] = self._make_serializable(confidence_breakdown)
            
        except Exception as e:
            print(f"Warning: Confidence calculation failed: {e}")
            enhanced_fields['confidence_calculation_error'] = str(e)
        
        # 2. Run validation pipeline
        try:
            validation_context = ValidationContext(
                text=analysis_text,
                error_position=error_position,
                error_text=error_text,
                rule_type=self.rule_type,
                rule_name=self.__class__.__name__,
                rule_severity=extra_data.get('severity', 'medium'),
                content_type=content_type,
                domain=domain,
                confidence_breakdown=enhanced_fields.get('confidence_breakdown'),
                additional_context={
                    'sentence': sentence,
                    'message': message,
                    'suggestions': extra_data.get('suggestions', []),
                    'original_context': context or {}
                }
            )
            
            pipeline_result = self._validation_pipeline.validate_error(validation_context)
            enhanced_fields['validation_result'] = self._make_serializable(pipeline_result)
            
            # Extract key validation insights
            if pipeline_result and hasattr(pipeline_result, 'final_result'):
                final_result = pipeline_result.final_result
                enhanced_fields['validation_decision'] = final_result.decision.value if hasattr(final_result.decision, 'value') else str(final_result.decision)
                enhanced_fields['validation_confidence'] = final_result.confidence_score
                enhanced_fields['validation_reasoning'] = final_result.reasoning
                
                # Update overall confidence if validation provides better estimate
                if final_result.confidence_score > enhanced_fields['confidence_score']:
                    enhanced_fields['confidence_score'] = final_result.confidence_score
            
        except Exception as e:
            print(f"Warning: Validation pipeline failed: {e}")
            enhanced_fields['validation_pipeline_error'] = str(e)
        
        # Preserve Level 2 Enhanced Validation fields
        if text is not None:
            enhanced_fields['text'] = text
        if context is not None:
            enhanced_fields['context'] = context
        
        return enhanced_fields
        
    def _make_serializable(self, data: Any) -> Any:
        """Recursively convert data structure to be JSON serializable."""
        if data is None: return None
        if hasattr(data, 'text') and hasattr(data, 'lemma_'): return self._token_to_dict(data)
        if (hasattr(data, '__iter__') and hasattr(data, 'get') and not isinstance(data, (str, dict, list, tuple))):
            try: return dict(data)
            except Exception: return str(data)
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                try:
                    serialized_value = self._make_serializable(value)
                    result[str(key)] = serialized_value
                except Exception: result[str(key)] = str(value)
            return result
        if isinstance(data, list): return [self._make_serializable(item) for item in data]
        if isinstance(data, tuple): return [self._make_serializable(item) for item in data]
        if isinstance(data, set): return [self._make_serializable(item) for item in data]
        if isinstance(data, (str, int, float, bool)): return data
        try: return str(data)
        except Exception: return None

    def _token_to_dict(self, token) -> Optional[Dict[str, Any]]:
        if token is None: return None
        try:
            token_dict = {'text': token.text, 'lemma': token.lemma_, 'pos': token.pos_, 'tag': token.tag_, 'dep': token.dep_, 'idx': token.idx, 'i': token.i}
            if hasattr(token, 'morph') and token.morph:
                try: token_dict['morphology'] = dict(token.morph)
                except Exception: token_dict['morphology'] = str(token.morph)
            else: token_dict['morphology'] = {}
            return token_dict
        except Exception:
            return {'text': str(token), 'lemma': getattr(token, 'lemma_', ''), 'pos': getattr(token, 'pos_', ''), 'tag': getattr(token, 'tag_', ''), 'dep': getattr(token, 'dep_', ''), 'idx': getattr(token, 'idx', 0), 'i': getattr(token, 'i', 0), 'morphology': {}}

