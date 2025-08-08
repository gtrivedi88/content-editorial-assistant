"""
Dates and Times Rule
Based on IBM Style Guide topic: "Dates and times"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class DatesAndTimesRule(BaseNumbersRule):
    """
    Checks for correct and internationally understandable date and time formats.
    """
    def _get_rule_type(self) -> str:
        return 'dates_and_times'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for dates and times:
          - Avoid ambiguous all-numeric dates; prefer '14 July 2020' or ISO 8601 in code
          - Use 'AM'/'PM' uppercase without periods (not 'am', 'a.m.')
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
        doc = nlp(text)

        numeric_date_pattern = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b')
        am_pm_pattern = re.compile(r'\b\d{1,2}:\d{2}\s?(A\.M\.|p\.m\.|am|pm)\b')
        iso_8601_pattern = re.compile(r'\b\d{4}-\d{2}-\d{2}\b')

        for i, sent in enumerate(doc.sents):
            # Numeric dates
            for match in numeric_date_pattern.finditer(sent.text):
                flagged = match.group(0)
                span = (sent.start_char + match.start(), sent.start_char + match.end())

                ev_date = self._calculate_numeric_date_evidence(flagged, sent, text, context or {}, iso_8601_pattern)
                if ev_date > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=self._get_contextual_numeric_date_message(flagged, ev_date, context or {}),
                        suggestions=self._generate_smart_numeric_date_suggestions(flagged, ev_date, sent, context or {}),
                        severity='medium' if ev_date > 0.6 else 'low',
                        text=text,
                        context=context,
                        evidence_score=ev_date,
                        span=span,
                        flagged_text=flagged
                    ))

            # AM/PM formatting
            for match in am_pm_pattern.finditer(sent.text):
                flagged = match.group(0)
                span = (sent.start_char + match.start(), sent.start_char + match.end())

                ev_ampm = self._calculate_ampm_evidence(flagged, sent, text, context or {})
                if ev_ampm > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=self._get_contextual_ampm_message(flagged, ev_ampm, context or {}),
                        suggestions=self._generate_smart_ampm_suggestions(flagged, ev_ampm, sent, context or {}),
                        severity='low' if ev_ampm < 0.7 else 'medium',
                        text=text,
                        context=context,
                        evidence_score=ev_ampm,
                        span=span,
                        flagged_text=flagged
                    ))
        return errors

    # === EVIDENCE CALCULATION ===

    def _calculate_numeric_date_evidence(self, flagged: str, sentence, text: str, context: Dict[str, Any], iso_pat: re.Pattern) -> float:
        """Calculate evidence (0.0-1.0) that a numeric date is ambiguous/inappropriate."""
        evidence: float = 0.65  # base for all-numeric

        # Exempt ISO-8601 patterns (YYYY-MM-DD) used in technical/code contexts
        if iso_pat.search(flagged):
            evidence -= 0.6

        # Slash vs dash: slashes more ambiguous
        if '/' in flagged:
            evidence += 0.1

        # Two-digit year increases ambiguity
        if re.search(r'[/-]\d{2}$', flagged):
            evidence += 0.1

        # If month name also appears nearby, reduce
        if re.search(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b', sentence.text, flags=re.I):
            evidence -= 0.1

        # Structural/semantic/feedback
        evidence = self._apply_structural_clues_dates(evidence, context)
        evidence = self._apply_semantic_clues_dates(evidence, context)
        evidence = self._apply_feedback_clues_dates(evidence, flagged, context)

        return max(0.0, min(1.0, evidence))

    def _calculate_ampm_evidence(self, flagged: str, sentence, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence (0.0-1.0) that AM/PM formatting is incorrect."""
        evidence: float = 0.6  # base for wrong case/periods

        # Lowercase increases severity; periods increase severity
        if re.search(r'\b(am|pm)\b', flagged):
            evidence += 0.1
        if '.' in flagged:
            evidence += 0.1

        # If sentence shows 24-hour time as alternative, reduce
        if re.search(r'\b\d{2}:\d{2}\b', sentence.text):
            evidence -= 0.1

        # Structural/semantic/feedback
        evidence = self._apply_structural_clues_dates(evidence, context)
        evidence = self._apply_semantic_clues_dates(evidence, context)
        evidence = self._apply_feedback_clues_dates(evidence, flagged, context)

        return max(0.0, min(1.0, evidence))

    # === CLUE HELPERS ===

    def _apply_structural_clues_dates(self, ev: float, context: Dict[str, Any]) -> float:
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

    def _apply_semantic_clues_dates(self, ev: float, context: Dict[str, Any]) -> float:
        content_type = (context or {}).get('content_type', 'general')
        domain = (context or {}).get('domain', 'general')
        audience = (context or {}).get('audience', 'general')

        if domain in {'legal', 'finance', 'government'}:
            ev += 0.15
        if content_type in {'technical', 'api', 'procedural'}:
            ev += 0.05
        if content_type in {'marketing', 'narrative'}:
            ev -= 0.05
        if audience in {'beginner', 'general'}:
            ev += 0.05
        return ev

    def _apply_feedback_clues_dates(self, ev: float, flagged: str, context: Dict[str, Any]) -> float:
        patterns = self._get_cached_feedback_patterns_dates()
        f = flagged.lower()
        if f in patterns.get('often_flagged', set()):
            ev += 0.1
        if f in patterns.get('often_accepted', set()):
            ev -= 0.2
        return ev

    def _get_cached_feedback_patterns_dates(self) -> Dict[str, Any]:
        return {
            'often_flagged': set(),
            'often_accepted': set(),
        }

    # === SMART MESSAGING ===

    def _get_contextual_numeric_date_message(self, flagged: str, ev: float, context: Dict[str, Any]) -> str:
        if ev > 0.85:
            return "Avoid all-numeric date formats; they can be ambiguous internationally."
        if ev > 0.6:
            return f"Consider replacing '{flagged}' with an unambiguous format."
        return "Prefer unambiguous date formats for global audiences."

    def _generate_smart_numeric_date_suggestions(self, flagged: str, ev: float, sentence, context: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        suggestions.append("Use '14 July 2020' or 'July 14, 2020' depending on style.")
        if (context or {}).get('block_type') in {'code_block', 'inline_code'} or (context or {}).get('content_type') in {'technical', 'api'}:
            suggestions.append("In code/technical contexts, use ISO 8601: 'YYYY-MM-DD'.")
        suggestions.append("Avoid two-digit years and numeric month/day confusion.")
        return suggestions[:3]

    def _get_contextual_ampm_message(self, flagged: str, ev: float, context: Dict[str, Any]) -> str:
        if ev > 0.8:
            return "Use 'AM'/'PM' uppercase without periods for times."
        if ev > 0.6:
            return f"Consider formatting time as 'AM'/'PM' (not '{flagged.split()[-1]}')."
        return "Prefer uppercase 'AM'/'PM' without periods."

    def _generate_smart_ampm_suggestions(self, flagged: str, ev: float, sentence, context: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        suggestions.append("Replace 'a.m.'/'pm' with 'AM'/'PM'.")
        suggestions.append("Optionally use 24-hour time where appropriate (e.g., '16:30').")
        return suggestions[:3]
