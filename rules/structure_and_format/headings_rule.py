"""
Headings Rule (Modular-Aware)
Based on IBM Style Guide topic: "Headings"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class HeadingsRule(BaseStructureRule):
    """
    Checks for style issues in headings, such as incorrect capitalization,
    punctuation, and wording based on the topic type (Concept, Procedure, Reference).
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'headings'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes a heading for multiple style violations.
        """
        errors = []
        if not context or context.get('block_type') != 'heading' or not nlp:
            return errors
        
        topic_type = context.get('topic_type', 'Concept')

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            
            # Rule 1: Headings should not end with a period.
            if sentence.strip().endswith('.'):
                errors.append(self._create_error(
                    sentence=sentence, sentence_index=i,
                    message="Headings should not end with a period.",
                    suggestions=["Remove the period from the end of the heading."],
                    severity='medium',
                    span=(len(sentence) - 1, len(sentence)),
                    flagged_text='.'
                ))

            # Rule 2: Use sentence-style capitalization.
            words = sentence.split()
            if len(words) > 1:
                # Check for any non-proper nouns that are capitalized after the first word
                capitalized_words = []
                for word in words[1:]:
                    if word.istitle():
                        # Use spaCy to check if this word is a proper noun
                        word_doc = nlp(word)
                        if word_doc and len(word_doc) > 0:
                            # Check if it's a proper noun or named entity
                            is_proper_noun = word_doc[0].pos_ == 'PROPN' or any(ent.text == word for ent in word_doc.ents)
                            if not is_proper_noun:
                                capitalized_words.append(word)
                        else:
                            # If we can't analyze with spaCy, be conservative and flag it
                            capitalized_words.append(word)
                
                # Flag if ANY non-proper noun is capitalized after the first word
                if len(capitalized_words) >= 1:
                    errors.append(self._create_error(
                        sentence=sentence, sentence_index=i,
                        message="Headings should use sentence-style capitalization, not headline-style.",
                        suggestions=["Capitalize only the first word and any proper nouns in the heading."],
                        severity='low',
                        span=(0, len(sentence)),
                        flagged_text=sentence
                    ))

            # Rule 3: Avoid question-style headings.
            if sentence.strip().endswith('?'):
                errors.append(self._create_error(
                    sentence=sentence, sentence_index=i,
                    message="Avoid using questions in headings for technical documentation.",
                    suggestions=["Rewrite the heading as a statement or a noun phrase."],
                    severity='low',
                    span=(len(sentence) - 1, len(sentence)),
                    flagged_text='?'
                ))

            # Rule 4: Avoid weak lead-in words like gerunds (MODULAR-AWARE).
            if doc and len(doc) > 0:
                first_token = doc[0]
                if first_token.tag_ == 'VBG' and topic_type != 'Procedure':
                    errors.append(self._create_error(
                        sentence=sentence, sentence_index=i,
                        message=f"Headings for '{topic_type}' topics should not start with a gerund (e.g., 'Understanding...').",
                        suggestions=[f"Consider rewriting the heading to be more direct, for example, using a noun phrase like 'Overview of {first_token.lemma_}'."],
                        severity='low',
                        span=(first_token.idx, first_token.idx + len(first_token.text)),
                        flagged_text=first_token.text
                    ))
        return errors
