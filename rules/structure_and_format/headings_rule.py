"""
Headings Rule (Modular-Aware)
Based on IBM Style Guide topic: "Headings"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

class HeadingsRule(BaseStructureRule):
    """
    Checks for style issues in headings. This version is now aware of the
    modular topic type (Concept, Procedure, Reference) to apply rules correctly,
    especially regarding the use of gerunds in procedure titles.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'headings'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes a heading for multiple style violations.
        """
        errors = []
        if not context or context.get('block_type') != 'heading':
            return errors
        
        if not nlp:
            return errors

        # Get the topic type from the context to make decisions
        topic_type = context.get('topic_type', 'Concept') # Default to 'Concept' if not specified

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
            # This logic remains sound.
            words = sentence.split()
            if len(words) >= 2:
                words_after_first = words[1:]
                title_cased_words = [word for word in words_after_first if word.istitle() and not word.isupper()]
                
                if len(words) == 2 and len(title_cased_words) > 0:
                    if doc and len(doc) > 1 and doc[1].pos_ == 'NOUN':
                        errors.append(self._create_error(
                            sentence=sentence, sentence_index=i,
                            message="Headings should use sentence-style capitalization, not headline-style.",
                            suggestions=[f"Use lowercase for common words: '{words[0]} {words[1].lower()}'"],
                            severity='low'
                        ))
                elif len(words) > 2 and len(title_cased_words) > len(words) / 3:
                    errors.append(self._create_error(
                        sentence=sentence, sentence_index=i,
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

            # --- Rule 4: Avoid weak lead-in words like gerunds (MODULAR-AWARE) ---
            if len(doc) > 0:
                first_token = doc[0]
                # Check for a gerund, BUT ONLY if the topic type is NOT a Procedure.
                # Gerunds are the standard for Procedure titles in modular documentation.
                if first_token.tag_ == 'VBG' and topic_type != 'Procedure':
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Headings for '{topic_type}' topics should not start with a gerund (e.g., 'Understanding...').",
                        suggestions=[f"Consider rewriting the heading to be more direct, for example, using a noun phrase like 'Overview of {first_token.lemma_}'."],
                        severity='low'
                    ))

        return errors
