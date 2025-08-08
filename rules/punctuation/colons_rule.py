"""
Colons Rule
Based on IBM Style Guide topic: "Colons"

**UPDATED** with evidence-based scoring for nuanced colon usage analysis.
"""
from typing import List, Dict, Any, Optional
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens import Doc, Token, Span
except ImportError:
    Doc = None
    Token = None
    Span = None

class ColonsRule(BasePunctuationRule):
    """
    Checks for incorrect colon usage using evidence-based analysis,
    with dependency parsing and structural awareness.
    """
    def _get_rule_type(self) -> str:
        return 'colons'

    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for colon usage:
          - Colons should be preceded by complete independent clauses
          - Various contexts legitimize colon usage (times, URLs, titles, lists)
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        if not nlp:
            return errors

        is_list_introduction = context.get('is_list_introduction', False)
        if is_list_introduction:
            return []

        try:
            doc = nlp(text)
            for i, sent in enumerate(doc.sents):
                for token in sent:
                    if token.text == ':':
                        evidence_score = self._calculate_colon_evidence(token, sent, text, context)
                        
                        # Only flag if evidence suggests it's worth evaluating
                        if evidence_score > 0.1:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=self._get_contextual_colon_message(token, evidence_score, context),
                                suggestions=self._generate_smart_colon_suggestions(token, evidence_score, sent, context),
                                severity='low' if evidence_score < 0.7 else 'medium',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=(token.idx, token.idx + len(token.text)),
                                flagged_text=token.text
                            ))
        except IndexError as e:
            # This catch is a safeguard in case of unexpected SpaCy behavior
            errors.append(self._create_error(
                sentence=text,
                sentence_index=0,
                message=f"Rule ColonsRule failed with an indexing error: {e}",
                suggestions=["This may be a bug in the rule. Please report it."],
                severity='low',
                text=text,
                context=context
            ))
        return errors

    def _is_legitimate_context(self, colon_token: 'Token', sent: 'Span') -> bool:
        """
        Uses linguistic anchors to identify legitimate colon contexts.
        This version uses safe, sentence-relative indexing.
        """
        # colon_token.i is the index in the parent doc.
        # sent.start is the start index of the sentence in the parent doc.
        # So, the token's index *within the sentence* is:
        token_sent_idx = colon_token.i - sent.start

        # Check for time/ratios (e.g., 3:30, 2:1)
        if 0 < token_sent_idx < len(sent) - 1:
            prev_token = sent[token_sent_idx - 1]
            next_token = sent[token_sent_idx + 1]
            if prev_token.like_num and next_token.like_num:
                return True

        # Check for URLs (e.g., http:)
        if "http" in colon_token.head.text.lower():
            return True

        # Check for Title: Subtitle patterns
        if colon_token.head.pos_ in ("NOUN", "PROPN") and colon_token.head.is_title:
             if token_sent_idx < len(sent) - 1 and sent[token_sent_idx + 1].is_title:
                return True

        return False

    def _is_preceded_by_complete_clause(self, colon_token: 'Token', sent: 'Span') -> bool:
        """
        Checks if tokens before the colon form a complete independent clause.
        This version uses safe, sentence-relative indexing.
        """
        if colon_token.i <= sent.start:
            return False

        # Create a new doc object from the span before the colon for accurate parsing
        clause_span = sent.doc[sent.start : colon_token.i]
        clause_doc = clause_span.as_doc()

        has_subject = any(t.dep_ in ('nsubj', 'nsubjpass') for t in clause_doc)
        has_root_verb = any(t.dep_ == 'ROOT' for t in clause_doc)
        
        # Check if a verb directly precedes the colon
        token_sent_idx = colon_token.i - sent.start
        verb_before_colon = False
        if token_sent_idx > 0:
            verb_before_colon = sent[token_sent_idx - 1].pos_ == "VERB"

        return has_subject and has_root_verb and not verb_before_colon

    def _is_legitimate_context_aware(self, colon_token: 'Token', sent: 'Span', context: Optional[Dict[str, Any]]) -> bool:
        """
        LINGUISTIC ANCHOR: Context-aware colon legitimacy checking using structural information.
        Uses inter-block context to determine if colons are introducing content like admonitions.
        """
        if not context:
            return False
        
        # If this block introduces an admonition, colons are legitimate
        if context.get('next_block_type') == 'admonition':
            return True
        
        # If we're in a list introduction context, colons are legitimate
        if context.get('is_list_introduction', False):
            return True
        
        return False

    # === EVIDENCE CALCULATION ===

    def _calculate_colon_evidence(self, colon_token: 'Token', sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) that a colon usage is incorrect.
        
        Higher scores indicate stronger evidence of an error.
        Lower scores indicate acceptable usage or ambiguous cases.
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        # Start with assumption that problematic colons need high evidence
        if self._is_legitimate_context(colon_token, sent) or self._is_legitimate_context_aware(colon_token, sent, context):
            return 0.0  # Legitimate contexts get no evidence
        
        if not self._is_preceded_by_complete_clause(colon_token, sent):
            evidence_score = 0.8  # Strong evidence of incorrect usage
        else:
            return 0.0  # Complete clause before colon is generally correct
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_colon(evidence_score, colon_token, sent)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_colon(evidence_score, colon_token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_colon(evidence_score, colon_token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_colon(evidence_score, colon_token, context)
        
        return max(0.0, min(1.0, evidence_score))

    def _apply_linguistic_clues_colon(self, evidence_score: float, colon_token: 'Token', sent: 'Span') -> float:
        """Apply SpaCy-based linguistic analysis clues for colon usage."""
        
        token_sent_idx = colon_token.i - sent.start
        
        # Check preceding token patterns
        if token_sent_idx > 0:
            prev_token = sent[token_sent_idx - 1]
            
            # Verb immediately before colon often indicates incomplete clause
            if prev_token.pos_ == 'VERB':
                evidence_score += 0.2
            
            # Preposition before colon is problematic
            if prev_token.pos_ == 'ADP':
                evidence_score += 0.3
            
            # Article before colon is very problematic
            if prev_token.pos_ == 'DET':
                evidence_score += 0.4
            
            # Conjunction before colon suggests incomplete thought
            if prev_token.pos_ in ['CCONJ', 'SCONJ']:
                evidence_score += 0.3
        
        # Check for common legitimate patterns we might have missed
        if token_sent_idx > 1 and token_sent_idx < len(sent) - 1:
            # Pattern: "Note: ..." or "Warning: ..."
            if token_sent_idx == 1:
                first_token = sent[0]
                if first_token.text.lower() in ['note', 'warning', 'tip', 'important', 'caution']:
                    evidence_score -= 0.6
            
            # Pattern: "Chapter 1: Introduction"
            prev_prev = sent[token_sent_idx - 2] if token_sent_idx > 1 else None
            prev_token = sent[token_sent_idx - 1]
            if prev_prev and prev_prev.text.lower() in ['chapter', 'section', 'part', 'step'] and prev_token.like_num:
                evidence_score -= 0.5
        
        # Check sentence length - very short sentences with colons are often labels
        if len(sent) <= 3:
            evidence_score -= 0.3
        
        return evidence_score

    def _apply_structural_clues_colon(self, evidence_score: float, colon_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply document structure-based clues for colon usage."""
        
        block_type = context.get('block_type', 'paragraph')
        
        # Headings often use colons legitimately
        if block_type in ['heading', 'title']:
            evidence_score -= 0.5
        
        # List items may use colons for definitions
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.3
        
        # Admonitions commonly use colons
        elif block_type == 'admonition':
            evidence_score -= 0.4
        
        # Table cells may use colons for ratios or labels
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.2
        
        # Code blocks have different punctuation rules
        elif block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.7
        
        # Next block type context
        if context.get('next_block_type') in ['ordered_list', 'unordered_list']:
            evidence_score -= 0.4  # Introducing a list
        
        return evidence_score

    def _apply_semantic_clues_colon(self, evidence_score: float, colon_token: 'Token', text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for colon usage."""
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # Technical content often uses colons for definitions and ratios
        if content_type == 'technical':
            evidence_score -= 0.1
        
        # Academic writing has more structured colon usage
        elif content_type == 'academic':
            evidence_score -= 0.05
        
        # Legal writing is very structured
        elif content_type == 'legal':
            evidence_score += 0.05  # Be stricter
        
        # Marketing content more creative but should still follow rules
        elif content_type == 'marketing':
            evidence_score -= 0.05
        
        # Procedural content often uses colons for step introductions
        elif content_type == 'procedural':
            evidence_score -= 0.2
        
        # Domain-specific adjustments
        if domain in ['software', 'engineering']:
            evidence_score -= 0.1  # More technical contexts
        elif domain in ['finance', 'legal']:
            evidence_score += 0.05  # More formal contexts
        
        # Expert audiences more familiar with technical colon usage
        if audience in ['expert', 'developer']:
            evidence_score -= 0.1
        elif audience in ['beginner', 'general']:
            evidence_score += 0.05  # Be more helpful
        
        return evidence_score

    def _apply_feedback_clues_colon(self, evidence_score: float, colon_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply clues learned from user feedback patterns for colon usage."""
        
        feedback_patterns = self._get_cached_feedback_patterns_colon()
        
        # Get context around the colon
        token_sent_idx = colon_token.i - colon_token.sent.start
        sent = colon_token.sent
        
        # Look for patterns in accepted/rejected colon usage
        if token_sent_idx > 0:
            prev_word = sent[token_sent_idx - 1].text.lower()
            
            # Words commonly accepted before colons
            if prev_word in feedback_patterns.get('accepted_preceding_words', set()):
                evidence_score -= 0.3
            
            # Words commonly flagged before colons
            elif prev_word in feedback_patterns.get('flagged_preceding_words', set()):
                evidence_score += 0.2
        
        # Context-specific patterns
        block_type = context.get('block_type', 'paragraph')
        block_patterns = feedback_patterns.get(f'{block_type}_colon_patterns', {})
        
        if 'accepted_rate' in block_patterns:
            acceptance_rate = block_patterns['accepted_rate']
            if acceptance_rate > 0.8:
                evidence_score -= 0.2  # High acceptance in this context
            elif acceptance_rate < 0.3:
                evidence_score += 0.1  # Low acceptance in this context
        
        return evidence_score

    def _get_cached_feedback_patterns_colon(self) -> Dict[str, Any]:
        """Load feedback patterns for colon usage from cache or feedback analysis."""
        return {
            'accepted_preceding_words': {'following', 'below', 'these', 'note', 'warning', 'example'},
            'flagged_preceding_words': {'the', 'a', 'an', 'to', 'for', 'with'},
            'paragraph_colon_patterns': {'accepted_rate': 0.6},
            'heading_colon_patterns': {'accepted_rate': 0.9},
            'list_item_colon_patterns': {'accepted_rate': 0.8},
        }

    # === SMART MESSAGING ===

    def _get_contextual_colon_message(self, colon_token: 'Token', evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for colon usage."""
        
        if evidence_score > 0.8:
            return "Incorrect colon usage: A colon must be preceded by a complete independent clause."
        elif evidence_score > 0.6:
            return "Consider revising colon usage: Ensure the text before the colon forms a complete thought."
        elif evidence_score > 0.4:
            return "Colon usage may be unclear: Check if the preceding text is a complete sentence."
        else:
            return "Review colon usage for clarity and grammatical correctness."

    def _generate_smart_colon_suggestions(self, colon_token: 'Token', evidence_score: float, sent: 'Span', context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for colon usage."""
        
        suggestions = []
        block_type = context.get('block_type', 'paragraph')
        
        # High evidence suggestions
        if evidence_score > 0.7:
            suggestions.append("Rewrite the text before the colon to form a complete sentence.")
            suggestions.append("Remove the colon if it's not introducing a list, quote, or explanation.")
        
        # Medium evidence suggestions
        elif evidence_score > 0.4:
            suggestions.append("Ensure the clause before the colon can stand alone as a sentence.")
            if block_type in ['paragraph', 'list_item']:
                suggestions.append("Consider using a period and starting a new sentence instead.")
        
        # Context-specific suggestions
        if block_type == 'heading':
            suggestions.append("In headings, colons can separate main topics from subtopics.")
        elif context.get('next_block_type') in ['ordered_list', 'unordered_list']:
            suggestions.append("Colons can introduce lists when preceded by a complete statement.")
        elif block_type == 'admonition':
            suggestions.append("Admonition labels (Note:, Warning:) commonly use colons.")
        
        # General guidance
        if len(suggestions) < 2:
            suggestions.append("Use colons to introduce explanations, lists, or quotations.")
            suggestions.append("Ensure proper grammar in the clause preceding the colon.")
        
        return suggestions[:3]