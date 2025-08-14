"""
Ellipses Rule
Based on IBM Style Guide topic: "Ellipses"
"""
from typing import List, Dict, Any, Optional
from .base_punctuation_rule import BasePunctuationRule
import re

try:
    from spacy.tokens import Doc, Token, Span
except ImportError:
    Doc = None
    Token = None
    Span = None

class EllipsesRule(BasePunctuationRule):
    """
    Checks for the use of ellipses using evidence-based analysis,
    with context awareness for legitimate usage scenarios.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'ellipses'

    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for ellipses usage:
          - Ellipses are generally discouraged in technical writing
          - Various contexts may legitimize ellipses usage (quotes, code, etc.)
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        
        # Fallback analysis when nlp is not available
        if not nlp:
            for i, sentence in enumerate(sentences):
                # Apply basic guards for fallback analysis
                content_type = context.get('content_type', 'general')
                block_type = context.get('block_type', 'paragraph')
                
                # Skip if in contexts where ellipses are legitimate
                if content_type in ['creative', 'literary', 'narrative']:
                    continue
                if block_type in ['quote', 'blockquote', 'citation', 'code_block', 'literal_block']:
                    continue
                
                # Check for both three consecutive dots and Unicode ellipsis character
                for match in re.finditer(r'\.\.\.', sentence):
                    # Check for bracketed ellipses which are legitimate
                    start_pos = max(0, match.start() - 1)
                    end_pos = min(len(sentence), match.end() + 1)
                    context_text = sentence[start_pos:end_pos]
                    if '[' in context_text and ']' in context_text:
                        continue  # Skip bracketed ellipses
                    
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Avoid using ellipses (...) in technical writing.",
                        suggestions=["If text is omitted from a quote, this may be acceptable. Otherwise, if used for a pause, rewrite for a more formal and direct tone."],
                        severity='low',
                        text=text,
                        context=context,
                        evidence_score=0.6,  # Default evidence for fallback analysis
                        span=(match.start(), match.end()),
                        flagged_text=match.group(0)
                    ))
                
                for match in re.finditer(r'…', sentence):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Avoid using ellipses (…) in technical writing.",
                        suggestions=["If text is omitted from a quote, this may be acceptable. Otherwise, if used for a pause, rewrite for a more formal and direct tone."],
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
                    if token.text in ['...', '…'] or (len(token.text) >= 3 and all(c == '.' for c in token.text)):
                        evidence_score = self._calculate_ellipses_evidence(token, sent, text, context)
                        
                        # Only flag if evidence suggests it's worth evaluating
                        if evidence_score > 0.1:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=self._get_contextual_ellipses_message(token, evidence_score, context),
                                suggestions=self._generate_smart_ellipses_suggestions(token, evidence_score, sent, context),
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
                message=f"Rule EllipsesRule failed with error: {e}",
                suggestions=["This may be a bug in the rule. Please report it."],
                severity='low',
                text=text,
                context=context,
                evidence_score=0.0  # No evidence when analysis fails
            ))
        return errors

    # === EVIDENCE CALCULATION ===

    def _calculate_ellipses_evidence(self, ellipses_token: 'Token', sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) that ellipses usage is incorrect.
        
        Higher scores indicate stronger evidence of an error.
        Lower scores indicate acceptable usage or ambiguous cases.
        """
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        # Apply surgical guards FIRST to eliminate false positives
        if self._apply_zero_false_positive_guards_punctuation(ellipses_token, context):
            return 0.0
        
        # Creative content commonly uses ellipses for stylistic effect
        content_type = context.get('content_type', 'general')
        if content_type in ['creative', 'literary', 'narrative']:
            return 0.0
        
        # Marketing content uses ellipses for stylistic emphasis
        if content_type == 'marketing':
            return 0.0
        
        # Quotes and citations legitimately use ellipses for omissions
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['quote', 'blockquote', 'citation']:
            return 0.0
        
        # Check for bracketed ellipses [...] which are standard omission notation
        token_sent_idx = ellipses_token.i - sent.start
        if 0 < token_sent_idx < len(sent) - 1:
            prev_token = sent[token_sent_idx - 1]
            next_token = sent[token_sent_idx + 1]
            if prev_token.text in ['[', '('] and next_token.text in [']', ')']:
                return 0.0  # Standard omission notation
        
        # Check for quote patterns around ellipses
        sent_text = sent.text
        ellipses_pos = ellipses_token.idx - sent.start_char
        
        # Look for quotes around ellipses indicating omission
        before_ellipses = sent_text[:ellipses_pos]
        after_ellipses = sent_text[ellipses_pos + len(ellipses_token.text):]
        
        if ('"' in before_ellipses or "'" in before_ellipses) and ('"' in after_ellipses or "'" in after_ellipses):
            return 0.0  # Likely quote omission
        
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        # Ellipses are generally discouraged in technical writing
        evidence_score = 0.6  # Start with moderate evidence
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_ellipses(evidence_score, ellipses_token, sent)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_ellipses(evidence_score, ellipses_token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_ellipses(evidence_score, ellipses_token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_ellipses(evidence_score, ellipses_token, context)
        
        return max(0.0, min(1.0, evidence_score))

    def _apply_linguistic_clues_ellipses(self, evidence_score: float, ellipses_token: 'Token', sent: 'Span') -> float:
        """Apply SpaCy-based linguistic analysis clues for ellipses usage."""
        
        token_sent_idx = ellipses_token.i - sent.start
        
        # Check for legitimate ellipses usage patterns
        if 0 < token_sent_idx < len(sent) - 1:
            prev_token = sent[token_sent_idx - 1]
            next_token = sent[token_sent_idx + 1]
            
            # Quote continuation patterns (text... more text)
            if prev_token.text.endswith('"') or next_token.text.startswith('"'):
                evidence_score -= 0.4  # Likely quote omission
            
            # Mid-sentence ellipses often indicate hesitation or informal tone
            if prev_token.pos_ in ['NOUN', 'VERB', 'ADJ'] and next_token.pos_ in ['NOUN', 'VERB', 'ADJ']:
                evidence_score += 0.2
        
        # Start of sentence ellipses (... like this) often stylistic
        if token_sent_idx == 0:
            evidence_score -= 0.1
        
        # End of sentence ellipses (like this...) common in informal writing
        if token_sent_idx == len(sent) - 1:
            evidence_score += 0.1
        
        # Check for bracketed or parenthetical ellipses [...]
        if token_sent_idx > 0 and token_sent_idx < len(sent) - 1:
            prev_token = sent[token_sent_idx - 1]
            next_token = sent[token_sent_idx + 1]
            if prev_token.text in ['[', '('] and next_token.text in [']', ')']:
                evidence_score -= 0.5  # Standard omission notation
        
        return evidence_score

    def _apply_structural_clues_ellipses(self, evidence_score: float, ellipses_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply document structure-based clues for ellipses usage."""
        
        block_type = context.get('block_type', 'paragraph')
        
        # Quotes may use ellipses legitimately for omissions
        if block_type in ['quote', 'blockquote']:
            evidence_score -= 0.5
        
        # Code examples may use ellipses to indicate continuation
        elif block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.6
        
        # Academic content often uses ellipses in citations
        elif block_type in ['citation', 'reference']:
            evidence_score -= 0.4
        
        # Headings rarely need ellipses
        elif block_type in ['heading', 'title']:
            evidence_score += 0.2
        
        # Lists may use ellipses inappropriately
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score += 0.1
        
        # Table content should be concise
        elif block_type in ['table_cell', 'table_header']:
            evidence_score += 0.2
        
        # Dialogue or creative content may use ellipses
        elif block_type in ['dialogue', 'verse']:
            evidence_score -= 0.3
        
        return evidence_score

    def _apply_semantic_clues_ellipses(self, evidence_score: float, ellipses_token: 'Token', text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for ellipses usage."""
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # Technical content should avoid ellipses more strictly
        if content_type == 'technical':
            evidence_score += 0.15
        
        # Academic writing may use ellipses in citations
        elif content_type == 'academic':
            evidence_score -= 0.1
        
        # Legal writing should be precise
        elif content_type == 'legal':
            evidence_score += 0.1
        
        # Marketing content may be more conversational
        elif content_type == 'marketing':
            evidence_score -= 0.05
        
        # Creative writing uses ellipses more freely
        elif content_type == 'creative':
            evidence_score -= 0.4
        
        # Procedural content should be clear and direct
        elif content_type == 'procedural':
            evidence_score += 0.1
        
        # Domain-specific adjustments
        if domain in ['software', 'engineering']:
            evidence_score += 0.1  # More technical contexts
        elif domain in ['literature', 'journalism']:
            evidence_score -= 0.2  # More creative contexts
        elif domain in ['academic', 'research']:
            evidence_score -= 0.1  # Citations may use ellipses
        
        # Audience considerations
        if audience in ['expert', 'developer']:
            evidence_score += 0.05  # Prefer technical precision
        elif audience in ['general', 'consumer']:
            evidence_score -= 0.05  # More flexible
        
        return evidence_score

    def _apply_feedback_clues_ellipses(self, evidence_score: float, ellipses_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply clues learned from user feedback patterns for ellipses usage."""
        
        feedback_patterns = self._get_cached_feedback_patterns_ellipses()
        
        # Get context around the ellipses
        token_sent_idx = ellipses_token.i - ellipses_token.sent.start
        sent = ellipses_token.sent
        
        # Look for patterns in accepted/rejected ellipses usage
        if token_sent_idx > 0:
            prev_word = sent[token_sent_idx - 1].text.lower()
            
            # Words commonly accepted before ellipses
            if prev_word in feedback_patterns.get('accepted_preceding_words', set()):
                evidence_score -= 0.3
            
            # Words commonly flagged before ellipses
            elif prev_word in feedback_patterns.get('flagged_preceding_words', set()):
                evidence_score += 0.2
        
        if token_sent_idx < len(sent) - 1:
            next_word = sent[token_sent_idx + 1].text.lower()
            
            # Words commonly accepted after ellipses
            if next_word in feedback_patterns.get('accepted_following_words', set()):
                evidence_score -= 0.2
        
        # Context-specific patterns
        block_type = context.get('block_type', 'paragraph')
        block_patterns = feedback_patterns.get(f'{block_type}_ellipses_patterns', {})
        
        if 'accepted_rate' in block_patterns:
            acceptance_rate = block_patterns['accepted_rate']
            if acceptance_rate > 0.7:
                evidence_score -= 0.3  # High acceptance in this context
            elif acceptance_rate < 0.3:
                evidence_score += 0.2  # Low acceptance in this context
        
        return evidence_score

    def _get_cached_feedback_patterns_ellipses(self) -> Dict[str, Any]:
        """Load feedback patterns for ellipses usage from cache or feedback analysis."""
        return {
            'accepted_preceding_words': {'quote', 'said', 'wrote', 'text', 'excerpt'},
            'flagged_preceding_words': {'well', 'so', 'um', 'like', 'you', 'i'},
            'accepted_following_words': {'and', 'then', 'but', 'or', 'more'},
            'paragraph_ellipses_patterns': {'accepted_rate': 0.2},
            'quote_ellipses_patterns': {'accepted_rate': 0.8},
            'code_block_ellipses_patterns': {'accepted_rate': 0.7},
        }

    # === SMART MESSAGING ===

    def _get_contextual_ellipses_message(self, ellipses_token: 'Token', evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for ellipses usage."""
        
        content_type = context.get('content_type', 'general')
        block_type = context.get('block_type', 'paragraph')
        
        if evidence_score > 0.8:
            if content_type == 'technical':
                return "Avoid ellipses (...) in technical writing: they create ambiguity and appear informal."
            else:
                return "Ellipses usage may be inappropriate: consider more direct expression."
        elif evidence_score > 0.6:
            if block_type in ['quote', 'blockquote']:
                return "Consider if ellipses are necessary: only use them to indicate omitted text in quotes."
            else:
                return "Consider replacing ellipses: complete sentences are clearer and more professional."
        elif evidence_score > 0.4:
            return "Ellipses usage may affect clarity: consider whether they add necessary meaning."
        else:
            return "Review ellipses usage for appropriateness and consistency with style guidelines."

    def _generate_smart_ellipses_suggestions(self, ellipses_token: 'Token', evidence_score: float, sent: 'Span', context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for ellipses usage."""
        
        suggestions = []
        token_sent_idx = ellipses_token.i - sent.start
        block_type = context.get('block_type', 'paragraph')
        content_type = context.get('content_type', 'general')
        
        # High evidence suggestions
        if evidence_score > 0.7:
            suggestions.append("Replace ellipses with complete sentences for clarity.")
            if token_sent_idx < len(sent) - 1:
                suggestions.append("Remove ellipses and continue the sentence directly.")
            else:
                suggestions.append("End the sentence with a period instead of ellipses.")
        
        # Medium evidence suggestions
        elif evidence_score > 0.4:
            if block_type in ['quote', 'blockquote']:
                suggestions.append("Use ellipses only to indicate omitted text from original quotes.")
                suggestions.append("Consider including the full quote if context is important.")
            else:
                suggestions.append("Consider rewriting without ellipses for a more direct tone.")
                suggestions.append("Use complete thoughts instead of trailing off with ellipses.")
        
        # Context-specific suggestions
        if content_type == 'technical':
            suggestions.append("Technical writing benefits from complete, unambiguous statements.")
        elif content_type == 'academic':
            suggestions.append("In academic writing, use ellipses only for quote omissions.")
        elif block_type in ['code_block', 'literal_block']:
            suggestions.append("In code examples, use comments to indicate continuation instead.")
        
        # General guidance
        if len(suggestions) < 2:
            suggestions.append("Ellipses should be used sparingly and only when necessary.")
            suggestions.append("Complete sentences are clearer than trailing ellipses.")
        
        return suggestions[:3]