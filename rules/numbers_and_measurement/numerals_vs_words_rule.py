"""
Numerals versus Words Rule
Based on IBM Style Guide topic: "Numerals versus words"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class NumeralsVsWordsRule(BaseNumbersRule):
    """
    Checks for consistency in using numerals versus words for numbers,
    especially for numbers under 10.
    """
    def _get_rule_type(self) -> str:
        return 'numerals_vs_words'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for consistent usage of numerals vs. words for numbers < 10.
        Flags minority style within the same document/section with nuanced scoring.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
        doc = nlp(text)

        words_under_10 = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine"}

        # Collect global counts
        counts = {"words": 0, "numerals": 0}
        tokens_list = list(doc)
        for t in tokens_list:
            if self._is_small_number_word(t, words_under_10):
                counts["words"] += 1
            elif self._is_small_number_numeral(t):
                counts["numerals"] += 1

        if counts["words"] == 0 and counts["numerals"] == 0:
            return errors

        dominant = "words" if counts["words"] >= counts["numerals"] else "numerals"

        for i, sent in enumerate(doc.sents):
            for token in sent:
                style = None
                if self._is_small_number_word(token, words_under_10):
                    style = "words"
                elif self._is_small_number_numeral(token):
                    style = "numerals"
                if not style:
                    continue

                # Flag only if this token is of the minority style (inconsistent with dominant usage)
                if counts["words"] > 0 and counts["numerals"] > 0 and style != dominant:
                    ev = self._calculate_numerals_words_evidence(token, style, dominant, sent, text, context or {})
                    if ev > 0.1:
                        message = self._get_contextual_numerals_words_message(style, dominant, ev, context or {})
                        suggestions = self._generate_smart_numerals_words_suggestions(style, dominant, ev, sent, context or {})
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=message,
                            suggestions=suggestions,
                            severity='low' if ev < 0.7 else 'medium',
                            text=text,
                            context=context,
                            evidence_score=ev,
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
        return errors

    # === EVIDENCE CALCULATION ===

    def _calculate_numerals_words_evidence(self, token, style: str, dominant: str, sentence, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence (0.0-1.0) that the token's style is inconsistent."""
        evidence: float = 0.6  # base when both styles present

        # Linguistic: exceptions (version numbers, figures, chapters) reduce evidence
        head_lemma = getattr(token.head, 'lemma_', '').lower()
        exceptions = {"version", "release", "chapter", "figure", "table", "page", "step"}
        if head_lemma in exceptions:
            evidence -= 0.25

        # Sentence start spelled-out words may be acceptable in narrative contexts
        if style == "words" and getattr(token, 'i', 0) == sentence.start:
            evidence -= 0.05

        # If the sentence contains other small numbers in dominant style, increase
        if any((self._is_small_number_word(t, {"one","two","three","four","five","six","seven","eight","nine"}) and dominant == "words") or
               (self._is_small_number_numeral(t) and dominant == "numerals") for t in sentence):
            evidence += 0.1

        # Structural
        evidence = self._apply_structural_clues_numerals_words(evidence, context)

        # Semantic
        evidence = self._apply_semantic_clues_numerals_words(evidence, style, dominant, context)

        # Feedback
        evidence = self._apply_feedback_clues_numerals_words(evidence, token.text, context)

        return max(0.0, min(1.0, evidence))

    # === CLUE HELPERS ===

    def _is_small_number_word(self, token, words_under_10: set) -> bool:
        return getattr(token, 'lemma_', '').lower() in words_under_10 and getattr(token, 'pos_', '') in {"NUM", "DET", "ADJ", "NOUN", "PRON"}

    def _is_small_number_numeral(self, token) -> bool:
        if not getattr(token, 'like_num', False):
            return False
        try:
            num_value = float(token.text)
            return num_value.is_integer() and 0 < int(num_value) < 10
        except Exception:
            return False

    def _apply_structural_clues_numerals_words(self, ev: float, context: Dict[str, Any]) -> float:
        block_type = (context or {}).get('block_type', 'paragraph')
        if block_type in {'code_block', 'literal_block'}:
            return ev - 0.7
        if block_type == 'inline_code':
            return ev - 0.5
        if block_type in {'table_cell', 'table_header', 'ordered_list_item', 'unordered_list_item'}:
            ev -= 0.05
        if block_type in {'heading', 'title'}:
            ev -= 0.05
        return ev

    def _apply_semantic_clues_numerals_words(self, ev: float, style: str, dominant: str, context: Dict[str, Any]) -> float:
        content_type = (context or {}).get('content_type', 'general')
        audience = (context or {}).get('audience', 'general')
        domain = (context or {}).get('domain', 'general')

        # Technical/procedural contexts prefer numerals
        if content_type in {'technical', 'api', 'procedural'} or audience in {'developer', 'expert'}:
            if style == 'words' and dominant == 'numerals':
                ev += 0.1
            if style == 'numerals' and dominant == 'words':
                ev -= 0.05

        # Narrative/marketing tolerate words
        if content_type in {'narrative', 'marketing'}:
            if style == 'words':
                ev -= 0.05
            if style == 'numerals' and dominant == 'words':
                ev += 0.05

        if domain in {'legal', 'finance'}:
            if style == 'words' and dominant == 'numerals':
                ev += 0.05

        return ev

    def _apply_feedback_clues_numerals_words(self, ev: float, token_text: str, context: Dict[str, Any]) -> float:
        patterns = self._get_cached_feedback_patterns_numerals_words()
        t = token_text.lower()
        if t in patterns.get('often_accepted_words', set()):
            ev -= 0.2
        if t in patterns.get('often_flagged_words', set()):
            ev += 0.1
        return ev

    def _get_cached_feedback_patterns_numerals_words(self) -> Dict[str, Any]:
        return {
            'often_accepted_words': set(),
            'often_flagged_words': set(),
        }

    # === SMART MESSAGING ===

    def _get_contextual_numerals_words_message(self, style: str, dominant: str, ev: float, context: Dict[str, Any]) -> str:
        if ev > 0.85:
            return "Inconsistent use of numerals and words for numbers under 10. Use one style consistently."
        if ev > 0.6:
            return "Consider aligning small-number formatting with the dominant style in this document."
        return "Prefer consistent formatting for numbers under 10 across the document."

    def _generate_smart_numerals_words_suggestions(self, style: str, dominant: str, ev: float, sentence, context: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        if dominant == 'numerals':
            suggestions.append("Use numerals for numbers under 10 for consistency.")
        else:
            suggestions.append("Spell out numbers under 10 for consistency.")
        if (context or {}).get('content_type') in {'technical', 'api', 'procedural'}:
            suggestions.append("In technical/procedural content, numerals are typically preferred.")
        suggestions.append("Apply the chosen style consistently throughout the section.")
        return suggestions[:3]
