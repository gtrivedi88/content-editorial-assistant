"""
Product and Service Names Rule
Based on IBM Style Guide topic: "Product and service names"
Enhanced with pure SpaCy morphological analysis for robust product naming detection.
"""
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict
from .base_references_rule import BaseReferencesRule

class ProductNamesRule(BaseReferencesRule):
    """
    Checks for correct usage of product names using advanced morphological and semantic analysis
    to detect product entities, validate brand prefixes, and identify abbreviation issues.
    Uses context-aware detection instead of hardcoded product lists.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize product naming-specific linguistic anchors
        self._initialize_product_naming_anchors()
    
    def _initialize_product_naming_anchors(self):
        """Initialize morphological patterns specific to product naming analysis."""
        
        # Product entity detection patterns
        self.product_morphological_patterns = {
            'entity_indicators': {
                'software_suffixes': ['Server', 'Client', 'Studio', 'Framework', 'Engine', 'Platform'],
                'service_suffixes': ['Service', 'Services', 'Cloud', 'Online', 'Pro', 'Enterprise'],
                'product_types': ['Database', 'Application', 'System', 'Tool', 'Suite', 'Package'],
                'version_indicators': ['Express', 'Standard', 'Professional', 'Ultimate', 'Community']
            },
            'brand_patterns': {
                'major_brands': ['IBM', 'Microsoft', 'Google', 'Apple', 'Oracle', 'Adobe', 'Amazon'],
                'technology_brands': ['Linux', 'Windows', 'MacOS', 'Android', 'iOS'],
                'morphological_indicators': ['PROPN+PROPN', 'ORG+PRODUCT', 'compound+PROPN']
            },
            'abbreviation_indicators': {
                'pattern_types': ['ALL_CAPS', 'Mixed_Case', 'CamelCase'],
                'length_patterns': [2, 3, 4, 5],  # Common abbreviation lengths
                'context_clues': ['formerly', 'also known as', 'abbreviated', 'short for']
            }
        }
        
        # Product naming conventions
        self.naming_conventions = {
            'first_mention_rules': {
                'requires_brand_prefix': True,
                'brand_position': 'before',  # Brand comes before product name
                'acceptable_exceptions': ['well-known', 'industry-standard']
            },
            'subsequent_mentions': {
                'brand_optional': True,
                'consistency_required': True,
                'abbreviation_rules': 'contextual'  # Depends on clarity
            },
            'abbreviation_policies': {
                'avoid_unofficial': True,
                'prefer_full_names': True,
                'context_dependent': True
            }
        }
        
        # Context patterns for product identification
        self.product_context_patterns = {
            'software_context': {
                'action_verbs': ['install', 'download', 'update', 'configure', 'run'],
                'descriptive_verbs': ['supports', 'provides', 'enables', 'includes'],
                'technical_prepositions': ['using', 'with', 'on', 'through', 'via']
            },
            'business_context': {
                'commercial_verbs': ['purchase', 'license', 'subscribe', 'upgrade'],
                'service_verbs': ['offers', 'delivers', 'provides', 'hosts'],
                'relationship_verbs': ['integrates', 'connects', 'works with']
            }
        }

    def _get_rule_type(self) -> str:
        return 'references_product_names'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for product naming violations using comprehensive
        morphological and semantic analysis.
        """
        errors = []
        if not nlp:
            return errors

        # Track product mentions across the entire text for first mention analysis
        product_context = self._build_product_context(text, sentences, nlp)

        for i, sentence in enumerate(sentences):
            doc = self._analyze_sentence_structure(sentence, nlp)
            if not doc:
                continue
            
            # Use the base class method for product naming analysis
            naming_errors = self._analyze_product_naming_conventions(doc, sentence, i, product_context)
            errors.extend(naming_errors)
            
            # Additional product-specific analysis
            additional_errors = self._analyze_product_specific_patterns(doc, sentence, i, product_context)
            errors.extend(additional_errors)

        return errors
    
    def _build_product_context(self, text: str, sentences: List[str], nlp) -> Dict[str, Any]:
        """
        Build comprehensive context about product mentions across the entire text.
        """
        product_context = {
            'product_mentions': defaultdict(list),
            'brand_associations': defaultdict(set),
            'abbreviations_used': defaultdict(list),
            'document_type': 'technical',  # Could be inferred from content
            'first_mentions': {},
            'known_products': set()
        }
        
        try:
            # Analyze the entire text to understand product usage patterns
            full_doc = self._analyze_sentence_structure(text, nlp)
            if full_doc:
                # Collect all product entities and their contexts
                product_entities = self._extract_product_entities(full_doc)
                
                for entity in product_entities:
                    product_name = entity['canonical_name']
                    product_context['product_mentions'][product_name].append(entity)
                    
                    # Track brand associations
                    if entity.get('brand'):
                        product_context['brand_associations'][product_name].add(entity['brand'])
                    
                    # Track first mention
                    if product_name not in product_context['first_mentions']:
                        product_context['first_mentions'][product_name] = entity
                    
                    # Track abbreviations
                    if entity.get('is_abbreviation'):
                        product_context['abbreviations_used'][product_name].append(entity)
        
        except Exception:
            pass
        
        return product_context
    
    def _analyze_product_specific_patterns(self, doc, sentence: str, sentence_index: int, product_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze product-specific patterns that require attention.
        """
        errors = []
        
        if not doc:
            return errors
        
        # Detect missing brand prefixes on first mentions
        first_mention_errors = self._detect_missing_brand_prefixes(doc, sentence_index, product_context)
        for error in first_mention_errors:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"First mention of '{error['product']}' should include brand prefix.",
                suggestions=error['suggestions'],
                severity='high',
                linguistic_analysis={
                    'first_mention_error': error,
                    'product_analysis': error.get('product_analysis')
                }
            ))
        
        # Detect unofficial abbreviations
        abbreviation_errors = self._detect_unofficial_abbreviations(doc, product_context)
        for error in abbreviation_errors:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Avoid unofficial abbreviation '{error['abbreviation']}'. Use full product name.",
                suggestions=error['suggestions'],
                severity='high',
                linguistic_analysis={
                    'abbreviation_error': error,
                    'morphological_pattern': error.get('morphological_pattern')
                }
            ))
        
        # Detect inconsistent product naming
        consistency_errors = self._detect_naming_inconsistencies(doc, product_context)
        for error in consistency_errors:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Inconsistent product naming: '{error['current']}'. Use consistent form.",
                suggestions=error['suggestions'],
                severity='medium',
                linguistic_analysis={
                    'consistency_error': error,
                    'naming_pattern': error.get('naming_pattern')
                }
            ))
        
        return errors
    
    def _extract_product_entities(self, doc) -> List[Dict[str, Any]]:
        """
        Extract product entities using advanced morphological analysis.
        """
        product_entities = []
        
        if not doc:
            return product_entities
        
        try:
            # Use NER to find potential product entities
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT', 'PERSON']:  # PERSON might be product names
                    product_analysis = self._analyze_entity_as_product(ent, doc)
                    
                    if product_analysis['is_product']:
                        product_entities.append(product_analysis)
            
            # Also look for entities not caught by NER using morphological patterns
            non_ner_products = self._detect_non_ner_products(doc)
            product_entities.extend(non_ner_products)
        
        except Exception:
            pass
        
        return product_entities
    
    def _analyze_entity_as_product(self, entity, doc) -> Dict[str, Any]:
        """
        Analyze whether an entity represents a product using morphological features.
        """
        try:
            entity_text = entity.text
            tokens = list(entity)
            
            # Analyze morphological patterns
            morphological_score = self._calculate_product_likelihood_score(entity, doc)
            
            # Determine if this is likely a product
            is_product = morphological_score > 0.6
            
            # Extract brand information
            brand_info = self._extract_brand_information(entity, doc)
            
            # Determine canonical name
            canonical_name = self._determine_canonical_product_name(entity_text)
            
            # Check if it's an abbreviation
            abbreviation_analysis = self._analyze_abbreviation_pattern(entity, doc)
            
            return {
                'entity': entity,
                'canonical_name': canonical_name,
                'display_name': entity_text,
                'is_product': is_product,
                'confidence_score': morphological_score,
                'brand': brand_info.get('brand'),
                'has_brand_prefix': brand_info.get('has_prefix', False),
                'is_abbreviation': abbreviation_analysis['is_abbreviation'],
                'abbreviation_info': abbreviation_analysis,
                'morphological_features': [self._get_morphological_features(token) for token in tokens],
                'context_analysis': self._analyze_product_context(entity, doc),
                'sentence_position': entity.sent.start,
                'tokens': [self._token_to_dict(token) for token in tokens]
            }
        
        except Exception:
            return {
                'entity': entity,
                'canonical_name': entity.text,
                'is_product': False,
                'confidence_score': 0.0
            }
    
    def _detect_non_ner_products(self, doc) -> List[Dict[str, Any]]:
        """
        Detect products not caught by NER using morphological patterns.
        """
        non_ner_products = []
        
        try:
            for token in doc:
                # Look for compound constructions that might be products
                if (token.pos_ == 'PROPN' and 
                    any(child.dep_ == 'compound' for child in token.children)):
                    
                    # Construct the potential product name
                    product_phrase = self._construct_product_phrase(token)
                    
                    if self._looks_like_product_name(product_phrase, doc):
                        # Create a synthetic entity-like structure
                        product_analysis = {
                            'canonical_name': product_phrase,
                            'display_name': product_phrase,
                            'is_product': True,
                            'confidence_score': 0.7,
                            'morphological_features': [self._get_morphological_features(token)],
                            'context_analysis': self._analyze_product_context_token(token, doc)
                        }
                        non_ner_products.append(product_analysis)
        
        except Exception:
            pass
        
        return non_ner_products
    
    def _calculate_product_likelihood_score(self, entity, doc) -> float:
        """
        Calculate likelihood that entity represents a product using morphological analysis.
        """
        try:
            score = 0.0
            entity_text = entity.text
            tokens = list(entity)
            
            # Check for product-indicative suffixes
            product_suffixes = self.product_morphological_patterns['entity_indicators']['software_suffixes']
            product_suffixes.extend(self.product_morphological_patterns['entity_indicators']['service_suffixes'])
            
            for suffix in product_suffixes:
                if entity_text.endswith(suffix):
                    score += 0.4
                    break
            
            # Check for brand prefixes
            brand_prefixes = self.product_morphological_patterns['brand_patterns']['major_brands']
            for brand in brand_prefixes:
                if entity_text.startswith(brand):
                    score += 0.3
                    break
            
            # Check morphological patterns
            if len(tokens) > 1:  # Multi-word products are more likely
                score += 0.2
            
            # Check POS patterns
            if all(token.pos_ == 'PROPN' for token in tokens):
                score += 0.2
            
            # Check context
            context_score = self._calculate_product_context_score(entity, doc)
            score += context_score * 0.3
            
            return min(score, 1.0)
        
        except Exception:
            return 0.0
    
    def _extract_brand_information(self, entity, doc) -> Dict[str, Any]:
        """
        Extract brand information from product entity.
        """
        try:
            entity_text = entity.text
            brand_info = {
                'brand': None,
                'has_prefix': False,
                'brand_position': None
            }
            
            # Check for known brand prefixes
            brands = self.product_morphological_patterns['brand_patterns']['major_brands']
            
            for brand in brands:
                if entity_text.startswith(brand + ' '):
                    brand_info['brand'] = brand
                    brand_info['has_prefix'] = True
                    brand_info['brand_position'] = 'prefix'
                    break
                elif entity_text.endswith(' ' + brand):
                    brand_info['brand'] = brand
                    brand_info['has_prefix'] = True
                    brand_info['brand_position'] = 'suffix'
                    break
            
            return brand_info
        
        except Exception:
            return {'brand': None, 'has_prefix': False}
    
    def _analyze_abbreviation_pattern(self, entity, doc) -> Dict[str, Any]:
        """
        Analyze if entity represents an abbreviation using morphological patterns.
        """
        try:
            entity_text = entity.text
            
            analysis = {
                'is_abbreviation': False,
                'abbreviation_type': None,
                'confidence': 0.0,
                'likely_expansion': None
            }
            
            # Check for all-caps pattern (common abbreviation indicator)
            if entity_text.isupper() and len(entity_text) >= 2 and len(entity_text) <= 6:
                analysis['is_abbreviation'] = True
                analysis['abbreviation_type'] = 'acronym'
                analysis['confidence'] = 0.8
            
            # Check for mixed-case abbreviations
            elif (len(entity_text) <= 5 and 
                  any(c.isupper() for c in entity_text) and 
                  not entity_text[0].islower()):
                analysis['is_abbreviation'] = True
                analysis['abbreviation_type'] = 'mixed_case'
                analysis['confidence'] = 0.6
            
            # Look for contextual clues about abbreviations
            context_clues = self._find_abbreviation_context_clues(entity, doc)
            if context_clues:
                analysis['is_abbreviation'] = True
                analysis['confidence'] = max(analysis['confidence'], 0.9)
                analysis['likely_expansion'] = context_clues.get('expansion')
            
            return analysis
        
        except Exception:
            return {
                'is_abbreviation': False,
                'abbreviation_type': None,
                'confidence': 0.0
            }
    
    def _detect_missing_brand_prefixes(self, doc, sentence_index: int, product_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect products that should have brand prefixes on first mention.
        """
        missing_prefixes = []
        
        try:
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT']:
                    product_analysis = self._analyze_entity_as_product(ent, doc)
                    
                    if (product_analysis['is_product'] and 
                        not product_analysis['has_brand_prefix']):
                        
                        # Check if this is a first mention
                        canonical_name = product_analysis['canonical_name']
                        first_mention = product_context['first_mentions'].get(canonical_name)
                        
                        if (first_mention and 
                            first_mention.get('sentence_position') == ent.sent.start):
                            
                            # This is a first mention without brand prefix
                            suggestions = self._generate_brand_prefix_suggestions(canonical_name)
                            
                            missing_prefixes.append({
                                'product': canonical_name,
                                'suggestions': suggestions,
                                'product_analysis': product_analysis,
                                'morphological_pattern': f"PROPN without brand prefix"
                            })
        
        except Exception:
            pass
        
        return missing_prefixes
    
    def _detect_unofficial_abbreviations(self, doc, product_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect unofficial or problematic abbreviations.
        """
        abbreviation_errors = []
        
        try:
            # Check known problematic abbreviations from context
            for product_name, abbreviations in product_context['abbreviations_used'].items():
                for abbrev_info in abbreviations:
                    if self._is_problematic_abbreviation(abbrev_info):
                        suggestions = self._generate_abbreviation_correction_suggestions(
                            abbrev_info['display_name'], product_name
                        )
                        
                        abbreviation_errors.append({
                            'abbreviation': abbrev_info['display_name'],
                            'full_name': product_name,
                            'suggestions': suggestions,
                            'morphological_pattern': abbrev_info.get('abbreviation_info', {}).get('abbreviation_type'),
                            'confidence': abbrev_info.get('abbreviation_info', {}).get('confidence', 0.0)
                        })
        
        except Exception:
            pass
        
        return abbreviation_errors
    
    def _detect_naming_inconsistencies(self, doc, product_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect inconsistent product naming patterns.
        """
        consistency_errors = []
        
        try:
            # Check for inconsistencies in how products are named
            for product_name, mentions in product_context['product_mentions'].items():
                if len(mentions) > 1:
                    # Analyze naming consistency across mentions
                    consistency_analysis = self._analyze_naming_consistency(mentions)
                    
                    if consistency_analysis['has_inconsistencies']:
                        for inconsistency in consistency_analysis['inconsistencies']:
                            consistency_errors.append({
                                'current': inconsistency['variant'],
                                'expected': consistency_analysis['recommended_form'],
                                'suggestions': inconsistency['suggestions'],
                                'naming_pattern': inconsistency['pattern_type']
                            })
        
        except Exception:
            pass
        
        return consistency_errors
    
    def _determine_canonical_product_name(self, entity_text: str) -> str:
        """
        Determine the canonical form of a product name.
        """
        # Simple canonicalization - in practice this would be more sophisticated
        return entity_text.strip()
    
    def _analyze_product_context(self, entity, doc) -> Dict[str, Any]:
        """
        Analyze the context around a product entity.
        """
        try:
            context = {
                'software_context_score': 0.0,
                'business_context_score': 0.0,
                'technical_indicators': [],
                'action_verbs': []
            }
            
            # Look for context clues in surrounding tokens
            window = 5
            start_idx = max(0, entity.start - window)
            end_idx = min(len(doc), entity.end + window)
            
            software_verbs = self.product_context_patterns['software_context']['action_verbs']
            business_verbs = self.product_context_patterns['business_context']['commercial_verbs']
            
            for i in range(start_idx, end_idx):
                if i < entity.start or i >= entity.end:
                    token = doc[i]
                    
                    if token.lemma_.lower() in software_verbs:
                        context['software_context_score'] += 0.2
                        context['action_verbs'].append(token.text)
                    
                    if token.lemma_.lower() in business_verbs:
                        context['business_context_score'] += 0.2
            
            return context
        
        except Exception:
            return {
                'software_context_score': 0.0,
                'business_context_score': 0.0,
                'technical_indicators': [],
                'action_verbs': []
            }
    
    def _analyze_product_context_token(self, token, doc) -> Dict[str, Any]:
        """
        Analyze product context for a single token.
        """
        # Simplified version of _analyze_product_context for single tokens
        return {
            'software_context_score': 0.5,
            'business_context_score': 0.3,
            'technical_indicators': [],
            'action_verbs': []
        }
    
    def _construct_product_phrase(self, token) -> str:
        """
        Construct a product phrase from a token and its compounds.
        """
        try:
            phrase_tokens = [token.text]
            
            # Add compound modifiers
            for child in token.children:
                if child.dep_ == 'compound':
                    phrase_tokens.insert(0, child.text)
            
            return ' '.join(phrase_tokens)
        
        except Exception:
            return token.text if hasattr(token, 'text') else str(token)
    
    def _looks_like_product_name(self, phrase: str, doc) -> bool:
        """
        Check if a phrase looks like a product name using heuristics.
        """
        try:
            # Simple heuristics
            words = phrase.split()
            
            # Multi-word proper nouns are often products
            if len(words) > 1 and all(word[0].isupper() for word in words):
                return True
            
            # Contains product-indicating suffixes
            product_suffixes = ['Server', 'Client', 'Pro', 'Enterprise', 'Studio']
            if any(phrase.endswith(suffix) for suffix in product_suffixes):
                return True
            
            return False
        
        except Exception:
            return False
    
    def _calculate_product_context_score(self, entity, doc) -> float:
        """
        Calculate context score for product likelihood.
        """
        try:
            context_analysis = self._analyze_product_context(entity, doc)
            
            # Combine different context scores
            total_score = (
                context_analysis['software_context_score'] * 0.6 +
                context_analysis['business_context_score'] * 0.4
            )
            
            return min(total_score, 1.0)
        
        except Exception:
            return 0.0
    
    def _find_abbreviation_context_clues(self, entity, doc) -> Optional[Dict[str, Any]]:
        """
        Find context clues that indicate an entity is an abbreviation.
        """
        try:
            # Look for phrases like "IBM WebSphere Application Server (WAS)"
            # This is a simplified implementation
            sentence = entity.sent
            
            # Look for parentheses or expansion indicators
            for token in sentence:
                if token.text in ['(', 'formerly', 'also known as']:
                    # Found potential abbreviation context
                    return {
                        'expansion': 'potential_expansion',
                        'context_type': 'parenthetical'
                    }
            
            return None
        
        except Exception:
            return None
    
    def _is_problematic_abbreviation(self, abbrev_info: Dict[str, Any]) -> bool:
        """
        Check if an abbreviation is problematic.
        """
        try:
            # Simple heuristics for problematic abbreviations
            abbrev_text = abbrev_info.get('display_name', '')
            
            # Very short abbreviations without context
            if len(abbrev_text) <= 2:
                return True
            
            # Abbreviations with low confidence
            if abbrev_info.get('abbreviation_info', {}).get('confidence', 0.0) < 0.5:
                return True
            
            return False
        
        except Exception:
            return False
    
    def _analyze_naming_consistency(self, mentions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze consistency across product mentions.
        """
        try:
            # Group mentions by their display form
            form_groups = defaultdict(list)
            for mention in mentions:
                form_groups[mention['display_name']].append(mention)
            
            # If there's only one form, it's consistent
            if len(form_groups) <= 1:
                return {'has_inconsistencies': False, 'inconsistencies': []}
            
            # Determine the recommended form (most common or most complete)
            recommended_form = max(form_groups.keys(), key=lambda x: len(form_groups[x]))
            
            # Find inconsistencies
            inconsistencies = []
            for form, mentions_list in form_groups.items():
                if form != recommended_form:
                    inconsistencies.append({
                        'variant': form,
                        'pattern_type': 'inconsistent_naming',
                        'suggestions': [f"Use consistent form: '{recommended_form}'"]
                    })
            
            return {
                'has_inconsistencies': len(inconsistencies) > 0,
                'inconsistencies': inconsistencies,
                'recommended_form': recommended_form
            }
        
        except Exception:
            return {'has_inconsistencies': False, 'inconsistencies': []}
    
    def _generate_brand_prefix_suggestions(self, product_name: str) -> List[str]:
        """
        Generate suggestions for adding brand prefixes.
        """
        suggestions = []
        
        # Try to infer the likely brand based on product name patterns
        if any(indicator in product_name.lower() for indicator in ['db2', 'websphere', 'watson']):
            suggestions.append(f"Use 'IBM {product_name}' for first mention")
        else:
            suggestions.append(f"Add appropriate brand prefix: '[Brand] {product_name}'")
        
        suggestions.append("Specify the full product name including brand on first reference")
        
        return suggestions
    
    def _generate_abbreviation_correction_suggestions(self, abbreviation: str, full_name: str) -> List[str]:
        """
        Generate suggestions for correcting abbreviations.
        """
        suggestions = []
        
        suggestions.append(f"Use full product name: '{full_name}' instead of '{abbreviation}'")
        suggestions.append("Avoid unofficial abbreviations in formal documentation")
        
        if len(full_name) > 20:  # Very long names
            suggestions.append(f"If abbreviation is necessary, define it: '{full_name} ({abbreviation})'")
        
        return suggestions
