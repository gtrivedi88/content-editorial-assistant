"""
Colons Rule
Based on IBM Style Guide topic: "Colons"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens import Doc, Token
except ImportError:
    Doc = None
    Token = None

class ColonsRule(BasePunctuationRule):
    """
    Checks for incorrect colon usage using dependency parsing to understand
    the colon's grammatical function. It identifies when a colon is used
    incorrectly after an incomplete clause or verb, while ignoring
    legitimate uses like time expressions, ratios, and titles.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'punctuation_colons'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for various colon usage violations.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        for i, sent in enumerate(doc.sents):
            for token in sent:
                if token.text == ':':
                    # First, check for legitimate contexts to avoid false positives.
                    if self._is_legitimate_context(token, sent):
                        continue

                    # Main Rule: A colon must follow a complete independent clause.
                    if not self._is_preceded_by_complete_clause(token, sent):
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message="Incorrect colon usage: A colon must be preceded by a complete clause.",
                            suggestions=["Rewrite the text before the colon to form a complete sentence.", "Remove the colon if it is not introducing a list, quote, or explanation."],
                            severity='high',
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
        return errors

    def _is_legitimate_context(self, colon_token: Token, sent: Doc) -> bool:
        """
        Uses linguistic anchors to identify legitimate colon contexts that should be ignored.
        """
        # Linguistic Anchor: Time expressions (e.g., 3:30 PM) and ratios (e.g., 5:1).
        if colon_token.i > sent.start and colon_token.i < sent.end - 1:
            prev_token = sent.doc[colon_token.i - 1]
            next_token = sent.doc[colon_token.i + 1]
            if prev_token.like_num and next_token.like_num:
                return True

        # Linguistic Anchor: Technical paths or URLs (e.g., http:).
        if "http" in colon_token.head.text.lower():
            return True

        # Linguistic Anchor: Title/subtitle patterns (e.g., "Chapter 1: Getting Started").
        if colon_token.head.pos_ in ("NOUN", "PROPN") and colon_token.head.is_title:
             if colon_token.i < sent.end - 1 and sent.doc[colon_token.i + 1].is_title:
                return True

        return False

    def _is_preceded_by_complete_clause(self, colon_token: Token, sent: Doc) -> bool:
        """
        Checks if the tokens before the colon form a complete independent clause.
        A complete clause must have a subject and a verb.
        """
        if colon_token.i == sent.start:
            return False

        # Analyze the part of the sentence before the colon.
        clause_before_colon = sent.doc[sent.start : colon_token.i]

        # Linguistic Anchor: A complete clause has a subject and a root verb.
        has_subject = any(token.dep_ in ('nsubj', 'nsubjpass') for token in clause_before_colon)
        has_root_verb = any(token.dep_ == 'ROOT' for token in clause_before_colon)
        
        # Also check for a common error pattern: a verb directly preceding the colon.
        verb_before_colon = sent.doc[colon_token.i - 1].pos_ == "VERB"

        return has_subject and has_root_verb and not verb_before_colon
