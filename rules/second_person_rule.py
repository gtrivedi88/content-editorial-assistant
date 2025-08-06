"""
Second Person Rule (Consolidated)
Based on IBM Style Guide topic: "Verbs: Person"
Enhanced with pure SpaCy morphological analysis and linguistic anchors.
"""
from typing import List, Dict, Any, Set, Optional
from .language_and_grammar.base_language_rule import BaseLanguageRule

class SecondPersonRule(BaseLanguageRule):
    """
    Enforces the use of second person ("you") using pure spaCy morphological analysis.
    Uses linguistic anchors to detect first-person pronouns and third-person substitutes
    while avoiding false positives in compound nouns and proper names.
    """
    
    def __init__(self):
        super().__init__()
        # The exception framework is initialized in the BaseRule constructor.
        self._initialize_person_anchors()
    
    def _initialize_person_anchors(self):
        """Initialize morphological and semantic anchors for person analysis."""
        # This method remains the same
        self.first_person_patterns = {
            'pronoun_indicators': {
                'subject_pronouns': {'i', 'we'},
                'object_pronouns': {'me', 'us'},
                'possessive_pronouns': {'my', 'our', 'mine', 'ours'},
            }
        }
        self.third_person_substitutes = {
            'user', 'users', 'administrator', 'admin', 'developer', 
            'operator', 'customer', 'person', 'individual'
        }

    def _get_rule_type(self) -> str:
        return 'second_person'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for person violations using comprehensive
        morphological and syntactic analysis with linguistic anchors.
        """
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            sent_doc = self._analyze_sentence_structure(sentence, nlp)
            if not sent_doc:
                continue
            
            first_person_errors = self._analyze_first_person(sent_doc, sentence, i, text=text, context=context)
            errors.extend(first_person_errors)
            
            substitute_errors = self._analyze_third_person_substitutes(sent_doc, sentence, i, text=text, context=context)
            errors.extend(substitute_errors)

        return errors

    def _analyze_first_person(self, doc, sentence: str, sentence_index: int, text: str = None, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Detect first-person pronouns using morphological analysis."""
        errors = []
        first_person_pronouns = self.first_person_patterns['pronoun_indicators']['subject_pronouns'] | \
                                self.first_person_patterns['pronoun_indicators']['object_pronouns'] | \
                                self.first_person_patterns['pronoun_indicators']['possessive_pronouns']

        for token in doc:
            if token.lemma_.lower() in first_person_pronouns:
                # Add contextual checks here if needed (e.g., quotations, company names)
                if self._is_in_quotation(token) or self._is_part_of_proper_noun(token):
                    continue
                
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message=f"Avoid first-person pronoun '{token.text}'; use second person ('you') instead.",
                    suggestions=["Rewrite using 'you' to address the user directly."],
                    severity='high',
                    text=text,  # Enhanced: Pass full text for better confidence analysis
                    context=context,  # Enhanced: Pass context for domain-specific validation
                    span=(token.idx, token.idx + len(token.text)),
                    flagged_text=token.text
                ))
        return errors

    def _analyze_third_person_substitutes(self, doc, sentence: str, sentence_index: int, text: str = None, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Detect third-person substitutes using morphological analysis, now with exception checking.
        """
        errors = []
        
        # LINGUISTIC ANCHOR: Check if 'you' is already present in the sentence. If so, any third-person
        # substitute is likely defining the role of 'you' and should not be flagged.
        if any(token.lemma_.lower() == 'you' for token in doc):
            return errors # The sentence correctly uses second person.

        for token in doc:
            # Check if the token is a potential substitute (e.g., "user", "administrator")
            if token.lemma_.lower() in self.third_person_substitutes:
                
                # *** NEW EXCEPTION HANDLING LOGIC ***
                # Check for multi-word exceptions first (e.g., "user interface")
                if token.i + 1 < len(doc):
                    next_token = doc[token.i + 1]
                    two_word_phrase = f"{token.text} {next_token.text}"
                    if self._is_excepted(two_word_phrase):
                        # This is an allowed phrase like "user interface", so we skip the next token as well
                        # to avoid it being processed individually.
                        # We can simply continue here, as the loop will advance past the current token.
                        continue

                # Check for single-word exceptions (e.g., if you wanted to allow "admin" in some contexts)
                if self._is_excepted(token.text):
                    continue
                # *** END OF NEW LOGIC ***

                # If not an exception, proceed with the original logic
                if self._is_part_of_compound_noun(token):
                    continue
                
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message=f"Consider using 'you' instead of '{token.text}' for direct user engagement.",
                    suggestions=[f"Replace '{token.text}' with 'you' or rewrite the sentence to address the user directly."],
                    severity='medium',
                    text=text,  # Enhanced: Pass full text for better confidence analysis
                    context=context,  # Enhanced: Pass context for domain-specific validation
                    span=(token.idx, token.idx + len(token.text)),
                    flagged_text=token.text
                ))
        
        return errors

    # Helper methods (can be simplified or kept as is)
    def _is_part_of_compound_noun(self, token) -> bool:
        """Check if token is part of a compound noun using dependency analysis."""
        # This check is still useful for generic compounds not in the exception list.
        if token.dep_ == 'compound':
            return True
        # Check for constructions like "the user's guide"
        if token.head.dep_ == 'poss' and token.head.head.pos_ == 'NOUN':
            return True
        return False

    def _is_in_quotation(self, token) -> bool:
        # Simple check, can be made more robust if needed
        return token.sent.text.startswith('"') and token.sent.text.endswith('"')

    def _is_part_of_proper_noun(self, token) -> bool:
        # Check if the token or its head is a proper noun, indicating a name
        return token.pos_ == 'PROPN' or token.head.pos_ == 'PROPN'

    def _analyze_sentence_structure(self, sentence: str, nlp):
        """Helper to get a SpaCy doc from a sentence string."""
        if not sentence or not sentence.strip():
            return None
        try:
            return nlp(sentence)
        except Exception:
            return None
