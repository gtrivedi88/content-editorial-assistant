"""
Pronouns Rule (Consolidated)
Based on IBM Style Guide topic: "Pronouns"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class PronounsRule(BaseLanguageRule):
    """
    Checks for specific pronoun style issues:
    1. Use of gender-specific pronouns in technical writing.
    
    Note: Ambiguous pronoun detection is handled by the more sophisticated
    PronounAmbiguityDetector in the ambiguity module to avoid duplication.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'pronouns'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for gender-specific pronouns.
        Calculates a nuanced evidence score for each candidate pronoun
        considering linguistic, structural, semantic, and feedback clues.
        
        Note: Ambiguous reference resolution is handled by the ambiguity module.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        doc = nlp(text)
        gendered_pronouns = {'he', 'him', 'his', 'she', 'her', 'hers'}

        for i, sent in enumerate(doc.sents):
            for token in sent:
                lemma_lower = getattr(token, 'lemma_', '').lower()
                if lemma_lower in gendered_pronouns and getattr(token, 'pos_', '') in {'PRON', 'DET'}:
                    evidence_score = self._calculate_pronoun_evidence(token, sent, text, context or {})
                    if evidence_score > 0.1:
                        message = self._get_contextual_pronouns_message(token, evidence_score, sent)
                        suggestions = self._generate_smart_pronouns_suggestions(token, evidence_score, sent, context or {})
                        severity = 'high' if evidence_score > 0.75 else 'medium'

                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=message,
                            suggestions=suggestions,
                            severity=severity,
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
        return errors

    # === EVIDENCE-BASED CALCULATION ===

    def _calculate_pronoun_evidence(self, token, sentence, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence (0.0-1.0) that a gendered pronoun is non-inclusive."""
        # Base evidence: gendered pronoun present
        evidence_score: float = 0.6

        # Linguistic clues
        evidence_score = self._apply_linguistic_clues_pronouns(evidence_score, token, sentence)

        # Structural clues
        evidence_score = self._apply_structural_clues_pronouns(evidence_score, context)

        # Semantic clues
        evidence_score = self._apply_semantic_clues_pronouns(evidence_score, token, sentence, text, context)

        # Feedback-based clues
        evidence_score = self._apply_feedback_clues_pronouns(evidence_score, token, context)

        return max(0.0, min(1.0, evidence_score))

    # === CLUE APPLICATION METHODS ===

    def _apply_linguistic_clues_pronouns(self, evidence_score: float, token, sentence) -> float:
        """Micro-level linguistic adjustments."""
        token_text = getattr(token, 'text', '')
        lemma_lower = getattr(token, 'lemma_', '').lower()
        dep = getattr(token, 'dep_', '')

        # Possessive determiners (his/her) in attributive use are often easy to replace
        if lemma_lower in {'his', 'her'} and dep in {'det', 'poss'}:
            evidence_score += 0.1

        # Quoted speech may be reporting; reduce impact
        in_quotes = '"' in sentence.text or "'" in sentence.text
        if in_quotes:
            evidence_score -= 0.1

        # Nearby generic roles raise evidence
        sent_lower = sentence.text.lower()
        if any(term in sent_lower for term in {'user', 'developer', 'administrator', 'person', 'individual', 'customer', 'client'}):
            evidence_score += 0.15

        # Nearby named entities of type PERSON reduces evidence (specific reference)
        has_person_ner = any(getattr(t, 'ent_type_', '') == 'PERSON' for t in sentence)
        if has_person_ner:
            evidence_score -= 0.2

        # Avoid double penalizing if plural/generic already present
        if any(t.lemma_.lower() in {'they', 'them', 'their'} for t in sentence):
            evidence_score -= 0.05

        return evidence_score

    def _apply_structural_clues_pronouns(self, evidence_score: float, context: Dict[str, Any]) -> float:
        block_type = (context or {}).get('block_type', 'paragraph')

        if block_type in {'code_block', 'literal_block'}:
            return evidence_score - 0.7  # Do not flag inside code blocks
        if block_type == 'inline_code':
            return evidence_score - 0.5
        if block_type in {'table_cell', 'table_header', 'heading'}:
            evidence_score -= 0.1

        admonition = (context or {}).get('admonition_type', '').upper()
        if block_type == 'admonition' and admonition in {'NOTE', 'TIP'}:
            evidence_score -= 0.05

        return evidence_score

    def _apply_semantic_clues_pronouns(self, evidence_score: float, token, sentence, text: str, context: Dict[str, Any]) -> float:
        content_type = (context or {}).get('content_type', 'general')
        domain = (context or {}).get('domain', 'general')
        audience = (context or {}).get('audience', 'general')

        # Inclusive expectation is higher in technical, API, and docs aimed at broad audiences
        if content_type in {'technical', 'api', 'procedural'}:
            evidence_score += 0.05
        if content_type in {'marketing'}:
            evidence_score += 0.05
        if content_type in {'legal', 'academic'}:
            evidence_score += 0.1

        if audience in {'beginner', 'general'}:
            evidence_score += 0.05
        elif audience in {'developer', 'expert'}:
            evidence_score += 0.0

        # Domain: formal domains stricter
        if domain in {'legal', 'finance', 'medical'}:
            evidence_score += 0.05

        # If sentence contains explicit inclusive alternatives, reduce evidence
        sent_lower = sentence.text.lower()
        if any(phrase in sent_lower for phrase in {"they/them", 'use inclusive language'}):
            evidence_score -= 0.1

        return evidence_score

    def _apply_feedback_clues_pronouns(self, evidence_score: float, token, context: Dict[str, Any]) -> float:
        patterns = self._get_cached_feedback_patterns_pronouns()
        token_lower = getattr(token, 'text', '').lower()
        if token_lower in patterns.get('often_ignored', set()):
            evidence_score -= 0.1
        if token_lower in patterns.get('often_flagged', set()):
            evidence_score += 0.1
        return evidence_score

    def _get_cached_feedback_patterns_pronouns(self) -> Dict[str, Any]:
        return {
            'often_ignored': set(),
            'often_flagged': {'his', 'her'},
        }

    # === SMART MESSAGING ===

    def _get_contextual_pronouns_message(self, token, evidence_score: float, sentence) -> str:
        t = getattr(token, 'text', '')
        if evidence_score > 0.85:
            return f"Gender-specific pronoun '{t}' used in a generic or instructional context. Prefer inclusive alternatives."
        if evidence_score > 0.6:
            return f"Gender-specific pronoun '{t}' detected. Consider using inclusive language."
        return f"Consider replacing '{t}' with a gender-neutral alternative for broader inclusivity."

    def _generate_smart_pronouns_suggestions(self, token, evidence_score: float, sentence, context: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        t = getattr(token, 'text', '')

        # Direct replacement options
        suggestions.append("Use 'they/them/their' where grammatically appropriate.")
        suggestions.append("Address the reader as 'you' when giving instructions.")

        # Structural rewrite
        suggestions.append("Rewrite to remove the pronoun by repeating the noun or restructuring the clause.")

        return suggestions[:3]
