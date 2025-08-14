"""
Parentheses Rule
Based on IBM Style Guide topic: "Parentheses"

**UPDATED** with evidence-based scoring for nuanced parentheses usage analysis.
"""
from typing import List, Dict, Any, Optional
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens import Doc, Token, Span
except ImportError:
    Doc = None
    Token = None
    Span = None

class ParenthesesRule(BasePunctuationRule):
    """
    Checks for incorrect punctuation within or around parentheses using evidence-based analysis,
    with dependency parsing to determine if parenthetical content is a complete sentence.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'parentheses'

    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for parentheses punctuation:
          - Period placement depends on whether parenthetical content is a complete sentence
          - Various contexts affect proper parentheses usage
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        
        # Fallback analysis when nlp is not available
        if not nlp:
            # Apply basic guards for fallback analysis
            content_type = context.get('content_type', 'general')
            block_type = context.get('block_type', 'paragraph')
            
            # Skip if in contexts where parentheses punctuation is legitimate
            if content_type in ['creative', 'literary', 'narrative']:
                return errors  # No errors for creative content
            if block_type in ['quote', 'blockquote', 'code_block', 'literal_block', 'citation']:
                return errors  # No errors for quotes, code, and citations
            
            import re
            for i, sentence in enumerate(sentences):
                # Simple pattern for period inside parentheses
                for match in re.finditer(r'\([^)]*\.\)', sentence):
                    # Check for abbreviations that legitimately end with periods
                    match_text = match.group(0).lower()
                    if any(abbrev in match_text for abbrev in ['e.g.', 'i.e.', 'etc.', 'et al.', 'cf.']):
                        continue  # Skip abbreviations
                    
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Check parentheses punctuation: periods should be outside parentheses for fragments.",
                        suggestions=["Move the period outside the parentheses if the content is not a complete sentence."],
                        severity='low',
                        text=text,
                        context=context,
                        evidence_score=0.6,  # Default evidence for fallback analysis
                        span=(match.start(), match.end()),
                        flagged_text=match.group(0)
                    ))
            return errors

        try:
            doc = nlp(text)
            for i, sent in enumerate(doc.sents):
                for token in sent:
                    if token.text == ')':
                        evidence_score = self._calculate_parentheses_evidence(token, sent, text, context)
                        
                        # Only flag if evidence suggests it's worth evaluating
                        if evidence_score > 0.1:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=self._get_contextual_parentheses_message(token, evidence_score, context),
                                suggestions=self._generate_smart_parentheses_suggestions(token, evidence_score, sent, context),
                                severity='low' if evidence_score < 0.7 else 'medium',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=(token.idx, token.idx + len(token.text)),
                                flagged_text=token.text
                            ))
        except Exception as e:
            # Safeguard for unexpected SpaCy behavior
            errors.append(self._create_error(
                sentence=text,
                sentence_index=0,
                message=f"Rule ParenthesesRule failed with error: {e}",
                suggestions=["This may be a bug in the rule. Please report it."],
                severity='low',
                text=text,
                context=context,
                evidence_score=0.0  # No evidence when analysis fails
            ))
        return errors

    # === EVIDENCE CALCULATION ===

    def _calculate_parentheses_evidence(self, paren_token: 'Token', sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) that parentheses punctuation is incorrect.
        
        Higher scores indicate stronger evidence of an error.
        Lower scores indicate acceptable usage or ambiguous cases.
        """
        # Check if there's a period inside the parentheses
        if not self._has_period_inside_parentheses(paren_token, sent):
            return 0.0  # No period inside, no punctuation issue
        
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        # Apply surgical guards FIRST to eliminate false positives
        if self._apply_zero_false_positive_guards_punctuation(paren_token, context):
            return 0.0
        
        # Creative content commonly uses parentheses for asides and thoughts
        content_type = context.get('content_type', 'general')
        if content_type in ['creative', 'literary', 'narrative']:
            return 0.0
        
        # Quotes preserve original punctuation including parentheses
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['quote', 'blockquote']:
            return 0.0
        
        # Citations and academic references have specific formatting
        if block_type in ['citation', 'reference', 'footnote']:
            return 0.0
        
        # Academic content often has complex parenthetical content
        if content_type == 'academic':
            domain = context.get('domain', 'general')
            if domain in ['research', 'academic']:
                return 0.0
        
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        # Start with moderate evidence for period inside parentheses
        evidence_score = 0.6
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_parentheses(evidence_score, paren_token, sent)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_parentheses(evidence_score, paren_token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_parentheses(evidence_score, paren_token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_parentheses(evidence_score, paren_token, context)
        
        return max(0.0, min(1.0, evidence_score))

    def _has_period_inside_parentheses(self, paren_token: 'Token', sent: 'Span') -> bool:
        """Check if there's a period immediately before the closing parenthesis."""
        if paren_token.i > sent.start:
            prev_token = sent.doc[paren_token.i - 1]
            return prev_token.text == '.'
        return False

    def _apply_linguistic_clues_parentheses(self, evidence_score: float, paren_token: 'Token', sent: 'Span') -> float:
        """Apply SpaCy-based linguistic analysis clues for parentheses punctuation."""
        
        # Find the opening parenthesis and analyze the content
        paren_start_index = -1
        for j in range(paren_token.i - 1, sent.start - 1, -1):
            if sent.doc[j].text == '(':
                paren_start_index = j
                break
        
        if paren_start_index == -1:
            return evidence_score  # Can't find opening parenthesis
        
        # Get the content between parentheses (excluding the period)
        period_before_paren = paren_token.i > sent.start and sent.doc[paren_token.i - 1].text == '.'
        end_idx = paren_token.i - 1 if period_before_paren else paren_token.i
        
        if end_idx <= paren_start_index + 1:
            return evidence_score  # Empty or minimal content
        
        paren_content = sent.doc[paren_start_index + 1:end_idx]
        
        # === LINGUISTIC ANALYSIS ===
        
        # Check if parenthetical content forms a complete sentence
        has_subject = any(t.dep_ in ('nsubj', 'nsubjpass') for t in paren_content)
        has_root_verb = any(t.dep_ == 'ROOT' for t in paren_content)
        has_object_or_complement = any(t.dep_ in ('dobj', 'iobj', 'attr', 'acomp') for t in paren_content)
        
        # Complete sentence indicators
        if has_subject and has_root_verb:
            evidence_score -= 0.5  # Likely a complete sentence, period inside is correct
            
            # Additional completeness indicators
            if has_object_or_complement:
                evidence_score -= 0.2
        
        # Fragment indicators
        elif len(paren_content) <= 3:
            evidence_score += 0.3  # Short fragments unlikely to need internal periods
        
        # Check for sentence-like patterns
        starts_with_capital = paren_content[0].text[0].isupper() if paren_content else False
        if starts_with_capital and len(paren_content) > 3:
            evidence_score -= 0.2  # Capitalized longer content may be sentence
        
        # Check for specific linguistic patterns
        
        # Abbreviations or acronyms (e.g., etc., i.e., e.g.)
        abbreviation_patterns = {'etc', 'i.e', 'e.g', 'cf', 'vs', 'et', 'al'}
        if any(token.text.lower().rstrip('.') in abbreviation_patterns for token in paren_content):
            evidence_score -= 0.4  # Abbreviations legitimately end with periods
        
        # Citations or references
        if any(token.like_num for token in paren_content):
            # Contains numbers, might be citation
            evidence_score -= 0.2
        
        # Common parenthetical expressions
        common_expressions = {'see', 'cf', 'compare', 'note', 'emphasis', 'added', 'original'}
        if any(token.text.lower() in common_expressions for token in paren_content):
            evidence_score -= 0.1
        
        return evidence_score

    def _apply_structural_clues_parentheses(self, evidence_score: float, paren_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply document structure-based clues for parentheses punctuation."""
        
        block_type = context.get('block_type', 'paragraph')
        
        # Academic and technical content often has complex parenthetical citations
        if block_type in ['citation', 'reference', 'footnote']:
            evidence_score -= 0.4
        
        # Code blocks may have different punctuation rules
        elif block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.3
        
        # Lists may contain abbreviated items
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.2
        
        # Tables may have condensed notation
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.2
        
        # Quotes should preserve original punctuation
        elif block_type in ['quote', 'blockquote']:
            evidence_score -= 0.5
        
        # Headings rarely have complex parenthetical content
        elif block_type in ['heading', 'title']:
            evidence_score += 0.1
        
        return evidence_score

    def _apply_semantic_clues_parentheses(self, evidence_score: float, paren_token: 'Token', text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for parentheses punctuation."""
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # Academic writing frequently uses complex parenthetical citations
        if content_type == 'academic':
            evidence_score -= 0.2
        
        # Legal writing has specific citation formats
        elif content_type == 'legal':
            evidence_score -= 0.15
        
        # Technical writing may have specifications in parentheses
        elif content_type == 'technical':
            evidence_score -= 0.1
        
        # Scientific writing often has methodology notes
        elif content_type == 'scientific':
            evidence_score -= 0.15
        
        # Creative writing may use parentheses for asides
        elif content_type == 'creative':
            evidence_score -= 0.1
        
        # Marketing content typically simpler
        elif content_type == 'marketing':
            evidence_score += 0.05
        
        # Domain-specific adjustments
        if domain in ['academic', 'research']:
            evidence_score -= 0.1  # More complex parenthetical content
        elif domain in ['journalism', 'news']:
            evidence_score -= 0.05  # May have attribution in parentheses
        elif domain in ['legal', 'law']:
            evidence_score -= 0.15  # Legal citations
        elif domain in ['medicine', 'science']:
            evidence_score -= 0.1  # Scientific notation
        
        # Audience considerations
        if audience in ['academic', 'researcher']:
            evidence_score -= 0.1  # Familiar with complex parenthetical content
        elif audience in ['expert', 'professional']:
            evidence_score -= 0.05
        elif audience in ['general', 'consumer']:
            evidence_score += 0.05  # Simpler parenthetical content expected
        
        return evidence_score

    def _apply_feedback_clues_parentheses(self, evidence_score: float, paren_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply clues learned from user feedback patterns for parentheses punctuation."""
        
        feedback_patterns = self._get_cached_feedback_patterns_parentheses()
        
        # Analyze parenthetical content for common patterns
        paren_content = self._extract_parenthetical_content(paren_token, paren_token.sent)
        
        if paren_content:
            content_words = [word.lower() for word in paren_content.split() if word.isalpha()]
            
            # Check for commonly accepted internal punctuation patterns
            accepted_patterns = feedback_patterns.get('accepted_internal_punctuation', set())
            if any(pattern in paren_content.lower() for pattern in accepted_patterns):
                evidence_score -= 0.3
            
            # Check for commonly flagged patterns
            flagged_patterns = feedback_patterns.get('flagged_internal_punctuation', set())
            if any(pattern in paren_content.lower() for pattern in flagged_patterns):
                evidence_score += 0.2
            
            # Length-based patterns
            if len(content_words) <= 2:
                # Short parenthetical content rarely needs internal periods
                evidence_score += 0.2
            elif len(content_words) > 8:
                # Long parenthetical content more likely to be complete sentences
                evidence_score -= 0.2
        
        # Context-specific feedback patterns
        block_type = context.get('block_type', 'paragraph')
        block_patterns = feedback_patterns.get(f'{block_type}_parentheses_patterns', {})
        
        if 'internal_period_accepted_rate' in block_patterns:
            acceptance_rate = block_patterns['internal_period_accepted_rate']
            if acceptance_rate > 0.7:
                evidence_score -= 0.2
            elif acceptance_rate < 0.3:
                evidence_score += 0.2
        
        return evidence_score

    def _extract_parenthetical_content(self, paren_token: 'Token', sent: 'Span') -> str:
        """Extract the text content between parentheses."""
        paren_start_index = -1
        for j in range(paren_token.i - 1, sent.start - 1, -1):
            if sent.doc[j].text == '(':
                paren_start_index = j
                break
        
        if paren_start_index == -1:
            return ""
        
        # Extract content, excluding the period if it's there
        period_before_paren = paren_token.i > sent.start and sent.doc[paren_token.i - 1].text == '.'
        end_idx = paren_token.i - 1 if period_before_paren else paren_token.i
        
        if end_idx <= paren_start_index + 1:
            return ""
        
        tokens = sent.doc[paren_start_index + 1:end_idx]
        return ' '.join(token.text for token in tokens)

    def _get_cached_feedback_patterns_parentheses(self) -> Dict[str, Any]:
        """Load feedback patterns for parentheses punctuation from cache or feedback analysis."""
        return {
            'accepted_internal_punctuation': {
                'i.e.', 'e.g.', 'etc.', 'cf.', 'et al.', 'vs.', 'see also',
                'emphasis added', 'emphasis mine', 'original emphasis'
            },
            'flagged_internal_punctuation': {
                'for example.', 'such as.', 'including.', 'like.'
            },
            'paragraph_parentheses_patterns': {'internal_period_accepted_rate': 0.3},
            'citation_parentheses_patterns': {'internal_period_accepted_rate': 0.8},
            'code_block_parentheses_patterns': {'internal_period_accepted_rate': 0.5},
            'academic_parentheses_patterns': {'internal_period_accepted_rate': 0.7},
        }

    # === SMART MESSAGING ===

    def _get_contextual_parentheses_message(self, paren_token: 'Token', evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for parentheses punctuation."""
        
        content_type = context.get('content_type', 'general')
        block_type = context.get('block_type', 'paragraph')
        
        if evidence_score > 0.8:
            if content_type in ['academic', 'legal']:
                return "Check parentheses punctuation: periods should be outside parentheses unless the content is a complete sentence."
            else:
                return "Incorrect punctuation: period should be outside parentheses for fragmentary content."
        elif evidence_score > 0.6:
            return "Consider parentheses punctuation: move period outside unless parenthetical content is a complete sentence."
        elif evidence_score > 0.4:
            return "Review parentheses punctuation: ensure period placement follows content completeness."
        else:
            return "Evaluate parentheses punctuation for consistency with style guidelines."

    def _generate_smart_parentheses_suggestions(self, paren_token: 'Token', evidence_score: float, sent: 'Span', context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for parentheses punctuation."""
        
        suggestions = []
        content_type = context.get('content_type', 'general')
        block_type = context.get('block_type', 'paragraph')
        
        # Analyze the parenthetical content
        paren_content = self._extract_parenthetical_content(paren_token, sent)
        
        # High evidence suggestions
        if evidence_score > 0.7:
            suggestions.append("Move the period outside the closing parenthesis.")
            
            if len(paren_content.split()) <= 3:
                suggestions.append("Short parenthetical phrases do not need periods inside parentheses.")
            else:
                suggestions.append("Check if the parenthetical content forms a complete sentence before placing period inside.")
        
        # Medium evidence suggestions
        elif evidence_score > 0.4:
            suggestions.append("Consider whether the parenthetical content is a complete sentence.")
            suggestions.append("Periods go outside parentheses for fragments, inside for complete sentences.")
        
        # Content-specific suggestions
        if 'i.e.' in paren_content or 'e.g.' in paren_content or 'etc.' in paren_content:
            suggestions.append("Abbreviations like 'i.e.', 'e.g.', and 'etc.' keep their periods inside parentheses.")
        elif content_type == 'academic' and block_type in ['citation', 'reference']:
            suggestions.append("Academic citations may have specific punctuation rules - verify with style guide.")
        elif content_type == 'legal':
            suggestions.append("Legal documents follow specific citation formats - check applicable style guide.")
        
        # General guidance
        if len(suggestions) < 2:
            suggestions.append("Parenthetical fragments end with periods outside; complete sentences end with periods inside.")
            suggestions.append("Test by removing parentheses: if content can stand alone, period goes inside.")
        
        return suggestions[:3]