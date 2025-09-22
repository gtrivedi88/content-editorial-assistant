"""
Contractions Rule
Based on IBM Style Guide topic: "Contractions"
Enhanced with universal spaCy morphological analysis for scalable detection.
"""
import re
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
        """
        Evidence-based analysis for contractions.
        Calculates nuanced evidence scores for each detected contraction using
        linguistic, structural, semantic, and feedback clues.
        """
        errors = []
        if not nlp:
            return errors
        
        doc = nlp(text)

        # Find all potential issues first
        potential_issues = self._find_potential_issues(doc, text)
        
        for potential_issue in potential_issues:
            # Calculate nuanced evidence score
            evidence_score = self._calculate_contraction_evidence(
                potential_issue, doc, text, context or {}
            )
            
            # Only create error if evidence suggests it's worth evaluating
            if evidence_score >= 0.1:  # Low threshold - let enhanced validation decide
                errors.append(self._create_error(
                    sentence=potential_issue['sentence'].text,
                    sentence_index=potential_issue['sentence_index'],
                    message=self._get_contextual_contraction_message(potential_issue, evidence_score),
                    suggestions=self._generate_smart_contraction_suggestions(potential_issue, evidence_score, context or {}),
                    severity=potential_issue.get('severity', 'low'),
                    text=text,
                    context=context,
                    evidence_score=evidence_score,  # Your nuanced assessment
                    span=potential_issue['span'],
                    flagged_text=potential_issue['flagged_text']
                ))
        
        return errors

    def _find_potential_issues(self, doc, text: str) -> List[Dict[str, Any]]:
        """Find all potential contraction issues in the document."""
        potential_issues = []
        
        # METHOD 1: spaCy morphological analysis
        for sent in doc.sents:
            sent_index = list(doc.sents).index(sent)
            for token in sent:
                # UNIVERSAL LINGUISTIC ANCHOR: Check if token has contraction characteristics
                if self._is_contraction_by_morphology(token):
                    contraction_info = self._analyze_contraction_morphology(token)
                    
                    potential_issues.append({
                        'type': 'morphological_contraction',
                        'token': token,
                        'contraction_info': contraction_info,
                        'sentence': sent,
                        'sentence_index': sent_index,
                        'span': (token.idx, token.idx + len(token.text)),
                        'flagged_text': token.text,
                        'severity': 'low'
                    })
        
        # METHOD 2: Comprehensive regex-based detection
        self._find_regex_contractions(text, doc, potential_issues)
        
        return potential_issues

    def _find_regex_contractions(self, text: str, doc, potential_issues: List[Dict[str, Any]]):
        """Find regex-based contractions and add to potential issues."""
        # COMPREHENSIVE REGEX PATTERN: Any word containing an apostrophe
        contraction_pattern = r"\b\w+'\w+\b"
        
        # Track already found contractions to avoid duplicates
        found_spans = set()
        for issue in potential_issues:
            if 'span' in issue and isinstance(issue['span'], tuple):
                found_spans.add(issue['span'])
        
        # Find all apostrophe-containing words in the text
        for match in re.finditer(contraction_pattern, text):
            match_start = match.start()
            match_end = match.end()
            match_span = (match_start, match_end)
            
            # Skip if already found by morphological analysis
            if match_span in found_spans:
                continue
            
            contraction_text = match.group()
            
            # Find which sentence this belongs to and get spaCy analysis
            sentence_info = self._find_sentence_for_span(match_start, match_end, doc)
            if not sentence_info:
                continue
            
            sent, sent_index = sentence_info
            
            # Get spaCy token analysis for this contraction if available
            token_analysis = self._find_token_for_span(match_start, match_end, sent)
            
            # Generate intelligent suggestions based on pattern analysis
            suggestion_info = self._analyze_regex_contraction(contraction_text, token_analysis)
            
            potential_issues.append({
                'type': 'regex_contraction',
                'contraction_text': contraction_text,
                'token_analysis': token_analysis,
                'suggestion_info': suggestion_info,
                'sentence': sent,
                'sentence_index': sent_index,
                'span': match_span,
                'flagged_text': contraction_text,
                'severity': 'low'
            })
            
            # Add to found spans to prevent further duplicates
            found_spans.add(match_span)
    
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
        
        # LINGUISTIC POLISH: Strong possessive filtering (EARLY EXIT)
        # Prevent possessive 's from being considered as contractions with near-100% certainty
        if "'s" in token.text.lower():
            # A token with 's that has dependency tag of "case" is always possessive, not contraction
            if hasattr(token, 'dep_') and token.dep_ == 'case':
                return False  # This is definitely a possessive, not a contraction
            
            # Additional possessive checks using part-of-speech analysis
            # Possessive 's tokens often have POS tag indicating possession
            if hasattr(token, 'tag_') and token.tag_ == 'POS':
                return False  # This is definitely a possessive marker, not a contraction
            
            # Check if the head word indicates possessive relationship
            if hasattr(token, 'head') and hasattr(token.head, 'pos_'):
                head_pos = token.head.pos_
                # If 's follows a noun, proper noun, or pronoun, it's likely possessive
                if head_pos in ['NOUN', 'PROPN', 'PRON'] and hasattr(token, 'dep_'):
                    # Common possessive dependency patterns
                    if token.dep_ in ['case', 'poss']:  # Direct possessive markers
                        return False  # Definitely possessive, not a contraction
        
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
        
        # More specific contraction detection with enhanced possessive distinction
        if "'s" in token_text or "'s" in token_text:
            # LINGUISTIC POLISH: Strong possessive detection using dependency parsing
            # A token with 's that has dependency tag of "case" is always possessive, not contraction
            if hasattr(token, 'dep_') and token.dep_ == 'case':
                return None  # This is definitely a possessive, don't flag as contraction
            
            # Additional possessive checks using part-of-speech analysis
            # Possessive 's tokens often have POS tag indicating possession
            if hasattr(token, 'tag_') and token.tag_ == 'POS':
                return None  # This is definitely a possessive marker, don't flag as contraction
            
            # Check if the head word indicates possessive relationship
            if hasattr(token, 'head') and hasattr(token.head, 'pos_'):
                head_pos = token.head.pos_
                # If 's follows a noun, proper noun, or pronoun, it's likely possessive
                if head_pos in ['NOUN', 'PROPN', 'PRON'] and hasattr(token, 'dep_'):
                    # Common possessive dependency patterns
                    if token.dep_ in ['case', 'poss']:  # Direct possessive markers
                        return None  # Definitely possessive, don't flag
            
            # Determine if remaining 's is "is" or possessive using existing logic
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
    
    def _analyze_contractions_by_regex_evidence_based(self, text: str, doc: 'Doc', errors: List[Dict[str, Any]], context: Dict[str, Any] = None):
        """
        Evidence-based regex contraction detection to catch any apostrophe-containing words
        that might be missed by morphological analysis with context-aware scoring.
        """
        # COMPREHENSIVE REGEX PATTERN: Any word containing an apostrophe
        contraction_pattern = r"\b\w+'\w+\b"
        
        # Track already found contractions to avoid duplicates
        found_spans = set()
        for error in errors:
            if 'span' in error and isinstance(error['span'], tuple):
                found_spans.add(error['span'])
        
        # Find all apostrophe-containing words in the text
        for match in re.finditer(contraction_pattern, text):
            match_start = match.start()
            match_end = match.end()
            match_span = (match_start, match_end)
            
            # Skip if already found by morphological analysis
            if match_span in found_spans:
                continue
            
            contraction_text = match.group()
            
            # Find which sentence this belongs to and get spaCy analysis
            sentence_info = self._find_sentence_for_span(match_start, match_end, doc)
            if not sentence_info:
                continue
            
            sent, sent_index = sentence_info
            
            # Get spaCy token analysis for this contraction if available
            token_analysis = self._find_token_for_span(match_start, match_end, sent)
            
            # Generate intelligent suggestions based on pattern analysis
            suggestion_info = self._analyze_regex_contraction(contraction_text, token_analysis)
            
            # Calculate evidence score for this regex-detected contraction
            evidence_score = self._calculate_regex_contraction_evidence(
                contraction_text, token_analysis, sent, text, context, suggestion_info
            )
            
            # Only create error if evidence suggests it's worth flagging
            if evidence_score >= 0.1:  # Low threshold - let enhanced validation decide
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=sent_index,
                    message=self._get_contextual_message_regex(contraction_text, suggestion_info, evidence_score),
                    suggestions=self._generate_smart_suggestions_regex(contraction_text, suggestion_info, evidence_score, context),
                    severity='low',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,  # Your nuanced assessment
                    span=match_span,
                    flagged_text=contraction_text
                ))
            
            # Add to found spans to prevent further duplicates
            found_spans.add(match_span)
    
    def _find_sentence_for_span(self, start: int, end: int, doc: 'Doc'):
        """Find which sentence contains the given character span."""
        for i, sent in enumerate(doc.sents):
            if sent.start_char <= start < sent.end_char:
                return sent, i
        return None
    
    def _find_token_for_span(self, start: int, end: int, sent):
        """Find the spaCy token that corresponds to the given span."""
        for token in sent:
            if token.idx <= start < token.idx + len(token.text):
                return token
        return None
    
    def _analyze_regex_contraction(self, contraction_text: str, token=None):
        """
        Analyze a regex-matched contraction and provide intelligent suggestions.
        Combines pattern matching with spaCy token analysis when available.
        """
        contraction_lower = contraction_text.lower()
        
        # PATTERN-BASED ANALYSIS: Common contraction patterns with enhanced possessive detection
        if "'s" in contraction_lower:
            # LINGUISTIC POLISH: Strong possessive detection using dependency parsing
            if token:
                # A token with 's that has dependency tag of "case" is always possessive, not contraction
                if hasattr(token, 'dep_') and token.dep_ == 'case':
                    return None  # This is definitely a possessive, don't flag as contraction
                
                # Additional possessive checks using part-of-speech analysis
                # Possessive 's tokens often have POS tag indicating possession
                if hasattr(token, 'tag_') and token.tag_ == 'POS':
                    return None  # This is definitely a possessive marker, don't flag as contraction
                
                # Check if the head word indicates possessive relationship
                if hasattr(token, 'head') and hasattr(token.head, 'pos_'):
                    head_pos = token.head.pos_
                    # If 's follows a noun, proper noun, or pronoun, it's likely possessive
                    if head_pos in ['NOUN', 'PROPN', 'PRON'] and hasattr(token, 'dep_'):
                        # Common possessive dependency patterns
                        if token.dep_ in ['case', 'poss']:  # Direct possessive markers
                            return None  # Definitely possessive, don't flag
            
            # After possessive filtering, check for verb contractions
            if token and hasattr(token, 'pos_') and token.pos_ == 'VERB':
                return {
                    'type': "auxiliary verb contraction ('s = is)",
                    'suggestion': "use 'is' instead of the contraction"
                }
            else:
                return {
                    'type': "contraction with 's",
                    'suggestion': "expand to 'is' or rephrase if possessive"
                }
        
        elif "'re" in contraction_lower:
            return {
                'type': "auxiliary verb contraction ('re = are)",
                'suggestion': "use 'are' instead of the contraction"
            }
        
        elif "'ve" in contraction_lower:
            return {
                'type': "auxiliary verb contraction ('ve = have)",
                'suggestion': "use 'have' instead of the contraction"
            }
        
        elif "'ll" in contraction_lower:
            return {
                'type': "auxiliary verb contraction ('ll = will)",
                'suggestion': "use 'will' instead of the contraction"
            }
        
        elif "'d" in contraction_lower:
            return {
                'type': "auxiliary verb contraction ('d = would/had)",
                'suggestion': "use 'would' or 'had' instead of the contraction"
            }
        
        elif "'t" in contraction_lower:
            if "n't" in contraction_lower:
                return {
                    'type': "negative contraction (n't = not)",
                    'suggestion': "use 'not' instead of the negative contraction"
                }
            else:
                return {
                    'type': "contraction with 't",
                    'suggestion': "expand the contraction"
                }
        
        elif "'m" in contraction_lower:
            return {
                'type': "auxiliary verb contraction ('m = am)",
                'suggestion': "use 'am' instead of the contraction"
            }
        
        # ADVANCED PATTERN ANALYSIS: Use spaCy token information if available
        elif token:
            if hasattr(token, 'lemma_') and token.lemma_:
                lemma = token.lemma_.lower()
                if lemma in ['be', 'have', 'will', 'would', 'can', 'could', 'should']:
                    return {
                        'type': f"auxiliary verb contraction ({lemma})",
                        'suggestion': f"use '{lemma}' instead of the contraction"
                    }
            
            if hasattr(token, 'pos_') and token.pos_ in ['PRON']:
                return {
                    'type': "pronominal contraction",
                    'suggestion': "use the full pronoun form"
                }
        
        # FALLBACK: Generic contraction handling
        return {
            'type': "contraction",
            'suggestion': "expand the contraction for a more formal tone"
        }

    # === EVIDENCE-BASED CALCULATION METHODS ===

    def _calculate_contraction_evidence(self, potential_issue: Dict[str, Any], doc, text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for contraction formality concerns.
        
        Higher scores indicate stronger evidence that the contraction should be flagged.
        Lower scores indicate acceptable usage in the given context.
        
        Args:
            potential_issue: Dictionary containing issue details
            doc: SpaCy document
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (acceptable) to 1.0 (should be flagged)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_contraction_evidence(potential_issue)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this contraction
        
        # === NARRATIVE/BLOG CONTENT CLUE (CONTROLLED ADJUSTMENT) ===
        # Detect narrative/blog writing style and reduce evidence, but not excessively
        if self._is_narrative_or_blog_content(text, context):
            evidence_score -= 0.3  # Moderate reduction (reduced from -0.5) - still flag some contractions in formal contexts
            # In narrative/blog content, contractions are more acceptable but formal technical guides
            # should still consider flagging them with lower confidence
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_contraction(evidence_score, potential_issue, doc)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_contraction(evidence_score, potential_issue, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_contraction(evidence_score, potential_issue, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_contraction(evidence_score, potential_issue, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    def _is_narrative_or_blog_content(self, text: str, context: Dict[str, Any]) -> bool:
        """
        Detect if content is narrative/blog style using enhanced ContextAnalyzer.
        
        Looks for blog/narrative indicators like:
        - Frequent first-person pronouns ("we", "our", "I")  
        - Contractions ("we're", "it's", "wasn't")
        - Rhetorical questions
        - Informal sentence structure
        - Blog-specific phrases ("Why we switched", "Our journey")
        
        Args:
            text: The document text to analyze
            context: Document context information
            
        Returns:
            bool: True if content appears to be narrative/blog style
        """
        if not text:
            return False
            
        # Import ContextAnalyzer to leverage enhanced narrative detection
        try:
            from validation.confidence.context_analyzer import ContextAnalyzer
            analyzer = ContextAnalyzer()
            
            # Use enhanced content type detection  
            content_result = analyzer.detect_content_type(text, context)
            
            # Check if identified as narrative with reasonable confidence
            if (content_result.content_type.value == 'narrative' and 
                content_result.confidence > 0.4):
                return True
            
            # Additional check for blog-specific patterns even if not classified as narrative
            # Look for strong blog indicators in the text
            text_lower = text.lower()
            blog_strong_indicators = [
                'why we', 'how we', 'what we', 'when we', 'we switched', 
                'we decided', 'our journey', 'our experience', 'our story',
                'we learned', 'we discovered', 'we realized'
            ]
            
            strong_indicator_count = sum(1 for indicator in blog_strong_indicators 
                                       if indicator in text_lower)
            
            if strong_indicator_count >= 2:  # Multiple strong blog indicators
                return True
                
            # Check for high contraction density (blog/informal characteristic)
            contractions = ["i'm", "we're", "we've", "it's", "that's", "wasn't", "weren't", "didn't"]
            contraction_count = sum(1 for contraction in contractions 
                                  if contraction in text_lower)
            
            # Check for high first-person pronoun density (blog characteristic)
            words = text_lower.split()
            if len(words) > 20:  # Only for substantial text
                first_person_count = sum(1 for word in words 
                                       if word in ['i', 'we', 'my', 'our', 'me', 'us'])
                first_person_ratio = first_person_count / len(words)
                
                # More than 3% first-person pronouns suggests blog/narrative
                if first_person_ratio > 0.03:
                    return True
                    
        except ImportError:
            # Fallback to simple pattern matching if ContextAnalyzer unavailable
            text_lower = text.lower()
            
            # Simple blog indicators
            simple_indicators = ['why we', 'we switched', 'our journey', 'we decided']
            if any(indicator in text_lower for indicator in simple_indicators):
                return True
        
        return False

    def _calculate_regex_contraction_evidence(self, contraction_text: str, token_analysis, sentence, text: str, context: dict, suggestion_info: dict) -> float:
        """
        Calculate evidence score for regex-detected contractions.
        
        Args:
            contraction_text: The contraction text found by regex
            token_analysis: SpaCy token analysis if available
            sentence: Sentence containing the contraction
            text: Full document text
            context: Document context
            suggestion_info: Analysis from _analyze_regex_contraction
            
        Returns:
            float: Evidence score from 0.0 (acceptable) to 1.0 (should be flagged)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_regex_contraction_evidence(contraction_text, suggestion_info)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this contraction
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_regex_contraction(evidence_score, contraction_text, token_analysis, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_contraction(evidence_score, None, context)  # Use same structural logic
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_regex_contraction(evidence_score, contraction_text, suggestion_info, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_regex_contraction(evidence_score, contraction_text, suggestion_info, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    def _get_base_contraction_evidence(self, potential_issue: Dict[str, Any]) -> float:
        """Get base evidence score based on contraction type and context."""
        
        issue_type = potential_issue.get('type', '')
        
        if issue_type == 'morphological_contraction':
            contraction_info = potential_issue['contraction_info']
            
            # Handle possessive filtering - if contraction_info is None, this was filtered out as possessive
            if contraction_info is None:
                return 0.0  # No evidence - this is a possessive, not a contraction
            
            token = potential_issue['token']
            contraction_type = contraction_info.get('type', '').lower()
            pattern = contraction_info.get('pattern', '')
        elif issue_type == 'regex_contraction':
            suggestion_info = potential_issue['suggestion_info']
            
            # Handle possessive filtering - if suggestion_info is None, this was filtered out as possessive
            if suggestion_info is None:
                return 0.0  # No evidence - this is a possessive, not a contraction
            
            contraction_text = potential_issue['contraction_text']
            contraction_type = suggestion_info.get('type', '').lower()
            pattern = 'regex_detected'
            # Use contraction_text directly instead of creating mock token
        else:
            return 0.7  # Higher default for unknown types (was 0.5)
        
        # === ENHANCED BASE EVIDENCE FOR FORMAL TECHNICAL WRITING ===
        # In formal technical guides, contractions should generally be flagged with higher confidence
        
        # Get the text to analyze (either from token or contraction_text)
        if issue_type == 'morphological_contraction':
            text_to_check = token.text.lower()
        else:
            text_to_check = contraction_text.lower()
        
        # === COMMON CONTRACTIONS - Higher base evidence ===
        # These are very common and should be flagged in formal writing
        if any(pattern in text_to_check for pattern in ["'s", "'re", "'ve", "'ll", "'d", "'m", "n't"]):
            # Possessive contractions often more problematic in formal writing
            if 'possessive' in contraction_type or "'s" in text_to_check:
                return 0.8  # High evidence - possessives often inappropriate
            
            # Common auxiliary contractions - should be flagged in formal technical guides
            elif "'re" in text_to_check or "'ve" in text_to_check or "'ll" in text_to_check:
                return 0.7  # High evidence for formal writing (increased from 0.6)
            
            # Negative contractions - even these should be considered in formal contexts
            elif "n't" in text_to_check or "'t" in text_to_check:
                return 0.6  # Moderate-high evidence (increased from 0.4)
            
            # Less formal contractions like 's (is), 'm (am)
            elif "'s" in text_to_check or "'m" in text_to_check:
                return 0.7  # Moderate-high evidence (increased from 0.5)
            
            # Ambiguous contractions like 'd (would/had)
            elif "'d" in text_to_check:
                return 0.8  # High evidence - ambiguous meaning (increased from 0.7)
            
            else:
                return 0.7  # Higher default for other contractions (increased from 0.5)
        
        # === CONTRACTION TYPE BASE EVIDENCE (Fallback) ===
        # Pronominal contractions (pronoun + auxiliary)  
        elif 'pronominal' in contraction_type:
            return 0.6  # Higher evidence (increased from 0.5)
        
        # Modal and copula contractions
        elif 'modal' in contraction_type or 'copula' in contraction_type:
            return 0.7  # Higher evidence (increased from 0.6)
        
        # Auxiliary verb contractions 
        elif 'auxiliary' in contraction_type:
            return 0.7  # Higher evidence (increased from 0.5)
        
        # Unknown contraction types - be more conservative
        else:
            return 0.6  # Higher default evidence (increased from 0.5)

    def _get_base_regex_contraction_evidence(self, contraction_text: str, suggestion_info: dict) -> float:
        """Get base evidence score for regex-detected contractions."""
        
        # Handle possessive filtering - if suggestion_info is None, this was filtered out as possessive
        if suggestion_info is None:
            return 0.0  # No evidence - this is a possessive, not a contraction
        
        contraction_type = suggestion_info.get('type', '').lower()
        contraction_lower = contraction_text.lower()
        
        # === ENHANCED PATTERN-BASED BASE EVIDENCE FOR FORMAL WRITING ===
        # Formal technical guides should generally flag contractions with higher confidence
        
        # Possessive patterns
        if 'possessive' in contraction_type:
            return 0.8  # High evidence - possessives often inappropriate
        
        # Negative contractions - increased for formal context
        elif "n't" in contraction_lower or ('negative' in contraction_type and "'t" in contraction_lower):
            return 0.6  # Moderate-high evidence (increased from 0.4) 
        
        # === COMMON CONTRACTIONS - Higher evidence for formal writing ===
        elif "'s" in contraction_lower:
            return 0.7  # Higher evidence (increased from 0.5) - could be 'is' or possessive
        elif "'re" in contraction_lower:
            return 0.7  # Higher evidence (increased from 0.6)
        elif "'ve" in contraction_lower:
            return 0.7  # Higher evidence (increased from 0.6) 
        elif "'ll" in contraction_lower:
            return 0.7  # Higher evidence (increased from 0.6)
        elif "'d" in contraction_lower:
            return 0.8  # Higher evidence (increased from 0.7) - ambiguous meaning
        elif "'m" in contraction_lower:
            return 0.7  # Higher evidence (increased from 0.5)
        
        # Fallback for unknown patterns
        else:
            return 0.6  # Higher default evidence (increased from 0.5)

    # === LINGUISTIC CLUES FOR CONTRACTIONS ===

    def _apply_linguistic_clues_contraction(self, evidence_score: float, potential_issue: Dict[str, Any], doc) -> float:
        """Apply linguistic analysis clues for contractions."""
        
        issue_type = potential_issue.get('type', '')
        
        if issue_type == 'morphological_contraction':
            token = potential_issue['token']
            contraction_info = potential_issue['contraction_info']
            sentence = potential_issue['sentence']
            
            # === CONTRACTION MORPHOLOGY ANALYSIS ===
            # Handle possessive filtering - if contraction_info is None, this was filtered out as possessive
            if contraction_info is None:
                return evidence_score  # Don't modify evidence, this is a possessive
            
            pattern = contraction_info.get('pattern', '')
            
            # High-certainty morphological patterns
            if pattern.startswith('specific_'):
                evidence_score += 0.1  # Specific patterns well-identified
            elif pattern.startswith('fallback_'):
                evidence_score -= 0.1  # Fallback patterns less certain
            
            # === POSITION AND CONTEXT ANALYSIS ===
            # Sentence-initial contractions often more acceptable
            if hasattr(token, 'i') and hasattr(sentence, 'start') and token.i == sentence.start:
                evidence_score -= 0.2  # Sentence-initial more acceptable
            
            # === SURROUNDING WORD ANALYSIS ===
            # Contractions near informal words
            if self._has_informal_context_words(token):
                evidence_score -= 0.2  # Informal context makes contractions more acceptable
            
            # Contractions near formal indicators
            if self._has_formal_context_words(token):
                evidence_score += 0.2  # Formal context makes contractions less acceptable
            
            # === MORPHOLOGICAL FEATURE ANALYSIS ===
            if hasattr(token, 'morph') and token.morph:
                morph_str = str(token.morph)
                
                # Negative contractions in questions more acceptable
                if 'Polarity=Neg' in morph_str and self._is_in_question_context(token):
                    evidence_score -= 0.2
                
                # Auxiliary contractions with strong subjects
                if 'VerbForm=Fin' in morph_str and self._has_strong_subject_nearby(token):
                    evidence_score += 0.1  # Clear auxiliary usage
            
            # === NAMED ENTITY RECOGNITION ===
            # Named entities may affect contraction acceptability
            if hasattr(token, 'ent_type_') and token.ent_type_:
                ent_type = token.ent_type_
                # Organizations, products, and places in contractions
                if ent_type in ['ORG', 'PRODUCT', 'GPE', 'FAC']:
                    evidence_score += 0.05  # Entity contractions less appropriate
                # Personal names in contractions 
                elif ent_type in ['PERSON']:
                    evidence_score += 0.02  # "John's" vs "John is"
                # Time and date entities often acceptable
                elif ent_type in ['DATE', 'TIME']:
                    evidence_score -= 0.02  # Temporal entities often contracted
            
            # Check surrounding tokens for entity context
            if hasattr(token, 'doc'):
                for nearby_token in token.doc[max(0, token.i-2):min(len(token.doc), token.i+3)]:
                    if hasattr(nearby_token, 'ent_type_') and nearby_token.ent_type_:
                        nearby_ent_type = nearby_token.ent_type_
                        # Contractions near technical entities
                        if nearby_ent_type in ['ORG', 'PRODUCT', 'GPE']:
                            evidence_score += 0.02  # Technical context suggests formality
                        # Contractions near money/quantities
                        elif nearby_ent_type in ['MONEY', 'QUANTITY', 'PERCENT']:
                            evidence_score += 0.03  # Financial context suggests formality
            
            # === PHONETIC FLOW ANALYSIS ===
            # Some contractions improve phonetic flow
            if self._improves_phonetic_flow(token):
                evidence_score -= 0.1
        
        elif issue_type == 'regex_contraction':
            contraction_text = potential_issue['contraction_text']
            token_analysis = potential_issue.get('token_analysis')
            sentence = potential_issue['sentence']
            
            # Apply regex-specific linguistic analysis
            evidence_score = self._apply_linguistic_clues_regex_contraction(evidence_score, contraction_text, token_analysis, sentence)
        
        return max(0.0, min(1.0, evidence_score))

    def _apply_linguistic_clues_regex_contraction(self, evidence_score: float, contraction_text: str, token_analysis, sentence) -> float:
        """Apply linguistic analysis clues for regex-detected contractions."""
        
        contraction_lower = contraction_text.lower()
        
        # === PATTERN-SPECIFIC LINGUISTIC ANALYSIS ===
        # Common patterns that are often acceptable
        if contraction_lower in ["let's", "it's", "that's", "here's", "there's"]:
            evidence_score -= 0.2  # Common, often acceptable contractions
        
        # Formal-sounding contractions that may be less acceptable
        elif contraction_lower in ["shan't", "mayn't", "ought'nt"]:
            evidence_score += 0.2  # Archaic/formal contractions often inappropriate
        
        # === TOKEN ANALYSIS INTEGRATION ===
        if token_analysis:
            # Use spaCy analysis when available
            if hasattr(token_analysis, 'pos_') and token_analysis.pos_ == 'VERB':
                evidence_score += 0.1  # Verb contractions in formal writing
            elif hasattr(token_analysis, 'dep_') and token_analysis.dep_ in ['aux', 'cop']:
                evidence_score += 0.1  # Auxiliary contractions
        
        # === CONTEXT POSITION ANALYSIS ===
        # Sentence position affects acceptability
        if sentence and contraction_text in sentence.text[:20]:  # First 20 characters
            evidence_score -= 0.1  # Beginning of sentence more acceptable
        
        return evidence_score

    def _apply_structural_clues_contraction(self, evidence_score: float, potential_issue: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Apply document structure-based clues for contraction analysis."""
        
        if not context:
            return evidence_score
        
        block_type = context.get('block_type', 'paragraph')
        
        # === FORMAL WRITING CONTEXTS ===
        # Academic and formal contexts expect no contractions
        if block_type in ['heading', 'title']:
            evidence_score += 0.3  # Headings should be formal
        elif block_type == 'paragraph':
            evidence_score += 0.1  # Body text generally more formal
        
        # === TECHNICAL CONTEXTS ===
        # Technical documentation may use contractions for readability
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.3  # Code comments often informal
        elif block_type == 'inline_code':
            evidence_score -= 0.2  # Inline technical content more flexible
        
        # === LISTS AND PROCEDURES ===
        # Instructions and lists often use contractions for brevity
        if block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.2  # List items often abbreviated/informal
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.1  # Tables may use contractions for space
        
        # === ADMONITIONS ===
        # Notes and tips often use conversational tone
        if block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'TIP', 'HINT']:
                evidence_score -= 0.3  # Notes/tips often conversational
            elif admonition_type in ['WARNING', 'CAUTION']:
                evidence_score -= 0.1  # Warnings may be conversational
            elif admonition_type in ['IMPORTANT', 'ATTENTION']:
                evidence_score += 0.1  # Important notices more formal
        
        # === QUOTES AND EXAMPLES ===
        # Quoted material may preserve original contractions
        if block_type in ['block_quote', 'citation']:
            evidence_score -= 0.4  # Quotes preserve original style
        elif block_type in ['example', 'sample']:
            evidence_score -= 0.2  # Examples may be conversational
        
        return max(0.0, min(1.0, evidence_score))

    def _apply_semantic_clues_contraction(self, evidence_score: float, potential_issue: Dict[str, Any], text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for contraction analysis."""
        
        if not context:
            return evidence_score
        
        content_type = context.get('content_type', 'general')
        
        # === FALLBACK TECHNICAL CONTEXT DETECTION ===
        # If no explicit content_type but format suggests formal technical documentation
        if content_type == 'general':
            format_hint = context.get('format', '').lower()
            block_type = context.get('block_type', '').lower()
            
            # AsciiDoc files are typically formal technical documentation
            if format_hint in ['asciidoc', 'adoc']:
                content_type = 'technical'
                
            # Formal block types suggest technical documentation  
            elif block_type in ['procedure_step', 'code_block', 'literal_block', 'table_cell']:
                content_type = 'technical'
        
        # === ENHANCED CONTENT TYPE ANALYSIS FOR FORMAL WRITING ===
        # CRITICAL: For formal technical guides, contractions should generally be flagged with HIGH confidence
        # FIXED: Formal contexts should INCREASE evidence scores, not decrease them
        if content_type == 'technical':
            evidence_score += 0.3  # Technical docs should flag contractions - formal writing expected (ensure all pass 0.35 threshold)
        elif content_type == 'api':
            evidence_score += 0.3  # API docs must be formal and precise - high confidence for contractions
        elif content_type == 'academic':
            evidence_score += 0.3  # Academic writing expects formal language (unchanged)
        elif content_type == 'legal':
            evidence_score += 0.4  # Legal writing demands precision and formality (unchanged)
        elif content_type == 'marketing':
            evidence_score -= 0.4  # Marketing uses conversational tone (unchanged)
        elif content_type == 'narrative':
            evidence_score -= 0.3  # Storytelling often uses contractions (unchanged)
        elif content_type == 'procedural':
            evidence_score += 0.1  # Procedures should be clear and formal - flag contractions
        
        # === ENHANCED DOMAIN-SPECIFIC PATTERNS ===
        domain = context.get('domain', 'general')
        if domain in ['software', 'engineering', 'devops']:
            evidence_score += 0.1  # Technical domains should use formal language - flag contractions
        elif domain in ['documentation', 'tutorial']:
            evidence_score += 0.1  # Documentation should be formal and clear - flag contractions  
        elif domain in ['academic', 'research', 'scientific']:
            evidence_score += 0.2  # Academic domains expect formality (unchanged)
        elif domain in ['legal', 'compliance', 'regulatory']:
            evidence_score += 0.3  # Legal domains demand precision (unchanged)
        
        # === ENHANCED AUDIENCE CONSIDERATIONS ===
        audience = context.get('audience', 'general')
        if audience in ['developer', 'technical', 'expert']:
            evidence_score += 0.1  # Technical audiences get professional, formal documentation - flag contractions
        elif audience in ['academic', 'research']:
            evidence_score += 0.2  # Academic audiences expect formal language (unchanged)
        elif audience in ['beginner', 'general', 'consumer']:
            evidence_score -= 0.2  # General audiences benefit from conversational tone (slightly less reduction)
        elif audience in ['professional', 'business']:
            evidence_score += 0.1  # Professional contexts more formal (unchanged)
        
        # === WRITING STYLE INDICATORS ===
        # Analyze the overall document tone  
        if self._has_conversational_tone_indicators(text):
            evidence_score -= 0.1  # Reduced from -0.2 - even conversational tech docs can flag contractions
        
        if self._has_formal_tone_indicators(text):
            evidence_score += 0.2  # Formal documents avoid contractions (unchanged)
        
        # === CONTRACTION TYPE IN CONTEXT ===
        issue_type = potential_issue.get('type', '')
        if issue_type == 'morphological_contraction':
            contraction_info = potential_issue['contraction_info']
            # Handle possessive filtering
            if contraction_info is None:
                return evidence_score  # Don't modify evidence, this is a possessive
            contraction_type = contraction_info.get('type', '').lower()
        elif issue_type == 'regex_contraction':
            suggestion_info = potential_issue['suggestion_info']
            # Handle possessive filtering
            if suggestion_info is None:
                return evidence_score  # Don't modify evidence, this is a possessive
            contraction_type = suggestion_info.get('type', '').lower()
        else:
            contraction_type = ''
        
        # Possessive contractions particularly problematic in formal writing
        if 'possessive' in contraction_type and content_type in ['academic', 'legal']:
            evidence_score += 0.2  # Possessives especially problematic in formal contexts
        
        # Negative contractions often acceptable even in formal contexts
        if 'negative' in contraction_type and content_type not in ['legal']:
            evidence_score -= 0.1  # Negative contractions more broadly acceptable
        
        # === BUSINESS COMMUNICATION CONTEXT ===
        # Business communications balance professionalism with relationship-building
        if self._is_business_communication_context(text, context):
            # Contractions can help build rapport in business contexts
            evidence_score -= 0.2  # Business contexts often accept contractions for warmth
            
            # But certain contractions still problematic in business
            if 'possessive' in contraction_type:
                evidence_score += 0.1  # Possessive contractions still formal issue
        
        return max(0.0, min(1.0, evidence_score))

    def _apply_semantic_clues_regex_contraction(self, evidence_score: float, contraction_text: str, suggestion_info: dict, text: str, context: dict) -> float:
        """Apply semantic clues for regex-detected contractions."""
        
        if not context:
            return evidence_score
        
        # Handle possessive filtering
        if suggestion_info is None:
            return evidence_score  # Don't modify evidence, this is a possessive
        
        content_type = context.get('content_type', 'general')
        contraction_type = suggestion_info.get('type', '').lower()
        
        # === CONTENT TYPE ANALYSIS ===
        # Different content types have different contraction tolerance
        if content_type == 'technical':
            evidence_score -= 0.2  # Technical writing often conversational for clarity
        elif content_type == 'api':
            evidence_score -= 0.3  # API docs often use conversational tone
        elif content_type == 'academic':
            evidence_score += 0.3  # Academic writing expects formal language
        elif content_type == 'legal':
            evidence_score += 0.4  # Legal writing demands precision and formality
        elif content_type == 'marketing':
            evidence_score -= 0.4  # Marketing uses conversational tone
        elif content_type == 'narrative':
            evidence_score -= 0.3  # Storytelling often uses contractions
        elif content_type == 'procedural':
            evidence_score -= 0.2  # Instructions often use contractions for clarity
        
        # === DOMAIN-SPECIFIC PATTERNS ===
        domain = context.get('domain', 'general')
        if domain in ['software', 'engineering', 'devops']:
            evidence_score -= 0.2  # Technical domains often informal for readability
        elif domain in ['documentation', 'tutorial']:
            evidence_score -= 0.2  # Educational content often conversational
        elif domain in ['academic', 'research', 'scientific']:
            evidence_score += 0.2  # Academic domains expect formality
        elif domain in ['legal', 'compliance', 'regulatory']:
            evidence_score += 0.3  # Legal domains demand precision
        
        # === AUDIENCE CONSIDERATIONS ===
        audience = context.get('audience', 'general')
        if audience in ['developer', 'technical', 'expert']:
            evidence_score -= 0.2  # Technical audiences expect practical communication
        elif audience in ['academic', 'research']:
            evidence_score += 0.2  # Academic audiences expect formal language
        elif audience in ['beginner', 'general', 'consumer']:
            evidence_score -= 0.3  # General audiences benefit from conversational tone
        elif audience in ['professional', 'business']:
            evidence_score += 0.1  # Professional contexts more formal
        
        # === SPECIFIC PATTERN ANALYSIS ===
        contraction_lower = contraction_text.lower()
        
        # Common conversational contractions
        if contraction_lower in ["let's", "it's", "that's", "what's", "how's"]:
            if content_type in ['marketing', 'narrative', 'tutorial']:
                evidence_score -= 0.2  # Very appropriate in conversational contexts
        
        # Formal-sounding contractions
        elif contraction_lower in ["shan't", "won't", "can't"]:
            if content_type in ['academic', 'legal']:
                evidence_score += 0.1  # Even formal contractions problematic in academic/legal
        
        # Possessive contractions particularly problematic in formal writing
        if 'possessive' in contraction_type and content_type in ['academic', 'legal']:
            evidence_score += 0.2  # Possessives especially problematic in formal contexts
        
        # Negative contractions often acceptable even in formal contexts
        if 'negative' in contraction_type and content_type not in ['legal']:
            evidence_score -= 0.1  # Negative contractions more broadly acceptable
        
        return max(0.0, min(1.0, evidence_score))

    def _apply_feedback_clues_contraction(self, evidence_score: float, potential_issue: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Apply feedback patterns for contraction analysis."""
        
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns('contractions')
        
        # === CONTRACTION-SPECIFIC FEEDBACK ===
        issue_type = potential_issue.get('type', '')
        
        if issue_type == 'morphological_contraction':
            token = potential_issue['token']
            contraction_info = potential_issue['contraction_info']
            # Handle possessive filtering
            if contraction_info is None:
                return evidence_score  # Don't modify evidence, this is a possessive
            contraction_text = token.text.lower() if token else ''
            contraction_type = contraction_info.get('type', '').lower()
        elif issue_type == 'regex_contraction':
            contraction_text = potential_issue['contraction_text'].lower()
            suggestion_info = potential_issue['suggestion_info']
            # Handle possessive filtering
            if suggestion_info is None:
                return evidence_score  # Don't modify evidence, this is a possessive
            contraction_type = suggestion_info.get('type', '').lower()
        else:
            contraction_text = ''
            contraction_type = ''
        
        # Check if this specific contraction is commonly accepted
        accepted_contractions = feedback_patterns.get('accepted_contractions', set())
        if contraction_text in accepted_contractions:
            evidence_score -= 0.3  # Users consistently accept this contraction
        
        flagged_contractions = feedback_patterns.get('flagged_contractions', set())
        if contraction_text in flagged_contractions:
            evidence_score += 0.3  # Users consistently flag this contraction
        
        # === CONTRACTION TYPE FEEDBACK ===
        type_patterns = feedback_patterns.get('contraction_type_patterns', {})
        
        # Check feedback for this type of contraction
        if 'possessive' in contraction_type:
            possessive_acceptance = type_patterns.get('possessive_acceptance_rate', 0.3)
            if possessive_acceptance > 0.7:
                evidence_score -= 0.2  # High acceptance rate
            elif possessive_acceptance < 0.3:
                evidence_score += 0.2  # Low acceptance rate
        
        elif 'negative' in contraction_type:
            negative_acceptance = type_patterns.get('negative_acceptance_rate', 0.6)
            if negative_acceptance > 0.7:
                evidence_score -= 0.2
            elif negative_acceptance < 0.4:
                evidence_score += 0.1
        
        elif 'auxiliary' in contraction_type:
            auxiliary_acceptance = type_patterns.get('auxiliary_acceptance_rate', 0.5)
            if auxiliary_acceptance > 0.7:
                evidence_score -= 0.2
            elif auxiliary_acceptance < 0.3:
                evidence_score += 0.2
        
        # === CONTEXT-SPECIFIC FEEDBACK ===
        if context:
            content_type = context.get('content_type', 'general')
            context_patterns = feedback_patterns.get(f'{content_type}_contraction_patterns', {})
            
            if contraction_text in context_patterns.get('acceptable', set()):
                evidence_score -= 0.2
            elif contraction_text in context_patterns.get('problematic', set()):
                evidence_score += 0.2
        
        # === FREQUENCY-BASED FEEDBACK ===
        contraction_frequency = feedback_patterns.get('contraction_frequencies', {}).get(contraction_text, 0)
        if contraction_frequency > 50:  # Frequently seen contraction
            acceptance_rate = feedback_patterns.get('contraction_acceptance_rates', {}).get(contraction_text, 0.5)
            if acceptance_rate > 0.7:
                evidence_score -= 0.2  # Frequently accepted
            elif acceptance_rate < 0.3:
                evidence_score += 0.2  # Frequently rejected
        
        return max(0.0, min(1.0, evidence_score))

    def _apply_feedback_clues_regex_contraction(self, evidence_score: float, contraction_text: str, suggestion_info: dict, context: dict) -> float:
        """Apply feedback patterns for regex-detected contractions."""
        
        # Handle possessive filtering
        if suggestion_info is None:
            return evidence_score  # Don't modify evidence, this is a possessive
        
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns('contractions')
        
        contraction_text_lower = contraction_text.lower()
        contraction_type = suggestion_info.get('type', '').lower()
        
        # Check if this specific contraction is commonly accepted
        accepted_contractions = feedback_patterns.get('accepted_contractions', set())
        if contraction_text_lower in accepted_contractions:
            evidence_score -= 0.3  # Users consistently accept this contraction
        
        flagged_contractions = feedback_patterns.get('flagged_contractions', set())
        if contraction_text_lower in flagged_contractions:
            evidence_score += 0.3  # Users consistently flag this contraction
        
        # === CONTRACTION TYPE FEEDBACK ===
        type_patterns = feedback_patterns.get('contraction_type_patterns', {})
        
        if 'possessive' in contraction_type:
            possessive_acceptance = type_patterns.get('possessive_acceptance_rate', 0.3)
            if possessive_acceptance > 0.7:
                evidence_score -= 0.2
            elif possessive_acceptance < 0.3:
                evidence_score += 0.2
        elif 'negative' in contraction_type:
            negative_acceptance = type_patterns.get('negative_acceptance_rate', 0.6)
            if negative_acceptance > 0.7:
                evidence_score -= 0.2
            elif negative_acceptance < 0.4:
                evidence_score += 0.1
        elif 'auxiliary' in contraction_type:
            auxiliary_acceptance = type_patterns.get('auxiliary_acceptance_rate', 0.5)
            if auxiliary_acceptance > 0.7:
                evidence_score -= 0.2
            elif auxiliary_acceptance < 0.3:
                evidence_score += 0.2
        
        # === CONTEXT-SPECIFIC FEEDBACK ===
        if context:
            content_type = context.get('content_type', 'general')
            context_patterns = feedback_patterns.get(f'{content_type}_contraction_patterns', {})
            
            if contraction_text_lower in context_patterns.get('acceptable', set()):
                evidence_score -= 0.2
            elif contraction_text_lower in context_patterns.get('problematic', set()):
                evidence_score += 0.2
        
        return max(0.0, min(1.0, evidence_score))

    # === HELPER METHODS ===

    def _has_informal_context_words(self, token) -> bool:
        """Check if contraction is near informal indicators."""
        if not token or not hasattr(token, 'doc'):
            return False
        
        informal_indicators = {
            'hey', 'ok', 'okay', 'yeah', 'yep', 'nope', 'wow', 'cool', 'awesome',
            'basically', 'just', 'really', 'pretty', 'kinda', 'sorta', 'gonna'
        }
        
        # Check surrounding tokens (±5 positions)
        start_idx = max(0, token.i - 5)
        end_idx = min(len(token.doc), token.i + 6)
        
        for i in range(start_idx, end_idx):
            if token.doc[i].text.lower() in informal_indicators:
                return True
        
        return False

    def _has_formal_context_words(self, token) -> bool:
        """Check if contraction is near formal indicators."""
        if not token or not hasattr(token, 'doc'):
            return False
        
        formal_indicators = {
            'therefore', 'however', 'furthermore', 'moreover', 'consequently',
            'nevertheless', 'accordingly', 'subsequently', 'specifically',
            'particularly', 'respectively', 'aforementioned', 'aforedescribed'
        }
        
        # Check surrounding tokens (±5 positions)
        start_idx = max(0, token.i - 5)
        end_idx = min(len(token.doc), token.i + 6)
        
        for i in range(start_idx, end_idx):
            if token.doc[i].text.lower() in formal_indicators:
                return True
        
        return False

    def _is_in_question_context(self, token) -> bool:
        """Check if contraction is in a question context."""
        if not token or not hasattr(token, 'sent'):
            return False
        
        sentence_text = token.sent.text
        return sentence_text.strip().endswith('?') or sentence_text.lower().startswith(('what', 'how', 'when', 'where', 'why', 'who', 'which'))

    def _has_strong_subject_nearby(self, token) -> bool:
        """Check if contraction has a clear, strong subject nearby."""
        if not token or not hasattr(token, 'head'):
            return False
        
        # Look for subject dependencies
        if hasattr(token, 'children'):
            for child in token.children:
                if child.dep_ in ['nsubj', 'nsubjpass'] and child.pos_ in ['NOUN', 'PROPN', 'PRON']:
                    return True
        
        # Look at the head's children
        if hasattr(token.head, 'children'):
            for child in token.head.children:
                if child.dep_ in ['nsubj', 'nsubjpass'] and child.pos_ in ['NOUN', 'PROPN']:
                    return True
        
        return False

    def _improves_phonetic_flow(self, token) -> bool:
        """Check if contraction improves phonetic flow."""
        if not token:
            return False
        
        # Some contractions that commonly improve flow
        flow_improving_contractions = {
            "it's", "that's", "what's", "let's", "here's", "there's"
        }
        
        return token.text.lower() in flow_improving_contractions

    def _has_conversational_tone_indicators(self, text: str) -> bool:
        """Check if text has indicators of conversational tone."""
        conversational_indicators = [
            'let me', 'you can', 'you should', 'you might', 'you may',
            'we recommend', 'we suggest', 'simply', 'just', 'easy',
            'quick', 'tip:', 'note:', 'remember', 'keep in mind'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in conversational_indicators)

    def _has_formal_tone_indicators(self, text: str) -> bool:
        """Check if text has indicators of formal tone."""
        formal_indicators = [
            'pursuant to', 'in accordance with', 'hereby', 'whereas',
            'therefore', 'consequently', 'furthermore', 'moreover',
            'notwithstanding', 'heretofore', 'shall be', 'must be'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in formal_indicators)

    def _is_business_communication_context(self, text: str, context: dict) -> bool:
        """
        Detect if content is business communication documentation.
        
        Business communications often use contractions for relationship-building
        while maintaining professionalism, making contraction usage context-dependent.
        
        Args:
            text: Document text
            context: Document context
            
        Returns:
            bool: True if business communication context detected
        """
        business_indicators = {
            'customer', 'client', 'stakeholder', 'partner', 'vendor',
            'meeting', 'presentation', 'proposal', 'agreement', 'contract',
            'team', 'collaboration', 'communication', 'relationship',
            'sales', 'marketing', 'support', 'service', 'solution'
        }
        
        text_lower = text.lower()
        domain = context.get('domain', '')
        content_type = context.get('content_type', '')
        audience = context.get('audience', '')
        
        # Direct text indicators
        business_score = sum(1 for indicator in business_indicators if indicator in text_lower)
        
        # Context-based indicators
        if domain in {'business', 'sales', 'marketing', 'corporate', 'enterprise'}:
            business_score += 2
        
        if content_type in {'communication', 'correspondence', 'proposal', 'presentation'}:
            business_score += 2
            
        if audience in {'customer', 'client', 'stakeholder', 'business', 'executive'}:
            business_score += 2
        
        # Check for business communication patterns
        business_patterns = [
            'we recommend', 'our team', 'your business', 'our solution',
            'customer experience', 'business needs', 'partnership',
            'collaboration', 'customer success', 'business value'
        ]
        
        pattern_matches = sum(1 for pattern in business_patterns if pattern in text_lower)
        business_score += pattern_matches
        
        # Threshold for business context detection
        return business_score >= 3

    # === HELPER METHODS FOR SMART MESSAGING ===

    def _get_contextual_contraction_message(self, potential_issue: Dict[str, Any], evidence_score: float) -> str:
        """Generate context-aware error messages for contraction patterns."""
        issue_type = potential_issue.get('type', '')
        
        if issue_type == 'morphological_contraction':
            token = potential_issue['token']
            contraction_info = potential_issue['contraction_info']
            return self._get_contextual_message(token, contraction_info, evidence_score)
        elif issue_type == 'regex_contraction':
            contraction_text = potential_issue['contraction_text']
            suggestion_info = potential_issue['suggestion_info']
            return self._get_contextual_message_regex(contraction_text, suggestion_info, evidence_score)
        else:
            return "Contraction detected."

    def _generate_smart_contraction_suggestions(self, potential_issue: Dict[str, Any], evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for contraction patterns."""
        issue_type = potential_issue.get('type', '')
        
        if issue_type == 'morphological_contraction':
            token = potential_issue['token']
            contraction_info = potential_issue['contraction_info']
            return self._generate_smart_suggestions(token, contraction_info, evidence_score, context)
        elif issue_type == 'regex_contraction':
            contraction_text = potential_issue['contraction_text']
            suggestion_info = potential_issue['suggestion_info']
            return self._generate_smart_suggestions_regex(contraction_text, suggestion_info, evidence_score, context)
        else:
            return ["Consider expanding the contraction for a more formal tone."]

    def _get_contextual_message(self, token, contraction_info: dict, evidence_score: float) -> str:
        """Generate context-aware error messages for contractions."""
        
        # Handle possessive filtering
        if contraction_info is None:
            return f"Possessive form: '{token.text}' is correctly used."
        
        contraction_type = contraction_info.get('type', 'contraction')
        
        if evidence_score > 0.8:
            return f"Formal writing: Avoid contraction '{token.text}' ({contraction_type}). Expand for professional tone."
        elif evidence_score > 0.3:
            return f"Technical guide style: Consider expanding '{token.text}' ({contraction_type}) for formal documentation."
        elif evidence_score > 0.1:
            return f"Contraction usage: '{token.text}' ({contraction_type}). Consider expanding for formal technical writing."
        else:
            return f"Contraction noted: '{token.text}' ({contraction_type}). May be acceptable depending on context."

    def _get_contextual_message_regex(self, contraction_text: str, suggestion_info: dict, evidence_score: float) -> str:
        """Generate context-aware error messages for regex-detected contractions."""
        
        # Handle possessive filtering
        if suggestion_info is None:
            return f"Possessive form: '{contraction_text}' is correctly used."
        
        contraction_type = suggestion_info.get('type', 'contraction')
        
        if evidence_score > 0.8:
            return f"Formal writing: Avoid contraction '{contraction_text}' ({contraction_type}). Expand for professional tone."
        elif evidence_score > 0.3:
            return f"Technical guide style: Consider expanding '{contraction_text}' ({contraction_type}) for formal documentation."
        elif evidence_score > 0.1:
            return f"Contraction usage: '{contraction_text}' ({contraction_type}). Consider expanding for formal technical writing."
        else:
            return f"Contraction noted: '{contraction_text}' ({contraction_type}). May be acceptable depending on context."

    def _generate_smart_suggestions(self, token, contraction_info: dict, evidence_score: float, context: dict) -> List[str]:
        """Generate context-aware suggestions for contractions."""
        
        # Handle possessive filtering
        if contraction_info is None:
            return [f"'{token.text}' is correctly used as a possessive form."]
        
        suggestions = []
        base_suggestion = contraction_info.get('suggestion', 'expand the contraction')
        
        # Base suggestions based on evidence strength
        if evidence_score > 0.7:
            suggestions.append(f"Expand for formal tone: {base_suggestion}.")
        else:
            suggestions.append(f"Consider expansion: {base_suggestion}.")
        
        # Context-specific advice
        if context:
            content_type = context.get('content_type', 'general')
            
            if content_type in ['academic', 'legal']:
                suggestions.append("Formal writing typically avoids contractions entirely.")
            elif content_type in ['marketing', 'narrative']:
                suggestions.append("Contractions may be acceptable for conversational tone.")
            elif content_type == 'technical':
                suggestions.append("Technical documentation may use contractions for readability.")
        
        # Evidence-based advice
        if evidence_score < 0.3:
            suggestions.append("This contraction may be acceptable in your writing context.")
        elif evidence_score > 0.8:
            suggestions.append("Strong recommendation to expand this contraction.")
        
        return suggestions

    def _generate_smart_suggestions_regex(self, contraction_text: str, suggestion_info: dict, evidence_score: float, context: dict) -> List[str]:
        """Generate context-aware suggestions for regex-detected contractions."""
        
        # Handle possessive filtering
        if suggestion_info is None:
            return [f"'{contraction_text}' is correctly used as a possessive form."]
        
        suggestions = []
        base_suggestion = suggestion_info.get('suggestion', 'expand the contraction')
        
        # Base suggestions based on evidence strength
        if evidence_score > 0.7:
            suggestions.append(f"Expand for formal tone: {base_suggestion}.")
        else:
            suggestions.append(f"Consider expansion: {base_suggestion}.")
        
        # Context-specific advice
        if context:
            content_type = context.get('content_type', 'general')
            
            if content_type in ['academic', 'legal']:
                suggestions.append("Formal writing typically avoids contractions entirely.")
            elif content_type in ['marketing', 'narrative']:
                suggestions.append("Contractions may be acceptable for conversational tone.")
            elif content_type == 'technical':
                suggestions.append("Technical documentation may use contractions for readability.")
        
        # Evidence-based advice
        if evidence_score < 0.3:
            suggestions.append("This contraction may be acceptable in your writing context.")
        elif evidence_score > 0.8:
            suggestions.append("Strong recommendation to expand this contraction.")
        
        return suggestions
