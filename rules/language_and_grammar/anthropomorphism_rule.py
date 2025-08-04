"""
Anthropomorphism Rule
Based on IBM Style Guide topic: "Anthropomorphism"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

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
            return errors

        doc = nlp(text)
        human_verb_lemmas = {'think', 'know', 'believe', 'want', 'see', 'ask', 'tell', 'allow', 'let', 'permit', 'decide', 'expect'}
        inanimate_subject_lemmas = {'system', 'application', 'program', 'module', 'server', 'window', 'interface', 'team', 'software', 'feature'}

        for i, sent in enumerate(doc.sents):
            for token in sent:
                if token.lemma_ in human_verb_lemmas:
                    subject_tokens = [child for child in token.children if child.dep_ == 'nsubj']
                    if subject_tokens:
                        subject = subject_tokens[0]
                        if subject.lemma_ in inanimate_subject_lemmas:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=f"Anthropomorphism: The {subject.text} '{token.text}' like a person.",
                                suggestions=["Rewrite the sentence to focus on user actions or state facts directly. For example, instead of 'The system thinks...', write 'The system determines...'."],
                                severity='low',
                                text=text,  # Enhanced: Pass full text for better confidence analysis
                                context=context,  # Enhanced: Pass context for domain-specific validation
                                span=(subject.idx, token.idx + len(token.text)),
                                flagged_text=f"{subject.text} {token.text}"
                            ))
        return errors
