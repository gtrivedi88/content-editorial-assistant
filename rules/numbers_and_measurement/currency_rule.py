"""
Currency Rule
Based on IBM Style Guide topic: "Currency"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class CurrencyRule(BaseNumbersRule):
    """
    Checks for correct currency formatting, including the use of ISO codes
    and the avoidance of letter abbreviations for multipliers like 'M' for million.
    """
    def _get_rule_type(self) -> str:
        return 'numbers_currency'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for currency formatting:
          - Prefer ISO currency codes (e.g., 'USD 100') over symbols for global audiences
          - Avoid letter multipliers like 'M'/'K' (e.g., '4M') in currency amounts
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
        doc = nlp(text)

        # Pattern to find currency symbols or multipliers.
        currency_pattern = re.compile(r'([\$€£]\s?\d[\d,.]*)|(\d[\d,.]*\s?[MK])\b', re.IGNORECASE)

        for i, sent in enumerate(doc.sents):
            for match in currency_pattern.finditer(sent.text):
                flagged_text = match.group(0)
                span = (sent.start_char + match.start(), sent.start_char + match.end())

                # --- Evidence for symbol usage ---
                if any(c in flagged_text for c in "$€£"):
                    ev_symbol = self._calculate_currency_symbol_evidence(flagged_text, sent, text, context or {})
                    if ev_symbol > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=self._get_contextual_currency_symbol_message(flagged_text, ev_symbol, context or {}),
                            suggestions=self._generate_smart_currency_symbol_suggestions(flagged_text, ev_symbol, sent, context or {}),
                            severity='low' if ev_symbol < 0.6 else 'medium',
                            text=text,
                            context=context,
                            evidence_score=ev_symbol,
                            span=span,
                            flagged_text=flagged_text
                        ))

                # --- Evidence for multiplier usage (M/K) ---
                if any(c in flagged_text.upper() for c in "MK"):
                    ev_mult = self._calculate_currency_multiplier_evidence(flagged_text, sent, text, context or {})
                    if ev_mult > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=self._get_contextual_multiplier_message(flagged_text, ev_mult, context or {}),
                            suggestions=self._generate_smart_multiplier_suggestions(flagged_text, ev_mult, sent, context or {}),
                            severity='medium' if ev_mult > 0.6 else 'low',
                            text=text,
                            context=context,
                            evidence_score=ev_mult,
                            span=span,
                            flagged_text=flagged_text
                        ))
        return errors

    # === EVIDENCE CALCULATION: SYMBOLS ===

    def _calculate_currency_symbol_evidence(self, flagged_text: str, sentence, text: str, context: Dict[str, Any]) -> float:
        evidence: float = 0.55  # base for symbol usage

        sent_lower = sentence.text.lower()

        # Linguistic: reduce if ISO code is present near amount (e.g., 'USD', 'EUR')
        if any(code in sentence.text for code in ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "INR"]):
            evidence -= 0.25

        # Reduce if currency word present clarifying (e.g., 'USD 100' nearby)
        if re.search(r'\b(usd|eur|gbp|jpy|aud|cad|chf|cny|inr)\b\s?\d', sentence.text, flags=re.I):
            evidence -= 0.2

        # Increase if ambiguous symbol-only amount without currency word
        if re.search(r'[\$€£]\s?\d', flagged_text) and not re.search(r'\b(dollar|euro|pound|usd|eur|gbp)\b', sent_lower):
            evidence += 0.1

        # Structural clues
        evidence = self._apply_structural_clues_currency(evidence, context)

        # Semantic clues: stricter in legal/finance/commercial docs
        evidence = self._apply_semantic_clues_currency(evidence, context)

        # Feedback clues
        evidence = self._apply_feedback_clues_currency(evidence, flagged_text, context)

        return max(0.0, min(1.0, evidence))

    # === EVIDENCE CALCULATION: MULTIPLIERS ===

    def _calculate_currency_multiplier_evidence(self, flagged_text: str, sentence, text: str, context: Dict[str, Any]) -> float:
        evidence: float = 0.65  # base for M/K multiplier

        # Linguistic: avoid false positives for non-currency contexts like 4k resolution, 8k video
        if re.search(r'\b(\d+\s?(k|m))\b', flagged_text, flags=re.I):
            sent_lower = sentence.text.lower()
            if any(term in sent_lower for term in ['resolution', 'video', 'display', 'pixels', 'kb', 'mb']):
                evidence -= 0.35

        # Presence of ISO code alongside multiplier slightly reduces (still prefer spelled-out)
        if any(code in sentence.text for code in ["USD", "EUR", "GBP", "JPY"]):
            evidence -= 0.1

        # Structural/semantic/feedback
        evidence = self._apply_structural_clues_currency(evidence, context)
        evidence = self._apply_semantic_clues_currency(evidence, context)
        evidence = self._apply_feedback_clues_currency(evidence, flagged_text, context)

        return max(0.0, min(1.0, evidence))

    # === CLUE HELPERS ===

    def _apply_structural_clues_currency(self, ev: float, context: Dict[str, Any]) -> float:
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

    def _apply_semantic_clues_currency(self, ev: float, context: Dict[str, Any]) -> float:
        content_type = (context or {}).get('content_type', 'general')
        domain = (context or {}).get('domain', 'general')
        audience = (context or {}).get('audience', 'general')

        if domain in {'finance', 'legal'}:
            ev += 0.15
        if content_type in {'technical', 'api', 'procedural'}:
            ev += 0.05
        if content_type in {'marketing', 'narrative'}:
            ev -= 0.05
        if audience in {'beginner', 'general'}:
            ev += 0.05
        return ev

    def _apply_feedback_clues_currency(self, ev: float, flagged_text: str, context: Dict[str, Any]) -> float:
        patterns = self._get_cached_feedback_patterns_currency()
        f = flagged_text.lower()
        if f in patterns.get('often_accepted', set()):
            ev -= 0.2
        if f in patterns.get('often_flagged', set()):
            ev += 0.1
        return ev

    def _get_cached_feedback_patterns_currency(self) -> Dict[str, Any]:
        return {
            'often_accepted': set(),
            'often_flagged': set(),
        }

    # === SMART MESSAGING & SUGGESTIONS ===

    def _get_contextual_currency_symbol_message(self, flagged_text: str, ev: float, context: Dict[str, Any]) -> str:
        if ev > 0.85:
            return "Use the three-letter ISO currency code before the amount for global audiences."
        if ev > 0.6:
            return "Consider using the ISO currency code (e.g., 'USD 100') instead of a symbol."
        return "ISO currency codes improve clarity for international readers."

    def _generate_smart_currency_symbol_suggestions(self, flagged_text: str, ev: float, sentence, context: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        # Suggest replacing symbol with ISO code
        amount = re.sub(r'^[\$€£]\s?', '', flagged_text)
        suggestions.append(f"Replace with 'USD {amount}' (or appropriate ISO code).")
        suggestions.append("Use ISO codes (USD, EUR, GBP) consistently across the document.")
        return suggestions[:3]

    def _get_contextual_multiplier_message(self, flagged_text: str, ev: float, context: Dict[str, Any]) -> str:
        if ev > 0.8:
            return f"Avoid letter abbreviations like '{flagged_text}' for currency. Spell out the full amount."
        if ev > 0.6:
            return f"Consider spelling out currency multipliers instead of '{flagged_text}'."
        return "Spell out currency multipliers for clarity (e.g., '4 million')."

    def _generate_smart_multiplier_suggestions(self, flagged_text: str, ev: float, sentence, context: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        # Extract numeric portion
        num = re.findall(r'\d[\d,.]*', flagged_text)
        num_str = num[0] if num else ''
        if flagged_text.strip().lower().endswith('m'):
            suggestions.append(f"Use 'USD {num_str} million' or 'USD {num_str},000,000'.")
        elif flagged_text.strip().lower().endswith('k'):
            suggestions.append(f"Use 'USD {num_str} thousand' or 'USD {num_str},000'.")
        else:
            suggestions.append("Spell out the full number with an ISO currency code.")
        suggestions.append("Ensure numeric formatting uses separators appropriate for the style guide.")
        return suggestions[:3]
