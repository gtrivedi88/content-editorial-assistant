"""Procedure Module Rule - validates procedure modules per Red Hat modular documentation guidelines."""
import re
import os
from typing import List, Optional, Dict, Any
from rules.base_rule import BaseRule
from .modular_structure_bridge import ModularStructureBridge
try:
    import yaml
except ImportError:
    yaml = None


class ProcedureModuleRule(BaseRule):
    
    def __init__(self):
        super().__init__()
        self.rule_type = "procedure_module"
        self.rule_subtype = "procedure_module"
        self.parser = ModularStructureBridge()
        self._load_config()
    
    def _get_rule_type(self) -> str:
        return "procedure_module"
        
    def _load_config(self):
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
                
            except (yaml.YAMLError, OSError, ValueError):
                self._set_fallback_config()
        else:
            self._set_fallback_config()
            
        # NOTE: 'limitations' removed per Red Hat Apr 2025 update
        self.approved_subheadings = {
            'prerequisites', 'verification', 
            'troubleshooting', 'next steps', 'additional resources'
        }
        
        # Track deprecated sections for warnings
        self.deprecated_subheadings = {
            'limitations': 'Apr 2025'
        }
    
    def _set_fallback_config(self):
        self.imperative_verbs = {
            'click', 'run', 'type', 'enter', 'execute', 'select', 'start', 'stop',
            'create', 'delete', 'install', 'configure', 'edit', 'open', 'save',
            'verify', 'check', 'test', 'copy', 'paste', 'download', 'upload',
            'navigate', 'scroll', 'press', 'choose', 'pick', 'add', 'remove',
            'list', 'display', 'show', 'view', 'set', 'use', 'enable', 'disable',
            'activate', 'apply', 'update', 'modify', 'change', 'replace', 'rename',
            'move', 'specify', 'define', 'assign', 'connect', 'restart', 'reload',
            'clear', 'reset', 'restore', 'export', 'import', 'deploy', 'build'
        }
        self.evidence_scoring = {
            'base_scores': {
                'exact_violation_match': 0.9,
                'pattern_violation': 0.7,
                'generic_detection': 0.5
            }
        }
    
    def analyze(self, text: str, sentences: List[str] = None, nlp=None, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        # === UNIVERSAL CODE CONTEXT GUARD ===
        # Skip analysis for code blocks, listings, and literal blocks (technical syntax, not prose)
        if context and context.get('block_type') in ['listing', 'literal', 'code_block', 'inline_code']:
            return []
        errors = []
        
        if context and context.get('content_type'):
            content_type = context.get('content_type')
            if content_type not in ['procedure', 'auto', 'unknown']:
                return errors
            
        structure = self.parser.parse(text)
        compliance_issues = []
        
        compliance_issues.extend(self._validate_metadata(text))
        compliance_issues.extend(self._validate_deprecated_discrete_tag(text))
        compliance_issues.extend(self._validate_anchor_prefixes(text))
        compliance_issues.extend(self._validate_attribute_position(text))
        compliance_issues.extend(self._find_title_issues(structure))
        compliance_issues.extend(self._find_introduction_issues(structure))
        compliance_issues.extend(self._validate_introduction_quality(structure))
        compliance_issues.extend(self._find_procedure_issues(structure))
        compliance_issues.extend(self._find_subheading_issues(structure, text))
        compliance_issues.extend(self._validate_verification_section(structure, text))
        compliance_issues.extend(self._check_deprecated_limitations_section(structure))
        compliance_issues.extend(self._find_step_issues(structure))
        compliance_issues.extend(self._find_section_order_issues(structure))
        compliance_issues.extend(self._validate_heading_case(structure, text))
        
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
    
    def _map_compliance_level_to_severity(self, level: str) -> str:
        mapping = {
            'FAIL': 'high',
            'WARN': 'medium',
            'INFO': 'low'
        }
        return mapping.get(level, 'medium')
    
    def _validate_metadata(self, text: str) -> List[Dict[str, Any]]:
        issues = []

        has_new_attr = ':_mod-docs-content-type:' in text
        has_old_attr = ':_content-type:' in text and not has_new_attr

        if has_old_attr:
            issues.append({
                'type': 'metadata_format',
                'level': 'WARN',
                'message': "Using deprecated content type attribute ':_content-type:'",
                'flagged_text': ':_content-type:',
                'line_number': 0,
                'span': (0, 0),
                'suggestions': [
                    "Change ':_content-type:' to ':_mod-docs-content-type:' per Red Hat Aug 2023",
                    "Update: :_mod-docs-content-type: PROCEDURE"
                ]
            })

        return issues
    
    def _validate_deprecated_discrete_tag(self, text: str) -> List[Dict[str, Any]]:
        """
        Flag deprecated [discrete] tag per Red Hat Oct 2025 update.
        
        The modular documentation guide removed references to [discrete] tag.
        """
        issues = []
        
        if '[discrete]' in text:
            line_number = 0
            for i, line in enumerate(text.split('\n'), 1):
                if '[discrete]' in line:
                    line_number = i
                    break
            
            issues.append({
                'type': 'metadata_format',
                'level': 'WARN',
                'message': "Using deprecated [discrete] tag",
                'flagged_text': '[discrete]',
                'line_number': line_number,
                'span': (0, 0),
                'suggestions': [
                    "Remove [discrete] tag per Red Hat Oct 2025 update",
                    "Use appropriate heading levels instead",
                    "See: https://redhat-documentation.github.io/modular-docs/#whats-new"
                ]
            })
        
        return issues
    
    def _validate_anchor_prefixes(self, text: str) -> List[Dict[str, Any]]:
        """
        Flag deprecated module prefixes in anchors per Red Hat May 2023 update.
        
        Anchors should no longer use con_, proc_, ref_ prefixes.
        """
        issues = []
        
        deprecated_patterns = [
            (r'\[\[(con_[^\]]+)\]\]', 'con_', 'concept'),
            (r'\[\[(proc_[^\]]+)\]\]', 'proc_', 'procedure'),
            (r'\[\[(ref_[^\]]+)\]\]', 'ref_', 'reference'),
        ]
        
        for pattern, prefix, module_type in deprecated_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                anchor_id = match.group(1)
                line_number = text[:match.start()].count('\n') + 1
                
                issues.append({
                    'type': 'anchor_naming',
                    'level': 'WARN',
                    'message': f"Anchor uses deprecated '{prefix}' prefix: [[{anchor_id}]]",
                    'flagged_text': f'[[{anchor_id}]]',
                    'line_number': line_number,
                    'span': (match.start(), match.end()),
                    'suggestions': [
                        f"Remove '{prefix}' prefix per Red Hat May 2023 update",
                        f"Use: [[{anchor_id[len(prefix):]}]] instead",
                        "See: https://redhat-documentation.github.io/modular-docs/#whats-new"
                    ]
                })
        
        return issues
    
    def _validate_attribute_position(self, text: str) -> List[Dict[str, Any]]:
        """
        Validate content type attribute is near document start.
        """
        issues = []
        
        match = re.search(r':_mod-docs-content-type:', text)
        if match:
            lines_before = text[:match.start()].count('\n')
            
            if lines_before > 10:
                issues.append({
                    'type': 'attribute_position',
                    'level': 'INFO',
                    'message': f"Content type attribute at line {lines_before + 1}, should be near document start",
                    'flagged_text': ':_mod-docs-content-type:',
                    'line_number': lines_before + 1,
                    'span': (match.start(), match.end()),
                    'suggestions': [
                        "Move :_mod-docs-content-type: to document header",
                        "Place after title and ID, before main content"
                    ]
                })
        
        return issues
    
    def _validate_introduction_quality(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Validate introduction quality per Red Hat SSG guidelines.
        """
        issues = []
        intro_paragraphs = structure.get('introduction_paragraphs', [])
        
        if not intro_paragraphs:
            return issues
        
        intro_text = intro_paragraphs[0]
        intro_lower = intro_text.lower().strip()
        
        antipatterns = [
            (r'^this\s+(section|module|procedure|topic)\s+', 
             "Introduction starts with 'This section/module...'"),
            (r'^the\s+following\s+(steps|procedure)',
             "Introduction starts with 'The following steps/procedure...'"),
            (r'^in\s+this\s+(section|module|procedure)',
             "Introduction starts with 'In this section/module...'"),
            (r'^use\s+this\s+procedure\s+to',
             "Introduction starts with 'Use this procedure to...'"),
        ]
        
        for pattern, message in antipatterns:
            if re.match(pattern, intro_lower):
                issues.append({
                    'type': 'introduction_quality',
                    'level': 'INFO',
                    'message': message,
                    'flagged_text': intro_text[:80] + "..." if len(intro_text) > 80 else intro_text,
                    'line_number': 2,
                    'span': (0, 0),
                    'suggestions': [
                        "Start with WHAT the procedure accomplishes",
                        "Example: 'Configure X to enable Y' instead of 'Use this procedure to configure X'",
                        "See Red Hat SSG: Short descriptions guidelines"
                    ]
                })
                break
        
        return issues
    
    def _validate_verification_section(self, structure: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
        """
        Validate Verification section format per Red Hat guidelines.
        
        Verification sections should contain actionable verification steps,
        not just prose explanations.
        """
        issues = []
        
        for section in structure.get('sections', []):
            if 'verification' in section['title'].lower():
                section_start = section.get('line_number', 0)
                section_content = self._extract_section_content(text, section_start)
                
                # Check if section has actionable content (list or steps)
                has_steps = bool(re.search(r'^\s*[\d.]+\s+|^\s*\*\s+|^\s*-\s+', section_content, re.MULTILINE))
                has_code = bool(re.search(r'----|\[source', section_content))
                
                if not has_steps and not has_code:
                    issues.append({
                        'type': 'verification_format',
                        'level': 'WARN',
                        'message': "Verification section lacks verification steps or commands",
                        'flagged_text': section['title'],
                        'line_number': section_start,
                        'span': section.get('span', (0, 0)),
                        'suggestions': [
                            "Add numbered or bulleted verification steps",
                            "Include commands users can run to verify success",
                            "Example: '1. Verify the service is running: `systemctl status myservice`'"
                        ]
                    })
        
        return issues
    
    def _extract_section_content(self, text: str, section_start_line: int) -> str:
        """Extract content of a section starting at the given line."""
        lines = text.split('\n')
        
        if section_start_line <= 0 or section_start_line > len(lines):
            return ""
        
        content_lines = []
        in_section = False
        
        for i, line in enumerate(lines, 1):
            if i == section_start_line:
                in_section = True
                continue
            
            if in_section:
                # Stop at next section heading
                if re.match(r'^[.=]+\s+', line):
                    break
                content_lines.append(line)
        
        return '\n'.join(content_lines)
    
    def _check_deprecated_limitations_section(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Flag Limitations section as deprecated per Red Hat Apr 2025 update.
        
        The 'Limitations' section was removed from procedure module guidelines.
        """
        issues = []
        
        for section in structure.get('sections', []):
            section_title_lower = section['title'].lower().strip()
            
            if 'limitation' in section_title_lower:
                issues.append({
                    'type': 'deprecated_section',
                    'level': 'INFO',
                    'message': f"Limitations section deprecated per Red Hat Apr 2025 update: \"{section['title']}\"",
                    'flagged_text': section['title'],
                    'line_number': section.get('line_number', 0),
                    'span': section.get('span', (0, 0)),
                    'suggestions': [
                        "Per Red Hat Apr 2025: 'Limitations' section removed from procedure guidelines",
                        "Move constraints/limitations to Prerequisites section",
                        "Or mention limitations in the introductory paragraph",
                        "See: https://redhat-documentation.github.io/modular-docs/#whats-new"
                    ]
                })
        
        return issues
    
    def _find_title_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        issues = []
        title = structure.get('title')
        
        if title:
            clean_title = re.sub(r'`[^`]+`', '', title)
            clean_title = re.sub(r'<[^>]+>', '', clean_title)
            title_words = clean_title.strip().split()
            
            if title_words:
                first_word = title_words[0].lower()
                has_gerund = first_word.endswith('ing')
                
                if not has_gerund and len(title_words) > 1:
                    for word in title_words[1:3]:
                        if word.lower().endswith('ing'):
                            has_gerund = True
                            break
                
                if not has_gerund:
                    issues.append({
                        'type': 'title_format',
                        'level': 'FAIL',
                        'message': f"Title is not a gerund phrase: \"{title}\"",
                        'flagged_text': title,
                        'line_number': 1,
                        'span': (0, len(title)),
                        'suggestions': [
                            "Change title to a gerund form starting with or containing a verb ending in '-ing'",
                            f"Example: '{self._suggest_gerund_title(title)}'",
                            "Remove phrases like 'How to' or 'Steps to'"
                        ]
                    })
        
        return issues
    
    def _find_introduction_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        issues = []
        intro_paragraphs = structure.get('introduction_paragraphs', [])
        
        if not intro_paragraphs:
            if structure.get('has_content', False) and structure.get('word_count', 0) >= 50:
                return issues
        
        if not intro_paragraphs:
            issues.append({
                'type': 'critical_structural',
                'level': 'FAIL',
                'message': "Module lacks a brief introductory paragraph after the title",
                'flagged_text': "Missing introduction",
                'line_number': 2,
                'span': (0, 0),
                'suggestions': [
                    "Add introductory paragraph explaining what this procedure accomplishes",
                    "Include when or why someone would perform this procedure"
                ]
            })
        
        return issues
    
    def _find_procedure_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        issues = []
        
        has_procedure_section = any('procedure' in section['title'].lower() for section in structure.get('sections', []))
        has_ordered_steps = len(structure.get('ordered_lists', [])) > 0
        
        if not has_procedure_section and not has_ordered_steps:
            issues.append({
                'type': 'critical_structural',
                'level': 'FAIL',
                'message': "Module does not contain a Procedure section with steps to follow",
                'flagged_text': "Missing procedure steps",
                'line_number': 0,
                'span': (0, 0),
                'suggestions': [
                    "Add a 'Procedure' section with numbered steps",
                    "Include clear, actionable steps that users can follow",
                    "Each step should be a single, direct action"
                ]
            })
        
        return issues
    
    def _find_subheading_issues(self, structure: Dict[str, Any], text: str = '') -> List[Dict[str, Any]]:
        issues = []
        
        for section in structure.get('sections', []):
            section_title_lower = section['title'].lower().strip()
            
            if section['level'] == 0:
                continue
            
            if section_title_lower == 'procedure':
                continue
            
            if self._is_singular_plural_issue(section['title']):
                issues.append({
                    'type': 'optional_improvement',
                    'level': 'WARN',
                    'message': f"Heading should be plural: \"{section['title']}\"",
                    'flagged_text': section['title'],
                    'line_number': section['line_number'],
                    'span': section['span'],
                    'suggestions': [
                        f"Change '{section['title']}' to '{self._get_plural_form(section['title'])}'",
                        "Per Red Hat 2021: Prerequisites, Limitations, etc. are always plural"
                    ]
                })
            elif not any(approved in section_title_lower for approved in self.approved_subheadings):
                issues.append({
                    'type': 'optional_improvement',
                    'level': 'WARN',
                    'message': f"Non-standard subheading: \"{section['title']}\"",
                    'flagged_text': section['title'],
                    'line_number': section['line_number'],
                    'span': section['span'],
                    'suggestions': [
                        f"Consider using one of the approved subheadings: {', '.join(self.approved_subheadings)}",
                        "Move content to the main Procedure section if it contains steps"
                    ]
                })
        
        # Text-level fallback for singular headings (parser may miss sections)
        if text:
            singular_patterns = {
                r'^\.Prerequisite\s*$': 'Prerequisite',
                r'^\.Limitation\s*$': 'Limitation',
                r'^\.Requirement\s*$': 'Requirement'
            }
            
            for pattern, singular_form in singular_patterns.items():
                if re.search(pattern, text, re.MULTILINE):
                    issues.append({
                        'type': 'optional_improvement',
                        'level': 'WARN',
                        'message': f"Heading should be plural: \"{singular_form}\"",
                        'flagged_text': singular_form,
                        'line_number': 0,
                        'span': (0, 0),
                        'suggestions': [
                            f"Change '.{singular_form}' to '.{self._get_plural_form(singular_form)}'",
                            "Per Red Hat 2021: headings like Prerequisites are always plural"
                    ]
                })
        
        return issues
    
    def _find_step_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        issues = []
        
        for list_data in structure.get('ordered_lists', []):
            if len(list_data['items']) == 1:
                issues.append({
                    'type': 'optional_improvement',
                    'level': 'WARN',
                    'message': "Single step uses numbered list format",
                    'flagged_text': "Single numbered step",
                    'line_number': list_data['start_line'],
                    'span': (0, 0),
                    'suggestions': [
                            "Change from numbered list (1.) to bullet point (*) for single steps"
                    ]
                })
            
            for item in list_data['items']:
                if not self._starts_with_action(item['text']):
                    issues.append({
                        'type': 'step_validation',
                        'level': 'FAIL',
                        'message': f"Step does not begin with an action: \"{item['text'][:50]}...\"",
                        'flagged_text': item['text'],
                        'line_number': item['line_number'],
                        'span': item['span'],
                        'suggestions': [
                            "Start the step with an action verb (click, type, select, etc.)",
                            "Make the step a clear, direct command"
                        ]
                    })
                
                if self._has_multiple_actions(item['text']):
                    issues.append({
                        'type': 'step_validation',
                        'level': 'FAIL',
                        'message': f"Step contains multiple actions: \"{item['text'][:50]}...\"",
                        'flagged_text': item['text'],
                        'line_number': item['line_number'],
                        'span': item['span'],
                        'suggestions': [
                            "Break this step into multiple, separate steps",
                            "Each step should have only one action"
                        ]
                    })
                
                if self._has_conceptual_explanation(item['text']):
                    issues.append({
                        'type': 'step_validation',
                        'level': 'FAIL',
                        'message': f"Step contains conceptual explanation instead of direct action: \"{item['text'][:50]}...\"",
                        'flagged_text': item['text'],
                        'line_number': item['line_number'],
                        'span': item['span'],
                        'suggestions': [
                            "Remove explanatory content and focus on the action",
                            "Move detailed explanations to a Concept module"
                        ]
                    })
                
                if self._is_vague_step(item['text']):
                    issues.append({
                        'type': 'step_validation',
                        'level': 'FAIL',
                        'message': f"Step is too vague and not actionable: \"{item['text'][:50]}...\"",
                        'flagged_text': item['text'],
                        'line_number': item['line_number'],
                        'span': item['span'],
                        'suggestions': [
                            "Make the step more specific and actionable",
                            "Replace vague instructions with concrete commands"
                        ]
                    })
        
        return issues
    
    def _find_section_order_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        issues = []
        next_steps_index = None
        additional_resources_index = None
        
        for i, section in enumerate(structure.get('sections', [])):
            title_lower = section['title'].lower()
            if 'next steps' in title_lower:
                next_steps_index = i
            elif 'additional resources' in title_lower:
                additional_resources_index = i
        
        if (next_steps_index is not None and additional_resources_index is not None and 
            additional_resources_index < next_steps_index):
            
            issues.append({
                'type': 'optional_improvement',
                'level': 'INFO',
                'message': "Additional resources appears before Next steps",
                'flagged_text': "Section order",
                'line_number': structure['sections'][additional_resources_index]['line_number'],
                'span': (0, 0),
                'suggestions': ["Move 'Additional resources' section after 'Next steps'"]
            })
        
        return issues
    
    def _validate_heading_case(self, structure: Dict[str, Any], text: str = '') -> List[Dict[str, Any]]:
        issues = []
        
        for section in structure.get('sections', []):
            heading = section.get('title', '')
            if not heading or section.get('level', 0) == 0:
                continue
            
            words = heading.split()
            if len(words) < 2:
                continue
            
            capitalized_count = 0
            short_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
            
            for i, word in enumerate(words[1:], start=1):
                clean_word = word.strip('.,!?:;()[]{}')
                if not clean_word:
                    continue
                
                if clean_word[0].isupper() and clean_word.lower() not in short_words:
                    if not (clean_word.isupper() or self._is_proper_noun(clean_word)):
                        capitalized_count += 1
            
            if capitalized_count >= 2:
                issues.append({
                    'type': 'heading_format',
                    'level': 'WARN',
                    'message': f'Heading uses title case instead of sentence case: "{heading}"',
                    'flagged_text': heading,
                    'line_number': section.get('line_number', 0),
                    'span': section.get('span', (0, 0)),
                    'suggestions': [
                        f'Convert to sentence case: "{self._to_sentence_case(heading)}"',
                        "Per Red Hat 2022: Use sentence case for headings"
                    ]
                })
        
        # Text-level fallback for title case in steps
        if text:
            step_pattern = r'^\d+\.\s+(.+)$'
            for match in re.finditer(step_pattern, text, re.MULTILINE):
                step_text = match.group(1).strip()
                words = step_text.split()
                if len(words) >= 3:
                    cap_count = sum(1 for w in words[1:3] if w and w[0].isupper() and not w.isupper())
                    if cap_count >= 2:
                        issues.append({
                            'type': 'heading_format',
                            'level': 'INFO',
                            'message': f'Step uses title case: "{step_text[:50]}"',
                            'flagged_text': step_text[:50],
                            'line_number': 0,
                            'span': (0, 0),
                            'suggestions': [
                                "Use sentence case in step text per Red Hat 2022"
                            ]
                        })
                        break
        
        return issues
    
    def _is_proper_noun(self, word: str) -> bool:
        proper_nouns = {
            'red', 'hat', 'linux', 'kubernetes', 'openshift', 'ansible', 'docker',
            'python', 'java', 'javascript', 'api', 'rest', 'http', 'https', 'ssh'
        }
        return word.lower() in proper_nouns
    
    def _to_sentence_case(self, heading: str) -> str:
        words = heading.split()
        if not words:
            return heading
        
        result = [words[0]]
        short_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        
        for word in words[1:]:
            clean_word = word.strip('.,!?:;()[]{}')
            if clean_word.isupper() or self._is_proper_noun(clean_word):
                result.append(word)
            elif clean_word.lower() in short_words:
                result.append(clean_word.lower())
            else:
                result.append(clean_word.lower())
        
        return ' '.join(result)
    
    def _suggest_gerund_title(self, title: str) -> str:
        title_lower = title.lower()
        
        if title_lower.startswith('how to '):
            base = title[7:]
        elif title_lower.startswith('steps to '):
            base = title[9:]
        elif title_lower.startswith('to '):
            base = title[3:]
        else:
            base = title
        
        words = base.split()
        if words:
            first_word = words[0].lower()
            if first_word == 'deploy':
                words[0] = 'Deploying'
            elif first_word == 'install':
                words[0] = 'Installing'
            elif first_word == 'configure':
                words[0] = 'Configuring'
            elif first_word == 'create':
                words[0] = 'Creating'
            elif first_word == 'delete':
                words[0] = 'Deleting'
            else:
                words[0] = first_word.capitalize() + 'ing'
        
        return ' '.join(words)
    
    def _starts_with_action(self, text: str) -> bool:
        """
        Check if step starts with an action verb (imperative).
        
        Handles common qualifier patterns:
        - "Optional: [action]..."
        - "If [condition], [action]..."
        - "For [product/condition]: [action]..." or "For [product] only: [action]..."
        - "In [location], [action]..."
        - "From [location], [action]..."
        """
        text_clean = text.strip()
        text_lower = text_clean.lower()
        words = text_lower.split()
        
        if not words:
            return False
        
        # Handle "Optional: [action]..."
        if text_lower.startswith('optional:'):
            remaining_text = text_clean[9:].strip()
            if remaining_text:
                remaining_words = remaining_text.lower().split()
                if remaining_words:
                    return remaining_words[0].strip('.,!?:;') in self.imperative_verbs
            return False
        
        # Handle "For [product/condition]: [action]..." or "For [product] only: [action]..."
        # Also handle "For [condition], [additional qualifier], [action]..."
        if text_lower.startswith('for '):
            colon_pos = text_clean.find(':')
            # Only treat as qualifier colon if it appears early (within first 60 chars)
            # This avoids matching colons in URLs or later content
            if colon_pos > 0 and colon_pos < 60:
                # Found qualifier with colon, check what comes after the colon
                action_part = text_clean[colon_pos + 1:].strip()
                
                # Skip "To [purpose]," and get to the actual action
                if action_part.lower().startswith('to '):
                    comma_pos = action_part.find(',')
                    if comma_pos > 0:
                        action_part = action_part[comma_pos + 1:].strip()
                    else:
                        # "To [action]" pattern - extract the verb after "to"
                        action_words = action_part[3:].strip().split()
                        if action_words:
                            return action_words[0].strip('.,!?:;') in self.imperative_verbs
                
                action_words = action_part.lower().split()
                if action_words:
                    return action_words[0].strip('.,!?:;') in self.imperative_verbs
            else:
                # No colon - pattern like "For [condition], [action]..." or "For [condition], from [location], [action]..."
                # Find where the action verb appears after commas
                remaining = text_clean[4:].strip()  # Skip "for "
                
                # Look for any action verb in the remaining text
                for i, word in enumerate(remaining.lower().split()):
                    clean_word = word.strip('.,!?:;<>')
                    clean_word = re.sub(r'<[^>]+>', '', clean_word)
                    clean_word = clean_word.strip('.,!?:;')
                    if clean_word and clean_word in self.imperative_verbs:
                        return True
            return False
        
        # Handle "In [location], [action]..." or "From [location], [action]..."
        if text_lower.startswith(('in ', 'from ', 'at ', 'on ', 'within ', 'inside ')):
            # Look for the comma that ends the location qualifier
            comma_pos = text_clean.find(',')
            if comma_pos > 0:
                action_part = text_clean[comma_pos + 1:].strip()
                action_words = action_part.lower().split()
                if action_words:
                    return action_words[0].strip('.,!?:;') in self.imperative_verbs
            # No comma - check if there's an action verb later in the sentence
            # This handles "In the field paste..." (no comma)
            for i, word in enumerate(words):
                if i == 0:
                    continue
                if word.strip('.,!?:;') in self.imperative_verbs:
                    return True
            return False
        
        # Handle "If [condition], [action]..."
        if text_lower.startswith('if '):
            comma_pos = text_clean.find(',')
            if comma_pos > 0:
                action_part = text_clean[comma_pos + 1:].strip()
                if action_part:
                    if action_part.lower().startswith('then '):
                        action_part = action_part[5:].strip()
                    action_words = action_part.lower().split()
                    if action_words:
                        return action_words[0].strip('.,!?:;') in self.imperative_verbs
            return False
        
        # Reject "To [infinitive]..." at the start (not imperative)
        if words[0] == 'to' and len(words) > 1:
            return False
        
        # Standard case: check if first word is an action verb
        return words[0].strip('.,!?:;') in self.imperative_verbs
    
    def _starts_with_imperative(self, text: str) -> bool:
        return self._starts_with_action(text)
    
    def _has_multiple_actions(self, text: str) -> bool:
        """
        Check if step contains multiple INDEPENDENT actions that should be separate steps.
        
        Per Red Hat guidelines, steps can be complex and include:
        - Related micro-actions (e.g., "Open the file and edit the values")
        - Explanatory context (e.g., "This file stores...")
        - Multiple sentences providing guidance
        
        This should only flag truly independent actions that belong in separate steps.
        """
        text_lower = text.lower().strip()
        
        # Allow conditional steps
        if text_lower.startswith('if '):
            return False
        
        # Allow infinitive purpose clauses ("to verify", "to check", etc.)
        if text_lower.startswith('to '):
            return False
        
        # Allow "use X to Y" patterns
        if re.search(r'\buse\s+\w+.*?\s+to\s+(verify|check|test|validate|confirm|ensure)', text_lower):
            return False
        
        # Allow explanatory sentences that provide context (common in good procedures)
        # These are INFORMATIVE, not separate actions
        explanatory_patterns = [
            r'\.\s+This (action|command|file|setting|configuration|option)',
            r'\.\s+(The|This|That)\s+\w+\s+(stores|provides|contains|displays|shows)',
            r'\.\s+For example,',
            r'\.\s+Default is',
            r'\.\s+Otherwise,',
            r'\.\s+Alternatively,',
        ]
        
        for pattern in explanatory_patterns:
            if re.search(pattern, text_lower):
                # Has explanatory content - likely a single complex step
                # Only flag if there are VERY clear independent actions
                pass
        
        # Strong indicators of truly separate actions
        strong_separators = [
            ' and then ', 
            ' then ',
            '; then ',
            ', then ',
            ' followed by ',
            ' subsequently ',
            ' after that ',
            ' afterwards ',
            ' next ',
        ]
        
        # Check for clear sequential separate actions
        for separator in strong_separators:
            if separator in text_lower:
                # Look for imperative verb AFTER the separator
                parts = text_lower.split(separator)
                if len(parts) >= 2:
                    second_part = parts[1].strip()
                    words = second_part.split()
                    if words and words[0].strip('.,!?:;') in self.imperative_verbs:
                        # True separate action found
                        return True
        
        # Check for semicolon-separated commands (clear separate actions)
        if '; ' in text_lower:
            parts = text_lower.split('; ')
            action_count = 0
            for part in parts:
                words = part.strip().split()
                if words and words[0].strip('.,!?:;') in self.imperative_verbs:
                    action_count += 1
            if action_count >= 2:
                return True
        
        return False
    
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
    
    def _has_conceptual_explanation(self, text: str) -> bool:
        """
        Check if step contains EXCESSIVE conceptual explanations instead of direct actions.
        
        Per Red Hat guidelines, steps CAN and SHOULD include:
        - Brief context about what the action does (e.g., "This action adjusts...")
        - Purpose or outcome of the step
        - Brief clarifying information
        
        Only flag if the step is PRIMARILY explanation rather than action.
        """
        text_lower = text.lower()
        
        # Strong indicators of purely conceptual content (no action)
        purely_conceptual_indicators = [
            'this is important because',
            'this is crucial because', 
            'this is necessary because',
            'the reason for this is',
            'it is important to understand',
            'it is worth noting',
            'keep in mind that',
            'remember that',
            'note that this',
            'be aware that',
            'understanding how',
            'the concept of',
            'to understand why',
        ]
        
        # Check if step starts with conceptual language (red flag)
        words = text_lower.split()
        if len(words) > 5:
            first_phrase = ' '.join(words[:5])
            for indicator in purely_conceptual_indicators:
                if indicator in first_phrase:
                    return True
        
        # Check for very long explanatory content (>40 words) WITHOUT an action verb at start
        if len(text.split()) > 40:
            # Check if it starts with an action verb
            if words and words[0].strip('.,!?:;') not in self.imperative_verbs:
                # Long content without action verb - likely conceptual
                if any(indicator in text_lower for indicator in purely_conceptual_indicators):
                    return True
                
                # Check for technical definition patterns (not procedures)
                definition_patterns = [
                    r'^(A|An|The)\s+\w+\s+(is|are|defines|represents)',
                    r'^\w+\s+(refer|refers)\s+to',
                    r'^\w+\s+(mean|means)\s+',
                ]
                
                for pattern in definition_patterns:
                    if re.search(pattern, text_lower):
                        return True
        
        return False
    
    def _is_vague_step(self, text: str) -> bool:
        """
        Check if step is too vague or non-actionable.
        
        Only flag steps that are truly vague and don't provide actionable guidance.
        Steps like "Check the log file" or "Verify the installation" are concrete and acceptable.
        """
        text_lower = text.lower().strip()
        
        # Truly vague verbs that don't specify concrete actions
        # NOTE: Removed "review", "examine", "monitor", "check", "verify", "confirm", "ensure" 
        # as these are legitimate procedure verbs when used with specific objects
        vague_verbs = {
            'consider',
            'think about',
            'be aware',
            'notice',
            'realize',
            'understand',
            'comprehend',
            'contemplate',
            'ponder',
        }
        
        # Check if step starts with vague verbs
        words = text_lower.split()
        if words:
            first_word = words[0].strip('.,!?:;')
            if first_word in vague_verbs:
                return True
            
            # Check for multi-word vague phrases at the start
            if len(words) >= 2:
                two_word_start = f"{words[0]} {words[1]}"
                if two_word_start in vague_verbs:
                    return True
        
        # Check for vague patterns that lack specificity
        vague_patterns = [
            r'^consider\s+',
            r'^think\s+about\s+',
            r'^be\s+aware\s+(of|that)',
            r'^notice\s+(that|how)',
            r'^realize\s+that',
            r'^understand\s+that',
        ]
        
        for pattern in vague_patterns:
            if re.match(pattern, text_lower):
                return True
        
        return False
    
    def _is_singular_plural_issue(self, heading: str) -> bool:
        heading_lower = heading.lower().strip()
        
        should_be_plural = {
            'prerequisite': 'prerequisites',
            'limitation': 'limitations',
            'requirement': 'requirements',
            'resource': 'resources',
            'step': 'steps'
        }
        
        for singular, plural in should_be_plural.items():
            if heading_lower == singular or (singular in heading_lower and plural not in heading_lower and len(heading_lower.split()) <= 2):
                return True
        
        return False
    
    def _get_plural_form(self, heading: str) -> str:
        """Get the plural form of a heading."""
        heading_lower = heading.lower()
        
        # Known singular to plural conversions
        conversions = {
            'prerequisite': 'Prerequisites',
            'limitation': 'Limitations',
            'requirement': 'Requirements',
            'resource': 'Resources',
            'step': 'Steps'
        }
        
        for singular, plural in conversions.items():
            if singular in heading_lower:
                return heading.replace(singular.title(), plural)
        
        # Fallback: just add 's'
        return heading + 's'
