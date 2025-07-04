"""
Base Rule Class - Abstract interface for all writing rules using pure SpaCy morphological analysis.
All rules must inherit from this class and implement the required methods.
Provides comprehensive linguistic analysis utilities without hardcoded patterns.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set, Tuple, Union
import re
from collections import defaultdict


class BaseRule(ABC):
    """
    Abstract base class for all writing rules using pure SpaCy morphological analysis.
    Provides comprehensive linguistic utilities without hardcoded patterns.
    """
    
    def __init__(self) -> None:
        self.rule_type = self._get_rule_type()
        self.severity_levels = ['low', 'medium', 'high']
    
    @abstractmethod
    def _get_rule_type(self) -> str:
        """Return the rule type identifier (e.g., 'passive_voice', 'sentence_length')."""
        pass
    
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
            List of error dictionaries with structure:
            {
                'type': str,
                'message': str,
                'suggestions': List[str],
                'sentence': str,
                'sentence_index': int,
                'severity': str
            }
        """
        pass
    
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
                     **extra_data) -> Dict[str, Any]:
        """Create standardized error dictionary with proper serialization."""
        if severity not in self.severity_levels:
            severity = 'medium'
        
        error = {
            'type': self.rule_type,
            'message': str(message),
            'suggestions': [str(s) for s in suggestions],
            'sentence': str(sentence),
            'sentence_index': int(sentence_index),
            'severity': severity
        }
        
        # Add extra data with safe serialization
        for key, value in extra_data.items():
            try:
                error[str(key)] = self._make_serializable(value)
            except Exception as e:
                error[str(key)] = f"<serialization_error: {str(e)}>"
        
        return error 