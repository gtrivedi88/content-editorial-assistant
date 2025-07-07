"""
Quotation Marks Rule (Enhanced)
Based on IBM Style Guide topic: "Quotation marks"
"""
from typing import List, Dict, Any
import re
from .base_punctuation_rule import BasePunctuationRule

class QuotationMarksRule(BasePunctuationRule):
    """
    Checks for multiple quotation mark issues, including incorrect placement
    of punctuation and inappropriate use for titles, using dependency parsing
    and linguistic anchors to ensure context-aware analysis.
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
            errors.extend(self._check_punctuation_placement(doc, sentence, i))
            
            # --- Rule 2: Check for Inappropriate Use for Titles ---
            errors.extend(self._check_inappropriate_use_for_titles(sentence, i))

        return errors

    def _check_punctuation_placement(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Checks for incorrect placement of punctuation relative to quotes."""
        errors = []
        for token in doc:
            # In US English, periods and commas almost always go inside the closing quote.
            # This rule checks for the common error of placing them outside.
            if token.text == '"' and token.i < len(doc) - 1:
                next_token = doc[token.i + 1]
                if next_token.text in {'.', ','}:
                    errors.append(self._create_error(
                        sentence=sentence, sentence_index=sentence_index,
                        message="Punctuation placement with quotation mark may be incorrect for US English style.",
                        suggestions=[f"In US English, periods and commas are placed inside the closing quotation mark. Consider moving the '{next_token.text}' to before the closing quote."],
                        severity='low'
                    ))
            
            # For '?' and '!', placement depends on the sentence's grammatical structure.
            if token.text in {'?', '!'} and token.i > 0:
                prev_token = doc[token.i - 1]
                # Case: Punctuation is OUTSIDE the quote (e.g., ... "title"?).
                # This is only correct if the entire sentence is a question/exclamation.
                if prev_token.text == '"':
                    # We check if the punctuation mark is the root of the dependency tree.
                    # If it's not the root, it probably belongs inside the quote.
                    if token.dep_ != 'ROOT':
                        errors.append(self._create_error(
                            sentence=sentence, sentence_index=sentence_index,
                            message="Incorrect punctuation placement. A question mark or exclamation point should be inside the quotation mark if it applies only to the quoted material.",
                            suggestions=["If the quote itself is a question or exclamation, move the punctuation inside. Example: He shouted, 'Stop!'"],
                            severity='medium'
                        ))
        return errors

    def _check_inappropriate_use_for_titles(self, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Checks if quotes are used for titles where italics are preferred."""
        errors = []
        # This regex finds text inside double quotes.
        quoted_phrases = re.findall(r'"([^"]+)"', sentence)
        for phrase in quoted_phrases:
            # Linguistic Anchor: Check if the quoted phrase is followed by a word
            # that indicates it's a title (like 'chapter', 'section', 'article').
            if self._is_likely_title(sentence, phrase):
                errors.append(self._create_error(
                    sentence=sentence, sentence_index=sentence_index,
                    message=f"Quotation marks may be used inappropriately for the title '{phrase}'.",
                    suggestions=["Use italics for titles of chapters, sections, or articles, not quotation marks."],
                    severity='medium'
                ))
        return errors

    def _is_likely_title(self, sentence: str, phrase: str) -> bool:
        """
        A helper function to determine if a quoted phrase is likely a title by
        checking the words that follow it.
        """
        # Linguistic Anchor: Words that often follow a title reference.
        title_indicators = ['chapter', 'section', 'article', 'topic', 'book', 'paper', 'guide']
        
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
