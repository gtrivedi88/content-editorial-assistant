"""
Global Audiences Rule
Based on IBM Style Guide topic: "Global audiences"
Uses YAML-based vocabulary management for maintainable, updateable patterns.
"""
from typing import List, Dict, Any
from .base_audience_rule import BaseAudienceRule
from .services.vocabulary_service import get_global_patterns, DomainContext

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class GlobalAudiencesRule(BaseAudienceRule):
    """
    PRODUCTION-GRADE: Checks for constructs difficult for global audiences.
    
    Features:
    - YAML-based pattern management
    - Context-aware negative construction detection
    - Configurable sentence length thresholds
    - Dynamic evidence calculation
    """
    
    def __init__(self):
        super().__init__()
        self.vocabulary_service = get_global_patterns()
    
    def _get_rule_type(self) -> str:
        return 'global_audiences'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for global audiences. Computes nuanced evidence
        scores for:
          - Negative constructions that can confuse non-native readers
          - Excessive sentence length that hinders comprehension
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        doc = nlp(text)
        for i, sent in enumerate(doc.sents):
            # --- Evidence-based: Negative constructions ---
            for token in sent:
                if token.dep_ == 'neg':
                    head = token.head
                    evidence_score = self._calculate_negative_construction_evidence(
                        neg_token=token, head=head, sentence=sent, text=text, context=context or {}
                    )
                    if evidence_score > 0.1:
                        # PRODUCTION FIX: Better flagged text construction for contractions
                        acomp = next((c for c in head.children if c.dep_ == 'acomp'), None)
                        span_start = min(token.idx, (acomp.idx if acomp else head.idx))
                        span_end = (acomp.idx + len(acomp.text)) if acomp else (head.idx + len(head.text))
                        
                        # Handle contractions properly - flag the full word, not just "n't"
                        if token.text == "n't" and token.idx > 0:
                            # Find the contraction start (e.g., "Don't", "can't")
                            full_word_start = token.idx
                            sent_start = sent.start_char
                            text_pos = token.idx - sent_start
                            
                            while text_pos > 0 and sent.text[text_pos - 1].isalpha():
                                text_pos -= 1
                                full_word_start -= 1
                            
                            contraction = sent.text[text_pos:token.idx - sent_start + len(token.text)]
                            flagged_text = contraction
                        else:
                            flagged_text = f"{token.text} {(acomp.text if acomp else head.text)}"
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=self._get_contextual_negative_message(flagged_text, evidence_score, context or {}),
                            suggestions=self._generate_smart_negative_suggestions(flagged_text, evidence_score, sent, context or {}),
                            severity='low' if evidence_score < 0.7 else 'medium',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(span_start, span_end),
                            flagged_text=flagged_text
                        ))

            # --- Evidence-based: Sentence length ---
            evidence_len = self._calculate_sentence_length_evidence(sent, text, context or {})
            if evidence_len > 0.1:
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message=self._get_contextual_length_message(len([t for t in sent if not t.is_space]), evidence_len, context or {}),
                    suggestions=self._generate_smart_length_suggestions(sent, evidence_len, context or {}),
                    severity='low' if evidence_len < 0.7 else 'medium',
                    text=text,
                    context=context,
                    evidence_score=evidence_len,
                    span=(sent.start_char, sent.end_char),
                    flagged_text=sent.text
                ))
        return errors

    # === Evidence calculation: Negative constructions ===

    def _calculate_negative_construction_evidence(self, neg_token, head, sentence, text: str, context: Dict[str, Any]) -> float:
        evidence: float = 0.55  # base for presence of explicit negation

        # === NARRATIVE/BLOG CONTENT CLUE (RELAX FORMAL RULES) ===
        # Detect narrative/blog writing style and significantly reduce evidence
        if self._is_narrative_or_blog_content(text, context):
            evidence -= 0.35  # Major reduction for narrative/blog content
            # In narrative/blog content, negative constructions ("wasn't", "didn't") are 
            # natural and appropriate for conversational storytelling tone

        sent_lower = sentence.text.lower()

        # Linguistic: problematic complements and patterns
        acomp = next((c for c in head.children if c.dep_ == 'acomp'), None)
        problematic_acomps = {'different', 'unusual', 'dissimilar', 'impossible', 'unsupported', 'incorrect'}
        if acomp and acomp.lemma_.lower() in problematic_acomps:
            evidence += 0.15

        # Common negative patterns that hinder clarity
        negative_phrases = ['cannot', "can't", 'do not', "don't", 'should not', "shouldn't", 'not able to']
        if any(p in sent_lower for p in negative_phrases):
            evidence += 0.1

        # Double negation penalty
        if sum(1 for t in sentence if t.dep_ == 'neg') >= 2:
            evidence += 0.2

        # Long sentence amplifies the impact
        token_count = len([t for t in sentence if not t.is_space])
        if token_count > 25:
            evidence += 0.1

        # Structural clues
        evidence = self._apply_structural_clues_global(evidence, context)

        # Semantic clues
        evidence = self._apply_semantic_clues_global(evidence, sentence, text, context)

        # Feedback clues
        evidence = self._apply_feedback_clues_global(evidence, sentence, context)

        return max(0.0, min(1.0, evidence))

    def _is_narrative_or_blog_content(self, text: str, context: Dict[str, Any]) -> bool:
        """
        Detect if content is narrative/blog style using enhanced ContextAnalyzer.
        
        Looks for blog/narrative indicators like:
        - Frequent first-person pronouns ("we", "our", "I")  
        - Contractions ("we're", "it's", "wasn't")
        - Rhetorical questions
        - Informal sentence structure
        - Blog-specific phrases ("Why we switched", "Our journey")
        
        Args:
            text: The document text to analyze
            context: Document context information
            
        Returns:
            bool: True if content appears to be narrative/blog style
        """
        if not text:
            return False
            
        # Import ContextAnalyzer to leverage enhanced narrative detection
        try:
            from validation.confidence.context_analyzer import ContextAnalyzer
            analyzer = ContextAnalyzer()
            
            # Use enhanced content type detection  
            content_result = analyzer.detect_content_type(text, context)
            
            # Check if identified as narrative with reasonable confidence
            if (content_result.content_type.value == 'narrative' and 
                content_result.confidence > 0.4):
                return True
            
            # Additional check for blog-specific patterns even if not classified as narrative
            # Look for strong blog indicators in the text
            text_lower = text.lower()
            blog_strong_indicators = [
                'why we', 'how we', 'what we', 'when we', 'we switched', 
                'we decided', 'our journey', 'our experience', 'our story',
                'we learned', 'we discovered', 'we realized'
            ]
            
            strong_indicator_count = sum(1 for indicator in blog_strong_indicators 
                                       if indicator in text_lower)
            
            if strong_indicator_count >= 2:  # Multiple strong blog indicators
                return True
                
            # Check for high first-person pronoun density (blog characteristic)
            words = text_lower.split()
            if len(words) > 20:  # Only for substantial text
                first_person_count = sum(1 for word in words 
                                       if word in ['i', 'we', 'my', 'our', 'me', 'us'])
                first_person_ratio = first_person_count / len(words)
                
                # More than 3% first-person pronouns suggests blog/narrative
                if first_person_ratio > 0.03:
                    return True
                    
        except ImportError:
            # Fallback to simple pattern matching if ContextAnalyzer unavailable
            text_lower = text.lower()
            
            # Simple blog indicators
            simple_indicators = ['why we', 'we switched', 'our journey', 'we decided']
            if any(indicator in text_lower for indicator in simple_indicators):
                return True
        
        return False

    # === Evidence calculation: Sentence length ===

    def _calculate_sentence_length_evidence(self, sentence, text: str, context: Dict[str, Any]) -> float:
        tokens = [t for t in sentence if not t.is_space]
        length = len(tokens)
        if length <= 32:
            return 0.0

        # Base evidence scales with overage beyond 32 words
        over = length - 32
        evidence: float = min(1.0, 0.4 + min(0.4, over / 40.0))

        # Clause complexity increases evidence
        clause_factor = self._estimate_clause_complexity(sentence)
        evidence += min(0.2, clause_factor)

        # Structural and semantic adjustments
        evidence = self._apply_structural_clues_global(evidence, context)
        evidence = self._apply_semantic_clues_global(evidence, sentence, text, context)
        evidence = self._apply_feedback_clues_global(evidence, sentence, context)

        return max(0.0, min(1.0, evidence))

    def _estimate_clause_complexity(self, sentence) -> float:
        # Approximate complexity via punctuation and conjunctions
        commas = sum(1 for t in sentence if t.text == ',')
        semicolons = sum(1 for t in sentence if t.text == ';')
        and_ors = sum(1 for t in sentence if t.lemma_.lower() in {'and', 'or'} and t.dep_ == 'cc')
        subords = sum(1 for t in sentence if t.dep_ == 'mark')
        return 0.04 * commas + 0.06 * semicolons + 0.05 * and_ors + 0.05 * subords

    # === Shared structural/semantic/feedback clues for this rule ===

    def _apply_structural_clues_global(self, evidence: float, context: Dict[str, Any]) -> float:
        block_type = (context or {}).get('block_type', 'paragraph')
        if block_type in {'code_block', 'literal_block'}:
            return 0.0  # Code blocks should not be flagged for global audience issues
        if block_type == 'inline_code':
            return 0.0  # Inline code should not be flagged
        if block_type in {'table_cell', 'table_header'}:
            evidence -= 0.1
        if block_type in {'heading', 'title'}:
            evidence -= 0.05
        if block_type == 'admonition':
            admon = (context or {}).get('admonition_type', '').upper()
            if admon in {'WARNING', 'CAUTION', 'IMPORTANT'}:
                evidence -= 0.05  # Severity may justify clarity over tone
        return evidence

    def _apply_semantic_clues_global(self, evidence: float, sentence, text: str, context: Dict[str, Any]) -> float:
        content_type = (context or {}).get('content_type', 'general')
        domain = (context or {}).get('domain', 'general')
        audience = (context or {}).get('audience', 'general')

        # PRODUCTION FIX: More nuanced technical context handling
        # Technical warnings and API documentation may appropriately use negative constructions
        sent_text = sentence.text.lower()
        if (content_type == 'technical' and 
            any(word in sent_text for word in ['deprecated', 'warning', 'error', 'caution', 'avoid'])):
            evidence -= 0.5  # PRODUCTION FIX: Technical warnings appropriately use negative constructions
        elif content_type in {'marketing', 'procedural', 'tutorial'}:
            evidence += 0.08
        elif content_type in {'legal', 'academic'}:
            evidence -= 0.1

        if audience in {'beginner', 'general', 'user'}:
            evidence += 0.07
        elif audience in {'developer', 'expert'} and content_type == 'technical':
            evidence -= 0.1  # Developers can handle more complex constructions
            
        if domain in {'legal', 'finance'}:
            evidence -= 0.05

        return evidence

    def _apply_feedback_clues_global(self, evidence: float, sentence, context: Dict[str, Any]) -> float:
        patterns = self._get_cached_feedback_patterns_global()
        sent_lower = sentence.text.lower()
        if any(p in sent_lower for p in patterns.get('accepted_phrases', set())):
            evidence -= 0.1
        if any(p in sent_lower for p in patterns.get('flagged_phrases', set())):
            evidence += 0.1
        return evidence

    def _get_cached_feedback_patterns_global(self) -> Dict[str, Any]:
        """PRODUCTION-GRADE: Get feedback patterns from YAML configuration."""
        return self.vocabulary_service.get_feedback_patterns()

    # === Smart messaging & suggestions ===

    def _get_contextual_negative_message(self, flagged_text: str, ev: float, context: Dict[str, Any]) -> str:
        if ev > 0.8:
            return f"Negative construction ('{flagged_text}') may be hard for global audiences. Prefer positive phrasing."
        if ev > 0.5:
            return f"Consider rewriting '{flagged_text}' as a positive statement for clarity."
        return f"Positive phrasing instead of '{flagged_text}' can improve comprehension for global audiences."

    def _generate_smart_negative_suggestions(self, flagged_text: str, ev: float, sentence, context: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        suggestions.append("Rewrite negatively phrased statements as positive requirements or capabilities.")
        suggestions.append("Replace 'cannot/should not' with positive alternatives that specify allowed behavior.")
        if any(w in sentence.text.lower() for w in ['different', 'unusual', 'dissimilar']):
            suggestions.append("Prefer positive comparisons (e.g., 'similar', 'the same as').")
        return suggestions[:3]

    def _get_contextual_length_message(self, length: int, ev: float, context: Dict[str, Any]) -> str:
        if ev > 0.8:
            return f"Very long sentence ({length} words) may hinder global comprehension. Split into shorter sentences."
        if ev > 0.5:
            return f"Long sentence ({length} words). Consider breaking it up for clarity."
        return f"Consider shortening this sentence ({length} words) to improve readability for global audiences."

    def _generate_smart_length_suggestions(self, sentence, ev: float, context: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        suggestions.append("Split complex ideas into separate sentences with a single action each.")
        suggestions.append("Reduce nested clauses and remove non-essential details.")
        suggestions.append("Prefer simple connectors and bullet lists for multi-step ideas.")
        return suggestions[:3]
