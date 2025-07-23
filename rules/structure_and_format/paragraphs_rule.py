"""
Paragraphs Rule
Based on IBM Style Guide topic: "Paragraphs"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

class ParagraphsRule(BaseStructureRule):
    """
    Checks for paragraph formatting issues, specifically indentation,
    by inspecting the structural properties of a parsed paragraph node.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'structure_format_paragraphs'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes a parsed paragraph node for indentation.
        """
        errors = []
        if not context:
            return errors

        # This rule operates on the structural node provided by the parser.
        paragraph_node = context.get('node')
        if not paragraph_node or paragraph_node.node_type != 'paragraph':
            return errors

        # The structural parser must provide indentation information.
        # We assume the parser adds an 'indent' attribute to the node.
        indentation = getattr(paragraph_node, 'indent', 0)

        # IBM Style Guide: "Omit paragraph indentation, setting the first line flush left."
        if indentation > 0:
            # The flagged text is the entire paragraph.
            # The span covers the beginning of the text to highlight the indentation.
            errors.append(self._create_error(
                sentence=sentences[0] if sentences else text,
                sentence_index=0,
                message="Paragraphs should not be indented.",
                suggestions=["Remove the indentation from the beginning of the paragraph."],
                severity='low',
                span=(0, indentation),
                flagged_text=text[:indentation]
            ))
            
        return errors
