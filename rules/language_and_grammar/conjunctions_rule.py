"""
Conjunctions Rule - Clean Implementation
Based on IBM Style Guide topic: "Conjunctions"

Focuses exclusively on conjunction-specific issues:
- Coordinating conjunction usage (FANBOYS)
- Subordinating conjunction placement
- Parallel structure in coordinated elements

"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc, Token
except ImportError:
    Doc = None
    Token = None

class ConjunctionsRule(BaseLanguageRule):
    """
    Checks for conjunction-related issues:
    - Coordinating conjunction usage (FANBOYS)
    - Subordinating conjunction placement
    - Parallel structure in coordinated elements
    - Sentence-initial conjunction appropriateness

    """
    def _get_rule_type(self) -> str:
        return 'conjunctions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyze conjunction usage patterns.
        """
        errors = []
        if not nlp:
            return errors
        
        context = context or {}
        
        for i, sent_text in enumerate(sentences):
            if not sent_text.strip():
                continue
            
            try:
                doc = nlp(sent_text)

                # Check coordinating conjunctions
                coord_errors = self._analyze_coordinating_conjunctions(doc, sent_text, i, text, context)
                errors.extend(coord_errors)
                
                # Check subordinating conjunctions
                subord_errors = self._analyze_subordinating_conjunctions(doc, sent_text, i, text, context)
                errors.extend(subord_errors)
                
                # Check parallel structure
                parallel_errors = self._analyze_parallel_structure(doc, sent_text, i, text, context)
                errors.extend(parallel_errors)
                
            except Exception as e:
                # Graceful degradation
                continue
            
        return errors
    
    def _analyze_coordinating_conjunctions(self, doc: 'Doc', sent_text: str, sentence_index: int, full_text: str, context: dict) -> List[Dict[str, Any]]:
        """
        Analyze coordinating conjunction usage (FANBOYS).
        """
        errors = []
        coordinating_conjunctions = {'and', 'but', 'or', 'nor', 'for', 'yet', 'so'}
        
        for token in doc:
            if (token.lemma_.lower() in coordinating_conjunctions and 
                token.pos_ == 'CCONJ'):
                
                # Check sentence-initial coordinating conjunctions
                if token.i == 0:
                    evidence_score = self._calculate_sentence_initial_evidence(token, doc, context)
                    
                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent_text,
                            sentence_index=sentence_index,
                            message=self._get_sentence_initial_message(token.text, evidence_score, context),
                            suggestions=self._generate_sentence_initial_suggestions(token.text, context),
                            severity='low' if evidence_score < 0.5 else 'medium',
                            text=full_text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
        
        return errors
    
    def _analyze_subordinating_conjunctions(self, doc: 'Doc', sent_text: str, sentence_index: int, full_text: str, context: dict) -> List[Dict[str, Any]]:
        """
        Analyze subordinating conjunction placement.
        """
        errors = []
        subordinating_conjunctions = {
            'after', 'although', 'as', 'because', 'before', 'if', 'since', 
            'unless', 'until', 'when', 'while', 'whereas', 'wherever', 'though'
        }
        
        for token in doc:
            if (token.lemma_.lower() in subordinating_conjunctions and 
                token.i == 0):  # Sentence-initial subordinating conjunction
                
                # Check for missing comma after introductory clause
                evidence_score = self._calculate_subordinate_comma_evidence(token, doc, context)
                
                if evidence_score > 0.1:
                    main_clause_start = self._find_main_clause_start(token, doc)
                    
                    if main_clause_start and not self._has_comma_before_main_clause(token, main_clause_start, doc):
                        errors.append(self._create_error(
                            sentence=sent_text,
                            sentence_index=sentence_index,
                            message=f"Consider adding a comma after the introductory clause beginning with '{token.text}'.",
                            suggestions=[
                                "Add a comma after the introductory subordinate clause.",
                                "This helps readers identify where the main clause begins."
                            ],
                            severity='low',
                            text=full_text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(token.idx, main_clause_start.idx if main_clause_start else token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
        
        return errors
    
    def _analyze_parallel_structure(self, doc: 'Doc', sent_text: str, sentence_index: int, full_text: str, context: dict) -> List[Dict[str, Any]]:
        """
        Analyze parallel structure in coordinated elements.
        """
        errors = []
        
        for token in doc:
            if token.pos_ == 'CCONJ':
                parallel_error = self._check_parallel_structure(token, doc, sent_text, sentence_index, full_text, context)
                if parallel_error:
                    errors.append(parallel_error)
        
        return errors
    
    def _check_parallel_structure(self, conjunction: 'Token', doc: 'Doc', sent_text: str, sentence_index: int, full_text: str, context: dict):
        """
        Check parallel structure around coordinating conjunctions.
        """
        # Get coordinated elements
        coordinated_elements = []
        
        # Find the head and its conjuncts
        head = conjunction.head
        coordinated_elements.append(head)
        
        for child in head.children:
            if child.dep_ == 'conj':
                coordinated_elements.append(child)
        
        if len(coordinated_elements) >= 2:
            # Check if elements have similar grammatical structure
            pos_tags = [elem.pos_ for elem in coordinated_elements]
            
            if len(set(pos_tags)) > 1:  # Different POS tags indicate potential parallel structure issue
                evidence_score = 0.4
                
                # Adjust based on context
                content_type = context.get('content_type', 'general')
                if content_type in ['academic', 'formal']:
                    evidence_score += 0.2
                
                if evidence_score > 0.1:
                    element_texts = [elem.text for elem in coordinated_elements]
                    
                    return self._create_error(
                        sentence=sent_text,
                        sentence_index=sentence_index,
                        message=f"Consider using parallel structure - coordinated elements should have similar grammatical form.",
                        suggestions=[
                            "Ensure coordinated elements have the same grammatical structure.",
                            f"Make elements like '{', '.join(element_texts)}' match in form (e.g., all nouns, all verbs)."
                        ],
                        severity='low',
                        text=full_text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(coordinated_elements[0].idx, coordinated_elements[-1].idx + len(coordinated_elements[-1].text)),
                        flagged_text=' '.join(element_texts)
                    )
        
        return None
    
    def _calculate_sentence_initial_evidence(self, conjunction: 'Token', doc: 'Doc', context: dict) -> float:
        """
        Calculate evidence for sentence-initial conjunction being problematic.
        """
        evidence_score = 0.2  # Base evidence
        
        content_type = context.get('content_type', 'general')
        
        # More problematic in formal contexts
        if content_type in ['academic', 'formal', 'legal']:
            evidence_score += 0.4
        elif content_type in ['technical', 'documentation']:
            evidence_score += 0.2
        elif content_type in ['conversational', 'creative']:
            evidence_score -= 0.1
        
        # Some conjunctions are more acceptable at sentence start
        if conjunction.lemma_.lower() in ['but', 'and']:
            evidence_score -= 0.1
        
        return max(0.0, min(1.0, evidence_score))
    
    def _calculate_subordinate_comma_evidence(self, conjunction: 'Token', doc: 'Doc', context: dict) -> float:
        """
        Calculate evidence for missing comma after subordinate clause.
        """
        evidence_score = 0.3  # Base evidence
        
        # Find where the subordinate clause ends
        main_clause_start = self._find_main_clause_start(conjunction, doc)
        if main_clause_start:
            subordinate_clause_length = main_clause_start.i - conjunction.i
            
            # Longer subordinate clauses more likely need comma
            if subordinate_clause_length > 5:
                evidence_score += 0.4
            elif subordinate_clause_length > 3:
                evidence_score += 0.2
        
        # More important in formal writing
        content_type = context.get('content_type', 'general')
        if content_type in ['academic', 'formal']:
            evidence_score += 0.3
        elif content_type == 'technical':
            evidence_score += 0.1
        
        return max(0.0, min(1.0, evidence_score))
    
    def _find_main_clause_start(self, subordinating_conj: 'Token', doc: 'Doc'):
        """
        Find the start of the main clause after a subordinating conjunction.
        """
        # Look for the main verb (ROOT)
        for token in doc:
            if token.dep_ == 'ROOT' and token.i > subordinating_conj.i:
                # Find the subject of this main verb
                for child in token.children:
                    if child.dep_ in ('nsubj', 'nsubjpass'):
                        return child
                return token
        return None
    
    def _has_comma_before_main_clause(self, subordinating_conj: 'Token', main_clause_start: 'Token', doc: 'Doc') -> bool:
        """
        Check if there's a comma between subordinate clause and main clause.
        """
        for token in doc[subordinating_conj.i:main_clause_start.i]:
            if token.text == ',':
                return True
        return False
    
    def _get_sentence_initial_message(self, conjunction: str, evidence_score: float, context: dict) -> str:
        """
        Generate appropriate message for sentence-initial conjunctions.
        """
        content_type = context.get('content_type', 'general')
        
        if evidence_score > 0.6:
            if content_type in ['academic', 'formal']:
                return f"Avoid starting sentences with '{conjunction}' in formal writing."
            else:
                return f"Consider avoiding '{conjunction}' at the beginning of sentences."
        else:
            return f"Starting with '{conjunction}' may be informal - consider the context."
    
    def _generate_sentence_initial_suggestions(self, conjunction: str, context: dict) -> List[str]:
        """
        Generate suggestions for sentence-initial conjunctions.
        """
        suggestions = []
        
        content_type = context.get('content_type', 'general')
        
        if content_type in ['academic', 'formal']:
            suggestions.extend([
                f"Rewrite to avoid starting with '{conjunction}'.",
                "Use a transitional phrase like 'However,' or 'Additionally,' instead.",
                "Combine with the previous sentence if appropriate."
            ])
        else:
            suggestions.extend([
                f"Consider rewriting to avoid starting with '{conjunction}'.",
                "This may be acceptable depending on your writing style.",
                "Use transitional phrases for more formal writing."
            ])
        
        return suggestions[:3]
