"""
Capitalization Rule (Context-Aware)
Based on IBM Style Guide topic: "Capitalization"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class CapitalizationRule(BaseLanguageRule):
    """
    Checks for various capitalization issues, applying different logic based
    on the structural context (heading, list item, paragraph). It uses
    Part-of-Speech tagging to distinguish between common and proper nouns,
    which significantly reduces false positives.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'capitalization'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for capitalization errors based on the provided context.
        """
        errors = []
        if not nlp:
            return errors

        # --- Context-Aware Rule Dispatcher ---
        # Get the block type from the context dictionary provided by the parser.
        block_type = context.get('block_type', 'paragraph') if context else 'paragraph'

        # Apply different checks based on the block type.
        if block_type == 'heading':
            for i, sentence in enumerate(sentences):
                errors.extend(self._check_heading_capitalization(sentence, i))
        
        elif block_type in ['list_item_ordered', 'list_item_unordered']:
            for i, sentence in enumerate(sentences):
                doc = nlp(sentence)
                if doc:
                    errors.extend(self._check_list_item_capitalization(doc, sentence, i))

        else: # Default to paragraph rules
            for i, sentence in enumerate(sentences):
                doc = nlp(sentence)
                if doc:
                    errors.extend(self._check_general_text_capitalization(doc, sentence, i))

        return errors

    def _check_heading_capitalization(self, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Rule for headings: Enforces sentence-style capitalization.
        """
        errors = []
        words = sentence.split()
        # Check headings with 2 or more words for sentence-style capitalization
        if len(words) >= 2:
            # Count words (ignoring the first) that are title-cased but not all-caps (like acronyms).
            title_cased_words = [word for word in words[1:] if word.istitle() and not word.isupper()]
            
            # For 2-word headings, be more strict about common nouns
            if len(words) == 2 and len(title_cased_words) > 0:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Headings should use sentence-style capitalization, not headline-style.",
                    suggestions=[f"Use lowercase for common words: '{words[0]} {words[1].lower()}'"],
                    severity='low'
                ))
            # For longer headings, use the original heuristic
            elif len(words) > 2 and len(title_cased_words) > len(words) / 3:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Headings should use sentence-style capitalization, not headline-style.",
                    suggestions=["Capitalize only the first word and any proper nouns in the heading."],
                    severity='low'
                ))
        return errors

    def _check_list_item_capitalization(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Rule for list items: The first word should be capitalized.
        """
        errors = []
        if len(doc) > 0:
            first_token = doc[0]
            # Linguistic Anchor: The first token of a list item should be capitalized.
            if not first_token.is_upper and not first_token.is_title:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="The first word of a list item should be capitalized.",
                    suggestions=[f"Capitalize the word '{first_token.text}'."],
                    severity='low'
                ))
        return errors

    def _check_general_text_capitalization(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Rule for general paragraphs: Avoid capitalizing common nouns mid-sentence.
        """
        errors = []
        for token in doc:
            # Linguistic Anchor: Check for words that are title-cased but are NOT
            # at the beginning of a sentence and are NOT proper nouns (NNP/NNPS).
            # This prevents flagging names like "IBM" or "Jane Doe".
            if token.is_title and not token.is_sent_start and token.tag_ not in ['NNP', 'NNPS']:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message=f"Unnecessary capitalization of the common noun '{token.text}'.",
                    suggestions=[f"Use lowercase for '{token.text.lower()}' unless it is a proper noun."],
                    severity='low'
                ))
        return errors
