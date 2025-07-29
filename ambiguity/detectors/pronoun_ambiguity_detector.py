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
        
        self.ambiguous_pronouns = {
            'it', 'its', 'this', 'that', 'these', 'those', 
            'they', 'them', 'their', 'theirs', 'which', 'what'
        }
        self.clear_pronouns = {
            'you', 'your', 'yours', 'i', 'me', 'my', 'mine', 
            'we', 'us', 'our', 'ours'
        }
        self.max_referent_distance = 2
        self.min_confidence = 0.6
        self.min_referents_for_ambiguity = 2
        self.discourse_markers = {
            'also', 'additionally', 'furthermore', 'moreover',
            'then', 'next', 'subsequently', 'therefore', 'thus',
            'however', 'nevertheless', 'nonetheless', 'meanwhile'
        }
        self.strong_discourse_markers = {
            'also', 'additionally', 'furthermore', 'moreover', 
            'then', 'therefore', 'thus'
        }
    
    def detect(self, context: AmbiguityContext, nlp) -> List[AmbiguityDetection]:
        detections = []
        if not context.sentence.strip():
            return detections
        
        try:
            doc = nlp(context.sentence)
            for token in doc:
                if self._is_ambiguous_pronoun(token):
                    # LINGUISTIC ANCHOR 1: Check for clear coordinated antecedents first.
                    if self._has_clear_coordinated_antecedent(token):
                        continue

                    # LINGUISTIC ANCHOR 2: Check for clear demonstrative subjects.
                    if self._is_clear_demonstrative_subject(token, doc):
                        continue

                    ambiguity_info = self._analyze_pronoun_ambiguity(token, doc, context, nlp)
                    if ambiguity_info and ambiguity_info['confidence'] >= self.min_confidence:
                        detection = self._create_detection(token, ambiguity_info, context)
                        detections.append(detection)
        except Exception:
            pass
        return detections

    def _is_clear_demonstrative_subject(self, pronoun_token, doc) -> bool:
        """
        Checks if a sentence-initial pronoun is a clear demonstrative subject or determiner.
        This is a linguistic anchor to prevent false positives for sentences like:
        - "This document is..."
        - "This tests the rule."
        - "This preamble tests..." (determiner case)
        """
        if pronoun_token.i != 0 or pronoun_token.lemma_.lower() not in ['this', 'it']:
            return False

        # Case 1: Direct subject (nsubj/nsubjpass)
        if pronoun_token.dep_ in ('nsubj', 'nsubjpass'):
            verb = pronoun_token.head
            if verb.pos_ != 'VERB':
                return False

            if verb.lemma_ == 'be':
                for child in verb.children:
                    if child.dep_ in ('attr', 'acomp') and child.pos_ in ('NOUN', 'ADJ'):
                        return True

            meta_verbs = {'test', 'describe', 'show', 'explain', 'illustrate', 'is'}
            if verb.lemma_ in meta_verbs:
                return True

        # Case 2: Determiner at sentence start with clear noun pattern (e.g., "This preamble tests...")
        elif pronoun_token.dep_ == 'det':
            verb_head = pronoun_token.head
            if verb_head.pos_ == 'VERB':
                # Look for a concrete noun that's also attached to the same verb head
                # This handles "This [noun] [verb]..." patterns
                for sibling in verb_head.children:
                    if (sibling.pos_ in ('NOUN', 'PROPN') and 
                        sibling.dep_ in ('amod', 'nsubj', 'nsubjpass') and
                        self._is_concrete_noun(sibling)):
                        return True
                        
                # Also check if this is a meta verb that indicates document structure
                meta_verbs = {'test', 'describe', 'show', 'explain', 'illustrate', 'demonstrate'}
                if verb_head.lemma_ in meta_verbs:
                    return True

        return False

    def _is_concrete_noun(self, noun_token) -> bool:
        """
        Checks if a noun is concrete and unambiguous enough to be a clear referent.
        Excludes vague nouns like 'thing', 'stuff', etc.
        """
        noun_text = noun_token.lemma_.lower()
        
        # Common vague/abstract nouns that shouldn't be considered concrete
        vague_nouns = {
            'thing', 'stuff', 'item', 'one', 'way', 'part', 'use', 'work', 
            'place', 'time', 'case', 'point', 'fact', 'area', 'aspect'
        }
        
        if noun_text in vague_nouns:
            return False
            
        # Very short nouns are often pronouns or unclear
        if len(noun_text) < 3:
            return False
            
        return True

    def _has_clear_coordinated_antecedent(self, pronoun_token) -> bool:
        """
        Checks for a clear antecedent in a coordinated verb phrase (e.g., "...action1 noun1 and action2 it").
        """
        if pronoun_token.dep_ != 'dobj':
            return False
        verb2 = pronoun_token.head
        if verb2.pos_ != 'VERB' or verb2.dep_ != 'conj':
            return False
        verb1 = verb2.head
        if verb1.pos_ != 'VERB':
            return False
        for child in verb1.children:
            if child.dep_ == 'dobj':
                return True
        return False

    def _is_ambiguous_pronoun(self, token) -> bool:
        return (
            token.pos_ in ['PRON', 'DET'] and
            token.lemma_.lower() in self.ambiguous_pronouns and
            token.lemma_.lower() not in self.clear_pronouns
        )
    
    def _analyze_pronoun_ambiguity(self, pronoun_token, doc, context: AmbiguityContext, nlp) -> Optional[Dict[str, Any]]:
        current_referents = self._find_potential_referents(pronoun_token, doc)
        context_referents = self._find_context_referents(context, nlp)
        all_referents = current_referents + context_referents
        matching_referents = self._filter_matching_referents(pronoun_token, all_referents)
        prioritized_referents = self._prioritize_referents_by_grammar(pronoun_token, matching_referents)
        
        if self._has_clear_dominant_antecedent(pronoun_token, doc, context, nlp, prioritized_referents):
            return None
        if len(prioritized_referents) < self.min_referents_for_ambiguity:
            return None
        
        confidence = self._calculate_ambiguity_confidence(pronoun_token, prioritized_referents, context, doc)
        ambiguity_type = self._determine_ambiguity_type(pronoun_token, doc, prioritized_referents)
        
        return {
            'pronoun': pronoun_token.text,
            'referents': prioritized_referents,
            'confidence': confidence,
            'referent_count': len(prioritized_referents),
            'ambiguity_type': ambiguity_type
        }
    
    def _determine_ambiguity_type(self, pronoun_token, doc, referents: List[Dict[str, Any]]) -> AmbiguityType:
        if (pronoun_token.i == 0 and 
            pronoun_token.text.lower() in ['it', 'this', 'that'] and
            any(r.get('source') == 'context' for r in referents)):
            return AmbiguityType.UNCLEAR_ANTECEDENT
        return AmbiguityType.AMBIGUOUS_PRONOUN
    
    def _has_clear_dominant_antecedent(self, pronoun_token, doc, context: AmbiguityContext, nlp, referents: List[Dict[str, Any]]) -> bool:
        if len(referents) == 1:
            return True
        subjects = [r for r in referents if r.get('is_subject', False)]
        objects = [r for r in referents if r.get('is_object', False)]
        if len(subjects) == 1 and len(referents) <= 3:
            return True
        if len(referents) >= 3 and len(subjects) > 1:
            return False
        if len(referents) == 2:
            if len(subjects) == 1 and len(objects) == 1:
                return True
            if len(subjects) == 2 or len(objects) == 2:
                return self._has_strong_discourse_continuation(doc)
        if self._has_strong_discourse_continuation(doc):
            return True
        return False
    
    def _has_strong_discourse_continuation(self, doc) -> bool:
        for token in doc:
            if token.lemma_.lower() in self.strong_discourse_markers:
                return True
        return False

    def _find_potential_referents(self, pronoun_token, doc) -> List[Dict[str, Any]]:
        referents = []
        for token in doc:
            if token == pronoun_token or token.i >= pronoun_token.i:
                continue
            if token.pos_ in ['NOUN', 'PROPN'] and self._is_potential_referent(token, pronoun_token):
                referents.append({
                    'text': token.text, 'lemma': token.lemma_, 'pos': token.pos_,
                    'is_subject': token.dep_ in ['nsubj', 'nsubjpass'],
                    'is_object': token.dep_ in ['dobj', 'iobj', 'pobj'],
                    'distance': abs(token.i - pronoun_token.i), 'source': 'current_sentence'
                })
        return referents
    
    def _find_context_referents(self, context: AmbiguityContext, nlp) -> List[Dict[str, Any]]:
        referents = []
        if not context.preceding_sentences:
            return referents
        for i, sentence in enumerate(context.preceding_sentences):
            if i >= self.max_referent_distance: break
            try:
                doc = nlp(sentence)
                for token in doc:
                    if token.pos_ in ['NOUN', 'PROPN'] and self._is_potential_antecedent(token):
                        is_subject = self._is_subject_token(token, doc)
                        is_object = token.dep_ in ['dobj', 'iobj', 'pobj']
                        priority = 1 if is_subject else (2 if is_object else 3)
                        referents.append({
                            'text': token.text, 'lemma': token.lemma_, 'pos': token.pos_,
                            'is_subject': is_subject, 'is_object': is_object,
                            'distance': i + 1, 'source': 'context', 'priority': priority,
                            'source_sentence': sentence
                        })
            except Exception: continue
        return referents
    
    def _is_potential_referent(self, token, pronoun_token) -> bool:
        if len(token.text) < 2 or token.is_stop or abs(token.i - pronoun_token.i) < 2:
            return False
        return True
    
    def _is_potential_antecedent(self, token) -> bool:
        if token.pos_ not in ['NOUN', 'PROPN'] or len(token.text) < 2 or token.is_stop:
            return False
        if token.text.lower() in ['thing', 'stuff', 'item', 'one']:
            return False
        return True
    
    def _is_subject_token(self, token, doc) -> bool:
        if token.dep_ in ['nsubj', 'nsubjpass']: return True
        if token.dep_ == 'conj':
            head = token.head
            if head.dep_ in ['nsubj', 'nsubjpass']: return True
            current = token
            while current.head != current and current.dep_ == 'conj':
                current = current.head
                if current.dep_ in ['nsubj', 'nsubjpass']: return True
        return False
    
    def _filter_matching_referents(self, pronoun_token, referents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [r for r in referents if self._pronoun_referent_match(pronoun_token, r)]
    
    def _pronoun_referent_match(self, pronoun_token, referent: Dict[str, Any]) -> bool:
        return not self._is_unlikely_referent(referent)
    
    def _is_unlikely_referent(self, referent: Dict[str, Any]) -> bool:
        if len(referent['text']) < 3: return True
        if referent['lemma'].lower() in {'thing', 'way', 'time', 'part', 'use', 'work', 'place'}: return True
        return False
    
    def _prioritize_referents_by_grammar(self, pronoun_token, referents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not referents: return referents
        if pronoun_token.text.lower() == 'it' and pronoun_token.i == 0:
            subjects = [r for r in referents if r.get('is_subject', False)]
            objects = [r for r in referents if r.get('is_object', False)]
            other = [r for r in referents if not r.get('is_subject', False) and not r.get('is_object', False)]
            if subjects:
                if len(subjects) > 1: return subjects + objects
                else:
                    likely_objects = [o for o in objects if self._is_likely_antecedent_object(o)]
                    return subjects + likely_objects
            else: return objects + other
        return referents
    
    def _is_likely_antecedent_object(self, referent: Dict[str, Any]) -> bool:
        text = referent['text'].lower()
        likely_object_entities = [
            'system', 'platform', 'framework', 'service', 'tool', 'interface',
            'application', 'program', 'software', 'module', 'component', 'database',
            'server', 'network', 'device', 'machine', 'engine', 'processor'
        ]
        unlikely_object_entities = [
            'information', 'file', 'document', 'record', 'entry',
            'value', 'parameter', 'setting', 'option', 'field'
        ]
        for entity in likely_object_entities:
            if entity == text or entity in text: return True
        for entity in unlikely_object_entities:
            if re.search(r'\b' + re.escape(entity) + r'\b', text): return False
        if re.search(r'\bdata\b', text) and text not in ['database', 'metadata', 'dataset']: return False
        return True
    
    def _calculate_ambiguity_confidence(self, pronoun_token, referents: List[Dict[str, Any]], context: AmbiguityContext, doc) -> float:
        if len(referents) < self.min_referents_for_ambiguity: return 0.0
        referent_count = len(referents)
        if referent_count == 2: confidence = 0.6
        elif referent_count == 3: confidence = 0.8
        else: confidence = 0.9
        subjects = [r for r in referents if r.get('is_subject', False)]
        objects = [r for r in referents if r.get('is_object', False)]
        if len(subjects) > 1: confidence += 0.1
        if len(objects) > 1: confidence += 0.1
        if len(subjects) >= 1 and len(objects) >= 1: confidence += 0.05
        if pronoun_token.text.lower() in ['it', 'this', 'that']: confidence += 0.05
        if pronoun_token.i == 0: confidence += 0.05
        if self._has_strong_discourse_continuation(doc): confidence -= 0.2
        context_referents = [r for r in referents if r.get('source') == 'context']
        if len(context_referents) > 0: confidence -= 0.05
        return min(1.0, max(0.0, confidence))

    def _create_detection(self, pronoun_token, ambiguity_info: Dict[str, Any], context: AmbiguityContext) -> AmbiguityDetection:
        pronoun_text = pronoun_token.text
        referents = ambiguity_info['referents']
        referent_texts = [r['text'] for r in referents]
        ambiguity_type = ambiguity_info['ambiguity_type']
        span_start, span_end = pronoun_token.idx, pronoun_token.idx + len(pronoun_text)
        evidence = AmbiguityEvidence(
            tokens=[pronoun_text], linguistic_pattern=f"ambiguous_pronoun_{pronoun_token.lemma_}",
            confidence=ambiguity_info['confidence'],
            spacy_features={'pronoun_pos': pronoun_token.pos_, 'pronoun_lemma': pronoun_token.lemma_, 'referent_count': len(referents), 'referent_types': [r['pos'] for r in referents], 'sentence_start': pronoun_token.i == 0},
            context_clues={'referents': referent_texts, 'source_sentences': [r.get('source_sentence', '') for r in referents if r.get('source_sentence')]}
        )
        strategies = [ResolutionStrategy.CLARIFY_PRONOUN, ResolutionStrategy.RESTRUCTURE_SENTENCE]
        if ambiguity_type == AmbiguityType.UNCLEAR_ANTECEDENT: strategies.append(ResolutionStrategy.SPECIFY_REFERENCE)
        referent_list = ", ".join(f"'{text}'" for text in referent_texts)
        if ambiguity_type == AmbiguityType.UNCLEAR_ANTECEDENT:
            ai_instructions = [f"Replace the pronoun '{pronoun_text}' with a specific noun to clarify the reference.", f"The pronoun could refer to: {referent_list}", "Choose the most appropriate referent based on context and rewrite the sentence."]
        else:
            ai_instructions = [f"Clarify the pronoun '{pronoun_text}' by replacing it with a specific noun.", f"Potential referents include: {referent_list}", "Rewrite to eliminate ambiguity about what the pronoun refers to."]
        if ambiguity_info['confidence'] >= 0.8 or len(referents) >= 3: severity = AmbiguitySeverity.HIGH
        elif ambiguity_info['confidence'] >= 0.6 or len(referents) == 2: severity = AmbiguitySeverity.MEDIUM
        else: severity = AmbiguitySeverity.LOW
        return AmbiguityDetection(
            ambiguity_type=ambiguity_type, category=AmbiguityCategory.SEMANTIC, severity=severity,
            context=context, evidence=evidence, resolution_strategies=strategies,
            ai_instructions=ai_instructions, examples=self._generate_examples(pronoun_text, referent_texts),
            span=(span_start, span_end), flagged_text=pronoun_text
        ) 

    def _generate_examples(self, pronoun_text: str, referent_texts: List[str]) -> List[str]:
        examples = []
        if len(referent_texts) >= 2:
            if pronoun_text.lower() in ['it', 'this', 'that']:
                examples.append(f"Instead of '{pronoun_text} performs...', write 'The {referent_texts[0]} performs...' or 'The {referent_texts[1]} performs...'")
                examples.append(f"Replace '{pronoun_text} is' with 'The {referent_texts[0]} is' for clarity")
            elif pronoun_text.lower() in ['they', 'them', 'these', 'those']:
                examples.append(f"Instead of '{pronoun_text} are...', specify 'The {referent_texts[0]} and {referent_texts[1]} are...'")
        return examples
