"""
Pronoun Ambiguity Detector

Detects pronouns with unclear referents that create ambiguity about 
what the pronoun refers to. This consolidated detector handles both:
1. Sentence-initial pronouns with unclear antecedents (e.g., "It is fast")
2. Mid-sentence pronouns with ambiguous references (e.g., "The server and gateway. It is fast")

Examples: 
- "The server connects to the gateway. It is fast." - unclear if "It" refers to server or gateway
- "The application sends a confirmation to the database. It is critical." - unclear antecedent
"""

from typing import List, Dict, Any, Optional, Set
import re

from ..base_ambiguity_rule import AmbiguityDetector
from ..types import (
    AmbiguityType, AmbiguityCategory, AmbiguitySeverity,
    AmbiguityContext, AmbiguityEvidence, AmbiguityDetection,
    ResolutionStrategy, AmbiguityConfig
)


class PronounAmbiguityDetector(AmbiguityDetector):
    """
    Consolidated detector for ambiguous pronoun references in technical writing.
    
    This detector identifies pronouns that could refer to multiple entities,
    creating ambiguity for the reader about the intended referent. It handles
    both sentence-initial unclear antecedents and general pronoun ambiguity.
    """
    
    def __init__(self, config: AmbiguityConfig, parent_rule=None):
        super().__init__(config, parent_rule)
        
        # Pronouns that commonly create ambiguity
        self.ambiguous_pronouns = {
            'it', 'its', 'this', 'that', 'these', 'those', 
            'they', 'them', 'their', 'theirs', 'which', 'what'
        }
        
        # Pronouns that are typically clear (less ambiguous)
        self.clear_pronouns = {
            'you', 'your', 'yours', 'i', 'me', 'my', 'mine', 
            'we', 'us', 'our', 'ours'
        }
        
        # Distance threshold for considering potential referents
        self.max_referent_distance = 2  # sentences
        
        # Minimum confidence threshold for flagging ambiguity
        self.min_confidence = 0.6
        
        # Minimum number of potential referents to flag as ambiguous
        self.min_referents_for_ambiguity = 2
        
        # Discourse continuation markers that often indicate clear reference
        self.discourse_markers = {
            'also', 'additionally', 'furthermore', 'moreover',
            'then', 'next', 'subsequently', 'therefore', 'thus',
            'however', 'nevertheless', 'nonetheless', 'meanwhile'
        }
        
        # Strong discourse markers (subset of above)
        self.strong_discourse_markers = {
            'also', 'additionally', 'furthermore', 'moreover', 
            'then', 'therefore', 'thus'
        }
    
    def detect(self, context: AmbiguityContext, nlp) -> List[AmbiguityDetection]:
        """
        Detect ambiguous pronoun references in the given context.
        
        Args:
            context: Sentence context for analysis
            nlp: SpaCy nlp object
            
        Returns:
            List of ambiguity detections
        """
        detections = []
        
        if not context.sentence.strip():
            return detections
        
        try:
            # Parse sentence with SpaCy
            doc = nlp(context.sentence)
            
            # Find pronouns in the sentence
            for token in doc:
                if self._is_ambiguous_pronoun(token):
                    # Check if this pronoun has clear referents
                    ambiguity_info = self._analyze_pronoun_ambiguity(token, doc, context, nlp)
                    
                    if ambiguity_info and ambiguity_info['confidence'] >= self.min_confidence:
                        detection = self._create_detection(token, ambiguity_info, context)
                        detections.append(detection)
        
        except Exception as e:
            # Log error but don't crash
            pass
        
        return detections
    
    def _is_ambiguous_pronoun(self, token) -> bool:
        """Check if a token is an ambiguous pronoun."""
        return (
            token.pos_ in ['PRON', 'DET'] and
            token.lemma_.lower() in self.ambiguous_pronouns and
            token.lemma_.lower() not in self.clear_pronouns
        )
    
    def _analyze_pronoun_ambiguity(self, pronoun_token, doc, context: AmbiguityContext, nlp) -> Optional[Dict[str, Any]]:
        """Analyze a pronoun for potential ambiguity."""
        
        # Find potential referents in the current sentence (before the pronoun)
        current_referents = self._find_potential_referents(pronoun_token, doc)
        
        # Find potential referents in context (previous sentences)
        context_referents = self._find_context_referents(context, nlp)
        
        # Combine all potential referents
        all_referents = current_referents + context_referents
        
        # Filter referents that could match the pronoun
        matching_referents = self._filter_matching_referents(pronoun_token, all_referents)
        
        # Apply grammatical prioritization
        prioritized_referents = self._prioritize_referents_by_grammar(pronoun_token, matching_referents)
        
        # Check for clear dominant antecedent before flagging as ambiguous
        if self._has_clear_dominant_antecedent(pronoun_token, doc, context, nlp, prioritized_referents):
            return None  # Clear reference, not ambiguous
        
        # Check if there are enough referents to create ambiguity
        if len(prioritized_referents) < self.min_referents_for_ambiguity:
            return None  # Not enough referents for ambiguity
        
        # Calculate ambiguity confidence
        confidence = self._calculate_ambiguity_confidence(
            pronoun_token, prioritized_referents, context, doc
        )
        
        # Determine ambiguity type based on position and context
        ambiguity_type = self._determine_ambiguity_type(pronoun_token, doc, prioritized_referents)
        
        return {
            'pronoun': pronoun_token.text,
            'referents': prioritized_referents,
            'confidence': confidence,
            'referent_count': len(prioritized_referents),
            'ambiguity_type': ambiguity_type
        }
    
    def _determine_ambiguity_type(self, pronoun_token, doc, referents: List[Dict[str, Any]]) -> AmbiguityType:
        """Determine whether this is an unclear antecedent or general pronoun ambiguity."""
        
        # If it's sentence-initial "It/This/That" with context referents, it's unclear antecedent
        if (pronoun_token.i == 0 and 
            pronoun_token.text.lower() in ['it', 'this', 'that'] and
            any(r.get('source') == 'context' for r in referents)):
            return AmbiguityType.UNCLEAR_ANTECEDENT
        
        # Otherwise, it's general pronoun ambiguity
        return AmbiguityType.AMBIGUOUS_PRONOUN
    
    def _has_clear_dominant_antecedent(self, pronoun_token, doc, context: AmbiguityContext, nlp, referents: List[Dict[str, Any]]) -> bool:
        """Check if there's a clear dominant antecedent that makes the pronoun unambiguous."""
        
        # Analyze grammatical roles first
        subjects = [r for r in referents if r.get('is_subject', False)]
        objects = [r for r in referents if r.get('is_object', False)]
        
        # If there's exactly one subject and strong discourse continuation, it's likely clear
        if len(subjects) == 1 and self._has_strong_discourse_continuation(doc):
            return True
        
        # If we have 3+ referents with multiple subjects, it's likely ambiguous
        if len(referents) >= 3 and len(subjects) > 1:
            return False
        
        # For 2 referents, be more selective about what counts as "clear"
        if len(referents) == 2:
            # If we have exactly 1 subject and 1 object, check discourse signals
            if len(subjects) == 1 and len(objects) == 1:
                # Only consider it clear if there's a strong discourse signal
                return self._has_strong_discourse_continuation(doc)
            
            # If both are subjects or both are objects, it's ambiguous
            if len(subjects) == 2 or len(objects) == 2:
                return False
        
        # Check for strong discourse continuation markers
        if self._has_strong_discourse_continuation(doc):
            return True
        
        return False
    
    def _has_strong_discourse_continuation(self, doc) -> bool:
        """Check if the sentence has strong discourse continuation markers."""
        for token in doc:
            if token.lemma_.lower() in self.strong_discourse_markers:
                return True
        return False
    
    def _has_discourse_continuation(self, doc) -> bool:
        """Check if the sentence has any discourse continuation markers."""
        for token in doc:
            if token.lemma_.lower() in self.discourse_markers:
                return True
        return False

    def _find_potential_referents(self, pronoun_token, doc) -> List[Dict[str, Any]]:
        """Find potential referents in the current sentence (before the pronoun)."""
        referents = []
        
        for token in doc:
            # Skip the pronoun itself
            if token == pronoun_token:
                continue
            
            # Only consider tokens that come BEFORE the pronoun (antecedents)
            if token.i >= pronoun_token.i:
                continue
            
            # Look for nouns that could be referents
            if token.pos_ in ['NOUN', 'PROPN']:
                # Check if it's a potential referent based on grammatical features
                if self._is_potential_referent(token, pronoun_token):
                    referents.append({
                        'text': token.text,
                        'lemma': token.lemma_,
                        'pos': token.pos_,
                        'is_subject': token.dep_ in ['nsubj', 'nsubjpass'],
                        'is_object': token.dep_ in ['dobj', 'iobj', 'pobj'],
                        'distance': abs(token.i - pronoun_token.i),
                        'source': 'current_sentence'
                    })
        
        return referents
    
    def _find_context_referents(self, context: AmbiguityContext, nlp) -> List[Dict[str, Any]]:
        """Find potential referents in the context (previous sentences)."""
        referents = []
        
        if not context.preceding_sentences:
            return referents
        
        # Check preceding sentences for potential referents
        for i, sentence in enumerate(context.preceding_sentences):
            if i >= self.max_referent_distance:
                break  # Too far back
            
            try:
                doc = nlp(sentence)
                for token in doc:
                    if token.pos_ in ['NOUN', 'PROPN'] and self._is_potential_antecedent(token):
                        # Check if it's a subject (including compound subjects)
                        is_subject = self._is_subject_token(token, doc)
                        is_object = token.dep_ in ['dobj', 'iobj', 'pobj']
                        
                        # Priority: subjects > objects > other
                        priority = 1 if is_subject else (2 if is_object else 3)
                        
                        referents.append({
                            'text': token.text,
                            'lemma': token.lemma_,
                            'pos': token.pos_,
                            'is_subject': is_subject,
                            'is_object': is_object,
                            'distance': i + 1,  # sentences back
                            'source': 'context',
                            'priority': priority,
                            'source_sentence': sentence
                        })
            except Exception:
                continue
        
        return referents
    
    def _is_potential_referent(self, token, pronoun_token) -> bool:
        """Check if a token in current sentence is a potential referent for a pronoun."""
        # Skip very short words that are unlikely to be referents
        if len(token.text) < 2:
            return False
        
        # Skip stop words that are unlikely to be referents
        if token.is_stop:
            return False
        
        # Skip tokens that are too close to the pronoun (likely not referents)
        if abs(token.i - pronoun_token.i) < 2:
            return False
        
        return True
    
    def _is_potential_antecedent(self, token) -> bool:
        """Check if a token in context is a potential antecedent."""
        # Must be a noun or proper noun
        if token.pos_ not in ['NOUN', 'PROPN']:
            return False
        
        # Skip very short words that are unlikely to be antecedents
        if len(token.text) < 2:
            return False
        
        # Skip stop words that are unlikely to be antecedents
        if token.is_stop:
            return False
        
        # Skip common function words
        if token.text.lower() in ['thing', 'stuff', 'item', 'one']:
            return False
        
        return True
    
    def _is_subject_token(self, token, doc) -> bool:
        """Check if a token is a subject, including compound/coordinated subjects."""
        # Direct subject
        if token.dep_ in ['nsubj', 'nsubjpass']:
            return True
        
        # Coordinated/compound subject (e.g., "manager and developer")
        if token.dep_ == 'conj':
            # Check if it's conjoined to a subject
            head = token.head
            if head.dep_ in ['nsubj', 'nsubjpass']:
                return True
            
            # Or if it's in a coordination chain where the root is a subject
            current = token
            while current.head != current and current.dep_ == 'conj':
                current = current.head
                if current.dep_ in ['nsubj', 'nsubjpass']:
                    return True
        
        return False
    
    def _filter_matching_referents(self, pronoun_token, referents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter referents that could match the pronoun based on agreement."""
        matching = []
        
        for referent in referents:
            if self._pronoun_referent_match(pronoun_token, referent):
                matching.append(referent)
        
        return matching
    
    def _pronoun_referent_match(self, pronoun_token, referent: Dict[str, Any]) -> bool:
        """Check if a pronoun could refer to a specific referent."""
        pronoun_lemma = pronoun_token.lemma_.lower()
        
        # Enhanced matching rules - be more selective
        if pronoun_lemma in ['it', 'this', 'that']:
            # These can refer to singular nouns or concepts
            return not self._is_unlikely_referent(referent)
        
        if pronoun_lemma in ['they', 'them', 'these', 'those']:
            # These typically refer to plural nouns
            return not self._is_unlikely_referent(referent)
        
        if pronoun_lemma in ['which', 'what']:
            # These can refer to any noun
            return not self._is_unlikely_referent(referent)
        
        # Default: be conservative
        return not self._is_unlikely_referent(referent)
    
    def _is_unlikely_referent(self, referent: Dict[str, Any]) -> bool:
        """Check if a referent is unlikely to be what the pronoun refers to."""
        
        # Skip very short words
        if len(referent['text']) < 3:
            return True
        
        # Skip common words that are unlikely to be referents
        unlikely_words = {'thing', 'way', 'time', 'part', 'use', 'work', 'place'}
        if referent['lemma'].lower() in unlikely_words:
            return True
        
        return False
    
    def _prioritize_referents_by_grammar(self, pronoun_token, referents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize referents based on grammatical roles and likelihood."""
        if not referents:
            return referents
        
        pronoun_text = pronoun_token.text.lower()
        
        # For sentence-initial "It", strongly prefer subjects over objects
        if pronoun_text == 'it' and pronoun_token.i == 0:
            subjects = [r for r in referents if r.get('is_subject', False)]
            objects = [r for r in referents if r.get('is_object', False)]
            other = [r for r in referents if not r.get('is_subject', False) and not r.get('is_object', False)]
            
            # If we have subjects, significantly prefer them
            if subjects:
                # Only include objects if there are multiple competitive subjects
                if len(subjects) > 1:
                    return subjects + objects  # Include objects to show genuine ambiguity
                else:
                    # Single subject: only include objects if they're likely antecedents
                    likely_objects = [o for o in objects if self._is_likely_antecedent_object(o)]
                    return subjects + likely_objects
            else:
                # No subjects, return objects and other
                return objects + other
        
        # For other pronouns, return all matching
        return referents
    
    def _is_likely_antecedent_object(self, referent: Dict[str, Any]) -> bool:
        """Check if an object is likely to be a pronoun antecedent."""
        text = referent['text'].lower()
        
        # Technical systems/entities that could be subjects of discourse
        likely_object_entities = [
            'system', 'platform', 'framework', 'service', 'tool', 'interface',
            'application', 'program', 'software', 'module', 'component'
        ]
        
        # Less likely: concrete items, data, files
        unlikely_object_entities = [
            'data', 'information', 'file', 'document', 'record', 'entry',
            'value', 'parameter', 'setting', 'option', 'field'
        ]
        
        if any(entity in text for entity in likely_object_entities):
            return True
        if any(entity in text for entity in unlikely_object_entities):
            return False
        
        return True  # Default to including if unsure
    
    def _calculate_ambiguity_confidence(self, pronoun_token, referents: List[Dict[str, Any]], 
                                      context: AmbiguityContext, doc) -> float:
        """Calculate confidence that this pronoun is ambiguous."""
        if len(referents) < self.min_referents_for_ambiguity:
            return 0.0
        
        # Base confidence increases with number of referents
        referent_count = len(referents)
        if referent_count == 2:
            confidence = 0.6  # Medium confidence for 2 referents
        elif referent_count == 3:
            confidence = 0.8  # High confidence for 3 referents
        else:  # 4+ referents
            confidence = 0.9  # Very high confidence for many referents
        
        # Analyze grammatical roles for linguistic grounding
        subjects = [r for r in referents if r.get('is_subject', False)]
        objects = [r for r in referents if r.get('is_object', False)]
        
        # Multiple subjects or objects = higher ambiguity
        if len(subjects) > 1:
            confidence += 0.1
        if len(objects) > 1:
            confidence += 0.1
        
        # Mix of subjects and objects = moderate ambiguity
        if len(subjects) >= 1 and len(objects) >= 1:
            confidence += 0.05
        
        # Check pronoun type - some are more ambiguous than others
        pronoun_text = pronoun_token.text.lower()
        if pronoun_text in ['it', 'this', 'that']:
            confidence += 0.05  # These are commonly ambiguous
        
        # Additional boost for sentence-initial pronouns
        if pronoun_token.i == 0:
            confidence += 0.05
        
        # Reduce confidence for strong discourse signals
        if self._has_strong_discourse_continuation(doc):
            confidence -= 0.2  # Moderate reduction for strong signals
        
        # Slight reduction if referents are from different sentences (less immediate)
        context_referents = [r for r in referents if r.get('source') == 'context']
        if len(context_referents) > 0:
            confidence -= 0.05
        
        return min(1.0, max(0.0, confidence))

    def _create_detection(self, pronoun_token, ambiguity_info: Dict[str, Any], 
                         context: AmbiguityContext) -> AmbiguityDetection:
        """Create an ambiguity detection for this pronoun."""
        
        pronoun_text = pronoun_token.text
        referents = ambiguity_info['referents']
        referent_texts = [r['text'] for r in referents]
        ambiguity_type = ambiguity_info['ambiguity_type']
        
        # Create evidence
        evidence = AmbiguityEvidence(
            tokens=[pronoun_text],
            linguistic_pattern=f"ambiguous_pronoun_{pronoun_token.lemma_}",
            confidence=ambiguity_info['confidence'],
            spacy_features={
                'pronoun_pos': pronoun_token.pos_,
                'pronoun_lemma': pronoun_token.lemma_,
                'referent_count': len(referents),
                'referent_types': [r['pos'] for r in referents],
                'sentence_start': pronoun_token.i == 0
            },
            context_clues={
                'referents': referent_texts,
                'source_sentences': [r.get('source_sentence', '') for r in referents if r.get('source_sentence')]
            }
        )
        
        # Create resolution strategies
        strategies = [
            ResolutionStrategy.CLARIFY_PRONOUN,
            ResolutionStrategy.RESTRUCTURE_SENTENCE
        ]
        
        if ambiguity_type == AmbiguityType.UNCLEAR_ANTECEDENT:
            strategies.append(ResolutionStrategy.SPECIFY_REFERENCE)
        
        # Create AI instructions based on ambiguity type
        referent_list = ", ".join(f"'{text}'" for text in referent_texts)
        
        if ambiguity_type == AmbiguityType.UNCLEAR_ANTECEDENT:
            ai_instructions = [
                f"The pronoun '{pronoun_text}' has an unclear antecedent. Multiple nouns in the previous sentence could be the referent: {referent_list}",
                f"Replace '{pronoun_text}' with the specific noun it refers to",
                "Choose the most logical antecedent based on the context and meaning",
                f"For example: Instead of '{pronoun_text} is...', write 'The [specific noun] is...'"
            ]
        else:
            ai_instructions = [
                f"Replace the ambiguous pronoun '{pronoun_text}' with the specific noun it refers to",
                f"Possible referents: {referent_list}",
                "Choose the most logical referent based on context"
            ]
        
        # Add examples
        examples = []
        if len(referent_texts) >= 2:
            examples.append(f"Instead of '{pronoun_text} performs...', write 'The {referent_texts[0]} performs...' or 'The {referent_texts[1]} performs...'")
        
        return AmbiguityDetection(
            ambiguity_type=ambiguity_type,
            category=AmbiguityCategory.REFERENTIAL,
            severity=AmbiguitySeverity.MEDIUM,
            context=context,
            evidence=evidence,
            resolution_strategies=strategies,
            ai_instructions=ai_instructions,
            examples=examples
        ) 