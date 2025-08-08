"""
Spelling Rule
Based on IBM Style Guide topic: "Spelling"
"""
from typing import List, Dict, Any
import re
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class SpellingRule(BaseLanguageRule):
    """
    Checks for common non-US spellings and suggests the preferred US spelling,
    as required by the IBM Style Guide.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'spelling'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for common non-US English spellings.
        Calculates a nuanced evidence score for each detected case using
        linguistic, structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        doc = nlp(text)

        spelling_map = {
            "centre": "center", "colour": "color", "flavour": "flavor",
            "licence": "license", "organise": "organize", "analyse": "analyze",
            "catalogue": "catalog", "dialogue": "dialog", "grey": "gray",
            "behaviour": "behavior", "programme": "program",
        }

        for i, sent in enumerate(doc.sents):
            for non_us, us_spelling in spelling_map.items():
                pattern = r'\b' + re.escape(non_us) + r'\b'
                for match in re.finditer(pattern, sent.text, re.IGNORECASE):
                    char_start = sent.start_char + match.start()
                    char_end = sent.start_char + match.end()
                    matched_text = match.group(0)

                    # Try to find a spaCy token that aligns with the match
                    token = None
                    for t in sent:
                        if t.idx == char_start and t.idx + len(t.text) == char_end:
                            token = t
                            break

                    evidence_score = self._calculate_spelling_evidence(
                        non_us=matched_text,
                        us=us_spelling,
                        token=token,
                        sentence=sent,
                        text=text,
                        context=context or {}
                    )

                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=self._get_contextual_spelling_message(matched_text, us_spelling, evidence_score),
                            suggestions=self._generate_smart_spelling_suggestions(matched_text, us_spelling, evidence_score, sent, context or {}),
                            severity='medium',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(char_start, char_end),
                            flagged_text=matched_text
                        ))

        return errors

    # === EVIDENCE-BASED CALCULATION ===

    def _calculate_spelling_evidence(self, non_us: str, us: str, token, sentence, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence (0.0-1.0) that non-US spelling should be corrected to US style."""
        # Base evidence for non-US spelling presence
        evidence_score: float = 0.6

        # Linguistic clues (micro)
        evidence_score = self._apply_linguistic_clues_spelling(evidence_score, token, sentence)

        # Structural clues (meso)
        evidence_score = self._apply_structural_clues_spelling(evidence_score, context)

        # Semantic clues (macro)
        evidence_score = self._apply_semantic_clues_spelling(evidence_score, non_us, us, text, context)

        # Feedback clues (learning)
        evidence_score = self._apply_feedback_clues_spelling(evidence_score, non_us, context)

        return max(0.0, min(1.0, evidence_score))

    # === CLUE APPLICATION METHODS ===

    def _apply_linguistic_clues_spelling(self, evidence_score: float, token, sentence) -> float:
        # Quoted text often reports speech; reduce impact
        if '"' in sentence.text or "'" in sentence.text:
            evidence_score -= 0.1

        # Named entities that are organizations/products should not be corrected
        if token is not None:
            ent_type = getattr(token, 'ent_type_', '')
            if ent_type in {'ORG', 'PRODUCT', 'WORK_OF_ART'}:
                evidence_score -= 0.6

            # All caps likely an acronym/brand
            if token.text.isupper() and len(token.text) <= 10:
                evidence_score -= 0.4

            # If the token is part of inline code via backticks in sentence
            # (crude heuristic): reduce
            if '`' in sentence.text:
                evidence_score -= 0.2

        return evidence_score

    def _apply_structural_clues_spelling(self, evidence_score: float, context: Dict[str, Any]) -> float:
        block_type = (context or {}).get('block_type', 'paragraph')
        if block_type in {'code_block', 'literal_block'}:
            return evidence_score - 0.9
        if block_type == 'inline_code':
            return evidence_score - 0.7
        if block_type in {'table_cell', 'table_header'}:
            evidence_score -= 0.1
        if block_type == 'heading':
            evidence_score += 0.05
        return evidence_score

    def _apply_semantic_clues_spelling(self, evidence_score: float, non_us: str, us: str, text: str, context: Dict[str, Any]) -> float:
        content_type = (context or {}).get('content_type', 'general')
        domain = (context or {}).get('domain', 'general')
        audience = (context or {}).get('audience', 'general')

        # IBM Style: prefer US spellings broadly; slightly stronger in formal docs
        if content_type in {'api', 'technical', 'legal', 'academic'}:
            evidence_score += 0.1
        if content_type in {'marketing', 'narrative'}:
            evidence_score += 0.05

        if domain in {'legal', 'finance', 'medical'}:
            evidence_score += 0.05

        # If document shows strong UK indicators, reduce evidence slightly
        uk_indicators = {'behaviour', 'colour', 'organise', 'licence', 'programme', 'grey'}
        text_lower = text.lower()
        if sum(1 for w in uk_indicators if w in text_lower) >= 3:
            evidence_score -= 0.15

        # Audience: general/beginner should adhere more strictly for consistency
        if audience in {'beginner', 'general'}:
            evidence_score += 0.05

        return evidence_score

    def _apply_feedback_clues_spelling(self, evidence_score: float, non_us: str, context: Dict[str, Any]) -> float:
        patterns = self._get_cached_feedback_patterns_spelling()
        if non_us.lower() in patterns.get('accepted_non_us_terms', set()):
            evidence_score -= 0.3
        if non_us.lower() in patterns.get('often_flagged_non_us', set()):
            evidence_score += 0.1
        return evidence_score

    def _get_cached_feedback_patterns_spelling(self) -> Dict[str, Any]:
        return {
            'accepted_non_us_terms': {
                # Common product/project names that intentionally use British variants
                'greylog', 'dialogflow'
            },
            'often_flagged_non_us': {'colour', 'organise', 'programme'}
        }

    # === SMART MESSAGING ===

    def _get_contextual_spelling_message(self, non_us: str, us: str, evidence_score: float) -> str:
        if evidence_score > 0.85:
            return f"Non-US spelling '{non_us}' detected. IBM Style prefers US spelling: '{us}'."
        if evidence_score > 0.6:
            return f"Consider using US spelling '{us}' instead of '{non_us}'."
        return f"US spelling '{us}' is preferred over '{non_us}' for consistency."

    def _generate_smart_spelling_suggestions(self, non_us: str, us: str, evidence_score: float, sentence, context: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        suggestions.append(f"Replace '{non_us}' with '{us}'.")
        # If in quotes/code-like context, suggest alternative handling
        if '"' in sentence.text or "'" in sentence.text or '`' in sentence.text:
            suggestions.append("If this is a quoted name or code, consider leaving as-is.")
        # General guidance
        suggestions.append("Ensure consistent US spelling throughout the document.")
        return suggestions[:3]
