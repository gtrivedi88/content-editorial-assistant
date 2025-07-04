"""
Commas Rule
Based on IBM Style Guide topic: "Commas"
"""
from typing import List, Dict, Any
from rules.punctuation.base_punctuation_rule import BasePunctuationRule

class CommasRule(BasePunctuationRule):
    """
    Checks for a variety of comma-related style issues using dependency parsing
    to understand grammatical context. It focuses on serial commas, comma splices,
    and commas with introductory elements.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'commas'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for various comma usage violations.
        """
        errors = []
        if not nlp:
            # This rule requires dependency parsing, so NLP is essential.
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            errors.extend(self._check_serial_comma(doc, sentence, i))
            errors.extend(self._check_comma_splice(doc, sentence, i))
            errors.extend(self._check_introductory_clause(doc, sentence, i))
            
        return errors

    def _check_serial_comma(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Checks for the required serial (Oxford) comma in lists of three or more.
        """
        errors = []
        # Linguistic Anchor: Coordinating conjunctions that end a list.
        conjunctions = {'and', 'or'}

        for token in doc:
            # Find a coordinating conjunction that is part of a list structure.
            if token.lemma_ in conjunctions and token.dep_ == 'cc':
                head = token.head
                # A list exists if the head has at least one 'conj' (conjunct) dependency.
                conjuncts = [child for child in head.children if child.dep_ == 'conj']
                
                # Check for a list of 3 or more items.
                if len(conjuncts) >= 1:
                    if token.i > 0 and doc[token.i - 1].text != ',':
                         # This check prevents flagging simple "A and B" lists of only two items.
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
        errors = []
        for token in doc:
            if token.text == ',':
                # Check if the comma is connecting two independent clauses.
                # An independent clause has its own subject and verb.
                left_clause = doc[:token.i]
                right_clause = doc[token.i+1:]

                # Linguistic Anchor: A clause is independent if it has a nominal subject and a root verb.
                is_left_independent = any(t.dep_ == 'nsubj' for t in left_clause) and any(t.dep_ == 'ROOT' for t in left_clause)
                is_right_independent = any(t.dep_ == 'nsubj' for t in right_clause) and any(t.dep_ == 'ROOT' for t in right_clause)
                
                if is_left_independent and is_right_independent:
                    # Check if there is no coordinating conjunction after the comma.
                    if token.i < len(doc) - 1 and doc[token.i + 1].dep_ != 'cc':
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="Comma splice detected: two independent clauses joined only by a comma.",
                            suggestions=["Use a semicolon instead of a comma.", "Add a coordinating conjunction (like 'and', 'but', 'or') after the comma.", "Split the text into two separate sentences."],
                            severity='high'
                        ))
        return errors

    def _check_introductory_clause(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Checks for a missing comma after an introductory clause or phrase.
        """
        errors = []
        # Linguistic Anchor: Introductory clauses often start with a subordinating conjunction ('mark')
        # or are adverbial clauses ('advcl').
        for token in doc:
            if token.dep_ in ('mark', 'advcl') and token.head.i > token.i:
                # Find the end of the introductory clause by finding the verb it modifies.
                clause_head = token.head
                if clause_head.i < len(doc) - 1 and doc[clause_head.i].text != ',':
                     # Exception for very short introductory phrases (e.g., "In 2025 you can...")
                    if clause_head.i > 3:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="Missing comma after an introductory clause or phrase.",
                            suggestions=[f"Add a comma after '{doc[clause_head.i - 1].text}'."],
                            severity='medium'
                        ))
                break # Only check the first introductory clause in a sentence.
        return errors
