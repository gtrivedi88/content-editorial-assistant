"""
Word Usage Rule for words starting with 'T' (Production-Grade)
Evidence-based analysis with surgical zero false positive guards for T-word usage detection.
Based on IBM Style Guide recommendations with production-grade evidence calculation.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class TWordsRule(BaseWordUsageRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect usage of specific words starting with 'T'.
    
    Implements evidence-based analysis with:
    - Surgical zero false positive guards for T-word usage
    - Dynamic base evidence scoring based on word specificity and context
    - Context-aware adjustments for different writing domains
    
    Features:
    - Near 100% false positive elimination through surgical guards
    - Word-specific evidence calculation for each T-word violation
    - Evidence-aware suggestions tailored to writing context
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_t'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for T-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define T-word patterns with evidence categories
        t_word_patterns = {
            "tap on": {"alternatives": ["tap"], "category": "redundant_preposition", "severity": "medium"},
            "tarball": {"alternatives": [".tar file"], "category": "jargon", "severity": "medium"},
            "team room": {"alternatives": ["teamroom"], "category": "spacing", "severity": "low"},
            "terminate": {"alternatives": ["end", "stop"], "category": "word_choice", "severity": "low"},
            "thank you": {"alternatives": ["(remove)"], "category": "cultural_sensitivity", "severity": "medium"},
            "that": {"alternatives": ["that (include for clarity)"], "category": "clarity", "severity": "low"},
            "time frame": {"alternatives": ["timeframe"], "category": "spacing", "severity": "low"},
            "time out": {"alternatives": ["time out (verb)", "timeout (noun)"], "category": "form_usage", "severity": "low"},
            "toast": {"alternatives": ["notification"], "category": "ui_language", "severity": "medium"},
            "tool kit": {"alternatives": ["toolkit"], "category": "spacing", "severity": "low"},
            "trade-off": {"alternatives": ["tradeoff"], "category": "hyphenation", "severity": "low"},
            "transparent": {"alternatives": ["clear", "obvious"], "category": "ambiguous_term", "severity": "medium"},
            "tribe": {"alternatives": ["team", "squad"], "category": "inclusive_language", "severity": "high"},
            "try and": {"alternatives": ["try to"], "category": "grammar", "severity": "medium"},
            "text": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "table": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "true": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "test": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
        }

        # Evidence-based analysis for T-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Check single words (excluding multi-word patterns) - case-insensitive
            for pattern in t_word_patterns:
                if ' ' not in pattern and '-' not in pattern:  # Single word pattern (no hyphens/spaces)
                    if (token_lemma == pattern.lower() or 
                        token_text == pattern.lower()):
                        matched_pattern = pattern
                        break
            
            if matched_pattern:
                details = t_word_patterns[matched_pattern]
                
                # Skip acceptable usage patterns
                if details["category"] == "acceptable_usage":
                    continue
                
                # Apply surgical guards
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue
                
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_t_word_evidence(
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

        # 2. Multi-word phrase detection for T-words (including hyphenated words)
        multi_word_patterns = {pattern: details for pattern, details in t_word_patterns.items() if (' ' in pattern or '-' in pattern) and details["category"] != "acceptable_usage"}
        
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
                
                evidence_score = self._calculate_t_word_evidence(
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

        # 3. Special handling for hyphenated T-words
        # Handle patterns like "trade-off" that are tokenized as ["word", "-", "word"]
        hyphenated_patterns = {
            'trade-off': {'alternatives': ['tradeoff'], 'category': 'hyphenation', 'severity': 'low'}
        }
        
        for i in range(len(doc) - 2):
            token1 = doc[i]
            hyphen = doc[i + 1]
            token2 = doc[i + 2]
            
            if hyphen.text == '-':
                # Check if this forms a hyphenated pattern we're looking for
                combined_text = f"{token1.text.lower()}-{token2.text.lower()}"
                
                if combined_text in hyphenated_patterns:
                    details = hyphenated_patterns[combined_text]
                    
                    # Apply surgical guards on the first token
                    if self._apply_surgical_zero_false_positive_guards_word_usage(token1, context or {}):
                        continue
                    
                    sent = token1.sent
                    sentence_index = 0
                    for j, s in enumerate(doc.sents):
                        if s == sent:
                            sentence_index = j
                            break
                    
                    evidence_score = self._calculate_t_word_evidence(
                        combined_text, token1, sent, text, context or {}, details["category"]
                    )
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message(combined_text, evidence_score, details["category"]),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions(combined_text, details["alternatives"], evidence_score, context or {}, details["category"]),
                            severity=details["severity"] if evidence_score < 0.7 else 'high',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(token1.idx, token2.idx + len(token2.text)),
                            flagged_text=f"{token1.text}-{token2.text}"
                        ))
        
        return errors

    def _calculate_t_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for T-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and violation type
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        - Special handling for inclusive language and cultural sensitivity
        
        Args:
            word: The T-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (inclusive_language, cultural_sensitivity, jargon, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_t_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_t_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_t_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_t_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_t_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_t_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on T-word category and violation specificity.
        Higher priority categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # Very high-risk inclusive language issues
        if category == 'inclusive_language':
            if word_lower == 'tribe':
                return 0.85  # Critical inclusive language violation
            else:
                return 0.85  # Other inclusive language issues
        
        # High-risk professionalism and clarity issues
        elif category in ['jargon', 'ui_language', 'cultural_sensitivity']:
            if word_lower == 'tarball':
                return 0.75  # Technical jargon clarity
            elif word_lower == 'toast':
                return 0.7   # UI terminology professionalism
            elif word_lower == 'thank you':
                return 0.8   # Cultural sensitivity critical
            else:
                return 0.75  # Other professionalism issues
        
        # Medium-high risk clarity and correctness issues
        elif category in ['redundant_preposition', 'grammar', 'ambiguous_term']:
            if word_lower == 'tap on':
                return 0.65  # Redundant preposition clarity
            elif word_lower == 'try and':
                return 0.7   # Grammar correctness important
            elif word_lower == 'transparent':
                return 0.65  # Ambiguous term clarity
            else:
                return 0.7   # Other clarity issues
        
        # Medium-risk improvement opportunities
        elif category in ['word_choice', 'form_usage', 'clarity']:
            if word_lower == 'terminate':
                return 0.55  # Word choice context-dependent
            elif word_lower == 'time out':
                return 0.6   # Form usage important
            elif word_lower == 'that':
                return 0.5   # Clarity context-dependent
            else:
                return 0.6   # Other improvement opportunities
        
        # Lower-risk consistency issues
        elif category in ['spacing', 'hyphenation']:
            if word_lower in ['team room', 'time frame', 'tool kit']:
                return 0.45  # Spacing consistency
            elif word_lower == 'trade-off':
                return 0.5   # Hyphenation consistency
            else:
                return 0.5   # Other consistency issues
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_t_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply T-word-specific linguistic clues using SpaCy analysis."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # === INCLUSIVE LANGUAGE CLUES ===
        if word_lower == 'tribe':
            # Organizational context needs inclusive language
            if any(indicator in sent_text for indicator in ['team', 'organization', 'group', 'department']):
                ev += 0.3  # Strong organizational context suggests inclusive language need
            elif any(indicator in sent_text for indicator in ['work', 'project', 'collaboration', 'members']):
                ev += 0.2  # Work context benefits from inclusive language
            elif any(indicator in sent_text for indicator in ['culture', 'values', 'community']):
                ev += 0.15  # Cultural context needs sensitivity
        
        # === CULTURAL SENSITIVITY CLUES ===
        if word_lower == 'thank you':
            # Technical content should avoid cultural assumptions
            if any(indicator in sent_text for indicator in ['technical', 'documentation', 'guide', 'manual']):
                ev += 0.2  # Technical content should be culturally neutral
            elif any(indicator in sent_text for indicator in ['instruction', 'procedure', 'step']):
                ev += 0.15  # Procedural content benefits from objectivity
            elif any(indicator in sent_text for indicator in ['international', 'global', 'worldwide']):
                ev += 0.25  # International content needs cultural neutrality
        
        # === UI LANGUAGE CLUES ===
        if word_lower == 'toast':
            # UI context needs professional terminology
            if any(indicator in sent_text for indicator in ['ui', 'interface', 'notification', 'alert']):
                ev += 0.15  # UI context needs professional terminology
            elif any(indicator in sent_text for indicator in ['display', 'show', 'appear', 'popup']):
                ev += 0.1  # Display context benefits from precise terminology
            elif any(indicator in sent_text for indicator in ['user', 'customer', 'client']):
                ev += 0.05  # User-facing context benefits from clear language
        
        # === GRAMMAR CLUES ===
        if word_lower == 'try and':
            # Action context benefits from correct grammar
            if any(indicator in sent_text for indicator in ['attempt', 'effort', 'action', 'goal']):
                ev += 0.15  # Action context benefits from correct grammar
            elif any(indicator in sent_text for indicator in ['procedure', 'instruction', 'step']):
                ev += 0.1  # Procedural context needs grammatical precision
            # Check grammatical context using POS tags
            if hasattr(token, 'head') and token.head.pos_ in ['VERB']:
                if token.head.lemma_.lower() in ['will', 'should', 'must', 'can']:
                    ev += 0.05  # Modal context suggests infinitive usage
        
        # === JARGON CLUES ===
        if word_lower == 'tarball':
            # Technical jargon clarity for broader audiences
            if any(indicator in sent_text for indicator in ['user', 'customer', 'documentation', 'guide']):
                ev += 0.2  # User-facing content needs accessible language
            elif any(indicator in sent_text for indicator in ['download', 'install', 'extract']):
                ev += 0.15  # User action context benefits from clear terminology
            elif any(indicator in sent_text for indicator in ['file', 'archive', 'package']):
                ev += 0.1  # File context can benefit from standard terminology
        
        # === REDUNDANT PREPOSITION CLUES ===
        if word_lower == 'tap on':
            # Redundancy context
            if any(indicator in sent_text for indicator in ['button', 'link', 'icon', 'menu']):
                ev += 0.1  # UI element context benefits from concise language
            elif any(indicator in sent_text for indicator in ['click', 'select', 'touch']):
                ev += 0.05  # Action context can be more concise
        
        # === AMBIGUOUS TERM CLUES ===
        if word_lower == 'transparent':
            # Ambiguity context
            if any(indicator in sent_text for indicator in ['process', 'operation', 'system']):
                ev += 0.15  # Technical context needs precise language
            elif any(indicator in sent_text for indicator in ['user', 'visible', 'obvious']):
                ev += 0.1  # User experience context benefits from clarity
        
        # === WORD CHOICE CLUES ===
        if word_lower == 'terminate':
            # Context-dependent word choice
            if any(indicator in sent_text for indicator in ['user', 'customer', 'person']):
                ev += 0.15  # People context benefits from gentler language
            elif any(indicator in sent_text for indicator in ['process', 'session', 'connection']):
                ev += 0.05  # Technical context may accept technical terms
        
        return ev

    def _apply_structural_clues_t_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for T-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_t_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for T-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'customer_facing' and word_lower in ['tribe', 'tarball', 'thank you']:
            ev += 0.25  # Customer content needs professional, inclusive language
        elif content_type == 'international' and word_lower in ['tribe', 'thank you']:
            ev += 0.2  # International content requires inclusive, neutral language
        elif content_type == 'technical' and word_lower in ['tarball', 'terminate']:
            ev += 0.15  # Technical docs benefit from clear, standard terminology
        elif content_type == 'ui_documentation' and word_lower == 'toast':
            ev += 0.2  # UI docs need professional interface terminology
        
        if audience == 'external' and word_lower in ['tribe', 'tarball']:
            ev += 0.2  # External audiences need clear, professional language
        elif audience == 'global' and word_lower in ['tribe', 'thank you']:
            ev += 0.15  # Global audiences need inclusive, culturally neutral language
        
        return ev

    def _apply_feedback_clues_t_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for T-words."""
        patterns = self._get_cached_feedback_patterns_t_words()
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

    def _get_cached_feedback_patterns_t_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for T-words."""
        return {
            'often_flagged_terms': {'tribe', 'toast', 'thank you', 'try and', 'tarball', 'transparent'},
            'accepted_terms': {'text', 'table', 'true', 'test', 'terminate'},  # Generally acceptable terms in some contexts
            'technical_patterns': {
                'flagged': {'tribe', 'toast', 'thank you'},  # Technical docs need professional language
                'accepted': {'terminate', 'time out', 'tarball', 'text', 'table'}  # Technical terms acceptable
            },
            'customer_facing_patterns': {
                'flagged': {'tribe', 'tarball', 'thank you', 'toast', 'terminate'},  # Customer content needs accessible language
                'accepted': {'text', 'table', 'true', 'test'}  # Customer-friendly terms
            },
            'ui_documentation_patterns': {
                'flagged': {'toast', 'tap on', 'tribe'},  # UI docs need professional terminology
                'accepted': {'text', 'table', 'time out', 'test'}  # UI context terms
            },
            'international_patterns': {
                'flagged': {'tribe', 'thank you', 'transparent'},  # International content needs cultural neutrality
                'accepted': {'text', 'table', 'true', 'test'}  # Neutral terms
            },
            'documentation_patterns': {
                'flagged': {'tribe', 'thank you', 'tarball', 'try and'},  # Documentation needs clear language
                'accepted': {'text', 'table', 'test', 'terminate'}  # Documentation-friendly terms
            },
            'formal_patterns': {
                'flagged': {'toast', 'try and', 'tribe'},  # Formal writing prefers precise language
                'accepted': {'terminate', 'text', 'table', 'true'}  # Formal terms acceptable
            },
            'general_patterns': {
                'flagged': {'tribe', 'toast', 'thank you'},  # General content prefers inclusive language
                'accepted': {'text', 'table', 'true', 'test', 'terminate'}  # Common terms acceptable
            }
        }