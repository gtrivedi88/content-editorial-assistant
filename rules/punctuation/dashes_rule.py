"""
Dashes Rule
Based on IBM Style Guide topic: "Dashes"
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

class DashesRule(BasePunctuationRule):
    """
    Checks for the use of em dashes using evidence-based analysis,
    with context awareness for legitimate usage scenarios.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'dashes'

    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for em dash usage:
          - Em dashes are generally discouraged in technical writing
          - Various contexts may legitimize dash usage (dialogue, titles, etc.)
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        
        # Fallback analysis when nlp is not available
        if not nlp:
            for i, sentence in enumerate(sentences):
                for match in re.finditer(r'—', sentence):
                    # Apply basic guards for fallback analysis
                    content_type = context.get('content_type', 'general')
                    block_type = context.get('block_type', 'paragraph')
                    
                    # Skip if in contexts where dashes are legitimate
                    if content_type in ['creative', 'literary', 'narrative', 'marketing']:
                        continue
                    if block_type in ['quote', 'blockquote', 'dialogue', 'heading', 'title', 'code_block', 'literal_block']:
                        continue
                    
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Avoid em dashes (—) in technical writing.",
                        suggestions=["Rewrite the sentence using commas, parentheses, or a colon instead."],
                        severity='medium',
                        text=text,
                        context=context,
                        evidence_score=0.7,  # Default evidence for fallback analysis
                        span=(match.start(), match.end()),
                        flagged_text=match.group(0)
                    ))
            return errors

        try:
            doc = nlp(text)
            for i, sent in enumerate(doc.sents):
                for token in sent:
                    if token.text == '—':
                        evidence_score = self._calculate_dash_evidence(token, sent, text, context)
                        
                        # Only flag if evidence suggests it's worth evaluating
                        if evidence_score > 0.1:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=self._get_contextual_dash_message(token, evidence_score, context),
                                suggestions=self._generate_smart_dash_suggestions(token, evidence_score, sent, context),
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
                message=f"Rule DashesRule failed with error: {e}",
                suggestions=["This may be a bug in the rule. Please report it."],
                severity='low',
                text=text,
                context=context,
                evidence_score=0.0  # No evidence when analysis fails
            ))
        return errors

    # === EVIDENCE CALCULATION ===

    def _calculate_dash_evidence(self, dash_token: 'Token', sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) that a dash usage is incorrect.
        
        Higher scores indicate stronger evidence of an error.
        Lower scores indicate acceptable usage or ambiguous cases.
        """
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        # Apply surgical guards FIRST to eliminate false positives
        if self._apply_zero_false_positive_guards_punctuation(dash_token, context):
            return 0.0
        
        # Creative content allows em dashes
        content_type = context.get('content_type', 'general')
        if content_type in ['creative', 'literary', 'narrative']:
            return 0.0
        
        # Marketing content is more flexible with stylistic punctuation
        if content_type == 'marketing':
            return 0.0
        
        # Quotes and dialogue commonly use dashes
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['quote', 'blockquote', 'dialogue']:
            return 0.0
        
        # Headings often use dashes for subtitles (Chapter 5 — Introduction)
        if block_type in ['heading', 'title']:
            return 0.0
        
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        # Em dashes are generally discouraged in technical writing
        evidence_score = 0.7  # Start with moderate evidence
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_dash(evidence_score, dash_token, sent)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_dash(evidence_score, dash_token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_dash(evidence_score, dash_token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_dash(evidence_score, dash_token, context)
        
        return max(0.0, min(1.0, evidence_score))

    def _apply_linguistic_clues_dash(self, evidence_score: float, dash_token: 'Token', sent: 'Span') -> float:
        """Apply SpaCy-based linguistic analysis clues for dash usage."""
        
        token_sent_idx = dash_token.i - sent.start
        
        # Check for legitimate dash usage patterns
        if 0 < token_sent_idx < len(sent) - 1:
            prev_token = sent[token_sent_idx - 1]
            next_token = sent[token_sent_idx + 1]
            
            # Parenthetical usage (word — phrase — word) is more acceptable
            if token_sent_idx > 1 and token_sent_idx < len(sent) - 2:
                # Look for paired dashes
                for j in range(token_sent_idx + 1, len(sent)):
                    if sent[j].text == '—':
                        evidence_score -= 0.3  # Paired dashes more acceptable
                        break
            
            # Attribution dashes (— Author Name) are common
            if next_token.pos_ == 'PROPN':
                # Check if this looks like an attribution
                remaining_tokens = sent[token_sent_idx + 1:]
                if len(remaining_tokens) <= 3 and all(t.pos_ in ['PROPN', 'NOUN'] for t in remaining_tokens):
                    evidence_score -= 0.4
            
            # Dialogue attribution
            if prev_token.text.endswith('"') or next_token.text.startswith('"'):
                evidence_score -= 0.3
        
        # Start of sentence dash (— Like this) is often stylistic
        if token_sent_idx == 0:
            evidence_score -= 0.2
        
        # End of sentence dash (like this —) is often stylistic
        if token_sent_idx == len(sent) - 1:
            evidence_score -= 0.2
        
        return evidence_score

    def _apply_structural_clues_dash(self, evidence_score: float, dash_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply document structure-based clues for dash usage."""
        
        block_type = context.get('block_type', 'paragraph')
        
        # Quotes and dialogue blocks may use dashes legitimately
        if block_type in ['quote', 'blockquote']:
            evidence_score -= 0.4
        
        # Literary or creative content may use dashes
        elif block_type in ['verse', 'poem']:
            evidence_score -= 0.5
        
        # Headings sometimes use dashes for separation
        elif block_type in ['heading', 'title']:
            evidence_score -= 0.2
        
        # Lists may use dashes as bullet points
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.3
        
        # Code blocks have different punctuation rules
        elif block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.6
        
        # Table content may use dashes for ranges or separators
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.2
        
        return evidence_score

    def _apply_semantic_clues_dash(self, evidence_score: float, dash_token: 'Token', text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for dash usage."""
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # Technical content should avoid dashes more strictly
        if content_type == 'technical':
            evidence_score += 0.1
        
        # Academic writing prefers formal punctuation
        elif content_type == 'academic':
            evidence_score += 0.05
        
        # Legal writing is very formal
        elif content_type == 'legal':
            evidence_score += 0.1
        
        # Marketing content may be more creative
        elif content_type == 'marketing':
            evidence_score -= 0.1
        
        # Creative writing uses dashes more freely
        elif content_type == 'creative':
            evidence_score -= 0.3
        
        # Procedural content should be clear and direct
        elif content_type == 'procedural':
            evidence_score += 0.05
        
        # Domain-specific adjustments
        if domain in ['software', 'engineering']:
            evidence_score += 0.05  # More technical contexts
        elif domain in ['literature', 'journalism']:
            evidence_score -= 0.2  # More creative contexts
        
        # Audience considerations
        if audience in ['expert', 'developer']:
            evidence_score += 0.05  # Prefer technical precision
        elif audience in ['general', 'consumer']:
            evidence_score -= 0.05  # More flexible
        
        return evidence_score

    def _apply_feedback_clues_dash(self, evidence_score: float, dash_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply clues learned from user feedback patterns for dash usage."""
        
        feedback_patterns = self._get_cached_feedback_patterns_dash()
        
        # Get context around the dash
        token_sent_idx = dash_token.i - dash_token.sent.start
        sent = dash_token.sent
        
        # Look for patterns in accepted/rejected dash usage
        if token_sent_idx > 0:
            prev_word = sent[token_sent_idx - 1].text.lower()
            
            # Words commonly accepted before dashes
            if prev_word in feedback_patterns.get('accepted_preceding_words', set()):
                evidence_score -= 0.2
            
            # Words commonly flagged before dashes
            elif prev_word in feedback_patterns.get('flagged_preceding_words', set()):
                evidence_score += 0.1
        
        if token_sent_idx < len(sent) - 1:
            next_word = sent[token_sent_idx + 1].text.lower()
            
            # Words commonly accepted after dashes
            if next_word in feedback_patterns.get('accepted_following_words', set()):
                evidence_score -= 0.2
        
        # Context-specific patterns
        block_type = context.get('block_type', 'paragraph')
        block_patterns = feedback_patterns.get(f'{block_type}_dash_patterns', {})
        
        if 'accepted_rate' in block_patterns:
            acceptance_rate = block_patterns['accepted_rate']
            if acceptance_rate > 0.7:
                evidence_score -= 0.2  # High acceptance in this context
            elif acceptance_rate < 0.3:
                evidence_score += 0.1  # Low acceptance in this context
        
        return evidence_score

    def _get_cached_feedback_patterns_dash(self) -> Dict[str, Any]:
        """Load feedback patterns for dash usage from cache or feedback analysis."""
        return {
            'accepted_preceding_words': {'quote', 'said', 'wrote', 'chapter', 'section'},
            'flagged_preceding_words': {'the', 'a', 'an', 'to', 'for', 'with', 'in', 'on'},
            'accepted_following_words': {'that', 'this', 'which', 'author', 'speaker'},
            'paragraph_dash_patterns': {'accepted_rate': 0.3},
            'quote_dash_patterns': {'accepted_rate': 0.8},
            'heading_dash_patterns': {'accepted_rate': 0.6},
        }

    # === SMART MESSAGING ===

    def _get_contextual_dash_message(self, dash_token: 'Token', evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for dash usage."""
        
        content_type = context.get('content_type', 'general')
        
        if evidence_score > 0.8:
            if content_type == 'technical':
                return "Avoid em dashes (—) in technical writing: they can interrupt reading flow and appear informal."
            else:
                return "Em dash usage may be inappropriate: consider more formal punctuation."
        elif evidence_score > 0.6:
            return "Consider replacing em dash: commas, parentheses, or colons may be more appropriate."
        elif evidence_score > 0.4:
            return "Em dash usage may affect readability: consider alternative punctuation."
        else:
            return "Review em dash usage for consistency with style guidelines."

    def _generate_smart_dash_suggestions(self, dash_token: 'Token', evidence_score: float, sent: 'Span', context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for dash usage."""
        
        suggestions = []
        token_sent_idx = dash_token.i - sent.start
        
        # High evidence suggestions
        if evidence_score > 0.7:
            suggestions.append("Replace the em dash with commas to set off the parenthetical phrase.")
            suggestions.append("Use parentheses instead of the em dash for additional information.")
            
            # Check if it might be introducing something
            if token_sent_idx < len(sent) - 1:
                suggestions.append("Consider using a colon if introducing a list or explanation.")
        
        # Medium evidence suggestions
        elif evidence_score > 0.4:
            suggestions.append("Consider using commas or parentheses for better readability.")
            
            # Check for paired dashes
            has_second_dash = any(t.text == '—' for t in sent[token_sent_idx + 1:])
            if has_second_dash:
                suggestions.append("If setting off a phrase, consider using paired commas instead of dashes.")
            else:
                suggestions.append("For single interruptions, consider parentheses or commas.")
        
        # Context-specific suggestions
        content_type = context.get('content_type', 'general')
        if content_type == 'technical':
            suggestions.append("Technical writing benefits from precise, unambiguous punctuation.")
        elif content_type == 'academic':
            suggestions.append("Academic writing typically uses more formal punctuation conventions.")
        
        # General guidance
        if len(suggestions) < 2:
            suggestions.append("Em dashes can be replaced with commas, parentheses, or colons.")
            suggestions.append("Choose punctuation that maintains clarity and formality.")
        
        return suggestions[:3]
