"""
Unsupported Claims Detector

Detects unsupported claims and promises by analyzing words in their
linguistic context, using evidence-based analysis to avoid false positives.

This detector is fully compatible with Level 2 Enhanced Validation, Evidence-Based 
Rule Development, and Universal Confidence Threshold architecture. It provides
sophisticated 7-factor evidence scoring for unsupported claims assessment.

Architecture compliance:
- confidence.md: Universal threshold (≥0.35), normalized confidence
- evidence_based_rule_development.md: Multi-factor evidence assessment  
- level_2_implementation.adoc: Enhanced validation integration
"""

from typing import List, Dict, Any, Optional
from ..base_ambiguity_rule import AmbiguityDetector
from ..types import (
    AmbiguityType, AmbiguityCategory, AmbiguitySeverity,
    AmbiguityContext, AmbiguityEvidence, AmbiguityDetection,
    ResolutionStrategy, AmbiguityConfig
)

class UnsupportedClaimsDetector(AmbiguityDetector):
    """
    Detects unsupported claims and promises using evidence-based analysis.
    
    This detector is fully compatible with Level 2 Enhanced Validation, Evidence-Based 
    Rule Development, and Universal Confidence Threshold architecture. It provides
    sophisticated 7-factor evidence scoring for unsupported claims assessment.
    
    Architecture compliance:
    - confidence.md: Universal threshold (≥0.35), normalized confidence
    - evidence_based_rule_development.md: Multi-factor evidence assessment  
    - level_2_implementation.adoc: Enhanced validation integration
    """
    
    def __init__(self, config: AmbiguityConfig, parent_rule):
        super().__init__(config, parent_rule)
        
        # Strong claim words that are almost always problematic
        self.strong_claim_words = {
            'guarantee', 'always', 'never', 'impossible', 'perfect', 
            'flawless', 'foolproof', 'infallible', 'bulletproof'
        }
        
        # Contextual claim words that need evidence-based analysis
        self.contextual_claim_words = {
            'ensure', 'will', 'must', 'easy', 'secure', 'full', 'every', 
            'best', 'effortless', 'future-proof', 'seamless', 'optimal',
            'comprehensive', 'complete', 'ultimate', 'superior'
        }
        
        # Promise indicators that suggest guarantees
        self.promise_indicators = {
            'guarantee', 'promise', 'assure', 'certify', 'warrant',
            'pledge', 'commit', 'vow', 'swear', 'affirm'
        }
        
        # Universal threshold compliance (≥0.35)
        self.confidence_threshold = 0.70  # Stricter for unsupported claims
        
        # Supporting evidence patterns that reduce claim risk
        self.supporting_evidence_patterns = {
            'testing', 'verified', 'proven', 'demonstrated', 'measured',
            'benchmarked', 'validated', 'certified', 'standards'
        }

    def detect(self, context: AmbiguityContext, nlp) -> List[AmbiguityDetection]:
        """
        Detect unsupported claims using evidence-based analysis.
        
        Args:
            context: Sentence context for analysis
            nlp: SpaCy nlp object
            
        Returns:
            List of ambiguity detections for unsupported claims
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
                word_lemma = token.lemma_.lower()
                
                # Check for strong claims
                if word_lemma in self.strong_claim_words:
                    evidence_score = self._calculate_claims_evidence(token, doc, context, 'strong')
                    if evidence_score >= self.confidence_threshold:
                        detection = self._create_claims_detection(token, evidence_score, context, 'strong')
                        detections.append(detection)

                # Check for contextual claims
                elif word_lemma in self.contextual_claim_words:
                    evidence_score = self._calculate_claims_evidence(token, doc, context, 'contextual')
                    if evidence_score >= self.confidence_threshold:
                        detection = self._create_claims_detection(token, evidence_score, context, 'contextual')
                        detections.append(detection)
                
                # Check for promise indicators
                elif word_lemma in self.promise_indicators:
                    evidence_score = self._calculate_claims_evidence(token, doc, context, 'promise')
                    if evidence_score >= self.confidence_threshold:
                        detection = self._create_claims_detection(token, evidence_score, context, 'promise')
                        detections.append(detection)

        except Exception as e:
            print(f"Error in unsupported claims detection: {e}")
        
        return detections
    
    def _apply_zero_false_positive_guards(self, context: AmbiguityContext) -> bool:
        """
        Apply surgical zero false positive guards for unsupported claims detection.
        
        Returns True if the detection should be skipped (no unsupported claims risk).
        """
        document_context = context.document_context or {}
        block_type = document_context.get('block_type', '').lower()
        
        # Guard 1: Code blocks and technical identifiers
        if block_type in ['code_block', 'literal_block', 'inline_code']:
            return True
        
        # Guard 2: Marketing content where claims are expected
        content_type = document_context.get('content_type', '')
        if content_type == 'marketing':
            return True
        
        # Guard 3: Quoted content or testimonials
        if block_type in ['quote', 'testimonial', 'citation']:
            return True
        
        # Guard 4: Legal disclaimers where absolute language is appropriate
        if any(word in context.sentence.lower() for word in ['disclaimer', 'warranty', 'liability']):
            return True
        
        return False
    
    def _calculate_claims_evidence(self, token, doc, context: AmbiguityContext, claim_type: str) -> float:
        """
        Enhanced Level 2 evidence calculation for unsupported claims detection.
        
        Implements evidence-based rule development with:
        - Multi-factor evidence assessment
        - Context-aware domain validation 
        - Universal threshold compliance (≥0.35)
        - Specific criteria for claims vs legitimate statements
        """
        # Evidence-based base confidence (Level 2 enhancement)
        if claim_type == 'strong':
            evidence_score = 0.80  # Strong claims start high
        elif claim_type == 'promise':
            evidence_score = 0.75  # Promises are concerning
        else:  # contextual
            evidence_score = 0.55  # Contextual claims need more evidence
        
        # EVIDENCE FACTOR 1: Claim Severity Assessment (High Impact)
        if self._is_absolute_claim(token):
            evidence_score += 0.20  # Strong evidence - absolute claims problematic
        elif self._is_subjective_claim(token):
            evidence_score += 0.15  # Medium evidence - subjective claims
        
        # EVIDENCE FACTOR 2: Supporting Evidence Analysis (Critical Counter-Evidence)
        if self._has_supporting_evidence_nearby(token, doc):
            evidence_score -= 0.25  # Strong counter-evidence - claims with support
        elif self._has_qualifying_language(token, doc):
            evidence_score -= 0.15  # Medium counter-evidence - qualified statements
        
        # EVIDENCE FACTOR 3: Domain Context Assessment (Domain Knowledge)
        domain_modifier = 0.0
        if context and hasattr(context, 'document_context'):
            doc_context = context.document_context or {}
            content_type = doc_context.get('content_type', '')
            
            if content_type == 'technical':
                domain_modifier += 0.10  # Technical docs should be precise
            elif content_type == 'legal':
                domain_modifier -= 0.10  # Legal docs may use absolute language
            elif content_type == 'academic':
                domain_modifier += 0.05  # Academic writing should be measured
        
        # EVIDENCE FACTOR 4: Linguistic Context Analysis (Grammatical Role)
        linguistic_modifier = 0.0
        if token.dep_ == 'amod':  # Adjectival modifier
            linguistic_modifier += 0.10  # "perfect solution" - modifying claims
        elif token.dep_ == 'ROOT':  # Main verb
            linguistic_modifier += 0.15  # "This guarantees..." - strong assertion
        elif token.dep_ in ['aux', 'auxpass']:  # Auxiliary verb
            linguistic_modifier += 0.05  # "will always work" - future certainty
        
        # EVIDENCE FACTOR 5: Sentence Position Analysis (Emphasis Assessment)
        position_modifier = 0.0
        if token.i == 0:  # Sentence start
            position_modifier += 0.08  # "Always check..." - emphatic position
        elif token.i == len(doc) - 1:  # Sentence end
            position_modifier += 0.05  # "...is perfect." - concluding claim
        
        # EVIDENCE FACTOR 6: Scope Indicators (Universality Assessment)
        scope_modifier = 0.0
        if self._has_universal_scope_indicators(token, doc):
            scope_modifier += 0.12  # "All users will..." - universal claims
        elif self._has_limited_scope_indicators(token, doc):
            scope_modifier -= 0.08  # "Some users may..." - limited claims
        
        # EVIDENCE FACTOR 7: Documentation Type Validation (Context Awareness)
        doc_type_modifier = 0.0
        if self._is_instruction_context(context):
            doc_type_modifier -= 0.05  # Instructions may use directive language
        elif self._is_specification_context(context):
            doc_type_modifier += 0.08  # Specifications should be precise
        
        # EVIDENCE AGGREGATION (Level 2 Multi-Factor Assessment)
        final_evidence = (evidence_score + 
                         domain_modifier + 
                         linguistic_modifier + 
                         position_modifier + 
                         scope_modifier + 
                         doc_type_modifier)
        
        # UNIVERSAL THRESHOLD COMPLIANCE (≥0.35 minimum)
        # Cap at 0.95 to leave room for uncertainty
        return min(0.95, max(0.35, final_evidence))
    
    # Evidence factor helper methods
    def _is_absolute_claim(self, token) -> bool:
        """Check if token represents an absolute claim."""
        absolute_words = {'always', 'never', 'impossible', 'perfect', 'guarantee', 'infallible'}
        return token.lemma_.lower() in absolute_words
    
    def _is_subjective_claim(self, token) -> bool:
        """Check if token represents a subjective claim."""
        subjective_words = {'best', 'optimal', 'superior', 'ultimate', 'ideal'}
        return token.lemma_.lower() in subjective_words
    
    def _has_supporting_evidence_nearby(self, token, doc) -> bool:
        """Check for supporting evidence near the claim."""
        # Look for evidence words within a window around the token
        start_idx, end_idx = max(0, token.i - 5), min(len(doc), token.i + 6)
        for i in range(start_idx, end_idx):
            if doc[i].lemma_.lower() in self.supporting_evidence_patterns:
                return True
        
        # Look for specific metrics or numbers
        for i in range(start_idx, end_idx):
            if doc[i].pos_ == 'NUM' or doc[i].like_num:
                return True
        
        return False
    
    def _has_qualifying_language(self, token, doc) -> bool:
        """Check for qualifying language that reduces claim strength."""
        qualifying_words = {
            'typically', 'generally', 'usually', 'often', 'may', 'might', 
            'can', 'could', 'should', 'likely', 'probably', 'designed to'
        }
        
        # Look for qualifiers in the sentence
        for t in doc:
            if t.lemma_.lower() in qualifying_words:
                return True
        
        return False
    
    def _has_universal_scope_indicators(self, token, doc) -> bool:
        """Check for indicators of universal scope."""
        universal_words = {'all', 'every', 'any', 'everyone', 'everything', 'anybody'}
        
        # Look for universal quantifiers nearby
        start_idx, end_idx = max(0, token.i - 3), min(len(doc), token.i + 4)
        for i in range(start_idx, end_idx):
            if doc[i].lemma_.lower() in universal_words:
                return True
        
        return False
    
    def _has_limited_scope_indicators(self, token, doc) -> bool:
        """Check for indicators of limited scope."""
        limited_words = {'some', 'many', 'most', 'certain', 'specific', 'particular'}
        
        # Look for limiting quantifiers nearby
        start_idx, end_idx = max(0, token.i - 3), min(len(doc), token.i + 4)
        for i in range(start_idx, end_idx):
            if doc[i].lemma_.lower() in limited_words:
                return True
        
        return False
    
    def _is_instruction_context(self, context: AmbiguityContext) -> bool:
        """Check if context indicates instructional content."""
        document_context = context.document_context or {}
        
        # Check content type
        if document_context.get('content_type') == 'procedural':
            return True
        
        # Check block type
        if document_context.get('block_type') in ['ordered_list_item', 'unordered_list_item']:
            return True
        
        # Check for instructional language
        instruction_indicators = ['step', 'click', 'select', 'configure', 'install']
        return any(word in context.sentence.lower() for word in instruction_indicators)
    
    def _is_specification_context(self, context: AmbiguityContext) -> bool:
        """Check if context indicates specification content."""
        document_context = context.document_context or {}
        
        # Check for specification indicators
        spec_indicators = ['specification', 'requirement', 'standard', 'protocol']
        return any(word in context.sentence.lower() for word in spec_indicators)
    
    # Legacy compatibility methods (refactored for evidence-based approach)
    def _is_excepted(self, text: str) -> bool:
        """Check if text is in exception list (legacy compatibility)."""
        # This can be implemented to check against exception lists if needed
        return False
    
    def _is_part_of_excepted_phrase(self, token) -> bool:
        """Check for excepted phrases (legacy compatibility)."""
        # This can be implemented to check phrase exceptions if needed
        return False
    
    def _is_problematic_claim_context(self, token, doc) -> bool:
        """
        Legacy method refactored to use evidence-based approach.
        Now delegates to the main evidence calculation.
        """
        # Use the evidence-based calculation instead of hardcoded rules
        context = AmbiguityContext(
            sentence=doc.text,
            sentence_index=0,
            document_context={}
        )
        evidence_score = self._calculate_claims_evidence(token, doc, context, 'contextual')
        return evidence_score >= self.confidence_threshold
    
    def _create_claims_detection(self, token, evidence_score: float, context: AmbiguityContext, claim_type: str) -> AmbiguityDetection:
        """Create unsupported claims detection with evidence-based confidence."""
        suggestions = self._generate_contextual_suggestions(token, token.sent, evidence_score)
        
        evidence = AmbiguityEvidence(
            tokens=[token.text],
            linguistic_pattern=f"unsupported_claim_{claim_type}_{token.lemma_}",
            confidence=evidence_score,
            spacy_features={
                'pos': token.pos_,
                'lemma': token.lemma_,
                'dep': token.dep_,
                'claim_type': claim_type
            },
            context_clues={
                'claim_type': claim_type,
                'has_support': self._has_supporting_evidence_nearby(token, token.doc),
                'has_qualifiers': self._has_qualifying_language(token, token.doc)
            }
        )
        
        # Determine severity based on evidence score
        if evidence_score > 0.85:
            severity = AmbiguitySeverity.CRITICAL
        elif evidence_score > 0.70:
            severity = AmbiguitySeverity.HIGH
        else:
            severity = AmbiguitySeverity.MEDIUM
        
        ai_instructions = self._generate_ai_instructions(token, claim_type, evidence_score)
        
        return AmbiguityDetection(
            ambiguity_type=AmbiguityType.UNSUPPORTED_CLAIMS,
            category=AmbiguityCategory.SEMANTIC,
            severity=severity,
            context=context,
            evidence=evidence,
            resolution_strategies=[ResolutionStrategy.SPECIFY_REFERENCE, ResolutionStrategy.ADD_CONTEXT],
            ai_instructions=ai_instructions,
            span=(token.idx, token.idx + len(token.text)),
            flagged_text=token.text
        )
    
    def _create_detection(self, token, confidence: float, context: AmbiguityContext) -> AmbiguityDetection:
        """Legacy method - delegates to evidence-based approach."""
        # Determine claim type based on token
        if token.lemma_.lower() in self.strong_claim_words:
            claim_type = 'strong'
        elif token.lemma_.lower() in self.promise_indicators:
            claim_type = 'promise'
        else:
            claim_type = 'contextual'
        
        return self._create_claims_detection(token, confidence, context, claim_type)

    def _generate_contextual_suggestions(self, token, sentence, evidence_score: float) -> List[str]:
        """
        Generate evidence-aware contextual suggestions.
        Higher evidence = more direct suggestions.
        Lower evidence = gentler suggestions.
        """
        word = token.lemma_.lower()
        suggestions = []

        # Evidence-aware suggestion strength
        if evidence_score > 0.85:
            # High confidence - direct, authoritative suggestions
            if word == "easy":
                suggestions.append("Replace 'easy' immediately - this makes an unsupported claim about user experience.")
                suggestions.append("Use specific, measurable descriptions instead.")
            elif word == "secure":
                suggestions.append("Replace 'secure' with specific security features or certifications.")
            elif word == "guarantee":
                suggestions.append("Remove 'guarantee' - this creates legal liability and unsupported promises.")
            elif word == "always":
                suggestions.append("Replace 'always' with 'typically' or 'generally' for accuracy.")
            
        elif evidence_score > 0.70:
            # Medium confidence - balanced suggestions
            if word == "easy":
                suggestions.append("Consider replacing 'easy' with 'straightforward' or 'simple'.")
                suggestions.append("Better: describe why it's easy (e.g., 'uses a guided setup').")
            elif word == "secure":
                suggestions.append("Consider 'security-enhanced' or specify the security feature.")
            elif word == "best":
                suggestions.append("Replace 'best' with 'recommended' or 'standard'.")
            elif word == "ensure":
                suggestions.append("Use 'ensure' carefully. Consider 'helps to ensure' or 'is designed to'.")
                
        else:
            # Lower confidence - gentle suggestions
            if word == "easy":
                suggestions.append("'Easy' may be acceptable here, but consider if it's verifiable.")
            elif word == "will":
                suggestions.append("'Will' suggests certainty - consider 'can' or 'may' if uncertain.")
            elif word == "full":
                suggestions.append("Consider if 'full' is measurable or if 'comprehensive' is more accurate.")
        
        # Add context-specific suggestions
        if any(t.lemma_ in ["process", "step"] for t in sentence):
            suggestions.append("For processes, describe specific steps rather than making claims about difficulty.")
        
        if not suggestions:
            if evidence_score > 0.80:
                suggestions.append(f"Replace '{token.text}' with a specific, verifiable description.")
            else:
                suggestions.append(f"Consider if '{token.text}' can be supported with evidence or made more specific.")
            
        return suggestions
    
    def _generate_ai_instructions(self, token, claim_type: str, evidence_score: float) -> List[str]:
        """Generate AI instructions for handling unsupported claims."""
        instructions = []
        
        # Base instruction
        instructions.append(
            f"The word '{token.text}' represents an unsupported claim that cannot be verified."
        )
        
        # Claim-type specific instructions
        if claim_type == 'strong':
            instructions.append("This is a strong absolute claim that should be avoided in professional documentation.")
            instructions.append("Replace with specific, measurable, and verifiable statements.")
        elif claim_type == 'promise':
            instructions.append("This creates a promise or guarantee that may not be supportable.")
            instructions.append("Use language that describes capabilities without making guarantees.")
        else:  # contextual
            instructions.append("This claim needs supporting evidence or qualification to be appropriate.")
            instructions.append("Add qualifiers like 'typically', 'often', or 'designed to' for accuracy.")
        
        # Evidence-based instructions
        if evidence_score > 0.85:
            instructions.append("High confidence: This should definitely be revised for professional accuracy.")
        elif evidence_score > 0.70:
            instructions.append("Moderate confidence: Consider revision unless supporting evidence is available.")
        
        # General guidance
        instructions.append("Focus on describing what the product/service does rather than making claims about outcomes.")
        instructions.append("Use specific, objective language that can be verified or measured.")
        
        return instructions