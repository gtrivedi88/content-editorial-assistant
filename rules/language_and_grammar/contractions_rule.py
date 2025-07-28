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
        """Initialize universal linguistic anchors for contraction detection."""
        
        # UNIVERSAL LINGUISTIC ANCHORS - Based on morphological features
        self.contraction_morphological_patterns = {
            'negative_contractions': {
                'morph_features': {'Polarity': 'Neg'},
                'pos_patterns': ['PART'],
                'lemma_indicators': ['not'],
                'description': 'negative particle'
            },
            'auxiliary_contractions': {
                'morph_features': {'VerbForm': 'Fin', 'VerbType': 'Mod'},
                'pos_patterns': ['AUX', 'VERB'],
                'lemma_indicators': ['be', 'have', 'will', 'would', 'shall', 'should'],
                'description': 'auxiliary verb'
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
                'description': 'pronominal contraction'
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
        Universal contraction detection using morphological features.
        No hardcoded patterns - uses spaCy's linguistic analysis.
        """
        if not token or not hasattr(token, 'text'):
            return False
            
        # UNIVERSAL ANCHOR 1: Must contain apostrophe (all contractions do)
        if "'" not in token.text:
            return False
        
        # Get comprehensive morphological features
        morph_features = self._get_morphological_features(token)
        
        # UNIVERSAL ANCHOR 2: Check against morphological patterns
        for pattern_name, pattern in self.contraction_morphological_patterns.items():
            if self._matches_morphological_pattern(morph_features, pattern):
                return True
        
        return False
    
    def _matches_morphological_pattern(self, token_features: Dict[str, Any], pattern: Dict[str, Any]) -> bool:
        """Check if token features match a morphological pattern."""
        
        # PRIORITY 1: Check TAG patterns first (most specific for contractions)
        if 'tag_patterns' in pattern:
            if token_features.get('tag') in pattern['tag_patterns']:
                # Additional validation for TAG patterns
                if 'pos_patterns' in pattern:
                    return token_features.get('pos') in pattern['pos_patterns']
                if 'dep_patterns' in pattern:
                    return token_features.get('dep') in pattern['dep_patterns']
                return True
        
        # PRIORITY 2: Check morphological features (for verbs and negatives)
        if 'morph_features' in pattern and 'morph' in token_features:
            pattern_morph = pattern['morph_features']
            token_morph = token_features.get('morph', {})
            
            if isinstance(token_morph, dict):
                # ALL morphological features in pattern must match
                matches_all = True
                for key, value in pattern_morph.items():
                    if token_morph.get(key) != value:
                        matches_all = False
                        break
                if matches_all and pattern_morph:  # Ensure pattern is not empty
                    return True
        
        # PRIORITY 3: Check POS patterns with additional constraints
        if 'pos_patterns' in pattern:
            if token_features.get('pos') in pattern['pos_patterns']:
                # Additional validation for POS patterns
                if 'lemma_indicators' in pattern:
                    token_lemma = token_features.get('lemma', '').lower()
                    return token_lemma in pattern['lemma_indicators']
                return True
        
        # PRIORITY 4: Check dependency patterns
        if 'dep_patterns' in pattern:
            if token_features.get('dep') in pattern['dep_patterns']:
                return True
        
        return False
    
    def _analyze_contraction_morphology(self, token) -> Dict[str, str]:
        """Analyze contraction type and generate suggestions using morphology."""
        morph_features = self._get_morphological_features(token)
        
        # Determine contraction type based on morphological features
        for pattern_name, pattern in self.contraction_morphological_patterns.items():
            if self._matches_morphological_pattern(morph_features, pattern):
                suggestion = self._generate_expansion_suggestion(token, morph_features, pattern)
                return {
                    'type': pattern['description'],
                    'suggestion': suggestion,
                    'pattern': pattern_name
                }
        
        # Fallback for unknown patterns
        return {
            'type': 'contraction',
            'suggestion': 'expand the contraction',
            'pattern': 'unknown'
        }
    
    def _generate_expansion_suggestion(self, token, features: Dict[str, Any], pattern: Dict[str, Any]) -> str:
        """Generate context-aware expansion suggestions using morphological analysis."""
        
        lemma = features.get('lemma', '').lower()
        pos = features.get('pos', '')
        pattern_desc = pattern.get('description', '')
        
        # Pattern-specific suggestions
        if pattern_desc == 'possessive marker':
            return "avoid possessive contractions; rephrase to use 'of' or full forms (e.g., 'the system configuration' not 'system's configuration')"
        elif pattern_desc == 'pronominal contraction':
            return f"expand to '{lemma}'" if lemma and lemma != token.text.lower() else "use the full pronoun form"
        
        # Use morphological lemma for accurate suggestions
        if lemma and lemma != token.text.lower():
            if lemma in ['be', 'have', 'will', 'would', 'shall', 'should', 'can', 'could', 'must']:
                return f"use '{lemma}' instead of the contraction"
            elif lemma == 'not':
                return "use 'not' instead of the negative contraction"
            else:
                return f"expand to '{lemma}'"
        
        # Morphological pattern-based suggestions
        morph = features.get('morph', {})
        if isinstance(morph, dict):
            if morph.get('Polarity') == 'Neg':
                return "use 'not' instead of the negative contraction"
            elif morph.get('VerbForm') == 'Fin':
                return "use the full verb form instead of the contraction"
            elif morph.get('VerbType') == 'Mod':
                return "use the full modal verb instead of the contraction"
        
        return "expand the contraction for a more formal tone"
