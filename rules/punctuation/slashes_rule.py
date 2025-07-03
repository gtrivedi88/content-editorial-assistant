"""
Slashes Rule
Based on IBM Style Guide topic: "Slashes"
"""
from typing import List, Dict, Any, Set, Tuple, Optional
import re
from .base_punctuation_rule import BasePunctuationRule

class SlashesRule(BasePunctuationRule):
    """
    Comprehensive slashes checker using morphological spaCy analysis with linguistic anchors.
    Handles forward/back slashes, dates, URLs, file paths, alternatives, fractions, and formatting.
    """
    
    def _get_rule_type(self) -> str:
        return 'slashes'

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
        """Comprehensive NLP-based slash analysis using linguistic anchors."""
        errors = []
        
        # Find all slash tokens
        slash_analysis = self._analyze_slash_structure(doc)
        
        # Check each slash usage
        for slash_info in slash_analysis:
            errors.extend(self._analyze_slash_context(doc, slash_info, sentence, sentence_index))
            errors.extend(self._check_slash_spacing(doc, slash_info, sentence, sentence_index))
            errors.extend(self._check_slash_appropriateness(doc, slash_info, sentence, sentence_index))
            errors.extend(self._check_alternative_usage(doc, slash_info, sentence, sentence_index))
            errors.extend(self._check_date_format(doc, slash_info, sentence, sentence_index))
            errors.extend(self._check_fraction_format(doc, slash_info, sentence, sentence_index))
            errors.extend(self._check_technical_context(doc, slash_info, sentence, sentence_index))
        
        return errors

    def _analyze_slash_structure(self, doc) -> List[Dict[str, Any]]:
        """Analyze the structure and context of slashes in the document."""
        slash_positions = []
        
        for i, token in enumerate(doc):
            if token.text in ['/', '\\']:
                slash_positions.append({
                    'index': i,
                    'token': token,
                    'slash_type': 'forward' if token.text == '/' else 'backward',
                    'before_context': self._get_context_before(doc, i),
                    'after_context': self._get_context_after(doc, i),
                    'surrounding_context': self._get_surrounding_context(doc, i)
                })
        
        return slash_positions

    def _get_context_before(self, doc, slash_idx: int) -> Dict[str, Any]:
        """Get context information before the slash."""
        if slash_idx == 0:
            return {'tokens': [], 'text': '', 'pos_tags': [], 'last_char': ''}
        
        # Get previous token
        prev_token = doc[slash_idx - 1]
        
        # Get wider context
        start_idx = max(0, slash_idx - 3)
        tokens_before = doc[start_idx:slash_idx]
        
        return {
            'tokens': tokens_before,
            'text': ''.join([token.text for token in tokens_before]),
            'pos_tags': [token.pos_ for token in tokens_before],
            'last_char': prev_token.text[-1] if prev_token.text else '',
            'last_token': prev_token,
            'is_numeric': self._is_numeric_context(tokens_before),
            'is_alphabetic': self._is_alphabetic_context(tokens_before)
        }

    def _get_context_after(self, doc, slash_idx: int) -> Dict[str, Any]:
        """Get context information after the slash."""
        if slash_idx >= len(doc) - 1:
            return {'tokens': [], 'text': '', 'pos_tags': [], 'first_char': ''}
        
        # Get next token
        next_token = doc[slash_idx + 1]
        
        # Get wider context
        end_idx = min(len(doc), slash_idx + 4)
        tokens_after = doc[slash_idx + 1:end_idx]
        
        return {
            'tokens': tokens_after,
            'text': ''.join([token.text for token in tokens_after]),
            'pos_tags': [token.pos_ for token in tokens_after],
            'first_char': next_token.text[0] if next_token.text else '',
            'first_token': next_token,
            'is_numeric': self._is_numeric_context(tokens_after),
            'is_alphabetic': self._is_alphabetic_context(tokens_after)
        }

    def _get_surrounding_context(self, doc, slash_idx: int) -> Dict[str, Any]:
        """Get broader surrounding context for the slash."""
        # Get wider context window
        start_idx = max(0, slash_idx - 10)
        end_idx = min(len(doc), slash_idx + 10)
        surrounding_tokens = doc[start_idx:end_idx]
        
        # Analyze patterns
        full_text = ''.join([token.text for token in surrounding_tokens])
        
        return {
            'tokens': surrounding_tokens,
            'text': full_text,
            'has_url_pattern': self._has_url_pattern(full_text),
            'has_file_path_pattern': self._has_file_path_pattern(full_text),
            'has_date_pattern': self._has_date_pattern(full_text),
            'has_fraction_pattern': self._has_fraction_pattern(full_text),
            'has_alternative_pattern': self._has_alternative_pattern(full_text),
            'writing_context': self._determine_writing_context(surrounding_tokens)
        }

    def _is_numeric_context(self, tokens) -> bool:
        """Check if tokens contain numeric content using linguistic anchors."""
        if not tokens:
            return False
        
        # Check for numeric patterns
        for token in tokens:
            if token.pos_ == 'NUM' or token.text.isdigit():
                return True
            # Check for numeric patterns in text
            if re.search(r'\d', token.text):
                return True
        
        return False

    def _is_alphabetic_context(self, tokens) -> bool:
        """Check if tokens contain alphabetic content using linguistic anchors."""
        if not tokens:
            return False
        
        # Check for alphabetic patterns
        for token in tokens:
            if token.pos_ in ['NOUN', 'ADJ', 'VERB', 'PROPN', 'ADV']:
                return True
            if token.text.isalpha():
                return True
        
        return False

    def _has_url_pattern(self, text: str) -> bool:
        """Check if text contains URL patterns using linguistic anchors."""
        url_indicators = {
            'http://', 'https://', 'www.', '.com', '.org', '.edu', '.gov', '.net',
            'ftp://', 'file://', '.html', '.php', '.asp', '.jsp'
        }
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in url_indicators)

    def _has_file_path_pattern(self, text: str) -> bool:
        """Check if text contains file path patterns using linguistic anchors."""
        file_path_indicators = {
            'c:\\', 'd:\\', 'e:\\', '\\\\', '\\usr\\', '\\home\\', '\\temp\\',
            '.txt', '.doc', '.pdf', '.exe', '.dll', '.sys', '.bat', '.cmd',
            '/usr/', '/home/', '/tmp/', '/var/', '/etc/', '/bin/', '/opt/'
        }
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in file_path_indicators)

    def _has_date_pattern(self, text: str) -> bool:
        """Check if text contains date patterns using linguistic anchors."""
        # Check for numeric date patterns
        if re.search(r'\d{1,2}/\d{1,2}/\d{2,4}', text):
            return True
        if re.search(r'\d{1,2}/\d{1,2}', text):
            return True
        
        # Check for month names
        month_names = {
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
        }
        
        text_lower = text.lower()
        return any(month in text_lower for month in month_names)

    def _has_fraction_pattern(self, text: str) -> bool:
        """Check if text contains fraction patterns using linguistic anchors."""
        # Check for numeric fractions
        if re.search(r'\d+/\d+', text):
            return True
        
        # Check for written fractions
        fraction_words = {
            'half', 'third', 'quarter', 'fifth', 'sixth', 'seventh', 'eighth',
            'ninth', 'tenth', 'halves', 'thirds', 'quarters', 'fifths'
        }
        
        text_lower = text.lower()
        return any(fraction in text_lower for fraction in fraction_words)

    def _has_alternative_pattern(self, text: str) -> bool:
        """Check if text contains alternative/choice patterns using linguistic anchors."""
        # Check for alternative indicators
        alternative_indicators = {
            'either', 'neither', 'choice', 'option', 'alternative', 'select',
            'choose', 'pick', 'decide', 'versus', 'vs', 'compared'
        }
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in alternative_indicators)

    def _determine_writing_context(self, tokens) -> str:
        """Determine the writing context using linguistic anchors."""
        if not tokens:
            return 'general'
        
        # Check for technical indicators
        technical_indicators = {
            'system', 'file', 'directory', 'folder', 'path', 'url', 'link',
            'server', 'database', 'code', 'programming', 'software', 'hardware'
        }
        
        # Check for academic indicators
        academic_indicators = {
            'research', 'study', 'analysis', 'theory', 'hypothesis', 'method',
            'result', 'conclusion', 'data', 'statistic', 'experiment'
        }
        
        # Check for business indicators
        business_indicators = {
            'company', 'business', 'organization', 'department', 'team',
            'meeting', 'project', 'plan', 'strategy', 'goal', 'objective'
        }
        
        text_lower = ' '.join([token.text.lower() for token in tokens])
        
        if any(indicator in text_lower for indicator in technical_indicators):
            return 'technical'
        elif any(indicator in text_lower for indicator in academic_indicators):
            return 'academic'
        elif any(indicator in text_lower for indicator in business_indicators):
            return 'business'
        else:
            return 'general'

    def _analyze_slash_context(self, doc, slash_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Analyze the context and classify slash usage."""
        errors = []
        
        # Classify the slash usage type
        usage_type = self._classify_slash_usage(slash_info)
        
        # Check appropriateness based on usage type
        if usage_type == 'and_or_alternative':
            errors.extend(self._check_and_or_alternative(slash_info, sentence, sentence_index))
        elif usage_type == 'date_separator':
            errors.extend(self._check_date_separator(slash_info, sentence, sentence_index))
        elif usage_type == 'fraction':
            errors.extend(self._check_fraction_usage(slash_info, sentence, sentence_index))
        elif usage_type == 'url':
            errors.extend(self._check_url_usage(slash_info, sentence, sentence_index))
        elif usage_type == 'file_path':
            errors.extend(self._check_file_path_usage(slash_info, sentence, sentence_index))
        elif usage_type == 'inappropriate':
            errors.extend(self._check_inappropriate_usage(slash_info, sentence, sentence_index))
        
        return errors

    def _classify_slash_usage(self, slash_info: Dict[str, Any]) -> str:
        """Classify the type of slash usage using linguistic anchors."""
        before_context = slash_info['before_context']
        after_context = slash_info['after_context']
        surrounding_context = slash_info['surrounding_context']
        
        # Check for URL patterns
        if surrounding_context['has_url_pattern']:
            return 'url'
        
        # Check for file path patterns
        if surrounding_context['has_file_path_pattern']:
            return 'file_path'
        
        # Check for date patterns
        if surrounding_context['has_date_pattern']:
            return 'date_separator'
        
        # Check for fraction patterns
        if surrounding_context['has_fraction_pattern']:
            return 'fraction'
        
        # Check for alternative patterns
        if (before_context['is_alphabetic'] and after_context['is_alphabetic'] and
            surrounding_context['has_alternative_pattern']):
            return 'and_or_alternative'
        
        # Check for simple alternative between words
        if (before_context['is_alphabetic'] and after_context['is_alphabetic'] and
            len(before_context['tokens']) == 1 and len(after_context['tokens']) == 1):
            return 'and_or_alternative'
        
        # Check for inappropriate usage
        if not any([
            surrounding_context['has_url_pattern'],
            surrounding_context['has_file_path_pattern'],
            surrounding_context['has_date_pattern'],
            surrounding_context['has_fraction_pattern']
        ]):
            return 'inappropriate'
        
        return 'unclear'

    def _check_and_or_alternative(self, slash_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check and/or alternative usage patterns."""
        errors = []
        
        before_context = slash_info['before_context']
        after_context = slash_info['after_context']
        
        # Check if this is ambiguous and/or usage
        if (before_context['last_token'].pos_ in ['NOUN', 'ADJ', 'PROPN'] and
            after_context['first_token'].pos_ in ['NOUN', 'ADJ', 'PROPN']):
            
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Avoid using slash (/) to mean 'and/or' as it can be ambiguous.",
                suggestions=["Use 'and' if both items apply.",
                           "Use 'or' if only one item applies.",
                           "Use 'and/or' explicitly if both meanings are intended.",
                           "Restructure the sentence to clarify the relationship."],
                severity='medium'
            ))
        
        return errors

    def _check_date_separator(self, slash_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check date separator usage patterns."""
        errors = []
        
        before_context = slash_info['before_context']
        after_context = slash_info['after_context']
        
        # Check for proper date format
        if (before_context['is_numeric'] and after_context['is_numeric']):
            # Check for ambiguous date format (MM/DD vs DD/MM)
            before_num = before_context['text']
            after_num = after_context['text']
            
            if (before_num.isdigit() and after_num.isdigit() and
                int(before_num) <= 12 and int(after_num) <= 12):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Date format may be ambiguous (MM/DD vs DD/MM).",
                    suggestions=["Use ISO format (YYYY-MM-DD) for clarity.",
                               "Spell out month names to avoid confusion.",
                               "Specify date format in documentation."],
                    severity='low'
                ))
        
        return errors

    def _check_fraction_usage(self, slash_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check fraction usage patterns."""
        errors = []
        
        before_context = slash_info['before_context']
        after_context = slash_info['after_context']
        
        # Check for proper fraction format
        if (before_context['is_numeric'] and after_context['is_numeric']):
            # Check for spacing around fractions
            if (before_context['last_char'] == ' ' or after_context['first_char'] == ' '):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Fractions should not have spaces around the slash.",
                    suggestions=["Remove spaces around the slash in fractions.",
                               "Use proper fraction formatting (e.g., 1/2, 3/4)."],
                    severity='low'
                ))
        
        return errors

    def _check_url_usage(self, slash_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check URL usage patterns."""
        errors = []
        
        # URLs are generally appropriate - minimal checking
        surrounding_context = slash_info['surrounding_context']
        
        # Check if URL might be better formatted
        if surrounding_context['writing_context'] == 'academic':
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Consider formatting URLs appropriately for academic context.",
                suggestions=["Use proper citation format for URLs.",
                           "Consider using footnotes or references for URLs.",
                           "Ensure URLs are accessible and permanent."],
                severity='low'
            ))
        
        return errors

    def _check_file_path_usage(self, slash_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check file path usage patterns."""
        errors = []
        
        slash_type = slash_info['slash_type']
        surrounding_context = slash_info['surrounding_context']
        
        # Check for consistent path separator usage
        if slash_type == 'backward' and surrounding_context['writing_context'] != 'technical':
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Backslash in file paths may not be clear to all readers.",
                suggestions=["Use forward slashes for universal compatibility.",
                           "Explain file path conventions if necessary.",
                           "Consider using generic path descriptions."],
                severity='low'
            ))
        
        return errors

    def _check_inappropriate_usage(self, slash_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check for inappropriate slash usage."""
        errors = []
        
        errors.append(self._create_error(
            sentence=sentence,
            sentence_index=sentence_index,
            message="Slash usage may be unclear or inappropriate.",
            suggestions=["Consider using more explicit language.",
                       "Replace slash with appropriate conjunction or punctuation.",
                       "Clarify the intended meaning."],
            severity='medium'
        ))
        
        return errors

    def _check_slash_spacing(self, doc, slash_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check spacing around slashes using linguistic anchors."""
        errors = []
        
        slash_idx = slash_info['index']
        before_context = slash_info['before_context']
        after_context = slash_info['after_context']
        usage_type = self._classify_slash_usage(slash_info)
        
        # Check spacing based on usage type
        if usage_type == 'and_or_alternative':
            # No spaces around alternative slashes
            if before_context['last_char'] == ' ':
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Remove space before slash in alternatives.",
                    suggestions=["Remove space before slash (word/word).",
                               "Use consistent spacing for alternative expressions."],
                    severity='low'
                ))
            
            if after_context['first_char'] == ' ':
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Remove space after slash in alternatives.",
                    suggestions=["Remove space after slash (word/word).",
                               "Use consistent spacing for alternative expressions."],
                    severity='low'
                ))
        
        elif usage_type == 'fraction':
            # No spaces around fractions
            if before_context['last_char'] == ' ' or after_context['first_char'] == ' ':
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Fractions should not have spaces around the slash.",
                    suggestions=["Remove spaces around fraction slash (1/2).",
                               "Use proper fraction formatting."],
                    severity='low'
                ))
        
        return errors

    def _check_slash_appropriateness(self, doc, slash_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check overall appropriateness of slash usage."""
        errors = []
        
        usage_type = self._classify_slash_usage(slash_info)
        surrounding_context = slash_info['surrounding_context']
        
        # Check context appropriateness
        if usage_type == 'and_or_alternative' and surrounding_context['writing_context'] == 'academic':
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Consider avoiding slashes in formal academic writing.",
                suggestions=["Use 'and' or 'or' instead of slash.",
                           "Clarify the relationship between alternatives.",
                           "Use more formal language constructions."],
                severity='low'
            ))
        
        return errors

    def _check_alternative_usage(self, doc, slash_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check alternative usage patterns."""
        errors = []
        
        usage_type = self._classify_slash_usage(slash_info)
        before_context = slash_info['before_context']
        after_context = slash_info['after_context']
        
        if usage_type == 'and_or_alternative':
            # Check for clarity
            if (len(before_context['tokens']) > 1 or len(after_context['tokens']) > 1):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Complex alternatives with slashes may be confusing.",
                    suggestions=["Use bullet points for multiple alternatives.",
                               "Restructure as separate sentences.",
                               "Use 'either...or' construction for clarity."],
                    severity='low'
                ))
        
        return errors

    def _check_date_format(self, doc, slash_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check date format consistency."""
        errors = []
        
        usage_type = self._classify_slash_usage(slash_info)
        
        if usage_type == 'date_separator':
            # Check for international date format clarity
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Consider using unambiguous date format.",
                suggestions=["Use ISO format (YYYY-MM-DD) for international clarity.",
                           "Spell out month names (e.g., January 15, 2024).",
                           "Be consistent with date format throughout document."],
                severity='low'
            ))
        
        return errors

    def _check_fraction_format(self, doc, slash_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check fraction format consistency."""
        errors = []
        
        usage_type = self._classify_slash_usage(slash_info)
        
        if usage_type == 'fraction':
            # Check for consistency with other fraction representations
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Ensure consistent fraction formatting throughout document.",
                suggestions=["Use decimal notation for precise values.",
                           "Use consistent fraction formatting (1/2 vs one-half).",
                           "Consider using Unicode fraction characters (½, ¼, ¾)."],
                severity='low'
            ))
        
        return errors

    def _check_technical_context(self, doc, slash_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check technical context appropriateness."""
        errors = []
        
        surrounding_context = slash_info['surrounding_context']
        usage_type = self._classify_slash_usage(slash_info)
        
        # Technical contexts are more permissive
        if surrounding_context['writing_context'] == 'technical':
            if usage_type == 'and_or_alternative':
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Even in technical writing, consider clarifying alternatives.",
                    suggestions=["Use 'and' or 'or' for precision.",
                               "Define the relationship between alternatives.",
                               "Consider using technical notation if appropriate."],
                    severity='low'
                ))
        
        return errors

    def _analyze_with_regex(self, text: str, sentences: List[str]) -> List[Dict[str, Any]]:
        """Fallback regex-based analysis when NLP is unavailable."""
        errors = []
        
        for i, sentence in enumerate(sentences):
            if '/' not in sentence and '\\' not in sentence:
                continue
            
            # Pattern 1: And/or usage between words
            if re.search(r'\b\w+/\w+\b', sentence):
                # Check if it's not a date, fraction, or URL
                if not re.search(r'\d+/\d+', sentence) and not re.search(r'https?://', sentence):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Avoid using slash (/) to mean 'and/or' as it can be ambiguous.",
                        suggestions=["Use 'and' if both items apply.",
                                   "Use 'or' if only one item applies.",
                                   "Use 'and/or' explicitly if both meanings are intended."],
                        severity='medium'
                    ))
            
            # Pattern 2: Spaces around slashes (inappropriate)
            if re.search(r'\w\s+/\s+\w', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Remove spaces around slashes in alternatives.",
                    suggestions=["Remove spaces around slash (word/word).",
                               "Use consistent spacing for alternative expressions."],
                    severity='low'
                ))
            
            # Pattern 3: Multiple consecutive slashes
            if re.search(r'/{2,}', sentence) and not re.search(r'https?://', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Multiple consecutive slashes detected.",
                    suggestions=["Check for extra slashes.",
                               "Use single slash for alternatives.",
                               "Verify URL formatting if intended."],
                    severity='medium'
                ))
            
            # Pattern 4: Backslash in non-technical context
            if '\\' in sentence and not re.search(r'[A-Za-z]:\\', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Backslash usage may be unclear.",
                    suggestions=["Use forward slashes for universal compatibility.",
                               "Explain file path conventions if necessary.",
                               "Consider using generic path descriptions."],
                    severity='low'
                ))
            
            # Pattern 5: Date format ambiguity
            if re.search(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Date format may be ambiguous (MM/DD vs DD/MM).",
                    suggestions=["Use ISO format (YYYY-MM-DD) for clarity.",
                               "Spell out month names to avoid confusion.",
                               "Specify date format in documentation."],
                    severity='low'
                ))
            
            # Pattern 6: Fraction spacing
            if re.search(r'\d\s+/\s+\d', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Fractions should not have spaces around the slash.",
                    suggestions=["Remove spaces around fraction slash (1/2).",
                               "Use proper fraction formatting."],
                    severity='low'
                ))
            
            # Pattern 7: Complex alternatives
            if re.search(r'\b\w+\s+\w+/\w+\s+\w+\b', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Complex alternatives with slashes may be confusing.",
                    suggestions=["Use bullet points for multiple alternatives.",
                               "Restructure as separate sentences.",
                               "Use 'either...or' construction for clarity."],
                    severity='low'
                ))
            
            # Pattern 8: Slash at end of sentence
            if re.search(r'/\s*[.!?]', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Slash at end of sentence may be incomplete.",
                    suggestions=["Complete the alternative expression.",
                               "Remove trailing slash if not needed.",
                               "Clarify the intended meaning."],
                    severity='medium'
                ))
        
        return errors
