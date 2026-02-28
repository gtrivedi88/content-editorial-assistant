"""
Pronouns Rule — Deterministic SpaCy-based detection.
IBM Style Guide (Pages 109-111): Avoid first person, gender-specific pronouns,
and ambiguous pronoun references.
"""

from typing import List, Dict, Any, Optional
from .base_language_rule import BaseLanguageRule

# Citation auto-loaded from style_guides/ibm/ibm_style_mapping.yaml by BaseRule

# First-person pronouns to flag
FIRST_PERSON = {'i', 'me', 'my', 'mine', 'we', 'us', 'our', 'ours', 'myself', 'ourselves'}

# Gender-specific pronouns to flag
GENDER_SPECIFIC = {
    'he', 'him', 'his', 'himself',
    'she', 'her', 'hers', 'herself',
    'he/she', 'his/her', 'him/her', 's/he',
}

# Combined gender constructions
COMBINED_GENDER_PATTERNS = {'he or she', 'his or her', 'him or her', 'his or hers'}


class PronounsRule(BaseLanguageRule):
    """Detects first-person, gender-specific, and ambiguous pronoun references."""

    def __init__(self):
        super().__init__()

    def _get_rule_type(self) -> str:
        return 'pronouns'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        if context and context.get('block_type') in ['listing', 'literal', 'code_block', 'inline_code']:
            return []
        if not nlp and not spacy_doc:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors = []

        for token in doc:
            if token.pos_ != 'PRON' and token.pos_ != 'DET':
                continue

            # --- First-person pronoun check ---
            if token.lower_ in FIRST_PERSON:
                # Guard: quoted text, blog posts, FAQs, marketing
                if context and context.get('block_type') in ('quote', 'blockquote'):
                    continue
                # Guard: "we" in company context (IBM Style p.109: "we, us, our" for IBM)
                if token.lower_ in ('we', 'us', 'our', 'ours') and context and context.get('content_type') == 'marketing':
                    continue

                errors.append(self._create_error(
                    sentence=token.sent.text,
                    sentence_index=0,
                    message=f"Avoid first-person pronoun '{token.text}'. Use second person ('you') instead.",
                    suggestions=["Rewrite using 'you' or 'your', or use the imperative mood."],
                    severity='low',
                    text=text,
                    context=context,
                    flagged_text=token.text,
                    span=(token.idx, token.idx + len(token.text))
                ))
                continue

            # --- Gender-specific pronoun check ---
            if token.lower_ in GENDER_SPECIFIC:
                # Guard: if preceded by a proper name, gender pronoun is acceptable
                if self._follows_proper_name(token, doc):
                    continue

                errors.append(self._create_error(
                    sentence=token.sent.text,
                    sentence_index=0,
                    message=f"Avoid gender-specific pronoun '{token.text}'. Use gender-neutral language.",
                    suggestions=[
                        "Use 'they/them/their' for singular gender-neutral reference.",
                        "Rewrite using second person ('you') or the imperative mood."
                    ],
                    severity='medium',
                    text=text,
                    context=context,
                    flagged_text=token.text,
                    span=(token.idx, token.idx + len(token.text))
                ))

        return errors

    def _follows_proper_name(self, pronoun_token, doc) -> bool:
        """Check if a gender pronoun follows a proper name (acceptable per IBM Style)."""
        # Look backward in the same sentence for a PERSON entity
        for token in pronoun_token.sent:
            if token.i >= pronoun_token.i:
                break
            if token.ent_type_ == 'PERSON':
                return True
        return False
