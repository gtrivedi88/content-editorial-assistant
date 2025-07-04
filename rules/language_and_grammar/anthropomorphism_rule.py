"""
Anthropomorphism Rule (Corrected)
Based on IBM Style Guide topic: "Anthropomorphism"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class AnthropomorphismRule(BaseLanguageRule):
    """
    Checks for instances where inanimate or abstract objects are given
    human characteristics. This version uses verb lemmas for more reliable detection.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'anthropomorphism'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for anthropomorphism.
        """
        errors = []
        if not nlp:
            return errors

        # Linguistic Anchor: Verbs (lemmas) that often imply human thought or action.
        human_verb_lemmas = {'think', 'know', 'believe', 'want', 'see', 'ask', 'tell', 'allow', 'let', 'permit'}
        
        # Linguistic Anchor: Nouns representing inanimate or abstract objects.
        inanimate_subject_lemmas = {'system', 'application', 'program', 'module', 'server', 'window', 'interface', 'team'}

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # Check if a human-like verb has an inanimate or abstract subject.
                if token.lemma_ in human_verb_lemmas:
                    # Find the subject of the verb using the dependency parse.
                    subject = [child for child in token.children if child.dep_ == 'nsubj']
                    if subject and subject[0].lemma_ in inanimate_subject_lemmas:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=f"Anthropomorphism: The {subject[0].text} '{token.text}' like a person.",
                            suggestions=["Rewrite the sentence to focus on user actions or state facts directly. For example, instead of 'The system thinks...', write 'The system determines...'."],
                            severity='low'
                        ))
        return errors
