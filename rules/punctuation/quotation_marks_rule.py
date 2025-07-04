"""
Quotation Marks Rule
Based on IBM Style Guide topic: "Quotation marks"
"""
from typing import List, Dict, Any
from rules.punctuation.base_punctuation_rule import BasePunctuationRule

class QuotationMarksRule(BasePunctuationRule):
    """
    Checks for incorrect placement of punctuation with quotation marks.
    This rule uses dependency parsing to understand the grammatical context
    and determine if punctuation belongs inside or outside the quote,
    reducing false positives.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'quotation_marks'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for incorrect punctuation placement with quotes.
        """
        errors = []
        if not nlp:
            # This rule requires dependency parsing for context awareness.
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # --- Rule 1: Periods and Commas ---
                # In US English, periods and commas are almost always placed
                # inside the closing quotation mark. This rule checks for the
                # common error of placing them outside.
                if token.text == '"' and token.i < len(doc) - 1:
                    next_token = doc[token.i + 1]
                    if next_token.text in {'.', ','}:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message="Punctuation placement with quotation mark may be incorrect for US English style.",
                            suggestions=[f"In US English, periods and commas are placed inside the closing quotation mark. Consider moving the '{next_token.text}' to before the closing quote."],
                            severity='low'
                        ))

                # --- Rule 2: Question Marks and Exclamation Points ---
                # The placement of these depends on the grammar of the sentence.
                # This is where dependency parsing is crucial.
                if token.text in {'?', '!'} and token.i > 0:
                    prev_token = doc[token.i - 1]
                    if prev_token.text == '"':
                        # The punctuation is INSIDE the quote. This is only correct if
                        # the quoted material itself is a question or exclamation.
                        # We check if the main sentence verb is NOT interrogative.
                        main_verb = self._find_main_verb(doc)
                        if main_verb and not self._is_interrogative(main_verb):
                             # Example: He asked, "Are you leaving?". The main verb "asked" is not interrogative.
                             # But this is complex. A simpler check is to see if the punctuation is the ROOT of the sentence.
                             # If it is, it belongs outside.
                             if token.dep_ != 'ROOT':
                                pass # This is likely correct.
                        
                    elif prev_token.i > 0 and doc[token.i - 2].text == '"':
                        # The punctuation is OUTSIDE the quote. This is only correct if the
                        # entire sentence is a question or exclamation.
                        # We check if the punctuation mark is the root of the dependency tree.
                        if token.dep_ != 'ROOT':
                            errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=i,
                                message="Incorrect punctuation placement. A question mark or exclamation point should be inside the quotation mark if it applies only to the quoted material.",
                                suggestions=["If the quote itself is a question/exclamation, move the punctuation inside. Example: He shouted, 'Stop!'"],
                                severity='medium'
                            ))


        return errors

    def _find_main_verb(self, doc):
        """Finds the root verb of the document."""
        for token in doc:
            if token.dep_ == "ROOT" and token.pos_ == "VERB":
                return token
        return None

    def _is_interrogative(self, verb_token) -> bool:
        """Checks if a verb is part of an interrogative clause."""
        # Check for auxiliary verbs that start questions (e.g., "Do you...", "Is he...")
        for child in verb_token.children:
            if child.dep_ == 'aux' and child.i < verb_token.i:
                return True
        # Check for interrogative pronouns/adverbs (e.g., "Who did...", "Why is...")
        for child in verb_token.children:
            if child.dep_ == 'nsubj' and child.tag_ in ['WDT', 'WP', 'WPS', 'WRB']:
                return True
        return False