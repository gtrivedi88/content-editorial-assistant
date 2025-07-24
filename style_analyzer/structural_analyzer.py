"""
Structural Analyzer - Enhanced for hierarchical processing and compatible output.
This module coordinates structural parsing and analysis, producing a flat
list of blocks suitable for the existing UI.
"""
import logging
from typing import Dict, List, Any
from .base_types import AnalysisMode
from .block_processors import BlockProcessor
from .analysis_modes import AnalysisModeExecutor
from structural_parsing.parser_factory import StructuralParserFactory

logger = logging.getLogger(__name__)

class StructuralAnalyzer:
    def __init__(self, readability_analyzer, sentence_analyzer, statistics_calculator,
                 suggestion_generator, rules_registry=None, nlp=None):
        self.parser_factory = StructuralParserFactory()
        self.mode_executor = AnalysisModeExecutor(
            readability_analyzer, sentence_analyzer, rules_registry, nlp
        )

    # CRITICAL FIX: Restored this method for compatibility with base_analyzer.py
    def analyze_with_structure(self, text: str, format_hint: str, analysis_mode: AnalysisMode) -> List[Dict[str, Any]]:
        """
        Parses, analyzes, and flattens the document structure into a simple
        list of error dictionaries, as expected by the legacy analyze() method.
        """
        result = self.analyze_with_blocks(text, format_hint, analysis_mode)
        all_errors = []
        for block in result.get('structural_blocks', []):
            all_errors.extend(block.get('errors', []))
            # Also collect errors from children for nested structures like lists/tables
            for child in block.get('children', []):
                all_errors.extend(child.get('errors', []))
        return all_errors

    def analyze_with_blocks(self, text: str, format_hint: str, analysis_mode: AnalysisMode) -> Dict[str, Any]:
        """
        Analyzes a document and returns a dictionary containing the analysis results
        and a flat list of structural blocks for the UI.
        """
        parse_result = self.parser_factory.parse(text, format_hint=format_hint)

        if not parse_result.success or not parse_result.document:
            return {'analysis': {'errors': [{'message': parse_result.error}]}, 'structural_blocks': [], 'has_structure': False}

        document = parse_result.document
        processor = BlockProcessor(self.mode_executor, analysis_mode)
        flat_blocks = processor.analyze_and_flatten_tree(document)

        return {
            'analysis': self._create_final_analysis_from_blocks(flat_blocks, analysis_mode),
            'structural_blocks': [block.to_dict() for block in flat_blocks],
            'has_structure': bool(flat_blocks)
        }

    def _create_final_analysis_from_blocks(self, blocks: List[Any], analysis_mode: AnalysisMode) -> Dict[str, Any]:
        """Creates the final, consolidated analysis result from the flattened blocks."""
        all_errors = []
        for block in blocks:
            all_errors.extend(getattr(block, '_analysis_errors', []))
        
        return {
            'errors': all_errors,
            'suggestions': [], 'statistics': {}, 'technical_writing_metrics': {},
            'overall_score': max(0, 100 - len(all_errors) * 5),
            'analysis_mode': analysis_mode.value,
            'spacy_available': True, 'modular_rules_available': True
        }