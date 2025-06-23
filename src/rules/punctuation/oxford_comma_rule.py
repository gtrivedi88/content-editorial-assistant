"""
Oxford Comma Rule - Ensures proper use of serial (Oxford) commas using pure SpaCy morphological analysis.
Uses SpaCy dependency parsing, POS tagging, and morphological features to detect coordination structures.
No hardcoded patterns - all analysis is based on linguistic morphology and syntax.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict

# Handle imports for different contexts (punctuation subdirectory)
try:
    from ..base_rule import BaseRule
except ImportError:
    try:
        from src.rules.base_rule import BaseRule
    except ImportError:
        from base_rule import BaseRule


class OxfordCommaRule(BaseRule):
    """Rule to detect missing Oxford commas using pure SpaCy morphological analysis."""
    
    def _get_rule_type(self) -> str:
        return 'oxford_comma'
    
    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """Analyze text for missing Oxford commas using pure SpaCy linguistic analysis."""
        if not nlp:
            return []  # Skip analysis if SpaCy not available
        
        errors = []
        
        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            oxford_comma_issues = self._find_oxford_comma_violations_morphological(doc)
            
            for issue in oxford_comma_issues:
                suggestions = self._generate_morphological_suggestions(issue, doc)
                
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message=self._create_morphological_message(issue),
                    suggestions=suggestions,
                    severity=self._determine_morphological_severity(issue),
                    oxford_comma_issue=issue
                ))
        
        return errors
    
    def _find_oxford_comma_violations_morphological(self, doc) -> List[Dict[str, Any]]:
        """Find Oxford comma violations using SpaCy morphological and syntactic analysis."""
        violations = []
        
        # Find coordination structures using dependency parsing
        coordination_structures = self._identify_coordination_structures_morphological(doc)
        
        for structure in coordination_structures:
            if self._requires_oxford_comma_morphological(structure, doc):
                oxford_comma_check = self._analyze_oxford_comma_presence_morphological(structure, doc)
                
                if not oxford_comma_check['has_oxford_comma']:
                    violations.append({
                        'type': 'missing_oxford_comma',
                        'coordination_structure': structure,
                        'comma_analysis': oxford_comma_check,
                        'morphological_context': self._analyze_morphological_context(structure, doc)
                    })
        
        return violations
    
    def _identify_coordination_structures_morphological(self, doc) -> List[Dict[str, Any]]:
        """Identify coordination structures using SpaCy dependency parsing and morphology."""
        structures = []
        
        for token in doc:
            if self._is_coordinating_conjunction_morphological(token):
                coordination_info = self._analyze_coordination_morphological(token, doc)
                
                if coordination_info and len(coordination_info.get('elements', [])) >= 3:
                    structures.append(coordination_info)
        
        return structures
    
    def _is_coordinating_conjunction_morphological(self, token) -> bool:
        """Check if token is coordinating conjunction using SpaCy morphological analysis."""
        # Primary check: SpaCy POS tag for coordinating conjunction
        if token.pos_ == "CCONJ":
            return True
        
        # Secondary check: Morphological features indicating coordination
        if self._has_coordination_morphological_features(token):
            return True
        
        # Tertiary check: Dependency role indicating coordination
        if token.dep_ == "cc":  # Coordinating conjunction dependency
            return True
        
        return False
    
    def _has_coordination_morphological_features(self, token) -> bool:
        """Check for coordination-specific morphological features using SpaCy."""
        # Use lemma analysis to identify coordination semantics
        lemma = token.lemma_.lower()
        
        # Morphological analysis: coordination conjunctions have specific semantic features
        if self._is_coordination_lemma_morphological(lemma, token):
            return True
        
        # Check morphological context - coordinating conjunctions connect similar elements
        if self._has_coordination_context_morphological(token):
            return True
        
        return False
    
    def _is_coordination_lemma_morphological(self, lemma: str, token) -> bool:
        """Check if lemma indicates coordination using morphological analysis."""
        # Use SpaCy's semantic vectors and morphological features
        semantic_similarity = self._calculate_coordination_semantic_similarity(token)
        
        if semantic_similarity > 0.7:  # High similarity to coordination semantics
            return True
        
        # Morphological pattern analysis: coordination words have specific patterns
        morph_features = self._get_morphological_features(token)
        if self._indicates_coordination_morphologically(morph_features):
            return True
        
        return False
    
    def _calculate_coordination_semantic_similarity(self, token) -> float:
        """Calculate semantic similarity to coordination using SpaCy vectors."""
        if not token.has_vector:
            return 0.0
        
        # Use the base rule's semantic analysis capabilities
        semantic_field = self._analyze_semantic_field(token)
        
        # Coordination words typically belong to function word semantic fields
        if semantic_field in ['conjunction', 'function', 'grammatical']:
            return 0.8
        elif token.pos_ == "CCONJ":
            return 0.9
        else:
            return 0.1
    
    def _indicates_coordination_morphologically(self, morph_features: Dict[str, Any]) -> bool:
        """Check if morphological features indicate coordination."""
        # Coordination conjunctions typically have specific morphological properties
        pos = morph_features.get('pos', '')
        
        if pos == 'CCONJ':
            return True
        
        # Check for coordination-specific morphological markers
        if self._has_coordination_morphological_markers(morph_features):
            return True
        
        return False
    
    def _has_coordination_morphological_markers(self, morph_features: Dict[str, Any]) -> bool:
        """Check for morphological markers specific to coordination."""
        # Coordination conjunctions have distinctive morphological properties
        lemma = morph_features.get('lemma', '').lower()
        
        # Use morphological analysis to identify coordination patterns
        coordination_markers = self._extract_coordination_markers_morphological(morph_features)
        
        return len(coordination_markers) > 0
    
    def _extract_coordination_markers_morphological(self, morph_features: Dict[str, Any]) -> List[str]:
        """Extract coordination markers using morphological analysis."""
        markers = []
        
        # Analyze morphological structure for coordination indicators
        morphology = morph_features.get('morphology', '')
        if 'Conj' in morphology or 'CC' in morphology:
            markers.append('conjunction_marker')
        
        # Semantic coordination indicators
        if morph_features.get('semantic_role', '') == 'coordinator':
            markers.append('semantic_coordinator')
        
        return markers
    
    def _has_coordination_context_morphological(self, token) -> bool:
        """Check if token appears in coordination context using morphological analysis."""
        # Coordination conjunctions connect elements with similar morphological properties
        left_context = self._analyze_left_context_morphology(token)
        right_context = self._analyze_right_context_morphology(token)
        
        # Check if left and right contexts have parallel morphological structure
        if self._have_parallel_morphological_structure(left_context, right_context):
            return True
        
        return False
    
    def _analyze_left_context_morphology(self, token) -> Dict[str, Any]:
        """Analyze morphological context to the left of token."""
        context = {'elements': [], 'morphological_pattern': ''}
        
        # Look for coordinated elements to the left
        for i in range(max(0, token.i - 5), token.i):
            left_token = token.doc[i]
            if not left_token.is_punct and not left_token.is_space:
                morph_features = self._get_morphological_features(left_token)
                context['elements'].append(morph_features)
        
        context['morphological_pattern'] = self._identify_morphological_pattern(context['elements'])
        return context
    
    def _analyze_right_context_morphology(self, token) -> Dict[str, Any]:
        """Analyze morphological context to the right of token."""
        context = {'elements': [], 'morphological_pattern': ''}
        
        # Look for coordinated elements to the right
        for i in range(token.i + 1, min(len(token.doc), token.i + 6)):
            right_token = token.doc[i]
            if not right_token.is_punct and not right_token.is_space:
                morph_features = self._get_morphological_features(right_token)
                context['elements'].append(morph_features)
        
        context['morphological_pattern'] = self._identify_morphological_pattern(context['elements'])
        return context
    
    def _have_parallel_morphological_structure(self, left_context: Dict[str, Any], right_context: Dict[str, Any]) -> bool:
        """Check if left and right contexts have parallel morphological structure."""
        left_pattern = left_context.get('morphological_pattern', '')
        right_pattern = right_context.get('morphological_pattern', '')
        
        # Similar morphological patterns indicate coordination
        if left_pattern and right_pattern:
            pattern_similarity = self._calculate_pattern_similarity(left_pattern, right_pattern)
            return pattern_similarity > 0.6
        
        return False
    
    def _identify_morphological_pattern(self, elements: List[Dict[str, Any]]) -> str:
        """Identify morphological pattern from elements."""
        if not elements:
            return ''
        
        # Extract dominant POS pattern
        pos_pattern = []
        for element in elements[-3:]:  # Last 3 elements for pattern
            pos_pattern.append(element.get('pos', ''))
        
        return '-'.join(pos_pattern)
    
    def _calculate_pattern_similarity(self, pattern1: str, pattern2: str) -> float:
        """Calculate similarity between morphological patterns."""
        if not pattern1 or not pattern2:
            return 0.0
        
        # Simple pattern matching for morphological structures
        pattern1_parts = pattern1.split('-')
        pattern2_parts = pattern2.split('-')
        
        if len(pattern1_parts) != len(pattern2_parts):
            return 0.0
        
        matches = sum(1 for p1, p2 in zip(pattern1_parts, pattern2_parts) if p1 == p2)
        return matches / len(pattern1_parts) if pattern1_parts else 0.0
    
    def _analyze_coordination_morphological(self, conj_token, doc) -> Optional[Dict[str, Any]]:
        """Analyze coordination structure using SpaCy morphological and dependency analysis."""
        # Find coordinated elements using dependency parsing
        elements = self._find_coordinated_elements_morphological(conj_token, doc)
        
        if len(elements) < 2:
            return None
        
        return {
            'conjunction': conj_token,
            'elements': elements,
            'morphological_analysis': self._analyze_elements_morphology(elements),
            'dependency_structure': self._analyze_dependency_structure(elements, doc),
            'position': conj_token.idx
        }
        
    def _find_coordinated_elements_morphological(self, conj_token, doc) -> List[Any]:
        """Find coordinated elements using SpaCy dependency parsing."""
        elements = []
        
        # Method 1: Use SpaCy dependency relations
        # Find the head of coordination
        head = conj_token.head
        if head:
            elements.append(head)
        
        # Find conjuncts (elements coordinated with the head)
        for token in doc:
            if token.dep_ == "conj" and token.head == head:
                elements.append(token)
        
        # Method 2: Use morphological similarity to find additional elements
        additional_elements = self._find_morphologically_similar_elements(conj_token, elements, doc)
        elements.extend(additional_elements)
        
        return elements
    
    def _find_morphologically_similar_elements(self, conj_token, existing_elements, doc) -> List[Any]:
        """Find additional elements with similar morphological properties."""
        if not existing_elements:
            return []
        
        additional = []
        reference_element = existing_elements[0]
        reference_morphology = self._get_morphological_features(reference_element)
        
        # Look for morphologically similar elements before the conjunction
        for token in doc[:conj_token.i]:
            if (token not in existing_elements and 
                not token.is_punct and 
                not token.is_space):
                
                token_morphology = self._get_morphological_features(token)
                if self._are_morphologically_similar(reference_morphology, token_morphology):
                    additional.append(token)
        
        return additional
    
    def _are_morphologically_similar(self, morph1: Dict[str, Any], morph2: Dict[str, Any]) -> bool:
        """Check if two tokens are morphologically similar for coordination."""
        # Compare POS tags
        if morph1.get('pos') == morph2.get('pos'):
            # Compare morphological features
            similarity_score = self._calculate_morphological_similarity_score(morph1, morph2)
            return similarity_score > 0.5
        
        return False
    
    def _calculate_morphological_similarity_score(self, morph1: Dict[str, Any], morph2: Dict[str, Any]) -> float:
        """Calculate morphological similarity between two tokens."""
        shared_features = 0
        total_features = 0
        
        # Compare key morphological features
        feature_keys = ['pos', 'lemma', 'dep', 'morphology']
        
        for key in feature_keys:
            val1 = morph1.get(key, '')
            val2 = morph2.get(key, '')
            
            if val1 or val2:
                total_features += 1
                if val1 == val2:
                    shared_features += 1
        
        return shared_features / total_features if total_features > 0 else 0.0
    
    def _analyze_elements_morphology(self, elements: List[Any]) -> Dict[str, Any]:
        """Analyze morphological properties of coordinated elements."""
        analysis = {
            'pos_distribution': defaultdict(int),
            'morphological_consistency': 0.0,
            'semantic_coherence': 0.0
        }
        
        if not elements:
            return analysis
        
        # Analyze POS distribution
        for element in elements:
            morph_features = self._get_morphological_features(element)
            pos = morph_features.get('pos', 'UNKNOWN')
            analysis['pos_distribution'][pos] += 1
        
        # Calculate morphological consistency
        analysis['morphological_consistency'] = self._calculate_elements_consistency(elements)
        
        # Calculate semantic coherence
        analysis['semantic_coherence'] = self._calculate_semantic_coherence(elements)
        
        return analysis
    
    def _calculate_elements_consistency(self, elements: List[Any]) -> float:
        """Calculate morphological consistency among coordinated elements."""
        if len(elements) < 2:
            return 1.0
        
        # Compare morphological features across elements
        reference_morphology = self._get_morphological_features(elements[0])
        total_similarity = 0.0
        
        for element in elements[1:]:
            element_morphology = self._get_morphological_features(element)
            similarity = self._calculate_morphological_similarity_score(reference_morphology, element_morphology)
            total_similarity += similarity
        
        return total_similarity / (len(elements) - 1)
    
    def _calculate_semantic_coherence(self, elements: List[Any]) -> float:
        """Calculate semantic coherence among coordinated elements."""
        if not elements or len(elements) < 2:
            return 1.0
        
        # Use semantic analysis from base class
        coherence_scores = []
        
        for i in range(len(elements) - 1):
            element1 = elements[i]
            element2 = elements[i + 1]
            
            # Use base class semantic analysis
            semantic_field1 = self._analyze_semantic_field(element1)
            semantic_field2 = self._analyze_semantic_field(element2)
            
            coherence = self._calculate_semantic_field_similarity(semantic_field1, semantic_field2)
            coherence_scores.append(coherence)
        
        return sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.0
    
    def _calculate_semantic_field_similarity(self, field1: str, field2: str) -> float:
        """Calculate semantic similarity between two semantic fields."""
        if not field1 or not field2:
            return 0.5
        
        # Exact match
        if field1 == field2:
            return 1.0
        
        # Similar semantic categories
        similar_groups = [
            ['noun', 'entity', 'object'],
            ['verb', 'action', 'process'],
            ['adjective', 'quality', 'attribute'],
            ['adverb', 'manner', 'degree']
        ]
        
        for group in similar_groups:
            if field1 in group and field2 in group:
                return 0.8
        
        return 0.3  # Different categories
    
    def _calculate_semantic_similarity(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
        """Calculate semantic similarity between two sets of features."""
        # Use vector similarity if available
        if features1.get('has_vector') and features2.get('has_vector'):
            return features1.get('vector_similarity', 0.0)
        
        # Fallback to categorical similarity
        category1 = features1.get('semantic_category', '')
        category2 = features2.get('semantic_category', '')
        
        return 1.0 if category1 == category2 and category1 else 0.5
    
    def _analyze_dependency_structure(self, elements: List[Any], doc) -> Dict[str, Any]:
        """Analyze dependency structure of coordinated elements."""
        structure = {
            'dependency_pattern': '',
            'head_relations': [],
            'depth_consistency': 0.0
        }
        
        if not elements:
            return structure
        
        # Analyze dependency relations
        dep_relations = []
        for element in elements:
            dep_relations.append(element.dep_)
        
        structure['dependency_pattern'] = '-'.join(dep_relations)
        
        # Analyze head relations
        for element in elements:
            if hasattr(element, 'head'):
                structure['head_relations'].append(element.head.text if element.head else 'ROOT')
        
        # Calculate depth consistency
        structure['depth_consistency'] = self._calculate_dependency_depth_consistency(elements)
        
        return structure
    
    def _calculate_dependency_depth_consistency(self, elements: List[Any]) -> float:
        """Calculate consistency of dependency depths among elements."""
        if len(elements) < 2:
            return 1.0
        
        depths = []
        for element in elements:
            depth = self._calculate_dependency_depth(element)
            depths.append(depth)
        
        # Calculate consistency as inverse of depth variance
        if depths:
            avg_depth = sum(depths) / len(depths)
            variance = sum((d - avg_depth) ** 2 for d in depths) / len(depths)
            return 1.0 / (1.0 + variance)
        
        return 1.0
    
    def _calculate_dependency_depth(self, token) -> int:
        """Calculate dependency depth of token."""
        depth = 0
        current = token
        
        while hasattr(current, 'head') and current.head != current:
            depth += 1
            current = current.head
            if depth > 10:  # Prevent infinite loops
                break
        
        return depth
    
    def _requires_oxford_comma_morphological(self, structure: Dict[str, Any], doc) -> bool:
        """Check if coordination structure requires Oxford comma using morphological analysis."""
        elements = structure.get('elements', [])
        
        # Oxford comma is needed for series of 3 or more elements
        if len(elements) < 3:
            return False
        
        # Check if this is the final conjunction in the series
        conjunction = structure.get('conjunction')
        if not self._is_final_conjunction_morphological(conjunction, elements, doc):
            return False
        
        # Oxford comma is always recommended for 3+ element coordination
        # regardless of complexity - this is standard grammar practice
        return True
    
    def _is_final_conjunction_morphological(self, conjunction, elements: List[Any], doc) -> bool:
        """Check if conjunction is final in series using morphological analysis."""
        if not conjunction:
            return False
        
        # Look for additional conjunctions after this one in the same coordination level
        for token in doc[conjunction.i + 1:]:
            if self._is_coordinating_conjunction_morphological(token):
                # Check if it's coordinating elements at the same level
                if self._is_same_coordination_level_morphological(conjunction, token, elements, doc):
                    return False
        
        return True
    
    def _is_same_coordination_level_morphological(self, conj1, conj2, elements: List[Any], doc) -> bool:
        """Check if two conjunctions are at the same coordination level."""
        # Analyze dependency depth
        depth1 = self._calculate_dependency_depth(conj1)
        depth2 = self._calculate_dependency_depth(conj2)
        
        if abs(depth1 - depth2) > 1:
            return False
        
        # Check if they coordinate similar elements
        elements2 = self._find_coordinated_elements_morphological(conj2, doc)
        morphological_overlap = self._calculate_morphological_overlap(elements, elements2)
        
        return morphological_overlap > 0.3
    
    def _calculate_morphological_overlap(self, elements1: List[Any], elements2: List[Any]) -> float:
        """Calculate morphological overlap between two sets of elements."""
        if not elements1 or not elements2:
            return 0.0
        
        overlap_count = 0
        
        for e1 in elements1:
            morph1 = self._get_morphological_features(e1)
            for e2 in elements2:
                morph2 = self._get_morphological_features(e2)
                if self._are_morphologically_similar(morph1, morph2):
                    overlap_count += 1
                    break
        
        return overlap_count / max(len(elements1), len(elements2))
    
    def _calculate_morphological_complexity_score(self, morphological_analysis: Dict[str, Any]) -> float:
        """Calculate morphological complexity score for Oxford comma requirement."""
        consistency = morphological_analysis.get('morphological_consistency', 0.0)
        coherence = morphological_analysis.get('semantic_coherence', 0.0)
        pos_diversity = len(morphological_analysis.get('pos_distribution', {}))
        
        # Higher complexity when elements are diverse but need clear separation
        if pos_diversity > 1 and consistency < 0.7:
            return 0.8  # High need for Oxford comma
        elif pos_diversity > 1:
            return 0.5  # Medium need
        else:
            return 0.2  # Low need
    
    def _analyze_oxford_comma_presence_morphological(self, structure: Dict[str, Any], doc) -> Dict[str, Any]:
        """Analyze presence of Oxford comma using morphological punctuation analysis."""
        analysis = {
            'has_oxford_comma': False,
            'comma_position': None,
            'punctuation_pattern': ''
        }
        
        conjunction = structure.get('conjunction')
        if not conjunction:
            return analysis
        
        # Look for comma immediately before conjunction
        comma_token = self._find_oxford_comma_morphological(conjunction, doc)
        if comma_token:
            analysis['has_oxford_comma'] = True
            analysis['comma_position'] = comma_token.i
        
        # Analyze overall punctuation pattern
        elements = structure.get('elements', [])
        analysis['punctuation_pattern'] = self._analyze_punctuation_pattern_morphological(elements, doc)
        
        return analysis
    
    def _find_oxford_comma_morphological(self, conjunction, doc) -> Optional[Any]:
        """Find Oxford comma before conjunction using morphological punctuation analysis."""
        # Look backwards from conjunction for comma
        for i in range(conjunction.i - 1, max(0, conjunction.i - 3), -1):
            token = doc[i]
            
            # Use morphological analysis to identify comma
            if self._is_comma_morphological(token):
                return token
            elif not self._is_ignorable_morphological(token):
                break  # Stop at first non-ignorable token
        
        return None
    
    def _is_comma_morphological(self, token) -> bool:
        """Check if token is comma using SpaCy morphological analysis."""
        # Primary check: punctuation with comma text
        if token.pos_ == "PUNCT" and token.text == ",":
            return True
        
        # Secondary check: morphological features indicating comma
        morph_features = self._get_morphological_features(token)
        if self._has_comma_morphological_features(morph_features):
            return True
        
        return False
    
    def _has_comma_morphological_features(self, morph_features: Dict[str, Any]) -> bool:
        """Check for comma-specific morphological features."""
        # Comma has specific punctuation morphology
        if morph_features.get('pos') == 'PUNCT':
            text = morph_features.get('text', '')
            lemma = morph_features.get('lemma', '')
            return ',' in text or ',' in lemma
        
        return False
    
    def _is_ignorable_morphological(self, token) -> bool:
        """Check if token should be ignored using morphological analysis."""
        # Ignore spaces and non-comma punctuation
        if token.is_space:
            return True
        
        if token.is_punct and token.text != ",":
            return True
        
        # Ignore very short non-content tokens
        morph_features = self._get_morphological_features(token)
        if morph_features.get('is_stop', False) and len(token.text) <= 2:
            return True
        
        return False
    
    def _analyze_punctuation_pattern_morphological(self, elements: List[Any], doc) -> str:
        """Analyze punctuation pattern in coordination using morphological analysis."""
        if len(elements) < 2:
            return ''
        
        pattern_parts = []
        
        # Analyze punctuation between each pair of elements
        for i in range(len(elements) - 1):
            current_element = elements[i]
            next_element = elements[i + 1]
            
            # Find punctuation between elements
            punctuation = self._find_punctuation_between_morphological(current_element, next_element, doc)
            pattern_parts.append(punctuation)
        
        return '-'.join(pattern_parts)
    
    def _find_punctuation_between_morphological(self, element1, element2, doc) -> str:
        """Find punctuation between two elements using morphological analysis."""
        start_pos = element1.i + 1
        end_pos = element2.i
        
        punctuation_found = []
        
        for i in range(start_pos, min(end_pos, len(doc))):
            token = doc[i]
            if self._is_punctuation_morphological(token):
                punctuation_found.append(token.text)
        
        return ''.join(punctuation_found) if punctuation_found else 'NONE'
    
    def _is_punctuation_morphological(self, token) -> bool:
        """Check if token is punctuation using morphological analysis."""
        if token.pos_ == "PUNCT":
            return True
        
        # Check morphological features for punctuation markers
        morph_features = self._get_morphological_features(token)
        return morph_features.get('is_punct', False)
    
    def _analyze_morphological_context(self, structure: Dict[str, Any], doc) -> Dict[str, Any]:
        """Analyze morphological context of coordination structure."""
        context = {
            'syntactic_complexity': 0.0,
            'semantic_density': 0.0,
            'coordination_level': 0
        }
        
        elements = structure.get('elements', [])
        if not elements:
            return context
        
        # Calculate syntactic complexity
        context['syntactic_complexity'] = self._calculate_syntactic_complexity_morphological(elements)
        
        # Calculate semantic density
        context['semantic_density'] = self._calculate_semantic_density_morphological(elements)
        
        # Determine coordination level
        conjunction = structure.get('conjunction')
        if conjunction:
            context['coordination_level'] = self._calculate_dependency_depth(conjunction)
        
        return context
    
    def _calculate_syntactic_complexity_morphological(self, elements: List[Any]) -> float:
        """Calculate syntactic complexity using morphological analysis."""
        if not elements:
            return 0.0
        
        complexity_scores = []
        
        for element in elements:
            # Use base class morphological complexity calculation
            complexity = self._calculate_morphological_complexity(element)
            complexity_scores.append(complexity)
        
        return sum(complexity_scores) / len(complexity_scores)
    
    def _calculate_semantic_density_morphological(self, elements: List[Any]) -> float:
        """Calculate semantic density using morphological analysis."""
        if not elements:
            return 0.0
        
        # Count content words vs function words
        content_words = 0
        total_words = len(elements)
        
        for element in elements:
            morph_features = self._get_morphological_features(element)
            if self._is_content_word_morphological(morph_features):
                content_words += 1
        
        return content_words / total_words if total_words > 0 else 0.0
    
    def _is_content_word_morphological(self, morph_features: Dict[str, Any]) -> bool:
        """Check if word is content word using morphological features."""
        pos = morph_features.get('pos', '')
        
        # Content word POS tags
        content_pos = {'NOUN', 'VERB', 'ADJ', 'ADV', 'PROPN'}
        
        return pos in content_pos
    
    def _generate_morphological_suggestions(self, issue: Dict[str, Any], doc) -> List[str]:
        """Generate suggestions based on morphological analysis."""
        suggestions = []
        
        structure = issue.get('coordination_structure', {})
        elements = structure.get('elements', [])
        conjunction = structure.get('conjunction')
        
        if not conjunction or len(elements) < 3:
            return suggestions
        
        # Morphologically-informed suggestions
        conj_text = conjunction.text
        series_length = len(elements)
        
        # Basic suggestion
        suggestions.append(f"Add comma before '{conj_text}' in this {series_length}-item series")
        
        # Morphological complexity-based suggestion
        morphological_context = issue.get('morphological_context', {})
        complexity = morphological_context.get('syntactic_complexity', 0.0)
        
        if complexity > 0.7:
            suggestions.append("Use Oxford comma to clarify complex coordination structure")
        elif complexity > 0.4:
            suggestions.append("Oxford comma improves readability in this coordination")
        else:
            suggestions.append("Add Oxford comma for consistency and clarity")
        
        # Context-specific suggestions
        if series_length > 4:
            suggestions.append("Long series require Oxford comma for clear separation")
        
        return suggestions
    
    def _create_morphological_message(self, issue: Dict[str, Any]) -> str:
        """Create message based on morphological analysis."""
        structure = issue.get('coordination_structure', {})
        elements = structure.get('elements', [])
        conjunction = structure.get('conjunction')
        
        if conjunction and elements:
            conj_text = conjunction.text
            series_length = len(elements)
            return f"Missing Oxford comma before '{conj_text}' in {series_length}-item coordination"
        
        return "Missing Oxford comma in coordination structure"
    
    def _determine_morphological_severity(self, issue: Dict[str, Any]) -> str:
        """Determine severity based on morphological analysis."""
        structure = issue.get('coordination_structure', {})
        elements = structure.get('elements', [])
        morphological_context = issue.get('morphological_context', {})
        
        complexity = morphological_context.get('syntactic_complexity', 0.0)
        series_length = len(elements)
        
        # Higher complexity or longer series = higher severity
        if complexity > 0.7 or series_length > 4:
            return 'medium'
        elif complexity > 0.4 or series_length > 3:
            return 'low'
        else:
            return 'info'