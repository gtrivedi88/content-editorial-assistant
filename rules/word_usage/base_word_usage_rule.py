"""
Base Word Usage Rule
Abstract base class that all word usage rules inherit from.
Provides shared matching logic with protected product name awareness.
"""
import re
from typing import List, Dict, Any, Optional

try:
    from ..base_rule import BaseRule  # type: ignore
except ImportError:
    class BaseRule:  # type: ignore
        def _get_rule_type(self) -> str:
            return 'base'

        def _create_error(self, sentence: str, sentence_index: int, message: str,
                          suggestions: List[str], severity: str = 'medium',
                          text: Optional[str] = None,
                          context: Optional[Dict[str, Any]] = None,
                          **extra_data) -> Dict[str, Any]:
            """Fallback _create_error when main BaseRule import fails."""
            error = {
                'type': getattr(self, 'rule_type', 'unknown'),
                'message': str(message),
                'suggestions': [str(s) for s in suggestions],
                'sentence': str(sentence),
                'sentence_index': int(sentence_index),
                'severity': severity,
            }
            error.update(extra_data)
            return error

        def _get_protected_ranges(self, text):
            return []

        @staticmethod
        def _is_in_protected_range(start, end, protected_ranges):
            return False


class BaseWordUsageRule(BaseRule):
    """Abstract base class for all word usage rules."""

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        """Analyze text for word usage violations."""
        raise NotImplementedError("Subclasses must implement the analyze method.")

    def _match_terms(self, doc, text: str, term_map: Dict[str, str],
                     context: Dict[str, Any],
                     severity: str = 'medium',
                     message_fmt: str = "Use '{right}' instead of '{found}'.") -> List[Dict[str, Any]]:
        """
        Match terms against SpaCy doc with protected product name awareness.

        Iterates sentences, applies word-boundary regex for each term,
        skips matches inside protected product names, and creates errors.

        Args:
            doc: SpaCy Doc object
            text: Full block text
            term_map: Dict mapping wrong_term -> correct_term
            context: Block context dict
            severity: Error severity (default 'medium')
            message_fmt: Format string with {found} and {right} placeholders
        """
        errors: List[Dict[str, Any]] = []

        for i, sent in enumerate(doc.sents):
            protected_ranges = self._get_protected_ranges(sent.text)

            for wrong, right in term_map.items():
                pattern = r'\b' + re.escape(wrong) + r'\b'
                for match in re.finditer(pattern, sent.text, re.IGNORECASE):
                    if self._is_in_protected_range(match.start(), match.end(), protected_ranges):
                        continue

                    found = match.group(0)
                    start = sent.start_char + match.start()
                    end = sent.start_char + match.end()

                    error = self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=message_fmt.format(found=found, right=right),
                        suggestions=[f"Change '{found}' to '{right}'"],
                        severity=severity,
                        text=text,
                        context=context,
                        flagged_text=found,
                        span=(start, end),
                    )
                    if error:
                        errors.append(error)

        return errors

    def _match_pattern_terms(self, doc, text: str, term_list: List[Dict[str, str]],
                             context: Dict[str, Any],
                             severity: str = 'medium',
                             message_fmt: str = "Use '{right}' instead of '{found}'.") -> List[Dict[str, Any]]:
        """Match terms using optional regex patterns with lookaheads.

        Iterates sentences, applies either a custom regex pattern or an
        auto-generated word-boundary regex for each term, skips matches
        inside protected product names, and creates errors.

        Args:
            doc: SpaCy Doc object.
            text: Full block text.
            term_list: List of dicts with 'wrong', 'right', and optional 'pattern' keys.
            context: Block context dict.
            severity: Error severity.
            message_fmt: Format string with {found} and {right} placeholders.

        Returns:
            List of error dicts for matched terms.
        """
        errors: List[Dict[str, Any]] = []
        for i, sent in enumerate(doc.sents):
            protected_ranges = self._get_protected_ranges(sent.text)
            for entry in term_list:
                wrong = entry['wrong']
                right = entry['right']
                pattern = entry.get('pattern', r'\b' + re.escape(wrong) + r'\b')
                for match in re.finditer(pattern, sent.text, re.IGNORECASE):
                    if self._is_in_protected_range(match.start(), match.end(), protected_ranges):
                        continue
                    found = match.group(0)
                    start = sent.start_char + match.start()
                    end = sent.start_char + match.end()
                    error = self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=message_fmt.format(found=found, right=right),
                        suggestions=[f"Change '{found}' to '{right}'"],
                        severity=severity,
                        text=text,
                        context=context,
                        flagged_text=found,
                        span=(start, end),
                    )
                    if error:
                        errors.append(error)
        return errors
