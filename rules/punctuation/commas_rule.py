"""
Commas Rule (Corrected and Finalized)
Based on IBM Style Guide topic: "Commas"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens.doc import Doc
    from spacy.tokens.token import Token
except ImportError:
    Doc = None
    Token = None

class CommasRule(BasePunctuationRule):
    """
    Checks for a variety of comma-related style issues, including serial commas,
    comma splices, and missing commas after introductory clauses. This version
    is updated to be compatible with the new error consolidation system and to
    prevent false positives on compound predicates.
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

        doc = nlp(text)

        for i, sent in enumerate(doc.sents):
            errors.extend(self._check_serial_comma(sent, i))
            errors.extend(self._check_comma_splice(sent, i))
            errors.extend(self._check_introductory_clause(sent, i))
            
        return errors

    def _check_serial_comma(self, sent: Doc, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Checks for the required serial (Oxford) comma in lists of three or more.
        **ENHANCED** to distinguish between noun lists and verb phrases.
        """
        errors = []
        conjunctions = {'and', 'or'}

        for token in sent:
            # Linguistic Anchor: Find a coordinating conjunction ('cc')
            if token.lemma_ in conjunctions and token.dep_ == 'cc':
                
                # Find all items potentially in the list by traversing the dependency tree
                list_items = self._get_list_items(token)
                
                # **PRODUCTION-GRADE FIX: This is the core of the fix.**
                # Before proceeding, analyze the nature of the list items.
                if list_items and len(list_items) < 3:
                    # Check the Part-of-Speech of the identified list items.
                    pos_tags = [item.pos_ for item in list_items]
                    is_verb_phrase = pos_tags.count('VERB') >= 1

                    # If it's a compound predicate with only two verbs (e.g., "do this and do that"),
                    # it is NOT a serial comma error. This prevents the false positive.
                    if is_verb_phrase:
                        continue # Skip to the next token in the sentence.

                # Now, proceed with the original logic only if it's a list of 3+ items.
                if len(list_items) >= 3:
                    # Check if the token before the conjunction is NOT a comma.
                    if token.i > sent.start and sent.doc[token.i - 1].text != ',':
                        flagged_token = sent.doc[token.i - 1]
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=sentence_index,
                            message="Missing serial (Oxford) comma before conjunction in a list.",
                            suggestions=[f"Add a comma before '{token.text}'."],
                            severity='high',
                            span=(flagged_token.idx + len(flagged_token.text), flagged_token.idx + len(flagged_token.text)),
                            flagged_text=token.text
                        ))
        return errors

    def _get_list_items(self, conjunction: Token) -> List[Token]:
        """
        Traverses the dependency tree from a conjunction to find all items
        in a potential list.
        """
        list_items = set()
        
        # The head of the conjunction is the item right before it.
        head = conjunction.head
        list_items.add(head)

        # Add direct conjuncts of the head.
        for child in head.children:
            if child.dep_ == 'conj':
                list_items.add(child)

        # Traverse up the tree to find the root of the list and its conjuncts.
        # This handles cases like "A, B, C and D" where C is the head of 'and'.
        current = head
        while current.dep_ == 'conj' and current.head != current:
            current = current.head
            list_items.add(current)
            # Also add siblings of the parent item.
            for child in current.children:
                if child.dep_ == 'conj':
                    list_items.add(child)
        
        # Final check for conjuncts of the root item.
        for child in current.children:
            if child.dep_ == 'conj':
                list_items.add(child)
                
        return sorted(list(list_items), key=lambda x: x.i)


    def _check_comma_splice(self, sent: Doc, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Checks for comma splices, where two independent clauses are joined only by a comma.
        """
        errors = []
        # Find commas that might be joining two independent clauses.
        for token in sent:
            if token.text == ',' and token.dep_ == 'punct':
                # Check if what follows the comma looks like a new independent clause.
                # An independent clause must have a subject.
                is_splice = False
                if token.i < sent.end - 1:
                    next_token = sent.doc[token.i + 1]
                    # Find potential verb of the second clause.
                    second_clause_verb = None
                    for t in sent[token.i + 1:]:
                        if t.pos_ == 'VERB' and t.dep_ != 'amod':
                            second_clause_verb = t
                            break
                    
                    if second_clause_verb:
                        # Check if this verb has its own subject.
                        has_subject = any(c.dep_ in ('nsubj', 'nsubjpass') for c in second_clause_verb.children)
                        # Check if the first clause is also independent.
                        has_first_subject = any(c.dep_ in ('nsubj', 'nsubjpass') for c in token.head.children)

                        if has_subject and has_first_subject:
                            # It's a potential splice. Verify it's not a legitimate structure.
                             if not self._is_legitimate_dependent_clause(sent, token):
                                is_splice = True

                if is_splice:
                    word_before_comma = sent.doc[token.i - 1].text
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_index,
                        message="Potential comma splice: two independent clauses joined by only a comma.",
                        suggestions=[
                            f"Replace the comma after '{word_before_comma}' with a semicolon.",
                            f"Add a coordinating conjunction (like 'and' or 'but') after the comma.",
                            "Split into two separate sentences."
                        ],
                        severity='medium',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
        return errors

    def _is_legitimate_dependent_clause(self, sent: Doc, comma: Token) -> bool:
        """
        Checks if the clause before the comma is a valid introductory dependent clause.
        """
        # If the sentence starts with a subordinating conjunction, it's likely a valid structure.
        subordinating_conjunctions = {'after', 'although', 'as', 'because', 'before', 'if', 'since', 'unless', 'until', 'when', 'while'}
        if sent[sent.start].lemma_.lower() in subordinating_conjunctions:
            return True

        # Check for adverbial clause modifiers before the comma.
        for token in sent[:comma.i]:
            if token.dep_ == 'advcl':
                return True
        return False


    def _check_introductory_clause(self, sent: Doc, sentence_index: int) -> List[Dict[str, Any]]:
        """
        A robust check for a missing comma after an introductory clause.
        """
        errors = []
        if len(sent) < 4:
            return errors

        # Linguistic Anchor: An introductory clause is often an adverbial clause ('advcl')
        # or prepositional phrase ('prep') that appears before the main clause's subject.
        
        # Find the main verb and its subject
        main_verb = next((tok for tok in sent if tok.dep_ == 'ROOT'), None)
        if not main_verb: return errors
        
        main_subject = next((child for child in main_verb.children if child.dep_ in ('nsubj', 'nsubjpass')), None)
        if not main_subject: return errors

        # Find the first token of the main clause (usually the subject, but could be an aux verb)
        main_clause_start_token = main_subject
        for child in main_verb.children:
            if child.dep_ in ('aux', 'auxpass') and child.i < main_clause_start_token.i:
                main_clause_start_token = child

        # If the main clause doesn't start the sentence, we have an introductory element.
        if main_clause_start_token.i > sent.start:
            token_before_main_clause = sent.doc[main_clause_start_token.i - 1]
            
            # The introductory element must be longer than a few words to require a comma.
            intro_element_length = main_clause_start_token.i - sent.start
            
            if intro_element_length > 2 and token_before_main_clause.text != ',':
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=sentence_index,
                    message="Missing comma after an introductory clause or phrase.",
                    suggestions=[f"Add a comma after '{token_before_main_clause.text}'."],
                    severity='medium',
                    span=(token_before_main_clause.idx + len(token_before_main_clause.text), token_before_main_clause.idx + len(token_before_main_clause.text)),
                    flagged_text=token_before_main_clause.text
                ))
        return errors
