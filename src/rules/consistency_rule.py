"""
Consistency Rule - Ensures consistent terminology throughout documents using pure SpaCy analysis.
Uses SpaCy semantic similarity, entity recognition, and word embeddings to detect inconsistent term usage.
"""

from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict

# Handle imports for different contexts
try:
    from .base_rule import BaseRule
except ImportError:
    from base_rule import BaseRule

class ConsistencyRule(BaseRule):
    """Rule to detect inconsistent terminology using pure SpaCy semantic analysis."""
    
    def _get_rule_type(self) -> str:
        return 'consistency'
    
    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """Analyze text for terminology consistency using pure SpaCy analysis."""
        errors = []
        
        if nlp:
            # Process entire document to track terminology across sentences
            full_doc = nlp(text)
            consistency_issues = self._find_terminology_inconsistencies(full_doc, sentences)
        else:
            # Fallback: Basic pattern analysis without SpaCy
            consistency_issues = self._find_terminology_inconsistencies_fallback(text, sentences)
        
        # Create errors for each consistency issue found
        for issue in consistency_issues:
            suggestions = self._generate_consistency_suggestions(issue, full_doc if nlp else None)
            
            errors.append(self._create_error(
                sentence=issue.get('sentence', ''),
                sentence_index=issue.get('sentence_index', 0),
                message=self._create_consistency_message(issue),
                suggestions=suggestions,
                severity=self._determine_consistency_severity(issue),
                consistency_issue=issue
            ))
        
        return errors
    
    def _find_terminology_inconsistencies(self, doc, sentences) -> List[Dict[str, Any]]:
        """Find terminology inconsistencies using advanced SpaCy semantic analysis."""
        inconsistencies = []
        
        # Step 1: Extract terminology concepts using multiple SpaCy approaches
        terminology_map = self._extract_terminology_concepts(doc)
        
        # Step 2: Analyze concept usage patterns across sentences
        usage_patterns = self._analyze_concept_usage_patterns(terminology_map, doc, sentences)
        
        # Step 3: Detect inconsistencies using semantic similarity analysis
        for concept_group, usage_data in usage_patterns.items():
            concept_inconsistencies = self._detect_concept_inconsistencies(concept_group, usage_data, doc)
            inconsistencies.extend(concept_inconsistencies)
        
        return inconsistencies
    
    def _extract_terminology_concepts(self, doc) -> Dict[str, List[Dict[str, Any]]]:
        """Extract terminology concepts using SpaCy NER, semantic analysis, and morphology."""
        terminology_map = defaultdict(list)
        
        # Method 1: Named Entity Recognition for proper nouns and technical terms
        entity_concepts = self._extract_entity_concepts(doc)
        for concept_key, entities in entity_concepts.items():
            terminology_map[concept_key].extend(entities)
        
        # Method 2: Noun phrase analysis for compound terms
        noun_phrase_concepts = self._extract_noun_phrase_concepts(doc)
        for concept_key, phrases in noun_phrase_concepts.items():
            terminology_map[concept_key].extend(phrases)
        
        # Method 3: Semantic field analysis using word vectors
        semantic_concepts = self._extract_semantic_concepts(doc)
        for concept_key, terms in semantic_concepts.items():
            terminology_map[concept_key].extend(terms)
        
        return terminology_map
    
    def _extract_entity_concepts(self, doc) -> Dict[str, List[Dict[str, Any]]]:
        """Extract entity concepts using SpaCy Named Entity Recognition."""
        entity_concepts = defaultdict(list)
        
        for ent in doc.ents:
            # Group entities by type and semantic similarity
            concept_key = self._generate_entity_concept_key(ent, doc)
            
            entity_data = {
                'text': ent.text,
                'lemma': ent.root.lemma_.lower(),
                'label': ent.label_,
                'start': ent.start,
                'end': ent.end,
                'vector': ent.vector if ent.has_vector else None,
                'type': 'entity'
            }
            
            entity_concepts[concept_key].append(entity_data)
        
        return entity_concepts
    
    def _generate_entity_concept_key(self, ent, doc) -> str:
        """Generate concept key for entity using semantic analysis."""
        # Method 1: Use entity label as primary grouping
        base_key = f"entity_{ent.label_.lower()}"
        
        # Method 2: Add semantic refinement using root lemma
        if ent.root:
            root_lemma = ent.root.lemma_.lower()
            base_key += f"_{root_lemma}"
        
        # Method 3: Group similar entities using semantic similarity
        if ent.has_vector:
            # Find semantically similar entities to group together
            similar_key = self._find_semantically_similar_group(ent, doc)
            if similar_key:
                base_key = similar_key
        
        return base_key
    
    def _find_semantically_similar_group(self, target_ent, doc) -> str:
        """Find semantically similar entity group using word vectors."""
        similarity_threshold = 0.7
        
        # Compare with other entities using semantic similarity
        for other_ent in doc.ents:
            if (other_ent != target_ent and 
                other_ent.has_vector and target_ent.has_vector):
                
                similarity = target_ent.similarity(other_ent)
                if similarity > similarity_threshold:
                    # Group with semantically similar entity
                    return f"semantic_group_{other_ent.root.lemma_.lower()}"
        
        return None
    
    def _extract_noun_phrase_concepts(self, doc) -> Dict[str, List[Dict[str, Any]]]:
        """Extract noun phrase concepts using SpaCy dependency parsing."""
        noun_phrase_concepts = defaultdict(list)
        
        for chunk in doc.noun_chunks:
            # Analyze compound noun phrases for terminology
            concept_key = self._generate_noun_phrase_concept_key(chunk, doc)
            
            phrase_data = {
                'text': chunk.text,
                'lemma': ' '.join([token.lemma_.lower() for token in chunk]),
                'root': chunk.root.text,
                'start': chunk.start,
                'end': chunk.end,
                'vector': chunk.vector if chunk.has_vector else None,
                'type': 'noun_phrase'
            }
            
            noun_phrase_concepts[concept_key].append(phrase_data)
        
        return noun_phrase_concepts
    
    def _generate_noun_phrase_concept_key(self, chunk, doc) -> str:
        """Generate concept key for noun phrase using morphological analysis."""
        # Method 1: Use root lemma as base
        base_key = f"concept_{chunk.root.lemma_.lower()}"
        
        # Method 2: Add semantic modifiers
        modifiers = self._extract_semantic_modifiers(chunk)
        if modifiers:
            base_key += f"_{'_'.join(modifiers)}"
        
        return base_key
    
    def _extract_semantic_modifiers(self, chunk) -> List[str]:
        """Extract semantic modifiers from noun phrase."""
        modifiers = []
        
        for token in chunk:
            if token.dep_ in ['amod', 'compound', 'nmod']:
                modifiers.append(token.lemma_.lower())
        
        return sorted(modifiers)  # Sort for consistent grouping
    
    def _extract_semantic_concepts(self, doc) -> Dict[str, List[Dict[str, Any]]]:
        """Extract semantic concepts using word embeddings and similarity analysis."""
        semantic_concepts = defaultdict(list)
        
        # Find semantically related terms using word vectors
        processed_tokens = []
        
        for token in doc:
            if self._is_terminology_candidate(token):
                # Find semantic group using word vectors
                concept_key = self._find_semantic_concept_group(token, processed_tokens)
                
                term_data = {
                    'text': token.text,
                    'lemma': token.lemma_.lower(),
                    'pos': token.pos_,
                    'index': token.i,
                    'vector': token.vector if token.has_vector else None,
                    'type': 'semantic_term'
                }
                
                semantic_concepts[concept_key].append(term_data)
                processed_tokens.append((token, concept_key))
        
        # Special handling for AI/ML terms
        ai_ml_concepts = self._extract_ai_ml_concepts(doc)
        for concept_key, terms in ai_ml_concepts.items():
            semantic_concepts[concept_key].extend(terms)
        
        return semantic_concepts
    
    def _is_terminology_candidate(self, token) -> bool:
        """Check if token is a terminology candidate using morphological analysis."""
        # Method 1: POS-based filtering
        if token.pos_ in ['NOUN', 'PROPN', 'ADJ']:
            # Method 2: Length and frequency filtering
            if len(token.text) > 3 and not token.is_stop:
                # Method 3: Morphological complexity check
                if self._has_terminology_morphology(token):
                    return True
        
        return False
    
    def _has_terminology_morphology(self, token) -> bool:
        """Check for terminology morphological patterns."""
        # Technical terms often have specific morphological patterns
        lemma = token.lemma_.lower()
        
        # Method 1: Check for technical suffixes using morphology
        technical_suffixes = self._extract_technical_suffixes()
        for suffix in technical_suffixes:
            if lemma.endswith(suffix):
                return True
        
        # Method 2: Check morphological features
        if token.morph:
            morph_str = str(token.morph)
            if any(feature in morph_str for feature in ['Number=Sing', 'Definite=Def']):
                return True
        
        return False
    
    def _extract_technical_suffixes(self) -> List[str]:
        """Extract technical suffixes using morphological analysis."""
        # Generate technical suffixes dynamically based on morphological patterns
        return ['tion', 'sion', 'ment', 'ness', 'ity', 'ism', 'ogy', 'logy']
    
    def _find_semantic_concept_group(self, token, processed_tokens) -> str:
        """Find semantic concept group using word vector similarity."""
        similarity_threshold = 0.6
        
        if token.has_vector:
            # Compare with previously processed tokens
            for processed_token, existing_key in processed_tokens:
                if processed_token.has_vector:
                    similarity = token.similarity(processed_token)
                    if similarity > similarity_threshold:
                        return existing_key
        
        # Create new concept group
        return f"semantic_{token.lemma_.lower()}_{token.pos_}"
    
    def _analyze_concept_usage_patterns(self, terminology_map, doc, sentences) -> Dict[str, Dict[str, Any]]:
        """Analyze how concepts are used across the document."""
        usage_patterns = {}
        
        for concept_key, concept_terms in terminology_map.items():
            if len(concept_terms) > 1:  # Only analyze concepts with multiple instances
                pattern_data = {
                    'terms': concept_terms,
                    'usage_frequency': self._calculate_usage_frequency(concept_terms),
                    'context_similarity': self._analyze_context_similarity(concept_terms, doc),
                    'sentence_distribution': self._analyze_sentence_distribution(concept_terms, sentences),
                    'semantic_consistency': self._analyze_semantic_consistency(concept_terms)
                }
                
                usage_patterns[concept_key] = pattern_data
        
        return usage_patterns
    
    def _calculate_usage_frequency(self, concept_terms) -> Dict[str, int]:
        """Calculate frequency of each term variant."""
        frequency = defaultdict(int)
        
        for term in concept_terms:
            term_key = term['text'].lower()
            frequency[term_key] += 1
        
        return dict(frequency)
    
    def _analyze_context_similarity(self, concept_terms, doc) -> Dict[str, float]:
        """Analyze context similarity between term usages."""
        context_analysis = {}
        
        # Compare contexts where terms appear
        for i, term1 in enumerate(concept_terms):
            for j, term2 in enumerate(concept_terms[i+1:], i+1):
                context_sim = self._calculate_context_similarity(term1, term2, doc)
                pair_key = f"{term1['text']}_vs_{term2['text']}"
                context_analysis[pair_key] = context_sim
        
        return context_analysis
    
    def _calculate_context_similarity(self, term1, term2, doc) -> float:
        """Calculate similarity between contexts of two terms."""
        # Get context windows around each term
        context1 = self._extract_context_window(term1, doc)
        context2 = self._extract_context_window(term2, doc)
        
        if context1 and context2:
            # Calculate semantic similarity of contexts
            if hasattr(context1, 'similarity') and hasattr(context2, 'similarity'):
                return context1.similarity(context2)
        
        return 0.0
    
    def _extract_context_window(self, term, doc, window_size=5):
        """Extract context window around a term."""
        if 'start' in term and 'end' in term:
            start_idx = max(0, term['start'] - window_size)
            end_idx = min(len(doc), term['end'] + window_size)
            return doc[start_idx:end_idx]
        elif 'index' in term:
            start_idx = max(0, term['index'] - window_size)
            end_idx = min(len(doc), term['index'] + window_size + 1)
            return doc[start_idx:end_idx]
        
        return None
    
    def _analyze_sentence_distribution(self, concept_terms, sentences) -> Dict[str, List[int]]:
        """Analyze distribution of terms across sentences."""
        distribution = defaultdict(list)
        
        for sentence_idx, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            for term in concept_terms:
                if term['text'].lower() in sentence_lower:
                    distribution[term['text']].append(sentence_idx)
        
        return dict(distribution)
    
    def _analyze_semantic_consistency(self, concept_terms) -> Dict[str, float]:
        """Analyze semantic consistency between term variants."""
        consistency_scores = {}
        
        # Compare semantic similarity between all term pairs
        for i, term1 in enumerate(concept_terms):
            for j, term2 in enumerate(concept_terms[i+1:], i+1):
                if (term1.get('vector') is not None and 
                    term2.get('vector') is not None):
                    # Calculate vector similarity
                    sim_score = self._calculate_vector_similarity(term1['vector'], term2['vector'])
                    pair_key = f"{term1['text']}_vs_{term2['text']}"
                    consistency_scores[pair_key] = sim_score
        
        return consistency_scores
    
    def _calculate_vector_similarity(self, vector1, vector2) -> float:
        """Calculate similarity between word vectors."""
        try:
            import numpy as np
            # Calculate cosine similarity
            dot_product = np.dot(vector1, vector2)
            norm1 = np.linalg.norm(vector1)
            norm2 = np.linalg.norm(vector2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except:
            return 0.0
    
    def _detect_concept_inconsistencies(self, concept_group, usage_data, doc) -> List[Dict[str, Any]]:
        """Detect inconsistencies within a concept group."""
        inconsistencies = []
        
        terms = usage_data['terms']
        frequency = usage_data['usage_frequency']
        sentence_distribution = usage_data['sentence_distribution']
        
        # Method 1: Detect frequency-based inconsistencies
        frequency_inconsistencies = self._detect_frequency_inconsistencies(terms, frequency, sentence_distribution)
        inconsistencies.extend(frequency_inconsistencies)
        
        # Method 2: Detect context-based inconsistencies
        context_inconsistencies = self._detect_context_inconsistencies(terms, usage_data, doc)
        inconsistencies.extend(context_inconsistencies)
        
        # Method 3: Detect semantic drift inconsistencies
        semantic_inconsistencies = self._detect_semantic_inconsistencies(terms, usage_data)
        inconsistencies.extend(semantic_inconsistencies)
        
        return inconsistencies
    
    def _detect_frequency_inconsistencies(self, terms, frequency, sentence_distribution) -> List[Dict[str, Any]]:
        """Detect inconsistencies based on usage frequency patterns."""
        inconsistencies = []
        
        if len(frequency) > 1:  # Multiple variants exist
            # Find the most frequent term (likely the preferred one)
            most_frequent_term = max(frequency.keys(), key=frequency.get)
            max_frequency = frequency[most_frequent_term]
            
            # Check for minority variants that should be standardized
            for term_text, freq in frequency.items():
                if term_text != most_frequent_term and freq < max_frequency * 0.5:
                    # This is a minority variant
                    inconsistency = {
                        'type': 'frequency_inconsistency',
                        'inconsistent_term': term_text,
                        'preferred_term': most_frequent_term,
                        'inconsistent_frequency': freq,
                        'preferred_frequency': max_frequency,
                        'sentence_occurrences': sentence_distribution.get(term_text, []),
                        'concept_group': terms
                    }
                    inconsistencies.append(inconsistency)
        
        return inconsistencies
    
    def _detect_context_inconsistencies(self, terms, usage_data, doc) -> List[Dict[str, Any]]:
        """Detect inconsistencies based on context analysis."""
        inconsistencies = []
        
        context_similarity = usage_data.get('context_similarity', {})
        
        # Find term pairs with high context similarity but different forms
        for pair_key, similarity in context_similarity.items():
            if similarity > 0.8:  # High context similarity threshold
                term1, term2 = pair_key.split('_vs_')
                if term1.lower() != term2.lower():  # Different terms in similar contexts
                    # Skip if it's just plural vs singular variation
                    if not self._is_plural_singular_variation(term1, term2):
                        inconsistency = {
                            'type': 'context_inconsistency',
                            'term_pair': [term1, term2],
                            'context_similarity': similarity,
                            'concept_group': terms,
                            'recommendation': 'standardize_usage'
                        }
                        inconsistencies.append(inconsistency)
        
        return inconsistencies
    
    def _is_plural_singular_variation(self, term1: str, term2: str) -> bool:
        """Check if two terms are just plural/singular variations."""
        import re
        
        # Normalize terms by removing articles and converting to lowercase
        clean_term1 = re.sub(r'^(the|a|an)\s+', '', term1.lower()).strip()
        clean_term2 = re.sub(r'^(the|a|an)\s+', '', term2.lower()).strip()
        
        # Check common plural patterns
        if clean_term1 + 's' == clean_term2 or clean_term2 + 's' == clean_term1:
            return True
        
        # Check irregular plurals (basic cases)
        irregular_pairs = [
            ('person', 'people'), ('child', 'children'), ('man', 'men'), 
            ('woman', 'women'), ('foot', 'feet'), ('tooth', 'teeth'),
            ('mouse', 'mice'), ('goose', 'geese')
        ]
        
        for singular, plural in irregular_pairs:
            if (clean_term1 == singular and clean_term2 == plural) or \
               (clean_term1 == plural and clean_term2 == singular):
                return True
        
        return False
    
    def _detect_semantic_inconsistencies(self, terms, usage_data) -> List[Dict[str, Any]]:
        """Detect semantic drift inconsistencies."""
        inconsistencies = []
        
        semantic_consistency = usage_data.get('semantic_consistency', {})
        
        # Find semantically similar terms that should be unified
        for pair_key, consistency_score in semantic_consistency.items():
            if consistency_score > 0.7:  # High semantic similarity
                term1, term2 = pair_key.split('_vs_')
                if term1.lower() != term2.lower():
                    inconsistency = {
                        'type': 'semantic_inconsistency',
                        'similar_terms': [term1, term2],
                        'semantic_similarity': consistency_score,
                        'concept_group': terms,
                        'recommendation': 'choose_primary_term'
                    }
                    inconsistencies.append(inconsistency)
        
        return inconsistencies
    
    def _generate_consistency_suggestions(self, issue: Dict[str, Any], doc=None) -> List[str]:
        """Generate suggestions for consistency issues."""
        suggestions = []
        
        issue_type = issue.get('type', '')
        
        if issue_type == 'frequency_inconsistency':
            inconsistent_term = issue.get('inconsistent_term', '')
            preferred_term = issue.get('preferred_term', '')
            suggestions.append(f"Replace '{inconsistent_term}' with '{preferred_term}' for consistency")
            suggestions.append(f"Standardize on '{preferred_term}' throughout the document")
            suggestions.append("Maintain consistent terminology to improve clarity")
        
        elif issue_type == 'context_inconsistency':
            term_pair = issue.get('term_pair', [])
            if len(term_pair) == 2:
                suggestions.append(f"Choose either '{term_pair[0]}' or '{term_pair[1]}' and use consistently")
                suggestions.append("Avoid using synonyms for the same concept in similar contexts")
        
        elif issue_type == 'semantic_inconsistency':
            similar_terms = issue.get('similar_terms', [])
            if len(similar_terms) == 2:
                suggestions.append(f"Unify usage of '{similar_terms[0]}' and '{similar_terms[1]}'")
                suggestions.append("Select one primary term and use it consistently throughout")
        
        # General consistency suggestions
        suggestions.append("Create a terminology glossary to maintain consistency")
        suggestions.append("Review document for other instances of terminology variation")
        
        return suggestions
    
    def _create_consistency_message(self, issue: Dict[str, Any]) -> str:
        """Create message describing the consistency issue."""
        issue_type = issue.get('type', '')
        
        if issue_type == 'frequency_inconsistency':
            inconsistent_term = issue.get('inconsistent_term', '')
            preferred_term = issue.get('preferred_term', '')
            return f"Inconsistent terminology: '{inconsistent_term}' vs '{preferred_term}'"
        
        elif issue_type == 'context_inconsistency':
            term_pair = issue.get('term_pair', [])
            if len(term_pair) == 2:
                return f"Inconsistent terms in similar contexts: '{term_pair[0]}' vs '{term_pair[1]}'"
        
        elif issue_type == 'semantic_inconsistency':
            similar_terms = issue.get('similar_terms', [])
            if len(similar_terms) == 2:
                return f"Synonymous terms used inconsistently: '{similar_terms[0]}' vs '{similar_terms[1]}'"
        
        return "Terminology inconsistency detected"
    
    def _determine_consistency_severity(self, issue: Dict[str, Any]) -> str:
        """Determine severity of consistency issue."""
        issue_type = issue.get('type', '')
        
        if issue_type == 'frequency_inconsistency':
            preferred_freq = issue.get('preferred_frequency', 1)
            inconsistent_freq = issue.get('inconsistent_frequency', 1)
            
            # Higher frequency difference = higher severity
            if preferred_freq / inconsistent_freq >= 5:
                return 'medium'
            else:
                return 'low'
        
        elif issue_type == 'context_inconsistency':
            similarity = issue.get('context_similarity', 0)
            if similarity > 0.9:
                return 'high'
            else:
                return 'medium'
        
        elif issue_type == 'semantic_inconsistency':
            similarity = issue.get('semantic_similarity', 0)
            if similarity > 0.8:
                return 'medium'
            else:
                return 'low'
        
        return 'info'
    
    def _find_terminology_inconsistencies_fallback(self, text: str, sentences: List[str]) -> List[Dict[str, Any]]:
        """Fallback consistency detection when SpaCy unavailable."""
        import re
        from collections import Counter
        
        inconsistencies = []
        
        # Very basic approach: find similar words that might be inconsistent
        words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
        word_freq = Counter(words)
        
        # Look for words that appear multiple times
        for word, freq in word_freq.items():
            if freq > 1:
                # Very basic inconsistency detection
                similar_words = [w for w in word_freq.keys() if w != word and w[:3] == word[:3]]
                if similar_words:
                    inconsistencies.append({
                        'type': 'basic_inconsistency',
                        'term': word,
                        'similar_terms': similar_words,
                        'frequency': freq,
                        'sentence_index': 0
                    })
        
        return inconsistencies[:5]  # Limit to avoid too many false positives
    
    def _extract_ai_ml_concepts(self, doc) -> Dict[str, List[Dict[str, Any]]]:
        """Extract AI/ML related concepts that might be missed by standard NER."""
        ai_ml_concepts = defaultdict(list)
        
        # Define AI/ML term groups using domain knowledge
        ai_terms = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning', 'neural network']
        
        text_lower = doc.text.lower()
        
        # Find AI/ML terms in the text
        found_terms = []
        for term in ai_terms:
            if term in text_lower:
                # Find actual positions in the document
                for token in doc:
                    if term.replace(' ', '') in token.text.lower() or \
                       (len(term.split()) > 1 and term.split()[0] in token.text.lower()):
                        found_terms.append({
                            'text': token.text,
                            'lemma': token.lemma_.lower(),
                            'pos': token.pos_,
                            'index': token.i,
                            'vector': token.vector if token.has_vector else None,
                            'type': 'ai_ml_term'
                        })
        
        if found_terms:
            ai_ml_concepts['ai_ml_concept'].extend(found_terms)
        
        return ai_ml_concepts 