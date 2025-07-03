"""
Parentheses Rule
Based on IBM Style Guide topic: "Parentheses"
"""
from typing import List, Dict, Any, Set, Tuple, Optional
import re
from .base_punctuation_rule import BasePunctuationRule

class ParenthesesRule(BasePunctuationRule):
    """
    Comprehensive parentheses usage checker using morphological spaCy analysis with linguistic anchors.
    Handles parenthetical expressions, citations, abbreviations, mathematical expressions, and punctuation placement.
    """
    
    def _get_rule_type(self) -> str:
        return 'parentheses'

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
        """Comprehensive NLP-based parentheses analysis using linguistic anchors."""
        errors = []
        
        # Find all parentheses pairs and unmatched parentheses
        parentheses_analysis = self._analyze_parentheses_structure(doc)
        
        # Check for unmatched parentheses
        errors.extend(self._check_unmatched_parentheses(parentheses_analysis, sentence, sentence_index))
        
        # Analyze each parenthetical expression
        for paren_info in parentheses_analysis['matched_pairs']:
            errors.extend(self._analyze_parenthetical_expression(doc, paren_info, sentence, sentence_index))
            errors.extend(self._check_punctuation_placement(doc, paren_info, sentence, sentence_index))
            errors.extend(self._check_spacing_issues(doc, paren_info, sentence, sentence_index))
            errors.extend(self._check_content_appropriateness(doc, paren_info, sentence, sentence_index))
            errors.extend(self._check_nested_parentheses(doc, paren_info, sentence, sentence_index))
        
        return errors

    def _analyze_parentheses_structure(self, doc) -> Dict[str, Any]:
        """Analyze the structure of parentheses in the document."""
        open_parens = []
        close_parens = []
        matched_pairs = []
        unmatched_opens = []
        unmatched_closes = []
        
        # Find all parentheses positions
        for token in doc:
            if token.text == '(':
                open_parens.append(token.i)
            elif token.text == ')':
                close_parens.append(token.i)
        
        # Match parentheses pairs
        open_stack = []
        for i, token in enumerate(doc):
            if token.text == '(':
                open_stack.append(token.i)
            elif token.text == ')':
                if open_stack:
                    open_idx = open_stack.pop()
                    matched_pairs.append({
                        'open': open_idx,
                        'close': token.i,
                        'content_start': open_idx + 1,
                        'content_end': token.i - 1
                    })
                else:
                    unmatched_closes.append(token.i)
        
        # Remaining open parentheses are unmatched
        unmatched_opens.extend(open_stack)
        
        return {
            'matched_pairs': matched_pairs,
            'unmatched_opens': unmatched_opens,
            'unmatched_closes': unmatched_closes,
            'total_opens': len(open_parens),
            'total_closes': len(close_parens)
        }

    def _check_unmatched_parentheses(self, parentheses_analysis: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check for unmatched parentheses using linguistic anchors."""
        errors = []
        
        if parentheses_analysis['unmatched_opens']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Unmatched opening parenthesis detected.",
                suggestions=["Add a closing parenthesis to complete the parenthetical expression.",
                           "Check if the parenthetical expression is intended to continue to the next sentence."],
                severity='high'
            ))
        
        if parentheses_analysis['unmatched_closes']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Unmatched closing parenthesis detected.",
                suggestions=["Add an opening parenthesis to start the parenthetical expression.",
                           "Check if this closing parenthesis belongs to a previous sentence."],
                severity='high'
            ))
        
        return errors

    def _analyze_parenthetical_expression(self, doc, paren_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Analyze the type and appropriateness of parenthetical expressions."""
        errors = []
        
        # Extract content within parentheses
        content_tokens = doc[paren_info['content_start']:paren_info['content_end'] + 1]
        
        if not content_tokens:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Empty parentheses detected.",
                suggestions=["Remove empty parentheses or add appropriate content.",
                           "Consider if parentheses are necessary for this context."],
                severity='medium'
            ))
            return errors
        
        # Analyze parenthetical content type using linguistic anchors
        content_analysis = self._classify_parenthetical_content(content_tokens, doc, paren_info)
        
        # Check content appropriateness based on type
        if content_analysis['type'] == 'citation':
            errors.extend(self._check_citation_format(content_tokens, sentence, sentence_index))
        elif content_analysis['type'] == 'abbreviation':
            errors.extend(self._check_abbreviation_format(content_tokens, doc, paren_info, sentence, sentence_index))
        elif content_analysis['type'] == 'explanation':
            errors.extend(self._check_explanation_format(content_tokens, doc, paren_info, sentence, sentence_index))
        elif content_analysis['type'] == 'aside':
            errors.extend(self._check_aside_format(content_tokens, doc, paren_info, sentence, sentence_index))
        elif content_analysis['type'] == 'mathematical':
            errors.extend(self._check_mathematical_format(content_tokens, sentence, sentence_index))
        elif content_analysis['type'] == 'enumeration':
            errors.extend(self._check_enumeration_format(content_tokens, sentence, sentence_index))
        elif content_analysis['type'] == 'complete_sentence':
            errors.extend(self._check_complete_sentence_format(content_tokens, doc, paren_info, sentence, sentence_index))
        
        return errors

    def _classify_parenthetical_content(self, content_tokens, doc, paren_info: Dict[str, Any]) -> Dict[str, Any]:
        """Classify the type of parenthetical content using linguistic anchors."""
        if not content_tokens:
            return {'type': 'empty', 'confidence': 1.0}
        
        content_text = ' '.join([token.text for token in content_tokens])
        
        # Citation detection using linguistic anchors
        if self._is_citation_pattern(content_tokens, content_text):
            return {'type': 'citation', 'confidence': 0.9}
        
        # Abbreviation detection using linguistic anchors
        if self._is_abbreviation_pattern(content_tokens, doc, paren_info):
            return {'type': 'abbreviation', 'confidence': 0.8}
        
        # Mathematical expression detection
        if self._is_mathematical_pattern(content_tokens, content_text):
            return {'type': 'mathematical', 'confidence': 0.9}
        
        # Enumeration detection (e.g., (1), (a), (i))
        if self._is_enumeration_pattern(content_tokens, content_text):
            return {'type': 'enumeration', 'confidence': 0.9}
        
        # Complete sentence detection
        if self._is_complete_sentence_pattern(content_tokens):
            return {'type': 'complete_sentence', 'confidence': 0.7}
        
        # Explanation/clarification detection
        if self._is_explanation_pattern(content_tokens, doc, paren_info):
            return {'type': 'explanation', 'confidence': 0.6}
        
        # Default to aside/comment
        return {'type': 'aside', 'confidence': 0.5}

    def _is_citation_pattern(self, content_tokens, content_text: str) -> bool:
        """Detect citation patterns using linguistic anchors."""
        # Author-year patterns
        if re.search(r'^[A-Z][a-z]+,?\s+(19|20)\d{2}', content_text):
            return True
        
        # Numeric citations
        if re.search(r'^\d+(-\d+)?(,\s*\d+(-\d+)?)*$', content_text):
            return True
        
        # "see" references
        if any(token.text.lower() in ['see', 'cf', 'e.g', 'i.e', 'ibid', 'op', 'cit'] for token in content_tokens):
            return True
        
        # Page references
        if re.search(r'p\.\s*\d+|pp\.\s*\d+-\d+', content_text, re.IGNORECASE):
            return True
        
        return False

    def _is_abbreviation_pattern(self, content_tokens, doc, paren_info: Dict[str, Any]) -> bool:
        """Detect abbreviation patterns using linguistic anchors."""
        if len(content_tokens) != 1:
            return False
        
        abbrev_token = content_tokens[0]
        
        # Check if it's all caps (common abbreviation pattern)
        if not abbrev_token.text.isupper():
            return False
        
        # Check if there's a potential full form before the parentheses
        if paren_info['open'] > 0:
            # Look for capitalized words before parentheses that could be the full form
            preceding_tokens = doc[max(0, paren_info['open'] - 5):paren_info['open']]
            capitalized_words = [token for token in preceding_tokens if token.text[0].isupper() and token.pos_ in ['NOUN', 'PROPN']]
            
            if len(capitalized_words) >= 2:
                # Check if abbreviation matches first letters of preceding words
                abbrev_letters = abbrev_token.text.lower()
                word_initials = ''.join([word.text[0].lower() for word in capitalized_words])
                
                if abbrev_letters == word_initials:
                    return True
        
        return False

    def _is_mathematical_pattern(self, content_tokens, content_text: str) -> bool:
        """Detect mathematical expressions using linguistic anchors."""
        # Mathematical symbols and operators
        math_symbols = {'+', '-', '*', '/', '=', '<', '>', '≤', '≥', '±', '∑', '∫', '∆', 'π', 'α', 'β', 'γ', 'θ', 'λ', 'μ', 'σ'}
        
        if any(token.text in math_symbols for token in content_tokens):
            return True
        
        # Mathematical expressions with variables and numbers
        if re.search(r'[a-zA-Z]\s*[+\-*/=]\s*[a-zA-Z0-9]', content_text):
            return True
        
        # Function notation
        if re.search(r'[a-zA-Z]+\([^)]*\)', content_text):
            return True
        
        # Mathematical ranges or coordinates
        if re.search(r'\d+[,\s]+\d+', content_text) and len(content_tokens) <= 5:
            return True
        
        return False

    def _is_enumeration_pattern(self, content_tokens, content_text: str) -> bool:
        """Detect enumeration patterns using linguistic anchors."""
        if len(content_tokens) != 1:
            return False
        
        token_text = content_tokens[0].text
        
        # Numeric enumeration (1, 2, 3, etc.)
        if re.match(r'^\d+$', token_text):
            return True
        
        # Alphabetic enumeration (a, b, c, etc.)
        if re.match(r'^[a-z]$', token_text):
            return True
        
        # Roman numeral enumeration (i, ii, iii, etc.)
        if re.match(r'^(i|ii|iii|iv|v|vi|vii|viii|ix|x)$', token_text.lower()):
            return True
        
        return False

    def _is_complete_sentence_pattern(self, content_tokens) -> bool:
        """Detect complete sentences using linguistic anchors."""
        if len(content_tokens) < 3:
            return False
        
        # Check for sentence-like structure
        has_verb = any(token.pos_ == 'VERB' for token in content_tokens)
        has_subject = any(token.pos_ in ['NOUN', 'PRON', 'PROPN'] for token in content_tokens)
        
        # Check for sentence-ending punctuation
        has_end_punct = content_tokens[-1].text in ['.', '!', '?']
        
        # Check for capitalized first word
        starts_capitalized = content_tokens[0].text[0].isupper()
        
        return has_verb and has_subject and (has_end_punct or starts_capitalized)

    def _is_explanation_pattern(self, content_tokens, doc, paren_info: Dict[str, Any]) -> bool:
        """Detect explanation/clarification patterns using linguistic anchors."""
        # Check for explanation indicators
        explanation_indicators = {'that', 'which', 'meaning', 'i.e.', 'namely', 'specifically', 'also', 'known', 'as'}
        
        content_text = ' '.join([token.text.lower() for token in content_tokens])
        
        if any(indicator in content_text for indicator in explanation_indicators):
            return True
        
        # Check if content provides clarification for preceding noun
        if paren_info['open'] > 0:
            preceding_token = doc[paren_info['open'] - 1]
            if preceding_token.pos_ in ['NOUN', 'PROPN']:
                # Check if parenthetical content relates to the preceding noun
                if len(content_tokens) > 1 and content_tokens[0].pos_ in ['NOUN', 'ADJ', 'PROPN']:
                    return True
        
        return False

    def _check_citation_format(self, content_tokens, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check citation format using linguistic anchors."""
        errors = []
        
        content_text = ' '.join([token.text for token in content_tokens])
        
        # Check for proper citation format
        if re.search(r'[A-Z][a-z]+\s+\d{4}', content_text):
            # Author-year format - check for comma
            if not re.search(r'[A-Z][a-z]+,\s+\d{4}', content_text):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Citation format may need comma between author and year.",
                    suggestions=["Use format: (Author, Year) for author-year citations.",
                               "Check your citation style guide for proper formatting."],
                    severity='low'
                ))
        
        return errors

    def _check_abbreviation_format(self, content_tokens, doc, paren_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check abbreviation format using linguistic anchors."""
        errors = []
        
        if len(content_tokens) == 1:
            abbrev_token = content_tokens[0]
            
            # Check if abbreviation is properly capitalized
            if not abbrev_token.text.isupper() and len(abbrev_token.text) <= 5:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Abbreviation should typically be capitalized.",
                    suggestions=[f"Consider capitalizing abbreviation: '{abbrev_token.text.upper()}'.",
                               "Check if this follows standard abbreviation conventions."],
                    severity='low'
                ))
        
        return errors

    def _check_explanation_format(self, content_tokens, doc, paren_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check explanation format using linguistic anchors."""
        errors = []
        
        # Check if explanation is too long (may need restructuring)
        if len(content_tokens) > 10:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Long parenthetical explanation may impact readability.",
                suggestions=["Consider moving long explanations to separate sentences.",
                           "Use em dashes or commas for shorter parenthetical information."],
                severity='low'
            ))
        
        return errors

    def _check_aside_format(self, content_tokens, doc, paren_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check aside/comment format using linguistic anchors."""
        errors = []
        
        # Check if aside is too lengthy
        if len(content_tokens) > 8:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Lengthy parenthetical aside may disrupt sentence flow.",
                suggestions=["Consider breaking long asides into separate sentences.",
                           "Use em dashes for brief interruptions."],
                severity='low'
            ))
        
        return errors

    def _check_mathematical_format(self, content_tokens, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check mathematical expression format using linguistic anchors."""
        errors = []
        
        content_text = ' '.join([token.text for token in content_tokens])
        
        # Check for proper mathematical notation
        if re.search(r'[a-zA-Z]\s*=\s*[a-zA-Z0-9]', content_text):
            # Mathematical equations should have proper spacing
            if re.search(r'[a-zA-Z]=[a-zA-Z0-9]', content_text):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Mathematical expressions should have proper spacing around operators.",
                    suggestions=["Add spaces around mathematical operators for clarity.",
                               "Follow mathematical notation standards."],
                    severity='low'
                ))
        
        return errors

    def _check_enumeration_format(self, content_tokens, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check enumeration format using linguistic anchors."""
        errors = []
        
        if len(content_tokens) == 1:
            enum_text = content_tokens[0].text
            
            # Check for consistent enumeration style
            if re.match(r'^\d+$', enum_text):
                # Numeric enumeration is generally fine
                pass
            elif re.match(r'^[a-z]$', enum_text):
                # Check if it should be capitalized for formal contexts
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Consider capitalization consistency for enumeration.",
                    suggestions=["Use consistent capitalization for enumeration items.",
                               "Check if formal enumeration requires capitals."],
                    severity='low'
                ))
        
        return errors

    def _check_complete_sentence_format(self, content_tokens, doc, paren_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check complete sentence format using linguistic anchors."""
        errors = []
        
        # Check for proper punctuation in complete sentences
        if not content_tokens[-1].text in ['.', '!', '?']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Complete sentences in parentheses should end with appropriate punctuation.",
                suggestions=["Add period, exclamation mark, or question mark to complete sentence.",
                           "Consider if parenthetical content should be a separate sentence."],
                severity='medium'
            ))
        
        # Check capitalization of first word
        if not content_tokens[0].text[0].isupper():
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Complete sentences in parentheses should start with capital letter.",
                suggestions=["Capitalize the first word of complete sentences.",
                           "Check if parenthetical content forms a complete sentence."],
                severity='medium'
            ))
        
        return errors

    def _check_punctuation_placement(self, doc, paren_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check punctuation placement around parentheses using linguistic anchors."""
        errors = []
        
        open_idx = paren_info['open']
        close_idx = paren_info['close']
        
        # Check punctuation after closing parenthesis
        if close_idx < len(doc) - 1:
            next_token = doc[close_idx + 1]
            
            # Check for proper punctuation placement
            if next_token.text in ['.', ',', ';', ':', '!', '?']:
                # Check if punctuation should be inside parentheses
                content_tokens = doc[paren_info['content_start']:paren_info['content_end'] + 1]
                
                if self._is_complete_sentence_pattern(content_tokens):
                    # Complete sentences should have punctuation inside
                    if content_tokens and content_tokens[-1].text not in ['.', '!', '?']:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="Complete sentences in parentheses should have punctuation inside.",
                            suggestions=["Move punctuation inside parentheses for complete sentences.",
                                       "Place period before closing parenthesis."],
                            severity='medium'
                        ))
                else:
                    # Fragments should have punctuation outside
                    if content_tokens and content_tokens[-1].text in ['.', '!', '?']:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="Sentence fragments in parentheses should not have internal punctuation.",
                            suggestions=["Remove punctuation from inside parentheses for fragments.",
                                       "Place punctuation after closing parenthesis."],
                            severity='medium'
                        ))
        
        return errors

    def _check_spacing_issues(self, doc, paren_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check spacing issues around parentheses using linguistic anchors."""
        errors = []
        
        open_idx = paren_info['open']
        close_idx = paren_info['close']
        
        # Check spacing before opening parenthesis
        if open_idx > 0:
            prev_token = doc[open_idx - 1]
            
            # Should have space before opening parenthesis (except after certain punctuation)
            if not prev_token.whitespace_ and prev_token.text not in [' ', '\t', '\n']:
                if prev_token.text not in ['(', '[', '{', '"', "'", '`']:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message="Missing space before opening parenthesis.",
                        suggestions=["Add space before opening parenthesis.",
                                   "Ensure proper spacing around parenthetical expressions."],
                        severity='low'
                    ))
        
        # Check spacing after closing parenthesis
        if close_idx < len(doc) - 1:
            next_token = doc[close_idx + 1]
            
            # Should have space after closing parenthesis (except before certain punctuation)
            if not next_token.whitespace_ and next_token.text not in ['.', ',', ';', ':', '!', '?', ')', ']', '}']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Missing space after closing parenthesis.",
                    suggestions=["Add space after closing parenthesis.",
                               "Ensure proper spacing around parenthetical expressions."],
                    severity='low'
                ))
        
        return errors

    def _check_content_appropriateness(self, doc, paren_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check if parenthetical content is appropriate using linguistic anchors."""
        errors = []
        
        content_tokens = doc[paren_info['content_start']:paren_info['content_end'] + 1]
        
        # Check for excessive parenthetical content
        total_sentence_length = len(doc)
        parenthetical_length = len(content_tokens)
        
        if parenthetical_length > total_sentence_length * 0.4:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Parenthetical content is disproportionately long compared to main sentence.",
                suggestions=["Consider restructuring sentence to reduce parenthetical content.",
                           "Move lengthy explanations to separate sentences."],
                severity='low'
            ))
        
        # Check for redundant parenthetical content
        if self._is_redundant_parenthetical(content_tokens, doc, paren_info):
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Parenthetical content may be redundant with main sentence.",
                suggestions=["Remove redundant parenthetical information.",
                           "Consider if parenthetical content adds necessary information."],
                severity='low'
            ))
        
        return errors

    def _check_nested_parentheses(self, doc, paren_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check for nested parentheses issues using linguistic anchors."""
        errors = []
        
        content_tokens = doc[paren_info['content_start']:paren_info['content_end'] + 1]
        
        # Check for nested parentheses within this parenthetical expression
        nested_opens = sum(1 for token in content_tokens if token.text == '(')
        nested_closes = sum(1 for token in content_tokens if token.text == ')')
        
        if nested_opens > 0 or nested_closes > 0:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Nested parentheses can be confusing and should be avoided.",
                suggestions=["Use square brackets for nested parenthetical expressions: (example [nested]).",
                           "Consider restructuring to avoid nested parentheses.",
                           "Use em dashes or commas for simpler alternatives."],
                severity='medium'
            ))
        
        return errors

    def _is_redundant_parenthetical(self, content_tokens, doc, paren_info: Dict[str, Any]) -> bool:
        """Check if parenthetical content is redundant with main sentence."""
        if not content_tokens:
            return False
        
        # Get content outside parentheses
        main_content = []
        main_content.extend(doc[:paren_info['open']])
        main_content.extend(doc[paren_info['close'] + 1:])
        
        # Check for word overlap
        content_words = set(token.lemma_.lower() for token in content_tokens if token.pos_ in ['NOUN', 'VERB', 'ADJ'])
        main_words = set(token.lemma_.lower() for token in main_content if token.pos_ in ['NOUN', 'VERB', 'ADJ'])
        
        # If significant overlap, might be redundant
        if content_words and main_words:
            overlap = len(content_words & main_words)
            return overlap / len(content_words) > 0.6
        
        return False

    def _analyze_with_regex(self, text: str, sentences: List[str]) -> List[Dict[str, Any]]:
        """Fallback regex-based analysis when NLP is unavailable."""
        errors = []
        
        for i, sentence in enumerate(sentences):
            # Pattern 1: Unmatched parentheses
            open_count = sentence.count('(')
            close_count = sentence.count(')')
            
            if open_count != close_count:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Unmatched parentheses detected.",
                    suggestions=["Ensure equal number of opening and closing parentheses.",
                               "Check for missing or extra parentheses."],
                    severity='high'
                ))
            
            # Pattern 2: Empty parentheses
            if re.search(r'\(\s*\)', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Empty parentheses detected.",
                    suggestions=["Remove empty parentheses or add appropriate content.",
                               "Check if parentheses serve a purpose."],
                    severity='medium'
                ))
            
            # Pattern 3: Spacing issues
            if re.search(r'[^\s]\(', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Missing space before opening parenthesis.",
                    suggestions=["Add space before opening parenthesis.",
                               "Ensure proper spacing around parenthetical expressions."],
                    severity='low'
                ))
            
            if re.search(r'\)[^\s,.;:!?)\]}]', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Missing space after closing parenthesis.",
                    suggestions=["Add space after closing parenthesis.",
                               "Check spacing around parenthetical expressions."],
                    severity='low'
                ))
            
            # Pattern 4: Nested parentheses
            if re.search(r'\([^)]*\([^)]*\)[^)]*\)', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Nested parentheses detected.",
                    suggestions=["Use square brackets for nested expressions: (example [nested]).",
                               "Consider restructuring to avoid nested parentheses."],
                    severity='medium'
                ))
            
            # Pattern 5: Excessive parentheses
            if sentence.count('(') > 3:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Excessive parentheses usage may impact readability.",
                    suggestions=["Consider reducing parenthetical expressions.",
                               "Use alternative punctuation like em dashes or commas."],
                    severity='low'
                ))
            
            # Pattern 6: Common punctuation placement issues
            if re.search(r'\.\)', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Check punctuation placement with parentheses.",
                    suggestions=["Place periods inside parentheses for complete sentences.",
                               "Place periods outside parentheses for fragments."],
                    severity='medium'
                ))
            
            # Pattern 7: Potential citation format issues
            if re.search(r'\([A-Z][a-z]+\s+\d{4}\)', sentence):
                if not re.search(r'\([A-Z][a-z]+,\s+\d{4}\)', sentence):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Citation format may need comma between author and year.",
                        suggestions=["Use format: (Author, Year) for citations.",
                                   "Check citation style guide for proper formatting."],
                        severity='low'
                    ))
        
        return errors
