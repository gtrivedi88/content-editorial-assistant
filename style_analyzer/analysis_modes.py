"""
Analysis Mode Implementations
Different analysis strategies based on available capabilities.
"""

import logging
from typing import List, Dict, Any, Optional

try:
    from structural_parsing.asciidoc.types import AsciiDocBlockType
    from structural_parsing.markdown.types import MarkdownBlockType
    STRUCTURAL_PARSING_AVAILABLE = True
except ImportError:
    STRUCTURAL_PARSING_AVAILABLE = False

from .base_types import ErrorDict, AnalysisMode, create_error
from .error_converters import ErrorConverter

logger = logging.getLogger(__name__)


class AnalysisModeExecutor:
    """Executes different analysis modes based on available capabilities."""
    
    def __init__(self, readability_analyzer, sentence_analyzer, rules_registry=None, nlp=None):
        """Initialize with analyzer components."""
        self.readability_analyzer = readability_analyzer
        self.sentence_analyzer = sentence_analyzer
        self.rules_registry = rules_registry
        self.nlp = nlp
        self.error_converter = ErrorConverter()
    
    def analyze_spacy_with_modular_rules(self, text: str, sentences: List[str], 
                                       block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Analyze using SpaCy enhanced with modular rules (highest accuracy)."""
        errors = []
        
        try:
            # SpaCy-enhanced readability analysis
            readability_errors = self.readability_analyzer.analyze_readability_spacy_enhanced(
                text, self.nlp
            )
            errors.extend(readability_errors)
            
            # SpaCy-enhanced sentence analysis
            sentence_errors = self.sentence_analyzer.analyze_sentence_length_spacy(
                sentences, self.nlp
            )
            errors.extend(sentence_errors)
            
            # Integrate modular rules analysis with context-aware rule selection
            if self.rules_registry:
                try:
                    # Use context-aware rule analysis to prevent false positives
                    rules_errors = self.rules_registry.analyze_with_context_aware_rules(
                        text, sentences, self.nlp, block_context
                    )
                    # Convert rules errors to our error format
                    for error in rules_errors:
                        converted_error = self.error_converter.convert_rules_error(error)
                        errors.append(converted_error)
                    logger.info(f"Context-aware modular rules analysis found {len(rules_errors)} issues")
                except Exception as e:
                    logger.error(f"Context-aware modular rules analysis failed: {e}")
            
        except Exception as e:
            logger.error(f"SpaCy with modular rules analysis failed: {e}")
            # Fall back to next best mode
            return self.analyze_modular_rules_with_fallbacks(text, sentences, block_context)
        
        return errors
    
    def analyze_modular_rules_with_fallbacks(self, text: str, sentences: List[str], 
                                           block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Analyze using modular rules with conservative fallbacks."""
        errors = []
        
        try:
            # Conservative readability analysis
            readability_errors = self.readability_analyzer.analyze_readability_conservative(text)
            errors.extend(readability_errors)
            
            # Conservative sentence analysis
            sentence_errors = self.sentence_analyzer.analyze_sentence_length_conservative(sentences)
            errors.extend(sentence_errors)
            
            # Integrate modular rules analysis with context-aware rule selection
            if self.rules_registry:
                try:
                    # Use context-aware rule analysis to prevent false positives
                    rules_errors = self.rules_registry.analyze_with_context_aware_rules(
                        text, sentences, self.nlp, block_context
                    )
                    # Convert rules errors to our error format
                    for error in rules_errors:
                        converted_error = self.error_converter.convert_rules_error(error)
                        errors.append(converted_error)
                    logger.info(f"Context-aware modular rules analysis found {len(rules_errors)} issues")
                except Exception as e:
                    logger.error(f"Context-aware modular rules analysis failed: {e}")
            
        except Exception as e:
            logger.error(f"Modular rules with fallbacks analysis failed: {e}")
            # Fall back to next best mode
            return self.analyze_spacy_legacy_only(text, sentences, block_context)
        
        return errors
    
    def analyze_spacy_legacy_only(self, text: str, sentences: List[str], 
                                 block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Analyze using only SpaCy (legacy mode)."""
        errors = []
        
        try:
            # SpaCy-only readability analysis
            readability_errors = self.readability_analyzer.analyze_readability_spacy_enhanced(
                text, self.nlp
            )
            errors.extend(readability_errors)
            
            # SpaCy-only sentence analysis
            sentence_errors = self.sentence_analyzer.analyze_sentence_length_spacy(
                sentences, self.nlp
            )
            errors.extend(sentence_errors)
            
        except Exception as e:
            logger.error(f"SpaCy legacy analysis failed: {e}")
            # Fall back to minimal safe mode
            return self.analyze_minimal_safe_mode(text, sentences, block_context)
        
        return errors
    
    def analyze_minimal_safe_mode(self, text: str, sentences: List[str], 
                                 block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Analyze using minimal safe methods (most conservative)."""
        errors = []
        
        try:
            # Minimal safe readability analysis
            readability_errors = self.readability_analyzer.analyze_readability_minimal_safe(text)
            errors.extend(readability_errors)
            
            # Minimal safe sentence analysis
            sentence_errors = self.sentence_analyzer.analyze_sentence_length_minimal_safe(sentences)
            errors.extend(sentence_errors)
            
        except Exception as e:
            logger.error(f"Minimal safe analysis failed: {e}")
            # This is the safest mode, so we just return empty errors
            return []
        
        return errors
    
    def analyze_block_content(self, block, content: str, analysis_mode: AnalysisMode, 
                            block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Analyze content within a specific block context."""
        errors = []
        
        try:
            # Get block-specific context
            block_type = getattr(block, 'block_type', None)
            
            # Apply different analysis based on block type
            if self._is_asciidoc_block(block_type):
                errors.extend(self._analyze_asciidoc_block(block, content, analysis_mode, block_context))
            elif self._is_markdown_block(block_type):
                errors.extend(self._analyze_markdown_block(block, content, analysis_mode, block_context))
            else:
                # Generic content analysis
                errors.extend(self._analyze_generic_content(content, analysis_mode, block_context))
                
        except Exception as e:
            logger.error(f"Error analyzing block content: {e}")
            
        return errors
    
    def _is_asciidoc_block(self, block_type) -> bool:
        """Check if block is an AsciiDoc block type."""
        if not STRUCTURAL_PARSING_AVAILABLE:
            return False
        try:
            return isinstance(block_type, AsciiDocBlockType)
        except:
            return False
    
    def _is_markdown_block(self, block_type) -> bool:
        """Check if block is a Markdown block type."""
        if not STRUCTURAL_PARSING_AVAILABLE:
            return False
        try:
            return isinstance(block_type, MarkdownBlockType)
        except:
            return False
    
    def _analyze_asciidoc_block(self, block, content: str, analysis_mode: AnalysisMode, 
                              block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Apply AsciiDoc-specific analysis rules."""
        errors = []
        
        try:
            block_type = block.block_type
            
            # Skip code/literal blocks
            if block_type in [AsciiDocBlockType.LISTING, AsciiDocBlockType.LITERAL, AsciiDocBlockType.PASS]:
                return errors
            
            # Apply special rules for admonitions
            if block_type == AsciiDocBlockType.ADMONITION:
                errors.extend(self._analyze_admonition_content(block, content, block_context))
            
            # Apply special rules for ordered lists - analyze each list item individually
            elif block_type == AsciiDocBlockType.ORDERED_LIST:
                errors.extend(self._analyze_ordered_list_content(block, content, analysis_mode, block_context))
            
            # Apply general content analysis for other blocks
            elif block_type in [AsciiDocBlockType.PARAGRAPH, AsciiDocBlockType.HEADING, AsciiDocBlockType.QUOTE, AsciiDocBlockType.LIST_ITEM]:
                errors.extend(self._analyze_generic_content(content, analysis_mode, block_context))
                
        except Exception as e:
            logger.error(f"Error in AsciiDoc block analysis: {e}")
            
        return errors
    
    def _analyze_markdown_block(self, block, content: str, analysis_mode: AnalysisMode, 
                              block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Apply Markdown-specific analysis rules."""
        errors = []
        
        try:
            block_type = block.block_type
            
            # Skip code blocks
            if block_type in [MarkdownBlockType.CODE_BLOCK, MarkdownBlockType.INLINE_CODE]:
                return errors
            
            # Apply general content analysis for text blocks
            if block_type in [MarkdownBlockType.PARAGRAPH, MarkdownBlockType.HEADING, MarkdownBlockType.BLOCKQUOTE]:
                errors.extend(self._analyze_generic_content(content, analysis_mode, block_context))
                
        except Exception as e:
            logger.error(f"Error in Markdown block analysis: {e}")
            
        return errors
    
    def _analyze_admonition_content(self, block, content: str, block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Special analysis for AsciiDoc admonition blocks."""
        errors = []
        
        try:
            admonition_type = getattr(block, 'admonition_type', None)
            if admonition_type:
                # Apply admonition-specific rules using the rules registry
                if self.rules_registry:
                    try:
                        # Look for admonitions rule
                        admonition_rule = getattr(self.rules_registry, 'get_rule', lambda x: None)('admonitions')
                        if admonition_rule:
                            rule_errors = admonition_rule.analyze(content, [content], self.nlp, block_context)
                            for error in rule_errors:
                                converted_error = self.error_converter.convert_rules_error(error)
                                errors.append(converted_error)
                    except Exception as e:
                        logger.warning(f"Admonition rule analysis failed: {e}")
                        
        except Exception as e:
            logger.error(f"Error analyzing admonition content: {e}")
            
        return errors
    
    def _analyze_ordered_list_content(self, block, content: str, analysis_mode: AnalysisMode, 
                                    block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Analyze ordered list content by analyzing each list item individually and storing errors on children."""
        errors = []
        
        try:
            # Get the children (list items) from the block
            children = getattr(block, 'children', [])
            
            for i, child in enumerate(children):
                # Create context for the individual list item
                child_context = child.get_context_info()
                
                # Add step number to context for procedures rule
                if child_context:
                    child_context['step_number'] = i + 1
                    child_context['is_ordered_list_item'] = True
                
                child_content = child.content
                
                # Analyze this individual list item
                child_errors = self._analyze_generic_content(child_content, analysis_mode, child_context)
                
                # Store errors on the child instead of returning them to parent
                if not hasattr(child, '_analysis_errors'):
                    child._analysis_errors = []
                child._analysis_errors.extend(child_errors)
        
        except Exception as e:
            logger.error(f"Error analyzing ordered list content: {e}")
            
        # Return empty errors for parent block since errors are stored on children
        return errors
    
    def _analyze_generic_content(self, content: str, analysis_mode: AnalysisMode, 
                               block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Apply general style analysis to content."""
        errors = []
        
        try:
            sentences = self._split_sentences(content)
            
            if analysis_mode == AnalysisMode.SPACY_WITH_MODULAR_RULES:
                errors = self.analyze_spacy_with_modular_rules(content, sentences, block_context)
            elif analysis_mode == AnalysisMode.MODULAR_RULES_WITH_FALLBACKS:
                errors = self.analyze_modular_rules_with_fallbacks(content, sentences, block_context)
            elif analysis_mode == AnalysisMode.SPACY_LEGACY_ONLY:
                errors = self.analyze_spacy_legacy_only(content, sentences, block_context)
            elif analysis_mode == AnalysisMode.MINIMAL_SAFE_MODE:
                errors = self.analyze_minimal_safe_mode(content, sentences, block_context)
                
        except Exception as e:
            logger.error(f"Error in generic content analysis: {e}")
            
        return errors
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences safely."""
        try:
            if self.nlp:
                return self.sentence_analyzer.split_sentences_safe(text, self.nlp)
            else:
                return self.sentence_analyzer.split_sentences_safe(text)
        except Exception as e:
            logger.error(f"Error splitting sentences: {e}")
            # Ultimate fallback
            import re
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()] 