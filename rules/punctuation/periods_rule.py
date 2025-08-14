"""
Periods Rule - Evidence-Based Analysis
Based on IBM Style Guide topic: "Periods"

**UPDATED** with evidence-based scoring for nuanced period usage analysis.
"""
from typing import List, Dict, Any, Optional
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens import Doc, Token, Span
except ImportError:
    Doc = None
    Token = None
    Span = None

class PeriodsRule(BasePunctuationRule):
    """
    Checks for incorrect use of periods using evidence-based analysis:
    - Periods within uppercase abbreviations
    - Other period usage violations
    Enhanced with dependency parsing and contextual awareness.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'periods'

    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for period usage violations:
        - Periods within uppercase abbreviations
        - Other contextual period issues
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        
        # Fallback analysis when nlp is not available
        if not nlp:
            # Apply basic guards for fallback analysis
            content_type = context.get('content_type', 'general')
            block_type = context.get('block_type', 'paragraph')
            
            # Skip if in contexts where periods in abbreviations are legitimate
            if content_type in ['creative', 'literary', 'narrative', 'legal']:
                return errors  # No errors for creative or legal content
            if block_type in ['quote', 'blockquote', 'code_block', 'literal_block', 'citation']:
                return errors  # No errors for quotes, code, and citations
            
            import re
            # Pattern for abbreviations with periods (e.g., U.S.A., A.P.I., E.U.)
            for i, sentence in enumerate(sentences):
                for match in re.finditer(r'\b[A-Z]\.(?:[A-Z]\.)*[A-Z]?\.?\b', sentence):
                    match_text = match.group(0)
                    
                    # Check for legitimate abbreviations that should keep periods
                    # Include variations without final period for regex match
                    legitimate_patterns = ['P.M.', 'A.M.', 'P.O.', 'U.K.', 'U.S.', 'P.M', 'A.M', 'P.O', 'U.K', 'U.S']
                    if match_text.upper() in legitimate_patterns:
                        continue  # Skip legitimate time/location abbreviations
                    
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Consider removing periods from this abbreviation for modern style.",
                        suggestions=["Remove periods from abbreviations (e.g., 'USA' instead of 'U.S.A.')", "Modern style guides prefer clean abbreviations without periods."],
                        severity='low',
                        text=text,
                        context=context,
                        evidence_score=0.7,  # Default evidence for fallback analysis
                        span=(match.start(), match.end()),
                        flagged_text=match_text
                    ))
            return errors

        try:
            doc = nlp(text)
            for i, sent in enumerate(doc.sents):
                for token in sent:
                    # Look for tokens that contain periods in abbreviations (e.g., "U.S.A.")
                    if self._is_abbreviation_with_periods(token):
                        evidence_score = self._calculate_period_evidence(token, sent, text, context)
                        
                        if evidence_score > 0.1:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=self._get_contextual_period_message(evidence_score, context),
                                suggestions=self._generate_smart_period_suggestions(token, evidence_score, context),
                                severity='low' if evidence_score < 0.7 else 'medium',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=(token.idx, token.idx + len(token.text)),
                                flagged_text=token.text
                            ))
        except Exception as e:
            # Graceful degradation for SpaCy errors
            errors.append(self._create_error(
                sentence=text,
                sentence_index=0,
                message=f"Period analysis failed: {str(e)}",
                suggestions=["Please check for obvious period issues manually."],
                severity='low',
                text=text,
                context=context,
                evidence_score=0.0  # No evidence when analysis fails
            ))
        
        return errors

    # === EVIDENCE CALCULATION ===

    def _is_abbreviation_with_periods(self, token: 'Token') -> bool:
        """
        Check if this token is an abbreviation containing periods.
        SpaCy tokenizes "U.S.A." as a single token, so we check the token text.
        """
        import re
        # Pattern for abbreviations with periods (e.g., U.S.A., A.P.I., E.U.)
        return bool(re.match(r'^[A-Z]\.(?:[A-Z]\.)*[A-Z]?\.?$', token.text))

    def _calculate_period_evidence(self, abbrev_token: 'Token', sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) that a period usage is incorrect.
        
        Higher scores indicate stronger evidence of an error.
        Lower scores indicate acceptable usage or ambiguous cases.
        """
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        # Apply surgical guards FIRST to eliminate false positives
        if self._apply_zero_false_positive_guards_punctuation(abbrev_token, context):
            return 0.0
        
        # Creative content commonly uses various punctuation styles
        content_type = context.get('content_type', 'general')
        if content_type in ['creative', 'literary', 'narrative']:
            return 0.0
        
        # Legal documents often require periods in abbreviations
        if content_type == 'legal':
            return 0.0
        
        # Quotes preserve original punctuation
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['quote', 'blockquote']:
            return 0.0
        
        # Citations and academic references have specific formatting
        if block_type in ['citation', 'reference', 'footnote', 'bibliography']:
            return 0.0
        
        # Check for legitimate abbreviations that should keep periods
        if self._is_legitimate_abbreviation_period(abbrev_token, sent, context):
            return 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        # Start with strong evidence for abbreviation periods
        evidence_score = 0.8
        
        # === STEP 2: LINGUISTIC CLUES ===
        evidence_score = self._apply_common_linguistic_clues_punctuation(evidence_score, abbrev_token, sent)
        
        # === STEP 3: STRUCTURAL CLUES ===
        evidence_score = self._apply_common_structural_clues_punctuation(evidence_score, abbrev_token, context)
        
        # === STEP 4: SEMANTIC CLUES ===
        evidence_score = self._apply_common_semantic_clues_punctuation(evidence_score, abbrev_token, context)
        
        return max(0.0, min(1.0, evidence_score))

    def _is_legitimate_abbreviation_period(self, abbrev_token: 'Token', sent: 'Span', context: Dict[str, Any]) -> bool:
        """
        Check if this abbreviation period usage is legitimate in this context.
        """
        # Check for common legitimate abbreviations that should keep periods
        legitimate_abbrevs = ['P.M.', 'A.M.', 'P.O.', 'U.K.', 'U.S.', 'Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.']
        if abbrev_token.text in legitimate_abbrevs:
            return True
        
        return False

    # === SMART MESSAGING ===

    def _get_contextual_period_message(self, evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for period usage."""
        if evidence_score > 0.8:
            return "Avoid using periods within uppercase abbreviations."
        elif evidence_score > 0.6:
            return "Consider removing periods from this uppercase abbreviation."
        else:
            return "Review period usage in this abbreviation for style consistency."

    def _generate_smart_period_suggestions(self, period_token: 'Token', evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for period usage."""
        suggestions = []
        
        if evidence_score > 0.7:
            suggestions.append("Remove the periods from the abbreviation (e.g., 'USA' instead of 'U.S.A.').")
            suggestions.append("Modern style guides prefer abbreviations without internal periods.")
        else:
            suggestions.append("Consider removing periods for a cleaner, modern style.")
            suggestions.append("Check your style guide's preference for abbreviation periods.")
        
        # Context-specific suggestions
        content_type = context.get('content_type', 'general')
        if content_type == 'technical':
            suggestions.append("Technical documentation typically uses abbreviations without periods.")
        elif content_type == 'legal':
            suggestions.append("Legal documents may require periods in abbreviations - check your style guide.")
        elif content_type == 'academic':
            suggestions.append("Academic style may vary - consult your institution's guidelines.")
        
        return suggestions[:3]
