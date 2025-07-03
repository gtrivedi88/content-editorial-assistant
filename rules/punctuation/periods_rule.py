"""
Periods Rule
Based on IBM Style Guide topic: "Periods"
"""
from typing import List, Dict, Any, Set, Tuple, Optional
import re
from .base_punctuation_rule import BasePunctuationRule

class PeriodsRule(BasePunctuationRule):
    """
    Comprehensive period usage checker using morphological spaCy analysis with linguistic anchors.
    Handles sentence endings, abbreviations, decimals, initials, academic formatting, and technical writing.
    """
    
    def _get_rule_type(self) -> str:
        return 'periods'

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
        """Comprehensive NLP-based period analysis using linguistic anchors."""
        errors = []
        
        # Find all period tokens in the sentence
        period_tokens = self._find_period_tokens(doc)
        
        for token_idx in period_tokens:
            # Check various period usage patterns
            errors.extend(self._check_sentence_ending_periods(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_abbreviation_periods(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_decimal_periods(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_initials_periods(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_academic_periods(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_technical_periods(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_list_periods(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_spacing_periods(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_multiple_periods(doc, token_idx, sentence, sentence_index))
            errors.extend(self._check_inappropriate_periods(doc, token_idx, sentence, sentence_index))
        
        # Check for missing periods
        errors.extend(self._check_missing_periods(doc, sentence, sentence_index))
        
        return errors

    def _find_period_tokens(self, doc) -> List[int]:
        """Find all period tokens in the document."""
        period_indices = []
        
        for token in doc:
            if token.text == '.':
                period_indices.append(token.i)
        
        return period_indices

    def _check_sentence_ending_periods(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check sentence-ending period usage using linguistic anchors."""
        errors = []
        
        # Check if this period is at the end of a sentence
        if not self._is_sentence_ending_period(doc, token_idx):
            return errors
        
        # Check for proper sentence structure before period
        sentence_analysis = self._analyze_sentence_structure(doc, token_idx)
        
        if sentence_analysis['is_incomplete']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Sentence appears incomplete before period.",
                suggestions=["Check if sentence has proper subject and predicate.",
                           "Consider if this is a fragment that needs completion.",
                           "Verify sentence structure is grammatically complete."],
                severity='medium'
            ))
        
        if sentence_analysis['is_run_on']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Sentence may be too long and complex.",
                suggestions=["Consider breaking into shorter sentences.",
                           "Use semicolons or conjunctions to separate clauses.",
                           "Simplify sentence structure for clarity."],
                severity='low'
            ))
        
        return errors

    def _check_abbreviation_periods(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check abbreviation period usage using linguistic anchors."""
        errors = []
        
        abbrev_analysis = self._analyze_abbreviation_context(doc, token_idx)
        
        if abbrev_analysis['is_abbreviation']:
            if abbrev_analysis['type'] == 'uppercase_acronym':
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message=f"Uppercase abbreviation '{abbrev_analysis['text']}' typically doesn't need periods.",
                    suggestions=[f"Consider using '{abbrev_analysis['text'].replace('.', '')}' without periods.",
                               "Modern style guides prefer periods omitted in uppercase abbreviations."],
                    severity='low'
                ))
            
            elif abbrev_analysis['type'] == 'inconsistent_style':
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Inconsistent abbreviation style detected.",
                    suggestions=["Use consistent style for abbreviations throughout document.",
                               "Choose either periods or no periods for similar abbreviations."],
                    severity='low'
                ))
            
            elif abbrev_analysis['type'] == 'title_abbreviation':
                # Titles like Dr., Mr., Mrs. typically keep periods
                if not abbrev_analysis['has_period']:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message="Title abbreviation may need period.",
                        suggestions=["Consider adding period to title abbreviation.",
                                   "Follow standard conventions for title abbreviations."],
                        severity='low'
                    ))
        
        return errors

    def _check_decimal_periods(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check decimal period usage using linguistic anchors."""
        errors = []
        
        if self._is_decimal_period(doc, token_idx):
            decimal_analysis = self._analyze_decimal_context(doc, token_idx)
            
            if decimal_analysis['needs_consistency_check']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Decimal formatting should be consistent.",
                    suggestions=["Use consistent decimal notation throughout document.",
                               "Ensure proper spacing around decimal numbers."],
                    severity='low'
                ))
            
            if decimal_analysis['has_spacing_issue']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Improper spacing around decimal number.",
                    suggestions=["Remove spaces within decimal numbers.",
                               "Ensure decimal point is properly positioned."],
                    severity='medium'
                ))
        
        return errors

    def _check_initials_periods(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check initials period usage using linguistic anchors."""
        errors = []
        
        if self._is_initials_period(doc, token_idx):
            initials_analysis = self._analyze_initials_context(doc, token_idx)
            
            if initials_analysis['style'] == 'mixed':
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Mixed style detected in initials formatting.",
                    suggestions=["Use consistent style for initials: either 'J.R.R.' or 'JRR'.",
                               "Choose one style and apply consistently."],
                    severity='low'
                ))
            
            if initials_analysis['spacing_issue']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Improper spacing in initials.",
                    suggestions=["Use proper spacing between initials and names.",
                               "Follow standard conventions for name formatting."],
                    severity='low'
                ))
        
        return errors

    def _check_academic_periods(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check academic writing period usage using linguistic anchors."""
        errors = []
        
        if self._is_academic_context(doc):
            academic_analysis = self._analyze_academic_period_usage(doc, token_idx)
            
            if academic_analysis['citation_issue']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Citation punctuation may need adjustment.",
                    suggestions=["Check citation style guide for proper punctuation.",
                               "Ensure periods are placed correctly with citations."],
                    severity='low'
                ))
            
            if academic_analysis['reference_formatting']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Reference formatting may need standardization.",
                    suggestions=["Follow academic style guide for reference punctuation.",
                               "Ensure consistent formatting across all references."],
                    severity='low'
                ))
        
        return errors

    def _check_technical_periods(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check technical writing period usage using linguistic anchors."""
        errors = []
        
        if self._is_technical_context(doc):
            tech_analysis = self._analyze_technical_period_usage(doc, token_idx)
            
            if tech_analysis['file_extension']:
                # File extensions like .txt, .pdf should not have extra periods
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="File extension formatting should be consistent.",
                    suggestions=["Ensure file extensions are properly formatted.",
                               "Avoid unnecessary periods around file extensions."],
                    severity='low'
                ))
            
            if tech_analysis['version_number']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Version number formatting should be consistent.",
                    suggestions=["Use standard version number format (e.g., 2.1.0).",
                               "Follow semantic versioning conventions."],
                    severity='low'
                ))
        
        return errors

    def _check_list_periods(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check list period usage using linguistic anchors."""
        errors = []
        
        if self._is_list_context(doc, token_idx):
            list_analysis = self._analyze_list_period_usage(doc, token_idx)
            
            if list_analysis['inconsistent_style']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Inconsistent punctuation in list items.",
                    suggestions=["Use consistent punctuation across all list items.",
                               "Either use periods for all items or none."],
                    severity='low'
                ))
            
            if list_analysis['fragment_with_period']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="List fragment may not need period.",
                    suggestions=["Consider removing period from list fragments.",
                               "Use periods only for complete sentences in lists."],
                    severity='low'
                ))
        
        return errors

    def _check_spacing_periods(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check spacing around periods using linguistic anchors."""
        errors = []
        
        spacing_analysis = self._analyze_period_spacing(doc, token_idx)
        
        if spacing_analysis['extra_space_before']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Extra space before period.",
                suggestions=["Remove space before period.",
                           "Periods should directly follow the preceding word."],
                severity='medium'
            ))
        
        if spacing_analysis['missing_space_after']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Missing space after period.",
                suggestions=["Add space after period before next word.",
                           "Ensure proper spacing between sentences."],
                severity='medium'
            ))
        
        if spacing_analysis['multiple_spaces_after']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Multiple spaces after period.",
                suggestions=["Use single space after period.",
                           "Modern style uses single space between sentences."],
                severity='low'
            ))
        
        return errors

    def _check_multiple_periods(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check for multiple consecutive periods using linguistic anchors."""
        errors = []
        
        if self._has_multiple_consecutive_periods(doc, token_idx):
            period_analysis = self._analyze_multiple_periods(doc, token_idx)
            
            if period_analysis['is_ellipsis_candidate']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Multiple periods may indicate ellipsis.",
                    suggestions=["Use proper ellipsis (...) or Unicode ellipsis (…).",
                               "Consider if ellipsis is appropriate for the context."],
                    severity='medium'
                ))
            
            elif period_analysis['is_accidental']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Multiple consecutive periods detected.",
                    suggestions=["Remove extra periods.",
                               "Use single period for sentence endings."],
                    severity='high'
                ))
        
        return errors

    def _check_inappropriate_periods(self, doc, token_idx: int, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check for inappropriate period usage using linguistic anchors."""
        errors = []
        
        inappropriate_analysis = self._analyze_inappropriate_period_usage(doc, token_idx)
        
        if inappropriate_analysis['in_questions']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Question should end with question mark, not period.",
                suggestions=["Use question mark (?) for interrogative sentences.",
                           "Check if sentence is truly a question."],
                severity='high'
            ))
        
        if inappropriate_analysis['in_exclamations']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Exclamation should end with exclamation point, not period.",
                suggestions=["Use exclamation point (!) for exclamatory sentences.",
                           "Consider if exclamation is appropriate."],
                severity='medium'
            ))
        
        if inappropriate_analysis['in_titles']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Titles typically don't end with periods.",
                suggestions=["Remove period from title or heading.",
                           "Check style guide for title punctuation."],
                severity='low'
            ))
        
        return errors

    def _check_missing_periods(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check for missing periods using linguistic anchors."""
        errors = []
        
        # Check if sentence should end with period but doesn't
        if self._should_have_period(doc) and not self._ends_with_period(doc):
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Sentence may be missing ending period.",
                suggestions=["Add period to complete the sentence.",
                           "Check if sentence is complete and declarative."],
                severity='medium'
            ))
        
        return errors

    # Helper methods using linguistic anchors

    def _is_sentence_ending_period(self, doc, token_idx: int) -> bool:
        """Check if period is at sentence end using linguistic anchors."""
        if token_idx == len(doc) - 1:
            return True
        
        next_token = doc[token_idx + 1]
        
        # Check if next token starts a new sentence
        return (next_token.is_sent_start or 
                next_token.text[0].isupper() or
                next_token.text in ['\n', '\r', '\t'])

    def _analyze_sentence_structure(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze sentence structure before period using linguistic anchors."""
        sentence_tokens = doc[:token_idx]
        
        # Check for basic sentence completeness
        has_subject = any(token.dep_ in ['nsubj', 'nsubjpass', 'csubj'] for token in sentence_tokens)
        has_verb = any(token.pos_ == 'VERB' for token in sentence_tokens)
        
        # Check sentence length
        is_too_long = len(sentence_tokens) > 30
        is_too_short = len(sentence_tokens) < 3
        
        return {
            'is_incomplete': not (has_subject and has_verb) and not is_too_short,
            'is_run_on': is_too_long,
            'has_subject': has_subject,
            'has_verb': has_verb,
            'length': len(sentence_tokens)
        }

    def _analyze_abbreviation_context(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze abbreviation context using linguistic anchors."""
        if token_idx == 0:
            return {'is_abbreviation': False}
        
        prev_token = doc[token_idx - 1]
        
        # Check if previous token is part of abbreviation
        if len(prev_token.text) == 1 and prev_token.text.isupper():
            # Look for pattern like U.S.A.
            abbrev_tokens = []
            i = token_idx - 1
            while i >= 0 and len(doc[i].text) == 1 and doc[i].text.isupper():
                abbrev_tokens.append(doc[i])
                i -= 1
                if i >= 0 and doc[i].text == '.':
                    i -= 1
                else:
                    break
            
            if len(abbrev_tokens) >= 2:
                full_abbrev = ''.join([token.text + '.' for token in reversed(abbrev_tokens)])
                return {
                    'is_abbreviation': True,
                    'type': 'uppercase_acronym',
                    'text': full_abbrev,
                    'has_period': True
                }
        
        # Check for title abbreviations
        if prev_token.text.lower() in ['dr', 'mr', 'mrs', 'ms', 'prof', 'rev']:
            return {
                'is_abbreviation': True,
                'type': 'title_abbreviation',
                'text': prev_token.text,
                'has_period': True
            }
        
        return {'is_abbreviation': False}

    def _is_decimal_period(self, doc, token_idx: int) -> bool:
        """Check if period is part of decimal number using linguistic anchors."""
        if token_idx == 0 or token_idx >= len(doc) - 1:
            return False
        
        prev_token = doc[token_idx - 1]
        next_token = doc[token_idx + 1]
        
        # Check if surrounded by digits
        return (prev_token.text.isdigit() and next_token.text.isdigit())

    def _analyze_decimal_context(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze decimal number context using linguistic anchors."""
        prev_token = doc[token_idx - 1]
        next_token = doc[token_idx + 1]
        
        # Check for proper decimal formatting
        has_space_before = prev_token.whitespace_
        has_space_after = token_idx + 1 < len(doc) and doc[token_idx + 1].whitespace_
        
        return {
            'needs_consistency_check': False,  # Could be enhanced with document-wide analysis
            'has_spacing_issue': has_space_before or has_space_after
        }

    def _is_initials_period(self, doc, token_idx: int) -> bool:
        """Check if period is part of initials using linguistic anchors."""
        if token_idx == 0:
            return False
        
        prev_token = doc[token_idx - 1]
        
        # Check if previous token is single uppercase letter
        return (len(prev_token.text) == 1 and prev_token.text.isupper())

    def _analyze_initials_context(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze initials context using linguistic anchors."""
        # Look for patterns like J.R.R. Tolkien
        initials_count = 0
        i = token_idx - 1
        
        while i >= 0:
            if len(doc[i].text) == 1 and doc[i].text.isupper():
                initials_count += 1
                i -= 1
                if i >= 0 and doc[i].text == '.':
                    i -= 1
                else:
                    break
            else:
                break
        
        return {
            'style': 'consistent',  # Could be enhanced with document-wide analysis
            'spacing_issue': False,  # Could be enhanced with detailed spacing analysis
            'initials_count': initials_count
        }

    def _is_academic_context(self, doc) -> bool:
        """Determine if this is academic writing context."""
        academic_indicators = {
            'research', 'study', 'analysis', 'methodology', 'bibliography',
            'citation', 'reference', 'journal', 'publication', 'abstract',
            'hypothesis', 'conclusion', 'figure', 'table', 'appendix'
        }
        
        doc_text = doc.text.lower()
        return any(indicator in doc_text for indicator in academic_indicators)

    def _analyze_academic_period_usage(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze academic period usage patterns."""
        return {
            'citation_issue': False,  # Could be enhanced with citation pattern analysis
            'reference_formatting': False  # Could be enhanced with reference pattern analysis
        }

    def _is_technical_context(self, doc) -> bool:
        """Determine if this is technical writing context."""
        technical_indicators = {
            'system', 'software', 'hardware', 'algorithm', 'protocol',
            'interface', 'api', 'database', 'server', 'client',
            'version', 'configuration', 'implementation', 'documentation'
        }
        
        doc_text = doc.text.lower()
        return any(indicator in doc_text for indicator in technical_indicators)

    def _analyze_technical_period_usage(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze technical period usage patterns."""
        # Check for file extensions
        if token_idx > 0 and token_idx < len(doc) - 1:
            prev_token = doc[token_idx - 1]
            next_token = doc[token_idx + 1]
            
            # Common file extensions
            file_extensions = {'txt', 'pdf', 'doc', 'html', 'xml', 'json', 'py', 'js', 'css'}
            
            if next_token.text.lower() in file_extensions:
                return {'file_extension': True, 'version_number': False}
        
        return {'file_extension': False, 'version_number': False}

    def _is_list_context(self, doc, token_idx: int) -> bool:
        """Check if period is in a list context using linguistic anchors."""
        # Look for list indicators before this point
        for i in range(max(0, token_idx - 10), token_idx):
            if doc[i].text in ['•', '-', '*'] or re.match(r'^\d+\.', doc[i].text):
                return True
        
        return False

    def _analyze_list_period_usage(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze list period usage patterns."""
        return {
            'inconsistent_style': False,  # Could be enhanced with document-wide analysis
            'fragment_with_period': False  # Could be enhanced with fragment detection
        }

    def _analyze_period_spacing(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze spacing around periods using linguistic anchors."""
        has_space_before = False
        has_space_after = False
        multiple_spaces_after = False
        
        # Check space before period
        if token_idx > 0:
            prev_token = doc[token_idx - 1]
            has_space_before = prev_token.whitespace_
        
        # Check space after period
        if token_idx < len(doc) - 1:
            next_token = doc[token_idx + 1]
            current_token = doc[token_idx]
            
            # Check if there's proper spacing
            if current_token.whitespace_:
                space_count = len(current_token.whitespace_)
                has_space_after = space_count > 0
                multiple_spaces_after = space_count > 1
            else:
                has_space_after = False
        
        return {
            'extra_space_before': has_space_before,
            'missing_space_after': not has_space_after and token_idx < len(doc) - 1,
            'multiple_spaces_after': multiple_spaces_after
        }

    def _has_multiple_consecutive_periods(self, doc, token_idx: int) -> bool:
        """Check for multiple consecutive periods."""
        if token_idx >= len(doc) - 1:
            return False
        
        next_token = doc[token_idx + 1]
        return next_token.text == '.'

    def _analyze_multiple_periods(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze multiple consecutive periods."""
        consecutive_count = 1
        i = token_idx + 1
        
        while i < len(doc) and doc[i].text == '.':
            consecutive_count += 1
            i += 1
        
        return {
            'is_ellipsis_candidate': consecutive_count == 3,
            'is_accidental': consecutive_count == 2 or consecutive_count > 3,
            'count': consecutive_count
        }

    def _analyze_inappropriate_period_usage(self, doc, token_idx: int) -> Dict[str, Any]:
        """Analyze inappropriate period usage patterns."""
        # Check if sentence has question words
        question_words = {'what', 'when', 'where', 'why', 'how', 'who', 'which', 'whom'}
        sentence_tokens = doc[:token_idx]
        
        has_question_word = any(token.text.lower() in question_words for token in sentence_tokens)
        has_question_structure = any(token.dep_ in ['aux', 'auxpass'] for token in sentence_tokens[:3])
        
        # Check for exclamatory patterns
        exclamatory_words = {'wow', 'amazing', 'incredible', 'fantastic', 'terrible', 'awful'}
        has_exclamatory_word = any(token.text.lower() in exclamatory_words for token in sentence_tokens)
        
        return {
            'in_questions': has_question_word or has_question_structure,
            'in_exclamations': has_exclamatory_word,
            'in_titles': self._is_title_context(doc, token_idx)
        }

    def _is_title_context(self, doc, token_idx: int) -> bool:
        """Check if period is in a title context."""
        # Simple heuristic: if sentence is short and mostly capitalized
        sentence_tokens = doc[:token_idx]
        if len(sentence_tokens) <= 8:
            capitalized_count = sum(1 for token in sentence_tokens if token.text[0].isupper())
            return capitalized_count / len(sentence_tokens) > 0.5
        
        return False

    def _should_have_period(self, doc) -> bool:
        """Check if sentence should have period using linguistic anchors."""
        if len(doc) == 0:
            return False
        
        # Check if it's a declarative sentence
        has_subject = any(token.dep_ in ['nsubj', 'nsubjpass', 'csubj'] for token in doc)
        has_verb = any(token.pos_ == 'VERB' for token in doc)
        
        # Check if it's not a question or exclamation
        is_question = any(token.text.lower() in ['what', 'when', 'where', 'why', 'how', 'who'] for token in doc)
        is_exclamation = any(token.text.lower() in ['wow', 'amazing', 'incredible'] for token in doc)
        
        return has_subject and has_verb and not is_question and not is_exclamation

    def _ends_with_period(self, doc) -> bool:
        """Check if sentence ends with period."""
        if len(doc) == 0:
            return False
        
        return doc[-1].text == '.'

    def _analyze_with_regex(self, text: str, sentences: List[str]) -> List[Dict[str, Any]]:
        """Fallback regex-based analysis when NLP is unavailable."""
        errors = []
        
        for i, sentence in enumerate(sentences):
            # Pattern 1: Uppercase abbreviations with periods
            uppercase_abbrev_pattern = re.compile(r'\b(?:[A-Z]\.){2,}')
            for match in uppercase_abbrev_pattern.finditer(sentence):
                abbreviation = match.group(0)
                suggestion = abbreviation.replace('.', '')
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message=f"Uppercase abbreviation '{abbreviation}' typically doesn't need periods.",
                    suggestions=[f"Consider using '{suggestion}' without periods.",
                               "Modern style guides prefer periods omitted in uppercase abbreviations."],
                    severity='low'
                ))
            
            # Pattern 2: Multiple consecutive periods
            if re.search(r'\.{2,}', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Multiple consecutive periods detected.",
                    suggestions=["Use proper ellipsis (...) for omissions.",
                               "Use single period for sentence endings.",
                               "Check for accidental extra periods."],
                    severity='medium'
                ))
            
            # Pattern 3: Space before period
            if re.search(r'\s+\.', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Extra space before period.",
                    suggestions=["Remove space before period.",
                               "Periods should directly follow the preceding word."],
                    severity='medium'
                ))
            
            # Pattern 4: Missing space after period
            if re.search(r'\.[a-zA-Z]', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Missing space after period.",
                    suggestions=["Add space after period before next word.",
                               "Ensure proper spacing between sentences."],
                    severity='medium'
                ))
            
            # Pattern 5: Multiple spaces after period
            if re.search(r'\.\s{2,}', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Multiple spaces after period.",
                    suggestions=["Use single space after period.",
                               "Modern style uses single space between sentences."],
                    severity='low'
                ))
            
            # Pattern 6: Periods in decimal numbers with spaces
            if re.search(r'\d\s+\.\s+\d', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Improper spacing in decimal numbers.",
                    suggestions=["Remove spaces within decimal numbers.",
                               "Format as: 3.14 not 3 . 14."],
                    severity='medium'
                ))
            
            # Pattern 7: Question with period instead of question mark
            if re.search(r'\b(what|when|where|why|how|who|which|whom)\b.*\.$', sentence, re.IGNORECASE):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Question should end with question mark, not period.",
                    suggestions=["Use question mark (?) for interrogative sentences.",
                               "Check if sentence is truly a question."],
                    severity='high'
                ))
            
            # Pattern 8: Common file extensions
            if re.search(r'\b\w+\.\w+\b', sentence):
                # Check if it might be a file extension in inappropriate context
                file_ext_matches = re.findall(r'\b\w+\.([a-z]{2,4})\b', sentence.lower())
                common_extensions = {'txt', 'pdf', 'doc', 'html', 'xml', 'json', 'py', 'js', 'css', 'jpg', 'png', 'gif'}
                
                for ext in file_ext_matches:
                    if ext in common_extensions:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message="File extension formatting should be consistent.",
                            suggestions=["Ensure file extensions are properly formatted.",
                                       "Use consistent formatting for technical references."],
                            severity='low'
                        ))
                        break
        
        return errors
