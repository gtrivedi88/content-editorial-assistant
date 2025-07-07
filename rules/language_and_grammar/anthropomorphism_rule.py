"""
Anthropomorphism Rule
Based on IBM Style Guide topic: "Anthropomorphism"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class AnthropomorphismRule(BaseLanguageRule):
    """
    Checks for instances where inanimate objects or abstract concepts are
    given human characteristics, using dependency parsing to identify the
    grammatical subject of human-like verbs.
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
            # This rule requires dependency parsing, so NLP is essential.
            return errors

        # Linguistic Anchor: A set of verb lemmas that often imply human thought or action.
        human_verb_lemmas = {'think', 'know', 'believe', 'want', 'see', 'ask', 'tell', 'allow', 'let', 'permit', 'decide', 'expect'}
        
        # Linguistic Anchor: A set of noun lemmas representing inanimate or abstract objects
        # that should not perform human actions.
        inanimate_subject_lemmas = {'system', 'application', 'program', 'module', 'server', 'window', 'interface', 'team', 'software', 'feature'}

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # Check if the token is a verb from our human-like list.
                if token.lemma_ in human_verb_lemmas:
                    
                    # --- Context-Aware Check ---
                    # Find the subject of this verb using the dependency parse.
                    subject_tokens = [child for child in token.children if child.dep_ == 'nsubj']
                    
                    if subject_tokens:
                        subject = subject_tokens[0]
                        # If the subject's lemma is in our list of inanimate objects, it's an error.
                        if subject.lemma_ in inanimate_subject_lemmas:
                            errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=i,
                                message=f"Anthropomorphism: The {subject.text} '{token.text}' like a person.",
                                suggestions=["Rewrite the sentence to focus on user actions or state facts directly. For example, instead of 'The system thinks...', write 'The system determines...'."],
                                severity='low'
                            ))
        return errors
