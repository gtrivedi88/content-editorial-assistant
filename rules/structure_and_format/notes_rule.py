"""
Notes Rule (Consolidated and Enhanced)
Based on IBM Style Guide topic: "Notes"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class NotesRule(BaseStructureRule):
    """
    Checks for the correct formatting of notes, including labels and sentence structure.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'structure_format_notes'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        note_labels = {
            'note', 'exception', 'fast path', 'important', 'remember',
            'requirement', 'restriction', 'tip', 'attention', 'caution', 'danger', 'warning'
        }
        
        # This rule assumes each sentence passed in could be a note.
        for i, sentence in enumerate(sentences):
            # Linguistic Anchor: Check if the first word is a known label.
            match = re.match(r'(\w+(\s\w+)?)', sentence.strip())
            if not match:
                continue
            
            first_word_or_phrase = match.group(1)
            
            if first_word_or_phrase.lower().strip(':') in note_labels:
                # Rule 1: The label must be immediately followed by a colon.
                if not first_word_or_phrase.endswith(':'):
                    errors.append(self._create_error(
                        sentence=sentence, sentence_index=i,
                        message=f"The note label '{first_word_or_phrase}' should be followed by a colon.",
                        suggestions=[f"Add a colon after '{first_word_or_phrase}'."],
                        severity='high',
                        span=(sentence.find(first_word_or_phrase), sentence.find(first_word_or_phrase) + len(first_word_or_phrase)),
                        flagged_text=first_word_or_phrase
                    ))
                
                # Rule 2: The content of the note should be a complete sentence.
                note_content = sentence[len(first_word_or_phrase):].strip()
                if note_content:
                    doc = nlp(note_content)
                    if not self._is_complete_sentence(doc):
                        errors.append(self._create_error(
                            sentence=sentence, sentence_index=i,
                            message="The content of the note may not be a complete sentence.",
                            suggestions=["Ensure the text within the note forms a complete, standalone sentence for clarity."],
                            severity='low',
                            span=(sentence.find(note_content), sentence.find(note_content) + len(note_content)),
                            flagged_text=note_content
                        ))
        return errors

    def _is_complete_sentence(self, doc: Doc) -> bool:
        """
        Uses dependency parsing to check if the text forms a complete sentence.
        """
        if not doc or len(doc) < 2:
            return False
            
        has_root = any(token.dep_ == 'ROOT' for token in doc)
        has_subject = any(token.dep_ in ('nsubj', 'nsubjpass', 'csubj') for token in doc)
        is_imperative = doc[0].pos_ == 'VERB' and doc[0].dep_ == 'ROOT'

        return has_root and (has_subject or is_imperative)
