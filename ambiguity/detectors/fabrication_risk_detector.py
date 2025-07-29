"""
Fabrication Risk Detector

Detects situations where AI might be tempted to add information
that is not present in the original text, leading to hallucination.

Examples:
- Vague actions that could be expanded with unverified details
- Incomplete explanations that invite elaboration
- Technical processes that could be over-specified
"""

from typing import List, Dict, Any, Optional, Set
import re

from ..base_ambiguity_rule import AmbiguityDetector
from ..types import (
    AmbiguityType, AmbiguityCategory, AmbiguitySeverity,
    AmbiguityContext, AmbiguityEvidence, AmbiguityDetection,
    ResolutionStrategy, AmbiguityConfig
)


class FabricationRiskDetector(AmbiguityDetector):
    """
    Detects situations with high risk of information fabrication.
    
    This detector identifies text patterns that commonly lead AI rewriters
    to add information that wasn't in the original text.
    """
    
    def __init__(self, config: AmbiguityConfig, parent_rule=None):
        super().__init__(config, parent_rule)
        
        self.vague_action_verbs = {
            'communicate', 'interact', 'process', 'handle', 'manage',
            'work', 'operate', 'function', 'perform', 'execute'
        }
        self.incomplete_patterns = [
            r'communicates?\s+with', r'connects?\s+to', r'works?\s+with',
            r'interacts?\s+with', r'processes?\s+the', r'handles?\s+the',
            r'manages?\s+the', r'performs?\s+the', r'executes?\s+the'
        ]
        self.technical_processes = {
            'backup', 'configuration', 'installation', 'deployment',
            'integration', 'synchronization', 'authentication',
            'authorization', 'validation', 'verification',
            'monitoring', 'logging', 'analysis', 'processing'
        }
        self.purpose_indicators = [
            r'for\s+\w+\s+purposes?', r'to\s+ensure', r'to\s+verify',
            r'to\s+confirm', r'to\s+check', r'to\s+validate',
            r'to\s+monitor', r'in\s+order\s+to'
        ]
        self.min_confidence = 0.7
    
    def detect(self, context: AmbiguityContext, nlp) -> List[AmbiguityDetection]:
        detections = []
        if not context.sentence.strip():
            return detections
        
        document_context = context.document_context or {}
        block_type = document_context.get('block_type', '').lower()
        
        if 'list_item' in block_type or block_type in ['heading', 'section', 'table_cell']:
            if self._is_technical_label(context.sentence):
                return detections
        
        try:
            doc = nlp(context.sentence)
            vague_actions = self._detect_vague_actions(doc, context)
            detections.extend(vague_actions)
            incomplete_explanations = self._detect_incomplete_explanations(context, doc)
            detections.extend(incomplete_explanations)
            technical_risks = self._detect_technical_process_risks(doc, context)
            detections.extend(technical_risks)
            purpose_risks = self._detect_purpose_fabrication_risks(context, doc)
            detections.extend(purpose_risks)
        except Exception as e:
            print(f"Error in fabrication risk detection: {e}")
        return detections
    
    def _detect_vague_actions(self, doc, context: AmbiguityContext) -> List[AmbiguityDetection]:
        detections = []
        for token in doc:
            # LINGUISTIC ANCHOR: Only flag actual verbs, not nouns.
            # This prevents flagging standalone nouns like "handling" or "logging".
            if token.pos_ == 'VERB' and self._is_vague_action_verb(token):
                # LINGUISTIC ANCHOR 2: Skip gerunds that function as compound noun modifiers
                # Examples: "error handling", "data processing", "file handling"
                if self._is_gerund_noun_modifier(token, doc):
                    continue
                    
                risk_score = self._calculate_action_risk(token, doc, context)
                if risk_score >= self.min_confidence:
                    detection = self._create_vague_action_detection(token, risk_score, context)
                    detections.append(detection)
        return detections
    
    def _detect_incomplete_explanations(self, context: AmbiguityContext, doc) -> List[AmbiguityDetection]:
        detections = []
        sentence_lower = context.sentence.lower()
        for pattern in self.incomplete_patterns:
            for match in re.finditer(pattern, sentence_lower):
                risk_score = self._calculate_explanation_risk(match.group(), context)
                if risk_score >= self.min_confidence:
                    tokens = match.group().split()
                    detection = self._create_incomplete_explanation_detection(match.group(), tokens, risk_score, context)
                    detections.append(detection)
        return detections
    
    def _detect_technical_process_risks(self, doc, context: AmbiguityContext) -> List[AmbiguityDetection]:
        detections = []
        for token in doc:
            if self._is_technical_process(token):
                # LINGUISTIC ANCHOR: Skip gerunds that function as noun modifiers
                # Examples: "data processing", "network monitoring", "error logging"
                if self._is_gerund_noun_modifier(token, doc):
                    continue
                
                # LINGUISTIC ANCHOR: Skip compound technical nouns
                # Examples: "data processing systems", "network monitoring tools"
                if self._is_compound_technical_noun(token, doc):
                    continue
                    
                risk_score = self._calculate_process_risk(token, doc, context)
                if risk_score >= self.min_confidence:
                    detection = self._create_technical_process_detection(token, risk_score, context)
                    detections.append(detection)
        return detections
    
    def _detect_purpose_fabrication_risks(self, context: AmbiguityContext, doc) -> List[AmbiguityDetection]:
        detections = []
        sentence_lower = context.sentence.lower()
        for pattern in self.purpose_indicators:
            for match in re.finditer(pattern, sentence_lower):
                risk_score = self._calculate_purpose_risk(match.group(), context)
                if risk_score >= self.min_confidence:
                    tokens = match.group().split()
                    detection = self._create_purpose_fabrication_detection(match.group(), tokens, risk_score, context)
                    detections.append(detection)
        return detections
    
    def _is_vague_action_verb(self, token) -> bool:
        if not token: return False
        return token.lemma_.lower() in self.vague_action_verbs
    
    def _is_technical_process(self, token) -> bool:
        if not token: return False
        lemma = token.lemma_.lower()
        text = token.text.lower()
        return lemma in self.technical_processes or text in self.technical_processes
    
    def _calculate_action_risk(self, token, doc, context: AmbiguityContext) -> float:
        risk = 0.5
        if token.lemma_.lower() in ['communicate', 'interact', 'work', 'handle']: risk += 0.3
        if not self._has_clear_object(token, doc): risk += 0.2
        if self._is_technical_context(context): risk += 0.2
        if self._has_specific_details(token, doc): risk -= 0.2
        return min(1.0, max(0.0, risk))
    
    def _calculate_explanation_risk(self, pattern: str, context: AmbiguityContext) -> float:
        risk = 0.6
        if pattern in ['communicates with', 'works with', 'interacts with']: risk += 0.2
        if self._is_technical_context(context): risk += 0.2
        return min(1.0, max(0.0, risk))
    
    def _calculate_process_risk(self, token, doc, context: AmbiguityContext) -> float:
        risk = 0.5
        if token.lemma_.lower() in ['backup', 'configuration', 'integration']: risk += 0.3
        if not self._has_process_details(token, doc): risk += 0.2
        return min(1.0, max(0.0, risk))
    
    def _calculate_purpose_risk(self, pattern: str, context: AmbiguityContext) -> float:
        risk = 0.6
        if pattern in ['to ensure', 'to verify', 'to confirm']: risk += 0.2
        return min(1.0, max(0.0, risk))
    
    def _has_clear_object(self, token, doc) -> bool:
        for child in token.children:
            if child.dep_ in ['dobj', 'pobj'] and not child.is_stop: return True
        return False
    
    def _has_specific_details(self, token, doc) -> bool:
        start_idx, end_idx = max(0, token.i - 3), min(len(doc), token.i + 4)
        for i in range(start_idx, end_idx):
            if (doc[i].pos_ in ['PROPN', 'NUM'] or doc[i].like_url or len(doc[i].text) > 8):
                return True
        return False
    
    def _has_process_details(self, token, doc) -> bool:
        for child in token.children:
            if child.pos_ in ['NOUN', 'PROPN', 'NUM'] and not child.is_stop: return True
        return False
    
    def _is_technical_context(self, context: AmbiguityContext) -> bool:
        technical_keywords = ['system', 'server', 'application', 'software', 'service', 'database', 'network', 'api', 'configuration', 'deployment']
        return any(keyword in context.sentence.lower() for keyword in technical_keywords)
    
    def _create_vague_action_detection(self, token, risk_score: float, context: AmbiguityContext) -> AmbiguityDetection:
        evidence = AmbiguityEvidence(
            tokens=[token.text], linguistic_pattern=f"vague_action_{token.lemma_}", confidence=risk_score,
            spacy_features={'pos': token.pos_, 'lemma': token.lemma_, 'dep': token.dep_, 'has_object': self._has_clear_object(token, None)},
            context_clues={'action_type': 'vague_verb'}
        )
        strategies = [ResolutionStrategy.SPECIFY_REFERENCE, ResolutionStrategy.RESTRUCTURE_SENTENCE]
        ai_instructions = [f"The verb '{token.text}' is vague and could lead to adding unverified details", "Do not add specific purposes, methods, or details that are not in the original text", "Keep the action description as general as the original unless specific details are provided"]
        return AmbiguityDetection(
            ambiguity_type=AmbiguityType.FABRICATION_RISK, category=AmbiguityCategory.SEMANTIC,
            severity=AmbiguitySeverity.CRITICAL, context=context, evidence=evidence,
            resolution_strategies=strategies, ai_instructions=ai_instructions
        )
    
    def _create_incomplete_explanation_detection(self, pattern: str, tokens: List[str], risk_score: float, context: AmbiguityContext) -> AmbiguityDetection:
        evidence = AmbiguityEvidence(
            tokens=tokens, linguistic_pattern=f"incomplete_explanation_{pattern.replace(' ', '_')}",
            confidence=risk_score, spacy_features={'pattern_type': 'incomplete'}, context_clues={'pattern': pattern}
        )
        strategies = [ResolutionStrategy.SPECIFY_REFERENCE, ResolutionStrategy.ADD_CONTEXT]
        ai_instructions = [f"The phrase '{pattern}' is incomplete and could invite adding unverified details", "Do not add specific purposes, methods, or explanations not in the original text", "Preserve the level of detail from the original text"]
        return AmbiguityDetection(
            ambiguity_type=AmbiguityType.FABRICATION_RISK, category=AmbiguityCategory.SEMANTIC,
            severity=AmbiguitySeverity.CRITICAL, context=context, evidence=evidence,
            resolution_strategies=strategies, ai_instructions=ai_instructions
        )
    
    def _create_technical_process_detection(self, token, risk_score: float, context: AmbiguityContext) -> AmbiguityDetection:
        evidence = AmbiguityEvidence(
            tokens=[token.text], linguistic_pattern=f"technical_process_{token.lemma_}",
            confidence=risk_score, spacy_features={'pos': token.pos_, 'lemma': token.lemma_, 'process_type': 'technical'},
            context_clues={'process': token.text}
        )
        strategies = [ResolutionStrategy.SPECIFY_REFERENCE, ResolutionStrategy.RESTRUCTURE_SENTENCE]
        ai_instructions = [f"The technical process '{token.text}' could be over-specified with unverified details", "Do not add specific steps, parameters, or configurations not in the original text", "Keep technical descriptions as general as the original unless specifics are provided"]
        return AmbiguityDetection(
            ambiguity_type=AmbiguityType.FABRICATION_RISK, category=AmbiguityCategory.SEMANTIC,
            severity=AmbiguitySeverity.CRITICAL, context=context, evidence=evidence,
            resolution_strategies=strategies, ai_instructions=ai_instructions
        )
    
    def _create_purpose_fabrication_detection(self, pattern: str, tokens: List[str], risk_score: float, context: AmbiguityContext) -> AmbiguityDetection:
        evidence = AmbiguityEvidence(
            tokens=tokens, linguistic_pattern=f"purpose_statement_{pattern.replace(' ', '_')}",
            confidence=risk_score, spacy_features={'pattern_type': 'purpose'}, context_clues={'pattern': pattern}
        )
        strategies = [ResolutionStrategy.SPECIFY_REFERENCE, ResolutionStrategy.RESTRUCTURE_SENTENCE]
        ai_instructions = [f"The purpose statement '{pattern}' could invite adding unverified explanations", "Do not add specific purposes or reasons not explicitly stated in the original text", "Keep purpose statements as general as the original unless specific purposes are provided"]
        return AmbiguityDetection(
            ambiguity_type=AmbiguityType.FABRICATION_RISK, category=AmbiguityCategory.SEMANTIC,
            severity=AmbiguitySeverity.CRITICAL, context=context, evidence=evidence,
            resolution_strategies=strategies, ai_instructions=ai_instructions
        ) 

    def _is_technical_label(self, text: str) -> bool:
        text_lower = text.lower().strip()
        if len(text.split()) <= 3:
            technical_terms = [
                'deployment', 'code scanning', 'image building', 'vulnerability detection',
                'integration', 'monitoring', 'authentication', 'configuration',
                'backup', 'scaling', 'logging', 'api', 'cli', 'sdk'
            ]
            if text_lower in technical_terms: return True
            words = text_lower.split()
            if len(words) == 2:
                if any(word in ['code', 'image', 'security', 'data', 'system'] for word in words):
                    return True
        return False

    def _is_gerund_noun_modifier(self, token, doc) -> bool:
        """
        Detects when a gerund (VBG) is functioning as a noun modifier rather than an active verb.
        Examples: "error handling", "data processing", "file handling"
        """
        # Only applies to gerunds (VBG tags)
        if token.tag_ != 'VBG':
            return False
        
        # Check if it's functioning as a compound noun modifier
        if token.dep_ in ('compound', 'amod', 'acl'):
            # If modifying a noun, it's likely a noun modifier, not an active verb
            if token.head.pos_ in ('NOUN', 'PROPN'):
                return True
        
        # Check for common technical compound patterns: "[adjective] [gerund] [noun]"
        # Examples: "error handling module", "data processing system"
        if (token.i > 0 and token.i < len(doc) - 1):
            prev_token = doc[token.i - 1]
            next_token = doc[token.i + 1]
            
            # Pattern: technical_adjective + gerund + noun
            technical_adjectives = {
                'error', 'data', 'file', 'image', 'user', 'system', 'network',
                'security', 'application', 'database', 'server', 'client',
                'automatic', 'manual', 'real-time', 'batch', 'background'
            }
            
            if (prev_token.lemma_.lower() in technical_adjectives and 
                next_token.pos_ in ('NOUN', 'PROPN')):
                return True
        
        # Check if the gerund has no typical verb arguments (no direct objects, etc.)
        # Real verbs usually have objects, but noun modifiers don't
        has_verb_args = any(child.dep_ in ('dobj', 'iobj', 'ccomp', 'xcomp') 
                           for child in token.children)
        
        if not has_verb_args and token.dep_ in ('compound', 'amod', 'acl'):
            return True
        
        return False

    def _is_compound_technical_noun(self, token, doc) -> bool:
        """
        Detects compound technical nouns that should not be flagged as fabrication risks.
        Examples: "data processing systems", "network monitoring tools", "image processing algorithms"
        """
        # Check if it's a compound noun (NN tag with compound dependency)
        if token.pos_ != 'NOUN' or token.dep_ != 'compound':
            return False
        
        # Check if it's modifying another noun (typical compound pattern)
        if token.head.pos_ not in ('NOUN', 'PROPN'):
            return False
        
        # Check for technical compound patterns
        if (token.i > 0 and token.i < len(doc) - 1):
            prev_token = doc[token.i - 1]
            next_token = doc[token.i + 1]
            
            # Pattern: [technical_noun] + [process_noun] + [system_noun]
            # Examples: "data processing systems", "image processing algorithms"
            technical_nouns = {
                'data', 'image', 'network', 'system', 'user', 'error', 'file',
                'security', 'application', 'database', 'server', 'client',
                'backup', 'real-time', 'automatic', 'manual', 'real', 'time'
            }
            
            system_nouns = {
                'systems', 'tools', 'algorithms', 'capabilities', 'procedures',
                'modules', 'frameworks', 'components', 'services', 'applications',
                'methods', 'techniques', 'processes', 'mechanisms', 'features'
            }
            
            if (prev_token.lemma_.lower() in technical_nouns and 
                next_token.lemma_.lower() in system_nouns):
                return True
        
        # Also check if the compound is clearly a noun phrase, not an action
        # Compound nouns typically don't have direct objects or other verb-like children
        if token.head.dep_ in ('nsubj', 'dobj', 'pobj'):
            return True
        
        return False 
