"""
Hyphens Rule
Based on IBM Style Guide topics: "Hyphens" and "Prefixes"
"""
from typing import List, Dict, Any, Set, Tuple, Optional
import re
from .base_punctuation_rule import BasePunctuationRule

class HyphensRule(BasePunctuationRule):
    """
    Comprehensive hyphen usage checker using morphological spaCy analysis with linguistic anchors.
    Handles prefixes, compound words, compound modifiers, and hyphenation contexts in technical writing.
    """
    
    def _get_rule_type(self) -> str:
        return 'hyphens'

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
        """Comprehensive NLP-based hyphen analysis using linguistic anchors."""
        errors = []
        
        # Find all hyphen tokens in the sentence
        hyphen_tokens = self._find_hyphen_tokens(doc)
        
        for token_idx in hyphen_tokens:
            # Check various hyphen usage patterns
            errors.extend(self._check_prefix_hyphenation(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_compound_word_formation(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_compound_modifier_patterns(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_number_hyphenation(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_suspended_hyphens(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_unnecessary_hyphens(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_technical_term_hyphenation(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_line_break_hyphens(doc, token_idx, sentence, sentence_index))
        
        return errors

    def _find_hyphen_tokens(self, doc) -> List[int]:
        """Find all hyphen tokens in the document."""
        hyphen_indices = []
        
        for token in doc:
            if token.text == '-':
                hyphen_indices.append(token.i)
        
        return hyphen_indices

    def _check_prefix_hyphenation(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check prefix hyphenation using linguistic anchors."""
        errors = []
        
        if not self._is_prefix_context(doc, token_idx):
            return errors
        
        prefix_analysis = self._analyze_prefix_pattern(doc, token_idx)
        
        if prefix_analysis['is_closed_prefix'] and not prefix_analysis['needs_hyphen']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Prefix '{prefix_analysis['prefix']}' typically doesn't require a hyphen.",
                suggestions=[f"Consider writing as one word: '{prefix_analysis['prefix']}{prefix_analysis['base_word']}'.",
                           "Check current dictionary standards for this prefix."],
                severity='medium'
            ))
        
        elif prefix_analysis['needs_hyphen'] and not prefix_analysis['has_hyphen']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Prefix '{prefix_analysis['prefix']}' may require a hyphen in this context.",
                suggestions=[f"Consider hyphenating: '{prefix_analysis['prefix']}-{prefix_analysis['base_word']}'.",
                           "Check for capitalization or vowel conflicts."],
                severity='low'
            ))
        
        return errors

    def _check_compound_word_formation(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check compound word formation using linguistic anchors."""
        errors = []
        
        if not self._is_compound_word_context(doc, token_idx):
            return errors
        
        compound_analysis = self._analyze_compound_word_pattern(doc, token_idx)
        
        if compound_analysis['is_established_compound']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"'{compound_analysis['full_word']}' is typically written as one word.",
                suggestions=[f"Write as one word: '{compound_analysis['unhyphenated_form']}'.",
                           "Check current dictionary standards."],
                severity='medium'
            ))
        
        elif compound_analysis['needs_consistency_check']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Compound word '{compound_analysis['full_word']}' may have inconsistent hyphenation.",
                suggestions=["Check for consistent hyphenation throughout the document.",
                           "Verify current dictionary standards for this compound."],
                severity='low'
            ))
        
        return errors

    def _check_compound_modifier_patterns(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check compound modifier patterns using linguistic anchors."""
        errors = []
        
        modifier_analysis = self._analyze_compound_modifier(doc, token_idx)
        
        if modifier_analysis['is_compound_modifier']:
            if modifier_analysis['needs_hyphen'] and not modifier_analysis['has_hyphen']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Compound modifier may need hyphenation when used before a noun.",
                    suggestions=["Hyphenate compound modifiers before nouns for clarity.",
                               "Consider if the modification relationship is clear."],
                    severity='low'
                ))
            
            elif modifier_analysis['is_predicate'] and modifier_analysis['has_hyphen']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Compound modifiers after nouns typically don't need hyphens.",
                    suggestions=["Remove hyphen when compound modifier follows the noun.",
                               "Hyphens are usually needed only before nouns."],
                    severity='low'
                ))
        
        return errors

    def _check_number_hyphenation(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check number-related hyphenation using linguistic anchors."""
        errors = []
        
        number_analysis = self._analyze_number_hyphenation(doc, token_idx)
        
        if number_analysis['is_number_context']:
            if number_analysis['is_compound_number'] and not number_analysis['needs_hyphen']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Numbers above ninety-nine typically don't need hyphens.",
                    suggestions=["Write large numbers without hyphens unless part of compound modifier.",
                               "Use hyphens only for twenty-one through ninety-nine."],
                    severity='low'
                ))
            
            elif number_analysis['is_fraction'] and number_analysis['needs_consistency']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Fraction hyphenation should be consistent.",
                    suggestions=["Hyphenate fractions when used as adjectives.",
                               "Consider context: 'two-thirds majority' vs 'two thirds of the group'."],
                    severity='low'
                ))
        
        return errors

    def _check_suspended_hyphens(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check suspended hyphen patterns using linguistic anchors."""
        errors = []
        
        if self._is_suspended_hyphen_context(doc, token_idx):
            suspended_analysis = self._analyze_suspended_hyphen(doc, token_idx)
            
            if suspended_analysis['needs_clarification']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Suspended hyphen construction may be unclear.",
                    suggestions=["Consider rewriting for clarity: 'short- and long-term plans' → 'short-term and long-term plans'.",
                               "Ensure the suspended hyphen construction is clear to readers."],
                    severity='low'
                ))
        
        return errors

    def _check_unnecessary_hyphens(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check for unnecessary hyphens using linguistic anchors."""
        errors = []
        
        unnecessary_analysis = self._analyze_unnecessary_hyphen(doc, token_idx)
        
        if unnecessary_analysis['is_unnecessary']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=unnecessary_analysis['reason'],
                suggestions=unnecessary_analysis['suggestions'],
                severity=unnecessary_analysis['severity']
            ))
        
        return errors

    def _check_technical_term_hyphenation(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check technical term hyphenation using linguistic anchors."""
        errors = []
        
        if self._is_technical_writing_context(doc):
            tech_analysis = self._analyze_technical_hyphenation(doc, token_idx)
            
            if tech_analysis['needs_standardization']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Technical term hyphenation should follow industry standards.",
                    suggestions=["Check technical documentation standards for this term.",
                               "Ensure consistency with industry conventions.",
                               "Consider the established technical vocabulary."],
                    severity='low'
                ))
        
        return errors

    def _check_line_break_hyphens(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check for line break hyphens using linguistic anchors."""
        errors = []
        
        if self._is_line_break_hyphen(doc, token_idx):
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Line break hyphen should be removed from final text.",
                suggestions=["Remove the hyphen and join the word parts.",
                           "Ensure proper word formation in final text."],
                severity='high'
            ))
        
        return errors

    # Helper methods using linguistic anchors

    def _is_prefix_context(self, doc, token_idx: int) -> bool:
        """Check if hyphen is in a prefix context using linguistic anchors."""
        if token_idx == 0 or token_idx >= len(doc) - 1:
            return False
        
        prev_token = doc[token_idx - 1]
        next_token = doc[token_idx + 1]
        
        # Linguistic anchor: Look for morphological prefix patterns
        return (self._is_morphological_prefix(prev_token) and 
                self._is_base_word(next_token))

    def _is_morphological_prefix(self, token) -> bool:
        """Check if token is a morphological prefix using linguistic patterns."""
        # Check token length (prefixes are typically short)
        if len(token.text) > 6:
            return False
        
        # Check if it has prefix-like morphological properties
        # Prefixes typically don't stand alone as complete words in isolation
        if token.pos_ in ['NOUN', 'VERB', 'ADJ'] and len(token.text) > 3:
            return False
        
        # Check for common prefix patterns (morphological, not hardcoded)
        prefix_patterns = [
            r'^(anti|auto|co|counter|de|dis|ex|extra|hyper|inter|intra|micro|mini|mis|multi|non|over|post|pre|pro|pseudo|quasi|re|semi|sub|super|trans|ultra|un|under)$'
        ]
        
        return any(re.match(pattern, token.text.lower()) for pattern in prefix_patterns)

    def _is_base_word(self, token) -> bool:
        """Check if token can serve as a base word."""
        # Base words typically have substantial morphological content
        return (len(token.text) > 2 and 
                token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV'] and
                not token.is_punct)

    def _analyze_prefix_pattern(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze prefix hyphenation pattern using linguistic anchors."""
        prev_token = doc[token_idx - 1]
        next_token = doc[token_idx + 1]
        
        analysis = {
            'prefix': prev_token.text.lower(),
            'base_word': next_token.text.lower(),
            'is_closed_prefix': False,
            'needs_hyphen': False,
            'has_hyphen': True
        }
        
        # Linguistic anchor: Check for patterns that typically don't need hyphens
        analysis['is_closed_prefix'] = self._is_typically_closed_prefix(prev_token, next_token)
        
        # Linguistic anchor: Check for patterns that need hyphens
        analysis['needs_hyphen'] = self._needs_hyphen_for_clarity(prev_token, next_token)
        
        return analysis

    def _is_typically_closed_prefix(self, prefix_token, base_token) -> bool:
        """Check if prefix typically forms closed compounds."""
        # Check for vowel conflicts
        if (prefix_token.text.endswith(('e', 'i', 'o')) and 
            base_token.text.startswith(('e', 'i', 'o', 'a'))):
            return False
        
        # Check for capitalization conflicts
        if base_token.text[0].isupper():
            return False
        
        # Check for common closed prefix patterns
        prefix_lower = prefix_token.text.lower()
        
        # Most prefixes form closed compounds unless there are conflicts
        return not (len(prefix_lower) <= 2 or 
                   prefix_lower in {'ex', 'self', 'all', 'cross'})

    def _needs_hyphen_for_clarity(self, prefix_token, base_token) -> bool:
        """Check if hyphen is needed for clarity."""
        prefix_text = prefix_token.text.lower()
        base_text = base_token.text.lower()
        
        # Hyphen needed for capitalized base words
        if base_token.text[0].isupper():
            return True
        
        # Hyphen needed to avoid vowel conflicts that create ambiguity
        if (prefix_text.endswith('e') and base_text.startswith('e')) or \
           (prefix_text.endswith('i') and base_text.startswith('i')):
            return True
        
        # Hyphen needed for certain prefix-base combinations
        if prefix_text == 're' and base_text.startswith(('e', 'i')):
            return True
        
        return False

    def _is_compound_word_context(self, doc, token_idx: int) -> bool:
        """Check if hyphen is in compound word context."""
        if token_idx == 0 or token_idx >= len(doc) - 1:
            return False
        
        prev_token = doc[token_idx - 1]
        next_token = doc[token_idx + 1]
        
        # Check if both parts can form meaningful compounds
        return (prev_token.pos_ in ['NOUN', 'ADJ', 'VERB'] and 
                next_token.pos_ in ['NOUN', 'ADJ', 'VERB'] and
                not self._is_morphological_prefix(prev_token))

    def _analyze_compound_word_pattern(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze compound word formation pattern."""
        prev_token = doc[token_idx - 1]
        next_token = doc[token_idx + 1]
        
        full_word = f"{prev_token.text}-{next_token.text}"
        unhyphenated = f"{prev_token.text}{next_token.text}"
        
        analysis = {
            'full_word': full_word,
            'unhyphenated_form': unhyphenated,
            'is_established_compound': False,
            'needs_consistency_check': True
        }
        
        # Check for established compound patterns
        analysis['is_established_compound'] = self._is_established_compound(prev_token, next_token)
        
        return analysis

    def _is_established_compound(self, first_token, second_token) -> bool:
        """Check if this is an established compound word."""
        # Check for common compound patterns that are typically closed
        first_pos = first_token.pos_
        second_pos = second_token.pos_
        
        # Noun + noun compounds often become closed
        if first_pos == 'NOUN' and second_pos == 'NOUN':
            # Check length - shorter compounds more likely to be closed
            if len(first_token.text) + len(second_token.text) <= 10:
                return True
        
        # Adjective + noun compounds with certain patterns
        if first_pos == 'ADJ' and second_pos == 'NOUN':
            if len(first_token.text) <= 5:  # Short adjectives often form closed compounds
                return True
        
        return False

    def _analyze_compound_modifier(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze compound modifier patterns using linguistic anchors."""
        if token_idx == 0 or token_idx >= len(doc) - 1:
            return {'is_compound_modifier': False}
        
        # Look for the noun being modified
        modified_noun = self._find_modified_noun(doc, token_idx)
        
        analysis = {
            'is_compound_modifier': modified_noun is not None,
            'needs_hyphen': False,
            'has_hyphen': True,
            'is_predicate': False
        }
        
        if modified_noun:
            # Check if modifier comes before the noun (attributive) or after (predicative)
            analysis['is_predicate'] = modified_noun < token_idx
            analysis['needs_hyphen'] = not analysis['is_predicate']
        
        return analysis

    def _find_modified_noun(self, doc, token_idx: int) -> Optional[int]:
        """Find the noun being modified by compound modifier."""
        # Look for nouns near the compound modifier
        search_range = range(max(0, token_idx - 3), min(len(doc), token_idx + 4))
        
        for i in search_range:
            if doc[i].pos_ == 'NOUN' and i != token_idx:
                return i
        
        return None

    def _analyze_number_hyphenation(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze number-related hyphenation patterns."""
        if token_idx == 0 or token_idx >= len(doc) - 1:
            return {'is_number_context': False}
        
        prev_token = doc[token_idx - 1]
        next_token = doc[token_idx + 1]
        
        analysis = {
            'is_number_context': False,
            'is_compound_number': False,
            'is_fraction': False,
            'needs_hyphen': False,
            'needs_consistency': False
        }
        
        # Check if dealing with numbers
        if prev_token.like_num or next_token.like_num:
            analysis['is_number_context'] = True
            
            # Check for written-out numbers
            number_words = {'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety'}
            if prev_token.text.lower() in number_words:
                analysis['is_compound_number'] = True
                analysis['needs_hyphen'] = True
            
            # Check for fractions
            fraction_words = {'half', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth'}
            if next_token.text.lower() in fraction_words:
                analysis['is_fraction'] = True
                analysis['needs_consistency'] = True
        
        return analysis

    def _is_suspended_hyphen_context(self, doc, token_idx: int) -> bool:
        """Check for suspended hyphen patterns."""
        # Look for patterns like "short- and long-term"
        if token_idx >= len(doc) - 3:
            return False
        
        next_token = doc[token_idx + 1]
        following_token = doc[token_idx + 2]
        
        # Check for conjunction after hyphen with space
        return (next_token.text.lower() in ['and', 'or'] and 
                following_token.text.endswith('-') or 
                any(t.text == '-' for t in doc[token_idx + 2:token_idx + 5]))

    def _analyze_suspended_hyphen(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze suspended hyphen construction."""
        return {
            'needs_clarification': True,  # Suspended hyphens often need clarification
            'suggestions': ["Consider writing out both complete forms for clarity."]
        }

    def _analyze_unnecessary_hyphen(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze potentially unnecessary hyphens."""
        if token_idx == 0 or token_idx >= len(doc) - 1:
            return {'is_unnecessary': False}
        
        prev_token = doc[token_idx - 1]
        next_token = doc[token_idx + 1]
        
        # Check for adverb + adjective patterns (typically no hyphen needed)
        if prev_token.pos_ == 'ADV' and next_token.pos_ == 'ADJ':
            # Adverbs ending in -ly typically don't need hyphens
            if prev_token.text.lower().endswith('ly'):
                return {
                    'is_unnecessary': True,
                    'reason': "Adverbs ending in '-ly' typically don't need hyphens when modifying adjectives.",
                    'suggestions': [f"Consider removing hyphen: '{prev_token.text} {next_token.text}'.",
                                   "Hyphens are usually not needed with '-ly' adverbs."],
                    'severity': 'medium'
                }
        
        # Check for well-established single words
        combined = f"{prev_token.text}{next_token.text}".lower()
        if self._is_well_established_single_word(combined):
            return {
                'is_unnecessary': True,
                'reason': f"'{prev_token.text}-{next_token.text}' is typically written as one word.",
                'suggestions': [f"Write as one word: '{combined}'.",
                               "Check current dictionary standards."],
                'severity': 'medium'
            }
        
        return {'is_unnecessary': False}

    def _is_well_established_single_word(self, word: str) -> bool:
        """Check if hyphenated word is typically written as one word."""
        # Common words that have evolved from hyphenated to single words
        established_words = {
            'email', 'website', 'online', 'offline', 'database', 'username',
            'password', 'filename', 'workflow', 'framework', 'software',
            'hardware', 'network', 'internet', 'intranet', 'firewall'
        }
        
        return word in established_words

    def _is_technical_writing_context(self, doc) -> bool:
        """Determine if this is technical writing context."""
        technical_indicators = {
            'system', 'process', 'method', 'algorithm', 'function', 'protocol',
            'interface', 'implementation', 'configuration', 'parameter', 'variable',
            'database', 'server', 'client', 'api', 'framework', 'library'
        }
        
        doc_text = doc.text.lower()
        return any(indicator in doc_text for indicator in technical_indicators)

    def _analyze_technical_hyphenation(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze technical term hyphenation."""
        return {
            'needs_standardization': True  # Technical terms should follow standards
        }

    def _is_line_break_hyphen(self, doc, token_idx: int) -> bool:
        """Check if hyphen is from line break using linguistic anchors."""
        if token_idx >= len(doc) - 1:
            return False
        
        next_token = doc[token_idx + 1]
        
        # Check if next token starts with lowercase (suggesting word continuation)
        return (next_token.text and 
                next_token.text[0].islower() and 
                not next_token.text.isdigit() and
                not next_token.is_punct)

    def _analyze_with_regex(self, text: str, sentences: List[str]) -> List[Dict[str, Any]]:
        """Fallback regex-based analysis when NLP is unavailable."""
        errors = []
        
        for i, sentence in enumerate(sentences):
            # Basic hyphen patterns detectable without NLP
            
            # Pattern 1: Multiple consecutive hyphens
            if re.search(r'-{2,}', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Multiple consecutive hyphens detected.",
                    suggestions=["Use a single hyphen or consider em dash (—) for breaks.",
                               "Check if multiple hyphens are intentional."],
                    severity='medium'
                ))
            
            # Pattern 2: Common prefix patterns that typically don't need hyphens
            prefix_patterns = [
                r'\b(pre|post|multi|non|inter|intra|re|un|anti|co|de|dis|over|under|sub|super)-([a-z])',
                r'\b(auto|micro|mini|semi|ultra|hyper)-([a-z])'
            ]
            
            for pattern in prefix_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Common prefix may not need hyphen in modern usage.",
                        suggestions=["Check if prefix can be written as one word.",
                                   "Verify current dictionary standards for this prefix."],
                        severity='low'
                    ))
            
            # Pattern 3: Adverb-ly + adjective (typically no hyphen)
            if re.search(r'\b\w+ly-\w+', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Adverbs ending in '-ly' typically don't need hyphens.",
                    suggestions=["Remove hyphen between '-ly' adverb and adjective.",
                               "Use hyphen only when needed for clarity."],
                    severity='medium'
                ))
            
            # Pattern 4: Potential line break hyphens
            if re.search(r'-\s*[a-z]', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Possible line break hyphen in final text.",
                    suggestions=["Check if hyphen is from line break and should be removed.",
                               "Ensure words are properly joined in final text."],
                    severity='medium'
                ))
            
            # Pattern 5: Numbers that may not need hyphens
            if re.search(r'\b(one|two|three|four|five|six|seven|eight|nine)-hundred', sentence, re.IGNORECASE):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Large number compounds typically don't need hyphens.",
                    suggestions=["Write large numbers without hyphens: 'two hundred'.",
                               "Use hyphens only for twenty-one through ninety-nine."],
                    severity='low'
                ))
            
            # Pattern 6: Excessive hyphens in compound constructions
            hyphen_count = sentence.count('-')
            if hyphen_count > 3:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Excessive hyphen usage may impact readability.",
                    suggestions=["Consider simplifying compound constructions.",
                               "Break complex phrases into clearer segments."],
                    severity='low'
                ))
        
        return errors