"""
Articles Rule
Based on IBM Style Guide topic: "Articles"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class ArticlesRule(BaseLanguageRule):
    """
    Checks for common article errors, such as using 'a' vs 'an'.
    """
    def _get_rule_type(self) -> str:
        return 'articles'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        vowel_sounds = 'aeiou'
        
        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for j, token in enumerate(doc):
                if token.lower_ == 'a' and j < len(doc) - 1:
                    next_token = doc[j + 1]
                    # Check if the next word starts with a vowel sound.
                    if next_token.text[0].lower() in vowel_sounds:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=f"Incorrect article usage: Use 'an' before a vowel sound.",
                            suggestions=[f"Change 'a {next_token.text}' to 'an {next_token.text}'."],
                            severity='medium'
                        ))
                elif token.lower_ == 'an' and j < len(doc) - 1:
                    next_token = doc[j + 1]
                    # Check if the next word starts with a consonant sound.
                    if next_token.text[0].lower() not in vowel_sounds:
                         errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=f"Incorrect article usage: Use 'a' before a consonant sound.",
                            suggestions=[f"Change 'an {next_token.text}' to 'a {next_token.text}'."],
                            severity='medium'
                        ))
        return errors
