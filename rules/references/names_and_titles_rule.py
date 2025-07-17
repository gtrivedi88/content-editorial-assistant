"""
Names and Titles Rule
Based on IBM Style Guide topic: "Names and titles"
Enhanced with pure SpaCy morphological analysis for robust title and name analysis.
"""
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
from .base_references_rule import BaseReferencesRule

class NamesAndTitlesRule(BaseReferencesRule):
    """
    Checks for correct capitalization of professional titles using advanced morphological analysis,
    dependency parsing for name-title relationships, and context-aware capitalization rules.
    Distinguishes between titles used with names vs. standalone usage.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize title-specific linguistic anchors
        self._initialize_title_name_anchors()
    
    def _initialize_title_name_anchors(self):
        """Initialize morphological patterns specific to professional title and name analysis."""
        
        # Professional title morphological patterns
        self.title_morphological_patterns = {
            'executive_titles': {
                'c_level': ['CEO', 'CTO', 'CFO', 'COO', 'CISO', 'CMO', 'CIO'],
                'vice_presidents': ['Vice President', 'VP', 'Senior Vice President', 'Executive Vice President'],
                'directors': ['Director', 'Managing Director', 'Executive Director', 'Senior Director'],
                'morphological_indicators': ['PROPN+title', 'compound+PROPN', 'appos+PERSON']
            },
            'management_titles': {
                'managers': ['Manager', 'Senior Manager', 'Team Manager', 'Project Manager'],
                'supervisors': ['Supervisor', 'Team Lead', 'Lead', 'Team Leader'],
                'coordinators': ['Coordinator', 'Program Coordinator', 'Project Coordinator'],
                'specialists': ['Specialist', 'Senior Specialist', 'Principal Specialist']
            },
            'technical_titles': {
                'engineers': ['Engineer', 'Software Engineer', 'Systems Engineer', 'Principal Engineer'],
                'developers': ['Developer', 'Software Developer', 'Senior Developer', 'Lead Developer'],
                'architects': ['Architect', 'Solution Architect', 'Technical Architect', 'Enterprise Architect'],
                'analysts': ['Analyst', 'Business Analyst', 'Systems Analyst', 'Data Analyst']
            },
            'academic_titles': {
                'professors': ['Professor', 'Associate Professor', 'Assistant Professor', 'Adjunct Professor'],
                'doctors': ['Doctor', 'Dr', 'MD', 'PhD', 'Ph.D.'],
                'researchers': ['Researcher', 'Research Scientist', 'Principal Researcher']
            }
        }
        
        # Title-name relationship patterns using dependency parsing
        self.title_name_relationships = {
            'with_name_patterns': {
                'dependency_relations': ['appos', 'nmod', 'compound', 'flat'],  # Title modifying name
                'position_patterns': ['before_name', 'after_name', 'appositive'],
                'capitalization_rule': 'title_case'  # Capitalize when with names
            },
            'standalone_patterns': {
                'dependency_relations': ['nsubj', 'dobj', 'pobj', 'attr'],  # Title as subject/object
                'grammatical_contexts': ['generic_reference', 'job_description', 'role_mention'],
                'capitalization_rule': 'sentence_case'  # Lowercase when standalone
            },
            'descriptive_patterns': {
                'dependency_relations': ['amod', 'attr', 'nmod'],  # Title as descriptor
                'contexts': ['job_posting', 'role_description', 'organizational_chart'],
                'capitalization_rule': 'contextual'  # Depends on usage
            }
        }
        
        # Context patterns for title identification and validation
        self.title_context_patterns = {
            'name_indicators': {
                'person_markers': ['Mr', 'Ms', 'Mrs', 'Dr', 'Prof'],
                'name_patterns': ['FirstName LastName', 'LastName, FirstName'],
                'morphological_cues': ['PERSON+NER', 'PROPN+PROPN', 'title+NAME']
            },
            'organizational_context': {
                'company_indicators': ['company', 'organization', 'corporation', 'firm'],
                'department_indicators': ['department', 'division', 'team', 'group'],
                'hierarchical_indicators': ['reports to', 'manages', 'leads', 'oversees']
            },
            'formal_context': {
                'document_types': ['resume', 'biography', 'announcement', 'introduction'],
                'formal_indicators': ['appointed', 'promoted', 'named', 'elected'],
                'ceremony_contexts': ['presentation', 'award', 'recognition', 'ceremony']
            }
        }
        
        # Capitalization rules based on context
        self.capitalization_rules = {
            'with_proper_names': {
                'rule': 'title_case',
                'examples': ['Director Smith', 'Chief Executive Officer Johnson'],
                'exceptions': ['articles', 'conjunctions', 'short_prepositions']
            },
            'standalone_generic': {
                'rule': 'sentence_case',
                'examples': ['the director', 'a manager', 'chief executive officer'],
                'contexts': ['generic_reference', 'job_description']
            },
            'formal_standalone': {
                'rule': 'title_case',
                'examples': ['the Director will speak', 'our Chief Executive Officer'],
                'contexts': ['formal_reference', 'organizational_communication']
            }
        }

    def _get_rule_type(self) -> str:
        return 'references_names_titles'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for incorrect capitalization of professional titles using comprehensive
        morphological and dependency analysis.
        """
        errors = []
        if not nlp:
            return errors

        # Build comprehensive context about titles and names across the text
        title_name_context = self._build_title_name_context(text, sentences, nlp)

        for i, sentence in enumerate(sentences):
            doc = self._analyze_sentence_structure(sentence, nlp)
            if not doc:
                continue
            
            # Use the base class method for title-name relationship analysis
            title_errors = self._analyze_title_name_relationships(doc, sentence, i)
            errors.extend(title_errors)
            
            # Additional title-specific analysis
            additional_errors = self._analyze_title_specific_patterns(doc, sentence, i, title_name_context)
            errors.extend(additional_errors)

        return errors
    
    def _build_title_name_context(self, text: str, sentences: List[str], nlp) -> Dict[str, Any]:
        """
        Build comprehensive context about title and name usage across the entire text.
        """
        context = {
            'person_entities': [],
            'title_entities': [],
            'title_name_pairs': [],
            'document_formality': 'formal',  # Could be inferred from content
            'organizational_context': False,
            'title_usage_patterns': defaultdict(list),
            'capitalization_patterns': defaultdict(set)
        }
        
        try:
            # Analyze the entire text to understand title and name patterns
            full_doc = self._analyze_sentence_structure(text, nlp)
            if full_doc:
                # Extract all person entities
                context['person_entities'] = self._extract_person_entities(full_doc)
                
                # Extract all title entities
                context['title_entities'] = self._extract_title_entities(full_doc)
                
                # Find title-name relationships
                context['title_name_pairs'] = self._find_all_title_name_relationships(full_doc)
                
                # Analyze document formality
                context['document_formality'] = self._determine_document_formality(full_doc)
                
                # Track usage patterns
                for title_entity in context['title_entities']:
                    title_text = title_entity['canonical_title']
                    context['title_usage_patterns'][title_text].append(title_entity)
                    context['capitalization_patterns'][title_text].add(title_entity['capitalization_pattern'])
        
        except Exception:
            pass
        
        return context
    
    def _analyze_title_specific_patterns(self, doc, sentence: str, sentence_index: int, title_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze title-specific capitalization patterns that require correction.
        """
        errors = []
        
        if not doc:
            return errors
        
        # Detect incorrect title capitalization with names
        title_name_errors = self._detect_title_capitalization_with_names(doc, title_context)
        for error in title_name_errors:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Title '{error['title']}' with name '{error['name']}' should use title case.",
                suggestions=error['suggestions'],
                severity='medium',
                linguistic_analysis={
                    'title_name_error': error,
                    'dependency_analysis': error.get('dependency_analysis'),
                    'morphological_pattern': error.get('morphological_pattern')
                }
            ))
        
        # Detect incorrect standalone title capitalization
        standalone_errors = self._detect_standalone_title_capitalization(doc, title_context)
        for error in standalone_errors:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Standalone title '{error['title']}' should use sentence case.",
                suggestions=error['suggestions'],
                severity='medium',
                linguistic_analysis={
                    'standalone_error': error,
                    'context_analysis': error.get('context_analysis'),
                    'grammatical_role': error.get('grammatical_role')
                }
            ))
        
        # Detect inconsistent title capitalization
        consistency_errors = self._detect_title_capitalization_inconsistencies(doc, title_context)
        for error in consistency_errors:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Inconsistent capitalization of title '{error['title']}'. Use consistent style.",
                suggestions=error['suggestions'],
                severity='low',
                linguistic_analysis={
                    'consistency_error': error,
                    'usage_patterns': error.get('usage_patterns')
                }
            ))
        
        return errors
    
    def _extract_person_entities(self, doc) -> List[Dict[str, Any]]:
        """
        Extract person entities using advanced morphological analysis.
        """
        person_entities = []
        
        if not doc:
            return person_entities
        
        try:
            for ent in doc.ents:
                if ent.label_ == 'PERSON':
                    person_analysis = self._analyze_person_entity(ent, doc)
                    person_entities.append(person_analysis)
            
            # Also detect persons not caught by NER using morphological patterns
            non_ner_persons = self._detect_non_ner_persons(doc)
            person_entities.extend(non_ner_persons)
        
        except Exception:
            pass
        
        return person_entities
    
    def _extract_title_entities(self, doc) -> List[Dict[str, Any]]:
        """
        Extract professional title entities using morphological pattern matching.
        """
        title_entities = []
        
        if not doc:
            return title_entities
        
        try:
            # Use pattern matching to find professional titles
            for token in doc:
                title_analysis = self._analyze_token_as_title(token, doc)
                
                if title_analysis['is_title']:
                    title_entities.append(title_analysis)
            
            # Look for multi-word titles using dependency patterns
            multi_word_titles = self._detect_multi_word_titles(doc)
            title_entities.extend(multi_word_titles)
        
        except Exception:
            pass
        
        return title_entities
    
    def _find_all_title_name_relationships(self, doc) -> List[Dict[str, Any]]:
        """
        Find all title-name relationships using dependency parsing.
        """
        relationships = []
        
        if not doc:
            return relationships
        
        try:
            # Find relationships between titles and names
            for ent in doc.ents:
                if ent.label_ == 'PERSON':
                    # Look for associated titles
                    associated_titles = self._find_titles_for_person(ent, doc)
                    
                    for title_info in associated_titles:
                        relationship = {
                            'person': self._entity_to_dict(ent),
                            'title': title_info,
                            'relationship_type': title_info['relationship_type'],
                            'dependency_pattern': title_info['dependency_pattern'],
                            'morphological_context': {
                                'person_features': [self._get_morphological_features(token) for token in ent],
                                'title_features': title_info.get('morphological_features', [])
                            }
                        }
                        relationships.append(relationship)
        
        except Exception:
            pass
        
        return relationships
    
    def _analyze_person_entity(self, entity, doc) -> Dict[str, Any]:
        """
        Analyze a person entity and its morphological context.
        """
        try:
            return {
                'entity': entity,
                'name': entity.text,
                'tokens': [self._token_to_dict(token) for token in entity],
                'morphological_features': [self._get_morphological_features(token) for token in entity],
                'context_analysis': self._analyze_person_context(entity, doc),
                'name_structure': self._analyze_name_structure(entity)
            }
        
        except Exception:
            return {
                'entity': entity,
                'name': entity.text,
                'tokens': [],
                'morphological_features': []
            }
    
    def _detect_non_ner_persons(self, doc) -> List[Dict[str, Any]]:
        """
        Detect person names not caught by NER using morphological patterns.
        """
        non_ner_persons = []
        
        try:
            # Look for proper noun sequences that might be names
            for i, token in enumerate(doc):
                if (token.pos_ == 'PROPN' and 
                    i + 1 < len(doc) and 
                    doc[i + 1].pos_ == 'PROPN'):
                    
                    # Potential two-word name
                    name_candidate = f"{token.text} {doc[i + 1].text}"
                    
                    if self._looks_like_person_name(name_candidate, doc):
                        non_ner_persons.append({
                            'name': name_candidate,
                            'tokens': [self._token_to_dict(token), self._token_to_dict(doc[i + 1])],
                            'confidence': 0.7,
                            'detection_method': 'morphological_pattern'
                        })
        
        except Exception:
            pass
        
        return non_ner_persons
    
    def _analyze_token_as_title(self, token, doc) -> Dict[str, Any]:
        """
        Analyze if a token represents a professional title.
        """
        try:
            analysis = {
                'is_title': False,
                'title_text': token.text,
                'canonical_title': '',
                'title_category': '',
                'confidence_score': 0.0,
                'capitalization_pattern': '',
                'context_type': '',
                'morphological_features': self._get_morphological_features(token)
            }
            
            # Check against known title patterns
            title_score = self._calculate_title_likelihood_score(token, doc)
            
            if title_score > 0.6:
                analysis['is_title'] = True
                analysis['confidence_score'] = title_score
                analysis['canonical_title'] = self._normalize_title_text(token.text)
                analysis['title_category'] = self._categorize_title(token.text)
                analysis['capitalization_pattern'] = self._analyze_title_capitalization_pattern(token)
                analysis['context_type'] = self._determine_title_context_type(token, doc)
            
            return analysis
        
        except Exception:
            return {
                'is_title': False,
                'title_text': token.text,
                'confidence_score': 0.0
            }
    
    def _detect_multi_word_titles(self, doc) -> List[Dict[str, Any]]:
        """
        Detect multi-word professional titles using dependency patterns.
        """
        multi_word_titles = []
        
        try:
            # Look for compound title constructions
            for token in doc:
                if self._is_potential_title_word(token.text):
                    # Build multi-word title from dependencies
                    title_phrase = self._build_title_phrase(token, doc)
                    
                    if len(title_phrase.split()) > 1:
                        title_analysis = {
                            'is_title': True,
                            'title_text': title_phrase,
                            'canonical_title': self._normalize_title_text(title_phrase),
                            'title_category': self._categorize_title(title_phrase),
                            'confidence_score': 0.8,
                            'detection_method': 'multi_word_pattern',
                            'morphological_features': [self._get_morphological_features(token)]
                        }
                        multi_word_titles.append(title_analysis)
        
        except Exception:
            pass
        
        return multi_word_titles
    
    def _find_titles_for_person(self, person_entity, doc) -> List[Dict[str, Any]]:
        """
        Find professional titles associated with a person using dependency parsing.
        """
        associated_titles = []
        
        try:
            # Look for titles in appositive relationships
            for token in person_entity:
                # Check for appositive modifiers
                for child in token.children:
                    if child.dep_ == 'appos' and self._is_potential_title_word(child.text):
                        title_info = {
                            'title_text': child.text,
                            'relationship_type': 'appositive',
                            'dependency_pattern': 'appos',
                            'position': 'after_name',
                            'morphological_features': [self._get_morphological_features(child)]
                        }
                        associated_titles.append(title_info)
                
                # Check for compound titles (titles before names)
                if token.dep_ == 'compound' and self._is_potential_title_word(token.head.text):
                    title_info = {
                        'title_text': token.head.text,
                        'relationship_type': 'compound',
                        'dependency_pattern': 'compound',
                        'position': 'before_name',
                        'morphological_features': [self._get_morphological_features(token.head)]
                    }
                    associated_titles.append(title_info)
            
            # Look for titles in nearby context
            context_titles = self._find_contextual_titles(person_entity, doc)
            associated_titles.extend(context_titles)
        
        except Exception:
            pass
        
        return associated_titles
    
    def _calculate_title_likelihood_score(self, token, doc) -> float:
        """
        Calculate likelihood that token represents a professional title.
        """
        try:
            score = 0.0
            text = token.text.lower()
            
            # Check against known title patterns
            all_titles = []
            for category in self.title_morphological_patterns.values():
                for title_list in category.values():
                    if isinstance(title_list, list):
                        all_titles.extend([t.lower() for t in title_list])
            
            if text in all_titles:
                score += 0.8
            
            # Check for title-like suffixes
            title_suffixes = ['manager', 'director', 'officer', 'engineer', 'analyst']
            if any(text.endswith(suffix) for suffix in title_suffixes):
                score += 0.6
            
            # Check morphological patterns
            if token.pos_ in ['NOUN', 'PROPN']:
                score += 0.2
            
            # Check context
            context_score = self._calculate_title_context_score(token, doc)
            score += context_score * 0.4
            
            return min(score, 1.0)
        
        except Exception:
            return 0.0
    
    def _detect_title_capitalization_with_names(self, doc, title_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect incorrect title capitalization when used with names.
        """
        capitalization_errors = []
        
        try:
            for relationship in title_context['title_name_pairs']:
                title_info = relationship['title']
                person_info = relationship['person']
                
                # Check if title with name should be title case
                if self._should_be_title_case_with_name(title_info, person_info, relationship):
                    current_cap = self._get_current_capitalization(title_info['title_text'])
                    
                    if current_cap != 'title_case':
                        suggestions = self._generate_title_case_suggestions(
                            title_info['title_text'], person_info['text']
                        )
                        
                        capitalization_errors.append({
                            'title': title_info['title_text'],
                            'name': person_info['text'],
                            'current_capitalization': current_cap,
                            'expected_capitalization': 'title_case',
                            'suggestions': suggestions,
                            'dependency_analysis': relationship.get('dependency_pattern'),
                            'morphological_pattern': f"title+name:{relationship['relationship_type']}"
                        })
        
        except Exception:
            pass
        
        return capitalization_errors
    
    def _detect_standalone_title_capitalization(self, doc, title_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect incorrect capitalization of standalone titles.
        """
        standalone_errors = []
        
        try:
            for title_entity in title_context['title_entities']:
                if title_entity['context_type'] == 'standalone':
                    # Check if standalone title should be sentence case
                    if self._should_be_sentence_case_standalone(title_entity, title_context):
                        current_cap = self._get_current_capitalization(title_entity['title_text'])
                        
                        if current_cap != 'sentence_case':
                            suggestions = self._generate_sentence_case_suggestions(title_entity['title_text'])
                            
                            standalone_errors.append({
                                'title': title_entity['title_text'],
                                'current_capitalization': current_cap,
                                'expected_capitalization': 'sentence_case',
                                'suggestions': suggestions,
                                'context_analysis': title_entity.get('context_type'),
                                'grammatical_role': title_entity.get('grammatical_role', 'unknown')
                            })
        
        except Exception:
            pass
        
        return standalone_errors
    
    def _detect_title_capitalization_inconsistencies(self, doc, title_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect inconsistent capitalization of the same title across the document.
        """
        consistency_errors = []
        
        try:
            for title_text, usage_patterns in title_context['title_usage_patterns'].items():
                if len(usage_patterns) > 1:
                    # Check for inconsistencies in capitalization
                    cap_patterns = title_context['capitalization_patterns'][title_text]
                    
                    if len(cap_patterns) > 1:
                        # Found inconsistent capitalization
                        recommended_pattern = self._determine_recommended_capitalization(
                            title_text, usage_patterns, title_context
                        )
                        
                        for usage in usage_patterns:
                            if usage.get('capitalization_pattern') != recommended_pattern:
                                suggestions = self._generate_consistency_suggestions(
                                    title_text, recommended_pattern
                                )
                                
                                consistency_errors.append({
                                    'title': title_text,
                                    'current_pattern': usage.get('capitalization_pattern'),
                                    'recommended_pattern': recommended_pattern,
                                    'suggestions': suggestions,
                                    'usage_patterns': len(usage_patterns)
                                })
        
        except Exception:
            pass
        
        return consistency_errors
    
    # Helper methods implementation
    def _determine_document_formality(self, doc) -> str:
        """Determine document formality level."""
        # Simplified implementation
        return 'formal'
    
    def _analyze_person_context(self, entity, doc) -> Dict[str, Any]:
        """Analyze context around a person entity."""
        return {
            'formal_context': True,
            'professional_context': True,
            'organizational_context': False
        }
    
    def _analyze_name_structure(self, entity) -> Dict[str, Any]:
        """Analyze the structure of a person's name."""
        try:
            tokens = [token.text for token in entity]
            return {
                'num_components': len(tokens),
                'has_title_prefix': len(tokens) > 2 and tokens[0] in ['Mr', 'Ms', 'Dr'],
                'pattern': 'first_last' if len(tokens) == 2 else 'complex'
            }
        except Exception:
            return {'num_components': 1, 'pattern': 'simple'}
    
    def _looks_like_person_name(self, name_candidate: str, doc) -> bool:
        """Check if text looks like a person name."""
        # Simple heuristics
        words = name_candidate.split()
        return len(words) == 2 and all(word[0].isupper() for word in words)
    
    def _normalize_title_text(self, title_text: str) -> str:
        """Normalize title text to canonical form."""
        return title_text.strip()
    
    def _categorize_title(self, title_text: str) -> str:
        """Categorize a title into a broad category."""
        text_lower = title_text.lower()
        
        if any(exec_title in text_lower for exec_title in ['ceo', 'cto', 'cfo', 'president']):
            return 'executive'
        elif any(mgmt_title in text_lower for mgmt_title in ['manager', 'director', 'supervisor']):
            return 'management'
        elif any(tech_title in text_lower for tech_title in ['engineer', 'developer', 'architect']):
            return 'technical'
        else:
            return 'general'
    
    def _analyze_title_capitalization_pattern(self, token) -> str:
        """Analyze current capitalization pattern of a title."""
        text = token.text
        
        if text.isupper():
            return 'all_caps'
        elif text.islower():
            return 'all_lower'
        elif text[0].isupper() and text[1:].islower():
            return 'title_case'
        else:
            return 'mixed_case'
    
    def _determine_title_context_type(self, token, doc) -> str:
        """Determine the context type of a title usage."""
        # Look for nearby person entities or names
        window = 3
        
        for i in range(max(0, token.i - window), min(len(doc), token.i + window + 1)):
            if i != token.i:
                nearby_token = doc[i]
                if nearby_token.ent_type_ == 'PERSON':
                    return 'with_name'
        
        return 'standalone'
    
    def _is_potential_title_word(self, text: str) -> bool:
        """Check if text could be part of a professional title."""
        text_lower = text.lower()
        title_words = ['manager', 'director', 'officer', 'engineer', 'analyst', 'specialist', 
                       'coordinator', 'supervisor', 'architect', 'developer', 'president']
        return text_lower in title_words
    
    def _build_title_phrase(self, token, doc) -> str:
        """Build multi-word title phrase from dependencies."""
        try:
            phrase_tokens = [token.text]
            
            # Add compound modifiers
            for child in token.children:
                if child.dep_ in ['compound', 'amod']:
                    phrase_tokens.insert(0, child.text)
            
            return ' '.join(phrase_tokens)
        except Exception:
            return token.text
    
    def _find_contextual_titles(self, person_entity, doc) -> List[Dict[str, Any]]:
        """Find titles in contextual proximity to a person."""
        contextual_titles = []
        
        try:
            # Look for titles in a window around the person
            window = 5
            start_idx = max(0, person_entity.start - window)
            end_idx = min(len(doc), person_entity.end + window)
            
            for i in range(start_idx, end_idx):
                if i < person_entity.start or i >= person_entity.end:
                    token = doc[i]
                    if self._is_potential_title_word(token.text):
                        title_info = {
                            'title_text': token.text,
                            'relationship_type': 'contextual',
                            'dependency_pattern': 'proximity',
                            'position': 'before_name' if i < person_entity.start else 'after_name',
                            'morphological_features': [self._get_morphological_features(token)]
                        }
                        contextual_titles.append(title_info)
        
        except Exception:
            pass
        
        return contextual_titles
    
    def _calculate_title_context_score(self, token, doc) -> float:
        """Calculate context score for title likelihood."""
        score = 0.0
        
        # Look for organizational context
        window = 5
        for i in range(max(0, token.i - window), min(len(doc), token.i + window + 1)):
            if i != token.i:
                nearby_token = doc[i]
                if nearby_token.text.lower() in ['company', 'organization', 'department']:
                    score += 0.2
        
        return min(score, 1.0)
    
    def _should_be_title_case_with_name(self, title_info: Dict, person_info: Dict, relationship: Dict) -> bool:
        """Check if title with name should use title case."""
        # Generally, titles with names should be title case
        return relationship['relationship_type'] in ['appositive', 'compound']
    
    def _should_be_sentence_case_standalone(self, title_entity: Dict, context: Dict) -> bool:
        """Check if standalone title should use sentence case."""
        # Generally, standalone titles should be sentence case unless in formal context
        return context['document_formality'] != 'very_formal'
    
    def _get_current_capitalization(self, text: str) -> str:
        """Get current capitalization pattern of text."""
        if text.isupper():
            return 'all_caps'
        elif text.islower():
            return 'all_lower'
        elif text[0].isupper() and all(c.islower() for c in text[1:] if c.isalpha()):
            return 'title_case'
        else:
            return 'sentence_case'
    
    def _determine_recommended_capitalization(self, title_text: str, usage_patterns: List, context: Dict) -> str:
        """Determine recommended capitalization pattern."""
        # Simple heuristics - could be more sophisticated
        if any(usage.get('context_type') == 'with_name' for usage in usage_patterns):
            return 'title_case'
        else:
            return 'sentence_case'
    
    def _generate_title_case_suggestions(self, title: str, name: str) -> List[str]:
        """Generate suggestions for title case correction."""
        corrected_title = ' '.join(word.capitalize() for word in title.split())
        return [
            f"Use title case: '{corrected_title} {name}'",
            "Capitalize titles when used with names"
        ]
    
    def _generate_sentence_case_suggestions(self, title: str) -> List[str]:
        """Generate suggestions for sentence case correction."""
        words = title.split()
        corrected = words[0].lower() + ' ' + ' '.join(words[1:]) if len(words) > 1 else words[0].lower()
        return [
            f"Use sentence case: '{corrected}'",
            "Use lowercase for standalone titles in generic references"
        ]
    
    def _generate_consistency_suggestions(self, title: str, recommended_pattern: str) -> List[str]:
        """Generate suggestions for consistency correction."""
        return [
            f"Use consistent capitalization: {recommended_pattern}",
            f"Maintain consistent style for '{title}' throughout the document"
        ]
