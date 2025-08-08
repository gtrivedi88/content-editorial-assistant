"""
Personal Information Rule
Based on IBM Style Guide topic: "Personal information"
"""
from typing import List, Dict, Any
from .base_legal_rule import BaseLegalRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class PersonalInformationRule(BaseLegalRule):
    """
    Checks for the use of culturally specific terms like "first name" or
    "last name" and suggests more global alternatives.
    """
    def _get_rule_type(self) -> str:
        return 'legal_personal_information'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for globally inclusive personal information terms.
        Flags culturally-specific labels (e.g., "first name/last name", "christian name")
        with nuanced evidence using linguistic, structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
        doc = nlp(text)

        # Linguistic Anchor: discouraged → preferred
        name_terms = {
            "first name": "given name",
            "christian name": "given name",
            "last name": "family name",
        }

        for i, sent in enumerate(doc.sents):
            for bad_term, good_term in name_terms.items():
                for match in re.finditer(r'\b' + re.escape(bad_term) + r'\b', sent.text, re.IGNORECASE):
                    start = sent.start_char + match.start()
                    end = sent.start_char + match.end()
                    term_text = match.group(0)

                    evidence_score = self._calculate_personal_info_evidence(
                        term_text, sent, text, context or {}
                    )
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=self._get_contextual_personal_info_message(term_text, good_term, evidence_score, context or {}),
                            suggestions=self._generate_smart_personal_info_suggestions(term_text, good_term, evidence_score, sent, context or {}),
                            severity='low' if evidence_score < 0.7 else 'medium',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(start, end),
                            flagged_text=term_text
                        ))
        return errors

    # === EVIDENCE-BASED CALCULATION ===

    def _calculate_personal_info_evidence(self, term: str, sentence, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence (0.0-1.0) that a name label is not globally inclusive."""
        evidence: float = 0.6  # base for discouraged term

        # Linguistic clues (micro)
        evidence = self._apply_linguistic_clues_personal_info(evidence, term, sentence)

        # Structural clues (meso)
        evidence = self._apply_structural_clues_personal_info(evidence, context)

        # Semantic clues (macro)
        evidence = self._apply_semantic_clues_personal_info(evidence, text, context)

        # Feedback clues (learning)
        evidence = self._apply_feedback_clues_personal_info(evidence, term, context)

        return max(0.0, min(1.0, evidence))

    # === CLUE METHODS ===

    def _apply_linguistic_clues_personal_info(self, ev: float, term: str, sentence) -> float:
        sent_text = sentence.text
        sent_lower = sent_text.lower()

        # If paired with inclusive alternatives already, reduce
        if any(p in sent_lower for p in {"given name", "family name", "surname"}):
            ev -= 0.2

        # Form labels/fields (colon, form-like) increase seriousness
        if any(k in sent_text for k in [":", "*"]):
            ev += 0.05

        # Quoted UI/labels lower severity slightly
        if '"' in sent_text or "'" in sent_text or '`' in sent_text:
            ev -= 0.05

        return ev

    def _apply_structural_clues_personal_info(self, ev: float, context: Dict[str, Any]) -> float:
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

    def _apply_semantic_clues_personal_info(self, ev: float, text: str, context: Dict[str, Any]) -> float:
        content_type = (context or {}).get('content_type', 'general')
        domain = (context or {}).get('domain', 'general')
        audience = (context or {}).get('audience', 'general')

        # Stricter in legal/compliance/registration flows
        if content_type in {'legal', 'compliance', 'form', 'procedural'}:
            ev += 0.15
        if content_type in {'technical', 'api'}:
            ev += 0.05
        if content_type in {'marketing', 'narrative'}:
            ev -= 0.05

        if domain in {'legal', 'finance', 'government'}:
            ev += 0.1

        if audience in {'beginner', 'general', 'user'}:
            ev += 0.05

        return ev

    def _apply_feedback_clues_personal_info(self, ev: float, term: str, context: Dict[str, Any]) -> float:
        patterns = self._get_cached_feedback_patterns_personal_info()
        t = term.lower()
        if t in patterns.get('accepted_terms', set()):
            ev -= 0.2
        if t in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        ctype = (context or {}).get('content_type', 'general')
        pc = patterns.get(f'{ctype}_patterns', {})
        if t in pc.get('accepted', set()):
            ev -= 0.1
        if t in pc.get('flagged', set()):
            ev += 0.1
        return ev

    def _get_cached_feedback_patterns_personal_info(self) -> Dict[str, Any]:
        return {
            'accepted_terms': set(),
            'often_flagged_terms': {'christian name'},
            'form_patterns': {
                'accepted': set(),
                'flagged': {'first name', 'last name'}
            }
        }

    # === SMART MESSAGING ===

    def _get_contextual_personal_info_message(self, term: str, preferred: str, ev: float, context: Dict[str, Any]) -> str:
        if ev > 0.85:
            return f"The term '{term}' is not globally inclusive. Use '{preferred}'."
        if ev > 0.6:
            return f"Consider using globally inclusive terminology: replace '{term}' with '{preferred}'."
        return f"Prefer '{preferred}' over '{term}' for global inclusivity."

    def _generate_smart_personal_info_suggestions(self, term: str, preferred: str, ev: float, sentence, context: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        suggestions.append(f"Replace '{term}' with '{preferred}'.")
        suggestions.append("Ensure forms and UI labels use 'given name' and 'family name' to support global naming conventions.")
        if 'surname' in sentence.text.lower():
            suggestions.append("Use 'family name' consistently alongside 'given name'.")
        return suggestions[:3]
