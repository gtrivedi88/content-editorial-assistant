"""
Pronoun Ambiguity Detector

Detects pronouns with unclear referents that create ambiguity about 
what the pronoun refers to.

Example: "The server connects to the gateway. It is fast." - unclear if "It" refers to the server or gateway.
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
    Detects ambiguous pronoun references in technical writing.
    
    This detector identifies pronouns that could refer to multiple entities,
    creating ambiguity for the reader about the intended referent.
    """
    
    def __init__(self, config: AmbiguityConfig):
        super().__init__(config)
        
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
            # Log error but don't fail the analysis
            print(f"Error in pronoun ambiguity detection: {e}")
        
        return detections
    
    def _is_ambiguous_pronoun(self, token) -> bool:
        """Check if a token is a potentially ambiguous pronoun."""
        if not token:
            return False
        
        # Check if it's a pronoun
        if token.pos_ not in ['PRON', 'DET']:
            return False
        
        # Check if it's in our ambiguous pronouns list
        lemma = token.lemma_.lower()
        text = token.text.lower()
        
        return lemma in self.ambiguous_pronouns or text in self.ambiguous_pronouns
    
    def _analyze_pronoun_ambiguity(self, pronoun_token, doc, context: AmbiguityContext, nlp) -> Optional[Dict[str, Any]]:
        """Analyze a pronoun for potential ambiguity."""
        
        # Find potential referents in the current sentence
        current_referents = self._find_potential_referents(pronoun_token, doc)
        
        # Find potential referents in context (previous sentences)
        context_referents = self._find_context_referents(context, nlp)
        
        # Combine all potential referents
        all_referents = current_referents + context_referents
        
        # Filter referents that could match the pronoun
        matching_referents = self._filter_matching_referents(pronoun_token, all_referents)
        
        # Determine if there's ambiguity
        if len(matching_referents) <= 1:
            return None  # No ambiguity
        
        # Calculate ambiguity confidence
        confidence = self._calculate_ambiguity_confidence(
            pronoun_token, matching_referents, context
        )
        
        return {
            'pronoun': pronoun_token.text,
            'referents': matching_referents,
            'confidence': confidence,
            'referent_count': len(matching_referents)
        }
    
    def _find_potential_referents(self, pronoun_token, doc) -> List[Dict[str, Any]]:
        """Find potential referents in the current sentence."""
        referents = []
        
        for token in doc:
            # Skip the pronoun itself
            if token == pronoun_token:
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
                    if token.pos_ in ['NOUN', 'PROPN']:
                        referents.append({
                            'text': token.text,
                            'lemma': token.lemma_,
                            'pos': token.pos_,
                            'is_subject': token.dep_ in ['nsubj', 'nsubjpass'],
                            'is_object': token.dep_ in ['dobj', 'iobj', 'pobj'],
                            'distance': i + 1,  # sentences back
                            'source': 'context'
                        })
            except Exception:
                continue
        
        return referents
    
    def _filter_matching_referents(self, pronoun_token, referents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter referents that could match the pronoun based on agreement."""
        matching = []
        
        for referent in referents:
            if self._pronoun_referent_match(pronoun_token, referent):
                matching.append(referent)
        
        return matching
    
    def _pronoun_referent_match(self, pronoun_token, referent: Dict[str, Any]) -> bool:
        """Check if a pronoun could refer to a specific referent."""
        pronoun_text = pronoun_token.text.lower()
        pronoun_lemma = pronoun_token.lemma_.lower()
        
        # Basic matching rules
        if pronoun_lemma in ['it', 'this', 'that']:
            # These can refer to singular nouns or concepts
            return True
        
        if pronoun_lemma in ['they', 'them', 'these', 'those']:
            # These typically refer to plural nouns
            # For simplicity, we'll assume they could match any noun
            return True
        
        if pronoun_lemma in ['which', 'what']:
            # These can refer to any noun
            return True
        
        # Default: assume it could match
        return True
    
    def _is_potential_referent(self, token, pronoun_token) -> bool:
        """Check if a token is a potential referent for a pronoun."""
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
    
    def _calculate_ambiguity_confidence(self, pronoun_token, referents: List[Dict[str, Any]], 
                                      context: AmbiguityContext) -> float:
        """Calculate confidence that this pronoun is ambiguous."""
        if len(referents) <= 1:
            return 0.0
        
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on number of potential referents
        referent_count = len(referents)
        if referent_count == 2:
            confidence += 0.3
        elif referent_count > 2:
            confidence += 0.4
        
        # Increase confidence for certain ambiguous pronouns
        pronoun_text = pronoun_token.text.lower()
        if pronoun_text in ['it', 'this', 'that']:
            confidence += 0.2
        
        # Increase confidence if referents are close in distance
        distances = [r.get('distance', 0) for r in referents]
        if all(d <= 3 for d in distances):  # All referents are close
            confidence += 0.1
        
        # Decrease confidence if there's a clear dominant referent
        subjects = [r for r in referents if r.get('is_subject', False)]
        if len(subjects) == 1:
            confidence -= 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def _create_detection(self, pronoun_token, ambiguity_info: Dict[str, Any], 
                         context: AmbiguityContext) -> AmbiguityDetection:
        """Create an ambiguity detection for this pronoun."""
        
        pronoun_text = pronoun_token.text
        referents = ambiguity_info['referents']
        referent_texts = [r['text'] for r in referents]
        
        # Create evidence
        evidence = AmbiguityEvidence(
            tokens=[pronoun_text],
            linguistic_pattern=f"ambiguous_pronoun_{pronoun_token.lemma_}",
            confidence=ambiguity_info['confidence'],
            spacy_features={
                'pronoun_pos': pronoun_token.pos_,
                'pronoun_lemma': pronoun_token.lemma_,
                'referent_count': len(referents),
                'referent_types': [r['pos'] for r in referents]
            },
            context_clues={'referents': referent_texts}
        )
        
        # Create resolution strategies
        strategies = [
            ResolutionStrategy.CLARIFY_PRONOUN,
            ResolutionStrategy.RESTRUCTURE_SENTENCE
        ]
        
        # Create AI instructions
        referent_list = ", ".join(referent_texts)
        ai_instructions = [
            f"Replace the ambiguous pronoun '{pronoun_text}' with the specific noun it refers to",
            f"Possible referents: {referent_list}",
            "Choose the most logical referent based on context"
        ]
        
        return AmbiguityDetection(
            ambiguity_type=AmbiguityType.AMBIGUOUS_PRONOUN,
            category=AmbiguityCategory.REFERENTIAL,
            severity=AmbiguitySeverity.MEDIUM,
            context=context,
            evidence=evidence,
            resolution_strategies=strategies,
            ai_instructions=ai_instructions
        ) 