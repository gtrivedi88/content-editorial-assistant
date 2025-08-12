"""
Tone Rule (Production-Grade)
Evidence-based professional tone analysis following production standards.
Implements rule-specific evidence calculation for optimal precision and zero false positives.
"""
from typing import List, Dict, Any
from .base_audience_rule import BaseAudienceRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ToneRule(BaseAudienceRule):
    """
    PRODUCTION-GRADE: Checks for violations of professional tone using evidence-based analysis.
    
    Implements rule-specific evidence calculation for:
    - Idioms and business jargon (high specificity violations)
    - Sports metaphors and casual expressions
    - Colloquialisms and slang
    
    Features:
    - Zero false positive guards for quoted text, code blocks
    - Dynamic base evidence scoring based on phrase specificity
    - Evidence-aware messaging and suggestions
    """
    def _get_rule_type(self) -> str:
        return 'tone'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        PRODUCTION-GRADE: Evidence-based analysis for professional tone violations.
        
        Implements the required production pattern:
        1. Find potential issues using rule-specific detection
        2. Calculate evidence using rule-specific _calculate_tone_evidence()
        3. Apply zero false positive guards specific to tone analysis
        4. Use evidence-aware messaging and suggestions
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        doc = nlp(text)
        context = context or {}

        # === STEP 1: Find potential tone issues ===
        potential_issues = self._find_potential_tone_issues(doc, text, context)
        
        # === STEP 2: Process each potential issue with evidence calculation ===
        for issue in potential_issues:
            # Calculate rule-specific evidence score
            evidence_score = self._calculate_tone_evidence(
                issue, doc, text, context
            )
            
            # Only create error if evidence suggests it's worth evaluating
            if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                error = self._create_error(
                    sentence=issue['sentence'],
                    sentence_index=issue['sentence_index'],
                    message=self._generate_evidence_aware_message(issue, evidence_score, "tone"),
                    suggestions=self._generate_evidence_aware_suggestions(issue, evidence_score, context, "tone"),
                    severity='low' if evidence_score < 0.7 else 'medium',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=issue.get('span', [0, 0]),
                    flagged_text=issue.get('phrase', issue.get('text', ''))
                )
                errors.append(error)
        
        return errors
    
    # === RULE-SPECIFIC METHODS ===
    
    def _find_potential_tone_issues(self, doc, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find potential tone issues for evidence assessment.
        Detects idioms, slang, and casual expressions.
        """
        issues = []
        
        # Professional tone violation patterns with specificity levels
        informal_phrases = {
            # Extremely inappropriate phrases (high base evidence)
            "take a dump": 0.95,
            "bit the dust": 0.9,
            
            # Clear business jargon (high base evidence)
            "low-hanging fruit": 0.85,
            "low hanging fruit": 0.85,  # Handle both hyphenated and non-hyphenated versions
            "a slam dunk": 0.85,
            "slam dunk": 0.85,  # Handle both with and without article
            "game changer": 0.85,
            "game-changer": 0.85,  # Handle hyphenated version
            "move the needle": 0.85,
            "leverage": 0.8,  # Add common business term
            
            # Common informal expressions (medium-high base evidence)
            "nail it": 0.8,
            "no-brainer": 0.8,
            "in the ballpark": 0.8,
            "hit the ground running": 0.8,
            
            # Mild colloquialisms (medium base evidence)
            "elephant in the room": 0.75,
            "it's not rocket science": 0.75,
            "full-court press": 0.75,
            "in your wheelhouse": 0.75
        }
        
        for i, sent in enumerate(doc.sents):
            for phrase, base_evidence in informal_phrases.items():
                for match in re.finditer(r'\b' + re.escape(phrase) + r'\b', sent.text, re.IGNORECASE):
                    issues.append({
                        'type': 'tone',
                        'subtype': 'informal_phrase',
                        'phrase': phrase,
                        'text': match.group(0),
                        'sentence': sent.text,
                        'sentence_index': i,
                        'span': [sent.start_char + match.start(), sent.start_char + match.end()],
                        'base_evidence': base_evidence,
                        'sentence_obj': sent,
                        'match_start': match.start(),
                        'match_end': match.end()
                    })
        
        return issues
    
    def _calculate_tone_evidence(self, issue: Dict[str, Any], doc, text: str, context: Dict[str, Any]) -> float:
        """
        PRODUCTION-GRADE: Calculate evidence score (0.0-1.0) for tone violations.
        
        Implements rule-specific evidence calculation with:
        - Zero false positive guards for tone analysis
        - Dynamic base evidence based on phrase specificity
        - Context-aware adjustments for professional communication
        """
        
        # === SURGICAL ZERO FALSE POSITIVE GUARDS FOR TONE ===
        # Apply ultra-precise tone-specific guards that eliminate false positives
        # while preserving ALL legitimate tone violations
        
        sentence_obj = issue.get('sentence_obj')
        if not sentence_obj:
            return 0.0
            
        phrase = issue.get('phrase', issue.get('text', ''))
        
        # === GUARD 1: QUOTED EXAMPLES AND CITATIONS ===
        # Don't flag phrases in direct quotes, examples, or citations
        sent_text = sentence_obj.text
        if self._is_phrase_in_actual_quotes(phrase, sent_text, issue):
            return 0.0  # Quoted examples are not tone violations
            
        # === GUARD 2: INTENTIONAL STYLE CONTEXT ===
        # Don't flag phrases in contexts where informal tone is intentional
        if self._is_intentional_informal_context(sentence_obj, context):
            return 0.0  # Marketing copy, user quotes, etc.
            
        # === GUARD 3: TECHNICAL DOMAIN APPROPRIATENESS ===
        # Don't flag domain-appropriate language in technical contexts
        if self._is_domain_appropriate_phrase(phrase, context):
            return 0.0  # "Game changer" in gaming docs, etc.
            
        # === GUARD 4: PROPER NOUNS AND BRAND NAMES ===
        # Don't flag phrases that are part of proper nouns or brand names
        if self._is_proper_noun_phrase(phrase, sentence_obj):
            return 0.0  # Company names, product names, etc.
            
        # Apply common audience guards (structural, entities, etc.)
        mock_token = type('MockToken', (), {
            'text': phrase, 
            'doc': sentence_obj.doc,
            'sent': sentence_obj,
            'i': sentence_obj.start
        })
        if self._apply_zero_false_positive_guards_audience(mock_token, context):
            return 0.0
        
        # === DYNAMIC BASE EVIDENCE ASSESSMENT ===
        evidence_score = issue.get('base_evidence', 0.7)  # Phrase-specific base score
        
        # === LINGUISTIC CLUES (TONE-SPECIFIC) ===
        evidence_score = self._apply_tone_linguistic_clues(evidence_score, issue, sentence_obj)
        
        # === STRUCTURAL CLUES ===
        evidence_score = self._apply_tone_structural_clues(evidence_score, issue, context)
        
        # === SEMANTIC CLUES ===
        evidence_score = self._apply_tone_semantic_clues(evidence_score, issue, text, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range
    
    def _apply_tone_linguistic_clues(self, evidence_score: float, issue: Dict[str, Any], sentence_obj) -> float:
        """Apply linguistic clues specific to tone analysis."""
        sent_text = sentence_obj.text
        
        # Exclamation points increase casualness evidence
        if sent_text.strip().endswith('!'):
            evidence_score += 0.1
        
        # Personal pronouns can indicate conversational style
        personal_pronouns = sum(1 for token in sentence_obj if token.lemma_.lower() in {'i', 'we', 'you'})
        if personal_pronouns > 0:
            evidence_score -= 0.05  # Slight reduction - may be acceptable
        
        # Sentence length affects clarity of violation
        token_count = len([t for t in sentence_obj if not t.is_space])
        if token_count > 25:
            evidence_score += 0.05  # Long sentences amplify confusion
        
        return evidence_score
    
    def _apply_tone_structural_clues(self, evidence_score: float, issue: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Apply structural clues specific to tone analysis."""
        block_type = context.get('block_type', 'paragraph')
        
        # Reduce evidence for certain structural contexts
        if block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.1  # Tables often more condensed
        elif block_type in ['heading', 'title']:
            evidence_score -= 0.05  # Headings slightly more flexible
        
        return evidence_score
    
    def _apply_tone_semantic_clues(self, evidence_score: float, issue: Dict[str, Any], text: str, context: Dict[str, Any]) -> float:
        """Apply semantic clues specific to tone analysis."""
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        
        # Stricter standards for formal contexts
        if content_type in ['technical', 'legal', 'academic']:
            evidence_score += 0.1
        elif content_type in ['marketing', 'narrative']:
            evidence_score -= 0.1  # Slightly more flexible
        
        # Audience-specific adjustments
        if audience in ['beginner', 'general']:
            evidence_score += 0.05  # Clearer communication needed
        elif audience in ['expert', 'developer']:
            evidence_score -= 0.05  # Experts may appreciate directness
        
        return evidence_score
    
    # === SURGICAL ZERO FALSE POSITIVE GUARD METHODS ===
    
    def _is_phrase_in_actual_quotes(self, phrase: str, sent_text: str, issue: Dict[str, Any]) -> bool:
        """
        Surgical check: Is the phrase actually within quotation marks?
        Only returns True for genuine quoted content, not incidental apostrophes.
        """
        match_start = issue.get('match_start', 0)
        match_end = issue.get('match_end', len(phrase))
        
        # Look for quote pairs that actually enclose the phrase
        quote_chars = ['"', '"', '"', "'", "'", "'"]
        
        # Check text before phrase for opening quote
        before_text = sent_text[:match_start]
        after_text = sent_text[match_end:]
        
        # Find closest quote before and after
        open_quote_found = False
        close_quote_found = False
        
        # Look backwards for opening quote
        for i in range(len(before_text) - 1, -1, -1):
            if before_text[i] in quote_chars:
                open_quote_found = True
                break
            elif before_text[i] in '.!?':  # Sentence boundary
                break
                
        # Look forwards for closing quote
        for i in range(len(after_text)):
            if after_text[i] in quote_chars:
                close_quote_found = True
                break
            elif after_text[i] in '.!?':  # Sentence boundary
                break
        
        return open_quote_found and close_quote_found
    
    def _is_intentional_informal_context(self, sentence_obj, context: Dict[str, Any]) -> bool:
        """
        Surgical check: Is this a context where informal tone is intentionally appropriate?
        Only returns True for genuine informal contexts, not style violations.
        """
        content_type = context.get('content_type', '')
        block_type = context.get('block_type', '')
        
        # Marketing copy often uses informal language intentionally
        if content_type == 'marketing':
            return True
            
        # User quotes or testimonials
        if block_type in ['quote', 'testimonial', 'user_story']:
            return True
            
        # Casual tutorials or beginner content
        if (content_type == 'tutorial' and 
            context.get('audience') in ['beginner', 'casual']):
            return True
            
        # Check for explicit informal indicators in the sentence
        informal_indicators = [
            'user says', 'customer feedback', 'quote from', 'testimonial',
            'user review', 'community comment'
        ]
        
        sent_lower = sentence_obj.text.lower()
        return any(indicator in sent_lower for indicator in informal_indicators)
    
    def _is_domain_appropriate_phrase(self, phrase: str, context: Dict[str, Any]) -> bool:
        """
        Surgical check: Is this phrase appropriate for the specific domain?
        Only returns True when phrase is genuinely domain-appropriate.
        """
        domain = context.get('domain', '')
        content_type = context.get('content_type', '')
        phrase_lower = phrase.lower()
        
        # Domain-specific appropriateness mapping
        domain_appropriate = {
            'gaming': ['game changer', 'level up', 'power up'],
            'sports': ['slam dunk', 'home run', 'touchdown'],
            'business': ['low-hanging fruit', 'move the needle'],  # Only in business context
            'startup': ['disruptive', 'game changer', 'breakthrough'],
            'finance': ['cash flow', 'bottom line', 'profit margin']
        }
        
        # Check if phrase is appropriate for this specific domain
        if domain in domain_appropriate:
            return phrase_lower in domain_appropriate[domain]
            
        # Content type specific checks
        if content_type == 'marketing' and phrase_lower in ['game changer', 'breakthrough']:
            return True
            
        return False
    
    def _is_proper_noun_phrase(self, phrase: str, sentence_obj) -> bool:
        """
        Surgical check: Is this phrase part of a proper noun, brand name, or title?
        Only returns True for genuine proper nouns, not style violations.
        """
        # Check if any tokens in the phrase are tagged as proper nouns
        phrase_tokens = [token for token in sentence_obj if phrase.lower() in token.text.lower()]
        
        for token in phrase_tokens:
            # Check if token is part of named entity
            if hasattr(token, 'ent_type_') and token.ent_type_ in ['ORG', 'PRODUCT', 'PERSON', 'EVENT']:
                return True
                
            # Check if token is proper noun by POS tag
            if hasattr(token, 'tag_') and token.tag_ in ['NNP', 'NNPS']:
                return True
                
        # Check for title case patterns (likely proper nouns)
        words = phrase.split()
        if len(words) >= 2 and all(word[0].isupper() for word in words if word):
            return True
            
        return False
