"""
Product Versions Rule
Based on IBM Style Guide topic: "Product versions"
Enhanced with pure SpaCy morphological analysis for robust version pattern detection.
"""
from typing import List, Dict, Any, Optional
from .base_references_rule import BaseReferencesRule

class ProductVersionsRule(BaseReferencesRule):
    """
    Checks for incorrect formatting of product version numbers using advanced
    morphological analysis to detect version patterns and validate formatting.
    Replaces regex-based detection with SpaCy linguistic analysis.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize version-specific linguistic anchors
        self._initialize_version_anchors()
    
    def _initialize_version_anchors(self):
        """Initialize morphological patterns specific to version analysis."""
        
        # Version pattern morphological indicators
        self.version_morphological_patterns = {
            'version_prefixes': {
                'invalid_prefixes': ['V.', 'Ver.', 'Version', 'Release', 'Build'],
                'acceptable_forms': ['v', 'ver', 'version', 'release', 'build'],  # When used appropriately
                'morphological_context': ['NOUN+compound', 'X+NUM', 'SYM+NUM']
            },
            'number_patterns': {
                'valid_separators': ['.', '-'],
                'invalid_separators': ['_', ' ', ':'],
                'number_types': ['CARDINAL', 'NUM'],
                'wildcard_patterns': ['x', 'X', '*']
            },
            'version_structure': {
                'semantic_versioning': ['major.minor.patch'],
                'extended_versioning': ['major.minor.patch.build'],
                'date_versioning': ['YYYY.MM.DD'],
                'invalid_structures': ['.x', 'X.X', 'v.X']
            }
        }
        
        # Context patterns for version identification
        self.version_context_patterns = {
            'product_context': {
                'preceding_words': ['version', 'release', 'build', 'update'],
                'following_words': ['released', 'available', 'supports'],
                'dependency_patterns': ['nmod', 'nummod', 'appos']
            },
            'document_context': {
                'software_indicators': ['software', 'application', 'system', 'product'],
                'compatibility_indicators': ['compatible', 'supports', 'requires'],
                'temporal_indicators': ['latest', 'current', 'previous', 'new']
            }
        }

    def _get_rule_type(self) -> str:
        return 'references_product_versions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for product version formatting errors using comprehensive
        morphological and syntactic analysis.
        """
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = self._analyze_sentence_structure(sentence, nlp)
            if not doc:
                continue
            
            # Use the base class method for version pattern analysis
            version_errors = self._analyze_product_version_patterns(doc, sentence, i)
            errors.extend(version_errors)
            
            # Additional version-specific analysis
            additional_errors = self._analyze_version_specific_patterns(doc, sentence, i)
            errors.extend(additional_errors)

        return errors
    
    def _analyze_version_specific_patterns(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Analyze version-specific patterns that require correction.
        """
        errors = []
        
        if not doc:
            return errors
        
        # Detect invalid version prefixes
        prefix_errors = self._detect_invalid_version_prefixes(doc)
        for prefix_error in prefix_errors:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Invalid version prefix: '{prefix_error['text']}'. Use numbers only for versions.",
                suggestions=prefix_error['suggestions'],
                severity='medium',
                linguistic_analysis={
                    'prefix_error': prefix_error,
                    'morphological_pattern': prefix_error.get('morphological_pattern')
                }
            ))
        
        # Detect wildcard version patterns
        wildcard_errors = self._detect_wildcard_version_patterns(doc)
        for wildcard_error in wildcard_errors:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Avoid wildcard in version: '{wildcard_error['text']}'. Use specific version numbers.",
                suggestions=wildcard_error['suggestions'],
                severity='medium',
                linguistic_analysis={
                    'wildcard_error': wildcard_error,
                    'pattern_type': wildcard_error.get('pattern_type')
                }
            ))
        
        # Detect inconsistent version formatting
        format_errors = self._detect_version_format_inconsistencies(doc)
        for format_error in format_errors:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Inconsistent version format: '{format_error['text']}'. Use standard versioning.",
                suggestions=format_error['suggestions'],
                severity='low',
                linguistic_analysis={
                    'format_error': format_error,
                    'recommended_format': format_error.get('recommended_format')
                }
            ))
        
        return errors
    
    def _detect_invalid_version_prefixes(self, doc) -> List[Dict[str, Any]]:
        """
        Detect invalid version prefixes using morphological analysis.
        """
        invalid_prefixes = []
        
        if not doc:
            return invalid_prefixes
        
        try:
            for i, token in enumerate(doc):
                # Check for problematic version prefixes
                if self._is_invalid_version_prefix(token):
                    # Look for version numbers following the prefix
                    version_context = self._analyze_version_context(token, doc, i)
                    
                    if version_context['has_version_number']:
                        prefix_text = token.text
                        version_number = version_context['version_number']
                        
                        # Generate correction suggestions
                        suggestions = self._generate_prefix_correction_suggestions(prefix_text, version_number)
                        
                        invalid_prefixes.append({
                            'text': f"{prefix_text} {version_number}",
                            'prefix_token': token.text,
                            'version_number': version_number,
                            'suggestions': suggestions,
                            'morphological_pattern': f"{token.pos_}+{token.dep_}",
                            'morphological_features': self._get_morphological_features(token)
                        })
        
        except Exception:
            pass
        
        return invalid_prefixes
    
    def _detect_wildcard_version_patterns(self, doc) -> List[Dict[str, Any]]:
        """
        Detect wildcard patterns in version numbers using morphological analysis.
        """
        wildcard_patterns = []
        
        if not doc:
            return wildcard_patterns
        
        try:
            for token in doc:
                # Check for version-like tokens containing wildcards
                if self._contains_version_wildcard(token):
                    wildcard_analysis = self._analyze_wildcard_pattern(token, doc)
                    
                    if wildcard_analysis['is_problematic']:
                        suggestions = self._generate_wildcard_correction_suggestions(token.text)
                        
                        wildcard_patterns.append({
                            'text': token.text,
                            'pattern_type': wildcard_analysis['pattern_type'],
                            'wildcard_char': wildcard_analysis['wildcard_char'],
                            'suggestions': suggestions,
                            'morphological_features': self._get_morphological_features(token),
                            'context_analysis': wildcard_analysis.get('context')
                        })
        
        except Exception:
            pass
        
        return wildcard_patterns
    
    def _detect_version_format_inconsistencies(self, doc) -> List[Dict[str, Any]]:
        """
        Detect inconsistent version formatting patterns.
        """
        format_inconsistencies = []
        
        if not doc:
            return format_inconsistencies
        
        try:
            # Collect all version-like patterns in the document
            version_tokens = self._collect_version_tokens(doc)
            
            if len(version_tokens) > 1:
                # Analyze consistency across version patterns
                consistency_analysis = self._analyze_version_consistency(version_tokens)
                
                for inconsistency in consistency_analysis['inconsistencies']:
                    format_inconsistencies.append({
                        'text': inconsistency['text'],
                        'format_type': inconsistency['format_type'],
                        'expected_format': consistency_analysis['recommended_format'],
                        'suggestions': inconsistency['suggestions'],
                        'recommended_format': consistency_analysis['recommended_format']
                    })
        
        except Exception:
            pass
        
        return format_inconsistencies
    
    def _is_invalid_version_prefix(self, token) -> bool:
        """
        Check if token is an invalid version prefix using morphological analysis.
        """
        try:
            text = token.text.lower()
            
            # Check against known invalid prefixes
            invalid_prefixes = ['v.', 'ver.', 'version.', 'release.']
            
            if text in invalid_prefixes:
                return True
            
            # Check for uppercase variants
            if (token.text in ['V', 'VER', 'VERSION', 'RELEASE'] and 
                self._is_followed_by_punctuation_and_number(token)):
                return True
            
            return False
        
        except Exception:
            return False
    
    def _analyze_version_context(self, prefix_token, doc, prefix_index: int) -> Dict[str, Any]:
        """
        Analyze the context around a version prefix to identify version numbers.
        """
        try:
            context = {
                'has_version_number': False,
                'version_number': '',
                'confidence_score': 0.0
            }
            
            # Look for version numbers in the following tokens
            for i in range(prefix_index + 1, min(len(doc), prefix_index + 4)):
                token = doc[i]
                
                # Skip punctuation
                if token.is_punct:
                    continue
                
                # Check if this looks like a version number
                if self._is_version_number_token(token):
                    context['has_version_number'] = True
                    context['version_number'] = token.text
                    context['confidence_score'] = self._calculate_version_confidence(token)
                    break
            
            return context
        
        except Exception:
            return {'has_version_number': False, 'version_number': '', 'confidence_score': 0.0}
    
    def _contains_version_wildcard(self, token) -> bool:
        """
        Check if token contains version wildcard patterns.
        """
        try:
            text = token.text.lower()
            
            # Common wildcard patterns in versions
            wildcard_patterns = ['.x', 'x.', '.x.', 'x.x', '*.']
            
            return any(pattern in text for pattern in wildcard_patterns)
        
        except Exception:
            return False
    
    def _analyze_wildcard_pattern(self, token, doc) -> Dict[str, Any]:
        """
        Analyze wildcard patterns in version tokens.
        """
        try:
            text = token.text.lower()
            
            analysis = {
                'is_problematic': True,
                'pattern_type': 'unknown',
                'wildcard_char': '',
                'context': {}
            }
            
            # Identify wildcard character and pattern
            if '.x' in text:
                analysis['pattern_type'] = 'dot_x_wildcard'
                analysis['wildcard_char'] = 'x'
            elif 'x.' in text:
                analysis['pattern_type'] = 'x_dot_wildcard'
                analysis['wildcard_char'] = 'x'
            elif '*' in text:
                analysis['pattern_type'] = 'asterisk_wildcard'
                analysis['wildcard_char'] = '*'
            
            # Analyze surrounding context
            analysis['context'] = self._analyze_token_context(token, doc)
            
            return analysis
        
        except Exception:
            return {
                'is_problematic': False,
                'pattern_type': 'unknown',
                'wildcard_char': '',
                'context': {}
            }
    
    def _collect_version_tokens(self, doc) -> List[Dict[str, Any]]:
        """
        Collect all tokens that appear to be version numbers.
        """
        version_tokens = []
        
        try:
            for token in doc:
                if self._is_version_number_token(token):
                    version_analysis = self._analyze_version_token_structure(token)
                    
                    version_tokens.append({
                        'token': token,
                        'text': token.text,
                        'structure': version_analysis,
                        'morphological_features': self._get_morphological_features(token)
                    })
        
        except Exception:
            pass
        
        return version_tokens
    
    def _analyze_version_consistency(self, version_tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze consistency across multiple version tokens.
        """
        try:
            if not version_tokens:
                return {'inconsistencies': [], 'recommended_format': 'major.minor.patch'}
            
            # Analyze format patterns
            format_patterns = {}
            for version_token in version_tokens:
                pattern = version_token['structure']['format_pattern']
                if pattern not in format_patterns:
                    format_patterns[pattern] = []
                format_patterns[pattern].append(version_token)
            
            # Determine recommended format (most common or most standard)
            recommended_format = self._determine_recommended_format(format_patterns)
            
            # Find inconsistencies
            inconsistencies = []
            for pattern, tokens in format_patterns.items():
                if pattern != recommended_format:
                    for token_info in tokens:
                        inconsistencies.append({
                            'text': token_info['text'],
                            'format_type': pattern,
                            'suggestions': [f"Use consistent format: {recommended_format} (e.g., '2.1.0')"]
                        })
            
            return {
                'inconsistencies': inconsistencies,
                'recommended_format': recommended_format,
                'format_patterns': format_patterns
            }
        
        except Exception:
            return {'inconsistencies': [], 'recommended_format': 'major.minor.patch'}
    
    def _is_followed_by_punctuation_and_number(self, token) -> bool:
        """
        Check if token is followed by punctuation and a number.
        """
        try:
            doc = token.doc
            token_index = token.i
            
            # Check next few tokens for pattern like "V. 1.0"
            if token_index + 2 < len(doc):
                next_token = doc[token_index + 1]
                following_token = doc[token_index + 2]
                
                return (next_token.is_punct and 
                        (following_token.like_num or self._is_version_number_token(following_token)))
            
            return False
        
        except Exception:
            return False
    
    def _is_version_number_token(self, token) -> bool:
        """
        Check if token represents a version number using morphological analysis.
        """
        try:
            text = token.text
            
            # Basic patterns for version numbers
            import re
            
            # Semantic versioning pattern (e.g., "1.2.3")
            if re.match(r'^\d+\.\d+(\.\d+)*$', text):
                return True
            
            # Version with wildcards (problematic but still version-like)
            if re.match(r'^\d+\.\d*[xX*]\d*$', text):
                return True
            
            # Single or double numbers that might be versions in context
            if re.match(r'^\d+(\.\d+)?$', text) and self._is_in_version_context(token):
                return True
            
            return False
        
        except Exception:
            return False
    
    def _is_in_version_context(self, token) -> bool:
        """
        Check if token is in a version-related context.
        """
        try:
            # Look for version-related words nearby
            window = 3
            doc = token.doc
            start_idx = max(0, token.i - window)
            end_idx = min(len(doc), token.i + window + 1)
            
            version_keywords = ['version', 'release', 'build', 'update', 'v', 'ver']
            
            for i in range(start_idx, end_idx):
                if i != token.i:
                    nearby_token = doc[i]
                    if nearby_token.lemma_.lower() in version_keywords:
                        return True
            
            return False
        
        except Exception:
            return False
    
    def _analyze_version_token_structure(self, token) -> Dict[str, Any]:
        """
        Analyze the structure of a version token.
        """
        try:
            text = token.text
            
            # Determine format pattern
            if '.' in text:
                parts = text.split('.')
                if len(parts) == 3:
                    format_pattern = 'major.minor.patch'
                elif len(parts) == 2:
                    format_pattern = 'major.minor'
                else:
                    format_pattern = 'custom_dotted'
            else:
                format_pattern = 'single_number'
            
            return {
                'format_pattern': format_pattern,
                'components': text.split('.') if '.' in text else [text],
                'has_wildcards': 'x' in text.lower() or '*' in text
            }
        
        except Exception:
            return {
                'format_pattern': 'unknown',
                'components': [text] if hasattr(token, 'text') else [],
                'has_wildcards': False
            }
    
    def _determine_recommended_format(self, format_patterns: Dict[str, List]) -> str:
        """
        Determine the recommended format based on usage patterns.
        """
        # Preference order for version formats
        preferred_formats = [
            'major.minor.patch',  # Semantic versioning (preferred)
            'major.minor',        # Simple two-part versioning
            'custom_dotted',      # Other dotted formats
            'single_number'       # Single number versions
        ]
        
        for preferred in preferred_formats:
            if preferred in format_patterns:
                return preferred
        
        return 'major.minor.patch'  # Default recommendation
    
    def _generate_prefix_correction_suggestions(self, prefix: str, version_number: str) -> List[str]:
        """
        Generate correction suggestions for invalid version prefixes.
        """
        suggestions = []
        
        # Remove prefix and use number only
        suggestions.append(f"Use '{version_number}' instead of '{prefix} {version_number}'")
        
        # Alternative: proper product name context
        suggestions.append(f"Specify the product name: 'Product Name {version_number}'")
        
        return suggestions
    
    def _generate_wildcard_correction_suggestions(self, wildcard_version: str) -> List[str]:
        """
        Generate correction suggestions for wildcard versions.
        """
        suggestions = []
        
        # Replace wildcard with specific version
        if '.x' in wildcard_version.lower():
            specific_version = wildcard_version.lower().replace('.x', '.0')
            suggestions.append(f"Use specific version: '{specific_version}'")
        
        # General advice
        suggestions.append("Specify exact version numbers instead of wildcards")
        suggestions.append("Example: '2.1.0' instead of '2.1.x'")
        
        return suggestions
    
    def _calculate_version_confidence(self, token) -> float:
        """
        Calculate confidence that token represents a version number.
        """
        try:
            confidence = 0.5  # Base confidence
            
            # Increase confidence for standard patterns
            if self._is_version_number_token(token):
                confidence += 0.3
            
            # Increase confidence for version context
            if self._is_in_version_context(token):
                confidence += 0.2
            
            return min(confidence, 1.0)
        
        except Exception:
            return 0.5
    
    def _analyze_token_context(self, token, doc) -> Dict[str, Any]:
        """
        Analyze the morphological and syntactic context of a token.
        """
        try:
            context = {
                'preceding_words': [],
                'following_words': [],
                'dependency_context': token.dep_,
                'semantic_context': 'version'
            }
            
            # Analyze preceding and following tokens
            window = 2
            for i in range(max(0, token.i - window), min(len(doc), token.i + window + 1)):
                if i != token.i:
                    nearby_token = doc[i]
                    if i < token.i:
                        context['preceding_words'].append(nearby_token.text)
                    else:
                        context['following_words'].append(nearby_token.text)
            
            return context
        
        except Exception:
            return {
                'preceding_words': [],
                'following_words': [],
                'dependency_context': 'unknown',
                'semantic_context': 'unknown'
            }
