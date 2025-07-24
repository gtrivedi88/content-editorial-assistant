"""
Highlighting Rule
Based on IBM Style Guide topic: "Highlighting"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class HighlightingRule(BaseStructureRule):
    """
    Checks for missing highlighting on UI elements by performing a two-pass analysis:
    1. Linguistic Pass: Identifies text that *should* be highlighted.
    2. Structural Pass: Verifies if that text *is* highlighted in the document model.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'highlighting'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes a paragraph node for missing bold highlighting on UI elements.
        """
        errors = []
        if not nlp or not context:
            return errors

        paragraph_node = context.get('node')
        if not paragraph_node or paragraph_node.node_type != 'paragraph':
            return errors

        # --- Pass 1: Linguistic Analysis ---
        # Identify phrases that should be highlighted based on linguistic patterns.
        doc = nlp(text)
        candidates = self._find_highlighting_candidates(doc)

        # --- Pass 2: Structural Verification ---
        # Check the rich document model to see if candidates are already highlighted.
        for candidate in candidates:
            start_char, end_char = candidate['span']
            is_highlighted = self._is_span_highlighted(paragraph_node, start_char, end_char, style='bold')
            
            if not is_highlighted:
                errors.append(self._create_error(
                    sentence=candidate['sentence'],
                    sentence_index=candidate['sentence_index'],
                    message=f"UI element '{candidate['text']}' should be highlighted in bold.",
                    suggestions=[f"Apply bold formatting to '{candidate['text']}'."],
                    severity='medium',
                    span=candidate['span'],
                    flagged_text=candidate['text']
                ))

        return errors

    def _find_highlighting_candidates(self, doc: Doc) -> List[Dict[str, Any]]:
        """
        Uses linguistic anchors to find phrases that are likely UI elements.
        """
        candidates = []
        ui_element_lemmas = {"button", "menu", "window", "dialog", "tab", "field", "checkbox", "link", "icon", "list", "panel", "pane"}

        for token in doc:
            # Linguistic Anchor: A UI element is often a noun phrase ending with a UI keyword,
            # especially when it's the object of an imperative verb like "Click" or "Select".
            if token.lemma_ in ui_element_lemmas and token.pos_ == 'NOUN':
                # Check if the head is an imperative verb
                if token.head.pos_ == 'VERB' and token.head.tag_ == 'VB':
                    # Reconstruct the full noun phrase (e.g., "the Save button")
                    phrase_tokens = list(token.lefts) + [token]
                    start_token = min(phrase_tokens, key=lambda t: t.i)
                    end_token = max(phrase_tokens, key=lambda t: t.i)
                    
                    phrase_text = doc.text[start_token.idx : end_token.idx + len(end_token.text)]
                    
                    # Find which sentence this belongs to
                    sent_span = doc.char_span(start_token.idx, end_token.idx + len(end_token.text), alignment_mode="expand")
                    if sent_span:
                        sentence_text = sent_span.sent.text
                        # Correctly find the sentence index within the doc
                        sentence_index = -1
                        for idx, sent in enumerate(doc.sents):
                            if sent.start_char == sent_span.sent.start_char:
                                sentence_index = idx
                                break

                        if sentence_index != -1:
                            candidates.append({
                                'text': phrase_text,
                                'span': (start_token.idx, end_token.idx + len(end_token.text)),
                                'sentence': sentence_text,
                                'sentence_index': sentence_index
                            })
        return candidates

    def _is_span_highlighted(self, node, start_char: int, end_char: int, style: str) -> bool:
        """
        Traverses the rich document model to check if a character span has a specific style.
        """
        current_pos = 0
        for child in getattr(node, 'children', []):
            child_text = getattr(child, 'text_content', '')
            child_len = len(child_text)
            child_start = current_pos
            child_end = current_pos + child_len

            # Check if the target span is fully contained within this child node
            if start_char >= child_start and end_char <= child_end:
                # Check if the node's style matches the required style
                if style == 'bold' and getattr(child, 'node_type', 'text') in ['strong', 'b']:
                    return True
                if style == 'italic' and getattr(child, 'node_type', 'text') in ['emphasis', 'i']:
                    return True
                # If the span is within a single node that is NOT styled correctly, it's an error.
                return False

            current_pos += child_len
        
        # If the span crosses multiple nodes, this simple check returns False.
        # A more complex implementation could check if all nodes covering the span are highlighted.
        return False
