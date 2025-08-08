"""
Numbers Rule
Based on IBM Style Guide topic: "Numbers"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class NumbersRule(BaseNumbersRule):
    """
    Checks for general number formatting issues, such as missing comma
    separators and incorrect decimal formatting.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'numbers_general'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for number formatting:
          - Large integers should use thousands separators
          - Decimals <1 should include a leading zero
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
        
        doc = nlp(text)
        
        no_comma_pattern = re.compile(r'\b\d{5,}\b')
        leading_decimal_pattern = re.compile(r'(?<!\d)\.\d+')

        for i, sent in enumerate(doc.sents):
            # Thousands separators
            for match in no_comma_pattern.finditer(sent.text):
                flagged = match.group(0)
                span = (sent.start_char + match.start(), sent.start_char + match.end())
                ev_sep = self._calculate_thousands_separator_evidence(flagged, sent, text, context or {})
                if ev_sep > 0.1:
                    message = self._get_contextual_thousands_message(flagged, ev_sep, context or {})
                    suggestions = self._generate_smart_thousands_suggestions(flagged, ev_sep, sent, context or {})
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=message,
                        suggestions=suggestions,
                        severity='low' if ev_sep < 0.7 else 'medium',
                        text=text,
                        context=context,
                        evidence_score=ev_sep,
                        span=span,
                        flagged_text=flagged
                    ))

            # Leading zero for <1 decimals
            for match in leading_decimal_pattern.finditer(sent.text):
                flagged = match.group(0)
                span = (sent.start_char + match.start(), sent.start_char + match.end())
                ev_dec = self._calculate_leading_decimal_evidence(flagged, sent, text, context or {})
                if ev_dec > 0.1:
                    message = self._get_contextual_leading_decimal_message(flagged, ev_dec, context or {})
                    suggestions = self._generate_smart_leading_decimal_suggestions(flagged, ev_dec, sent, context or {})
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=message,
                        suggestions=suggestions,
                        severity='low' if ev_dec < 0.7 else 'medium',
                        text=text,
                        context=context,
                        evidence_score=ev_dec,
                        span=span,
                        flagged_text=flagged
                    ))
        return errors

    # === EVIDENCE CALCULATION ===

    def _calculate_thousands_separator_evidence(self, number_str: str, sentence, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence (0.0-1.0) that a large integer should use separators."""
        try:
            digits = len(number_str)
        except Exception:
            digits = 5
        # Base scales with length beyond 4
        over = max(0, digits - 4)
        evidence: float = min(1.0, 0.5 + min(0.4, over * 0.05))

        # Linguistic: scientific/ID tokens reduce (heuristic)
        sent_lower = sentence.text.lower()
        if any(k in sent_lower for k in ['id ', 'uuid', 'hash', 'checksum']):
            evidence -= 0.2

        # If surrounded by non-breaking formatting (monospace/backticks), reduce
        if '`' in sentence.text:
            evidence -= 0.15

        # Structural/semantic/feedback
        evidence = self._apply_structural_clues_numbers(evidence, context)
        evidence = self._apply_semantic_clues_numbers(evidence, context)
        evidence = self._apply_feedback_clues_numbers(evidence, number_str, context)

        return max(0.0, min(1.0, evidence))

    def _calculate_leading_decimal_evidence(self, flagged: str, sentence, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence (0.0-1.0) that a <1 decimal needs a leading zero."""
        evidence: float = 0.6

        # Linguistic: math contexts like ranges or coefficients still should include zero
        # Reduce if clearly in code/monospace
        if '`' in sentence.text:
            evidence -= 0.2

        # Structural/semantic/feedback
        evidence = self._apply_structural_clues_numbers(evidence, context)
        evidence = self._apply_semantic_clues_numbers(evidence, context)
        evidence = self._apply_feedback_clues_numbers(evidence, flagged, context)

        return max(0.0, min(1.0, evidence))

    # === CLUE HELPERS ===

    def _apply_structural_clues_numbers(self, ev: float, context: Dict[str, Any]) -> float:
        block_type = (context or {}).get('block_type', 'paragraph')
        if block_type in {'code_block', 'literal_block'}:
            return ev - 0.7
        if block_type == 'inline_code':
            return ev - 0.5
        if block_type in {'table_cell', 'table_header'}:
            ev -= 0.05
        if block_type in {'heading', 'title'}:
            ev -= 0.05
        return ev

    def _apply_semantic_clues_numbers(self, ev: float, context: Dict[str, Any]) -> float:
        content_type = (context or {}).get('content_type', 'general')
        domain = (context or {}).get('domain', 'general')
        audience = (context or {}).get('audience', 'general')

        if domain in {'finance', 'legal', 'medical'}:
            ev += 0.15
        if content_type in {'technical', 'api', 'procedural'}:
            ev += 0.05
        if content_type in {'marketing', 'narrative'}:
            ev -= 0.05
        if audience in {'beginner', 'general'}:
            ev += 0.05
        return ev

    def _apply_feedback_clues_numbers(self, ev: float, flagged_text: str, context: Dict[str, Any]) -> float:
        patterns = self._get_cached_feedback_patterns_numbers()
        f = flagged_text.lower()
        if f in patterns.get('often_accepted', set()):
            ev -= 0.2
        if f in patterns.get('often_flagged', set()):
            ev += 0.1
        return ev

    def _get_cached_feedback_patterns_numbers(self) -> Dict[str, Any]:
        return {
            'often_accepted': set(),
            'often_flagged': set(),
        }

    # === SMART MESSAGING ===

    def _get_contextual_thousands_message(self, flagged: str, ev: float, context: Dict[str, Any]) -> str:
        if ev > 0.85:
            return "Large numbers should include thousands separators for readability."
        if ev > 0.6:
            return f"Consider adding separators to '{flagged}' to improve readability."
        return "Separators can make large numbers easier to read."

    def _generate_smart_thousands_suggestions(self, flagged: str, ev: float, sentence, context: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        try:
            suggestion_number = f"{int(flagged):,}"
            suggestions.append(f"Format as '{suggestion_number}'.")
        except Exception:
            suggestions.append("Insert thousands separators as appropriate.")
        suggestions.append("Follow locale/guide conventions consistently across the document.")
        return suggestions[:3]

    def _get_contextual_leading_decimal_message(self, flagged: str, ev: float, context: Dict[str, Any]) -> str:
        if ev > 0.8:
            return "Include a leading zero for decimals less than 1 (e.g., '0.5')."
        if ev > 0.6:
            return f"Consider adding a leading zero to '{flagged}'."
        return "Leading zeros improve clarity for small decimal values."

    def _generate_smart_leading_decimal_suggestions(self, flagged: str, ev: float, sentence, context: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        suggestions.append(f"Use '0{flagged}'.")
        suggestions.append("Apply this consistently for all decimals less than 1.")
        return suggestions[:3]
