"""
Conversational Style Rule
Based on IBM Style Guide topic: "Conversational style"
Uses YAML-based vocabulary management for maintainable, updateable vocabularies.
"""
from typing import List, Dict, Any
from .base_audience_rule import BaseAudienceRule
from .services.vocabulary_service import get_conversational_vocabulary, DomainContext
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ConversationalStyleRule(BaseAudienceRule):
    """
    PRODUCTION-GRADE: Checks for language that is overly formal or complex.
    
    Features:
    - YAML-based vocabulary management
    - Dynamic morphological variant generation
    - Context-aware evidence calculation
    - Zero false positive guards
    """
    
    def __init__(self):
        super().__init__()
        self.vocabulary_service = get_conversational_vocabulary()
    
    def _get_rule_type(self) -> str:
        return 'conversational_style'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for conversational style. Flags overly-formal
        word choices with a nuanced evidence score based on linguistic,
        structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        doc = nlp(text)

        # PRODUCTION-GRADE: Use YAML-based vocabulary service
        # Create domain context for vocabulary service
        domain_context = DomainContext(
            content_type=context.get('content_type', ''),
            domain=context.get('domain', ''),
            audience=context.get('audience', ''),
            block_type=context.get('block_type', '')
        )

        for i, sent in enumerate(doc.sents):
            for token in sent:
                lemma_lower = getattr(token, 'lemma_', '').lower()
                
                # Check if this formal word is in our YAML vocabulary
                vocab_entry = self.vocabulary_service.get_vocabulary_entry(lemma_lower)
                if vocab_entry:
                    evidence_score = self._calculate_conversational_evidence(
                        token=token, sentence=sent, text=text, context=context or {}
                    )
                    if evidence_score > 0.1:
                        # Get conversational alternative from vocabulary
                        conversational_alt = vocab_entry.context_adjustments.get('conversational_alternative', 'simpler alternative')
                        
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=self._get_contextual_conversational_message(
                                formal=token.text, 
                                simple=conversational_alt, 
                                ev=evidence_score, 
                                context=context or {},
                                vocab_entry=vocab_entry
                            ),
                            suggestions=self._generate_smart_conversational_suggestions(
                                formal=token.text, 
                                simple=conversational_alt, 
                                ev=evidence_score, 
                                sentence=sent, 
                                context=context or {},
                                vocab_entry=vocab_entry
                            ),
                            severity='low' if evidence_score < 0.7 else 'medium',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text,
                            vocab_entry=vocab_entry
                        ))
        return errors

    # === EVIDENCE-BASED CALCULATION ===

    def _calculate_conversational_evidence(self, token, sentence, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence (0.0-1.0) that a word is too formal for a conversational style."""
        
        # === ZERO FALSE POSITIVE GUARDS FIRST ===
        # Apply common audience guards
        if self._apply_zero_false_positive_guards_audience(token, context):
            return 0.0
        
        evidence: float = 0.6  # base for formal term present

        # Linguistic clues (micro)
        evidence = self._apply_linguistic_clues_conversational(evidence, token, sentence)

        # Structural clues (meso)
        evidence = self._apply_structural_clues_conversational(evidence, context)

        # Semantic clues (macro)
        evidence = self._apply_semantic_clues_conversational(evidence, sentence, text, context)

        # Feedback clues (learning)
        evidence = self._apply_feedback_clues_conversational(evidence, token, context)

        return max(0.0, min(1.0, evidence))

    # === CLUES ===

    def _apply_linguistic_clues_conversational(self, evidence: float, token, sentence) -> float:
        sent_text = sentence.text
        sent_lower = sent_text.lower()

        # Long sentences benefit more from simplification
        token_count = len([t for t in sentence if not getattr(t, 'is_space', False)])
        if token_count > 25:
            evidence += 0.1
        if token_count > 40:
            evidence += 0.05

        # Contractions already present → tone is conversational; reduce evidence
        if any("'" in t.text for t in sentence if getattr(t, 'pos_', '') == 'AUX'):
            evidence -= 0.05

        # Phrasal verbosity patterns increase evidence
        if any(p in sent_lower for p in {"in order to", "with regard to", "for the purpose of"}):
            evidence += 0.1

        # Quoted text (reported speech/UI labels) → reduce
        if '"' in sent_text or "'" in sent_text:
            evidence -= 0.05

        return evidence

    def _apply_structural_clues_conversational(self, evidence: float, context: Dict[str, Any]) -> float:
        block_type = (context or {}).get('block_type', 'paragraph')
        if block_type in {'code_block', 'literal_block'}:
            return 0.0  # Code blocks should not flag conversational style issues
        if block_type == 'inline_code':
            return 0.0  # Inline code should not flag conversational style issues
        if block_type in {'table_cell', 'table_header'}:
            evidence -= 0.05
        if block_type in {'heading', 'title'}:
            evidence -= 0.05  # headings can be concise but not necessarily conversational
        return evidence

    def _apply_semantic_clues_conversational(self, evidence: float, sentence, text: str, context: Dict[str, Any]) -> float:
        content_type = (context or {}).get('content_type', 'general')
        domain = (context or {}).get('domain', 'general')
        audience = (context or {}).get('audience', 'general')

        # Encourage conversational tone more in marketing, tutorials, UI copy
        if content_type in {'marketing', 'tutorial', 'procedural'}:
            evidence += 0.1
        if content_type in {'api', 'technical'}:
            # Technical content for experts should be more permissive
            if audience in {'expert', 'developer'}:
                evidence -= 0.2  # Much more permissive for technical experts
            else:
                evidence += 0.05  # still beneficial for general technical content
        if content_type in {'legal', 'academic'}:
            evidence -= 0.6  # PRODUCTION FIX: formal tone is fully appropriate in legal/academic contexts

        if audience in {'beginner', 'general', 'user'}:
            evidence += 0.05
        elif audience in {'expert', 'developer'}:
            evidence -= 0.1  # Experts more comfortable with formal terms
            
        if domain in {'legal', 'finance'}:
            evidence -= 0.05

        return evidence

    def _apply_feedback_clues_conversational(self, evidence: float, token, context: Dict[str, Any]) -> float:
        patterns = self._get_cached_feedback_patterns_conversational()
        t_lower = getattr(token, 'lemma_', '').lower()

        if t_lower in patterns.get('accepted_formal_terms', set()):
            evidence -= 0.2
        if t_lower in patterns.get('often_flagged_formal_terms', set()):
            evidence += 0.1

        ctype = (context or {}).get('content_type', 'general')
        pc = patterns.get(f'{ctype}_patterns', {})
        if t_lower in pc.get('accepted', set()):
            evidence -= 0.1
        if t_lower in pc.get('flagged', set()):
            evidence += 0.1

        return evidence

    def _get_cached_feedback_patterns_conversational(self) -> Dict[str, Any]:
        return {
            'accepted_formal_terms': set(),
            'often_flagged_formal_terms': {'utilize', 'facilitate'},
            'marketing_patterns': {
                'accepted': set(),
                'flagged': {'utilize', 'commence'}
            },
            'technical_patterns': {
                'accepted': {'implement'},
                'flagged': {'utilize'}
            }
        }

    # === SMART MESSAGING ===

    def _get_contextual_conversational_message(self, formal: str, simple: str, ev: float, context: Dict[str, Any], vocab_entry=None) -> str:
        """PRODUCTION-GRADE: Generate context-aware messages using vocabulary metadata."""
        category = vocab_entry.category if vocab_entry else 'formal'
        
        if ev > 0.8:
            if category == 'overused_formal':
                return f"'{formal}' is overused business language. Use '{simple}' for better clarity."
            elif category == 'legal_formal':
                return f"'{formal}' sounds too legal/formal here. Consider '{simple}' instead."
            else:
                return f"'{formal}' sounds overly formal here. Prefer a conversational alternative like '{simple}'."
        if ev > 0.6:
            return f"Consider a simpler alternative to '{formal}', such as '{simple}'."
        return f"A simpler word than '{formal}' (e.g., '{simple}') can improve conversational tone."

    def _generate_smart_conversational_suggestions(self, formal: str, simple: str, ev: float, sentence, context: Dict[str, Any], vocab_entry=None) -> List[str]:
        """PRODUCTION-GRADE: Generate smart suggestions using vocabulary metadata."""
        suggestions: List[str] = []
        category = vocab_entry.category if vocab_entry else 'formal'
        
        suggestions.append(f"Replace '{formal}' with '{simple}' for a more conversational tone.")
        
        # Category-specific suggestions
        if category == 'overused_formal':
            suggestions.append("This word is commonly overused in business writing. Simple alternatives are more effective.")
        elif category == 'legal_formal':
            suggestions.append("Legal terminology can confuse general audiences. Use everyday language instead.")
        elif category == 'academic_formal':
            suggestions.append("Academic language may not suit conversational content. Consider simpler phrasing.")
        
        # Context-aware suggestions
        content_type = context.get('content_type', '')
        if content_type == 'tutorial':
            suggestions.append("Keep tutorial language simple and accessible for all skill levels.")
        elif content_type == 'documentation':
            suggestions.append("Use plain language to make documentation more user-friendly.")
        
        # Evidence-based suggestions
        if ev > 0.8:
            suggestions.append("This formal language may alienate readers seeking conversational content.")
        
        # Streamline common verbose phrases
        if 'in order to' in sentence.text.lower():
            suggestions.append("Shorten 'in order to' to 'to'.")
        # General guidance
        suggestions.append("Favor shorter, direct words to keep a conversational tone.")
        return suggestions[:3]
