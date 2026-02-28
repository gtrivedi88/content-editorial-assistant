"""
Modular Base Rule - Shared validation utilities for all modular compliance rules.

This base class provides common validation methods used across concept, procedure,
reference, and assembly module rules, per Red Hat Modular Documentation guidelines.

Updates tracked:
- Oct 2025: [discrete] tag deprecated
- Apr 2025: Limitations section removed from procedures
- May 2023: Module prefixes (con_, proc_, ref_) removed from anchors
- Jan 2024: [role="_abstract"] tag removed
- Aug 2023: Content type attribute renamed to :_mod-docs-content-type:
- Sept 2022: Assembly title guidelines added
- Apr 2022: Sentence case for headings
- June 2021: Modules should not contain other modules (snippets allowed)
"""
import re
import os
from typing import List, Optional, Dict, Any
from rules.base_rule import BaseRule

try:
    import yaml
except ImportError:
    yaml = None


class ModularBaseRule(BaseRule):
    """
    Base class for modular documentation compliance rules.
    
    Provides shared validation methods for:
    - Deprecated features ([discrete], anchor prefixes, [role="_abstract"])
    - Attribute position validation
    - Introduction quality checks per Red Hat SSG
    - Snippet vs module detection
    - Heading case validation
    """
    
    def __init__(self):
        super().__init__()
        self._load_shared_config()
    
    def _load_shared_config(self):
        """Load shared configuration for modular compliance."""
        config_path = os.path.join(
            os.path.dirname(__file__), 
            'config', 
            'modular_compliance_types.yaml'
        )
        
        # Default configuration
        self.deprecated_anchor_prefixes = ['con_', 'proc_', 'ref_']
        self.allowed_snippet_patterns = [
            r'snippets?/',
            r'_snip[^/]*\.adoc$',
            r'snp_',
            r'_attributes',
            r'_variables',
            r'_common',
            r'shared/',
            r'partials/',
            r'includes/',
        ]
        self.module_include_patterns = [
            r'con_[^/]*\.adoc$',
            r'proc_[^/]*\.adoc$',
            r'ref_[^/]*\.adoc$',
            r'assembly_[^/]*\.adoc$',
            r'/modules/[^/]+\.adoc$',
        ]
        
        if yaml and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    
                # Load deprecated features config
                deprecated = config.get('deprecated_features', {})
                anchor_config = deprecated.get('anchor_prefixes', {})
                self.deprecated_anchor_prefixes = anchor_config.get(
                    'prefixes', self.deprecated_anchor_prefixes
                )
                
                # Load snippet patterns
                self.allowed_snippet_patterns = config.get(
                    'allowed_snippet_patterns', self.allowed_snippet_patterns
                )
                    
            except (yaml.YAMLError, OSError, ValueError):
                pass  # Use defaults
    
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
    
    def _validate_introduction_quality_base(
        self, 
        intro_text: str, 
        module_type: str = 'module'
    ) -> List[Dict[str, Any]]:
        """
        Validate introduction quality per Red Hat SSG guidelines.
        
        Per Red Hat Supplementary Style Guide:
        - Don't start with "This section/module..."
        - Don't start with "The following..."
        - Don't repeat the title verbatim
        - Should explain WHAT and WHY
        
        Args:
            intro_text: The introduction paragraph text
            module_type: Type of module for context-specific messages
            
        Returns:
            List of issues found
        """
        issues = []
        
        if not intro_text:
            return issues
        
        intro_lower = intro_text.lower().strip()
        
        # Generic anti-patterns applicable to all module types
        antipatterns = [
            (r'^this\s+(section|module|chapter|document|topic|assembly|procedure|reference)\s+', 
             f"Introduction starts with 'This {module_type}...'"),
            (r'^the\s+following\s+',
             "Introduction starts with 'The following...'"),
            (r'^in\s+this\s+(section|module|chapter|assembly|procedure|reference)',
             "Introduction starts with 'In this...'"),
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
    
    def _detect_module_includes(self, text: str) -> List[str]:
        """
        Detect module include directives (as opposed to snippet includes).
        
        Per Red Hat June 2021: Modules should not contain other modules,
        but can contain text snippets.
        
        Args:
            text: Document text to analyze
            
        Returns:
            List of detected module include paths
        """
        # Find all include directives
        all_includes = re.findall(r'include::([^[\]]+\.adoc)', text, re.IGNORECASE)
        
        if not all_includes:
            return []
        
        module_includes = []
        for inc in all_includes:
            inc_lower = inc.lower()
            
            # Check if it's explicitly a snippet (allow these)
            is_snippet = any(
                re.search(pat, inc_lower) for pat in self.allowed_snippet_patterns
            )
            if is_snippet:
                continue
            
            # Check if it matches module patterns (flag these)
            is_module = any(
                re.search(pat, inc_lower) for pat in self.module_include_patterns
            )
            if is_module:
                module_includes.append(inc)
        
        return module_includes
    
    def _validate_heading_case_base(
        self, 
        sections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate heading case per Red Hat April 2022 update (sentence case).
        
        Args:
            sections: List of section dictionaries with 'title', 'level', etc.
            
        Returns:
            List of issues for headings using title case instead of sentence case
        """
        issues = []
        
        # Words that should remain lowercase (unless first word)
        short_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 
            'to', 'for', 'of', 'with', 'by', 'as', 'is', 'if'
        }
        
        # Known proper nouns and acronyms (always capitalized)
        proper_nouns = {
            'red', 'hat', 'linux', 'kubernetes', 'openshift', 'ansible', 
            'docker', 'python', 'java', 'javascript', 'api', 'rest', 
            'http', 'https', 'ssh', 'tcp', 'ip', 'dns', 'url', 'uri', 
            'json', 'xml', 'yaml', 'html', 'css', 'aws', 'azure', 'gcp'
        }
        
        for section in sections:
            heading = section.get('title', '')
            if not heading or section.get('level', 0) == 0:
                continue
            
            words = heading.split()
            if len(words) < 2:
                continue
            
            capitalized_count = 0
            
            for i, word in enumerate(words[1:], start=1):
                clean_word = word.strip('.,!?:;()[]{}')
                if not clean_word:
                    continue
                
                # Check if word is capitalized when it shouldn't be
                if clean_word[0].isupper() and clean_word.lower() not in short_words:
                    # Skip if it's a proper noun or all caps (acronym)
                    if not (clean_word.isupper() or clean_word.lower() in proper_nouns):
                        capitalized_count += 1
            
            # Flag if 2+ words are incorrectly capitalized
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
                        "Per Red Hat Apr 2022: Use sentence case for headings",
                        "Capitalize only: first word, proper nouns, and acronyms"
                    ]
                })
        
        return issues
    
    def _to_sentence_case(self, heading: str) -> str:
        """Convert heading to sentence case."""
        words = heading.split()
        if not words:
            return heading
        
        short_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 
            'to', 'for', 'of', 'with', 'by', 'as', 'is', 'if'
        }
        proper_nouns = {
            'red', 'hat', 'linux', 'kubernetes', 'openshift', 'ansible', 
            'docker', 'python', 'java', 'javascript', 'api', 'rest', 
            'http', 'https', 'ssh', 'tcp', 'ip', 'dns', 'url', 'uri', 
            'json', 'xml', 'yaml', 'html', 'css', 'aws', 'azure', 'gcp'
        }
        
        result = [words[0]]  # Keep first word as-is
        
        for word in words[1:]:
            clean_word = word.strip('.,!?:;()[]{}')
            if clean_word.isupper() or clean_word.lower() in proper_nouns:
                result.append(word)
            elif clean_word.lower() in short_words:
                result.append(clean_word.lower())
            else:
                result.append(clean_word.lower())
        
        return ' '.join(result)
    
    def _is_proper_noun(self, word: str) -> bool:
        """Check if word is a known proper noun or technical term."""
        proper_nouns = {
            'red', 'hat', 'linux', 'kubernetes', 'openshift', 'ansible', 
            'docker', 'python', 'java', 'javascript', 'api', 'rest', 
            'http', 'https', 'ssh', 'tcp', 'ip', 'dns', 'url', 'uri', 
            'json', 'xml', 'yaml', 'html', 'css', 'aws', 'azure', 'gcp'
        }
        return word.lower() in proper_nouns
    
    def _detect_content_type_from_metadata(self, text: str) -> Optional[str]:
        """
        Detect content type from document metadata attributes.
        
        Looks for:
        - :_mod-docs-content-type: PROCEDURE|CONCEPT|REFERENCE|ASSEMBLY
        - :_content-type: (deprecated but still supported)
        
        Returns lowercase type or None if not found.
        """
        # Check for new-style attribute
        new_style = re.search(
            r':_mod-docs-content-type:\s*(PROCEDURE|CONCEPT|REFERENCE|ASSEMBLY)', 
            text, 
            re.IGNORECASE
        )
        if new_style:
            return new_style.group(1).lower()
        
        # Check for old-style attribute (deprecated but still supported)
        old_style = re.search(
            r':_content-type:\s*(PROCEDURE|CONCEPT|REFERENCE|ASSEMBLY)', 
            text, 
            re.IGNORECASE
        )
        if old_style:
            return old_style.group(1).lower()
        
        return None
    
    def _validate_metadata_common(self, text: str) -> List[Dict[str, Any]]:
        """
        Validate common metadata issues across all module types.

        Checks for:
        - Deprecated :_content-type: attribute (Aug 2023)
        """
        issues = []

        has_new_attr = ':_mod-docs-content-type:' in text
        has_old_attr = ':_content-type:' in text and not has_new_attr

        if has_old_attr:
            # Find line number
            line_number = 0
            for i, line in enumerate(text.split('\n'), 1):
                if ':_content-type:' in line:
                    line_number = i
                    break

            issues.append({
                'type': 'metadata_format',
                'level': 'WARN',
                'message': "Using deprecated content type attribute ':_content-type:'",
                'flagged_text': ':_content-type:',
                'line_number': line_number,
                'span': (0, 0),
                'suggestions': [
                    "Change ':_content-type:' to ':_mod-docs-content-type:' per Red Hat Aug 2023",
                    "See: https://redhat-documentation.github.io/modular-docs/#whats-new"
                ]
            })

        return issues

