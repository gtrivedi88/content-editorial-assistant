"""
Cross-Reference Rule for Advanced Modular Compliance
Validates xref links, inter-module references, and cross-reference best practices.
"""
import re
import os
from typing import List, Optional, Dict, Any, Set, Tuple
from rules.base_rule import BaseRule
from .modular_structure_bridge import ModularStructureBridge
try:
    import yaml
except ImportError:
    yaml = None


class CrossReferenceRule(BaseRule):
    """Advanced cross-reference validation for modular documentation"""
    
    def __init__(self):
        super().__init__()
        self.rule_type = "cross_reference_compliance"
        self.rule_subtype = "xref_validation"
        self.parser = ModularStructureBridge()
        
        # Cross-reference patterns
        self.xref_pattern = re.compile(r'xref:([^[\]]+)(?:\[([^\]]*)\])?', re.IGNORECASE)
        self.internal_link_pattern = re.compile(r'<<([^,>]+)(?:,([^>]*))?>>', re.IGNORECASE)
        self.anchor_pattern = re.compile(r'\[\[([^\]]+)\]\]', re.IGNORECASE)
        self.section_anchor_pattern = re.compile(r'^=+\s+.*?\[\[([^\]]+)\]\]', re.MULTILINE)
        
        # Load configuration
        self._load_config()
    
    def _get_rule_type(self) -> str:
        """Return the rule type for BaseRule compatibility."""
        return "cross_reference_compliance"
        
    def _load_config(self):
        """Load cross-reference validation configuration."""
        config_path = os.path.join(
            os.path.dirname(__file__), 
            'config', 
            'cross_reference_types.yaml'
        )
        
        # Default configuration
        self.valid_file_extensions = ['.adoc', '.asciidoc']
        self.required_anchor_naming = r'^[a-z][a-z0-9_-]*[a-z0-9]$'
        self.max_xref_depth = 3  # Maximum levels of cross-references
        
        if yaml and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    self.valid_file_extensions = config.get('valid_file_extensions', self.valid_file_extensions)
                    self.required_anchor_naming = config.get('required_anchor_naming', self.required_anchor_naming)
                    self.max_xref_depth = config.get('max_xref_depth', self.max_xref_depth)
            except Exception:
                pass  # Use defaults
    
    def analyze(self, text: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Analyze cross-references in modular documentation.
        
        Args:
            text: Document text to analyze
            context: Analysis context including module type and file path
            
        Returns:
            List of cross-reference compliance issues
        """
        if not text or not text.strip():
            return []
        
        errors = []
        context = context or {}
        
        try:
            # Parse document structure
            structure = self.parser.parse(text)
            
            # Extract all cross-references
            xrefs = self._extract_cross_references(text)
            internal_links = self._extract_internal_links(text)
            anchors = self._extract_anchors(text)
            
            # Validate cross-references
            errors.extend(self._validate_xref_format(xrefs, text, context))
            errors.extend(self._validate_internal_links(internal_links, anchors, text, context))
            errors.extend(self._validate_anchor_naming(anchors, text, context))
            errors.extend(self._check_broken_references(xrefs, internal_links, text, context))
            errors.extend(self._check_circular_references(xrefs, text, context))
            errors.extend(self._validate_reference_context(xrefs, structure, text, context))
            
        except Exception as e:
            # Graceful degradation - create low-confidence error
            errors.append(self._create_error(
                text[:50],  # sentence (first 50 chars)
                0,  # sentence_index
                "Cross-reference analysis failed due to parsing error",  # message
                [f"Unable to analyze cross-references: {str(e)}"],  # suggestions
                severity="low",
                text=text,
                context=context,
                confidence=0.2,
                error_type="xref_analysis_error"
            ))
        
        return errors
    
    def _extract_cross_references(self, text: str) -> List[Dict[str, Any]]:
        """Extract all xref links from text."""
        xrefs = []
        for match in self.xref_pattern.finditer(text):
            target = match.group(1).strip()
            label = match.group(2) if match.group(2) else None
            line_number = text[:match.start()].count('\n') + 1
            
            xrefs.append({
                'target': target,
                'label': label,
                'line_number': line_number,
                'full_match': match.group(0),
                'start_pos': match.start(),
                'end_pos': match.end()
            })
        
        return xrefs
    
    def _extract_internal_links(self, text: str) -> List[Dict[str, Any]]:
        """Extract all internal <<>> links from text."""
        links = []
        for match in self.internal_link_pattern.finditer(text):
            target = match.group(1).strip()
            label = match.group(2) if match.group(2) else None
            line_number = text[:match.start()].count('\n') + 1
            
            links.append({
                'target': target,
                'label': label,
                'line_number': line_number,
                'full_match': match.group(0),
                'start_pos': match.start(),
                'end_pos': match.end()
            })
        
        return links
    
    def _extract_anchors(self, text: str) -> Set[str]:
        """Extract all anchor definitions from text."""
        anchors = set()
        
        # Extract [[anchor]] style anchors
        for match in self.anchor_pattern.finditer(text):
            anchors.add(match.group(1).strip())
        
        # Extract section anchors
        for match in self.section_anchor_pattern.finditer(text):
            anchors.add(match.group(1).strip())
        
        return anchors
    
    def _validate_xref_format(self, xrefs: List[Dict[str, Any]], text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate xref link format and syntax."""
        errors = []
        
        for xref in xrefs:
            target = xref['target']
            
            # Check for valid file extension in external references
            if '#' in target:
                file_part = target.split('#')[0]
                if file_part and not any(file_part.endswith(ext) for ext in self.valid_file_extensions):
                    errors.append(self._create_error(
                        target,  # sentence
                        xref['line_number'],  # sentence_index
                        f"Invalid file extension in xref: {target}",  # message
                        [f"Use: xref:{file_part}.adoc#{target.split('#')[1] if '#' in target else ''}"],  # suggestions
                        severity="medium",
                        text=text,
                        context=context,
                        confidence=0.8,
                        error_type="invalid_xref_extension"
                    ))
            
            # Check for missing labels in external references
            if not xref['label'] and ('/' in target or '.' in target):
                errors.append(self._create_error(
                    target,  # sentence
                    xref['line_number'],  # sentence_index
                    f"Missing label in external xref: {target}",  # message
                    [f"Use: xref:{target}[descriptive label text]"],  # suggestions
                    severity="medium",
                    text=text,
                    context=context,
                    confidence=0.6,
                    error_type="missing_xref_label"
                ))
        
        return errors
    
    def _validate_internal_links(self, links: List[Dict[str, Any]], anchors: Set[str], text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate internal <<>> links against defined anchors."""
        errors = []
        
        for link in links:
            target = link['target']
            
            # Check if target anchor exists
            if target not in anchors:
                # Check for auto-generated section anchors (from headings)
                section_anchors = self._extract_section_ids_from_headings(text)
                if target not in section_anchors:
                    errors.append(self._create_error(
                        target,  # sentence
                        link['line_number'],  # sentence_index
                        f"Broken internal link: {target}",  # message
                        [f"Define the anchor: [[{target}]] or check spelling"],  # suggestions
                        severity="high",
                        text=text,
                        context=context,
                        confidence=0.9,
                        error_type="broken_internal_link"
                    ))
        
        return errors
    
    def _validate_anchor_naming(self, anchors: Set[str], text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate anchor naming conventions."""
        errors = []
        anchor_pattern = re.compile(self.required_anchor_naming)
        
        for anchor in anchors:
            if not anchor_pattern.match(anchor):
                # Find line number for this anchor
                anchor_match = re.search(rf'\[\[{re.escape(anchor)}\]\]', text)
                line_number = text[:anchor_match.start()].count('\n') + 1 if anchor_match else None
                
                errors.append(self._create_error(
                    anchor,  # sentence
                    line_number or 0,  # sentence_index
                    f"Invalid anchor naming: {anchor}",  # message
                    [f"Use: {self._suggest_anchor_name(anchor)}"],  # suggestions
                    severity="medium",
                    text=text,
                    context=context,
                    confidence=0.7,
                    error_type="invalid_anchor_naming"
                ))
        
        return errors
    
    def _check_broken_references(self, xrefs: List[Dict[str, Any]], internal_links: List[Dict[str, Any]], text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for potentially broken external references."""
        errors = []
        
        for xref in xrefs:
            target = xref['target']
            
            # Check for suspicious patterns
            if target.startswith('http'):
                errors.append(self._create_error(
                    target,  # sentence
                    xref['line_number'],  # sentence_index
                    f"HTTP URL in xref (should use link macro): {target}",  # message
                    [f"Use: link:{target}[link text]"],  # suggestions
                    severity="medium",
                    text=text,
                    context=context,
                    confidence=0.8,
                    error_type="http_in_xref"
                ))
            
            # Check for file extensions in fragment references
            if '#' in target and target.count('#') > 1:
                errors.append(self._create_error(
                    target,  # sentence
                    xref['line_number'],  # sentence_index
                    f"Multiple fragments in xref: {target}",  # message
                    ["Cross-references should have only one fragment identifier"],  # suggestions
                    severity="medium",
                    text=text,
                    context=context,
                    confidence=0.7,
                    error_type="multiple_fragments"
                ))
        
        return errors
    
    def _check_circular_references(self, xrefs: List[Dict[str, Any]], text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for potential circular reference patterns."""
        errors = []
        
        # This is a simplified check - in a real implementation, you'd track file dependencies
        current_file = context.get('file_path', '')
        if current_file:
            current_filename = os.path.basename(current_file)
            
            for xref in xrefs:
                target = xref['target']
                if '#' in target:
                    target_file = target.split('#')[0]
                    if target_file == current_filename:
                        errors.append(self._create_error(
                            target,  # sentence
                            xref['line_number'],  # sentence_index
                            f"Self-reference detected: {target}",  # message
                            [f"Use: <<{target.split('#')[1]}>> instead"],  # suggestions
                            severity="low",
                            text=text,
                            context=context,
                            confidence=0.5,
                            error_type="self_reference_xref"
                        ))
        
        return errors
    
    def _validate_reference_context(self, xrefs: List[Dict[str, Any]], structure: Dict[str, Any], text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate that references are contextually appropriate."""
        errors = []
        module_type = context.get('content_type', 'concept')
        
        for xref in xrefs:
            target = xref['target']
            
            # Check for procedure-specific references in concept modules
            if module_type == 'concept' and any(keyword in target.lower() for keyword in ['install', 'configure', 'setup', 'deploy']):
                errors.append(self._create_error(
                    target,  # sentence
                    xref['line_number'],  # sentence_index
                    f"Procedural reference in concept module: {target}",  # message
                    ["Consider if this reference fits the concept module purpose"],  # suggestions
                    severity="low",
                    text=text,
                    context=context,
                    confidence=0.4,
                    error_type="procedural_ref_in_concept"
                ))
        
        return errors
    
    def _extract_section_ids_from_headings(self, text: str) -> Set[str]:
        """Extract auto-generated section IDs from headings."""
        section_ids = set()
        heading_pattern = re.compile(r'^=+\s+(.+?)(?:\[\[([^\]]+)\]\])?$', re.MULTILINE)
        
        for match in heading_pattern.finditer(text):
            heading_text = match.group(1).strip()
            explicit_id = match.group(2)
            
            if explicit_id:
                section_ids.add(explicit_id)
            else:
                # Generate auto ID (simplified version of AsciiDoctor's algorithm)
                auto_id = self._generate_auto_section_id(heading_text)
                section_ids.add(auto_id)
        
        return section_ids
    
    def _generate_auto_section_id(self, heading_text: str) -> str:
        """Generate automatic section ID from heading text (simplified)."""
        # Remove markup and convert to lowercase
        clean_text = re.sub(r'[^\w\s-]', '', heading_text.lower())
        # Replace spaces with hyphens
        section_id = re.sub(r'\s+', '-', clean_text.strip())
        # Remove multiple consecutive hyphens
        section_id = re.sub(r'-+', '-', section_id)
        # Remove leading/trailing hyphens
        section_id = section_id.strip('-')
        
        return section_id or 'section'
    
    def _suggest_anchor_name(self, anchor: str) -> str:
        """Suggest a properly formatted anchor name."""
        # Convert to lowercase and replace invalid characters
        suggested = re.sub(r'[^a-z0-9_-]', '_', anchor.lower())
        # Remove multiple underscores
        suggested = re.sub(r'_+', '_', suggested)
        # Ensure it starts and ends with alphanumeric
        suggested = re.sub(r'^[_-]+|[_-]+$', '', suggested)
        
        return suggested or 'anchor'
