"""
Abbreviations Rule (Enhanced with Evidence-Based Scoring)
Based on IBM Style Guide topic: "Abbreviations"
"""
import re
from typing import List, Dict, Any, Set, Optional
# Assuming base_language_rule.py is in the same directory or a reachable path
from .base_language_rule import BaseLanguageRule 

try:
    from spacy.tokens import Doc, Token
except ImportError:
    # Define dummy classes if spaCy is not available to allow the script to be parsed
    Doc = type('Doc', (object,), {})
    Token = type('Token', (object,), {})

class AbbreviationsRule(BaseLanguageRule):
    """
    Checks for multiple abbreviation-related style issues using a nuanced,
    evidence-based scoring system to achieve high accuracy and minimize false positives.
    It detects:
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
        document_signature = hashlib.md5(text[:200].encode()).hexdigest()
        
        if self.current_document_hash != document_signature:
            self.defined_abbreviations.clear()
            self.current_document_hash = document_signature

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Orchestrates the analysis of the full text for abbreviation violations.
        It identifies potential candidates and delegates to specialized "detective"
        methods to calculate an evidence score for each potential violation.
        """
        errors = []
        if not nlp:
            return errors

        self._reset_document_state_if_needed(text)
        doc = nlp(text)
        
        # --- Orchestration ---
        # Loop through every token once and check for all possible violations.
        for token in doc:
            # First, handle definitions to update our state
            if self._is_abbreviation_candidate(token) and self._is_definition_pattern(token, doc):
                self.defined_abbreviations.add(token.text)
                continue

            # --- Detective Call 1: Latin Abbreviations ---
            latin_evidence_score = self._calculate_latin_abbreviation_evidence(token, doc, context)
            if latin_evidence_score > 0.1: # Threshold to create an error for evaluation
                errors.append(self._create_latin_abbreviation_error(token, latin_evidence_score, text, context))

            # --- Detective Call 2: Undefined First Use ---
            if token.text not in self.defined_abbreviations:
                undefined_evidence_score = self._calculate_undefined_abbreviation_evidence(token, doc, context)
                if undefined_evidence_score > 0.1:
                    errors.append(self._create_undefined_abbreviation_error(token, undefined_evidence_score, text, context))
                    # Mark as "defined" to avoid re-flagging it
                    self.defined_abbreviations.add(token.text)

            # --- Detective Call 3: Abbreviation Used as a Verb ---
            verb_evidence_score = self._calculate_verb_usage_evidence(token, doc, context)
            if verb_evidence_score > 0.1:
                errors.append(self._create_verb_usage_error(token, verb_evidence_score, text, context))
        
        return errors

    # ==========================================================================
    # === EVIDENCE-BASED CALCULATION METHODS (The "Detectives") ==============
    # ==========================================================================

    def _calculate_latin_abbreviation_evidence(self, token: Token, doc: Doc, context: Optional[Dict[str, Any]]) -> float:
        """
        Detective #1: Calculates the evidence score (0.0 to 1.0) for Latin abbreviation violations.
        """
        # STEP 1: BASE EVIDENCE ASSESSMENT
        if not self._is_latin_abbreviation(token, doc):
            return 0.0
        evidence_score = 0.7  # Start with moderate evidence.

        # STEP 2: GATHER MITIGATING & AGGRAVATING CLUES
        
        # Clue (Structural): Is it inside parentheses? This is more acceptable.
        if self._is_in_parenthetical_context(token, doc):
            evidence_score -= 0.3  # Moderate mitigator.
        else:
            # Clue (Aggravating): Used outside parentheses is a stronger violation.
            evidence_score += 0.2
            
        # Clue (Semantic): Is the content academic or legal? More common there.
        # This check would be powered by your ContentTypeDetector.
        content_type = context.get('content_type', 'general') if context else 'general'
        if content_type in ['academic', 'legal']:
            evidence_score -= 0.3 # Strong mitigator.
        elif content_type in ['marketing', 'general']:
            evidence_score += 0.2 # Strong aggravator for general audiences.

        return max(0.0, min(1.0, evidence_score))

    def _calculate_undefined_abbreviation_evidence(self, token: Token, doc: Doc, context: Optional[Dict[str, Any]]) -> float:
        """
        Detective #2: Calculates the evidence score for undefined abbreviation violations.
        """
        # STEP 1: BASE EVIDENCE ASSESSMENT
        if not self._is_abbreviation_candidate(token):
            return 0.0
        evidence_score = 0.8  # Start with HIGH evidence. An undefined acronym is usually an error.

        # STEP 2: GATHER MITIGATING CLUES (Reasons it might NOT be an error)

        # Clue (Semantic): Is it a universally known acronym? Strongest mitigator.
        common_acronyms = {'API', 'URL', 'HTTP', 'SDK', 'SQL', 'JSON', 'XML', 'CPU', 'RAM', 'HTML', 'CSS'}
        if token.text in common_acronyms:
            evidence_score -= 0.8  # Drastically reduce score. This is almost never an error.

        # Clue (Linguistic): Is it already defined in the immediate context? (e.g., "Full Form (ABBR)")
        if self._is_contextually_defined(token, doc):
            evidence_score -= 0.9  # This is a definition, so it's definitively not an error.

        # Clue (Linguistic): Is it being used as a compound modifier? (e.g., "API key")
        if token.dep_ == 'compound':
            evidence_score -= 0.3  # Moderate mitigator.

        # Clue (Structural): Is the abbreviation in a heading? Often a product name.
        if context and context.get('block_type') == 'heading':
            evidence_score -= 0.4  # Strong mitigator.

        # Clue (Structural): Is it in a less formal context like a NOTE or TIP?
        if self._is_admonition_context(token, context):
            evidence_score -= 0.2  # Minor mitigator.

        # STEP 3: GATHER AGGRAVATING CLUES (Reasons it's MORE LIKELY an error)

        # Clue (Linguistic): Is the abbreviation the subject of a sentence?
        if token.dep_ == 'nsubj':
            evidence_score += 0.15  # Moderate aggravator.

        # Clue (Semantic): Is the content for a beginner audience?
        if context and context.get('audience') == 'beginner':
            evidence_score += 0.2 # Strong aggravator.

        return max(0.0, min(1.0, evidence_score))

    def _calculate_verb_usage_evidence(self, token: Token, doc: Doc, context: Optional[Dict[str, Any]]) -> float:
        """
        Detective #3: Calculates the evidence score for abbreviation-as-verb violations.
        """
        # STEP 1: BASE EVIDENCE ASSESSMENT
        if not self._is_used_as_verb(token, doc):
            return 0.0
        evidence_score = 0.9  # Start with very high evidence.

        # STEP 2: GATHER MITIGATING CLUES
        
        # Clue (Semantic): Is it a rare but accepted verb form?
        accepted_verb_forms = {'FTP', 'SSH'} # e.g., "to FTP the file"
        if token.text in accepted_verb_forms:
            evidence_score -= 0.7 # Strong mitigator. This is likely acceptable usage.
            
        # Clue (Structural): Is it in a code block? Syntax rules are different.
        if context and context.get('block_type') in ['code_block', 'inline_code']:
            evidence_score -= 0.8 # Very strong mitigator.

        return max(0.0, min(1.0, evidence_score))

    # ==========================================================================
    # === HELPER METHODS (The Detective's Tools) ===============================
    # ==========================================================================

    def _is_latin_abbreviation(self, token: Token, doc: Doc) -> bool:
        text_lower = token.text.lower().rstrip('.')
        latin_terms = {'e.g', 'eg', 'i.e', 'ie', 'etc', 'et al', 'vs', 'cf'}
        return text_lower in latin_terms

    def _is_abbreviation_candidate(self, token: Token) -> bool:
        if (token.is_upper and len(token.text) >= 2 and token.text.isalpha() and not token.is_stop):
            if token.ent_type_ in ['PERSON', 'GPE']:
                return False
            return True
        return False

    def _is_used_as_verb(self, token: Token, doc: Doc) -> bool:
        if token.pos_ == 'VERB': return True
        if token.dep_ in ['ROOT', 'ccomp', 'xcomp'] and any(c.dep_ in ['dobj', 'nsubj'] for c in token.children): return True
        if token.i > 0 and doc[token.i - 1].tag_ == 'MD': return True # Preceded by modal verb
        return False
        
    def _is_contextually_defined(self, token: Token, doc: Doc) -> bool:
        # Pattern: "Full Name (ABBR)"
        if token.i > 1 and doc[token.i - 1].text == ')' and self._is_abbreviation_in_parens(token, doc):
            return True
        return False

    def _is_definition_pattern(self, token: Token, doc: Doc) -> bool:
        # Check if abbreviation is inside parentheses after a multi-word phrase
        if token.i > 2 and doc[token.i - 1].text == '(' and doc[token.i + 1].text == ')':
            # Check if the words before the parenthesis look like a definition
            words_before = [t for t in doc[token.i-4:token.i-1] if t.is_alpha]
            if len(words_before) >= 2:
                return True
        return False
        
    def _is_abbreviation_in_parens(self, token: Token, doc: Doc) -> bool:
        # Simplified check for "Full Name (ABBR)" pattern
        if token.i > 2 and doc[token.i-1].text == ')' and doc[token.i-2].text == token.text and doc[token.i-3].text == '(':
            return True
        return False

    def _is_in_parenthetical_context(self, token: Token, doc: Doc) -> bool:
        # This is a simplified check
        return (token.i > 0 and doc[token.i - 1].text == '(') or \
               (token.i < len(doc) - 1 and doc[token.i + 1].text == ')')

    def _is_admonition_context(self, token: Token, context: Optional[Dict[str, Any]]) -> bool:
        if not context: return False
        if context.get('block_type') == 'admonition': return True
        admonition_keywords = {'NOTE', 'TIP', 'IMPORTANT', 'WARNING', 'CAUTION'}
        if token.text in admonition_keywords: return True
        return False

    # ==========================================================================
    # === ERROR CREATION HELPERS ===============================================
    # ==========================================================================

    def _create_latin_abbreviation_error(self, token, evidence_score, text, context):
        replacement = self._get_latin_equivalent(token.text.lower())
        return self._create_error(
            sentence=token.sent.text,
            sentence_index=list(token.doc.sents).index(token.sent),
            message=f"Consider replacing the Latin abbreviation '{token.text}'.",
            suggestions=[f"Use its English equivalent, such as '{replacement}'."],
            severity='low', text=text, context=context,
            evidence_score=evidence_score,
            span=(token.idx, token.idx + len(token.text)), flagged_text=token.text
        )

    def _create_undefined_abbreviation_error(self, token, evidence_score, text, context):
        return self._create_error(
            sentence=token.sent.text,
            sentence_index=list(token.doc.sents).index(token.sent),
            message=f"Abbreviation '{token.text}' may not be defined on first use.",
            suggestions=[f"If '{token.text}' is not a commonly known abbreviation, spell it out on its first use, followed by the abbreviation in parentheses. For example: 'Application Programming Interface (API)'."],
            severity='medium', text=text, context=context,
            evidence_score=evidence_score,
            span=(token.idx, token.idx + len(token.text)), flagged_text=token.text
        )

    def _create_verb_usage_error(self, token, evidence_score, text, context):
        action_verb = self._get_semantic_action(token.text.lower())
        suggestion = f"Rewrite the sentence to use a proper verb. For example, instead of '...to {token.text} the file', write '...to {action_verb} the file using {token.text}'."
        return self._create_error(
            sentence=token.sent.text,
            sentence_index=list(token.doc.sents).index(token.sent),
            message=f"Avoid using the abbreviation '{token.text}' as a verb.",
            suggestions=[suggestion],
            severity='medium', text=text, context=context,
            evidence_score=evidence_score,
            span=(token.idx, token.idx + len(token.text)), flagged_text=token.text
        )
        
    def _get_latin_equivalent(self, latin_term: str) -> str:
        equivalents = {'e.g': 'for example', 'eg': 'for example', 'i.e': 'that is', 'ie': 'that is', 'etc': 'and so on', 'vs': 'versus', 'cf': 'compare'}
        return equivalents.get(latin_term.rstrip('.'), 'an English equivalent')
        
    def _get_semantic_action(self, abbreviation: str) -> str:
        actions = {'ftp': 'transfer', 'sftp': 'transfer', 'ssh': 'connect to', 'telnet': 'connect to', 'http': 'access', 'https': 'access'}
        return actions.get(abbreviation, 'use')

