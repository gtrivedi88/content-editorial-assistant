"""
Terminology Rule
Based on IBM Style Guide topic: "Terminology" and "Word usage"
"""
from typing import List, Dict, Any
import re
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class TerminologyRule(BaseLanguageRule):
    """
    Checks for the use of non-preferred or outdated terminology and suggests
    the correct IBM-approved terms.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'terminology'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for non-preferred/outdated terminology.
        Calculates a nuanced evidence score per match using
        linguistic, structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
        doc = nlp(text)

        term_map = {
            "info center": "IBM Documentation", "infocenter": "IBM Documentation",
            "knowledge center": "IBM Documentation", "dialog box": "dialog",
            "un-install": "uninstall", "de-install": "uninstall",
            "e-mail": "email", "end user": "user", "log on to": "log in to",
            "logon": "log in", "web site": "website", "work station": "workstation",
        }

        for i, sent in enumerate(doc.sents):
            for term, replacement in term_map.items():
                pattern = r'\b' + re.escape(term) + r'\b'
                for match in re.finditer(pattern, sent.text, re.IGNORECASE):
                    start = sent.start_char + match.start()
                    end = sent.start_char + match.end()
                    found = match.group(0)

                    # Try to align a token (best-effort; match may span tokens)
                    token = None
                    for t in sent:
                        if t.idx == start:
                            token = t
                            break

                    evidence_score = self._calculate_terminology_evidence(
                        found, replacement, token, sent, text, context or {}
                    )

                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=self._get_contextual_terminology_message(found, replacement, evidence_score),
                            suggestions=self._generate_smart_terminology_suggestions(found, replacement, evidence_score, sent, context or {}),
                            severity='medium',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(start, end),
                            flagged_text=found
                        ))
        return errors

    # === EVIDENCE-BASED CALCULATION ===

    def _calculate_terminology_evidence(self, found: str, preferred: str, token, sentence, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence (0.0-1.0) that a non-preferred term should be replaced."""
        # Base evidence: term is recognized as non-preferred
        evidence_score: float = 0.65

        # Linguistic clues
        evidence_score = self._apply_linguistic_clues_terminology(evidence_score, found, token, sentence)

        # Structural clues
        evidence_score = self._apply_structural_clues_terminology(evidence_score, context)

        # Semantic clues
        evidence_score = self._apply_semantic_clues_terminology(evidence_score, found, preferred, text, context)

        # Feedback clues
        evidence_score = self._apply_feedback_clues_terminology(evidence_score, found, context)

        return max(0.0, min(1.0, evidence_score))

    # === CLUE APPLICATION METHODS ===

    def _apply_linguistic_clues_terminology(self, evidence_score: float, found: str, token, sentence) -> float:
        sent_text = sentence.text
        lower = sent_text.lower()

        # Reduce inside quotes (reported UI text)
        if '"' in sent_text or "'" in sent_text:
            evidence_score -= 0.1

        # Inline code heuristic via backticks in sentence
        if '`' in sent_text:
            evidence_score -= 0.2

        # Named entities (ORG/PRODUCT) — keep names as-is
        if token is not None:
            ent_type = getattr(token, 'ent_type_', '')
            if ent_type in {'ORG', 'PRODUCT', 'WORK_OF_ART'}:
                evidence_score -= 0.5

        # UI/UX strings: if found within quotes and includes typical UI nouns, slightly lower
        if (('"' in sent_text or "'" in sent_text) and any(k in lower for k in {'button', 'menu', 'tab', 'dialog'})):
            evidence_score -= 0.05

        return evidence_score

    def _apply_structural_clues_terminology(self, evidence_score: float, context: Dict[str, Any]) -> float:
        block_type = (context or {}).get('block_type', 'paragraph')
        if block_type in {'code_block', 'literal_block'}:
            return evidence_score - 0.9
        if block_type == 'inline_code':
            return evidence_score - 0.7
        if block_type in {'table_cell', 'table_header'}:
            evidence_score -= 0.1
        if block_type in {'heading', 'title'}:
            evidence_score += 0.05
        if block_type in {'ordered_list_item', 'unordered_list_item'}:
            evidence_score += 0.02
        return evidence_score

    def _apply_semantic_clues_terminology(self, evidence_score: float, found: str, preferred: str, text: str, context: Dict[str, Any]) -> float:
        content_type = (context or {}).get('content_type', 'general')
        domain = (context or {}).get('domain', 'general')
        audience = (context or {}).get('audience', 'general')

        # Formal/technical content expects preferred terminology
        if content_type in {'technical', 'api', 'procedural'}:
            evidence_score += 0.08
        if content_type in {'academic', 'legal'}:
            evidence_score += 0.12
        if content_type in {'marketing', 'narrative'}:
            evidence_score += 0.04

        # Domain-specific adjustments
        if domain in {'software', 'engineering', 'devops'}:
            evidence_score += 0.05
        if domain in {'legal', 'finance', 'medical'}:
            evidence_score += 0.05

        # Audience
        if audience in {'beginner', 'general'}:
            evidence_score += 0.05

        # Historical/legacy context — reduce if explicitly referencing past terms
        legacy_indicators = {'legacy', 'formerly known as', 'previously called', 'historical term', 'old terminology'}
        text_lower = text.lower()
        if any(ind in text_lower for ind in legacy_indicators):
            evidence_score -= 0.1

        return evidence_score

    def _apply_feedback_clues_terminology(self, evidence_score: float, found: str, context: Dict[str, Any]) -> float:
        patterns = self._get_cached_feedback_patterns_terminology()
        f = found.lower()
        if f in patterns.get('accepted_terms', set()):
            evidence_score -= 0.3
        if f in patterns.get('often_flagged_terms', set()):
            evidence_score += 0.1
        # Content-type specific
        ctype = (context or {}).get('content_type', 'general')
        pc = patterns.get(f'{ctype}_patterns', {})
        if f in pc.get('accepted', set()):
            evidence_score -= 0.1
        if f in pc.get('flagged', set()):
            evidence_score += 0.1
        return evidence_score

    def _get_cached_feedback_patterns_terminology(self) -> Dict[str, Any]:
        return {
            'accepted_terms': set(),
            'often_flagged_terms': {'e-mail', 'web site', 'dialog box'},
            'technical_patterns': {
                'accepted': set(),
                'flagged': {'dialog box', 'web site'}
            },
            'marketing_patterns': {
                'accepted': set(),
                'flagged': {'e-mail'}
            }
        }

    # === SMART MESSAGING ===

    def _get_contextual_terminology_message(self, found: str, preferred: str, evidence_score: float) -> str:
        if evidence_score > 0.85:
            return f"Non-preferred term '{found}' detected. Use '{preferred}'."
        if evidence_score > 0.6:
            return f"Consider using preferred term '{preferred}' instead of '{found}'."
        return f"Preferred term '{preferred}' is recommended instead of '{found}' for consistency."

    def _generate_smart_terminology_suggestions(self, found: str, preferred: str, evidence_score: float, sentence, context: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        suggestions.append(f"Replace '{found}' with '{preferred}'.")
        # If quoted or code-like, suggest caution
        if '"' in sentence.text or "'" in sentence.text or '`' in sentence.text:
            suggestions.append("If this is a quoted label or code/UI string, consider keeping the original term.")
        suggestions.append("Align terminology with IBM Style for consistency across documents.")
        return suggestions[:3]
