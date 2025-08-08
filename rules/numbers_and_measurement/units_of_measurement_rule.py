"""
Units of Measurement Rule
Based on IBM Style Guide topic: "Units of measurement"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class UnitsOfMeasurementRule(BaseNumbersRule):
    """
    Checks for correct formatting of units of measurement, such as ensuring
    a space between the number and the unit abbreviation.
    """
    def _get_rule_type(self) -> str:
        return 'units_of_measurement'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for unit-of-measurement formatting:
          - Prefer a space between number and unit (e.g., '600 MHz')
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
        doc = nlp(text)
        
        no_space_pattern = re.compile(r'\b\d+(mm|cm|m|km|mg|g|kg|ms|s|min|hr|Hz|MHz|GHz|KB|MB|GB|TB)\b')

        for i, sent in enumerate(doc.sents):
            for match in no_space_pattern.finditer(sent.text):
                flagged = match.group(0)
                span = (sent.start_char + match.start(), sent.start_char + match.end())
                ev = self._calculate_units_evidence(flagged, sent, text, context or {})
                if ev > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=self._get_contextual_units_message(flagged, ev, context or {}),
                        suggestions=self._generate_smart_units_suggestions(flagged, ev, sent, context or {}),
                        severity='low' if ev < 0.7 else 'medium',
                        text=text,
                        context=context,
                        evidence_score=ev,
                        span=span,
                        flagged_text=flagged
                    ))
        return errors

    # === EVIDENCE CALCULATION ===

    def _calculate_units_evidence(self, flagged: str, sentence, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence (0.0-1.0) that a missing space before a unit needs correction."""
        evidence: float = 0.65  # base for missing space

        # Linguistic: if inside quotes/backticks (UI/code), reduce severity
        sent_text = sentence.text
        if '"' in sent_text or "'" in sent_text or '`' in sent_text:
            evidence -= 0.2

        # If part of an identifier-like token (camelCase or snake_case) reduce
        if re.search(r'[A-Za-z0-9_]{2,}', sent_text) and '`' in sent_text:
            evidence -= 0.1

        # Very small units (ms) adjacent to timing verbs may be slightly tolerated
        if flagged.endswith('ms') and any(t.lemma_.lower() in {'wait', 'sleep', 'timeout'} for t in sentence):
            evidence -= 0.05

        # Structural/semantic/feedback
        evidence = self._apply_structural_clues_units(evidence, context)
        evidence = self._apply_semantic_clues_units(evidence, context)
        evidence = self._apply_feedback_clues_units(evidence, flagged, context)

        return max(0.0, min(1.0, evidence))

    # === CLUE HELPERS ===

    def _apply_structural_clues_units(self, ev: float, context: Dict[str, Any]) -> float:
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

    def _apply_semantic_clues_units(self, ev: float, context: Dict[str, Any]) -> float:
        content_type = (context or {}).get('content_type', 'general')
        domain = (context or {}).get('domain', 'general')
        audience = (context or {}).get('audience', 'general')

        if domain in {'technical', 'engineering'} or content_type in {'technical', 'api', 'procedural'}:
            ev += 0.1
        if content_type in {'marketing', 'narrative'}:
            ev -= 0.05
        if audience in {'beginner', 'general'}:
            ev += 0.05
        return ev

    def _apply_feedback_clues_units(self, ev: float, flagged: str, context: Dict[str, Any]) -> float:
        patterns = self._get_cached_feedback_patterns_units()
        f = flagged.lower()
        if f in patterns.get('often_accepted', set()):
            ev -= 0.2
        if f in patterns.get('often_flagged', set()):
            ev += 0.1
        return ev

    def _get_cached_feedback_patterns_units(self) -> Dict[str, Any]:
        return {
            'often_accepted': set(),
            'often_flagged': set(),
        }

    # === SMART MESSAGING ===

    def _get_contextual_units_message(self, flagged: str, ev: float, context: Dict[str, Any]) -> str:
        if ev > 0.85:
            return f"Missing space between number and unit: '{flagged}'."
        if ev > 0.6:
            return f"Consider inserting a space between the number and unit in '{flagged}'."
        return "A space between the number and unit improves clarity."

    def _generate_smart_units_suggestions(self, flagged: str, ev: float, sentence, context: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        # Split number and unit
        m = re.match(r'^(\d+)([A-Za-z]+)$', flagged)
        if m:
            suggestions.append(f"Write as '{m.group(1)} {m.group(2)}'.")
        suggestions.append("Use SI-consistent spacing (e.g., '600 MHz', '10 kg').")
        if (context or {}).get('block_type') in {'code_block', 'inline_code'}:
            suggestions.append("If this is code, leave literals as-is but document units clearly in surrounding text.")
        return suggestions[:3]
