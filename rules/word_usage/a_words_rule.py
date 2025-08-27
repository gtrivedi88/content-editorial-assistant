"""
Word Usage Rule for words starting with 'A'.
Enhanced with spaCy Matcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
    from spacy.matcher import PhraseMatcher
except ImportError:
    Doc = None
    PhraseMatcher = None

class AWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'A'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_a'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for A-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define A-word patterns with evidence categories
        a_word_patterns = {
            "abort": {"alternatives": ["cancel", "stop"], "category": "action_verb", "severity": "high"},
            "above": {"alternatives": ["previous", "preceding"], "category": "location_relative", "severity": "medium"},
            "ad hoc": {"alternatives": ["ad hoc (two words)"], "category": "spelling", "severity": "low"},
            "adviser": {"alternatives": ["advisor"], "category": "spelling", "severity": "low"},
            "afterwards": {"alternatives": ["afterward"], "category": "spelling", "severity": "low"},
            "allow": {"alternatives": ["you can use"], "category": "user_focus", "severity": "medium"},
            "amongst": {"alternatives": ["among"], "category": "spelling", "severity": "low"},
            "and/or": {"alternatives": ["a or b", "a, b, or both"], "category": "ambiguous", "severity": "medium"},
            "appear": {"alternatives": ["open", "is displayed"], "category": "ui_language", "severity": "medium"},
            "architect": {"alternatives": ["design", "plan", "structure"], "category": "verb_misuse", "severity": "high"},
            "asap": {"alternatives": ["as soon as possible"], "category": "informal_abbrev", "severity": "medium"},
        }

        # PRESERVE EXISTING FUNCTIONALITY: Context-aware check for 'action' as a verb
        # This specialized grammar check uses evidence-based scoring with improved linguistic detection
        for token in doc:
            if token.lemma_.lower() == "action" and self._is_action_used_as_verb(token, doc):
                # Apply surgical guards first
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue
                
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                # Calculate evidence for verb misuse of 'action'
                evidence_score = self._calculate_a_word_evidence(
                    "action", token, sent, text, context or {}, "verb_misuse"
                )
                
                if evidence_score > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_index,
                        message=self._generate_evidence_aware_word_usage_message("action", evidence_score, "verb_misuse"),
                        suggestions=self._generate_evidence_aware_word_usage_suggestions("action", ["run", "perform"], evidence_score, context or {}, "verb_misuse"),
                        severity='high' if evidence_score > 0.8 else 'medium',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))

        # Evidence-based analysis for other A-words using lemma-based matching
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Check exact lemma matches first
            if token_lemma in a_word_patterns:
                matched_pattern = token_lemma
            # Also check for exact text matches (for phrases like "and/or", "ad hoc", and acronyms)
            elif token_text in a_word_patterns:
                matched_pattern = token_text
            
            if matched_pattern:
                details = a_word_patterns[matched_pattern]
                
                # Apply surgical guards with exception for abbreviations we want to flag
                should_skip = self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {})
                
                # Override guard for abbreviations in our patterns - we want to flag these
                if should_skip and matched_pattern in ['asap', 'and/or', 'ad hoc']:
                    # Check if this is actually our target abbreviation, not a legitimate entity
                    if self._is_target_abbreviation(token, matched_pattern):
                        should_skip = False
                
                if should_skip:
                    continue
                
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_a_word_evidence(
                    matched_pattern, token, sent, text, context or {}, details["category"]
                )
                
                if evidence_score > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_index,
                        message=self._generate_evidence_aware_word_usage_message(matched_pattern, evidence_score, details["category"]),
                        suggestions=self._generate_evidence_aware_word_usage_suggestions(matched_pattern, details["alternatives"], evidence_score, context or {}, details["category"]),
                        severity=details["severity"] if evidence_score < 0.7 else 'high',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
        
        return errors

    # === EVIDENCE-BASED CALCULATION ===

    def _calculate_a_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for A-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and context
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        
        Args:
            word: The A-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (action_verb, spelling, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_a_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_a_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_a_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_a_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_a_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_a_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on A-word category and violation specificity.
        Higher risk categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # Very high-risk verb misuse (highest base evidence)
        if category == 'verb_misuse':
            return 0.9  # "architect" as verb, "action" as verb - clear violations
        
        # High-risk ambiguous constructions
        elif category == 'ambiguous':
            return 0.85  # "and/or" creates ambiguity
        
        # Medium-high risk user focus issues
        elif category in ['user_focus', 'ui_language']:
            return 0.75  # "allow" shifts focus from user, "appear" for UI elements
        
        # Medium risk action verbs that could be more specific
        elif category == 'action_verb':
            return 0.7  # "abort" could be more specific
        
        # Medium risk relative location references
        elif category == 'location_relative':
            return 0.65  # "above" is relative and unclear
        
        # Lower risk spelling preferences
        elif category in ['spelling', 'informal_abbrev']:
            return 0.5  # "adviser"/"advisor", "asap" are preferences
        
        return 0.6  # Default moderate evidence for other patterns
    
    # === CLUE METHODS ===

    def _apply_linguistic_clues_a_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply A-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # Presence of hedging language reduces severity
        hedges = ['might', 'could', 'may', 'perhaps', 'possibly']
        if any(hedge in sent_text for hedge in hedges):
            ev -= 0.1
        
        # Formal writing indicators increase evidence for informal words
        formal_indicators = ['pursuant to', 'heretofore', 'notwithstanding']
        if any(formal in sent_text for formal in formal_indicators):
            if word_lower in ['asap']:
                ev += 0.2  # Informal abbreviations more problematic in formal context
        
        # Technical writing indicators affect certain words
        tech_indicators = ['system', 'process', 'function', 'method']
        if any(tech in sent_text for tech in tech_indicators):
            if word_lower == 'allow':
                ev += 0.1  # "Allow" less user-focused in technical context
        
        # User interface context affects UI-related words
        ui_indicators = ['button', 'dialog', 'window', 'menu', 'screen']
        if any(ui in sent_text for ui in ui_indicators):
            if word_lower == 'appear':
                ev += 0.15  # "Appear" particularly problematic for UI elements
            if word_lower == 'above':
                ev += 0.1  # Relative positioning problematic in UI
        
        return ev

    def _apply_structural_clues_a_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for A-words."""
        block_type = context.get('block_type', 'paragraph')
        
        # Heading context - some words more acceptable
        if block_type == 'heading':
            ev -= 0.2  # Headings can be more concise
        
        # List context - brevity preferred
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            ev += 0.1  # Lists benefit from concise language
        
        # Table context - precision important
        elif block_type in ['table_cell', 'table_header']:
            ev += 0.05  # Tables need precise language
        
        # Procedural context - clarity critical
        elif block_type == 'step':
            ev += 0.1  # Procedural steps need clear language
        
        return ev

    def _apply_semantic_clues_a_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for A-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        # Content type adjustments
        if content_type == 'tutorial':
            if word_lower in ['allow', 'appear', 'above']:
                ev += 0.15  # User-focused language critical in tutorials
        
        elif content_type == 'reference':
            if word_lower in ['asap', 'and/or']:
                ev += 0.1  # Reference docs need precise language
        
        elif content_type == 'marketing':
            if word_lower in ['abort', 'amongst']:
                ev += 0.1  # Marketing needs accessible language
        
        # Audience adjustments
        if audience == 'beginner':
            if word_lower in ['amongst', 'afterwards']:
                ev += 0.1  # Beginners benefit from simpler variants
        
        elif audience == 'expert':
            if word_lower in ['asap', 'and/or']:
                ev -= 0.1  # Experts may accept some informality
        
        # Document-level context
        text_lower = text.lower()
        if 'user interface' in text_lower or 'ui' in text_lower:
            if word_lower in ['appear', 'above']:
                ev += 0.1  # UI documentation needs spatial clarity
        
        return ev

    def _apply_feedback_clues_a_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for A-words."""
        patterns = self._get_cached_feedback_patterns_a_words()
        word_lower = word.lower()
        
        # Consistently flagged terms
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        
        # Consistently accepted terms
        if word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.2
        
        # Context-specific patterns
        content_type = context.get('content_type', 'general')
        context_patterns = patterns.get(f'{content_type}_patterns', {})
        
        if word_lower in context_patterns.get('flagged', set()):
            ev += 0.1
        elif word_lower in context_patterns.get('accepted', set()):
            ev -= 0.1
        
        return ev

    def _is_action_used_as_verb(self, token, doc) -> bool:
        """
        LINGUISTIC ANCHOR: Determine if 'action' is being used as a verb.
        
        SpaCy often tags 'action' as NOUN even when used as a verb, so we need
        more sophisticated linguistic analysis to detect verb usage patterns.
        
        Args:
            token: The 'action' token
            doc: spaCy doc object
            
        Returns:
            bool: True if 'action' is being used as a verb
        """
        # PATTERN 1: Direct verb tagging (most reliable when it occurs)
        if token.pos_ == "VERB":
            return True
        
        # PATTERN 2: ROOT dependency with noun tag (imperative constructions)
        # "Please action this" - 'action' is ROOT but tagged as NOUN
        if token.dep_ == "ROOT" and token.pos_ == "NOUN":
            # Check if sentence has imperative markers
            sent_text = token.sent.text.lower()
            imperative_markers = ['please', 'let us', 'we should', 'you should', 'make sure to']
            if any(marker in sent_text for marker in imperative_markers):
                return True
            
            # Check if it's sentence-initial (imperative without 'please')
            if token.i == 0 or (token.i == 1 and doc[0].pos_ == "INTJ"):  # INTJ for 'please'
                return True
        
        # PATTERN 3: Following modal verbs (should, can, will, etc.)
        if token.i > 0:
            prev_token = doc[token.i - 1]
            if prev_token.pos_ == "AUX" or prev_token.tag_ in ["MD", "VBP", "VBZ"]:  # Modals and auxiliary verbs
                return True
        
        # PATTERN 4: Infinitive constructions (to action)
        if token.i > 0:
            prev_token = doc[token.i - 1]
            if prev_token.text.lower() == "to" and prev_token.pos_ == "PART":
                return True
        
        # PATTERN 5: Object dependency pattern suggests verb usage
        # Look for direct objects following 'action'
        for child in token.children:
            if child.dep_ in ["dobj", "obj"]:  # Direct object dependencies
                return True
        
        # PATTERN 6: Sentence structure analysis for imperatives
        # If 'action' is followed by determiners + nouns, likely verb usage
        if token.i + 1 < len(doc):
            next_token = doc[token.i + 1]
            if next_token.pos_ in ["DET", "PRON"] and token.dep_ == "ROOT":
                return True
        
        return False

    def _is_target_abbreviation(self, token, pattern: str) -> bool:
        """
        Check if a token flagged by entity recognition is actually our target abbreviation.
        
        Args:
            token: SpaCy token
            pattern: The pattern we're trying to match
            
        Returns:
            bool: True if this is our target abbreviation that should be flagged
        """
        # For "asap" - if it's tagged as ORG but is clearly the abbreviation
        if pattern == 'asap':
            # ASAP as an abbreviation should be flagged even if tagged as ORG
            if token.text.upper() == 'ASAP' and len(token.text) == 4:
                return True
        
        # For "and/or" - this should always be flagged regardless of entity tagging
        elif pattern == 'and/or':
            if '/' in token.text and 'and' in token.text.lower():
                return True
        
        # For "ad hoc" - this should be flagged if it's the Latin phrase
        elif pattern == 'ad hoc':
            if token.text.lower() in ['ad', 'hoc'] and 'ad hoc' in token.sent.text.lower():
                return True
        
        return False

    def _get_cached_feedback_patterns_a_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for A-words."""
        return {
            'often_flagged_terms': {'and/or', 'appear', 'allow'},
            'accepted_terms': set(),
            'tutorial_patterns': {
                'flagged': {'above', 'appear'},
                'accepted': set()
            },
            'technical_patterns': {
                'flagged': {'allow'},
                'accepted': {'abort'}  # In error handling contexts
            },
            'reference_patterns': {
                'flagged': {'and/or', 'asap'},
                'accepted': set()
            }
        }