"""
Commands Rule
Based on IBM Style Guide topic: "Commands"
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class CommandsRule(BaseTechnicalRule):
    """
    Checks for the incorrect use of command names as verbs.
    """
    def _get_rule_type(self) -> str:
        return 'technical_commands'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text to find command names used as verbs.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        command_words = {"import", "reorg", "export", "load", "install"}

        for i, sent in enumerate(doc.sents):
            for token in sent:
                # Linguistic Anchor: Check if a known command word is tagged as a verb.
                if token.lemma_.lower() in command_words and token.pos_ == 'VERB':
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Do not use the command name '{token.text}' as a verb.",
                        suggestions=[f"Rewrite the sentence to use an appropriate verb, e.g., 'To {token.lemma_} the data, use the {token.lemma_.upper()} command.'"],
                        severity='high',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
        return errors
