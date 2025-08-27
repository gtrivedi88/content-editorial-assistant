"""
Word Usage Rule for words starting with 'H'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class HWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'H'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_h'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for H-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define H-word patterns with evidence categories
        h_word_patterns = {
            "hamburger menu": {"alternatives": ["menu", "navigation menu"], "category": "ui_language", "severity": "medium"},
            "hard copy": {"alternatives": ["hardcopy"], "category": "spacing", "severity": "low"},
            "hard-coded": {"alternatives": ["hardcoded"], "category": "hyphenation", "severity": "low"},
            "hardcoded": {"alternatives": ["hardcoded (preferred)", "coded"], "category": "preferred_form", "severity": "low"},
            "have to": {"alternatives": ["must"], "category": "action_clarity", "severity": "medium"},
            "health care": {"alternatives": ["healthcare"], "category": "spacing", "severity": "low"},
            "healthcare": {"alternatives": ["healthcare (preferred)"], "category": "preferred_form", "severity": "low"},
            "help desk": {"alternatives": ["helpdesk"], "category": "spacing", "severity": "low"},
            "helpdesk": {"alternatives": ["helpdesk (preferred)", "support"], "category": "preferred_form", "severity": "low"},
            "high-availability": {"alternatives": ["high availability"], "category": "hyphenation", "severity": "low"},
            "high-level": {"alternatives": ["high level"], "category": "hyphenation", "severity": "low"},
            "hit": {"alternatives": ["press", "select", "click"], "category": "action_clarity", "severity": "high"},
            "home page": {"alternatives": ["homepage"], "category": "spacing", "severity": "low"},
            "homepage": {"alternatives": ["homepage (preferred)", "home"], "category": "preferred_form", "severity": "low"},
            "host name": {"alternatives": ["hostname"], "category": "spacing", "severity": "low"},
            "hostname": {"alternatives": ["hostname (preferred)", "server name"], "category": "preferred_form", "severity": "low"},
            "how-to": {"alternatives": ["instructional", "procedural"], "category": "word_choice", "severity": "medium"},
        }

        # Evidence-based analysis for H-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Check exact lemma matches first (single words)
            if token_lemma in h_word_patterns and ' ' not in token_lemma:
                matched_pattern = token_lemma
            # Also check for exact text matches (single words)  
            elif token_text in h_word_patterns and ' ' not in token_text:
                matched_pattern = token_text
            
            if matched_pattern:
                details = h_word_patterns[matched_pattern]
                
                # Apply surgical guards
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue
                
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_h_word_evidence(
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

        # 2. Hyphenated word detection for H-words
        hyphenated_patterns = ['hard-coded', 'high-availability', 'high-level', 'how-to']
        for i in range(len(doc) - 2):
            if (i < len(doc) - 2 and 
                doc[i + 1].text == "-" and
                doc[i].text.lower() + "-" + doc[i + 2].text.lower() in hyphenated_patterns):
                
                hyphenated_word = doc[i].text.lower() + "-" + doc[i + 2].text.lower()
                if hyphenated_word in h_word_patterns:
                    details = h_word_patterns[hyphenated_word]
                    
                    # Apply surgical guards on the first token
                    if self._apply_surgical_zero_false_positive_guards_word_usage(doc[i], context or {}):
                        continue
                    
                    sent = doc[i].sent
                    sentence_index = 0
                    for j, s in enumerate(doc.sents):
                        if s == sent:
                            sentence_index = j
                            break
                    
                    evidence_score = self._calculate_h_word_evidence(
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

        # 3. Multi-word phrase detection for H-words
        multi_word_patterns = {pattern: details for pattern, details in h_word_patterns.items() if ' ' in pattern}
        
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
                
                evidence_score = self._calculate_h_word_evidence(
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

    def _calculate_h_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for H-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and context
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        
        Args:
            word: The H-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (ui_language, action_clarity, spacing, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_h_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_h_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_h_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_h_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_h_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_h_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on H-word category and violation specificity.
        Higher risk categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # Very high-risk action clarity issues
        if category == 'action_clarity':
            if word_lower == 'hit':
                return 0.9  # "Hit" is very unprofessional, high priority
            elif word_lower == 'have to':
                return 0.75  # "Have to" needs authoritative language
            else:
                return 0.8  # Other action clarity issues
        
        # High-risk UI language issues
        elif category == 'ui_language':
            return 0.85  # "hamburger menu" - needs professional UI terminology
        
        # Medium risk word choice issues
        elif category == 'word_choice':
            return 0.7  # "how-to" - improve word choice for clarity
        
        # Lower risk spacing issues
        elif category == 'spacing':
            if word_lower in ['hard copy', 'health care', 'help desk', 'home page', 'host name']:
                return 0.6  # Standard spacing corrections
            else:
                return 0.5  # Other spacing preferences
        
        # Lower risk hyphenation preferences
        elif category == 'hyphenation':
            return 0.5  # "hard-coded", "high-availability", etc. - style preferences
        
        # Context-dependent preferred forms
        elif category == 'preferred_form':
            # These are actually preferred - very low evidence
            if word_lower in ['hardcoded', 'healthcare', 'helpdesk', 'homepage', 'hostname']:
                return 0.05  # Very low evidence since these are preferred
            else:
                return 0.4  # Other forms may need consideration
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_h_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply H-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        if word_lower == 'hit' and any(indicator in sent_text for indicator in ['key', 'button', 'click', 'press']):
            ev += 0.15  # Action context needs precise language
        
        if word_lower == 'hamburger menu' and any(indicator in sent_text for indicator in ['ui', 'interface', 'navigation']):
            ev += 0.1  # UI context needs professional terminology
        
        if word_lower == 'have to' and any(indicator in sent_text for indicator in ['must', 'required', 'mandatory']):
            ev += 0.1  # Instruction context needs authoritative language
        
        return ev

    def _apply_structural_clues_h_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for H-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_h_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for H-words."""
        content_type = context.get('content_type', 'general')
        word_lower = word.lower()
        
        if content_type == 'tutorial' and word_lower in ['hit', 'have to']:
            ev += 0.15  # Tutorials need clear, professional instructions
        elif content_type == 'ui_documentation' and word_lower == 'hamburger menu':
            ev += 0.2  # UI docs need professional terminology
        elif content_type == 'technical' and word_lower in ['host name', 'hard-coded']:
            ev += 0.1  # Technical docs need standard terminology
        
        return ev

    def _apply_feedback_clues_h_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for H-words."""
        patterns = self._get_cached_feedback_patterns_h_words()
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

    def _get_cached_feedback_patterns_h_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for H-words."""
        return {
            'often_flagged_terms': {'hit', 'hamburger menu', 'have to', 'how-to'},
            'accepted_terms': {'hardcoded', 'healthcare', 'helpdesk', 'homepage', 'hostname'},
            'ui_documentation_patterns': {
                'flagged': {'hamburger menu', 'hit'},  # UI docs need professional terminology
                'accepted': {'homepage', 'helpdesk'}  # These are standard in UI contexts
            },
            'tutorial_patterns': {
                'flagged': {'hit', 'have to'},  # Tutorials need clear professional language
                'accepted': {'hardcoded', 'hostname'}  # Technical terms acceptable in tutorials
            },
            'technical_patterns': {
                'flagged': {'hard copy', 'host name'},  # Technical docs prefer consistent forms
                'accepted': {'hardcoded', 'hostname', 'healthcare'}  # Standard technical terms
            },
            'procedure_patterns': {
                'flagged': {'hit', 'have to', 'hard-coded'},  # Procedures need precise language
                'accepted': {'homepage', 'helpdesk'}  # Common procedural contexts
            }
        }