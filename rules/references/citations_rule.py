"""
Citations and References Rule
Based on IBM Style Guide topic: "Citations and references"
"""
from typing import List, Dict, Any
from .base_references_rule import BaseReferencesRule
from .services.references_config_service import get_citation_config, ReferenceContext
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class CitationsRule(BaseReferencesRule):
    """
    Checks for incorrect formatting of citations and links, such as the
    use of "Click here" and incorrect capitalization of cited elements.
    """
    def __init__(self):
        super().__init__()
        self.config_service = get_citation_config()
    
    def _get_rule_type(self) -> str:
        return 'references_citations'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for citation and linking errors using configuration-based approach.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        ref_context = ReferenceContext(
            content_type=context.get('content_type', '') if context else '',
            domain=context.get('domain', '') if context else '',
            block_type=context.get('block_type', '') if context else '',
            has_citations=bool(context.get('has_citations', False)) if context else False
        )
        
        # Skip analysis if configured to do so
        if self.config_service.should_skip_analysis(ref_context):
            return errors
        
        # Find potential citation issues
        for i, sent in enumerate(doc.sents):
            # Rule 1: Problematic Link Text - use configuration patterns
            problematic_patterns = self.config_service.get_feedback_patterns().get('link_phrase_acceptance', {})
            
            for phrase in problematic_patterns.keys():
                pattern = r'\b' + re.escape(phrase) + r'\b'
                for match in re.finditer(pattern, sent.text, re.IGNORECASE):
                    citation_pattern = self.config_service.get_citation_pattern(phrase)
                    if citation_pattern:
                        # Create mock token for evidence calculation
                        mock_token = type('MockToken', (), {
                            'text': match.group(0),
                            'lemma_': match.group(0).lower(),
                            'pos_': 'VERB',
                            'ent_type_': '',
                            'like_url': False
                        })()
                        
                        evidence_score = self._calculate_citation_evidence(
                            mock_token, sent, text, context, issue_type='problematic_link'
                        )
                        
                        if evidence_score > 0.1:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=citation_pattern.message,
                                suggestions=citation_pattern.alternatives or self._generate_smart_suggestions_citation(match.group(0), context, evidence_score, 'problematic_link'),
                                severity=citation_pattern.severity if hasattr(citation_pattern, 'severity') else 'high',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=(sent.start_char + match.start(), sent.start_char + match.end()),
                                flagged_text=match.group(0)
                            ))

            # Rule 2: Incorrect Reference Capitalization - use configuration
            reference_indicators = self.config_service.get_reference_indicators()
            for token in sent:
                if self.config_service.is_reference_term(token.text):
                    # Check if this is in a reference context
                    sent_text_lower = sent.text.lower()
                    is_reference_context = any(indicator in sent_text_lower for indicator in reference_indicators)
                    
                    if is_reference_context and token.i + 1 < len(doc) and doc[token.i + 1].like_num:
                        evidence_score = self._calculate_citation_evidence(
                            token, sent, text, context, issue_type='reference_capitalization'
                        )
                        
                        if evidence_score > 0.1:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=self._get_contextual_message_citation(token.text, evidence_score, 'reference_capitalization'),
                                suggestions=self._generate_smart_suggestions_citation(token.text, context, evidence_score, 'reference_capitalization'),
                                severity='medium',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=(token.idx, token.idx + len(token.text)),
                                flagged_text=token.text
                            ))
        return errors
    
    def _calculate_citation_evidence(self, token, sentence, text: str, context: Dict[str, Any] = None, issue_type: str = 'general') -> float:
        """
        Calculate evidence score (0.0-1.0) for potential citation violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            token: The potential issue token/phrase
            sentence: Sentence containing the token
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            issue_type: Type of citation issue ('problematic_link', 'reference_capitalization')
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === ZERO FALSE POSITIVE GUARDS ===
        # CRITICAL: Apply rule-specific guards FIRST to eliminate common exceptions
        
        # Kill evidence immediately for contexts where this specific rule should never apply
        if context and context.get('block_type') in ['code_block', 'inline_code', 'literal_block']:
            return 0.0  # Code has its own rules
        
        # Don't flag recognized entities or proper nouns for this rule type
        if hasattr(token, 'ent_type_') and token.ent_type_ in ['PERSON', 'ORG', 'PRODUCT', 'EVENT', 'GPE']:
            return 0.0  # Proper names are not citation style errors
        
        # Don't flag technical identifiers, URLs, file paths
        if hasattr(token, 'like_url') and token.like_url:
            return 0.0
        if hasattr(token, 'text') and ('/' in token.text or '\\' in token.text):
            return 0.0
        
        # Citation-specific guards: Don't flag quoted examples
        if self._is_phrase_in_actual_quotes(token, sentence, context):
            return 0.0  # Quoted examples are not citation violations
        
        # Apply inherited zero false positive guards
        if self._apply_zero_false_positive_guards_references(token, context):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_citation_base_evidence_score(token, sentence, context, issue_type)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this token
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_references(evidence_score, token, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_references(evidence_score, token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_references(evidence_score, token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_citations(evidence_score, token, context, issue_type)
        
        # === STEP 6: CONFIGURATION-BASED ADJUSTMENTS ===
        ref_context = ReferenceContext(
            content_type=context.get('content_type', '') if context else '',
            block_type=context.get('block_type', '') if context else ''
        )
        evidence_score = self.config_service.calculate_context_adjusted_evidence(evidence_score, ref_context)
        
        # Issue-specific final adjustments (moderate increases to avoid evidence inflation)
        if issue_type == 'problematic_link':
            evidence_score += 0.1  # Link text issues are important but don't over-inflate
        elif issue_type == 'reference_capitalization':
            evidence_score += 0.05  # Capitalization issues important but context-dependent
        
        return max(0.0, min(1.0, evidence_score))
    
    def _get_citation_base_evidence_score(self, token, sentence, context: Dict[str, Any] = None, issue_type: str = 'general') -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Exact problematic pattern like "click here" → 0.9 (very specific)
        - Generic reference term like "Chapter" → 0.7 (specific pattern)
        - Partial pattern like "click" + context → 0.8 (pattern-based)
        """
        if not self._meets_basic_criteria_references(token):
            return 0.0
        
        if hasattr(token, 'text'):
            text = token.text.lower()
            
            # Problematic link patterns - exact match analysis
            if issue_type == 'problematic_link':
                if self._is_exact_violation_match_citations(token, text):
                    return 0.7  # Very specific, clear violation (reduced from 0.9)
                elif self._is_pattern_violation_citations(token, sentence, text):
                    return 0.6  # Pattern-based, moderate specificity (reduced from 0.8)
                else:
                    return 0.4  # Generic detection, needs more evidence (reduced from 0.6)
                    
            # Reference capitalization patterns - context-aware scoring
            elif issue_type == 'reference_capitalization':
                if self._is_exact_reference_violation(token, text):
                    return 0.6  # Clear reference terms (reduced from 0.8)
                elif self._is_likely_reference_term(token, sentence, text):
                    return 0.5  # Probable reference, moderate confidence (reduced from 0.7)
                else:
                    return 0.4  # Possible reference, needs more context (reduced from 0.6)
        
        return 0.5  # Default moderate evidence for other patterns
    
    def _get_contextual_message_citation(self, issue_text: str, evidence_score: float, issue_type: str) -> str:
        """
        Generate contextual error message based on evidence strength.
        """
        if issue_type == 'problematic_link':
            if evidence_score > 0.85:
                return f"Avoid using generic link text like '{issue_text}'. The link text should be meaningful."
            elif evidence_score > 0.6:
                return f"Consider making the link text '{issue_text}' more descriptive."
            else:
                return f"Link text '{issue_text}' could be more descriptive."
                
        elif issue_type == 'reference_capitalization':
            if evidence_score > 0.85:
                return f"Reference term '{issue_text}' should be lowercase in cross-references."
            elif evidence_score > 0.6:
                return f"Consider using lowercase for the reference term '{issue_text}'."
            else:
                return f"Reference term '{issue_text}' may need lowercase formatting."
        
        return f"Citation issue detected with '{issue_text}'."
    
    def _generate_smart_suggestions_citation(self, issue_text: str, context: Dict[str, Any] = None, evidence_score: float = 0.5, issue_type: str = 'general') -> List[str]:
        """
        Generate evidence-aware suggestions for citation issues.
        """
        suggestions = []
        
        if issue_type == 'problematic_link':
            if evidence_score > 0.8:
                suggestions.append("Rewrite the link to describe its destination, e.g., 'For more information, see the Installation Guide.'")
                suggestions.append("Use descriptive link text that explains what the user will find.")
            elif evidence_score > 0.6:
                suggestions.append("Consider making the link text more descriptive.")
                suggestions.append("Link text should indicate the destination or purpose.")
            else:
                suggestions.append("This link text could be more specific.")
                
        elif issue_type == 'reference_capitalization':
            if evidence_score > 0.8:
                suggestions.append(f"Use lowercase for the reference type, e.g., 'see {issue_text.lower()} 9'.")
                suggestions.append("References to document parts should be lowercase in cross-references.")
            elif evidence_score > 0.6:
                suggestions.append(f"Consider using lowercase: '{issue_text.lower()}'.")
            else:
                suggestions.append(f"Reference formatting could be improved: '{issue_text.lower()}'.")
        
        return suggestions[:3]
    
    def _is_phrase_in_actual_quotes(self, token, sentence, context: Dict[str, Any] = None) -> bool:
        """
        Surgical check: Is the phrase actually within quotation marks?
        Only returns True for genuine quoted content, not incidental apostrophes.
        """
        if not hasattr(token, 'text') or not hasattr(sentence, 'text'):
            return False
        
        phrase = token.text
        sent_text = sentence.text
        
        # Look for quote pairs that actually enclose the phrase
        import re
        
        # Find all potential quote pairs
        quote_patterns = [
            (r'"([^"]*)"', '"'),  # Double quotes
            (r"'([^']*)'", "'"),  # Single quotes
            (r'`([^`]*)`', '`')   # Backticks
        ]
        
        for pattern, quote_char in quote_patterns:
            matches = re.finditer(pattern, sent_text)
            for match in matches:
                quoted_content = match.group(1)
                if phrase.lower() in quoted_content.lower():
                    return True
        
        return False
    
    def _is_exact_violation_match_citations(self, token, text: str) -> bool:
        """
        Check if token represents an exact citation violation match.
        """
        # Only the most problematic exact phrases
        exact_violations = {
            'click here', 'see here', 'go here', 'this link'
        }
        return text in exact_violations
    
    def _is_pattern_violation_citations(self, token, sentence, text: str) -> bool:
        """
        Check if token is part of a problematic citation pattern.
        Be conservative - only flag clearly problematic patterns.
        """
        if not hasattr(sentence, 'text'):
            return False
            
        sent_text = sentence.text.lower()
        
        # Check for imperative + here patterns (but exclude acceptable patterns)
        if text in ['click', 'see', 'go'] and 'here' in sent_text:
            # Exclude acceptable patterns like "see here in the documentation"
            if not any(acceptable in sent_text for acceptable in ['documentation', 'manual', 'guide', 'section']):
                return True
        
        # Check for vague demonstrative patterns only
        if text in ['this', 'that'] and 'link' in sent_text:
            return True
        
        return False
    
    def _is_exact_reference_violation(self, token, text: str) -> bool:
        """
        Check if token represents an exact reference capitalization violation.
        """
        # These should be lowercase in cross-references
        reference_terms = {
            'chapter', 'appendix', 'figure', 'table', 'section', 
            'page', 'part', 'volume', 'book'
        }
        
        # Check if the token is capitalized when it shouldn't be
        if hasattr(token, 'text') and token.text[0].isupper():
            return text in reference_terms
        
        return False
    
    def _is_likely_reference_term(self, token, sentence, text: str) -> bool:
        """
        Check if token is likely a reference term based on context.
        """
        if not hasattr(sentence, 'text'):
            return False
            
        sent_text = sentence.text.lower()
        
        # Check for reference context indicators
        reference_indicators = ['see', 'refer to', 'shown in', 'described in', 'listed in']
        
        # Check if any reference indicators appear before this token
        reference_terms = {
            'chapter', 'appendix', 'figure', 'table', 'section', 
            'page', 'part', 'volume', 'book'
        }
        
        for indicator in reference_indicators:
            if indicator in sent_text and text in reference_terms:
                return True
        
        return False
    
    def _apply_feedback_clues_citations(self, evidence_score: float, token, context: Dict[str, Any] = None, issue_type: str = 'general') -> float:
        """
        Apply clues learned from user feedback patterns specific to citations.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_citations()
        
        if not hasattr(token, 'text'):
            return evidence_score
        
        text = token.text.lower()
        
        # Consistently Accepted Terms
        if text in feedback_patterns.get('accepted_terms', set()):
            evidence_score -= 0.5  # Users consistently accept this
        
        # Consistently Rejected Suggestions
        if text in feedback_patterns.get('rejected_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: Short link phrases in different contexts
        if issue_type == 'problematic_link':
            link_acceptance = feedback_patterns.get('link_phrase_acceptance', {})
            acceptance_rate = link_acceptance.get(text, 0.5)
            if acceptance_rate > 0.8:
                evidence_score -= 0.4  # High acceptance, likely valid in some contexts
            elif acceptance_rate < 0.2:
                evidence_score += 0.2  # Low acceptance, strong violation
        
        # Pattern: Reference terms in technical documentation
        elif issue_type == 'reference_capitalization':
            content_type = context.get('content_type', 'general') if context else 'general'
            reference_patterns = feedback_patterns.get(f'{content_type}_reference_acceptance', {})
            
            acceptance_rate = reference_patterns.get(text, 0.5)
            if acceptance_rate > 0.7:
                evidence_score -= 0.3  # Accepted in this content type
            elif acceptance_rate < 0.3:
                evidence_score += 0.2  # Consistently flagged in this content type
        
        # Pattern: Context-specific acceptance
        block_type = context.get('block_type', 'paragraph') if context else 'paragraph'
        context_patterns = feedback_patterns.get(f'{block_type}_citation_patterns', {})
        
        if text in context_patterns.get('accepted', set()):
            evidence_score -= 0.2
        elif text in context_patterns.get('flagged', set()):
            evidence_score += 0.2
        
        # Pattern: Frequency-based adjustment for citations
        term_frequency = feedback_patterns.get('citation_term_frequencies', {}).get(text, 0)
        if term_frequency > 10:  # Commonly seen term
            acceptance_rate = feedback_patterns.get('citation_term_acceptance', {}).get(text, 0.5)
            if acceptance_rate > 0.7:
                evidence_score -= 0.3  # Frequently accepted
            elif acceptance_rate < 0.3:
                evidence_score += 0.2  # Frequently rejected
        
        return evidence_score
    
    def _get_cached_feedback_patterns_citations(self) -> Dict[str, Any]:
        """
        Load feedback patterns from configuration service.
        """
        return self.config_service.get_feedback_patterns()
