"""
Structural Analyzer Module
Orchestrates document parsing, inter-block context enrichment, and rule application.
This is the central component for structure-aware analysis.
"""
import logging
from typing import List, Dict, Any, Optional

# Import the parser factory to handle different document formats
from structural_parsing.parser_factory import StructuralParserFactory
# Import the block processor to flatten the AST
from .block_processors import BlockProcessor
# Import the analysis executor to run the rules
from .analysis_modes import AnalysisModeExecutor
from .base_types import AnalysisResult, create_analysis_result, create_error

logger = logging.getLogger(__name__)

class StructuralAnalyzer:
    """
    Analyzes document content with full awareness of its structure,
    preventing structure-based false positives.
    """
    def __init__(self, readability_analyzer, sentence_analyzer, 
                 statistics_calculator, suggestion_generator, 
                 rules_registry, nlp):
        """Initializes the analyzer with all necessary components."""
        self.parser_factory = StructuralParserFactory()
        self.rules_registry = rules_registry
        self.nlp = nlp
        
        # We will use this to run the actual analysis on each block
        self.mode_executor = AnalysisModeExecutor(
            readability_analyzer,
            sentence_analyzer,
            rules_registry,
            nlp
        )

    def analyze_with_blocks(self, text: str, format_hint: str, analysis_mode: Any) -> Dict[str, Any]:
        """
        Parses a document, enriches blocks with structural context, runs analysis,
        and returns a structured result for the UI.
        """
        # 1. Parse the document to get a structured Abstract Syntax Tree (AST)
        parse_result = self.parser_factory.parse(text, format_hint=format_hint)

        if not parse_result.success or not parse_result.document:
            # Handle parsing failure
            return {
                'analysis': create_analysis_result(
                    errors=[create_error('system', 'Failed to parse document structure.', [])],
                    suggestions=[], statistics={}, technical_metrics={}, overall_score=0,
                    analysis_mode='error', spacy_available=bool(self.nlp), modular_rules_available=bool(self.rules_registry)
                ),
                'structural_blocks': [],
                'has_structure': False
            }

        # 2. Use the BlockProcessor to get a flattened, ordered list of blocks
        # This processor already runs a preliminary analysis pass.
        block_processor = BlockProcessor(self.mode_executor, analysis_mode)
        flat_blocks = block_processor.analyze_and_flatten_tree(parse_result.document)
        
        # 3. **CRUCIAL STEP: Add Inter-Block Context**
        # This is where we make each block aware of its neighbors.
        self._add_inter_block_context(flat_blocks)

        # 4. Final Analysis Pass (if needed, or just use errors from BlockProcessor)
        # The block_processor already attached errors. We can now collect them.
        all_errors = []
        for block in flat_blocks:
            # The context is now enriched, so rules would have run correctly.
            # We just need to collect the errors that were attached during the
            # block_processor's recursive analysis.
            if hasattr(block, '_analysis_errors'):
                all_errors.extend(block._analysis_errors)

        # 5. Prepare the final structured output for the UI
        # The `to_dict` method on the blocks will include the errors.
        structural_blocks_dict = [block.to_dict() for block in flat_blocks]

        return {
            'analysis': create_analysis_result(
                errors=all_errors,
                suggestions=[], statistics={}, technical_metrics={}, overall_score=50, # Placeholder score
                analysis_mode=analysis_mode.value, spacy_available=bool(self.nlp), modular_rules_available=bool(self.rules_registry)
            ),
            'structural_blocks': structural_blocks_dict,
            'has_structure': True
        }

    def _add_inter_block_context(self, flat_blocks: List[Any]):
        """
        Iterates through the flattened block list to add contextual information
        about neighboring blocks. This is the core of the structure-aware logic.
        """
        logger.info(f"Adding inter-block context to {len(flat_blocks)} blocks.")
        for i, current_block in enumerate(flat_blocks):
            # Ensure the block has a context dictionary to modify
            if not hasattr(current_block, 'context_info'):
                # get_context_info() should exist on your block types
                if hasattr(current_block, 'get_context_info'):
                    current_block.context_info = current_block.get_context_info()
                else:
                    current_block.context_info = {'block_type': getattr(current_block.block_type, 'value', 'unknown')}

            # --- Add context about the NEXT block ---
            next_block = flat_blocks[i + 1] if (i + 1) < len(flat_blocks) else None
            next_block_type = next_block.block_type.value if next_block and hasattr(next_block, 'block_type') else None
            current_block.context_info['next_block_type'] = next_block_type

            # --- Add context about the PREVIOUS block ---
            prev_block = flat_blocks[i - 1] if i > 0 else None
            prev_block_type = prev_block.block_type.value if prev_block and hasattr(prev_block, 'block_type') else None
            current_block.context_info['previous_block_type'] = prev_block_type

            # --- **SPECIFIC CONTEXT TO SOLVE THE COLON PROBLEM** ---
            is_list_intro = False
            # A paragraph ending in a colon is a list intro if the next block is a list.
            if current_block.context_info['block_type'] == 'paragraph' and \
               getattr(current_block, 'content', '').strip().endswith(':'):
                if next_block_type in ['ulist', 'olist', 'dlist']:
                    is_list_intro = True
            
            current_block.context_info['is_list_introduction'] = is_list_intro
            
            # This framework is extensible. You can add more structural context here.
            # For example: 'is_in_admonition_block', 'is_final_block', etc.
