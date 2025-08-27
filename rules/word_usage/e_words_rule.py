"""
Word Usage Rule for words starting with 'E'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class EWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'E'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_e'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for E-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define E-word patterns with evidence categories
        e_word_patterns = {
            "e-business": {"alternatives": ["business"], "category": "outdated_term", "severity": "high"},
            "e-mail": {"alternatives": ["email"], "category": "hyphenation", "severity": "high"},
            "easy": {"alternatives": ["simple", "straightforward"], "category": "subjective_claim", "severity": "high"},
            "effortless": {"alternatives": ["simple", "quick"], "category": "subjective_claim", "severity": "high"},
            "e.g.": {"alternatives": ["for example"], "category": "abbreviation", "severity": "medium"},
            "enable": {"alternatives": ["you can", "turn on"], "category": "user_focus", "severity": "medium"},
            "end user": {"alternatives": ["user"], "category": "redundant", "severity": "medium"},
            "enter": {"alternatives": ["type", "specify"], "category": "action_clarity", "severity": "low"},
            "etc": {"alternatives": ["and others", "and more"], "category": "abbreviation", "severity": "medium"},
            "execute": {"alternatives": ["run", "start"], "category": "word_choice", "severity": "low"},
        }

        # Evidence-based analysis for E-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Check exact lemma matches first (single words)
            if token_lemma in e_word_patterns and ' ' not in token_lemma and '-' not in token_lemma:
                matched_pattern = token_lemma
            # Also check for exact text matches (for abbreviations like "e.g.", "etc.")
            elif token_text in e_word_patterns and ' ' not in token_text and '-' not in token_text:
                matched_pattern = token_text
            
            if matched_pattern:
                details = e_word_patterns[matched_pattern]
                
                # Apply surgical guards with exception for abbreviations we want to flag
                should_skip = self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {})
                
                # Override guard for abbreviations in our patterns - we want to flag these
                if should_skip and matched_pattern in ['e.g.', 'etc']:
                    # Check if this is actually our target abbreviation, not a legitimate entity
                    if self._is_target_abbreviation_e_words(token, matched_pattern):
                        should_skip = False
                
                if should_skip:
                    continue
                
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_e_word_evidence(
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
        
        # 2. Multi-word and hyphenated phrase detection (e-mail, end user)
        multi_word_patterns = {pattern: details for pattern, details in e_word_patterns.items() if ' ' in pattern or '-' in pattern}
        
        if multi_word_patterns:
            # Handle hyphenated words (e-mail, e-business) - need special logic for spaCy tokenization
            hyphen_patterns = {pattern: details for pattern, details in multi_word_patterns.items() if '-' in pattern}
            for pattern, details in hyphen_patterns.items():
                # For patterns like "e-mail", look for "e", "-", "mail" sequence
                pattern_parts = pattern.split('-')
                if len(pattern_parts) == 2:
                    first_part, second_part = pattern_parts
                    
                    # Scan through tokens looking for the pattern
                    for i in range(len(doc) - 2):
                        if (doc[i].text.lower() == first_part and 
                            doc[i + 1].text == '-' and 
                            doc[i + 2].text.lower() == second_part):
                            
                            # Found the pattern
                            start_token = doc[i]
                            end_token = doc[i + 2]
                            
                            # Apply surgical guards
                            if self._apply_surgical_zero_false_positive_guards_word_usage(start_token, context or {}):
                                continue
                            
                            sent = start_token.sent
                            sentence_index = 0
                            for j, s in enumerate(doc.sents):
                                if s == sent:
                                    sentence_index = j
                                    break
                            
                            evidence_score = self._calculate_e_word_evidence(
                                pattern, start_token, sent, text, context or {}, details["category"]
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
                                    span=(start_token.idx, end_token.idx + len(end_token.text)),
                                    flagged_text=f"{start_token.text}{doc[i + 1].text}{end_token.text}"
                                ))
            
            # Handle space-separated phrases (end user)
            space_patterns = {pattern: details for pattern, details in multi_word_patterns.items() if ' ' in pattern}
            if space_patterns:
                phrase_matches = self._find_multi_word_phrases_with_lemma(doc, list(space_patterns.keys()), case_sensitive=False)
                
                for match in phrase_matches:
                    pattern = match['phrase']
                    details = space_patterns[pattern]
                    
                    # Apply surgical guards on the first token
                    if self._apply_surgical_zero_false_positive_guards_word_usage(match['start_token'], context or {}):
                        continue
                    
                    sent = match['start_token'].sent
                    sentence_index = 0
                    for i, s in enumerate(doc.sents):
                        if s == sent:
                            sentence_index = i
                            break
                    
                    evidence_score = self._calculate_e_word_evidence(
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

    def _calculate_e_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """Calculate evidence score for E-word usage violations."""
        evidence_score = self._get_base_e_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0
        
        evidence_score = self._apply_linguistic_clues_e_words(evidence_score, word, token, sentence)
        evidence_score = self._apply_structural_clues_e_words(evidence_score, context)
        evidence_score = self._apply_semantic_clues_e_words(evidence_score, word, text, context)
        evidence_score = self._apply_feedback_clues_e_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_base_e_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """Set dynamic base evidence score based on E-word category."""
        if category in ['subjective_claim', 'outdated_term']:
            return 0.95  # "easy", "effortless", "e-business" - high priority
        elif category == 'hyphenation':
            return 0.9  # "e-mail" vs "email"
        elif category == 'user_focus':
            return 0.8  # "enable" - shifts focus from user
        elif category in ['abbreviation', 'redundant']:
            return 0.7  # "e.g.", "etc.", "end user"
        elif category in ['action_clarity', 'word_choice']:
            return 0.55  # "enter", "execute"
        return 0.6

    def _apply_linguistic_clues_e_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply E-word-specific linguistic clues."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # Subjective claim context
        if word_lower in ['easy', 'effortless']:
            claim_indicators = ['very', 'extremely', 'incredibly', 'so']
            if any(claim in sent_text for claim in claim_indicators):
                ev += 0.2  # Intensifiers make subjective claims worse
        
        # User action context
        if word_lower in ['enable', 'enter', 'execute']:
            action_indicators = ['user', 'you', 'click', 'select']
            if any(action in sent_text for action in action_indicators):
                ev += 0.1  # User-facing language needs precision
        
        # Business/marketing context
        if word_lower == 'e-business':
            business_indicators = ['solution', 'service', 'platform']
            if any(biz in sent_text for biz in business_indicators):
                ev += 0.15  # Outdated business terms particularly problematic
        
        return ev

    def _apply_structural_clues_e_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for E-words."""
        block_type = context.get('block_type', 'paragraph')
        
        if block_type in ['step', 'procedure']:
            ev += 0.1  # Procedural content needs precision
        elif block_type == 'heading':
            ev -= 0.1  # Headings more flexible
        
        return ev

    def _apply_semantic_clues_e_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for E-words."""
        content_type = context.get('content_type', 'general')
        word_lower = word.lower()
        
        if content_type == 'tutorial':
            if word_lower in ['easy', 'effortless', 'enable']:
                ev += 0.2  # Tutorials should avoid subjective claims and focus on users
        elif content_type == 'marketing':
            if word_lower in ['easy', 'effortless', 'e-business']:
                ev += 0.15  # Marketing copy needs modern, precise language
        elif content_type == 'technical':
            if word_lower in ['e.g.', 'etc.', 'execute']:
                ev += 0.1  # Technical docs need formal language
        
        return ev

    def _is_target_abbreviation_e_words(self, token, pattern: str) -> bool:
        """
        Check if a token flagged by entity recognition is actually our target abbreviation.
        """
        # For "e.g." - if it's tagged as ORG but is clearly the abbreviation
        if pattern == 'e.g.':
            if token.text.lower() in ['e.g.', 'eg', 'e.g']:
                return True
        
        # For "etc" - this should be flagged if it's the Latin abbreviation
        elif pattern == 'etc':
            if token.text.lower() in ['etc.', 'etc', 'et cetera']:
                return True
        
        return False

    def _apply_feedback_clues_e_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for E-words."""
        patterns = {'often_flagged_terms': {'easy', 'e-mail', 'enable', 'effortless'}, 'accepted_terms': set()}
        word_lower = word.lower()
        
        if word_lower in patterns.get('often_flagged_terms', set()):
            ev += 0.1
        elif word_lower in patterns.get('accepted_terms', set()):
            ev -= 0.2
        
        return ev