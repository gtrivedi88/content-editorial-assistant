"""
Pronouns Rule (Consolidated)
Based on IBM Style Guide topic: "Pronouns"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule
from spacy.tokens import Doc

class PronounsRule(BaseLanguageRule):
    """
    Checks for a comprehensive set of pronoun-related style issues, including:
    1. Use of gender-specific pronouns.
    2. Ambiguous pronoun references (e.g., unclear 'it' or 'this').
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'pronouns'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for gender-specific and ambiguous pronouns.
        """
        errors = []
        if not nlp:
            return errors
        
        doc = nlp(text)
        sents = list(doc.sents)
        
        gendered_pronouns = {'he', 'him', 'his', 'she', 'her'}

        for i, sent in enumerate(sents):
            # --- Rule 1: Gender-Specific Pronouns ---
            for token in sent:
                if token.lemma_.lower() in gendered_pronouns:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Gender-specific pronoun '{token.text}' used.",
                        suggestions=["Use gender-neutral language. Consider rewriting with 'they' or addressing the user directly with 'you'."],
                        severity='medium',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))

            # --- Rule 2: Ambiguous Pronouns ('it', 'this') ---
            # Linguistic Anchor: Check for sentences starting with 'It is', 'It's', or 'This'.
            # This is a heuristic that becomes more reliable when the previous sentence is complex.
            if sent.text.lower().startswith(("it is", "it's", "this")):
                if i > 0: # Ensure there is a previous sentence
                    prev_sent = sents[i-1]
                    # Heuristic: If the previous sentence has multiple nouns, the pronoun is more likely to be ambiguous.
                    noun_count = sum(1 for token in prev_sent if token.pos_ == 'NOUN')
                    if noun_count > 1:
                        pronoun_token = sent[0]
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=f"Ambiguous pronoun: '{pronoun_token.text}' may have an unclear antecedent.",
                            suggestions=[f"Replace '{pronoun_token.text}' with the specific noun to improve clarity."],
                            severity='low',
                            span=(pronoun_token.idx, pronoun_token.idx + len(pronoun_token.text)),
                            flagged_text=pronoun_token.text
                        ))
        return errors

    # This is a placeholder for the base class method
    def _create_error(self, **kwargs) -> Dict[str, Any]:
        return kwargs
