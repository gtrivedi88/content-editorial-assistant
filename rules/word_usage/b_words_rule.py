"""
Word Usage Rule for words starting with 'B'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
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

class BWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'B'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_b'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for B-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define B-word patterns with evidence categories
        b_word_patterns = {
            "back-end": {"alternatives": ["back end (noun)", "server"], "category": "hyphenation", "severity": "low"},
            "backward compatible": {"alternatives": ["compatible with earlier versions"], "category": "technical_jargon", "severity": "medium"},
            "bar code": {"alternatives": ["barcode"], "category": "spelling", "severity": "low"},
            "below": {"alternatives": ["following", "in the next section"], "category": "location_relative", "severity": "medium"},
            "best practice": {"alternatives": ["recommended practice"], "category": "subjective_claim", "severity": "high"},
            "beta": {"alternatives": ["beta program (adjective)"], "category": "usage_specific", "severity": "low"},
            "between": {"alternatives": ["from X to Y", "X–Y (en dash)"], "category": "range_formatting", "severity": "medium"},
            "blacklist": {"alternatives": ["blocklist"], "category": "inclusive_language", "severity": "high"},
            "boot": {"alternatives": ["start", "turn on"], "category": "technical_simplification", "severity": "low"},
            "breadcrumb": {"alternatives": ["breadcrumb trail (not BCT)"], "category": "abbreviation_usage", "severity": "low"},
            "built in": {"alternatives": ["built-in (adjective)"], "category": "hyphenation", "severity": "low"},
        }

        # Evidence-based analysis for B-words
        for word, details in b_word_patterns.items():
            # Use regex for precise word boundary matching
            for match in re.finditer(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE):
                char_start = match.start()
                char_end = match.end()
                matched_text = match.group(0)
                
                # Find the token and sentence
                token = None
                sent = None
                sentence_index = 0
                
                for i, s in enumerate(doc.sents):
                    if s.start_char <= char_start < s.end_char:
                        sent = s
                        sentence_index = i
                        # Find the specific token
                        for t in s:
                            if t.idx <= char_start < t.idx + len(t.text):
                                token = t
                                break
                        break
                
                if sent and token:
                    # Apply surgical guards
                    if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                        continue
                    
                    evidence_score = self._calculate_b_word_evidence(
                        word, token, sent, text, context or {}, details["category"]
                    )
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message(word, evidence_score, details["category"]),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions(word, details["alternatives"], evidence_score, context or {}, details["category"]),
                            severity=details["severity"] if evidence_score < 0.7 else 'high',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(char_start, char_end),
                            flagged_text=matched_text
                        ))

        # PRESERVE EXISTING FUNCTIONALITY: Enhanced morphological analysis for backup vs back up
        # This sophisticated linguistic analysis uses evidence-based scoring
        self._analyze_backup_forms_evidence_based(doc, errors, text, context)
        
        return errors
    
    def _analyze_backup_forms_evidence_based(self, doc, errors, text: str = None, context: Dict[str, Any] = None):
        """
        Enhanced morphological analysis for backup vs back up using evidence-based scoring.
        Uses comprehensive POS tagging, dependency parsing, and semantic analysis.
        """
        for token in doc:
            # LINGUISTIC ANCHOR 1: Single token "backup" analysis
            if self._is_backup_single_token(token):
                # Apply surgical guards
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue
                    
                if self._should_be_phrasal_verb(token, doc):
                    evidence_score = self._calculate_backup_evidence(
                        "backup", token, token.sent, text, context or {}, "verb_form"
                    )
                    
                    if evidence_score > 0.1:
                        sent = token.sent
                        sentence_idx = list(doc.sents).index(sent)
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=sentence_idx,
                            message=self._generate_evidence_aware_word_usage_message("backup", evidence_score, "verb_form"),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions("backup", ["back up (two words)"], evidence_score, context or {}, "verb_form"),
                            severity='medium' if evidence_score < 0.8 else 'high',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
            
            # LINGUISTIC ANCHOR 2: Phrasal "back up" analysis
            elif self._is_back_token(token):
                next_token = self._get_next_up_token(token, doc)
                if next_token:
                    # Apply surgical guards
                    if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                        continue
                        
                    if self._should_be_compound_noun(token, next_token, doc):
                        evidence_score = self._calculate_backup_evidence(
                            "back up", token, token.sent, text, context or {}, "noun_form"
                        )
                        
                        if evidence_score > 0.1:
                            sent = token.sent
                            sentence_idx = list(doc.sents).index(sent)
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=sentence_idx,
                                message=self._generate_evidence_aware_word_usage_message("back up", evidence_score, "noun_form"),
                                suggestions=self._generate_evidence_aware_word_usage_suggestions("back up", ["backup (one word)"], evidence_score, context or {}, "noun_form"),
                                severity='medium' if evidence_score < 0.8 else 'high',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=(token.idx, next_token.idx + len(next_token.text)),
                                flagged_text=f"{token.text} {next_token.text}"
                            ))

    # === EVIDENCE-BASED CALCULATION ===

    def _calculate_b_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for B-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and context
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_b_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_b_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_b_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_b_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_b_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    def _calculate_backup_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score specifically for backup/back up distinctions."""
        evidence_score = self._get_base_backup_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0
        
        # Apply specialized clues for backup forms
        evidence_score = self._apply_backup_linguistic_clues(evidence_score, word, token, sentence)
        evidence_score = self._apply_structural_clues_b_words(evidence_score, context)
        evidence_score = self._apply_semantic_clues_b_words(evidence_score, word, text, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_b_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on B-word category and violation specificity.
        """
        word_lower = word.lower()
        
        # Very high-risk inclusive language violations
        if category == 'inclusive_language':
            return 0.95  # "blacklist" requires immediate attention
        
        # High-risk subjective claims
        elif category == 'subjective_claim':
            return 0.9  # "best practice" is unsupported claim
        
        # Medium-high risk technical jargon and relative positioning
        elif category in ['technical_jargon', 'location_relative']:
            return 0.75  # "backward compatible", "below" 
        
        # Medium risk formatting and range issues
        elif category == 'range_formatting':
            return 0.7  # "between" for number ranges
        
        # Lower risk spelling and hyphenation preferences
        elif category in ['spelling', 'hyphenation', 'abbreviation_usage']:
            return 0.5  # "bar code"/"barcode", "built in"/"built-in"
        
        # Technical simplification and usage-specific
        elif category in ['technical_simplification', 'usage_specific']:
            return 0.55  # "boot", "beta"
        
        return 0.6  # Default moderate evidence

    def _get_base_backup_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Base evidence score for backup/back up form distinctions."""
        if category in ['verb_form', 'noun_form']:
            return 0.8  # High confidence in morphological analysis
        return 0.6

    # === CLUE METHODS ===

    def _apply_linguistic_clues_b_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply B-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # Presence of inclusive language context increases urgency
        if word_lower == 'blacklist':
            inclusive_indicators = ['diversity', 'inclusion', 'accessibility', 'equity']
            if any(indicator in sent_text for indicator in inclusive_indicators):
                ev += 0.1  # Higher urgency in inclusive contexts
        
        # Technical writing context affects certain words
        tech_indicators = ['system', 'server', 'database', 'network']
        if any(tech in sent_text for tech in tech_indicators):
            if word_lower in ['boot', 'back-end']:
                ev += 0.1  # Technical context makes these more problematic
        
        # Range/number context affects "between"
        number_indicators = ['number', 'range', 'from', 'to', 'through']
        if any(indicator in sent_text for indicator in number_indicators):
            if word_lower == 'between':
                ev += 0.15  # "Between" particularly problematic with numbers
        
        # Subjective claim context
        claim_indicators = ['recommend', 'suggest', 'should', 'must', 'always']
        if any(indicator in sent_text for indicator in claim_indicators):
            if word_lower == 'best practice':
                ev += 0.1  # Subjective claims more problematic in prescriptive context
        
        return ev

    def _apply_backup_linguistic_clues(self, ev: float, word: str, token, sentence) -> float:
        """Apply specialized linguistic clues for backup forms."""
        sent_text = sentence.text.lower()
        
        # Command/instruction context increases evidence for verb form
        command_indicators = ['please', 'make sure to', 'remember to', 'be sure to']
        if any(indicator in sent_text for indicator in command_indicators):
            if word.lower() == 'backup':
                ev += 0.1  # Commands suggest verb usage
        
        # Technical procedure context
        procedure_indicators = ['procedure', 'process', 'step', 'instruction']
        if any(indicator in sent_text for indicator in procedure_indicators):
            ev += 0.05  # Procedures often mix noun/verb forms incorrectly
        
        return ev

    def _apply_structural_clues_b_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for B-words."""
        block_type = context.get('block_type', 'paragraph')
        
        # Procedural contexts need precision
        if block_type == 'step':
            ev += 0.1  # Steps need precise language
        
        # List contexts benefit from brevity
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            ev += 0.05  # Lists need concise language
        
        # Heading contexts
        elif block_type == 'heading':
            ev -= 0.1  # Headings can be more flexible
        
        return ev

    def _apply_semantic_clues_b_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for B-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        # Content type adjustments
        if content_type == 'policy':
            if word_lower == 'blacklist':
                ev += 0.2  # Policy documents need inclusive language
        
        elif content_type == 'tutorial':
            if word_lower in ['below', 'between']:
                ev += 0.15  # Tutorials need spatial clarity
        
        elif content_type == 'technical':
            if word_lower in ['boot', 'back-end']:
                ev += 0.1  # Technical docs need precise terminology
        
        # Audience adjustments
        if audience == 'beginner':
            if word_lower in ['backward compatible', 'beta']:
                ev += 0.1  # Beginners need clear, accessible language
        
        elif audience == 'expert':
            if word_lower in ['built in', 'bar code']:
                ev -= 0.05  # Experts may accept minor variations
        
        return ev

    def _apply_feedback_clues_b_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for B-words."""
        patterns = self._get_cached_feedback_patterns_b_words()
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

    def _get_cached_feedback_patterns_b_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for B-words."""
        return {
            'often_flagged_terms': {'blacklist', 'best practice', 'below'},
            'accepted_terms': set(),
            'policy_patterns': {
                'flagged': {'blacklist'},
                'accepted': set()
            },
            'technical_patterns': {
                'flagged': {'boot', 'back-end'},
                'accepted': {'beta'}  # In software contexts
            },
            'tutorial_patterns': {
                'flagged': {'below', 'between'},
                'accepted': set()
            }
        }

    # === PRESERVED MORPHOLOGICAL ANALYSIS METHODS ===
    # These methods maintain the sophisticated linguistic analysis for backup/back up

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