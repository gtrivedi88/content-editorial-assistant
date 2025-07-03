"""
Dashes Rule
Based on IBM Style Guide topic: "Dashes"
"""
from typing import List, Dict, Any, Set, Tuple, Optional
import re
from .base_punctuation_rule import BasePunctuationRule

class DashesRule(BasePunctuationRule):
    """
    Comprehensive dash usage checker using morphological spaCy analysis with linguistic anchors.
    Handles em dashes, en dashes, hyphens, and their various contexts in technical writing.
    """
    
    def _get_rule_type(self) -> str:
        return 'dashes'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        
        # Fallback to regex-based analysis if nlp is unavailable
        if not nlp:
            return self._analyze_with_regex(text, sentences)
        
        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            errors.extend(self._analyze_sentence_with_nlp(doc, sentence, i))
            
        return errors

    def _analyze_sentence_with_nlp(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Comprehensive NLP-based dash analysis using linguistic anchors."""
        errors = []
        
        # Check various dash usage patterns
        errors.extend(self._check_em_dash_usage(doc, sentence, sentence_index))
        errors.extend(self._check_en_dash_usage(doc, sentence, sentence_index))
        errors.extend(self._check_hyphen_usage(doc, sentence, sentence_index))
        errors.extend(self._check_dash_spacing(doc, sentence, sentence_index))
        errors.extend(self._check_compound_modifier_patterns(doc, sentence, sentence_index))
        errors.extend(self._check_dash_alternatives(doc, sentence, sentence_index))
        
        return errors

    def _check_em_dash_usage(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check em dash usage using linguistic anchors."""
        errors = []
        
        for token in doc:
            if token.text == '—':
                context_type = self._determine_em_dash_context(token, doc)
                
                if context_type == 'parenthetical':
                    # Check if properly paired
                    if not self._is_em_dash_properly_paired(token, doc):
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="Em dashes used for parenthetical expressions should be paired.",
                            suggestions=["Use a pair of em dashes or consider commas/parentheses instead."],
                            severity='medium'
                        ))
                
                elif context_type == 'break_in_thought':
                    # In technical writing, suggest alternatives
                    if self._is_technical_writing_context(doc):
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="Em dashes indicating breaks in thought should be avoided in technical writing.",
                            suggestions=["Use a period to end the sentence.", 
                                       "Rewrite as two separate sentences.",
                                       "Use parentheses for additional information."],
                            severity='medium'
                        ))
                
                elif context_type == 'range':
                    # Should use en dash instead
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message="Use en dash (–) instead of em dash (—) for ranges.",
                        suggestions=["Replace with en dash (–) for ranges."],
                        severity='high'
                    ))
                
                elif context_type == 'attribution':
                    # Check if at end of quotation
                    if not self._is_proper_attribution_context(token, doc):
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="Em dash for attribution should follow quoted material.",
                            suggestions=["Move em dash to follow the quotation.", 
                                       "Use standard citation format instead."],
                            severity='medium'
                        ))
        
        return errors

    def _check_en_dash_usage(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check en dash usage using linguistic anchors."""
        errors = []
        
        for token in doc:
            if token.text == '–':
                context_type = self._determine_en_dash_context(token, doc)
                
                if context_type == 'compound_adjective':
                    # Check if properly used in compound adjective
                    if not self._is_proper_compound_adjective_context(token, doc):
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="En dash in compound adjective may not be necessary.",
                            suggestions=["Consider using a hyphen for compound adjectives.",
                                       "Check if the compound modifier needs punctuation."],
                            severity='low'
                        ))
                
                elif context_type == 'range':
                    # Check proper range format
                    if not self._is_proper_range_format(token, doc):
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="En dash range format may be incorrect.",
                            suggestions=["Ensure proper spacing around en dash in ranges.",
                                       "Consider using 'to' or 'through' for clarity."],
                            severity='medium'
                        ))
                
                elif context_type == 'connection':
                    # Check if it's a proper connection context
                    if not self._is_proper_connection_context(token, doc):
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="En dash connection usage should be clear and purposeful.",
                            suggestions=["Consider using 'and' or 'to' for clarity.",
                                       "Ensure the connection is meaningful."],
                            severity='low'
                        ))
        
        return errors

    def _check_hyphen_usage(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check hyphen usage using linguistic anchors."""
        errors = []
        
        for token in doc:
            if token.text == '-':
                context_type = self._determine_hyphen_context(token, doc)
                
                if context_type == 'compound_word':
                    # Check if hyphenation is necessary
                    if not self._is_hyphenation_necessary(token, doc):
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="Hyphen in compound word may not be necessary.",
                            suggestions=["Check if the compound word is typically written as one word.",
                                       "Consider current dictionary standards."],
                            severity='low'
                        ))
                
                elif context_type == 'prefix':
                    # Check prefix hyphenation rules
                    if not self._is_prefix_hyphenation_correct(token, doc):
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="Prefix hyphenation may be incorrect.",
                            suggestions=["Most prefixes don't require hyphens.",
                                       "Check for specific prefix rules (re-, pre-, etc.)."],
                            severity='medium'
                        ))
                
                elif context_type == 'line_break':
                    # Should not appear in final text
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message="Line-break hyphens should not appear in final text.",
                        suggestions=["Remove line-break hyphens from final text.",
                                   "Ensure proper word joining."],
                        severity='high'
                    ))
                
                elif context_type == 'range':
                    # Should use en dash instead
                    if self._should_use_en_dash_for_range(token, doc):
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="Use en dash (–) instead of hyphen (-) for ranges.",
                            suggestions=["Replace hyphen with en dash for ranges."],
                            severity='medium'
                        ))
        
        return errors

    def _check_dash_spacing(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check spacing around dashes using linguistic anchors."""
        errors = []
        
        for token in doc:
            if token.text in ['—', '–', '-']:
                spacing_issues = self._analyze_dash_spacing(token, doc)
                
                for issue in spacing_issues:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message=issue['message'],
                        suggestions=issue['suggestions'],
                        severity=issue['severity']
                    ))
        
        return errors

    def _check_compound_modifier_patterns(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check compound modifier patterns using linguistic anchors."""
        errors = []
        
        # Find potential compound modifiers
        compound_modifiers = self._find_compound_modifiers(doc)
        
        for modifier_span in compound_modifiers:
            start_idx, end_idx = modifier_span
            
            # Check if proper punctuation is used
            punctuation_analysis = self._analyze_compound_modifier_punctuation(doc, start_idx, end_idx)
            
            if punctuation_analysis['needs_hyphen'] and not punctuation_analysis['has_hyphen']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Compound modifier may need hyphenation.",
                    suggestions=["Consider hyphenating the compound modifier for clarity."],
                    severity='low'
                ))
            
            elif punctuation_analysis['has_unnecessary_hyphen']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Compound modifier may have unnecessary hyphenation.",
                    suggestions=["Consider removing unnecessary hyphens."],
                    severity='low'
                ))
        
        return errors

    def _check_dash_alternatives(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check for better alternatives to dashes using linguistic anchors."""
        errors = []
        
        for token in doc:
            if token.text in ['—', '–']:
                alternatives = self._suggest_dash_alternatives(token, doc)
                
                if alternatives:
                    for alt in alternatives:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message=alt['message'],
                            suggestions=alt['suggestions'],
                            severity=alt['severity']
                        ))
        
        return errors

    # Helper methods using linguistic anchors

    def _determine_em_dash_context(self, token, doc) -> str:
        """Linguistic anchor: Determine the context of em dash usage."""
        # Check if it's parenthetical (interruption in sentence)
        if self._is_parenthetical_em_dash(token, doc):
            return 'parenthetical'
        
        # Check if it's indicating a break in thought
        if self._is_break_in_thought(token, doc):
            return 'break_in_thought'
        
        # Check if it's used for a range (incorrect usage)
        if self._is_range_context(token, doc):
            return 'range'
        
        # Check if it's used for attribution
        if self._is_attribution_context(token, doc):
            return 'attribution'
        
        return 'unknown'

    def _determine_en_dash_context(self, token, doc) -> str:
        """Linguistic anchor: Determine the context of en dash usage."""
        # Check if it's in a compound adjective
        if self._is_compound_adjective_context(token, doc):
            return 'compound_adjective'
        
        # Check if it's indicating a range
        if self._is_range_context(token, doc):
            return 'range'
        
        # Check if it's connecting equal elements
        if self._is_connection_context(token, doc):
            return 'connection'
        
        return 'unknown'

    def _determine_hyphen_context(self, token, doc) -> str:
        """Linguistic anchor: Determine the context of hyphen usage."""
        # Check if it's in a compound word
        if self._is_compound_word_context(token, doc):
            return 'compound_word'
        
        # Check if it's with a prefix
        if self._is_prefix_context(token, doc):
            return 'prefix'
        
        # Check if it's a line break remnant
        if self._is_line_break_context(token, doc):
            return 'line_break'
        
        # Check if it's used for a range (should be en dash)
        if self._is_range_context(token, doc):
            return 'range'
        
        return 'unknown'

    def _is_parenthetical_em_dash(self, token, doc) -> bool:
        """Check if em dash is used parenthetically."""
        # Look for sentence structure that indicates parenthetical use
        # Em dashes used parenthetically typically interrupt the main clause
        before_tokens = doc[:token.i]
        after_tokens = doc[token.i + 1:]
        
        # Check if both sides could form a complete sentence when joined
        has_main_clause_before = any(t.dep_ == 'ROOT' for t in before_tokens)
        has_continuation_after = any(t.pos_ in ['VERB', 'NOUN', 'ADJ'] for t in after_tokens[:3])
        
        return has_main_clause_before and has_continuation_after

    def _is_break_in_thought(self, token, doc) -> bool:
        """Check if em dash indicates a break in thought."""
        # Typically at the end of a sentence or before a significant shift
        return token.i >= len(doc) - 3  # Near end of sentence

    def _is_range_context(self, token, doc) -> bool:
        """Linguistic anchor: Check if dash is used for ranges."""
        if token.i == 0 or token.i >= len(doc) - 1:
            return False
        
        prev_token = doc[token.i - 1]
        next_token = doc[token.i + 1]
        
        # Check for numerical ranges
        if prev_token.like_num and next_token.like_num:
            return True
        
        # Check for date ranges
        if self._is_date_component(prev_token) and self._is_date_component(next_token):
            return True
        
        # Check for time ranges
        if self._is_time_component(prev_token) and self._is_time_component(next_token):
            return True
        
        # Check for page ranges
        context_text = doc.text.lower()
        if any(indicator in context_text for indicator in ['page', 'pp', 'p.']):
            return prev_token.like_num and next_token.like_num
        
        return False

    def _is_attribution_context(self, token, doc) -> bool:
        """Check if em dash is used for attribution."""
        # Look for quotation marks before the dash
        before_tokens = doc[:token.i]
        has_quotation = any(t.text in ['"', "'", '"', '"'] for t in before_tokens[-5:])
        
        return has_quotation

    def _is_compound_adjective_context(self, token, doc) -> bool:
        """Check if dash is in compound adjective context."""
        if token.i == 0 or token.i >= len(doc) - 1:
            return False
        
        prev_token = doc[token.i - 1]
        next_token = doc[token.i + 1]
        
        # Check if surrounded by adjectives or adverbs
        return (prev_token.pos_ in ['ADJ', 'ADV'] and 
                next_token.pos_ in ['ADJ', 'NOUN'])

    def _is_connection_context(self, token, doc) -> bool:
        """Check if dash connects equal elements."""
        if token.i == 0 or token.i >= len(doc) - 1:
            return False
        
        prev_token = doc[token.i - 1]
        next_token = doc[token.i + 1]
        
        # Check if connecting proper nouns (like place names)
        return (prev_token.pos_ == 'PROPN' and next_token.pos_ == 'PROPN')

    def _is_compound_word_context(self, token, doc) -> bool:
        """Check if hyphen is in compound word context."""
        if token.i == 0 or token.i >= len(doc) - 1:
            return False
        
        prev_token = doc[token.i - 1]
        next_token = doc[token.i + 1]
        
        # Check if forming a compound word
        return (prev_token.pos_ in ['NOUN', 'ADJ'] and 
                next_token.pos_ in ['NOUN', 'ADJ'])

    def _is_prefix_context(self, token, doc) -> bool:
        """Check if hyphen is with a prefix."""
        if token.i == 0 or token.i >= len(doc) - 1:
            return False
        
        prev_token = doc[token.i - 1]
        
        # Common prefixes that might use hyphens
        common_prefixes = {
            'anti', 'co', 'de', 'dis', 'ex', 'extra', 'inter', 'micro',
            'mid', 'mini', 'multi', 'non', 'over', 'post', 'pre', 'pro',
            'pseudo', 'quasi', 're', 'semi', 'sub', 'super', 'trans', 'ultra'
        }
        
        return prev_token.lemma_ in common_prefixes

    def _is_line_break_context(self, token, doc) -> bool:
        """Check if hyphen is from line break."""
        # Look for patterns that suggest line breaks
        if token.i >= len(doc) - 1:
            return False
        
        next_token = doc[token.i + 1]
        
        # Check if next token starts with lowercase (suggesting word continuation)
        return (next_token.text and next_token.text[0].islower() and 
                not next_token.text.isdigit())

    def _is_technical_writing_context(self, doc) -> bool:
        """Determine if this is technical writing context."""
        # Look for technical indicators
        technical_indicators = {
            'system', 'process', 'method', 'algorithm', 'function', 'protocol',
            'interface', 'implementation', 'configuration', 'parameter', 'variable',
            'database', 'server', 'client', 'api', 'framework', 'library'
        }
        
        doc_text = doc.text.lower()
        return any(indicator in doc_text for indicator in technical_indicators)

    def _is_em_dash_properly_paired(self, token, doc) -> bool:
        """Check if em dash is properly paired."""
        em_dash_positions = [i for i, t in enumerate(doc) if t.text == '—']
        
        # If only one em dash, it's not paired
        if len(em_dash_positions) == 1:
            return False
        
        # Check if current token is part of a proper pair
        current_pos = token.i
        if current_pos in em_dash_positions:
            # Find if there's a matching dash
            for pos in em_dash_positions:
                if pos != current_pos and abs(pos - current_pos) > 1:
                    return True
        
        return False

    def _is_proper_attribution_context(self, token, doc) -> bool:
        """Check if em dash is properly used for attribution."""
        # Should be near end of sentence after quoted material
        return token.i >= len(doc) - 5

    def _is_proper_compound_adjective_context(self, token, doc) -> bool:
        """Check if en dash is properly used in compound adjective."""
        if token.i == 0 or token.i >= len(doc) - 1:
            return False
        
        # Look for the noun being modified
        for i in range(token.i + 1, min(token.i + 3, len(doc))):
            if doc[i].pos_ == 'NOUN':
                return True
        
        return False

    def _is_proper_range_format(self, token, doc) -> bool:
        """Check if en dash range format is correct."""
        # Check spacing and context
        if token.i == 0 or token.i >= len(doc) - 1:
            return False
        
        prev_token = doc[token.i - 1]
        next_token = doc[token.i + 1]
        
        # Should not have spaces around en dash in ranges
        has_space_before = len(prev_token.text_with_ws) > len(prev_token.text)
        has_space_after = token.whitespace_
        
        return not has_space_before and not has_space_after

    def _is_proper_connection_context(self, token, doc) -> bool:
        """Check if en dash connection is meaningful."""
        if token.i == 0 or token.i >= len(doc) - 1:
            return False
        
        prev_token = doc[token.i - 1]
        next_token = doc[token.i + 1]
        
        # Should connect elements of equal weight
        return prev_token.pos_ == next_token.pos_

    def _is_hyphenation_necessary(self, token, doc) -> bool:
        """Check if hyphenation is necessary for compound word."""
        if token.i == 0 or token.i >= len(doc) - 1:
            return False
        
        prev_token = doc[token.i - 1]
        next_token = doc[token.i + 1]
        
        # Check if it's a well-established compound
        compound_word = f"{prev_token.text}-{next_token.text}"
        
        # This would need a dictionary lookup in a real implementation
        # For now, check common patterns
        if prev_token.pos_ == 'ADJ' and next_token.pos_ == 'NOUN':
            return True  # Adjective-noun compounds often need hyphens
        
        return False

    def _is_prefix_hyphenation_correct(self, token, doc) -> bool:
        """Check if prefix hyphenation follows rules."""
        if token.i == 0 or token.i >= len(doc) - 1:
            return False
        
        prev_token = doc[token.i - 1]
        next_token = doc[token.i + 1]
        
        # Most prefixes don't need hyphens
        # Exceptions: when base word is capitalized, or to avoid confusion
        base_word_capitalized = next_token.text and next_token.text[0].isupper()
        
        return base_word_capitalized

    def _should_use_en_dash_for_range(self, token, doc) -> bool:
        """Check if hyphen should be en dash for range."""
        return self._is_range_context(token, doc)

    def _analyze_dash_spacing(self, token, doc) -> List[Dict[str, Any]]:
        """Analyze spacing around dashes."""
        issues = []
        
        if token.text == '—':  # Em dash
            # Em dashes typically have no spaces
            if token.i > 0 and doc[token.i - 1].text_with_ws.endswith(' '):
                issues.append({
                    'message': "Em dash typically has no space before it.",
                    'suggestions': ["Remove space before em dash."],
                    'severity': 'low'
                })
            
            if token.whitespace_:
                issues.append({
                    'message': "Em dash typically has no space after it.",
                    'suggestions': ["Remove space after em dash."],
                    'severity': 'low'
                })
        
        elif token.text == '–':  # En dash
            # En dashes in ranges have no spaces
            if self._is_range_context(token, doc):
                if token.i > 0 and doc[token.i - 1].text_with_ws.endswith(' '):
                    issues.append({
                        'message': "En dash in ranges should have no space before it.",
                        'suggestions': ["Remove space before en dash in range."],
                        'severity': 'medium'
                    })
                
                if token.whitespace_:
                    issues.append({
                        'message': "En dash in ranges should have no space after it.",
                        'suggestions': ["Remove space after en dash in range."],
                        'severity': 'medium'
                    })
        
        return issues

    def _find_compound_modifiers(self, doc) -> List[Tuple[int, int]]:
        """Find potential compound modifiers."""
        modifiers = []
        
        for token in doc:
            if token.pos_ == 'ADJ':
                # Look for adjective + noun or adjective + adjective patterns
                for i in range(token.i + 1, min(token.i + 3, len(doc))):
                    if doc[i].pos_ in ['NOUN', 'ADJ']:
                        modifiers.append((token.i, i))
                        break
        
        return modifiers

    def _analyze_compound_modifier_punctuation(self, doc, start_idx, end_idx) -> Dict[str, bool]:
        """Analyze punctuation in compound modifiers."""
        result = {
            'needs_hyphen': False,
            'has_hyphen': False,
            'has_unnecessary_hyphen': False
        }
        
        # Check if there's a hyphen between the tokens
        for i in range(start_idx, end_idx):
            if doc[i].text in ['-', '–']:
                result['has_hyphen'] = True
                break
        
        # Determine if hyphen is needed
        start_token = doc[start_idx]
        end_token = doc[end_idx]
        
        # Check if it's modifying a noun
        if end_idx < len(doc) - 1 and doc[end_idx + 1].pos_ == 'NOUN':
            result['needs_hyphen'] = True
        
        return result

    def _suggest_dash_alternatives(self, token, doc) -> List[Dict[str, Any]]:
        """Suggest alternatives to dashes."""
        alternatives = []
        
        if token.text == '—':
            if self._is_parenthetical_em_dash(token, doc):
                alternatives.append({
                    'message': "Consider using parentheses instead of em dashes for parenthetical information.",
                    'suggestions': ["Use parentheses ( ) for additional information.",
                               "Use commas for non-essential information."],
                    'severity': 'low'
                })
            
            if self._is_break_in_thought(token, doc):
                alternatives.append({
                    'message': "Consider ending the sentence instead of using em dash for break in thought.",
                    'suggestions': ["End the sentence with a period.",
                               "Start a new sentence for the new thought."],
                    'severity': 'low'
                })
        
        return alternatives

    # Helper methods for date/time detection
    def _is_date_component(self, token) -> bool:
        """Check if token is a date component."""
        if token.like_num:
            return True
        
        # Check for month names
        months = {'january', 'february', 'march', 'april', 'may', 'june',
                 'july', 'august', 'september', 'october', 'november', 'december',
                 'jan', 'feb', 'mar', 'apr', 'may', 'jun',
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'}
        
        return token.lemma_.lower() in months

    def _is_time_component(self, token) -> bool:
        """Check if token is a time component."""
        if token.like_num:
            return True
        
        # Check for time indicators
        time_indicators = {'am', 'pm', 'a.m.', 'p.m.', 'hour', 'minute', 'second'}
        
        return token.lemma_.lower() in time_indicators

    def _analyze_with_regex(self, text: str, sentences: List[str]) -> List[Dict[str, Any]]:
        """Fallback regex-based analysis when NLP is unavailable."""
        errors = []
        
        for i, sentence in enumerate(sentences):
            # Basic dash patterns detectable without NLP
            
            # Pattern 1: Multiple consecutive dashes
            if re.search(r'[-–—]{2,}', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Multiple consecutive dashes detected.",
                    suggestions=["Use a single appropriate dash type.",
                               "Consider alternative punctuation."],
                    severity='medium'
                ))
            
            # Pattern 2: Em dash at start of sentence
            if sentence.strip().startswith('—'):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Sentence should not begin with an em dash.",
                    suggestions=["Remove the em dash or rewrite the sentence."],
                    severity='medium'
                ))
            
            # Pattern 3: Hyphen used for ranges (basic detection)
            if re.search(r'\b\d+\s*-\s*\d+\b', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Consider using en dash (–) instead of hyphen (-) for number ranges.",
                    suggestions=["Use en dash (–) for ranges like '1–10'."],
                    severity='low'
                ))
            
            # Pattern 4: Excessive em dash usage
            em_dash_count = sentence.count('—')
            if em_dash_count > 2:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Excessive use of em dashes may impact readability.",
                    suggestions=["Consider using other punctuation marks.",
                               "Break into multiple sentences."],
                    severity='medium'
                ))
        
        return errors
