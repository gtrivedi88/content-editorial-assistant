"""
Commas Rule
Based on IBM Style Guide topic: "Commas"
"""
from typing import List, Dict, Any, Set, Tuple, Optional
import re
from .base_punctuation_rule import BasePunctuationRule

class CommasRule(BasePunctuationRule):
    """
    Comprehensive comma usage checker using morphological spaCy analysis with linguistic anchors.
    Handles serial commas, comma splices, compound sentences, appositives, clauses, and more.
    """
    
    def _get_rule_type(self) -> str:
        return 'commas'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        
        # Fallback to regex-based analysis if nlp is unavailable
        if not nlp:
            return self._analyze_with_regex(text, sentences)
        
        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            errors.extend(self._analyze_sentence_with_nlp(doc, sentence, i))
            
        return errors

    def _analyze_sentence_with_nlp(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Comprehensive NLP-based comma analysis using linguistic anchors."""
        errors = []
        
        # Check various comma usage patterns
        errors.extend(self._check_serial_comma_usage(doc, sentence, sentence_index))
        errors.extend(self._check_comma_splices(doc, sentence, sentence_index))
        errors.extend(self._check_compound_sentences(doc, sentence, sentence_index))
        errors.extend(self._check_restrictive_vs_nonrestrictive_clauses(doc, sentence, sentence_index))
        errors.extend(self._check_introductory_elements(doc, sentence, sentence_index))
        errors.extend(self._check_appositives(doc, sentence, sentence_index))
        errors.extend(self._check_coordinate_adjectives(doc, sentence, sentence_index))
        errors.extend(self._check_parenthetical_expressions(doc, sentence, sentence_index))
        errors.extend(self._check_conjunctive_adverbs(doc, sentence, sentence_index))
        errors.extend(self._check_unnecessary_commas(doc, sentence, sentence_index))
        
        return errors

    def _check_serial_comma_usage(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check for missing serial (Oxford) comma using linguistic anchors."""
        errors = []
        
        for token in doc:
            # Linguistic anchor: Coordinating conjunctions in lists
            if self._is_coordinating_conjunction(token) and token.dep_ == 'cc':
                head = token.head
                conjuncts = [child for child in head.children if child.dep_ == 'conj']
                
                if len(conjuncts) >= 1:  # Multiple items in series
                    # Check if there's a comma before the conjunction
                    if token.i > 0:
                        prev_token = doc[token.i - 1]
                        
                        # Skip if it's a two-item list (no serial comma needed)
                        if len(conjuncts) == 1 and not self._has_additional_items_in_series(token, doc):
                            continue
                        
                        # Check for missing serial comma
                        if prev_token.text != ',' and not self._is_legitimate_no_comma_context(token, doc):
                            errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=sentence_index,
                                message="Missing serial (Oxford) comma before conjunction in a list of three or more items.",
                                suggestions=[f"Add a comma before '{token.text}'."],
                                severity='high'
                            ))
        
        return errors

    def _check_comma_splices(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check for comma splices using linguistic anchors."""
        errors = []
        
        for token in doc:
            if token.text == ',':
                # Linguistic anchor: Check if comma joins two independent clauses
                if self._is_comma_splice_pattern(token, doc):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message="Comma splice detected: Two independent clauses joined by only a comma.",
                        suggestions=["Use a semicolon instead of a comma.", 
                                   "Add a coordinating conjunction after the comma.",
                                   "Split into two separate sentences."],
                        severity='high'
                    ))
        
        return errors

    def _check_compound_sentences(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check compound sentences for proper comma usage."""
        errors = []
        
        for token in doc:
            if self._is_coordinating_conjunction(token):
                # Linguistic anchor: Check if joining independent clauses
                if self._joins_independent_clauses(token, doc):
                    # Check if comma is missing before conjunction
                    if token.i > 0 and doc[token.i - 1].text != ',':
                        # Skip short clauses (common exception)
                        if not self._are_clauses_short(token, doc):
                            errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=sentence_index,
                                message="Missing comma before coordinating conjunction joining independent clauses.",
                                suggestions=[f"Add a comma before '{token.text}'."],
                                severity='medium'
                            ))
        
        return errors

    def _check_restrictive_vs_nonrestrictive_clauses(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check restrictive vs. nonrestrictive clause punctuation."""
        errors = []
        
        for token in doc:
            # Linguistic anchor: Relative pronouns introducing clauses
            if self._is_relative_pronoun(token):
                clause_type = self._determine_clause_restrictiveness(token, doc)
                
                if clause_type == 'nonrestrictive':
                    # Should be surrounded by commas
                    if not self._is_properly_comma_enclosed(token, doc):
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="Nonrestrictive clause should be set off by commas.",
                            suggestions=["Add commas around the nonrestrictive clause."],
                            severity='medium'
                        ))
                elif clause_type == 'restrictive':
                    # Should NOT be surrounded by commas
                    if self._is_incorrectly_comma_enclosed(token, doc):
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="Restrictive clause should not be set off by commas.",
                            suggestions=["Remove commas around the restrictive clause."],
                            severity='medium'
                        ))
        
        return errors

    def _check_introductory_elements(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check for commas after introductory elements."""
        errors = []
        
        # Find potential introductory elements
        intro_elements = self._find_introductory_elements(doc)
        
        for element_end_idx in intro_elements:
            if element_end_idx < len(doc) - 1:  # Not at end of sentence
                next_token = doc[element_end_idx + 1]
                
                # Check if comma is missing after introductory element
                if next_token.text != ',' and not self._is_short_introductory_element(doc, element_end_idx):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message="Missing comma after introductory element.",
                        suggestions=["Add a comma after the introductory phrase or clause."],
                        severity='medium'
                    ))
        
        return errors

    def _check_appositives(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check comma usage with appositives."""
        errors = []
        
        appositives = self._find_appositives(doc)
        
        for appositive_span in appositives:
            start_idx, end_idx = appositive_span
            
            # Check if appositive is properly comma-enclosed
            if not self._is_appositive_properly_punctuated(doc, start_idx, end_idx):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Appositive should be set off by commas.",
                    suggestions=["Add commas around the appositive phrase."],
                    severity='medium'
                ))
        
        return errors

    def _check_coordinate_adjectives(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check comma usage between coordinate adjectives."""
        errors = []
        
        for token in doc:
            if token.pos_ == 'ADJ':
                # Look for adjacent adjectives
                if self._has_coordinate_adjective_following(token, doc):
                    next_adj_idx = self._find_next_coordinate_adjective(token, doc)
                    
                    if next_adj_idx and doc[next_adj_idx - 1].text != ',':
                        # Verify they're truly coordinate (not cumulative)
                        if self._are_truly_coordinate_adjectives(token, doc[next_adj_idx], doc):
                            errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=sentence_index,
                                message="Missing comma between coordinate adjectives.",
                                suggestions=["Add a comma between the coordinate adjectives."],
                                severity='low'
                            ))
        
        return errors

    def _check_parenthetical_expressions(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check comma usage with parenthetical expressions."""
        errors = []
        
        parentheticals = self._find_parenthetical_expressions(doc)
        
        for paren_span in parentheticals:
            start_idx, end_idx = paren_span
            
            if not self._is_parenthetical_properly_punctuated(doc, start_idx, end_idx):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Parenthetical expression should be set off by commas.",
                    suggestions=["Add commas around the parenthetical expression."],
                    severity='medium'
                ))
        
        return errors

    def _check_conjunctive_adverbs(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check comma usage with conjunctive adverbs."""
        errors = []
        
        for token in doc:
            if self._is_conjunctive_adverb(token):
                # Check position and comma usage
                if self._is_sentence_initial_conjunctive_adverb(token, doc):
                    # Should have comma after
                    if token.i < len(doc) - 1 and doc[token.i + 1].text != ',':
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="Missing comma after conjunctive adverb at sentence beginning.",
                            suggestions=[f"Add a comma after '{token.text}'."],
                            severity='medium'
                        ))
                elif self._is_mid_sentence_conjunctive_adverb(token, doc):
                    # Should be enclosed by commas
                    if not self._is_conjunctive_adverb_properly_enclosed(token, doc):
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="Conjunctive adverb should be set off by commas.",
                            suggestions=["Add commas around the conjunctive adverb."],
                            severity='medium'
                        ))
        
        return errors

    def _check_unnecessary_commas(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check for unnecessary commas using linguistic anchors."""
        errors = []
        
        for token in doc:
            if token.text == ',':
                # Check various patterns of unnecessary commas
                if self._is_comma_between_subject_and_verb(token, doc):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message="Unnecessary comma between subject and verb.",
                        suggestions=["Remove the comma between subject and verb."],
                        severity='medium'
                    ))
                
                elif self._is_comma_between_verb_and_object(token, doc):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message="Unnecessary comma between verb and direct object.",
                        suggestions=["Remove the comma between verb and object."],
                        severity='medium'
                    ))
                
                elif self._is_comma_before_essential_clause(token, doc):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message="Unnecessary comma before essential (restrictive) clause.",
                        suggestions=["Remove the comma before the restrictive clause."],
                        severity='medium'
                    ))
        
        return errors

    # Helper methods using linguistic anchors

    def _is_coordinating_conjunction(self, token) -> bool:
        """Linguistic anchor: Identify coordinating conjunctions."""
        return token.dep_ == 'cc' and token.lemma_ in {'and', 'or', 'but', 'yet', 'so', 'for', 'nor'}

    def _has_additional_items_in_series(self, conjunction_token, doc) -> bool:
        """Check if there are more than two items in the series."""
        head = conjunction_token.head
        conjuncts = [child for child in head.children if child.dep_ == 'conj']
        return len(conjuncts) > 1

    def _is_legitimate_no_comma_context(self, token, doc) -> bool:
        """Check for contexts where no comma is legitimate."""
        # Short phrases or titles
        if token.i < 5:  # Very short construct
            return True
        
        # Check for title-like patterns
        context_tokens = doc[max(0, token.i-3):min(len(doc), token.i+3)]
        title_indicators = any(t.pos_ == 'PROPN' for t in context_tokens)
        
        return title_indicators

    def _is_comma_splice_pattern(self, comma_token, doc) -> bool:
        """Linguistic anchor: Detect comma splices."""
        if comma_token.i == 0 or comma_token.i >= len(doc) - 1:
            return False
        
        # Check if comma connects two independent clauses
        left_clause = doc[:comma_token.i]
        right_clause = doc[comma_token.i + 1:]
        
        left_has_subject_verb = self._has_subject_and_verb(left_clause)
        right_has_subject_verb = self._has_subject_and_verb(right_clause)
        
        return left_has_subject_verb and right_has_subject_verb

    def _joins_independent_clauses(self, conjunction_token, doc) -> bool:
        """Check if conjunction joins two independent clauses."""
        # Find clauses on either side of conjunction
        left_tokens = doc[:conjunction_token.i]
        right_tokens = doc[conjunction_token.i + 1:]
        
        return (self._has_subject_and_verb(left_tokens) and 
                self._has_subject_and_verb(right_tokens))

    def _are_clauses_short(self, conjunction_token, doc) -> bool:
        """Check if clauses are short (common exception for comma usage)."""
        left_tokens = doc[:conjunction_token.i]
        right_tokens = doc[conjunction_token.i + 1:]
        
        return len(left_tokens) <= 4 and len(right_tokens) <= 4

    def _has_subject_and_verb(self, tokens) -> bool:
        """Linguistic anchor: Check if token sequence has subject and verb."""
        if not tokens:
            return False
        
        has_subject = any(token.dep_ in ['nsubj', 'nsubjpass', 'csubj'] for token in tokens)
        has_verb = any(token.pos_ == 'VERB' for token in tokens)
        
        return has_subject and has_verb

    def _is_relative_pronoun(self, token) -> bool:
        """Linguistic anchor: Identify relative pronouns."""
        return token.lemma_ in {'who', 'whom', 'whose', 'which', 'that'} and token.dep_ in ['nsubj', 'dobj', 'pobj']

    def _determine_clause_restrictiveness(self, rel_pronoun_token, doc) -> str:
        """Determine if a relative clause is restrictive or nonrestrictive."""
        # Linguistic anchor: Use semantic and syntactic cues
        head = rel_pronoun_token.head
        
        # Check for definiteness of antecedent
        antecedent_tokens = [child for child in head.children if child.dep_ in ['det', 'amod']]
        has_definite_article = any(token.lemma_ == 'the' for token in antecedent_tokens)
        
        # "That" typically introduces restrictive clauses
        if rel_pronoun_token.lemma_ == 'that':
            return 'restrictive'
        
        # "Which" with definite antecedent often nonrestrictive
        if rel_pronoun_token.lemma_ == 'which' and has_definite_article:
            return 'nonrestrictive'
        
        # Default to restrictive for ambiguous cases
        return 'restrictive'

    def _is_properly_comma_enclosed(self, token, doc) -> bool:
        """Check if element is properly enclosed by commas."""
        # Find clause boundaries
        clause_start = token.i
        clause_end = self._find_clause_end(token, doc)
        
        has_comma_before = (clause_start > 0 and doc[clause_start - 1].text == ',')
        has_comma_after = (clause_end < len(doc) - 1 and doc[clause_end + 1].text == ',')
        
        return has_comma_before and has_comma_after

    def _find_introductory_elements(self, doc) -> List[int]:
        """Find introductory elements using linguistic anchors."""
        intro_elements = []
        
        for token in doc:
            # Introductory subordinate clauses
            if token.dep_ == 'mark' and token.i < len(doc) // 2:  # In first half of sentence
                clause_end = self._find_clause_end(token, doc)
                intro_elements.append(clause_end)
            
            # Introductory prepositional phrases
            elif token.dep_ == 'prep' and token.i < 5:  # Early in sentence
                phrase_end = self._find_phrase_end(token, doc)
                intro_elements.append(phrase_end)
        
        return intro_elements

    def _find_appositives(self, doc) -> List[Tuple[int, int]]:
        """Find appositives using linguistic anchors."""
        appositives = []
        
        for token in doc:
            if token.dep_ == 'appos':
                # Find the span of the appositive
                start = token.i
                end = self._find_appositive_end(token, doc)
                appositives.append((start, end))
        
        return appositives

    def _are_truly_coordinate_adjectives(self, adj1, adj2, doc) -> bool:
        """Test if adjectives are coordinate (can be separated by 'and')."""
        # Linguistic anchor: Coordinate adjectives modify the noun equally
        # Check if they're in the same syntactic position
        return adj1.head == adj2.head and adj1.dep_ == adj2.dep_

    def _is_conjunctive_adverb(self, token) -> bool:
        """Linguistic anchor: Identify conjunctive adverbs."""
        conjunctive_adverbs = {
            'however', 'therefore', 'consequently', 'moreover', 'furthermore',
            'nevertheless', 'nonetheless', 'meanwhile', 'likewise', 'similarly',
            'conversely', 'instead', 'otherwise', 'thus', 'hence', 'accordingly'
        }
        return token.lemma_ in conjunctive_adverbs

    def _find_parenthetical_expressions(self, doc) -> List[Tuple[int, int]]:
        """Find parenthetical expressions using linguistic anchors."""
        parentheticals = []
        
        # Look for discourse markers and interjections
        for token in doc:
            if token.pos_ == 'INTJ' or token.dep_ == 'discourse':
                start = token.i
                end = self._find_parenthetical_end(token, doc)
                parentheticals.append((start, end))
        
        return parentheticals

    def _is_comma_between_subject_and_verb(self, comma_token, doc) -> bool:
        """Check if comma incorrectly separates subject and verb."""
        if comma_token.i == 0 or comma_token.i >= len(doc) - 1:
            return False
        
        left_token = doc[comma_token.i - 1]
        right_token = doc[comma_token.i + 1]
        
        # Simple check: subject POS followed by verb POS
        is_subject_verb = (left_token.dep_ in ['nsubj', 'nsubjpass'] and 
                          right_token.pos_ == 'VERB')
        
        return is_subject_verb

    def _is_comma_between_verb_and_object(self, comma_token, doc) -> bool:
        """Check if comma incorrectly separates verb and direct object."""
        if comma_token.i == 0 or comma_token.i >= len(doc) - 1:
            return False
        
        left_token = doc[comma_token.i - 1]
        right_token = doc[comma_token.i + 1]
        
        is_verb_object = (left_token.pos_ == 'VERB' and 
                         right_token.dep_ in ['dobj', 'pobj'])
        
        return is_verb_object

    # Additional helper methods for clause and phrase boundary detection
    def _find_clause_end(self, start_token, doc) -> int:
        """Find the end of a clause starting from a token."""
        for i in range(start_token.i + 1, len(doc)):
            token = doc[i]
            if token.dep_ == 'ROOT' or token.text in ['.', '!', '?', ';']:
                return i - 1
        return len(doc) - 1

    def _find_phrase_end(self, start_token, doc) -> int:
        """Find the end of a phrase starting from a token."""
        for i in range(start_token.i + 1, len(doc)):
            token = doc[i]
            if token.pos_ == 'VERB' or token.text in [',', '.', '!', '?', ';']:
                return i - 1
        return len(doc) - 1

    def _analyze_with_regex(self, text: str, sentences: List[str]) -> List[Dict[str, Any]]:
        """Fallback regex-based analysis when NLP is unavailable."""
        errors = []
        
        for i, sentence in enumerate(sentences):
            # Basic comma patterns detectable without NLP
            
            # Pattern 1: Comma at start of sentence
            if sentence.strip().startswith(','):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Sentence should not begin with a comma.",
                    suggestions=["Remove the comma at the beginning."],
                    severity='high'
                ))
            
            # Pattern 2: Double commas
            if ',,' in sentence:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Double commas detected.",
                    suggestions=["Remove the extra comma."],
                    severity='medium'
                ))
            
            # Pattern 3: Comma before end punctuation
            if re.search(r',\s*[.!?]', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Unnecessary comma before end punctuation.",
                    suggestions=["Remove the comma before the period, exclamation point, or question mark."],
                    severity='medium'
                ))
            
            # Pattern 4: Common series patterns
            series_pattern = r'\b\w+\s+\w+\s+and\s+\w+\b'
            if re.search(series_pattern, sentence) and not re.search(r'\b\w+,\s*\w+,\s*and\s+\w+\b', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Possible missing serial comma in list.",
                    suggestions=["Consider adding a comma before 'and' in the series."],
                    severity='low'
                ))
        
        return errors

    # Additional helper methods (simplified versions for missing methods)
    def _is_incorrectly_comma_enclosed(self, token, doc) -> bool:
        """Check if restrictive clause is incorrectly enclosed by commas."""
        return self._is_properly_comma_enclosed(token, doc)  # Simplified

    def _is_short_introductory_element(self, doc, element_end_idx) -> bool:
        """Check if introductory element is short (< 4 words)."""
        return element_end_idx < 4

    def _is_appositive_properly_punctuated(self, doc, start_idx, end_idx) -> bool:
        """Check if appositive is properly punctuated."""
        has_comma_before = start_idx > 0 and doc[start_idx - 1].text == ','
        has_comma_after = end_idx < len(doc) - 1 and doc[end_idx + 1].text == ','
        return has_comma_before and has_comma_after

    def _has_coordinate_adjective_following(self, token, doc) -> bool:
        """Check if token is followed by coordinate adjective."""
        return self._find_next_coordinate_adjective(token, doc) is not None

    def _find_next_coordinate_adjective(self, token, doc) -> Optional[int]:
        """Find the next coordinate adjective."""
        for i in range(token.i + 1, min(token.i + 3, len(doc))):
            if doc[i].pos_ == 'ADJ':
                return i
        return None

    def _is_parenthetical_properly_punctuated(self, doc, start_idx, end_idx) -> bool:
        """Check if parenthetical is properly punctuated."""
        has_comma_before = start_idx > 0 and doc[start_idx - 1].text == ','
        has_comma_after = end_idx < len(doc) - 1 and doc[end_idx + 1].text == ','
        return has_comma_before and has_comma_after

    def _is_sentence_initial_conjunctive_adverb(self, token, doc) -> bool:
        """Check if conjunctive adverb is at sentence start."""
        return token.i == 0 or doc[token.i - 1].text in ['.', '!', '?', ';']

    def _is_mid_sentence_conjunctive_adverb(self, token, doc) -> bool:
        """Check if conjunctive adverb is mid-sentence."""
        return not self._is_sentence_initial_conjunctive_adverb(token, doc)

    def _is_conjunctive_adverb_properly_enclosed(self, token, doc) -> bool:
        """Check if conjunctive adverb is properly enclosed by commas."""
        has_comma_before = token.i > 0 and doc[token.i - 1].text == ','
        has_comma_after = token.i < len(doc) - 1 and doc[token.i + 1].text == ','
        return has_comma_before and has_comma_after

    def _is_comma_before_essential_clause(self, comma_token, doc) -> bool:
        """Check if comma is before essential clause."""
        if comma_token.i >= len(doc) - 1:
            return False
        
        next_token = doc[comma_token.i + 1]
        return next_token.lemma_ == 'that' and next_token.dep_ in ['nsubj', 'dobj']

    def _find_appositive_end(self, token, doc) -> int:
        """Find end of appositive phrase."""
        for i in range(token.i + 1, len(doc)):
            if doc[i].text in [',', '.', '!', '?', ';']:
                return i - 1
        return len(doc) - 1

    def _find_parenthetical_end(self, token, doc) -> int:
        """Find end of parenthetical expression."""
        for i in range(token.i + 1, len(doc)):
            if doc[i].text in [',', '.', '!', '?', ';']:
                return i - 1
        return len(doc) - 1
