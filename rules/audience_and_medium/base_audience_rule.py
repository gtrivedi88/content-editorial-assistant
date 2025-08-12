"""
Base Audience and Medium Rule
Enhanced base class following evidence-based rule development standards.
Provides shared utilities for audience/medium rules while enforcing rule-specific evidence calculation.
Each rule must implement its own _calculate_[RULE_TYPE]_evidence() method.
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
        def _create_error(self, sentence: str, sentence_index: int, message: str, 
                         suggestions: List[str], severity: str = 'medium', 
                         text: Optional[str] = None, context: Optional[Dict[str, Any]] = None,
                         **extra_data) -> Dict[str, Any]:
            """Fallback _create_error implementation when main BaseRule import fails."""
            # Create basic error structure for fallback scenarios
            error = {
                'type': getattr(self, 'rule_type', 'unknown'),
                'message': str(message),
                'suggestions': [str(s) for s in suggestions],
                'sentence': str(sentence),
                'sentence_index': int(sentence_index),
                'severity': severity,
                'enhanced_validation_available': False  # Mark as fallback
            }
            # Add any extra data
            error.update(extra_data)
            return error
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
    This class provides shared utilities for audience and medium rules.Each rule must implement its own _calculate_[RULE_TYPE]_evidence()
    method for zero false positive goals.
    
    Provides:
    - Shared linguistic analysis utilities
    - Common morphological pattern detection
    - Consistent error message formatting
    - Evidence-aware suggestion generation helpers
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
        ABSTRACT: Each rule must implement its own analyze method.
        
        Rules must implement rule-specific evidence calculation
        rather than using centralized evidence methods for optimal precision.
        
        Required implementation pattern:
        1. Find potential issues using rule-specific detection
        2. Calculate evidence using rule-specific _calculate_[RULE_TYPE]_evidence()
        3. Apply zero false positive guards specific to rule domain
        4. Use evidence-aware messaging and suggestions
        
        Returns:
            List of errors with rule-specific evidence scores
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement its own analyze() method "
            f"with rule-specific evidence calculation."
        )
    
    # === SHARED UTILITIES ===
    # These methods provide common functionality for all audience/medium rules
    # while each rule implements its own evidence calculation for precision
    
    def _apply_zero_false_positive_guards_audience(self, token, context: Dict[str, Any]) -> bool:
        """
        Apply surgical zero false positive guards for audience/medium rules.
        Returns True if evidence should be killed immediately.
        
        CRITICAL: These guards must be surgical - eliminate false positives while 
        preserving ALL legitimate violations. Individual rules should extend with 
        rule-specific guards.
        """
        if not token or not hasattr(token, 'text'):
            return True
            
        # === STRUCTURAL CONTEXT GUARDS ===
        # Code blocks have different linguistic rules
        if context and context.get('block_type') in ['code_block', 'inline_code', 'literal_block']:
            return True
            
        # === ENTITY AND PROPER NOUN GUARDS ===
        # Named entities are not style violations
        if hasattr(token, 'ent_type_') and token.ent_type_ in ['PERSON', 'ORG', 'PRODUCT', 'EVENT', 'GPE']:
            return True
            
        # === TECHNICAL IDENTIFIER GUARDS ===
        # URLs, file paths, technical identifiers
        if hasattr(token, 'like_url') and token.like_url:
            return True
        if hasattr(token, 'text') and ('/' in token.text or '\\' in token.text or token.text.startswith('http')):
            return True
            
        # === ACRONYM AND ABBREVIATION GUARDS ===
        # Short uppercase tokens in technical contexts (but allow style rules to check appropriateness)
        if (hasattr(token, 'text') and token.text.isupper() and len(token.text) <= 5 and
            context and context.get('content_type') in ['technical', 'api', 'code']):
            return True
            
        # === QUOTED CONTENT GUARDS ===
        # Don't flag content in quotes (examples, citations, UI labels)
        if self._is_in_quoted_context(token, context):
            return True
            
        # === FOREIGN LANGUAGE GUARDS ===
        # Don't flag tokens identified as foreign language
        if hasattr(token, 'lang_') and token.lang_ != 'en':
            return True
            
        return False
    
    def _is_in_quoted_context(self, token, context: Dict[str, Any]) -> bool:
        """
        Check if token appears in quoted context (examples, citations, UI labels).
        Surgical check - only true quotes, not legitimate content with apostrophes.
        """
        if not hasattr(token, 'doc') or not token.doc:
            return False
            
        # Look for actual quotation marks around the token
        sent = token.sent
        token_idx = token.i - sent.start
        
        # Check for quotation marks in reasonable proximity
        quote_chars = ['"', '"', '"', "'", "'"]
        
        # Look backwards and forwards for quote pairs
        before_quotes = 0
        after_quotes = 0
        
        # Search backwards
        for i in range(max(0, token_idx - 10), token_idx):
            if i < len(sent) and sent[i].text in quote_chars:
                before_quotes += 1
                
        # Search forwards  
        for i in range(token_idx + 1, min(len(sent), token_idx + 10)):
            if i < len(sent) and sent[i].text in quote_chars:
                after_quotes += 1
        
        # If we have quotes both before and after, likely quoted content
        return before_quotes > 0 and after_quotes > 0
    
    def _generate_evidence_aware_message(self, issue: Dict[str, Any], evidence_score: float, 
                                       rule_type: str = "audience") -> str:
        """
        Generate evidence-aware error messages for audience/medium rules.
        Adapts message tone based on evidence confidence.
        """
        token_text = issue.get('text', issue.get('phrase', ''))
        
        if evidence_score > 0.85:
            # High confidence -> Direct, authoritative message
            return f"The {rule_type} concern '{token_text}' clearly violates style guidelines."
        elif evidence_score > 0.6:
            # Medium confidence -> Balanced suggestion
            return f"Consider if '{token_text}' is appropriate for your target audience."
        else:
            # Low confidence -> Gentle, optional suggestion
            return f"'{token_text}' may be acceptable, but alternatives could improve audience alignment."
    
    def _generate_evidence_aware_suggestions(self, issue: Dict[str, Any], evidence_score: float,
                                           context: Dict[str, Any], rule_type: str = "audience") -> List[str]:
        """
        Generate evidence-aware suggestions for audience/medium rules.
        Higher evidence = more confident, direct suggestions.
        """
        suggestions = []
        token_text = issue.get('text', issue.get('phrase', ''))
        
        if evidence_score > 0.8:
            # High confidence -> Direct, confident suggestions
            suggestions.append(f"Replace '{token_text}' for immediate compliance with {rule_type} guidelines.")
            suggestions.append("This clearly violates professional communication standards.")
        elif evidence_score > 0.6:
            # Medium confidence -> Balanced suggestions  
            suggestions.append(f"Consider revising '{token_text}' for better audience alignment.")
            suggestions.append("A more appropriate alternative would improve communication effectiveness.")
        else:
            # Low confidence -> Gentle, optional suggestions
            suggestions.append(f"'{token_text}' may be acceptable, but consider alternatives for optimization.")
            suggestions.append("This is a minor style suggestion for enhanced audience engagement.")
        
        # Add context-specific suggestions based on evidence
        if evidence_score > 0.7:
            audience = context.get('audience', 'general')
            if audience in ['general', 'beginner']:
                suggestions.append("Simpler language improves accessibility for general audiences.")
            elif audience in ['expert', 'developer']:
                suggestions.append("Even expert audiences benefit from clear, direct communication.")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    # === SHARED MORPHOLOGICAL ANALYSIS UTILITIES ===
    
    def _get_shared_formality_indicators(self, token) -> Dict[str, Any]:
        """Get formality indicators that are shared across audience rules."""
        if not token or not hasattr(token, 'text'):
            return {}
            
        return {
            'formality_score': self._analyze_formality_level(token),
            'morphological_complexity': self._calculate_morphological_complexity(token),
            'has_latinate_morphology': self._has_latinate_morphology(token),
            'semantic_field': self._analyze_semantic_field(token),
            'syllable_count': self._estimate_syllables_morphological(token),
            'word_frequency_class': self._analyze_word_frequency_class(token)
        }
    
    def _detect_common_audience_patterns(self, doc) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect common patterns that multiple audience rules care about.
        Returns categorized findings for rules to use in their specific evidence calculation.
        """
        if not doc:
            return {}
            
        patterns = {
            'formal_words': [],
            'informal_patterns': [],
            'complex_constructions': [],
            'accessibility_issues': []
        }
        
        try:
            for token in doc:
                if not token.is_alpha or token.is_stop:
                    continue
                    
                # Detect overly formal words
                formality_indicators = self._get_shared_formality_indicators(token)
                if (formality_indicators['formality_score'] > 0.7 and 
                    formality_indicators['morphological_complexity'] > 1.8):
                    patterns['formal_words'].append({
                        'token': token,
                        'indicators': formality_indicators
                    })
                
                # Detect informal patterns (contractions, discourse markers)
                if "'" in token.text and token.pos_ in ['VERB', 'AUX']:
                    patterns['informal_patterns'].append({
                        'token': token,
                        'type': 'contraction',
                        'indicators': formality_indicators
                    })
                
                # Detect complex constructions
                if token.dep_ in ['nsubjpass', 'ccomp', 'xcomp', 'advcl']:
                    patterns['complex_constructions'].append({
                        'token': token,
                        'construction_type': token.dep_,
                        'complexity': formality_indicators['morphological_complexity']
                    })
        
        except Exception:
            pass  # Graceful degradation
            
        return patterns
    
    def _find_simpler_morphological_alternative(self, token) -> Optional[str]:
        """
        Find simpler alternatives using morphological analysis.
        Shared utility for audience rules that need to suggest alternatives.
        """
        if not token or not hasattr(token, 'lemma_'):
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