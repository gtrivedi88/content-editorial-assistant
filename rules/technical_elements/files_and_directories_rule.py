"""
Files and Directories Rule
Based on IBM Style Guide topic: "Files and directories"
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class FilesAndDirectoriesRule(BaseTechnicalRule):
    """
    Checks for incorrect usage of file names and extensions as nouns.
    """
    def _get_rule_type(self) -> str:
        return 'technical_files_directories'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for file name and directory naming violations.
        """
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        file_extension_pattern = re.compile(r'\b\.(pdf|txt|exe|zip|html)\b', re.IGNORECASE)

        for i, sent in enumerate(doc.sents):
            for match in file_extension_pattern.finditer(sent.text):
                # Linguistic Anchor: Check if the preceding word is "a" or "the",
                # suggesting it's being used as a noun.
                preceding_text = sent.text[:match.start()].strip()
                if preceding_text.endswith((' a', ' an', ' the')):
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Do not use a file extension like '{match.group()}' as a stand-alone noun.",
                        suggestions=[f"Specify the type of object, e.g., 'Convert the document to a {match.group()} file.'"],
                        severity='medium',
                        text=text,  # Enhanced: Pass full text for better confidence analysis
                        context=context,  # Enhanced: Pass context for domain-specific validation
                        span=(sent.start_char + match.start(), sent.start_char + match.end()),
                        flagged_text=match.group(0)
                    ))
        return errors
