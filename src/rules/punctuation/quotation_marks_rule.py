"""
Quotation Marks Rule
Based on IBM Style Guide topic: "Quotation marks"
"""
from typing import List, Dict, Any, Set, Tuple, Optional
import re
from .base_punctuation_rule import BasePunctuationRule

class QuotationMarksRule(BasePunctuationRule):
    """
    Comprehensive quotation marks checker using morphological spaCy analysis with linguistic anchors.
    Handles dialogue, titles, nested quotes, punctuation placement, attribution, and formatting consistency.
    """
    
    def _get_rule_type(self) -> str:
        return 'quotation_marks'

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
        """Comprehensive NLP-based quotation marks analysis using linguistic anchors."""
        errors = []
        
        # Find all quotation mark tokens and pairs
        quote_analysis = self._analyze_quotation_structure(doc)
        
        # Check for unmatched quotation marks
        errors.extend(self._check_unmatched_quotes(quote_analysis, sentence, sentence_index))
        
        # Analyze each quotation pair
        for quote_info in quote_analysis['matched_pairs']:
            errors.extend(self._analyze_quotation_content(doc, quote_info, sentence, sentence_index))
            errors.extend(self._check_punctuation_placement(doc, quote_info, sentence, sentence_index))
            errors.extend(self._check_quotation_attribution(doc, quote_info, sentence, sentence_index))
            errors.extend(self._check_quotation_spacing(doc, quote_info, sentence, sentence_index))
            errors.extend(self._check_quotation_formatting(doc, quote_info, sentence, sentence_index))
            errors.extend(self._check_nested_quotations(doc, quote_info, sentence, sentence_index))
        
        # Check quotation mark consistency
        errors.extend(self._check_quotation_consistency(doc, quote_analysis, sentence, sentence_index))
        
        return errors

    def _analyze_quotation_structure(self, doc) -> Dict[str, Any]:
        """Analyze the structure of quotation marks in the document."""
        quote_tokens = []
        matched_pairs = []
        unmatched_opens = []
        unmatched_closes = []
        
        # Find all quotation mark tokens
        for i, token in enumerate(doc):
            if self._is_quotation_mark(token.text):
                quote_tokens.append({
                    'index': i,
                    'text': token.text,
                    'type': self._classify_quote_mark(token.text),
                    'direction': self._get_quote_direction(token.text)
                })
        
        # Match quotation pairs
        open_stack = []
        for quote in quote_tokens:
            if quote['direction'] == 'open' or quote['direction'] == 'ambiguous':
                if quote['direction'] == 'ambiguous':
                    # For ambiguous quotes (straight quotes), use context to determine direction
                    if self._is_opening_quote_context(doc, quote['index']):
                        quote['direction'] = 'open'
                    else:
                        quote['direction'] = 'close'
                
                if quote['direction'] == 'open':
                    open_stack.append(quote)
                else:
                    if open_stack and self._quotes_match(open_stack[-1], quote):
                        open_quote = open_stack.pop()
                        matched_pairs.append({
                            'open': open_quote,
                            'close': quote,
                            'content_start': open_quote['index'] + 1,
                            'content_end': quote['index'] - 1
                        })
                    else:
                        unmatched_closes.append(quote)
            else:  # closing quote
                if open_stack and self._quotes_match(open_stack[-1], quote):
                    open_quote = open_stack.pop()
                    matched_pairs.append({
                        'open': open_quote,
                        'close': quote,
                        'content_start': open_quote['index'] + 1,
                        'content_end': quote['index'] - 1
                    })
                else:
                    unmatched_closes.append(quote)
        
        # Remaining open quotes are unmatched
        unmatched_opens.extend(open_stack)
        
        return {
            'all_quotes': quote_tokens,
            'matched_pairs': matched_pairs,
            'unmatched_opens': unmatched_opens,
            'unmatched_closes': unmatched_closes
        }

    def _is_quotation_mark(self, text: str) -> bool:
        """Check if text is a quotation mark using linguistic anchors."""
        quote_marks = {
            '"', "'", '"', '"', ''', ''', '«', '»', '‹', '›', 
            '„', '‚', '‛', '‟', '´', '`', '′', '″'
        }
        return text in quote_marks

    def _classify_quote_mark(self, text: str) -> str:
        """Classify the type of quotation mark."""
        if text in ['"', '"', '"']:
            return 'double'
        elif text in ["'", ''', ''']:
            return 'single'
        elif text in ['«', '»', '‹', '›']:
            return 'guillemet'
        elif text in ['„', '‚', '‛', '‟']:
            return 'low_quote'
        else:
            return 'other'

    def _get_quote_direction(self, text: str) -> str:
        """Determine if quote mark is opening, closing, or ambiguous."""
        opening_marks = {'"', ''', '«', '‹', '„', '‚'}
        closing_marks = {'"', ''', '»', '›', '‛', '‟'}
        ambiguous_marks = {'"', "'", '′', '″', '´', '`'}
        
        if text in opening_marks:
            return 'open'
        elif text in closing_marks:
            return 'close'
        elif text in ambiguous_marks:
            return 'ambiguous'
        else:
            return 'unknown'

    def _is_opening_quote_context(self, doc, token_idx: int) -> bool:
        """Determine if ambiguous quote is opening using context."""
        # Check if preceded by space or sentence start
        if token_idx == 0:
            return True
        
        prev_token = doc[token_idx - 1]
        
        # Opening quotes typically follow spaces, punctuation, or sentence starts
        if prev_token.whitespace_ or prev_token.text in ['.', '!', '?', ':', ';', ',', '(', '[', '{']:
            return True
        
        # Check for speech verbs before quotes
        speech_verbs = self._find_speech_verbs_before(doc, token_idx)
        if speech_verbs:
            return True
        
        return False

    def _quotes_match(self, open_quote: Dict[str, Any], close_quote: Dict[str, Any]) -> bool:
        """Check if opening and closing quotes match."""
        # Same type quotes match
        if open_quote['type'] == close_quote['type']:
            return True
        
        # Mixed single/double can work in nested contexts
        return True  # Allow mixed for now - will check nesting separately

    def _check_unmatched_quotes(self, quote_analysis: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check for unmatched quotation marks using linguistic anchors."""
        errors = []
        
        if quote_analysis['unmatched_opens']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Unmatched opening quotation mark detected.",
                suggestions=["Add a closing quotation mark to complete the quote.",
                           "Check if the quotation continues to the next sentence.",
                           "Verify the quotation is intended."],
                severity='high'
            ))
        
        if quote_analysis['unmatched_closes']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Unmatched closing quotation mark detected.",
                suggestions=["Add an opening quotation mark to start the quote.",
                           "Check if this closing quote belongs to a previous sentence.",
                           "Verify the quotation structure."],
                severity='high'
            ))
        
        return errors

    def _analyze_quotation_content(self, doc, quote_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Analyze the content and purpose of quotations using linguistic anchors."""
        errors = []
        
        # Extract quoted content
        if quote_info['content_end'] < quote_info['content_start']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Empty quotation marks detected.",
                suggestions=["Remove empty quotation marks or add content.",
                           "Check if quotation marks are necessary."],
                severity='medium'
            ))
            return errors
        
        content_tokens = doc[quote_info['content_start']:quote_info['content_end'] + 1]
        
        # Classify quotation type using linguistic anchors
        quote_classification = self._classify_quotation_type(content_tokens, doc, quote_info)
        
        # Check appropriateness based on type
        if quote_classification['type'] == 'dialogue':
            errors.extend(self._check_dialogue_formatting(content_tokens, doc, quote_info, sentence, sentence_index))
        elif quote_classification['type'] == 'title':
            errors.extend(self._check_title_formatting(content_tokens, doc, quote_info, sentence, sentence_index))
        elif quote_classification['type'] == 'emphasis':
            errors.extend(self._check_emphasis_formatting(content_tokens, doc, quote_info, sentence, sentence_index))
        elif quote_classification['type'] == 'citation':
            errors.extend(self._check_citation_formatting(content_tokens, doc, quote_info, sentence, sentence_index))
        elif quote_classification['type'] == 'technical_term':
            errors.extend(self._check_technical_term_formatting(content_tokens, doc, quote_info, sentence, sentence_index))
        
        return errors

    def _classify_quotation_type(self, content_tokens, doc, quote_info: Dict[str, Any]) -> Dict[str, Any]:
        """Classify the type of quotation using linguistic anchors."""
        if not content_tokens:
            return {'type': 'empty', 'confidence': 1.0}
        
        content_text = ' '.join([token.text for token in content_tokens])
        
        # Dialogue detection using linguistic anchors
        if self._is_dialogue_pattern(content_tokens, doc, quote_info):
            return {'type': 'dialogue', 'confidence': 0.9}
        
        # Title detection using linguistic anchors
        if self._is_title_pattern(content_tokens, doc, quote_info):
            return {'type': 'title', 'confidence': 0.8}
        
        # Citation detection using linguistic anchors
        if self._is_citation_pattern(content_tokens, doc, quote_info):
            return {'type': 'citation', 'confidence': 0.8}
        
        # Technical term detection
        if self._is_technical_term_pattern(content_tokens, doc, quote_info):
            return {'type': 'technical_term', 'confidence': 0.7}
        
        # Emphasis detection
        if self._is_emphasis_pattern(content_tokens, doc, quote_info):
            return {'type': 'emphasis', 'confidence': 0.6}
        
        # Default to general quotation
        return {'type': 'general', 'confidence': 0.5}

    def _is_dialogue_pattern(self, content_tokens, doc, quote_info: Dict[str, Any]) -> bool:
        """Detect dialogue patterns using linguistic anchors."""
        # Check for speech verbs around quotation
        speech_verbs = self._find_speech_verbs_around(doc, quote_info)
        if speech_verbs:
            return True
        
        # Check for conversational language patterns
        conversational_indicators = {'i', 'you', 'we', 'my', 'your', 'our', 'yes', 'no', 'okay', 'well', 'um', 'ah'}
        content_words = {token.text.lower() for token in content_tokens}
        
        if len(content_words & conversational_indicators) > 0:
            return True
        
        # Check for imperative sentences (commands in dialogue)
        has_imperative = any(token.tag_ == 'VB' and token.dep_ == 'ROOT' for token in content_tokens)
        if has_imperative:
            return True
        
        return False

    def _is_title_pattern(self, content_tokens, doc, quote_info: Dict[str, Any]) -> bool:
        """Detect title patterns using linguistic anchors."""
        # Check if content is title case
        title_case_count = sum(1 for token in content_tokens if token.text.istitle())
        if title_case_count / len(content_tokens) > 0.5:
            return True
        
        # Check for title indicators in surrounding context
        title_indicators = {'title', 'book', 'article', 'song', 'movie', 'chapter', 'essay', 'work', 'piece'}
        
        # Look for title indicators before the quote
        preceding_tokens = doc[max(0, quote_info['open']['index'] - 5):quote_info['open']['index']]
        if any(token.text.lower() in title_indicators for token in preceding_tokens):
            return True
        
        return False

    def _is_citation_pattern(self, content_tokens, doc, quote_info: Dict[str, Any]) -> bool:
        """Detect citation patterns using linguistic anchors."""
        # Check for academic/formal language
        formal_indicators = {'according', 'states', 'argues', 'claims', 'suggests', 'maintains', 'asserts'}
        
        # Look for citation verbs before the quote
        preceding_tokens = doc[max(0, quote_info['open']['index'] - 5):quote_info['open']['index']]
        if any(token.text.lower() in formal_indicators for token in preceding_tokens):
            return True
        
        # Check for citation markers after the quote
        following_tokens = doc[quote_info['close']['index'] + 1:min(len(doc), quote_info['close']['index'] + 6)]
        citation_markers = {'(', '[', 'p.', 'pp.', '19', '20'}  # Simple patterns
        if any(token.text.startswith(marker) for token in following_tokens for marker in citation_markers):
            return True
        
        return False

    def _is_technical_term_pattern(self, content_tokens, doc, quote_info: Dict[str, Any]) -> bool:
        """Detect technical term patterns using linguistic anchors."""
        # Check for technical vocabulary
        content_text = ' '.join([token.text.lower() for token in content_tokens])
        
        # Single technical terms are often quoted
        if len(content_tokens) <= 3:
            # Check for technical indicators in surrounding text
            technical_indicators = {'term', 'called', 'known', 'referred', 'defined', 'concept'}
            surrounding_text = ' '.join([token.text.lower() for token in doc])
            if any(indicator in surrounding_text for indicator in technical_indicators):
                return True
        
        return False

    def _is_emphasis_pattern(self, content_tokens, doc, quote_info: Dict[str, Any]) -> bool:
        """Detect emphasis patterns using linguistic anchors."""
        # Check for emphasis indicators
        emphasis_indicators = {'so-called', 'alleged', 'supposed', 'claimed'}
        
        # Look for emphasis indicators before the quote
        preceding_tokens = doc[max(0, quote_info['open']['index'] - 3):quote_info['open']['index']]
        if any(token.text.lower() in emphasis_indicators for token in preceding_tokens):
            return True
        
        # Single words in quotes often indicate emphasis or irony
        if len(content_tokens) == 1:
            return True
        
        return False

    def _find_speech_verbs_around(self, doc, quote_info: Dict[str, Any]) -> List[int]:
        """Find speech verbs around quotation using linguistic anchors."""
        speech_verbs = {
            'say', 'said', 'tell', 'told', 'ask', 'asked', 'reply', 'replied',
            'answer', 'answered', 'speak', 'spoke', 'talk', 'talked', 'whisper',
            'whispered', 'shout', 'shouted', 'scream', 'screamed', 'yell', 'yelled',
            'mumble', 'mumbled', 'mutter', 'muttered', 'declare', 'declared',
            'announce', 'announced', 'exclaim', 'exclaimed', 'state', 'stated'
        }
        
        found_verbs = []
        
        # Check before quotation
        start_search = max(0, quote_info['open']['index'] - 10)
        for i in range(start_search, quote_info['open']['index']):
            if doc[i].lemma_.lower() in speech_verbs or doc[i].text.lower() in speech_verbs:
                found_verbs.append(i)
        
        # Check after quotation
        end_search = min(len(doc), quote_info['close']['index'] + 10)
        for i in range(quote_info['close']['index'] + 1, end_search):
            if doc[i].lemma_.lower() in speech_verbs or doc[i].text.lower() in speech_verbs:
                found_verbs.append(i)
        
        return found_verbs

    def _find_speech_verbs_before(self, doc, token_idx: int) -> List[int]:
        """Find speech verbs before a token position."""
        speech_verbs = {
            'say', 'said', 'tell', 'told', 'ask', 'asked', 'reply', 'replied',
            'answer', 'answered', 'speak', 'spoke', 'talk', 'talked'
        }
        
        found_verbs = []
        start_search = max(0, token_idx - 5)
        
        for i in range(start_search, token_idx):
            if doc[i].lemma_.lower() in speech_verbs:
                found_verbs.append(i)
        
        return found_verbs

    def _check_dialogue_formatting(self, content_tokens, doc, quote_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check dialogue formatting using linguistic anchors."""
        errors = []
        
        # Check for proper capitalization
        if content_tokens and not content_tokens[0].text[0].isupper():
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Dialogue should start with capital letter.",
                suggestions=["Capitalize the first word of dialogue.",
                           "Check if this is the beginning of a spoken sentence."],
                severity='medium'
            ))
        
        # Check for proper ending punctuation
        if content_tokens and content_tokens[-1].text not in ['.', '!', '?', ',']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Dialogue may need ending punctuation.",
                suggestions=["Add appropriate punctuation at the end of dialogue.",
                           "Use comma if dialogue continues with attribution.",
                           "Use period, question mark, or exclamation point for complete sentences."],
                severity='medium'
            ))
        
        return errors

    def _check_title_formatting(self, content_tokens, doc, quote_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check title formatting using linguistic anchors."""
        errors = []
        
        # Check if title should use italics instead of quotes
        title_length = len(content_tokens)
        if title_length > 5:  # Longer titles often use italics
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Long titles may be better formatted with italics.",
                suggestions=["Consider using italics for book titles, long works.",
                           "Use quotation marks for shorter works like articles or songs."],
                severity='low'
            ))
        
        return errors

    def _check_emphasis_formatting(self, content_tokens, doc, quote_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check emphasis formatting using linguistic anchors."""
        errors = []
        
        # Check if emphasis quotes are overused
        errors.append(self._create_error(
            sentence=sentence,
            sentence_index=sentence_index,
            message="Consider if quotation marks are the best choice for emphasis.",
            suggestions=["Use italics or bold for emphasis instead of quotation marks.",
                       "Reserve quotation marks for actual quotations.",
                       "Consider if the emphasis is necessary."],
            severity='low'
        ))
        
        return errors

    def _check_citation_formatting(self, content_tokens, doc, quote_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check citation formatting using linguistic anchors."""
        errors = []
        
        # Citations should be properly attributed
        has_attribution = bool(self._find_speech_verbs_around(doc, quote_info))
        
        if not has_attribution:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Citation may need proper attribution.",
                suggestions=["Add attribution with verbs like 'states', 'argues', 'claims'.",
                           "Include source information for the quotation.",
                           "Ensure proper citation format."],
                severity='low'
            ))
        
        return errors

    def _check_technical_term_formatting(self, content_tokens, doc, quote_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check technical term formatting using linguistic anchors."""
        errors = []
        
        # Technical terms might be better in italics
        if len(content_tokens) <= 2:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Consider formatting for technical terms.",
                suggestions=["Consider using italics for technical terms.",
                           "Use quotation marks only when introducing new terminology.",
                           "Be consistent with technical term formatting."],
                severity='low'
            ))
        
        return errors

    def _check_punctuation_placement(self, doc, quote_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check punctuation placement with quotation marks using linguistic anchors."""
        errors = []
        
        close_idx = quote_info['close']['index']
        
        # Check punctuation after closing quote
        if close_idx < len(doc) - 1:
            next_token = doc[close_idx + 1]
            
            if next_token.text in ['.', ',']:
                # US style: periods and commas go inside quotes
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Punctuation placement may be incorrect for US English style.",
                    suggestions=[f"Consider moving the '{next_token.text}' inside the closing quotation mark.",
                               "In US English, periods and commas typically go inside quotes.",
                               "Check your style guide for punctuation placement rules."],
                    severity='low'
                ))
            
            elif next_token.text in ['!', '?']:
                # Check if exclamation/question is part of the quote
                content_tokens = doc[quote_info['content_start']:quote_info['content_end'] + 1]
                if content_tokens:
                    last_content = content_tokens[-1].text
                    if last_content not in ['!', '?']:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="Question mark or exclamation point placement may be incorrect.",
                            suggestions=["Move punctuation inside quotes if it's part of the quoted material.",
                                       "Keep punctuation outside quotes if it applies to the whole sentence."],
                            severity='low'
                        ))
            
            elif next_token.text in [';', ':']:
                # Semicolons and colons typically go outside quotes
                content_tokens = doc[quote_info['content_start']:quote_info['content_end'] + 1]
                if content_tokens and content_tokens[-1].text in [';', ':']:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message="Semicolon or colon should typically go outside quotation marks.",
                        suggestions=["Move semicolon or colon outside the closing quotation mark.",
                                   "These punctuation marks usually apply to the whole sentence."],
                        severity='low'
                    ))
        
        return errors

    def _check_quotation_attribution(self, doc, quote_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check quotation attribution using linguistic anchors."""
        errors = []
        
        # Find speech verbs for attribution
        speech_verbs = self._find_speech_verbs_around(doc, quote_info)
        
        # Check for dialogue without attribution
        content_tokens = doc[quote_info['content_start']:quote_info['content_end'] + 1]
        is_dialogue = self._is_dialogue_pattern(content_tokens, doc, quote_info)
        
        if is_dialogue and not speech_verbs:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Dialogue may need attribution or speech tag.",
                suggestions=["Add attribution like 'he said' or 'she asked'.",
                           "Include speaker identification for clarity.",
                           "Consider if the speaker is clear from context."],
                severity='low'
            ))
        
        # Check attribution placement
        if speech_verbs:
            attribution_analysis = self._analyze_attribution_placement(doc, quote_info, speech_verbs)
            
            if attribution_analysis['needs_comma']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Attribution may need proper comma placement.",
                    suggestions=["Use comma to separate dialogue from attribution.",
                               "Check punctuation in dialogue tags."],
                    severity='low'
                ))
        
        return errors

    def _analyze_attribution_placement(self, doc, quote_info: Dict[str, Any], speech_verbs: List[int]) -> Dict[str, Any]:
        """Analyze attribution placement patterns."""
        # Simple analysis - could be enhanced
        return {
            'needs_comma': False,  # Placeholder for more complex logic
            'placement': 'after'   # Could detect before/during/after placement
        }

    def _check_quotation_spacing(self, doc, quote_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check spacing around quotation marks using linguistic anchors."""
        errors = []
        
        open_idx = quote_info['open']['index']
        close_idx = quote_info['close']['index']
        
        # Check spacing before opening quote
        if open_idx > 0:
            prev_token = doc[open_idx - 1]
            if not prev_token.whitespace_ and prev_token.text not in [' ', '\t', '\n', '(', '[', '{']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Missing space before opening quotation mark.",
                    suggestions=["Add space before opening quotation mark.",
                               "Ensure proper spacing around quotations."],
                    severity='low'
                ))
        
        # Check spacing after closing quote
        if close_idx < len(doc) - 1:
            next_token = doc[close_idx + 1]
            current_token = doc[close_idx]
            
            if not current_token.whitespace_ and next_token.text not in ['.', ',', ';', ':', '!', '?', ')', ']', '}']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Missing space after closing quotation mark.",
                    suggestions=["Add space after closing quotation mark.",
                               "Check spacing around quotation marks."],
                    severity='low'
                ))
        
        return errors

    def _check_quotation_formatting(self, doc, quote_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check quotation mark formatting using linguistic anchors."""
        errors = []
        
        open_quote = quote_info['open']['text']
        close_quote = quote_info['close']['text']
        
        # Check for straight vs. curly quotes consistency
        if self._is_straight_quote(open_quote) and self._is_curly_quote(close_quote):
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Mixed quotation mark styles detected.",
                suggestions=["Use consistent quotation mark style throughout.",
                           "Choose either straight quotes (\") or curly quotes (" ")."],
                severity='low'
            ))
        
        # Check for inappropriate quote types
        if quote_info['open']['type'] != quote_info['close']['type']:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Mismatched quotation mark types.",
                suggestions=["Use matching opening and closing quotation marks.",
                           "Ensure single quotes match single quotes, double quotes match double quotes."],
                severity='medium'
            ))
        
        return errors

    def _is_straight_quote(self, quote: str) -> bool:
        """Check if quote is a straight quote."""
        return quote in ['"', "'"]

    def _is_curly_quote(self, quote: str) -> bool:
        """Check if quote is a curly quote."""
        return quote in ['"', '"', ''', ''']

    def _check_nested_quotations(self, doc, quote_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check nested quotations using linguistic anchors."""
        errors = []
        
        # Check for quotes within quotes
        content_tokens = doc[quote_info['content_start']:quote_info['content_end'] + 1]
        
        nested_quotes = [token for token in content_tokens if self._is_quotation_mark(token.text)]
        
        if nested_quotes:
            # Check if nested quotes use appropriate style
            outer_type = quote_info['open']['type']
            
            for nested_quote in nested_quotes:
                nested_type = self._classify_quote_mark(nested_quote.text)
                
                if outer_type == 'double' and nested_type != 'single':
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message="Nested quotations should use single quotes inside double quotes.",
                        suggestions=["Use single quotes for quotations within double quotes.",
                                   "Follow standard nesting conventions for quotation marks."],
                        severity='medium'
                    ))
                
                elif outer_type == 'single' and nested_type != 'double':
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message="Nested quotations should use double quotes inside single quotes.",
                        suggestions=["Use double quotes for quotations within single quotes.",
                                   "Follow standard nesting conventions for quotation marks."],
                        severity='medium'
                    ))
        
        return errors

    def _check_quotation_consistency(self, doc, quote_analysis: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check quotation mark consistency using linguistic anchors."""
        errors = []
        
        if not quote_analysis['all_quotes']:
            return errors
        
        # Check for consistent quote style
        quote_types = [quote['type'] for quote in quote_analysis['all_quotes']]
        unique_types = set(quote_types)
        
        if len(unique_types) > 2:  # Allow for single and double quotes
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Multiple quotation mark styles detected.",
                suggestions=["Use consistent quotation mark style throughout document.",
                           "Stick to standard single and double quotation marks.",
                           "Avoid mixing different quotation mark styles."],
                severity='low'
            ))
        
        return errors

    def _analyze_with_regex(self, text: str, sentences: List[str]) -> List[Dict[str, Any]]:
        """Fallback regex-based analysis when NLP is unavailable."""
        errors = []
        
        for i, sentence in enumerate(sentences):
            # Pattern 1: Unmatched quotation marks
            double_quote_count = sentence.count('"')
            single_quote_count = sentence.count("'")
            
            if double_quote_count % 2 != 0:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Unmatched double quotation marks detected.",
                    suggestions=["Ensure equal number of opening and closing quotation marks.",
                               "Check for missing or extra quotation marks."],
                    severity='high'
                ))
            
            if single_quote_count % 2 != 0:
                # Filter out contractions
                contraction_pattern = r"\b\w+'\w+\b"
                contractions = len(re.findall(contraction_pattern, sentence))
                adjusted_count = single_quote_count - contractions
                
                if adjusted_count % 2 != 0:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Unmatched single quotation marks detected.",
                        suggestions=["Ensure equal number of opening and closing quotation marks.",
                                   "Check for missing or extra quotation marks.",
                                   "Distinguish between apostrophes and quotation marks."],
                        severity='high'
                    ))
            
            # Pattern 2: Punctuation outside quotes (US style issue)
            if re.search(r'"\s*[.,]', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Punctuation placement may be incorrect for US English style.",
                    suggestions=["Consider moving periods and commas inside quotation marks.",
                               "Follow US English conventions for punctuation placement."],
                    severity='low'
                ))
            
            # Pattern 3: Missing spaces around quotes
            if re.search(r'\w"', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Missing space before opening quotation mark.",
                    suggestions=["Add space before opening quotation mark.",
                               "Ensure proper spacing around quotations."],
                    severity='low'
                ))
            
            if re.search(r'"\w', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Missing space after closing quotation mark.",
                    suggestions=["Add space after closing quotation mark.",
                               "Check spacing around quotation marks."],
                    severity='low'
                ))
            
            # Pattern 4: Nested quotes with wrong style
            if re.search(r'"[^"]*"[^"]*"', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Nested quotation marks may need style adjustment.",
                    suggestions=["Use single quotes for quotations within double quotes.",
                               "Follow standard nesting conventions."],
                    severity='medium'
                ))
            
            # Pattern 5: Empty quotation marks
            if re.search(r'""|\'\'\s*|"\s*"', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Empty quotation marks detected.",
                    suggestions=["Remove empty quotation marks or add content.",
                               "Check if quotation marks are necessary."],
                    severity='medium'
                ))
            
            # Pattern 6: Multiple consecutive quotes
            if re.search(r'"{2,}|\'{{2,}', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Multiple consecutive quotation marks detected.",
                    suggestions=["Check for extra quotation marks.",
                               "Use proper nesting for quotes within quotes."],
                    severity='medium'
                ))
            
            # Pattern 7: Mixed straight and curly quotes
            has_straight = '"' in sentence or "'" in sentence
            has_curly = any(char in sentence for char in ['"', '"', ''', '''])
            
            if has_straight and has_curly:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Mixed quotation mark styles detected.",
                    suggestions=["Use consistent quotation mark style throughout.",
                               "Choose either straight quotes or curly quotes."],
                    severity='low'
                ))
            
            # Pattern 8: Potential dialogue without proper formatting
            if re.search(r'"[A-Z][^"]*[.!?]"[^,]', sentence):
                # This might be dialogue that needs attribution
                if not re.search(r'(said|asked|replied|answered|spoke|told)', sentence, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Dialogue may need attribution or speech tag.",
                        suggestions=["Add attribution like 'he said' or 'she asked'.",
                                   "Include speaker identification for clarity."],
                        severity='low'
                    ))
        
        return errors
