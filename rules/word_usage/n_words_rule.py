"""
Word Usage Rule for words starting with 'N'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class NWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'N'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_n'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for N-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define N-word patterns with evidence categories
        n_word_patterns = {
            "name space": {"alternatives": ["namespace"], "category": "spacing", "severity": "low"},
            "native": {"alternatives": ["local", "basic", "default"], "category": "vague_language", "severity": "medium"},
            "need to": {"alternatives": ["must"], "category": "action_clarity", "severity": "medium"},
            "new": {"alternatives": ["latest", "current"], "category": "temporal_language", "severity": "low"},
            "news feed": {"alternatives": ["newsfeed"], "category": "spacing", "severity": "low"},
            "no.": {"alternatives": ["number"], "category": "abbreviation", "severity": "medium"},
            "non-English": {"alternatives": ["in languages other than English"], "category": "inclusive_language", "severity": "medium"},
            "notebook": {"alternatives": ["notebook (UI)", "laptop (computer)"], "category": "context_specific", "severity": "low"},
            "near real time": {"alternatives": ["near real-time"], "category": "hyphenation", "severity": "low"},
            "node": {"alternatives": ["system", "device"], "category": "technical_clarity", "severity": "low"},
        }

        # Evidence-based analysis for N-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Check single words (excluding multi-word patterns)
            if (token_lemma in n_word_patterns and ' ' not in token_lemma):
                matched_pattern = token_lemma
            elif (token_text in n_word_patterns and ' ' not in token_text):
                matched_pattern = token_text
            
            if matched_pattern:
                details = n_word_patterns[matched_pattern]
                
                # Apply surgical guards
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    continue
                
                # Additional guard for organization entities (companies)
                if token.ent_type_ == 'ORG':
                    continue
                
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_n_word_evidence(
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

        # 2. Multi-word phrase detection for N-words
        multi_word_patterns = {pattern: details for pattern, details in n_word_patterns.items() if ' ' in pattern}
        
        if multi_word_patterns:
            phrase_matches = self._find_multi_word_phrases_with_lemma(doc, list(multi_word_patterns.keys()), case_sensitive=False)
            
            for match in phrase_matches:
                pattern = match['phrase']
                details = multi_word_patterns[pattern]
                
                # Apply surgical guards on the first token
                if self._apply_surgical_zero_false_positive_guards_word_usage(match['start_token'], context or {}):
                    continue
                
                # Additional guard for organization entities (companies) in phrases
                if any(token.ent_type_ == 'ORG' for token in [match['start_token']] + 
                      [match['start_token'].doc[i] for i in range(match['start_token'].i + 1, 
                                                                 min(match['start_token'].i + 5, len(match['start_token'].doc)))]):
                    continue
                
                sent = match['start_token'].sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_n_word_evidence(
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

        # 3. Special handling for "no." abbreviation with period detection
        for i in range(len(doc) - 1):
            if (doc[i].text.lower() == "no" and 
                i + 1 < len(doc) and 
                doc[i + 1].text == "."):
                
                if "no." in n_word_patterns:
                    details = n_word_patterns["no."]
                    
                    # Apply surgical guards on the first token
                    if self._apply_surgical_zero_false_positive_guards_word_usage(doc[i], context or {}):
                        continue
                    
                    sent = doc[i].sent
                    sentence_index = 0
                    for j, s in enumerate(doc.sents):
                        if s == sent:
                            sentence_index = j
                            break
                    
                    evidence_score = self._calculate_n_word_evidence(
                        "no.", doc[i], sent, text, context or {}, details["category"]
                    )
                    
                    if evidence_score > 0.1:
                        start_char = doc[i].idx
                        end_char = doc[i + 1].idx + len(doc[i + 1].text)
                        flagged_text = doc[i].text + "."
                        
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message("no.", evidence_score, details["category"]),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions("no.", details["alternatives"], evidence_score, context or {}, details["category"]),
                            severity=details["severity"] if evidence_score < 0.7 else 'high',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(start_char, end_char),
                            flagged_text=flagged_text
                        ))

        # 4. Special handling for "non-English" hyphenated pattern
        for i in range(len(doc) - 2):
            if (doc[i].text.lower() == "non" and 
                i + 1 < len(doc) and 
                doc[i + 1].text == "-" and 
                i + 2 < len(doc) and 
                doc[i + 2].text.lower() == "english"):
                
                if "non-English" in n_word_patterns:
                    details = n_word_patterns["non-English"]
                    
                    # Apply surgical guards on the first token
                    if self._apply_surgical_zero_false_positive_guards_word_usage(doc[i], context or {}):
                        continue
                    
                    sent = doc[i].sent
                    sentence_index = 0
                    for j, s in enumerate(doc.sents):
                        if s == sent:
                            sentence_index = j
                            break
                    
                    evidence_score = self._calculate_n_word_evidence(
                        "non-English", doc[i], sent, text, context or {}, details["category"]
                    )
                    
                    if evidence_score > 0.1:
                        start_char = doc[i].idx
                        end_char = doc[i + 2].idx + len(doc[i + 2].text)
                        flagged_text = doc[i].text + "-" + doc[i + 2].text
                        
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=sentence_index,
                            message=self._generate_evidence_aware_word_usage_message("non-English", evidence_score, details["category"]),
                            suggestions=self._generate_evidence_aware_word_usage_suggestions("non-English", details["alternatives"], evidence_score, context or {}, details["category"]),
                            severity=details["severity"] if evidence_score < 0.7 else 'high',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(start_char, end_char),
                            flagged_text=flagged_text
                        ))
        
        return errors

    def _calculate_n_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for N-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and violation type
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        
        Args:
            word: The N-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (vague_language, action_clarity, spacing, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_n_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_n_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_n_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_n_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_n_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_n_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on N-word category and violation specificity.
        Higher priority categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # Very high-risk clarity and action issues
        if category in ['vague_language', 'action_clarity']:
            if word_lower == 'need to':
                return 0.8  # Action clarity critical for instructions
            elif word_lower == 'native':
                return 0.75  # Vague technical terminology
            else:
                return 0.75  # Other clarity issues
        
        # High-risk communication and inclusive language
        elif category in ['abbreviation', 'inclusive_language']:
            if word_lower == 'non-english':
                return 0.8  # Inclusive language critical for global content
            elif word_lower == 'no.':
                return 0.7  # Abbreviation clarity for international audiences
            else:
                return 0.7  # Other communication issues
        
        # Medium-risk technical and formatting issues
        elif category in ['technical_clarity', 'hyphenation']:
            if word_lower == 'node':
                return 0.6  # Technical precision context-dependent
            elif word_lower == 'near real time':
                return 0.55  # Hyphenation consistency
            else:
                return 0.6  # Other technical issues
        
        # Lower risk consistency and contextual issues
        elif category in ['spacing', 'temporal_language', 'context_specific']:
            if word_lower in ['name space', 'news feed']:
                return 0.5  # Spacing consistency
            elif word_lower == 'new':
                return 0.45  # Temporal language context-dependent
            elif word_lower == 'notebook':
                return 0.4  # Context-specific disambiguation
            else:
                return 0.5  # Other consistency issues
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_n_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply N-word-specific linguistic clues using SpaCy analysis."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # === ACTION CLARITY CLUES ===
        if word_lower == 'need to':
            # Instruction and procedural contexts increase importance
            if any(indicator in sent_text for indicator in ['must', 'required', 'mandatory', 'should']):
                ev += 0.2  # Instruction context needs authoritative language
            elif any(indicator in sent_text for indicator in ['procedure', 'step', 'instruction', 'follow']):
                ev += 0.15  # Procedural context benefits from clear directives
        
        # === VAGUE LANGUAGE CLUES ===
        if word_lower == 'native':
            # Technical contexts need specific terminology
            if any(indicator in sent_text for indicator in ['application', 'feature', 'support', 'functionality']):
                ev += 0.15  # Technical context needs specific terminology
            elif any(indicator in sent_text for indicator in ['implementation', 'default', 'built-in']):
                ev += 0.1  # Implementation context benefits from precision
        
        # === INCLUSIVE LANGUAGE CLUES ===
        if word_lower == 'non-english':
            # Global and international contexts increase importance
            if any(indicator in sent_text for indicator in ['international', 'global', 'translation', 'localization']):
                ev += 0.2  # Global context needs inclusive language
            elif any(indicator in sent_text for indicator in ['language', 'locale', 'region', 'country']):
                ev += 0.15  # Language-specific context especially important
        
        # === ABBREVIATION CLUES ===
        if word_lower == 'no.':
            # Translation and international contexts avoid abbreviations
            if any(indicator in sent_text for indicator in ['translation', 'international', 'localization', 'global']):
                ev += 0.15  # Translation context avoids problematic abbreviations
            elif any(indicator in sent_text for indicator in ['number', 'count', 'reference', 'identifier']):
                ev += 0.1  # Numeric context benefits from clarity
        
        # === TEMPORAL LANGUAGE CLUES ===
        if word_lower == 'new':
            # Version and release contexts
            if any(indicator in sent_text for indicator in ['version', 'release', 'update', 'latest']):
                ev += 0.1  # Version context benefits from specific terminology
        
        # === TECHNICAL CLARITY CLUES ===
        if word_lower == 'node':
            # Network and system contexts
            if any(indicator in sent_text for indicator in ['network', 'cluster', 'distributed', 'architecture']):
                ev += 0.1  # Network context benefits from specificity
        
        # === SPACING AND FORMATTING CLUES ===
        if word_lower in ['name space', 'news feed']:
            # Technical documentation contexts
            if any(indicator in sent_text for indicator in ['code', 'programming', 'api', 'system']):
                ev += 0.1  # Technical contexts prefer compound forms
        
        if word_lower == 'near real time':
            # Performance and system contexts
            if any(indicator in sent_text for indicator in ['performance', 'latency', 'processing', 'data']):
                ev += 0.1  # Performance contexts prefer hyphenated form
        
        # === CONTEXT-SPECIFIC CLUES ===
        if word_lower == 'notebook':
            # Ambiguous contexts need disambiguation
            if any(indicator in sent_text for indicator in ['computer', 'laptop', 'interface', 'application']):
                ev += 0.1  # Disambiguation important for clarity
        
        return ev

    def _apply_structural_clues_n_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for N-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_n_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for N-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'tutorial' and word_lower == 'need to':
            ev += 0.15  # Tutorials need clear, authoritative instructions
        elif content_type == 'international' and word_lower in ['non-english', 'no.']:
            ev += 0.2  # International content needs inclusive language
        elif content_type == 'technical' and word_lower in ['native', 'name space']:
            ev += 0.1  # Technical docs need precise terminology
        
        if audience == 'global' and word_lower in ['non-english', 'no.', 'native']:
            ev += 0.15  # Global audiences need inclusive, clear language
        elif audience == 'external' and word_lower == 'non-english':
            ev += 0.2  # External audiences need inclusive terminology
        
        return ev

    def _apply_feedback_clues_n_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for N-words."""
        patterns = self._get_cached_feedback_patterns_n_words()
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

    def _get_cached_feedback_patterns_n_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for N-words."""
        return {
            'often_flagged_terms': {'need to', 'native', 'non-english', 'no.', 'name space', 'news feed'},
            'accepted_terms': set(),  # Context-dependent acceptance
            'technical_patterns': {
                'flagged': {'need to', 'native', 'name space', 'news feed', 'near real time'},  # Technical docs need precision
                'accepted': {'node', 'notebook', 'new'}  # Technical terms sometimes acceptable
            },
            'tutorial_patterns': {
                'flagged': {'need to', 'native', 'new'},  # Tutorials need clear instructions
                'accepted': {'notebook', 'node', 'no.'}  # Tutorial-specific terms
            },
            'international_patterns': {
                'flagged': {'non-english', 'no.', 'native'},  # International content needs inclusive language
                'accepted': {'new', 'node', 'notebook'}  # Technical terms acceptable
            },
            'customer_facing_patterns': {
                'flagged': {'need to', 'native', 'non-english', 'no.'},  # Customer content needs clarity
                'accepted': {'new', 'notebook'}  # Customer-friendly terms
            },
            'procedure_patterns': {
                'flagged': {'need to', 'native', 'new'},  # Procedures need clear language
                'accepted': {'node', 'notebook', 'no.'}  # Procedural terms acceptable
            },
            'formal_patterns': {
                'flagged': {'need to', 'native'},  # Formal writing prefers authoritative language
                'accepted': {'new', 'node', 'notebook', 'no.'}  # Formal terms acceptable
            },
            'general_patterns': {
                'flagged': {'need to', 'native'},  # General content prefers clear language
                'accepted': {'new', 'node', 'notebook', 'name space', 'news feed'}  # Common terms acceptable
            }
        }