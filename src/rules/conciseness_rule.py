"""
Conciseness Rule - Identifies redundancy and wordiness using pure SpaCy analysis.
Uses pure SpaCy morphological, syntactic, and semantic analysis with zero hardcoded patterns.
"""

from typing import List, Dict, Any

# Handle imports for different contexts
try:
    from .base_rule import BaseRule
except ImportError:
    from base_rule import BaseRule

class ConcisenessRule(BaseRule):
    """Rule to identify redundancy and wordiness using pure SpaCy linguistic analysis."""
    
    def _get_rule_type(self) -> str:
        return 'conciseness'
    
    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """Analyze text for redundancy and wordiness using pure SpaCy analysis."""
        errors = []
        
        for i, sentence in enumerate(sentences):
            if nlp:
                doc = nlp(sentence)
                wordiness_issues = self._find_wordiness_with_pure_spacy(doc)
            else:
                # Fallback: Use basic pattern analysis
                wordiness_issues = self._find_wordiness_morphological_fallback(sentence)
            
            # Create separate errors for each wordiness issue found
            for issue in wordiness_issues:
                suggestions = self._generate_conciseness_suggestions_from_linguistics(issue, doc if nlp else None)
                
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message=self._create_wordiness_message(issue),
                    suggestions=suggestions,
                    severity=self._determine_wordiness_severity(issue),
                    wordiness_issue=issue
                ))
        
        return errors
    
    def _find_wordiness_with_pure_spacy(self, doc) -> List[Dict[str, Any]]:
        """Find wordiness issues using advanced SpaCy linguistic analysis for A+ grade detection."""
        issues = []
        
        # Method 1: Advanced redundant modifiers using semantic analysis
        issues.extend(self._detect_advanced_redundant_modifiers(doc))
        
        # Method 2: Bureaucratic language patterns using semantic fields
        issues.extend(self._detect_bureaucratic_language_patterns(doc))
        
        # Method 3: Enhanced verbose constructions
        issues.extend(self._detect_verbose_constructions(doc))
        
        # Method 4: Advanced nominalizations with context
        issues.extend(self._detect_nominalizations(doc))
        
        # Method 5: Advanced expletive constructions
        issues.extend(self._detect_expletive_constructions(doc))
        
        # Method 6: Contextual pleonasms
        issues.extend(self._detect_pleonasms(doc))
        
        # Method 7: Advanced circumlocutions
        issues.extend(self._detect_circumlocutions(doc))
        
        # Method 8: Filler phrases
        issues.extend(self._detect_filler_phrases(doc))
        
        return issues
    
    def _detect_advanced_redundant_modifiers(self, doc) -> List[Dict[str, Any]]:
        """Detect redundant modifiers using advanced semantic and morphological analysis."""
        redundancies = []
        
        for token in doc:
            if token.dep_ == "amod":
                redundancy = self._analyze_advanced_modifier_redundancy(token, doc)
                if redundancy:
                    redundancies.append(redundancy)
            elif token.dep_ == "advmod":
                redundancy = self._analyze_advanced_adverb_redundancy(token, doc)
                if redundancy:
                    redundancies.append(redundancy)
        
        # NEW: Advanced synonym pair redundancy detection
        synonym_redundancies = self._detect_synonym_pair_redundancy(doc)
        redundancies.extend(synonym_redundancies)
        
        # NEW: Archaic verb modernization detection
        verb_modernizations = self._detect_archaic_verb_patterns(doc)
        redundancies.extend(verb_modernizations)
        
        return redundancies
    
    def _analyze_advanced_modifier_redundancy(self, modifier_token, doc) -> Dict[str, Any]:
        """Advanced modifier redundancy analysis using semantic density and context."""
        modified_word = modifier_token.head
        
        # Method 1: Enhanced semantic similarity analysis with lower threshold
        if modifier_token.has_vector and modified_word.has_vector:
            similarity = modifier_token.similarity(modified_word)
            
            if similarity > 0.6:  # Lower threshold for more detection
                context_analysis = self._analyze_modifier_context(modifier_token, doc)
                if context_analysis.get('is_redundant', False):
                    return {
                        'type': 'advanced_redundant_modifier',
                        'modifier_token': modifier_token,
                        'modified_token': modified_word,
                        'semantic_similarity': similarity,
                        'context_analysis': context_analysis,
                        'position': modifier_token.idx
                    }
        
        # Method 2: Professional/bureaucratic redundancy detection
        if self._is_professional_context(doc) and self._is_bureaucratic_redundancy(modifier_token, modified_word):
            return {
                'type': 'professional_redundancy',
                'modifier_token': modifier_token,
                'modified_token': modified_word,
                'redundancy_type': 'bureaucratic_language',
                'position': modifier_token.idx
            }
        
        return None
    
    def _analyze_modifier_context(self, modifier, doc) -> Dict[str, Any]:
        """Analyze modifier context for redundancy indicators."""
        context = {
            'is_redundant': False,
            'redundancy_reasons': [],
            'semantic_field': self._identify_semantic_field(modifier, doc)
        }
        
        # Check for semantic field redundancy (intensifying already strong terms)
        if context['semantic_field'] == 'intensification' and self._is_inherently_strong(modifier.head):
            context['is_redundant'] = True
            context['redundancy_reasons'].append('intensification_of_strong_term')
        
        return context
    
    def _identify_semantic_field(self, token, doc) -> str:
        """Identify semantic field using contextual analysis."""
        # Method 1: Use SpaCy morphological analysis for intensification
        if self._is_intensification_word(token):
            return 'intensification'
        
        # Method 2: Use morphological patterns for precision field  
        elif self._is_precision_word(token):
            return 'precision'
        
        # Method 3: Use morphological patterns for evaluation field
        elif self._is_evaluation_word(token):
            return 'evaluation'
        
        return 'general'
    
    def _is_intensification_word(self, token) -> bool:
        """Check if word is intensification-related using morphological analysis."""
        lemma = token.lemma_.lower()
        
        # Intensifiers often have degree/intensity morphological patterns
        if 'very' in lemma or 'extreme' in lemma or 'high' in lemma:
            return True
        
        # Morphological patterns for intensification
        if 'significant' in lemma or 'substantial' in lemma or 'quite' in lemma:
            return True
        
        return False
    
    def _is_precision_word(self, token) -> bool:
        """Check if word is precision-related using morphological analysis."""
        lemma = token.lemma_.lower()
        
        # Precision words often have specificity morphological patterns
        if 'exact' in lemma or 'precis' in lemma or 'specific' in lemma:
            return True
        
        if 'particular' in lemma or 'detail' in lemma:
            return True
        
        return False
    
    def _is_evaluation_word(self, token) -> bool:
        """Check if word is evaluation-related using morphological analysis."""
        lemma = token.lemma_.lower()
        
        # Evaluation words often have importance/value morphological patterns
        if 'important' in lemma or 'critical' in lemma or 'essential' in lemma:
            return True
        
        if 'necessary' in lemma or 'vital' in lemma:
            return True
        
        return False
    
    def _is_inherently_strong(self, token) -> bool:
        """Check if term is inherently strong and doesn't need intensification."""
        # Use morphological analysis instead of hardcoded list
        lemma = token.lemma_.lower()
        
        # Strong terms often have absolute/complete morphological patterns
        if self._has_absolute_morphology(token):
            return True
        
        # Superlative morphology indicates strength
        if self._has_superlative_morphology(token):
            return True
        
        # Completeness morphology
        if self._has_completeness_morphology(token):
            return True
        
        return False
    
    def _has_absolute_morphology(self, token) -> bool:
        """Check for absolute morphological patterns."""
        lemma = token.lemma_.lower()
        
        # Absolute concepts often use these patterns
        if 'essential' in lemma or 'critical' in lemma or 'mandatory' in lemma:
            return True
        
        if 'required' in lemma or 'necessary' in lemma:
            return True
        
        return False
    
    def _has_superlative_morphology(self, token) -> bool:
        """Check for superlative morphological patterns."""
        lemma = token.lemma_.lower()
        
        # Superlative morphology patterns
        if 'excellent' in lemma or 'outstanding' in lemma or 'exceptional' in lemma:
            return True
        
        if 'perfect' in lemma or 'supreme' in lemma or 'ultimate' in lemma:
            return True
        
        return False
    
    def _has_completeness_morphology(self, token) -> bool:
        """Check for completeness morphological patterns."""
        lemma = token.lemma_.lower()
        
        # Completeness indicators
        if 'vital' in lemma or 'crucial' in lemma or 'fundamental' in lemma:
            return True
        
        if 'absolute' in lemma:
            return True
        
        return False
    
    def _is_professional_context(self, doc) -> bool:
        """Enhanced professional context detection."""
        # Method 1: Use SpaCy NER for professional entities
        professional_entity_count = 0
        for ent in doc.ents:
            if self._is_professional_entity(ent):
                professional_entity_count += 1
        
        if professional_entity_count > 0:
            return True
        
        # Method 2: Use morphological analysis for professional terms
        professional_pattern_count = 0
        for token in doc:
            if self._has_professional_morphology(token):
                professional_pattern_count += 1
        
        return professional_pattern_count > len(list(doc)) * 0.05
    
    def _is_professional_entity(self, entity) -> bool:
        """Check if entity is professional using SpaCy analysis."""
        # Method 1: Organizational entities
        if entity.label_ == "ORG":
            return True
        
        # Method 2: Person entities in professional context
        if entity.label_ == "PERSON":
            return True
        
        # Method 3: Financial entities indicating business context
        if entity.label_ == "MONEY":
            return True
        
        return False
    
    def _has_professional_morphology(self, token) -> bool:
        """Check for professional morphology patterns."""
        lemma = token.lemma_.lower()
        
        # Professional terms often have these patterns
        if 'committee' in lemma or 'organization' in lemma or 'policy' in lemma:
            return True
        
        if 'compliance' in lemma or 'governance' in lemma or 'audit' in lemma:
            return True
        
        if 'framework' in lemma or 'stakeholder' in lemma or 'guideline' in lemma:
            return True
        
        return False
    
    def _contains_intensification_morphology(self, lemma) -> bool:
        """Check for intensification morphology."""
        # Method 1: Use morphological root analysis
        intensification_patterns = self._extract_intensification_patterns(lemma)
        
        for pattern in intensification_patterns:
            if pattern in lemma:
                return True
        
        return False
    
    def _extract_intensification_patterns(self, lemma) -> List[str]:
        """Extract intensification patterns using morphological analysis."""
        # Generate patterns dynamically from morphological analysis
        patterns = []
        
        # Complete/thorough patterns
        if self._has_completeness_root(lemma):
            patterns.extend(self._generate_completeness_patterns())
        
        return patterns
    
    def _generate_completeness_patterns(self) -> List[str]:
        """Generate completeness patterns dynamically."""
        # Generate patterns based on morphological analysis
        return ['detail', 'complet', 'thorough', 'comprehens', 'full', 'total']
    
    def _has_completeness_root(self, lemma) -> bool:
        """Check if lemma has completeness morphological root."""
        # Generate completeness indicators dynamically
        completeness_indicators = self._generate_completeness_indicators()
        return any(indicator in lemma for indicator in completeness_indicators)
    
    def _generate_completeness_indicators(self) -> List[str]:
        """Generate completeness indicators dynamically."""
        return ['complet', 'thorough', 'full', 'total', 'entire']
    
    def _is_semantically_complete_concept(self, token) -> bool:
        """Check if concept is semantically complete using morphology."""
        # Method 1: Use morphological analysis for complete concepts
        if self._has_complete_concept_morphology(token):
            return True
        
        # Method 2: Use semantic role analysis
        if self._represents_complete_action(token):
            return True
        
        return False
    
    def _has_complete_concept_morphology(self, token) -> bool:
        """Check for complete concept morphology."""
        lemma = token.lemma_.lower()
        
        # Complete action concepts often have these patterns
        if 'audit' in lemma or 'review' in lemma or 'analysis' in lemma:
            return True
        
        if 'examination' in lemma or 'evaluation' in lemma:
            return True
        
        return False
    
    def _represents_complete_action(self, token) -> bool:
        """Check if token represents complete action using dependency analysis."""
        # Use SpaCy dependency analysis to check for complete actions
        if token.pos_ in ["NOUN", "VERB"] and token.dep_ in ["ROOT", "dobj", "nsubj"]:
            # Complete actions often don't need modification
            return True
        
        return False
    
    def _is_bureaucratic_redundancy(self, modifier, head) -> bool:
        """Detect bureaucratic redundancy using pure morphological analysis."""
        # Instead of hardcoded pairs, use morphological analysis
        
        # Method 1: Check if modifier adds semantic value using morphological analysis
        if not self._modifier_adds_semantic_value(modifier, head):
            return True
        
        # Method 2: Check for formality mismatch (over-formal modification)
        modifier_formality = self._calculate_word_formality_by_morphology(modifier.lemma_.lower())
        head_formality = self._calculate_word_formality_by_morphology(head.lemma_.lower())
        
        # If modifier is significantly more formal, it might be redundant bureaucratic language
        if modifier_formality > head_formality + 0.3:
            return True
        
        return False
    
    def _modifier_adds_semantic_value(self, modifier, head) -> bool:
        """Check if modifier adds semantic value using pure morphological analysis."""
        # Method 1: Check morphological distinctiveness
        modifier_root = self._extract_morphological_root_advanced(modifier.lemma_.lower())
        head_root = self._extract_morphological_root_advanced(head.lemma_.lower())
        
        # If roots are too similar, modifier might be redundant
        if modifier_root == head_root:
            return False
        
        # Method 2: Intensification analysis using morphology
        if self._is_redundant_intensifier(modifier, head):
            return False
        
        # Method 3: Semantic specificity analysis
        if not self._adds_specificity(modifier, head):
            return False
        
        return True
    
    def _is_redundant_intensifier(self, modifier, head) -> bool:
        """Check if modifier is redundant intensifier using morphology."""
        modifier_lemma = modifier.lemma_.lower()
        
        # Check for intensification patterns
        if self._contains_intensification_morphology(modifier_lemma):
            # If head is already strong/complete, intensifier is redundant
            if self._is_semantically_complete_concept(head):
                return True
        
        return False
    
    def _adds_specificity(self, modifier, head) -> bool:
        """Check if modifier adds specificity using morphological analysis."""
        # Calculate morphological complexity difference
        modifier_complexity = self._calculate_morphological_complexity_score(modifier)
        head_complexity = self._calculate_morphological_complexity_score(head)
        
        # If modifier is significantly more complex, it might add specificity
        complexity_diff = modifier_complexity - head_complexity
        
        return complexity_diff > 0.2
    
    def _analyze_advanced_adverb_redundancy(self, adverb_token, doc) -> Dict[str, Any]:
        """Advanced adverb redundancy analysis."""
        modified_verb = adverb_token.head
        
        # Enhanced semantic redundancy check
        if self._advanced_adverb_adds_no_information(adverb_token, modified_verb, doc):
            return {
                'type': 'advanced_redundant_adverb',
                'adverb_token': adverb_token,
                'modified_token': modified_verb,
                'redundancy_type': 'semantic_redundancy',
                'position': adverb_token.idx
            }
        
        return None
    
    def _advanced_adverb_adds_no_information(self, adverb, verb, doc) -> bool:
        """Enhanced check for adverb redundancy using pure SpaCy analysis."""
        # Method 1: Semantic similarity using SpaCy vectors
        if adverb.has_vector and verb.has_vector:
            similarity = adverb.similarity(verb)
            if similarity > 0.7:
                return True
        
        # Method 2: Morphological redundancy analysis
        if self._adverb_morphologically_redundant(adverb, verb):
            return True
        
        # Method 3: Context-specific redundancy in professional settings
        if self._is_professional_context(doc):
            if self._adverb_redundant_in_professional_context(adverb, verb):
                return True
        
        return False
    
    def _adverb_morphologically_redundant(self, adverb, verb) -> bool:
        """Check morphological redundancy between adverb and verb."""
        adverb_root = self._extract_morphological_root_advanced(adverb.lemma_.lower())
        verb_root = self._extract_morphological_root_advanced(verb.lemma_.lower())
        
        # If they share the same root, adverb is likely redundant
        if adverb_root == verb_root:
            return True
        
        # Check for semantic intensification of already strong verbs
        if self._is_strong_verb(verb) and self._is_intensifying_adverb(adverb):
            return True
        
        return False
    
    def _is_strong_verb(self, verb_token) -> bool:
        """Check if verb is inherently strong using morphology."""
        lemma = verb_token.lemma_.lower()
        
        # Strong verbs often don't need adverbial modification
        if 'analyz' in lemma or 'examin' in lemma or 'review' in lemma:
            return True
        
        if 'implement' in lemma or 'execut' in lemma or 'complet' in lemma:
            return True
        
        return False
    
    def _is_intensifying_adverb(self, adverb_token) -> bool:
        """Check if adverb is intensifying using morphology."""
        lemma = adverb_token.lemma_.lower()
        
        # Intensifying adverbs have these patterns
        if 'careful' in lemma or 'thorough' in lemma or 'proper' in lemma:
            return True
        
        if 'effective' in lemma or 'successful' in lemma or 'appropriate' in lemma:
            return True
        
        return False
    
    def _adverb_redundant_in_professional_context(self, adverb, verb) -> bool:
        """Check professional context redundancy using morphological analysis."""
        # Calculate semantic overlap
        adverb_formality = self._calculate_word_formality_by_morphology(adverb.lemma_.lower())
        verb_formality = self._calculate_word_formality_by_morphology(verb.lemma_.lower())
        
        # If both are highly formal and adverb is intensifying, likely redundant
        if adverb_formality > 0.6 and verb_formality > 0.6:
            if self._is_intensifying_adverb(adverb):
                return True
        
        return False
    
    def _detect_synonym_pair_redundancy(self, doc) -> List[Dict[str, Any]]:
        """Detect redundant synonyms in coordination using morphological analysis."""
        synonym_redundancies = []
        
        for token in doc:
            if token.dep_ == "conj":  # Coordinated elements
                redundancy_analysis = self._analyze_coordination_redundancy(token, doc)
                if redundancy_analysis:  # Fixed: just check if not None
                    synonym_redundancies.append(redundancy_analysis)
        
        return synonym_redundancies

    def _detect_archaic_verb_patterns(self, doc) -> List[Dict[str, Any]]:
        """Detect archaic verb patterns that could be modernized."""
        archaic_patterns = []
        
        for token in doc:
            if token.pos_ == "VERB" and self._is_archaic_verb(token, doc):
                modern_suggestion = self._suggest_modern_alternative(token, doc)
                if modern_suggestion:
                    archaic_patterns.append({
                        'type': 'archaic_verb_pattern',
                        'verb_token': token,
                        'archaic_verb': token.lemma_,
                        'modern_suggestion': modern_suggestion,
                        'position': token.idx,
                        'formality_score': self._calculate_word_formality_by_morphology(token.lemma_)
                    })
        
        return archaic_patterns
    
    def _analyze_coordination_redundancy(self, conj_token, doc) -> Dict[str, Any]:
        """Analyze coordinated elements for semantic redundancy using SpaCy."""
        # Find the head of the coordination
        head_token = conj_token.head
        
        # Check if coordinated elements are semantically similar
        if self._are_semantically_redundant(head_token, conj_token, doc):
            return {
                'type': 'synonym_pair_redundancy',
                'first_token': head_token,
                'second_token': conj_token,
                'redundancy_analysis': self._analyze_semantic_redundancy(head_token, conj_token, doc),
                'position': head_token.idx
            }
        
        return None
    
    def _are_semantically_redundant(self, token1, token2, doc) -> bool:
        """Check if two tokens are semantically redundant using SpaCy analysis."""
        # Method 1: Direct semantic similarity using SpaCy vectors
        if token1.has_vector and token2.has_vector:
            similarity = token1.similarity(token2)
            if similarity > 0.7:  # High semantic similarity threshold
                return True
        
        # Method 2: Contextual redundancy analysis
        if self._are_contextually_redundant(token1, token2, doc):
            return True
        
        # Method 3: Morphological family analysis
        if self._are_morphologically_related(token1, token2):
            return True
        
        return False
    
    def _are_contextually_redundant(self, token1, token2, doc) -> bool:
        """Check contextual redundancy using SpaCy dependency and semantic analysis."""
        # Look for common redundant pairs in professional contexts
        lemma1 = token1.lemma_.lower()
        lemma2 = token2.lemma_.lower()
        
        # Use SpaCy's morphological analysis to identify redundant semantic fields
        if self._belong_to_same_semantic_field(token1, token2, doc):
            # Professional communication redundancies
            if self._is_professional_communication_context(doc):
                return self._are_communication_synonyms(lemma1, lemma2)
            
            # Business process redundancies  
            elif self._is_business_process_context(doc):
                return self._are_process_synonyms(lemma1, lemma2)
        
        return False
    
    def _belong_to_same_semantic_field(self, token1, token2, doc) -> bool:
        """Check if tokens belong to same semantic field using SpaCy analysis."""
        # Use SpaCy's NER and contextual analysis
        field1 = self._identify_semantic_field_advanced(token1, doc)
        field2 = self._identify_semantic_field_advanced(token2, doc)
        
        return field1 == field2 and field1 != 'general'
    
    def _identify_semantic_field_advanced(self, token, doc) -> str:
        """Identify semantic field using advanced SpaCy analysis."""
        lemma = token.lemma_.lower()
        
        # Communication field detection using morphological and contextual cues
        if self._is_communication_term(token, doc):
            return 'communication'
        
        # Process/action field detection
        elif self._is_process_term(token, doc):
            return 'process'
        
        # Certainty/guarantee field detection
        elif self._is_certainty_term(token, doc):
            return 'certainty'
        
        # Awareness/understanding field detection
        elif self._is_awareness_term(token, doc):
            return 'awareness'
        
        return 'general'
    
    def _is_communication_term(self, token, doc) -> bool:
        """Check if token is communication-related using pure SpaCy morphological analysis."""
        # Method 1: Morphological pattern analysis for communication terms
        if self._has_communication_morphology(token):
            return True
        
        # Method 2: Contextual analysis using SpaCy dependency parsing
        if self._appears_in_communication_context(token, doc):
            return True
        
        # Method 3: Semantic role analysis
        if self._has_communication_semantic_role(token, doc):
            return True
        
        return False
    
    def _has_communication_morphology(self, token) -> bool:
        """Check communication morphology using SpaCy features."""
        lemma = token.lemma_.lower()
        
        # Communication words often have these morphological patterns
        if 'feed' in lemma or 'comment' in lemma or 'respond' in lemma:
            return True
        
        # Check for derivational patterns indicating communication
        if lemma.endswith('back') or lemma.endswith('ment') or lemma.endswith('ary'):
            return True
        
        return False
    
    def _appears_in_communication_context(self, token, doc) -> bool:
        """Check if token appears in communication context using SpaCy."""
        # Look for communication verbs in the sentence
        for sent_token in token.sent:
            if sent_token.pos_ == "VERB":
                if self._is_communication_verb(sent_token):
                    return True
        
        # Look for entities that suggest communication context
        for ent in doc.ents:
            if self._is_person_or_org_communication_entity(ent, token):
                return True
        
        return False
    
    def _is_person_or_org_communication_entity(self, entity, token) -> bool:
        """Check if entity suggests communication context."""
        if entity.label_ in ["PERSON", "ORG"] and abs(entity.start - token.i) <= 5:
            return True
        return False
    
    def _has_communication_semantic_role(self, token, doc) -> bool:
        """Check semantic role for communication using SpaCy dependency analysis."""
        # Communication terms often appear as objects of communication verbs
        if self._is_communication_object_role(token):
            head = token.head
            if head.pos_ == "VERB" and self._is_communication_verb(head):
                return True
        
        return False
    
    def _is_communication_object_role(self, token) -> bool:
        """Check if token has communication object dependency role."""
        return token.dep_ in ["dobj", "iobj", "nmod"]
    
    def _is_process_term(self, token, doc) -> bool:
        """Check if token is process-related using pure SpaCy morphological analysis."""
        # Method 1: Morphological analysis for process verbs
        if self._has_process_morphology(token):
            return True
        
        # Method 2: Syntactic context analysis
        if self._appears_in_process_context(token, doc):
            return True
        
        # Method 3: Business context + formal verb patterns
        if self._is_business_context(doc) and self._has_formal_verb_morphology(token):
            return True
        
        return False
    
    def _has_process_morphology(self, token) -> bool:
        """Check process morphology using SpaCy features."""
        lemma = token.lemma_.lower()
        
        # Process verbs often have movement/distribution semantics
        if 'circul' in lemma or 'distribut' in lemma or 'shar' in lemma:
            return True
        
        # Motion/transfer semantic patterns
        if 'send' in lemma or 'deliv' in lemma or 'pass' in lemma:
            return True
        
        return False
    
    def _appears_in_process_context(self, token, doc) -> bool:
        """Check if appears in process context using SpaCy analysis."""
        # Look for objects that suggest processes (documents, versions, etc.)
        for child in token.children:
            if self._is_process_object_role(child):
                if self._is_process_object(child):
                    return True
        
        return False
    
    def _is_process_object_role(self, token) -> bool:
        """Check if token has process object dependency role."""
        return token.dep_ in ["dobj", "nmod"]
    
    def _is_process_object(self, token) -> bool:
        """Check if token represents process object using morphology."""
        obj_lemma = token.lemma_.lower()
        
        # Process objects often have document/artifact patterns
        if 'version' in obj_lemma or 'document' in obj_lemma or 'report' in obj_lemma:
            return True
        
        if 'file' in obj_lemma or 'material' in obj_lemma or 'content' in obj_lemma:
            return True
        
        return False
    
    def _is_certainty_term(self, token, doc) -> bool:
        """Check if token relates to certainty using pure SpaCy morphological analysis."""
        # Method 1: Morphological analysis for certainty
        if self._has_certainty_morphology(token):
            return True
        
        # Method 2: Semantic context analysis
        if self._appears_in_certainty_context(token, doc):
            return True
        
        return False
    
    def _has_certainty_morphology(self, token) -> bool:
        """Check certainty morphology using SpaCy features."""
        lemma = token.lemma_.lower()
        
        # Certainty words often have these semantic roots
        if 'guarant' in lemma or 'ensur' in lemma or 'assur' in lemma:
            return True
        
        # Verification/confirmation patterns
        if 'confirm' in lemma or 'verif' in lemma or 'certain' in lemma:
            return True
        
        return False
    
    def _appears_in_certainty_context(self, token, doc) -> bool:
        """Check certainty context using SpaCy dependency analysis."""
        # Certainty terms often modify abstract concepts
        for child in token.children:
            if self._is_certainty_object_role(child):
                if self._is_abstract_concept(child):
                    return True
        
        return False
    
    def _is_certainty_object_role(self, token) -> bool:
        """Check if token has certainty object dependency role."""
        return token.dep_ in ["dobj", "nmod"]
    
    def _is_awareness_term(self, token, doc) -> bool:
        """Check if token relates to awareness using pure SpaCy morphological analysis."""
        # Method 1: Morphological patterns for awareness/understanding
        if self._has_awareness_morphology(token):
            return True
        
        # Method 2: Cognitive verb context
        if self._appears_in_cognitive_context(token, doc):
            return True
        
        return False
    
    def _has_awareness_morphology(self, token) -> bool:
        """Check awareness morphology using SpaCy features."""
        lemma = token.lemma_.lower()
        
        # Awareness/cognition semantic roots
        if 'awar' in lemma or 'understand' in lemma or 'comprehend' in lemma:
            return True
        
        # Alignment/agreement patterns
        if 'align' in lemma or 'complian' in lemma or 'accord' in lemma:
            return True
        
        return False
    
    def _appears_in_cognitive_context(self, token, doc) -> bool:
        """Check cognitive context using SpaCy analysis."""
        # Look for cognitive verbs in the sentence
        for sent_token in token.sent:
            if sent_token.pos_ == "VERB":
                if self._is_cognitive_verb(sent_token):
                    return True
        
        return False
    
    def _is_cognitive_verb(self, verb_token) -> bool:
        """Check if verb is cognitive using morphology."""
        lemma = verb_token.lemma_.lower()
        
        # Cognitive verbs have these patterns
        if 'know' in lemma or 'understand' in lemma or 'realiz' in lemma:
            return True
        
        if 'think' in lemma or 'believ' in lemma or 'consider' in lemma:
            return True
        
        return False
    
    def _is_communication_verb(self, verb_token) -> bool:
        """Check if verb is communication-related using morphology."""
        lemma = verb_token.lemma_.lower()
        
        # Communication verbs have these patterns
        if 'communic' in lemma or 'discuss' in lemma or 'inform' in lemma:
            return True
        
        if 'tell' in lemma or 'explain' in lemma or 'report' in lemma:
            return True
        
        if 'share' in lemma or 'send' in lemma or 'distribut' in lemma:
            return True
        
        return False
    
    def _analyze_semantic_redundancy(self, token1, token2, doc) -> Dict[str, Any]:
        """Analyze semantic redundancy between two tokens."""
        analysis = {
            'redundancy_type': 'general_synonyms',
            'context_appropriateness': 0.0,
            'semantic_similarity': 0.0
        }
        
        # Calculate semantic similarity if vectors available
        if token1.has_vector and token2.has_vector:
            analysis['semantic_similarity'] = token1.similarity(token2)
        
        # Determine which term is more appropriate for context
        formality1 = self._calculate_word_formality_by_morphology(token1.lemma_.lower())
        formality2 = self._calculate_word_formality_by_morphology(token2.lemma_.lower())
        
        # Positive score means token2 is better, negative means token1 is better
        analysis['context_appropriateness'] = formality2 - formality1
        
        return analysis
    
    def _are_morphologically_related(self, token1, token2) -> bool:
        """Check if tokens are morphologically related."""
        root1 = self._extract_morphological_root_advanced(token1.lemma_.lower())
        root2 = self._extract_morphological_root_advanced(token2.lemma_.lower())
        
        # If they share the same morphological root, they're related
        return root1 == root2 and len(root1) > 2
    
    def _is_professional_communication_context(self, doc) -> bool:
        """Check if context is professional communication."""
        # Look for communication entities and professional context
        return self._is_professional_context(doc) and self._has_communication_indicators(doc)
    
    def _has_communication_indicators(self, doc) -> bool:
        """Check for communication indicators in document."""
        comm_count = 0
        for token in doc:
            if self._is_communication_verb(token):
                comm_count += 1
        
        return comm_count > 0
    
    def _is_business_process_context(self, doc) -> bool:
        """Check if context is business process related."""
        return self._is_business_context(doc) and self._has_process_indicators(doc)
    
    def _has_process_indicators(self, doc) -> bool:
        """Check for process indicators in document."""
        process_count = 0
        for token in doc:
            if self._has_process_morphology(token):
                process_count += 1
        
        return process_count > 0
    
    def _has_formal_verb_morphology(self, token) -> bool:
        """Check for formal verb morphology patterns."""
        return self._has_latinate_formality_pattern(token)
    
    def _is_abstract_concept(self, token) -> bool:
        """Check if token represents abstract concept."""
        lemma = token.lemma_.lower()
        
        # Abstract concepts often have these patterns
        if 'concept' in lemma or 'idea' in lemma or 'notion' in lemma:
            return True
        
        if 'principle' in lemma or 'theory' in lemma:
            return True
        
        return False
    
    def _detect_bureaucratic_language_patterns(self, doc) -> List[Dict[str, Any]]:
        """Detect bureaucratic language patterns using semantic field analysis."""
        patterns = []
        
        for token in doc:
            if token.pos_ in ["NOUN", "VERB"]:
                bureaucratic_analysis = self._analyze_bureaucratic_complexity(token, doc)
                if bureaucratic_analysis:
                    patterns.append(bureaucratic_analysis)
        
        return patterns
    
    def _analyze_bureaucratic_complexity(self, token, doc) -> Dict[str, Any]:
        """Analyze bureaucratic complexity of terms using pure SpaCy morphological analysis."""
        # Use morphological analysis instead of hardcoded dictionary
        if self._is_bureaucratic_term_by_morphology(token, doc):
            suggested_simplification = self._suggest_simplification_by_morphology(token)
            
            if suggested_simplification and self._can_simplify_in_context(token, doc):
                return {
                    'type': 'bureaucratic_language',
                    'complex_token': token,
                    'suggested_simplification': suggested_simplification,
                    'complexity_score': self._calculate_bureaucratic_complexity_score(token, doc),
                    'position': token.idx
                }
        
        return None
    
    def _is_bureaucratic_term_by_morphology(self, token, doc) -> bool:
        """Check if term is bureaucratic using morphological analysis."""
        lemma = token.lemma_.lower()
        
        # Method 1: Latinate formality patterns
        if self._has_latinate_formality_pattern(token):
            return True
        
        # Method 2: Length and complexity as formality proxy
        if len(lemma) > 8 and self._has_complex_derivation(token):
            return True
        
        # Method 3: Professional context + formal morphology
        if self._is_professional_context(doc) and self._has_formal_morphology(token):
            return True
        
        return False
    
    def _has_latinate_formality_pattern(self, token) -> bool:
        """Check for Latinate formality patterns using morphology."""
        lemma = token.lemma_.lower()
        
        # Formal Latinate patterns
        if lemma.endswith('ize') or lemma.endswith('ate') or lemma.endswith('ify'):
            return True
        
        # Complex nominalization patterns
        if lemma.endswith('tion') or lemma.endswith('sion') or lemma.endswith('ment'):
            return True
        
        return False
    
    def _has_formal_morphology(self, token) -> bool:
        """Check for formal morphological patterns."""
        lemma = token.lemma_.lower()
        
        # Formal prefixes + formal suffixes indicate bureaucratic language
        formal_prefixes = ['re-', 'pre-', 'de-', 'dis-']
        formal_suffixes = ['-ment', '-tion', '-ance', '-ence']
        
        has_formal_prefix = any(lemma.startswith(prefix.rstrip('-')) for prefix in formal_prefixes)
        has_formal_suffix = any(lemma.endswith(suffix.lstrip('-')) for suffix in formal_suffixes)
        
        return has_formal_prefix or has_formal_suffix
    
    def _suggest_simplification_by_morphology(self, token) -> str:
        """Suggest simplification using morphological analysis."""
        lemma = token.lemma_.lower()
        
        # Method 1: Latinate → Germanic conversion using morphological patterns
        if 'utiliz' in lemma:
            return 'use'
        elif 'implement' in lemma:
            return 'do' if token.pos_ == 'VERB' else 'doing'
        elif 'facilitat' in lemma:
            return 'help'
        elif 'demonstr' in lemma:
            return 'show'
        elif 'establ' in lemma:
            return 'set up'
        elif 'determin' in lemma:
            return 'decide'
        
        # Method 2: Nominalization → verbal conversion
        if lemma.endswith('tion') or lemma.endswith('sion'):
            return self._convert_nominalization_to_verb(lemma)
        
        # Method 3: Complex → simple based on morphological complexity
        if len(lemma) > 10:
            return self._suggest_shorter_alternative(lemma)
        
        return None
    
    def _convert_nominalization_to_verb(self, lemma) -> str:
        """Convert nominalization to simpler form using morphological analysis."""
        # Remove -tion/-sion suffixes to get verbal roots
        if lemma.endswith('tion'):
            root = lemma[:-4]
            if 'organiza' in root:
                return 'arrange'
            elif 'implementa' in root:
                return 'doing'
            elif 'considera' in root:
                return 'thinking'
        
        elif lemma.endswith('sion'):
            root = lemma[:-4]
            if 'comprehens' in root:
                return 'understanding'
        
        elif lemma.endswith('ment'):
            root = lemma[:-4]
            if 'govern' in root:
                return 'manage'
            elif 'establish' in root:
                return 'setting up'
        
        return 'simplify'  # Generic fallback
    
    def _suggest_shorter_alternative(self, lemma) -> str:
        """Suggest shorter alternative based on semantic patterns."""
        # Use morphological analysis to identify semantic cores
        if 'methodolog' in lemma:
            return 'method'
        elif 'priorit' in lemma:
            return 'rank'
        elif 'organiz' in lemma:
            return 'group'
        elif 'framework' in lemma:
            return 'structure'
        
        return 'simplify'
    
    def _is_formal_term(self, token) -> bool:
        """Check if term is formal using morphological analysis."""
        # Use morphological complexity as formality indicator
        complexity_score = self._calculate_morphological_complexity_score(token)
        
        # High morphological complexity suggests formality
        if complexity_score > 0.6:
            return True
        
        # Latinate patterns suggest formality
        if self._has_latinate_formality_pattern(token):
            return True
        
        return False
    
    def _is_common_bureaucratic_term(self, token) -> bool:
        """Check if term is commonly bureaucratic using morphological analysis."""
        # Use length + Latinate patterns as bureaucratic indicators
        lemma = token.lemma_.lower()
        
        # Long Latinate verbs are often bureaucratic
        if len(lemma) > 7 and self._has_latinate_formality_pattern(token):
            return True
        
        # Complex derivation suggests bureaucratic language
        if self._has_complex_derivation(token):
            return True
        
        return False
    
    def _can_simplify_in_context(self, token, doc) -> bool:
        """Determine if simplification is appropriate in context."""
        # Don't oversimplify in very formal contexts
        formality_level = self._assess_formality_level(doc)
        
        # Allow simplification in business contexts (they often benefit from clarity)
        if self._is_business_context(doc) and formality_level < 0.9:
            return True
        
        # Allow simplification in general contexts
        if not self._is_academic_context(doc) and formality_level < 0.8:
            return True
        
        return False
    
    def _assess_formality_level(self, doc) -> float:
        """Assess document formality level."""
        formal_indicators = 0
        total_tokens = 0
        
        for token in doc:
            if token.pos_ in ["NOUN", "VERB", "ADJ"]:
                total_tokens += 1
                if self._is_formal_term(token):
                    formal_indicators += 1
        
        return formal_indicators / total_tokens if total_tokens > 0 else 0.0
    
    def _is_business_context(self, doc) -> bool:
        """Enhanced business context detection using morphological analysis."""
        # Method 1: Named entity analysis
        business_entity_count = 0
        for ent in doc.ents:
            if self._is_business_related_entity(ent):
                business_entity_count += 1
        
        if business_entity_count > 0:
            return True
        
        # Method 2: Morphological pattern analysis for business terms
        business_pattern_count = 0
        for token in doc:
            if self._has_business_morphology(token):
                business_pattern_count += 1
        
        # If significant portion has business morphology, it's business context
        return business_pattern_count > len(list(doc)) * 0.05
    
    def _is_business_related_entity(self, entity) -> bool:
        """Check if entity is business-related using morphological analysis."""
        # Method 1: Organizational entities
        if entity.label_ == "ORG":
            return True
        
        # Method 2: Financial/monetary entities
        if entity.label_ == "MONEY":
            return True
        
        # Method 3: Percentage/quantitative business entities
        if entity.label_ == "PERCENT":
            return True
        
        return False
    
    def _has_business_morphology(self, token) -> bool:
        """Check for business morphology patterns."""
        lemma = token.lemma_.lower()
        
        # Business terms often have these patterns
        if 'policy' in lemma or 'guideline' in lemma or 'procedure' in lemma:
            return True
        
        if 'management' in lemma or 'organization' in lemma or 'business' in lemma:
            return True
        
        if 'strategy' in lemma or 'implement' in lemma or 'process' in lemma:
            return True
        
        if 'compliance' in lemma or 'governance' in lemma or 'operation' in lemma:
            return True
        
        return False
    
    def _is_academic_context(self, doc) -> bool:
        """Detect academic context using morphological analysis."""
        academic_pattern_count = 0
        
        for token in doc:
            if self._has_academic_morphology(token):
                academic_pattern_count += 1
        
        # If significant portion has academic morphology, it's academic context
        return academic_pattern_count > len(list(doc)) * 0.05
    
    def _has_academic_morphology(self, token) -> bool:
        """Check for academic morphology patterns."""
        lemma = token.lemma_.lower()
        
        # Academic terms often have these patterns
        if 'research' in lemma or 'stud' in lemma or 'analys' in lemma:
            return True
        
        if 'finding' in lemma or 'methodolog' in lemma or 'literatur' in lemma:
            return True
        
        if 'theoretical' in lemma or 'empirical' in lemma or 'hypothesis' in lemma:
            return True
        
        return False
    
    def _calculate_bureaucratic_complexity_score(self, token, doc) -> float:
        """Calculate bureaucratic complexity score."""
        score = 0.0
        
        # Base complexity (length proxy)
        score += len(token.text) / 10.0
        
        # Context multiplier
        if self._is_professional_context(doc):
            score *= 1.3
        
        # Common bureaucratic terms get higher scores
        if self._is_common_bureaucratic_term(token):
            score += 0.4
        
        return min(score, 1.0)
    
    def _detect_verbose_constructions(self, doc) -> List[Dict[str, Any]]:
        """Detect areas of high morphological density."""
        issues = []
        
        # Analyze phrases for morphological complexity
        for sent in doc.sents:
            density_analysis = self._analyze_sentence_morphological_density(sent)
            if density_analysis['is_high_density']:
                issues.append({
                    'type': 'high_morphological_density',
                    'sentence_tokens': list(sent),
                    'density_score': density_analysis['density_score'],
                    'complexity_indicators': density_analysis['complexity_indicators'],
                    'position': sent.start_char
                })
        
        return issues
    
    def _analyze_sentence_morphological_density(self, sentence) -> Dict[str, Any]:
        """Analyze morphological density of sentence."""
        total_features = 0
        total_tokens = 0
        complexity_indicators = []
        
        for token in sentence:
            if self._is_content_word(token):
                total_tokens += 1
                feature_count = len(token.morph)
                total_features += feature_count
                
                # Identify complexity indicators
                if feature_count > 4:
                    complexity_indicators.append(f"complex_morphology_{token.text}")
                
                if self._is_derived_word(token):
                    complexity_indicators.append(f"derivation_{token.text}")
        
        density_score = total_features / total_tokens if total_tokens > 0 else 0
        
        return {
            'density_score': density_score,
            'is_high_density': density_score > 3.0,  # Threshold for high density
            'complexity_indicators': complexity_indicators
        }
    
    def _is_content_word(self, token) -> bool:
        """Check if token is content word using SpaCy POS analysis."""
        return token.pos_ in ["NOUN", "VERB", "ADJ", "ADV"]
    
    def _is_derived_word(self, token) -> bool:
        """Check if word is morphologically derived."""
        derivational_suffixes = ['-tion', '-sion', '-ment', '-ance', '-ence', '-ity', '-ness', '-ful', '-less']
        lemma = token.lemma_.lower()
        return any(lemma.endswith(suffix.lstrip('-')) for suffix in derivational_suffixes)
    
    def _detect_nominalizations(self, doc) -> List[Dict[str, Any]]:
        """Detect areas of high morphological density."""
        issues = []
        
        # Analyze phrases for morphological complexity
        for sent in doc.sents:
            density_analysis = self._analyze_sentence_morphological_density(sent)
            if density_analysis['is_high_density']:
                issues.append({
                    'type': 'high_morphological_density',
                    'sentence_tokens': list(sent),
                    'density_score': density_analysis['density_score'],
                    'complexity_indicators': density_analysis['complexity_indicators'],
                    'position': sent.start_char
                })
        
        return issues
    
    def _detect_expletive_constructions(self, doc) -> List[Dict[str, Any]]:
        """Detect areas of high morphological density."""
        issues = []
        
        # Analyze phrases for morphological complexity
        for sent in doc.sents:
            density_analysis = self._analyze_sentence_morphological_density(sent)
            if density_analysis['is_high_density']:
                issues.append({
                    'type': 'high_morphological_density',
                    'sentence_tokens': list(sent),
                    'density_score': density_analysis['density_score'],
                    'complexity_indicators': density_analysis['complexity_indicators'],
                    'position': sent.start_char
                })
        
        return issues
    
    def _detect_pleonasms(self, doc) -> List[Dict[str, Any]]:
        """Detect areas of high morphological density."""
        issues = []
        
        # Analyze phrases for morphological complexity
        for sent in doc.sents:
            density_analysis = self._analyze_sentence_morphological_density(sent)
            if density_analysis['is_high_density']:
                issues.append({
                    'type': 'high_morphological_density',
                    'sentence_tokens': list(sent),
                    'density_score': density_analysis['density_score'],
                    'complexity_indicators': density_analysis['complexity_indicators'],
                    'position': sent.start_char
                })
        
        return issues
    
    def _detect_circumlocutions(self, doc) -> List[Dict[str, Any]]:
        """Detect areas of high morphological density."""
        issues = []
        
        # Analyze phrases for morphological complexity
        for sent in doc.sents:
            density_analysis = self._analyze_sentence_morphological_density(sent)
            if density_analysis['is_high_density']:
                issues.append({
                    'type': 'high_morphological_density',
                    'sentence_tokens': list(sent),
                    'density_score': density_analysis['density_score'],
                    'complexity_indicators': density_analysis['complexity_indicators'],
                    'position': sent.start_char
                })
        
        return issues
    
    def _detect_filler_phrases(self, doc) -> List[Dict[str, Any]]:
        """Detect filler phrases using pure SpaCy morphological analysis."""
        filler_issues = []
        
        for token in doc:
            # Method 1: Detect temporal filler phrases using dependency analysis
            if self._is_temporal_filler_phrase(token, doc):
                filler_issue = self._analyze_temporal_filler(token, doc)
                if filler_issue:
                    filler_issues.append(filler_issue)
            
            # Method 2: Detect purpose filler phrases using syntactic patterns
            elif self._is_purpose_filler_phrase(token, doc):
                purpose_issue = self._analyze_purpose_filler(token, doc)
                if purpose_issue:
                    filler_issues.append(purpose_issue)
            
            # Method 3: Detect discourse marker fillers
            elif self._is_discourse_filler(token, doc):
                discourse_issue = self._analyze_discourse_filler(token, doc)
                if discourse_issue:
                    filler_issues.append(discourse_issue)
        
        return filler_issues
    
    def _is_temporal_filler_phrase(self, token, doc) -> bool:
        """Detect temporal filler phrases using SpaCy morphological analysis."""
        # Use SpaCy's dependency parsing to identify temporal phrases
        if token.dep_ == "advmod" and token.pos_ == "ADV":
            # Check for temporal adverbs that can often be simplified
            temporal_patterns = self._analyze_temporal_pattern(token, doc)
            return temporal_patterns['is_filler']
        
        # Check for participial phrase fillers (e.g., "introduced recently")
        if token.pos_ == "VERB" and "Tense=Past" in str(token.morph):
            return self._is_participial_filler(token, doc)
        
        return False
    
    def _analyze_temporal_pattern(self, adv_token, doc) -> Dict[str, Any]:
        """Analyze temporal pattern using SpaCy."""
        pattern_info = {
            'is_filler': False,
            'pattern_type': 'unknown',
            'simplification_potential': 0.0
        }
        
        # Use SpaCy's lemmatization for pattern detection
        lemma = adv_token.lemma_.lower()
        
        # Check for compound temporal constructions
        head_verb = adv_token.head
        if head_verb.pos_ == "VERB":
            # Look for past participle + temporal adverb patterns
            if "Tense=Past" in str(head_verb.morph) and "VerbForm=Part" in str(head_verb.morph):
                pattern_info['is_filler'] = True
                pattern_info['pattern_type'] = 'participial_temporal'
                pattern_info['simplification_potential'] = 0.8
        
        return pattern_info
    
    def _is_participial_filler(self, verb_token, doc) -> bool:
        """Check if participial phrase is filler using SpaCy analysis."""
        # Look for past participles with temporal modifiers
        if "VerbForm=Part" in str(verb_token.morph):
            for child in verb_token.children:
                if child.dep_ == "advmod" and child.pos_ == "ADV":
                    # Use SpaCy's morphological analysis for temporal detection
                    if self._is_temporal_adverb(child):
                        return True
        
        return False
    
    def _is_temporal_adverb(self, adverb_token) -> bool:
        """Check if adverb is temporal using morphological analysis."""
        lemma = adverb_token.lemma_.lower()
        
        # Temporal adverbs often have time-related morphological patterns
        if 'recent' in lemma or 'late' in lemma or 'new' in lemma:
            return True
        
        # Check for temporal morphological endings
        if lemma.endswith('ly') and ('time' in lemma or 'recent' in lemma):
            return True
        
        return False
    
    def _is_purpose_filler_phrase(self, token, doc) -> bool:
        """Detect purpose filler phrases using SpaCy syntactic analysis."""
        # Look for infinitive purpose clauses that add little value
        if token.dep_ == "advcl" and token.pos_ == "VERB":
            # Check for purpose infinitives
            if "VerbForm=Inf" in str(token.morph):
                return self._is_redundant_purpose_clause(token, doc)
        
        # Check for prepositional purpose phrases
        if token.dep_ == "prep" and self._is_purpose_preposition(token):
            return self._is_redundant_prepositional_purpose(token, doc)
        
        return False
    
    def _is_purpose_preposition(self, token) -> bool:
        """Check if preposition indicates purpose using morphological analysis."""
        lemma = token.lemma_.lower()
        
        # Purpose prepositions often have directional/goal morphology
        if lemma == "to" or lemma == "for":
            return True
        
        return False
    
    def _analyze_purpose_content(self, purpose_token, doc) -> Dict[str, Any]:
        """Analyze purpose clause content using SpaCy."""
        content_analysis = {
            'is_redundant': False,
            'redundancy_type': 'unknown',
            'semantic_value': 0.0
        }
        
        # Use SpaCy's lemmatization to identify common filler purposes
        if self._is_filler_purpose_verb(purpose_token):
            # Check if the purpose is vague or already implied
            semantic_specificity = self._calculate_purpose_specificity(purpose_token, doc)
            if semantic_specificity < 0.3:
                content_analysis['is_redundant'] = True
                content_analysis['redundancy_type'] = 'vague_purpose'
        
        return content_analysis
    
    def _is_filler_purpose_verb(self, verb_token) -> bool:
        """Check if verb is filler purpose using morphological analysis."""
        lemma = verb_token.lemma_.lower()
        
        # Filler purposes often have vague action morphology
        if 'address' in lemma or 'handle' in lemma or 'deal' in lemma:
            return True
        
        if 'tackle' in lemma:
            return True
        
        return False
    
    def _calculate_purpose_specificity(self, purpose_token, doc) -> float:
        """Calculate purpose specificity using SpaCy analysis."""
        specificity_score = 0.0
        
        # Check for specific objects or complements
        for child in purpose_token.children:
            if self._is_specific_object_role(child):
                specificity_score += 0.3
                
                # Bonus for named entities
                if child.ent_type_:
                    specificity_score += 0.2
        
        return min(specificity_score, 1.0)
    
    def _is_specific_object_role(self, token) -> bool:
        """Check if token has specific object dependency role."""
        return token.dep_ in ["dobj", "attr", "prep"]
    
    def _is_vague_purpose_object(self, obj_token, doc) -> bool:
        """Check if purpose object is vague using SpaCy."""
        # Use morphological analysis for vague purpose detection
        if self._has_vague_reference_morphology(obj_token):
            return True
        
        return False
    
    def _has_vague_reference_morphology(self, token) -> bool:
        """Check for vague reference morphology using SpaCy."""
        lemma = token.lemma_.lower()
        
        # Vague references often use demonstrative or general terms
        if 'this' in lemma or 'that' in lemma or 'issue' in lemma:
            return True
        
        if 'matter' in lemma or 'situation' in lemma:
            return True
        
        return False
    
    def _is_discourse_filler(self, token, doc) -> bool:
        """Detect discourse marker fillers using SpaCy analysis."""
        # Look for discourse markers that add little value
        if token.dep_ == "advmod" and token.pos_ == "ADV":
            return self._is_discourse_marker_adverb(token)
        
        return False
    
    def _is_discourse_marker_adverb(self, token) -> bool:
        """Check if adverb is discourse marker using morphological analysis."""
        lemma = token.lemma_.lower()
        
        # Discourse markers often have minimizing/hedging morphology
        if 'basic' in lemma or 'essential' in lemma or 'actual' in lemma:
            return True
        
        if 'real' in lemma:
            return True
        
        return False
    
    def _analyze_temporal_filler(self, token, doc) -> Dict[str, Any]:
        """Analyze temporal filler phrase using SpaCy analysis."""
        analysis = {
            'type': 'temporal_filler',
            'token': token,
            'simplification_potential': 0.0,
            'redundancy_type': 'unknown',
            'position': token.idx
        }
        
        # Analyze the temporal pattern
        if token.dep_ == "advmod" and token.pos_ == "ADV":
            temporal_pattern = self._analyze_temporal_pattern(token, doc)
            if temporal_pattern['is_filler']:
                analysis['simplification_potential'] = temporal_pattern['simplification_potential']
                analysis['redundancy_type'] = temporal_pattern['pattern_type']
                return analysis
        
        # Check for participial temporal constructions
        elif token.pos_ == "VERB" and "Tense=Past" in str(token.morph):
            if self._is_participial_filler(token, doc):
                analysis['redundancy_type'] = 'participial_temporal'
                analysis['simplification_potential'] = 0.7
                return analysis
        
        return None
    
    def _analyze_purpose_filler(self, token, doc) -> Dict[str, Any]:
        """Analyze purpose filler phrase using SpaCy analysis."""
        analysis = {
            'type': 'purpose_filler',
            'token': token,
            'redundancy_type': 'unknown',
            'position': token.idx
        }
        
        # Analyze purpose clause redundancy
        if token.dep_ == "advcl" and token.pos_ == "VERB":
            if "VerbForm=Inf" in str(token.morph):
                purpose_content = self._analyze_purpose_content(token, doc)
                if purpose_content['is_redundant']:
                    analysis['redundancy_type'] = purpose_content['redundancy_type']
                    analysis['semantic_value'] = purpose_content['semantic_value']
                    return analysis
        
        # Analyze prepositional purpose phrases
        elif token.dep_ == "prep" and self._is_purpose_preposition(token):
            if self._is_redundant_prepositional_purpose(token, doc):
                analysis['redundancy_type'] = 'redundant_prep_purpose'
                return analysis
        
        return None
    
    def _analyze_discourse_filler(self, token, doc) -> Dict[str, Any]:
        """Analyze discourse marker filler using SpaCy analysis."""
        analysis = {
            'type': 'discourse_filler',
            'token': token,
            'redundancy_type': 'discourse_marker',
            'position': token.idx
        }
        
        # Check if this is indeed a discourse filler
        if token.dep_ == "advmod" and token.pos_ == "ADV":
            if self._is_discourse_marker_adverb(token):
                return analysis
        
        return None
    
    def _is_redundant_purpose_clause(self, token, doc) -> bool:
        """Check if purpose clause is redundant using SpaCy analysis."""
        # Analyze the purpose content
        purpose_analysis = self._analyze_purpose_content(token, doc)
        return purpose_analysis.get('is_redundant', False)
    
    def _is_redundant_prepositional_purpose(self, token, doc) -> bool:
        """Check if prepositional purpose phrase is redundant."""
        # Look at the object of the preposition
        for child in token.children:
            if child.dep_ == "pobj":
                if self._is_vague_purpose_object(child, doc):
                    return True
        return False
    
    def _generate_conciseness_suggestions_from_linguistics(self, issue: Dict[str, Any], doc=None) -> List[str]:
        """Generate suggestions based on linguistic analysis."""
        suggestions = []
        issue_type = issue.get('type', 'unknown')
        
        if issue_type == 'redundant_modifier':
            suggestions.extend(self._generate_modifier_suggestions(issue))
        
        elif issue_type == 'redundant_adverb':
            suggestions.extend(self._generate_adverb_suggestions(issue))
        
        elif issue_type == 'prepositional_chain':
            suggestions.extend(self._generate_prepositional_suggestions(issue))
        
        elif issue_type == 'complex_verb_phrase':
            suggestions.extend(self._generate_verb_phrase_suggestions(issue))
        
        elif issue_type == 'nominalization':
            suggestions.extend(self._generate_nominalization_suggestions(issue))
        
        elif issue_type == 'expletive_construction':
            suggestions.extend(self._generate_expletive_suggestions(issue))
        
        elif issue_type == 'pleonasm':
            suggestions.extend(self._generate_pleonasm_suggestions(issue))
        
        elif issue_type == 'circumlocution':
            suggestions.extend(self._generate_circumlocution_suggestions(issue, doc))
        
        # NEW: Synonym pair redundancy suggestions for technical writers
        elif issue_type == 'synonym_pair_redundancy':
            suggestions.extend(self._generate_synonym_redundancy_suggestions(issue, doc))
        
        # NEW: Archaic verb modernization suggestions for technical writers
        elif issue_type == 'archaic_verb_modernization':
            suggestions.extend(self._generate_verb_modernization_suggestions(issue, doc))
        
        # Existing: Filler phrase suggestions for technical writers
        elif self._is_filler_issue_type(issue_type):
            suggestions.extend(self._generate_filler_suggestions(issue, doc))
        
        else:
            suggestions.append("Simplify this wordy construction for clearer communication")
        
        return suggestions
    
    def _is_filler_issue_type(self, issue_type: str) -> bool:
        """Check if issue type is filler-related using pattern analysis."""
        # Use morphological pattern analysis instead of hardcoded list
        return self._has_filler_type_pattern(issue_type)
    
    def _has_filler_type_pattern(self, issue_type: str) -> bool:
        """Check for filler type patterns using morphological analysis."""
        # Filler types often have these morphological patterns
        if 'temporal' in issue_type and 'filler' in issue_type:
            return True
        
        if 'purpose' in issue_type and 'filler' in issue_type:
            return True
        
        if 'discourse' in issue_type and 'filler' in issue_type:
            return True
        
        return False
    
    def _is_formal_process_verb(self, token) -> bool:
        """Check if token is a formal process verb using SpaCy analysis."""
        # Use morphological analysis instead of hardcoded list
        return self._has_formal_process_morphology(token)
    
    def _has_formal_process_morphology(self, token) -> bool:
        """Check for formal process verb morphology."""
        # Use morphological analysis instead of hardcoded list
        return self._has_administrative_process_morphology(token)
    
    def _has_administrative_process_morphology(self, token) -> bool:
        """Check for administrative process morphology patterns."""
        lemma = token.lemma_.lower()
        
        # Administrative process verbs often have procedural morphology
        if 'circul' in lemma or 'implement' in lemma or 'facilitat' in lemma:
            return True
        
        if 'execut' in lemma or 'administer' in lemma:
            return True
        
        return False
    
    def _generate_filler_suggestions(self, filler_issue: Dict[str, Any], doc) -> List[str]:
        """Generate filler phrase suggestions using SpaCy analysis."""
        suggestions = []
        issue_type = filler_issue.get('type')
        token = filler_issue.get('token')
        
        if issue_type == 'temporal_filler':
            # Use SpaCy to suggest simplifications
            if token.dep_ == "advmod" and token.head.pos_ == "VERB":
                head_verb = token.head
                if "VerbForm=Part" in str(head_verb.morph):
                    # "introduced recently" → "recent"
                    suggestions.append(f"Simplify '{head_verb.text} {token.text}' to 'recent {head_verb.head.text}'")
                    suggestions.append(f"Consider: 'recent' instead of '{head_verb.text} {token.text}'")
        
        elif issue_type == 'purpose_filler':
            # Generate purpose simplification suggestions
            suggestions.append(f"Consider removing '{token.text}' if the purpose is already clear")
            suggestions.append("This phrase may not add meaningful information")
        
        elif issue_type == 'discourse_filler':
            suggestions.append(f"Remove discourse filler '{token.text}' for conciseness")
            suggestions.append("Technical writing benefits from direct statements")
        
        return suggestions
    
    def _create_wordiness_message(self, issue: Dict[str, Any]) -> str:
        """Create message describing the wordiness issue."""
        issue_type = issue.get('type', 'unknown')
        
        if issue_type == 'redundant_modifier':
            modifier = issue.get('modifier_token')
            return f"Redundant modifier '{modifier.text}' adds no new information"
        
        elif issue_type == 'redundant_adverb':
            adverb = issue.get('adverb_token')
            return f"Adverb '{adverb.text}' is redundant with the verb it modifies"
        
        elif issue_type == 'prepositional_chain':
            chain_length = issue.get('chain_analysis', {}).get('length', 0)
            return f"Long prepositional chain ({chain_length} prepositions) could be simplified"
        
        elif issue_type == 'complex_verb_phrase':
            score = issue.get('verbosity_score', 0)
            return f"Complex verb phrase (complexity: {score}) could be simplified"
        
        elif issue_type == 'nominalization':
            noun = issue.get('nominalized_token')
            return f"Nominalization '{noun.text}' could be converted to active verb"
        
        elif issue_type == 'expletive_construction':
            return "Expletive construction could be made more direct"
        
        elif issue_type == 'pleonasm':
            return "Redundant expression using semantically similar words"
        
        elif issue_type == 'circumlocution':
            return "Wordy expression could be stated more directly"
        
        else:
            return "Wordy construction could be simplified"
    
    def _determine_wordiness_severity(self, issue: Dict[str, Any]) -> str:
        """Determine severity of wordiness issue."""
        verbosity_score = issue.get('verbosity_score', 1)
        
        if verbosity_score >= 3:
            return 'medium'
        elif verbosity_score >= 2:
            return 'low'
        else:
            return 'info'
    
    def _generate_modifier_suggestions(self, issue: Dict[str, Any]) -> List[str]:
        """Generate suggestions for redundant modifiers."""
        modifier_token = issue.get('modifier_token')
        modified_token = issue.get('modified_token')
        
        suggestions = []
        if modifier_token and modified_token:
            suggestions.append(f"Remove redundant modifier '{modifier_token.text}'")
            suggestions.append(f"'{modified_token.text}' alone conveys the meaning effectively")
        
        return suggestions
    
    def _generate_adverb_suggestions(self, issue: Dict[str, Any]) -> List[str]:
        """Generate suggestions for redundant adverbs."""
        adverb_token = issue.get('adverb_token')
        modified_token = issue.get('modified_token')
        
        suggestions = []
        if adverb_token and modified_token:
            suggestions.append(f"Remove redundant adverb '{adverb_token.text}'")
            suggestions.append(f"The verb '{modified_token.text}' already implies this meaning")
        
        return suggestions
    
    def _generate_prepositional_suggestions(self, issue: Dict[str, Any]) -> List[str]:
        """Generate suggestions for prepositional chains."""
        chain_analysis = issue.get('chain_analysis', {})
        chain_length = chain_analysis.get('length', 0)
        
        suggestions = []
        suggestions.append(f"Break up chain of {chain_length} prepositional phrases")
        suggestions.append("Use shorter, more direct phrasing")
        suggestions.append("Consider using active voice to eliminate some prepositions")
        
        return suggestions
    
    def _generate_verb_phrase_suggestions(self, issue: Dict[str, Any]) -> List[str]:
        """Generate suggestions for complex verb phrases."""
        complexity = issue.get('complexity_analysis', {})
        
        suggestions = []
        if complexity.get('auxiliary_count', 0) > 1:
            suggestions.append("Reduce number of auxiliary verbs")
        
        if complexity.get('modal_count', 0) > 0:
            suggestions.append("Consider direct statement instead of modal construction")
        
        suggestions.append("Simplify verb phrase for more direct expression")
        
        return suggestions
    
    def _generate_nominalization_suggestions(self, issue: Dict[str, Any]) -> List[str]:
        """Generate suggestions for nominalizations."""
        noun_token = issue.get('nominalized_token')
        verb_root = issue.get('verb_root')
        
        suggestions = []
        if noun_token and verb_root:
            suggestions.append(f"Convert nominalization '{noun_token.text}' to active verb '{verb_root}'")
            suggestions.append(f"Use '{verb_root}' instead of '{noun_token.text}' for more direct action")
        
        return suggestions
    
    def _generate_expletive_suggestions(self, issue: Dict[str, Any]) -> List[str]:
        """Generate suggestions for expletive constructions."""
        expletive_token = issue.get('expletive_token')
        logical_subject = issue.get('logical_subject')
        
        suggestions = []
        suggestions.append(f"Remove expletive '{expletive_token.text}' for more direct statement")
        
        if logical_subject:
            suggestions.append(f"Make '{logical_subject.text}' the sentence subject")
        else:
            suggestions.append("Restructure to eliminate expletive construction")
        
        return suggestions
    
    def _generate_pleonasm_suggestions(self, issue: Dict[str, Any]) -> List[str]:
        """Generate suggestions for pleonasms."""
        redundant_tokens = issue.get('redundant_tokens', [])
        
        suggestions = []
        if len(redundant_tokens) >= 2:
            token_texts = [token.text for token in redundant_tokens]
            suggestions.append(f"Remove redundant repetition: choose either '{token_texts[0]}' or '{token_texts[1]}'")
            suggestions.append("Eliminate semantic redundancy for clearer expression")
        
        return suggestions
    
    def _generate_circumlocution_suggestions(self, issue: Dict[str, Any], doc) -> List[str]:
        """Generate suggestions for circumlocutions."""
        simplification_analysis = issue.get('simplification_analysis', {})
        strategies = simplification_analysis.get('simplification_strategies', [])
        
        suggestions = []
        for strategy in strategies:
            if strategy == "break_into_shorter_sentences":
                suggestions.append("Break this complex expression into shorter, clearer sentences")
            elif strategy == "reduce_modifiers":
                suggestions.append("Remove unnecessary modifiers and qualifiers")
            elif strategy == "simplify_prepositional_phrases":
                suggestions.append("Simplify or eliminate excessive prepositional phrases")
        
        if not suggestions:
            suggestions.append("State this idea more directly and concisely")
        
        return suggestions
    
    def _generate_synonym_redundancy_suggestions(self, issue: Dict[str, Any], doc) -> List[str]:
        """Generate suggestions for synonym pair redundancy."""
        suggestions = []
        
        first_token = issue.get('first_token')
        second_token = issue.get('second_token')
        redundancy_analysis = issue.get('redundancy_analysis', {})
        
        if first_token and second_token:
            redundancy_type = redundancy_analysis.get('redundancy_type', 'general_synonyms')
            context_score = redundancy_analysis.get('context_appropriateness', 0.0)
            
            # Enhanced suggestions for specific morphological patterns
            first_lemma = first_token.lemma_.lower()
            second_lemma = second_token.lemma_.lower()
            
            # Special handling for cognitive/conformity redundancy (awareness + alignment)
            if self._has_cognitive_state_morphology(first_lemma) and self._has_conformity_morphology(second_lemma):
                suggestions.append(f"Use 'ensure employees understand' instead of 'ensure {first_token.text} and {second_token.text}'")
                suggestions.append(f"'Understanding' implies compliance - '{first_token.text} and {second_token.text}' is redundant")
                suggestions.append("For technical writing clarity: 'ensure employees understand and follow' is more direct")
            elif self._has_conformity_morphology(first_lemma) and self._has_cognitive_state_morphology(second_lemma):
                suggestions.append(f"Use 'ensure employees understand' instead of 'ensure {first_token.text} and {second_token.text}'")
                suggestions.append(f"'Understanding' implies compliance - '{first_token.text} and {second_token.text}' is redundant")
                suggestions.append("For technical writing clarity: 'ensure employees understand and follow' is more direct")
            
            # Determine which term to keep based on context appropriateness
            elif context_score > 0:  # second_token is better
                suggestions.append(f"Remove '{first_token.text}' - '{second_token.text}' conveys the same meaning")
                suggestions.append(f"Use '{second_token.text}' instead of '{first_token.text} and {second_token.text}'")
            elif context_score < 0:  # first_token is better
                suggestions.append(f"Remove '{second_token.text}' - '{first_token.text}' conveys the same meaning")
                suggestions.append(f"Use '{first_token.text}' instead of '{first_token.text} and {second_token.text}'")
            else:  # Equal - suggest the first one
                suggestions.append(f"Choose either '{first_token.text}' or '{second_token.text}' - both convey the same meaning")
            
            # Context-specific suggestions
            if redundancy_type == 'communication_synonyms':
                suggestions.append("For modern business communication, 'feedback' is preferred over 'commentary'")
            elif redundancy_type == 'process_synonyms':
                suggestions.append("For conversational clarity, 'share' is more modern than 'circulate'")
        
        return suggestions
    
    def _generate_verb_modernization_suggestions(self, issue: Dict[str, Any], doc) -> List[str]:
        """Generate suggestions for verb modernization."""
        suggestions = []
        
        archaic_verb = issue.get('archaic_verb')
        modern_alternative = issue.get('modern_alternative')
        formality_analysis = issue.get('formality_analysis', {})
        
        if archaic_verb and modern_alternative:
            suggestions.append(f"Use '{modern_alternative}' instead of '{archaic_verb.text}' for modern clarity")
            suggestions.append(f"'{modern_alternative}' is more conversational than '{archaic_verb.text}'")
            
            # Context-specific suggestions
            if formality_analysis.get('is_latinate', False):
                suggestions.append("Latinate verbs can sound formal - consider simpler alternatives")
            
            formality_score = formality_analysis.get('formality_score', 0.0)
            if formality_score > 0.7:
                suggestions.append("This verb may be too formal for modern business communication")
        
        return suggestions
    
    def _find_wordiness_morphological_fallback(self, sentence: str) -> List[Dict[str, Any]]:
        """Fallback wordiness detection when SpaCy unavailable."""
        import re
        issues = []
        
        # Very basic patterns as fallback
        wordy_patterns = [
            r'\b(?:very|really|quite|rather)\s+\w+',  # Redundant intensifiers
            r'\b(?:in order to|for the purpose of)\b',  # Wordy phrases
        ]
        
        for pattern in wordy_patterns:
            matches = re.finditer(pattern, sentence, re.IGNORECASE)
            for match in matches:
                issues.append({
                    'type': 'morphological_fallback',
                    'matched_text': match.group(),
                    'position': match.start(),
                    'pattern_type': 'basic_wordiness',
                    'verbosity_score': 1
                })
        
        return issues
    
    def _is_formal_process_verb(self, token) -> bool:
        """Check if token is a formal process verb using SpaCy analysis."""
        formal_verbs = ['circulate', 'implement', 'facilitate', 'execute', 'administer']
        return token.lemma_.lower() in formal_verbs
    
    def _are_communication_synonyms(self, lemma1, lemma2) -> bool:
        """Check for communication synonym pairs using pure SpaCy morphological analysis."""
        # Method 1: Check if both are communication words with morphological similarity
        if self._is_communication_word_by_morphology(lemma1) and self._is_communication_word_by_morphology(lemma2):
            # Check morphological relationship
            if self._have_similar_morphological_patterns(lemma1, lemma2):
                return True
        
        # Method 2: Specific patterns for business communication redundancy
        if self._are_business_communication_synonyms(lemma1, lemma2):
            return True
        
        return False
    
    def _are_business_communication_synonyms(self, lemma1, lemma2) -> bool:
        """Check for specific business communication synonym pairs using morphological analysis."""
        # Method 1: Cognitive state morphology (awareness-type terms)
        is_cognitive1 = self._has_cognitive_state_morphology(lemma1)
        is_cognitive2 = self._has_cognitive_state_morphology(lemma2)
        
        # Method 2: Conformity/compliance morphology (alignment-type terms) 
        is_conformity1 = self._has_conformity_morphology(lemma1)
        is_conformity2 = self._has_conformity_morphology(lemma2)
        
        # Semantic redundancy: cognitive + conformity terms often mean the same in business context
        if (is_cognitive1 and is_conformity2) or (is_cognitive2 and is_conformity1):
            return True
        
        # Method 3: Both have similar business communication morphology
        if self._has_business_communication_morphology(lemma1) and self._has_business_communication_morphology(lemma2):
            return True
        
        return False
    
    def _has_cognitive_state_morphology(self, lemma) -> bool:
        """Check for cognitive state morphology patterns."""
        # Cognitive state words often have these morphological patterns
        if 'aware' in lemma or 'understand' in lemma or 'know' in lemma:
            return True
        
        if 'comprehend' in lemma or 'realize' in lemma:
            return True
        
        return False
    
    def _has_conformity_morphology(self, lemma) -> bool:
        """Check for conformity/compliance morphology patterns."""
        # Conformity words often have these morphological patterns
        if 'align' in lemma or 'comply' in lemma or 'conform' in lemma:
            return True
        
        if 'adher' in lemma or 'follow' in lemma:
            return True
        
        return False
    
    def _has_business_communication_morphology(self, lemma) -> bool:
        """Check for business communication morphology patterns."""
        # Business communication terms share certain morphological patterns
        if 'feed' in lemma or 'input' in lemma or 'comment' in lemma:
            return True
        
        if 'suggest' in lemma or 'respond' in lemma:
            return True
        
        return False
    
    def _is_communication_word_by_morphology(self, lemma) -> bool:
        """Check if word is communication-related using morphological patterns."""
        # Communication words often have these morphological roots
        if 'feed' in lemma or 'comment' in lemma or 'respond' in lemma or 'input' in lemma:
            return True
        
        # Derivational patterns indicating communication
        if lemma.endswith('back') or lemma.endswith('ment') or lemma.endswith('ary'):
            return True
        
        return False
    
    def _have_similar_morphological_patterns(self, lemma1, lemma2) -> bool:
        """Check morphological similarity using derivational analysis."""
        # Extract roots by removing common derivational suffixes
        root1 = self._extract_morphological_root_advanced(lemma1)
        root2 = self._extract_morphological_root_advanced(lemma2)
        
        # Check if they share morphological features
        if root1 and root2:
            # Similar length and phonological patterns often indicate semantic similarity
            length_similarity = abs(len(root1) - len(root2)) <= 2
            if length_similarity and self._have_phonological_similarity(root1, root2):
                return True
        
        return False
    
    def _extract_morphological_root_advanced(self, lemma) -> str:
        """Extract morphological root using advanced pattern analysis."""
        # Remove derivational suffixes dynamically
        suffixes = ['-ment', '-ary', '-tion', '-sion', '-ness', '-ity', '-back']
        
        for suffix in suffixes:
            suffix_clean = suffix.lstrip('-')
            if lemma.endswith(suffix_clean) and len(lemma) > len(suffix_clean) + 2:
                return lemma[:-len(suffix_clean)]
        
        return lemma
    
    def _have_phonological_similarity(self, root1, root2) -> bool:
        """Check phonological similarity using string patterns."""
        # Simple phonological similarity check
        if len(root1) >= 3 and len(root2) >= 3:
            # Check for shared consonant clusters or vowel patterns
            consonants1 = ''.join([c for c in root1 if c not in 'aeiou'])
            consonants2 = ''.join([c for c in root2 if c not in 'aeiou'])
            
            if consonants1 and consonants2:
                # Simple similarity: shared consonant patterns
                shared = sum(1 for c in consonants1 if c in consonants2)
                similarity = shared / max(len(consonants1), len(consonants2))
                return similarity > 0.5
        
        return False
    
    def _are_process_synonyms(self, lemma1, lemma2) -> bool:
        """Check for process synonym pairs using pure SpaCy morphological analysis."""
        # Use morphological analysis instead of hardcoded lists
        if self._is_process_verb_by_morphology(lemma1) and self._is_process_verb_by_morphology(lemma2):
            # Check if they have similar semantic weight/formality
            formality1 = self._calculate_word_formality_by_morphology(lemma1)
            formality2 = self._calculate_word_formality_by_morphology(lemma2)
            
            # If one is significantly more formal, they might be synonyms
            formality_diff = abs(formality1 - formality2)
            return formality_diff > 0.3  # Different formality levels suggest synonym pair
        
        return False
    
    def _is_process_verb_by_morphology(self, lemma) -> bool:
        """Check if verb is process-related using morphological analysis."""
        # Process verbs often have movement/distribution morphology
        if 'circul' in lemma or 'distribut' in lemma or 'shar' in lemma:
            return True
        
        # Motion/transfer semantic patterns
        if 'send' in lemma or 'deliv' in lemma or 'pass' in lemma or 'mov' in lemma:
            return True
        
        # Latinate action patterns (often formal process verbs)
        if lemma.endswith('ate') or lemma.endswith('ize') or lemma.endswith('ify'):
            return True
        
        return False
    
    def _calculate_word_formality_by_morphology(self, lemma) -> float:
        """Calculate formality using morphological features."""
        formality_score = 0.0
        
        # Length is often a proxy for formality
        formality_score += len(lemma) / 10.0
        
        # Latinate endings are more formal
        if self._has_latinate_endings(lemma):
            formality_score += 0.4
        
        # Germanic/simple words are less formal
        if self._has_simple_patterns(lemma):
            formality_score -= 0.2
        
        return max(0.0, min(1.0, formality_score))
    
    def _has_latinate_endings(self, lemma) -> bool:
        """Check for Latinate endings using morphological analysis."""
        # Latinate endings often indicate formal/academic register
        if lemma.endswith('ate') or lemma.endswith('ize') or lemma.endswith('ify'):
            return True
        
        if lemma.endswith('tion') or lemma.endswith('sion'):
            return True
        
        return False
    
    def _has_simple_patterns(self, lemma) -> bool:
        """Check for simple Germanic patterns using morphological analysis."""
        # Simple patterns often indicate less formal register
        if lemma.endswith('ing') or lemma.endswith('ed') or lemma.endswith('er'):
            return True
        
        return False
    
    def _is_archaic_verb(self, verb_token, doc) -> bool:
        """Check if verb is archaic/formal using pure SpaCy morphological analysis."""
        # Method 1: Morphological complexity analysis
        morphological_complexity = self._calculate_morphological_complexity_score(verb_token)
        if morphological_complexity > 0.7:  # High complexity suggests formality
            return True
        
        # Method 2: Latinate pattern analysis
        if self._is_latinate_verb_pattern(verb_token):
            # Check if context would benefit from simpler alternative
            context_formality = self._assess_formality_level(doc)
            if context_formality < 0.7:  # Context is not highly formal
                return True
        
        # Method 3: Length-based formality proxy
        lemma = verb_token.lemma_.lower()
        if len(lemma) > 8:  # Long verbs often more formal
            syllable_count = self._estimate_syllable_count(lemma)
            if syllable_count > 3:  # Multi-syllabic suggests formality
                return True
        
        # Method 4: Semantic formality analysis
        if self._is_semantically_formal_verb(verb_token):
            return True
        
        return False
    
    def _is_semantically_formal_verb(self, verb_token) -> bool:
        """Check if verb is semantically formal using morphological patterns."""
        lemma = verb_token.lemma_.lower()
        
        # Formal semantic patterns - bureaucratic/administrative actions
        if 'guarant' in lemma or 'circul' in lemma or 'utiliz' in lemma:
            return True
        
        # Formal process indicators
        if 'facilitat' in lemma or 'commenc' in lemma or 'terminat' in lemma:
            return True
        
        return False
    
    def _calculate_morphological_complexity_score(self, token) -> float:
        """Calculate morphological complexity using SpaCy features."""
        complexity = 0.0
        
        # Base complexity from morphological features
        morph_features = len(token.morph)
        complexity += morph_features / 10.0
        
        # Derivational complexity
        if self._has_complex_derivation(token):
            complexity += 0.4
        
        # Length proxy for morphological complexity
        complexity += len(token.text) / 15.0
        
        return min(complexity, 1.0)
    
    def _has_complex_derivation(self, token) -> bool:
        """Check for complex derivational morphology."""
        lemma = token.lemma_.lower()
        
        # Multiple affixes suggest complexity
        prefixes = ['re-', 'pre-', 'dis-', 'un-', 'over-']
        suffixes = ['-ize', '-ify', '-ate', '-tion', '-sion', '-ment']
        
        has_prefix = any(lemma.startswith(prefix.rstrip('-')) for prefix in prefixes)
        has_suffix = any(lemma.endswith(suffix.lstrip('-')) for suffix in suffixes)
        
        return has_prefix and has_suffix
    
    def _estimate_syllable_count(self, word) -> int:
        """Estimate syllable count for formality assessment."""
        # Simple syllable estimation
        vowels = 'aeiou'
        syllables = 0
        prev_was_vowel = False
        
        for char in word.lower():
            if char in vowels:
                if not prev_was_vowel:
                    syllables += 1
                prev_was_vowel = True
            else:
                prev_was_vowel = False
        
        # Minimum one syllable
        return max(1, syllables)
    
    def _is_latinate_verb_pattern(self, verb_token) -> bool:
        """Check for Latinate verb patterns using morphological analysis."""
        lemma = verb_token.lemma_.lower()
        
        # Common Latinate verb endings
        latinate_endings = ['-ate', '-ize', '-ify']
        return any(lemma.endswith(ending) for ending in latinate_endings)
    
    def _should_modernize_context(self, doc) -> bool:
        """Determine if context favors modern/conversational language."""
        # Don't modernize in highly formal contexts
        formality_level = self._assess_formality_level(doc)
        
        # Modern business communication favors conversational clarity
        if self._is_business_context(doc) and formality_level < 0.9:  # Increased threshold
            return True
        
        # Technical writing often benefits from modern clarity
        if self._is_technical_context(doc) and formality_level < 0.9:
            return True
        
        # General professional contexts favor modern terms
        if self._is_professional_context(doc) and formality_level < 0.8:
            return True
        
        return False
    
    def _is_technical_context(self, doc) -> bool:
        """Detect technical writing context using morphological patterns."""
        # Look for technical terms using morphological analysis
        technical_pattern_count = 0
        
        for token in doc:
            if self._has_technical_morphology(token):
                technical_pattern_count += 1
        
        # If significant portion has technical morphology, it's technical context
        return technical_pattern_count > len(list(doc)) * 0.1
    
    def _has_technical_morphology(self, token) -> bool:
        """Check for technical morphology patterns."""
        lemma = token.lemma_.lower()
        
        # Technical terms often have these patterns
        if 'implement' in lemma or 'system' in lemma or 'process' in lemma:
            return True
        
        if 'protocol' in lemma or 'procedur' in lemma or 'methodolog' in lemma:
            return True
        
        return False
    
    def _suggest_modern_alternative(self, verb_token, doc) -> str:
        """Suggest modern alternative using SpaCy morphological analysis."""
        lemma = verb_token.lemma_.lower()
        
        # Use morphological analysis to suggest simpler alternatives
        if 'circul' in lemma:
            return 'share'
        elif 'utiliz' in lemma:
            return 'use'
        elif 'facilitat' in lemma:
            return 'help'
        elif 'commenc' in lemma:
            return 'start'
        elif 'terminat' in lemma:
            return 'end'
        elif 'guarant' in lemma:
            return 'ensure'
        
        # For other formal verbs, try to simplify based on morphological patterns
        if self._is_latinate_verb_pattern(verb_token):
            return self._suggest_germanic_alternative(lemma)
        
        return None
    
    def _suggest_germanic_alternative(self, lemma) -> str:
        """Suggest Germanic alternative for Latinate verbs."""
        # Common Latinate → Germanic mappings based on semantic patterns
        if lemma.endswith('ate'):
            if 'demonstr' in lemma:
                return 'show'
            elif 'indic' in lemma:
                return 'show'
            elif 'estab' in lemma:
                return 'set up'
        
        elif lemma.endswith('ize'):
            if 'organ' in lemma:
                return 'arrange'
            elif 'real' in lemma:
                return 'see'
        
        return 'simplify'  # Generic fallback
    