"""
Commas Rule (Corrected and Finalized)
Based on IBM Style Guide topic: "Commas"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens.doc import Doc
except ImportError:
    Doc = None

class CommasRule(BasePunctuationRule):
    """
    Checks for a variety of comma-related style issues, including serial commas,
    comma splices, and missing commas after introductory clauses. This version
    is updated to be compatible with the new error consolidation system.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'punctuation_commas'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for various comma usage violations.
        """
        errors = []
        if not nlp:
            return errors

        # Process the entire text once for efficiency and correct indexing
        doc = nlp(text)

        # Iterate through each sentence in the processed document
        for i, sent in enumerate(doc.sents):
            errors.extend(self._check_serial_comma(sent, i))
            errors.extend(self._check_comma_splice(sent, i))
            errors.extend(self._check_introductory_clause(sent, i))
            
        return errors

    def _check_serial_comma(self, sent: Doc, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Checks for the required serial (Oxford) comma in lists of three or more.
        """
        errors = []
        conjunctions = {'and', 'or'}

        for token in sent:
            # Linguistic Anchor: Find a coordinating conjunction ('cc')
            if token.lemma_ in conjunctions and token.dep_ == 'cc':
                # Find the items in the list connected by the conjunction
                head = token.head
                conjuncts = [child for child in head.children if child.dep_ == 'conj']
                
                # Check if it's a list of 3 or more items
                if len(conjuncts) >= 1:
                    # Check if the token before the conjunction is NOT a comma
                    if token.i > sent.start and sent.doc[token.i - 1].text != ',':
                         # Confirm it's a list by checking for other conjuncts or commas
                         if len(conjuncts) > 1 or (len(conjuncts) == 1 and ',' in [t.text for t in head.lefts]):
                            flagged_token = sent.doc[token.i - 1]
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=sentence_index,
                                message="Missing serial (Oxford) comma before conjunction in a list.",
                                suggestions=[f"Add a comma before '{token.text}'."],
                                severity='high',
                                # Span points to where the comma should be inserted
                                span=(flagged_token.idx + len(flagged_token.text), flagged_token.idx + len(flagged_token.text)),
                                flagged_text=token.text
                            ))
        return errors

    def _check_comma_splice(self, sent: Doc, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Checks for comma splices, where two independent clauses are joined only by a comma.
        """
        errors = []
        for token in sent:
            # Linguistic Anchor: A comma splice is often a comma used as punctuation ('punct')
            # between two verbs that are heads of their own clauses.
            if token.text == ',' and token.dep_ == 'punct':
                head_verb = token.head
                # Check if the verb has a clausal conjunct that appears after the comma
                clausal_conjuncts = [child for child in head_verb.children if child.dep_ == 'conj' and child.pos_ == 'VERB']
                
                for conjunct in clausal_conjuncts:
                    if conjunct.i > token.i:
                        # An independent clause must have its own subject.
                        has_subject = any(child.dep_ in ('nsubj', 'nsubjpass') for child in conjunct.children)
                        if has_subject:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=sentence_index,
                                message="Potential comma splice: two independent clauses joined by only a comma.",
                                suggestions=[f"Replace the comma after '{head_verb.text}' with a semicolon, or add a coordinating conjunction like 'and' or 'but'."],
                                severity='medium',
                                span=(token.idx, token.idx + len(token.text)),
                                flagged_text=token.text
                            ))
        return errors

    def _check_introductory_clause(self, sent: Doc, sentence_index: int) -> List[Dict[str, Any]]:
        """
        A robust check for a missing comma after an introductory clause.
        """
        errors = []
        if len(sent) < 4:
            return errors

        # Linguistic Anchor: An introductory clause is often an adverbial clause modifier ('advcl')
        # that appears before the subject of the main clause.
        adv_clause_verb = next((token for token in sent if token.dep_ == 'advcl'), None)

        if adv_clause_verb:
            main_verb = adv_clause_verb.head
            main_subject = next((child for child in main_verb.children if child.dep_ in ('nsubj', 'nsubjpass')), None)

            if main_subject and adv_clause_verb.i < main_subject.i:
                # The introductory clause ends at the token right before the main subject's part of the tree begins.
                end_of_clause = max(list(adv_clause_verb.subtree))
                
                if end_of_clause.i < len(sent.doc) - 1:
                    token_after_clause = sent.doc[end_of_clause.i + 1]

                    # If the token after the end of the clause is not a comma, it's an error.
                    if token_after_clause.text != ',':
                        # To avoid flagging very short phrases, ensure the clause is long enough.
                        if len(list(adv_clause_verb.subtree)) > 2:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=sentence_index,
                                message="Missing comma after an introductory clause or phrase.",
                                suggestions=[f"Consider adding a comma after '{end_of_clause.text}'."],
                                severity='medium',
                                # Span points to where the comma should be inserted
                                span=(end_of_clause.idx + len(end_of_clause.text), end_of_clause.idx + len(end_of_clause.text)),
                                flagged_text=end_of_clause.text
                            ))
        return errors
