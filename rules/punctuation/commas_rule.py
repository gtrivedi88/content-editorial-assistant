"""
Commas Rule - Evidence-Based Analysis
Based on IBM Style Guide topic: "Commas"

"""
from typing import List, Dict, Any, Optional
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens.doc import Doc
    from spacy.tokens.token import Token
    from spacy.tokens import Span
except ImportError:
    Doc = None
    Token = None
    Span = None

class CommasRule(BasePunctuationRule):
    """
    Checks for a variety of comma-related style issues using evidence-based analysis:
    - Serial (Oxford) comma requirements
    - Comma splice detection  
    - Missing commas after introductory clauses
    Enhanced with dependency parsing and contextual awareness.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'commas'

    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for comma usage violations:
        - Serial comma requirements with contextual awareness
        - Comma splice detection with structural analysis
        - Missing commas after introductory clauses
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        if not nlp:
            return errors

        try:
            doc = nlp(text)
            for i, sent in enumerate(doc.sents):
                # Check for serial comma issues
                serial_comma_errors = self._analyze_serial_comma_evidence(sent, i, text, context)
                errors.extend(serial_comma_errors)
                
                # Check for comma splice issues
                comma_splice_errors = self._analyze_comma_splice_evidence(sent, i, text, context)
                errors.extend(comma_splice_errors)
                
                # Check for missing commas after introductory clauses
                intro_comma_errors = self._analyze_introductory_comma_evidence(sent, i, text, context)
                errors.extend(intro_comma_errors)
                
        except Exception as e:
            # Graceful degradation for SpaCy errors
            errors.append(self._create_error(
                sentence=text,
                sentence_index=0,
                message=f"Comma analysis failed: {str(e)}",
                suggestions=["Please check the text for obvious comma issues manually."],
                severity='low',
                text=text,
                context=context,
                evidence_score=0.0  # No evidence when analysis fails
            ))
        
        return errors

    # === EVIDENCE-BASED ANALYSIS METHODS ===

    def _analyze_serial_comma_evidence(self, sent: 'Span', sentence_index: int, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for serial comma requirements.
        """
        errors = []
        conjunctions = {'and', 'or'}

        for token in sent:
            if token.lemma_ in conjunctions and token.dep_ == 'cc':
                list_items = self._get_list_items(token)
                
                # Only proceed if we have 3+ items (potential serial comma situation)
                if len(list_items) >= 3:
                    # Check if comma is missing before conjunction
                    if token.i > sent.start and sent.doc[token.i - 1].text != ',':
                        evidence_score = self._calculate_serial_comma_evidence(token, list_items, sent, text, context)
                        
                        if evidence_score > 0.1:
                            # Safe token access to avoid span index errors
                            if token.i > sent.start:
                                flagged_token = sent.doc[token.i - 1]
                                span = (flagged_token.idx + len(flagged_token.text), token.idx + len(token.text))
                            else:
                                flagged_token = token
                                span = (token.idx, token.idx + len(token.text))
                                
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=sentence_index,
                                message=self._get_contextual_serial_comma_message(evidence_score),
                                suggestions=self._generate_smart_serial_comma_suggestions(token, evidence_score, context),
                                severity='high' if evidence_score > 0.7 else 'medium',
                                text=text,
                                context=context,
                                evidence_score=evidence_score,
                                span=span,
                                flagged_text=token.text
                            ))
        return errors

    def _analyze_comma_splice_evidence(self, sent: 'Span', sentence_index: int, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for comma splice detection.
        """
        errors = []
        
        for token in sent:
            if token.text == ',' and token.dep_ == 'punct':
                evidence_score = self._calculate_comma_splice_evidence(token, sent, text, context)
                
                if evidence_score > 0.1:
                    word_before_comma = sent.doc[token.i - 1].text if token.i > sent.start else ""
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_index,
                        message=self._get_contextual_comma_splice_message(evidence_score),
                        suggestions=self._generate_smart_comma_splice_suggestions(word_before_comma, evidence_score, context),
                        severity='medium' if evidence_score > 0.6 else 'low',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
        return errors

    def _analyze_introductory_comma_evidence(self, sent: 'Span', sentence_index: int, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for missing commas after introductory clauses.
        
        === ZERO FALSE POSITIVE GUARD FOR PROPER INTRODUCTORY ELEMENTS ===
        Only flags TRUE introductory elements (subordinate clauses, prepositional phrases
        at sentence start), not random words before the subject.
        """
        errors = []
        
        if len(sent) < 4:
            return errors

        # === CRITICAL FIX: Proper introductory element detection ===
        # ONLY flag actual introductory elements, not arbitrary words before subject
        
        # Check if sentence starts with a subordinating conjunction (true introductory clause)
        subordinating_conjunctions = {
            'after', 'although', 'as', 'because', 'before', 'if', 'since', 
            'unless', 'until', 'when', 'while', 'though', 'whereas', 'wherever'
        }
        
        first_token = sent[sent.start]
        starts_with_subordinator = first_token.lemma_.lower() in subordinating_conjunctions
        
        # Check for adverbial phrases at start (e.g., "In the morning, ...")
        starts_with_prep_phrase = (
            first_token.pos_ == 'ADP' or  # Preposition
            (first_token.pos_ == 'ADV' and len(sent) > 3)  # Adverbial phrase
        )
        
        # Check for participial phrases (e.g., "Walking to work, ...")
        starts_with_participle = first_token.pos_ == 'VERB' and first_token.tag_ in ('VBG', 'VBN')
        
        # If none of these patterns match, this is NOT a true introductory element
        if not (starts_with_subordinator or starts_with_prep_phrase or starts_with_participle):
            return errors  # No introductory element detected
        
        # Find the main clause boundary using proper linguistic analysis
        main_verb = next((tok for tok in sent if tok.dep_ == 'ROOT'), None)
        if not main_verb:
            return errors
        
        main_subject = next((child for child in main_verb.children if child.dep_ in ('nsubj', 'nsubjpass')), None)
        if not main_subject:
            return errors

        # Find the actual end of the introductory element
        # Look for the point where the main clause truly begins
        intro_end_index = None
        
        if starts_with_subordinator:
            # For subordinate clauses, find the subordinate clause's verb and its end
            for token in sent:
                if token.dep_ == 'advcl' or (token.head == main_verb and token.dep_ in ('prep', 'advmod')):
                    # Find the rightmost token in this subordinate structure
                    clause_tokens = [token] + list(token.subtree)
                    intro_end_index = max(t.i for t in clause_tokens if t.i < main_subject.i)
                    break
        elif starts_with_prep_phrase:
            # For prepositional phrases, find the end of the phrase
            for token in sent:
                if token.head == main_verb and token.dep_ == 'prep':
                    phrase_tokens = list(token.subtree)
                    intro_end_index = max(t.i for t in phrase_tokens if t.i < main_subject.i)
                    break
        
        # If we found a proper introductory element, check if it needs a comma
        if intro_end_index and intro_end_index > sent.start:
            intro_element_length = intro_end_index - sent.start + 1
            
            # Only flag if the introductory element is substantial (4+ tokens)
            if intro_element_length >= 4:
                # Check if comma already exists
                last_intro_token = sent.doc[intro_end_index]
                if last_intro_token.nbor(1).text == ',':
                    return errors  # Comma already present
                
                evidence_score = self._calculate_introductory_comma_evidence(
                    main_subject, sent, text, context, intro_element_length
                )
                
                if evidence_score > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_index,
                        message=self._get_contextual_introductory_comma_message(evidence_score),
                        suggestions=self._generate_smart_introductory_comma_suggestions(last_intro_token, evidence_score, context),
                        severity='medium' if evidence_score > 0.6 else 'low',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(last_intro_token.idx + len(last_intro_token.text), last_intro_token.idx + len(last_intro_token.text)),
                        flagged_text=last_intro_token.text
                    ))
        
        return errors

    # === EVIDENCE CALCULATION METHODS ===

    def _calculate_serial_comma_evidence(self, conjunction: 'Token', list_items: List['Token'], sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) that a serial comma is required.
        """
        # Apply zero false positive guards
        if self._apply_zero_false_positive_guards_punctuation(conjunction, context):
            return 0.0
        
        # Base evidence for missing serial comma in 3+ item list
        evidence_score = 0.8
        
        # Check if it's a compound predicate (verbs) vs noun list
        pos_tags = [item.pos_ for item in list_items]
        is_verb_phrase = pos_tags.count('VERB') >= 1
        
        # Compound predicates with only 2 verbs don't need serial comma
        if is_verb_phrase and len(list_items) == 2:
            return 0.0
        
        # Apply linguistic clues
        evidence_score = self._apply_common_linguistic_clues_punctuation(evidence_score, conjunction, sent)
        
        # Apply structural clues
        evidence_score = self._apply_common_structural_clues_punctuation(evidence_score, conjunction, context)
        
        # Apply semantic clues  
        evidence_score = self._apply_common_semantic_clues_punctuation(evidence_score, conjunction, context)
        
        # Adjust for list characteristics
        if len(list_items) >= 4:
            evidence_score += 0.1  # Longer lists more likely need serial comma
        
        # Check for ambiguity potential
        if self._has_potential_ambiguity(list_items):
            evidence_score += 0.2
        
        return max(0.0, min(1.0, evidence_score))

    def _calculate_comma_splice_evidence(self, comma: 'Token', sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) that a comma splice exists.
        """
        # Apply zero false positive guards
        if self._apply_zero_false_positive_guards_punctuation(comma, context):
            return 0.0
        
        # Check if this is actually a comma splice
        if not self._is_potential_comma_splice(comma, sent):
            return 0.0
        
        # Base evidence for comma splice
        evidence_score = 0.7
        
        # Apply linguistic clues
        evidence_score = self._apply_common_linguistic_clues_punctuation(evidence_score, comma, sent)
        
        # Apply structural clues
        evidence_score = self._apply_common_structural_clues_punctuation(evidence_score, comma, context)
        
        # Apply semantic clues
        evidence_score = self._apply_common_semantic_clues_punctuation(evidence_score, comma, context)
        
        # Check for legitimate dependent clause structure
        if self._is_legitimate_dependent_clause(sent, comma):
            evidence_score -= 0.5
        
        return max(0.0, min(1.0, evidence_score))

    def _calculate_introductory_comma_evidence(self, main_clause_start: 'Token', sent: 'Span', text: str, context: Dict[str, Any], intro_length: int) -> float:
        """
        Calculate evidence (0.0-1.0) that a comma is needed after introductory clause.
        """
        # Apply zero false positive guards
        if self._apply_zero_false_positive_guards_punctuation(main_clause_start, context):
            return 0.0
        
        # Check if comma already exists in introductory clause
        has_comma_in_intro = any(
            token.text == ',' 
            for token in sent if sent.start <= token.i < main_clause_start.i
        )
        
        if has_comma_in_intro:
            return 0.0
        
        # Base evidence based on introductory element length
        if intro_length > 5:
            evidence_score = 0.8
        elif intro_length > 3:
            evidence_score = 0.6
        else:
            evidence_score = 0.4
        
        # Apply linguistic clues
        evidence_score = self._apply_common_linguistic_clues_punctuation(evidence_score, main_clause_start, sent)
        
        # Apply structural clues
        evidence_score = self._apply_common_structural_clues_punctuation(evidence_score, main_clause_start, context)
        
        # Apply semantic clues
        evidence_score = self._apply_common_semantic_clues_punctuation(evidence_score, main_clause_start, context)
        
        # Check for subordinating conjunctions at start
        subordinating_conjunctions = {'after', 'although', 'as', 'because', 'before', 'if', 'since', 'unless', 'until', 'when', 'while'}
        if sent[sent.start].lemma_.lower() in subordinating_conjunctions:
            evidence_score += 0.2
        
        return max(0.0, min(1.0, evidence_score))

    # === HELPER METHODS ===

    def _get_list_items(self, conjunction: 'Token') -> List['Token']:
        """
        Traverses the dependency tree from a conjunction to find all items in a potential list.
        """
        list_items = set()
        
        # The head of the conjunction is the item right before it
        head = conjunction.head
        list_items.add(head)

        # Add direct conjuncts of the head
        for child in head.children:
            if child.dep_ == 'conj':
                list_items.add(child)

        # Traverse up the tree to find the root of the list and its conjuncts
        current = head
        while current.dep_ == 'conj' and current.head != current:
            current = current.head
            list_items.add(current)
            for child in current.children:
                if child.dep_ == 'conj':
                    list_items.add(child)
        
        # Final check for conjuncts of the root item
        for child in current.children:
            if child.dep_ == 'conj':
                list_items.add(child)
                
        return sorted(list(list_items), key=lambda x: x.i)

    def _has_potential_ambiguity(self, list_items: List['Token']) -> bool:
        """
        Check if the list items could be ambiguous without a serial comma.
        """
        if len(list_items) < 3:
            return False
        
        # Check if any items are compound or complex
        for item in list_items:
            if any(child.dep_ == 'conj' for child in item.children):
                return True
        
        return False

    def _is_potential_comma_splice(self, comma: 'Token', sent: 'Span') -> bool:
        """
        Check if a comma potentially creates a comma splice.
        """
        if comma.i >= sent.end - 1:
            return False
        
        # Look for independent clause after comma
        second_clause_verb = None
        for t in sent[comma.i + 1:]:
            if t.pos_ == 'VERB' and t.dep_ != 'amod':
                second_clause_verb = t
                break
        
        if not second_clause_verb:
            return False
        
        # Check if this verb has its own subject
        has_subject = any(c.dep_ in ('nsubj', 'nsubjpass') for c in second_clause_verb.children)
        
        # Check if the first clause is also independent
        has_first_subject = any(c.dep_ in ('nsubj', 'nsubjpass') for c in comma.head.children)
        
        return has_subject and has_first_subject

    def _is_legitimate_dependent_clause(self, sent: 'Span', comma: 'Token') -> bool:
        """
        Check if the clause before the comma is a valid introductory dependent clause.
        """
        subordinating_conjunctions = {'after', 'although', 'as', 'because', 'before', 'if', 'since', 'unless', 'until', 'when', 'while'}
        if sent[sent.start].lemma_.lower() in subordinating_conjunctions:
            return True

        # Check for adverbial clause modifiers before the comma
        for token in sent[:comma.i]:
            if token.dep_ == 'advcl':
                return True
        return False


    # === SMART MESSAGING AND SUGGESTIONS ===

    def _get_contextual_serial_comma_message(self, evidence_score: float) -> str:
        """Generate context-aware error message for serial comma issues."""
        if evidence_score > 0.8:
            return "Missing serial (Oxford) comma before conjunction in a list."
        elif evidence_score > 0.6:
            return "Consider adding a serial comma before the conjunction for clarity."
        else:
            return "A serial comma before the conjunction may improve readability."

    def _generate_smart_serial_comma_suggestions(self, conjunction: 'Token', evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for serial comma issues."""
        suggestions = []
        
        if evidence_score > 0.7:
            suggestions.append(f"Add a comma before '{conjunction.text}' to follow standard style guidelines.")
            suggestions.append("Use the serial (Oxford) comma for consistency and clarity.")
        else:
            suggestions.append(f"Consider adding a comma before '{conjunction.text}' for clarity.")
            suggestions.append("The serial comma can help prevent ambiguity in complex lists.")
        
        # Context-specific guidance
        content_type = context.get('content_type', 'general')
        if content_type == 'academic':
            suggestions.append("Academic writing typically requires the serial comma.")
        elif content_type == 'technical':
            suggestions.append("Technical documentation benefits from consistent comma usage.")
        
        return suggestions[:3]

    def _get_contextual_comma_splice_message(self, evidence_score: float) -> str:
        """Generate context-aware error message for comma splice issues."""
        if evidence_score > 0.8:
            return "Comma splice detected: two independent clauses joined by only a comma."
        elif evidence_score > 0.6:
            return "Potential comma splice: consider revising the comma usage."
        else:
            return "Review comma usage between these clauses for grammatical correctness."

    def _generate_smart_comma_splice_suggestions(self, word_before_comma: str, evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for comma splice issues."""
        suggestions = []
        
        if evidence_score > 0.7:
            suggestions.append(f"Replace the comma after '{word_before_comma}' with a semicolon.")
            suggestions.append("Add a coordinating conjunction (like 'and' or 'but') after the comma.")
            suggestions.append("Split into two separate sentences.")
        else:
            suggestions.append("Consider using a semicolon if both clauses are independent.")
            suggestions.append("Add a conjunction to properly connect the clauses.")
        
        # Context-specific guidance
        if context.get('content_type') == 'technical':
            suggestions.append("Technical writing benefits from clear sentence boundaries.")
        
        return suggestions[:3]

    def _get_contextual_introductory_comma_message(self, evidence_score: float) -> str:
        """Generate context-aware error message for introductory comma issues."""
        if evidence_score > 0.8:
            return "Missing comma after an introductory clause or phrase."
        elif evidence_score > 0.6:
            return "Consider adding a comma after the introductory element."
        else:
            return "A comma after the introductory phrase may improve clarity."

    def _generate_smart_introductory_comma_suggestions(self, last_intro_token: 'Token', evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for introductory comma issues."""
        suggestions = []
        
        if evidence_score > 0.7:
            suggestions.append(f"Add a comma after '{last_intro_token.text}' to separate the introductory element.")
            suggestions.append("Use a comma to clearly separate introductory clauses from the main clause.")
        else:
            suggestions.append(f"Consider adding a comma after '{last_intro_token.text}' for clarity.")
            suggestions.append("A comma can help readers identify where the main clause begins.")
        
        # Context-specific guidance
        block_type = context.get('block_type', 'paragraph')
        if block_type in ['procedure', 'instruction']:
            suggestions.append("Clear comma usage helps readers follow procedural steps.")
        
        return suggestions[:3]
