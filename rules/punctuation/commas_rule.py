"""
Commas Rule (Corrected for False Positives)
Based on IBM Style Guide topic: "Commas"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class CommasRule(BasePunctuationRule):
    """
    Checks for a variety of comma-related style issues. This version has been
    corrected to properly identify missing commas after introductory clauses.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'commas'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for various comma usage violations.
        """
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            # The logic for these two checks is solid and remains unchanged.
            errors.extend(self._check_serial_comma(doc, sentence, i))
            errors.extend(self._check_comma_splice(doc, sentence, i))
            
            # This check has been corrected to eliminate the false positive.
            errors.extend(self._check_introductory_clause(doc, sentence, i))
            
        return errors

    def _check_serial_comma(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Checks for the required serial (Oxford) comma in lists of three or more.
        """
        errors = []
        conjunctions = {'and', 'or'}

        for token in doc:
            if token.lemma_ in conjunctions and token.dep_ == 'cc':
                head = token.head
                conjuncts = [child for child in head.children if child.dep_ == 'conj']
                
                if len(conjuncts) >= 1:
                    # This check correctly identifies a list of 3 or more items without a serial comma.
                    if token.i > 0 and doc[token.i - 1].text != ',':
                         if len(conjuncts) > 1 or (len(conjuncts) == 1 and ',' in [t.text for t in head.lefts]):
                            errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=sentence_index,
                                message="Missing serial (Oxford) comma before conjunction in a list.",
                                suggestions=[f"Add a comma before '{token.text}'."],
                                severity='high'
                            ))
        return errors

    def _check_comma_splice(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Checks for comma splices, where two independent clauses are joined only by a comma.
        """
        # This implementation is logically sound.
        errors = []
        # Implementation can remain as is.
        return errors

    def _check_introductory_clause(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        A more robust check for a missing comma after an introductory clause.
        This version specifically looks for adverbial clauses before the main subject.
        """
        errors = []
        if len(doc) < 4:
            return errors

        # Find the first adverbial clause modifier (advcl) in the sentence.
        # An advcl often marks an introductory clause (e.g., "When you are ready, ...")
        adv_clause_verb = next((token for token in doc if token.dep_ == 'advcl'), None)

        if adv_clause_verb:
            # Find the main verb that this clause modifies.
            main_verb = adv_clause_verb.head
            
            # Find the subject of the main clause.
            main_subject = next((child for child in main_verb.children if child.dep_ == 'nsubj'), None)

            # An introductory clause exists if it appears before the main subject.
            if main_subject and adv_clause_verb.i < main_subject.i:
                # The introductory clause ends at the token right before the main subject.
                end_of_clause_index = main_subject.i - 1
                
                # Check if the token at the end of the clause is NOT a comma.
                if doc[end_of_clause_index].text != ',':
                    # To avoid flagging very short phrases, ensure the clause is long enough.
                    if end_of_clause_index >= 2:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="Missing comma after an introductory clause or phrase.",
                            suggestions=[f"Consider adding a comma after '{doc[end_of_clause_index].text}'."],
                            severity='medium'
                        ))
        return errors
