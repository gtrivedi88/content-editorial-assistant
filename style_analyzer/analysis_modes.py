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
        """Analyze using ONLY modular rules with SpaCy (highest accuracy)."""
        errors = []
        
        try:
            # Use ONLY modular rules analysis with context-aware rule selection
            if self.rules_registry:
                try:
                    # Use context-aware rule analysis to prevent false positives
                    rules_errors = self.rules_registry.analyze_with_context_aware_rules(
                        text, sentences, self.nlp, block_context
                    )
                    # Convert rules errors to our error format
                    for error in rules_errors:
                        converted_error = self.error_converter.convert_rules_error(error, block_context)
                        errors.append(converted_error)
                    logger.info(f"Context-aware modular rules analysis found {len(rules_errors)} issues")
                except Exception as e:
                    logger.error(f"Context-aware modular rules analysis failed: {e}")
            
        except Exception as e:
            logger.error(f"Modular rules analysis failed: {e}")
            # Ultimate fallback - try minimal safe mode
            return self.analyze_minimal_safe_mode(text, sentences, block_context)
        
        return errors
    
    def analyze_modular_rules_with_fallbacks(self, text: str, sentences: List[str], 
                                           block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Analyze using ONLY modular rules with conservative fallbacks."""
        errors = []
        
        try:
            # Use ONLY modular rules analysis with context-aware rule selection
            if self.rules_registry:
                try:
                    # Use context-aware rule analysis to prevent false positives
                    rules_errors = self.rules_registry.analyze_with_context_aware_rules(
                        text, sentences, self.nlp, block_context
                    )
                    # Convert rules errors to our error format
                    for error in rules_errors:
                        converted_error = self.error_converter.convert_rules_error(error, block_context)
                        errors.append(converted_error)
                    logger.info(f"Context-aware modular rules analysis found {len(rules_errors)} issues")
                except Exception as e:
                    logger.error(f"Context-aware modular rules analysis failed: {e}")
            
        except Exception as e:
            logger.error(f"Modular rules analysis failed: {e}")
            # Ultimate fallback - try minimal safe mode
            return self.analyze_minimal_safe_mode(text, sentences, block_context)
        
        return errors
    
    def analyze_spacy_legacy_only(self, text: str, sentences: List[str], 
                                 block_context: Optional[dict] = None) -> List[ErrorDict]:
        """DEPRECATED: Legacy analysis mode removed for simplification."""
        # This mode has been eliminated to reduce complexity
        # Fall back to modular rules analysis
        return self.analyze_modular_rules_with_fallbacks(text, sentences, block_context)
    
    def analyze_minimal_safe_mode(self, text: str, sentences: List[str], 
                                 block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Analyze using minimal safe methods (most conservative)."""
        errors = []
        
        try:
            # Use ONLY modular rules analysis in minimal safe mode
            if self.rules_registry:
                try:
                    rules_errors = self.rules_registry.analyze_with_context_aware_rules(
                        text, sentences, self.nlp, block_context
                    )
                    # Convert rules errors to our error format  
                    for error in rules_errors:
                        converted_error = self.error_converter.convert_rules_error(error, block_context)
                        errors.append(converted_error)
                    logger.info(f"Minimal safe modular rules analysis found {len(rules_errors)} issues")
                except Exception as e:
                    logger.error(f"Minimal safe modular rules analysis failed: {e}")
            
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
            
            # Apply special rules for admonitions (no need for additional generic analysis)
            if block_type == AsciiDocBlockType.ADMONITION:
                errors.extend(self._analyze_admonition_content(block, content, block_context))
            
            # Apply special rules for ordered lists - analyze each list item individually
            elif block_type == AsciiDocBlockType.ORDERED_LIST:
                errors.extend(self._analyze_ordered_list_content(block, content, analysis_mode, block_context))
            
            # Apply special analysis for unordered lists to extract clean text and analyze each item
            elif block_type == AsciiDocBlockType.UNORDERED_LIST:
                errors.extend(self._analyze_unordered_list_content(block, content, analysis_mode, block_context))
            
            # Apply special analysis for sidebar blocks to extract clean text  
            elif block_type == AsciiDocBlockType.SIDEBAR:
                errors.extend(self._analyze_sidebar_content(block, content, analysis_mode, block_context))
            
            # Apply special analysis for table blocks to analyze cell content
            elif block_type == AsciiDocBlockType.TABLE:
                errors.extend(self._analyze_table_content(block, content, analysis_mode, block_context))
            
            # Apply basic analysis for table rows (primarily for structural issues)
            elif block_type == AsciiDocBlockType.TABLE_ROW:
                errors.extend(self._analyze_table_row_content(block, content, analysis_mode, block_context))
            
            # Apply focused analysis for table cells (content-specific)
            elif block_type == AsciiDocBlockType.TABLE_CELL:
                errors.extend(self._analyze_table_cell_content(block, content, analysis_mode, block_context))
            
            # Apply general content analysis for other blocks (including headings)
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
        """Special analysis for AsciiDoc admonition blocks with enhanced context."""
        errors = []
        
        try:
            admonition_type = getattr(block, 'admonition_type', None)
            if admonition_type:
                # Enhance the context with the required 'kind' field that the notes rule expects
                enhanced_context = (block_context or {}).copy()
                enhanced_context['kind'] = admonition_type.value if hasattr(admonition_type, 'value') else str(admonition_type)
                
                # Apply ALL rules mapped to admonition blocks using the rules registry with enhanced context
                if self.rules_registry:
                    try:
                        # Use context-aware rule analysis to apply all mapped rules for admonition blocks
                        sentences = self.sentence_analyzer.split_sentences_safe(content) if self.sentence_analyzer else [content]
                        rules_errors = self.rules_registry.analyze_with_context_aware_rules(
                            content, sentences, self.nlp, enhanced_context
                        )
                        # Convert rules errors to our error format
                        for error in rules_errors:
                            converted_error = self.error_converter.convert_rules_error(error, enhanced_context)
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
            
            # SURGICAL FIX: Remove duplicates while preserving structure for analysis
            # Asciidoctor gem provides both blocks and items - deduplicate by content
            unique_children = []
            seen_content = set()
            for child in children:
                child_content = self._extract_clean_child_content(child)
                if child_content and child_content not in seen_content:
                    unique_children.append(child)
                    seen_content.add(child_content)
            
            all_list_items = []
            
            for i, child in enumerate(unique_children):
                # Create context for the individual list item
                child_context = child.get_context_info() if hasattr(child, 'get_context_info') else {}
                
                # Add step number to context for procedures rule
                if child_context:
                    child_context['step_number'] = i + 1
                    child_context['is_ordered_list_item'] = True
                
                child_content = self._extract_clean_child_content(child)
                
                if child_content:
                    all_list_items.append(child_content)
                    
                    # Analyze this individual list item
                    child_errors = self._analyze_generic_content(child_content, analysis_mode, child_context)
                    
                    # Store errors on the child and mark as analyzed to prevent duplicate processing
                    if not hasattr(child, '_analysis_errors'):
                        child._analysis_errors = []
                    child._analysis_errors.extend(child_errors)
                    
                    # CRITICAL FIX: Add child errors to the main errors list so they're returned
                    errors.extend(child_errors)
                    
                    # CRITICAL FIX: Mark child as already analyzed to prevent duplicate processing
                    # in the recursive _analyze_recursively method
                    child._already_analyzed = True
                    
                    # NEW FIX: Recursively analyze nested lists within this list item
                    self._analyze_nested_lists_in_item(child, analysis_mode)
            
            # ESSENTIAL: Analyze the whole list for structure issues (parallelism, etc.)
            # This ensures list structure errors appear in the "List Structure Issues" section
            if len(all_list_items) >= 2:
                # Create context for whole-list analysis
                whole_list_context = block_context.copy() if block_context else {}
                whole_list_context['block_type'] = 'ordered_list'
                whole_list_context['is_whole_list_analysis'] = True
                whole_list_context['parallelism_analysis_only'] = True  # Focus on list structure rules
                
                # Combine all list items for parallelism analysis
                combined_content = '\n'.join(all_list_items)
                
                # Run list structure analysis
                list_structure_errors = self._analyze_generic_content(combined_content, analysis_mode, whole_list_context)
                
                # CRITICAL: Add list structure errors to parent block for "List Structure Issues" section
                errors.extend(list_structure_errors)
        
        except Exception as e:
            logger.error(f"Error analyzing ordered list content: {e}")
            
        return errors
    
    def _analyze_unordered_list_content(self, block, content: str, analysis_mode: AnalysisMode, 
                                      block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Analyze unordered list content by analyzing each list item individually and the list as a whole."""
        errors = []
        
        try:
            # Get the children (list items) from the block
            children = getattr(block, 'children', [])
            
            # SURGICAL FIX: Remove duplicates while preserving structure for analysis
            # Asciidoctor gem provides both blocks and items - deduplicate by content
            unique_children = []
            seen_content = set()
            for child in children:
                child_content = self._extract_clean_child_content(child)
                if child_content and child_content not in seen_content:
                    unique_children.append(child)
                    seen_content.add(child_content)
            
            # Extract clean content from all unique children for whole-list analysis
            all_list_items = []
            
            for i, child in enumerate(unique_children):
                # Create context for the individual list item
                child_context = child.get_context_info() if hasattr(child, 'get_context_info') else {}
                
                # Add context for unordered list items
                if child_context:
                    child_context['item_number'] = i + 1
                    child_context['is_unordered_list_item'] = True
                
                # Extract clean content from the child
                child_content = self._extract_clean_child_content(child)
                
                # Only analyze if we have clean content
                if child_content:
                    # Store for whole-list analysis
                    all_list_items.append(child_content)
                    
                    # Analyze this individual list item
                    child_errors = self._analyze_generic_content(child_content, analysis_mode, child_context)
                    
                    # Store errors on the child and mark as analyzed to prevent duplicate processing
                    if not hasattr(child, '_analysis_errors'):
                        child._analysis_errors = []
                    child._analysis_errors.extend(child_errors)
                    
                    # CRITICAL FIX: Add child errors to the main errors list so they're returned
                    errors.extend(child_errors)
                    
                    # CRITICAL FIX: Mark child as already analyzed to prevent duplicate processing
                    # in the recursive _analyze_recursively method
                    child._already_analyzed = True
                    
                    # NEW FIX: Recursively analyze nested lists within this list item
                    self._analyze_nested_lists_in_item(child, analysis_mode)
            
            # ESSENTIAL: Analyze the whole list for structure issues (parallelism, etc.)
            # This ensures list structure errors appear in the "List Structure Issues" section
            if len(all_list_items) >= 2:
                # Create a combined context for the whole list
                whole_list_context = block_context.copy() if block_context else {}
                whole_list_context['block_type'] = 'unordered_list'
                whole_list_context['is_whole_list_analysis'] = True
                whole_list_context['parallelism_analysis_only'] = True  # Focus on list structure rules
                
                # Combine all list items into a single text for analysis
                combined_content = '\n'.join(all_list_items)
                
                # Analyze the combined list content (this will trigger the lists_rule for parallelism)
                whole_list_errors = self._analyze_generic_content(combined_content, analysis_mode, whole_list_context)
                
                # CRITICAL: Add list structure errors to parent block for "List Structure Issues" section
                errors.extend(whole_list_errors)
        
        except Exception as e:
            logger.error(f"Error analyzing unordered list content: {e}")
            
        return errors

    def _analyze_nested_lists_in_item(self, list_item, analysis_mode: AnalysisMode):
        """Recursively analyze nested lists within a list item."""
        try:
            # Check if this list item has children that are lists
            children = getattr(list_item, 'children', [])
            for child in children:
                if hasattr(child, 'block_type'):
                    block_type = getattr(child.block_type, 'value', str(child.block_type))
                    
                    # If child is a nested list, analyze it
                    if block_type in ['olist', 'ulist', 'ordered_list', 'unordered_list']:
                        # Get context for the nested list
                        child_context = child.get_context_info() if hasattr(child, 'get_context_info') else {}
                        child_content = child.get_text_content() if hasattr(child, 'get_text_content') else ''
                        
                        # Analyze the nested list using the appropriate method
                        if block_type in ['olist', 'ordered_list']:
                            nested_errors = self._analyze_ordered_list_content(child, child_content, analysis_mode, child_context)
                        else:
                            nested_errors = self._analyze_unordered_list_content(child, child_content, analysis_mode, child_context)
                        
                        # Store errors on the nested list
                        if not hasattr(child, '_analysis_errors'):
                            child._analysis_errors = []
                        child._analysis_errors.extend(nested_errors)
                        child._already_analyzed = True
                    
                    # Recursively check children of this child for even deeper nesting
                    self._analyze_nested_lists_in_item(child, analysis_mode)
                        
        except Exception as e:
            logger.error(f"Error analyzing nested lists in item: {e}")
    
    def _extract_clean_child_content(self, child) -> Optional[str]:
        """Extract clean content from a child block, handling various content types."""
        child_content = None
        
        # Method 1: Try get_text_content first (ensures HTML stripping)
        if hasattr(child, 'get_text_content'):
            try:
                text_content = child.get_text_content().strip()
                if text_content:
                    child_content = text_content
            except Exception:
                pass
        
        # Method 2: Fallback to direct content only if get_text_content failed
        if not child_content and hasattr(child, 'content') and isinstance(child.content, str):
            content_str = child.content.strip()
            if len(content_str) < 500 and not content_str.startswith('[#'):  # Not Ruby AST
                child_content = content_str
        
        # Method 3: Try get_text_content if available (this was the old Method 2)
        if not child_content and hasattr(child, 'get_text_content'):
            try:
                text_content = child.get_text_content().strip()
                if text_content and len(text_content) < 500:
                    child_content = text_content
            except:
                pass
        
        # Method 4: Try text attribute
        if not child_content and hasattr(child, 'text') and child.text:
            child_content = str(child.text).strip()
        
        return child_content
    
    def _analyze_sidebar_content(self, block, content: str, analysis_mode: AnalysisMode, 
                                block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Analyze sidebar content by extracting clean text from children and avoiding Ruby AST objects."""
        errors = []
        
        try:
            # Get the children from the sidebar block
            children = getattr(block, 'children', [])
            
            if children:
                # Extract clean text from children, skipping problematic content
                clean_parts = []
                for child in children:
                    if hasattr(child, 'block_type'):
                        # Handle unordered lists that contain Ruby AST objects
                        if child.block_type == AsciiDocBlockType.UNORDERED_LIST:
                            # Extract clean list items dynamically
                            list_items = self._extract_clean_list_items(child)
                            if list_items:
                                clean_parts.extend(list_items)
                            else:
                                # Fallback - indicate list is present but content unavailable
                                clean_parts.append("* [List content not available]")
                        else:
                            # Use clean content for other block types
                            child_content = getattr(child, 'content', '')
                            if isinstance(child_content, str) and len(child_content) < 1000:
                                clean_parts.append(child_content.strip())
                
                if clean_parts:
                    clean_content = '\n\n'.join(clean_parts)
                    # Analyze the clean content
                    errors.extend(self._analyze_generic_content(clean_content, analysis_mode, block_context))
        
        except Exception as e:
            logger.error(f"Error analyzing sidebar content: {e}")
            
        return errors
    
    def _extract_clean_list_items(self, list_block) -> List[str]:
        """Extract clean text from list items, handling Ruby AST objects."""
        list_items = []
        
        try:
            # Try to extract from children first
            children = getattr(list_block, 'children', [])
            if children:
                for child in children:
                    # Try multiple methods to get clean text
                    item_text = None
                    
                    # Method 1: Check for 'text' attribute (often clean)
                    if hasattr(child, 'text') and child.text:
                        item_text = str(child.text).strip()
                    
                    # Method 2: Try get_text_content first (ensures HTML stripping)
                    elif hasattr(child, 'get_text_content'):
                        try:
                            text_content = child.get_text_content().strip()
                            if text_content:
                                item_text = text_content
                        except Exception:
                            pass
                    
                    # Method 3: Fallback to direct content if get_text_content failed
                    if not item_text and hasattr(child, 'content') and isinstance(child.content, str):
                        content = child.content.strip()
                        if len(content) < 500 and not content.startswith('[#'):  # Not Ruby AST
                            item_text = content
                    
                    # Method 4: Try get_text_content if available (fallback)
                    elif not item_text and hasattr(child, 'get_text_content'):
                        try:
                            text_content = child.get_text_content().strip()
                            if text_content and len(text_content) < 500:
                                item_text = text_content
                        except:
                            pass
                    
                    if item_text:
                        list_items.append(f"* {item_text}")
            
            # If no clean items found, try to parse the raw content
            if not list_items:
                list_items = self._parse_list_from_ruby_ast(list_block)
                
        except Exception as e:
            logger.error(f"Error extracting list items: {e}")
            
        return list_items
    
    def _parse_list_from_ruby_ast(self, list_block) -> List[str]:
        """Parse list items from Ruby AST object as last resort."""
        list_items = []
        
        try:
            # Look for common patterns in the Ruby AST string
            content = getattr(list_block, 'content', '')
            if isinstance(content, str) and len(content) > 1000:
                # Try to find text patterns that look like list items
                import re
                
                # Look for quoted strings that might be list items
                quoted_patterns = re.findall(r'"([^"]{10,100})"', content)
                for pattern in quoted_patterns:
                    # Filter out Ruby code patterns
                    if not any(ruby_keyword in pattern.lower() for ruby_keyword in 
                              ['context', 'document', 'attributes', 'node_name', 'blocks']):
                        # Clean up the text
                        clean_text = pattern.strip()
                        if clean_text and len(clean_text.split()) >= 2:  # At least 2 words
                            list_items.append(f"* {clean_text}")
                
                # If still no items, try a different approach
                if not list_items:
                    # Look for lines that might be list content
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if (line and 
                            len(line.split()) >= 2 and 
                            not line.startswith('[') and 
                            not line.startswith('"@') and
                            not any(ruby_keyword in line.lower() for ruby_keyword in 
                                   ['context', 'document', 'attributes', 'node_name', 'blocks'])):
                            # This might be list content
                            list_items.append(f"* {line}")
                            if len(list_items) >= 5:  # Don't extract too many
                                break
                                
        except Exception as e:
            logger.error(f"Error parsing Ruby AST: {e}")
            
        return list_items
    
    def _analyze_table_content(self, block, content: str, analysis_mode: AnalysisMode, 
                              block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Special analysis for table blocks focusing on overall table structure and content."""
        errors = []
        
        try:
            # Apply general content analysis to the combined table content
            if content and content.strip():
                errors.extend(self._analyze_generic_content(content, analysis_mode, block_context))
            
            # Analyze each table row and cell individually for more specific issues
            children = getattr(block, 'children', [])
            for i, child in enumerate(children):
                child_context = child.get_context_info() if hasattr(child, 'get_context_info') else {}
                child_context['table_row_index'] = i
                
                # Get child content
                child_content = None
                # Try get_text_content first (ensures HTML stripping)  
                if hasattr(child, 'get_text_content'):
                    try:
                        child_content = child.get_text_content().strip()
                    except Exception:
                        pass
                # Fallback to direct content if get_text_content failed
                if not child_content and hasattr(child, 'content') and isinstance(child.content, str):
                    child_content = child.content.strip()
                elif not child_content and hasattr(child, 'get_text_content'):
                    try:
                        child_content = child.get_text_content().strip()
                    except:
                        pass
                
                # Analyze child content if available
                if child_content:
                    child_errors = self._analyze_generic_content(child_content, analysis_mode, child_context)
                    # Store errors on the child for detailed tracking
                    if not hasattr(child, '_analysis_errors'):
                        child._analysis_errors = []
                    child._analysis_errors.extend(child_errors)
                    # CRITICAL FIX: Also add to parent's error list so they appear in final results
                    errors.extend(child_errors)
                        
        except Exception as e:
            logger.error(f"Error analyzing table content: {e}")
            
        return errors
    
    def _analyze_table_row_content(self, block, content: str, analysis_mode: AnalysisMode, 
                                  block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Special analysis for table row blocks focusing on row-level consistency."""
        errors = []
        
        try:
            # Apply basic content analysis to the row content
            if content and content.strip():
                errors.extend(self._analyze_generic_content(content, analysis_mode, block_context))
                
        except Exception as e:
            logger.error(f"Error analyzing table row content: {e}")
            
        return errors
    
    def _analyze_table_cell_content(self, block, content: str, analysis_mode: AnalysisMode, 
                                   block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Special analysis for table cell blocks focusing on cell-specific content."""
        errors = []
        
        try:
            # Apply focused content analysis to the cell content
            if content and content.strip():
                # Add cell-specific context
                cell_context = block_context.copy() if block_context else {}
                cell_context['is_table_cell'] = True
                
                # Get cell position information from attributes
                if hasattr(block, 'attributes') and hasattr(block.attributes, 'named_attributes'):
                    cell_attrs = block.attributes.named_attributes
                    cell_context['cell_type'] = cell_attrs.get('cell_type', 'body')
                    cell_context['row_index'] = cell_attrs.get('row_index', 0)
                    cell_context['cell_index'] = cell_attrs.get('cell_index', 0)
                
                errors.extend(self._analyze_generic_content(content, analysis_mode, cell_context))
                
        except Exception as e:
            logger.error(f"Error analyzing table cell content: {e}")
            
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
            elif analysis_mode == AnalysisMode.MINIMAL_SAFE_MODE:
                errors = self.analyze_minimal_safe_mode(content, sentences, block_context)
            else:
                # Default fallback to modular rules
                errors = self.analyze_modular_rules_with_fallbacks(content, sentences, block_context)
                
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