"""
Verbs Rule (Corrected for False Positives)
Based on IBM Style Guide topic: "Verbs"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class VerbsRule(BaseLanguageRule):
    """
    Checks for verb-related style issues. This version has been corrected
    to eliminate false positives in the tense-checking logic by focusing on
    clear, actionable violations of the style guide.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'verbs'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for passive voice and specific, incorrect tense usage.
        """
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            
            # --- Rule 1: Passive Voice Check (Enhanced) ---
            # Enhanced logic to catch more passive voice constructions
            has_passive_aux = any(token.dep_ == 'auxpass' for token in doc)
            has_passive_subject = any(token.dep_ == 'nsubjpass' for token in doc)
            
            # Additional passive voice patterns
            has_be_verb_with_past_participle = False
            for token in doc:
                # Look for "be" verbs (is, was, are, were, be, been) followed by past participles
                if token.lemma_ in ['be'] and token.pos_ == 'AUX':
                    # Check if there's a past participle (VBN) that could indicate passive
                    for child in token.head.children:
                        if child.tag_ == 'VBN':  # Past participle
                            has_be_verb_with_past_participle = True
                            break

            # Passive voice if we have passive auxiliary OR the be+participle pattern
            is_passive = (has_passive_subject and has_passive_aux) or has_passive_aux or has_be_verb_with_past_participle

            if is_passive:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Sentence may be in the passive voice.",
                    suggestions=["Consider rewriting in the active voice to be more direct. For example, change 'The button was clicked by the user' to 'The user clicked the button'."],
                    severity='medium'
                ))

            # --- Rule 2: Tense Check (Corrected and More Conservative Logic) ---
            # This check now focuses on clear violations to avoid false positives.
            
            # Check for past tense on the main verb of the sentence.
            has_past_tense_violation = False
            root_verb = next((token for token in doc if token.dep_ == 'ROOT' and token.pos_ == 'VERB'), None)
            if root_verb and root_verb.morph.get("Tense") == ["Past"]:
                has_past_tense_violation = True

            # Check for future tense ONLY when used in a direct instruction to the user.
            # This is the clearest violation of the guide's preference for imperative commands.
            has_future_tense_violation = False
            for token in doc:
                # Find "will" used as an auxiliary verb.
                if token.lemma_ == 'will' and token.pos_ == 'AUX':
                    # Check if the subject of the verb it modifies is "you".
                    main_verb = token.head
                    subject = next((child for child in main_verb.children if child.dep_ == 'nsubj'), None)
                    if subject and subject.lemma_.lower() == 'you':
                        has_future_tense_violation = True
                        break
            
            if has_past_tense_violation or has_future_tense_violation:
                 errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Sentence may not be in the preferred present tense.",
                    suggestions=["Use present tense for instructions and descriptions. For commands, use the imperative mood (e.g., 'Click the button' instead of 'You will click the button')."],
                    severity='low'
                ))

            # --- Rule 3: Check for "login" used as verb ---
            # "Login" should be a noun; use "log in" as a verb
            for token in doc:
                if token.text.lower() == 'login' and token.pos_ == 'VERB':
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Use 'log in' (two words) as a verb, not 'login' (one word).",
                        suggestions=["Change 'Login to the server' to 'Log in to the server'. Use 'login' as a noun only (e.g., 'Enter your login credentials')."],
                        severity='medium'
                    ))

        return errors
