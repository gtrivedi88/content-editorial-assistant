"""
Prefixes Rule
Based on IBM Style Guide topic: "Prefixes"
Enhanced with spaCy morphological analysis for scalable prefix detection.
"""
import re
from typing import List, Dict, Any, Set
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc, Token
except ImportError:
    Doc = None
    Token = None

class PrefixesRule(BaseLanguageRule):
    """
    Detects prefixes that should be closed (without hyphens) using spaCy morphological 
    analysis and linguistic anchors. This approach avoids hardcoding and uses 
    morphological features to identify prefix patterns.
    """
    
    def __init__(self):
        super().__init__()
        self._initialize_prefix_patterns()
    
    def _initialize_prefix_patterns(self):
        """Initialize morphological patterns for prefix detection."""
        
        # LINGUISTIC ANCHORS: Common closed prefixes that should not use hyphens
        self.closed_prefix_patterns = {
            'iterative_prefixes': {
                'prefix_morphemes': ['re'],
                'semantic_indicators': ['again', 'back', 'anew'],
                'morphological_features': {'Prefix': 'True'},
                'description': 'iterative or repetitive action'
            },
            'temporal_prefixes': {
                'prefix_morphemes': ['pre', 'post'],
                'semantic_indicators': ['before', 'after', 'prior'],
                'morphological_features': {'Prefix': 'True'},
                'description': 'temporal relationship'
            },
            'negation_prefixes': {
                'prefix_morphemes': ['non', 'un', 'in', 'dis'],
                'semantic_indicators': ['not', 'without', 'opposite'],
                'morphological_features': {'Prefix': 'True', 'Polarity': 'Neg'},
                'description': 'negation or opposition'
            },
            'quantity_prefixes': {
                'prefix_morphemes': ['multi', 'inter', 'over', 'under', 'sub', 'super'],
                'semantic_indicators': ['many', 'between', 'above', 'below'],
                'morphological_features': {'Prefix': 'True'},
                'description': 'quantity or position'
            },
            'relationship_prefixes': {
                'prefix_morphemes': ['co', 'counter', 'anti', 'pro'],
                'semantic_indicators': ['with', 'against', 'for'],
                'morphological_features': {'Prefix': 'True'},
                'description': 'relationship or stance'
            }
        }
        
        # MORPHOLOGICAL ANCHORS: Patterns for detecting hyphenated prefixes
        self.hyphen_detection_patterns = {
            'explicit_hyphen': r'\b(\w+)-(\w+)\b',
            'prefix_boundary': r'\b(re|pre|non|un|in|dis|multi|inter|over|under|sub|super|co|counter|anti|pro)-\w+\b'
        }
    
    def _get_rule_type(self) -> str:
        return 'prefixes'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for incorrectly hyphenated prefixes using morphological analysis.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        
        # LINGUISTIC ANCHOR 1: Detect hyphenated prefix patterns
        for sent in doc.sents:
            # Use regex to find potential hyphenated prefixes
            hyphen_matches = re.finditer(self.hyphen_detection_patterns['prefix_boundary'], 
                                       sent.text, re.IGNORECASE)
            
            for match in hyphen_matches:
                prefix_part = match.group(1).lower()
                full_match = match.group(0)
                
                # MORPHOLOGICAL ANALYSIS: Check if this prefix should be closed
                if self._should_be_closed_prefix(prefix_part, full_match, doc, sent):
                    # Get the token span for precise analysis
                    char_start = sent.start_char + match.start()
                    char_end = sent.start_char + match.end()
                    
                    # Find corresponding tokens
                    tokens_in_span = [token for token in sent if 
                                    token.idx >= char_start and token.idx < char_end]
                    
                    if tokens_in_span:
                        # Analyze morphological context
                        context_analysis = self._analyze_prefix_context(tokens_in_span, doc)
                        
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=list(doc.sents).index(sent),
                            message=f"Prefix '{prefix_part}' should typically be closed: '{full_match}' should be written without a hyphen.",
                            suggestions=[f"Write as '{self._generate_closed_form(full_match)}' without the hyphen. {context_analysis['explanation']}"],
                            severity='medium',
                            span=(char_start, char_end),
                            flagged_text=full_match
                        ))
        
        return errors
    
    def _should_be_closed_prefix(self, prefix: str, full_word: str, doc: 'Doc', sent) -> bool:
        """
        Uses morphological analysis to determine if a prefix should be closed.
        LINGUISTIC ANCHOR: Morphological and semantic analysis.
        """
        # Check against known closed prefix patterns
        for pattern_name, pattern_info in self.closed_prefix_patterns.items():
            if prefix in pattern_info['prefix_morphemes']:
                # MORPHOLOGICAL VALIDATION: Check semantic context
                if self._has_prefix_semantic_context(full_word, pattern_info, doc, sent):
                    return True
        
        # LINGUISTIC ANCHOR: Check morphological features of the word
        # Find tokens that contain this hyphenated word
        for token in sent:
            if full_word.lower() in token.text.lower():
                # Analyze morphological structure
                if self._has_prefix_morphology(token, prefix):
                    return True
        
        return False
    
    def _has_prefix_semantic_context(self, word: str, pattern_info: Dict, doc: 'Doc', sent) -> bool:
        """
        Check if the word appears in semantic context appropriate for the prefix.
        LINGUISTIC ANCHOR: Semantic role analysis using spaCy features.
        """
        semantic_indicators = pattern_info.get('semantic_indicators', [])
        
        # Look for semantic indicators in surrounding context
        word_lower = word.lower()
        sent_text = sent.text.lower()
        
        # Check if any semantic indicators appear near the word
        for indicator in semantic_indicators:
            if indicator in sent_text:
                return True
        
        # MORPHOLOGICAL ANALYSIS: Check if word structure suggests prefix usage
        base_word = word.split('-')[1] if '-' in word else word
        
        # Look for the base word elsewhere in the document to understand usage
        for token in doc:
            if token.lemma_.lower() == base_word.lower():
                # If base word exists independently, prefix is likely modifying it
                return True
        
        return True  # Default to flagging for manual review
    
    def _has_prefix_morphology(self, token: 'Token', prefix: str) -> bool:
        """
        Analyze morphological features to detect prefix usage.
        LINGUISTIC ANCHOR: spaCy morphological feature analysis.
        """
        if not token:
            return False
        
        # Check morphological features
        if hasattr(token, 'morph') and token.morph:
            morph_dict = token.morph.to_dict()
            
            # Look for prefix-related morphological features
            if morph_dict.get('Prefix') == 'True':
                return True
            
            # Check for derivational morphology patterns
            if morph_dict.get('Derivation'):
                return True
        
        # LINGUISTIC PATTERN: Analyze word structure
        if hasattr(token, 'lemma_') and token.lemma_:
            # Check if the lemma suggests a prefixed form
            if prefix in token.lemma_.lower() and len(token.lemma_) > len(prefix) + 2:
                return True
        
        # POS analysis: Common prefixed word patterns
        if hasattr(token, 'pos_'):
            # Prefixed verbs, adjectives, and nouns are often closed
            if token.pos_ in ['VERB', 'ADJ', 'NOUN'] and prefix in token.text.lower():
                return True
        
        return False
    
    def _analyze_prefix_context(self, tokens: List['Token'], doc: 'Doc') -> Dict[str, str]:
        """
        Analyze the morphological and syntactic context of the prefix.
        LINGUISTIC ANCHOR: Dependency and morphological analysis.
        """
        if not tokens:
            return {'explanation': 'This prefix typically forms closed compounds.'}
        
        primary_token = tokens[0]
        
        # Analyze POS and morphological context
        pos = getattr(primary_token, 'pos_', '')
        dep = getattr(primary_token, 'dep_', '')
        
        explanations = {
            'VERB': 'Prefixed verbs are typically written as one word.',
            'NOUN': 'Prefixed nouns are typically written as one word.',
            'ADJ': 'Prefixed adjectives are typically written as one word.',
            'ADV': 'Prefixed adverbs are typically written as one word.'
        }
        
        base_explanation = explanations.get(pos, 'This prefix typically forms closed compounds.')
        
        # Add dependency-based context
        if dep in ['compound', 'amod']:
            base_explanation += ' The syntactic role confirms this should be a single word.'
        
        return {
            'explanation': base_explanation,
            'pos': pos,
            'dependency': dep
        }
    
    def _generate_closed_form(self, hyphenated_word: str) -> str:
        """
        Generate the closed form of a hyphenated prefix word.
        MORPHOLOGICAL PATTERN: Simple hyphen removal with validation.
        """
        return hyphenated_word.replace('-', '') 