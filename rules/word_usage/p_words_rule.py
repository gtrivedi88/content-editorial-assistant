"""
Word Usage Rule for words starting with 'P'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class PWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'P'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_p'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for P-word usage violations.
        Computes a nuanced evidence score per occurrence considering linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        
        # Define P-word patterns with evidence categories
        p_word_patterns = {
            "pain point": {"alternatives": ["challenge", "issue", "problem"], "category": "jargon", "severity": "medium"},
            "pane": {"alternatives": ["pane (framed section)", "panel", "window"], "category": "context_specific", "severity": "low"},
            "partner": {"alternatives": ["IBM Business Partner"], "category": "brand_specific", "severity": "medium"},
            "path name": {"alternatives": ["pathname"], "category": "spacing", "severity": "low"},
            "PDF": {"alternatives": ["PDF file", "PDF document"], "category": "noun_usage", "severity": "medium"},
            "per": {"alternatives": ["according to"], "category": "preposition_choice", "severity": "low"},
            "perform": {"alternatives": ["run", "install", "execute"], "category": "action_clarity", "severity": "low"},
            "please": {"alternatives": ["(remove)", "ensure"], "category": "cultural_sensitivity", "severity": "medium"},
            "plug-in": {"alternatives": ["plugin"], "category": "hyphenation", "severity": "low"},
            "pop up": {"alternatives": ["pop-up"], "category": "hyphenation", "severity": "low"},
            "power up": {"alternatives": ["power on", "turn on"], "category": "action_clarity", "severity": "medium"},
            "practise": {"alternatives": ["practice"], "category": "spelling", "severity": "low"},
            "preinstall": {"alternatives": ["preinstall"], "category": "acceptable_usage", "severity": "none"},
            "prior to": {"alternatives": ["before"], "category": "redundant_phrase", "severity": "low"},
            "program product": {"alternatives": ["licensed program"], "category": "technical_precision", "severity": "medium"},
            "punch": {"alternatives": ["press", "type"], "category": "action_clarity", "severity": "high"},
            "press": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
            "process": {"alternatives": [], "category": "acceptable_usage", "severity": "none"},
        }

        # Evidence-based analysis for P-words using lemma-based matching and phrase detection
        
        # 1. Single-word matches
        for token in doc:
            # Check if token lemma matches any of our target words
            token_lemma = token.lemma_.lower()
            token_text = token.text.lower()
            matched_pattern = None
            
            # Check single words (excluding multi-word patterns) - case-insensitive
            for pattern in p_word_patterns:
                if ' ' not in pattern:  # Single word pattern
                    if (token_lemma == pattern.lower() or 
                        token_text == pattern.lower() or
                        token.text == pattern):  # Handle case-sensitive patterns like "PDF"
                        matched_pattern = pattern
                        break
            
            if matched_pattern:
                details = p_word_patterns[matched_pattern]
                
                # Skip acceptable usage patterns
                if details["category"] == "acceptable_usage":
                    continue
                
                # Apply surgical guards with entity override
                if self._apply_surgical_zero_false_positive_guards_word_usage(token, context or {}):
                    # Special override for legitimate P-words that might be tagged as entities
                    # but ONLY if it's entity filtering (not quotes, URLs, code, etc.)
                    if (token.ent_type_ and 
                        self._is_target_p_word_override(token, matched_pattern) and
                        self._is_entity_only_filtering(token, context or {})):
                        pass  # Continue with analysis despite guard
                    else:
                        continue  # Respect guard (quotes, URLs, code, etc.)
                
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                evidence_score = self._calculate_p_word_evidence(
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

        # 2. Multi-word phrase detection for P-words
        multi_word_patterns = {pattern: details for pattern, details in p_word_patterns.items() if ' ' in pattern and details["category"] != "acceptable_usage"}
        
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
                
                evidence_score = self._calculate_p_word_evidence(
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

        # 3. Special handling for hyphenated patterns
        hyphenated_patterns = ['plug-in']  # 'pop up' handled by phrase detection
        
        for pattern in hyphenated_patterns:
            if pattern in p_word_patterns:
                details = p_word_patterns[pattern]
                
                # Find hyphenated versions in text
                for i in range(len(doc)):
                    tokens_found = []
                    current_pos = i
                    
                    # Check for pattern like "plug", "-", "in"
                    if pattern == 'plug-in' and current_pos + 2 < len(doc):
                        if (doc[current_pos].text.lower() == 'plug' and
                            doc[current_pos + 1].text == '-' and
                            doc[current_pos + 2].text.lower() == 'in'):
                            tokens_found = [doc[current_pos], doc[current_pos + 1], doc[current_pos + 2]]
                    

                    
                    if tokens_found:
                        # Apply surgical guards on the first token
                        if self._apply_surgical_zero_false_positive_guards_word_usage(tokens_found[0], context or {}):
                            continue
                        
                        sent = tokens_found[0].sent
                        sentence_index = 0
                        for j, s in enumerate(doc.sents):
                            if s == sent:
                                sentence_index = j
                                break
                        
                        evidence_score = self._calculate_p_word_evidence(
                            pattern, tokens_found[0], sent, text, context or {}, details["category"]
                        )
                        
                        if evidence_score > 0.1:
                            start_char = tokens_found[0].idx
                            end_char = tokens_found[-1].idx + len(tokens_found[-1].text)
                            flagged_text = ''.join([t.text_with_ws for t in tokens_found]).strip()
                            
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=sentence_index,
                                message=self._generate_evidence_aware_word_usage_message(pattern, evidence_score, details["category"]),
                                suggestions=self._generate_evidence_aware_word_usage_suggestions(pattern, details["alternatives"], evidence_score, context or {}, details["category"]),
                                severity=details["severity"] if evidence_score < 0.7 else 'high',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=(start_char, end_char),
                                flagged_text=flagged_text
                            ))
        
        return errors

    def _calculate_p_word_evidence(self, word: str, token, sentence, text: str, context: Dict[str, Any], category: str) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for P-word usage violations.
        
        Implements rule-specific evidence calculation with:
        - Dynamic base evidence scoring based on word category and violation type
        - Context-aware adjustments for different writing domains
        - Linguistic, structural, semantic, and feedback pattern analysis
        
        Args:
            word: The P-word being analyzed
            token: SpaCy token object
            sentence: Sentence containing the word
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            category: Word category (action_clarity, cultural_sensitivity, jargon, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_p_word_evidence_score(word, category, sentence, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this word
        
        # === STEP 1: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_p_words(evidence_score, word, token, sentence)
        
        # === STEP 2: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_p_words(evidence_score, context)
        
        # === STEP 3: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_p_words(evidence_score, word, text, context)
        
        # === STEP 4: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_p_words(evidence_score, word, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _get_base_p_word_evidence_score(self, word: str, category: str, sentence, context: Dict[str, Any]) -> float:
        """
        Set dynamic base evidence score based on P-word category and violation specificity.
        Higher priority categories get higher base scores for surgical precision.
        """
        word_lower = word.lower()
        
        # Very high-risk action and clarity issues
        if category == 'action_clarity':
            if word_lower == 'punch':
                return 0.85  # Action clarity critical for user instructions
            elif word_lower in ['power up', 'perform']:
                return 0.75  # Other action clarity issues
            else:
                return 0.8  # Default action clarity
        
        # High-risk professional and cultural issues
        elif category in ['jargon', 'cultural_sensitivity', 'technical_precision']:
            if word_lower == 'please':
                return 0.8  # Cultural sensitivity critical for global content
            elif word_lower == 'pain point':
                return 0.75  # Jargon clarity for professional content
            elif word_lower == 'program product':
                return 0.7  # Technical precision context-dependent
            else:
                return 0.75  # Other professional issues
        
        # Medium-high risk consistency and precision issues
        elif category in ['brand_specific', 'noun_usage']:
            if word_lower == 'pdf':
                return 0.7  # Noun usage precision
            elif word_lower == 'partner':
                return 0.65  # Brand-specific context-dependent
            else:
                return 0.7  # Other precision issues
        
        # Medium-risk consistency issues
        elif category in ['spacing', 'hyphenation', 'spelling', 'redundant_phrase', 'preposition_choice']:
            if word_lower in ['prior to', 'path name']:
                return 0.55  # Redundancy and spacing consistency
            elif word_lower in ['plug-in', 'pop up']:
                return 0.5  # Hyphenation consistency
            elif word_lower in ['practise', 'per']:
                return 0.45  # Lower priority spelling and preposition
            else:
                return 0.5  # Other consistency issues
        
        # Lower risk context-dependent issues
        elif category == 'context_specific':
            if word_lower == 'pane':
                return 0.4  # Context-dependent disambiguation
            else:
                return 0.4  # Other context issues
        
        return 0.6  # Default moderate evidence for other patterns

    def _apply_linguistic_clues_p_words(self, ev: float, word: str, token, sentence) -> float:
        """Apply P-word-specific linguistic clues using SpaCy analysis."""
        sent_text = sentence.text.lower()
        word_lower = word.lower()
        
        # === ACTION CLARITY CLUES ===
        if word_lower == 'punch':
            # Action contexts need precise language
            if any(indicator in sent_text for indicator in ['key', 'button', 'keyboard', 'enter']):
                ev += 0.2  # Action context needs precise language
            elif any(indicator in sent_text for indicator in ['type', 'press', 'click', 'select']):
                ev += 0.15  # Input context benefits from clarity
        
        if word_lower in ['power up', 'perform']:
            # Technical action contexts
            if any(indicator in sent_text for indicator in ['system', 'device', 'machine', 'computer']):
                ev += 0.15  # Technical context needs specific actions
            elif any(indicator in sent_text for indicator in ['operation', 'task', 'procedure', 'function']):
                ev += 0.1  # Operational context benefits from precision
        
        # === CULTURAL SENSITIVITY CLUES ===
        if word_lower == 'please':
            # International and global contexts avoid cultural assumptions
            if any(indicator in sent_text for indicator in ['international', 'global', 'documentation', 'manual']):
                ev += 0.2  # International content avoids cultural assumptions
            elif any(indicator in sent_text for indicator in ['instruction', 'procedure', 'step', 'guide']):
                ev += 0.15  # Instructional context benefits from direct language
        
        # === JARGON CLUES ===
        if word_lower == 'pain point':
            # Business and professional contexts
            if any(indicator in sent_text for indicator in ['business', 'customer', 'solution', 'strategy']):
                ev += 0.15  # Business context benefits from professional language
            elif any(indicator in sent_text for indicator in ['problem', 'issue', 'challenge', 'difficulty']):
                ev += 0.1  # Problem context benefits from clear terminology
        
        # === NOUN USAGE CLUES ===
        if word_lower == 'pdf':
            # File and document contexts
            if any(indicator in sent_text for indicator in ['document', 'file', 'download', 'format']):
                ev += 0.15  # File context needs precise noun usage
            elif any(indicator in sent_text for indicator in ['open', 'view', 'read', 'save']):
                ev += 0.1  # Document action context benefits from clarity
        
        # === BRAND SPECIFIC CLUES ===
        if word_lower == 'partner':
            # Business relationship contexts
            if any(indicator in sent_text for indicator in ['business', 'company', 'vendor', 'supplier']):
                ev += 0.1  # Business context benefits from specific terminology
        
        # === HYPHENATION CLUES ===
        if word_lower in ['plug-in', 'pop up']:
            # Technical interface contexts
            if any(indicator in sent_text for indicator in ['software', 'application', 'browser', 'interface']):
                ev += 0.1  # Technical contexts prefer standard forms
        
        # === REDUNDANCY CLUES ===
        if word_lower == 'prior to':
            # Temporal contexts
            if any(indicator in sent_text for indicator in ['before', 'after', 'during', 'when']):
                ev += 0.1  # Temporal context benefits from concise language
        
        # === SPACING CLUES ===
        if word_lower == 'path name':
            # Technical file system contexts
            if any(indicator in sent_text for indicator in ['file', 'directory', 'folder', 'system']):
                ev += 0.1  # File system context prefers compound forms
        
        return ev

    def _apply_structural_clues_p_words(self, ev: float, context: Dict[str, Any]) -> float:
        """Apply structural context clues for P-words."""
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['step', 'procedure']:
            ev += 0.1
        elif block_type == 'heading':
            ev -= 0.1
        return ev

    def _apply_semantic_clues_p_words(self, ev: float, word: str, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for P-words."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        word_lower = word.lower()
        
        if content_type == 'tutorial' and word_lower in ['punch', 'please', 'perform']:
            ev += 0.15  # Tutorials need clear, direct instructions
        elif content_type == 'customer_facing' and word_lower in ['pain point', 'please']:
            ev += 0.2  # Customer content needs professional, inclusive language
        elif content_type == 'international' and word_lower == 'please':
            ev += 0.25  # International content avoids cultural assumptions
        elif content_type == 'technical' and word_lower in ['program product', 'perform']:
            ev += 0.1  # Technical docs need precise terminology
        
        if audience == 'global' and word_lower in ['please', 'pain point']:
            ev += 0.15  # Global audiences need inclusive, professional language
        elif audience == 'external' and word_lower in ['partner', 'please']:
            ev += 0.2  # External audiences need specific, inclusive language
        
        return ev

    def _apply_feedback_clues_p_words(self, ev: float, word: str, context: Dict[str, Any]) -> float:
        """Apply feedback pattern clues for P-words."""
        patterns = self._get_cached_feedback_patterns_p_words()
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

    def _is_target_p_word_override(self, token, matched_pattern: str) -> bool:
        """
        Override surgical guards for legitimate P-words that might be incorrectly tagged as entities.
        Returns True if the word should be flagged despite entity detection.
        """
        word_lower = matched_pattern.lower()
        
        # Words that should be flagged even if tagged as entities
        target_overrides = {
            'pdf', 'partner', 'please', 'perform', 'punch', 'per', 'practise'
        }
        
        return word_lower in target_overrides

    def _is_entity_only_filtering(self, token, context: Dict[str, Any]) -> bool:
        """
        Check if the surgical guard is filtering ONLY because of entity detection,
        not because of other valid reasons like quotes, URLs, or code.
        Returns True if it's entity-only filtering (and override should apply).
        """
        # Quick check for non-entity filtering reasons
        # If any of these apply, it's not entity-only filtering
        
        # Check for quoted content (simplified check for quotes around token)
        sentence_text = token.sent.text
        token_start = token.idx - token.sent.start_char
        
        # Look for quotes before and after the token position in the sentence
        before_token = sentence_text[:token_start]
        after_token = sentence_text[token_start + len(token.text):]
        
        # Check if there are quotes immediately around the token
        if (before_token.rstrip().endswith('"') and '"' in after_token) or \
           (before_token.rstrip().endswith("'") and "'" in after_token):
            return False  # Quoted content, not entity-only filtering
        
        # Check for code blocks
        if context.get('block_type') in ['code_block', 'inline_code', 'literal_block']:
            return False  # Code context, not entity-only filtering
        
        # Check for URLs (simplified)
        if 'http' in sentence_text.lower() or 'www.' in sentence_text.lower():
            return False  # URL context, not entity-only filtering
        
        # If we get here and the token has an entity type, it's likely entity-only filtering
        return bool(token.ent_type_)

    def _get_cached_feedback_patterns_p_words(self) -> Dict[str, Any]:
        """Get cached feedback patterns for P-words."""
        return {
            'often_flagged_terms': {'punch', 'please', 'pain point', 'pdf', 'prior to', 'power up'},
            'accepted_terms': {'preinstall', 'press', 'process'},  # Correct forms
            'technical_patterns': {
                'flagged': {'punch', 'please', 'pain point', 'power up', 'per'},  # Technical docs need precision
                'accepted': {'pdf', 'plug-in', 'process', 'perform', 'preinstall'}  # Technical terms acceptable
            },
            'customer_facing_patterns': {
                'flagged': {'punch', 'please', 'pain point', 'prior to', 'per'},  # Customer content needs clarity
                'accepted': {'pdf', 'pop up', 'press', 'process'}  # Customer-friendly terms
            },
            'tutorial_patterns': {
                'flagged': {'punch', 'please', 'pain point', 'power up'},  # Tutorials need clear instructions
                'accepted': {'press', 'process', 'pdf', 'perform'}  # Tutorial-friendly terms
            },
            'international_patterns': {
                'flagged': {'please', 'pain point', 'punch', 'per'},  # International content needs inclusive language
                'accepted': {'pdf', 'process', 'press', 'perform'}  # Universal terms
            },
            'procedure_patterns': {
                'flagged': {'punch', 'please', 'power up', 'prior to'},  # Procedures need clear language
                'accepted': {'press', 'perform', 'pdf', 'process'}  # Procedural terms acceptable
            },
            'formal_patterns': {
                'flagged': {'punch', 'pain point', 'please', 'pop up'},  # Formal writing prefers professional language
                'accepted': {'perform', 'pdf', 'prior to', 'per'}  # Formal terms acceptable
            },
            'general_patterns': {
                'flagged': {'punch', 'please', 'pain point'},  # General content prefers clear language
                'accepted': {'press', 'process', 'pdf', 'perform', 'preinstall'}  # Common terms acceptable
            }
        }