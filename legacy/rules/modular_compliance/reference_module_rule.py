"""Reference Module Rule - validates reference modules per Red Hat modular documentation guidelines."""
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
    
    def __init__(self):
        super().__init__()
        self.rule_type = "reference_module"
        self.rule_subtype = "reference_module"
        self.parser = ModularStructureBridge()
        self._load_config()
    
    def _get_rule_type(self) -> str:
        return "reference_module"
    
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
                self.evidence_scoring = config.get('evidence_scoring', {})
                self.module_types = config.get('module_types', {})
                
            except Exception:
                self._set_fallback_config()
        else:
            self._set_fallback_config()
    
    def _set_fallback_config(self):
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
        
        # Only analyze if this is a reference module
        if content_type and content_type != 'reference':
            return errors
            
        structure = self.parser.parse(text)
        
        compliance_issues = []
        
        compliance_issues.extend(self._validate_metadata(text))
        compliance_issues.extend(self._validate_deprecated_discrete_tag(text))
        compliance_issues.extend(self._validate_anchor_prefixes(text))
        compliance_issues.extend(self._validate_attribute_position(text))
        compliance_issues.extend(self._find_introduction_issues(structure, text))
        compliance_issues.extend(self._validate_introduction_quality(structure))
        compliance_issues.extend(self._find_structured_data_issues(structure, text))
        compliance_issues.extend(self._find_organization_issues(structure))
        compliance_issues.extend(self._find_structure_issues(structure))
        compliance_issues.extend(self._find_procedural_content_issues(structure, text))
        compliance_issues.extend(self._find_explanatory_content_issues(structure, text))
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
                    "Change ':_content-type:' to ':_mod-docs-content-type:' per Red Hat Aug 2023",
                    "Update: :_mod-docs-content-type: REFERENCE"
                ]
            })

        return issues
    
    def _validate_deprecated_discrete_tag(self, text: str) -> List[Dict[str, Any]]:
        """
        Flag deprecated [discrete] tag per Red Hat Oct 2025 update.
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
            (r'^this\s+(section|module|reference|topic)\s+', 
             "Introduction starts with 'This section/module...'"),
            (r'^the\s+following\s+(table|list|section)',
             "Introduction starts with 'The following...'"),
            (r'^in\s+this\s+(section|module|reference)',
             "Introduction starts with 'In this section/module...'"),
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
                        "Start with what reference information is provided",
                        "Describe when users would consult this reference",
                        "See Red Hat SSG: Short descriptions guidelines"
                    ]
                })
                break
        
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
                        "Per Red Hat 2022: Use sentence case for headings"
                    ]
                })
        
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
    
    def _find_introduction_issues(self, structure: Dict[str, Any], text: str = "") -> List[Dict[str, Any]]:
        """
        Validate introduction per Red Hat guidelines for reference modules.
        
        Per Red Hat: Reference modules require a short introduction (single paragraph).
        If parser can't extract intro_paragraphs but document has content, assume it's present.
        """
        issues = []
        intro_paragraphs = structure.get('introduction_paragraphs', [])
        
        # Try manual extraction if parser didn't get it
        if not intro_paragraphs and text:
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
                    if current_para:
                        paragraphs_after_title.append(' '.join(current_para))
                    break
            
            if current_para:
                paragraphs_after_title.append(' '.join(current_para))
            
            intro_paragraphs = paragraphs_after_title
        
        # If still no intro but document has content (>15 words), assume it's present
        if not intro_paragraphs:
            word_count = structure.get('word_count', 0)
            has_content = structure.get('has_content', False)
            
            if has_content and word_count >= 15:
                return issues
        
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
        elif len(intro_paragraphs) > 1:
            # Check total word count - if intro is concise despite multiple paragraphs, it's acceptable
            total_intro_words = sum(len(p.split()) for p in intro_paragraphs)
            if total_intro_words > 100:  # Only warn if intro is long AND multi-paragraph
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
        issues = []
        
        has_tables = len(structure.get('tables', [])) > 0
        has_lists = len(structure.get('ordered_lists', [])) + len(structure.get('unordered_lists', [])) > 0
        has_dlists = self._has_definition_lists(text)
        
        if not has_tables and text and '|===' in text:
            has_tables = True
        if not has_lists and text:
            if re.search(r'^\d+\.\s+|^\*\s+|^-\s+', text, re.MULTILINE):
                has_lists = True
        
        if not (has_tables or has_lists or has_dlists):
            total_words = structure.get('word_count', 0) or len(text.split())
            
            if total_words > 30:
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
                        "Use definition lists (Term::) for terminology or parameters"
                    ]
                })
        
        return issues
    
    def _has_definition_lists(self, text: str) -> bool:
        """
        Check if text contains AsciiDoc definition lists.
        
        Definition lists use the format:
        - term:: description (standard)
        - term::: description (nested)
        - term;; description (alternative)
        """
        if not text:
            return False
        
        # Pattern: term followed by ::, :::, or ;; and then content
        dlist_patterns = [
            r'^[^\n]+::+\s+',      # term:: description
            r'^[^\n]+;;+\s+',      # term;; description (alternative syntax)
        ]
        
        for pattern in dlist_patterns:
            if re.search(pattern, text, re.MULTILINE):
                return True
        
        return False
    
    def _find_organization_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        issues = []
        
        for list_data in structure.get('unordered_lists', []):
            if len(list_data['items']) > 10:
                item_texts = [item['text'].lower() for item in list_data['items']]
                
                if self._could_be_alphabetized(item_texts):
                    issues.append({
                        'type': 'data_organization',
                        'level': 'INFO',
                        'message': "Large list may benefit from alphabetical organization",
                        'flagged_text': "List organization",
                        'line_number': list_data['start_line'],
                        'span': (0, 0),
                        'suggestions': [
                            "Consider alphabetizing list items for easier lookup"
                        ]
                    })
        
        return issues
    
    def _find_structure_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        issues = []
        word_count = structure.get('word_count', 0)
        
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
        issues = []
        procedural_items = []
        
        ordered_lists = structure.get('ordered_lists', [])
        
        if not ordered_lists and text:
            import re
            numbered_patterns = re.findall(r'^\d+\.\s+(.+)', text, re.MULTILINE)
            if numbered_patterns:
                mock_items = [{'text': pattern} for pattern in numbered_patterns]
                ordered_lists = [{'items': mock_items, 'start_line': 0}]
        
        for list_data in ordered_lists:
            imperative_count = sum(1 for item in list_data['items'] if self._starts_with_action(item['text']))
            
            if imperative_count >= 2:
                for item in list_data['items']:
                    procedural_items.append({
                        'text': item['text'],
                        'source': 'ordered_list'
                    })
            else:
                for item in list_data['items']:
                    if self._is_procedural_content(item['text']):
                        procedural_items.append({
                            'text': item['text'],
                            'source': 'ordered_list'
                        })
        
        for list_data in structure.get('unordered_lists', []):
            for item in list_data['items']:
                if self._is_procedural_content(item['text']):
                    procedural_items.append({
                        'text': item['text'],
                        'source': 'unordered_list'
                    })
        
        for cell in structure.get('table_cells', []):
            if self._is_procedural_content(cell['text']):
                procedural_items.append({
                    'text': cell['text'],
                    'source': 'table_cell'
                })
        
        if len(procedural_items) >= 2:
            sources = {}
            for item in procedural_items:
                source = item.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            
            source_desc = ", ".join([f"{count} in {src.replace('_', ' ')}s" for src, count in sources.items()])
            
            issues.append({
                'type': 'prohibited_content',
                'level': 'FAIL',
                'message': f"Module contains {len(procedural_items)} procedural steps ({source_desc})",
                'flagged_text': f"Procedural steps detected: {len(procedural_items)} steps",
                'line_number': 0,
                'span': (0, 0),
                'suggestions': [
                    "Move step-by-step instructions to a procedure module",
                    "Convert procedural content to reference information"
                ]
            })
        
        return issues
    
    def _find_explanatory_content_issues(self, structure: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
        issues = []
        
        explanatory_indicators = [
            'philosophy', 'design philosophy', 'principles', 'approach', 'concept',
            'understanding', 'explanation', 'describes', 'overview', 'background',
            'theory', 'fundamentals', 'key concept', 'important to remember',
            'restful principles', 'consistency is a key concept', 'simplifies integration',
            'improves the overall', 'developer experience'
        ]
        
        content_lower = text.lower()
        explanatory_score = sum(1 for indicator in explanatory_indicators if indicator in content_lower)
        
        conceptual_patterns = [
            r'it\'?s important to (understand|remember|know)',
            r'the (philosophy|principle|concept|approach) behind',
            r'this (approach|philosophy|design) (simplifies|improves|ensures)',
            r'we follow.*principles.*which means',
            r'this consistency is.*that allows',
            r'(allows|enables) developers to.*without.*proprietary'
        ]
        
        pattern_matches = sum(1 for pattern in conceptual_patterns if re.search(pattern, content_lower))
        long_intro_paras = [para for para in structure.get('introduction_paragraphs', []) if len(para.split()) > 50]
        
        paragraphs = text.split('\n\n')
        explanatory_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if len(para.split()) > 30:
                para_lower = para.lower()
                if any(indicator in para_lower for indicator in explanatory_indicators[:5]):
                    explanatory_paragraphs.append(para)
        
        if (explanatory_score >= 3 or pattern_matches >= 1 or 
            len(explanatory_paragraphs) >= 2 or len(long_intro_paras) > 0):
            
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
        command_like = sum(1 for text in item_texts if any(
            text.startswith(prefix) for prefix in ['--', '-', 'get', 'set', 'list', 'create', 'delete']
        ))
        
        if command_like > len(item_texts) * 0.5:
            sorted_texts = sorted(item_texts)
            misplaced = sum(1 for i, text in enumerate(item_texts) 
                          if i < len(sorted_texts) and text != sorted_texts[i])
            return misplaced > len(item_texts) * 0.3
        
        return False
    
    def _starts_with_action(self, text: str) -> bool:
        words = text.lower().split()
        if not words:
            return False
        return words[0].strip('.,!?:;') in self.imperative_verbs
    
    def _is_procedural_content(self, text: str) -> bool:
        text_lower = text.lower().strip()
        
        # Descriptive reference lists: "command - Description" are allowed
        # Pattern: "verb - description" or "verb: description"
        if re.match(r'^\w+\s*[-:]\s+\w+', text_lower):
            return False
        
        # Direct imperative at start with sequential indicator
        if self._starts_with_action(text):
            sequence_words = ['first', 'then', 'next', 'finally', 'after']
            if any(word in text_lower for word in sequence_words):
                return True
            # Standalone imperative in reference is likely procedural
            if len(text.split()) > 5:
                return True
        
        # Explicit procedural patterns
        procedural_patterns = [
            r'\bfollow\s+these\s+steps\b',
            r'\bstep\s+\d+\b',
            r'\bthen\b.*?\b(run|execute)\b',
            r'\bnext\b.*?\bstep\b'
        ]
        
        for pattern in procedural_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def _has_excessive_prose_before_data(self, structure: Dict[str, Any], text: str = "") -> bool:
        intro_words = sum(len(para.split()) for para in structure.get('introduction_paragraphs', []))
        
        if intro_words == 0 and text:
            lines = text.split('\n')
            words_before_structure = 0
            found_title = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('= ') and not found_title:
                    found_title = True
                    continue
                elif found_title and (line.startswith('|') or (line and line[0].isdigit() and '.' in line)):
                    break
                elif found_title and line:
                    words_before_structure += len(line.split())
            
            intro_words = words_before_structure
        
        total_words = structure.get('word_count', 0) or len(text.split())
        sections = structure.get('sections', [])
        early_prose_sections = len([s for s in sections if s.get('level', 0) > 0])
        
        return (
            intro_words > 120 or
            early_prose_sections > 2 or
            (total_words > 250 and intro_words > total_words * 0.35)
        )
    
