"""
Pronoun Ambiguity Detector

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
    Consolidated detector for ambiguous pronoun references using evidence-based analysis.
    
    This detector is fully compatible with Level 2 Enhanced Validation, Evidence-Based 
    Rule Development, and Universal Confidence Threshold architecture. It provides
    sophisticated 7-factor evidence scoring for pronoun ambiguity assessment.
    
    Architecture compliance:
    - confidence.md: Universal threshold (≥0.35), normalized confidence
    - evidence_based_rule_development.md: Multi-factor evidence assessment  
    - level_2_implementation.adoc: Enhanced validation integration
    """
    
    def __init__(self, config: AmbiguityConfig, parent_rule=None):
        super().__init__(config, parent_rule)
        
        # Pronouns that can create ambiguity
        self.ambiguous_pronouns = {
            'it', 'its', 'this', 'that', 'these', 'those', 
            'they', 'them', 'their', 'theirs', 'which', 'what'
        }
        
        # Pronouns with clear referents (first/second person)
        self.clear_pronouns = {
            'you', 'your', 'yours', 'i', 'me', 'my', 'mine', 
            'we', 'us', 'our', 'ours'
        }
        
        # Configuration for evidence-based analysis
        self.max_referent_distance = 2  # Sentences to look back
        self.confidence_threshold = 0.70  # Universal threshold compliance (≥0.35)
        self.min_referents_for_ambiguity = 2  # Minimum competing referents
        
        # Discourse markers that affect ambiguity
        self.discourse_markers = {
            'also', 'additionally', 'furthermore', 'moreover',
            'then', 'next', 'subsequently', 'therefore', 'thus',
            'however', 'nevertheless', 'nonetheless', 'meanwhile'
        }
        
        self.strong_discourse_markers = {
            'also', 'additionally', 'furthermore', 'moreover', 
            'then', 'therefore', 'thus'
        }
        
        # Clear antecedent patterns that reduce ambiguity
        self.clear_referent_patterns = {
            'meta_verbs': {'test', 'describe', 'show', 'explain', 'illustrate', 'demonstrate'},
            'temporal_nouns': {'update', 'release', 'version', 'change', 'fix', 'patch'},
            'temporal_preps': {'before', 'after', 'with', 'in', 'during', 'following'}
        }
    
    def detect(self, context: AmbiguityContext, nlp) -> List[AmbiguityDetection]:
        """
        Detect pronoun ambiguities using evidence-based analysis.
        
        Args:
            context: Sentence context for analysis
            nlp: SpaCy nlp object
            
        Returns:
            List of ambiguity detections for pronoun ambiguities
        """
        detections = []
        if not context.sentence.strip():
            return detections
        
        # Apply zero false positive guards first
        if self._apply_zero_false_positive_guards(context):
            return detections
        
        try:
            doc = nlp(context.sentence)
            for token in doc:
                if self._is_ambiguous_pronoun(token):
                    # Apply linguistic anchors to prevent false positives
                    if self._has_clear_coordinated_antecedent(token):
                        continue
                    if self._is_clear_demonstrative_subject(token, doc):
                        continue
                    if self._is_clear_temporal_reference(token, doc):
                        continue

                    # Calculate evidence for ambiguity
                    evidence_score = self._calculate_pronoun_evidence(token, doc, context, nlp)
                    if evidence_score >= self.confidence_threshold:
                        detection = self._create_pronoun_detection(token, evidence_score, context, nlp)
                        detections.append(detection)
                        
        except Exception as e:
            print(f"Error in pronoun ambiguity detection: {e}")
        
        return detections
    
    def _apply_zero_false_positive_guards(self, context: AmbiguityContext) -> bool:
        """
        Apply surgical zero false positive guards for pronoun ambiguity detection.
        
        Returns True if the detection should be skipped (no pronoun ambiguity risk).
        """
        document_context = context.document_context or {}
        block_type = document_context.get('block_type', '').lower()
        
        # Guard 1: Code blocks and technical identifiers
        if block_type in ['code_block', 'literal_block', 'inline_code']:
            return True
        
        # Guard 2: Very short sentences (< 4 words) rarely have ambiguous pronouns
        if len(context.sentence.split()) < 4:
            return True
        
        # Guard 3: Questions often have clear pronoun usage
        if context.sentence.strip().endswith('?'):
            return True
        
        return False
    
    def _calculate_pronoun_evidence(self, pronoun_token, doc, context: AmbiguityContext, nlp) -> float:
        """
        Enhanced Level 2 evidence calculation for pronoun ambiguity detection.
        
        Implements evidence-based rule development with:
        - Multi-factor evidence assessment
        - Context-aware domain validation 
        - Universal threshold compliance (≥0.35)
        - Specific criteria for ambiguous vs clear pronouns
        """
        # Get referent analysis for evidence calculation
        ambiguity_info = self._analyze_pronoun_ambiguity(pronoun_token, doc, context, nlp)
        if not ambiguity_info:
            return 0.0
        
        referents = ambiguity_info['referents']
        referent_count = len(referents)
        
        # Evidence-based base confidence (Level 2 enhancement)
        if referent_count < 2:
            return 0.0  # No ambiguity with fewer than 2 referents
        
        evidence_score = 0.45  # Starting point for potential ambiguity
        
        # EVIDENCE FACTOR 1: Referent Count Assessment (High Impact)
        if referent_count == 2:
            evidence_score += 0.15  # Medium evidence - two competing referents
        elif referent_count == 3:
            evidence_score += 0.25  # High evidence - multiple competing referents
        elif referent_count >= 4:
            evidence_score += 0.30  # Very high evidence - many competing referents
        
        # EVIDENCE FACTOR 2: Grammatical Role Analysis (Critical for Clarity)
        subjects = [r for r in referents if r.get('is_subject', False)]
        objects = [r for r in referents if r.get('is_object', False)]
        
        if len(subjects) > 1:
            evidence_score += 0.15  # Multiple subjects increase ambiguity
        if len(objects) > 1:
            evidence_score += 0.10  # Multiple objects add ambiguity
        if len(subjects) >= 1 and len(objects) >= 1:
            evidence_score += 0.08  # Mixed grammatical roles increase complexity
        
        # EVIDENCE FACTOR 3: Pronoun Type and Position Analysis (Linguistic Patterns)
        linguistic_modifier = 0.0
        if pronoun_token.text.lower() in ['it', 'this', 'that']:
            linguistic_modifier += 0.08  # Singular pronouns more ambiguous
        if pronoun_token.i == 0:  # Sentence-initial position
            linguistic_modifier += 0.10  # Sentence-initial pronouns often unclear
        if pronoun_token.pos_ == 'PRON':
            linguistic_modifier += 0.05  # True pronouns vs determiners
        
        # EVIDENCE FACTOR 4: Discourse Context Analysis (Contextual Clues)
        discourse_modifier = 0.0
        if self._has_strong_discourse_continuation(doc):
            discourse_modifier -= 0.15  # Strong discourse markers reduce ambiguity
        elif self._has_weak_discourse_markers(doc):
            discourse_modifier -= 0.05  # Weak discourse markers help slightly
        
        # EVIDENCE FACTOR 5: Referent Distance and Source Analysis (Proximity Assessment)
        distance_modifier = 0.0
        context_referents = [r for r in referents if r.get('source') == 'context']
        current_referents = [r for r in referents if r.get('source') == 'current_sentence']
        
        if len(context_referents) > 0:
            distance_modifier += 0.05  # Cross-sentence references add ambiguity
        if len(current_referents) > 1:
            distance_modifier += 0.10  # Multiple same-sentence referents
        
        # EVIDENCE FACTOR 6: Semantic Coherence Analysis (Domain Knowledge)
        semantic_modifier = 0.0
        if self._has_competing_entity_types(referents):
            semantic_modifier += 0.12  # Different entity types increase ambiguity
        elif self._has_similar_entity_types(referents):
            semantic_modifier += 0.08  # Similar entities still ambiguous but less so
        
        # EVIDENCE FACTOR 7: Technical Context Validation (Context Awareness)
        technical_modifier = 0.0
        if context and hasattr(context, 'document_context'):
            doc_context = context.document_context or {}
            content_type = doc_context.get('content_type', '')
            
            if content_type == 'technical':
                technical_modifier += 0.08  # Technical docs need precise references
            elif content_type == 'procedural':
                technical_modifier += 0.12  # Procedures must be unambiguous
            elif content_type == 'narrative':
                technical_modifier -= 0.05  # Narrative allows some ambiguity
        
        # EVIDENCE AGGREGATION (Level 2 Multi-Factor Assessment)
        final_evidence = (evidence_score + 
                         linguistic_modifier + 
                         discourse_modifier + 
                         distance_modifier + 
                         semantic_modifier + 
                         technical_modifier)
        
        # UNIVERSAL THRESHOLD COMPLIANCE (≥0.35 minimum)
        # Cap at 0.95 to leave room for uncertainty
        return min(0.95, max(0.35, final_evidence))
    
    # Evidence factor helper methods
    def _has_weak_discourse_markers(self, doc) -> bool:
        """Check for weak discourse markers that provide some coherence."""
        weak_markers = {'however', 'nevertheless', 'nonetheless', 'meanwhile', 'next'}
        for token in doc:
            if token.lemma_.lower() in weak_markers:
                return True
        return False
    
    def _has_competing_entity_types(self, referents: List[Dict[str, Any]]) -> bool:
        """Check if referents represent different types of entities."""
        entity_types = set()
        for referent in referents:
            lemma = referent['lemma'].lower()
            if lemma in ['system', 'service', 'application', 'software']:
                entity_types.add('software_entity')
            elif lemma in ['server', 'database', 'network', 'device']:
                entity_types.add('hardware_entity')
            elif lemma in ['user', 'administrator', 'client', 'person']:
                entity_types.add('person_entity')
            elif lemma in ['file', 'document', 'data', 'information']:
                entity_types.add('data_entity')
            else:
                entity_types.add('other_entity')
        
        return len(entity_types) > 1
    
    def _has_similar_entity_types(self, referents: List[Dict[str, Any]]) -> bool:
        """Check if referents represent similar types of entities."""
        if len(referents) < 2:
            return False
        
        # Group similar entities
        software_entities = ['system', 'service', 'application', 'software', 'program', 'tool']
        hardware_entities = ['server', 'database', 'network', 'device', 'machine', 'computer']
        
        software_count = sum(1 for r in referents if r['lemma'].lower() in software_entities)
        hardware_count = sum(1 for r in referents if r['lemma'].lower() in hardware_entities)
        
        # If most referents are of the same type, they're similar
        return software_count >= 2 or hardware_count >= 2
    
    # Legacy methods enhanced with evidence-based approach
    def _analyze_pronoun_ambiguity(self, pronoun_token, doc, context: AmbiguityContext, nlp) -> Optional[Dict[str, Any]]:
        """Analyze pronoun for potential ambiguity - enhanced for evidence-based approach."""
        current_referents = self._find_potential_referents(pronoun_token, doc)
        context_referents = self._find_context_referents(context, nlp)
        all_referents = current_referents + context_referents
        matching_referents = self._filter_matching_referents(pronoun_token, all_referents)
        prioritized_referents = self._prioritize_referents_by_grammar(pronoun_token, matching_referents)
        
        if self._has_clear_dominant_antecedent(pronoun_token, doc, context, nlp, prioritized_referents):
            return None
        if len(prioritized_referents) < self.min_referents_for_ambiguity:
            return None
        
        # Use legacy confidence calculation as fallback
        legacy_confidence = self._calculate_ambiguity_confidence(pronoun_token, prioritized_referents, context, doc)
        ambiguity_type = self._determine_ambiguity_type(pronoun_token, doc, prioritized_referents)
        
        return {
            'pronoun': pronoun_token.text,
            'referents': prioritized_referents,
            'confidence': legacy_confidence,
            'referent_count': len(prioritized_referents),
            'ambiguity_type': ambiguity_type
        }
    
    def _is_ambiguous_pronoun(self, token) -> bool:
        """Check if token is potentially ambiguous pronoun."""
        return (
            token.pos_ in ['PRON', 'DET'] and
            token.lemma_.lower() in self.ambiguous_pronouns and
            token.lemma_.lower() not in self.clear_pronouns
        )
    
    def _is_clear_demonstrative_subject(self, pronoun_token, doc) -> bool:
        """
        Enhanced check for clear demonstrative subjects using evidence-based patterns.
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

            if verb.lemma_ in self.clear_referent_patterns['meta_verbs']:
                return True

        # Case 2: Determiner at sentence start with clear noun pattern
        elif pronoun_token.dep_ == 'det':
            noun = pronoun_token.head
            
            if (noun.pos_ in ('NOUN', 'PROPN') and 
                noun.dep_ in ('nsubj', 'nsubjpass') and
                self._is_concrete_noun(noun)):
                
                verb = noun.head
                if verb.pos_ == 'VERB':
                    return True

        return False
    
    def _is_concrete_noun(self, noun_token) -> bool:
        """Enhanced concrete noun detection for evidence-based analysis."""
        noun_text = noun_token.lemma_.lower()
        
        # Vague/abstract nouns that shouldn't be considered concrete
        vague_nouns = {
            'thing', 'stuff', 'item', 'one', 'way', 'part', 'use', 'work', 
            'place', 'time', 'case', 'point', 'fact', 'area', 'aspect',
            'condition', 'situation', 'problem', 'issue', 'matter', 'state',
            'status', 'result', 'outcome', 'effect', 'consequence'
        }
        
        if noun_text in vague_nouns:
            return False
            
        # Very short nouns are often pronouns or unclear
        if len(noun_text) < 3:
            return False
        
        # Concrete technical nouns are good referents
        concrete_tech_nouns = {
            'system', 'server', 'database', 'application', 'service',
            'network', 'device', 'file', 'document', 'interface'
        }
        
        if noun_text in concrete_tech_nouns:
            return True
            
        return True
    
    def _is_clear_temporal_reference(self, pronoun_token, doc) -> bool:
        """Enhanced temporal reference detection using evidence-based patterns."""
        if pronoun_token.lemma_.lower() != 'this':
            return False
        
        if pronoun_token.dep_ == 'det':
            noun = pronoun_token.head
            if noun.pos_ in ['NOUN', 'PROPN']:
                if noun.lemma_.lower() in self.clear_referent_patterns['temporal_nouns']:
                    # Check if it's in a prepositional phrase
                    prep_head = noun.head
                    if (prep_head.pos_ == 'ADP' and 
                        prep_head.lemma_.lower() in self.clear_referent_patterns['temporal_preps']):
                        return True
                    
                    # Also check for sentence-initial temporal context
                    if (pronoun_token.i == 0 and 
                        noun.dep_ in ['nsubj', 'nsubjpass'] and
                        noun.head.pos_ == 'VERB'):
                        return True
        
        return False
    
    def _has_clear_coordinated_antecedent(self, pronoun_token) -> bool:
        """Enhanced coordinated antecedent detection."""
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
    
    def _has_clear_dominant_antecedent(self, pronoun_token, doc, context: AmbiguityContext, nlp, referents: List[Dict[str, Any]]) -> bool:
        """Enhanced dominant antecedent detection using evidence-based analysis."""
        if len(referents) == 1:
            return True
        
        # Separate current sentence referents from context referents
        current_sentence_refs = [r for r in referents if r.get('source') == 'current_sentence']
        context_refs = [r for r in referents if r.get('source') == 'context']
        
        # Prioritize same-sentence referents
        if current_sentence_refs:
            current_subjects = [r for r in current_sentence_refs if r.get('is_subject', False)]
            
            # If there's exactly one subject in the current sentence, it's likely clear
            if len(current_subjects) == 1:
                return True
            
            # If there's only one current sentence referent total, it's clear
            if len(current_sentence_refs) == 1:
                return True
            
            # Check for subordinate clause patterns
            if self._has_clear_subordinate_antecedent(pronoun_token, doc, current_sentence_refs):
                return True
        
        # Fall back to original logic
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
    
    def _has_clear_subordinate_antecedent(self, pronoun_token, doc, current_sentence_refs: List[Dict[str, Any]]) -> bool:
        """Enhanced subordinate antecedent detection."""
        subordinate_conjunctions = {'when', 'while', 'if', 'as', 'after', 'before', 'since'}
        
        potential_antecedents = []
        
        for token in doc:
            if token.i >= pronoun_token.i:
                break
                
            if (token.lemma_.lower() in subordinate_conjunctions and 
                token.pos_ in ['SCONJ', 'ADP']):
                
                for next_token in doc[token.i:pronoun_token.i]:
                    if (next_token.pos_ in ['NOUN', 'PROPN'] and
                        next_token.lemma_.lower() not in ['way', 'time', 'thing']):
                        
                        matching_refs = [r for r in current_sentence_refs 
                                       if r['lemma'].lower() == next_token.lemma_.lower()]
                        
                        if matching_refs:
                            potential_antecedents.extend(matching_refs)
        
        if len(potential_antecedents) == 1:
            return True
            
        # Filter substantial nouns
        substantial_nouns = []
        for r in current_sentence_refs:
            lemma = r['lemma'].lower()
            if (lemma not in ['way', 'time', 'thing', 'place', 'update'] and
                r['pos'] in ['NOUN', 'PROPN'] and
                len(r['text']) > 3):
                substantial_nouns.append(r)
        
        if len(substantial_nouns) == 1:
            return True
            
        # Special case for 'service' in technical contexts
        service_refs = [r for r in current_sentence_refs if r['lemma'].lower() == 'service']
        if len(service_refs) == 1 and len(current_sentence_refs) <= 4:
            return True
            
        return False
    
    def _has_strong_discourse_continuation(self, doc) -> bool:
        """Check for strong discourse markers that indicate continuation."""
        for token in doc:
            if token.lemma_.lower() in self.strong_discourse_markers:
                return True
        return False

    def _find_potential_referents(self, pronoun_token, doc) -> List[Dict[str, Any]]:
        """Find potential referents in current sentence."""
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
        """Find potential referents in context sentences."""
        referents = []
        if not context.preceding_sentences:
            return referents
        for i, sentence in enumerate(context.preceding_sentences):
            if i >= self.max_referent_distance:
                break
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
            except Exception:
                continue
        return referents
    
    def _is_potential_referent(self, token, pronoun_token) -> bool:
        """Check if token could be a referent for the pronoun."""
        if len(token.text) < 2 or token.is_stop or abs(token.i - pronoun_token.i) < 2:
            return False
        return True
    
    def _is_potential_antecedent(self, token) -> bool:
        """Check if token could be an antecedent."""
        if token.pos_ not in ['NOUN', 'PROPN'] or len(token.text) < 2 or token.is_stop:
            return False
        if token.text.lower() in ['thing', 'stuff', 'item', 'one']:
            return False
        return True
    
    def _is_subject_token(self, token, doc) -> bool:
        """Check if token is a subject."""
        if token.dep_ in ['nsubj', 'nsubjpass']:
            return True
        if token.dep_ == 'conj':
            head = token.head
            if head.dep_ in ['nsubj', 'nsubjpass']:
                return True
            current = token
            while current.head != current and current.dep_ == 'conj':
                current = current.head
                if current.dep_ in ['nsubj', 'nsubjpass']:
                    return True
        return False
    
    def _filter_matching_referents(self, pronoun_token, referents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter referents that could match the pronoun."""
        return [r for r in referents if self._pronoun_referent_match(pronoun_token, r)]
    
    def _pronoun_referent_match(self, pronoun_token, referent: Dict[str, Any]) -> bool:
        """Check if pronoun and referent could match."""
        return not self._is_unlikely_referent(referent)
    
    def _is_unlikely_referent(self, referent: Dict[str, Any]) -> bool:
        """Check if referent is unlikely to be the antecedent."""
        if len(referent['text']) < 3:
            return True
        if referent['lemma'].lower() in {'thing', 'way', 'time', 'part', 'use', 'work', 'place'}:
            return True
        return False
    
    def _prioritize_referents_by_grammar(self, pronoun_token, referents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize referents based on grammatical roles."""
        if not referents:
            return referents
        if pronoun_token.text.lower() == 'it' and pronoun_token.i == 0:
            subjects = [r for r in referents if r.get('is_subject', False)]
            objects = [r for r in referents if r.get('is_object', False)]
            other = [r for r in referents if not r.get('is_subject', False) and not r.get('is_object', False)]
            if subjects:
                if len(subjects) > 1:
                    return subjects + objects
                else:
                    likely_objects = [o for o in objects if self._is_likely_antecedent_object(o)]
                    return subjects + likely_objects
            else:
                return objects + other
        return referents
    
    def _is_likely_antecedent_object(self, referent: Dict[str, Any]) -> bool:
        """Check if object referent is likely to be an antecedent."""
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
            if entity == text or entity in text:
                return True
        for entity in unlikely_object_entities:
            if re.search(r'\b' + re.escape(entity) + r'\b', text):
                return False
        if re.search(r'\bdata\b', text) and text not in ['database', 'metadata', 'dataset']:
            return False
        return True
    
    def _calculate_ambiguity_confidence(self, pronoun_token, referents: List[Dict[str, Any]], context: AmbiguityContext, doc) -> float:
        """Legacy confidence calculation method - kept for compatibility."""
        if len(referents) < self.min_referents_for_ambiguity:
            return 0.0
        referent_count = len(referents)
        if referent_count == 2:
            confidence = 0.6
        elif referent_count == 3:
            confidence = 0.8
        else:
            confidence = 0.9
        subjects = [r for r in referents if r.get('is_subject', False)]
        objects = [r for r in referents if r.get('is_object', False)]
        if len(subjects) > 1:
            confidence += 0.1
        if len(objects) > 1:
            confidence += 0.1
        if len(subjects) >= 1 and len(objects) >= 1:
            confidence += 0.05
        if pronoun_token.text.lower() in ['it', 'this', 'that']:
            confidence += 0.05
        if pronoun_token.i == 0:
            confidence += 0.05
        if self._has_strong_discourse_continuation(doc):
            confidence -= 0.2
        context_referents = [r for r in referents if r.get('source') == 'context']
        if len(context_referents) > 0:
            confidence -= 0.05
        return min(1.0, max(0.0, confidence))
    
    def _determine_ambiguity_type(self, pronoun_token, doc, referents: List[Dict[str, Any]]) -> AmbiguityType:
        """Determine the type of ambiguity detected."""
        if (pronoun_token.i == 0 and 
            pronoun_token.text.lower() in ['it', 'this', 'that'] and
            any(r.get('source') == 'context' for r in referents)):
            return AmbiguityType.UNCLEAR_ANTECEDENT
        return AmbiguityType.AMBIGUOUS_PRONOUN
    
    def _create_pronoun_detection(self, pronoun_token, evidence_score: float, context: AmbiguityContext, nlp) -> AmbiguityDetection:
        """Create pronoun ambiguity detection with evidence-based confidence."""
        # Get referent analysis for detection details
        ambiguity_info = self._analyze_pronoun_ambiguity(pronoun_token, doc=nlp(context.sentence), context=context, nlp=nlp)
        if not ambiguity_info:
            # Fallback if analysis fails
            ambiguity_info = {
                'pronoun': pronoun_token.text,
                'referents': [],
                'confidence': evidence_score,
                'referent_count': 0,
                'ambiguity_type': AmbiguityType.AMBIGUOUS_PRONOUN
            }
        
        pronoun_text = pronoun_token.text
        referents = ambiguity_info['referents']
        referent_texts = [r['text'] for r in referents]
        ambiguity_type = ambiguity_info['ambiguity_type']
        
        evidence = AmbiguityEvidence(
            tokens=[pronoun_text], 
            linguistic_pattern=f"ambiguous_pronoun_{pronoun_token.lemma_}",
            confidence=evidence_score,
            spacy_features={
                'pronoun_pos': pronoun_token.pos_, 
                'pronoun_lemma': pronoun_token.lemma_, 
                'referent_count': len(referents), 
                'referent_types': [r['pos'] for r in referents], 
                'sentence_start': pronoun_token.i == 0,
                'ambiguity_type': ambiguity_type.value
            },
            context_clues={
                'referents': referent_texts, 
                'source_sentences': [r.get('source_sentence', '') for r in referents if r.get('source_sentence')]
            }
        )
        
        # Determine severity based on evidence score
        if evidence_score > 0.85 or len(referents) >= 3:
            severity = AmbiguitySeverity.HIGH
        elif evidence_score > 0.70 or len(referents) == 2:
            severity = AmbiguitySeverity.MEDIUM
        else:
            severity = AmbiguitySeverity.LOW
        
        strategies = [ResolutionStrategy.CLARIFY_PRONOUN, ResolutionStrategy.RESTRUCTURE_SENTENCE]
        if ambiguity_type == AmbiguityType.UNCLEAR_ANTECEDENT:
            strategies.append(ResolutionStrategy.SPECIFY_REFERENCE)
        
        ai_instructions = self._generate_ai_instructions(pronoun_token, referent_texts, ambiguity_type, evidence_score)
        examples = self._generate_examples(pronoun_text, referent_texts)
        
        return AmbiguityDetection(
            ambiguity_type=ambiguity_type, 
            category=AmbiguityCategory.SEMANTIC, 
            severity=severity,
            context=context, 
            evidence=evidence, 
            resolution_strategies=strategies,
            ai_instructions=ai_instructions, 
            examples=examples,
            span=(pronoun_token.idx, pronoun_token.idx + len(pronoun_text)), 
            flagged_text=pronoun_text
        )
    
    def _create_detection(self, pronoun_token, ambiguity_info: Dict[str, Any], context: AmbiguityContext) -> AmbiguityDetection:
        """Legacy method - delegates to evidence-based approach."""
        evidence_score = ambiguity_info['confidence']
        return self._create_pronoun_detection(pronoun_token, evidence_score, context, None)
    
    def _generate_ai_instructions(self, pronoun_token, referent_texts: List[str], ambiguity_type: AmbiguityType, evidence_score: float) -> List[str]:
        """Generate AI instructions for handling pronoun ambiguity."""
        instructions = []
        pronoun_text = pronoun_token.text
        referent_list = ", ".join(f"'{text}'" for text in referent_texts)
        
        # Base instruction
        instructions.append(
            f"The pronoun '{pronoun_text}' creates ambiguity about its referent."
        )
        
        # Type-specific instructions
        if ambiguity_type == AmbiguityType.UNCLEAR_ANTECEDENT:
            instructions.append("This sentence-initial pronoun lacks a clear antecedent from previous context.")
            instructions.append(f"Replace '{pronoun_text}' with a specific noun to clarify the reference.")
        else:
            instructions.append("This pronoun has multiple potential referents within the sentence or context.")
            instructions.append(f"Clarify the pronoun '{pronoun_text}' by replacing it with a specific noun.")
        
        # Evidence-based instructions
        if evidence_score > 0.85:
            instructions.append("High confidence: This pronoun definitely needs clarification for professional accuracy.")
        elif evidence_score > 0.70:
            instructions.append("Moderate confidence: Consider clarification to improve readability.")
        
        # Referent-specific guidance
        if referent_texts:
            instructions.append(f"Potential referents include: {referent_list}")
            instructions.append("Choose the most appropriate referent based on context and rewrite the sentence.")
        
        # General guidance
        instructions.append("Rewrite to eliminate ambiguity about what the pronoun refers to.")
        instructions.append("Ensure the revised sentence clearly identifies the entity being referenced.")
        
        return instructions

    def _generate_examples(self, pronoun_text: str, referent_texts: List[str]) -> List[str]:
        """Generate examples for pronoun clarification."""
        examples = []
        if len(referent_texts) >= 2:
            if pronoun_text.lower() in ['it', 'this', 'that']:
                examples.append(f"Instead of '{pronoun_text} performs...', write 'The {referent_texts[0]} performs...' or 'The {referent_texts[1]} performs...'")
                examples.append(f"Replace '{pronoun_text} is' with 'The {referent_texts[0]} is' for clarity")
            elif pronoun_text.lower() in ['they', 'them', 'these', 'those']:
                examples.append(f"Instead of '{pronoun_text} are...', specify 'The {referent_texts[0]} and {referent_texts[1]} are...'")
        return examples