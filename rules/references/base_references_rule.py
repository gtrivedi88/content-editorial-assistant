"""
Base References Rule
A base class that all specific reference rules will inherit from.
Enhanced with robust SpaCy morphological analysis and linguistic anchors.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
import re

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
        def _analyze_sentence_structure(self, sentence: str, nlp=None):
            return nlp(sentence) if nlp and sentence.strip() else None
        def _get_morphological_features(self, token) -> Dict[str, Any]:
            return {}
        def _token_to_dict(self, token) -> Dict[str, Any]:
            return {'text': str(token), 'lemma': '', 'pos': '', 'dep': '', 'i': 0}
        def _analyze_semantic_field(self, token, doc=None) -> str:
            return 'unknown'
        def _calculate_morphological_complexity(self, token) -> float:
            return 1.0


class BaseReferencesRule(BaseRule):
    """
    Enhanced base class for all reference rules using pure SpaCy morphological analysis.
    Provides robust linguistic analysis utilities specific to reference concerns.
    """

    def __init__(self):
        super().__init__()
        # Initialize linguistic anchors for reference-specific analysis
        self._initialize_reference_anchors()
    
    def _initialize_reference_anchors(self):
        """Initialize morphological and semantic anchors for reference analysis."""
        
        # Named entity patterns for reference validation
        self.entity_morphological_patterns = {
            'proper_nouns': {
                'capitalization_patterns': ['Title_Case', 'ALL_CAPS', 'Mixed_Case'],
                'morphological_indicators': ['PROPN', 'NOUN+proper', 'compound+PROPN'],
                'dependency_patterns': ['nsubj+PROPN', 'dobj+PROPN', 'pobj+PROPN']
            },
            'geographic_entities': {
                'ner_labels': ['GPE', 'LOC', 'FAC'],
                'preposition_patterns': ['in', 'at', 'from', 'to', 'near', 'around'],
                'geographic_indicators': ['city', 'state', 'country', 'region', 'area']
            },
            'organizational_entities': {
                'ner_labels': ['ORG', 'PERSON', 'PRODUCT'],
                'title_patterns': ['CEO', 'President', 'Director', 'Manager', 'Chief'],
                'corporate_indicators': ['Inc', 'Corp', 'LLC', 'Ltd', 'Company']
            }
        }
        
        # Product and version reference patterns
        self.product_reference_patterns = {
            'version_morphology': {
                'number_patterns': ['CARDINAL', 'NUM', 'X'],
                'separator_patterns': ['.', '-', '_', ' '],
                'prefix_patterns': ['v', 'ver', 'version', 'release', 'build'],
                'invalid_patterns': ['V.', 'Ver.', '.x', 'X.X']
            },
            'product_naming': {
                'brand_prefixes': ['IBM', 'Microsoft', 'Google', 'Apple', 'Oracle'],
                'product_suffixes': ['Server', 'Client', 'Enterprise', 'Professional'],
                'abbreviation_patterns': True,  # Detected via morphological analysis
                'first_mention_patterns': True  # Context-aware detection
            }
        }
        
        # Citation and reference morphological indicators
        self.citation_morphological_patterns = {
            'reference_types': {
                'document_parts': ['chapter', 'section', 'appendix', 'figure', 'table', 'page'],
                'external_references': ['book', 'article', 'paper', 'document', 'manual'],
                'digital_references': ['website', 'url', 'link', 'page', 'site']
            },
            'link_patterns': {
                'problematic_link_text': ['click here', 'see here', 'go here', 'this link'],
                'imperative_patterns': ['click', 'see', 'go', 'visit', 'check'],
                'demonstrative_patterns': ['this', 'that', 'here', 'there']
            },
            'citation_formatting': {
                'capitalization_rules': {
                    'with_names': True,    # "Director Smith" 
                    'standalone': False,   # "the director"
                    'references': False    # "see chapter 5"
                }
            }
        }
        
        # Professional title and name analysis patterns
        self.title_name_patterns = {
            'professional_titles': {
                'executive_titles': ['CEO', 'CTO', 'CFO', 'President', 'Vice President'],
                'management_titles': ['Director', 'Manager', 'Supervisor', 'Lead', 'Head'],
                'technical_titles': ['Engineer', 'Developer', 'Architect', 'Analyst', 'Specialist'],
                'academic_titles': ['Professor', 'Doctor', 'PhD', 'MD', 'Dr']
            },
            'title_contexts': {
                'with_name': ['appos', 'nmod', 'compound'],  # Dependency relations
                'standalone': ['nsubj', 'dobj', 'pobj'],     # Generic usage
                'descriptive': ['amod', 'attr']              # Descriptive usage
            }
        }

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes the text for reference-related violations.
        This method must be implemented by all subclasses.
        """
        raise NotImplementedError("Subclasses must implement the analyze method.")
    
    def _apply_zero_false_positive_guards_references(self, token, context: Dict[str, Any] = None) -> bool:
        """
        Apply surgical zero false positive guards specific to references.
        Returns True if this token should be ignored (no evidence).
        """
        if not token or not hasattr(token, 'text'):
            return True
        
        # Guard 1: Code blocks and technical contexts
        if context and context.get('block_type') in ['code_block', 'inline_code', 'literal_block']:
            return True
        
        # Guard 2: URLs and file paths
        if hasattr(token, 'like_url') and token.like_url:
            return True
        if hasattr(token, 'text') and ('/' in token.text or '\\' in token.text):
            return True
        
        # Guard 3: Recognized entities that shouldn't be flagged
        if hasattr(token, 'ent_type_') and token.ent_type_ in ['PERSON', 'ORG', 'PRODUCT', 'EVENT', 'GPE']:
            # But allow specific reference rule logic to override this
            pass
        
        # Guard 4: Technical identifiers and version numbers
        if hasattr(token, 'text'):
            text = token.text
            if re.match(r'^[A-Z0-9_]+$', text) and len(text) <= 10:  # All caps technical identifier
                return True
            if re.match(r'^\d+\.\d+', text):  # Version numbers are handled by specific rules
                pass
        
        return False
    
    def _analyze_entity_capitalization(self, doc, sentence: str, sentence_index: int, entity_types: List[str] = None, text: str = None, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Analyze entity capitalization using advanced morphological analysis.
        """
        errors = []
        
        if not doc:
            return errors
        
        entity_types = entity_types if entity_types is not None else ['PERSON', 'ORG', 'GPE', 'LOC', 'PRODUCT']
        
        try:
            for ent in doc.ents:
                if ent.label_ in entity_types:
                    # Analyze capitalization patterns using morphological features
                    capitalization_analysis = self._analyze_capitalization_patterns(ent)
                    
                    if capitalization_analysis['has_errors']:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message=f"{ent.label_} '{ent.text}' has incorrect capitalization.",
                            suggestions=capitalization_analysis['suggestions'],
                            severity='medium',
                            text=text,  # Enhanced: Pass full text for better confidence analysis
                            context=context,  # Enhanced: Pass context for domain-specific validation
                            linguistic_analysis={
                                'entity': self._entity_to_dict(ent),
                                'capitalization_analysis': capitalization_analysis,
                                'morphological_pattern': capitalization_analysis.get('pattern')
                            }
                        ))
        
        except Exception:
            pass
        
        return errors
    
    def _analyze_product_version_patterns(self, doc, sentence: str, sentence_index: int, text: str = None, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Analyze product version patterns using morphological analysis.
        """
        errors = []
        
        if not doc:
            return errors
        
        try:
            # Detect version patterns using morphological analysis
            version_patterns = self._detect_version_patterns(doc)
            
            for pattern in version_patterns:
                if pattern['is_invalid']:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message=f"Invalid version format: '{pattern['text']}'",
                        suggestions=pattern['suggestions'],
                        severity='medium',
                        text=text,  # Enhanced: Pass full text for better confidence analysis
                        context=context,  # Enhanced: Pass context for domain-specific validation
                        linguistic_analysis={
                            'version_pattern': pattern,
                            'morphological_analysis': pattern.get('morphological_features')
                        }
                    ))
        
        except Exception:
            pass
        
        return errors
    
    def _analyze_product_naming_conventions(self, doc, sentence: str, sentence_index: int, product_context: Dict[str, Any] = None, text: str = None, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Analyze product naming conventions using context-aware morphological analysis.
        """
        errors = []
        
        if not doc:
            return errors
        
        try:
            # Detect product references and naming issues
            product_references = self._detect_product_references(doc, product_context)
            
            for reference in product_references:
                if reference['has_violations']:
                    for violation in reference['violations']:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message=violation['message'],
                            suggestions=violation['suggestions'],
                            severity=violation.get('severity', 'medium'),
                            text=text,  # Enhanced: Pass full text for better confidence analysis
                            context=context,  # Enhanced: Pass context for domain-specific validation
                            linguistic_analysis={
                                'product_reference': reference,
                                'violation_type': violation['type'],
                                'morphological_analysis': reference.get('morphological_features')
                            }
                        ))
        
        except Exception:
            pass
        
        return errors
    
    def _analyze_title_name_relationships(self, doc, sentence: str, sentence_index: int, text: str = None, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Analyze professional titles and their relationship to names using dependency parsing.
        """
        errors = []
        
        if not doc:
            return errors
        
        try:
            # Detect title-name relationships using dependency analysis
            title_name_pairs = self._detect_title_name_relationships(doc)
            
            for pair in title_name_pairs:
                capitalization_analysis = self._analyze_title_capitalization(pair)
                
                if capitalization_analysis['needs_correction']:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message=capitalization_analysis['message'],
                        suggestions=capitalization_analysis['suggestions'],
                        severity='medium',
                        text=text,  # Enhanced: Pass full text for better confidence analysis
                        context=context,  # Enhanced: Pass context for domain-specific validation
                        linguistic_analysis={
                            'title_name_pair': pair,
                            'capitalization_analysis': capitalization_analysis,
                            'morphological_context': pair.get('morphological_context')
                        }
                    ))
        
        except Exception:
            pass
        
        return errors
    
    def _analyze_citation_patterns(self, doc, sentence: str, sentence_index: int, text: str = None, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Analyze citation and reference patterns using morphological analysis.
        """
        errors = []
        
        if not doc:
            return errors
        
        try:
            # Detect problematic citation patterns
            citation_issues = self._detect_citation_issues(doc, sentence)
            
            for issue in citation_issues:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message=issue['message'],
                    suggestions=issue['suggestions'],
                    severity=issue.get('severity', 'medium'),
                    text=text,  # Enhanced: Pass full text for better confidence analysis
                    context=context,  # Enhanced: Pass context for domain-specific validation
                    linguistic_analysis={
                        'citation_issue': issue,
                        'issue_type': issue['type'],
                        'morphological_pattern': issue.get('morphological_pattern')
                    }
                ))
        
        except Exception:
            pass
        
        return errors
    
    def _analyze_capitalization_patterns(self, entity) -> Dict[str, Any]:
        """
        Analyze capitalization patterns of an entity using morphological features.
        """
        try:
            tokens = list(entity)
            capitalization_errors = []
            suggestions = []
            
            for token in tokens:
                # Skip articles, conjunctions, and prepositions in entity names
                if token.text.lower() in ['the', 'of', 'and', 'for', 'in', 'on', 'at']:
                    continue
                
                # Check capitalization based on token position and type
                is_first_token = token.i == entity.start
                is_proper_noun = token.pos_ == 'PROPN'
                
                # All significant words in proper nouns should be capitalized
                if is_proper_noun and token.text[0].islower():
                    capitalization_errors.append({
                        'token': token.text,
                        'error_type': 'missing_capital',
                        'position': 'first' if is_first_token else 'internal'
                    })
                    suggestions.append(f"Capitalize '{token.text}' to '{token.text.capitalize()}'")
                
                # Check for incorrect all-caps (unless it's an acronym)
                elif (token.text.isupper() and len(token.text) > 3 and 
                      not self._is_likely_acronym(token.text)):
                    capitalization_errors.append({
                        'token': token.text,
                        'error_type': 'excessive_caps',
                        'position': 'first' if is_first_token else 'internal'
                    })
                    suggestions.append(f"Use title case: '{token.text.capitalize()}'")
            
            return {
                'has_errors': len(capitalization_errors) > 0,
                'errors': capitalization_errors,
                'suggestions': suggestions,
                'pattern': self._identify_capitalization_pattern(entity)
            }
        
        except Exception:
            return {
                'has_errors': False,
                'errors': [],
                'suggestions': [],
                'pattern': 'unknown'
            }
    
    def _detect_version_patterns(self, doc) -> List[Dict[str, Any]]:
        """
        Detect version patterns using morphological analysis.
        """
        version_patterns = []
        
        if not doc:
            return version_patterns
        
        try:
            # Look for version-like patterns
            for i, token in enumerate(doc):
                # Check for version prefixes
                if (token.lemma_.lower() in ['v', 'ver', 'version', 'release', 'build'] and 
                    i + 1 < len(doc)):
                    
                    # Analyze the following tokens for version numbers
                    version_analysis = self._analyze_version_number_morphology(doc, i + 1)
                    
                    if version_analysis['is_version']:
                        version_text = ' '.join([token.text] + [t.text for t in version_analysis['tokens']])
                        
                        validation = self._validate_version_format(version_text, version_analysis)
                        
                        version_patterns.append({
                            'text': version_text,
                            'is_invalid': not validation['is_valid'],
                            'prefix_token': self._token_to_dict(token) or {},
                            'version_tokens': [self._token_to_dict(t) or {} for t in version_analysis['tokens']],
                            'suggestions': validation['suggestions'],
                            'morphological_features': {
                                'prefix': self._get_morphological_features(token),
                                'version_structure': version_analysis
                            }
                        })
                
                # Also check for standalone version patterns (e.g., "8.1.x")
                elif self._looks_like_version_number(token):
                    version_analysis = self._analyze_standalone_version(token)
                    
                    if version_analysis['is_invalid']:
                        version_patterns.append({
                            'text': token.text,
                            'is_invalid': True,
                            'version_tokens': [self._token_to_dict(token) or {}],
                            'suggestions': version_analysis['suggestions'],
                            'morphological_features': self._get_morphological_features(token)
                        })
        
        except Exception:
            pass
        
        return version_patterns
    
    def _detect_product_references(self, doc, product_context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Detect product references and analyze naming conventions.
        """
        product_references = []
        
        if not doc:
            return product_references
        
        try:
            # Track product mentions across the document
            product_tracker = defaultdict(list)
            
            # Detect potential product names using NER and morphological patterns
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT', 'PROPN']:
                    product_analysis = self._analyze_product_entity(ent, doc)
                    
                    if product_analysis['is_product']:
                        product_tracker[product_analysis['canonical_name']].append({
                            'entity': ent,
                            'analysis': product_analysis,
                            'sentence_position': ent.sent.start
                        })
            
            # Analyze each product for naming violations
            for product_name, mentions in product_tracker.items():
                violations = self._check_product_naming_violations(product_name, mentions, product_context)
                
                if violations:
                    first_mention = mentions[0]
                    product_references.append({
                        'product_name': product_name,
                        'has_violations': True,
                        'violations': violations,
                        'mentions': len(mentions),
                        'morphological_features': first_mention['analysis'].get('morphological_features')
                    })
        
        except Exception:
            pass
        
        return product_references
    
    def _detect_title_name_relationships(self, doc) -> List[Dict[str, Any]]:
        """
        Detect professional titles and their relationship to names using dependency parsing.
        """
        title_name_pairs = []
        
        if not doc:
            return title_name_pairs
        
        try:
            for ent in doc.ents:
                if ent.label_ == 'PERSON':
                    # Look for titles associated with this person
                    title_analysis = self._find_associated_titles(ent, doc)
                    
                    if title_analysis['has_titles']:
                        for title_info in title_analysis['titles']:
                            title_name_pairs.append({
                                'person': self._entity_to_dict(ent),
                                'title': title_info,
                                'relationship_type': title_info['relationship'],
                                'morphological_context': {
                                    'person_features': [self._get_morphological_features(token) for token in ent],
                                    'title_features': title_info.get('morphological_features')
                                }
                            })
            
            # Also look for standalone title usage
            standalone_titles = self._find_standalone_titles(doc)
            title_name_pairs.extend(standalone_titles)
        
        except Exception:
            pass
        
        return title_name_pairs
    
    def _detect_citation_issues(self, doc, sentence: str) -> List[Dict[str, Any]]:
        """
        Detect citation and reference issues using morphological analysis.
        """
        citation_issues = []
        
        if not doc:
            return citation_issues
        
        try:
            # Detect problematic link text patterns
            link_issues = self._detect_problematic_link_patterns(doc)
            citation_issues.extend(link_issues)
            
            # Detect incorrect reference capitalization
            reference_cap_issues = self._detect_reference_capitalization_issues(doc)
            citation_issues.extend(reference_cap_issues)
            
            # Detect malformed citations
            citation_format_issues = self._detect_citation_format_issues(doc, sentence)
            citation_issues.extend(citation_format_issues)
        
        except Exception:
            pass
        
        return citation_issues
    
    def _is_likely_acronym(self, text: str) -> bool:
        """Check if text is likely an acronym."""
        return (len(text) <= 5 and 
                text.isupper() and 
                not any(char in text for char in '.,!?'))
    
    def _identify_capitalization_pattern(self, entity) -> str:
        """Identify the capitalization pattern of an entity."""
        try:
            tokens = [token.text for token in entity]
            
            if all(token[0].isupper() for token in tokens if token.isalpha()):
                return 'title_case'
            elif all(token.isupper() for token in tokens if token.isalpha()):
                return 'all_caps'
            elif all(token.islower() for token in tokens if token.isalpha()):
                return 'all_lower'
            else:
                return 'mixed_case'
        except Exception:
            return 'unknown'
    
    def _entity_to_dict(self, entity) -> Dict[str, Any]:
        """Convert SpaCy entity to JSON-serializable dictionary."""
        try:
            return {
                'text': entity.text,
                'label': entity.label_,
                'start': entity.start,
                'end': entity.end,
                'tokens': [self._token_to_dict(token) for token in entity]
            }
        except Exception:
            return {'text': str(entity), 'label': 'unknown'}
    
    def _analyze_version_number_morphology(self, doc, start_index: int) -> Dict[str, Any]:
        """Analyze version number morphology starting from a given index."""
        try:
            version_tokens = []
            i = start_index
            
            while i < len(doc) and i < start_index + 5:  # Look ahead max 5 tokens
                token = doc[i]
                
                # Check if token is part of version number
                if (token.like_num or 
                    token.text in ['.', '-', '_'] or
                    token.text.lower() in ['x', 'beta', 'alpha', 'rc']):
                    version_tokens.append(token)
                    i += 1
                else:
                    break
            
            return {
                'is_version': len(version_tokens) > 0,
                'tokens': version_tokens,
                'pattern': self._classify_version_pattern(version_tokens)
            }
        
        except Exception:
            return {'is_version': False, 'tokens': [], 'pattern': 'unknown'}
    
    def _validate_version_format(self, version_text: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Validate version format and suggest corrections."""
        try:
            is_valid = True
            suggestions = []
            
            # Check for problematic patterns
            if re.search(r'\bV\.|Ver\.', version_text, re.IGNORECASE):
                is_valid = False
                suggestions.append("Remove 'V.' or 'Ver.' prefix. Use numbers only (e.g., '8.1.1')")
            
            if '.x' in version_text.lower():
                is_valid = False
                suggestions.append("Replace '.x' wildcard with specific version number")
            
            # Check for valid version pattern
            if not re.search(r'\d+(\.\d+)*', version_text):
                is_valid = False
                suggestions.append("Use standard version format: major.minor.patch (e.g., '2.1.0')")
            
            return {
                'is_valid': is_valid,
                'suggestions': suggestions
            }
        
        except Exception:
            return {'is_valid': True, 'suggestions': []}
    
    def _looks_like_version_number(self, token) -> bool:
        """Check if a token looks like a version number."""
        try:
            text = token.text
            # Pattern like "8.1.x" or "2.0.1"
            return bool(re.match(r'\d+\.\d+(\.\w+)+', text))
        except Exception:
            return False
    
    def _analyze_standalone_version(self, token) -> Dict[str, Any]:
        """Analyze a standalone version token."""
        try:
            text = token.text
            is_invalid = False
            suggestions = []
            
            if '.x' in text.lower():
                is_invalid = True
                suggestions.append(f"Replace '{text}' with specific version number (e.g., '2.1.0')")
            
            return {
                'is_invalid': is_invalid,
                'suggestions': suggestions
            }
        
        except Exception:
            return {'is_invalid': False, 'suggestions': []}
    
    def _classify_version_pattern(self, tokens) -> str:
        """Classify the type of version pattern."""
        if not tokens:
            return 'none'
        
        token_texts = [token.text for token in tokens]
        pattern = ''.join(token_texts)
        
        if re.match(r'\d+\.\d+\.\d+', pattern):
            return 'semantic_version'
        elif re.match(r'\d+\.\d+', pattern):
            return 'major_minor'
        elif '.x' in pattern:
            return 'wildcard_version'
        else:
            return 'custom_version'
    
    def _get_reference_base_evidence_score(self, token, sentence, context: Dict[str, Any] = None) -> float:
        """
        Get base evidence score for reference violations.
        More specific violations get higher base scores.
        """
        if not self._meets_basic_criteria_references(token):
            return 0.0
        
        # Higher scores for specific reference patterns
        if hasattr(token, 'text'):
            text = token.text.lower()
            
            # Specific problematic patterns get high scores
            if text in ['click here', 'see here', 'go here']:
                return 0.9  # Very specific violation
            
            # Professional titles in wrong context
            if text in ['ceo', 'director', 'manager', 'president']:
                return 0.7  # Clear pattern but needs context
            
            # Version prefixes
            if text in ['v.', 'ver.', 'version']:
                return 0.8  # Specific formatting violation
        
        return 0.6  # Default moderate evidence
    
    def _meets_basic_criteria_references(self, token) -> bool:
        """
        Check if token meets basic criteria for reference analysis.
        """
        if not token or not hasattr(token, 'text'):
            return False
        
        text = token.text.strip()
        if not text or len(text) < 2:
            return False
        
        return True
    
    def _apply_linguistic_clues_references(self, evidence_score: float, token, sentence) -> float:
        """
        Apply reference-specific linguistic clues.
        """
        if not token:
            return evidence_score
        
        # POS-based adjustments
        if hasattr(token, 'pos_'):
            if token.pos_ == 'PROPN':
                # Proper nouns need careful handling in references
                evidence_score += 0.1
            elif token.pos_ == 'NOUN':
                # Regular nouns less likely to be reference errors
                evidence_score -= 0.1
        
        # Dependency-based adjustments
        if hasattr(token, 'dep_'):
            if token.dep_ == 'appos':  # Appositional modifier (like titles with names)
                evidence_score += 0.2
            elif token.dep_ in ['nsubj', 'dobj']:
                # Subject/object usage patterns
                evidence_score -= 0.1
        
        # Named entity context
        if hasattr(token, 'ent_type_') and token.ent_type_:
            if token.ent_type_ in ['PERSON', 'ORG']:
                evidence_score += 0.1  # Names need proper handling
            elif token.ent_type_ in ['GPE', 'LOC']:
                evidence_score += 0.15  # Geographic locations need capitalization
        
        return evidence_score
    
    def _apply_structural_clues_references(self, evidence_score: float, token, context: Dict[str, Any] = None) -> float:
        """
        Apply reference-specific structural clues.
        """
        if not context:
            return evidence_score
        
        block_type = context.get('block_type', 'paragraph')
        
        # Heading context - names and titles more important
        if block_type == 'heading':
            evidence_score += 0.2
        
        # List context - product names and versions common
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score += 0.1
        
        # Table context - structured data, references important
        elif block_type in ['table_cell', 'table_header']:
            evidence_score += 0.15
        
        # Link context - citation rules very important
        elif 'link' in block_type or context.get('has_links', False):
            evidence_score += 0.3
        
        return evidence_score
    
    def _apply_semantic_clues_references(self, evidence_score: float, token, text: str, context: Dict[str, Any] = None) -> float:
        """
        Apply reference-specific semantic clues.
        """
        if not context:
            return evidence_score
        
        content_type = context.get('content_type', 'general')
        
        # Technical content - product names and versions critical
        if content_type == 'technical':
            evidence_score += 0.2
        
        # Marketing content - product names very important
        elif content_type == 'marketing':
            evidence_score += 0.25
        
        # Legal content - names and titles crucial
        elif content_type == 'legal':
            evidence_score += 0.3
        
        # Documentation - citations and references critical
        elif content_type in ['documentation', 'manual']:
            evidence_score += 0.2
        
        # Domain-specific adjustments
        domain = context.get('domain', 'general')
        if domain in ['software', 'technology']:
            evidence_score += 0.1  # Product names and versions important
        
        return evidence_score
    
    def _analyze_product_entity(self, entity, doc) -> Dict[str, Any]:
        """Analyze if an entity represents a product."""
        # Simplified implementation - would be more sophisticated in practice
        return {
            'is_product': True,
            'canonical_name': entity.text,
            'morphological_features': [self._get_morphological_features(token) for token in entity]
        }
    
    def _check_product_naming_violations(self, product_name: str, mentions: List[Dict], context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Check for product naming violations."""
        # Simplified implementation
        return []
    
    def _find_associated_titles(self, person_entity, doc) -> Dict[str, Any]:
        """Find titles associated with a person entity."""
        # Simplified implementation
        return {'has_titles': False, 'titles': []}
    
    def _find_standalone_titles(self, doc) -> List[Dict[str, Any]]:
        """Find standalone title usage."""
        # Simplified implementation
        return []
    
    def _analyze_title_capitalization(self, title_name_pair) -> Dict[str, Any]:
        """Analyze title capitalization rules."""
        # Simplified implementation
        return {'needs_correction': False}
    
    def _detect_problematic_link_patterns(self, doc) -> List[Dict[str, Any]]:
        """Detect problematic link text patterns."""
        # Simplified implementation
        return []
    
    def _detect_reference_capitalization_issues(self, doc) -> List[Dict[str, Any]]:
        """Detect reference capitalization issues."""
        # Simplified implementation
        return []
    
    def _detect_citation_format_issues(self, doc, sentence: str) -> List[Dict[str, Any]]:
        """Detect citation format issues."""
        # Simplified implementation
        return []
