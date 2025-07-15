"""
AsciiDoc Paragraph Parser

Handles parsing of AsciiDoc paragraph blocks:
- Regular text paragraphs
- Paragraph structure and content analysis
- Readability assessment
- Text formatting and style validation
"""

from typing import Dict, Any, List
import logging
import re

from ..base.element_parser import ElementParser, ElementParseResult

logger = logging.getLogger(__name__)

class ParagraphParser(ElementParser):
    """Parser for AsciiDoc paragraph blocks."""
    
    @property
    def element_type(self) -> str:
        return "paragraph"
    
    @property
    def supported_contexts(self) -> List[str]:
        return ["paragraph"]
    
    def can_parse(self, block_data: Dict[str, Any]) -> bool:
        """Check if this block is a paragraph."""
        context = block_data.get('context', '')
        return context == 'paragraph'
    
    def parse_element(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """
        Parse paragraph element data.
        
        Args:
            block_data: Raw block data from Ruby parser
            
        Returns:
            ElementParseResult with paragraph-specific data
        """
        try:
            content = block_data.get('content', '').strip()
            
            if not content:
                return ElementParseResult(
                    success=False,
                    errors=["Paragraph content is empty"]
                )
            
            # Analyze paragraph content
            content_analysis = self._analyze_paragraph_content(content)
            
            # Assess readability
            readability_analysis = self._assess_readability(content)
            
            # Check formatting
            formatting_analysis = self._analyze_formatting(content)
            
            element_data = {
                'content': content,
                'context': 'paragraph',
                'analysis': content_analysis,
                'readability': readability_analysis,
                'formatting': formatting_analysis,
                'raw_markup': content  # Paragraphs don't need special markup reconstruction
            }
            
            validation_errors = self.validate_element(element_data)
            
            return ElementParseResult(
                success=True,
                element_data=element_data,
                errors=validation_errors
            )
            
        except Exception as e:
            logger.error(f"Error parsing paragraph element: {e}")
            return ElementParseResult(
                success=False,
                errors=[f"Paragraph parsing failed: {str(e)}"]
            )
    
    def get_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get display information for UI rendering."""
        content = element_data.get('content', '')
        analysis = element_data.get('analysis', {})
        readability = element_data.get('readability', {})
        
        word_count = analysis.get('word_count', 0)
        readability_score = readability.get('score', 'unknown')
        
        # Create content preview
        preview = content[:100] + '...' if len(content) > 100 else content
        
        # Create summary
        summary = f"{word_count} words"
        if readability_score != 'unknown':
            summary += f", {readability_score} readability"
        
        return {
            'icon': 'fas fa-paragraph',
            'title': 'Paragraph',
            'content_preview': preview,
            'skip_analysis': False,  # Paragraphs should be analyzed
            'word_count': word_count,
            'readability_score': readability_score,
            'estimated_reading_time': analysis.get('reading_time', 0),
            'content_summary': summary
        }
    
    def validate_element(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate paragraph element data."""
        errors = []
        
        content = element_data.get('content', '')
        analysis = element_data.get('analysis', {})
        readability = element_data.get('readability', {})
        formatting = element_data.get('formatting', {})
        
        # Check paragraph length
        word_count = analysis.get('word_count', 0)
        sentence_count = analysis.get('sentence_count', 0)
        
        if word_count == 0:
            errors.append("Paragraph is empty")
        elif word_count < 5:
            errors.append("Paragraph is too short (< 5 words)")
        elif word_count > 200:
            errors.append("Paragraph is very long (> 200 words) - consider breaking up")
        
        # Check sentence structure
        if sentence_count == 0:
            errors.append("Paragraph contains no complete sentences")
        elif sentence_count == 1 and word_count > 50:
            errors.append("Single long sentence - consider breaking into multiple sentences")
        
        # Check readability
        readability_issues = readability.get('issues', [])
        if readability_issues:
            errors.extend(readability_issues)
        
        # Check formatting issues
        formatting_issues = formatting.get('issues', [])
        if formatting_issues:
            errors.extend(formatting_issues)
        
        # Check for specific writing issues
        if self._has_passive_voice_overuse(content):
            errors.append("Consider reducing passive voice usage")
        
        if self._has_repetitive_sentence_starts(content):
            errors.append("Many sentences start similarly - vary sentence beginnings")
        
        return errors
    
    def _analyze_paragraph_content(self, content: str) -> Dict[str, Any]:
        """Analyze paragraph content structure."""
        if not content:
            return {
                'word_count': 0,
                'sentence_count': 0,
                'character_count': 0,
                'reading_time': 0,
                'average_sentence_length': 0
            }
        
        # Count words
        words = content.split()
        word_count = len(words)
        
        # Count sentences (basic approach)
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)
        
        # Calculate metrics
        character_count = len(content)
        reading_time = max(1, word_count // 200)  # 200 words per minute
        avg_sentence_length = word_count / max(1, sentence_count)
        
        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'character_count': character_count,
            'reading_time': reading_time,
            'average_sentence_length': round(avg_sentence_length, 1)
        }
    
    def _assess_readability(self, content: str) -> Dict[str, Any]:
        """Assess paragraph readability."""
        if not content:
            return {
                'score': 'unknown',
                'complexity': 'unknown',
                'issues': []
            }
        
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        issues = []
        
        # Simple readability heuristics
        avg_word_length = sum(len(word.strip('.,!?;:')) for word in words) / max(1, len(words))
        avg_sentence_length = len(words) / max(1, len(sentences))
        
        # Assess complexity
        complexity = 'simple'
        if avg_word_length > 6 or avg_sentence_length > 25:
            complexity = 'moderate'
            if avg_word_length > 8 or avg_sentence_length > 35:
                complexity = 'complex'
        
        # Check for readability issues
        if avg_sentence_length > 30:
            issues.append("Sentences are too long - average > 30 words")
        
        if avg_word_length > 7:
            issues.append("Words are quite long - consider simpler alternatives")
        
        # Check for technical jargon (very basic)
        technical_indicators = ['implementation', 'configuration', 'optimization', 'initialization']
        jargon_count = sum(1 for word in words if any(tech in word.lower() for tech in technical_indicators))
        if jargon_count > len(words) * 0.1:  # More than 10% technical words
            issues.append("High technical jargon density - consider explanations")
        
        # Determine overall score
        if complexity == 'simple' and not issues:
            score = 'good'
        elif complexity == 'moderate' and len(issues) <= 1:
            score = 'fair'
        else:
            score = 'difficult'
        
        return {
            'score': score,
            'complexity': complexity,
            'average_word_length': round(avg_word_length, 1),
            'average_sentence_length': round(avg_sentence_length, 1),
            'issues': issues
        }
    
    def _analyze_formatting(self, content: str) -> Dict[str, Any]:
        """Analyze paragraph formatting and style."""
        issues = []
        
        # Check for formatting inconsistencies
        if content.startswith(' ') or content.endswith(' '):
            issues.append("Paragraph has extra whitespace at beginning or end")
        
        # Check for multiple spaces
        if '  ' in content:
            issues.append("Paragraph contains multiple consecutive spaces")
        
        # Check for proper sentence ending
        if not content.rstrip().endswith(('.', '!', '?')):
            issues.append("Paragraph doesn't end with proper punctuation")
        
        # Check for all caps sections
        words = content.split()
        caps_words = [word for word in words if word.isupper() and len(word) > 3]
        if len(caps_words) > len(words) * 0.1:  # More than 10% all caps
            issues.append("Excessive use of ALL CAPS - consider normal capitalization")
        
        # Check for proper paragraph structure
        if '\n' in content.strip():
            issues.append("Paragraph contains line breaks - may need restructuring")
        
        return {
            'issues': issues,
            'has_formatting_markup': any(marker in content for marker in ['*', '_', '`', '+', '^', '~']),
            'caps_word_ratio': len(caps_words) / max(1, len(words))
        }
    
    def _has_passive_voice_overuse(self, content: str) -> bool:
        """Check for overuse of passive voice (basic heuristic)."""
        # Simple passive voice indicators
        passive_indicators = [
            'was ', 'were ', 'been ', 'being ',
            'is ', 'are ', 'am '
        ]
        
        # Look for "to be" verbs followed by past participles
        passive_count = 0
        words = content.lower().split()
        
        for i, word in enumerate(words[:-1]):
            if any(indicator.strip() in word for indicator in passive_indicators):
                next_word = words[i + 1]
                # Very basic check for past participle (ends in -ed, -en, etc.)
                if (next_word.endswith('ed') or next_word.endswith('en') or 
                    next_word.endswith('ing')):
                    passive_count += 1
        
        total_sentences = len(re.split(r'[.!?]+', content))
        return passive_count > total_sentences * 0.3  # More than 30% passive
    
    def _has_repetitive_sentence_starts(self, content: str) -> bool:
        """Check for repetitive sentence beginnings."""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 3:
            return False
        
        # Get first word of each sentence
        first_words = []
        for sentence in sentences:
            words = sentence.split()
            if words:
                first_word = words[0].lower().strip('.,!?;:')
                first_words.append(first_word)
        
        # Check for repetition
        if len(first_words) < 3:
            return False
        
        # Count occurrences of most common first word
        from collections import Counter
        word_counts = Counter(first_words)
        most_common_count = word_counts.most_common(1)[0][1] if word_counts else 0
        
        # If most common first word appears in > 50% of sentences
        return most_common_count > len(first_words) * 0.5 