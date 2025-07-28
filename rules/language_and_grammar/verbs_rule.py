"""
Verbs Rule (Consolidated and Enhanced for Accuracy)
Based on IBM Style Guide topics: "Verbs: Tense", "Verbs: Voice"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc, Token
except ImportError:
    Doc = None
    Token = None

class VerbsRule(BaseLanguageRule):
    """
    Checks for verb-related style issues with high-accuracy linguistic checks
    to prevent false positives.
    """
    def _get_rule_type(self) -> str:
        return 'verbs'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        for i, sent_text in enumerate(sentences):
            if not sent_text.strip():
                continue
            
            doc = nlp(sent_text)
            
            # --- PRIORITY 1 FIX: High-Accuracy Passive Voice Check ---
            # This logic now iterates through each token to find a passive subject ('nsubjpass')
            # or a passive auxiliary verb ('auxpass'). This is a highly reliable
            # linguistic signal for passive voice and will not trigger on active sentences.
            passive_token = self._find_passive_token(doc)
            if passive_token:
                errors.append(self._create_error(
                    sentence=sent_text,
                    sentence_index=i,
                    message="Sentence may be in the passive voice.",
                    suggestions=["Rewrite in the active voice to be more direct. For example, change 'The button was clicked by the user' to 'The user clicked the button'."],
                    severity='medium',
                    flagged_text=passive_token.head.text
                ))

            # --- Future Tense Check ('will') ---
            for token in doc:
                if token.lemma_.lower() == "will" and token.tag_ == "MD":
                    head_verb = token.head
                    if head_verb.pos_ == "VERB":
                        suggestion = f"Use the present tense '{head_verb.lemma_}s' or the imperative mood '{head_verb.lemma_.capitalize()}'."
                        errors.append(self._create_error(
                            sentence=sent_text,
                            sentence_index=i,
                            message="Avoid future tense in procedural and descriptive text.",
                            suggestions=[suggestion],
                            severity='medium',
                            flagged_text=f"{token.text} {head_verb.text}"
                        ))

            # --- Past Tense Check ---
            root_verb = self._find_root_token(doc)
            if root_verb and root_verb.pos_ == 'VERB' and 'Tense=Past' in str(root_verb.morph):
                errors.append(self._create_error(
                    sentence=sent_text,
                    sentence_index=i,
                    message="Sentence may not be in the preferred present tense.",
                    suggestions=["Use present tense for instructions and system descriptions."],
                    severity='low',
                    flagged_text=root_verb.text
                ))
        
        return errors

    def _find_passive_token(self, doc: Doc) -> Token | None:
        """Finds the first token that indicates a passive construction."""
        for token in doc:
            if token.dep_ in ('nsubjpass', 'auxpass'):
                return token
        return None

    def _find_root_token(self, doc: Doc) -> Token | None:
        """Finds the root token of the sentence."""
        for token in doc:
            if token.dep_ == "ROOT":
                return token
        return None
