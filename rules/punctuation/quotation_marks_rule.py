"""
Quotation Marks Rule (Enhanced)
Based on IBM Style Guide topic: "Quotation marks"
"""
from typing import List, Dict, Any
import re
from .base_punctuation_rule import BasePunctuationRule

class QuotationMarksRule(BasePunctuationRule):
    """
    Checks for multiple quotation mark issues:
    1. Incorrect placement of punctuation (periods, commas).
    2. Inappropriate use of quotes for emphasis or for titles where
       italics are preferred.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'quotation_marks'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for various quotation mark violations.
        """
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            
            # --- Rule 1: Check for Punctuation Placement ---
            for token in doc:
                if token.text == '"' and token.i < len(doc) - 1:
                    next_token = doc[token.i + 1]
                    if next_token.text in {'.', ','}:
                        errors.append(self._create_error(
                            sentence=sentence, sentence_index=i,
                            message="Punctuation placement with quotation mark may be incorrect for US English style.",
                            suggestions=[f"In US English, periods and commas are placed inside the closing quotation mark. Consider moving the '{next_token.text}' to before the closing quote."],
                            severity='low'
                        ))
            
            # --- Rule 2: Check for Inappropriate Use for Titles ---
            # This regex finds text inside double quotes.
            quoted_phrases = re.findall(r'"([^"]+)"', sentence)
            for phrase in quoted_phrases:
                # Linguistic Anchor: Check if the quoted phrase is followed by a word
                # that indicates it's a title (like 'chapter', 'section', 'article').
                if self._is_likely_title(sentence, phrase):
                    # Determine the specific type of title for a more precise message
                    title_type = self._get_title_type(sentence, phrase)
                    if title_type == 'chapter':
                        message = "Chapter titles should be italicized, not enclosed in quotation marks."
                    elif title_type == 'section':
                        message = "Section titles should be italicized, not enclosed in quotation marks."
                    elif title_type == 'book':
                        message = "Book titles should be italicized, not enclosed in quotation marks."
                    else:
                        message = "Titles should be italicized, not enclosed in quotation marks."
                    
                    errors.append(self._create_error(
                        sentence=sentence, sentence_index=i,
                        message=message,
                        suggestions=[f"Consider italicizing '{phrase}' instead of using quotation marks."],
                        severity='medium'
                    ))

        return errors

    def _is_likely_title(self, sentence: str, phrase: str) -> bool:
        """
        A helper function to determine if a quoted phrase is likely a title.
        """
        # Linguistic Anchor: Words that often follow a title reference.
        title_indicators = ['chapter', 'section', 'article', 'topic', 'book', 'paper']
        
        # Create a regex pattern to find the quoted phrase followed by a title indicator.
        # Example: "Installation" chapter
        try:
            pattern = re.compile(re.escape(f'"{phrase}"') + r'\s+(' + '|'.join(title_indicators) + r')', re.IGNORECASE)
            if re.search(pattern, sentence):
                return True
        except re.error:
            # This can happen if the phrase contains special regex characters.
            return False
            
        return False
    
    def _get_title_type(self, sentence: str, phrase: str) -> str:
        """
        Determine the specific type of title based on the context.
        """
        # Check for specific title type indicators
        title_indicators = {
            'chapter': ['chapter'],
            'section': ['section'],
            'book': ['book'],
            'article': ['article'],
            'topic': ['topic'],
            'paper': ['paper']
        }
        
        try:
            for title_type, indicators in title_indicators.items():
                pattern = re.compile(re.escape(f'"{phrase}"') + r'\s+(' + '|'.join(indicators) + r')', re.IGNORECASE)
                if re.search(pattern, sentence):
                    return title_type
        except re.error:
            pass
            
        return 'general'
