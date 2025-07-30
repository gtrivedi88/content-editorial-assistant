"""
Structural Analyzer Module
Orchestrates document parsing, inter-block context enrichment, and rule application.
This is the central component for structure-aware analysis.

**UPDATED** to fix a race condition by ensuring inter-block context is added
*before* the final analysis is run.
"""
import logging
from typing import List, Dict, Any, Optional

from structural_parsing.parser_factory import StructuralParserFactory
from .block_processors import BlockProcessor
from .analysis_modes import AnalysisModeExecutor
from .base_types import AnalysisMode, create_analysis_result, create_error

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
        self.statistics_calculator = statistics_calculator
        self.suggestion_generator = suggestion_generator
        
        self.mode_executor = AnalysisModeExecutor(
            readability_analyzer,
            sentence_analyzer,
            rules_registry,
            nlp
        )

    def analyze_with_blocks(self, text: str, format_hint: str, analysis_mode: AnalysisMode) -> Dict[str, Any]:
        """
        Parses a document, enriches blocks with structural context, runs analysis,
        and returns a structured result for the UI.
        """
        parse_result = self.parser_factory.parse(text, format_hint=format_hint)

        if not parse_result.success or not parse_result.document:
            return {
                'analysis': create_analysis_result(
                    errors=[create_error('system', 'Failed to parse document structure.', [])],
                    suggestions=[], statistics={}, technical_metrics={}, overall_score=0,
                    analysis_mode='error', spacy_available=bool(self.nlp), modular_rules_available=bool(self.rules_registry)
                ),
                'structural_blocks': [],
                'has_structure': False
            }

        # Use a temporary BlockProcessor to get a flattened list without running analysis yet.
        # This is a key change to fix the race condition.
        temp_processor = BlockProcessor(None, analysis_mode)
        flat_blocks = self._flatten_tree_only(temp_processor, parse_result.document)
        
        # **Step 2: Add Inter-Block Context** to the flattened list.
        self._add_inter_block_context(flat_blocks)

        # **Step 3: Now, run the final, context-aware analysis on each block.**
        all_errors = []
        for block in flat_blocks:
            context = getattr(block, 'context_info', block.get_context_info())
            
            if not block.should_skip_analysis():
                content = block.get_text_content()
                
                # DLIST blocks have special handling - bypass content check
                is_dlist = hasattr(block, 'block_type') and str(block.block_type).endswith('DLIST')
                if is_dlist or (isinstance(content, str) and content.strip()):
                    # CRITICAL FIX: Ensure table cell context includes proper position information
                    if hasattr(block, 'block_type') and str(block.block_type).endswith('TABLE_CELL'):
                        # Add table cell specific context information
                        if hasattr(block, 'attributes') and hasattr(block.attributes, 'named_attributes'):
                            cell_attrs = block.attributes.named_attributes
                            context['table_row_index'] = cell_attrs.get('row_index', 999)  # Default to high number for non-headers
                            context['cell_index'] = cell_attrs.get('cell_index', 0)
                            context['is_table_cell'] = True
                    
                    errors = self.mode_executor.analyze_block_content(block, content, analysis_mode, context)
                    block._analysis_errors = errors
                    all_errors.extend(errors)

        # **Step 4: Calculate statistics and technical metrics from the original text**
        # This is what was missing - we need to calculate actual statistics!
        sentences = self._split_sentences(text)
        paragraphs = self.statistics_calculator.split_paragraphs_safe(text)
        
        # Use comprehensive calculation methods to get all the detailed metrics
        statistics = self.statistics_calculator.calculate_comprehensive_statistics(
            text, sentences, paragraphs
        )
        
        technical_metrics = self.statistics_calculator.calculate_comprehensive_technical_metrics(
            text, sentences, all_errors
        )
        
        # Generate suggestions
        suggestions = self.suggestion_generator.generate_suggestions(
            all_errors, statistics, technical_metrics
        )
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(
            all_errors, technical_metrics, statistics
        )

        structural_blocks_dict = [block.to_dict() for block in flat_blocks]

        return {
            'analysis': create_analysis_result(
                errors=all_errors,
                suggestions=suggestions,
                statistics=statistics,
                technical_metrics=technical_metrics,
                overall_score=overall_score,
                analysis_mode=analysis_mode.value, 
                spacy_available=bool(self.nlp), 
                modular_rules_available=bool(self.rules_registry)
            ),
            'structural_blocks': structural_blocks_dict,
            'has_structure': True
        }

    def _flatten_tree_only(self, processor, root_node):
        """Uses the BlockProcessor's flattening logic without running analysis."""
        processor.flat_blocks = []
        processor._flatten_recursively(root_node)
        return processor.flat_blocks

    def _add_inter_block_context(self, flat_blocks: List[Any]):
        """
        Iterates through the flattened block list to add contextual information
        about neighboring blocks.
        """
        for i, current_block in enumerate(flat_blocks):
            context = current_block.get_context_info() if hasattr(current_block, 'get_context_info') else {}

            next_block = flat_blocks[i + 1] if (i + 1) < len(flat_blocks) else None
            next_block_type = next_block.block_type.value if next_block and hasattr(next_block, 'block_type') else None
            context['next_block_type'] = next_block_type

            is_list_intro = False
            if context.get('block_type') == 'paragraph' and getattr(current_block, 'content', '').strip().endswith(':'):
                if next_block_type in ['ulist', 'olist', 'dlist']:
                    is_list_intro = True
            
            context['is_list_introduction'] = is_list_intro
            
            current_block.context_info = context

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences safely."""
        try:
            if self.nlp:
                # Use the sentence analyzer from the mode executor
                from .sentence_analyzer import SentenceAnalyzer
                sentence_analyzer = SentenceAnalyzer()
                return sentence_analyzer.split_sentences_safe(text, self.nlp)
            else:
                # Ultimate fallback
                import re
                sentences = re.split(r'[.!?]+', text)
                return [s.strip() for s in sentences if s.strip()]
        except Exception as e:
            logger.error(f"Error splitting sentences: {e}")
            # Ultimate fallback
            import re
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]

    def _calculate_overall_score(self, errors: List[Dict[str, Any]], technical_metrics: Dict[str, Any], 
                               statistics: Dict[str, Any]) -> float:
        """Calculate overall style score safely."""
        try:
            # Base score
            base_score = 85.0
            
            # Deduct points for errors
            error_penalty = min(len(errors) * 5, 30)  # Max 30 points penalty
            
            # Adjust for readability
            readability_score = technical_metrics.get('readability_score', 60.0)
            if readability_score < 60:
                readability_penalty = (60 - readability_score) * 0.3
            else:
                readability_penalty = 0
            
            # Final score
            final_score = base_score - error_penalty - readability_penalty
            
            # Ensure score is between 0 and 100
            return max(0, min(100, final_score))
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 50.0  # Safe default
