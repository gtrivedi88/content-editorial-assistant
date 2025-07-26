"""
Verbs Rule (Consolidated and Enhanced)
Based on IBM Style Guide topics: "Verbs: Tense", "Verbs: Voice", "Verbs: Person"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class VerbsRule(BaseLanguageRule):
    """
    Checks for a comprehensive set of verb-related style issues, including
    passive voice, incorrect tense, and specific word usage.
    """
    def _get_rule_type(self) -> str:
        return 'verbs'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        for i, sent_text in enumerate(sentences):
            if not sent_text.strip():
                continue
            
            doc = nlp(sent_text)
            
            # --- PRIORITY 1 FIX: Refined Passive Voice Check ---
            # This logic now uses precise spaCy dependency tags ('nsubjpass' and 'auxpass')
            # which are highly reliable indicators of passive voice. This will stop
            # the rule from incorrectly flagging active sentences.
            is_passive = False
            passive_token = None
            for token in doc:
                if token.dep_ in ('nsubjpass', 'auxpass'):
                    is_passive = True
                    # Find the main verb of the passive construction, which is the head of the auxiliary.
                    passive_token = token.head if token.dep_ == 'auxpass' else token
                    break
            
            if is_passive and passive_token:
                errors.append(self._create_error(
                    sentence=sent_text,
                    sentence_index=i,
                    message="Sentence may be in the passive voice.",
                    suggestions=["Rewrite in the active voice to be more direct. For example, change 'The button was clicked by the user' to 'The user clicked the button'."],
                    severity='medium',
                    flagged_text=passive_token.text
                ))

            # --- Rule 2: Future Tense Check ('will') ---
            for token in doc:
                if token.lemma_.lower() == "will" and token.tag_ == "MD":
                    head_verb = token.head
                    if head_verb.pos_ == "VERB":
                        suggestion = f"Use the present tense '{head_verb.lemma_}s' or the imperative mood '{head_verb.lemma_.capitalize()}'."
                        errors.append(self._create_error(
                            sentence=sent_text,
                            sentence_index=i,
                            message="Avoid future tense in procedural and descriptive text.",
                            suggestions=[suggestion],
                            severity='medium',
                            span=(token.idx, head_verb.idx + len(head_verb.text)),
                            flagged_text=f"{token.text} {head_verb.text}"
                        ))

            # --- Rule 3: Past Tense Check ---
            # Find the root token of the sentence
            root_verb = None
            for token in doc:
                if token.dep_ == "ROOT":
                    root_verb = token
                    break
            
            if root_verb and root_verb.pos_ == 'VERB' and 'Tense=Past' in str(root_verb.morph):
                errors.append(self._create_error(
                    sentence=sent_text,
                    sentence_index=i,
                    message="Sentence may not be in the preferred present tense.",
                    suggestions=["Use present tense for instructions and system descriptions."],
                    severity='low',
                    span=(root_verb.idx, root_verb.idx + len(root_verb.text)),
                    flagged_text=root_verb.text
                ))
        
        return errors
