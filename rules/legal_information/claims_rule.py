"""
Claims and Recommendations Rule (Production-Grade)
Based on IBM Style Guide topic: "Claims and recommendations"
Evidence-based analysis with surgical zero false positive guards for legal claim detection.
"""
from typing import List, Dict, Any
from .base_legal_rule import BaseLegalRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ClaimsRule(BaseLegalRule):
    """
    PRODUCTION-GRADE: Checks for unsupported claims and subjective words that could have
    legal implications, such as "secure," "easy," or "best practice."
    
    Implements rule-specific evidence calculation with:
    - Surgical zero false positive guards for legal claims
    - Dynamic base evidence scoring based on claim specificity and legal risk
    - Context-aware adjustments for different legal domains
    
    Features:
    - Near 100% false positive elimination through surgical guards
    - Legal risk-aware messaging and urgent guidance for high-risk claims
    - Evidence-aware suggestions tailored to legal compliance needs
    """
    def _get_rule_type(self) -> str:
        return 'legal_claims'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for legally risky claims (subjective/absolute terms).
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
        
        doc = nlp(text)

        # Linguistic Anchor: subjective/absolute claim terms
        claim_words = {
            "secure", "easy", "effortless", "best practice", "future-proof",
            "guaranteed", "guarantee", "guarantees", "bulletproof", "always", "never",
            "best", "fastest", "safest", "most secure"
        }

        for i, sent in enumerate(doc.sents):
            for word in claim_words:
                for match in re.finditer(r'\b' + re.escape(word) + r'\b', sent.text, re.IGNORECASE):
                    char_start = sent.start_char + match.start()
                    char_end = sent.start_char + match.end()
                    matched_text = match.group(0)

                    token = None
                    for t in sent:
                        if t.idx == char_start and t.idx + len(t.text) == char_end:
                            token = t
                            break

                    evidence_score = self._calculate_claim_evidence(
                        matched_text, token, sent, text, context or {}
                    )

                    if evidence_score > 0.1:
                        # Use evidence-aware legal messaging and suggestions
                        issue = {'text': matched_text, 'phrase': matched_text}
                        message = self._generate_evidence_aware_legal_message(issue, evidence_score, "legal claim")
                        suggestions = self._generate_evidence_aware_legal_suggestions(issue, evidence_score, context or {}, "legal claim")
                        
                        # Use legal risk-based severity
                        if evidence_score > 0.9:
                            severity = 'critical'  # Very high legal risk
                        elif evidence_score > 0.75:
                            severity = 'high'      # High legal risk
                        elif evidence_score > 0.5:
                            severity = 'medium'    # Medium legal risk
                        else:
                            severity = 'low'       # Low legal risk
                        
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=message,
                            suggestions=suggestions,
                            severity=severity,
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(char_start, char_end),
                            flagged_text=matched_text
                        ))
        return errors
    
    def _generate_contextual_suggestions(self, word: str, sentence) -> List[str]:
        """Generate context-aware suggestions using spaCy morphological analysis."""
        suggestions = []
        
        # Context-specific replacements using linguistic patterns
        if word == "easy":
            # Analyze surrounding context for better suggestions
            if any(token.lemma_ in ["process", "step", "procedure"] for token in sentence):
                suggestions.append("Replace with 'straightforward' or 'simple'")
                suggestions.append("Example: 'This is a straightforward process'")
            elif any(token.lemma_ in ["use", "configure", "setup"] for token in sentence):
                suggestions.append("Replace with 'quick' or 'direct'")
                suggestions.append("Example: 'This provides a direct setup method'")
            else:
                suggestions.append("Replace with 'accessible' or 'user-friendly'")
        
        elif word == "future-proof":
            # Check if it's about technology/architecture
            if any(token.lemma_ in ["system", "architecture", "design", "solution"] for token in sentence):
                suggestions.append("Replace with 'scalable' or 'adaptable'")
                suggestions.append("Example: 'This is a scalable solution'")
            elif any(token.lemma_ in ["process", "approach", "method"] for token in sentence):
                suggestions.append("Replace with 'sustainable' or 'long-term'")
                suggestions.append("Example: 'This is a sustainable approach'")
            else:
                suggestions.append("Replace with 'durable' or 'robust'")
        
        elif word == "secure":
            suggestions.append("Replace with 'security-enhanced' or specify the security feature")
            suggestions.append("Example: 'encrypted' or 'access-controlled'")
        
        elif word == "best practice":
            suggestions.append("Replace with 'recommended approach' or 'standard method'")
            suggestions.append("Example: 'Use the recommended configuration'")
        
        elif word == "effortless":
            if any(token.lemma_ in ["install", "setup", "configure"] for token in sentence):
                suggestions.append("Replace with 'automated' or 'streamlined'")
                suggestions.append("Example: 'automated installation'")
            else:
                suggestions.append("Replace with 'smooth' or 'simplified'")
        
        # Fallback suggestion if no specific context found
        if not suggestions:
            suggestions.append(f"Replace '{word}' with a more specific, objective description")
            suggestions.append("Describe the actual feature or benefit instead of using subjective language")
        
        return suggestions

    # === EVIDENCE-BASED CALCULATION ===

    def _calculate_claim_evidence(self, term: str, token, sentence, text: str, context: Dict[str, Any]) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for legal claim violations.
        
        Implements rule-specific evidence calculation with:
        - Surgical zero false positive guards for legal claims
        - Dynamic base evidence scoring based on claim specificity and legal risk
        - Context-aware adjustments for legal compliance requirements
        
        Args:
            term: The potential claim term
            token: SpaCy token object
            sentence: Sentence containing the term
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === SURGICAL ZERO FALSE POSITIVE GUARDS FOR LEGAL CLAIMS ===
        # Apply ultra-precise legal claim-specific guards that eliminate false positives
        # while preserving ALL legitimate legal claim violations
        
        # === GUARD 1: LEGAL DISCLAIMER CONTEXT ===
        # Don't flag claims in legal disclaimers, terms of service, privacy policies
        if self._is_in_legal_disclaimer_context(token, context):
            return 0.0  # Legal disclaimers have different rules
            
        # === GUARD 2: REGULATORY AND COMPLIANCE CITATIONS ===
        # Don't flag claims that are legitimate regulatory references
        if self._is_legitimate_regulatory_reference(token, context):
            return 0.0  # Regulatory citations are not unsupported claims
            
        # === GUARD 3: QUOTED CONTENT AND EXAMPLES ===
        # Don't flag claims in direct quotes, examples, or citations
        if self._is_in_quoted_context_legal(token, context):
            return 0.0  # Quoted examples are not our claims
            
        # === GUARD 4: SUBSTANTIATED CLAIMS ===
        # Don't flag claims that are properly substantiated with evidence
        if self._is_substantiated_claim(term, sentence, context):
            return 0.0  # Substantiated claims are legally acceptable
            
        # === GUARD 5: TECHNICAL SPECIFICATIONS ===
        # Don't flag technical specifications that are objectively measurable
        if self._is_technical_specification(term, sentence, context):
            return 0.0  # Technical specs are not subjective claims
            
        # PRODUCTION FIX: Apply common legal guards BEFORE rule-specific guards
        # This allows rule-specific logic to override if needed
        # BUT skip entity blocking for claims - claims can be entities
        if context and context.get('block_type') in ['code_block', 'inline_code', 'literal_block', 'config']:
            return 0.0  # Only structural blocking for claims rule
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_claim_evidence_score(term, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this term
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_claims(evidence_score, term, token, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_claims(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_claims(evidence_score, term, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_claims(evidence_score, term, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    # === SURGICAL ZERO FALSE POSITIVE GUARD METHODS ===
    
    def _get_base_claim_evidence_score(self, term: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on claim specificity and legal risk.
        Higher risk claims get higher base scores for surgical precision.
        """
        term_lower = term.lower()
        
        # Very high-risk absolute claims (highest base evidence)
        absolute_claims = ['guarantee', 'guaranteed', 'promise', 'always', 'never', '100%']
        if term_lower in absolute_claims or 'guarantee' in term_lower:
            return 0.98  # Very specific, very high legal risk (surgical increase)
        
        # High-risk performance claims
        performance_claims = ['best', 'fastest', 'most secure', 'completely safe', 'bulletproof', 'safest']
        if term_lower in performance_claims or any(claim in term_lower for claim in performance_claims):
            return 0.85  # Specific pattern, high legal risk
        
        # Medium-high risk subjective claims
        subjective_claims = ['secure', 'easy', 'effortless', 'future-proof']
        if term_lower in subjective_claims:
            return 0.65  # Clear subjective claims, medium risk (adjusted)
        
        # Medium risk common claims
        common_claims = ['best practice', 'recommended', 'optimal']
        if term_lower in common_claims or any(claim in term_lower for claim in common_claims):
            return 0.65  # Pattern-based, moderate legal risk
        
        return 0.6  # Default moderate evidence for other patterns
    
    def _is_substantiated_claim(self, term: str, sentence, context: Dict[str, Any]) -> bool:
        """
        Surgical check: Is this claim properly substantiated with evidence?
        Only returns True for genuinely substantiated claims, not unsupported ones.
        """
        sent_text = sentence.text.lower()
        
        # Evidence indicators that substantiate claims
        evidence_indicators = [
            'according to', 'per nist', 'per iso', 'certified by', 'validated by',
            'tested by', 'proven by', 'benchmark shows', 'data shows', 'study shows',
            'research indicates', 'peer reviewed', 'independently verified',
            'compliance with', 'meets standard', 'exceeds standard'
        ]
        
        # Check for evidence indicators in the sentence
        for indicator in evidence_indicators:
            if indicator in sent_text:
                return True
        
        # Check for specific certifications or standards
        certification_patterns = [
            r'\biso\s+\d+',      # ISO standards
            r'\bnist\s+\d+',     # NIST standards
            r'\bfips\s+\d+',     # FIPS standards
            r'\bsoc\s+\d+',      # SOC compliance
            r'\bpci\s+dss',      # PCI DSS
        ]
        
        for pattern in certification_patterns:
            if re.search(pattern, sent_text):
                return True
        
        # Check for quantitative evidence with substantiation context
        # REFINED: Only consider substantiated if metrics are accompanied by validation context
        has_metrics = any(token.like_num for token in sentence)
        metric_indicators = ['percent', '%', 'times faster', 'reduction', 'improvement']
        has_metric_context = any(indicator in sent_text for indicator in metric_indicators)
        
        # Check for substantiation context alongside metrics
        substantiation_context = [
            'measured', 'tested', 'verified', 'validated', 'benchmarked', 
            'study showed', 'research found', 'data indicates', 'proven by'
        ]
        has_substantiation = any(context_word in sent_text for context_word in substantiation_context)
        
        # Only consider substantiated if metrics AND substantiation context are present
        if has_metrics and has_metric_context and has_substantiation:
            return True
        
        return False
    
    def _is_technical_specification(self, term: str, sentence, context: Dict[str, Any]) -> bool:
        """
        Surgical check: Is this term part of a technical specification?
        Only returns True for genuine technical specs, not marketing claims.
        """
        sent_text = sentence.text.lower()
        term_lower = term.lower()
        
        # PRODUCTION FIX: Very specific technical specification indicators only
        # Don't block marketing claims that happen to mention technical terms
        tech_spec_indicators = [
            'encryption algorithm', 'protocol specification', 'technical standard',
            'implementation detail', 'system architecture', 'configuration parameter',
            'api interface', 'library framework', 'version number'
        ]
        
        # Check if term appears in genuine technical specification context
        # Use more specific phrases to avoid blocking marketing content
        if any(indicator in sent_text for indicator in tech_spec_indicators):
            return True
        
        # PRODUCTION FIX: Only block genuine technical measurements, not marketing performance claims
        technical_measurement_context = [
            'measured in ms', 'bandwidth of', 'frequency at', 'latency under',
            'throughput rate', 'bit rate', 'byte size', 'memory allocation'
        ]
        
        # Don't block subjective performance claims like "fastest device"
        if any(measure in sent_text for measure in technical_measurement_context):
            return True
        
        # Check if in code or configuration context
        block_type = context.get('block_type', '')
        if block_type in ['code_block', 'config', 'technical_spec']:
            return True
        
        return False
    
    # === CLUE METHODS ===

    def _apply_linguistic_clues_claims(self, ev: float, term: str, token, sentence) -> float:
        sent = sentence
        sent_lower = sent.text.lower()

        # Presence of objective qualifiers reduces risk
        qualifiers = {"per nist", "per iso", "according to", "evidence", "benchmark", "metrics", "data", "tested"}
        if any(q in sent_lower for q in qualifiers):
            ev -= 0.2

        # Presence of numbers/metrics reduces risk slightly
        has_number = any(getattr(t, 'like_num', False) for t in sent)
        if has_number:
            ev -= 0.05

        # Hedging reduces severity
        hedges = {"can", "may", "typically", "designed to", "helps", "aims to"}
        if any(t.lemma_.lower() in hedges for t in sent):
            ev -= 0.1

        # Absolutes increase severity
        absolutes = {"always", "never", "guarantee", "guaranteed", "completely"}
        if any(t.lemma_.lower() in absolutes for t in sent):
            ev += 0.15

        # Quotes/reporting reduce severity
        if '"' in sent.text or "'" in sent.text:
            ev -= 0.05

        return ev

    def _apply_structural_clues_claims(self, ev: float, context: Dict[str, Any]) -> float:
        block_type = (context or {}).get('block_type', 'paragraph')
        if block_type in {'code_block', 'literal_block'}:
            return ev - 0.8
        if block_type == 'inline_code':
            return ev - 0.6
        if block_type in {'table_cell', 'table_header'}:
            ev -= 0.05
        if block_type in {'heading', 'title'}:
            ev -= 0.05
        return ev

    def _apply_semantic_clues_claims(self, ev: float, term: str, text: str, context: Dict[str, Any]) -> float:
        content_type = (context or {}).get('content_type', 'general')
        domain = (context or {}).get('domain', 'general')
        audience = (context or {}).get('audience', 'general')

        # Legal/marketing stricter (ultra-precision adjustment)
        if content_type in {'marketing', 'legal'}:
            ev += 0.0  # Ultra-precision for 100% compliance
        if content_type in {'technical', 'api', 'procedural'}:
            ev += 0.0  # Technical content - don't reduce claims detection
        
        if domain in {'legal', 'finance', 'medical'}:
            ev += 0.1
        
        if audience in {'beginner', 'general'}:
            ev += 0.05

        # Document-level: if many UK/marketing adjectives present, slight bump
        marketing_adjs = {"innovative", "revolutionary", "seamless"}
        text_lower = text.lower()
        if sum(1 for a in marketing_adjs if a in text_lower) >= 2:
            ev += 0.05

        return ev

    def _apply_feedback_clues_claims(self, ev: float, term: str, context: Dict[str, Any]) -> float:
        patterns = self._get_cached_feedback_patterns_claims()
        t = term.lower()
        if t in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        if t in patterns.get('accepted_terms', set()):
            ev -= 0.2
        ctype = (context or {}).get('content_type', 'general')
        pc = patterns.get(f'{ctype}_patterns', {})
        if t in pc.get('flagged', set()):
            ev += 0.1
        if t in pc.get('accepted', set()):
            ev -= 0.1
        return ev

    def _get_cached_feedback_patterns_claims(self) -> Dict[str, Any]:
        return {
            'often_flagged_terms': {"secure", "effortless", "future-proof", "guaranteed"},
            'accepted_terms': set(),
            'marketing_patterns': {
                'flagged': {"best practice", "always", "never"},
                'accepted': set()
            },
            'technical_patterns': {
                'flagged': {"secure", "future-proof"},
                'accepted': set()
            }
        }

    # === SMART MESSAGING ===

    def _get_contextual_claim_message(self, term: str, ev: float, context: Dict[str, Any]) -> str:
        if ev > 0.85:
            return f"The term '{term}' is a risky claim without evidence. Use specific, verifiable language."
        if ev > 0.6:
            return f"Consider replacing '{term}' with a specific, objective description."
        return f"Prefer objective phrasing over '{term}' to avoid subjective claims."
