"""
Base Word Usage Rule
A base class that all specific word usage rules will inherit from.
"""

from typing import List, Dict, Any, Optional
import re

# Import spaCy Token type for proper type annotations
try:
    from spacy.tokens import Token
except ImportError:
    Token = None

# A generic base rule to be inherited from a central location
# in a real application. The # type: ignore comments prevent the
# static type checker from getting confused by the fallback class.
try:
    from ..base_rule import BaseRule  # type: ignore
except ImportError:
    class BaseRule:  # type: ignore
        def _get_rule_type(self) -> str:
            return 'base'
        def _create_error(self, **kwargs) -> Dict[str, Any]:
            return kwargs


class BaseWordUsageRule(BaseRule):
    """
    Abstract base class for all word usage rules.
    It defines the common interface for analyzing text for specific word violations.
    """

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes the text for specific word usage violations.
        This method must be implemented by all subclasses.
        """
        raise NotImplementedError("Subclasses must implement the analyze method.")

    def _find_multi_word_phrases_with_lemma(self, doc, phrase_list: List[str], case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """
        Find multi-word phrases in text using lemmatization to catch word variations.
        
        Args:
            doc: SpaCy doc object
            phrase_list: List of phrases to search for (e.g., ["click on", "log into"])
            case_sensitive: Whether matching should be case sensitive
            
        Returns:
            List of match dictionaries with keys: phrase, start_token, end_token, lemmatized_match
        """
        matches = []
        
        for phrase in phrase_list:
            phrase_tokens = phrase.strip().split()
            if not phrase_tokens:
                continue
                
            phrase_len = len(phrase_tokens)
            
            # Convert phrase to lemmas for comparison
            phrase_lemmas = [token.lower() if not case_sensitive else token for token in phrase_tokens]
            
            # Scan through document tokens
            for i in range(len(doc) - phrase_len + 1):
                # Get consecutive tokens matching phrase length
                token_sequence = doc[i:i + phrase_len]
                
                # Extract lemmas from token sequence
                token_lemmas = [
                    token.lemma_.lower() if not case_sensitive else token.lemma_ 
                    for token in token_sequence
                ]
                
                # Check if lemmas match the target phrase
                if token_lemmas == phrase_lemmas:
                    # Extract the actual text span
                    start_token = token_sequence[0]
                    end_token = token_sequence[-1]
                    
                    matches.append({
                        'phrase': phrase,
                        'start_token': start_token,
                        'end_token': end_token,
                        'lemmatized_match': ' '.join(token_lemmas),
                        'actual_text': doc[start_token.i:end_token.i + 1].text,
                        'start_char': start_token.idx,
                        'end_char': end_token.idx + len(end_token.text)
                    })
        
        return matches

    def _detect_phrasal_verbs_with_unnecessary_prepositions(self, doc) -> List[Dict[str, Any]]:
        """
        Automatically detect phrasal verbs with unnecessary prepositions using linguistic anchors.
        
        LINGUISTIC ANCHOR: Uses dependency parsing to find verb + preposition patterns
        where the preposition is semantically redundant for UI/technical instructions.
        
        This approach scales automatically without needing manual word lists.
        """
        violations = []
        
        # LINGUISTIC ANCHOR 1: Define semantic patterns for problematic phrasal verbs
        ui_interaction_verbs = {'click', 'select', 'choose', 'press', 'tap', 'touch', 'activate'}
        navigation_verbs = {'go', 'navigate', 'move', 'proceed', 'continue'}
        file_operation_verbs = {'save', 'download', 'upload', 'open', 'close', 'run'}
        
        # LINGUISTIC ANCHOR 2: Prepositions that are often redundant in technical writing
        redundant_prepositions = {
            'on': ['click', 'tap', 'press'],  # "click on" -> "click"
            'into': ['log', 'sign', 'enter'],  # "log into" -> "log in to" or "log in"
            'up': ['start', 'boot', 'fire'],   # "start up" -> "start" (when talking about systems)
            'to': ['connect', 'link', 'attach'],  # context-dependent
        }
        
        # LINGUISTIC ANCHOR 3: Scan for verb + preposition dependency patterns
        for token in doc:
            if token.pos_ == 'VERB' and token.lemma_.lower() in (ui_interaction_verbs | navigation_verbs | file_operation_verbs):
                # Look for immediate preposition children or siblings
                preposition_token = self._find_related_preposition(token, doc)
                
                if preposition_token:
                    prep_lemma = preposition_token.lemma_.lower()
                    verb_lemma = token.lemma_.lower()
                    
                    # LINGUISTIC ANCHOR 4: Check if this verb+preposition combination is problematic
                    if self._is_redundant_preposition(verb_lemma, prep_lemma, redundant_prepositions):
                        # Determine the appropriate suggestion based on linguistic context
                        suggestion = self._generate_preposition_suggestion(verb_lemma, prep_lemma, token, doc)
                        
                        violations.append({
                            'verb_token': token,
                            'preposition_token': preposition_token,
                            'phrase': f"{token.text} {preposition_token.text}",
                            'suggestion': suggestion,
                            'start_char': token.idx,
                            'end_char': preposition_token.idx + len(preposition_token.text),
                            'violation_type': 'redundant_preposition'
                        })
        
        return violations

    def _find_related_preposition(self, verb_token, doc) -> Optional[Any]:
        """
        Find preposition related to a verb using dependency parsing.
        
        LINGUISTIC ANCHOR: Uses SpaCy dependency relations to find prepositions
        that are syntactically connected to the verb.
        """
        # Look for prepositions that are immediate children of the verb
        for child in verb_token.children:
            if child.pos_ == 'ADP':  # Adposition (preposition)
                return child
        
        # Look for prepositions that immediately follow the verb
        if verb_token.i + 1 < len(doc):
            next_token = doc[verb_token.i + 1]
            if next_token.pos_ == 'ADP':
                return next_token
        
        return None

    def _is_redundant_preposition(self, verb_lemma: str, prep_lemma: str, redundant_map: Dict[str, List[str]]) -> bool:
        """
        Check if a verb+preposition combination represents a redundant preposition.
        
        LINGUISTIC ANCHOR: Uses semantic analysis to determine redundancy.
        """
        return prep_lemma in redundant_map and verb_lemma in redundant_map[prep_lemma]

    def _generate_preposition_suggestion(self, verb_lemma: str, prep_lemma: str, verb_token, doc) -> str:
        """
        Generate contextually appropriate suggestions for removing redundant prepositions.
        
        LINGUISTIC ANCHOR: Uses syntactic context to create intelligent suggestions.
        """
        # Analyze what follows the preposition for context-aware suggestions
        direct_object = self._find_direct_object_after_preposition(verb_token, doc)
        
        if verb_lemma == 'click' and prep_lemma == 'on':
            if direct_object:
                return f"Omit 'on'. Write 'Click {direct_object}', not 'Click on {direct_object}'."
            else:
                return "Omit 'on'. Write 'click the button', not 'click on the button'."
        
        elif verb_lemma in ['log', 'sign'] and prep_lemma == 'into':
            return f"Use 'log in to' (two words) or simply 'log in' instead of 'log into'."
        
        elif verb_lemma == 'start' and prep_lemma == 'up':
            return f"Use 'start' instead of 'start up' for system operations."
        
        else:
            return f"Consider removing '{prep_lemma}' after '{verb_lemma}' for concise technical writing."

    def _find_direct_object_after_preposition(self, verb_token, doc) -> Optional[str]:
        """
        Find the direct object that follows a preposition for context-aware suggestions.
        
        LINGUISTIC ANCHOR: Uses dependency parsing to find the object of the preposition.
        """
        for child in verb_token.children:
            if child.pos_ == 'ADP':  # Found the preposition
                # Look for the object of this preposition
                for prep_child in child.children:
                    if prep_child.dep_ == 'pobj':  # Object of preposition
                        return prep_child.text
        return None
