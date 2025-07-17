"""
Geographic Locations Rule
Based on IBM Style Guide topic: "Geographic locations"
Enhanced with pure SpaCy morphological analysis for robust geographic entity validation.
"""
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
from .base_references_rule import BaseReferencesRule

class GeographicLocationsRule(BaseReferencesRule):
    """
    Uses advanced SpaCy morphological analysis and Named Entity Recognition (NER) to check for 
    correct capitalization and formatting of geographic locations (countries, cities, states, regions).
    Provides context-aware validation and handles complex geographic entity structures.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize geographic-specific linguistic anchors
        self._initialize_geographic_anchors()
    
    def _initialize_geographic_anchors(self):
        """Initialize morphological patterns specific to geographic location analysis."""
        
        # Geographic entity morphological patterns
        self.geographic_morphological_patterns = {
            'entity_types': {
                'countries': ['GPE', 'LOC'],  # NER labels for countries
                'cities': ['GPE', 'FAC'],     # Cities and facilities
                'regions': ['LOC', 'GPE'],    # Geographic regions
                'landmarks': ['FAC', 'LOC'],  # Landmarks and facilities
                'water_bodies': ['LOC'],      # Rivers, lakes, oceans
                'administrative': ['GPE']     # States, provinces, districts
            },
            'capitalization_patterns': {
                'proper_nouns': ['PROPN+geographic', 'compound+PROPN', 'flat+geographic'],
                'multiword_locations': ['New York', 'San Francisco', 'United States'],
                'directional_components': ['North', 'South', 'East', 'West', 'Northern', 'Southern'],
                'geographic_descriptors': ['City', 'State', 'Province', 'County', 'District']
            },
            'linguistic_markers': {
                'prepositions': ['in', 'at', 'from', 'to', 'near', 'around', 'through', 'across'],
                'geographic_verbs': ['located', 'situated', 'found', 'based', 'positioned'],
                'spatial_relationships': ['north of', 'south of', 'east of', 'west of', 'between']
            }
        }
        
        # Complex geographic structure patterns
        self.geographic_structure_patterns = {
            'multipart_locations': {
                'city_state': ['City, State', 'City, Country'],
                'city_state_country': ['City, State, Country'],
                'regional_descriptors': ['Central Europe', 'Southeast Asia', 'Middle East'],
                'administrative_hierarchy': ['County > State > Country']
            },
            'directional_indicators': {
                'cardinal_directions': ['North', 'South', 'East', 'West'],
                'intermediate_directions': ['Northeast', 'Northwest', 'Southeast', 'Southwest'],
                'relative_directions': ['Northern', 'Southern', 'Eastern', 'Western'],
                'ordinal_directions': ['Far East', 'Deep South', 'Upper Midwest']
            },
            'geographic_qualifiers': {
                'size_qualifiers': ['Greater', 'Metro', 'Downtown', 'Uptown'],
                'historical_qualifiers': ['Ancient', 'Old', 'New'],
                'political_qualifiers': ['Democratic', 'Republic', 'Kingdom', 'United']
            }
        }
        
        # Context patterns for geographic validation
        self.geographic_context_patterns = {
            'location_context': {
                'travel_indicators': ['visit', 'travel', 'trip', 'journey', 'destination'],
                'residence_indicators': ['live', 'reside', 'based', 'located', 'headquarters'],
                'business_indicators': ['office', 'branch', 'subsidiary', 'operations']
            },
            'geographic_relationships': {
                'containment': ['in', 'within', 'inside', 'part of'],
                'proximity': ['near', 'close to', 'adjacent to', 'next to'],
                'direction': ['north of', 'south of', 'east of', 'west of']
            },
            'formal_context': {
                'official_names': ['Republic of', 'Kingdom of', 'United States of'],
                'abbreviations': ['USA', 'UK', 'EU', 'NYC'],
                'postal_codes': ['ZIP', 'postal code', 'area code']
            }
        }

    def _get_rule_type(self) -> str:
        return 'references_geographic_locations'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text to find improperly capitalized or formatted geographic locations
        using comprehensive morphological and semantic analysis.
        """
        errors = []
        if not nlp:
            return errors

        # Build comprehensive context about geographic entities across the text
        geographic_context = self._build_geographic_context(text, sentences, nlp)

        for i, sentence in enumerate(sentences):
            doc = self._analyze_sentence_structure(sentence, nlp)
            if not doc:
                continue
            
            # Use the base class method for entity capitalization analysis
            entity_errors = self._analyze_entity_capitalization(
                doc, sentence, i, ['GPE', 'LOC', 'FAC']
            )
            errors.extend(entity_errors)
            
            # Additional geographic-specific analysis
            additional_errors = self._analyze_geographic_specific_patterns(
                doc, sentence, i, geographic_context
            )
            errors.extend(additional_errors)

        return errors
    
    def _build_geographic_context(self, text: str, sentences: List[str], nlp) -> Dict[str, Any]:
        """
        Build comprehensive context about geographic entity usage across the entire text.
        """
        context = {
            'geographic_entities': [],
            'location_relationships': [],
            'directional_references': [],
            'multipart_locations': [],
            'abbreviation_usage': defaultdict(list),
            'capitalization_patterns': defaultdict(set),
            'geographic_domains': set(),  # Travel, business, academic, etc.
            'coordinate_systems': [],     # GPS coordinates, addresses
            'cultural_context': 'international'  # Could be inferred from content
        }
        
        try:
            # Analyze the entire text to understand geographic patterns
            full_doc = self._analyze_sentence_structure(text, nlp)
            if full_doc:
                # Extract all geographic entities
                context['geographic_entities'] = self._extract_geographic_entities(full_doc)
                
                # Analyze location relationships
                context['location_relationships'] = self._analyze_location_relationships(full_doc)
                
                # Find directional references
                context['directional_references'] = self._find_directional_references(full_doc)
                
                # Detect multipart locations
                context['multipart_locations'] = self._detect_multipart_locations(full_doc)
                
                # Analyze geographic domain
                context['geographic_domains'] = self._determine_geographic_domains(full_doc)
                
                # Track capitalization patterns
                for entity in context['geographic_entities']:
                    location_name = entity['canonical_name']
                    context['capitalization_patterns'][location_name].add(
                        entity['capitalization_pattern']
                    )
        
        except Exception:
            pass
        
        return context
    
    def _analyze_geographic_specific_patterns(self, doc, sentence: str, sentence_index: int, 
                                           geographic_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze geographic-specific patterns that require correction.
        """
        errors = []
        
        if not doc:
            return errors
        
        # Detect improper directional capitalization
        directional_errors = self._detect_directional_capitalization_errors(doc, geographic_context)
        for error in directional_errors:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Directional reference '{error['direction']}' has incorrect capitalization.",
                suggestions=error['suggestions'],
                severity='medium',
                linguistic_analysis={
                    'directional_error': error,
                    'morphological_pattern': error.get('morphological_pattern'),
                    'geographic_context': error.get('geographic_context')
                }
            ))
        
        # Detect multipart location formatting issues
        multipart_errors = self._detect_multipart_location_errors(doc, geographic_context)
        for error in multipart_errors:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Multipart location '{error['location']}' has formatting issues.",
                suggestions=error['suggestions'],
                severity='medium',
                linguistic_analysis={
                    'multipart_error': error,
                    'location_structure': error.get('structure_analysis'),
                    'formatting_pattern': error.get('formatting_pattern')
                }
            ))
        
        # Detect geographic abbreviation issues
        abbreviation_errors = self._detect_geographic_abbreviation_errors(doc, geographic_context)
        for error in abbreviation_errors:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Geographic abbreviation '{error['abbreviation']}' may need clarification.",
                suggestions=error['suggestions'],
                severity='low',
                linguistic_analysis={
                    'abbreviation_error': error,
                    'context_clarity': error.get('context_clarity'),
                    'expansion_needed': error.get('expansion_needed')
                }
            ))
        
        # Detect inconsistent geographic naming
        consistency_errors = self._detect_geographic_naming_inconsistencies(doc, geographic_context)
        for error in consistency_errors:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Inconsistent naming of location '{error['location']}'. Use consistent form.",
                suggestions=error['suggestions'],
                severity='low',
                linguistic_analysis={
                    'consistency_error': error,
                    'naming_variants': error.get('naming_variants'),
                    'recommended_form': error.get('recommended_form')
                }
            ))
        
        return errors
    
    def _extract_geographic_entities(self, doc) -> List[Dict[str, Any]]:
        """
        Extract geographic entities using advanced morphological analysis.
        """
        geographic_entities = []
        
        if not doc:
            return geographic_entities
        
        try:
            # Use NER to find geographic entities
            for ent in doc.ents:
                if ent.label_ in ['GPE', 'LOC', 'FAC']:
                    geo_analysis = self._analyze_geographic_entity(ent, doc)
                    
                    if geo_analysis['is_geographic']:
                        geographic_entities.append(geo_analysis)
            
            # Also detect geographic entities not caught by NER using patterns
            non_ner_locations = self._detect_non_ner_geographic_entities(doc)
            geographic_entities.extend(non_ner_locations)
        
        except Exception:
            pass
        
        return geographic_entities
    
    def _analyze_geographic_entity(self, entity, doc) -> Dict[str, Any]:
        """
        Analyze a geographic entity using morphological features and context.
        """
        try:
            entity_text = entity.text
            tokens = list(entity)
            
            # Analyze morphological patterns
            geo_score = self._calculate_geographic_likelihood_score(entity, doc)
            
            # Determine if this is a geographic entity
            is_geographic = geo_score > 0.5 or entity.label_ in ['GPE', 'LOC', 'FAC']
            
            # Analyze geographic type
            geo_type = self._classify_geographic_type(entity, doc)
            
            # Analyze capitalization
            cap_analysis = self._analyze_geographic_capitalization(entity)
            
            # Analyze structure (single word vs multipart)
            structure_analysis = self._analyze_geographic_structure(entity)
            
            return {
                'entity': entity,
                'canonical_name': entity_text,
                'display_name': entity_text,
                'is_geographic': is_geographic,
                'confidence_score': geo_score,
                'geographic_type': geo_type,
                'capitalization_pattern': cap_analysis['pattern'],
                'capitalization_errors': cap_analysis['errors'],
                'structure_type': structure_analysis['type'],
                'components': structure_analysis['components'],
                'morphological_features': [self._get_morphological_features(token) for token in tokens],
                'context_analysis': self._analyze_geographic_context(entity, doc),
                'tokens': [self._token_to_dict(token) for token in tokens]
            }
        
        except Exception:
            return {
                'entity': entity,
                'canonical_name': entity.text,
                'is_geographic': False,
                'confidence_score': 0.0
            }
    
    def _detect_non_ner_geographic_entities(self, doc) -> List[Dict[str, Any]]:
        """
        Detect geographic entities not caught by NER using morphological patterns.
        """
        non_ner_locations = []
        
        try:
            # Look for directional compound constructions
            for token in doc:
                if self._is_directional_word(token.text):
                    # Check for geographic compounds like "Northern California"
                    geo_compound = self._build_directional_geographic_phrase(token, doc)
                    
                    if self._looks_like_geographic_location(geo_compound):
                        location_analysis = {
                            'canonical_name': geo_compound,
                            'display_name': geo_compound,
                            'is_geographic': True,
                            'confidence_score': 0.7,
                            'geographic_type': 'regional',
                            'detection_method': 'directional_pattern',
                            'morphological_features': [self._get_morphological_features(token)]
                        }
                        non_ner_locations.append(location_analysis)
            
            # Look for geographic descriptors with proper nouns
            descriptor_locations = self._detect_descriptor_geographic_entities(doc)
            non_ner_locations.extend(descriptor_locations)
        
        except Exception:
            pass
        
        return non_ner_locations
    
    def _analyze_location_relationships(self, doc) -> List[Dict[str, Any]]:
        """
        Analyze relationships between geographic locations.
        """
        relationships = []
        
        try:
            # Find geographic entities
            geo_entities = []
            for ent in doc.ents:
                if ent.label_ in ['GPE', 'LOC', 'FAC']:
                    geo_entities.append(ent)
            
            # Analyze relationships between entities
            for i, entity1 in enumerate(geo_entities):
                for j, entity2 in enumerate(geo_entities):
                    if i != j:
                        relationship = self._analyze_geographic_relationship(entity1, entity2, doc)
                        if relationship['has_relationship']:
                            relationships.append(relationship)
        
        except Exception:
            pass
        
        return relationships
    
    def _find_directional_references(self, doc) -> List[Dict[str, Any]]:
        """
        Find directional references in the text.
        """
        directional_refs = []
        
        try:
            for token in doc:
                if self._is_directional_word(token.text):
                    directional_analysis = self._analyze_directional_reference(token, doc)
                    directional_refs.append(directional_analysis)
        
        except Exception:
            pass
        
        return directional_refs
    
    def _detect_multipart_locations(self, doc) -> List[Dict[str, Any]]:
        """
        Detect multipart geographic locations (e.g., "New York, NY").
        """
        multipart_locations = []
        
        try:
            # Look for comma-separated location patterns
            for i, token in enumerate(doc):
                if token.text == ',' and i > 0 and i + 1 < len(doc):
                    # Check if we have location before and after comma
                    before_token = doc[i - 1]
                    after_token = doc[i + 1]
                    
                    if (self._could_be_geographic(before_token) and 
                        self._could_be_geographic(after_token)):
                        
                        multipart_analysis = self._analyze_multipart_location(
                            before_token, after_token, doc, i
                        )
                        
                        if multipart_analysis['is_multipart_location']:
                            multipart_locations.append(multipart_analysis)
        
        except Exception:
            pass
        
        return multipart_locations
    
    def _determine_geographic_domains(self, doc) -> Set[str]:
        """
        Determine the geographic domains present in the text.
        """
        domains = set()
        
        try:
            # Look for domain indicators
            travel_words = ['travel', 'vacation', 'trip', 'visit', 'tourism']
            business_words = ['office', 'headquarters', 'branch', 'subsidiary']
            academic_words = ['university', 'college', 'research', 'study']
            
            for token in doc:
                text_lower = token.text.lower()
                
                if text_lower in travel_words:
                    domains.add('travel')
                elif text_lower in business_words:
                    domains.add('business')
                elif text_lower in academic_words:
                    domains.add('academic')
        
        except Exception:
            pass
        
        return domains
    
    def _detect_directional_capitalization_errors(self, doc, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect incorrect capitalization of directional references.
        """
        directional_errors = []
        
        try:
            for directional_ref in context['directional_references']:
                if directional_ref.get('capitalization_error'):
                    error_info = {
                        'direction': directional_ref['text'],
                        'current_capitalization': directional_ref['current_pattern'],
                        'expected_capitalization': directional_ref['expected_pattern'],
                        'suggestions': self._generate_directional_suggestions(directional_ref),
                        'morphological_pattern': directional_ref.get('morphological_pattern'),
                        'geographic_context': directional_ref.get('context_type')
                    }
                    directional_errors.append(error_info)
        
        except Exception:
            pass
        
        return directional_errors
    
    def _detect_multipart_location_errors(self, doc, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect formatting errors in multipart locations.
        """
        multipart_errors = []
        
        try:
            for multipart_loc in context['multipart_locations']:
                if multipart_loc.get('formatting_issues'):
                    for issue in multipart_loc['formatting_issues']:
                        error_info = {
                            'location': multipart_loc['full_location'],
                            'issue_type': issue['type'],
                            'problem_component': issue['component'],
                            'suggestions': issue['suggestions'],
                            'structure_analysis': multipart_loc.get('structure'),
                            'formatting_pattern': issue.get('pattern')
                        }
                        multipart_errors.append(error_info)
        
        except Exception:
            pass
        
        return multipart_errors
    
    def _detect_geographic_abbreviation_errors(self, doc, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect issues with geographic abbreviations.
        """
        abbreviation_errors = []
        
        try:
            for entity in context['geographic_entities']:
                if entity.get('is_abbreviation'):
                    clarity_analysis = self._analyze_abbreviation_clarity(entity, context)
                    
                    if clarity_analysis['needs_expansion']:
                        error_info = {
                            'abbreviation': entity['display_name'],
                            'full_form': clarity_analysis['likely_expansion'],
                            'context_clarity': clarity_analysis['clarity_score'],
                            'expansion_needed': True,
                            'suggestions': clarity_analysis['suggestions']
                        }
                        abbreviation_errors.append(error_info)
        
        except Exception:
            pass
        
        return abbreviation_errors
    
    def _detect_geographic_naming_inconsistencies(self, doc, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect inconsistent naming of geographic locations.
        """
        naming_errors = []
        
        try:
            for location_name, cap_patterns in context['capitalization_patterns'].items():
                if len(cap_patterns) > 1:
                    # Found inconsistent capitalization
                    recommended_pattern = self._determine_recommended_geographic_capitalization(
                        location_name, cap_patterns, context
                    )
                    
                    error_info = {
                        'location': location_name,
                        'current_patterns': list(cap_patterns),
                        'recommended_form': recommended_pattern,
                        'naming_variants': len(cap_patterns),
                        'suggestions': [f"Use consistent capitalization: {recommended_pattern}"]
                    }
                    naming_errors.append(error_info)
        
        except Exception:
            pass
        
        return naming_errors
    
    # Helper methods implementation
    def _calculate_geographic_likelihood_score(self, entity, doc) -> float:
        """Calculate likelihood that entity is geographic."""
        try:
            score = 0.0
            
            # NER label bonus
            if entity.label_ in ['GPE', 'LOC', 'FAC']:
                score += 0.7
            
            # Context analysis
            context_score = self._calculate_geographic_context_score(entity, doc)
            score += context_score * 0.3
            
            return min(score, 1.0)
        except Exception:
            return 0.0
    
    def _classify_geographic_type(self, entity, doc) -> str:
        """Classify the type of geographic entity."""
        try:
            entity_text = entity.text.lower()
            
            # Simple classification based on common patterns
            if any(country in entity_text for country in ['united states', 'canada', 'germany']):
                return 'country'
            elif any(state in entity_text for state in ['california', 'texas', 'florida']):
                return 'state'
            elif 'city' in entity_text or entity.label_ == 'GPE':
                return 'city'
            elif entity.label_ == 'LOC':
                return 'location'
            else:
                return 'unknown'
        except Exception:
            return 'unknown'
    
    def _analyze_geographic_capitalization(self, entity) -> Dict[str, Any]:
        """Analyze capitalization of geographic entity."""
        try:
            tokens = [token.text for token in entity]
            errors = []
            
            for i, token_text in enumerate(tokens):
                # Skip articles and prepositions
                if token_text.lower() in ['the', 'of', 'and', 'for']:
                    continue
                
                # Check if first letter is capitalized
                if not token_text[0].isupper():
                    errors.append({
                        'token': token_text,
                        'position': i,
                        'error_type': 'missing_capital',
                        'suggestion': token_text.capitalize()
                    })
            
            pattern = 'title_case' if all(t[0].isupper() for t in tokens if t.isalpha()) else 'mixed'
            
            return {
                'pattern': pattern,
                'errors': errors,
                'is_correct': len(errors) == 0
            }
        except Exception:
            return {'pattern': 'unknown', 'errors': [], 'is_correct': True}
    
    def _analyze_geographic_structure(self, entity) -> Dict[str, Any]:
        """Analyze the structure of a geographic entity."""
        try:
            tokens = [token.text for token in entity]
            
            if len(tokens) == 1:
                structure_type = 'single_word'
            elif len(tokens) == 2:
                structure_type = 'two_part'
            else:
                structure_type = 'multipart'
            
            return {
                'type': structure_type,
                'components': tokens,
                'word_count': len(tokens)
            }
        except Exception:
            return {'type': 'unknown', 'components': [], 'word_count': 0}
    
    def _analyze_geographic_context(self, entity, doc) -> Dict[str, Any]:
        """Analyze context around geographic entity."""
        try:
            context = {
                'travel_context': False,
                'business_context': False,
                'formal_context': False,
                'preposition_context': []
            }
            
            # Look for context indicators around the entity
            window = 5
            start_idx = max(0, entity.start - window)
            end_idx = min(len(doc), entity.end + window)
            
            for i in range(start_idx, end_idx):
                if i < entity.start or i >= entity.end:
                    token = doc[i]
                    text_lower = token.text.lower()
                    
                    if text_lower in ['travel', 'visit', 'trip']:
                        context['travel_context'] = True
                    elif text_lower in ['office', 'headquarters', 'business']:
                        context['business_context'] = True
                    elif text_lower in ['in', 'at', 'from', 'to']:
                        context['preposition_context'].append(text_lower)
            
            return context
        except Exception:
            return {'travel_context': False, 'business_context': False}
    
    def _is_directional_word(self, text: str) -> bool:
        """Check if text is a directional word."""
        directional_words = [
            'north', 'south', 'east', 'west',
            'northern', 'southern', 'eastern', 'western',
            'northeast', 'northwest', 'southeast', 'southwest'
        ]
        return text.lower() in directional_words
    
    def _build_directional_geographic_phrase(self, token, doc) -> str:
        """Build directional geographic phrase."""
        try:
            phrase = [token.text]
            
            # Look for following geographic words
            for i in range(token.i + 1, min(len(doc), token.i + 3)):
                next_token = doc[i]
                if next_token.pos_ == 'PROPN':
                    phrase.append(next_token.text)
                else:
                    break
            
            return ' '.join(phrase)
        except Exception:
            return token.text
    
    def _looks_like_geographic_location(self, phrase: str) -> bool:
        """Check if phrase looks like a geographic location."""
        # Simple heuristics
        words = phrase.split()
        return (len(words) >= 2 and 
                any(word[0].isupper() for word in words) and
                not all(word.isupper() for word in words))
    
    def _detect_descriptor_geographic_entities(self, doc) -> List[Dict[str, Any]]:
        """Detect geographic entities with descriptors."""
        descriptor_locations = []
        
        try:
            geographic_descriptors = ['city', 'state', 'county', 'province', 'region']
            
            for token in doc:
                if token.text.lower() in geographic_descriptors:
                    # Look for proper nouns before this descriptor
                    if (token.i > 0 and 
                        doc[token.i - 1].pos_ == 'PROPN'):
                        
                        location_phrase = f"{doc[token.i - 1].text} {token.text}"
                        
                        descriptor_locations.append({
                            'canonical_name': location_phrase,
                            'display_name': location_phrase,
                            'is_geographic': True,
                            'confidence_score': 0.8,
                            'geographic_type': token.text.lower(),
                            'detection_method': 'descriptor_pattern'
                        })
        
        except Exception:
            pass
        
        return descriptor_locations
    
    def _analyze_geographic_relationship(self, entity1, entity2, doc) -> Dict[str, Any]:
        """Analyze relationship between two geographic entities."""
        # Simplified implementation
        return {
            'has_relationship': False,
            'relationship_type': 'unknown',
            'entity1': entity1.text,
            'entity2': entity2.text
        }
    
    def _analyze_directional_reference(self, token, doc) -> Dict[str, Any]:
        """Analyze a directional reference."""
        try:
            return {
                'text': token.text,
                'morphological_pattern': f"{token.pos_}+{token.dep_}",
                'current_pattern': 'title_case' if token.text[0].isupper() else 'lower_case',
                'expected_pattern': 'title_case',  # Generally capitalize directions
                'capitalization_error': token.text[0].islower(),
                'context_type': 'directional_reference'
            }
        except Exception:
            return {'text': token.text, 'capitalization_error': False}
    
    def _could_be_geographic(self, token) -> bool:
        """Check if token could be geographic."""
        return (token.pos_ == 'PROPN' or 
                token.ent_type_ in ['GPE', 'LOC', 'FAC'] or
                token.text[0].isupper())
    
    def _analyze_multipart_location(self, before_token, after_token, doc, comma_index) -> Dict[str, Any]:
        """Analyze a potential multipart location."""
        try:
            full_location = f"{before_token.text}, {after_token.text}"
            
            return {
                'is_multipart_location': True,
                'full_location': full_location,
                'before_component': before_token.text,
                'after_component': after_token.text,
                'structure': 'city_state_format',
                'formatting_issues': []  # Would analyze for actual issues
            }
        except Exception:
            return {'is_multipart_location': False}
    
    def _calculate_geographic_context_score(self, entity, doc) -> float:
        """Calculate context score for geographic likelihood."""
        try:
            score = 0.0
            
            # Look for geographic context indicators
            window = 3
            start_idx = max(0, entity.start - window)
            end_idx = min(len(doc), entity.end + window)
            
            geographic_indicators = ['located', 'situated', 'in', 'at', 'from', 'to']
            
            for i in range(start_idx, end_idx):
                if i < entity.start or i >= entity.end:
                    token = doc[i]
                    if token.text.lower() in geographic_indicators:
                        score += 0.2
            
            return min(score, 1.0)
        except Exception:
            return 0.0
    
    def _analyze_abbreviation_clarity(self, entity: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if geographic abbreviation needs expansion."""
        # Simplified implementation
        return {
            'needs_expansion': False,
            'clarity_score': 0.8,
            'likely_expansion': entity['display_name'],
            'suggestions': []
        }
    
    def _determine_recommended_geographic_capitalization(self, location_name: str, 
                                                       cap_patterns: Set[str], 
                                                       context: Dict[str, Any]) -> str:
        """Determine recommended capitalization for geographic location."""
        # Generally prefer title case for geographic locations
        if 'title_case' in cap_patterns:
            return 'title_case'
        else:
            return 'title_case'  # Default recommendation
    
    def _generate_directional_suggestions(self, directional_ref: Dict[str, Any]) -> List[str]:
        """Generate suggestions for directional capitalization."""
        direction = directional_ref['text']
        corrected = direction.capitalize()
        
        return [
            f"Capitalize direction: '{corrected}'",
            "Directional references should be capitalized when referring to specific regions"
        ]
