"""
Punctuation and Symbols Rule
Based on IBM Style Guide topic: "Punctuation and symbols"

**UPDATED** with evidence-based scoring for nuanced symbol usage analysis.
"""
from typing import List, Dict, Any, Optional
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens import Doc, Token, Span
except ImportError:
    Doc = None
    Token = None
    Span = None

class PunctuationAndSymbolsRule(BasePunctuationRule):
    """
    Checks for the use of symbols instead of words in general text using evidence-based analysis,
    with dependency parsing to avoid flagging symbols in proper names or code.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'punctuation_and_symbols'

    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for symbol usage:
          - Symbols like & and + are generally discouraged in general text
          - Various contexts may legitimize symbol usage (names, code, technical content)
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        
        # Fallback analysis when nlp is not available
        if not nlp:
            # Apply basic guards for fallback analysis
            content_type = context.get('content_type', 'general')
            block_type = context.get('block_type', 'paragraph')
            
            # Skip if in contexts where symbols are legitimate
            if content_type in ['creative', 'literary', 'narrative']:
                return errors  # No errors for creative content
            if block_type in ['quote', 'blockquote', 'code_block', 'literal_block']:
                return errors  # No errors for quotes and code
            
            import re
            discouraged_symbols = {'&', '+'}
            
            for i, sentence in enumerate(sentences):
                for symbol in discouraged_symbols:
                    for match in re.finditer(re.escape(symbol), sentence):
                        # Skip obvious company names and mathematical expressions
                        context_text = sentence[max(0, match.start()-10):match.end()+10].lower()
                        
                        # Skip company names
                        if any(company in context_text for company in ['johnson', 'procter', 'at&t', 'h&r']):
                            continue
                        
                        # Skip mathematical expressions
                        if symbol == '+' and any(char.isdigit() for char in context_text):
                            continue
                        
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=f"Avoid using the symbol '{symbol}' in general text.",
                            suggestions=[f"Replace '{symbol}' with 'and'."] if symbol in '&+' else [],
                            severity='medium',
                            text=text,
                            context=context,
                            evidence_score=0.7,  # Default evidence for fallback analysis
                            span=(match.start(), match.end()),
                            flagged_text=symbol
                        ))
            return errors

        try:
            doc = nlp(text)
            # Linguistic Anchor: Symbols that should be spelled out in general text.
            discouraged_symbols = {'&', '+'}

            for i, sent in enumerate(doc.sents):
                for token in sent:
                    if token.text in discouraged_symbols:
                        evidence_score = self._calculate_symbol_evidence(token, sent, text, context)
                        
                        # Only flag if evidence suggests it's worth evaluating
                        if evidence_score > 0.1:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=self._get_contextual_symbol_message(token, evidence_score, context),
                                suggestions=self._generate_smart_symbol_suggestions(token, evidence_score, sent, context),
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
                message=f"Rule PunctuationAndSymbolsRule failed with error: {e}",
                suggestions=["This may be a bug in the rule. Please report it."],
                severity='low',
                text=text,
                context=context,
                evidence_score=0.0  # No evidence when analysis fails
            ))
        return errors

    # === EVIDENCE CALCULATION ===

    def _calculate_symbol_evidence(self, symbol_token: 'Token', sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) that symbol usage is incorrect.
        
        Higher scores indicate stronger evidence of an error.
        Lower scores indicate acceptable usage or ambiguous cases.
        """
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        # Apply surgical guards FIRST to eliminate false positives
        if self._apply_zero_false_positive_guards_punctuation(symbol_token, context):
            return 0.0
        
        # Creative content commonly uses symbols in natural expression
        content_type = context.get('content_type', 'general')
        if content_type in ['creative', 'literary', 'narrative']:
            return 0.0
        
        # Quotes preserve original text including symbols
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['quote', 'blockquote']:
            return 0.0
        
        # Mathematical expressions should preserve symbols
        token_sent_idx = symbol_token.i - sent.start
        if self._is_mathematical_expression(symbol_token, sent, token_sent_idx):
            return 0.0
        
        # Company names and proper names should preserve symbols
        if self._is_company_or_proper_name(symbol_token, sent, token_sent_idx):
            return 0.0
        
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        # Symbols are generally discouraged in general text
        evidence_score = 0.7  # Start with moderate to high evidence
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_symbol(evidence_score, symbol_token, sent)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_symbol(evidence_score, symbol_token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_symbol(evidence_score, symbol_token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_symbol(evidence_score, symbol_token, context)
        
        return max(0.0, min(1.0, evidence_score))

    def _is_mathematical_expression(self, symbol_token: 'Token', sent: 'Span', token_sent_idx: int) -> bool:
        """Check if the symbol is part of a mathematical expression."""
        # Check for numbers around the symbol
        if 0 < token_sent_idx < len(sent) - 1:
            prev_token = sent[token_sent_idx - 1]
            next_token = sent[token_sent_idx + 1]
            
            # Direct numeric context (2 + 3)
            if prev_token.like_num and next_token.like_num:
                return True
            
            # Variables in equations (a + b, x + y)
            if (len(prev_token.text) == 1 and prev_token.text.isalpha() and
                len(next_token.text) == 1 and next_token.text.isalpha()):
                return True
            
            # Mixed numeric and variable (2 + x)
            if (prev_token.like_num and len(next_token.text) == 1 and next_token.text.isalpha()) or \
               (len(prev_token.text) == 1 and prev_token.text.isalpha() and next_token.like_num):
                return True
        
        # Check for mathematical keywords nearby
        math_keywords = {'equation', 'formula', 'calculate', 'sum', 'total', 'equals', 'result'}
        sent_text = sent.text.lower()
        return any(keyword in sent_text for keyword in math_keywords)

    def _is_company_or_proper_name(self, symbol_token: 'Token', sent: 'Span', token_sent_idx: int) -> bool:
        """Check if the symbol is part of a company or proper name."""
        # Check for proper nouns around the symbol
        if 0 < token_sent_idx < len(sent) - 1:
            prev_token = sent[token_sent_idx - 1]
            next_token = sent[token_sent_idx + 1]
            
            # Both sides are proper nouns or title case (Johnson & Johnson)
            if (prev_token.pos_ == 'PROPN' and next_token.pos_ == 'PROPN') or \
               (prev_token.is_title and next_token.is_title):
                return True
        
        # Check for known company name patterns in immediate context (not entire sentence)
        # Get a small window around the symbol
        start_idx = max(0, token_sent_idx - 2)
        end_idx = min(len(sent), token_sent_idx + 3)
        context_window = ' '.join(token.text.lower() for token in sent[start_idx:end_idx])
        
        company_patterns = ['johnson & johnson', 'procter & gamble', 'barnes & noble', 
                          'h&r block', 'at&t', 'r&d', 'research & development']
        return any(pattern in context_window for pattern in company_patterns)

    def _apply_linguistic_clues_symbol(self, evidence_score: float, symbol_token: 'Token', sent: 'Span') -> float:
        """Apply SpaCy-based linguistic analysis clues for symbol usage."""
        
        token_sent_idx = symbol_token.i - sent.start
        
        # === CONTEXT-AWARE CHECKS ===
        
        # Check if symbol is part of a proper name or entity
        is_part_of_proper_name_or_code = any(
            ancestor.pos_ in ("PROPN", "X", "SYM") for ancestor in symbol_token.ancestors
        )
        
        if is_part_of_proper_name_or_code:
            evidence_score -= 0.6  # Much lower evidence if part of proper name
        
        # Check surrounding tokens for context
        if 0 < token_sent_idx < len(sent) - 1:
            prev_token = sent[token_sent_idx - 1]
            next_token = sent[token_sent_idx + 1]
            
            # Company names often use & (Johnson & Johnson, AT&T)
            if prev_token.pos_ == 'PROPN' and next_token.pos_ == 'PROPN':
                evidence_score -= 0.5
            
            # Check for brand names or product names
            if prev_token.is_title or next_token.is_title:
                evidence_score -= 0.3
            
            # Mathematical or technical expressions (3 + 2, A & B logic)
            if symbol_token.text == '+':
                if prev_token.like_num or next_token.like_num:
                    evidence_score -= 0.6  # Mathematical context
                if prev_token.pos_ == 'NOUN' and next_token.pos_ == 'NOUN':
                    # Could be combining two concepts
                    evidence_score -= 0.2
            
            # Ampersand in formal lists or pairs
            if symbol_token.text == '&':
                # Check for formal pairing (Research & Development)
                if (prev_token.pos_ == 'NOUN' and next_token.pos_ == 'NOUN') or \
                   (prev_token.is_title and next_token.is_title):
                    evidence_score -= 0.3
        
        # Check for URL or email patterns
        token_text_context = ' '.join(t.text for t in sent)
        if 'http' in token_text_context.lower() or '@' in token_text_context:
            evidence_score -= 0.5
        
        # Check if surrounded by punctuation (suggesting technical usage)
        if token_sent_idx > 0 and token_sent_idx < len(sent) - 1:
            prev_token = sent[token_sent_idx - 1]
            next_token = sent[token_sent_idx + 1]
            if prev_token.is_punct or next_token.is_punct:
                evidence_score -= 0.2
        
        return evidence_score

    def _apply_structural_clues_symbol(self, evidence_score: float, symbol_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply document structure-based clues for symbol usage."""
        
        block_type = context.get('block_type', 'paragraph')
        
        # Code blocks legitimately use symbols
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.8
        
        # Technical documentation may use symbols
        elif block_type in ['code_inline', 'monospace']:
            evidence_score -= 0.6
        
        # Headings may contain company names with symbols
        elif block_type in ['heading', 'title']:
            evidence_score -= 0.3
        
        # Lists may contain technical items or names
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.2
        
        # Tables may have technical content or abbreviations
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.3
        
        # Citations and references may have specific formatting
        elif block_type in ['citation', 'reference']:
            evidence_score -= 0.4
        
        # Quotes should preserve original text
        elif block_type in ['quote', 'blockquote']:
            evidence_score -= 0.5
        
        return evidence_score

    def _apply_semantic_clues_symbol(self, evidence_score: float, symbol_token: 'Token', text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for symbol usage."""
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # Technical content may legitimately use symbols
        if content_type == 'technical':
            evidence_score -= 0.2
        
        # Academic writing generally avoids symbols in running text
        elif content_type == 'academic':
            evidence_score += 0.1
        
        # Legal writing is formal and avoids symbols
        elif content_type == 'legal':
            evidence_score += 0.15
        
        # Marketing content may use symbols for brands
        elif content_type == 'marketing':
            evidence_score -= 0.1
        
        # Scientific writing may use symbols in formulas
        elif content_type == 'scientific':
            evidence_score -= 0.1
        
        # Business writing may include company names
        elif content_type == 'business':
            evidence_score -= 0.1
        
        # Domain-specific adjustments
        if domain in ['software', 'engineering', 'technology']:
            evidence_score -= 0.2  # More technical symbols acceptable
        elif domain in ['mathematics', 'science']:
            evidence_score -= 0.15  # Mathematical symbols common
        elif domain in ['business', 'finance']:
            evidence_score -= 0.1   # Company names common
        elif domain in ['literature', 'humanities']:
            evidence_score += 0.1   # More formal writing expected
        elif domain in ['legal', 'government']:
            evidence_score += 0.15  # Very formal writing
        
        # Audience considerations
        if audience in ['expert', 'developer', 'technical']:
            evidence_score -= 0.1  # Technical audience familiar with symbols
        elif audience in ['academic', 'researcher']:
            evidence_score += 0.05  # Academic preference for spelled-out words
        elif audience in ['general', 'consumer']:
            evidence_score += 0.1   # General audience benefits from spelled-out words
        elif audience in ['business', 'professional']:
            evidence_score -= 0.05  # Business context may have company names
        
        return evidence_score

    def _apply_feedback_clues_symbol(self, evidence_score: float, symbol_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply clues learned from user feedback patterns for symbol usage."""
        
        feedback_patterns = self._get_cached_feedback_patterns_symbol()
        
        # Get context around the symbol
        token_sent_idx = symbol_token.i - symbol_token.sent.start
        sent = symbol_token.sent
        
        symbol_text = symbol_token.text
        
        # Look for patterns in accepted/rejected symbol usage
        if token_sent_idx > 0:
            prev_word = sent[token_sent_idx - 1].text.lower()
            
            # Words commonly accepted before symbols
            if prev_word in feedback_patterns.get(f'accepted_before_{symbol_text}', set()):
                evidence_score -= 0.3
            
            # Words commonly flagged before symbols
            elif prev_word in feedback_patterns.get(f'flagged_before_{symbol_text}', set()):
                evidence_score += 0.2
        
        if token_sent_idx < len(sent) - 1:
            next_word = sent[token_sent_idx + 1].text.lower()
            
            # Words commonly accepted after symbols
            if next_word in feedback_patterns.get(f'accepted_after_{symbol_text}', set()):
                evidence_score -= 0.3
            
            # Words commonly flagged after symbols
            elif next_word in feedback_patterns.get(f'flagged_after_{symbol_text}', set()):
                evidence_score += 0.2
        
        # Check for specific symbol combinations
        if token_sent_idx > 0 and token_sent_idx < len(sent) - 1:
            context_phrase = f"{sent[token_sent_idx - 1].text.lower()} {symbol_text} {sent[token_sent_idx + 1].text.lower()}"
            
            # Common acceptable symbol phrases
            if context_phrase in feedback_patterns.get('accepted_symbol_phrases', set()):
                evidence_score -= 0.4
            elif context_phrase in feedback_patterns.get('flagged_symbol_phrases', set()):
                evidence_score += 0.3
        
        # Context-specific patterns
        block_type = context.get('block_type', 'paragraph')
        symbol_patterns = feedback_patterns.get(f'{block_type}_{symbol_text}_patterns', {})
        
        if 'accepted_rate' in symbol_patterns:
            acceptance_rate = symbol_patterns['accepted_rate']
            if acceptance_rate > 0.7:
                evidence_score -= 0.2
            elif acceptance_rate < 0.3:
                evidence_score += 0.2
        
        return evidence_score

    def _get_cached_feedback_patterns_symbol(self) -> Dict[str, Any]:
        """Load feedback patterns for symbol usage from cache or feedback analysis."""
        return {
            'accepted_before_&': {'johnson', 'procter', 'simon', 'barnes', 'black', 'research', 'development'},
            'flagged_before_&': {'you', 'i', 'we', 'they', 'this', 'that'},
            'accepted_after_&': {'johnson', 'gamble', 'schuster', 'noble', 'development', 'sons'},
            'flagged_after_&': {'then', 'also', 'more', 'so', 'now'},
            'accepted_before_+': {'grade', 'a', 'b', 'c', 'vitamin', 'covid'},
            'flagged_before_+': {'more', 'also', 'plus'},
            'accepted_after_+': {'more', 'plus', 'positive', 'benefits'},
            'accepted_symbol_phrases': {
                'johnson & johnson', 'procter & gamble', 'barnes & noble',
                'research & development', 'black & decker', 'a + b',
                'covid + symptoms', 'grade + performance'
            },
            'flagged_symbol_phrases': {
                'you & i', 'this & that', 'more & more',
                'fast + easy', 'quick + simple'
            },
            'paragraph_&_patterns': {'accepted_rate': 0.3},
            'heading_&_patterns': {'accepted_rate': 0.6},
            'code_block_&_patterns': {'accepted_rate': 0.9},
            'table_cell_&_patterns': {'accepted_rate': 0.5},
            'paragraph_+_patterns': {'accepted_rate': 0.2},
            'code_block_+_patterns': {'accepted_rate': 0.9},
            'technical_+_patterns': {'accepted_rate': 0.4},
        }

    # === SMART MESSAGING ===

    def _get_contextual_symbol_message(self, symbol_token: 'Token', evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for symbol usage."""
        
        symbol = symbol_token.text
        content_type = context.get('content_type', 'general')
        block_type = context.get('block_type', 'paragraph')
        
        if evidence_score > 0.8:
            if symbol == '&':
                return "Avoid using '&' in general text: spell out 'and' for better readability."
            elif symbol == '+':
                return "Avoid using '+' in general text: use 'and', 'plus', or 'in addition to' instead."
            else:
                return f"Avoid using the symbol '{symbol}' in general text."
        elif evidence_score > 0.6:
            if symbol == '&':
                return "Consider spelling out '&' as 'and' unless it's part of a proper name or technical context."
            elif symbol == '+':
                return "Consider replacing '+' with 'and' or 'plus' for clarity in general text."
            else:
                return f"Consider spelling out the symbol '{symbol}' in general text."
        elif evidence_score > 0.4:
            return f"Review symbol usage: '{symbol}' may be appropriate in technical contexts but consider readability."
        else:
            return f"Evaluate symbol usage for consistency with context and audience expectations."

    def _generate_smart_symbol_suggestions(self, symbol_token: 'Token', evidence_score: float, sent: 'Span', context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for symbol usage."""
        
        suggestions = []
        symbol = symbol_token.text
        content_type = context.get('content_type', 'general')
        block_type = context.get('block_type', 'paragraph')
        
        # Analyze surrounding context
        token_sent_idx = symbol_token.i - sent.start
        prev_word = sent[token_sent_idx - 1].text if token_sent_idx > 0 else ""
        next_word = sent[token_sent_idx + 1].text if token_sent_idx < len(sent) - 1 else ""
        
        # High evidence suggestions
        if evidence_score > 0.7:
            if symbol == '&':
                suggestions.append("Replace '&' with 'and' for better readability in general text.")
                
                # Check if it might be a company name
                if prev_word and next_word and (prev_word[0].isupper() or next_word[0].isupper()):
                    suggestions.append("If this is a company name, the ampersand may be acceptable.")
                else:
                    suggestions.append("Use 'and' to maintain a professional, readable tone.")
            
            elif symbol == '+':
                suggestions.append("Replace '+' with 'and', 'plus', or 'in addition to' as appropriate.")
                suggestions.append("Spelled-out words are clearer than symbols in general text.")
        
        # Medium evidence suggestions
        elif evidence_score > 0.4:
            if symbol == '&':
                suggestions.append("Consider 'and' instead of '&' unless this is a proper name or technical term.")
                suggestions.append("Ampersands are acceptable in company names and technical contexts.")
            elif symbol == '+':
                suggestions.append("Consider 'and' or 'plus' instead of '+' for general readability.")
                suggestions.append("The '+' symbol is acceptable in mathematical or technical contexts.")
        
        # Context-specific suggestions
        if content_type == 'technical' and evidence_score > 0.5:
            suggestions.append("Even in technical writing, consider whether spelled-out words improve clarity.")
        elif content_type == 'business' and symbol == '&':
            suggestions.append("In business writing, '&' is acceptable in company names but avoid in general text.")
        elif block_type in ['code_block', 'literal_block'] and evidence_score > 0.3:
            suggestions.append("Symbols are typically acceptable in code blocks and technical examples.")
        
        # General guidance
        if len(suggestions) < 2:
            suggestions.append("Spelled-out words are generally clearer and more accessible than symbols.")
            suggestions.append("Use symbols only when they're part of proper names or technical notation.")
        
        return suggestions[:3]