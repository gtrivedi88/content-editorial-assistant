"""
Core Analyzer Module
Main StyleAnalyzer class that coordinates all analysis with zero false positives.
Implements mutually exclusive analysis paths to prevent conflicts.
Supports structural parsing for context-aware analysis.
"""

import logging
from typing import Dict, List, Any, Optional

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    import rules
    RULES_AVAILABLE = True
    from rules import get_registry
except ImportError:
    RULES_AVAILABLE = False
    get_registry = None

try:
    from structural_parsing.parser_factory import StructuralParserFactory
    from structural_parsing.asciidoc.types import AsciiDocDocument, AsciiDocBlockType
    from structural_parsing.markdown.types import MarkdownDocument, MarkdownBlockType
    STRUCTURAL_PARSING_AVAILABLE = True
except ImportError:
    STRUCTURAL_PARSING_AVAILABLE = False

from .base_types import (
    AnalysisResult, AnalysisMode, AnalysisMethod, ErrorDict,
    create_analysis_result, create_error
)
from .readability_analyzer import ReadabilityAnalyzer
from .sentence_analyzer import SentenceAnalyzer
from .statistics_calculator import StatisticsCalculator
from .suggestion_generator import SuggestionGenerator

logger = logging.getLogger(__name__)


class StyleAnalyzer:
    """Main style analyzer with zero false positives design and structural parsing support."""
    
    def __init__(self, rules: Optional[dict] = None):
        """Initialize the style analyzer with components."""
        self.rules = rules or {}
        
        # Initialize components
        self.readability_analyzer = ReadabilityAnalyzer(rules)
        self.sentence_analyzer = SentenceAnalyzer(rules)
        self.statistics_calculator = StatisticsCalculator(rules)
        self.suggestion_generator = SuggestionGenerator(rules)
        
        # Initialize structural parser factory if available
        self.parser_factory = None
        if STRUCTURAL_PARSING_AVAILABLE:
            try:
                self.parser_factory = StructuralParserFactory()
                logger.info("Structural parsing enabled - context-aware analysis available")
            except Exception as e:
                logger.warning(f"Failed to initialize structural parser: {e}")
                self.parser_factory = None
        
        # Initialize rules registry
        self.rules_registry = None
        if RULES_AVAILABLE and get_registry:
            try:
                self.rules_registry = get_registry()
                logger.info("Rules registry loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load rules registry: {e}")
                self.rules_registry = None
        
        # Initialize NLP model if available
        self.nlp = None
        if SPACY_AVAILABLE:
            self._initialize_spacy()
    
    def _initialize_spacy(self):
        """Initialize SpaCy model safely."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("SpaCy model loaded successfully")
        except OSError:
            logger.warning("SpaCy model not found, using fallback methods")
            self.nlp = None
    
    def analyze(self, text: str, format_hint: str = 'auto') -> AnalysisResult:
        """Perform comprehensive style analysis with structural awareness."""
        if not text or not text.strip():
            return create_analysis_result(
                errors=[],
                suggestions=[],
                statistics={},
                technical_metrics={},
                overall_score=0,
                analysis_mode=AnalysisMode.NONE,
                spacy_available=SPACY_AVAILABLE,
                modular_rules_available=RULES_AVAILABLE
            )
        
        try:
            # Determine analysis mode based on available capabilities
            analysis_mode = self._determine_analysis_mode()
            
            # Try structural parsing for context-aware analysis
            parsed_document = None
            if self.parser_factory:
                try:
                    # Ensure format_hint is a valid value and cast to Literal type
                    from typing import cast, Literal
                    if format_hint in ['asciidoc', 'markdown', 'auto']:
                        validated_hint = cast(Literal['asciidoc', 'markdown', 'auto'], format_hint)
                    else:
                        validated_hint = 'auto'
                    parse_result = self.parser_factory.parse(text, format_hint=validated_hint)
                    if parse_result.success:
                        parsed_document = parse_result.document
                        logger.info(f"Successfully parsed as {type(parsed_document).__name__}")
                except Exception as e:
                    logger.warning(f"Structural parsing failed, falling back to text analysis: {e}")
            
            # Prepare text for analysis
            if parsed_document:
                # Use structural parsing for context-aware analysis
                errors = self._analyze_with_structure(parsed_document, analysis_mode)
                sentences = self._extract_content_sentences(parsed_document)
                paragraphs = self._extract_content_paragraphs(parsed_document)
                
                # Check if structural parsing extracted meaningful content
                # If not, fall back to direct text analysis
                if not sentences and text.strip():
                    logger.info("Structural parsing produced empty sentences, falling back to direct text analysis")
                    sentences = self._split_sentences(text)
                    paragraphs = self.statistics_calculator.split_paragraphs_safe(text)
                    errors = self._analyze_without_structure(text, sentences, analysis_mode)
            else:
                # Fall back to traditional text analysis
                sentences = self._split_sentences(text)
                paragraphs = self.statistics_calculator.split_paragraphs_safe(text)
                errors = self._analyze_without_structure(text, sentences, analysis_mode)
            
            # Calculate statistics and metrics
            statistics = self.statistics_calculator.calculate_safe_statistics(
                text, sentences, paragraphs
            )
            
            technical_metrics = self.statistics_calculator.calculate_safe_technical_metrics(
                text, sentences, len(errors)
            )
            
            # Generate suggestions
            suggestions = self.suggestion_generator.generate_suggestions(
                errors, statistics, technical_metrics
            )
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(
                errors, technical_metrics, statistics
            )
            
            return create_analysis_result(
                errors=errors,
                suggestions=suggestions,
                statistics=statistics,
                technical_metrics=technical_metrics,
                overall_score=overall_score,
                analysis_mode=analysis_mode,
                spacy_available=SPACY_AVAILABLE,
                modular_rules_available=RULES_AVAILABLE
            )
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return create_analysis_result(
                errors=[create_error(
                    error_type='system',
                    message=f'Analysis failed: {str(e)}',
                    suggestions=['Check text input and system configuration']
                )],
                suggestions=[],
                statistics={},
                technical_metrics={},
                overall_score=0,
                analysis_mode=AnalysisMode.ERROR,
                spacy_available=SPACY_AVAILABLE,
                modular_rules_available=RULES_AVAILABLE
            )
    
    def _analyze_with_structure(self, parsed_document, analysis_mode: AnalysisMode) -> List[ErrorDict]:
        """Analyze document using structural information for context-aware analysis."""
        errors = []
        
        try:
            # Extract content blocks that should be analyzed
            content_blocks = self._get_analyzable_blocks(parsed_document)
            
            for block in content_blocks:
                block_content = block.get_text_content()
                if not block_content.strip():
                    continue
                
                # Apply context-specific analysis based on block type
                block_errors = self._analyze_block_content(block, block_content, analysis_mode)
                errors.extend(block_errors)
            
            logger.info(f"Structural analysis completed: {len(errors)} issues found across {len(content_blocks)} blocks")
            
        except Exception as e:
            logger.error(f"Structural analysis failed: {e}")
            # Fall back to text-based analysis
            full_text = self._extract_all_text(parsed_document)
            sentences = self._split_sentences(full_text)
            errors = self._analyze_without_structure(full_text, sentences, analysis_mode)
        
        return errors
    
    def _get_analyzable_blocks(self, parsed_document):
        """Get blocks that should be analyzed for style issues."""
        analyzable_blocks = []
        
        try:
            if hasattr(parsed_document, 'get_content_blocks'):
                # Use document's built-in method to get content blocks
                content_blocks = parsed_document.get_content_blocks()
                for block in content_blocks:
                    if hasattr(block, 'should_skip_analysis') and not block.should_skip_analysis():
                        analyzable_blocks.append(block)
                    elif not hasattr(block, 'should_skip_analysis'):
                        # If should_skip_analysis doesn't exist, include the block
                        analyzable_blocks.append(block)
            else:
                # Fall back to manual filtering
                all_blocks = getattr(parsed_document, 'blocks', [])
                for block in all_blocks:
                    if hasattr(block, 'is_content_block') and block.is_content_block():
                        if hasattr(block, 'should_skip_analysis') and not block.should_skip_analysis():
                            analyzable_blocks.append(block)
                        elif not hasattr(block, 'should_skip_analysis'):
                            analyzable_blocks.append(block)
                        
        except Exception as e:
            logger.error(f"Error getting analyzable blocks: {e}")
            
        return analyzable_blocks
    
    def _analyze_block_content(self, block, content: str, analysis_mode: AnalysisMode) -> List[ErrorDict]:
        """Analyze content within a specific block context."""
        errors = []
        
        try:
            # Get block-specific context
            block_type = getattr(block, 'block_type', None)
            block_context = getattr(block, 'get_context_info', lambda: {})()
            
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
    
    def _analyze_asciidoc_block(self, block, content: str, analysis_mode: AnalysisMode, block_context: Optional[dict] = None) -> List[ErrorDict]:
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
            
            # Apply general content analysis for other blocks
            if block_type in [AsciiDocBlockType.PARAGRAPH, AsciiDocBlockType.HEADING, AsciiDocBlockType.QUOTE]:
                errors.extend(self._analyze_generic_content(content, analysis_mode, block_context))
                
        except Exception as e:
            logger.error(f"Error in AsciiDoc block analysis: {e}")
            
        return errors
    
    def _analyze_markdown_block(self, block, content: str, analysis_mode: AnalysisMode, block_context: Optional[dict] = None) -> List[ErrorDict]:
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
                                converted_error = self._convert_rules_error(error)
                                errors.append(converted_error)
                    except Exception as e:
                        logger.warning(f"Admonition rule analysis failed: {e}")
                        
        except Exception as e:
            logger.error(f"Error analyzing admonition content: {e}")
            
        return errors
    
    def _analyze_generic_content(self, content: str, analysis_mode: AnalysisMode, block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Apply general style analysis to content."""
        errors = []
        
        try:
            sentences = self._split_sentences(content)
            
            if analysis_mode == AnalysisMode.SPACY_WITH_MODULAR_RULES:
                errors = self._analyze_spacy_with_modular_rules(content, sentences, block_context)
            elif analysis_mode == AnalysisMode.MODULAR_RULES_WITH_FALLBACKS:
                errors = self._analyze_modular_rules_with_fallbacks(content, sentences, block_context)
            elif analysis_mode == AnalysisMode.SPACY_LEGACY_ONLY:
                errors = self._analyze_spacy_legacy_only(content, sentences, block_context)
            elif analysis_mode == AnalysisMode.MINIMAL_SAFE_MODE:
                errors = self._analyze_minimal_safe_mode(content, sentences, block_context)
                
        except Exception as e:
            logger.error(f"Error in generic content analysis: {e}")
            
        return errors
    
    def _extract_content_sentences(self, parsed_document) -> List[str]:
        """Extract sentences from content blocks only."""
        sentences = []
        try:
            content_blocks = self._get_analyzable_blocks(parsed_document)
            for block in content_blocks:
                block_content = block.get_text_content()
                if block_content.strip():
                    block_sentences = self._split_sentences(block_content)
                    sentences.extend(block_sentences)
        except Exception as e:
            logger.error(f"Error extracting content sentences: {e}")
            # Fall back to full text
            full_text = self._extract_all_text(parsed_document)
            sentences = self._split_sentences(full_text)
        return sentences
    
    def _extract_content_paragraphs(self, parsed_document) -> List[str]:
        """Extract paragraphs from content blocks only."""
        paragraphs = []
        try:
            content_blocks = self._get_analyzable_blocks(parsed_document)
            for block in content_blocks:
                block_content = block.get_text_content()
                if block_content.strip():
                    paragraphs.append(block_content)
        except Exception as e:
            logger.error(f"Error extracting content paragraphs: {e}")
            # Fall back to full text
            full_text = self._extract_all_text(parsed_document)
            paragraphs = self.statistics_calculator.split_paragraphs_safe(full_text)
        return paragraphs
    
    def _extract_all_text(self, parsed_document) -> str:
        """Extract all text from the parsed document."""
        try:
            all_text = []
            blocks = getattr(parsed_document, 'blocks', [])
            for block in blocks:
                if hasattr(block, 'get_all_text'):
                    # Use the block's get_all_text method which includes children
                    text = block.get_all_text()
                    if text.strip():
                        all_text.append(text)
                elif hasattr(block, 'get_text_content'):
                    # Fallback to get_text_content
                    text = block.get_text_content()
                    if text.strip():
                        all_text.append(text)
            return '\n\n'.join(all_text)
        except Exception as e:
            logger.error(f"Error extracting all text: {e}")
            return ""
    
    def _analyze_without_structure(self, text: str, sentences: List[str], analysis_mode: AnalysisMode) -> List[ErrorDict]:
        """Fall back to traditional text-based analysis."""
        errors = []
        
        if analysis_mode == AnalysisMode.SPACY_WITH_MODULAR_RULES:
            errors = self._analyze_spacy_with_modular_rules(text, sentences, None)
        elif analysis_mode == AnalysisMode.MODULAR_RULES_WITH_FALLBACKS:
            errors = self._analyze_modular_rules_with_fallbacks(text, sentences, None)
        elif analysis_mode == AnalysisMode.SPACY_LEGACY_ONLY:
            errors = self._analyze_spacy_legacy_only(text, sentences, None)
        elif analysis_mode == AnalysisMode.MINIMAL_SAFE_MODE:
            errors = self._analyze_minimal_safe_mode(text, sentences, None)
        else:
            # Error mode
            errors = [create_error(
                error_type='system',
                message='Analysis system could not determine safe analysis mode.',
                suggestions=['Check system configuration and dependencies']
            )]
        
        return errors
    
    def _determine_analysis_mode(self) -> AnalysisMode:
        """Determine the safest analysis mode based on available capabilities."""
        if SPACY_AVAILABLE and RULES_AVAILABLE and self.nlp:
            return AnalysisMode.SPACY_WITH_MODULAR_RULES
        elif RULES_AVAILABLE:
            return AnalysisMode.MODULAR_RULES_WITH_FALLBACKS
        elif SPACY_AVAILABLE and self.nlp:
            return AnalysisMode.SPACY_LEGACY_ONLY
        else:
            return AnalysisMode.MINIMAL_SAFE_MODE
    
    def _analyze_spacy_with_modular_rules(self, text: str, sentences: List[str], block_context: Optional[dict] = None) -> List[ErrorDict]:
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
            
            # Integrate modular rules analysis
            if self.rules_registry:
                try:
                    rules_errors = self.rules_registry.analyze_with_all_rules(text, sentences, self.nlp, block_context)
                    # Convert rules errors to our error format
                    for error in rules_errors:
                        converted_error = self._convert_rules_error(error)
                        errors.append(converted_error)
                    logger.info(f"Modular rules analysis found {len(rules_errors)} issues")
                except Exception as e:
                    logger.error(f"Modular rules analysis failed: {e}")
            
        except Exception as e:
            logger.error(f"SpaCy with modular rules analysis failed: {e}")
            # Fall back to next best mode
            return self._analyze_modular_rules_with_fallbacks(text, sentences, block_context)
        
        return errors
    
    def _analyze_modular_rules_with_fallbacks(self, text: str, sentences: List[str], block_context: Optional[dict] = None) -> List[ErrorDict]:
        """Analyze using modular rules with conservative fallbacks."""
        errors = []
        
        try:
            # Conservative readability analysis
            readability_errors = self.readability_analyzer.analyze_readability_conservative(text)
            errors.extend(readability_errors)
            
            # Conservative sentence analysis
            sentence_errors = self.sentence_analyzer.analyze_sentence_length_conservative(sentences)
            errors.extend(sentence_errors)
            
            # Integrate modular rules analysis
            if self.rules_registry:
                try:
                    rules_errors = self.rules_registry.analyze_with_all_rules(text, sentences, self.nlp, block_context)
                    # Convert rules errors to our error format
                    for error in rules_errors:
                        converted_error = self._convert_rules_error(error)
                        errors.append(converted_error)
                    logger.info(f"Modular rules analysis found {len(rules_errors)} issues")
                except Exception as e:
                    logger.error(f"Modular rules analysis failed: {e}")
            
        except Exception as e:
            logger.error(f"Modular rules with fallbacks analysis failed: {e}")
            # Fall back to next best mode
            return self._analyze_spacy_legacy_only(text, sentences, block_context)
        
        return errors
    
    def _analyze_spacy_legacy_only(self, text: str, sentences: List[str], block_context: Optional[dict] = None) -> List[ErrorDict]:
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
            return self._analyze_minimal_safe_mode(text, sentences, block_context)
        
        return errors
    
    def _analyze_minimal_safe_mode(self, text: str, sentences: List[str], block_context: Optional[dict] = None) -> List[ErrorDict]:
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
    
    def _calculate_overall_score(self, errors: List[ErrorDict], technical_metrics: Dict[str, Any], statistics: Dict[str, Any]) -> float:
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
    
    def _convert_rules_error(self, rules_error: Dict[str, Any]) -> ErrorDict:
        """Convert rules system error to our standardized error format."""
        try:
            # Extract information from rules error
            error_type = rules_error.get('type', 'unknown')
            message = rules_error.get('message', 'Unknown error')
            suggestions = rules_error.get('suggestions', [])
            severity = rules_error.get('severity', 'low')
            sentence = rules_error.get('sentence', '')
            sentence_index = rules_error.get('sentence_index', -1)
            
            # Create standardized error
            return create_error(
                error_type=error_type,
                message=message,
                suggestions=suggestions,
                severity=severity,
                sentence=sentence,
                sentence_index=sentence_index,
                confidence=0.85,  # High confidence for rules-based detection
                analysis_method=AnalysisMethod.SPACY_ENHANCED
            )
        except Exception as e:
            logger.error(f"Error converting rules error: {e}")
            return create_error(
                error_type='system',
                message=f'Error processing rule: {str(e)}',
                suggestions=['Check rule implementation']
            )

    def analyze_with_blocks(self, text: str, format_hint: str = 'auto') -> Dict[str, Any]:
        """Perform block-aware analysis returning structured results with errors per block."""
        if not text or not text.strip():
            return {
                'analysis': create_analysis_result(
                    errors=[], suggestions=[], statistics={}, technical_metrics={},
                    overall_score=0, analysis_mode=AnalysisMode.NONE,
                    spacy_available=SPACY_AVAILABLE, modular_rules_available=RULES_AVAILABLE
                ),
                'structural_blocks': [],
                'has_structure': False
            }
        
        try:
            # Determine analysis mode
            analysis_mode = self._determine_analysis_mode()
            
            # Try structural parsing for block-aware analysis
            parsed_document = None
            structural_blocks = []
            
            if self.parser_factory:
                try:
                    from typing import cast, Literal
                    if format_hint in ['asciidoc', 'markdown', 'auto']:
                        validated_hint = cast(Literal['asciidoc', 'markdown', 'auto'], format_hint)
                    else:
                        validated_hint = 'auto'
                    parse_result = self.parser_factory.parse(text, format_hint=validated_hint)
                    if parse_result.success:
                        parsed_document = parse_result.document
                        structural_blocks = self._create_structural_blocks_with_analysis(parsed_document, analysis_mode)
                        logger.info(f"Successfully created {len(structural_blocks)} structural blocks with individual analysis")
                except Exception as e:
                    logger.warning(f"Structural parsing failed, falling back to text analysis: {e}")
            
            # Collect all errors from blocks for overall analysis
            all_errors = []
            for block in structural_blocks:
                all_errors.extend(block.get('errors', []))
            
            # If no structural blocks, fall back to traditional analysis
            if not structural_blocks:
                logger.info("No structural blocks available, falling back to traditional analysis")
                sentences = self._split_sentences(text)
                paragraphs = self.statistics_calculator.split_paragraphs_safe(text)
                all_errors = self._analyze_without_structure(text, sentences, analysis_mode)
            
            # Calculate overall statistics using full text
            sentences = self._split_sentences(text)
            paragraphs = self.statistics_calculator.split_paragraphs_safe(text)
            
            statistics = self.statistics_calculator.calculate_safe_statistics(
                text, sentences, paragraphs
            )
            
            technical_metrics = self.statistics_calculator.calculate_safe_technical_metrics(
                text, sentences, len(all_errors)
            )
            
            # Generate suggestions
            suggestions = self.suggestion_generator.generate_suggestions(
                all_errors, statistics, technical_metrics
            )
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(
                all_errors, technical_metrics, statistics
            )
            
            # Create analysis result
            analysis = create_analysis_result(
                errors=all_errors,
                suggestions=suggestions,
                statistics=statistics,
                technical_metrics=technical_metrics,
                overall_score=overall_score,
                analysis_mode=analysis_mode,
                spacy_available=SPACY_AVAILABLE,
                modular_rules_available=RULES_AVAILABLE
            )
            
            return {
                'analysis': analysis,
                'structural_blocks': structural_blocks,
                'has_structure': len(structural_blocks) > 0
            }
            
        except Exception as e:
            logger.error(f"Block-aware analysis failed: {e}")
            return {
                'analysis': create_analysis_result(
                    errors=[create_error(
                        error_type='system',
                        message=f'Analysis failed: {str(e)}',
                        suggestions=['Check text input and system configuration']
                    )],
                    suggestions=[],
                    statistics={},
                    technical_metrics={},
                    overall_score=0,
                    analysis_mode=AnalysisMode.ERROR,
                    spacy_available=SPACY_AVAILABLE,
                    modular_rules_available=RULES_AVAILABLE
                ),
                'structural_blocks': [],
                'has_structure': False
            }

    def _create_structural_blocks_with_analysis(self, parsed_document, analysis_mode: AnalysisMode) -> List[Dict[str, Any]]:
        """Create structural blocks with individual analysis results."""
        structural_blocks = []
        
        try:
            # Get all blocks from the document and flatten hierarchy
            all_blocks = getattr(parsed_document, 'blocks', [])
            flattened_blocks = self._flatten_document_blocks(all_blocks)
            
            block_id = 0
            for block in flattened_blocks:
                # Get content, handling different block types appropriately
                content = self._get_block_display_content(block)
                
                # Skip blocks that truly have no content
                if not content.strip():
                    continue
                
                # Determine block type (check for synthetic type first)
                block_type = getattr(block, '_synthetic_block_type', block.block_type.value)
                
                # Create basic block info
                block_info = {
                    'block_id': block_id,
                    'block_type': block_type,
                    'content': content,
                    'raw_content': getattr(block, 'raw_content', ''),
                    'should_skip_analysis': block.should_skip_analysis() if hasattr(block, 'should_skip_analysis') else False,
                    'context': block.get_context_info() if hasattr(block, 'get_context_info') else {},
                    'level': getattr(block, 'level', 0),
                    'admonition_type': getattr(getattr(block, 'admonition_type', None), 'value', None) if getattr(block, 'admonition_type', None) else None,
                    'children': self._convert_children_to_dict(getattr(block, 'children', [])),
                    'errors': []
                }
                
                # Analyze the block if it shouldn't be skipped
                if not block_info['should_skip_analysis']:
                    try:
                        block_errors = self._analyze_block_content(block, block_info['content'], analysis_mode)
                        block_info['errors'] = block_errors
                        logger.debug(f"Block {block_id} ({block.block_type.value}): {len(block_errors)} errors found")
                    except Exception as e:
                        logger.error(f"Error analyzing block {block_id}: {e}")
                
                structural_blocks.append(block_info)
                block_id += 1
                
        except Exception as e:
            logger.error(f"Error creating structural blocks with analysis: {e}")
            
        return structural_blocks

    def _convert_children_to_dict(self, children) -> List[Dict[str, Any]]:
        """Convert child blocks to dictionary format for serialization."""
        children_list = []
        
        try:
            for child in children:
                # Check for synthetic block type first
                child_block_type = getattr(child, '_synthetic_block_type', getattr(child.block_type, 'value', str(child.block_type)))
                
                child_dict = {
                    'block_type': child_block_type,
                    'content': self._get_block_display_content(child),
                    'raw_content': getattr(child, 'raw_content', ''),
                    'level': getattr(child, 'level', 0),
                    'children': self._convert_children_to_dict(getattr(child, 'children', [])),
                    'errors': []  # Children will be analyzed separately if needed
                }
                children_list.append(child_dict)
        except Exception as e:
            logger.error(f"Error converting children to dict: {e}")
            
        return children_list

    def _flatten_document_blocks(self, blocks, parent_section_level=0):
        """Recursively flatten document blocks to individual analyzable elements with intelligent grouping."""
        flattened = []
        
        for block in blocks:
            block_type = getattr(block, 'block_type', None)
            
            if not block_type:
                continue
                
            block_type_str = getattr(block_type, 'value', str(block_type))
            
            # Determine how to handle this block based on its characteristics
            if self._should_extract_children(block_type_str):
                # Extract and process children instead of the container
                if block_type_str == 'section':
                    # Create a heading block for the section title
                    if hasattr(block, 'title') and block.title:
                        heading_block = self._create_synthetic_heading_block(block)
                        if heading_block:
                            flattened.append(heading_block)
                    
                    # Recursively process children of the section
                    if hasattr(block, 'children') and block.children:
                        child_blocks = self._flatten_document_blocks(block.children, getattr(block, 'level', 0))
                        flattened.extend(child_blocks)
                        
                elif block_type_str == 'preamble':
                    # Process children but don't include preamble itself
                    if hasattr(block, 'children') and block.children:
                        child_blocks = self._flatten_document_blocks(block.children, parent_section_level)
                        flattened.extend(child_blocks)
                        
                elif block_type_str == 'document':
                    # Process document children
                    if hasattr(block, 'children') and block.children:
                        child_blocks = self._flatten_document_blocks(block.children, parent_section_level)
                        flattened.extend(child_blocks)
                        
            elif self._should_group_children(block_type_str):
                # Handle blocks that should group their children intelligently
                if block_type_str in ['ordered_list', 'unordered_list', 'dlist']:
                    # Use intelligent list processing for title detection
                    processed_list_blocks = self._process_list_block(block)
                    flattened.extend(processed_list_blocks)
                elif block_type_str in ['admonition', 'sidebar', 'quote', 'example']:
                    # For compound blocks, consolidate their content from children
                    consolidated_block = self._consolidate_compound_block(block)
                    flattened.append(consolidated_block)
                else:
                    # For other groupable blocks, add them as single units
                    flattened.append(block)
                    
            else:
                # For all other blocks, add them directly as individual elements
                # This includes: paragraph, sidebar, example, quote, verse, literal, 
                # listing, admonition, heading, attribute_entry, etc.
                flattened.append(block)
                
        return flattened
    
    def _should_extract_children(self, block_type_str: str) -> bool:
        """Determine if a block's children should be extracted rather than keeping the container."""
        # These are structural containers that should be broken down
        container_types = {'document', 'section', 'preamble'}
        return block_type_str in container_types
    
    def _should_group_children(self, block_type_str: str) -> bool:
        """Determine if a block should intelligently group its children."""
        # These are blocks that have children but should be treated as cohesive units
        # with intelligent grouping logic
        groupable_types = {'ordered_list', 'unordered_list', 'dlist', 'admonition', 'sidebar', 'quote', 'example'}
        return block_type_str in groupable_types
    
    def _consolidate_compound_block(self, block):
        """Consolidate compound block content from its children."""
        try:
            if not hasattr(block, 'children') or not block.children:
                return block
            
            # Extract content from all child blocks
            combined_content = []
            for child in block.children:
                if hasattr(child, 'content') and child.content:
                    combined_content.append(child.content.strip())
            
            # Update the block's content with consolidated content
            if combined_content:
                block.content = '\n\n'.join(combined_content)
                # Also update raw_content if it exists
                if hasattr(block, 'raw_content'):
                    block.raw_content = block.content
            
            return block
            
        except Exception as e:
            logger.error(f"Error consolidating compound block: {e}")
            return block
    
    def _process_list_block(self, list_block):
        """Process a list block with intelligent grouping based on content."""
        processed_blocks = []
        
        if not hasattr(list_block, 'children') or not list_block.children:
            return [list_block]
            
        list_items = list_block.children
        block_type_str = getattr(list_block.block_type, 'value', str(list_block.block_type))
        
        # Only check for list titles in ordered lists (procedures)
        # Unordered lists should not have title detection
        if (block_type_str == 'ordered_list' and 
            list_items and 
            self._is_list_title(list_items[0])):
            
            # First item becomes a "list title"
            title_item = list_items[0]
            
            # Mark the title item as a list title for proper display
            if hasattr(title_item, 'block_type'):
                # Create a synthetic block type for list title
                title_item._synthetic_block_type = 'list_title'
            
            processed_blocks.append(title_item)
            
            # If there are remaining items, group them into a single list block
            if len(list_items) > 1:
                remaining_items = list_items[1:]
                grouped_list = self._create_grouped_list_block(list_block, remaining_items)
                if grouped_list:
                    processed_blocks.append(grouped_list)
        else:
            # No title detection needed - treat as a regular list with all items grouped
            processed_blocks.append(list_block)
            
        return processed_blocks
    
    def _is_list_title(self, list_item):
        """Check if a list item looks like a title rather than content."""
        if not hasattr(list_item, 'content'):
            return False
            
        content = list_item.content.strip()
        
        if not content:
            return False
        
        # Check for title-like characteristics
        words = content.split()
        
        # Short descriptive phrases (1-6 words) that look like titles
        if len(words) <= 6:
            # Check if it doesn't start with typical action verbs (common in procedure steps)
            action_verbs = {
                'download', 'install', 'run', 'execute', 'click', 'select', 
                'choose', 'enter', 'type', 'navigate', 'open', 'close',
                'save', 'delete', 'create', 'modify', 'edit', 'update',
                'configure', 'set', 'enable', 'disable', 'start', 'stop',
                'follow', 'complete', 'finish', 'verify', 'check', 'test',
                'copy', 'paste', 'move', 'remove', 'add', 'insert', 'press'
            }
            
            first_word = words[0].lower()
            if first_word not in action_verbs:
                # Check for title-like patterns
                title_patterns = [
                    'procedure', 'installation', 'setup', 'configuration', 
                    'overview', 'summary', 'introduction', 'conclusion',
                    'requirements', 'prerequisites', 'steps', 'process',
                    'method', 'approach', 'guide', 'tutorial', 'manual',
                    'checklist', 'instructions', 'guidelines', 'preparation'
                ]
                
                content_lower = content.lower()
                for pattern in title_patterns:
                    if pattern in content_lower:
                        return True
                        
                # Also check if it looks like a title format (Title Case, etc.)
                if content.istitle() or (len(words) <= 3 and not content.endswith(('.', '!', '?'))):
                    return True
                    
        return False
    
    def _create_grouped_list_block(self, original_list, items):
        """Create a new list block that groups multiple list items."""
        try:
            if not STRUCTURAL_PARSING_AVAILABLE:
                return None
                
            from structural_parsing.asciidoc.types import AsciiDocBlock
            
            # Combine content from all items
            combined_content = []
            for item in items:
                if hasattr(item, 'content') and item.content:
                    combined_content.append(item.content.strip())
            
            # Create a new block that represents the grouped list
            grouped_block = AsciiDocBlock(
                block_type=original_list.block_type,
                content='\n\n'.join(combined_content),
                raw_content=original_list.raw_content,
                start_line=original_list.start_line,
                end_line=original_list.end_line,
                start_pos=original_list.start_pos,
                end_pos=original_list.end_pos,
                level=original_list.level,
                attributes=original_list.attributes,
                parent=original_list.parent,
                children=items,  # Keep the original items as children
                title=original_list.title,
                style=original_list.style,
                admonition_type=original_list.admonition_type,
                list_marker=original_list.list_marker,
                source_location=original_list.source_location
            )
            
            return grouped_block
            
        except Exception as e:
            logger.error(f"Error creating grouped list block: {e}")
            return original_list

    def _create_synthetic_heading_block(self, section_block):
        """Create a synthetic heading block from a section block."""
        try:
            if not STRUCTURAL_PARSING_AVAILABLE:
                return None
                
            from structural_parsing.asciidoc.types import AsciiDocBlock, AsciiDocBlockType, AsciiDocAttributes
            
            section_level = getattr(section_block, 'level', 1)
            section_title = getattr(section_block, 'title', '')
            
            if not section_title:
                return None
            
            # Create heading block with appropriate markup
            heading_markup = '=' * (section_level + 1) + ' ' + section_title
            
            heading_block = AsciiDocBlock(
                block_type=AsciiDocBlockType.HEADING,
                content=section_title,
                raw_content=heading_markup,
                start_line=getattr(section_block, 'start_line', 0),
                end_line=getattr(section_block, 'start_line', 0),
                start_pos=0,
                end_pos=len(heading_markup),
                level=section_level,
                attributes=AsciiDocAttributes(),
                parent=None,
                children=[],
                title=None,
                style=None,
                admonition_type=None,
                list_marker=None,
                source_location=getattr(section_block, 'source_location', '')
            )
            
            return heading_block
            
        except Exception as e:
            logger.error(f"Error creating synthetic heading block: {e}")
            return None

    def _get_block_display_content(self, block):
        """Get appropriate display content for different block types."""
        if not block:
            return ""
            
        block_type_str = getattr(block.block_type, 'value', str(block.block_type))
        
        # For attribute entries, show the raw content (e.g., ":author: Jane Doe")
        if block_type_str == 'attribute_entry':
            return getattr(block, 'raw_content', '') or getattr(block, 'content', '')
            
        # For other blocks, use the standard text content
        if hasattr(block, 'get_text_content'):
            return block.get_text_content().strip()
        elif hasattr(block, 'content'):
            return block.content.strip()
        else:
            return getattr(block, 'raw_content', '').strip()

    def _get_block_type_display_name(self, block_type_value: str, context: Dict[str, Any]) -> str:
        """Get a human-readable display name for a block type."""
        level = context.get('level', 0)
        admonition_type = context.get('admonition_type')
        
        display_names = {
            'heading': f'HEADING (Level {level})',
            'paragraph': 'PARAGRAPH',
            'ordered_list': 'ORDERED LIST',
            'unordered_list': 'UNORDERED LIST',
            'list_item': 'LIST ITEM',
            'list_title': 'LIST TITLE',
            'admonition': f'ADMONITION ({admonition_type.upper()})' if admonition_type else 'ADMONITION',
            'sidebar': 'SIDEBAR',
            'example': 'EXAMPLE',
            'quote': 'QUOTE',
            'verse': 'VERSE',
            'listing': 'CODE BLOCK',
            'literal': 'LITERAL BLOCK',
            'attribute_entry': 'ATTRIBUTE',
            'comment': 'COMMENT',
            'table': 'TABLE',
            'image': 'IMAGE',
            'audio': 'AUDIO',
            'video': 'VIDEO'
        }
        
        return display_names.get(block_type_value, block_type_value.upper().replace('_', ' ')) 