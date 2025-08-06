"""
Word Usage Rule for words starting with 'B'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
    from spacy.matcher import PhraseMatcher
except ImportError:
    Doc = None
    PhraseMatcher = None

class BWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'B'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_b'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with B-word patterns."""
        # Define word details for 'B' words
        word_details = {
            "back-end": {"suggestion": "Write as 'back end' (noun) or use a more specific term like 'server'.", "severity": "low"},
            "backward compatible": {"suggestion": "Use 'compatible with earlier versions'.", "severity": "medium"},
            "bar code": {"suggestion": "Write as 'barcode'.", "severity": "low"},
            "below": {"suggestion": "Avoid relative locations. Use 'following' or 'in the next section'.", "severity": "medium"},
            "best practice": {"suggestion": "Use with caution. This is a subjective claim. Consider 'recommended practice'.", "severity": "high"},
            "beta": {"suggestion": "Use as an adjective (e.g., 'beta program'), not a noun.", "severity": "low"},
            "between": {"suggestion": "Do not use for ranges of numbers. Use an en dash (–) or 'from X to Y'.", "severity": "medium"},
            "blacklist": {"suggestion": "Use inclusive language. Use 'blocklist' instead.", "severity": "high"},
            "boot": {"suggestion": "Use 'start' or 'turn on' where possible.", "severity": "low"},
            "breadcrumb": {"suggestion": "Do not use 'BCT' as an abbreviation for 'breadcrumb trail'.", "severity": "low"},
            "built in": {"suggestion": "Hyphenate when used as an adjective before a noun: 'built-in'.", "severity": "low"},
        }
        
        # Use base class method to setup patterns
        self._setup_word_patterns(nlp, word_details)

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)
        
        # Ensure patterns are initialized
        self._ensure_patterns_ready(nlp)

        # PRESERVE EXISTING FUNCTIONALITY: Enhanced morphological analysis for backup vs back up
        # This sophisticated linguistic analysis is kept unchanged for maximum accuracy
        self._analyze_backup_forms(doc, errors, text, context)

        # NEW ENHANCED APPROACH: Use base class PhraseMatcher functionality
        word_usage_errors = self._find_word_usage_errors(doc, "Review usage of the term")
        errors.extend(word_usage_errors)
        
        return errors
    
    def _analyze_backup_forms(self, doc, errors, text: str = None, context: Dict[str, Any] = None):
        """
        Enhanced morphological analysis for backup vs back up using spaCy linguistic anchors.
        Uses comprehensive POS tagging, dependency parsing, and semantic analysis.
        """
        for token in doc:
            # LINGUISTIC ANCHOR 1: Single token "backup" analysis
            if self._is_backup_single_token(token):
                if self._should_be_phrasal_verb(token, doc):
                    sent = token.sent
                    sentence_idx = list(doc.sents).index(sent)
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_idx,
                        message="Incorrect verb form: 'backup' should be 'back up'.",
                        suggestions=["Use 'back up' (two words) for the verb form."],
                        severity='medium',
                        text=text,  # Enhanced: Pass full text for better confidence analysis
                        context=context,  # Enhanced: Pass context for domain-specific validation
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
            
            # LINGUISTIC ANCHOR 2: Phrasal "back up" analysis
            elif self._is_back_token(token):
                next_token = self._get_next_up_token(token, doc)
                if next_token and self._should_be_compound_noun(token, next_token, doc):
                    sent = token.sent
                    sentence_idx = list(doc.sents).index(sent)
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_idx,
                        message="Incorrect noun/adjective form: 'back up' should be 'backup'.",
                        suggestions=["Use 'backup' (one word) for the noun or adjective form."],
                        severity='medium',
                        text=text,  # Enhanced: Pass full text for better confidence analysis
                        context=context,  # Enhanced: Pass context for domain-specific validation
                        span=(token.idx, next_token.idx + len(next_token.text)),
                        flagged_text=f"{token.text} {next_token.text}"
                    ))
    
    def _is_backup_single_token(self, token):
        """Check if token is a single 'backup' word using morphological analysis."""
        return (token.text.lower() == "backup" and 
                hasattr(token, 'lemma_') and token.lemma_.lower() == "backup")
    
    def _is_back_token(self, token):
        """Check if token is 'back' part of potential phrasal construction."""
        return (token.text.lower() == "back" and 
                hasattr(token, 'lemma_') and token.lemma_.lower() == "back")
    
    def _get_next_up_token(self, back_token, doc):
        """Get the next 'up' token if it follows 'back'."""
        if (back_token.i + 1 < len(doc) and 
            doc[back_token.i + 1].text.lower() == "up" and
            doc[back_token.i + 1].lemma_.lower() == "up"):
            return doc[back_token.i + 1]
        return None
    
    def _should_be_phrasal_verb(self, token, doc):
        """
        Determine if 'backup' should be 'back up' based on syntactic context.
        LINGUISTIC ANCHOR: Uses POS tags, dependency parsing, and semantic roles.
        """
        # MORPHOLOGICAL PATTERN 1: Direct verb tagging
        if token.pos_ == "VERB":
            return True
        
        # MORPHOLOGICAL PATTERN 2: Auxiliary verb context
        if self._has_auxiliary_context(token, doc):
            return True
        
        # MORPHOLOGICAL PATTERN 3: Imperative context
        if self._is_imperative_context(token, doc):
            return True
        
        # MORPHOLOGICAL PATTERN 4: Object dependency pattern
        if self._has_direct_object_pattern(token, doc):
            return True
        
        # MORPHOLOGICAL PATTERN 5: Infinitive marker context
        if self._has_infinitive_context(token, doc):
            return True
        
        return False
    
    def _should_be_compound_noun(self, back_token, up_token, doc):
        """
        Determine if 'back up' should be 'backup' based on syntactic context.
        LINGUISTIC ANCHOR: Uses dependency parsing and semantic role analysis.
        """
        # MORPHOLOGICAL PATTERN 1: Noun phrase head
        if back_token.pos_ == "NOUN" or up_token.pos_ == "NOUN":
            return True
        
        # MORPHOLOGICAL PATTERN 2: Adjectival modifier pattern
        if self._is_adjectival_modifier_pattern(back_token, up_token, doc):
            return True
        
        # MORPHOLOGICAL PATTERN 3: Determiner context (a backup, the backup)
        if self._has_determiner_context(back_token, doc):
            return True
        
        # MORPHOLOGICAL PATTERN 4: Compound dependency
        if back_token.dep_ in ["compound", "amod"] or up_token.dep_ in ["compound", "amod"]:
            return True
        
        # MORPHOLOGICAL PATTERN 5: Object of preposition
        if self._is_prepositional_object(back_token, up_token, doc):
            return True
        
        return False
    
    def _has_auxiliary_context(self, token, doc):
        """Check for auxiliary verb context (can backup, will backup, etc.)."""
        if token.i > 0:
            prev_token = doc[token.i - 1]
            if prev_token.pos_ == "AUX" or prev_token.tag_ == "MD":  # Modal auxiliary
                return True
        return False
    
    def _is_imperative_context(self, token, doc):
        """Check if token appears in imperative context."""
        sent = token.sent
        # Check if this is sentence-initial or follows imperative markers
        if token == list(sent)[0]:  # First token in sentence
            return True
        # Check for imperative markers
        for t in sent:
            if t.dep_ == "ROOT" and t.pos_ == "VERB" and t.lemma_.lower() == token.lemma_.lower():
                return True
        return False
    
    def _has_direct_object_pattern(self, token, doc):
        """Check for direct object pattern (backup the files)."""
        if token.i + 1 < len(doc):
            next_token = doc[token.i + 1]
            # Look for determiners or nouns following
            if next_token.pos_ in ["DET", "NOUN", "PRON"]:
                return True
        return False
    
    def _has_infinitive_context(self, token, doc):
        """Check for infinitive marker context (to backup)."""
        if token.i > 0:
            prev_token = doc[token.i - 1]
            if prev_token.text.lower() == "to" and prev_token.pos_ == "PART":
                return True
        return False
    
    def _is_adjectival_modifier_pattern(self, back_token, up_token, doc):
        """Check if 'back up' functions as adjectival modifier."""
        # Look for patterns like "back up system", "back up procedure"
        if up_token.i + 1 < len(doc):
            next_token = doc[up_token.i + 1]
            if next_token.pos_ == "NOUN":
                return True
        return False
    
    def _has_determiner_context(self, back_token, doc):
        """Check for determiner context (a/the/this backup)."""
        if back_token.i > 0:
            prev_token = doc[back_token.i - 1]
            if prev_token.pos_ == "DET":  # Determiner
                return True
        return False
    
    def _is_prepositional_object(self, back_token, up_token, doc):
        """Check if 'back up' is object of preposition."""
        # Look for preposition before the phrase
        if back_token.i > 0:
            prev_token = doc[back_token.i - 1]
            if prev_token.pos_ == "ADP":  # Preposition
                return True
        return False
