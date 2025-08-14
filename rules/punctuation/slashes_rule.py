"""
Slashes Rule
Based on IBM Style Guide topic: "Slashes"

**UPDATED** with evidence-based scoring for nuanced slash usage analysis.
"""
from typing import List, Dict, Any, Optional
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens import Doc, Token, Span
except ImportError:
    Doc = None
    Token = None
    Span = None

class SlashesRule(BasePunctuationRule):
    """
    Checks for the ambiguous use of slashes to mean "and/or" using evidence-based analysis,
    with Part-of-Speech tagging to identify the grammatical context.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'slashes'

    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for slash usage:
          - Slashes can be ambiguous when used to mean "and/or"
          - Various contexts legitimize slash usage (URLs, paths, dates, ratios)
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        
        # Fallback analysis when nlp is not available
        if not nlp:
            import re
            
            # Apply context-aware guards first  
            content_type = context.get('content_type', '')
            block_type = context.get('block_type', '')
            
            # Surgical zero false positive guards for fallback
            if block_type in ['code_block', 'literal_block', 'inline_code']:
                return errors
            if block_type in ['url', 'link']:
                return errors
            
            for i, sentence in enumerate(sentences):
                # Simple pattern for potential ambiguous slash usage
                # Look for word/word patterns that might be ambiguous
                for match in re.finditer(r'\b\w+/\w+\b', sentence):
                    # Basic checks to avoid obvious false positives
                    matched_text = match.group(0).lower()
                    
                    # Skip URLs and web addresses
                    if any(pattern in sentence.lower() for pattern in ['http', 'www', '.com', '.org', '.net', '.gov', '.edu']):
                        continue
                    
                    # Skip file paths
                    if any(pattern in sentence.lower() for pattern in ['/usr/', '/bin/', '/etc/', '/var/', '/home/', 'directory', 'folder', 'path']):
                        continue
                    
                    # Skip dates
                    if re.match(r'\d+/\d+(/\d+)?', matched_text):
                        continue
                    
                    # Skip measurements and ratios
                    if any(unit in sentence.lower() for unit in ['km/h', 'mph', 'w/o', 'c/o', 'vol/issue', 'page/']):
                        continue
                    
                    # Basic evidence calculation for fallback
                    evidence_score = 0.6  # Default moderate evidence
                    
                    if content_type == 'legal':
                        evidence_score = 0.8  # Higher evidence for legal content
                    elif content_type == 'technical':
                        evidence_score = 0.4  # Lower evidence for technical content
                    
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Avoid using a slash (/) to mean 'and/or' as it can be ambiguous.",
                        suggestions=["Clarify the meaning by rewriting the sentence to use 'and', 'or', or 'and or'. For example, instead of 'Insert the CD/DVD', write 'Insert the CD or DVD'."],
                        severity='medium',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(match.start(), match.end()),
                        flagged_text=match.group(0)
                    ))
            return errors

        try:
            doc = nlp(text)
            for i, sent in enumerate(doc.sents):
                for token in sent:
                    if token.text == '/':
                        evidence_score = self._calculate_slash_evidence(token, sent, text, context)
                        
                        # Only flag if evidence suggests it's worth evaluating
                        if evidence_score > 0.1:
                            # Get the flagged text including surrounding words
                            flagged_text, span = self._get_slash_context(token, sent)
                            
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=self._get_contextual_slash_message(token, evidence_score, context),
                                suggestions=self._generate_smart_slash_suggestions(token, evidence_score, sent, context),
                                severity='low' if evidence_score < 0.7 else 'medium',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=span,
                                flagged_text=flagged_text
                            ))
        except Exception as e:
            # Safeguard for unexpected SpaCy behavior
            errors.append(self._create_error(
                sentence=text,
                sentence_index=0,
                message=f"Rule SlashesRule failed with error: {e}",
                suggestions=["This may be a bug in the rule. Please report it."],
                severity='low',
                text=text,
                context=context,
                evidence_score=0.0,  # No evidence when analysis fails
                span=(0, 0),
                flagged_text=""
            ))
        return errors

    def _get_slash_context(self, slash_token: 'Token', sent: 'Span') -> tuple:
        """Extract the context around the slash for better error reporting."""
        token_sent_idx = slash_token.i - sent.start
        
        if 0 < token_sent_idx < len(sent) - 1:
            prev_token = sent[token_sent_idx - 1]
            next_token = sent[token_sent_idx + 1]
            flagged_text = f"{prev_token.text}/{next_token.text}"
            span = (prev_token.idx, next_token.idx + len(next_token.text))
        else:
            flagged_text = slash_token.text
            span = (slash_token.idx, slash_token.idx + len(slash_token.text))
        
        return flagged_text, span

    # === EVIDENCE CALCULATION ===

    def _calculate_slash_evidence(self, slash_token: 'Token', sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) that slash usage is incorrect.
        
        Higher scores indicate stronger evidence of an error.
        Lower scores indicate acceptable usage or ambiguous cases.
        """
        
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        # Apply slash-specific guards first to eliminate false positives
        
        content_type = context.get('content_type', '')
        block_type = context.get('block_type', '')
        
        # GUARD 1: Code blocks and technical content
        if block_type in ['code_block', 'literal_block', 'inline_code']:
            return 0.0
        
        # GUARD 2: URLs and links
        if block_type in ['url', 'link']:
            return 0.0
        
        # GUARD 3: Check for file paths and system directories
        if self._is_file_path_slash(slash_token, sent):
            return 0.0
        
        # GUARD 4: Check for URLs in sentence context
        if self._is_url_slash(slash_token, sent):
            return 0.0
        
        # GUARD 5: Check for dates and numeric ratios
        if self._is_date_or_numeric_slash(slash_token, sent):
            return 0.0
        
        # GUARD 6: Check for measurement units
        if self._is_measurement_slash(slash_token, sent):
            return 0.0
        
        # GUARD 7: Check for academic citations and references
        if self._is_academic_notation_slash(slash_token, sent):
            return 0.0
        
        # Apply common structural guards (but skip the base slash check since we need to analyze slashes)
        # The base class incorrectly guards against all slashes, so we override with targeted checks
        if context and context.get('block_type') in ['code_block', 'inline_code', 'literal_block']:
            return 0.0
        if hasattr(slash_token, 'like_url') and slash_token.like_url:
            return 0.0
        if hasattr(slash_token, 'like_email') and slash_token.like_email:
            return 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        # Check if this looks like an ambiguous and/or usage
        if not self._is_ambiguous_slash_pattern(slash_token, sent):
            return 0.0  # Not an ambiguous pattern, don't flag
        
        # Start with moderate evidence for ambiguous patterns
        evidence_score = 0.6
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_slash(evidence_score, slash_token, sent)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_slash(evidence_score, slash_token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_slash(evidence_score, slash_token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_slash(evidence_score, slash_token, context)
        
        return max(0.0, min(1.0, evidence_score))

    def _is_ambiguous_slash_pattern(self, slash_token: 'Token', sent: 'Span') -> bool:
        """Check if this slash follows the ambiguous and/or pattern."""
        token_sent_idx = slash_token.i - sent.start
        
        if not (0 < token_sent_idx < len(sent) - 1):
            return False
        
        prev_token = sent[token_sent_idx - 1]
        next_token = sent[token_sent_idx + 1]
        
        # The ambiguous "and/or" usage can occur between various POS combinations
        ambiguous_pos_patterns = [
            (["NOUN", "ADJ", "PROPN"], ["NOUN", "ADJ", "PROPN"]),
            (["NOUN"], ["NOUN"]),
            (["ADJ"], ["ADJ"]),
            (["PROPN"], ["PROPN"]),
            (["ADP"], ["NOUN"]),  # "on/off", "in/out"
            (["ADV"], ["ADV"]),   # "yes/no", "here/there"
            (["VERB"], ["VERB"]), # "read/write", "send/receive"
            (["ADJ"], ["NOUN"]),  # "true/false"
            (["NOUN"], ["ADJ"])   # "input/output" variations
        ]
        
        for prev_pattern, next_pattern in ambiguous_pos_patterns:
            if prev_token.pos_ in prev_pattern and next_token.pos_ in next_pattern:
                return True
        
        return False

    # === SLASH-SPECIFIC GUARD METHODS ===
    
    def _is_file_path_slash(self, slash_token: 'Token', sent: 'Span') -> bool:
        """Check if this slash is part of a file path or directory."""
        sent_text = sent.text.lower()
        
        # Common file path indicators
        path_indicators = [
            '/usr/', '/bin/', '/etc/', '/var/', '/home/', '/opt/', '/tmp/',
            'directory', 'folder', 'path', 'file', 'config', 'system'
        ]
        
        if any(indicator in sent_text for indicator in path_indicators):
            return True
        
        # Check if slash is at the beginning (absolute path)
        token_sent_idx = slash_token.i - sent.start
        if token_sent_idx == 0 or (token_sent_idx > 0 and sent[token_sent_idx - 1].text.isspace()):
            return True
        
        # Check for path-like patterns around the slash
        if 0 < token_sent_idx < len(sent) - 1:
            prev_token = sent[token_sent_idx - 1]
            next_token = sent[token_sent_idx + 1]
            
            # Common directory names
            common_dirs = {'usr', 'bin', 'etc', 'var', 'home', 'opt', 'tmp', 'lib', 'sbin', 'local'}
            if prev_token.text.lower() in common_dirs or next_token.text.lower() in common_dirs:
                return True
        
        return False
    
    def _is_url_slash(self, slash_token: 'Token', sent: 'Span') -> bool:
        """Check if this slash is part of a URL."""
        sent_text = sent.text.lower()
        
        # URL indicators
        url_patterns = [
            'http://', 'https://', 'ftp://', 'www.',
            '.com', '.org', '.net', '.gov', '.edu', '.io'
        ]
        
        return any(pattern in sent_text for pattern in url_patterns)
    
    def _is_date_or_numeric_slash(self, slash_token: 'Token', sent: 'Span') -> bool:
        """Check if this slash is part of a date or numeric ratio."""
        token_sent_idx = slash_token.i - sent.start
        
        if not (0 < token_sent_idx < len(sent) - 1):
            return False
        
        prev_token = sent[token_sent_idx - 1]
        next_token = sent[token_sent_idx + 1]
        
        # Numeric patterns (dates, fractions, ratios)
        if prev_token.like_num and next_token.like_num:
            return True
        
        # Year patterns (MM/DD/YYYY, DD/MM/YYYY)
        prev_text = prev_token.text
        next_text = next_token.text
        
        if (prev_text.isdigit() and next_text.isdigit()):
            prev_len = len(prev_text)
            next_len = len(next_text)
            # Date-like patterns
            if (1 <= prev_len <= 2 and 1 <= next_len <= 4) or (1 <= prev_len <= 4 and 1 <= next_len <= 2):
                return True
        
        return False
    
    def _is_measurement_slash(self, slash_token: 'Token', sent: 'Span') -> bool:
        """Check if this slash is part of a measurement unit."""
        token_sent_idx = slash_token.i - sent.start
        
        if not (0 < token_sent_idx < len(sent) - 1):
            return False
        
        prev_token = sent[token_sent_idx - 1]
        next_token = sent[token_sent_idx + 1]
        
        # Common measurement units
        units = {
            'km', 'mile', 'meter', 'yard', 'foot', 'inch',
            'hour', 'minute', 'second', 'day', 'week', 'month', 'year',
            'gallon', 'liter', 'litre', 'ounce', 'cup', 'pint', 'quart',
            'pound', 'kg', 'gram', 'ton', 'oz', 'lb',
            'mph', 'kph', 'rpm', 'bpm', 'fps', 'psi',
            'h', 'm', 's', 'g', 'l'
        }
        
        prev_text = prev_token.text.lower()
        next_text = next_token.text.lower()
        
        return prev_text in units or next_text in units
    
    def _is_academic_notation_slash(self, slash_token: 'Token', sent: 'Span') -> bool:
        """Check if this slash is part of academic notation."""
        token_sent_idx = slash_token.i - sent.start
        
        if not (0 < token_sent_idx < len(sent) - 1):
            return False
        
        prev_token = sent[token_sent_idx - 1]
        next_token = sent[token_sent_idx + 1]
        
        # Academic notation patterns
        academic_terms = {
            'vol', 'volume', 'issue', 'page', 'line', 'chapter', 'section',
            'p', 'pp', 'ch', 'sec', 'fig', 'figure', 'table', 'ref',
            'ed', 'edition', 'rev', 'revision'
        }
        
        prev_text = prev_token.text.lower()
        next_text = next_token.text.lower()
        
        if prev_text in academic_terms or next_text in academic_terms:
            return True
        
        # Common abbreviations with slashes
        common_abbrevs = {
            'w/o', 'c/o', 'a/c', 'n/a', 'tbd', 'tbh', 'w/', 'w/out',
            'i/o', 'input/output', 'http/https', 'tcp/ip', 'ssl/tls'
        }
        combined = f"{prev_text}/{next_text}"
        
        return combined in common_abbrevs

    def _apply_linguistic_clues_slash(self, evidence_score: float, slash_token: 'Token', sent: 'Span') -> float:
        """Apply SpaCy-based linguistic analysis clues for slash usage."""
        
        token_sent_idx = slash_token.i - sent.start
        prev_token = sent[token_sent_idx - 1]
        next_token = sent[token_sent_idx + 1]
        
        # Note: Most legitimate contexts are now handled by surgical guards
        # This method should focus on linguistic patterns that affect ambiguity
        
        # === CHECK FOR INCREASED AMBIGUITY ===
        
        # Common ambiguous patterns that should be flagged
        ambiguous_pairs = {
            ('he', 'she'), ('his', 'her'), ('him', 'her'),
            ('true', 'false'), ('yes', 'no'), ('on', 'off'),
            ('input', 'output'), ('read', 'write'), ('send', 'receive'),
            ('option', 'choice'), ('laptop', 'tablet'), ('user', 'administrator'),
            ('equipment', 'software'), ('client', 'server'), ('desktop', 'mobile'),
            ('cat', 'dog'), ('clear', 'unambiguous')
        }
        
        prev_word = prev_token.text.lower()
        next_word = next_token.text.lower()
        
        if (prev_word, next_word) in ambiguous_pairs or (next_word, prev_word) in ambiguous_pairs:
            evidence_score += 0.3  # These are often ambiguous
        
        # Plural nouns often indicate choice between options
        if prev_token.tag_ in ['NNS', 'NNPS'] or next_token.tag_ in ['NNS', 'NNPS']:
            evidence_score += 0.1
        
        # Common word pairs that are often ambiguous
        common_ambiguous = {
            'and', 'or', 'plus', 'minus', 'with', 'without',
            'before', 'after', 'above', 'below', 'client', 'server'
        }
        
        if prev_word in common_ambiguous or next_word in common_ambiguous:
            evidence_score += 0.2
        
        return evidence_score

    def _apply_structural_clues_slash(self, evidence_score: float, slash_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply document structure-based clues for slash usage."""
        
        block_type = context.get('block_type', 'paragraph')
        
        # Code blocks legitimately use slashes
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.8
        
        # Technical documentation may use slashes for paths
        elif block_type in ['code_inline', 'monospace']:
            evidence_score -= 0.6
        
        # URLs in links
        elif block_type in ['link', 'url']:
            evidence_score -= 0.9
        
        # Tables may have technical notation
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.3
        
        # Lists may contain technical items
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.2
        
        # Citations and references have specific formats
        elif block_type in ['citation', 'reference']:
            evidence_score -= 0.4
        
        # Quotes should preserve original text
        elif block_type in ['quote', 'blockquote']:
            evidence_score -= 0.5
        
        # Headings may have paths or technical terms
        elif block_type in ['heading', 'title']:
            evidence_score -= 0.2
        
        return evidence_score

    def _apply_semantic_clues_slash(self, evidence_score: float, slash_token: 'Token', text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for slash usage."""
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # Technical content often has legitimate slash usage
        if content_type == 'technical':
            evidence_score -= 0.2
        
        # Academic writing should be precise
        elif content_type == 'academic':
            evidence_score += 0.1
        
        # Legal writing must be unambiguous
        elif content_type == 'legal':
            evidence_score += 0.2
        
        # Scientific writing may have ratios and measurements
        elif content_type == 'scientific':
            evidence_score -= 0.1
        
        # Business writing should be clear
        elif content_type == 'business':
            evidence_score += 0.05
        
        # Marketing content should be clear for general audience
        elif content_type == 'marketing':
            evidence_score += 0.1
        
        # Educational content should avoid ambiguity
        elif content_type == 'educational':
            evidence_score += 0.1
        
        # Domain-specific adjustments
        if domain in ['software', 'engineering', 'technology']:
            evidence_score -= 0.2  # Paths and technical notation common
        elif domain in ['web', 'internet']:
            evidence_score -= 0.3  # URLs very common
        elif domain in ['mathematics', 'science']:
            evidence_score -= 0.15  # Fractions and ratios common
        elif domain in ['literature', 'humanities']:
            evidence_score += 0.1   # Should be precise language
        elif domain in ['legal', 'government']:
            evidence_score += 0.2   # Must avoid ambiguity
        elif domain in ['finance', 'business']:
            evidence_score += 0.05  # Should be clear
        
        # Audience considerations
        if audience in ['technical', 'developer', 'expert']:
            evidence_score -= 0.1  # Technical audience understands notation
        elif audience in ['academic', 'researcher']:
            evidence_score += 0.05  # Academic precision expected
        elif audience in ['general', 'consumer']:
            evidence_score += 0.15  # General audience needs clarity
        elif audience in ['beginner', 'student']:
            evidence_score += 0.1   # Avoid confusing notation
        
        return evidence_score

    def _apply_feedback_clues_slash(self, evidence_score: float, slash_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply clues learned from user feedback patterns for slash usage."""
        
        feedback_patterns = self._get_cached_feedback_patterns_slash()
        
        # Get context around the slash
        token_sent_idx = slash_token.i - slash_token.sent.start
        sent = slash_token.sent
        
        if 0 < token_sent_idx < len(sent) - 1:
            prev_word = sent[token_sent_idx - 1].text.lower()
            next_word = sent[token_sent_idx + 1].text.lower()
            
            # Common word pairs that are accepted with slashes
            word_pair = f"{prev_word}/{next_word}"
            reverse_pair = f"{next_word}/{prev_word}"
            
            if word_pair in feedback_patterns.get('accepted_slash_pairs', set()) or \
               reverse_pair in feedback_patterns.get('accepted_slash_pairs', set()):
                evidence_score -= 0.4
            
            # Common word pairs that are flagged as ambiguous
            elif word_pair in feedback_patterns.get('flagged_slash_pairs', set()) or \
                 reverse_pair in feedback_patterns.get('flagged_slash_pairs', set()):
                evidence_score += 0.3
            
            # Words commonly accepted before slashes
            if prev_word in feedback_patterns.get('accepted_before_slash', set()):
                evidence_score -= 0.2
            elif prev_word in feedback_patterns.get('flagged_before_slash', set()):
                evidence_score += 0.2
            
            # Words commonly accepted after slashes
            if next_word in feedback_patterns.get('accepted_after_slash', set()):
                evidence_score -= 0.2
            elif next_word in feedback_patterns.get('flagged_after_slash', set()):
                evidence_score += 0.2
        
        # Context-specific patterns
        block_type = context.get('block_type', 'paragraph')
        slash_patterns = feedback_patterns.get(f'{block_type}_slash_patterns', {})
        
        if 'accepted_rate' in slash_patterns:
            acceptance_rate = slash_patterns['accepted_rate']
            if acceptance_rate > 0.7:
                evidence_score -= 0.2
            elif acceptance_rate < 0.3:
                evidence_score += 0.2
        
        return evidence_score

    def _get_cached_feedback_patterns_slash(self) -> Dict[str, Any]:
        """Load feedback patterns for slash usage from cache or feedback analysis."""
        return {
            'accepted_slash_pairs': {
                'km/h', 'mph/kph', 'miles/gallon', 'w/o', 'c/o',
                '24/7', '365/24', 'input/output', 'read/write',
                'vol/issue', 'page/line', 'mm/dd/yyyy', 'dd/mm/yyyy'
            },
            'flagged_slash_pairs': {
                'he/she', 'his/her', 'him/her', 'true/false',
                'yes/no', 'on/off', 'and/or', 'either/or',
                'cats/dogs', 'coffee/tea', 'windows/mac'
            },
            'accepted_before_slash': {
                'km', 'miles', 'http', 'https', 'file', 'folder',
                'input', 'output', 'read', 'write', 'vol', 'page'
            },
            'flagged_before_slash': {
                'he', 'she', 'his', 'her', 'true', 'false',
                'cats', 'dogs', 'either', 'and'
            },
            'accepted_after_slash': {
                'h', 'hour', 'gallon', 'output', 'write', 'issue',
                'line', 'dd', 'mm', 'yyyy'
            },
            'flagged_after_slash': {
                'she', 'her', 'false', 'no', 'off', 'or',
                'dogs', 'tea', 'mac'
            },
            'paragraph_slash_patterns': {'accepted_rate': 0.4},
            'code_block_slash_patterns': {'accepted_rate': 0.9},
            'table_cell_slash_patterns': {'accepted_rate': 0.6},
            'technical_slash_patterns': {'accepted_rate': 0.7},
        }

    # === SMART MESSAGING ===

    def _get_contextual_slash_message(self, slash_token: 'Token', evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for slash usage."""
        
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        
        # Get the specific word pair for more targeted messaging
        token_sent_idx = slash_token.i - slash_token.sent.start
        sent = slash_token.sent
        
        if 0 < token_sent_idx < len(sent) - 1:
            prev_word = sent[token_sent_idx - 1].text
            next_word = sent[token_sent_idx + 1].text
            word_pair = f"{prev_word}/{next_word}"
        else:
            word_pair = "slash"
        
        if evidence_score > 0.8:
            if content_type == 'legal':
                return f"Avoid ambiguous slash usage ('{word_pair}'): legal writing requires unambiguous language."
            else:
                return f"Ambiguous slash usage ('{word_pair}'): clarify whether you mean 'and', 'or', or 'and/or'."
        elif evidence_score > 0.6:
            if audience in ['general', 'consumer']:
                return f"Slash usage may be unclear ('{word_pair}'): consider spelling out the relationship for general readers."
            else:
                return f"Consider clarifying slash usage ('{word_pair}'): specify whether you mean 'and' or 'or'."
        elif evidence_score > 0.4:
            return f"Review slash usage ('{word_pair}'): ensure the intended meaning is clear to your audience."
        else:
            return f"Evaluate slash usage for clarity and appropriateness in context."

    def _generate_smart_slash_suggestions(self, slash_token: 'Token', evidence_score: float, sent: 'Span', context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for slash usage."""
        
        suggestions = []
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        
        # Get the word pair for specific suggestions
        token_sent_idx = slash_token.i - slash_token.sent.start
        
        if 0 < token_sent_idx < len(sent) - 1:
            prev_word = sent[token_sent_idx - 1].text
            next_word = sent[token_sent_idx + 1].text
            
            # High evidence suggestions
            if evidence_score > 0.7:
                suggestions.append(f"Replace '{prev_word}/{next_word}' with '{prev_word} or {next_word}' if you mean one option.")
                suggestions.append(f"Use '{prev_word} and {next_word}' if you mean both options.")
                suggestions.append("Consider 'and/or' only if truly necessary, but prefer clearer alternatives.")
            
            # Medium evidence suggestions
            elif evidence_score > 0.4:
                suggestions.append(f"Clarify whether '{prev_word}/{next_word}' means 'and' or 'or'.")
                suggestions.append("Consider rewriting to avoid the ambiguous slash construction.")
                
                # Specific suggestions for common patterns
                if prev_word.lower() in ['he', 'she'] or next_word.lower() in ['he', 'she']:
                    suggestions.append("Use 'they' or rewrite to avoid gendered pronouns if appropriate.")
                elif prev_word.lower() in ['his', 'her'] or next_word.lower() in ['his', 'her']:
                    suggestions.append("Use 'their' or rewrite to avoid gendered pronouns if appropriate.")
        
        # Content-specific suggestions
        if content_type == 'legal' and evidence_score > 0.5:
            suggestions.append("Legal writing requires precise language: avoid ambiguous constructions.")
        elif content_type == 'academic' and evidence_score > 0.5:
            suggestions.append("Academic writing benefits from explicit logical relationships between concepts.")
        elif audience in ['general', 'consumer'] and evidence_score > 0.4:
            suggestions.append("General audiences benefit from explicit rather than abbreviated expressions.")
        elif content_type == 'educational' and evidence_score > 0.4:
            suggestions.append("Educational content should model clear, unambiguous expression.")
        
        # General guidance
        if len(suggestions) < 2:
            suggestions.append("Slashes can be ambiguous: spell out the intended logical relationship.")
            suggestions.append("Use 'and' for inclusion, 'or' for alternatives, 'and/or' only when necessary.")
        
        return suggestions[:3]