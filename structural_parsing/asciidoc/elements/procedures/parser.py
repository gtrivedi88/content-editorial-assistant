"""
AsciiDoc Procedure Parser

Handles parsing of AsciiDoc procedures and step-by-step instructions:
- Numbered procedure steps (ordered lists)
- Procedure validation and structure analysis
- Step content and formatting
- Procedure completion tracking
"""

from typing import Dict, Any, List
import logging
import re

from ..base.element_parser import ElementParser, ElementParseResult

logger = logging.getLogger(__name__)

class ProcedureParser(ElementParser):
    """Parser for AsciiDoc procedure steps and ordered lists."""
    
    # Keywords that suggest this is a procedure rather than a regular list
    PROCEDURE_KEYWORDS = {
        'step', 'procedure', 'process', 'install', 'configure', 'setup',
        'create', 'build', 'deploy', 'run', 'execute', 'perform',
        'follow', 'complete', 'finish', 'start', 'begin', 'do'
    }
    
    # Action verbs that indicate procedure steps
    ACTION_VERBS = {
        'open', 'click', 'select', 'choose', 'enter', 'type', 'press',
        'navigate', 'go', 'visit', 'access', 'login', 'download',
        'upload', 'save', 'copy', 'paste', 'cut', 'delete', 'remove',
        'add', 'insert', 'modify', 'edit', 'update', 'change',
        'verify', 'check', 'confirm', 'validate', 'test', 'review'
    }
    
    @property
    def element_type(self) -> str:
        return "procedure"
    
    @property
    def supported_contexts(self) -> List[str]:
        return ["olist", "list_item"]  # ordered lists and their items
    
    def can_parse(self, block_data: Dict[str, Any]) -> bool:
        """Check if this block represents a procedure."""
        context = block_data.get('context', '')
        
        if context not in ['olist', 'list_item']:
            return False
        
        # For ordered lists, check if it looks like a procedure
        if context == 'olist':
            return self._is_procedure_list(block_data)
        
        # For list items, check if parent is a procedure
        # This will be handled by the coordinator for nested structures
        return True
    
    def parse_element(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """
        Parse procedure element data.
        
        Args:
            block_data: Raw block data from Ruby parser
            
        Returns:
            ElementParseResult with procedure-specific data
        """
        try:
            context = block_data.get('context', 'olist')
            
            if context == 'olist':
                return self._parse_procedure_list(block_data)
            elif context == 'list_item':
                return self._parse_procedure_step(block_data)
            else:
                return ElementParseResult(
                    success=False,
                    errors=[f"Unknown procedure context: {context}"]
                )
                
        except Exception as e:
            logger.error(f"Error parsing procedure element: {e}")
            return ElementParseResult(
                success=False,
                errors=[f"Procedure parsing failed: {str(e)}"]
            )
    
    def _parse_procedure_list(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """Parse main procedure list."""
        children = block_data.get('children', [])
        attributes = block_data.get('attributes', {})
        title = block_data.get('title', '')
        
        # Analyze procedure structure
        procedure_analysis = self._analyze_procedure_structure(children, title)
        
        # Extract procedure properties
        procedure_props = self._extract_procedure_properties(block_data)
        
        element_data = {
            'context': 'procedure_list',
            'title': title,
            'step_count': len(children),
            'analysis': procedure_analysis,
            'properties': procedure_props,
            'estimated_duration': self._estimate_duration(children),
            'complexity': self._assess_complexity(children),
            'has_title': bool(title),
            'raw_markup': self._reconstruct_procedure_markup(children, title)
        }
        
        validation_errors = self.validate_element(element_data)
        
        return ElementParseResult(
            success=True,
            element_data=element_data,
            errors=validation_errors
        )
    
    def _parse_procedure_step(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """Parse individual procedure step."""
        content = block_data.get('content', '').strip()
        text = block_data.get('text', '').strip()
        marker = block_data.get('marker', '')
        
        # Use text if content is empty (common in list items)
        step_content = content or text
        
        # Analyze step content
        step_analysis = self._analyze_step_content(step_content)
        
        element_data = {
            'context': 'procedure_step',
            'content': step_content,
            'marker': marker,
            'analysis': step_analysis,
            'word_count': len(step_content.split()) if step_content else 0,
            'estimated_time': self._estimate_step_time(step_content),
            'difficulty': self._assess_step_difficulty(step_content)
        }
        
        validation_errors = self._validate_procedure_step(element_data)
        
        return ElementParseResult(
            success=True,
            element_data=element_data,
            errors=validation_errors
        )
    
    def get_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get display information for UI rendering."""
        context = element_data.get('context', 'procedure_list')
        
        if context == 'procedure_list':
            return self._get_procedure_list_display_info(element_data)
        elif context == 'procedure_step':
            return self._get_procedure_step_display_info(element_data)
        else:
            return {'icon': 'fas fa-list-ol', 'title': 'Procedure'}
    
    def _get_procedure_list_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get display info for procedure list."""
        step_count = element_data.get('step_count', 0)
        title = element_data.get('title', '')
        complexity = element_data.get('complexity', 'unknown')
        duration = element_data.get('estimated_duration', 0)
        
        display_title = f"Procedure ({step_count} steps)"
        if title:
            display_title = f"Procedure: {title}"
        
        duration_text = f"~{duration} min" if duration > 0 else "Quick"
        
        return {
            'icon': 'fas fa-tasks',
            'title': display_title,
            'content_preview': f"{step_count} steps, {duration_text}, {complexity} complexity",
            'skip_analysis': False,  # Procedures should be analyzed
            'step_count': step_count,
            'complexity': complexity,
            'estimated_duration': duration,
            'has_custom_title': bool(title)
        }
    
    def _get_procedure_step_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get display info for procedure step."""
        content = element_data.get('content', '')
        difficulty = element_data.get('difficulty', 'normal')
        estimated_time = element_data.get('estimated_time', 0)
        
        return {
            'icon': 'fas fa-chevron-right',
            'title': 'Procedure Step',
            'content_preview': content[:50] + '...' if len(content) > 50 else content,
            'skip_analysis': True,  # Individual steps analyzed as part of procedure
            'difficulty': difficulty,
            'estimated_time': estimated_time,
            'has_action': self._has_action_verb(content)
        }
    
    def validate_element(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate procedure element data."""
        context = element_data.get('context', 'procedure_list')
        
        if context == 'procedure_list':
            return self._validate_procedure_list(element_data)
        elif context == 'procedure_step':
            return self._validate_procedure_step(element_data)
        else:
            return []
    
    def _validate_procedure_list(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate procedure list."""
        errors = []
        step_count = element_data.get('step_count', 0)
        analysis = element_data.get('analysis', {})
        
        # Check step count
        if step_count == 0:
            errors.append("Procedure has no steps")
        elif step_count == 1:
            errors.append("Single-step procedure may be better as a paragraph")
        elif step_count > 20:
            errors.append("Procedure has many steps (>20) - consider breaking into sections")
        
        # Check step quality
        incomplete_steps = analysis.get('incomplete_steps', 0)
        if incomplete_steps > 0:
            errors.append(f"{incomplete_steps} steps lack clear action verbs")
        
        vague_steps = analysis.get('vague_steps', 0)
        if vague_steps > step_count * 0.3:  # More than 30% vague
            errors.append("Many steps are vague - add more specific instructions")
        
        return errors
    
    def _validate_procedure_step(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate individual procedure step."""
        errors = []
        content = element_data.get('content', '')
        word_count = element_data.get('word_count', 0)
        analysis = element_data.get('analysis', {})
        
        # Check step content
        if not content.strip():
            errors.append("Procedure step is empty")
        elif word_count > 50:
            errors.append("Procedure step is very long - consider breaking down")
        elif word_count < 2:
            errors.append("Procedure step is too brief")
        
        # Check for action verbs
        if not analysis.get('has_action_verb', False):
            errors.append("Step should start with an action verb (click, open, enter, etc.)")
        
        # Check for vague language
        if analysis.get('is_vague', False):
            errors.append("Step contains vague language - be more specific")
        
        return errors
    
    def _is_procedure_list(self, block_data: Dict[str, Any]) -> bool:
        """Check if an ordered list represents a procedure."""
        title = block_data.get('title', '').lower()
        children = block_data.get('children', [])
        
        # Check title for procedure keywords
        if any(keyword in title for keyword in self.PROCEDURE_KEYWORDS):
            return True
        
        # Check if steps contain action verbs
        action_step_count = 0
        for child in children[:5]:  # Check first 5 steps
            content = child.get('content', '') or child.get('text', '')
            if self._has_action_verb(content):
                action_step_count += 1
        
        # If most steps have action verbs, likely a procedure
        return action_step_count >= len(children[:5]) * 0.6
    
    def _analyze_procedure_structure(self, children: List[Dict[str, Any]], title: str) -> Dict[str, Any]:
        """Analyze the structure and quality of a procedure."""
        if not children:
            return {
                'total_steps': 0,
                'action_steps': 0,
                'vague_steps': 0,
                'incomplete_steps': 0,
                'has_clear_goal': False
            }
        
        action_steps = 0
        vague_steps = 0
        incomplete_steps = 0
        
        for child in children:
            content = child.get('content', '') or child.get('text', '')
            analysis = self._analyze_step_content(content)
            
            if analysis.get('has_action_verb', False):
                action_steps += 1
            if analysis.get('is_vague', False):
                vague_steps += 1
            if analysis.get('is_incomplete', False):
                incomplete_steps += 1
        
        return {
            'total_steps': len(children),
            'action_steps': action_steps,
            'vague_steps': vague_steps,
            'incomplete_steps': incomplete_steps,
            'has_clear_goal': bool(title and any(word in title.lower() for word in ['to', 'how', 'setup', 'install']))
        }
    
    def _analyze_step_content(self, content: str) -> Dict[str, Any]:
        """Analyze individual step content."""
        if not content:
            return {
                'has_action_verb': False,
                'is_vague': True,
                'is_incomplete': True,
                'word_count': 0
            }
        
        content_lower = content.lower()
        words = content.split()
        
        # Check for action verbs at the beginning
        has_action_verb = self._has_action_verb(content)
        
        # Check for vague language
        vague_phrases = ['something', 'somehow', 'maybe', 'probably', 'might', 'should work']
        is_vague = any(phrase in content_lower for phrase in vague_phrases)
        
        # Check if step seems incomplete
        is_incomplete = (
            len(words) < 3 or
            content.endswith('...') or
            'TODO' in content or
            'TBD' in content
        )
        
        return {
            'has_action_verb': has_action_verb,
            'is_vague': is_vague,
            'is_incomplete': is_incomplete,
            'word_count': len(words)
        }
    
    def _has_action_verb(self, content: str) -> bool:
        """Check if content starts with an action verb."""
        if not content:
            return False
        
        first_word = content.split()[0].lower().rstrip('.,!?:;')
        return first_word in self.ACTION_VERBS
    
    def _extract_procedure_properties(self, block_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract procedure-specific properties."""
        attributes = block_data.get('attributes', {})
        
        return {
            'numbering_style': attributes.get('style', 'arabic'),
            'start_number': attributes.get('start', 1),
            'is_reversed': attributes.get('reversed', False)
        }
    
    def _estimate_duration(self, children: List[Dict[str, Any]]) -> int:
        """Estimate procedure duration in minutes."""
        if not children:
            return 0
        
        total_time = 0
        for child in children:
            content = child.get('content', '') or child.get('text', '')
            total_time += self._estimate_step_time(content)
        
        return max(1, total_time)  # At least 1 minute
    
    def _estimate_step_time(self, content: str) -> int:
        """Estimate time for a single step in minutes."""
        if not content:
            return 1
        
        word_count = len(content.split())
        
        # Base time estimates
        if word_count <= 5:
            return 1  # Quick action
        elif word_count <= 15:
            return 2  # Normal step
        elif word_count <= 30:
            return 3  # Complex step
        else:
            return 5  # Very complex step
    
    def _assess_complexity(self, children: List[Dict[str, Any]]) -> str:
        """Assess overall procedure complexity."""
        if not children:
            return 'unknown'
        
        step_count = len(children)
        avg_words = sum(len((child.get('content', '') or child.get('text', '')).split()) 
                       for child in children) / step_count
        
        if step_count <= 3 and avg_words <= 10:
            return 'simple'
        elif step_count <= 8 and avg_words <= 20:
            return 'moderate'
        elif step_count <= 15 and avg_words <= 30:
            return 'complex'
        else:
            return 'very_complex'
    
    def _assess_step_difficulty(self, content: str) -> str:
        """Assess difficulty of individual step."""
        if not content:
            return 'unknown'
        
        word_count = len(content.split())
        technical_terms = ['configure', 'install', 'deploy', 'compile', 'debug']
        
        has_technical = any(term in content.lower() for term in technical_terms)
        
        if word_count <= 5 and not has_technical:
            return 'easy'
        elif word_count <= 15 and not has_technical:
            return 'normal'
        elif has_technical or word_count > 30:
            return 'difficult'
        else:
            return 'normal'
    
    def _reconstruct_procedure_markup(self, children: List[Dict[str, Any]], title: str = '') -> str:
        """Reconstruct AsciiDoc procedure markup."""
        markup_lines = []
        
        if title:
            markup_lines.append(f".{title}")
        
        for i, child in enumerate(children, 1):
            content = child.get('content', '') or child.get('text', '')
            markup_lines.append(f"{i}. {content}")
        
        return '\n'.join(markup_lines) 