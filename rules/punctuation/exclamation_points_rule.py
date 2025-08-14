"""
Exclamation Points Rule
Based on IBM Style Guide topic: "Exclamation points"

**UPDATED** with evidence-based scoring for nuanced exclamation point usage analysis.
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

class ExclamationPointsRule(BasePunctuationRule):
    """
    Checks for exclamation points using evidence-based analysis,
    with context awareness for legitimate usage scenarios.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'exclamation_points'

    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for exclamation point usage:
          - Exclamation points are generally discouraged in technical writing
          - Various contexts may legitimize exclamation usage (warnings, commands, etc.)
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        
        # Fallback analysis when nlp is not available
        if not nlp:
            for i, sentence in enumerate(sentences):
                # Apply basic guards for fallback analysis
                content_type = context.get('content_type', 'general')
                block_type = context.get('block_type', 'paragraph')
                domain = context.get('domain', 'general')
                
                # Skip if in contexts where exclamations are legitimate
                if content_type in ['creative', 'literary', 'narrative']:
                    continue
                if content_type == 'marketing':
                    continue
                if block_type in ['admonition', 'warning', 'caution', 'quote', 'blockquote', 'code_block', 'literal_block']:
                    continue
                if domain in ['safety', 'security']:
                    continue
                
                for match in re.finditer(r'!', sentence):
                    # Check for warning words in the sentence
                    sentence_lower = sentence.lower()
                    warning_words = ['warning', 'caution', 'danger', 'important', 'note', 'alert', 'attention', 'stop']
                    if any(word in sentence_lower for word in warning_words):
                        continue  # Skip warnings
                    
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Avoid exclamation points in technical writing to maintain a professional tone.",
                        suggestions=["Replace the exclamation point with a period."],
                        severity='medium',
                        text=text,
                        context=context,
                        evidence_score=0.8,  # Default evidence for fallback analysis
                        span=(match.start(), match.end()),
                        flagged_text=match.group(0)
                    ))
            return errors

        try:
            doc = nlp(text)
            for i, sent in enumerate(doc.sents):
                for token in sent:
                    if token.text == '!':
                        evidence_score = self._calculate_exclamation_evidence(token, sent, text, context)
                        
                        # Only flag if evidence suggests it's worth evaluating
                        if evidence_score > 0.1:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=self._get_contextual_exclamation_message(token, evidence_score, context),
                                suggestions=self._generate_smart_exclamation_suggestions(token, evidence_score, sent, context),
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
                message=f"Rule ExclamationPointsRule failed with error: {e}",
                suggestions=["This may be a bug in the rule. Please report it."],
                severity='low',
                text=text,
                context=context,
                evidence_score=0.0  # No evidence when analysis fails
            ))
        return errors

    # === EVIDENCE CALCULATION ===

    def _calculate_exclamation_evidence(self, exclamation_token: 'Token', sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) that exclamation point usage is incorrect.
        
        Higher scores indicate stronger evidence of an error.
        Lower scores indicate acceptable usage or ambiguous cases.
        """
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        # Apply surgical guards FIRST to eliminate false positives
        if self._apply_zero_false_positive_guards_punctuation(exclamation_token, context):
            return 0.0
        
        # Creative content commonly uses exclamations for dramatic effect
        content_type = context.get('content_type', 'general')
        if content_type in ['creative', 'literary', 'narrative']:
            return 0.0
        
        # Marketing content uses exclamations for emphasis and engagement
        if content_type == 'marketing':
            return 0.0
        
        # Safety and security domains legitimately use exclamations for warnings
        domain = context.get('domain', 'general')
        if domain in ['safety', 'security']:
            return 0.0
        
        # Warning and alert blocks legitimately use exclamations
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['admonition', 'warning', 'caution']:
            return 0.0
        
        # Quotes preserve original punctuation including exclamations
        if block_type in ['quote', 'blockquote']:
            return 0.0
        
        # Headings may use exclamations for emphasis (especially in marketing/creative contexts)
        if block_type in ['heading', 'title']:
            return 0.0
        
        # Check for warning/command words in the sentence
        sent_text = sent.text.lower()
        warning_words = {'warning', 'caution', 'danger', 'important', 'note', 'alert', 'attention', 'stop'}
        if any(word in sent_text for word in warning_words):
            return 0.0
        
        # Check for imperative commands which may legitimately use exclamations
        sent_root = None
        for token in sent:
            if token.dep_ == 'ROOT':
                sent_root = token
                break
        
        if sent_root and sent_root.pos_ == 'VERB':
            # Check if it's an imperative (no explicit subject)
            has_explicit_subject = any(t.dep_ in ['nsubj', 'nsubjpass'] for t in sent)
            if not has_explicit_subject:
                return 0.0  # Commands are legitimate
        
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        # Exclamation points are generally discouraged in technical writing
        evidence_score = 0.8  # Start with high evidence
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_exclamation(evidence_score, exclamation_token, sent)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_exclamation(evidence_score, exclamation_token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_exclamation(evidence_score, exclamation_token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_exclamation(evidence_score, exclamation_token, context)
        
        return max(0.0, min(1.0, evidence_score))

    def _apply_linguistic_clues_exclamation(self, evidence_score: float, exclamation_token: 'Token', sent: 'Span') -> float:
        """Apply SpaCy-based linguistic analysis clues for exclamation point usage."""
        
        token_sent_idx = exclamation_token.i - sent.start
        
        # Check for legitimate exclamation usage patterns
        if token_sent_idx > 0:
            # Check for imperative sentences (commands)
            sent_root = None
            for token in sent:
                if token.dep_ == 'ROOT':
                    sent_root = token
                    break
            
            if sent_root and sent_root.pos_ == 'VERB':
                # Check if it's an imperative (no subject)
                has_explicit_subject = any(t.dep_ in ['nsubj', 'nsubjpass'] for t in sent)
                if not has_explicit_subject:
                    evidence_score -= 0.3  # Commands may use exclamations
            
            # Check for warning/alert words
            warning_words = {'warning', 'caution', 'danger', 'important', 'note', 'alert', 'attention'}
            for token in sent:
                if token.text.lower() in warning_words:
                    evidence_score -= 0.4  # Warnings may justify exclamations
                    break
            
            # Check for expressing strong positive/negative sentiment
            prev_token = sent[token_sent_idx - 1]
            
            # Interjections often use exclamation points
            if prev_token.pos_ == 'INTJ':
                evidence_score -= 0.2
            
            # Adjectives expressing strong emotion
            strong_adjectives = {'excellent', 'amazing', 'terrible', 'awful', 'fantastic', 'horrible'}
            if prev_token.text.lower() in strong_adjectives:
                evidence_score -= 0.1
        
        # Check for multiple exclamation points (very informal)
        if token_sent_idx < len(sent) - 1:
            next_token = sent[token_sent_idx + 1]
            if next_token.text == '!':
                evidence_score += 0.3  # Multiple exclamations are very informal
        
        # Single word exclamations may be more acceptable
        if len(sent) <= 2:
            evidence_score -= 0.1
        
        return evidence_score

    def _apply_structural_clues_exclamation(self, evidence_score: float, exclamation_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply document structure-based clues for exclamation point usage."""
        
        block_type = context.get('block_type', 'paragraph')
        
        # Warnings and alerts may use exclamation points legitimately
        if block_type in ['admonition', 'warning', 'caution']:
            evidence_score -= 0.6
        
        # Headings may use exclamation points for emphasis
        elif block_type in ['heading', 'title']:
            evidence_score -= 0.2
        
        # Code comments may include exclamations
        elif block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.3
        
        # Lists may use exclamations inappropriately
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score += 0.1
        
        # Table content should be formal
        elif block_type in ['table_cell', 'table_header']:
            evidence_score += 0.2
        
        # Quotes may contain exclamations from original source
        elif block_type in ['quote', 'blockquote']:
            evidence_score -= 0.3
        
        # Dialogue content may use exclamations
        elif block_type in ['dialogue']:
            evidence_score -= 0.4
        
        return evidence_score

    def _apply_semantic_clues_exclamation(self, evidence_score: float, exclamation_token: 'Token', text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for exclamation point usage."""
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # Technical content should avoid exclamation points most strictly
        if content_type == 'technical':
            evidence_score += 0.15
        
        # Academic writing should be formal
        elif content_type == 'academic':
            evidence_score += 0.1
        
        # Legal writing must be formal
        elif content_type == 'legal':
            evidence_score += 0.15
        
        # Marketing content may be more expressive
        elif content_type == 'marketing':
            evidence_score -= 0.2
        
        # Creative writing uses exclamation points more freely
        elif content_type == 'creative':
            evidence_score -= 0.4
        
        # Procedural content should be clear but may include warnings
        elif content_type == 'procedural':
            evidence_score -= 0.05
        
        # Educational content may use exclamations for engagement
        elif content_type == 'educational':
            evidence_score -= 0.1
        
        # Domain-specific adjustments
        if domain in ['software', 'engineering']:
            evidence_score += 0.1  # More technical contexts
        elif domain in ['marketing', 'social_media']:
            evidence_score -= 0.2  # More expressive contexts
        elif domain in ['safety', 'security']:
            evidence_score -= 0.3  # Warnings may need emphasis
        elif domain in ['literature', 'journalism']:
            evidence_score -= 0.1  # More creative contexts
        
        # Audience considerations
        if audience in ['expert', 'developer']:
            evidence_score += 0.05  # Prefer professional tone
        elif audience in ['children', 'beginner']:
            evidence_score -= 0.1  # May benefit from engaging tone
        elif audience in ['general', 'consumer']:
            evidence_score -= 0.05  # Slightly more flexible
        
        return evidence_score

    def _apply_feedback_clues_exclamation(self, evidence_score: float, exclamation_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply clues learned from user feedback patterns for exclamation point usage."""
        
        feedback_patterns = self._get_cached_feedback_patterns_exclamation()
        
        # Get context around the exclamation point
        token_sent_idx = exclamation_token.i - exclamation_token.sent.start
        sent = exclamation_token.sent
        
        # Look for patterns in accepted/rejected exclamation usage
        if token_sent_idx > 0:
            prev_word = sent[token_sent_idx - 1].text.lower()
            
            # Words commonly accepted before exclamation points
            if prev_word in feedback_patterns.get('accepted_preceding_words', set()):
                evidence_score -= 0.3
            
            # Words commonly flagged before exclamation points
            elif prev_word in feedback_patterns.get('flagged_preceding_words', set()):
                evidence_score += 0.2
        
        # Check for sentence patterns
        sentence_words = [t.text.lower() for t in sent if not t.is_punct]
        
        # Common acceptable exclamation patterns
        acceptable_patterns = feedback_patterns.get('acceptable_sentence_patterns', set())
        for pattern in acceptable_patterns:
            if any(word in sentence_words for word in pattern.split()):
                evidence_score -= 0.2
                break
        
        # Context-specific patterns
        block_type = context.get('block_type', 'paragraph')
        block_patterns = feedback_patterns.get(f'{block_type}_exclamation_patterns', {})
        
        if 'accepted_rate' in block_patterns:
            acceptance_rate = block_patterns['accepted_rate']
            if acceptance_rate > 0.7:
                evidence_score -= 0.2  # High acceptance in this context
            elif acceptance_rate < 0.2:
                evidence_score += 0.2  # Low acceptance in this context
        
        return evidence_score

    def _get_cached_feedback_patterns_exclamation(self) -> Dict[str, Any]:
        """Load feedback patterns for exclamation point usage from cache or feedback analysis."""
        return {
            'accepted_preceding_words': {'warning', 'caution', 'danger', 'stop', 'attention', 'note', 'important'},
            'flagged_preceding_words': {'good', 'nice', 'great', 'thanks', 'hello', 'hi'},
            'acceptable_sentence_patterns': {
                'warning', 'caution danger', 'stop immediately', 'attention required',
                'important note', 'emergency', 'alert'
            },
            'paragraph_exclamation_patterns': {'accepted_rate': 0.1},
            'admonition_exclamation_patterns': {'accepted_rate': 0.8},
            'heading_exclamation_patterns': {'accepted_rate': 0.3},
            'code_block_exclamation_patterns': {'accepted_rate': 0.4},
        }

    # === SMART MESSAGING ===

    def _get_contextual_exclamation_message(self, exclamation_token: 'Token', evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for exclamation point usage."""
        
        content_type = context.get('content_type', 'general')
        block_type = context.get('block_type', 'paragraph')
        
        if evidence_score > 0.8:
            if content_type == 'technical':
                return "Avoid exclamation points in technical writing: they appear unprofessional and may undermine credibility."
            else:
                return "Exclamation point usage may be inappropriate: consider a more professional tone."
        elif evidence_score > 0.6:
            if block_type in ['admonition', 'warning']:
                return "Consider if exclamation point adds necessary emphasis: warnings can be effective without them."
            else:
                return "Consider removing exclamation point: periods often provide adequate sentence ending."
        elif evidence_score > 0.4:
            return "Exclamation point may affect professional tone: evaluate if emphasis is truly necessary."
        else:
            return "Review exclamation point usage for consistency with professional writing standards."

    def _generate_smart_exclamation_suggestions(self, exclamation_token: 'Token', evidence_score: float, sent: 'Span', context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for exclamation point usage."""
        
        suggestions = []
        token_sent_idx = exclamation_token.i - sent.start
        block_type = context.get('block_type', 'paragraph')
        content_type = context.get('content_type', 'general')
        
        # High evidence suggestions
        if evidence_score > 0.7:
            suggestions.append("Replace the exclamation point with a period for a more professional tone.")
            
            # Check if it's a command that could be rewritten
            if token_sent_idx > 0:
                sent_text = sent.text.lower()
                if any(word in sent_text for word in ['do', 'use', 'try', 'make', 'ensure']):
                    suggestions.append("Rewrite as a statement rather than a command to reduce emphasis.")
            
            suggestions.append("Strong word choice often provides better emphasis than punctuation.")
        
        # Medium evidence suggestions
        elif evidence_score > 0.4:
            if block_type in ['admonition', 'warning']:
                suggestions.append("Consider if the warning content itself provides sufficient emphasis.")
                suggestions.append("Use 'Important:' or 'Warning:' labels instead of exclamation points.")
            else:
                suggestions.append("Consider whether the exclamation point adds necessary meaning.")
                suggestions.append("Replace with a period unless strong emphasis is truly needed.")
        
        # Context-specific suggestions
        if content_type == 'technical':
            suggestions.append("Technical writing benefits from measured, professional tone.")
        elif content_type == 'academic':
            suggestions.append("Academic writing typically avoids exclamation points except in direct quotes.")
        elif content_type == 'marketing' and evidence_score > 0.6:
            suggestions.append("Even in marketing, excessive exclamation points can appear unprofessional.")
        elif block_type in ['code_block', 'literal_block']:
            suggestions.append("In code comments, clear explanations are better than emphatic punctuation.")
        
        # General guidance
        if len(suggestions) < 2:
            suggestions.append("Exclamation points should be used sparingly in professional writing.")
            suggestions.append("Consider whether the content itself conveys the intended emphasis.")
        
        return suggestions[:3]