"""
LLM Consumability Rule
Based on IBM Style Guide topic: "LLM consumability"
Enhanced with pure SpaCy morphological analysis for robust LLM processing pattern detection.
"""
from typing import List, Dict, Any, Optional, Set
from .base_audience_rule import BaseAudienceRule

class LLMConsumabilityRule(BaseAudienceRule):
    """
    Checks for content patterns that are difficult for Large Language Models (LLMs)
    to process effectively. Uses advanced morphological and semantic analysis to identify
    structural patterns, reference ambiguities, and content organization issues.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize LLM consumability-specific linguistic anchors
        self._initialize_llm_consumability_anchors()
    
    def _initialize_llm_consumability_anchors(self):
        """Initialize morphological patterns specific to LLM consumability analysis."""
        
        # Content adequacy thresholds for LLM processing
        self.llm_content_thresholds = {
            'min_topic_length': 15,  # words per topic/section
            'min_context_density': 0.3,  # content words to total words ratio
            'max_reference_ambiguity': 0.4,  # pronoun to noun ratio
            'min_semantic_coherence': 0.6  # semantic consistency score
        }
        
        # Morphological patterns that indicate LLM processing difficulties
        self.llm_difficulty_patterns = {
            'structural_indicators': {
                'accordion_markers': ['expand', 'collapse', 'hidden', 'toggle'],
                'ui_references': ['click', 'select', 'dropdown', 'button', 'menu'],
                'navigation_patterns': ['next', 'previous', 'step', 'tab', 'section'],
                'formatting_dependent': ['bold', 'italic', 'highlighted', 'colored']
            },
            'reference_ambiguity': {
                'vague_pronouns': ['it', 'this', 'that', 'these', 'those'],
                'indefinite_references': ['something', 'anything', 'everything'],
                'temporal_deixis': ['now', 'then', 'later', 'before', 'after'],
                'spatial_deixis': ['here', 'there', 'above', 'below', 'nearby']
            },
            'content_fragmentation': {
                'incomplete_sentences': True,  # Detected via syntax analysis
                'orphaned_lists': True,  # Lists without context
                'cross_references': True,  # References to external content
                'modal_dependencies': True  # Content requiring specific modes/states
            }
        }
        
        # Semantic coherence indicators using morphological analysis
        self.semantic_coherence_patterns = {
            'topic_consistency': {
                'lexical_fields': True,  # Consistent vocabulary domains
                'entity_continuity': True,  # Named entity consistency
                'temporal_consistency': True,  # Time reference consistency
                'causal_coherence': True  # Logical flow indicators
            },
            'information_density': {
                'content_word_ratio': 0.4,  # Minimum content words per sentence
                'concept_density': 0.3,  # Unique concepts per sentence
                'elaboration_markers': ['specifically', 'particularly', 'namely', 'that is']
            }
        }

    def _get_rule_type(self) -> str:
        return 'audience_llm_consumability'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for structures and patterns that reduce LLM consumability
        using comprehensive morphological and semantic analysis.
        """
        errors = []
        if not nlp:
            return errors

        # Analyze overall document structure for LLM consumability
        document_errors = self._analyze_document_structure_for_llm(sentences, nlp, context)
        errors.extend(document_errors)

        # Analyze individual sentences
        for i, sentence in enumerate(sentences):
            doc = self._analyze_sentence_structure(sentence, nlp)
            if not doc:
                continue
            
            # Analyze sentence-level LLM consumability issues
            sentence_errors = self._analyze_sentence_llm_consumability(doc, sentence, i)
            errors.extend(sentence_errors)

        return errors
    
    def _analyze_document_structure_for_llm(self, sentences: List[str], nlp, context=None) -> List[Dict[str, Any]]:
        """
        Analyze document-level patterns that affect LLM processing.
        """
        errors = []
        
        # Check for content adequacy (avoiding tiny topics)
        content_adequacy = self._analyze_content_adequacy(sentences, nlp)
        if content_adequacy['is_inadequate']:
            errors.append(self._create_error(
                sentence=" ".join(sentences[:3]),  # Show first few sentences as context
                sentence_index=0,
                message="Content may be too brief for effective LLM processing. Provide more comprehensive information.",
                suggestions=[
                    "Expand the content with more details and context.",
                    "Add examples or explanations to increase information density.",
                    "Consider combining with related topics for better LLM comprehension."
                ],
                severity='medium',
                linguistic_analysis=content_adequacy
            ))
        
        # Check for structural fragmentation
        fragmentation_issues = self._detect_structural_fragmentation(sentences, nlp)
        for issue in fragmentation_issues:
            errors.append(self._create_error(
                sentence=issue.get('example_sentence', ''),
                sentence_index=issue.get('sentence_index', 0),
                message=f"Structural fragmentation detected: {issue['type']}",
                suggestions=issue.get('suggestions', ["Provide more context and complete information."]),
                severity='medium',
                linguistic_analysis={'fragmentation_issue': issue}
            ))
        
        return errors
    
    def _analyze_sentence_llm_consumability(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Analyze sentence-level patterns that affect LLM consumability.
        """
        errors = []
        
        # Analyze reference ambiguity
        reference_issues = self._analyze_reference_ambiguity(doc)
        for issue in reference_issues:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Ambiguous reference '{issue['reference']}' may confuse LLMs. Provide clearer context.",
                suggestions=[f"Replace '{issue['reference']}' with a specific noun or more detailed description."],
                severity='low',
                linguistic_analysis={
                    'reference_ambiguity': issue,
                    'morphological_pattern': issue.get('morphological_pattern')
                }
            ))
        
        # Analyze UI and structural dependencies
        ui_dependencies = self._detect_ui_structural_dependencies(doc)
        for dependency in ui_dependencies:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"UI-dependent language '{dependency['text']}' may not be processed correctly by LLMs.",
                suggestions=[
                    "Describe the action or concept directly without relying on UI elements.",
                    "Provide context that doesn't depend on visual interface elements."
                ],
                severity='medium',
                linguistic_analysis={
                    'ui_dependency': dependency,
                    'dependency_type': dependency.get('type')
                }
            ))
        
        # Analyze semantic density and coherence
        semantic_issues = self._analyze_semantic_density(doc)
        if semantic_issues['density_score'] < self.llm_content_thresholds['min_context_density']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Low information density may reduce LLM processing effectiveness.",
                suggestions=[
                    "Add more specific details and context.",
                    "Include concrete examples or explanations.",
                    "Reduce filler words and increase content words."
                ],
                severity='low',
                linguistic_analysis=semantic_issues
            ))
        
        return errors
    
    def _analyze_content_adequacy(self, sentences: List[str], nlp) -> Dict[str, Any]:
        """
        Analyze whether content is adequate for effective LLM processing.
        """
        try:
            total_words = 0
            content_words = 0
            unique_concepts = set()
            
            for sentence in sentences:
                doc = self._analyze_sentence_structure(sentence, nlp)
                if not doc:
                    continue
                
                sentence_words = len([token for token in doc if token.is_alpha])
                total_words += sentence_words
                
                # Count content words (nouns, verbs, adjectives, adverbs)
                sentence_content_words = len([
                    token for token in doc 
                    if token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV'] and not token.is_stop
                ])
                content_words += sentence_content_words
                
                # Extract unique concepts (lemmas of content words)
                for token in doc:
                    if token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV'] and not token.is_stop:
                        unique_concepts.add(token.lemma_.lower())
            
            # Calculate adequacy metrics
            avg_sentence_length = total_words / max(len(sentences), 1)
            content_density = content_words / max(total_words, 1)
            concept_diversity = len(unique_concepts) / max(total_words, 1)
            
            is_inadequate = (
                total_words < self.llm_content_thresholds['min_topic_length'] or
                content_density < self.llm_content_thresholds['min_context_density'] or
                len(unique_concepts) < 5  # Minimum concept diversity
            )
            
            return {
                'is_inadequate': is_inadequate,
                'total_words': total_words,
                'content_words': content_words,
                'unique_concepts': len(unique_concepts),
                'avg_sentence_length': avg_sentence_length,
                'content_density': content_density,
                'concept_diversity': concept_diversity,
                'adequacy_score': (content_density + concept_diversity + min(total_words/30, 1.0)) / 3
            }
        
        except Exception:
            return {
                'is_inadequate': False,
                'error': 'content_adequacy_analysis_failed'
            }
    
    def _detect_structural_fragmentation(self, sentences: List[str], nlp) -> List[Dict[str, Any]]:
        """
        Detect structural fragmentation that affects LLM processing.
        """
        fragmentation_issues = []
        
        try:
            for i, sentence in enumerate(sentences):
                doc = self._analyze_sentence_structure(sentence, nlp)
                if not doc:
                    continue
                
                # Detect incomplete sentences (missing main verb or subject)
                if self._is_incomplete_sentence(doc):
                    fragmentation_issues.append({
                        'type': 'incomplete_sentence',
                        'sentence_index': i,
                        'example_sentence': sentence,
                        'morphological_analysis': self._analyze_sentence_completeness(doc),
                        'suggestions': ["Complete the sentence with a clear subject and predicate."]
                    })
                
                # Detect orphaned lists (lists without sufficient context)
                if self._is_orphaned_list(doc, sentences, i):
                    fragmentation_issues.append({
                        'type': 'orphaned_list',
                        'sentence_index': i,
                        'example_sentence': sentence,
                        'suggestions': ["Provide context before presenting lists or examples."]
                    })
                
                # Detect cross-references that may be unclear to LLMs
                cross_refs = self._detect_cross_references(doc)
                if cross_refs:
                    fragmentation_issues.append({
                        'type': 'unclear_cross_reference',
                        'sentence_index': i,
                        'example_sentence': sentence,
                        'cross_references': cross_refs,
                        'suggestions': ["Make references more explicit and self-contained."]
                    })
        
        except Exception:
            pass
        
        return fragmentation_issues
    
    def _analyze_reference_ambiguity(self, doc) -> List[Dict[str, Any]]:
        """
        Analyze ambiguous references that can confuse LLMs.
        """
        ambiguous_references = []
        
        if not doc:
            return ambiguous_references
        
        try:
            # Track nouns for reference resolution analysis
            noun_entities = []
            for token in doc:
                if token.pos_ in ['NOUN', 'PROPN']:
                    noun_entities.append(token)
            
            # Analyze pronouns and their potential ambiguity
            for token in doc:
                if token.pos_ == 'PRON':
                    ambiguity_analysis = self._analyze_pronoun_ambiguity(token, noun_entities, doc)
                    
                    if ambiguity_analysis['is_ambiguous']:
                        ambiguous_references.append({
                            'reference': token.text,
                            'type': 'pronoun',
                            'ambiguity_score': ambiguity_analysis['ambiguity_score'],
                            'potential_antecedents': ambiguity_analysis['potential_antecedents'],
                            'morphological_pattern': f"{token.pos_}+{token.dep_}",
                            'morphological_features': self._get_morphological_features(token)
                        })
                
                # Analyze demonstrative references
                elif token.lemma_.lower() in ['this', 'that', 'these', 'those']:
                    demonstrative_analysis = self._analyze_demonstrative_ambiguity(token, doc)
                    
                    if demonstrative_analysis['is_ambiguous']:
                        ambiguous_references.append({
                            'reference': token.text,
                            'type': 'demonstrative',
                            'ambiguity_score': demonstrative_analysis['ambiguity_score'],
                            'morphological_pattern': f"{token.pos_}+{token.dep_}",
                            'context_analysis': demonstrative_analysis
                        })
        
        except Exception:
            pass
        
        return ambiguous_references
    
    def _detect_ui_structural_dependencies(self, doc) -> List[Dict[str, Any]]:
        """
        Detect UI and structural dependencies that LLMs may not process well.
        """
        ui_dependencies = []
        
        if not doc:
            return ui_dependencies
        
        try:
            # Analyze for UI-dependent language patterns
            ui_indicators = self.llm_difficulty_patterns['structural_indicators']
            
            for token in doc:
                lemma = token.lemma_.lower()
                
                # Check for UI action words
                for category, indicators in ui_indicators.items():
                    if lemma in indicators:
                        # Analyze the morphological context
                        context_analysis = self._analyze_ui_context(token, doc)
                        
                        ui_dependencies.append({
                            'text': token.text,
                            'type': category,
                            'ui_action': lemma,
                            'morphological_features': self._get_morphological_features(token),
                            'context_analysis': context_analysis,
                            'dependency_level': self._calculate_ui_dependency_level(token, doc)
                        })
            
            # Detect accordion/collapsible content patterns
            accordion_patterns = self._detect_accordion_patterns(doc)
            ui_dependencies.extend(accordion_patterns)
        
        except Exception:
            pass
        
        return ui_dependencies
    
    def _analyze_semantic_density(self, doc) -> Dict[str, Any]:
        """
        Analyze semantic density and information content for LLM processing.
        """
        if not doc:
            return {'density_score': 0.0}
        
        try:
            total_tokens = len([token for token in doc if token.is_alpha])
            content_tokens = len([
                token for token in doc 
                if token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV'] and not token.is_stop
            ])
            
            # Calculate information density metrics
            content_density = content_tokens / max(total_tokens, 1)
            
            # Analyze semantic coherence using entity and concept continuity
            entities = [ent.text for ent in doc.ents]
            unique_lemmas = set(token.lemma_.lower() for token in doc if token.pos_ in ['NOUN', 'VERB', 'ADJ'])
            lexical_diversity = len(unique_lemmas) / max(content_tokens, 1)
            
            # Calculate overall semantic density score
            density_score = (content_density + lexical_diversity) / 2
            
            return {
                'density_score': density_score,
                'content_density': content_density,
                'lexical_diversity': lexical_diversity,
                'total_tokens': total_tokens,
                'content_tokens': content_tokens,
                'unique_concepts': len(unique_lemmas),
                'entities': entities
            }
        
        except Exception:
            return {
                'density_score': 0.0,
                'error': 'semantic_density_analysis_failed'
            }
    
    def _is_incomplete_sentence(self, doc) -> bool:
        """
        Check if a sentence is structurally incomplete.
        """
        if not doc:
            return True
        
        try:
            # Check for main verb
            has_main_verb = any(token.dep_ == 'ROOT' and token.pos_ == 'VERB' for token in doc)
            
            # Check for subject
            has_subject = any(token.dep_ in ['nsubj', 'nsubjpass'] for token in doc)
            
            # Very short sentences are likely incomplete
            content_words = len([token for token in doc if token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV']])
            is_too_short = content_words < 2
            
            return not has_main_verb or not has_subject or is_too_short
        
        except Exception:
            return False
    
    def _is_orphaned_list(self, doc, sentences: List[str], current_index: int) -> bool:
        """
        Check if this sentence is an orphaned list item without sufficient context.
        """
        try:
            # Simple heuristic: check if sentence starts with bullet point or number
            text = sentences[current_index].strip()
            
            if (text.startswith(('•', '-', '*', '1.', '2.', '3.')) and 
                len(text.split()) < 5):  # Short list item
                
                # Check if previous sentences provide context
                context_words = 0
                for i in range(max(0, current_index - 2), current_index):
                    if i < len(sentences):
                        context_words += len(sentences[i].split())
                
                return context_words < 10  # Insufficient context
        
        except Exception:
            pass
        
        return False
    
    def _detect_cross_references(self, doc) -> List[Dict[str, Any]]:
        """
        Detect cross-references that may be unclear to LLMs.
        """
        cross_references = []
        
        try:
            # Look for referential patterns
            reference_patterns = [
                'see above', 'see below', 'as mentioned', 'refer to',
                'in the previous', 'in the next', 'earlier', 'later'
            ]
            
            text = doc.text.lower()
            for pattern in reference_patterns:
                if pattern in text:
                    cross_references.append({
                        'pattern': pattern,
                        'type': 'cross_reference',
                        'clarity_score': 0.3  # Low clarity for LLMs
                    })
        
        except Exception:
            pass
        
        return cross_references
    
    def _analyze_pronoun_ambiguity(self, pronoun_token, noun_entities, doc) -> Dict[str, Any]:
        """
        Analyze ambiguity of pronoun references.
        """
        try:
            # Simple ambiguity analysis based on potential antecedents
            potential_antecedents = []
            
            # Look for nouns that could be antecedents (before the pronoun)
            for noun in noun_entities:
                if noun.i < pronoun_token.i:  # Noun appears before pronoun
                    # Check morphological agreement (simplified)
                    if self._check_morphological_agreement(pronoun_token, noun):
                        potential_antecedents.append(self._token_to_dict(noun))
            
            # Calculate ambiguity score
            ambiguity_score = min(len(potential_antecedents) / 3.0, 1.0)  # More candidates = more ambiguous
            is_ambiguous = len(potential_antecedents) > 1 or len(potential_antecedents) == 0
            
            return {
                'is_ambiguous': is_ambiguous,
                'ambiguity_score': ambiguity_score,
                'potential_antecedents': potential_antecedents,
                'antecedent_count': len(potential_antecedents)
            }
        
        except Exception:
            return {
                'is_ambiguous': False,
                'ambiguity_score': 0.0,
                'potential_antecedents': [],
                'error': 'pronoun_analysis_failed'
            }
    
    def _analyze_demonstrative_ambiguity(self, demonstrative_token, doc) -> Dict[str, Any]:
        """
        Analyze ambiguity of demonstrative references.
        """
        try:
            # Check if demonstrative has clear referent
            has_clear_referent = False
            
            # Look for nearby nouns or noun phrases
            for token in doc:
                if (abs(token.i - demonstrative_token.i) <= 3 and 
                    token.pos_ in ['NOUN', 'PROPN'] and 
                    token.dep_ in ['dobj', 'pobj', 'nsubj']):
                    has_clear_referent = True
                    break
            
            ambiguity_score = 0.7 if not has_clear_referent else 0.2
            
            return {
                'is_ambiguous': not has_clear_referent,
                'ambiguity_score': ambiguity_score,
                'has_clear_referent': has_clear_referent
            }
        
        except Exception:
            return {
                'is_ambiguous': False,
                'ambiguity_score': 0.0,
                'error': 'demonstrative_analysis_failed'
            }
    
    def _analyze_sentence_completeness(self, doc) -> Dict[str, Any]:
        """
        Analyze structural completeness of a sentence.
        """
        try:
            root_verbs = [token for token in doc if token.dep_ == 'ROOT']
            subjects = [token for token in doc if token.dep_ in ['nsubj', 'nsubjpass']]
            objects = [token for token in doc if token.dep_ in ['dobj', 'iobj', 'pobj']]
            
            return {
                'has_root_verb': len(root_verbs) > 0,
                'has_subject': len(subjects) > 0,
                'has_object': len(objects) > 0,
                'root_verbs': [self._token_to_dict(token) for token in root_verbs],
                'subjects': [self._token_to_dict(token) for token in subjects],
                'structural_completeness_score': (len(root_verbs) + len(subjects)) / 2.0
            }
        
        except Exception:
            return {
                'has_root_verb': False,
                'has_subject': False,
                'structural_completeness_score': 0.0,
                'error': 'completeness_analysis_failed'
            }
    
    def _analyze_ui_context(self, token, doc) -> Dict[str, Any]:
        """
        Analyze the context of UI-dependent language.
        """
        try:
            # Check surrounding context for additional UI indicators
            window_size = 3
            start_idx = max(0, token.i - window_size)
            end_idx = min(len(doc), token.i + window_size + 1)
            
            context_tokens = doc[start_idx:end_idx]
            ui_context_words = []
            
            for ctx_token in context_tokens:
                if ctx_token.lemma_.lower() in ['click', 'select', 'choose', 'press', 'tap']:
                    ui_context_words.append(ctx_token.text)
            
            return {
                'context_window': [t.text for t in context_tokens],
                'ui_context_words': ui_context_words,
                'ui_density': len(ui_context_words) / len(context_tokens)
            }
        
        except Exception:
            return {
                'context_window': [],
                'ui_context_words': [],
                'ui_density': 0.0
            }
    
    def _calculate_ui_dependency_level(self, token, doc) -> float:
        """
        Calculate how dependent the text is on UI elements.
        """
        try:
            # Simple heuristic based on context and morphological features
            ui_score = 0.0
            
            # Check if it's an imperative (command)
            if token.tag_ in ['VB', 'VBP'] and token.dep_ == 'ROOT':
                ui_score += 0.3
            
            # Check for direct object that might be UI element
            for child in token.children:
                if child.dep_ == 'dobj' and child.lemma_.lower() in ['button', 'link', 'menu', 'option']:
                    ui_score += 0.4
            
            return min(ui_score, 1.0)
        
        except Exception:
            return 0.0
    
    def _detect_accordion_patterns(self, doc) -> List[Dict[str, Any]]:
        """
        Detect accordion or collapsible content patterns.
        """
        accordion_patterns = []
        
        try:
            accordion_indicators = ['expand', 'collapse', 'accordion', 'section', 'toggle', 'hidden']
            
            for token in doc:
                if token.lemma_.lower() in accordion_indicators:
                    # Check if this refers to content structure
                    structural_context = self._analyze_structural_context(token, doc)
                    
                    if structural_context['is_structural']:
                        accordion_patterns.append({
                            'text': token.text,
                            'type': 'accordion_reference',
                            'structural_indicator': token.lemma_.lower(),
                            'context_analysis': structural_context,
                            'morphological_features': self._get_morphological_features(token)
                        })
        
        except Exception:
            pass
        
        return accordion_patterns
    
    def _analyze_structural_context(self, token, doc) -> Dict[str, Any]:
        """
        Analyze if a token refers to structural/UI elements.
        """
        try:
            # Look for prepositions or determiners that indicate structural reference
            structural_indicators = []
            
            for child in token.children:
                if child.dep_ in ['prep', 'det'] and child.lemma_.lower() in ['the', 'in', 'under', 'within']:
                    structural_indicators.append(child.text)
            
            is_structural = len(structural_indicators) > 0
            
            return {
                'is_structural': is_structural,
                'structural_indicators': structural_indicators,
                'dependency_pattern': f"{token.dep_}+{token.pos_}"
            }
        
        except Exception:
            return {
                'is_structural': False,
                'structural_indicators': [],
                'error': 'structural_analysis_failed'
            }
    
    def _check_morphological_agreement(self, pronoun, noun) -> bool:
        """
        Check basic morphological agreement between pronoun and potential antecedent.
        """
        try:
            # Simplified agreement checking
            pronoun_features = self._get_morphological_features(pronoun)
            noun_features = self._get_morphological_features(noun)
            
            # Check number agreement
            pronoun_number = pronoun_features.get('morph', {}).get('Number', '')
            noun_number = noun_features.get('morph', {}).get('Number', '')
            
            if pronoun_number and noun_number:
                return pronoun_number == noun_number
            
            # Fallback: basic pronoun-noun compatibility
            singular_pronouns = ['it', 'he', 'she', 'this', 'that']
            plural_pronouns = ['they', 'these', 'those']
            
            if pronoun.text.lower() in singular_pronouns:
                return noun.tag_ in ['NN', 'NNP']  # Singular nouns
            elif pronoun.text.lower() in plural_pronouns:
                return noun.tag_ in ['NNS', 'NNPS']  # Plural nouns
            
            return True  # Default to compatible
        
        except Exception:
            return False
