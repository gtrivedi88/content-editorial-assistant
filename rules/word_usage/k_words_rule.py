"""
Word Usage Rule for 'key'
Enhanced with spaCy POS analysis for context-aware detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class KWordsRule(BaseWordUsageRule):
    """
    Checks for potentially incorrect usage of the word 'key'.
    Enhanced with spaCy POS analysis for context-aware detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_k'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for K-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define K-word patterns with evidence categories
        k_word_patterns = {
            "key": {"alternatives": ["press", "type", "enter"], "category": "verb_misuse", "severity": "medium"},
            "keyboard shortcut": {"alternatives": ["keyboard shortcuts"], "category": "spacing", "severity": "low"},
            "kick off": {"alternatives": ["start", "begin"], "category": "informal_language", "severity": "medium"},
            "kill": {"alternatives": ["stop", "end", "terminate"], "category": "harsh_language", "severity": "high"},
            "kind of": {"alternatives": ["somewhat", "rather"], "category": "informal_qualifier", "severity": "medium"},
            "know-how": {"alternatives": ["knowledge", "expertise"], "category": "hyphenation", "severity": "low"},
        }

        # Evidence-based analysis for K-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches with special POS handling for "key"
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Special handling for "key" - flag when used as verb OR in phrasal verb "key in"
            if token_lemma == 'key':
                # Check if it's used as verb OR part of "key in" phrasal verb
                next_token = token.nbor(1) if token.i < len(doc) - 1 else None
                is_key_in_phrasal = (next_token and next_token.text.lower() == 'in' and 
                                   next_token.pos_ in ['ADP', 'PART'])  # Preposition or particle
                
                if token.pos_ == 'VERB' or is_key_in_phrasal:
                    matched_pattern = 'key'
            # Check other single words (excluding multi-word patterns)
            elif (token_lemma in k_word_patterns and ' ' not in token_lemma and 
                  token_lemma != 'key'):  # Skip 'key' as it's handled above
                matched_pattern = token_lemma
            elif (token_text in k_word_patterns and ' ' not in token_text and
                  token_text != 'key'):  # Skip 'key' as it's handled above
                matched_pattern = token_text
            
            if matched_pattern:
                details = k_word_patterns[matched_pattern]
                
                # Apply surgical guards
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue
                
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_k_word_evidence(
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

        # 2. Hyphenated word detection for K-words
        hyphenated_patterns = ['know-how']
        for i in range(len(doc) - 2):
            if (i < len(doc) - 2 and 
                doc[i + 1].text == "-" and
                doc[i].text.lower() + "-" + doc[i + 2].text.lower() in hyphenated_patterns):
                
                hyphenated_word = doc[i].text.lower() + "-" + doc[i + 2].text.lower()
                if hyphenated_word in k_word_patterns:
                    details = k_word_patterns[hyphenated_word]
                    
                    # Apply surgical guards on the first token
                    if self._apply_surgical_zero_false_positive_guards_word_usage(doc[i], context or {}):
                        continue
                    
                    sent = doc[i].sent
                    sentence_index = 0
                    for j, s in enumerate(doc.sents):
                        if s == sent:
                            sentence_index = j
                            break
                    
                    evidence_score = self._calculate_k_word_evidence(
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

        # 3. Multi-word phrase detection for K-words
        multi_word_patterns = {pattern: details for pattern, details in k_word_patterns.items() if ' ' in pattern}
        
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
                
                evidence_score = self._calculate_k_word_evidence(
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

    def _calculate_k_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for K-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and violation type
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        
        Args:
            word: The K-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (verb_misuse, harsh_language, informal_language, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_k_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_k_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_k_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_k_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_k_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_k_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on K-word category and violation specificity.
        Higher priority categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # Very high-risk harsh language
        if category == 'harsh_language':
            return 0.9  # "kill" - avoid violent language in professional content
        
        # High-risk verb misuse in action contexts
        elif category == 'verb_misuse':
            return 0.8  # "key" as verb - needs specific action verbs for clarity
        
        # Medium-high risk informal language and qualifiers
        elif category in ['informal_language', 'informal_qualifier']:
            if word_lower == 'kick off':
                return 0.75  # Common but informal phrase
            elif word_lower == 'kind of':
                return 0.7  # Vague qualifier that weakens writing
            else:
                return 0.7  # Other informal language issues
        
        # Lower risk spacing and hyphenation issues
        elif category in ['spacing', 'hyphenation']:
            return 0.4  # "keyboard shortcuts", "know-how" - style consistency
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_k_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply K-word-specific linguistic clues using SpaCy analysis."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # === VERB MISUSE CLUES ===
        if word_lower == 'key':
            # Check if used as verb in action contexts
            if token.pos_ == 'VERB':
                # Technical action contexts require precise verbs
                if any(indicator in sent_text for indicator in ['keyboard', 'button', 'password', 'command', 'shortcut']):
                    ev += 0.2  # Action context needs "press" or "type"
                elif any(indicator in sent_text for indicator in ['enter', 'input', 'data', 'information']):
                    ev += 0.15  # Data entry context needs clear action verbs
                elif any(indicator in sent_text for indicator in ['system', 'computer', 'device']):
                    ev += 0.1  # Technical context benefits from precision
        
        # === HARSH LANGUAGE CLUES ===
        if word_lower == 'kill':
            # Check context to see if it's appropriate technical usage vs harsh language
            if any(indicator in sent_text for indicator in ['process', 'task', 'application', 'service', 'running', 'session']):
                ev -= 0.7  # Technical "kill process" context is much more acceptable
            elif any(indicator in sent_text for indicator in ['system', 'program', 'thread', 'job']):
                ev -= 0.6  # System/program context is technical
            elif any(indicator in sent_text for indicator in ['user', 'customer', 'person', 'team']):
                ev += 0.2  # Human context makes harsh language worse
        
        # === INFORMAL LANGUAGE CLUES ===
        if word_lower == 'kick off':
            # Check if in formal business context
            if any(indicator in sent_text for indicator in ['meeting', 'project', 'initiative', 'ceremony']):
                ev += 0.1  # Business contexts benefit from "start" or "begin"
        
        if word_lower == 'kind of':
            # Vague qualifier analysis
            if token.dep_ in ['advmod', 'amod']:  # Adverbial or adjectival modifier
                ev += 0.15  # Weakens statements, better to be precise
        
        # === SPACING/HYPHENATION CLUES ===
        if word_lower == 'know-how':
            # Technical documentation context
            if any(indicator in sent_text for indicator in ['technical', 'expertise', 'skill', 'knowledge']):
                ev += 0.1  # Formal contexts prefer "knowledge" or "expertise"
        
        return ev

    def _apply_structural_clues_k_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for K-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.15  # Procedural content needs precise action verbs
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_k_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for K-words."""
        content_type = context.get('content_type', 'general')
        word_lower = word.lower()
        
        if content_type == 'tutorial' and word_lower == 'key':
            ev += 0.2  # Tutorials need clear, unambiguous action instructions
        elif content_type == 'technical' and word_lower == 'key':
            ev += 0.15  # Technical docs benefit from precise terminology
        elif content_type == 'user_interface' and word_lower == 'key':
            ev += 0.15  # UI instructions need clear action verbs
        
        return ev

    def _apply_feedback_clues_k_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for K-words."""
        patterns = self._get_cached_feedback_patterns_k_words()
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
            ev -= 0.25  # Strong reduction for context-appropriate terms
        
        return ev

    def _get_cached_feedback_patterns_k_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for K-words."""
        return {
            'often_flagged_terms': {'key', 'kill', 'kick off', 'kind of'},
            'accepted_terms': set(),  # Context-dependent acceptance
            'technical_patterns': {
                'flagged': {'key', 'know-how'},  # Technical docs need precision
                'accepted': {'kill', 'keyboard shortcuts'}  # Technical terms sometimes acceptable
            },
            'tutorial_patterns': {
                'flagged': {'key', 'kill', 'kind of'},  # Tutorials need clear language
                'accepted': {'keyboard shortcuts'}  # Technical terms in tutorials
            },
            'formal_patterns': {
                'flagged': {'kick off', 'kind of', 'kill'},  # Formal writing avoids informal/harsh language
                'accepted': set()
            },
            'procedure_patterns': {
                'flagged': {'key', 'kick off', 'kind of'},  # Procedures need precise language
                'accepted': {'kill', 'keyboard shortcut', 'keyboard shortcuts'}  # "Kill process" and technical terms acceptable in procedures
            },
            'user_interface_patterns': {
                'flagged': {'key', 'kill', 'kind of'},  # UI docs need clear actions
                'accepted': {'keyboard shortcut', 'keyboard shortcuts'}  # UI elements acceptable
            },
            'general_patterns': {
                'flagged': {'kill', 'kind of'},  # General content avoids harsh/vague language
                'accepted': {'kick off'}  # "Kick off" sometimes acceptable in general content
            }
        }