"""
Headings Rule
Based on IBM Style Guide topic: "Headings"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

class HeadingsRule(BaseStructureRule):
    """
    Checks for common style issues in headings, such as incorrect
    capitalization, ending punctuation, and weak wording. This rule only
    applies to blocks identified as 'heading' by the parser.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'headings'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes a heading for multiple style violations.
        """
        errors = []
        # This rule should only run on blocks identified as headings by the parser.
        if not context or context.get('block_type') != 'heading':
            return errors
        
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            
            # --- Rule 1: Headings should not end with a period ---
            if sentence.strip().endswith('.'):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Headings should not end with a period.",
                    suggestions=["Remove the period from the end of the heading."],
                    severity='medium'
                ))

            # --- Rule 2: Use sentence-style capitalization ---
            words = sentence.split()
            if len(words) >= 2:  # Check headings with 2 or more words
                # Check if this looks like headline-style capitalization
                words_after_first = words[1:]
                title_cased_words = [word for word in words_after_first if word.istitle() and not word.isupper()]
                
                # For 2-word headings, be more strict since there's less ambiguity
                if len(words) == 2 and len(title_cased_words) > 0:
                    # Check if the second word is likely a proper noun using NLP
                    if doc and len(doc) > 1:
                        second_token = doc[1]
                        # Allow proper nouns (PROPN) but flag common nouns (NOUN)
                        if second_token.pos_ == 'NOUN':
                            errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=i,
                                message="Headings should use sentence-style capitalization, not headline-style.",
                                suggestions=[f"Use lowercase for common words: '{words[0]} {words[1].lower()}'"],
                                severity='low'
                            ))
                # For longer headings, use the original heuristic
                elif len(words) > 2 and len(title_cased_words) > len(words) / 3:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Headings should use sentence-style capitalization, not headline-style.",
                        suggestions=["Capitalize only the first word and any proper nouns in the heading."],
                        severity='low'
                    ))

            # --- Rule 3: Avoid question-style headings ---
            if sentence.strip().endswith('?'):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Avoid using questions in headings for technical documentation.",
                    suggestions=["Rewrite the heading as a statement or a noun phrase."],
                    severity='low'
                ))

            # --- Rule 4: Avoid weak lead-in words like gerunds ---
            if len(doc) > 0:
                first_token = doc[0]
                # Linguistic Anchor: Check if the first word is a gerund (verb ending in -ing).
                if first_token.tag_ == 'VBG':
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Headings that start with a gerund (e.g., 'Understanding...') can be weak.",
                        suggestions=[f"Consider rewriting the heading to be more direct, for example, using a noun phrase like 'Overview of {first_token.lemma_}'."],
                        severity='low'
                    ))

        return errors
