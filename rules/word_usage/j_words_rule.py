"""
Word Usage Rule for words starting with 'J'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class JWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'J'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_j'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for J-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define J-word patterns with evidence categories
        j_word_patterns = {
            "jar": {"alternatives": ["compress", "archive"], "category": "verb_misuse", "severity": "medium"},
            "javabeans": {"alternatives": ["JavaBeans (correct capitalization)"], "category": "capitalization", "severity": "low"},
            "javadoc": {"alternatives": ["Javadoc (correct capitalization)"], "category": "capitalization", "severity": "low"},
            "job log": {"alternatives": ["joblog"], "category": "spacing", "severity": "low"},
            "job stream": {"alternatives": ["jobstream"], "category": "spacing", "severity": "low"},
            "judgement": {"alternatives": ["judgment"], "category": "spelling", "severity": "low"},
            "just": {"alternatives": ["only", "simply"], "category": "word_choice", "severity": "low"},
        }

        # Evidence-based analysis for J-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches using lemma-based approach
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Check exact lemma matches first (single words)
            # Skip capitalization-sensitive words for now
            if (token_lemma in j_word_patterns and ' ' not in token_lemma and 
                token_lemma not in ['javabeans', 'javadoc']):
                matched_pattern = token_lemma
            # Also check for exact text matches (single words)  
            elif (token_text in j_word_patterns and ' ' not in token_text and
                  token_text not in ['javabeans', 'javadoc']):
                matched_pattern = token_text
            
            # Special case handling for capitalization patterns - ONLY flag incorrect ones
            if token_text == 'javabeans' and token.text != 'JavaBeans':
                matched_pattern = 'javabeans'  # Flag incorrect capitalization
            elif token_text == 'javadoc' and token.text != 'Javadoc':
                matched_pattern = 'javadoc'  # Flag incorrect capitalization
            
            if matched_pattern:
                details = j_word_patterns[matched_pattern]
                
                # Apply surgical guards
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue
                
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_j_word_evidence(
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

        # 2. Multi-word phrase detection for J-words
        multi_word_patterns = {pattern: details for pattern, details in j_word_patterns.items() if ' ' in pattern}
        
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
                
                evidence_score = self._calculate_j_word_evidence(
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

    def _calculate_j_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for J-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and violation type
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        
        Args:
            word: The J-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (verb_misuse, capitalization, spelling, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_j_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_j_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_j_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_j_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_j_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_j_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on J-word category and violation specificity.
        Higher priority categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # High-risk verb misuse in technical contexts
        if category == 'verb_misuse':
            return 0.8  # "jar" as verb - needs specific action verbs
        
        # Medium-high risk spelling and technical terminology
        elif category == 'spelling':
            return 0.7  # "judgement" vs "judgment" - standard spelling preferred
        
        # Medium risk capitalization issues
        elif category == 'capitalization':
            if word_lower in ['javabeans', 'javadoc']:
                return 0.65  # Technical terms need correct capitalization
            else:
                return 0.6  # Other capitalization issues
        
        # Medium risk spacing issues
        elif category == 'spacing':
            return 0.55  # "job log", "job stream" - format consistency
        
        # Lower risk word choice issues
        elif category == 'word_choice':
            if word_lower == 'just':
                return 0.4  # "just" often acceptable but can be improved
            else:
                return 0.5  # Other word choice issues
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_j_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply J-word-specific linguistic clues using SpaCy analysis."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # === VERB MISUSE CLUES ===
        if word_lower == 'jar':
            # Check if used as verb in technical file contexts
            if token.pos_ == 'VERB' and any(indicator in sent_text for indicator in ['file', 'compress', 'archive', 'package', 'create']):
                ev += 0.2  # Technical context needs precise action verbs
            elif any(indicator in sent_text for indicator in ['executable', 'library', 'deployment']):
                ev += 0.15  # Software context suggests verb misuse
        
        # === WORD CHOICE CLUES ===
        if word_lower == 'just':
            # Check for redundancy patterns
            if any(indicator in sent_text for indicator in ['only', 'simply', 'merely', 'exactly']):
                ev += 0.15  # Redundancy context suggests replacement
            # Check if used for emphasis vs precision
            elif token.dep_ in ['advmod'] and any(indicator in sent_text for indicator in ['need', 'have to', 'must']):
                ev += 0.1  # Emphasis usage often replaceable with precision
        
        # === CAPITALIZATION CLUES ===
        if word_lower in ['javabeans', 'javadoc']:
            # Technical programming context increases evidence
            if any(indicator in sent_text for indicator in ['java', 'programming', 'development', 'api', 'class', 'method']):
                ev += 0.15  # Technical context demands correct capitalization
            # Check if it's clearly a technical term vs general word
            if token.pos_ in ['NOUN', 'PROPN']:
                ev += 0.1  # Likely a technical term needing proper capitalization
        
        # === SPELLING CLUES ===
        if word_lower == 'judgement':
            # Formal writing context increases evidence for standard spelling
            if any(indicator in sent_text for indicator in ['decision', 'ruling', 'verdict', 'assessment']):
                ev += 0.1  # Legal/formal context prefers standard spelling
        
        # === SPACING CLUES ===
        if word_lower in ['job log', 'job stream']:
            # Technical system context suggests compound terms
            if any(indicator in sent_text for indicator in ['system', 'process', 'batch', 'schedule', 'queue']):
                ev += 0.1  # System context suggests compound formatting
        
        return ev

    def _apply_structural_clues_j_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for J-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_j_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for J-words."""
        content_type = context.get('content_type', 'general')
        word_lower = word.lower()
        
        if content_type == 'technical' and word_lower in ['jar', 'javabeans', 'javadoc']:
            ev += 0.15  # Technical docs need precise terminology
        elif content_type == 'tutorial' and word_lower == 'just':
            ev -= 0.1  # Tutorials allow more conversational language
        elif content_type == 'formal' and word_lower == 'judgement':
            ev += 0.1  # Formal writing prefers standard spelling
        
        return ev

    def _apply_feedback_clues_j_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for J-words."""
        patterns = self._get_cached_feedback_patterns_j_words()
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

    def _get_cached_feedback_patterns_j_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for J-words."""
        return {
            'often_flagged_terms': {'jar', 'judgement', 'javabeans', 'javadoc'},
            'accepted_terms': {'just'},  # Often acceptable depending on context
            'technical_patterns': {
                'flagged': {'jar', 'javabeans', 'javadoc', 'job log', 'job stream'},  # Technical docs need precision
                'accepted': set()
            },
            'formal_patterns': {
                'flagged': {'judgement', 'just'},  # Formal writing prefers standard forms
                'accepted': set()
            },
            'tutorial_patterns': {
                'flagged': {'jar'},  # Tutorials need clear action verbs
                'accepted': {'just', 'javabeans', 'javadoc'}  # Conversational and technical terms acceptable in tutorials
            },
            'procedure_patterns': {
                'flagged': {'jar', 'just', 'job log', 'job stream'},  # Procedures need precise language
                'accepted': set()
            },
            'general_patterns': {
                'flagged': {'jar', 'judgement'},  # General content prefers standard terms
                'accepted': {'just'}  # "just" often acceptable in general content
            }
        }