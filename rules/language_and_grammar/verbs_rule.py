"""
Verbs Rule (Consolidated and Enhanced)
Based on IBM Style Guide topics: "Verbs: Tense", "Verbs: Voice", "Verbs: Person"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule
import re

# Assuming spacy.tokens.Doc is available
try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class VerbsRule(BaseLanguageRule):
    """
    Checks for a comprehensive set of verb-related style issues.
    NOTE: The specific check for 'setup' vs 'set up' has been moved to the
    s_words_rule.py to eliminate redundant error reporting.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'verbs'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for passive voice, tense, and specific verb usage violations.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        for i, sent in enumerate(doc.sents):
            # --- Rule 1: Passive Voice Check ---
            is_passive = any(token.dep_ in ('nsubjpass', 'auxpass') for token in sent)
            if is_passive:
                passive_verb = next((tok for tok in sent if tok.dep_ in ('nsubjpass', 'auxpass')), sent.root)
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Sentence may be in the passive voice.",
                    suggestions=["Rewrite in the active voice to be more direct. For example, change 'The button was clicked by the user' to 'The user clicked the button'."],
                    severity='medium',
                    span=(passive_verb.idx, passive_verb.idx + len(passive_verb.text)),
                    flagged_text=passive_verb.text
                ))

            # --- Rule 2: Future Tense Check ('will') ---
            for token in sent:
                if token.lemma_.lower() == "will" and token.tag_ == "MD":
                    head_verb = token.head
                    if head_verb.pos_ == "VERB":
                        suggestion = f"Use the present tense '{head_verb.lemma_}s' or the imperative mood '{head_verb.lemma_.capitalize()}'."
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message="Avoid future tense in procedural and descriptive text.",
                            suggestions=[suggestion],
                            severity='medium',
                            span=(token.idx, head_verb.idx + len(head_verb.text)),
                            flagged_text=f"{token.text} {head_verb.text}"
                        ))

            # --- Rule 3: Past Tense Check ---
            root_verb = sent.root
            if root_verb.pos_ == 'VERB' and root_verb.morph.get("Tense") == ["Past"]:
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Sentence may not be in the preferred present tense.",
                    suggestions=["Use present tense for instructions and system descriptions."],
                    severity='low',
                    span=(root_verb.idx, root_verb.idx + len(root_verb.text)),
                    flagged_text=root_verb.text
                ))

            # --- Rule 4: Check for "login" used as a verb ---
            for token in sent:
                if token.text.lower() == 'login' and token.pos_ == 'VERB':
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message="Use 'log in' (two words) as a verb, not 'login' (one word).",
                        suggestions=["Change 'Login to the server' to 'Log in to the server'. Use 'login' as a noun only (e.g., 'Enter your login credentials')."],
                        severity='medium',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
        return errors

    # This is a placeholder for the base class method
    def _create_error(self, **kwargs) -> Dict[str, Any]:
        return kwargs
