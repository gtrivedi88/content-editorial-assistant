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
        Analyzes the full text for abbreviation violations using evidence-based scoring.
        This rule processes the entire text at once to track the first use of abbreviations
        and calculates nuanced evidence scores for each potential violation.
        """
        errors = []
        if not nlp:
            return errors

        # Reset state for new documents, preserve state within same document
        self._reset_document_state_if_needed(text)
        
        doc = nlp(text)
        
        # --- EVIDENCE-BASED ANALYSIS 1: Latin Abbreviations ---
        for i, sent in enumerate(doc.sents):
            for token in sent:
                if self._is_latin_abbreviation(token, doc):
                    # Calculate evidence score for this Latin abbreviation
                    evidence_score = self._calculate_latin_abbreviation_evidence(
                        token, sent, text, context
                    )
                    
                    # Only create error if evidence suggests it's worth evaluating
                    if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                        replacement = self._get_latin_equivalent(token.text.lower())
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=self._get_contextual_message(token, evidence_score, 'latin'),
                            suggestions=self._generate_smart_suggestions(token, context, 'latin', replacement),
                            severity='medium',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,  # Your nuanced assessment
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))

        # --- EVIDENCE-BASED ANALYSIS 2 & 3: Abbreviation Definition and Verb Usage ---
        for token in doc:
            # MORPHOLOGICAL PATTERN: Detect uppercase abbreviations
            if self._is_abbreviation_candidate(token):
                # First, check if this token is a definition (e.g., inside parentheses after full text)
                if self._is_definition_pattern(token, doc):
                    # This is a definition - mark it as defined
                    self.defined_abbreviations.add(token.text)
                    continue
                
                # Check for undefined first use with evidence scoring
                if token.text not in self.defined_abbreviations:
                    # Calculate evidence score for undefined abbreviation
                    evidence_score = self._calculate_undefined_abbreviation_evidence(
                        token, token.sent, text, context
                    )
                    
                    # Only create error if evidence suggests it's worth evaluating
                    if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                        sent = token.sent
                        sent_index = list(doc.sents).index(sent)
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=sent_index,
                            message=self._get_contextual_message(token, evidence_score, 'undefined'),
                            suggestions=self._generate_smart_suggestions(token, context, 'undefined'),
                            severity='medium',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,  # Your nuanced assessment
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
                    self.defined_abbreviations.add(token.text)
                
                # Check for verb usage with evidence scoring
                if self._is_used_as_verb(token, doc):
                    # Calculate evidence score for verb usage
                    evidence_score = self._calculate_verb_usage_evidence(
                        token, token.sent, text, context
                    )
                    
                    # Only create error if evidence suggests it's worth evaluating
                    if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                        sent = token.sent
                        sent_index = list(doc.sents).index(sent)
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=sent_index,
                            message=self._get_contextual_message(token, evidence_score, 'verb'),
                            suggestions=self._generate_smart_suggestions(token, context, 'verb'),
                            severity='medium',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,  # Your nuanced assessment
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

    # === EVIDENCE-BASED CALCULATION METHODS ===

    def _calculate_latin_abbreviation_evidence(self, token: 'Token', sentence, text: str, context: Optional[Dict[str, Any]]) -> float:
        """
        Calculate evidence score (0.0-1.0) for Latin abbreviation violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            token: The potential Latin abbreviation token
            sentence: Sentence containing the token
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        if self._is_latin_abbreviation(token, token.doc):
            evidence_score = 0.5  # Start with lower base to preserve differentiation
        else:
            return 0.0  # No evidence, skip this token
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_latin(evidence_score, token, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_latin(evidence_score, token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_latin(evidence_score, token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_latin(evidence_score, token, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    def _calculate_undefined_abbreviation_evidence(self, token: 'Token', sentence, text: str, context: Optional[Dict[str, Any]]) -> float:
        """
        Calculate evidence score (0.0-1.0) for undefined abbreviation violations.
        
        Args:
            token: The potential undefined abbreviation token
            sentence: Sentence containing the token
            text: Full document text
            context: Document context
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === ZERO FALSE POSITIVE GUARD FOR UNIVERSAL ABBREVIATIONS ===
        # CRITICAL: If the term is universally known in technical contexts,
        # it is not an error. Return 0.0 immediately to prevent other clues
        # from incorrectly raising the evidence score.
        if self._is_universally_known_abbreviation(token.text):
            return 0.0
        
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        if self._is_abbreviation_candidate(token):
            evidence_score = 0.6  # Start with moderate evidence
        else:
            return 0.0  # No evidence, skip this token
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_undefined(evidence_score, token, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_undefined(evidence_score, token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_undefined(evidence_score, token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_undefined(evidence_score, token, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    def _calculate_verb_usage_evidence(self, token: 'Token', sentence, text: str, context: Optional[Dict[str, Any]]) -> float:
        """
        Calculate evidence score (0.0-1.0) for abbreviation-as-verb violations.
        
        Args:
            token: The potential verb abbreviation token
            sentence: Sentence containing the token
            text: Full document text
            context: Document context
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        if self._is_used_as_verb(token, token.doc):
            evidence_score = 0.8  # Start with high evidence for verb usage
        else:
            return 0.0  # No evidence, skip this token
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_verb(evidence_score, token, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_verb(evidence_score, token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_verb(evidence_score, token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_verb(evidence_score, token, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    # === LINGUISTIC CLUES (MICRO-LEVEL) ===

    def _apply_linguistic_clues_latin(self, evidence_score: float, token: 'Token', sentence) -> float:
        """Apply SpaCy-based linguistic analysis clues for Latin abbreviations."""
        
        # Check if in parenthetical context (common for Latin abbreviations)
        if self._is_in_parenthetical_context(token, token.doc):
            evidence_score += 0.2  # Often indicates legitimate usage
        
        # Check surrounding punctuation context
        prev_token = token.nbor(-1) if token.i > 0 else None
        next_token = token.nbor(1) if token.i < len(token.doc) - 1 else None
        
        if prev_token and prev_token.text == '(':
            evidence_score -= 0.3  # In parentheses often acceptable
        
        if next_token and next_token.text in ['.', ',', ';']:
            evidence_score += 0.1  # End of sentence/clause usage more formal
        
        # Check for formal writing patterns
        if token.text.lower() in ['i.e.', 'e.g.'] and next_token and next_token.text == ',':
            evidence_score += 0.2  # Classic formal usage pattern
        
        return evidence_score

    def _apply_linguistic_clues_undefined(self, evidence_score: float, token: 'Token', sentence) -> float:
        """Apply SpaCy-based linguistic analysis clues for undefined abbreviations."""
        
        # Named Entity Recognition - be selective about entity-based reductions
        # Only reduce for entities that are clearly proper nouns, not potential abbreviations
        if token.ent_type_ == 'PERSON':
            # Person names don't need definition
            evidence_score -= 0.6
        elif token.ent_type_ == 'GPE':
            # Geographic/political entities don't need definition
            evidence_score -= 0.6
        elif token.ent_type_ == 'ORG':
            # BE CAREFUL: Organizations can be abbreviations that need definition
            # Only reduce if it's clearly a proper organization name (contains lowercase)
            if any(c.islower() for c in token.text):
                evidence_score -= 0.6  # Proper org name like "Microsoft"
            else:
                evidence_score -= 0.1  # Could be abbreviation like "API", "IBM"
        elif token.ent_type_ == 'PRODUCT':
            # Product names often don't need definition
            evidence_score -= 0.4
        elif token.ent_type_ in ['MISC', 'EVENT']:
            evidence_score -= 0.2  # Miscellaneous entities, be conservative
        
        # Check if it's a common technical acronym
        if len(token.text) <= 5 and token.text.isupper():
            if self._is_common_technical_acronym(token.text):
                evidence_score -= 0.3  # Reduce, but not as aggressively
        
        # Check for contextual definition patterns
        if self._is_contextually_defined(token, token.doc):
            evidence_score -= 0.9  # Already defined in context
        
        # Check if in admonition context
        if self._is_admonition_context(token, None):
            evidence_score -= 0.2  # Reduce conservatively
        
        return evidence_score

    def _apply_linguistic_clues_verb(self, evidence_score: float, token: 'Token', sentence) -> float:
        """Apply SpaCy-based linguistic analysis clues for verb usage."""
        
        # Direct verbal POS tagging
        if token.pos_ == 'VERB':
            evidence_score += 0.2  # Strong linguistic evidence
        
        # Check dependency relations
        if token.dep_ == 'ROOT':
            evidence_score += 0.3  # Root verb is very strong evidence
        elif token.dep_ in ['ccomp', 'xcomp']:
            evidence_score += 0.2  # Complement verbs
        
        # Check for direct objects (strong verb indicator)
        has_direct_object = any(child.dep_ == 'dobj' for child in token.children)
        if has_direct_object:
            evidence_score += 0.3  # Very strong verb evidence
        
        # Check for modal auxiliary patterns
        prev_token = token.nbor(-1) if token.i > 0 else None
        if prev_token and prev_token.tag_ == 'MD':  # Modal auxiliary
            evidence_score += 0.2  # "can API", "will SSH" patterns
        
        return evidence_score

    # === STRUCTURAL CLUES (MESO-LEVEL) ===

    def _apply_structural_clues_latin(self, evidence_score: float, token: 'Token', context: Optional[Dict[str, Any]]) -> float:
        """Apply document structure-based clues for Latin abbreviations."""
        
        if not context:
            return evidence_score
        
        block_type = context.get('block_type', 'paragraph')
        
        # Academic/formal contexts are more accepting of Latin abbreviations
        if block_type in ['citation', 'bibliography', 'reference']:
            evidence_score -= 0.4  # Academic contexts accept Latin
        
        # Lists often use shorthand
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.2  # Lists more permissive
        
        # Footnotes and asides often use Latin
        elif block_type in ['footnote', 'aside', 'sidebar']:
            evidence_score -= 0.3  # Side content more permissive
        
        # Main content should avoid Latin abbreviations
        elif block_type == 'paragraph':
            evidence_score += 0.1  # Main content should be clearer
        
        return evidence_score

    def _apply_structural_clues_undefined(self, evidence_score: float, token: 'Token', context: Optional[Dict[str, Any]]) -> float:
        """Apply document structure-based clues for undefined abbreviations."""
        
        if not context:
            return evidence_score
        
        block_type = context.get('block_type', 'paragraph')
        
        # Headings often use abbreviated forms
        if block_type == 'heading':
            heading_level = context.get('block_level', 1)
            if heading_level == 1:  # H1 - Main headings
                evidence_score -= 0.4  # Product names, main concepts
            elif heading_level >= 2:  # H2+ - Section headings
                evidence_score -= 0.2  # Section-specific terms
        
        # Code and technical blocks
        elif block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.9  # Code blocks have different rules
        elif block_type == 'inline_code':
            evidence_score -= 0.6  # Inline code often technical
        
        # Table context
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.3  # Tables often use abbreviated terms
        
        return evidence_score

    def _apply_structural_clues_verb(self, evidence_score: float, token: 'Token', context: Optional[Dict[str, Any]]) -> float:
        """Apply document structure-based clues for verb usage."""
        
        if not context:
            return evidence_score
        
        block_type = context.get('block_type', 'paragraph')
        
        # Code blocks have different grammar rules
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.8  # Code has different syntax
        elif block_type == 'inline_code':
            evidence_score -= 0.5  # Inline code context
        
        # Headings rarely use verbs
        elif block_type == 'heading':
            evidence_score += 0.2  # Verbs in headings unusual
        
        # Commands and procedures might use imperative forms
        elif block_type in ['procedure', 'step']:
            evidence_score -= 0.2  # Procedural writing more imperative
        
        return evidence_score

    # === SEMANTIC CLUES (MACRO-LEVEL) ===

    def _apply_semantic_clues_latin(self, evidence_score: float, token: 'Token', text: str, context: Optional[Dict[str, Any]]) -> float:
        """Apply semantic and content-type clues for Latin abbreviations."""
        
        if not context:
            return evidence_score
        
        content_type = context.get('content_type', 'general')
        
        # Academic content more accepting of Latin
        if content_type == 'academic':
            evidence_score -= 0.3  # Academic writing has different norms
        
        # Legal writing traditionally uses Latin
        elif content_type == 'legal':
            evidence_score -= 0.2  # Legal writing traditionally formal
        
        # Technical documentation should be clear
        elif content_type == 'technical':
            evidence_score += 0.2  # Technical docs should be accessible
        
        # Marketing should be accessible
        elif content_type == 'marketing':
            evidence_score += 0.3  # Marketing should avoid Latin
        
        # Check audience level
        audience = context.get('audience', 'general')
        if audience in ['expert', 'academic']:
            evidence_score -= 0.2  # Expert audience may accept Latin
        elif audience in ['beginner', 'general']:
            evidence_score += 0.3  # General audience needs clarity
        
        return evidence_score

    def _apply_semantic_clues_undefined(self, evidence_score: float, token: 'Token', text: str, context: Optional[Dict[str, Any]]) -> float:
        """Apply semantic and content-type clues for undefined abbreviations."""
        
        if not context:
            return evidence_score
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')

        # For non-universal abbreviations, be much more conservative with reductions
        # These abbreviations SHOULD be flagged in most contexts
        
        # Only minimal reductions for expert technical content
        if content_type == 'technical' and audience in ['expert', 'developer']:
            evidence_score -= 0.05  # Very minimal reduction

        # Domain-specific contexts - be conservative
        if domain in ['software', 'engineering', 'devops']:
            evidence_score -= 0.05  # Minimal reduction for technical domains
        elif domain in ['finance', 'legal', 'medical']:
            evidence_score += 0.1  # Professional domains need clarity

        # Document length context - be more conservative
        doc_length = len(text.split())
        if doc_length < 50:  # Only very short documents get reduction
            evidence_score -= 0.05  # Minimal reduction for brief content
        elif doc_length > 2000:  # Long documents
            evidence_score += 0.1  # Consistency more important in long docs

        # Audience level - prioritize clarity
        if audience in ['beginner', 'general']:
            evidence_score += 0.2  # Strong boost for general audience

        # Brand/product context analysis
        if self._is_brand_product_context(token, text, context):
            evidence_score -= 0.3  # Moderate reduction for brand/product names
        
        return evidence_score

    def _apply_semantic_clues_verb(self, evidence_score: float, token: 'Token', text: str, context: Optional[Dict[str, Any]]) -> float:
        """Apply semantic and content-type clues for verb usage."""
        
        if not context:
            return evidence_score
        
        content_type = context.get('content_type', 'general')
        
        # Technical documentation often uses imperative forms
        if content_type == 'technical':
            # Check if this looks like a command or instruction
            if self._is_imperative_context(token, text):
                evidence_score -= 0.3  # Imperative usage more acceptable
        
        # Procedural content uses more verbs
        elif content_type == 'procedural':
            evidence_score -= 0.2  # Step-by-step instructions
        
        # Narrative content has different verb patterns
        elif content_type == 'narrative':
            evidence_score -= 0.1  # Storytelling context
        
        return evidence_score

    # === FEEDBACK PATTERNS (LEARNING CLUES) ===

    def _apply_feedback_clues_latin(self, evidence_score: float, token: 'Token', context: Optional[Dict[str, Any]]) -> float:
        """Apply clues learned from user feedback patterns for Latin abbreviations."""
        
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns('abbreviations')
        
        # Check if this specific Latin abbreviation is consistently accepted
        if token.text.lower() in feedback_patterns.get('accepted_latin_terms', set()):
            evidence_score -= 0.5  # Users consistently accept this
        
        # Check if users consistently reject flagging this
        if token.text.lower() in feedback_patterns.get('rejected_latin_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        return evidence_score

    def _apply_feedback_clues_undefined(self, evidence_score: float, token: 'Token', context: Optional[Dict[str, Any]]) -> float:
        """Apply clues learned from user feedback patterns for undefined abbreviations."""
        
        feedback_patterns = self._get_cached_feedback_patterns('abbreviations')
        
        # Check if this abbreviation is consistently accepted without definition
        if token.text in feedback_patterns.get('accepted_undefined_terms', set()):
            evidence_score -= 0.6  # Users consistently accept without definition
        
        # Industry-specific accepted terms
        if context:
            industry = context.get('industry', 'general')
            industry_terms = feedback_patterns.get(f'{industry}_accepted_abbreviations', set())
            if token.text in industry_terms:
                evidence_score -= 0.4
        
        return evidence_score

    def _apply_feedback_clues_verb(self, evidence_score: float, token: 'Token', context: Optional[Dict[str, Any]]) -> float:
        """Apply clues learned from user feedback patterns for verb usage."""
        
        feedback_patterns = self._get_cached_feedback_patterns('abbreviations')
        
        # Check if this verb usage is consistently accepted
        if token.text.lower() in feedback_patterns.get('accepted_verb_abbreviations', set()):
            evidence_score -= 0.5  # Users consistently accept this usage
        
        return evidence_score

    # Removed _get_cached_feedback_patterns - using base class utility

    # === HELPER METHODS FOR EVIDENCE CALCULATION ===

    def _is_common_technical_acronym(self, text: str) -> bool:
        """Check if this is a commonly known technical acronym."""
        common_acronyms = {
            'API', 'SDK', 'HTTP', 'HTTPS', 'URL', 'JSON', 'XML', 'HTML', 'CSS', 'JS',
            'SQL', 'TCP', 'UDP', 'SSH', 'FTP', 'REST', 'SOAP', 'CRUD', 'GUI', 'CLI',
            'IDE', 'OS', 'CPU', 'GPU', 'RAM', 'SSD', 'HDD', 'USB', 'PDF', 'CSV'
        }
        return text.upper() in common_acronyms

    def _count_technical_density(self, text: str) -> int:
        """Count the density of technical terms in the text."""
        technical_terms = [
            'api', 'sdk', 'json', 'xml', 'http', 'https', 'html', 'css', 'sql',
            'database', 'server', 'client', 'protocol', 'framework', 'library',
            'algorithm', 'function', 'method', 'class', 'object', 'interface',
            'deployment', 'configuration', 'authentication', 'authorization'
        ]
        
        text_lower = text.lower()
        count = sum(1 for term in technical_terms if term in text_lower)
        return count

    def _is_universally_known_abbreviation(self, text: str) -> bool:
        """Check if this is a universally known abbreviation that might not need definition."""
        # Very common abbreviations that are widely understood
        # Should be conservative - only truly universal terms
        universal_abbreviations = {
            # Original
            'HTTP', 'HTTPS', 'HTML', 'CSS', 'XML', 'JSON', 'PDF', 'URL', 'URI',
            'USB', 'WIFI', 'GPS', 'CPU', 'GPU', 'RAM', 'SSD', 'DVD', 'CD',
            'SMS', 'EMAIL', 'FAQ', 'CEO', 'CTO', 'HR', 'IT', 'ID', 'IP',
            'API', 'REST', 'SDK', 'SQL', 'TCP', 'UDP', 'SSH', 'FTP'
        }
        return text.upper() in universal_abbreviations

    # Removed _has_technical_context_words - using base class utility

    def _is_imperative_context(self, token: 'Token', text: str) -> bool:
        """Check if the token appears in an imperative/command context."""
        # Look for imperative patterns in the sentence
        sent = token.sent
        
        # Check if sentence starts with an imperative verb
        if sent and len(sent) > 0:
            first_token = sent[0]
            if first_token.pos_ == 'VERB' and first_token.tag_ == 'VB':  # Base form verb
                return True
        
        # Check for command-like patterns
        command_indicators = ['run', 'execute', 'install', 'configure', 'setup', 'use']
        for word in command_indicators:
            if word in sent.text.lower():
                return True
        
        return False

    def _is_brand_product_context(self, token: 'Token', text: str, context: Optional[Dict[str, Any]]) -> bool:
        """Check if abbreviation appears in brand/product naming context."""
        if not context:
            return False
        
        # Direct context indicators
        content_type = context.get('content_type', '')
        domain = context.get('domain', '')
        
        if content_type in ['marketing', 'branding'] or domain in ['product', 'brand']:
            return True
        
        # Text-based indicators around the token
        sent = token.sent
        sent_text = sent.text.lower()
        
        # Brand/product context words - be more specific
        # Only flag as brand context if there are CLEAR brand/product naming patterns
        explicit_brand_indicators = [
            'brand', 'trademark', 'registered', 'patent', 'proprietary', 'licensed',
            'inc', 'ltd', 'corporation', 'enterprise'
        ]
        
        # Check for explicit brand context
        if any(indicator in sent_text for indicator in explicit_brand_indicators):
            return True
        
        # Check for product naming patterns (token followed by version or ownership)
        # e.g., "Microsoft Office", "IBM Watson", "Oracle Database"
        token_lower = token.text.lower()
        token_pos = sent_text.find(token_lower)
        if token_pos >= 0:
            # Look for company + product patterns
            before_token = sent_text[:token_pos].strip()
            after_token = sent_text[token_pos + len(token_lower):].strip()
            
            # Company names before the token
            company_names = ['microsoft', 'google', 'apple', 'ibm', 'oracle', 'amazon', 'adobe']
            if any(company in before_token[-20:] for company in company_names):
                return True
            
            # Product descriptors after the token
            product_descriptors = ['software', 'platform', 'solution', 'service']
            if any(descriptor in after_token[:20] for descriptor in product_descriptors):
                return True
        
        # Check if token is followed by version numbers or product identifiers
        next_token = token.nbor(1) if token.i < len(token.doc) - 1 else None
        if next_token:
            # Pattern: "API 2.0", "SDK v3", "Platform Pro"
            if (next_token.like_num or 
                next_token.text.lower() in ['pro', 'enterprise', 'premium', 'standard', 'lite'] or
                re.match(r'^v?\d+', next_token.text.lower())):
                return True
        
        # Check for specific brand name patterns (not just any capitalization)
        # Look for multi-word capitalized sequences that aren't just technical terms
        nearby_tokens = []
        start_idx = max(0, token.i - 2)
        end_idx = min(len(token.doc), token.i + 3)
        
        for i in range(start_idx, end_idx):
            if i != token.i:
                nearby_tokens.append(token.doc[i])
        
        # Count non-abbreviation capitalized words (longer than 3 chars, mixed case)
        brand_like_tokens = []
        for t in nearby_tokens:
            if (t.text and t.text[0].isupper() and t.is_alpha and 
                len(t.text) > 3 and any(c.islower() for c in t.text)):
                brand_like_tokens.append(t.text)
        
        # Only flag as brand context if we have multiple brand-like proper nouns
        # Not just technical abbreviations
        if len(brand_like_tokens) >= 2:
            return True
        
        return False

    # === HELPER METHODS FOR SMART MESSAGING ===

    def _get_contextual_message(self, token: 'Token', evidence_score: float, violation_type: str) -> str:
        """Generate context-aware error messages based on evidence score."""
        
        if violation_type == 'latin':
            if evidence_score > 0.8:
                return f"Avoid using the Latin abbreviation '{token.text}' in this context."
            elif evidence_score > 0.5:
                return f"Consider replacing the Latin abbreviation '{token.text}' with its English equivalent."
            else:
                return f"The Latin abbreviation '{token.text}' may not be appropriate for your audience."
        
        elif violation_type == 'undefined':
            if evidence_score > 0.8:
                return f"Abbreviation '{token.text}' appears undefined and may confuse readers."
            elif evidence_score > 0.5:
                return f"Consider defining '{token.text}' on first use if it's not widely known."
            else:
                return f"Abbreviation '{token.text}' may benefit from definition depending on your audience."
        
        elif violation_type == 'verb':
            if evidence_score > 0.8:
                return f"Avoid using the abbreviation '{token.text}' as a verb."
            elif evidence_score > 0.5:
                return f"Consider rephrasing to avoid using '{token.text}' as a verb."
            else:
                return f"The abbreviation '{token.text}' appears to be used as a verb, which may affect readability."
        
        return f"Issue detected with abbreviation '{token.text}'."

    def _generate_smart_suggestions(self, token: 'Token', context: Optional[Dict[str, Any]], 
                                  violation_type: str, replacement: str = None) -> List[str]:
        """Generate context-aware suggestions based on violation type and context."""
        
        suggestions = []
        
        if violation_type == 'latin':
            if replacement:
                suggestions.append(f"Use its English equivalent: '{replacement}'.")
            suggestions.append("Consider if your audience is familiar with Latin abbreviations.")
            if context and context.get('audience') == 'general':
                suggestions.append("For general audiences, English equivalents are usually clearer.")
        
        elif violation_type == 'undefined':
            suggestions.append(f"Define it on first use: 'Full Term ({token.text})'.")
            if self._is_common_technical_acronym(token.text):
                suggestions.append(f"While '{token.text}' is common in technical contexts, defining it helps all readers.")
            suggestions.append("Consider your audience's familiarity with this abbreviation.")
        
        elif violation_type == 'verb':
            action_verb = self._get_semantic_action(token.text.lower())
            suggestions.append(f"Use a proper verb: '{action_verb} {token.text}' instead of '{token.text}'.")
            suggestions.append("Rephrase the sentence to use the abbreviation as a noun.")
        
        return suggestions
