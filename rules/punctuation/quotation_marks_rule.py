"""
Quotation Marks Rule - Evidence-Based Analysis
Based on IBM Style Guide topic: "Quotation marks"

"""
from typing import List, Dict, Any, Optional
import re
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens import Doc, Token, Span
except ImportError:
    Doc = None
    Token = None
    Span = None

class QuotationMarksRule(BasePunctuationRule):
    """
    Checks for quotation mark issues using evidence-based analysis:
    - Inappropriate use for emphasis
    - Incorrect punctuation placement
    Enhanced with dependency parsing and contextual awareness.
    """
    def _get_rule_type(self) -> str:
        return 'quotation_marks'

    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for quotation mark usage violations.
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        if not nlp:
            return self._fallback_quotation_analysis(text, sentences, context)

        try:
            doc = nlp(text)
            for i, sent in enumerate(doc.sents):
                processed_quote_positions = set()  # Track processed quote positions to avoid duplicates
                for token in sent:
                    # Process all quote characters but avoid duplicates within pairs
                    if token.text in ['"', "'", "\u201c", "\u2018", "\u201d", "\u2019"]:
                        # Skip if we've already processed this quote position or its pair
                        if token.i in processed_quote_positions:
                            continue
                            
                        # Find the quote pair and mark both positions as processed
                        pair_position = self._find_quote_pair_position(token, sent)
                        processed_quote_positions.add(token.i)
                        if pair_position is not None:
                            processed_quote_positions.add(pair_position)
                        
                        evidence_score = self._calculate_quotation_evidence(token, sent, text, context)
                        
                        if evidence_score > 0.1:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=self._get_contextual_quotation_message(evidence_score, context),
                                suggestions=self._generate_smart_quotation_suggestions(token, evidence_score, context),
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
                message="Quotation mark analysis failed.",
                suggestions=["Review quotation mark usage manually."],
                severity='low',
                text=text,
                context=context,
                evidence_score=0.0,  # No evidence when analysis fails
                span=(0, 0),
                flagged_text=""
            ))
            return errors
        
        return errors

    def _fallback_quotation_analysis(self, text: str, sentences: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback analysis when nlp is not available."""
        errors = []
        
        # Apply context-aware guards first
        content_type = context.get('content_type', '')
        block_type = context.get('block_type', '')
        
        # Surgical zero false positive guards for fallback
        if content_type in ['creative', 'literary', 'narrative', 'marketing']:
            return errors
        if block_type in ['quote', 'blockquote', 'citation', 'code_block', 'literal_block']:
            return errors
        
        # Basic regex pattern for inappropriate emphasis quotes
        emphasis_pattern = r'"[^"]*"(?!\\s*(said|asked|replied|explained|stated))'
        
        for i, sent_text in enumerate(sentences):
            matches = re.finditer(emphasis_pattern, sent_text)
            for match in matches:
                # Skip UI elements and technical terms
                match_text = match.group().lower()
                if any(ui_word in match_text for ui_word in ['save', 'cancel', 'ok', 'button', 'menu', 'tab']):
                    continue
                if any(tech_word in match_text for tech_word in ['api', 'url', 'json', 'xml', 'sql']):
                    continue
                
                evidence_score = 0.6  # Moderate evidence for fallback analysis
                errors.append(self._create_error(
                    sentence=sent_text,
                    sentence_index=i,
                    message=self._get_contextual_quotation_message(evidence_score, context),
                    suggestions=self._generate_basic_quotation_suggestions(),
                    severity='low',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=(match.start(), match.end()),
                    flagged_text=match.group()
                ))
        return errors

    def _calculate_quotation_evidence(self, quote_token: 'Token', sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence (0.0-1.0) for quotation mark violations."""
        
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        # Apply quotation-specific guards first to eliminate false positives
        
        content_type = context.get('content_type', '')
        block_type = context.get('block_type', '')
        
        # GUARD 1: Creative, literary, and marketing content allows emphasis quotes
        if content_type in ['creative', 'literary', 'narrative', 'marketing']:
            return 0.0
        
        # GUARD 2: Quoted content blocks should not be flagged
        if block_type in ['quote', 'blockquote', 'citation', 'reference', 'footnote']:
            return 0.0
        
        # GUARD 3: Code blocks and technical content
        if block_type in ['code_block', 'literal_block', 'inline_code']:
            return 0.0
        
        # GUARD 4: Academic domain citations
        if content_type == 'academic' and context.get('domain') in ['research', 'academic']:
            return 0.0
        
        # GUARD 5: Check if this is an actual quotation with speech indicators
        if self._is_actual_quotation(quote_token, sent):
            return 0.0
        
        # GUARD 6: Check if this is a UI element or technical term definition
        if self._is_ui_element_or_definition(quote_token, sent, context):
            return 0.0
        
        # Apply common structural guards
        if self._apply_zero_false_positive_guards_punctuation(quote_token, context):
            return 0.0
        
        # === EVIDENCE CALCULATION ===
        evidence_score = 0.0
        
        # Check for inappropriate emphasis usage
        if self._is_inappropriate_emphasis_quote(quote_token, sent):
            evidence_score = 0.7
        
        # Check for punctuation placement issues
        elif self._has_punctuation_placement_issue(quote_token, sent):
            evidence_score = 0.6
        
        if evidence_score > 0.0:
            # Apply linguistic, structural, and semantic clues
            evidence_score = self._apply_linguistic_clues_quotation(evidence_score, quote_token, sent)
            evidence_score = self._apply_structural_clues_quotation(evidence_score, quote_token, context)
            evidence_score = self._apply_semantic_clues_quotation(evidence_score, quote_token, text, context)
            evidence_score = self._apply_feedback_clues_quotation(evidence_score, quote_token, context)
        
        return max(0.0, min(1.0, evidence_score))

    def _is_actual_quotation(self, quote_token: 'Token', sent: 'Span') -> bool:
        """Check if this is an actual quotation (not emphasis)."""
        # Look for speech indicators that suggest genuine quotation
        speech_verbs = {'say', 'ask', 'reply', 'explain', 'state', 'tell', 'mention', 'note', 
                       'observe', 'comment', 'remark', 'argue', 'claim', 'assert', 'declare'}
        reporting_phrases = ['according to', 'as noted by', 'as stated in']
        
        # Check for speech verbs in the sentence
        for token in sent:
            if token.lemma_.lower() in speech_verbs:
                return True
        
        # Check for reporting phrases
        sent_text = sent.text.lower()
        for phrase in reporting_phrases:
            if phrase in sent_text:
                return True
        
        return False
    
    def _is_ui_element_or_definition(self, quote_token: 'Token', sent: 'Span', context: Dict[str, Any]) -> bool:
        """Check if quotes are around UI elements, file names, or term definitions."""
        # Find the content within quotes
        quoted_content = self._get_quoted_content(quote_token, sent)
        if not quoted_content:
            return False
        
        quoted_text = quoted_content.lower()
        
        # UI element indicators
        ui_indicators = ['button', 'menu', 'tab', 'dialog', 'window', 'field', 'checkbox', 
                        'save', 'cancel', 'ok', 'apply', 'close', 'open', 'new', 'edit', 'server', 'database', 'cache']
        
        if any(ui_word in quoted_text for ui_word in ui_indicators):
            return True
        
        # File name patterns (extension or common file indicators)
        if ('.' in quoted_content and 
            any(quoted_content.lower().endswith(ext) for ext in ['.json', '.xml', '.yaml', '.yml', '.txt', '.csv', '.ini', '.conf', '.config'])):
            return True
        
        # Document/legal title patterns
        legal_indicators = ['terms', 'service', 'agreement', 'policy', 'license', 'contract', 'document']
        if any(legal_word in quoted_text for legal_word in legal_indicators):
            return True
        
        # Technical term definitions (short quoted terms followed by explanation)
        if len(quoted_text.split()) <= 3:
            # Look for definition indicators after the quote
            remaining_text = sent.text[quote_token.idx + len(quote_token.text):].lower()
            definition_indicators = ['stands for', 'means', 'refers to', 'is defined as', 'represents', 'file', 'document']
            if any(indicator in remaining_text for indicator in definition_indicators):
                return True
        
        # Procedure context often has legitimate UI quotes
        if context.get('block_type') == 'procedure':
            return True
        
        # Technical content is more permissive for file names and configuration
        content_type = context.get('content_type', '')
        if content_type == 'technical' and len(quoted_content.split()) <= 2:
            # Check if it's a technical term (not an emphasis adjective)
            technical_patterns = [
                quoted_content.isupper(),  # Acronyms like "API", "URL"
                '.' in quoted_content,     # File names
                quoted_content.endswith('js') or quoted_content.endswith('css'),  # Tech extensions
                quoted_content in ['config', 'server', 'database', 'cache', 'client', 'admin']  # Tech terms
            ]
            if any(technical_patterns):
                return True
        
        return False
    
    def _get_quoted_content(self, quote_token: 'Token', sent: 'Span') -> str:
        """Extract the content between quotes."""
        try:
            # Find matching closing quote
            start_idx = quote_token.i - sent.start
            closing_quote_idx = None
            
            # Map opening quotes to their closing counterparts
            quote_pairs = {
                '"': ['"', "\u201d"],        # Standard and smart double quotes
                "'": ["'", "\u2019"],        # Standard and smart single quotes  
                "\u201c": ["\u201d"],        # Smart double quotes (open to close)
                "\u2018": ["\u2019"]         # Smart single quotes (open to close)
            }
            
            # Get possible closing quotes for this opening quote
            possible_closing = quote_pairs.get(quote_token.text, ['"', "\u201d", "'", "\u2019"])
            
            for i, token in enumerate(sent[start_idx + 1:], start_idx + 1):
                if token.text in possible_closing:
                    closing_quote_idx = i
                    break
            
            if closing_quote_idx:
                # Extract text between quotes
                content_tokens = sent[start_idx + 1:closing_quote_idx]
                return ' '.join([token.text for token in content_tokens])
        except Exception:
            pass
        
        return ""
    
    def _find_quote_pair_position(self, quote_token: 'Token', sent: 'Span') -> Optional[int]:
        """Find the position of the matching quote in the pair."""
        try:
            start_idx = quote_token.i - sent.start
            quote_chars = ['"', "'", "\u201c", "\u2018", "\u201d", "\u2019"]
            
            # Look for the next quote character
            for i, token in enumerate(sent[start_idx + 1:], start_idx + 1):
                if token.text in quote_chars:
                    return sent.start + i  # Return absolute position
            
        except Exception:
            pass
        
        return None
    
    def _is_inappropriate_emphasis_quote(self, quote_token: 'Token', sent: 'Span') -> bool:
        """Check if quotes are being used inappropriately for emphasis."""
        # If we've already determined it's an actual quotation, UI element, or definition, it's not inappropriate
        return True  # Base case - if we reach here, it's likely inappropriate emphasis

    def _has_punctuation_placement_issue(self, quote_token: 'Token', sent: 'Span') -> bool:
        """Check for punctuation placement issues with quotes."""
        # Check for common punctuation placement errors
        # e.g., punctuation outside quotes when it should be inside
        try:
            # Find the closing quote
            quote_chars = ['"', "\u201d", "'", "\u2019", "\u201c", "\u2018"]
            start_idx = quote_token.i - sent.start
            
            for i, token in enumerate(sent[start_idx + 1:], start_idx + 1):
                if token.text in quote_chars:
                    # Check if there's punctuation immediately after the closing quote
                    if i < len(sent) - 1:
                        next_token = sent[i + 1]
                        if next_token.text in ['.', ',', '!', '?']:
                            # This might be a placement issue, but for now return False
                            # as this is complex and depends on context
                            return False
                    break
        except Exception:
            pass
        
        return False
    
    # === QUOTATION-SPECIFIC CLUE METHODS ===
    
    def _apply_linguistic_clues_quotation(self, evidence_score: float, quote_token: 'Token', sent: 'Span') -> float:
        """Apply linguistic analysis clues for quotation marks."""
        try:
            # Check surrounding tokens for context clues
            quoted_content = self._get_quoted_content(quote_token, sent)
            
            if quoted_content:
                # Single word in quotes often emphasis
                words = quoted_content.split()
                if len(words) == 1:
                    evidence_score += 0.1  # Likely emphasis
                
                # Check for emphasis adverbs
                emphasis_words = {'really', 'very', 'extremely', 'incredibly', 'amazing', 'awesome'}
                if any(word.lower() in emphasis_words for word in words):
                    evidence_score += 0.2  # Strong indicator of emphasis use
                
                # Check for business jargon
                jargon_phrases = {'game-changing', 'game changer', 'low-hanging fruit', 'move the needle', 'synergy'}
                quoted_lower = quoted_content.lower()
                if any(phrase in quoted_lower for phrase in jargon_phrases):
                    evidence_score += 0.2  # Business jargon often inappropriately quoted
            
            # Check for sentence position
            if quote_token.i == sent.start:  # Quote at beginning
                evidence_score -= 0.1  # More likely to be actual quote
            
        except Exception:
            pass
        
        return evidence_score
    
    def _apply_structural_clues_quotation(self, evidence_score: float, quote_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply structural clues for quotation marks."""
        block_type = context.get('block_type', '')
        
        # Lists often have legitimate quoted items
        if 'list' in block_type:
            evidence_score -= 0.2
        
        # Headings sometimes use quotes for emphasis (less acceptable)
        elif block_type == 'heading':
            evidence_score += 0.1
        
        # Tables often have quoted values
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.2
        
        # Admonitions (notes, tips) are more permissive
        elif block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').lower()
            if admonition_type in ['note', 'tip', 'hint']:
                evidence_score -= 0.2
        
        return evidence_score
    
    def _apply_semantic_clues_quotation(self, evidence_score: float, quote_token: 'Token', text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for quotation marks."""
        content_type = context.get('content_type', '')
        domain = context.get('domain', '')
        
        # Technical documentation is stricter about emphasis quotes
        if content_type == 'technical':
            evidence_score += 0.1
        
        # Legal and formal documents are stricter
        elif content_type == 'legal':
            evidence_score += 0.2
        
        # Academic writing has specific citation rules
        elif content_type == 'academic':
            evidence_score -= 0.1  # More permissive for citations
        
        # Business domain specific adjustments
        if domain in ['business', 'corporate']:
            evidence_score += 0.1  # Business writing should avoid emphasis quotes
        
        # Software domain adjustments
        elif domain in ['software', 'engineering']:
            evidence_score -= 0.1  # More permissive for technical terms
        
        # Document length considerations
        doc_length = len(text.split())
        if doc_length < 100:  # Short documents
            evidence_score -= 0.05  # Slightly more permissive
        
        return evidence_score
    
    def _apply_feedback_clues_quotation(self, evidence_score: float, quote_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply feedback-based clues for quotation marks."""
        # Placeholder for future feedback pattern integration
        # This would analyze user acceptance/rejection patterns for quotation mark suggestions
        
        # For now, apply basic frequency-based adjustments
        quoted_content = self._get_quoted_content(quote_token, quote_token.sent)
        
        if quoted_content:
            # Common UI terms that users often accept as legitimately quoted
            ui_terms = {'save', 'cancel', 'ok', 'apply', 'close', 'open', 'new', 'edit', 'delete'}
            if quoted_content.lower() in ui_terms:
                evidence_score -= 0.3  # Users typically accept these
            
            # Common emphasis words that users often flag as inappropriate
            emphasis_terms = {'really', 'very', 'excellent', 'amazing', 'awesome', 'perfect'}
            if quoted_content.lower() in emphasis_terms:
                evidence_score += 0.2  # Users typically want these flagged
        
        return evidence_score

    def _get_contextual_quotation_message(self, evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate evidence-aware error message for quotation mark usage."""
        content_type = context.get('content_type', '')
        
        if evidence_score > 0.85:
            # High confidence -> Direct, authoritative message
            return "Quotation marks should not be used for emphasis in professional writing."
        elif evidence_score > 0.7:
            # Medium-high confidence -> Clear guidance
            if content_type == 'technical':
                return "Reserve quotation marks for actual quotations and UI element names."
            else:
                return "Avoid using quotation marks for emphasis; use formatting instead."
        elif evidence_score > 0.5:
            # Medium confidence -> Balanced suggestion
            return "Consider if these quotation marks are appropriate for your writing style."
        else:
            # Low confidence -> Gentle suggestion
            return "Review whether quotation marks add value or could be removed."

    def _generate_smart_quotation_suggestions(self, quote_token: 'Token', evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate evidence-aware suggestions for quotation mark usage."""
        suggestions = []
        content_type = context.get('content_type', '')
        quoted_content = self._get_quoted_content(quote_token, quote_token.sent)
        
        if evidence_score > 0.8:
            # High confidence -> Direct, actionable suggestions
            suggestions.append("Remove the quotation marks - they appear to be used for emphasis.")
            if content_type == 'technical':
                suggestions.append("Use bold or italic formatting to emphasize important terms.")
            else:
                suggestions.append("Use formatting (bold, italic) or restructure the sentence for emphasis.")
            suggestions.append("Reserve quotation marks for actual speech or citations.")
            
        elif evidence_score > 0.6:
            # Medium confidence -> Helpful guidance
            if quoted_content and len(quoted_content.split()) == 1:
                suggestions.append(f"Consider removing quotes around '{quoted_content}' if used for emphasis.")
            suggestions.append("Use quotation marks only for direct quotes and UI element names.")
            suggestions.append("Try bold or italic formatting for emphasis instead.")
            
        else:
            # Low confidence -> Gentle suggestions
            suggestions.append("Verify that quotation marks serve a clear purpose here.")
            suggestions.append("Consider if the text would be clearer without quotation marks.")
            if content_type == 'technical':
                suggestions.append("Ensure UI elements and terms are appropriately marked.")
        
        return suggestions[:3]

    def _generate_basic_quotation_suggestions(self) -> List[str]:
        """Generate basic suggestions when nlp is not available."""
        return [
            "Avoid using quotation marks for emphasis.",
            "Use italics or bold formatting for emphasis instead.",
            "Reserve quotation marks for actual quotations."
        ]