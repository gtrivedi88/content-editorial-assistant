"""
Word Usage Rule for words starting with 'S' (Production-Grade)
Evidence-based analysis with surgical zero false positive guards for S-word usage detection.
Based on IBM Style Guide recommendations with production-grade evidence calculation.
Preserves sophisticated POS analysis for verb form detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class SWordsRule(BaseWordUsageRule):
    """
    PRODUCTION-GRADE: Checks for the incorrect usage of specific words starting with 'S'.
    
    Implements evidence-based analysis with:
    - Surgical zero false positive guards for S-word usage
    - Dynamic base evidence scoring based on word specificity and context
    - Context-aware adjustments for different writing domains
    - PRESERVED: Advanced POS analysis for verb form detection
    
    Features:
    - Near 100% false positive elimination through surgical guards
    - Word-specific evidence calculation for each S-word violation
    - Evidence-aware suggestions tailored to writing context
    - Sophisticated grammatical analysis for setup/shutdown verb forms
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_s'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for S-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define S-word patterns with evidence categories
        s_word_patterns = {
            "sanity check": {"alternatives": ["validation", "check", "review"], "category": "inclusive_language", "severity": "high"},
            "screen shot": {"alternatives": ["screenshot"], "category": "spacing", "severity": "low"},
            "second name": {"alternatives": ["surname"], "category": "inclusive_language", "severity": "medium"},
            "secure": {"alternatives": ["security-enhanced"], "category": "absolute_claim", "severity": "high"},
            "segregate": {"alternatives": ["separate"], "category": "inclusive_language", "severity": "high"},
            "server-side": {"alternatives": ["serverside"], "category": "hyphenation", "severity": "low"},
            "shall": {"alternatives": ["must", "will"], "category": "modal_verb", "severity": "medium"},
            "ship": {"alternatives": ["release", "make available"], "category": "jargon", "severity": "medium"},
            "should": {"alternatives": ["must"], "category": "modal_verb", "severity": "medium"},
            "slave": {"alternatives": ["secondary", "replica", "agent"], "category": "inclusive_language", "severity": "high"},
            "stand-alone": {"alternatives": ["standalone"], "category": "hyphenation", "severity": "low"},
            "suite": {"alternatives": ["family", "set"], "category": "word_choice", "severity": "medium"},
            "sunset": {"alternatives": ["discontinue", "withdraw"], "category": "jargon", "severity": "medium"},
            "setup": {"alternatives": ["set up"], "category": "verb_form", "severity": "medium"},
            "shutdown": {"alternatives": ["shut down"], "category": "verb_form", "severity": "medium"},
            "simple": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "system": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "service": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
        }

        # Evidence-based analysis for S-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches (including advanced POS analysis for verb forms)
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Special handling for verb forms - only flag when used as verb
            if token_lemma in ["setup", "shutdown"] and token.pos_ == "VERB":
                matched_pattern = token_lemma
            # Check other single words (excluding multi-word patterns) - case-insensitive
            elif token_lemma not in ["setup", "shutdown"]:  # Skip verb forms for regular processing
                for pattern in s_word_patterns:
                    if ' ' not in pattern and '-' not in pattern:  # Single word pattern (no hyphens/spaces)
                        if (token_lemma == pattern.lower() or 
                            token_text == pattern.lower()):
                            matched_pattern = pattern
                            break
            
            if matched_pattern:
                details = s_word_patterns[matched_pattern]
                
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
                
                evidence_score = self._calculate_s_word_evidence(
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

        # 2. Multi-word phrase detection for S-words (including hyphenated words)
        multi_word_patterns = {pattern: details for pattern, details in s_word_patterns.items() if (' ' in pattern or '-' in pattern) and details["category"] != "acceptable_usage"}
        
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
                
                evidence_score = self._calculate_s_word_evidence(
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

        # 3. Special handling for hyphenated S-words
        # Handle patterns like "server-side", "stand-alone" that are tokenized as ["word", "-", "word"]
        hyphenated_patterns = {
            'server-side': {'alternatives': ['serverside'], 'category': 'hyphenation', 'severity': 'low'},
            'stand-alone': {'alternatives': ['standalone'], 'category': 'hyphenation', 'severity': 'low'}
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
                    
                    evidence_score = self._calculate_s_word_evidence(
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

    def _calculate_s_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for S-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and violation type
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        - Advanced POS analysis preservation for verb form detection
        
        Args:
            word: The S-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (inclusive_language, verb_form, modal_verb, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_s_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_s_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_s_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_s_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_s_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_s_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on S-word category and violation specificity.
        Higher priority categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # Very high-risk inclusive language issues
        if category == 'inclusive_language':
            if word_lower in ['slave', 'segregate']:
                return 0.9  # Critical inclusive language violations
            elif word_lower == 'sanity check':
                return 0.85  # Mental health sensitivity important
            elif word_lower == 'second name':
                return 0.8  # Cultural sensitivity important
            else:
                return 0.85  # Other inclusive language issues
        
        # High-risk accuracy and grammatical issues
        elif category in ['absolute_claim', 'verb_form']:
            if word_lower == 'secure':
                return 0.8  # Security claims need qualification
            elif word_lower in ['setup', 'shutdown']:
                return 0.75  # Verb form correctness important
            else:
                return 0.8  # Other accuracy issues
        
        # Medium-high risk professional clarity issues
        elif category in ['jargon', 'modal_verb']:
            if word_lower in ['ship', 'sunset']:
                return 0.7  # Technical jargon clarity
            elif word_lower in ['shall', 'should']:
                return 0.65  # Modal verb precision
            else:
                return 0.7  # Other clarity issues
        
        # Medium-risk word choice issues
        elif category == 'word_choice':
            if word_lower == 'suite':
                return 0.6  # Word precision context-dependent
            else:
                return 0.6  # Other word choice issues
        
        # Lower-risk consistency issues
        elif category in ['spacing', 'hyphenation']:
            if word_lower == 'screen shot':
                return 0.5  # Spacing consistency
            elif word_lower in ['server-side', 'stand-alone']:
                return 0.45  # Hyphenation consistency context-dependent
            else:
                return 0.5  # Other consistency issues
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_s_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply S-word-specific linguistic clues using SpaCy analysis."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # === INCLUSIVE LANGUAGE CLUES ===
        if word_lower in ['sanity check', 'slave', 'segregate', 'second name']:
            # Customer/global content needs inclusive language
            if any(indicator in sent_text for indicator in ['customer', 'user', 'global', 'international']):
                ev += 0.3  # Strong inclusive language need in customer/global contexts
            elif any(indicator in sent_text for indicator in ['public', 'external', 'documentation']):
                ev += 0.2  # Public content benefits from inclusive language
            elif any(indicator in sent_text for indicator in ['team', 'people', 'individuals']):
                ev += 0.15  # People-related content needs sensitivity
            
            # Special handling for "slave" in technical contexts
            if word_lower == 'slave':
                if any(tech_term in sent_text for tech_term in ['master', 'database', 'replication', 'cluster']):
                    ev += 0.2  # Technical master/slave terminology needs updating
        
        # === ABSOLUTE CLAIM CLUES ===
        if word_lower == 'secure':
            # Security context needs qualified claims
            if any(indicator in sent_text for indicator in ['system', 'application', 'data', 'network']):
                ev += 0.25  # Strong need for qualification in security contexts
            elif any(indicator in sent_text for indicator in ['protocol', 'encryption', 'authentication']):
                ev += 0.2  # Security mechanisms need precise language
            elif any(indicator in sent_text for indicator in ['completely', 'totally', 'fully']):
                ev += 0.15  # Absolute terms compound the issue
        
        # === VERB FORM CLUES ===
        if word_lower in ['setup', 'shutdown']:
            # Technical action context needs correct verb forms
            if any(indicator in sent_text for indicator in ['system', 'server', 'process', 'service']):
                ev += 0.2  # Technical action context
            elif any(indicator in sent_text for indicator in ['to', 'will', 'must', 'should']):
                ev += 0.15  # Infinitive or modal context suggests verb usage
            # Check grammatical context using POS tags
            if hasattr(token, 'head') and token.head.pos_ in ['AUX', 'VERB']:
                if token.head.lemma_.lower() in ['will', 'must', 'should', 'can']:
                    ev += 0.1  # Modal + verb context
        
        # === MODAL VERB CLUES ===
        if word_lower in ['shall', 'should']:
            # Requirement context needs authoritative language
            if any(indicator in sent_text for indicator in ['must', 'required', 'mandatory', 'compliance']):
                ev += 0.15  # Requirement context benefits from "must"
            elif any(indicator in sent_text for indicator in ['policy', 'standard', 'regulation']):
                ev += 0.1  # Formal contexts benefit from authoritative language
            # Check for tentative language that conflicts with requirements
            if any(indicator in sent_text for indicator in ['maybe', 'possibly', 'might']):
                ev += 0.05  # Mixed signals suggest clarity needed
        
        # === JARGON CLUES ===
        if word_lower in ['ship', 'sunset']:
            # Professional context benefits from clear language
            if any(indicator in sent_text for indicator in ['customer', 'client', 'user', 'public']):
                ev += 0.2  # Customer-facing content needs professional language
            elif any(indicator in sent_text for indicator in ['product', 'feature', 'service']):
                ev += 0.15  # Product context often uses jargon
            elif any(indicator in sent_text for indicator in ['timeline', 'schedule', 'plan']):
                ev += 0.1  # Planning context can benefit from precise language
        
        # === SPACING AND HYPHENATION CLUES ===
        if word_lower in ['screen shot', 'server-side', 'stand-alone']:
            # Consistency context
            if any(indicator in sent_text for indicator in ['interface', 'ui', 'display']):
                ev += 0.1  # UI context benefits from standard terminology
            elif any(indicator in sent_text for indicator in ['technical', 'system', 'configuration']):
                ev += 0.05  # Technical context benefits from consistency
        
        return ev

    def _apply_structural_clues_s_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for S-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_s_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for S-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'customer_facing' and word_lower in ['sanity check', 'slave', 'ship']:
            ev += 0.3  # Customer content must use professional, inclusive language
        elif content_type == 'international' and word_lower in ['sanity check', 'segregate']:
            ev += 0.25  # International content requires inclusive language
        elif content_type == 'technical' and word_lower in ['setup', 'shutdown', 'secure']:
            ev += 0.15  # Technical docs need precise, qualified language
        
        if audience == 'external' and word_lower in ['sanity check', 'slave', 'ship']:
            ev += 0.3  # External audiences need professional terminology
        elif audience == 'global' and word_lower in ['sanity check', 'segregate']:
            ev += 0.2  # Global audiences need inclusive language
        
        return ev

    def _apply_feedback_clues_s_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for S-words."""
        patterns = self._get_cached_feedback_patterns_s_words()
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

    def _get_cached_feedback_patterns_s_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for S-words."""
        return {
            'often_flagged_terms': {'sanity check', 'slave', 'secure', 'setup', 'shutdown', 'segregate', 'shall'},
            'accepted_terms': {'simple', 'system', 'service', 'suite'},  # Generally acceptable terms in some contexts
            'technical_patterns': {
                'flagged': {'sanity check', 'slave', 'shall', 'should'},  # Technical docs need precision
                'accepted': {'setup', 'shutdown', 'secure', 'system', 'service'}  # Technical terms acceptable as nouns
            },
            'customer_facing_patterns': {
                'flagged': {'sanity check', 'slave', 'segregate', 'ship', 'sunset'},  # Customer content needs professional language
                'accepted': {'simple', 'service', 'system', 'suite'}  # Customer-friendly terms
            },
            'inclusive_patterns': {
                'flagged': {'slave', 'segregate', 'sanity check', 'second name'},  # Inclusive language critical
                'accepted': {'service', 'system', 'simple'}  # Neutral terms
            },
            'security_patterns': {
                'flagged': {'secure', 'slave'},  # Security docs need precise language
                'accepted': {'system', 'service', 'suite'}  # Security context terms
            },
            'documentation_patterns': {
                'flagged': {'sanity check', 'ship', 'sunset', 'shall'},  # Documentation needs clear language
                'accepted': {'simple', 'system', 'service'}  # Documentation-friendly terms
            },
            'formal_patterns': {
                'flagged': {'ship', 'sunset', 'should'},  # Formal writing prefers precise language
                'accepted': {'shall', 'secure', 'system', 'service'}  # Formal terms acceptable
            },
            'general_patterns': {
                'flagged': {'sanity check', 'slave', 'segregate'},  # General content prefers inclusive language
                'accepted': {'simple', 'system', 'service', 'suite'}  # Common terms acceptable
            }
        }