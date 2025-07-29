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
        return 'commas'

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
                # Find all items in the list by traversing the dependency tree
                list_items = set()  # Use set to avoid duplicates
                
                # Start with the head of the conjunction
                head = token.head
                list_items.add(head)
                
                # Add conjuncts of the head (items after the conjunction)
                for child in head.children:
                    if child.dep_ == 'conj':
                        list_items.add(child)
                
                # Traverse up to find the root of the list and its conjuncts
                current = head
                while current.dep_ == 'conj' and current.head != current:
                    current = current.head
                    list_items.add(current)
                
                # Add any conjuncts of the root item
                for child in current.children:
                    if child.dep_ == 'conj':
                        list_items.add(child)
                
                # LINGUISTIC ANCHOR 1: Dependency-based detection (primary method)
                dependency_based_detection = len(list_items) >= 3 and ',' in sent.text
                
                # LINGUISTIC ANCHOR 2: Text-based pattern detection (backup method)
                # Handle cases where SpaCy dependency parsing misses list items
                text_based_detection = False
                if not dependency_based_detection and ',' in sent.text:
                    text_based_detection = self._detect_serial_comma_by_pattern(token, sent)
                
                # Proceed if either method detects a potential serial comma issue
                if dependency_based_detection or text_based_detection:
                    # Check if the token before the conjunction is NOT a comma
                    if token.i > sent.start and sent.doc[token.i - 1].text != ',':
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

    def _detect_serial_comma_by_pattern(self, conjunction_token, sent: Doc) -> bool:
        """
        LINGUISTIC ANCHOR: Text-based pattern detection for serial comma cases
        where SpaCy dependency parsing fails to identify all list items.
        
        Looks for patterns like: "item1, item2, item3 and item4"
        where SpaCy might miss that item1 is part of the list.
        """
        # Get the text before the conjunction
        text_before = sent.text[:conjunction_token.idx - sent.start_char]
        
        # Count commas before the conjunction
        comma_count = text_before.count(',')
        
        # PATTERN 1: If there are 2+ commas before the conjunction, 
        # this suggests a list of 3+ items even if SpaCy misses some
        if comma_count >= 2:
            return True
        
        # PATTERN 2: Look for specific patterns that suggest compound list items
        # like "main console, the side panel and the log viewer"
        import re
        
        # Pattern: article + noun + comma + article + noun + (no comma) + conjunction
        # This catches cases like "the console, the panel and the viewer"
        pattern = r'\b(?:the|a|an)\s+\w+,\s+(?:the|a|an)\s+\w+\s+(?:and|or)\b'
        if re.search(pattern, sent.text, re.IGNORECASE):
            return True
        
        # PATTERN 3: Look for adjective + noun patterns that suggest list items
        # like "main console, side panel and log viewer" 
        words_before_conjunction = text_before.strip().split()
        if len(words_before_conjunction) >= 4:  # At least "word1, word2 word3"
            # Check if we have at least one comma and multiple potential noun phrases
            if comma_count >= 1:
                # Split by commas to get potential list items
                potential_items = [item.strip() for item in text_before.split(',')]
                if len(potential_items) >= 2:
                    # If each potential item has 1-3 words, likely a list
                    item_word_counts = [len(item.split()) for item in potential_items]
                    if all(1 <= count <= 3 for count in item_word_counts):
                        return True
        
        return False

    def _check_comma_splice(self, sent: Doc, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Checks for comma splices, where two independent clauses are joined only by a comma.
        Uses robust dependency parsing to accurately identify clause boundaries.
        """
        errors = []
        for token in sent:
            # LINGUISTIC ANCHOR 1: Find comma that punctuates clausal structure
            if token.text == ',' and token.dep_ == 'punct':
                head_verb = token.head
                
                # LINGUISTIC ANCHOR 2: Check for comma splices using robust pattern detection
                splice_detected = self._detect_comma_splice_patterns(token, head_verb, sent)
                
                if splice_detected:
                    conjunct_verb = splice_detected['second_clause_verb']
                    
                    # LINGUISTIC ANCHOR 3: Find the actual word before the comma for accurate error messaging
                    word_before_comma = self._find_word_before_comma(token, sent)
                    first_clause_end = self._find_first_clause_end(token, sent)
                    second_clause_start = self._find_second_clause_start(token, conjunct_verb, sent)
                    
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_index,
                        message=f"Potential comma splice: two independent clauses joined by only a comma.",
                        suggestions=[
                            f"Replace the comma after '{word_before_comma}' with a semicolon.",
                            f"Add a coordinating conjunction after the comma: '{first_clause_end}, and {second_clause_start}'.",
                            f"Split into two sentences: '{first_clause_end}. {second_clause_start.capitalize()}...'"
                        ],
                        severity='medium',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
        return errors

    def _detect_comma_splice_patterns(self, comma_token, head_verb, sent: Doc) -> dict:
        """
        LINGUISTIC ANCHOR: Detect comma splices using multiple dependency patterns.
        Handles both simple (ccomp) and complex (conj) comma splice structures.
        """
        
        # PATTERN 1: Clausal conjuncts (complex cases like original user example)
        # "...completed, this process is critical and it should not be skipped"
        clausal_conjuncts = [child for child in head_verb.children if child.dep_ == 'conj' and child.pos_ == 'VERB']
        
        for conjunct in clausal_conjuncts:
            if conjunct.i > comma_token.i:
                # Verify the conjunct has its own subject (independent clause)
                has_subject = any(child.dep_ in ('nsubj', 'nsubjpass') for child in conjunct.children)
                if has_subject:
                    return {'second_clause_verb': conjunct, 'pattern': 'conj'}
        
        # PATTERN 2: Clausal complements (simple cases)
        # "The server is running, it processes requests"
        clausal_complements = [child for child in head_verb.children if child.dep_ == 'ccomp' and child.pos_ == 'VERB']
        
        for ccomp in clausal_complements:
            if ccomp.i < comma_token.i:  # ccomp comes before comma
                # Check if the main verb (head_verb) has its own subject after the comma
                main_verb_subjects = [child for child in head_verb.children if child.dep_ in ('nsubj', 'nsubjpass')]
                if main_verb_subjects and any(subj.i > comma_token.i for subj in main_verb_subjects):
                    # Also verify the ccomp has its own subject (making it independent)
                    ccomp_has_subject = any(child.dep_ in ('nsubj', 'nsubjpass') for child in ccomp.children)
                    if ccomp_has_subject:
                        return {'second_clause_verb': head_verb, 'pattern': 'ccomp'}
        
        # PATTERN 3: Direct independent clauses after comma
        # Look for any verb after the comma that has its own subject
        for i in range(comma_token.i + 1, sent.end):
            token = sent.doc[i]
            if token.pos_ == 'VERB' and token.dep_ in ('ROOT', 'ccomp', 'advcl'):
                has_subject = any(child.dep_ in ('nsubj', 'nsubjpass') for child in token.children)
                if has_subject:
                    # Make sure this isn't a legitimate dependent clause
                    if not self._is_legitimate_dependent_clause(token, comma_token):
                        return {'second_clause_verb': token, 'pattern': 'independent'}
        
        return None

    def _is_legitimate_dependent_clause(self, verb_token, comma_token) -> bool:
        """
        LINGUISTIC ANCHOR: Check if a clause after a comma is a legitimate dependent clause.
        Examples of legitimate cases: "When X happens, Y occurs", "After deployment, the system starts"
        """
        # Check for subordinating conjunctions that indicate dependent clauses
        subordinating_conjunctions = {'when', 'while', 'although', 'because', 'since', 'if', 'unless', 'before', 'after', 'as'}
        
        # PATTERN 1: Look backwards from the comma for subordinating conjunctions
        for i in range(comma_token.i - 1, max(comma_token.i - 10, 0), -1):
            token = comma_token.doc[i]
            if token.lemma_.lower() in subordinating_conjunctions:
                return True
        
        # PATTERN 2: Check if sentence starts with subordinating conjunction
        # Handles: "When the system starts, it loads..." or "After deployment, the system requires..."
        sent_start = comma_token.doc[comma_token.sent.start:comma_token.i]
        for token in sent_start:
            if token.lemma_.lower() in subordinating_conjunctions:
                return True
        
        # PATTERN 3: Check for adverbial clause markers in dependency structure
        # Look for 'mark' dependency (subordinating conjunction markers)
        for token in comma_token.doc[comma_token.sent.start:comma_token.i]:
            if token.dep_ == 'mark' and token.lemma_.lower() in subordinating_conjunctions:
                return True
        
        # PATTERN 4: Check if the clause before comma is marked as advcl (adverbial clause)
        for token in comma_token.doc[comma_token.sent.start:comma_token.i]:
            if token.dep_ == 'advcl':
                return True
        
        return False

    def _find_word_before_comma(self, comma_token, sent: Doc) -> str:
        """
        LINGUISTIC ANCHOR: Find the actual word immediately before the comma.
        This provides accurate context for error messages.
        """
        if comma_token.i > sent.start:
            return sent.doc[comma_token.i - 1].text
        return "unknown"

    def _find_first_clause_end(self, comma_token, sent: Doc) -> str:
        """
        LINGUISTIC ANCHOR: Extract the first clause text ending at the comma.
        Walks backwards from comma to find clause boundary.
        """
        # Find the start of the sentence or a previous punctuation
        start_idx = sent.start
        for i in range(comma_token.i - 1, sent.start - 1, -1):
            if sent.doc[i].text in '.!?;':
                start_idx = i + 1
                break
        
        # Extract text from start to comma
        clause_tokens = [sent.doc[i].text for i in range(start_idx, comma_token.i)]
        return ' '.join(clause_tokens).strip()

    def _find_second_clause_start(self, comma_token, conjunct_verb, sent: Doc) -> str:
        """
        LINGUISTIC ANCHOR: Extract the beginning of the second clause after the comma.
        Uses the conjunct verb to identify the start of the independent clause.
        """
        # Start from the token immediately after the comma
        start_idx = comma_token.i + 1
        
        # Find the subject of the second clause
        subject = None
        for child in conjunct_verb.children:
            if child.dep_ in ('nsubj', 'nsubjpass'):
                subject = child
                break
        
        # If we found a subject, start from there, otherwise start after comma
        if subject and subject.i >= start_idx:
            start_idx = subject.i
        
        # Extract a reasonable portion of the second clause (up to 5-6 words)
        end_idx = min(start_idx + 6, sent.end)
        clause_tokens = [sent.doc[i].text for i in range(start_idx, end_idx)]
        return ' '.join(clause_tokens).strip()

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
