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
    
    def __init__(self, config: AmbiguityConfig):
        super().__init__(config)
        
        # Vague action verbs that often get over-specified
        self.vague_action_verbs = {
            'communicate', 'communicates', 'communicating', 'communicate',
            'interact', 'interacts', 'interacting', 'interact',
            'process', 'processes', 'processing', 'process',
            'handle', 'handles', 'handling', 'handle',
            'manage', 'manages', 'managing', 'manage',
            'work', 'works', 'working', 'work',
            'operate', 'operates', 'operating', 'operate',
            'function', 'functions', 'functioning', 'function',
            'perform', 'performs', 'performing', 'perform',
            'execute', 'executes', 'executing', 'execute'
        }
        
        # Incomplete explanation patterns
        self.incomplete_patterns = [
            r'communicates?\s+with',
            r'connects?\s+to',
            r'works?\s+with',
            r'interacts?\s+with',
            r'processes?\s+the',
            r'handles?\s+the',
            r'manages?\s+the',
            r'performs?\s+the',
            r'executes?\s+the'
        ]
        
        # Technical process indicators that might be over-specified
        self.technical_processes = {
            'backup', 'configuration', 'installation', 'deployment',
            'integration', 'synchronization', 'authentication',
            'authorization', 'validation', 'verification',
            'monitoring', 'logging', 'analysis', 'processing'
        }
        
        # Purpose/reason indicators that might invite fabrication
        self.purpose_indicators = [
            r'for\s+\w+\s+purposes?',
            r'to\s+ensure',
            r'to\s+verify',
            r'to\s+confirm',
            r'to\s+check',
            r'to\s+validate',
            r'to\s+monitor',
            r'in\s+order\s+to'
        ]
        
        # Risk threshold
        self.min_confidence = 0.7
    
    def detect(self, context: AmbiguityContext, nlp) -> List[AmbiguityDetection]:
        """
        Detect fabrication risks in the given context.
        
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
            
            # Check for vague actions
            vague_actions = self._detect_vague_actions(doc, context)
            detections.extend(vague_actions)
            
            # Check for incomplete explanations
            incomplete_explanations = self._detect_incomplete_explanations(context, doc)
            detections.extend(incomplete_explanations)
            
            # Check for technical processes that might be over-specified
            technical_risks = self._detect_technical_process_risks(doc, context)
            detections.extend(technical_risks)
            
            # Check for purpose statements that might invite fabrication
            purpose_risks = self._detect_purpose_fabrication_risks(context, doc)
            detections.extend(purpose_risks)
        
        except Exception as e:
            # Log error but don't fail the analysis
            print(f"Error in fabrication risk detection: {e}")
        
        return detections
    
    def _detect_vague_actions(self, doc, context: AmbiguityContext) -> List[AmbiguityDetection]:
        """Detect vague action verbs that might be over-specified."""
        detections = []
        
        for token in doc:
            if self._is_vague_action_verb(token):
                # Check if this action is vague enough to risk fabrication
                risk_score = self._calculate_action_risk(token, doc, context)
                
                if risk_score >= self.min_confidence:
                    detection = self._create_vague_action_detection(token, risk_score, context)
                    detections.append(detection)
        
        return detections
    
    def _detect_incomplete_explanations(self, context: AmbiguityContext, doc) -> List[AmbiguityDetection]:
        """Detect incomplete explanations that might invite fabrication."""
        detections = []
        
        sentence_lower = context.sentence.lower()
        
        for pattern in self.incomplete_patterns:
            matches = re.finditer(pattern, sentence_lower)
            
            for match in matches:
                # Check if this incomplete explanation has high fabrication risk
                risk_score = self._calculate_explanation_risk(match.group(), context)
                
                if risk_score >= self.min_confidence:
                    tokens = match.group().split()
                    detection = self._create_incomplete_explanation_detection(
                        match.group(), tokens, risk_score, context
                    )
                    detections.append(detection)
        
        return detections
    
    def _detect_technical_process_risks(self, doc, context: AmbiguityContext) -> List[AmbiguityDetection]:
        """Detect technical processes that might be over-specified."""
        detections = []
        
        for token in doc:
            if self._is_technical_process(token):
                # Check if this process description is vague enough to risk fabrication
                risk_score = self._calculate_process_risk(token, doc, context)
                
                if risk_score >= self.min_confidence:
                    detection = self._create_technical_process_detection(token, risk_score, context)
                    detections.append(detection)
        
        return detections
    
    def _detect_purpose_fabrication_risks(self, context: AmbiguityContext, doc) -> List[AmbiguityDetection]:
        """Detect purpose statements that might invite fabrication."""
        detections = []
        
        sentence_lower = context.sentence.lower()
        
        for pattern in self.purpose_indicators:
            matches = re.finditer(pattern, sentence_lower)
            
            for match in matches:
                # Check if this purpose statement has fabrication risk
                risk_score = self._calculate_purpose_risk(match.group(), context)
                
                if risk_score >= self.min_confidence:
                    tokens = match.group().split()
                    detection = self._create_purpose_fabrication_detection(
                        match.group(), tokens, risk_score, context
                    )
                    detections.append(detection)
        
        return detections
    
    def _is_vague_action_verb(self, token) -> bool:
        """Check if a token is a vague action verb."""
        if not token or token.pos_ != 'VERB':
            return False
        
        lemma = token.lemma_.lower()
        return lemma in self.vague_action_verbs
    
    def _is_technical_process(self, token) -> bool:
        """Check if a token represents a technical process."""
        if not token:
            return False
        
        lemma = token.lemma_.lower()
        text = token.text.lower()
        
        return lemma in self.technical_processes or text in self.technical_processes
    
    def _calculate_action_risk(self, token, doc, context: AmbiguityContext) -> float:
        """Calculate the fabrication risk for a vague action."""
        risk = 0.5  # Base risk
        
        # Higher risk for very vague verbs
        if token.lemma_.lower() in ['communicate', 'interact', 'work', 'handle']:
            risk += 0.3
        
        # Higher risk if there's no clear object or purpose
        if not self._has_clear_object(token, doc):
            risk += 0.2
        
        # Higher risk in technical contexts
        if self._is_technical_context(context):
            risk += 0.2
        
        # Lower risk if there are specific details already provided
        if self._has_specific_details(token, doc):
            risk -= 0.2
        
        return min(1.0, max(0.0, risk))
    
    def _calculate_explanation_risk(self, pattern: str, context: AmbiguityContext) -> float:
        """Calculate the fabrication risk for an incomplete explanation."""
        risk = 0.6  # Base risk for incomplete explanations
        
        # Higher risk for very vague patterns
        if pattern in ['communicates with', 'works with', 'interacts with']:
            risk += 0.2
        
        # Higher risk in technical contexts
        if self._is_technical_context(context):
            risk += 0.2
        
        return min(1.0, max(0.0, risk))
    
    def _calculate_process_risk(self, token, doc, context: AmbiguityContext) -> float:
        """Calculate the fabrication risk for a technical process."""
        risk = 0.5  # Base risk
        
        # Higher risk for processes that are often over-specified
        if token.lemma_.lower() in ['backup', 'configuration', 'integration']:
            risk += 0.3
        
        # Higher risk if the process is mentioned without details
        if not self._has_process_details(token, doc):
            risk += 0.2
        
        return min(1.0, max(0.0, risk))
    
    def _calculate_purpose_risk(self, pattern: str, context: AmbiguityContext) -> float:
        """Calculate the fabrication risk for a purpose statement."""
        risk = 0.6  # Base risk for purpose statements
        
        # Higher risk for vague purposes
        if pattern in ['to ensure', 'to verify', 'to confirm']:
            risk += 0.2
        
        return min(1.0, max(0.0, risk))
    
    def _has_clear_object(self, token, doc) -> bool:
        """Check if a verb has a clear object."""
        for child in token.children:
            if child.dep_ in ['dobj', 'pobj'] and not child.is_stop:
                return True
        return False
    
    def _has_specific_details(self, token, doc) -> bool:
        """Check if there are specific details around the token."""
        # Look for specific technical terms, numbers, or proper nouns
        start_idx = max(0, token.i - 3)
        end_idx = min(len(doc), token.i + 4)
        
        for i in range(start_idx, end_idx):
            if (doc[i].pos_ in ['PROPN', 'NUM'] or 
                doc[i].like_url or 
                len(doc[i].text) > 8):  # Longer words often more specific
                return True
        
        return False
    
    def _has_process_details(self, token, doc) -> bool:
        """Check if a technical process has specific details."""
        # Look for specific parameters, configurations, or technical terms
        for child in token.children:
            if child.pos_ in ['NOUN', 'PROPN', 'NUM'] and not child.is_stop:
                return True
        return False
    
    def _is_technical_context(self, context: AmbiguityContext) -> bool:
        """Check if this is a technical context."""
        technical_keywords = [
            'system', 'server', 'application', 'software', 'service',
            'database', 'network', 'api', 'configuration', 'deployment'
        ]
        
        sentence_lower = context.sentence.lower()
        return any(keyword in sentence_lower for keyword in technical_keywords)
    
    def _create_vague_action_detection(self, token, risk_score: float, context: AmbiguityContext) -> AmbiguityDetection:
        """Create a detection for a vague action verb."""
        
        # Create evidence
        evidence = AmbiguityEvidence(
            tokens=[token.text],
            linguistic_pattern=f"vague_action_{token.lemma_}",
            confidence=risk_score,
            spacy_features={
                'pos': token.pos_,
                'lemma': token.lemma_,
                'dep': token.dep_,
                'has_object': self._has_clear_object(token, None)
            },
            context_clues={'action_type': 'vague_verb'}
        )
        
        # Create resolution strategies
        strategies = [
            ResolutionStrategy.SPECIFY_REFERENCE,
            ResolutionStrategy.RESTRUCTURE_SENTENCE
        ]
        
        # Create AI instructions
        ai_instructions = [
            f"The verb '{token.text}' is vague and could lead to adding unverified details",
            "Do not add specific purposes, methods, or details that are not in the original text",
            "Keep the action description as general as the original unless specific details are provided"
        ]
        
        return AmbiguityDetection(
            ambiguity_type=AmbiguityType.FABRICATION_RISK,
            category=AmbiguityCategory.SEMANTIC,
            severity=AmbiguitySeverity.CRITICAL,
            context=context,
            evidence=evidence,
            resolution_strategies=strategies,
            ai_instructions=ai_instructions
        )
    
    def _create_incomplete_explanation_detection(self, pattern: str, tokens: List[str], 
                                               risk_score: float, context: AmbiguityContext) -> AmbiguityDetection:
        """Create a detection for an incomplete explanation."""
        
        # Create evidence
        evidence = AmbiguityEvidence(
            tokens=tokens,
            linguistic_pattern=f"incomplete_explanation_{pattern.replace(' ', '_')}",
            confidence=risk_score,
            spacy_features={'pattern_type': 'incomplete'},
            context_clues={'pattern': pattern}
        )
        
        # Create resolution strategies
        strategies = [
            ResolutionStrategy.SPECIFY_REFERENCE,
            ResolutionStrategy.ADD_CONTEXT
        ]
        
        # Create AI instructions
        ai_instructions = [
            f"The phrase '{pattern}' is incomplete and could invite adding unverified details",
            "Do not add specific purposes, methods, or explanations not in the original text",
            "Preserve the level of detail from the original text"
        ]
        
        return AmbiguityDetection(
            ambiguity_type=AmbiguityType.FABRICATION_RISK,
            category=AmbiguityCategory.SEMANTIC,
            severity=AmbiguitySeverity.CRITICAL,
            context=context,
            evidence=evidence,
            resolution_strategies=strategies,
            ai_instructions=ai_instructions
        )
    
    def _create_technical_process_detection(self, token, risk_score: float, context: AmbiguityContext) -> AmbiguityDetection:
        """Create a detection for a technical process with fabrication risk."""
        
        # Create evidence
        evidence = AmbiguityEvidence(
            tokens=[token.text],
            linguistic_pattern=f"technical_process_{token.lemma_}",
            confidence=risk_score,
            spacy_features={
                'pos': token.pos_,
                'lemma': token.lemma_,
                'process_type': 'technical'
            },
            context_clues={'process': token.text}
        )
        
        # Create resolution strategies
        strategies = [
            ResolutionStrategy.SPECIFY_REFERENCE,
            ResolutionStrategy.RESTRUCTURE_SENTENCE
        ]
        
        # Create AI instructions
        ai_instructions = [
            f"The technical process '{token.text}' could be over-specified with unverified details",
            "Do not add specific steps, parameters, or configurations not in the original text",
            "Keep technical descriptions as general as the original unless specifics are provided"
        ]
        
        return AmbiguityDetection(
            ambiguity_type=AmbiguityType.FABRICATION_RISK,
            category=AmbiguityCategory.SEMANTIC,
            severity=AmbiguitySeverity.CRITICAL,
            context=context,
            evidence=evidence,
            resolution_strategies=strategies,
            ai_instructions=ai_instructions
        )
    
    def _create_purpose_fabrication_detection(self, pattern: str, tokens: List[str], 
                                            risk_score: float, context: AmbiguityContext) -> AmbiguityDetection:
        """Create a detection for a purpose statement with fabrication risk."""
        
        # Create evidence
        evidence = AmbiguityEvidence(
            tokens=tokens,
            linguistic_pattern=f"purpose_statement_{pattern.replace(' ', '_')}",
            confidence=risk_score,
            spacy_features={'pattern_type': 'purpose'},
            context_clues={'pattern': pattern}
        )
        
        # Create resolution strategies
        strategies = [
            ResolutionStrategy.SPECIFY_REFERENCE,
            ResolutionStrategy.RESTRUCTURE_SENTENCE
        ]
        
        # Create AI instructions
        ai_instructions = [
            f"The purpose statement '{pattern}' could invite adding unverified explanations",
            "Do not add specific purposes or reasons not explicitly stated in the original text",
            "Keep purpose statements as general as the original unless specific purposes are provided"
        ]
        
        return AmbiguityDetection(
            ambiguity_type=AmbiguityType.FABRICATION_RISK,
            category=AmbiguityCategory.SEMANTIC,
            severity=AmbiguitySeverity.CRITICAL,
            context=context,
            evidence=evidence,
            resolution_strategies=strategies,
            ai_instructions=ai_instructions
        ) 