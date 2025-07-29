"""
Articles Rule (with True Linguistic Analysis)
Based on IBM Style Guide topic: "Articles"
"""
from typing import List, Dict, Any
import pyinflect
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ArticlesRule(BaseLanguageRule):
    """
    Checks for common article errors. This version uses true linguistic
    analysis to distinguish between countable and uncountable (mass) nouns.
    """
    def _get_rule_type(self) -> str:
        return 'articles'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        # ENTERPRISE CONTEXT INTELLIGENCE: Check if article rules should apply
        content_classification = self._get_content_classification(text, context, nlp)
        should_apply = self._should_apply_rule(self._get_rule_category(), content_classification)
        
        if not should_apply:
            return errors  # Skip for list items, labels, technical terms

        doc = nlp(text)

        for i, sent in enumerate(doc.sents):
            for token in sent:
                # Rule 1: 'a' vs 'an'
                if token.lower_ in ['a', 'an'] and token.i + 1 < len(doc):
                    next_token = doc[token.i + 1]
                    if self._is_incorrect_article_usage(token, next_token):
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=i,
                            message=f"Incorrect article usage: Use '{'an' if self._starts_with_vowel_sound(next_token.text) else 'a'}' before '{next_token.text}'.",
                            suggestions=[f"Change '{token.text} {next_token.text}' to '{'an' if self._starts_with_vowel_sound(next_token.text) else 'a'} {next_token.text}'."],
                            severity='medium',
                            span=(token.idx, next_token.idx + len(next_token.text)),
                            flagged_text=f"{token.text} {next_token.text}"
                        ))
                
                # Rule 2: Missing Articles (only for descriptive content)
                if content_classification == 'descriptive_content' and self._is_missing_article_candidate(token, doc):
                    errors.append(self._create_error(
                        sentence=sent.text, sentence_index=i,
                        message=f"Potentially missing article before the noun '{token.text}'.",
                        suggestions=["Singular countable nouns often require an article (a/an/the). Please review."],
                        severity='low',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
        return errors

    def _starts_with_vowel_sound(self, word: str) -> bool:
        word_lower = word.lower()
        if word_lower.startswith(('user', 'unit', 'one', 'uniform')):
            return False
        if word_lower.startswith(('hour', 'honest', 'honor')):
            return True
        return word_lower[0] in 'aeiou'

    def _is_incorrect_article_usage(self, article_token, next_token) -> bool:
        # PRODUCTION-GRADE FIX: If the next token is an attribute placeholder, we cannot determine
        # correctness, so we skip the check to avoid false positives.
        if 'attributeplaceholder' in next_token.text:
            return False

        starts_with_vowel = self._starts_with_vowel_sound(next_token.text)
        if article_token.lower_ == 'a' and starts_with_vowel:
            return True
        if article_token.lower_ == 'an' and not starts_with_vowel:
            return True
        return False

    def _is_uncountable(self, token) -> bool:
        lemma = token.lemma_
        plural_form = pyinflect.getInflection(lemma, 'NNS')
        return plural_form is None

    def _is_missing_article_candidate(self, token, doc) -> bool:
        # PRODUCTION-GRADE FIX: Do not flag missing articles for the placeholder itself.
        if 'attributeplaceholder' in token.text:
            return False

        if token.dep_ == 'compound' or (token.i > 0 and doc[token.i - 1].lower_ == 'to'):
            return False
        if token.pos_ == 'NOUN' and token.tag_ == 'NN':
            # PRODUCTION-GRADE FIX: If the previous token was a placeholder, an article might
            # have been correct for the original attribute. Don't flag the noun.
            if token.i > 0 and 'attributeplaceholder' in doc[token.i - 1].text:
                return False

            if any(child.dep_ in ('det', 'poss') for child in token.children):
                return False
            if self._is_uncountable(token):
                return False
            if token.dep_ in ('nsubj', 'dobj', 'pobj'):
                return True
        return False
