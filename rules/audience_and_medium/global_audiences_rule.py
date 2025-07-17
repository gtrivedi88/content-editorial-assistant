"""
Global Audiences Rule
Based on IBM Style Guide topic: "Global audiences"
Enhanced with pure SpaCy morphological analysis for robust global accessibility detection.
"""
from typing import List, Dict, Any, Optional, Set, Tuple
from .base_audience_rule import BaseAudienceRule

class GlobalAudiencesRule(BaseAudienceRule):
    """
    Checks for constructs that are difficult for a global audience to understand,
    using advanced morphological and syntactic analysis to detect complexity patterns,
    negative constructions, and cultural/linguistic barriers.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize global audience-specific linguistic anchors
        self._initialize_global_audience_anchors()
    
    def _initialize_global_audience_anchors(self):
        """Initialize morphological patterns specific to global audience accessibility."""
        
        # Complexity thresholds based on IBM Style Guide recommendations
        self.global_accessibility_thresholds = {
            'max_sentence_length': 32,  # words per sentence
            'max_dependency_depth': 4,  # syntactic embedding depth
            'max_morphological_complexity': 2.0,  # average per sentence
            'max_syllables_per_word': 3,  # preferred for non-native speakers
            'max_clauses_per_sentence': 2  # number of independent/dependent clauses
        }
        
        # Morphological patterns that create difficulties for global audiences
        self.global_difficulty_patterns = {
            'negative_constructions': {
                'double_negatives': ['not+un', 'not+non', 'not+in', 'not+dis'],
                'indirect_negatives': ['fail to', 'lack of', 'absence of', 'without'],
                'complex_negatives': ['neither+nor', 'not only+but', 'hardly+any']
            },
            'complex_syntax': {
                'passive_with_agent': ['nsubjpass+agent'],  # "was done by X"
                'nested_clauses': ['ccomp+advcl', 'xcomp+ccomp'],
                'inverted_structures': ['expl+there', 'advmod+fronted']
            },
            'cultural_specifics': {
                'idiomatic_patterns': True,  # Detected via semantic analysis
                'cultural_references': True,  # Sports, food, customs
                'temporal_absolutes': ['always', 'never', 'every', 'all']
            }
        }
        
        # Morphologically-based simplification strategies
        self.simplification_strategies = {
            'sentence_splitting_markers': {
                'coordinating_conjunctions': ['and', 'but', 'or', 'so'],
                'subordinating_conjunctions': ['because', 'although', 'since', 'while'],
                'transitional_phrases': ['however', 'therefore', 'moreover', 'furthermore']
            },
            'positive_reformulations': {
                'negative_to_positive': {
                    'not different': 'similar',
                    'not uncommon': 'common',
                    'not unusual': 'normal',
                    'not impossible': 'possible',
                    'not insignificant': 'important'
                }
            }
        }

    def _get_rule_type(self) -> str:
        return 'audience_global'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for clarity issues affecting global audiences using
        comprehensive morphological and syntactic analysis.
        """
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = self._analyze_sentence_structure(sentence, nlp)
            if not doc:
                continue
            
            # Use the base class method for global accessibility analysis
            sentence_errors = self._analyze_global_accessibility(doc, sentence, i)
            errors.extend(sentence_errors)
            
            # Additional global audience-specific analysis
            additional_errors = self._analyze_global_specific_patterns(doc, sentence, i)
            errors.extend(additional_errors)

        return errors
    
    def _analyze_global_specific_patterns(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Analyze patterns specifically problematic for global audiences.
        """
        errors = []
        
        # Analyze lexical complexity beyond basic metrics
        lexical_complexity_issues = self._analyze_lexical_complexity_for_global_audience(doc)
        for issue in lexical_complexity_issues:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"The word '{issue['word']}' may be difficult for global audiences. Consider simpler alternatives.",
                suggestions=issue.get('suggestions', ["Use simpler, more common words."]),
                severity='low',
                linguistic_analysis={
                    'lexical_complexity': issue,
                    'morphological_analysis': issue.get('morphological_features')
                }
            ))
        
        # Analyze cultural specificity
        cultural_barriers = self._detect_cultural_specificity(doc)
        for barrier in cultural_barriers:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"'{barrier['text']}' may not be understood by global audiences.",
                suggestions=["Use more universal language or provide explanation."],
                severity='medium',
                linguistic_analysis={
                    'cultural_barrier': barrier,
                    'barrier_type': barrier.get('type')
                }
            ))
        
        # Analyze temporal and modal absolutes
        absolute_language = self._detect_absolute_language(doc)
        for absolute in absolute_language:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Absolute language like '{absolute['text']}' can be misunderstood across cultures.",
                suggestions=["Use more qualified language (e.g., 'often', 'typically', 'in most cases')."],
                severity='low',
                linguistic_analysis={
                    'absolute_language': absolute,
                    'morphological_pattern': absolute.get('morphological_pattern')
                }
            ))
        
        # Analyze syntactic complexity for non-native speakers
        syntactic_complexity = self._analyze_syntactic_complexity_for_global_audience(doc)
        if syntactic_complexity['complexity_score'] > 0.7:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="This sentence structure is too complex for global audiences.",
                suggestions=[
                    "Break into shorter sentences.",
                    "Use simpler sentence structures.",
                    "Reduce embedded clauses."
                ],
                severity='medium',
                linguistic_analysis=syntactic_complexity
            ))
        
        return errors
    
    def _analyze_lexical_complexity_for_global_audience(self, doc) -> List[Dict[str, Any]]:
        """
        Analyze lexical complexity specifically for global audience accessibility.
        """
        complex_words = []
        
        if not doc:
            return complex_words
        
        try:
            for token in doc:
                if not token.is_alpha or token.is_stop:
                    continue
                
                # Calculate multiple complexity indicators
                formality_score = self._analyze_formality_level(token)
                morphological_complexity = self._calculate_morphological_complexity(token)
                syllable_count = self._estimate_syllables_morphological(token)
                frequency_class = self._analyze_word_frequency_class(token, doc)
                
                # Check if word exceeds global audience thresholds
                is_too_complex = (
                    formality_score > 0.7 or
                    morphological_complexity > self.global_accessibility_thresholds['max_morphological_complexity'] or
                    syllable_count > self.global_accessibility_thresholds['max_syllables_per_word'] or
                    frequency_class in ['rare', 'very_rare']
                )
                
                if is_too_complex:
                    # Find simpler alternatives
                    simpler_alternatives = self._find_global_friendly_alternatives(token)
                    
                    complex_words.append({
                        'word': token.text,
                        'lemma': token.lemma_,
                        'formality_score': formality_score,
                        'morphological_complexity': morphological_complexity,
                        'syllable_count': syllable_count,
                        'frequency_class': frequency_class,
                        'suggestions': simpler_alternatives,
                        'morphological_features': self._get_morphological_features(token),
                        'semantic_field': self._analyze_semantic_field(token, doc)
                    })
        
        except Exception:
            pass
        
        return complex_words
    
    def _detect_cultural_specificity(self, doc) -> List[Dict[str, Any]]:
        """
        Detect culturally specific language that may not translate well globally.
        """
        cultural_barriers = []
        
        if not doc:
            return cultural_barriers
        
        try:
            # Detect idiomatic expressions using syntactic patterns
            idiomatic_patterns = self._detect_idiomatic_patterns(doc)
            for idiom in idiomatic_patterns:
                cultural_barriers.append({
                    'text': idiom['text'],
                    'type': 'idiom',
                    'morphological_pattern': idiom.get('pattern'),
                    'tokens': idiom.get('tokens')
                })
            
            # Detect cultural references using named entity recognition
            for ent in doc.ents:
                if ent.label_ in ['PERSON', 'ORG', 'EVENT', 'WORK_OF_ART']:
                    # Check if this might be culture-specific
                    if self._is_culture_specific_entity(ent):
                        cultural_barriers.append({
                            'text': ent.text,
                            'type': 'cultural_reference',
                            'entity_type': ent.label_,
                            'morphological_features': [self._get_morphological_features(token) for token in ent]
                        })
            
            # Detect measurement and format conventions
            format_specifics = self._detect_format_specificity(doc)
            cultural_barriers.extend(format_specifics)
        
        except Exception:
            pass
        
        return cultural_barriers
    
    def _detect_absolute_language(self, doc) -> List[Dict[str, Any]]:
        """
        Detect absolute language that can be problematic across cultures.
        """
        absolute_language = []
        
        if not doc:
            return absolute_language
        
        try:
            # Morphological patterns for absolute language
            absolute_indicators = {
                'universal_quantifiers': ['all', 'every', 'everyone', 'everything', 'always'],
                'negative_universals': ['never', 'nothing', 'no one', 'nowhere'],
                'exclusive_language': ['only', 'just', 'merely', 'simply'],
                'definitive_statements': ['must', 'will', 'definitely', 'certainly']
            }
            
            for token in doc:
                lemma = token.lemma_.lower()
                
                for category, indicators in absolute_indicators.items():
                    if lemma in indicators:
                        # Analyze the morphological context
                        morphological_context = self._analyze_absolute_context(token, doc)
                        
                        absolute_language.append({
                            'text': token.text,
                            'lemma': lemma,
                            'category': category,
                            'morphological_pattern': f"{token.pos_}+{token.dep_}",
                            'morphological_features': self._get_morphological_features(token),
                            'context_analysis': morphological_context
                        })
        
        except Exception:
            pass
        
        return absolute_language
    
    def _analyze_syntactic_complexity_for_global_audience(self, doc) -> Dict[str, Any]:
        """
        Analyze syntactic complexity specifically for global audience comprehension.
        """
        if not doc:
            return {'complexity_score': 0.0}
        
        try:
            # Enhanced complexity calculation for global audiences
            sentence_complexity = self._calculate_sentence_complexity(doc)
            
            # Additional global-specific complexity factors
            clause_count = self._count_clauses(doc)
            embedding_depth = sentence_complexity.get('dependency_depth', 0)
            coordination_complexity = self._analyze_coordination_complexity(doc)
            
            # Global audience complexity score (0-1, where >0.7 is problematic)
            complexity_factors = [
                min(sentence_complexity.get('word_count', 0) / 32.0, 1.0),  # Length factor
                min(embedding_depth / 4.0, 1.0),  # Depth factor
                min(clause_count / 2.0, 1.0),  # Clause factor
                coordination_complexity  # Coordination factor
            ]
            
            complexity_score = sum(complexity_factors) / len(complexity_factors)
            
            return {
                'complexity_score': complexity_score,
                'clause_count': clause_count,
                'embedding_depth': embedding_depth,
                'coordination_complexity': coordination_complexity,
                'sentence_complexity': sentence_complexity,
                'recommendations': self._generate_simplification_recommendations(complexity_factors)
            }
        
        except Exception:
            return {
                'complexity_score': 0.0,
                'error': 'complexity_analysis_failed'
            }
    
    def _find_global_friendly_alternatives(self, token) -> List[str]:
        """
        Find alternatives that are more accessible to global audiences.
        """
        alternatives = []
        
        if not token:
            return alternatives
        
        # Use the base class method first
        base_alternative = self._find_simpler_morphological_alternative(token)
        if base_alternative:
            alternatives.append(base_alternative)
        
        # Additional global-friendly alternatives
        lemma = token.lemma_.lower()
        
        # Global-friendly vocabulary (shorter, more common words)
        global_alternatives = {
            'accomplish': ['do', 'finish'],
            'additional': ['more', 'extra'],
            'approximately': ['about', 'roughly'],
            'assistance': ['help'],
            'commence': ['start', 'begin'],
            'component': ['part'],
            'comprehensive': ['full', 'complete'],
            'demonstrate': ['show'],
            'eliminate': ['remove', 'delete'],
            'establish': ['set up', 'make'],
            'fundamental': ['basic', 'key'],
            'implement': ['do', 'carry out'],
            'indicate': ['show', 'point to'],
            'initial': ['first'],
            'investigate': ['check', 'look into'],
            'methodology': ['method', 'way'],
            'numerous': ['many'],
            'obtain': ['get'],
            'participate': ['take part', 'join'],
            'prerequisite': ['requirement', 'need'],
            'subsequent': ['next', 'later'],
            'sufficient': ['enough'],
            'terminate': ['end', 'stop'],
            'utilize': ['use']
        }
        
        if lemma in global_alternatives:
            alternatives.extend(global_alternatives[lemma])
        
        # If no specific alternatives, suggest general simplification
        if not alternatives:
            semantic_field = self._analyze_semantic_field(token)
            if semantic_field == 'action':
                alternatives.append('do')
            elif semantic_field == 'entity':
                alternatives.append('thing')
            elif semantic_field == 'property':
                alternatives.append('good' if token.pos_ == 'ADJ' else 'well')
        
        return alternatives[:3]  # Limit to top 3 suggestions
    
    def _detect_idiomatic_patterns(self, doc) -> List[Dict[str, Any]]:
        """
        Detect idiomatic expressions using morphological and syntactic patterns.
        """
        idioms = []
        
        if not doc:
            return idioms
        
        try:
            # Look for fixed expressions and collocations
            for i, token in enumerate(doc[:-2]):  # Check 3-gram patterns
                three_gram = " ".join([doc[j].text for j in range(i, min(i+3, len(doc)))])
                
                # Check if this follows idiomatic patterns
                if self._is_idiomatic_pattern(doc[i:i+3]):
                    idioms.append({
                        'text': three_gram,
                        'pattern': 'three_gram_idiom',
                        'tokens': [self._token_to_dict(doc[j]) for j in range(i, min(i+3, len(doc)))]
                    })
        
        except Exception:
            pass
        
        return idioms
    
    def _is_idiomatic_pattern(self, tokens) -> bool:
        """
        Check if a sequence of tokens forms an idiomatic pattern.
        """
        if not tokens or len(tokens) < 2:
            return False
        
        try:
            # Heuristics for idiomatic expressions
            # 1. Unusual POS sequences
            pos_sequence = "+".join([token.pos_ for token in tokens])
            unusual_sequences = ['VERB+DET+NOUN', 'ADJ+NOUN+VERB', 'VERB+ADP+DET+NOUN']
            
            if pos_sequence in unusual_sequences:
                return True
            
            # 2. Non-compositional meaning indicators (approximate)
            total_complexity = sum(self._calculate_morphological_complexity(token) for token in tokens)
            if total_complexity > len(tokens) * 2.0:  # Unusually complex for the length
                return True
            
            # 3. Fixed preposition patterns
            if (len(tokens) >= 2 and 
                tokens[0].pos_ == 'VERB' and 
                tokens[1].pos_ == 'ADP' and 
                tokens[1].lemma_ not in ['of', 'to', 'in', 'on', 'at']):  # Unusual prepositions
                return True
        
        except Exception:
            pass
        
        return False
    
    def _is_culture_specific_entity(self, ent) -> bool:
        """
        Determine if a named entity is likely culture-specific.
        """
        # This is a simplified heuristic - in practice, you'd use more sophisticated
        # cultural knowledge bases or machine learning models
        
        try:
            # Check for common global entities that are generally understood
            global_entities = {'google', 'microsoft', 'apple', 'facebook', 'amazon', 'twitter'}
            
            if ent.text.lower() in global_entities:
                return False
            
            # Sports, entertainment, and local business entities are often culture-specific
            if ent.label_ in ['PERSON', 'ORG'] and len(ent.text.split()) <= 2:
                return True
        
        except Exception:
            pass
        
        return False
    
    def _detect_format_specificity(self, doc) -> List[Dict[str, Any]]:
        """
        Detect format conventions that may be culture-specific.
        """
        format_issues = []
        
        try:
            for token in doc:
                # Date formats, currency, measurements, etc.
                if token.like_num or token.shape_ in ['dd/dd/dddd', 'dd.dd.dddd', '$d,ddd']:
                    format_issues.append({
                        'text': token.text,
                        'type': 'format_specific',
                        'format_pattern': token.shape_,
                        'morphological_features': self._get_morphological_features(token)
                    })
        
        except Exception:
            pass
        
        return format_issues
    
    def _count_clauses(self, doc) -> int:
        """
        Count the number of clauses in a sentence.
        """
        if not doc:
            return 0
        
        try:
            clause_count = 1  # Start with main clause
            
            for token in doc:
                # Count subordinate clauses
                if token.dep_ in ['advcl', 'ccomp', 'xcomp', 'acl', 'relcl']:
                    clause_count += 1
                # Count coordinated clauses
                elif token.dep_ == 'conj' and token.pos_ == 'VERB':
                    clause_count += 1
            
            return clause_count
        
        except Exception:
            return 1
    
    def _analyze_coordination_complexity(self, doc) -> float:
        """
        Analyze complexity from coordination structures.
        """
        if not doc:
            return 0.0
        
        try:
            coordination_count = 0
            total_tokens = len([token for token in doc if token.is_alpha])
            
            for token in doc:
                if token.dep_ == 'conj':
                    coordination_count += 1
            
            # Return ratio of coordination to total content
            return coordination_count / max(total_tokens, 1)
        
        except Exception:
            return 0.0
    
    def _analyze_absolute_context(self, token, doc) -> Dict[str, Any]:
        """
        Analyze the morphological context around absolute language.
        """
        context = {
            'head_relation': f"{token.dep_}+{token.head.pos_}" if token.head else '',
            'children_count': len(list(token.children)),
            'semantic_field': self._analyze_semantic_field(token, doc)
        }
        
        return context
    
    def _generate_simplification_recommendations(self, complexity_factors: List[float]) -> List[str]:
        """
        Generate specific recommendations based on complexity analysis.
        """
        recommendations = []
        
        if complexity_factors[0] > 0.7:  # Length
            recommendations.append("Break into shorter sentences (aim for 20-25 words)")
        
        if complexity_factors[1] > 0.7:  # Depth
            recommendations.append("Reduce nested clauses and embedded structures")
        
        if complexity_factors[2] > 0.7:  # Clauses
            recommendations.append("Use fewer subordinate clauses per sentence")
        
        if complexity_factors[3] > 0.7:  # Coordination
            recommendations.append("Simplify coordinated structures")
        
        if not recommendations:
            recommendations.append("Use simpler sentence structures for global audiences")
        
        return recommendations
