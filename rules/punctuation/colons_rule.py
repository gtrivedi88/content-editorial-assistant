"""
Colons Rule
Based on IBM Style Guide topic: "Colons"

**UPDATED** with a bug fix for SpaCy's span indexing to prevent crashes.
"""
from typing import List, Dict, Any, Optional
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens import Doc, Token, Span
except ImportError:
    Doc = None
    Token = None
    Span = None

class ColonsRule(BasePunctuationRule):
    """
    Checks for incorrect colon usage using dependency parsing, now with robust
    indexing and structural awareness.
    """
    def _get_rule_type(self) -> str:
        return 'colons'

    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        errors = []
        context = context or {}
        if not nlp:
            return errors

        is_list_introduction = context.get('is_list_introduction', False)
        if is_list_introduction:
            return []

        try:
            doc = nlp(text)
            for i, sent in enumerate(doc.sents):
                for token in sent:
                    if token.text == ':':
                        if self._is_legitimate_context(token, sent) or self._is_legitimate_context_aware(token, sent, context):
                            continue
                        if not self._is_preceded_by_complete_clause(token, sent):
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message="Incorrect colon usage: A colon must be preceded by a complete independent clause.",
                                suggestions=["Rewrite the text before the colon to form a complete sentence.", "Remove the colon if it is not introducing a list, quote, or explanation."],
                                severity='high',
                                span=(token.idx, token.idx + len(token.text)),
                                flagged_text=token.text
                            ))
        except IndexError as e:
            # This catch is a safeguard in case of unexpected SpaCy behavior
            errors.append(self._create_error(
                sentence=text,
                sentence_index=0,
                message=f"Rule ColonsRule failed with an indexing error: {e}",
                suggestions=["This may be a bug in the rule. Please report it."],
                severity='low'
            ))
        return errors

    def _is_legitimate_context(self, colon_token: Token, sent: Span) -> bool:
        """
        Uses linguistic anchors to identify legitimate colon contexts.
        This version uses safe, sentence-relative indexing.
        """
        # colon_token.i is the index in the parent doc.
        # sent.start is the start index of the sentence in the parent doc.
        # So, the token's index *within the sentence* is:
        token_sent_idx = colon_token.i - sent.start

        # Check for time/ratios (e.g., 3:30, 2:1)
        if 0 < token_sent_idx < len(sent) - 1:
            prev_token = sent[token_sent_idx - 1]
            next_token = sent[token_sent_idx + 1]
            if prev_token.like_num and next_token.like_num:
                return True

        # Check for URLs (e.g., http:)
        if "http" in colon_token.head.text.lower():
            return True

        # Check for Title: Subtitle patterns
        if colon_token.head.pos_ in ("NOUN", "PROPN") and colon_token.head.is_title:
             if token_sent_idx < len(sent) - 1 and sent[token_sent_idx + 1].is_title:
                return True

        return False

    def _is_preceded_by_complete_clause(self, colon_token: Token, sent: Span) -> bool:
        """
        Checks if tokens before the colon form a complete independent clause.
        This version uses safe, sentence-relative indexing.
        """
        if colon_token.i <= sent.start:
            return False

        # Create a new doc object from the span before the colon for accurate parsing
        clause_span = sent.doc[sent.start : colon_token.i]
        clause_doc = clause_span.as_doc()

        has_subject = any(t.dep_ in ('nsubj', 'nsubjpass') for t in clause_doc)
        has_root_verb = any(t.dep_ == 'ROOT' for t in clause_doc)
        
        # Check if a verb directly precedes the colon
        token_sent_idx = colon_token.i - sent.start
        verb_before_colon = False
        if token_sent_idx > 0:
            verb_before_colon = sent[token_sent_idx - 1].pos_ == "VERB"

        return has_subject and has_root_verb and not verb_before_colon

    def _is_legitimate_context_aware(self, colon_token: Token, sent: Span, context: Optional[Dict[str, Any]]) -> bool:
        """
        LINGUISTIC ANCHOR: Context-aware colon legitimacy checking using structural information.
        Uses inter-block context to determine if colons are introducing content like admonitions.
        """
        if not context:
            return False
        
        # If this block introduces an admonition, colons are legitimate
        if context.get('next_block_type') == 'admonition':
            return True
        
        # If we're in a list introduction context, colons are legitimate
        if context.get('is_list_introduction', False):
            return True
        
        return False
