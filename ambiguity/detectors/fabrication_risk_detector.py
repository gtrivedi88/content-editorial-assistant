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
    Detects situations with high risk of information fabrication using evidence-based analysis.
    
    This detector is fully compatible with Level 2 Enhanced Validation, Evidence-Based 
    Rule Development, and Universal Confidence Threshold architecture. It provides
    sophisticated 7-factor evidence scoring for fabrication risk assessment.
    
    Architecture compliance:
    - confidence.md: Universal threshold (≥0.35), normalized confidence
    - evidence_based_rule_development.md: Multi-factor evidence assessment  
    - level_2_implementation.adoc: Enhanced validation integration
    """
    
    def __init__(self, config: AmbiguityConfig, parent_rule=None):
        super().__init__(config, parent_rule)
        
        # High-risk vague action verbs that invite fabrication
        self.vague_action_verbs = {
            'communicate', 'interact', 'process', 'handle', 'manage',
            'work', 'operate', 'function', 'perform', 'execute',
            'coordinate', 'facilitate', 'optimize', 'streamline'
        }
        
        # Incomplete patterns that commonly lead to AI elaboration
        self.incomplete_patterns = [
            r'communicates?\s+with', r'connects?\s+to', r'works?\s+with',
            r'interacts?\s+with', r'processes?\s+the', r'handles?\s+the',
            r'manages?\s+the', r'performs?\s+the', r'executes?\s+the',
            r'coordinates?\s+with', r'facilitates?\s+the', r'optimizes?\s+the'
        ]
        
        # Technical processes prone to over-specification
        self.technical_processes = {
            'backup', 'configuration', 'installation', 'deployment',
            'integration', 'synchronization', 'authentication',
            'authorization', 'validation', 'verification',
            'monitoring', 'logging', 'analysis', 'processing',
            'optimization', 'coordination', 'facilitation'
        }
        
        # Purpose indicators that invite unverified explanations
        self.purpose_indicators = [
            r'for\s+\w+\s+purposes?', r'to\s+ensure', r'to\s+verify',
            r'to\s+confirm', r'to\s+check', r'to\s+validate',
            r'to\s+monitor', r'in\s+order\s+to', r'to\s+optimize',
            r'to\s+facilitate', r'to\s+coordinate'
        ]
        
        # Universal threshold compliance (≥0.35)
        self.confidence_threshold = 0.70  # Stricter for fabrication risks
        
        # Clear indicators that reduce fabrication risk
        self.specific_indicators = {
            'proper_nouns', 'specific_numbers', 'exact_dates', 'precise_quantities',
            'explicit_protocols', 'named_entities', 'concrete_examples'
        }
    
    def detect(self, context: AmbiguityContext, nlp) -> List[AmbiguityDetection]:
        """
        Detect fabrication risks using evidence-based analysis.
        
        Args:
            context: Sentence context for analysis
            nlp: SpaCy nlp object
            
        Returns:
            List of ambiguity detections for fabrication risks
        """
        detections = []
        if not context.sentence.strip():
            return detections
        
        document_context = context.document_context or {}
        block_type = document_context.get('block_type', '').lower()
        
        # Apply zero false positive guards first
        if self._apply_zero_false_positive_guards(context, block_type):
            return detections
        
        try:
            doc = nlp(context.sentence)
            
            # Detect various types of fabrication risks
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
    
    def _apply_zero_false_positive_guards(self, context: AmbiguityContext, block_type: str) -> bool:
        """
        Apply surgical zero false positive guards for fabrication risk detection.
        
        Returns True if the detection should be skipped (no fabrication risk).
        """
        # Guard 1: Technical labels and headings that are naturally brief
        if 'list_item' in block_type or block_type in ['heading', 'section', 'table_cell']:
            if self._is_technical_label(context.sentence):
                return True
        
        # Guard 2: Code blocks and technical identifiers
        if block_type in ['code_block', 'literal_block', 'inline_code']:
            return True
        
        # Guard 3: Very short sentences that are naturally incomplete
        if len(context.sentence.split()) <= 3:
            return True
        
        # Guard 4: Sentences with specific, concrete details
        if self._has_specific_details(context.sentence):
            return True
        
        return False
    
    def _detect_vague_actions(self, doc, context: AmbiguityContext) -> List[AmbiguityDetection]:
        """Detect vague action verbs that invite fabrication."""
        detections = []
        for token in doc:
            # LINGUISTIC ANCHOR: Only flag actual verbs, not nouns
            if token.pos_ == 'VERB' and self._is_vague_action_verb(token):
                # LINGUISTIC ANCHOR 2: Skip gerunds that function as compound noun modifiers
                if self._is_gerund_noun_modifier(token, doc):
                    continue
                    
                evidence_score = self._calculate_fabrication_evidence(token, doc, context)
                if evidence_score >= self.confidence_threshold:
                    detection = self._create_vague_action_detection(token, evidence_score, context)
                    detections.append(detection)
        return detections
    
    def _detect_incomplete_explanations(self, context: AmbiguityContext, doc) -> List[AmbiguityDetection]:
        """Detect incomplete explanations that invite elaboration."""
        detections = []
        sentence_lower = context.sentence.lower()
        for pattern in self.incomplete_patterns:
            for match in re.finditer(pattern, sentence_lower):
                evidence_score = self._calculate_fabrication_evidence_pattern(match.group(), context, doc)
                if evidence_score >= self.confidence_threshold:
                    tokens = match.group().split()
                    detection = self._create_incomplete_explanation_detection(match.group(), tokens, evidence_score, context)
                    detections.append(detection)
        return detections
    
    def _detect_technical_process_risks(self, doc, context: AmbiguityContext) -> List[AmbiguityDetection]:
        """Detect technical processes that could be over-specified."""
        detections = []
        for token in doc:
            if self._is_technical_process(token):
                # LINGUISTIC ANCHOR: Skip gerunds that function as noun modifiers
                if self._is_gerund_noun_modifier(token, doc):
                    continue
                
                # LINGUISTIC ANCHOR: Skip compound technical nouns
                if self._is_compound_technical_noun(token, doc):
                    continue
                    
                evidence_score = self._calculate_fabrication_evidence_process(token, doc, context)
                if evidence_score >= self.confidence_threshold:
                    detection = self._create_technical_process_detection(token, evidence_score, context)
                    detections.append(detection)
        return detections
    
    def _detect_purpose_fabrication_risks(self, context: AmbiguityContext, doc) -> List[AmbiguityDetection]:
        """Detect purpose statements that invite unverified explanations."""
        detections = []
        sentence_lower = context.sentence.lower()
        for pattern in self.purpose_indicators:
            for match in re.finditer(pattern, sentence_lower):
                evidence_score = self._calculate_fabrication_evidence_purpose(match.group(), context, doc)
                if evidence_score >= self.confidence_threshold:
                    tokens = match.group().split()
                    detection = self._create_purpose_fabrication_detection(match.group(), tokens, evidence_score, context)
                    detections.append(detection)
        return detections
    
    def _calculate_fabrication_evidence(self, token, doc, context: AmbiguityContext) -> float:
        """
        Enhanced Level 2 evidence calculation for fabrication risk detection.
        
        Implements evidence-based rule development with:
        - Multi-factor evidence assessment
        - Context-aware domain validation 
        - Universal threshold compliance (≥0.35)
        - Specific criteria for fabrication vs general vagueness
        """
        # Evidence-based base confidence (Level 2 enhancement)
        evidence_score = 0.50  # Starting point for potential fabrication scenarios
        
        # EVIDENCE FACTOR 1: Vagueness Severity Assessment (High Impact)
        if self._is_extremely_vague_verb(token):
            evidence_score += 0.25  # Strong evidence - highly vague actions
        elif self._is_moderately_vague_verb(token):
            evidence_score += 0.15  # Medium evidence - somewhat vague
        
        # EVIDENCE FACTOR 2: Context Specificity Analysis (Critical for Technical Content)
        if self._lacks_clear_object(token, doc):
            evidence_score += 0.20  # High evidence - no clear object increases fabrication risk
        
        # EVIDENCE FACTOR 3: Domain Context Assessment (Domain Knowledge)
        domain_modifier = 0.0
        if context and hasattr(context, 'document_context'):
            doc_context = context.document_context or {}
            content_type = doc_context.get('content_type', '')
            
            if content_type == 'technical':
                domain_modifier += 0.10  # Technical content needs specificity
            elif content_type == 'procedural':
                domain_modifier += 0.15  # Procedures must be specific
            elif content_type == 'marketing':
                domain_modifier -= 0.10  # Marketing allows more vagueness
        
        # EVIDENCE FACTOR 4: Sentence Complexity Analysis (Length vs Detail)
        sentence_complexity_modifier = 0.0
        sentence_length = len(doc)
        if sentence_length < 8:  # Very short sentences
            sentence_complexity_modifier += 0.10  # High evidence - brevity increases risk
        elif sentence_length < 15:  # Medium length
            sentence_complexity_modifier += 0.05  # Medium evidence
        
        # EVIDENCE FACTOR 5: Specificity Indicators (Counter-Evidence)
        specificity_modifier = 0.0
        if self._has_specific_details_nearby(token, doc):
            specificity_modifier -= 0.15  # Counter-evidence - specifics reduce risk
        
        # EVIDENCE FACTOR 6: Linguistic Pattern Strength (Pattern Recognition)
        linguistic_evidence = 0.0
        if token.dep_ in ['ROOT', 'ccomp']:  # Main verb of sentence
            linguistic_evidence += 0.08  # Higher risk when vague verb is central
        elif token.dep_ in ['xcomp', 'advcl']:  # Subordinate clauses
            linguistic_evidence += 0.05  # Medium risk in subordinate position
        
        # EVIDENCE FACTOR 7: Technical Context Validation (Context Awareness)
        technical_modifier = 0.0
        if self._is_technical_context(context):
            technical_modifier += 0.12  # Technical contexts need precision
        
        # EVIDENCE AGGREGATION (Level 2 Multi-Factor Assessment)
        final_evidence = (evidence_score + 
                         domain_modifier + 
                         sentence_complexity_modifier + 
                         specificity_modifier + 
                         linguistic_evidence + 
                         technical_modifier)
        
        # UNIVERSAL THRESHOLD COMPLIANCE (≥0.35 minimum)
        # Cap at 0.95 to leave room for uncertainty
        return min(0.95, max(0.35, final_evidence))
    
    def _calculate_fabrication_evidence_pattern(self, pattern: str, context: AmbiguityContext, doc) -> float:
        """Calculate evidence for incomplete explanation patterns."""
        evidence_score = 0.60  # Base score for incomplete patterns
        
        # High-risk patterns
        if pattern in ['communicates with', 'works with', 'interacts with']:
            evidence_score += 0.20
        
        # Technical context increases risk
        if self._is_technical_context(context):
            evidence_score += 0.15
        
        # Lack of specificity nearby
        if not self._has_specific_details(context.sentence):
            evidence_score += 0.10
        
        return min(0.95, max(0.35, evidence_score))
    
    def _calculate_fabrication_evidence_process(self, token, doc, context: AmbiguityContext) -> float:
        """Calculate evidence for technical process risks."""
        evidence_score = 0.55  # Base score for technical processes
        
        # High-risk processes
        if token.lemma_.lower() in ['backup', 'configuration', 'integration']:
            evidence_score += 0.25
        
        # Lack of process details
        if not self._has_process_details(token, doc):
            evidence_score += 0.15
        
        # Technical context assessment
        if self._is_technical_context(context):
            evidence_score += 0.10
        
        return min(0.95, max(0.35, evidence_score))
    
    def _calculate_fabrication_evidence_purpose(self, pattern: str, context: AmbiguityContext, doc) -> float:
        """Calculate evidence for purpose fabrication risks."""
        evidence_score = 0.65  # Base score for purpose statements
        
        # High-risk purpose patterns
        if pattern in ['to ensure', 'to verify', 'to confirm']:
            evidence_score += 0.15
        
        # Lack of specific purpose details
        if not self._has_specific_purpose_details(context.sentence):
            evidence_score += 0.10
        
        return min(0.95, max(0.35, evidence_score))
    
    # Helper methods
    def _is_extremely_vague_verb(self, token) -> bool:
        """Check if verb is extremely vague and prone to fabrication."""
        extremely_vague = {'handle', 'manage', 'work', 'operate', 'function'}
        return token.lemma_.lower() in extremely_vague
    
    def _is_moderately_vague_verb(self, token) -> bool:
        """Check if verb is moderately vague."""
        moderately_vague = {'process', 'execute', 'perform', 'communicate', 'interact'}
        return token.lemma_.lower() in moderately_vague
    
    def _lacks_clear_object(self, token, doc) -> bool:
        """Check if verb lacks a clear direct object."""
        for child in token.children:
            if child.dep_ in ['dobj', 'pobj'] and not child.is_stop:
                return False
        return True
    
    def _has_specific_details_nearby(self, token, doc) -> bool:
        """Check for specific details near the token."""
        start_idx, end_idx = max(0, token.i - 3), min(len(doc), token.i + 4)
        for i in range(start_idx, end_idx):
            if (doc[i].pos_ in ['PROPN', 'NUM'] or 
                doc[i].like_url or 
                len(doc[i].text) > 8 or
                doc[i].ent_type_ in ['PERSON', 'ORG', 'PRODUCT']):
                return True
        return False
    
    def _has_specific_details(self, sentence: str) -> bool:
        """Check if sentence contains specific, concrete details."""
        # Check for numbers, proper nouns, URLs, specific quantities
        import re
        
        # Specific patterns that indicate concrete details
        specific_patterns = [
            r'\d+',  # Numbers
            r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*',  # Proper nouns
            r'https?://',  # URLs
            r'\b\d+\s*(?:MB|GB|TB|KB|bytes?)\b',  # File sizes
            r'\b\d+\s*(?:ms|seconds?|minutes?|hours?)\b',  # Time units
        ]
        
        return any(re.search(pattern, sentence) for pattern in specific_patterns)
    
    def _has_specific_purpose_details(self, sentence: str) -> bool:
        """Check if purpose statement has specific details."""
        # Look for specific outcomes, metrics, or concrete goals
        specific_purpose_words = [
            'performance', 'security', 'reliability', 'accuracy', 'efficiency',
            'compliance', 'standards', 'requirements', 'specifications'
        ]
        return any(word in sentence.lower() for word in specific_purpose_words)
    
    def _is_vague_action_verb(self, token) -> bool:
        """Check if token is a vague action verb."""
        if not token:
            return False
        return token.lemma_.lower() in self.vague_action_verbs
    
    def _is_technical_process(self, token) -> bool:
        """Check if token represents a technical process."""
        if not token:
            return False
        lemma = token.lemma_.lower()
        text = token.text.lower()
        return lemma in self.technical_processes or text in self.technical_processes
    
    def _has_process_details(self, token, doc) -> bool:
        """Check if technical process has specific details."""
        for child in token.children:
            if child.pos_ in ['NOUN', 'PROPN', 'NUM'] and not child.is_stop:
                return True
        return False
    
    def _is_technical_context(self, context: AmbiguityContext) -> bool:
        """Check if context indicates technical content."""
        technical_keywords = [
            'system', 'server', 'application', 'software', 'service', 
            'database', 'network', 'api', 'configuration', 'deployment',
            'authentication', 'authorization', 'validation', 'monitoring'
        ]
        return any(keyword in context.sentence.lower() for keyword in technical_keywords)
    
    def _is_technical_label(self, text: str) -> bool:
        """Check if text is a technical label that should not be flagged."""
        text_lower = text.lower().strip()
        if len(text.split()) <= 3:
            technical_terms = [
                'deployment', 'code scanning', 'image building', 'vulnerability detection',
                'integration', 'monitoring', 'authentication', 'configuration',
                'backup', 'scaling', 'logging', 'api', 'cli', 'sdk'
            ]
            if text_lower in technical_terms:
                return True
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
        
        # Check for common technical compound patterns
        if (token.i > 0 and token.i < len(doc) - 1):
            prev_token = doc[token.i - 1]
            next_token = doc[token.i + 1]
            
            technical_adjectives = {
                'error', 'data', 'file', 'image', 'user', 'system', 'network',
                'security', 'application', 'database', 'server', 'client',
                'automatic', 'manual', 'real-time', 'batch', 'background'
            }
            
            if (prev_token.lemma_.lower() in technical_adjectives and 
                next_token.pos_ in ('NOUN', 'PROPN')):
                return True
        
        # Check if the gerund has no typical verb arguments
        has_verb_args = any(child.dep_ in ('dobj', 'iobj', 'ccomp', 'xcomp') 
                           for child in token.children)
        
        if not has_verb_args and token.dep_ in ('compound', 'amod', 'acl'):
            return True
        
        return False
    
    def _is_compound_technical_noun(self, token, doc) -> bool:
        """
        Detects compound technical nouns that should not be flagged as fabrication risks.
        Examples: "data processing systems", "network monitoring tools"
        """
        # Check if it's a compound noun
        if token.pos_ != 'NOUN' or token.dep_ != 'compound':
            return False
        
        # Check if it's modifying another noun
        if token.head.pos_ not in ('NOUN', 'PROPN'):
            return False
        
        # Check for technical compound patterns
        if (token.i > 0 and token.i < len(doc) - 1):
            prev_token = doc[token.i - 1]
            next_token = doc[token.i + 1]
            
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
        
        # Check if the compound is clearly a noun phrase
        if token.head.dep_ in ('nsubj', 'dobj', 'pobj'):
            return True
        
        return False
    
    def _create_vague_action_detection(self, token, evidence_score: float, context: AmbiguityContext) -> AmbiguityDetection:
        """Create fabrication risk detection for vague actions."""
        evidence = AmbiguityEvidence(
            tokens=[token.text], 
            linguistic_pattern=f"vague_action_{token.lemma_}", 
            confidence=evidence_score,
            spacy_features={
                'pos': token.pos_, 
                'lemma': token.lemma_, 
                'dep': token.dep_, 
                'has_object': not self._lacks_clear_object(token, token.doc)
            },
            context_clues={'action_type': 'vague_verb', 'fabrication_risk': 'high'}
        )
        
        strategies = [ResolutionStrategy.SPECIFY_REFERENCE, ResolutionStrategy.RESTRUCTURE_SENTENCE]
        
        ai_instructions = [
            f"The verb '{token.text}' is vague and could lead to adding unverified details",
            "Do not add specific purposes, methods, or details that are not in the original text",
            "Keep the action description as general as the original unless specific details are provided",
            "Avoid fabricating steps, processes, or explanations not explicitly stated"
        ]
        
        return AmbiguityDetection(
            ambiguity_type=AmbiguityType.FABRICATION_RISK, 
            category=AmbiguityCategory.SEMANTIC,
            severity=AmbiguitySeverity.CRITICAL, 
            context=context, 
            evidence=evidence,
            resolution_strategies=strategies, 
            ai_instructions=ai_instructions,
            span=(token.idx, token.idx + len(token.text)),
            flagged_text=token.text
        )
    
    def _create_incomplete_explanation_detection(self, pattern: str, tokens: List[str], evidence_score: float, context: AmbiguityContext) -> AmbiguityDetection:
        """Create fabrication risk detection for incomplete explanations."""
        evidence = AmbiguityEvidence(
            tokens=tokens, 
            linguistic_pattern=f"incomplete_explanation_{pattern.replace(' ', '_')}",
            confidence=evidence_score, 
            spacy_features={'pattern_type': 'incomplete'}, 
            context_clues={'pattern': pattern, 'fabrication_risk': 'high'}
        )
        
        strategies = [ResolutionStrategy.SPECIFY_REFERENCE, ResolutionStrategy.ADD_CONTEXT]
        
        ai_instructions = [
            f"The phrase '{pattern}' is incomplete and could invite adding unverified details",
            "Do not add specific purposes, methods, or explanations not in the original text",
            "Preserve the level of detail from the original text",
            "Avoid fabricating connections, relationships, or processes not explicitly stated"
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
    
    def _create_technical_process_detection(self, token, evidence_score: float, context: AmbiguityContext) -> AmbiguityDetection:
        """Create fabrication risk detection for technical processes."""
        evidence = AmbiguityEvidence(
            tokens=[token.text], 
            linguistic_pattern=f"technical_process_{token.lemma_}",
            confidence=evidence_score, 
            spacy_features={
                'pos': token.pos_, 
                'lemma': token.lemma_, 
                'process_type': 'technical'
            },
            context_clues={'process': token.text, 'fabrication_risk': 'high'}
        )
        
        strategies = [ResolutionStrategy.SPECIFY_REFERENCE, ResolutionStrategy.RESTRUCTURE_SENTENCE]
        
        ai_instructions = [
            f"The technical process '{token.text}' could be over-specified with unverified details",
            "Do not add specific steps, parameters, or configurations not in the original text",
            "Keep technical descriptions as general as the original unless specifics are provided",
            "Avoid fabricating technical procedures, settings, or implementation details"
        ]
        
        return AmbiguityDetection(
            ambiguity_type=AmbiguityType.FABRICATION_RISK, 
            category=AmbiguityCategory.SEMANTIC,
            severity=AmbiguitySeverity.CRITICAL, 
            context=context, 
            evidence=evidence,
            resolution_strategies=strategies, 
            ai_instructions=ai_instructions,
            span=(token.idx, token.idx + len(token.text)),
            flagged_text=token.text
        )
    
    def _create_purpose_fabrication_detection(self, pattern: str, tokens: List[str], evidence_score: float, context: AmbiguityContext) -> AmbiguityDetection:
        """Create fabrication risk detection for purpose statements."""
        evidence = AmbiguityEvidence(
            tokens=tokens, 
            linguistic_pattern=f"purpose_statement_{pattern.replace(' ', '_')}",
            confidence=evidence_score, 
            spacy_features={'pattern_type': 'purpose'}, 
            context_clues={'pattern': pattern, 'fabrication_risk': 'high'}
        )
        
        strategies = [ResolutionStrategy.SPECIFY_REFERENCE, ResolutionStrategy.RESTRUCTURE_SENTENCE]
        
        ai_instructions = [
            f"The purpose statement '{pattern}' could invite adding unverified explanations",
            "Do not add specific purposes or reasons not explicitly stated in the original text",
            "Keep purpose statements as general as the original unless specific purposes are provided",
            "Avoid fabricating motivations, goals, or objectives not explicitly mentioned"
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