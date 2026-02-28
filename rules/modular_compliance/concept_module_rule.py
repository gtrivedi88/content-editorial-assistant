"""Concept Module Rule - validates concept modules per Red Hat modular documentation guidelines."""
import re
import os
from typing import List, Optional, Dict, Any
from rules.base_rule import BaseRule
from .modular_structure_bridge import ModularStructureBridge
try:
    import yaml
except ImportError:
    yaml = None


class ConceptModuleRule(BaseRule):
    
    def __init__(self):
        super().__init__()
        self.rule_type = "concept_module"
        self.rule_subtype = "concept_module"
        self.parser = ModularStructureBridge()
        self._load_config()
    
    def _get_rule_type(self) -> str:
        return "concept_module"
    
    def _detect_content_type_from_metadata(self, text: str) -> Optional[str]:
        """
        Detect content type from document metadata attributes.
        
        Looks for:
        - :_mod-docs-content-type: PROCEDURE|CONCEPT|REFERENCE|ASSEMBLY
        - :_content-type: (deprecated but still supported)
        
        Returns lowercase type or None if not found.
        """
        # Check for new-style attribute
        new_style = re.search(r':_mod-docs-content-type:\s*(PROCEDURE|CONCEPT|REFERENCE|ASSEMBLY)', text, re.IGNORECASE)
        if new_style:
            return new_style.group(1).lower()
        
        # Check for old-style attribute (deprecated but still supported)
        old_style = re.search(r':_content-type:\s*(PROCEDURE|CONCEPT|REFERENCE|ASSEMBLY)', text, re.IGNORECASE)
        if old_style:
            return old_style.group(1).lower()
        
        return None
        
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
                self.thresholds.setdefault('concise_introduction_words', 100)
                self.evidence_scoring = config.get('evidence_scoring', {})
                self.module_types = config.get('module_types', {})
                
            except (yaml.YAMLError, OSError, ValueError):
                self._set_fallback_config()
        else:
            self._set_fallback_config()
    
    def _set_fallback_config(self):
        self.imperative_verbs = {
            'click', 'run', 'type', 'enter', 'execute', 'select', 'start', 'stop',
            'create', 'delete', 'install', 'configure', 'edit', 'open', 'save',
            'verify', 'check', 'test', 'copy', 'paste', 'download', 'upload',
            'navigate', 'scroll', 'press', 'choose', 'pick', 'add', 'remove'
        }
        self.thresholds = {
            'long_content_words': 400,
            'very_long_content_words': 500,
            'substantial_content_words': 100,
            'concise_introduction_words': 100
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
        context = context or {}
        
        # Detect content type from metadata if not provided
        detected_type = self._detect_content_type_from_metadata(text)
        content_type = context.get('content_type', detected_type)
        
        # Only analyze if this is a concept module
        if content_type and content_type != 'concept':
            return errors
            
        structure = self.parser.parse(text)
        compliance_issues = []
        
        compliance_issues.extend(self._validate_metadata(text))
        compliance_issues.extend(self._validate_deprecated_discrete_tag(text))
        compliance_issues.extend(self._validate_anchor_prefixes(text))
        compliance_issues.extend(self._validate_attribute_position(text))
        compliance_issues.extend(self._find_introduction_issues(structure, text))
        compliance_issues.extend(self._validate_introduction_quality(structure))
        compliance_issues.extend(self._find_content_issues(structure))
        compliance_issues.extend(self._find_title_issues(structure))
        compliance_issues.extend(self._find_procedural_content(structure, text))
        compliance_issues.extend(self._find_improvement_opportunities(structure))
        compliance_issues.extend(self._detect_assembly_pattern(structure, text))
        compliance_issues.extend(self._detect_module_nesting(text))
        compliance_issues.extend(self._validate_heading_case(structure))
        
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
                    "Change ':_content-type:' to ':_mod-docs-content-type:' per Red Hat Aug 2023 update",
                    "Update: :_mod-docs-content-type: CONCEPT"
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
            # Find line number
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
        
        The :_mod-docs-content-type: attribute should be in the document header,
        typically within the first 10 lines after the title.
        """
        issues = []
        
        match = re.search(r':_mod-docs-content-type:', text)
        if match:
            lines_before = text[:match.start()].count('\n')
            
            # Should be within first 10 lines (after title, before main content)
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
        
        Per Red Hat Supplementary Style Guide:
        - Don't start with "This section/module..."
        - Don't start with "The following..."
        - Don't repeat the title verbatim
        - Should explain WHAT and WHY
        """
        issues = []
        intro_paragraphs = structure.get('introduction_paragraphs', [])
        
        if not intro_paragraphs:
            return issues
        
        intro_text = intro_paragraphs[0]
        intro_lower = intro_text.lower().strip()
        
        # Anti-patterns per Red Hat SSG
        antipatterns = [
            (r'^this\s+(section|module|chapter|document|topic)\s+', 
             "Introduction starts with 'This section/module...'"),
            (r'^the\s+following\s+',
             "Introduction starts with 'The following...'"),
            (r'^in\s+this\s+(section|module|chapter)',
             "Introduction starts with 'In this section/module...'"),
            (r'^this\s+is\s+a\s+(concept|procedure|reference)',
             "Introduction starts with 'This is a...'"),
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
                        "Start with what the content IS, not what the section contains",
                        "Answer: What is this? Why should users care?",
                        "See Red Hat SSG: Short descriptions guidelines"
                    ]
                })
                break
        
        return issues
    
    def _find_introduction_issues(self, structure: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
        """
        Validate introduction per Red Hat guidelines.
        
        Per Red Hat: Concept modules require a short introduction (single paragraph).
        If the parser can't extract intro_paragraphs but document has content, assume it's present.
        """
        issues = []
        intro_paragraphs = structure.get('introduction_paragraphs', [])
        
        # If parser didn't extract intro_paragraphs, check if document has content
        if not intro_paragraphs:
            total_word_count = structure.get('word_count', 0)
            has_content = structure.get('has_content', False)
            
            # If document has meaningful content (>15 words), assume intro is present
            # Parser might not extract it properly due to formatting
            if has_content and total_word_count >= 15:
                return issues
        
        if not intro_paragraphs:
            issues.append({
                'type': 'critical_structural',
                'level': 'FAIL',
                'message': "Module must begin with a single, concise introductory paragraph",
                'flagged_text': "Missing introduction",
                'line_number': 2,
                'span': (0, 0),
                'suggestions': [
                    "Add introductory paragraph answering: What is this concept?",
                    "Explain why users should care about this concept",
                    "Keep introduction under 100 words for conciseness"
                ]
            })
        elif len(intro_paragraphs) > 1:
            issues.append({
                'type': 'improvement_suggestion',
                'level': 'WARN',
                'message': f"Introduction has {len(intro_paragraphs)} paragraphs, should be single paragraph",
                'flagged_text': "Multi-paragraph introduction",
                'line_number': 2,
                'span': (0, 0),
                'suggestions': [
                    "Combine into a single, concise paragraph",
                    "Move detailed explanations to the module body"
                ]
            })
        else:
            intro_text = intro_paragraphs[0]
            intro_word_count = len(intro_text.split())
            max_words = self.thresholds.get('concise_introduction_words', 100)
            
            if intro_word_count > max_words:
                issues.append({
                    'type': 'improvement_suggestion',
                    'level': 'INFO',
                    'message': f"Introduction is {intro_word_count} words (recommended: under {max_words})",
                    'flagged_text': intro_text[:100] + "...",
                    'line_number': 2,
                    'span': (0, 0),
                    'suggestions': [
                        "Shorten introduction to be more concise",
                        "Move detailed information to the module body"
                    ]
                })
        
        return issues
    
    def _find_content_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        issues = []
        
        body_content_indicators = (
            len(structure.get('sections', [])) > 0 or
            len(structure.get('introduction_paragraphs', [])) > 1 or
            structure.get('word_count', 0) > 15  # Lowered from 100 - any content is acceptable
        )
        
        # Only flag if there's truly NO content at all
        if not body_content_indicators and structure.get('word_count', 0) < 10:
            issues.append({
                'type': 'critical_structural',
                'level': 'FAIL',
                'message': "Module contains no body content after the introduction",
                'flagged_text': "Missing substantial content",
                'line_number': 0,
                'span': (0, 0),
                'suggestions': [
                    "Add detailed explanations of the concept",
                    "Include examples or use cases",
                    "Provide context about when and why this concept is relevant"
                ]
            })
        
        return issues
    
    def _find_procedural_content(self, structure: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
        """
        Check for prohibited step-by-step procedures.
        """
        issues = []
        action_steps = []
        
        for list_data in structure.get('ordered_lists', []):
            imperative_count = sum(1 for item in list_data['items'] if self._starts_with_imperative(item['text']))
            sequential_indicators = ['then ', 'next,', 'next ', 'finally', 'first', 'second', 'after ']
            has_sequential = any(
                any(indicator in item['text'].lower() for indicator in sequential_indicators)
                for item in list_data['items']
            )
            
            if imperative_count >= 2 or (has_sequential and imperative_count >= 1):
                action_steps.append({
                    'text': f"Ordered list with {imperative_count} imperatives, sequential={has_sequential}",
                    'line_number': list_data.get('start_line', 0),
                    'span': (0, 0),
                    'source': 'ordered_list'
                    })
        
        for list_data in structure.get('unordered_lists', []):
            procedural_count = sum(1 for item in list_data['items'] if self._is_procedural_step(item['text']))
            
            if procedural_count > 0:
                for item in list_data['items']:
                    if self._is_procedural_step(item['text']):
                        action_steps.append({
                            'text': item['text'],
                            'line_number': item['line_number'],
                            'span': item['span'],
                            'source': 'unordered_list'
                        })
        
        sequential_indicators = ['first', 'then', 'next', 'finally', 'after that', 'subsequently']
        sentences = re.split(r'[.!?]+\s+', text)
        
        sequential_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower().strip()
            if any(sentence_lower.startswith(ind) for ind in sequential_indicators):
                for ind in sequential_indicators:
                    if sentence_lower.startswith(ind):
                        remainder = sentence_lower[len(ind):].strip(',: ')
                        words = remainder.split()
                        if words and words[0] in self.imperative_verbs:
                            sequential_sentences.append(sentence.strip())
                            break
        
        if len(sequential_sentences) >= 2:
            action_steps.append({
                'text': f"{len(sequential_sentences)} sequential procedural sentences",
                'line_number': 0,
                'span': (0, 0),
                'source': 'paragraph'
            })
        
        if action_steps:
            step_count = len(action_steps)
            examples = [s['text'][:60] + "..." if len(s['text']) > 60 else s['text'] for s in action_steps[:3]]
            first_step = action_steps[0]
            
            issues.append({
                'type': 'prohibited_content',
                'level': 'FAIL',
                'message': f"Contains {step_count} procedural step(s) - move to procedure module",
                'flagged_text': f"{step_count} procedural steps",
                'line_number': first_step['line_number'],
                'span': first_step['span'],
                'suggestions': [
                    "Move step-by-step instructions to a procedure module",
                    "Replace with descriptive explanation of the process",
                    "Simple actions are allowed per Red Hat 2021 guidelines",
                    f"Examples: {', '.join(examples)}"
                ]
            })
        
        return issues
    
    def _is_procedural_step(self, text: str) -> bool:
        """
        Determine if text is a procedural step vs allowed simple action.
        
        Default: ALLOW simple actions (permissive)
        Flag: Only clear multi-step procedures (restrictive)
        """
        text_lower = text.lower().strip()
        
        if not self._starts_with_imperative(text):
            return False
        
        # Explicit indicators of multi-step procedure (PROHIBITED)
        procedural_indicators = [
            r'^\d+\.',
            r'step\s+\d+',
            r'\bthen\s+',
            r'\bnext,?\s+',
            r'after\s+that',
            r'finally,?\s+',
            r'and\s+then',
            r'first,?\s+',
            r'second,?\s+',
            r'subsequently',
        ]
        
        for indicator in procedural_indicators:
            if re.search(indicator, text_lower):
                return True
        
        # Very long instructions are likely procedural
        if len(text.split()) > 15:
            return True
        
        # Default: ALLOW (per Red Hat 2021 - simple actions are permitted)
        return False
    
    def _find_title_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Validate concept module titles per Red Hat guidelines.
        
        Per Red Hat modular docs, concept titles SHOULD start with:
        - "Understanding [topic]"  
        - "About [topic]"
        - "What is [topic]"
        - "Overview of [topic]"
        
        They should NOT use procedural gerunds like "Installing", "Configuring", etc.
        """
        issues = []
        
        title = structure.get('title', '')
        if not title:
            return issues
        
        title_lower = title.lower()
        
        # Red Hat RECOMMENDED concept title patterns (do NOT flag these)
        recommended_patterns = [
            'understanding',  # "Understanding software templates"
            'about',          # "About authentication"
            'what is',        # "What is a template"
            'what are',       # "What are security groups"
            'overview of',    # "Overview of deployment"
        ]
        
        # Check if title starts with recommended patterns
        starts_with_recommended = any(title_lower.startswith(pattern) for pattern in recommended_patterns)
        
        if not starts_with_recommended:
            # Only flag PROCEDURAL gerunds, not concept-appropriate ones
            procedural_gerunds = [
                'installing', 'configuring', 'deploying', 'creating', 'setting up',
                'building', 'developing', 'implementing', 'managing', 'troubleshooting'
            ]
            
            words = title_lower.split()
            bad_gerunds = [word for word in words if any(word.startswith(pg) for pg in procedural_gerunds)]
            
            if bad_gerunds:
                issues.append({
                    'type': 'title_format', 
                    'level': 'WARN',
                    'message': f'Title "{title}" uses procedural gerund inappropriate for concepts',
                    'flagged_text': title,
                    'line_number': 1,
                    'span': (0, len(title)),
                    'suggestions': [
                        f'Use "Understanding {title[len(bad_gerunds[0]):].strip()}" instead',
                        f'Or use "About {title[len(bad_gerunds[0]):].strip()}"',
                        'Concept titles should use "Understanding", "About", or "What is"',
                        'Procedural titles belong in procedure modules'
                    ]
                })
        
        if title.endswith('?'):
            issues.append({
                'type': 'title_format',
                'level': 'WARN', 
                'message': f'Title "{title}" is question-style, not appropriate for concepts',
                'flagged_text': title,
                'line_number': 1,
                'span': (0, len(title)),
                'suggestions': [
                    'Use a declarative noun phrase instead of a question',
                    'Convert question to statement form',
                    'Questions are better suited for procedure or troubleshooting topics'
                ]
            })
        
        return issues
    
    def _find_improvement_opportunities(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        issues = []
        word_count = structure.get('word_count', 0)
        
        if word_count > self.thresholds.get('long_content_words', 400) and len(structure.get('images', [])) == 0:
            issues.append({
                'type': 'improvement_suggestion',
                'level': 'INFO',
                'message': f"Long module ({word_count} words) lacks diagrams or images",
                'flagged_text': "Missing visual elements",
                'line_number': 0,
                'span': (0, 0),
                'suggestions': [
                    "Add diagrams to illustrate complex concepts",
                    "Include screenshots if relevant to the concept",
                    "Use flowcharts or process diagrams for multi-step concepts"
                ]
            })
        
        if (word_count > self.thresholds.get('very_long_content_words', 500) and 
            len(structure.get('sections', [])) <= 1):
            issues.append({
                'type': 'improvement_suggestion',
                'level': 'INFO',
                'message': f"Long module ({word_count} words) lacks subheadings",
                'flagged_text': "Missing structural organization",
                'line_number': 0,
                'span': (0, 0),
                'suggestions': [
                    "Add subheadings to organize the content into logical sections",
                    "Break up long paragraphs into smaller, focused sections",
                    "Use heading hierarchy (==, ===) to structure the information"
                ]
            })
        
        return issues
    
    def _starts_with_imperative(self, text: str) -> bool:
        words = text.lower().split()
        if not words:
            return False
        return words[0].strip('.,!?:;') in self.imperative_verbs
    
    def _detect_assembly_pattern(self, structure: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
        issues = []
        assembly_indicators = []
        
        if len(structure.get('tables', [])) > 0:
            table_cells = structure.get('table_cells', [])
            workflow_keywords = ['step', 'phase', 'stage', 'install', 'configure', 'deploy', 'create', 'update', 'manage']
            workflow_count = sum(1 for cell in table_cells if any(keyword in cell['text'].lower() for keyword in workflow_keywords))
            
            if workflow_count >= 3:
                assembly_indicators.append('workflow_table')
        
        major_sections = [s for s in structure.get('sections', []) if s.get('level', 0) == 2]
        if len(major_sections) >= 4:
            assembly_indicators.append('multiple_sections')
        
        user_story_patterns = [
            r'as a[n]?\s+\w+',  # "As a user/admin/developer"
            r'i want to\s+\w+',  # "I want to configure"
            r'so that\s+\w+',   # "so that it works"
            r'user\s+story',
            r'user\s+goal',
            r'workflow',
            r'development\s+workflow',
            r'process',
            r'lifecycle'
        ]
        
        user_story_matches = sum(1 for pattern in user_story_patterns if re.search(pattern, text.lower()))
        if user_story_matches >= 2:
            assembly_indicators.append('user_story_language')
        
        has_conceptual = len(structure.get('introduction_paragraphs', [])) > 0
        has_procedural = any(self._starts_with_imperative(cell.get('text', '')) for cell in structure.get('table_cells', []))
        has_reference = len(structure.get('tables', [])) > 0
        
        mixed_count = sum([has_conceptual, has_procedural, has_reference])
        if mixed_count >= 2:
            assembly_indicators.append('mixed_content_types')
        
        if len(assembly_indicators) >= 2:
            issues.append({
                'type': 'structural_recommendation',
                'level': 'WARN',
                'message': f"Content structure suggests this should be an assembly, not a concept module",
                'flagged_text': f"Assembly pattern detected: {', '.join(assembly_indicators)}",
                'line_number': 0,
                'span': (0, 0),
                'suggestions': [
                    "Consider restructuring as an assembly that includes multiple modules",
                    "Per Red Hat: 'Each assembly documents a user story' (https://redhat-documentation.github.io/modular-docs/#what-modular-documentation-is)",
                    "Break content into separate concept, procedure, and reference modules",
                    "Create an assembly file that includes these modules",
                    f"Indicators: {', '.join(assembly_indicators)}"
                ]
            })
        
        return issues
    
    def _detect_module_nesting(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect if module contains other modules (antipattern per Red Hat 2021).
        
        Per Red Hat June 2021: "A module should not contain another module."
        However: "a module can contain a text snippet"
        
        Enhanced snippet detection per June 2021 guidelines.
        """
        issues = []
        
        # Find all include directives
        all_includes = re.findall(r'include::([^[\]]+\.adoc)', text, re.IGNORECASE)
        
        if not all_includes:
            return issues
        
        # Expanded allowed snippet patterns per Red Hat conventions
        snippet_patterns = [
            r'snippets?/',           # snippets/ or snippet/ directory
            r'_snip[^/]*\.adoc$',    # *_snip*.adoc files
            r'snp_',                 # snp_ prefix (common convention)
            r'_attributes',          # attribute files
            r'_variables',           # variable files
            r'_common',              # common content files
            r'shared/',              # shared content directory
            r'partials/',            # partials directory
            r'includes/',            # includes directory (for shared content)
        ]
        
        # Module patterns that indicate actual modules (not snippets)
        module_patterns = [
            r'con_[^/]*\.adoc$',           # con_ prefix
            r'proc_[^/]*\.adoc$',          # proc_ prefix
            r'ref_[^/]*\.adoc$',           # ref_ prefix
            r'assembly_[^/]*\.adoc$',      # assembly_ prefix
            r'/modules/[^/]+\.adoc$',      # modules/ directory
        ]
        
        module_includes = []
        for inc in all_includes:
            inc_lower = inc.lower()
            
            # First check if it's explicitly a snippet (allow these)
            is_snippet = any(re.search(pat, inc_lower) for pat in snippet_patterns)
            if is_snippet:
                continue
            
            # Then check if it matches module patterns (flag these)
            is_module = any(re.search(pat, inc_lower) for pat in module_patterns)
            if is_module:
                module_includes.append(inc)
        
        if module_includes:
            # Find line numbers for the includes
            first_include_line = 0
            for i, line in enumerate(text.split('\n'), 1):
                if module_includes[0] in line:
                    first_include_line = i
                    break
            
            issues.append({
                'type': 'module_nesting_antipattern',
                'level': 'FAIL',
                'message': f"Module contains {len(module_includes)} other module(s) via include directives",
                'flagged_text': f"Module nesting detected: {len(module_includes)} includes",
                'line_number': first_include_line,
                'span': (0, 0),
                'suggestions': [
                    "Per Red Hat 2021: 'A module should not contain another module'",
                    "Move this content to an assembly file (assembly_*.adoc)",
                    "Assemblies are designed to include multiple modules",
                    "Text snippets (snippets/, _snip*, partials/) are allowed",
                    f"Found module includes: {', '.join(module_includes[:3])}{'...' if len(module_includes) > 3 else ''}",
                    "See: https://redhat-documentation.github.io/modular-docs/#creating-modules"
                ]
            })
        
        return issues
    
    def _validate_heading_case(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
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
                        "Per Red Hat 2022: Use sentence case for headings",
                        "Capitalize only: first word, proper nouns, and acronyms",
                        "See: https://redhat-documentation.github.io/modular-docs/#whats-new"
                    ]
                })
        
        return issues
    
    def _is_proper_noun(self, word: str) -> bool:
        proper_nouns = {
            'red', 'hat', 'linux', 'kubernetes', 'openshift', 'ansible', 'docker',
            'python', 'java', 'javascript', 'api', 'rest', 'http', 'https', 'ssh',
            'tcp', 'ip', 'dns', 'url', 'uri', 'json', 'xml', 'yaml', 'html', 'css'
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
