"""
Word Usage Rule for words starting with 'M'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection combined with context-aware analysis.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class MWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'M'.
    Enhanced with spaCy PhraseMatcher for efficient detection combined with context-aware analysis.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_m'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for M-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define M-word patterns with evidence categories
        m_word_patterns = {
            "man-hour": {"alternatives": ["person hour", "labor hour"], "category": "inclusive_language", "severity": "high"},
            "man day": {"alternatives": ["person day"], "category": "inclusive_language", "severity": "high"},
            "master": {"alternatives": ["primary", "main", "controller"], "category": "inclusive_language", "severity": "high"},
            "may": {"alternatives": ["can", "might"], "category": "word_distinction", "severity": "medium"},
            "menu bar": {"alternatives": ["menubar"], "category": "spacing", "severity": "low"},
            "meta data": {"alternatives": ["metadata"], "category": "spacing", "severity": "low"},
            "methodology": {"alternatives": ["method"], "category": "word_choice", "severity": "low"},
            "migrate": {"alternatives": ["move", "transfer"], "category": "technical_precision", "severity": "medium"},
            "minimize": {"alternatives": ["reduce"], "category": "word_choice", "severity": "low"},
            "maximize": {"alternatives": ["increase"], "category": "word_choice", "severity": "low"},
            "mouse click": {"alternatives": ["click"], "category": "redundancy", "severity": "low"},
        }

        # Evidence-based analysis for M-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches with special handling for "master"
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Special handling for "master" - only flag in master/slave context
            if token_lemma == 'master' or token_text == 'master':
                # Check if 'slave' appears in the same sentence for problematic master/slave terminology
                sent_text = token.sent.text.lower()
                if 'slave' in sent_text:
                    matched_pattern = 'master'
            # Check other single words (excluding multi-word patterns)
            elif (token_lemma in m_word_patterns and ' ' not in token_lemma and 
                  token_lemma != 'master'):  # Skip 'master' as it's handled above
                matched_pattern = token_lemma
            elif (token_text in m_word_patterns and ' ' not in token_text and
                  token_text != 'master'):  # Skip 'master' as it's handled above
                matched_pattern = token_text
            
            if matched_pattern:
                details = m_word_patterns[matched_pattern]
                
                # Apply surgical guards
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue
                
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_m_word_evidence(
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

        # 2. Hyphenated word detection for M-words
        hyphenated_patterns = ['man-hour']
        for i in range(len(doc) - 2):
            if (i < len(doc) - 2 and 
                doc[i + 1].text == "-" and
                doc[i].text.lower() + "-" + doc[i + 2].text.lower() in hyphenated_patterns):
                
                hyphenated_word = doc[i].text.lower() + "-" + doc[i + 2].text.lower()
                if hyphenated_word in m_word_patterns:
                    details = m_word_patterns[hyphenated_word]
                    
                    # Apply surgical guards on the first token
                    if self._apply_surgical_zero_false_positive_guards_word_usage(doc[i], context or {}):
                        continue
                    
                    sent = doc[i].sent
                    sentence_index = 0
                    for j, s in enumerate(doc.sents):
                        if s == sent:
                            sentence_index = j
                            break
                    
                    evidence_score = self._calculate_m_word_evidence(
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

        # 3. Multi-word phrase detection for M-words
        multi_word_patterns = {pattern: details for pattern, details in m_word_patterns.items() if ' ' in pattern}
        
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
                
                evidence_score = self._calculate_m_word_evidence(
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

        # 4. Special handling for "meta data" due to lemma issues ("data" -> "datum")
        for i in range(len(doc) - 1):
            if (doc[i].text.lower() == "meta" and 
                i + 1 < len(doc) and 
                doc[i + 1].text.lower() == "data"):
                
                if "meta data" in m_word_patterns:
                    details = m_word_patterns["meta data"]
                    
                    # Apply surgical guards on the first token
                    if self._apply_surgical_zero_false_positive_guards_word_usage(doc[i], context or {}):
                        continue
                    
                    sent = doc[i].sent
                    sentence_index = 0
                    for j, s in enumerate(doc.sents):
                        if s == sent:
                            sentence_index = j
                            break
                    
                    evidence_score = self._calculate_m_word_evidence(
                        "meta data", doc[i], sent, text, context or {}, details["category"]
                    )
                    
                    if evidence_score > 0.1:
                        start_char = doc[i].idx
                        end_char = doc[i + 1].idx + len(doc[i + 1].text)
                        flagged_text = doc[i].text + " " + doc[i + 1].text
                        
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message("meta data", evidence_score, details["category"]),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions("meta data", details["alternatives"], evidence_score, context or {}, details["category"]),
                            severity=details["severity"] if evidence_score < 0.7 else 'high',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(start_char, end_char),
                            flagged_text=flagged_text
                        ))
        
        return errors

    def _calculate_m_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for M-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and violation type
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        
        Args:
            word: The M-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (inclusive_language, word_distinction, spacing, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_m_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_m_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_m_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_m_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_m_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_m_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on M-word category and violation specificity.
        Higher priority categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # Very high-risk inclusive language issues
        if category == 'inclusive_language':
            if word_lower in ['man-hour', 'man day']:
                return 0.95  # Gender-specific terms - critical for inclusive content
            elif word_lower == 'master':
                return 0.9  # Master/slave terminology - highly problematic
            else:
                return 0.9  # Other inclusive language issues
        
        # High-risk precision and clarity issues
        elif category in ['technical_precision', 'word_distinction']:
            if word_lower == 'migrate':
                return 0.75  # Technical precision important
            elif word_lower == 'may':
                # Lower base score for "may" as it's often acceptable in technical contexts
                return 0.6  # Word distinction for clarity but context-dependent
            else:
                return 0.7  # Other precision issues
        
        # Medium-risk redundancy and word choice
        elif category in ['word_choice', 'redundancy']:
            if word_lower in ['minimize', 'maximize']:
                return 0.6  # Word choice precision
            elif word_lower == 'mouse click':
                return 0.55  # Redundancy reduction
            elif word_lower == 'methodology':
                return 0.5  # Simpler alternatives preferred
            else:
                return 0.55  # Other word choice issues
        
        # Lower risk spacing and consistency issues
        elif category == 'spacing':
            if word_lower in ['menu bar', 'meta data']:
                return 0.5  # Spacing consistency
            else:
                return 0.5  # Other spacing issues
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_m_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply M-word-specific linguistic clues using SpaCy analysis."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # === INCLUSIVE LANGUAGE CLUES ===
        if word_lower in ['man-hour', 'man day']:
            # Project and resource planning contexts increase importance
            if any(indicator in sent_text for indicator in ['estimate', 'project', 'resource', 'planning', 'budget']):
                ev += 0.2  # Project context needs inclusive language
            elif any(indicator in sent_text for indicator in ['team', 'staff', 'workforce', 'capacity']):
                ev += 0.15  # Personnel context especially important
        
        if word_lower == 'master':
            # Master/slave terminology detection (already filtered to only these contexts)
            if any(indicator in sent_text for indicator in ['slave', 'primary', 'secondary', 'controller']):
                ev += 0.25  # Master/slave terminology needs inclusive alternatives
            elif any(indicator in sent_text for indicator in ['device', 'server', 'node', 'system']):
                ev += 0.2  # Technical master/slave context
        
        # === TECHNICAL PRECISION CLUES ===
        if word_lower == 'migrate':
            # Technical migration contexts need precise terminology
            if any(indicator in sent_text for indicator in ['upgrade', 'port', 'version', 'deployment']):
                ev += 0.2  # Technical context needs precise terminology
            elif any(indicator in sent_text for indicator in ['user', 'customer', 'data']):
                ev += 0.15  # User/data migration contexts
        
        # === WORD DISTINCTION CLUES ===
        if word_lower == 'may':
            # Analyze context to determine if "can" or "might" is better
            if any(indicator in sent_text for indicator in ['permission', 'allowed', 'authorized']):
                ev += 0.15  # Permission context suggests "can"
            elif any(indicator in sent_text for indicator in ['possibility', 'perhaps', 'potentially']):
                ev += 0.1  # Possibility context suggests "might"
            elif any(indicator in sent_text for indicator in ['ability', 'capable', 'able']):
                ev += 0.1  # Ability context suggests "can"
        
        # === WORD CHOICE AND REDUNDANCY CLUES ===
        if word_lower in ['minimize', 'maximize']:
            # Technical or mathematical contexts
            if any(indicator in sent_text for indicator in ['performance', 'efficiency', 'optimization']):
                ev += 0.1  # Technical optimization context
        
        if word_lower == 'mouse click':
            # UI instruction contexts
            if any(indicator in sent_text for indicator in ['button', 'interface', 'menu', 'icon']):
                ev += 0.1  # UI context where "click" alone is clearer
        
        if word_lower == 'methodology':
            # Academic or process contexts
            if any(indicator in sent_text for indicator in ['process', 'approach', 'procedure', 'technique']):
                ev += 0.1  # Process context where "method" is simpler
        
        # === SPACING AND CONSISTENCY CLUES ===
        if word_lower in ['menu bar', 'meta data']:
            # Technical documentation contexts
            if any(indicator in sent_text for indicator in ['interface', 'application', 'software', 'system']):
                ev += 0.1  # Technical contexts prefer compound forms
        
        return ev

    def _apply_structural_clues_m_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for M-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_m_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for M-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'customer_facing' and word_lower in ['man-hour', 'man day', 'master']:
            ev += 0.3  # Customer content must use inclusive language
        elif content_type == 'technical' and word_lower in ['migrate', 'master']:
            ev += 0.2  # Technical docs need precise, inclusive terminology
        elif content_type == 'international' and word_lower in ['man-hour', 'man day']:
            ev += 0.25  # International content requires inclusive language
        
        if audience == 'global' and word_lower in ['man-hour', 'man day', 'master']:
            ev += 0.2  # Global audiences need inclusive terminology
        elif audience == 'external' and word_lower in ['man-hour', 'man day']:
            ev += 0.25  # External audiences need inclusive language
        
        return ev

    def _apply_feedback_clues_m_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for M-words."""
        patterns = self._get_cached_feedback_patterns_m_words()
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
            ev -= 0.3  # Strong reduction for context-appropriate terms
        
        return ev

    def _get_cached_feedback_patterns_m_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for M-words."""
        return {
            'often_flagged_terms': {'man-hour', 'man day', 'master', 'migrate', 'mouse click', 'methodology'},
            'accepted_terms': set(),  # Context-dependent acceptance
            'technical_patterns': {
                'flagged': {'man-hour', 'man day', 'migrate', 'menu bar', 'meta data'},  # Technical docs need precision
                'accepted': {'master', 'may', 'minimize', 'maximize'}  # Sometimes acceptable in technical contexts
            },
            'customer_facing_patterns': {
                'flagged': {'man-hour', 'man day', 'master', 'methodology', 'migrate'},  # Customer content needs inclusive/clear language
                'accepted': {'may', 'menu bar'}  # Customer-friendly terms
            },
            'international_patterns': {
                'flagged': {'man-hour', 'man day', 'master', 'methodology'},  # International content needs inclusive language
                'accepted': {'may', 'migrate', 'meta data'}  # Technical terms acceptable
            },
            'formal_patterns': {
                'flagged': {'mouse click', 'methodology'},  # Formal writing prefers precise language
                'accepted': {'may', 'migrate', 'master'}  # Formal contexts sometimes accept these
            },
            'procedure_patterns': {
                'flagged': {'mouse click', 'methodology', 'man-hour'},  # Procedures need clear language
                'accepted': {'may', 'migrate', 'menu bar'}  # Procedural terms acceptable
            },
            'general_patterns': {
                'flagged': {'methodology', 'mouse click'},  # General content prefers simple language
                'accepted': {'may', 'menu bar', 'meta data'}  # Common terms acceptable
            }
        }