"""
Abbreviations Rule (Enhanced)
Based on IBM Style Guide topic: "Abbreviations"
"""
import re
from typing import List, Dict, Any, Set, Optional
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
    def __init__(self):
        """Initialize the abbreviations rule with document-level state management."""
        super().__init__()
        # Document-level state to track defined abbreviations across blocks
        self.defined_abbreviations: Set[str] = set()
        self.current_document_hash: Optional[str] = None

    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'abbreviations'

    def _reset_document_state_if_needed(self, text: str) -> None:
        """
        Reset abbreviation state for new documents based on content hash.
        This ensures state persists across blocks within the same document
        but resets for different documents.
        """
        import hashlib
        
        # Create a simple hash of the first 200 characters to detect new documents
        # This is more reliable than trying to detect document boundaries
        document_signature = hashlib.md5(text[:200].encode()).hexdigest()
        
        if self.current_document_hash != document_signature:
            # New document - reset state
            self.defined_abbreviations.clear()
            self.current_document_hash = document_signature

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes the full text for abbreviation violations using pure morphological 
        analysis and linguistic anchors. This rule processes the entire text at once 
        to track the first use of abbreviations.
        """
        errors = []
        if not nlp:
            return errors

        # Reset state for new documents, preserve state within same document
        self._reset_document_state_if_needed(text)
        
        doc = nlp(text)
        
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
                        text=text,  # Enhanced: Pass full text for better confidence analysis
                        context=context,  # Enhanced: Pass context for domain-specific validation
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))

        # --- LINGUISTIC ANCHOR 2 & 3: Abbreviation Definition and Verb Usage ---
        for token in doc:
            # MORPHOLOGICAL PATTERN: Detect uppercase abbreviations
            if self._is_abbreviation_candidate(token):
                # First, check if this token is a definition (e.g., inside parentheses after full text)
                if self._is_definition_pattern(token, doc):
                    # This is a definition - mark it as defined
                    self.defined_abbreviations.add(token.text)
                    continue
                
                # Check for undefined first use
                if token.text not in self.defined_abbreviations:
                    # LINGUISTIC ANCHOR: Context-aware abbreviation checking
                    if not self._is_contextually_defined(token, doc) and not self._is_admonition_context(token, context):
                        sent = token.sent
                        sent_index = list(doc.sents).index(sent)
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=sent_index,
                            message=f"Abbreviation '{token.text}' may not be defined on first use.",
                            suggestions=[f"If '{token.text}' is not a commonly known abbreviation, spell it out on its first use, followed by the abbreviation in parentheses. For example: 'Application Programming Interface (API)'."],
                            severity='medium',
                            text=text,  # Enhanced: Pass full text for better confidence analysis
                            context=context,  # Enhanced: Pass context for domain-specific validation
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
                    self.defined_abbreviations.add(token.text)
                
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
                        text=text,  # Enhanced: Pass full text for better confidence analysis
                        context=context,  # Enhanced: Pass context for domain-specific validation
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
        """
        Check if abbreviation appears in parentheses after its definition.
        Pattern: "Full Name (ABBR)" where ABBR should not be flagged.
        """
        # Check if we're immediately after a closing parenthesis
        if token.i == 0 or doc[token.i - 1].text != ')':
            return False
        
        # Find the matching opening parenthesis
        paren_depth = 1
        open_paren_idx = None
        
        for i in range(token.i - 2, -1, -1):  # Start from before the closing paren
            if doc[i].text == ')':
                paren_depth += 1
            elif doc[i].text == '(':
                paren_depth -= 1
                if paren_depth == 0:
                    open_paren_idx = i
                    break
        
        if open_paren_idx is None:
            return False
        
        # Check if the text inside parentheses matches our abbreviation
        inside_parens = doc[open_paren_idx + 1:token.i - 1]
        inside_text = ''.join([t.text_with_ws for t in inside_parens]).strip()
        
        return inside_text == token.text

    def _is_definition_pattern(self, token: 'Token', doc: 'Doc') -> bool:
        """
        Check if this abbreviation is being defined (inside parentheses after full form).
        Pattern: "Full Name (ABBR)" - detect when we encounter ABBR inside parens.
        """
        # Check if we're inside parentheses
        if token.i == 0:
            return False
        
        # Look backwards to find if we're inside parentheses
        in_parens = False
        open_paren_idx = None
        
        for i in range(token.i - 1, -1, -1):
            if doc[i].text == ')':
                # Found closing paren before us - we're not in parens
                return False
            elif doc[i].text == '(':
                # Found opening paren - we might be in a definition
                in_parens = True
                open_paren_idx = i
                break
        
        if not in_parens:
            return False
        
        # Look forward to find the closing parenthesis
        close_paren_idx = None
        for i in range(token.i + 1, len(doc)):
            if doc[i].text == '(':
                # Nested parens - not a simple definition pattern
                return False
            elif doc[i].text == ')':
                close_paren_idx = i
                break
        
        if close_paren_idx is None:
            return False
        
        # Check if there's substantial text before the opening parenthesis
        # This should be the full form of the abbreviation
        if open_paren_idx > 0:
            text_before = doc[:open_paren_idx]
            # Should have at least 2 words to be a real definition
            word_count = len([t for t in text_before if t.is_alpha])
            return word_count >= 2
        
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

    def _is_admonition_context(self, token: 'Token', context: Optional[Dict[str, Any]]) -> bool:
        """
        LINGUISTIC ANCHOR: Context-aware admonition detection using structural information.
        Checks if we're in a context where admonition keywords are legitimate.
        """
        if not context:
            return False
        
        # Check if we're in an admonition block
        if context.get('block_type') == 'admonition':
            return True
        
        # Check if the next block is an admonition (introducing context)
        if context.get('next_block_type') == 'admonition':
            return True
        
        # Check if this is an admonition-related keyword
        admonition_keywords = {'NOTE', 'TIP', 'IMPORTANT', 'WARNING', 'CAUTION'}
        if token.text in admonition_keywords:
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
