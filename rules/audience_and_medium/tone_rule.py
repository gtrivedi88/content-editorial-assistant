"""
Tone Rule
Based on IBM Style Guide topic: "Tone"
Enhanced with pure SpaCy morphological analysis for robust professional tone detection.
"""
from typing import List, Dict, Any, Optional, Set, Tuple
from .base_audience_rule import BaseAudienceRule

class ToneRule(BaseAudienceRule):
    """
    Checks for violations of professional tone using advanced morphological and semantic analysis.
    Detects jargon, idioms, informal language, and other patterns that conflict with professional communication.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize tone-specific linguistic anchors
        self._initialize_tone_anchors()
    
    def _initialize_tone_anchors(self):
        """Initialize morphological patterns specific to professional tone analysis."""
        
        # Professional tone thresholds and indicators
        self.professional_tone_thresholds = {
            'max_informality_score': 0.4,  # Above this is too informal
            'min_objectivity_score': 0.6,  # Below this is too subjective
            'max_emotional_intensity': 0.5,  # Above this is too emotional
            'min_precision_score': 0.5  # Below this lacks precision
        }
        
        # Morphological patterns that indicate unprofessional tone
        self.tone_violation_patterns = {
            'informal_language': {
                'contractions': True,  # Detected via morphological analysis
                'colloquialisms': True,  # Detected via register analysis
                'slang_patterns': True,  # Detected via formality scoring
                'filler_words': ['like', 'um', 'you know', 'basically', 'actually']
            },
            'emotional_language': {
                'intensifiers': ['extremely', 'incredibly', 'absolutely', 'totally', 'completely'],
                'subjective_evaluatives': ['amazing', 'terrible', 'awesome', 'horrible', 'fantastic'],
                'emotional_adjectives': True,  # Detected via sentiment analysis
                'exclamatory_patterns': True  # Detected via punctuation and morphology
            },
            'imprecise_language': {
                'vague_quantifiers': ['lots of', 'tons of', 'bunch of', 'loads of'],
                'hedging_overuse': ['maybe', 'perhaps', 'possibly', 'probably'],
                'indefinite_pronouns': ['something', 'anything', 'everything', 'nothing'],
                'approximators': ['around', 'about', 'roughly', 'approximately']
            },
            'inappropriate_register': {
                'sports_metaphors': True,  # Detected via semantic analysis
                'idiomatic_expressions': True,  # Detected via collocation analysis
                'cultural_references': True,  # Detected via entity analysis
                'casual_discourse_markers': ['anyway', 'by the way', 'oh well']
            }
        }
        
        # Professional tone markers for positive detection
        self.professional_tone_markers = {
            'objective_language': {
                'evidence_markers': ['according to', 'based on', 'research shows', 'data indicates'],
                'factual_verbs': ['demonstrates', 'indicates', 'reveals', 'confirms'],
                'neutral_stance': True,  # Detected via sentiment neutrality
                'precise_quantifiers': ['specifically', 'precisely', 'exactly', 'approximately']
            },
            'formal_register': {
                'technical_vocabulary': True,  # Detected via domain analysis
                'complex_syntax': True,  # Detected via dependency depth
                'nominalizations': True,  # Detected via morphological patterns
                'passive_constructions': True  # When appropriate for objectivity
            }
        }

    def _get_rule_type(self) -> str:
        return 'audience_tone'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for professional tone violations using comprehensive
        morphological and semantic analysis.
        """
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = self._analyze_sentence_structure(sentence, nlp)
            if not doc:
                continue
            
            # Use the base class method for professional tone analysis
            sentence_errors = self._analyze_professional_tone(doc, sentence, i)
            errors.extend(sentence_errors)
            
            # Additional tone-specific analysis
            additional_errors = self._analyze_tone_specific_patterns(doc, sentence, i)
            errors.extend(additional_errors)

        return errors
    
    def _analyze_tone_specific_patterns(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Analyze patterns specifically related to professional tone violations.
        """
        errors = []
        
        # Analyze informality patterns
        informality_issues = self._detect_informality_patterns(doc)
        for issue in informality_issues:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Informal language pattern '{issue['text']}' is inappropriate for professional communication.",
                suggestions=issue.get('suggestions', ["Use more formal, professional language."]),
                severity=issue.get('severity', 'medium'),
                linguistic_analysis={
                    'informality_issue': issue,
                    'pattern_type': issue.get('type'),
                    'formality_score': issue.get('formality_score')
                }
            ))
        
        # Analyze emotional language
        emotional_language = self._detect_emotional_language(doc)
        for emotion in emotional_language:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Emotional language '{emotion['text']}' reduces professional objectivity.",
                suggestions=["Use neutral, objective language instead."],
                severity='medium',
                linguistic_analysis={
                    'emotional_language': emotion,
                    'emotion_type': emotion.get('type'),
                    'intensity_score': emotion.get('intensity')
                }
            ))
        
        # Analyze imprecise language
        imprecise_language = self._detect_imprecise_language(doc)
        for imprecision in imprecise_language:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Imprecise language '{imprecision['text']}' lacks professional clarity.",
                suggestions=imprecision.get('suggestions', ["Use more specific, precise language."]),
                severity='low',
                linguistic_analysis={
                    'imprecise_language': imprecision,
                    'precision_score': imprecision.get('precision_score')
                }
            ))
        
        # Analyze inappropriate register
        register_violations = self._detect_inappropriate_register(doc)
        for violation in register_violations:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Language register violation: '{violation['text']}' is too casual for professional contexts.",
                suggestions=["Use more appropriate professional language."],
                severity='medium',
                linguistic_analysis={
                    'register_violation': violation,
                    'violation_type': violation.get('type')
                }
            ))
        
        return errors
    
    def _detect_informality_patterns(self, doc) -> List[Dict[str, Any]]:
        """
        Detect informal language patterns using morphological analysis.
        """
        informality_issues = []
        
        if not doc:
            return informality_issues
        
        try:
            for token in doc:
                # Detect contractions using morphological features
                if self._is_contraction(token):
                    expanded_form = self._expand_contraction(token)
                    
                    informality_issues.append({
                        'text': token.text,
                        'type': 'contraction',
                        'expanded_form': expanded_form,
                        'formality_score': self._analyze_formality_level(token),
                        'morphological_features': self._get_morphological_features(token),
                        'suggestions': [f"Replace '{token.text}' with '{expanded_form}' for professional tone."],
                        'severity': 'low'
                    })
                
                # Detect filler words and discourse markers
                elif self._is_filler_word(token):
                    informality_issues.append({
                        'text': token.text,
                        'type': 'filler_word',
                        'formality_score': self._analyze_formality_level(token),
                        'morphological_features': self._get_morphological_features(token),
                        'suggestions': ["Remove filler words for clearer professional communication."],
                        'severity': 'low'
                    })
                
                # Detect colloquial language using register analysis
                elif self._is_colloquial(token):
                    formal_alternative = self._find_formal_alternative(token)
                    
                    informality_issues.append({
                        'text': token.text,
                        'type': 'colloquialism',
                        'formal_alternative': formal_alternative,
                        'formality_score': self._analyze_formality_level(token),
                        'morphological_features': self._get_morphological_features(token),
                        'suggestions': [f"Replace with more formal language: '{formal_alternative}'"] if formal_alternative else ["Use more formal language."],
                        'severity': 'medium'
                    })
        
        except Exception:
            pass
        
        return informality_issues
    
    def _detect_emotional_language(self, doc) -> List[Dict[str, Any]]:
        """
        Detect emotional language that reduces professional objectivity.
        """
        emotional_language = []
        
        if not doc:
            return emotional_language
        
        try:
            for token in doc:
                # Analyze emotional intensity using morphological and semantic features
                emotion_analysis = self._analyze_emotional_content(token, doc)
                
                if emotion_analysis['is_emotional']:
                    emotional_language.append({
                        'text': token.text,
                        'type': emotion_analysis['emotion_type'],
                        'intensity': emotion_analysis['intensity_score'],
                        'valence': emotion_analysis.get('valence'),  # positive/negative
                        'morphological_features': self._get_morphological_features(token),
                        'semantic_field': self._analyze_semantic_field(token, doc)
                    })
        
        except Exception:
            pass
        
        return emotional_language
    
    def _detect_imprecise_language(self, doc) -> List[Dict[str, Any]]:
        """
        Detect imprecise language that lacks professional clarity.
        """
        imprecise_language = []
        
        if not doc:
            return imprecise_language
        
        try:
            for token in doc:
                # Analyze precision using morphological and semantic features
                precision_analysis = self._analyze_precision_level(token, doc)
                
                if precision_analysis['is_imprecise']:
                    precise_alternative = self._find_precise_alternative(token, doc)
                    
                    imprecise_language.append({
                        'text': token.text,
                        'type': precision_analysis['imprecision_type'],
                        'precision_score': precision_analysis['precision_score'],
                        'precise_alternative': precise_alternative,
                        'morphological_features': self._get_morphological_features(token),
                        'suggestions': [f"Be more specific: '{precise_alternative}'"] if precise_alternative else ["Use more precise language."]
                    })
        
        except Exception:
            pass
        
        return imprecise_language
    
    def _detect_inappropriate_register(self, doc) -> List[Dict[str, Any]]:
        """
        Detect inappropriate register for professional communication.
        """
        register_violations = []
        
        if not doc:
            return register_violations
        
        try:
            # Detect idiomatic expressions
            idiomatic_patterns = self._detect_idiomatic_expressions(doc)
            for idiom in idiomatic_patterns:
                register_violations.append({
                    'text': idiom['text'],
                    'type': 'idiomatic_expression',
                    'pattern': idiom.get('pattern'),
                    'morphological_analysis': idiom.get('morphological_features'),
                    'professional_alternative': self._suggest_professional_alternative(idiom)
                })
            
            # Detect sports metaphors and cultural references
            metaphors_and_references = self._detect_metaphors_and_cultural_references(doc)
            register_violations.extend(metaphors_and_references)
            
            # Detect casual discourse markers
            casual_markers = self._detect_casual_discourse_markers(doc)
            register_violations.extend(casual_markers)
        
        except Exception:
            pass
        
        return register_violations
    
    def _is_contraction(self, token) -> bool:
        """
        Check if token is a contraction using morphological analysis.
        """
        try:
            # Check for apostrophe in token
            if "'" in token.text:
                return True
            
            # Check morphological features for contraction indicators
            morph_features = self._get_morphological_features(token)
            
            # Some contractions may be analyzed as separate morphological components
            if (token.pos_ in ['AUX', 'VERB'] and 
                'VerbForm' in str(morph_features.get('morph', '')) and
                token.text.lower() in ['ca', 'wo', 'sha', 've', 'll', 're']):
                return True
            
            return False
        
        except Exception:
            return False
    
    def _expand_contraction(self, token) -> str:
        """
        Expand contraction to its full form.
        """
        contractions_map = {
            "can't": "cannot",
            "won't": "will not",
            "shan't": "shall not",
            "n't": " not",
            "'ve": " have",
            "'ll": " will",
            "'re": " are",
            "'m": " am",
            "'d": " would",
            "it's": "it is",
            "that's": "that is",
            "here's": "here is",
            "there's": "there is",
            "what's": "what is",
            "who's": "who is",
            "where's": "where is",
            "how's": "how is"
        }
        
        text = token.text.lower()
        for contraction, expansion in contractions_map.items():
            if contraction in text:
                return text.replace(contraction, expansion)
        
        return token.text
    
    def _is_filler_word(self, token) -> bool:
        """
        Check if token is a filler word or discourse marker.
        """
        filler_words = self.tone_violation_patterns['informal_language']['filler_words']
        
        return (token.lemma_.lower() in filler_words or
                token.dep_ == 'discourse' or
                (token.pos_ == 'INTJ' and token.lemma_.lower() in ['um', 'uh', 'er']))
    
    def _is_colloquial(self, token) -> bool:
        """
        Check if token represents colloquial language using formality analysis.
        """
        try:
            formality_score = self._analyze_formality_level(token)
            morphological_complexity = self._calculate_morphological_complexity(token)
            
            # Colloquial language typically has low formality and low complexity
            return (formality_score < 0.3 and 
                    morphological_complexity < 1.5 and 
                    token.pos_ in ['VERB', 'ADJ', 'ADV', 'NOUN'] and
                    not token.is_stop)
        
        except Exception:
            return False
    
    def _find_formal_alternative(self, token) -> Optional[str]:
        """
        Find formal alternatives for colloquial language.
        """
        formal_alternatives = {
            'stuff': 'items',
            'things': 'elements',
            'get': 'obtain',
            'big': 'large',
            'small': 'minimal',
            'good': 'effective',
            'bad': 'ineffective',
            'ok': 'acceptable',
            'lots': 'many',
            'tons': 'numerous',
            'huge': 'substantial',
            'tiny': 'minimal',
            'fix': 'resolve',
            'break': 'malfunction',
            'work': 'function',
            'cool': 'effective',
            'neat': 'organized',
            'mess': 'disorder'
        }
        
        lemma = token.lemma_.lower()
        return formal_alternatives.get(lemma)
    
    def _analyze_emotional_content(self, token, doc) -> Dict[str, Any]:
        """
        Analyze emotional content of a token using morphological and semantic features.
        """
        try:
            # Basic emotion detection using lexical patterns
            emotional_intensifiers = ['extremely', 'incredibly', 'absolutely', 'totally', 'completely']
            subjective_evaluatives = ['amazing', 'terrible', 'awesome', 'horrible', 'fantastic', 'brilliant', 'awful']
            
            lemma = token.lemma_.lower()
            
            if lemma in emotional_intensifiers:
                return {
                    'is_emotional': True,
                    'emotion_type': 'intensifier',
                    'intensity_score': 0.8,
                    'valence': 'neutral'
                }
            
            elif lemma in subjective_evaluatives:
                # Determine valence based on word
                positive_words = ['amazing', 'awesome', 'fantastic', 'brilliant', 'excellent']
                valence = 'positive' if lemma in positive_words else 'negative'
                
                return {
                    'is_emotional': True,
                    'emotion_type': 'evaluative',
                    'intensity_score': 0.9,
                    'valence': valence
                }
            
            # Check for emotional punctuation patterns (multiple exclamation marks, etc.)
            elif (hasattr(doc, 'text') and 
                  ('!' in doc.text or '!!' in doc.text)):
                return {
                    'is_emotional': True,
                    'emotion_type': 'exclamatory',
                    'intensity_score': 0.6,
                    'valence': 'excited'
                }
            
            return {
                'is_emotional': False,
                'emotion_type': 'neutral',
                'intensity_score': 0.0,
                'valence': 'neutral'
            }
        
        except Exception:
            return {
                'is_emotional': False,
                'emotion_type': 'unknown',
                'intensity_score': 0.0,
                'valence': 'neutral'
            }
    
    def _analyze_precision_level(self, token, doc) -> Dict[str, Any]:
        """
        Analyze precision level of language using morphological analysis.
        """
        try:
            # Vague quantifiers and approximators
            vague_quantifiers = ['lots', 'tons', 'bunch', 'loads', 'heap']
            approximators = ['around', 'about', 'roughly', 'approximately', 'sort of', 'kind of']
            hedging_words = ['maybe', 'perhaps', 'possibly', 'probably', 'might', 'could']
            
            lemma = token.lemma_.lower()
            text = token.text.lower()
            
            if lemma in vague_quantifiers:
                return {
                    'is_imprecise': True,
                    'imprecision_type': 'vague_quantifier',
                    'precision_score': 0.2
                }
            
            elif lemma in approximators or text in approximators:
                return {
                    'is_imprecise': True,
                    'imprecision_type': 'approximator',
                    'precision_score': 0.4
                }
            
            elif lemma in hedging_words:
                # Some hedging is acceptable in professional contexts
                return {
                    'is_imprecise': True,
                    'imprecision_type': 'hedging',
                    'precision_score': 0.6
                }
            
            return {
                'is_imprecise': False,
                'imprecision_type': 'precise',
                'precision_score': 0.8
            }
        
        except Exception:
            return {
                'is_imprecise': False,
                'imprecision_type': 'unknown',
                'precision_score': 0.5
            }
    
    def _find_precise_alternative(self, token, doc) -> Optional[str]:
        """
        Find more precise alternatives for imprecise language.
        """
        precise_alternatives = {
            'lots': 'many',
            'tons': 'numerous',
            'bunch': 'group',
            'loads': 'many',
            'stuff': 'items',
            'things': 'elements',
            'around': 'approximately',
            'about': 'approximately',
            'sort of': 'somewhat',
            'kind of': 'somewhat',
            'maybe': 'possibly',
            'probably': 'likely'
        }
        
        text = token.text.lower()
        return precise_alternatives.get(text)
    
    def _detect_idiomatic_expressions(self, doc) -> List[Dict[str, Any]]:
        """
        Detect idiomatic expressions using morphological and syntactic patterns.
        """
        idiomatic_expressions = []
        
        try:
            # Look for common idiomatic patterns
            common_idioms = [
                'piece of cake', 'break the ice', 'hit the nail on the head',
                'spill the beans', 'let the cat out of the bag', 'bite the bullet',
                'cut to the chase', 'get the ball rolling', 'think outside the box',
                'touch base', 'circle back', 'low hanging fruit', 'move the needle'
            ]
            
            text = doc.text.lower()
            
            for idiom in common_idioms:
                if idiom in text:
                    idiomatic_expressions.append({
                        'text': idiom,
                        'type': 'common_idiom',
                        'pattern': 'multi_word_expression',
                        'morphological_features': 'idiomatic'
                    })
            
            # Detect potential idiomatic patterns using syntactic analysis
            for token in doc:
                if (token.pos_ == 'VERB' and 
                    any(child.pos_ == 'ADP' and child.dep_ == 'prep' for child in token.children)):
                    
                    # Phrasal verb patterns that might be idiomatic
                    phrasal_verb = f"{token.text} {' '.join([child.text for child in token.children if child.pos_ == 'ADP'])}"
                    
                    if self._is_idiomatic_phrasal_verb(phrasal_verb.lower()):
                        idiomatic_expressions.append({
                            'text': phrasal_verb,
                            'type': 'phrasal_verb_idiom',
                            'pattern': f"{token.pos_}+ADP",
                            'morphological_features': self._get_morphological_features(token)
                        })
        
        except Exception:
            pass
        
        return idiomatic_expressions
    
    def _detect_metaphors_and_cultural_references(self, doc) -> List[Dict[str, Any]]:
        """
        Detect sports metaphors and cultural references.
        """
        metaphors_references = []
        
        try:
            # Sports metaphors
            sports_terms = [
                'home run', 'slam dunk', 'touchdown', 'game changer', 'playing field',
                'ballpark', 'strike out', 'team player', 'bench', 'coaching',
                'play ball', 'full court press', 'punt', 'huddle'
            ]
            
            # Cultural references that may not be universal
            cultural_terms = [
                'american dream', 'wild west', 'melting pot', 'main street',
                'wall street', 'mom and pop', 'apple pie'
            ]
            
            text = doc.text.lower()
            
            for term in sports_terms:
                if term in text:
                    metaphors_references.append({
                        'text': term,
                        'type': 'sports_metaphor',
                        'register_violation': 'casual_metaphor'
                    })
            
            for term in cultural_terms:
                if term in text:
                    metaphors_references.append({
                        'text': term,
                        'type': 'cultural_reference',
                        'register_violation': 'culture_specific'
                    })
        
        except Exception:
            pass
        
        return metaphors_references
    
    def _detect_casual_discourse_markers(self, doc) -> List[Dict[str, Any]]:
        """
        Detect casual discourse markers inappropriate for professional tone.
        """
        casual_markers = []
        
        try:
            casual_discourse_words = ['anyway', 'by the way', 'oh well', 'whatever', 'frankly']
            
            for token in doc:
                if (token.lemma_.lower() in casual_discourse_words or
                    (token.dep_ == 'discourse' and token.lemma_.lower() in casual_discourse_words)):
                    
                    casual_markers.append({
                        'text': token.text,
                        'type': 'casual_discourse_marker',
                        'morphological_features': self._get_morphological_features(token),
                        'professional_alternative': self._get_professional_discourse_alternative(token)
                    })
        
        except Exception:
            pass
        
        return casual_markers
    
    def _is_idiomatic_phrasal_verb(self, phrasal_verb: str) -> bool:
        """
        Check if a phrasal verb is idiomatic and inappropriate for professional tone.
        """
        idiomatic_phrasal_verbs = [
            'blow up', 'blow away', 'freak out', 'chill out', 'hang out',
            'mess around', 'goof off', 'show off', 'pig out', 'zone out'
        ]
        
        return phrasal_verb in idiomatic_phrasal_verbs
    
    def _suggest_professional_alternative(self, idiom: Dict[str, Any]) -> Optional[str]:
        """
        Suggest professional alternatives for idiomatic expressions.
        """
        professional_alternatives = {
            'piece of cake': 'straightforward',
            'break the ice': 'initiate conversation',
            'hit the nail on the head': 'precisely correct',
            'spill the beans': 'reveal information',
            'let the cat out of the bag': 'disclose',
            'bite the bullet': 'proceed despite difficulty',
            'cut to the chase': 'address the main point',
            'get the ball rolling': 'initiate the process',
            'think outside the box': 'consider alternative approaches',
            'touch base': 'follow up',
            'circle back': 'return to discuss',
            'low hanging fruit': 'easily achievable goals',
            'move the needle': 'create significant impact'
        }
        
        return professional_alternatives.get(idiom.get('text', '').lower())
    
    def _get_professional_discourse_alternative(self, token) -> Optional[str]:
        """
        Get professional alternatives for casual discourse markers.
        """
        professional_discourse = {
            'anyway': 'in summary',
            'by the way': 'additionally',
            'oh well': 'nevertheless',
            'whatever': 'regardless',
            'frankly': 'to be direct'
        }
        
        return professional_discourse.get(token.lemma_.lower())
