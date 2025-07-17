"""
Files and Directories Rule
Based on IBM Style Guide topic: "Files and directories"
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule
import re

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
        # Regex to find common file extensions used without "file" or "directory"
        file_extension_pattern = re.compile(r'\b\.(pdf|txt|exe|zip|html)\b', re.IGNORECASE)

        for i, sentence in enumerate(sentences):
            matches = file_extension_pattern.finditer(sentence)
            for match in matches:
                # Linguistic Anchor: Check if the preceding word is "a" or "the",
                # suggesting it's being used as a noun.
                preceding_text = sentence[:match.start()].strip()
                if preceding_text.endswith((' a', ' an', ' the')):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Do not use a file extension like '{match.group()}' as a stand-alone noun.",
                        suggestions=[f"Specify the type of object, e.g., 'Convert the document to a {match.group()} file.'"],
                        severity='medium'
                    ))
        return errors
