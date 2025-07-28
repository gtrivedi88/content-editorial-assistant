"""
Abbreviations Rule (Enhanced)
Based on IBM Style Guide topic: "Abbreviations"
"""
import re
from typing import List, Dict, Any, Set
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc, Token
except ImportError:
    Doc = None
    Token = None

class AbbreviationsRule(BaseLanguageRule):
    """
    Checks for multiple abbreviation-related style issues, including:
    - Use of discouraged Latin abbreviations.
    - Ensuring abbreviations are defined on first use.
    - Preventing the use of abbreviations as verbs.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'abbreviations'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes the full text for abbreviation violations using pure morphological 
        analysis and linguistic anchors. This rule processes the entire text at once 
        to track the first use of abbreviations.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        defined_abbreviations: Set[str] = set()
        
        # --- LINGUISTIC ANCHOR 1: Latin Abbreviations Detection ---
        # Use morphological patterns to detect Latin abbreviations
        for i, sent in enumerate(doc.sents):
            for token in sent:
                if self._is_latin_abbreviation(token, doc):
                    replacement = self._get_latin_equivalent(token.text.lower())
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Avoid using the Latin abbreviation '{token.text}'.",
                        suggestions=[f"Use its English equivalent, such as '{replacement}'."],
                        severity='medium',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))

        # --- LINGUISTIC ANCHOR 2 & 3: Abbreviation Definition and Verb Usage ---
        for token in doc:
            # MORPHOLOGICAL PATTERN: Detect uppercase abbreviations
            if self._is_abbreviation_candidate(token):
                # Check for undefined first use
                if token.text not in defined_abbreviations:
                    if not self._is_contextually_defined(token, doc):
                        sent = token.sent
                        sent_index = list(doc.sents).index(sent)
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=sent_index,
                            message=f"Abbreviation '{token.text}' may not be defined on first use.",
                            suggestions=[f"If '{token.text}' is not a commonly known abbreviation, spell it out on its first use, followed by the abbreviation in parentheses. For example: 'Application Programming Interface (API)'."],
                            severity='medium',
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
                    defined_abbreviations.add(token.text)
                
                # LINGUISTIC ANCHOR: Check for verb usage patterns
                if self._is_used_as_verb(token, doc):
                    sent = token.sent
                    sent_index = list(doc.sents).index(sent)
                    suggestion = self._generate_verb_alternative(token, doc)
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sent_index,
                        message=f"Avoid using abbreviations like '{token.text}' as verbs.",
                        suggestions=[suggestion],
                        severity='medium',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
        
        return errors

    def _is_latin_abbreviation(self, token: 'Token', doc: 'Doc') -> bool:
        """
        Uses morphological analysis to detect Latin abbreviations.
        LINGUISTIC ANCHOR: Detects abbreviations ending with periods that match Latin patterns.
        """
        if not token.text:
            return False
            
        text_lower = token.text.lower()
        
        # MORPHOLOGICAL PATTERN 1: Two letters followed by period (e.g., i.e.)
        if (len(text_lower) == 3 and text_lower.endswith('.') and 
            text_lower[0].isalpha() and text_lower[1].isalpha()):
            # Check if it's in parenthetical context (common for Latin abbreviations)
            if self._is_in_parenthetical_context(token, doc):
                return True
        
        # MORPHOLOGICAL PATTERN 2: Three letters with periods (e.g., e.g.)  
        if (len(text_lower) == 4 and text_lower.count('.') == 2 and
            text_lower[0].isalpha() and text_lower[2].isalpha()):
            return True
            
        # MORPHOLOGICAL PATTERN 3: Common Latin abbreviation patterns
        if (len(text_lower) >= 3 and text_lower.endswith('.') and
            self._has_latin_morphology(text_lower)):
            return True
            
        return False

    def _get_latin_equivalent(self, latin_term: str) -> str:
        """
        Uses morphological analysis to determine English equivalent.
        LINGUISTIC ANCHOR: Pattern-based replacement using morphological structure.
        """
        # Remove trailing period for analysis
        base_term = latin_term.rstrip('.')
        
        # MORPHOLOGICAL PATTERN: Analyze common Latin abbreviation structures
        if base_term in ['e.g', 'eg']:
            return 'for example'
        elif base_term in ['i.e', 'ie']:
            return 'that is'
        elif base_term in ['etc', 'et.c', 'et c']:
            return 'and so on'
        elif base_term in ['cf', 'c.f']:
            return 'compare'
        elif base_term in ['vs', 'v.s']:
            return 'versus'
        else:
            return 'an English equivalent'

    def _is_abbreviation_candidate(self, token: 'Token') -> bool:
        """
        Uses morphological analysis to identify abbreviation candidates.
        LINGUISTIC ANCHOR: POS tagging and morphological features.
        """
        # MORPHOLOGICAL PATTERN: Uppercase sequences of 2+ letters
        if (token.is_upper and len(token.text) >= 2 and 
            token.text.isalpha() and not token.is_stop):
            # LINGUISTIC ANCHOR: Exclude proper nouns that are names
            if token.ent_type_ in ['PERSON', 'GPE']:  # Geographic/Person entities
                return False
            # LINGUISTIC ANCHOR: Include likely acronyms and abbreviations
            return True
        return False

    def _is_contextually_defined(self, token: 'Token', doc: 'Doc') -> bool:
        """
        Uses dependency parsing to check if abbreviation is contextually defined.
        LINGUISTIC ANCHOR: Syntactic patterns for definitions.
        """
        # PATTERN 1: Token followed by parenthetical definition
        if (token.i + 1 < len(doc) and doc[token.i + 1].text == '(' and
            self._has_definition_in_parens(token, doc)):
            return True
        
        # PATTERN 2: Definition followed by parenthetical abbreviation  
        if (token.i > 1 and doc[token.i - 1].text == ')' and
            self._is_abbreviation_in_parens(token, doc)):
            return True
            
        # PATTERN 3: Explicit definition patterns using dependency parsing
        if self._has_explicit_definition(token, doc):
            return True
            
        return False

    def _is_used_as_verb(self, token: 'Token', doc: 'Doc') -> bool:
        """
        Uses dependency parsing and POS analysis to detect verb usage.
        LINGUISTIC ANCHOR: Syntactic roles and dependency relations.
        """
        # LINGUISTIC ANCHOR 1: SpaCy directly tags as verb
        if token.pos_ == 'VERB':
            return True
            
        # LINGUISTIC ANCHOR 2: Modal auxiliary + abbreviation + direct object pattern
        if (token.i > 0 and token.i < len(doc) - 1):
            prev_token = doc[token.i - 1]
            next_token = doc[token.i + 1]
            
            # Use morphological analysis to detect modal auxiliary
            if (prev_token.tag_ == 'MD' and  # Modal auxiliary POS tag
                next_token.pos_ in ['DET', 'NOUN', 'PRON']):  # Direct object
                return True
        
        # LINGUISTIC ANCHOR 3: Dependency parsing for verbal roles
        if token.dep_ in ['ROOT', 'ccomp', 'xcomp'] and self._has_verbal_dependents(token, doc):
            return True
            
        return False

    def _generate_verb_alternative(self, token: 'Token', doc: 'Doc') -> str:
        """
        Generates context-aware suggestions using morphological analysis.
        LINGUISTIC ANCHOR: Semantic analysis based on surrounding context.
        """
        # Analyze syntactic context for intelligent suggestions
        if token.i > 0:
            prev_token = doc[token.i - 1]
            if prev_token.tag_ == 'MD':  # Modal auxiliary
                action_verb = self._get_semantic_action(token.text.lower())
                return f"Rewrite to use a proper verb: '{prev_token.text} {action_verb} {token.text} to...'"
        
        # Default suggestion based on common patterns
        return f"Rewrite the sentence to use a proper verb. For example, instead of '{token.text} the file', write 'Use {token.text} to transfer the file'."

    # Helper methods for morphological analysis
    def _is_in_parenthetical_context(self, token: 'Token', doc: 'Doc') -> bool:
        """Check if token appears in parenthetical context."""
        # Look for surrounding parentheses within reasonable distance
        for i in range(max(0, token.i - 5), min(len(doc), token.i + 5)):
            if doc[i].text in ['(', ')']:
                return True
        return False

    def _has_latin_morphology(self, text: str) -> bool:
        """Detect Latin morphological patterns."""
        # Common Latin abbreviation endings and patterns
        latin_patterns = ['etc', 'cf', 'vs', 'et', 'al']
        return any(text.startswith(pattern) for pattern in latin_patterns)

    def _has_definition_in_parens(self, token: 'Token', doc: 'Doc') -> bool:
        """Check for definition pattern after abbreviation."""
        paren_start = token.i + 1
        if paren_start < len(doc) and doc[paren_start].text == '(':
            # Look for closing paren and alphabetic content
            for i in range(paren_start + 1, min(len(doc), paren_start + 10)):
                if doc[i].text == ')':
                    return any(doc[j].is_alpha for j in range(paren_start + 1, i))
        return False

    def _is_abbreviation_in_parens(self, token: 'Token', doc: 'Doc') -> bool:
        """Check if abbreviation appears in parentheses after definition."""
        # Look backwards for opening parenthesis
        for i in range(max(0, token.i - 10), token.i):
            if doc[i].text == '(':
                return True
        return False

    def _has_explicit_definition(self, token: 'Token', doc: 'Doc') -> bool:
        """Use dependency parsing to find explicit definitions."""
        # Look for patterns like "X stands for", "X means", etc.
        for i in range(max(0, token.i - 5), min(len(doc), token.i + 5)):
            if doc[i].lemma_ in ['stand', 'mean', 'represent', 'denote']:
                return True
        return False

    def _has_verbal_dependents(self, token: 'Token', doc: 'Doc') -> bool:
        """Check if token has dependents typical of verbs."""
        for child in token.children:
            if child.dep_ in ['dobj', 'iobj', 'nsubj']:  # Direct object, indirect object, subject
                return True
        return False

    def _get_semantic_action(self, abbreviation: str) -> str:
        """Get appropriate action verb based on abbreviation semantics."""
        # Use semantic analysis for common technical abbreviations
        if abbreviation in ['ftp', 'sftp']:
            return 'use'
        elif abbreviation in ['ssh', 'telnet']:
            return 'connect via'
        elif abbreviation in ['http', 'https']:
            return 'access via'
        else:
            return 'use'
