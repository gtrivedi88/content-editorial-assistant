"""
Reference Module Rule
Evidence-based validation for reference modules following established architectural patterns.

"""
import re
import os
from typing import List, Optional, Dict, Any
from rules.base_rule import BaseRule
from .modular_structure_bridge import ModularStructureBridge
try:
    import yaml
except ImportError:
    yaml = None


class ReferenceModuleRule(BaseRule):
    """Evidence-based reference module validator following established patterns"""
    
    def __init__(self):
        super().__init__()
        self.rule_type = "modular_compliance"
        self.rule_subtype = "reference_module"
        self.parser = ModularStructureBridge()
        
        # Load configuration following established patterns
        self._load_config()
    
    def _get_rule_type(self) -> str:
        """Return the rule type for BaseRule compatibility."""
        return "reference_module"
        
    def _load_config(self):
        """Load configuration following established patterns from other rules."""
        config_path = os.path.join(
            os.path.dirname(__file__), 
            'config', 
            'modular_compliance_types.yaml'
        )
        
        if yaml and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    
                self.imperative_verbs = set(config.get('imperative_verbs', []))
                self.thresholds = config.get('thresholds', {})
                self.evidence_scoring = config.get('evidence_scoring', {})
                self.module_types = config.get('module_types', {})
                
            except Exception:
                self._set_fallback_config()
        else:
            self._set_fallback_config()
    
    def _set_fallback_config(self):
        """Set fallback configuration if config file not available."""
        self.imperative_verbs = {
            'click', 'run', 'type', 'enter', 'execute', 'select', 'start', 'stop',
            'create', 'delete', 'install', 'configure', 'edit', 'open', 'save',
            'verify', 'check', 'test', 'copy', 'paste', 'download', 'upload'
        }
        self.thresholds = {
            'long_content_words': 500,
            'substantial_content_words': 200
        }
        self.evidence_scoring = {
            'base_scores': {
                'exact_violation_match': 0.9,
                'pattern_violation': 0.7,
                'generic_detection': 0.5
            }
        }
    
    def analyze(self, text: str, sentences, nlp=None, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Analyze reference module compliance using direct compliance validation.
        
        Simple approach: Check structural requirements and reference rules directly.
        No complex evidence scoring - compliance is binary (meets requirement or doesn't).
        """
        errors = []
        
        # Analyze if this is explicitly a reference module OR if it contains reference-like elements
        # This makes the rule more defensive and user-friendly
        if context and context.get('content_type'):
            content_type = context.get('content_type')
            if content_type not in ['reference', 'auto', 'unknown']:
                # Skip analysis only if explicitly set to a different type
                return errors
            
        # Parse module structure
        structure = self.parser.parse(text)
        
        # Direct compliance checks - no evidence scoring complexity
        compliance_issues = []
        
        # Title and Introduction
        compliance_issues.extend(self._find_introduction_issues(structure, text))
        
        # Content and Structure
        compliance_issues.extend(self._find_structured_data_issues(structure, text))
        compliance_issues.extend(self._find_organization_issues(structure))
        compliance_issues.extend(self._find_structure_issues(structure))
        
        # Prohibited Content
        compliance_issues.extend(self._find_procedural_content_issues(structure, text))
        compliance_issues.extend(self._find_explanatory_content_issues(structure, text))
        
        # Create errors directly from compliance issues
        for issue in compliance_issues:
            error = self._create_error(
                sentence=issue.get('sentence', issue.get('flagged_text', '')),
                sentence_index=issue.get('line_number', 0),
                message=issue.get('message', ''),
                suggestions=issue.get('suggestions', []),
                severity=self._map_compliance_level_to_severity(issue.get('level')),
                text=text,
                context=context,
                flagged_text=issue.get('flagged_text', ''),
                span=issue.get('span', (0, 0))
            )
            errors.append(error)
        
        return errors
    
    # Simplified compliance validation - no complex evidence calculation needed
    
    def _map_compliance_level_to_severity(self, level: str) -> str:
        """Map compliance levels to standard severity levels."""
        mapping = {
            'FAIL': 'high',
            'WARN': 'medium',
            'INFO': 'low'
        }
        return mapping.get(level, 'medium')
    
    def _find_introduction_issues(self, structure: Dict[str, Any], text: str = "") -> List[Dict[str, Any]]:
        """Check introduction requirements with fallback text analysis."""
        issues = []
        
        # Fallback: analyze text directly if parser didn't extract intro paragraphs
        intro_paragraphs = structure.get('introduction_paragraphs', [])
        if not intro_paragraphs and text:
            # Extract paragraphs manually from text
            lines = text.split('\n')
            current_para = []
            paragraphs_after_title = []
            found_title = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('= ') and not found_title:
                    found_title = True
                    continue
                elif found_title and line and not line.startswith('|') and not line.startswith('==') and not line[0].isdigit():
                    if line:
                        current_para.append(line)
                    elif current_para:
                        paragraphs_after_title.append(' '.join(current_para))
                        current_para = []
                elif found_title and (line.startswith('|') or line.startswith('==') or (line and line[0].isdigit())):
                    # Hit structured content, stop collecting intro
                    if current_para:
                        paragraphs_after_title.append(' '.join(current_para))
                    break
            
            if current_para:
                paragraphs_after_title.append(' '.join(current_para))
            
            intro_paragraphs = paragraphs_after_title
        
        # [FAIL] No Introduction
        if not intro_paragraphs:
            issues.append({
                'type': 'critical_structural',
                'level': 'FAIL',
                'message': "Module lacks a brief, single-paragraph introduction after the title",
                'flagged_text': "Missing introduction",
                'line_number': 2,
                'span': (0, 0),
                'suggestions': [
                    "Add an introductory paragraph explaining what reference data is contained",
                    "Describe when users would consult this reference information",
                    "Keep the introduction brief and focused"
                ]
            })
        
        # [WARN] Multi-paragraph Introduction
        elif len(intro_paragraphs) > 1:
            issues.append({
                'type': 'improvement_suggestion',
                'level': 'WARN',
                'message': f"The introduction consists of {len(intro_paragraphs)} paragraphs instead of one",
                'flagged_text': f"Multi-paragraph introduction: {len(intro_paragraphs)} paragraphs",
                'line_number': 2,
                'span': (0, 0),
                'suggestions': [
                    "Combine introduction paragraphs into a single, concise paragraph",
                    "Move detailed explanations to the reference data sections",
                    "Focus introduction on what reference information is provided"
                ]
            })
        
        return issues
    
    def _find_structured_data_issues(self, structure: Dict[str, Any], text: str = "") -> List[Dict[str, Any]]:
        """Check for presence and position of structured data."""
        issues = []
        
        # Check for structured data indicators
        has_tables = len(structure.get('tables', [])) > 0
        has_lists = len(structure.get('ordered_lists', [])) + len(structure.get('unordered_lists', [])) > 0
        
        # Fallback detection for tables/lists if parser missed them
        if not has_tables and text and '|===' in text:
            has_tables = True
        if not has_lists and text:
            import re
            if re.search(r'^\d+\.\s+|^\*\s+|^-\s+', text, re.MULTILINE):
                has_lists = True
        
        # [FAIL] Lacks Structured Data completely
        if not (has_tables or has_lists):
            # Check if content is mostly prose
            total_words = structure.get('word_count', 0) or len(text.split())
            
            if total_words > self.thresholds.get('substantial_content_words', 200):
                issues.append({
                    'type': 'critical_structural',
                    'level': 'FAIL',
                    'message': "Module's body contains no structured data",
                    'flagged_text': "Missing structured data",
                    'line_number': 0,
                    'span': (0, 0),
                    'suggestions': [
                        "Convert prose content into tables for quick scanning",
                        "Use bulleted lists for sets of related information",
                        "Use definition lists (Term::) for terminology or parameters",
                        "Structure information for easy lookup and reference"
                    ]
                })
        else:
            # [FAIL] Primarily prose before structured data
            # Enhanced detection using text analysis
            if self._has_excessive_prose_before_data(structure, text):
                issues.append({
                    'type': 'critical_structural',
                    'level': 'FAIL',
                    'message': "Module contains excessive prose before presenting structured reference data",
                    'flagged_text': "Too much prose before structured data",
                    'line_number': 0,
                    'span': (0, 0),
                    'suggestions': [
                        "Move the structured data (table, lists) closer to the introduction",
                        "Reduce explanatory text and focus on reference information",
                        "Convert conceptual explanations to structured format where possible"
                    ]
                })
        
        return issues
    
    def _find_organization_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if data appears to be logically organized."""
        issues = []
        
        # Check list organization (simple heuristic)
        for list_data in structure.get('unordered_lists', []):
            if len(list_data['items']) > 5:  # Only check larger lists
                item_texts = [item['text'].lower() for item in list_data['items']]
                
                # Check if items might benefit from alphabetization
                if self._could_be_alphabetized(item_texts):
                    issues.append({
                        'type': 'data_organization',
                        'level': 'WARN',
                        'message': "List content does not appear to be logically organized",
                        'flagged_text': "Unorganized list data",
                        'line_number': list_data['start_line'],
                        'span': (0, 0),
                        'suggestions': [
                            "Consider alphabetizing list items for easier lookup",
                            "Group related items together",
                            "Use consistent organization principles throughout the reference"
                        ]
                    })
        
        # Check table organization - look for obvious sorting opportunities
        if len(structure.get('tables', [])) > 0:
            # For now, add a generic warning about table organization
            # This would require table parsing to do properly
            issues.append({
                'type': 'data_organization',
                'level': 'WARN',
                'message': "Table data may not be optimally organized for scanning",
                'flagged_text': "Table organization",
                'line_number': 0,
                'span': (0, 0),
                'suggestions': [
                    "Sort table rows logically (numerically, alphabetically, or by category)",
                    "Group related entries together",
                    "Consider if the current order supports quick lookup and scanning"
                ]
            })
        
        return issues
    
    def _find_structure_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check structure for long content."""
        issues = []
        
        word_count = structure.get('word_count', 0)
        
        # [INFO] Lacks Structure for Long Content - adjusted threshold
        if word_count > 250 and len(structure.get('sections', [])) <= 1:
            issues.append({
                'type': 'improvement_suggestion',
                'level': 'INFO',
                'message': f"Long module ({word_count} words) does not use subheadings",
                'flagged_text': "Missing structural organization",
                'line_number': 0,
                'span': (0, 0),
                'suggestions': [
                    "Add subheadings to group related reference information",
                    "Use heading hierarchy (==, ===) to organize content",
                    "Group similar types of reference data under common headings"
                ]
            })
        
        return issues
    
    def _find_procedural_content_issues(self, structure: Dict[str, Any], text: str = "") -> List[Dict[str, Any]]:
        """Check for procedural content that doesn't belong."""
        issues = []
        
        # Look for numbered lists with procedural content
        ordered_lists = structure.get('ordered_lists', [])
        
        # Fallback: if no ordered lists detected, check text directly for numbered steps
        if not ordered_lists and text:
            # Look for numbered list patterns in the text
            import re
            numbered_patterns = re.findall(r'^\d+\.\s+(.+)', text, re.MULTILINE)
            if numbered_patterns:
                # Create a mock list structure for analysis
                mock_items = [{'text': pattern} for pattern in numbered_patterns]
                ordered_lists = [{'items': mock_items, 'start_line': 0}]
        
        for list_data in ordered_lists:
            procedural_items = []
            for item in list_data['items']:
                if self._is_procedural_content(item['text']):
                    procedural_items.append(item)
            
            # [FAIL] Contains a Procedure
            if len(procedural_items) >= 2:  # At least 2 procedural steps indicate a procedure
                issues.append({
                    'type': 'prohibited_content',
                    'level': 'FAIL',
                    'message': "Module contains numbered procedural steps",
                    'flagged_text': f"Procedural steps detected: {len(procedural_items)} steps",
                    'line_number': list_data.get('start_line', 0),
                    'span': (0, 0),
                    'suggestions': [
                        "Move step-by-step instructions to a procedure module",
                        "Convert procedural content to reference information",
                        "Focus on providing data that users can look up, not follow step-by-step"
                    ]
                })
        
        return issues
    
    def _find_explanatory_content_issues(self, structure: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
        """Check for explanatory concepts that belong in concept modules."""
        issues = []
        
        # Enhanced detection for conceptual explanations
        explanatory_indicators = [
            'philosophy', 'design philosophy', 'principles', 'approach', 'concept',
            'understanding', 'explanation', 'describes', 'overview', 'background',
            'theory', 'fundamentals', 'key concept', 'important to remember',
            'restful principles', 'consistency is a key concept', 'simplifies integration',
            'improves the overall', 'developer experience'
        ]
        
        content_lower = text.lower()
        explanatory_score = sum(1 for indicator in explanatory_indicators if indicator in content_lower)
        
        # Check for conceptual explanation patterns
        conceptual_patterns = [
            r'it\'?s important to (understand|remember|know)',
            r'the (philosophy|principle|concept|approach) behind',
            r'this (approach|philosophy|design) (simplifies|improves|ensures)',
            r'we follow.*principles.*which means',
            r'this consistency is.*that allows',
            r'(allows|enables) developers to.*without.*proprietary'
        ]
        
        pattern_matches = sum(1 for pattern in conceptual_patterns if re.search(pattern, content_lower))
        
        # Check paragraph length in introduction and throughout document
        long_intro_paras = [para for para in structure.get('introduction_paragraphs', []) if len(para.split()) > 50]
        
        # Count total explanatory paragraphs by analyzing text structure
        paragraphs = text.split('\n\n')
        explanatory_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if len(para.split()) > 30:  # Substantial paragraphs only
                para_lower = para.lower()
                if any(indicator in para_lower for indicator in explanatory_indicators[:5]):  # Key conceptual terms
                    explanatory_paragraphs.append(para)
        
        # [WARN] Contains Long Conceptual Explanations  
        if (explanatory_score >= 3 or 
            pattern_matches >= 1 or 
            len(explanatory_paragraphs) >= 2 or
            len(long_intro_paras) > 0):
            
            issues.append({
                'type': 'prohibited_content',
                'level': 'WARN',
                'message': "Module contains long conceptual explanations that belong in a concept module",
                'flagged_text': f"Conceptual content detected: {len(explanatory_paragraphs)} explanatory paragraphs",
                'line_number': 0,
                'span': (0, 0),
                'suggestions': [
                    "Move conceptual explanations (philosophy, principles, approach) to a concept module",
                    "Keep reference content concise and factual",
                    "Focus on providing scannable data for quick lookup rather than detailed explanations"
                ]
            })
        
        return issues
    
    def _could_be_alphabetized(self, item_texts: List[str]) -> bool:
        """Simple heuristic to check if list could benefit from alphabetization."""
        # Check if items look like commands or parameters
        # that would benefit from alphabetical order
        
        command_like = sum(1 for text in item_texts if any(
            text.startswith(prefix) for prefix in ['--', '-', 'get', 'set', 'list', 'create', 'delete']
        ))
        
        if command_like > len(item_texts) * 0.5:  # More than half look like commands
            # Check if they're already roughly alphabetized
            sorted_texts = sorted(item_texts)
            
            # Simple check: if current order differs significantly from sorted
            misplaced = sum(1 for i, text in enumerate(item_texts) 
                          if i < len(sorted_texts) and text != sorted_texts[i])
            
            return misplaced > len(item_texts) * 0.3  # More than 30% out of order
        
        return False
    
    def _starts_with_action(self, text: str) -> bool:
        """Check if text starts with an action verb."""
        words = text.lower().split()
        if not words:
            return False
        
        first_word = words[0].strip('.,!?:;')
        return first_word in self.imperative_verbs
    
    def _is_procedural_content(self, text: str) -> bool:
        """Check if text contains procedural language patterns."""
        text_lower = text.lower()
        
        # Direct imperative verbs at start
        if self._starts_with_action(text):
            return True
        
        # Common procedural patterns
        procedural_patterns = [
            r'\bfirst\b.*?\bcheck\b',
            r'\bthen\b.*?\b(check|verify|run|execute|get|retrieve|search|report)\b',
            r'\bfollow\s+these\s+steps\b',
            r'\bstep\s+\d+\b',
            r'\bnext\b.*?\b(step|action)\b',
            r'\bwhen\s+this\s+happens\b.*?\bfollow\b',
            r'\bif\s+.*?\bthen\b.*?\b(check|run|execute|do)\b',
            r'\b(troubleshoot|debug|diagnose)\s+.*?\bissue\b',
            r'\bretrieve\s+.*?\bfrom\b',
            r'\bsearch\s+for\b.*?\bin\b',
            r'\breport\s+.*?\bto\b.*?\bteam\b'
        ]
        
        for pattern in procedural_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Sequence indicators
        sequence_words = ['first', 'second', 'third', 'then', 'next', 'finally', 'after', 'before']
        action_words = ['check', 'verify', 'run', 'execute', 'get', 'retrieve', 'search', 'report', 
                       'troubleshoot', 'debug', 'find', 'locate', 'contact', 'follow']
        
        # If text contains both sequence and action words, likely procedural
        has_sequence = any(word in text_lower for word in sequence_words)
        has_action = any(word in text_lower for word in action_words)
        
        return has_sequence and has_action
    
    def _has_excessive_prose_before_data(self, structure: Dict[str, Any], text: str = "") -> bool:
        """Check if there's too much prose before structured data appears."""
        # Count words in introduction from structure or fallback to text analysis
        intro_words = sum(len(para.split()) for para in structure.get('introduction_paragraphs', []))
        
        # Fallback text analysis if structure parsing didn't work
        if intro_words == 0 and text:
            # Count words before first table or numbered list
            lines = text.split('\n')
            words_before_structure = 0
            found_title = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('= ') and not found_title:
                    found_title = True
                    continue
                elif found_title and (line.startswith('|') or (line and line[0].isdigit() and '.' in line)):
                    # Hit structured content, stop counting
                    break
                elif found_title and line:
                    words_before_structure += len(line.split())
            
            intro_words = words_before_structure
        
        # If we have tables/lists, estimate when they appear in the document
        total_words = structure.get('word_count', 0) or len(text.split())
        
        # Count sections before we hit structured content
        sections = structure.get('sections', [])
        early_prose_sections = len([s for s in sections if s.get('level', 0) > 0])
        
        # Multiple criteria for excessive prose - adjusted thresholds
        return (
            intro_words > 120 or  # Long introduction (lowered threshold)
            early_prose_sections > 2 or  # Multiple prose sections before data
            (total_words > 250 and intro_words > total_words * 0.35)  # >35% of content is intro prose
        )
    
    def _get_contextual_message(self, issue: Dict[str, Any], evidence_score: float) -> str:
        """Generate contextual error message based on evidence strength."""
        base_message = issue.get('message', '')
        
        if evidence_score > 0.85:
            return f"[CRITICAL] {base_message}"
        elif evidence_score > 0.6:
            return f"[WARNING] {base_message}"
        else:
            return f"[SUGGESTION] {base_message}"
    
    def _generate_smart_suggestions(self, issue: Dict[str, Any], context: Dict[str, Any] = None, evidence_score: float = 0.5) -> List[str]:
        """Generate evidence-aware smart suggestions."""
        suggestions = issue.get('suggestions', [])
        
        if evidence_score > 0.8:
            suggestions = [f"High priority: {s}" for s in suggestions]
        elif evidence_score > 0.6:
            suggestions = [f"Recommended: {s}" for s in suggestions]
        else:
            suggestions = [f"Optional: {s}" for s in suggestions]
        
        return suggestions[:3]
