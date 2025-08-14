"""
Semicolons Rule - Evidence-Based Analysis
Based on IBM Style Guide topic: "Semicolons"

**UPDATED** with evidence-based scoring for nuanced semicolon usage analysis.
"""
import re
from typing import List, Dict, Any, Optional
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens import Doc, Token, Span
except ImportError:
    Doc = None
    Token = None
    Span = None

class SemicolonsRule(BasePunctuationRule):
    """
    Checks for semicolon usage using evidence-based analysis:
    - Discourages semicolons in technical writing
    - Considers context and legitimate uses
    Enhanced with dependency parsing and contextual awareness.
    """
    def _get_rule_type(self) -> str:
        return 'semicolons'

    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for semicolon usage:
        - Discourages semicolons in technical writing
        - Considers legitimate uses and context
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        if not nlp:
            return self._fallback_semicolon_analysis(text, sentences, context)

        try:
            doc = nlp(text)
            for i, sent in enumerate(doc.sents):
                for token in sent:
                    if token.text == ';':
                        evidence_score = self._calculate_semicolon_evidence(token, sent, text, context)
                        
                        if evidence_score > 0.1:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=self._get_contextual_semicolon_message(evidence_score, context),
                                suggestions=self._generate_smart_semicolon_suggestions(token, evidence_score, context),
                                severity='low' if evidence_score < 0.7 else 'medium',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=(token.idx, token.idx + len(token.text)),
                                flagged_text=token.text
                            ))
        except Exception as e:
            errors.append(self._create_error(
                sentence=text,
                sentence_index=0,
                message="Semicolon analysis failed.",
                suggestions=["Review semicolon usage manually."],
                severity='low',
                text=text,
                context=context,
                evidence_score=0.0,  # No evidence when analysis fails
                span=(0, 0),
                flagged_text=""
            ))
            return errors
        
        return errors

    def _fallback_semicolon_analysis(self, text: str, sentences: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback analysis when nlp is not available."""
        errors = []
        
        # Apply context-aware guards first
        content_type = context.get('content_type', '')
        block_type = context.get('block_type', '')
        
        # Surgical zero false positive guards for fallback
        if content_type in ['creative', 'literary', 'narrative']:
            return errors
        if content_type == 'legal':
            return errors  # Legal content often uses semicolons appropriately
        if block_type in ['code_block', 'literal_block', 'inline_code', 'citation', 'bibliography', 'reference']:
            return errors
        
        for i, sent_text in enumerate(sentences):
            if ';' in sent_text:
                # Remove HTML entities to avoid false positives
                text_without_entities = re.sub(r'&[a-zA-Z0-9#]+;', '', sent_text)
                
                if ';' in text_without_entities:
                    # Check for complex list patterns (basic heuristic)
                    comma_count = sent_text.count(',')
                    semicolon_count = text_without_entities.count(';')
                    
                    # If many commas and few semicolons, likely a complex list
                    if comma_count >= 4 and semicolon_count <= 3:
                        continue  # Skip complex lists
                    
                    semicolon_pos = sent_text.find(';')
                    
                    # Context-aware evidence calculation
                    evidence_score = 0.6  # Default moderate evidence
                    
                    if content_type == 'technical':
                        evidence_score = 0.8  # Higher evidence for technical content
                    elif content_type == 'academic':
                        evidence_score = 0.4  # Lower evidence for academic content
                    
                    errors.append(self._create_error(
                        sentence=sent_text,
                        sentence_index=i,
                        message=self._get_contextual_semicolon_message(evidence_score, context),
                        suggestions=self._generate_basic_semicolon_suggestions(sent_text, semicolon_pos),
                        severity='low',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(semicolon_pos, semicolon_pos + 1),
                        flagged_text=";"
                    ))
        return errors

    # === EVIDENCE CALCULATION ===

    def _calculate_semicolon_evidence(self, semicolon_token: 'Token', sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) that a semicolon usage should be flagged.
        
        Higher scores indicate stronger evidence for recommending against use.
        Lower scores indicate potentially acceptable usage.
        """
        
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        # Apply semicolon-specific guards first to eliminate false positives
        
        content_type = context.get('content_type', '')
        block_type = context.get('block_type', '')
        
        # GUARD 1: Creative, literary, and narrative content allows semicolons for style
        if content_type in ['creative', 'literary', 'narrative']:
            return 0.0
        
        # GUARD 2: Legal content often uses semicolons appropriately
        if content_type == 'legal':
            return 0.0
        
        # GUARD 3: Citation and reference blocks
        if block_type in ['citation', 'bibliography', 'reference', 'footnote']:
            return 0.0
        
        # GUARD 4: Code blocks and technical content
        if block_type in ['code_block', 'literal_block', 'inline_code']:
            return 0.0
        
        # GUARD 5: Academic content in paragraph context (often uses formal language)
        if content_type == 'academic' and block_type == 'paragraph':
            return 0.0
        
        # GUARD 6: Check if this is a complex list with internal commas
        if self._is_complex_list_separator(semicolon_token, sent):
            return 0.0
        
        # GUARD 7: Check for HTML entities (contains semicolon but not punctuation)
        if self._is_html_entity_semicolon(semicolon_token, sent):
            return 0.0
        
        # Apply common structural guards
        if self._apply_zero_false_positive_guards_punctuation(semicolon_token, context):
            return 0.0
        
        # === EVIDENCE CALCULATION ===
        # Base evidence for semicolon usage
        evidence_score = 0.6  # Moderate base evidence
        
        # Apply rule-specific clue methods
        evidence_score = self._apply_linguistic_clues_semicolon(evidence_score, semicolon_token, sent)
        evidence_score = self._apply_structural_clues_semicolon(evidence_score, semicolon_token, context)
        evidence_score = self._apply_semantic_clues_semicolon(evidence_score, semicolon_token, text, context)
        evidence_score = self._apply_feedback_clues_semicolon(evidence_score, semicolon_token, context)
        
        return max(0.0, min(1.0, evidence_score))

    def _is_html_entity_semicolon(self, semicolon_token: 'Token', sent: 'Span') -> bool:
        """Check if this semicolon is part of an HTML entity."""
        try:
            # Get the text around the semicolon
            token_idx = semicolon_token.i - sent.start
            sent_text = sent.text
            
            # Find position of semicolon in sentence text
            semicolon_pos = sent_text.find(';', semicolon_token.idx - sent.start_char)
            if semicolon_pos == -1:
                return False
            
            # Look backwards for & character (HTML entity start)
            for i in range(semicolon_pos - 1, max(0, semicolon_pos - 10), -1):
                if sent_text[i] == '&':
                    # Check if this looks like an HTML entity
                    entity_text = sent_text[i:semicolon_pos + 1]
                    # Basic HTML entity pattern check
                    if len(entity_text) <= 8 and entity_text.startswith('&') and entity_text.endswith(';'):
                        # Check for valid entity characters (alphanumeric, #)
                        entity_content = entity_text[1:-1]
                        if entity_content and all(c.isalnum() or c == '#' for c in entity_content):
                            return True
                elif sent_text[i].isspace():
                    break  # Stop at whitespace
            
        except Exception:
            pass
        
        return False

    def _is_complex_list_separator(self, semicolon_token: 'Token', sent: 'Span') -> bool:
        """Check if semicolon is being used to separate complex list items."""
        try:
            # Get relative position in sentence
            token_idx = semicolon_token.i - sent.start
            
            # Look for commas before and after the semicolon
            commas_before = any(token.text == ',' for token in sent[:token_idx])
            commas_after = any(token.text == ',' for token in sent[token_idx + 1:])
            
            # Count total commas and semicolons for ratio analysis
            comma_count = sum(1 for token in sent if token.text == ',')
            semicolon_count = sum(1 for token in sent if token.text == ';')
            
            # Complex list indicators:
            # 1. Commas on both sides of semicolon
            # 2. High comma-to-semicolon ratio (suggests list structure)
            # 3. Presence of list-like patterns
            if commas_before and commas_after:
                if comma_count >= 2 * semicolon_count:  # At least 2 commas per semicolon
                    return True
            
            # Look for typical list patterns (names, titles, etc.)
            sent_text = sent.text.lower()
            list_indicators = ['ceo', 'cto', 'cfo', 'director', 'manager', 'president', 
                             'dr.', 'mr.', 'mrs.', 'ms.', 'prof.']
            
            if any(indicator in sent_text for indicator in list_indicators):
                if commas_before and semicolon_count >= 2:
                    return True
            
        except Exception:
            pass
        
        return False

    # === SEMICOLON-SPECIFIC CLUE METHODS ===
    
    def _apply_linguistic_clues_semicolon(self, evidence_score: float, semicolon_token: 'Token', sent: 'Span') -> float:
        """Apply linguistic analysis clues for semicolons."""
        try:
            # Check the clauses around the semicolon
            token_idx = semicolon_token.i - sent.start
            
            # Analyze clause before semicolon
            clause_before = sent[:token_idx]
            clause_after = sent[token_idx + 1:]
            
            # Check for coordinating conjunctions that might suggest simple sentence structure
            coord_conjunctions = {'and', 'but', 'or', 'so', 'yet', 'for', 'nor'}
            
            # If clauses could be easily connected with "and" or "but", higher evidence
            if len(clause_before) > 0 and len(clause_after) > 0:
                # Look for transitional words after semicolon that suggest overcomplication
                transition_words = {'however', 'therefore', 'moreover', 'furthermore', 'nevertheless', 'consequently'}
                first_word_after = clause_after[0].text.lower() if clause_after else ''
                
                if first_word_after in transition_words:
                    evidence_score += 0.1  # Formal transitions might be overcomplicated
                
                # Check if clauses are short and could be simple sentences
                if len(clause_before) <= 5 and len(clause_after) <= 5:
                    evidence_score += 0.2  # Short clauses often don't need semicolons
            
            # Check for conjunctive adverbs that often accompany unnecessary semicolons
            conjunctive_adverbs = {'however', 'therefore', 'moreover', 'furthermore', 'nevertheless', 
                                 'consequently', 'meanwhile', 'otherwise', 'thus', 'hence'}
            
            for token in sent:
                if token.text.lower() in conjunctive_adverbs and token.i != semicolon_token.i:
                    evidence_score += 0.1  # Conjunctive adverbs often indicate complex structure
            
        except Exception:
            pass
        
        return evidence_score
    
    def _apply_structural_clues_semicolon(self, evidence_score: float, semicolon_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply structural clues for semicolons."""
        block_type = context.get('block_type', '')
        
        # Headings should avoid semicolons
        if block_type == 'heading':
            evidence_score += 0.3
        
        # Lists (other than complex ones) should avoid semicolons
        elif 'list' in block_type and not self._is_complex_list_separator(semicolon_token, semicolon_token.sent):
            evidence_score += 0.2
        
        # Procedures and instructions should be clear and simple
        elif block_type in ['procedure', 'instruction', 'step']:
            evidence_score += 0.2
        
        # Admonitions (notes, tips) should be clear
        elif block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').lower()
            if admonition_type in ['note', 'tip', 'important', 'warning']:
                evidence_score += 0.1
        
        return evidence_score
    
    def _apply_semantic_clues_semicolon(self, evidence_score: float, semicolon_token: 'Token', text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for semicolons."""
        content_type = context.get('content_type', '')
        domain = context.get('domain', '')
        
        # Technical documentation strongly discourages semicolons
        if content_type == 'technical':
            evidence_score += 0.2
        
        # Business communication should be clear and direct
        elif content_type == 'business':
            evidence_score += 0.1
        
        # Academic writing is more accepting of semicolons
        elif content_type == 'academic':
            evidence_score -= 0.4  # Much more permissive for academic content
        
        # Marketing content should be clear and engaging
        elif content_type == 'marketing':
            evidence_score += 0.15
        
        # Domain-specific adjustments
        if domain in ['software', 'engineering', 'technical']:
            evidence_score += 0.1  # Technical domains prefer clarity
        elif domain in ['legal', 'academic', 'research']:
            evidence_score -= 0.1  # More formal domains may accept semicolons
        
        # Document length considerations
        doc_length = len(text.split())
        if doc_length < 100:  # Short documents
            evidence_score += 0.1  # Short docs should be simple
        elif doc_length > 1000:  # Long documents
            evidence_score -= 0.05  # Long docs may need varied punctuation
        
        return evidence_score
    
    def _apply_feedback_clues_semicolon(self, evidence_score: float, semicolon_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply feedback-based clues for semicolons."""
        # Placeholder for future feedback pattern integration
        # This would analyze user acceptance/rejection patterns for semicolon suggestions
        
        # For now, apply basic pattern-based adjustments
        try:
            sent = semicolon_token.sent
            sent_text = sent.text.lower()
            
            # Users often accept semicolons in formal lists and references
            if any(word in sent_text for word in ['reference', 'citation', 'see also', 'cf.', 'ibid']):
                evidence_score -= 0.2
            
            # Users often flag semicolons in simple explanatory text
            if any(word in sent_text for word in ['this means', 'in other words', 'that is', 'for example']):
                evidence_score += 0.2
            
            # Check sentence length - users often accept semicolons in very long sentences
            word_count = len(sent_text.split())
            if word_count > 25:
                evidence_score -= 0.1  # Very long sentences may warrant semicolons
            elif word_count < 15:
                evidence_score += 0.1  # Short sentences rarely need semicolons
            
        except Exception:
            pass
        
        return evidence_score

    # === SMART MESSAGING ===

    def _get_contextual_semicolon_message(self, evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate evidence-aware error message for semicolon usage."""
        content_type = context.get('content_type', 'general')
        
        if evidence_score > 0.85:
            # High confidence -> Direct, authoritative message
            if content_type == 'technical':
                return "Semicolons should be avoided in technical writing for optimal clarity."
            else:
                return "This semicolon creates unnecessary complexity - use simpler punctuation."
        elif evidence_score > 0.7:
            # Medium-high confidence -> Clear guidance
            if content_type == 'technical':
                return "Technical writing benefits from simpler punctuation than semicolons."
            elif content_type == 'business':
                return "Business communication should avoid semicolons for better clarity."
            else:
                return "Consider breaking this into separate sentences for better readability."
        elif evidence_score > 0.5:
            # Medium confidence -> Balanced suggestion
            return "This semicolon might be replaced with simpler punctuation for clarity."
        else:
            # Low confidence -> Gentle suggestion
            return "Consider whether this semicolon enhances or complicates readability."

    def _generate_smart_semicolon_suggestions(self, semicolon_token: 'Token', evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate evidence-aware suggestions for semicolon usage."""
        suggestions = []
        content_type = context.get('content_type', 'general')
        
        if evidence_score > 0.8:
            # High confidence -> Direct, actionable suggestions
            suggestions.append("Replace the semicolon with a period to create two clear sentences.")
            if content_type == 'technical':
                suggestions.append("Technical documentation should use simple, direct sentence structures.")
            else:
                suggestions.append("Break complex ideas into separate, digestible sentences.")
            suggestions.append("Use coordinating conjunctions (and, but, or) only if the ideas must be connected.")
            
        elif evidence_score > 0.6:
            # Medium confidence -> Helpful guidance
            suggestions.append("Consider replacing the semicolon with a period for clearer separation.")
            suggestions.append("Try connecting ideas with 'and', 'but', or 'so' if they're closely related.")
            if content_type == 'business':
                suggestions.append("Business writing should prioritize clarity over formal punctuation.")
            else:
                suggestions.append("Shorter sentences improve readability for most audiences.")
            
        else:
            # Low confidence -> Gentle alternatives
            suggestions.append("Evaluate whether this semicolon improves or hinders readability.")
            suggestions.append("Consider if two sentences would be clearer than one complex sentence.")
            if content_type == 'academic':
                suggestions.append("Check your style guide's preferences for semicolon usage.")
            else:
                suggestions.append("Test different punctuation options to find the clearest approach.")
        
        return suggestions[:3]

    def _generate_basic_semicolon_suggestions(self, sent_text: str, semicolon_pos: int) -> List[str]:
        """Generate basic suggestions when nlp is not available."""
        words_before = sent_text[:semicolon_pos].strip().split()
        preceding_word = words_before[-1] if words_before else ""
        
        return [
            "Replace the semicolon with a period and create a new sentence.",
            f"Consider breaking this into clearer, shorter sentences after '{preceding_word}'.",
            "Use coordinating conjunctions (and, but, or) to connect ideas if needed."
        ]
