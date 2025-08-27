"""
Word Usage Rule for words starting with 'I'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class IWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'I'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_i'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for I-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define I-word patterns with evidence categories
        i_word_patterns = {
            "i.e.": {"alternatives": ["that is"], "category": "abbreviation", "severity": "medium"},
            "ibmer": {"alternatives": ["IBM employee"], "category": "internal_jargon", "severity": "high"},
            "inactivate": {"alternatives": ["deactivate"], "category": "word_choice", "severity": "low"},
            "in as much as": {"alternatives": ["because", "since"], "category": "redundant_phrase", "severity": "medium"},
            "in-depth": {"alternatives": ["in depth"], "category": "hyphenation", "severity": "low"},
            "info": {"alternatives": ["information"], "category": "informal_language", "severity": "medium"},
            "in order to": {"alternatives": ["to"], "category": "redundant_phrase", "severity": "low"},
            "input": {"alternatives": ["type", "enter"], "category": "verb_misuse", "severity": "medium"},
            "insure": {"alternatives": ["ensure"], "category": "word_distinction", "severity": "high"},
            "internet": {"alternatives": ["internet (capitalized form)", "the internet"], "category": "capitalization", "severity": "medium"},
            "invite": {"alternatives": ["invitation"], "category": "noun_misuse", "severity": "medium"},
            "issue": {"alternatives": ["run", "enter"], "category": "action_clarity", "severity": "low"},
        }

        # Evidence-based analysis for I-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches (including abbreviations with periods)
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Check exact lemma matches first (single words)
            if token_lemma in i_word_patterns and ' ' not in token_lemma:
                matched_pattern = token_lemma
            # Also check for exact text matches (single words)  
            elif token_text in i_word_patterns and ' ' not in token_text:
                matched_pattern = token_text
            
            # Special case: Only flag "Internet" when capitalized, not "internet"
            if token_text == 'internet' and token.text == 'internet':
                matched_pattern = None  # Don't flag lowercase "internet"
            elif token_text == 'internet' and token.text == 'Internet':
                matched_pattern = 'internet'  # Flag capitalized "Internet"
            
            if matched_pattern:
                details = i_word_patterns[matched_pattern]
                
                # Apply surgical guards with special handling for abbreviations
                should_skip = self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {})
                
                # Override guard for specific abbreviations we want to flag
                if should_skip and matched_pattern in ['i.e.']:
                    # Check if this is actually our target abbreviation, not a legitimate entity
                    if self._is_target_abbreviation_i_words(token, matched_pattern):
                        should_skip = False
                
                # Special handling: Don't flag "info" when it's clearly part of organization names
                if should_skip and matched_pattern in ['info'] and token.ent_type_ == 'ORG':
                    # This is properly tagged as organization, let the guard work
                    pass
                
                if should_skip:
                    continue
                
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_i_word_evidence(
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

        # 2. Hyphenated word detection for I-words
        hyphenated_patterns = ['in-depth']
        for i in range(len(doc) - 2):
            if (i < len(doc) - 2 and 
                doc[i + 1].text == "-" and
                doc[i].text.lower() + "-" + doc[i + 2].text.lower() in hyphenated_patterns):
                
                hyphenated_word = doc[i].text.lower() + "-" + doc[i + 2].text.lower()
                if hyphenated_word in i_word_patterns:
                    details = i_word_patterns[hyphenated_word]
                    
                    # Apply surgical guards on the first token
                    if self._apply_surgical_zero_false_positive_guards_word_usage(doc[i], context or {}):
                        continue
                    
                    sent = doc[i].sent
                    sentence_index = 0
                    for j, s in enumerate(doc.sents):
                        if s == sent:
                            sentence_index = j
                            break
                    
                    evidence_score = self._calculate_i_word_evidence(
                        hyphenated_word, doc[i], sent, text, context or {}, details["category"]
                    )
                    
                    if evidence_score > 0.1:
                        start_char = doc[i].idx
                        end_char = doc[i + 2].idx + len(doc[i + 2].text)
                        flagged_text = doc[i].text + "-" + doc[i + 2].text
                        
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message(hyphenated_word, evidence_score, details["category"]),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions(hyphenated_word, details["alternatives"], evidence_score, context or {}, details["category"]),
                            severity=details["severity"] if evidence_score < 0.7 else 'high',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(start_char, end_char),
                            flagged_text=flagged_text
                        ))

        # 3. Multi-word phrase detection for I-words
        multi_word_patterns = {pattern: details for pattern, details in i_word_patterns.items() if ' ' in pattern}
        
        if multi_word_patterns:
            phrase_matches = self._find_multi_word_phrases_with_lemma(doc, list(multi_word_patterns.keys()), case_sensitive=False)
            
            for match in phrase_matches:
                pattern = match['phrase']
                details = multi_word_patterns[pattern]
                
                # Apply surgical guards on the first token
                if self._apply_surgical_zero_false_positive_guards_word_usage(match['start_token'], context or {}):
                    continue
                
                sent = match['start_token'].sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_i_word_evidence(
                    pattern, match['start_token'], sent, text, context or {}, details["category"]
                )
                
                if evidence_score > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_index,
                        message=self._generate_evidence_aware_word_usage_message(pattern, evidence_score, details["category"]),
                        suggestions=self._generate_evidence_aware_word_usage_suggestions(pattern, details["alternatives"], evidence_score, context or {}, details["category"]),
                        severity=details["severity"] if evidence_score < 0.7 else 'high',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(match['start_char'], match['end_char']),
                        flagged_text=match['actual_text']
                    ))
        
        return errors

    def _calculate_i_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for I-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and context
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        
        Args:
            word: The I-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (internal_jargon, word_distinction, abbreviation, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_i_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_i_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_i_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_i_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_i_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_i_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on I-word category and violation specificity.
        Higher risk categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # Very high-risk internal jargon and word distinctions
        if category == 'internal_jargon':
            return 0.95  # "IBMer" - absolutely critical for external content
        elif category == 'word_distinction':
            return 0.9  # "insure" vs "ensure" - critical semantic distinction
        
        # High-risk professional clarity issues
        elif category in ['abbreviation', 'informal_language']:
            if word_lower == 'i.e.':
                return 0.8  # Latin abbreviation needs clear alternative
            elif word_lower == 'info':
                return 0.75  # Informal shortening in professional content
            else:
                return 0.75  # Other abbreviations and informal language
        
        # Medium-high risk verb/noun misuse
        elif category in ['verb_misuse', 'noun_misuse']:
            return 0.7  # "input" as verb, "invite" as noun - clarity needed
        
        # Medium risk redundant phrases
        elif category == 'redundant_phrase':
            if word_lower == 'in order to':
                return 0.6  # Common but unnecessary
            elif word_lower == 'in as much as':
                return 0.65  # More formal but still redundant
            else:
                return 0.6  # Other redundant phrases
        
        # Lower risk style consistency issues
        elif category in ['capitalization', 'hyphenation', 'word_choice', 'action_clarity']:
            if word_lower == 'internet':
                return 0.5  # Capitalization preference, not critical
            elif word_lower == 'in-depth':
                return 0.5  # Hyphenation style preference
            else:
                return 0.55  # Other style issues
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_i_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply I-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        if word_lower == 'insure' and any(indicator in sent_text for indicator in ['make sure', 'guarantee', 'verify']):
            ev += 0.2  # Wrong word choice for "ensure" meaning
        
        if word_lower == 'input' and any(indicator in sent_text for indicator in ['keyboard', 'type', 'enter', 'command']):
            ev += 0.15  # Action context needs precise verbs
        
        if word_lower == 'ibmer' and any(indicator in sent_text for indicator in ['customer', 'client', 'user', 'external']):
            ev += 0.3  # External content must avoid internal jargon
        
        if word_lower == 'info' and any(indicator in sent_text for indicator in ['documentation', 'manual', 'guide']):
            ev += 0.1  # Formal docs need professional language
        
        return ev

    def _apply_structural_clues_i_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for I-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_i_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for I-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'customer_facing' and word_lower in ['ibmer', 'info']:
            ev += 0.3  # Customer content needs professional language
        elif content_type == 'tutorial' and word_lower in ['input', 'issue']:
            ev += 0.15  # Tutorials need clear action language
        elif content_type == 'international' and word_lower == 'insure':
            ev += 0.2  # Global content needs correct word distinctions
        
        if audience == 'external' and word_lower == 'ibmer':
            ev += 0.4  # External audiences cannot understand internal jargon
        elif audience == 'global' and word_lower in ['insure', 'i.e.']:
            ev += 0.15  # Global audiences need clear, standard language
        
        return ev

    def _apply_feedback_clues_i_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for I-words."""
        patterns = self._get_cached_feedback_patterns_i_words()
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

    def _is_target_abbreviation_i_words(self, token, pattern: str) -> bool:
        """
        Check if a token flagged by entity recognition is actually our target abbreviation.
        """
        # For "i.e." - if it's tagged as entity but is clearly the abbreviation
        if pattern == 'i.e.':
            if token.text.lower() in ['i.e.', 'ie', 'i.e']:
                return True
        
        return False

    def _get_cached_feedback_patterns_i_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for I-words."""
        return {
            'often_flagged_terms': {'ibmer', 'insure', 'input', 'info', 'i.e.'},
            'accepted_terms': set(),
            'customer_facing_patterns': {
                'flagged': {'ibmer', 'info', 'input'},  # Customer content needs professional language
                'accepted': set()
            },
            'tutorial_patterns': {
                'flagged': {'input', 'issue', 'i.e.'},  # Tutorials need clear language
                'accepted': {'internet'}  # Common term in tutorials
            },
            'international_patterns': {
                'flagged': {'insure', 'i.e.', 'ibmer'},  # Global content needs precision
                'accepted': {'internet'}  # Standard international term
            },
            'technical_patterns': {
                'flagged': {'ibmer', 'info'},  # Technical docs avoid jargon
                'accepted': {'internet', 'input'}  # Technical terms acceptable
            },
            'external_patterns': {
                'flagged': {'ibmer', 'info', 'insure'},  # External content must be clear
                'accepted': {'internet'}  # Universal term
            }
        }