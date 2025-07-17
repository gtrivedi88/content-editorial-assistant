"""
Conversational Style Rule
Based on IBM Style Guide topic: "Conversational style"
Enhanced with pure SpaCy morphological analysis and linguistic anchors.
"""
from typing import List, Dict, Any, Optional
from .base_audience_rule import BaseAudienceRule

class ConversationalStyleRule(BaseAudienceRule):
    """
    Checks for language that is overly formal or complex, hindering a
    conversational style. Uses advanced morphological analysis to identify
    formal patterns and suggest conversational alternatives.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize conversational-specific linguistic anchors
        self._initialize_conversational_anchors()
    
    def _initialize_conversational_anchors(self):
        """Initialize morphological patterns specific to conversational style analysis."""
        
        # Morphological complexity thresholds for conversational appropriateness
        self.conversational_thresholds = {
            'max_formality_score': 0.75,  # Above this is too formal
            'max_morphological_complexity': 2.5,  # Above this is too complex
            'max_syllables': 4,  # Prefer shorter words
            'min_frequency_class': 'medium'  # Avoid rare words
        }
        
        # Morphological patterns that indicate overly formal language
        self.formal_morphological_patterns = {
            'latinate_derivational_suffixes': [
                'tion', 'sion', 'ment', 'ance', 'ence', 'ity', 'ous', 
                'ive', 'ate', 'ize', 'ify', 'able', 'ible', 'ous'
            ],
            'complex_verbal_forms': [
                'VerbForm=Ger+Tense=Pres',  # gerunds in formal contexts
                'VerbForm=Part+Tense=Past',  # past participles as adjectives
                'Mood=Sub'  # subjunctive mood
            ],
            'nominal_style_indicators': [
                'nmod',  # nominal modifiers (often in bureaucratic writing)
                'compound',  # compound constructions
                'amod+ADJ+Degree=Pos'  # formal adjective modifications
            ]
        }
        
        # Context-aware conversational alternatives based on semantic fields
        self.conversational_alternatives = {
            'action_verbs': {
                'utilize': ['use', 'apply'],
                'facilitate': ['help', 'enable'],
                'implement': ['do', 'carry out', 'put in place'],
                'demonstrate': ['show', 'prove'],
                'commence': ['start', 'begin'],
                'terminate': ['end', 'stop'],
                'accomplish': ['do', 'complete'],
                'acquire': ['get', 'obtain'],
                'construct': ['build', 'make'],
                'establish': ['set up', 'create']
            },
            'descriptive_adjectives': {
                'optimal': ['best', 'ideal'],
                'sufficient': ['enough', 'adequate'],
                'substantial': ['large', 'significant'],
                'comprehensive': ['complete', 'thorough'],
                'fundamental': ['basic', 'key'],
                'additional': ['more', 'extra'],
                'numerous': ['many', 'several'],
                'significant': ['important', 'major']
            },
            'connecting_words': {
                'consequently': ['so', 'therefore'],
                'furthermore': ['also', 'in addition'],
                'nevertheless': ['but', 'however'],
                'subsequently': ['then', 'later'],
                'alternatively': ['instead', 'or']
            }
        }

    def _get_rule_type(self) -> str:
        return 'audience_conversational'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for overly formal language that hinders conversational tone.
        Uses pure SpaCy morphological analysis to identify complex patterns.
        """
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = self._analyze_sentence_structure(sentence, nlp)
            if not doc:
                continue
            
            # Use the base class method for conversational analysis
            sentence_errors = self._analyze_conversational_appropriateness(doc, sentence, i)
            errors.extend(sentence_errors)
            
            # Additional conversational-specific analysis
            additional_errors = self._analyze_conversational_specific_patterns(doc, sentence, i)
            errors.extend(additional_errors)

        return errors
    
    def _analyze_conversational_specific_patterns(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Analyze patterns specifically problematic for conversational style.
        """
        errors = []
        
        # Analyze passive voice constructions (often formal)
        passive_constructions = self._detect_passive_voice_morphologically(doc)
        for passive in passive_constructions:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Passive voice can make writing less conversational. Consider using active voice.",
                suggestions=[f"Rewrite '{passive['text']}' in active voice for better conversational flow."],
                severity='low',
                linguistic_analysis={
                    'passive_construction': passive,
                    'morphological_pattern': passive.get('morphological_pattern')
                }
            ))
        
        # Analyze nominal style (noun-heavy constructions)
        nominal_style_issues = self._detect_nominal_style_morphologically(doc)
        for nominal_issue in nominal_style_issues:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="This construction is too noun-heavy for conversational style. Use more verbs.",
                suggestions=["Rewrite using more active, verb-based language."],
                severity='medium',
                linguistic_analysis={
                    'nominal_construction': nominal_issue,
                    'morphological_analysis': nominal_issue.get('morphological_features')
                }
            ))
        
        # Analyze complex subordinate constructions
        complex_subordination = self._detect_complex_subordination(doc)
        for complex_sub in complex_subordination:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Complex subordinate clauses can make text hard to follow conversationally.",
                suggestions=["Break this into simpler, shorter sentences."],
                severity='medium',
                linguistic_analysis={
                    'complex_subordination': complex_sub,
                    'dependency_depth': complex_sub.get('depth')
                }
            ))
        
        return errors
    
    def _detect_passive_voice_morphologically(self, doc) -> List[Dict[str, Any]]:
        """
        Detect passive voice constructions using morphological analysis.
        """
        passive_constructions = []
        
        if not doc:
            return passive_constructions
        
        try:
            for token in doc:
                # Look for passive voice patterns: auxiliary + past participle
                if (token.dep_ == 'auxpass' or 
                    (token.lemma_ in ['be', 'get', 'become'] and token.dep_ == 'aux')):
                    
                    # Find the past participle
                    for child in token.head.children:
                        if (child.tag_ in ['VBN', 'VBD'] and 
                            hasattr(child, 'morph') and 
                            'VerbForm=Part' in str(child.morph)):
                            
                            # Construct the passive phrase
                            passive_phrase = f"{token.text} {child.text}"
                            
                            passive_constructions.append({
                                'auxiliary': self._token_to_dict(token),
                                'participle': self._token_to_dict(child),
                                'text': passive_phrase,
                                'morphological_pattern': f"{token.lemma_}+{child.tag_}",
                                'morphological_features': {
                                    'auxiliary': self._get_morphological_features(token),
                                    'participle': self._get_morphological_features(child)
                                }
                            })
        
        except Exception:
            pass
        
        return passive_constructions
    
    def _detect_nominal_style_morphologically(self, doc) -> List[Dict[str, Any]]:
        """
        Detect nominal style (noun-heavy) constructions using morphological analysis.
        """
        nominal_issues = []
        
        if not doc:
            return nominal_issues
        
        try:
            # Count noun phrases and their complexity
            noun_phrase_count = 0
            verb_count = 0
            
            for token in doc:
                if token.pos_ in ['NOUN', 'PROPN']:
                    noun_phrase_count += 1
                elif token.pos_ == 'VERB' and token.dep_ != 'aux':
                    verb_count += 1
            
            # Calculate noun-to-verb ratio
            total_content_words = noun_phrase_count + verb_count
            if total_content_words > 0:
                noun_ratio = noun_phrase_count / total_content_words
                
                # Flag if too noun-heavy (conversational writing should be more verb-heavy)
                if noun_ratio > 0.6 and total_content_words > 5:
                    nominal_issues.append({
                        'noun_count': noun_phrase_count,
                        'verb_count': verb_count,
                        'noun_ratio': noun_ratio,
                        'morphological_features': {
                            'nouns': [self._token_to_dict(token) for token in doc if token.pos_ in ['NOUN', 'PROPN']],
                            'verbs': [self._token_to_dict(token) for token in doc if token.pos_ == 'VERB']
                        }
                    })
            
            # Detect complex noun phrases with multiple modifiers
            for token in doc:
                if token.pos_ in ['NOUN', 'PROPN'] and token.dep_ in ['nsubj', 'dobj', 'pobj']:
                    modifiers = [child for child in token.children if child.dep_ in ['amod', 'nmod', 'compound']]
                    
                    if len(modifiers) > 2:  # Complex noun phrase
                        nominal_issues.append({
                            'complex_noun_phrase': self._token_to_dict(token),
                            'modifiers': [self._token_to_dict(mod) for mod in modifiers],
                            'modifier_count': len(modifiers),
                            'morphological_features': {
                                'head_noun': self._get_morphological_features(token),
                                'modifiers': [self._get_morphological_features(mod) for mod in modifiers]
                            }
                        })
        
        except Exception:
            pass
        
        return nominal_issues
    
    def _detect_complex_subordination(self, doc) -> List[Dict[str, Any]]:
        """
        Detect complex subordinate clause constructions.
        """
        complex_subordinations = []
        
        if not doc:
            return complex_subordinations
        
        try:
            for token in doc:
                # Look for subordinate clause markers
                if token.dep_ in ['mark', 'advcl', 'ccomp', 'xcomp'] and token.pos_ in ['SCONJ', 'VERB']:
                    
                    # Calculate the depth of the subordinate clause
                    clause_depth = self._calculate_clause_depth(token)
                    
                    if clause_depth > 2:  # Deep subordination
                        complex_subordinations.append({
                            'subordinate_marker': self._token_to_dict(token),
                            'depth': clause_depth,
                            'clause_type': token.dep_,
                            'morphological_features': self._get_morphological_features(token)
                        })
        
        except Exception:
            pass
        
        return complex_subordinations
    
    def _calculate_clause_depth(self, token) -> int:
        """
        Calculate the depth of embedding for a clause.
        """
        if not token:
            return 0
        
        depth = 0
        current = token
        
        try:
            while current and current.dep_ != 'ROOT':
                if current.dep_ in ['advcl', 'ccomp', 'xcomp', 'acl']:
                    depth += 1
                current = current.head
        except Exception:
            pass
        
        return depth
    
    def _find_conversational_alternative(self, token) -> Optional[str]:
        """
        Find conversational alternatives using morphological and semantic analysis.
        Enhanced version of the base class method.
        """
        if not token:
            return None
        
        lemma = token.lemma_.lower()
        
        # Check all alternative categories
        for category, alternatives in self.conversational_alternatives.items():
            if lemma in alternatives:
                # Return the first (most conversational) alternative
                return alternatives[lemma][0]
        
        # Use the base class method as fallback
        return self._find_simpler_morphological_alternative(token)
