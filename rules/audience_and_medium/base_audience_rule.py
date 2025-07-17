"""
Base Audience and Medium Rule
A base class that all specific audience and medium rules will inherit from.
This ensures a consistent interface for all rules in this category.
Enhanced with robust SpaCy morphological analysis and linguistic anchors.
"""

from typing import List, Dict, Any, Set, Tuple, Optional
from collections import defaultdict

# A generic base rule to be inherited from a central location
# in a real application. The # type: ignore comments prevent the
# static type checker from getting confused by the fallback class.
try:
    from ..base_rule import BaseRule  # type: ignore
except ImportError:
    class BaseRule:  # type: ignore
        def _get_rule_type(self) -> str:
            return 'base'
        def _create_error(self, **kwargs) -> Dict[str, Any]:
            return kwargs
        def _analyze_formality_level(self, token) -> float:
            return 0.5
        def _calculate_morphological_complexity(self, token) -> float:
            return 1.0
        def _get_morphological_features(self, token) -> Dict[str, Any]:
            return {}
        def _has_latinate_morphology(self, token) -> bool:
            return False
        def _analyze_semantic_field(self, token, doc=None) -> str:
            return 'unknown'
        def _token_to_dict(self, token) -> Optional[Dict[str, Any]]:
            return None
        def _analyze_sentence_structure(self, sentence: str, nlp=None):
            return nlp(sentence) if nlp and sentence.strip() else None
        def _estimate_syllables_morphological(self, token) -> int:
            return 1
        def _analyze_word_frequency_class(self, token, doc=None) -> str:
            return 'medium'


class BaseAudienceRule(BaseRule):
    """
    Enhanced base class for all audience and medium rules using pure SpaCy morphological analysis.
    Provides robust linguistic analysis utilities specific to audience and medium concerns.
    """

    def __init__(self):
        super().__init__()
        # Initialize linguistic anchors for audience-specific analysis
        self._initialize_linguistic_anchors()
    
    def _initialize_linguistic_anchors(self):
        """Initialize morphological and semantic anchors for audience analysis."""
        
        # Formality indicators based on morphological patterns
        self.formality_morphological_patterns = {
            'high_formality': {
                'suffixes': ['tion', 'sion', 'ment', 'ance', 'ence', 'ity', 'ous', 'ive', 'ate'],
                'pos_patterns': ['VERB+VerbForm=Ger', 'NOUN+Number=Sing', 'ADJ+Degree=Pos'],
                'dependency_patterns': ['nsubj+NOUN', 'dobj+NOUN', 'pobj+NOUN']
            },
            'low_formality': {
                'contractions': True,
                'pos_patterns': ['INTJ', 'PART+Polarity=Neg'],
                'dependency_patterns': ['discourse', 'intj'],
                'lemma_length': lambda x: len(x) <= 4
            }
        }
        
        # Complexity indicators for global audience accessibility
        self.complexity_morphological_indicators = {
            'lexical_complexity': {
                'syllable_threshold': 3,
                'morphological_complexity_threshold': 2.5,
                'latinate_morphology': True,
                'derivational_depth': 2  # Number of morphological transformations
            },
            'syntactic_complexity': {
                'max_sentence_length': 32,  # IBM guideline
                'max_dependency_depth': 5,
                'complex_constructions': ['nsubjpass', 'ccomp', 'xcomp', 'advcl']
            }
        }
        
        # Professional tone indicators using morphological features
        self.tone_morphological_markers = {
            'unprofessional_patterns': {
                'colloquial_contractions': ['ca', 'wo', 'sha'],  # can't, won't, shall
                'informal_intensifiers': ['really', 'totally', 'super'],
                'discourse_markers': ['like', 'you know', 'basically']
            },
            'professional_patterns': {
                'formal_verbs': ['demonstrate', 'facilitate', 'implement'],
                'technical_precision': True,
                'objective_language': True
            }
        }

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes the text for a specific audience or medium violation.
        This method must be implemented by all subclasses.
        """
        raise NotImplementedError("Subclasses must implement the analyze method.")
    
    def _analyze_conversational_appropriateness(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Analyze conversational appropriateness using morphological complexity.
        Returns errors for overly formal language that hinders conversational tone.
        """
        errors = []
        
        if not doc:
            return errors
        
        # Analyze each token for formality level
        overly_formal_tokens = []
        
        for token in doc:
            if not token.is_alpha or token.is_stop:
                continue
            
            # Calculate formality using morphological features
            formality_score = self._analyze_formality_level(token)
            morphological_complexity = self._calculate_morphological_complexity(token)
            
            # Check for overly formal morphological patterns
            if (formality_score > 0.8 and 
                morphological_complexity > 2.0 and 
                token.pos_ in ['VERB', 'NOUN', 'ADJ']):
                
                # Find simpler alternatives using morphological analysis
                simpler_alternative = self._find_simpler_morphological_alternative(token)
                
                if simpler_alternative:
                    overly_formal_tokens.append({
                        'token': token,
                        'alternative': simpler_alternative,
                        'formality_score': formality_score,
                        'complexity': morphological_complexity
                    })
        
        # Generate errors for overly formal tokens
        for formal_token in overly_formal_tokens:
            token = formal_token['token']
            alternative = formal_token['alternative']
            
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"The word '{token.text}' is too formal for conversational style. Use simpler language.",
                suggestions=[f"Replace '{token.text}' with '{alternative}' for better conversational tone."],
                severity='low',
                linguistic_analysis={
                    'formality_score': formal_token['formality_score'],
                    'morphological_complexity': formal_token['complexity'],
                    'morphological_features': self._get_morphological_features(token)
                }
            ))
        
        return errors
    
    def _analyze_global_accessibility(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Analyze text for global audience accessibility using morphological and syntactic features.
        """
        errors = []
        
        if not doc:
            return errors
        
        # Check sentence length and complexity
        sentence_complexity = self._calculate_sentence_complexity(doc)
        
        if sentence_complexity['word_count'] > self.complexity_morphological_indicators['syntactic_complexity']['max_sentence_length']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Sentence is too long ({sentence_complexity['word_count']} words) for global audiences. Aim for 32 words or fewer.",
                suggestions=["Break this sentence into shorter, simpler sentences."],
                severity='medium',
                linguistic_analysis=sentence_complexity
            ))
        
        # Detect negative constructions using dependency parsing
        negative_constructions = self._detect_negative_constructions(doc)
        
        for neg_construction in negative_constructions:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Avoid negative constructions. State conditions positively for global audiences.",
                suggestions=[f"Rewrite '{neg_construction['text']}' using positive language."],
                severity='medium',
                linguistic_analysis={
                    'negative_construction': neg_construction,
                    'morphological_pattern': neg_construction.get('pattern')
                }
            ))
        
        return errors
    
    def _analyze_professional_tone(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Analyze professional tone using morphological and semantic analysis.
        """
        errors = []
        
        if not doc:
            return errors
        
        # Detect informal language patterns
        informal_patterns = self._detect_informal_language_patterns(doc)
        
        for pattern in informal_patterns:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"The language pattern '{pattern['text']}' is too informal for professional communication.",
                suggestions=["Use more direct and professional language."],
                severity='medium',
                linguistic_analysis={
                    'informal_pattern': pattern,
                    'pattern_type': pattern.get('type'),
                    'morphological_features': pattern.get('morphological_features')
                }
            ))
        
        return errors
    
    def _find_simpler_morphological_alternative(self, token) -> Optional[str]:
        """
        Find simpler alternatives using morphological analysis.
        """
        if not token:
            return None
        
        # Morphologically-derived alternatives based on semantic fields
        morphological_alternatives = {
            # Latinate -> Germanic alternatives
            'utilize': 'use',
            'facilitate': 'help',
            'demonstrate': 'show',
            'implement': 'do',
            'commence': 'start',
            'terminate': 'end',
            'acquire': 'get',
            'construct': 'build',
            'accomplish': 'do',
            'sufficient': 'enough'
        }
        
        lemma = token.lemma_.lower()
        
        # Direct lookup
        if lemma in morphological_alternatives:
            return morphological_alternatives[lemma]
        
        # Morphological pattern matching for systematic alternatives
        if self._has_latinate_morphology(token):
            # Suggest Germanic equivalent based on semantic field
            semantic_field = self._analyze_semantic_field(token)
            
            if semantic_field == 'action':
                return 'do'
            elif semantic_field == 'entity':
                return 'thing'
            elif semantic_field == 'property':
                return 'good' if token.pos_ == 'ADJ' else 'well'
        
        return None
    
    def _calculate_sentence_complexity(self, doc) -> Dict[str, Any]:
        """
        Calculate comprehensive sentence complexity using morphological and syntactic features.
        """
        if not doc:
            return {'word_count': 0, 'complexity_score': 0.0}
        
        try:
            # Basic metrics
            word_count = len([token for token in doc if token.is_alpha])
            
            # Dependency depth (syntactic complexity)
            dependency_depth = self._calculate_dependency_depth(doc)
            
            # Morphological complexity
            avg_morphological_complexity = sum(
                self._calculate_morphological_complexity(token) 
                for token in doc if token.is_alpha
            ) / max(word_count, 1)
            
            # Lexical diversity (type-token ratio)
            unique_lemmas = len(set(token.lemma_.lower() for token in doc if token.is_alpha))
            lexical_diversity = unique_lemmas / max(word_count, 1)
            
            # Complex constructions count
            complex_deps = len([
                token for token in doc 
                if token.dep_ in self.complexity_morphological_indicators['syntactic_complexity']['complex_constructions']
            ])
            
            # Overall complexity score
            complexity_score = (
                (word_count / 32.0) * 0.3 +  # Length factor
                (dependency_depth / 5.0) * 0.3 +  # Syntactic factor
                avg_morphological_complexity * 0.2 +  # Morphological factor
                (complex_deps / max(word_count, 1)) * 0.2  # Construction factor
            )
            
            return {
                'word_count': word_count,
                'dependency_depth': dependency_depth,
                'avg_morphological_complexity': avg_morphological_complexity,
                'lexical_diversity': lexical_diversity,
                'complex_constructions': complex_deps,
                'complexity_score': complexity_score
            }
        
        except Exception:
            return {
                'word_count': len(doc) if doc else 0,
                'complexity_score': 0.0,
                'error': 'complexity_calculation_failed'
            }
    
    def _calculate_dependency_depth(self, doc) -> int:
        """Calculate maximum dependency tree depth."""
        if not doc:
            return 0
        
        def get_depth(token, visited=None):
            if visited is None:
                visited = set()
            
            if token in visited:
                return 0
            
            visited.add(token)
            
            if not list(token.children):
                return 1
            
            return 1 + max(get_depth(child, visited.copy()) for child in token.children)
        
        try:
            # Find root token
            root_tokens = [token for token in doc if token.dep_ == 'ROOT']
            if not root_tokens:
                return 0
            
            return max(get_depth(root) for root in root_tokens)
        
        except Exception:
            return 0
    
    def _detect_negative_constructions(self, doc) -> List[Dict[str, Any]]:
        """
        Detect negative constructions using dependency parsing and morphological analysis.
        """
        negative_constructions = []
        
        if not doc:
            return negative_constructions
        
        try:
            for token in doc:
                # Look for negation patterns
                if token.dep_ == 'neg':
                    head = token.head
                    
                    # Analyze the morphological context of the negation
                    construction_info = {
                        'negation_token': self._token_to_dict(token),
                        'head_token': self._token_to_dict(head),
                        'text': f"{token.text} {head.text}",
                        'pattern': f"{token.dep_}+{head.pos_}",
                        'morphological_features': {
                            'negation': self._get_morphological_features(token),
                            'head': self._get_morphological_features(head)
                        }
                    }
                    
                    # Check for specific problematic patterns
                    if (head.lemma_ in ['be', 'seem', 'appear'] and 
                        any(child.pos_ == 'ADJ' and child.lemma_ in ['different', 'unusual', 'uncommon'] 
                            for child in head.children)):
                        
                        construction_info['type'] = 'negative_state_with_adjective'
                        construction_info['severity'] = 'high'
                        negative_constructions.append(construction_info)
                    
                    elif head.pos_ == 'VERB':
                        construction_info['type'] = 'negative_verb'
                        construction_info['severity'] = 'medium'
                        negative_constructions.append(construction_info)
        
        except Exception:
            pass
        
        return negative_constructions
    
    def _detect_informal_language_patterns(self, doc) -> List[Dict[str, Any]]:
        """
        Detect informal language patterns using morphological and semantic analysis.
        """
        informal_patterns = []
        
        if not doc:
            return informal_patterns
        
        try:
            for token in doc:
                # Check for contractions using morphological analysis
                if "'" in token.text and token.pos_ in ['VERB', 'AUX']:
                    informal_patterns.append({
                        'token': self._token_to_dict(token),
                        'text': token.text,
                        'type': 'contraction',
                        'morphological_features': self._get_morphological_features(token),
                        'formality_score': self._analyze_formality_level(token)
                    })
                
                # Check for discourse markers and filler words
                if (token.dep_ == 'discourse' or 
                    (token.lemma_.lower() in ['like', 'you know', 'basically', 'actually'] and 
                     token.pos_ in ['INTJ', 'ADV'])):
                    
                    informal_patterns.append({
                        'token': self._token_to_dict(token),
                        'text': token.text,
                        'type': 'discourse_marker',
                        'morphological_features': self._get_morphological_features(token),
                        'semantic_field': self._analyze_semantic_field(token)
                    })
                
                # Check for overly casual intensifiers
                if (token.pos_ == 'ADV' and 
                    token.lemma_.lower() in ['really', 'totally', 'super', 'way'] and
                    any(child.pos_ == 'ADJ' for child in token.children)):
                    
                    informal_patterns.append({
                        'token': self._token_to_dict(token),
                        'text': token.text,
                        'type': 'casual_intensifier',
                        'morphological_features': self._get_morphological_features(token),
                        'modified_adjective': [self._token_to_dict(child) for child in token.children if child.pos_ == 'ADJ']
                    })
        
        except Exception:
            pass
        
        return informal_patterns
