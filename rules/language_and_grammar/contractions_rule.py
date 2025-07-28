"""
Contractions Rule
Based on IBM Style Guide topic: "Contractions"
Enhanced with universal spaCy morphological analysis for scalable detection.
"""
from typing import List, Dict, Any, Optional
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ContractionsRule(BaseLanguageRule):
    """
    Detects contractions using universal spaCy morphological features.
    Uses linguistic anchors based on morphological analysis rather than 
    hardcoded patterns, making it scalable without code updates.
    """
    
    def __init__(self):
        super().__init__()
        self._initialize_morphological_anchors()
    
    def _initialize_morphological_anchors(self):
        """Initialize comprehensive universal linguistic anchors for contraction detection."""
        
        # UNIVERSAL LINGUISTIC ANCHORS - Based on morphological features
        self.contraction_morphological_patterns = {
            'negative_contractions': {
                'morph_features': {'Polarity': 'Neg'},
                'pos_patterns': ['PART'],
                'tag_patterns': ['RB'],  # Added for negative adverbs
                'lemma_indicators': ['not'],
                'description': 'negative particle'
            },
            'auxiliary_contractions': {
                'morph_features': {'VerbForm': 'Fin', 'VerbType': 'Mod'},
                'pos_patterns': ['AUX', 'VERB'],
                'tag_patterns': ['MD', 'VBP', 'VBZ', 'VBD', 'VBN'],  # Modal and verb tags
                'lemma_indicators': ['be', 'have', 'will', 'would', 'shall', 'should', 'can', 'could', 'must', 'might', 'may'],
                'description': 'auxiliary verb contraction'
            },
            'possessive_particles': {
                'tag_patterns': ['POS'],
                'pos_patterns': ['PART'],
                'dep_patterns': ['case'],
                'description': 'possessive marker'
            },
            'pronominal_contractions': {
                'morph_features': {'PronType': 'Prs'},
                'pos_patterns': ['PRON'],
                'tag_patterns': ['PRP'],  # Added personal pronoun tag
                'lemma_indicators': ['I', 'you', 'he', 'she', 'it', 'we', 'they'],
                'description': 'pronominal contraction'
            },
            # NEW PATTERNS for better coverage
            'modal_auxiliary': {
                'morph_features': {'VerbType': 'Mod'},
                'pos_patterns': ['AUX'],
                'tag_patterns': ['MD'],
                'lemma_indicators': ['will', 'would', 'shall', 'should', 'can', 'could', 'must', 'might', 'may'],
                'description': 'modal auxiliary'
            },
            'copula_contractions': {
                'morph_features': {'VerbForm': 'Fin'},
                'pos_patterns': ['AUX', 'VERB'],
                'tag_patterns': ['VBZ', 'VBP', 'VBD'],
                'lemma_indicators': ['be'],
                'description': 'copula verb'
            },
            'perfect_auxiliary': {
                'morph_features': {'VerbForm': 'Fin'},
                'pos_patterns': ['AUX', 'VERB'],
                'tag_patterns': ['VBZ', 'VBP', 'VBD', 'VBN'],
                'lemma_indicators': ['have', 'has', 'had'],
                'description': 'perfect auxiliary'
            },
            'future_auxiliary': {
                'pos_patterns': ['AUX'],
                'tag_patterns': ['MD'],
                'lemma_indicators': ['will', 'shall'],
                'description': 'future auxiliary'
            }
        }
        
        # ENHANCED FALLBACK PATTERNS - Still linguistic but more permissive
        self.fallback_linguistic_patterns = {
            'common_contraction_lemmas': {
                'be', 'have', 'has', 'had', 'will', 'would', 'shall', 'should', 
                'can', 'could', 'must', 'might', 'may', 'not', 'do', 'does', 'did'
            },
            'contraction_pos_tags': {
                'AUX', 'VERB', 'PART', 'PRON'
            },
            'contraction_penn_tags': {
                'MD', 'VBZ', 'VBP', 'VBD', 'VBN', 'POS', 'RB', 'PRP'
            },
            'contraction_dependencies': {
                'aux', 'auxpass', 'cop', 'neg', 'case'
            }
        }
    
    def _get_rule_type(self) -> str:
        return 'contractions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        
        doc = nlp(text)
        
        for sent in doc.sents:
            for token in sent:
                # UNIVERSAL LINGUISTIC ANCHOR: Check if token has contraction characteristics
                if self._is_contraction_by_morphology(token):
                    contraction_info = self._analyze_contraction_morphology(token)
                    
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=list(doc.sents).index(sent),
                        message=f"Contraction found: '{token.text}' ({contraction_info['type']}).",
                        suggestions=[f"Expand contractions for a more formal tone: {contraction_info['suggestion']}."],
                        severity='low',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
        
        return errors
    
    def _is_contraction_by_morphology(self, token) -> bool:
        """
        Enhanced universal contraction detection using comprehensive morphological features.
        No hardcoded patterns - uses spaCy's linguistic analysis with expanded coverage.
        """
        if not token or not hasattr(token, 'text'):
            return False
            
        # UNIVERSAL ANCHOR 1: Must contain apostrophe (all contractions do)
        if "'" not in token.text:
            return False
        
        # Get comprehensive morphological features
        morph_features = self._get_morphological_features(token)
        
        # UNIVERSAL ANCHOR 2: Check against expanded morphological patterns
        for pattern_name, pattern in self.contraction_morphological_patterns.items():
            if self._matches_morphological_pattern(morph_features, pattern):
                return True
        
        # UNIVERSAL ANCHOR 3: Enhanced linguistic fallback using spaCy analysis
        if self._is_linguistic_contraction_pattern(token):
            return True
        
        return False
    
    def _is_linguistic_contraction_pattern(self, token) -> bool:
        """
        Enhanced fallback using spaCy's comprehensive linguistic analysis.
        Still uses spaCy features but more permissive for missed morphological cases.
        """
        if not token:
            return False
        
        morph_features = self._get_morphological_features(token)
        
        # LINGUISTIC ANCHOR 1: Check lemma against common contraction sources
        lemma = morph_features.get('lemma', '').lower()
        if lemma in self.fallback_linguistic_patterns['common_contraction_lemmas']:
            return True
        
        # LINGUISTIC ANCHOR 2: Check POS patterns
        pos = morph_features.get('pos', '')
        if pos in self.fallback_linguistic_patterns['contraction_pos_tags']:
            return True
        
        # LINGUISTIC ANCHOR 3: Check Penn Treebank tags
        tag = morph_features.get('tag', '')
        if tag in self.fallback_linguistic_patterns['contraction_penn_tags']:
            return True
        
        # LINGUISTIC ANCHOR 4: Check dependency relations
        dep = morph_features.get('dep', '')
        if dep in self.fallback_linguistic_patterns['contraction_dependencies']:
            return True
        
        # LINGUISTIC ANCHOR 5: Check for auxiliary-like behavior in context
        if self._has_auxiliary_behavior(token):
            return True
        
        return False
    
    def _has_auxiliary_behavior(self, token) -> bool:
        """
        Detect auxiliary-like behavior using spaCy's dependency and context analysis.
        Uses syntactic patterns rather than morphological features.
        """
        if not token:
            return False
        
        try:
            # Check if token has auxiliary-like dependencies
            if hasattr(token, 'dep_') and token.dep_ in ['aux', 'auxpass', 'cop']:
                return True
            
            # Check if token governs auxiliary-like structures
            if hasattr(token, 'children'):
                child_deps = [child.dep_ for child in token.children]
                if any(dep in ['nsubj', 'dobj', 'prep'] for dep in child_deps):
                    return True
            
            # Check if token is governed by main verbs (auxiliary pattern)
            if hasattr(token, 'head') and hasattr(token.head, 'pos_'):
                if token.head.pos_ == 'VERB' and token.pos_ in ['AUX', 'VERB']:
                    return True
            
            return False
            
        except Exception:
            return False

    def _matches_morphological_pattern(self, token_features: Dict[str, Any], pattern: Dict[str, Any]) -> bool:
        """Enhanced pattern matching with multiple validation layers."""
        
        # PRIORITY 1: Check TAG patterns first (most reliable for contractions)
        if 'tag_patterns' in pattern:
            if token_features.get('tag') in pattern['tag_patterns']:
                return True
        
        # PRIORITY 2: Check morphological features (for semantic understanding)
        if 'morph_features' in pattern and 'morph' in token_features:
            pattern_morph = pattern['morph_features']
            token_morph = token_features.get('morph', {})
            
            if isinstance(token_morph, dict) and pattern_morph:
                # ANY morphological feature match (more permissive than ALL)
                for key, value in pattern_morph.items():
                    if token_morph.get(key) == value:
                        return True
        
        # PRIORITY 3: Check POS patterns with lemma validation
        if 'pos_patterns' in pattern:
            if token_features.get('pos') in pattern['pos_patterns']:
                # If lemma indicators exist, use them for additional validation
                if 'lemma_indicators' in pattern:
                    token_lemma = token_features.get('lemma', '').lower()
                    if token_lemma in pattern['lemma_indicators']:
                        return True
                else:
                    return True
        
        # PRIORITY 4: Check dependency patterns
        if 'dep_patterns' in pattern:
            if token_features.get('dep') in pattern['dep_patterns']:
                return True
        
        # PRIORITY 5: Check lemma patterns alone (for when morphology fails)
        if 'lemma_indicators' in pattern:
            token_lemma = token_features.get('lemma', '').lower()
            if token_lemma in pattern['lemma_indicators']:
                return True
        
        return False
    
    def _analyze_contraction_morphology(self, token) -> Dict[str, str]:
        """Enhanced contraction analysis with better pattern matching and suggestions."""
        morph_features = self._get_morphological_features(token)
        
        # Determine contraction type based on expanded morphological features
        for pattern_name, pattern in self.contraction_morphological_patterns.items():
            if self._matches_morphological_pattern(morph_features, pattern):
                suggestion = self._generate_expansion_suggestion(token, morph_features, pattern)
                return {
                    'type': pattern['description'],
                    'suggestion': suggestion,
                    'pattern': pattern_name
                }
        
        # Enhanced fallback analysis with specific contraction identification
        lemma = morph_features.get('lemma', '').lower()
        pos = morph_features.get('pos', '')
        token_text = token.text.lower()  # Get token text directly from token
        
        # More specific contraction detection
        if "'s" in token_text or "'s" in token_text:
            # Determine if 's is "is" or possessive
            if lemma == 'be' or pos in ['AUX', 'VERB']:
                return {
                    'type': "auxiliary verb contraction ('s = is)",
                    'suggestion': f"use 'is' instead of the contraction",
                    'pattern': 'specific_is_contraction'
                }
            else:
                return {
                    'type': "possessive or auxiliary contraction ('s)",
                    'suggestion': f"use the full form instead of the contraction",
                    'pattern': 'specific_s_contraction'
                }
        elif "'re" in token_text or "'re" in token_text:
            return {
                'type': "auxiliary verb contraction ('re = are)",
                'suggestion': "use 'are' instead of the contraction",
                'pattern': 'specific_are_contraction'
            }
        elif "'ve" in token_text or "'ve" in token_text:
            return {
                'type': "auxiliary verb contraction ('ve = have)",
                'suggestion': "use 'have' instead of the contraction",
                'pattern': 'specific_have_contraction'
            }
        elif "'ll" in token_text or "'ll" in token_text:
            return {
                'type': "auxiliary verb contraction ('ll = will)",
                'suggestion': "use 'will' instead of the contraction",
                'pattern': 'specific_will_contraction'
            }
        elif "'d" in token_text or "'d" in token_text:
            return {
                'type': "auxiliary verb contraction ('d = would/had)",
                'suggestion': "use 'would' or 'had' instead of the contraction",
                'pattern': 'specific_d_contraction'
            }
        elif "'t" in token_text or "'t" in token_text:
            return {
                'type': "negative contraction ('t = not)",
                'suggestion': "use 'not' instead of the negative contraction",
                'pattern': 'specific_not_contraction'
            }
        elif lemma in ['not']:
            return {
                'type': 'negative contraction',
                'suggestion': "use 'not' instead of the negative contraction",
                'pattern': 'fallback_negative'
            }
        elif lemma in ['be', 'have', 'will', 'would', 'can', 'could', 'should', 'shall', 'must', 'might', 'may']:
            return {
                'type': f'auxiliary verb contraction ({lemma})',
                'suggestion': f"use '{lemma}' instead of the contraction",
                'pattern': 'fallback_auxiliary'
            }
        elif pos == 'PRON':
            return {
                'type': 'pronominal contraction',
                'suggestion': "use the full pronoun form",
                'pattern': 'fallback_pronoun'
            }
        else:
            return {
                'type': 'contraction',
                'suggestion': 'expand the contraction for a more formal tone',
                'pattern': 'fallback_general'
            }
    
    def _generate_expansion_suggestion(self, token, features: Dict[str, Any], pattern: Dict[str, Any]) -> str:
        """Generate enhanced context-aware expansion suggestions using morphological analysis."""
        
        lemma = features.get('lemma', '').lower()
        pos = features.get('pos', '')
        pattern_desc = pattern.get('description', '')
        
        # Enhanced pattern-specific suggestions
        if pattern_desc == 'possessive marker':
            return "avoid possessive contractions; rephrase to use 'of' or full forms (e.g., 'the system configuration' not 'system's configuration')"
        elif pattern_desc == 'pronominal contraction':
            return f"expand to the full pronoun form" if lemma else "use the full pronoun form"
        elif pattern_desc == 'negative particle':
            return "use 'not' instead of the negative contraction"
        elif pattern_desc in ['modal auxiliary', 'future auxiliary']:
            return f"use '{lemma}' instead of the modal contraction" if lemma else "use the full modal verb form"
        elif pattern_desc == 'copula verb':
            return f"use '{lemma}' instead of the copula contraction" if lemma else "use the full copula verb form"
        elif pattern_desc == 'perfect auxiliary':
            return f"use '{lemma}' instead of the perfect auxiliary contraction" if lemma else "use the full auxiliary verb form"
        elif pattern_desc == 'auxiliary verb contraction':
            # Be specific about what type of auxiliary verb
            if lemma == 'be':
                return f"use 'is' instead of the contraction"
            elif lemma in ['have', 'will', 'would', 'can', 'could', 'should', 'shall', 'must', 'might', 'may']:
                return f"use '{lemma}' instead of the contraction"
            else:
                return f"use '{lemma}' instead of the auxiliary verb contraction"
        
        # Enhanced morphological pattern-based suggestions
        if lemma and lemma != token.text.lower():
            if lemma == 'not':
                return "use 'not' instead of the negative contraction"
            elif lemma in ['be', 'am', 'is', 'are', 'was', 'were']:
                return f"use the full form of 'be' instead of the contraction"
            elif lemma in ['have', 'has', 'had']:
                return f"use '{lemma}' instead of the perfect auxiliary contraction"
            elif lemma in ['will', 'would', 'shall', 'should', 'can', 'could', 'must', 'might', 'may']:
                return f"use '{lemma}' instead of the modal contraction"
            else:
                return f"expand to '{lemma}'"
        
        # Fallback suggestions based on morphological analysis
        morph = features.get('morph', {})
        if isinstance(morph, dict):
            if morph.get('Polarity') == 'Neg':
                return "use 'not' instead of the negative contraction"
            elif morph.get('VerbForm') == 'Fin':
                return "use the full verb form instead of the contraction"
            elif morph.get('VerbType') == 'Mod':
                return "use the full modal verb instead of the contraction"
            elif morph.get('PronType') == 'Prs':
                return "use the full pronoun form instead of the contraction"
        
        return "expand the contraction for a more formal tone"
