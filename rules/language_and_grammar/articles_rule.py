"""
Articles Rule (with True Linguistic Analysis)
Based on IBM Style Guide topic: "Articles"
"""
from typing import List, Dict, Any
import pyinflect
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc, Token
except ImportError:
    Doc = None
    Token = None

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

        content_classification = self._get_content_classification(text, context, nlp)
        if not self._should_apply_rule(self._get_rule_category(), content_classification):
            return errors

        doc = nlp(text)
        for i, sent in enumerate(doc.sents):
            for token in sent:
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
        if word_lower.startswith(('user', 'unit', 'one', 'uniform')): return False
        if word_lower.startswith(('hour', 'honest', 'honor')): return True
        return word_lower[0] in 'aeiou'

    def _is_incorrect_article_usage(self, article_token: Token, next_token: Token) -> bool:
        if 'attributeplaceholder' in next_token.text or 'asciidoclinkplaceholder' in next_token.text:
            return False
        starts_with_vowel = self._starts_with_vowel_sound(next_token.text)
        if article_token.lower_ == 'a' and starts_with_vowel: return True
        if article_token.lower_ == 'an' and not starts_with_vowel: return True
        return False

    def _is_uncountable(self, token: Token) -> bool:
        lemma = token.lemma_
        plural_form = pyinflect.getInflection(lemma, 'NNS')
        return plural_form is None

    def _is_missing_article_candidate(self, token: Token, doc: Doc) -> bool:
        # LINGUISTIC ANCHOR 1: Basic POS and morphology checks.
        if not (token.pos_ == 'NOUN' and token.tag_ == 'NN' and not self._is_uncountable(token)):
            return False
            
        # LINGUISTIC ANCHOR 2: Check for existing determiners or possessives.
        if any(child.dep_ in ('det', 'poss') for child in token.children) or token.dep_ == 'poss':
            return False

        # LINGUISTIC ANCHOR 3: Check for grammatical contexts where articles are not used.
        if token.dep_ == 'compound':
            return False
        if token.lemma_.lower() == 'step' and token.i + 1 < len(doc) and doc[token.i + 1].like_num:
            return False
            
        # LINGUISTIC ANCHOR 3a: Technical terms in prepositional phrases (existing logic)
        if token.dep_ == 'pobj':
            prep = token.head
            if prep.lemma_ in ['in', 'on', 'at', 'by', 'before', 'after'] and prep.head.pos_ == 'VERB':
                if token.lemma_ in ['bold', 'italic', 'deployment', 'substitution', 'text']:
                    return False
        
        # LINGUISTIC ANCHOR 3b: Compound technical phrases (NEW)
        if self._is_technical_compound_phrase(token, doc):
            return False
            
        # LINGUISTIC ANCHOR 3c: Technical terms in coordinated constructions (NEW)
        if self._is_technical_coordination(token, doc):
            return False
        
        # LINGUISTIC ANCHOR 4: The noun must be in a role that typically requires an article.
        if token.dep_ in ('nsubj', 'dobj', 'pobj', 'attr'):
            if token.i > 0 and ('attributeplaceholder' in doc[token.i - 1].text or 'asciidoclinkplaceholder' in doc[token.i - 1].text):
                return False
            return True
            
        return False

    def _is_technical_compound_phrase(self, token: Token, doc: Doc) -> bool:
        """
        Detects technical compound phrases where articles are typically omitted.
        Examples: "attribute substitution", "error handling", "data processing"
        """
        # Define technical terms commonly used without articles
        technical_terms = {
            'substitution', 'text', 'bold', 'italic', 'deployment', 'configuration',
            'analysis', 'processing', 'handling', 'formatting', 'styling', 'parsing',
            'validation', 'authentication', 'authorization', 'encryption', 'compression',
            'optimization', 'integration', 'implementation', 'documentation', 'testing',
            'debugging', 'monitoring', 'logging', 'caching', 'indexing', 'rendering',
            'compilation', 'execution', 'initialization', 'installation', 'backup',
            'recovery', 'migration', 'synchronization', 'serialization', 'deserialization'
        }
        
        if token.lemma_.lower() not in technical_terms:
            return False
        
        # Check if this noun is modified by technical adjectives or other nouns
        technical_modifiers = {
            'attribute', 'parameter', 'configuration', 'system', 'data', 'file',
            'database', 'network', 'security', 'user', 'admin', 'server', 'client',
            'application', 'service', 'component', 'module', 'library', 'framework',
            'algorithm', 'protocol', 'interface', 'api', 'endpoint', 'resource',
            'metadata', 'schema', 'template', 'pattern', 'model', 'structure',
            'format', 'syntax', 'semantic', 'logical', 'physical', 'virtual',
            'dynamic', 'static', 'automatic', 'manual', 'custom', 'default',
            'basic', 'advanced', 'complex', 'simple', 'standard', 'extended',
            'paragraph'  # Added for "paragraph analysis"
        }
        
        # Look for technical modifiers in children (adjectives or noun modifiers)
        for child in token.children:
            if (child.pos_ in ('ADJ', 'NOUN') and 
                child.dep_ in ('amod', 'nmod', 'compound') and
                child.lemma_.lower() in technical_modifiers):
                return True
        
        # Look for technical modifiers as siblings in coordinated structures
        if token.dep_ == 'dobj':
            # Check siblings that are coordinated or modify the same head
            for sibling in token.head.children:
                if (sibling != token and sibling.pos_ in ('ADJ', 'NOUN') and
                    sibling.dep_ in ('amod', 'nmod') and
                    sibling.lemma_.lower() in technical_modifiers):
                    return True
        
        return False

    def _is_technical_coordination(self, token: Token, doc: Doc) -> bool:
        """
        Detects when a technical term is part of a coordination with other technical terms.
        Examples: "analysis and substitution", "formatting and styling"
        """
        technical_terms = {
            'substitution', 'text', 'bold', 'italic', 'deployment', 'configuration',
            'analysis', 'processing', 'handling', 'formatting', 'styling', 'parsing',
            'validation', 'authentication', 'authorization', 'encryption', 'compression',
            'optimization', 'integration', 'implementation', 'documentation', 'testing',
            'debugging', 'monitoring', 'logging', 'caching', 'indexing', 'rendering'
        }
        
        if token.lemma_.lower() not in technical_terms:
            return False
        
        # Check if this token is part of a coordination (conj dependency)
        if token.dep_ == 'conj':
            # Check if it's coordinated with another technical term
            head = token.head
            if head.lemma_.lower() in technical_terms:
                return True
        
        # Check if this token has technical terms as conjuncts
        for child in token.children:
            if (child.dep_ == 'conj' and 
                child.pos_ == 'NOUN' and
                child.lemma_.lower() in technical_terms):
                return True
        
        return False
