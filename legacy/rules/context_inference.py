"""
Context Inference Service
Provides contextual hints and inference for rules when document metadata is incomplete.

All rules can use this service to get robust context information with multiple fallbacks.
"""
import os
import yaml
from typing import Dict, Any, Optional, List

class ContextInferenceService:
    """
    Service that infers content type and context from multiple signals:
    1. Explicit document metadata (Option 1 - already fixed)
    2. YAML context hints (Option 2)
    3. Structural analysis (Option 3)
    """
    
    def __init__(self):
        self.context_hints = self._load_context_hints()
    
    def _load_context_hints(self) -> Dict[str, Any]:
        """Load context hints from rule_mappings.yaml"""
        try:
            yaml_path = os.path.join(os.path.dirname(__file__), 'rule_mappings.yaml')
            with open(yaml_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('block_context_hints', {})
        except Exception as e:
            print(f"Warning: Could not load context hints: {e}")
            return {}
    
    def infer_content_type(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Infer content type using multiple fallback strategies.
        
        Priority order:
        1. Explicit context['content_type'] (from Option 1)
        2. YAML hints based on block_type (Option 2)
        3. Structural inference from headings/titles (Option 3)
        
        Returns:
            str: Inferred content type (PROCEDURE, CONCEPT, REFERENCE) or None
        """
        if not context:
            return None
        
        # === PRIORITY 1: Explicit metadata (from Option 1) ===
        if 'content_type' in context and context['content_type']:
            return context['content_type'].upper()
        
        # === PRIORITY 2: YAML hints (Option 2) ===
        block_type = context.get('block_type', '')
        if block_type in self.context_hints:
            hints = self.context_hints[block_type]
            likely_types = hints.get('likely_content_types', [])
            if likely_types and len(likely_types) > 0:
                # Use the first (most likely) content type as fallback
                # But only if confidence is high
                prob = hints.get('procedural_probability', 0.5)
                if prob > 0.7 and 'PROCEDURE' in likely_types:
                    return 'PROCEDURE'
        
        # === PRIORITY 3: Structural inference (Option 3) ===
        inferred = self.infer_from_structure(context)
        if inferred:
            return inferred
        
        return None
    
    def infer_from_structure(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Option 3: Infer content type from document structure.
        
        Analyzes:
        - Current block title
        - Parent block titles
        - Document title
        - Heading keywords
        
        Returns:
            str: Inferred content type or None
        """
        if not context:
            return None
        
        # Collect all relevant titles for analysis
        titles_to_check = []
        
        if context.get('title'):
            titles_to_check.append(context['title'])
        
        if context.get('parent_title'):
            titles_to_check.append(context['parent_title'])
        
        if context.get('document_title'):
            titles_to_check.append(context['document_title'])
        
        if not titles_to_check:
            return None
        
        # Check for procedural keywords
        procedural_keywords = self._get_keywords_for_content_type('PROCEDURE')
        if self._contains_keywords(titles_to_check, procedural_keywords):
            return 'PROCEDURE'
        
        # Check for concept keywords
        concept_keywords = self._get_keywords_for_content_type('CONCEPT')
        if self._contains_keywords(titles_to_check, concept_keywords):
            return 'CONCEPT'
        
        # Check for reference keywords
        reference_keywords = self._get_keywords_for_content_type('REFERENCE')
        if self._contains_keywords(titles_to_check, reference_keywords):
            return 'REFERENCE'
        
        return None
    
    def is_in_procedural_section(self, context: Dict[str, Any]) -> bool:
        """
        Check if the block is within a procedural section.
        
        This is used by rules like ListsRule to decide whether to apply
        strict parallelism checking.
        
        Returns:
            bool: True if in procedural context
        """
        # Check explicit content type first
        content_type = context.get('content_type', '').upper()
        if content_type == 'PROCEDURE':
            return True
        
        # Check YAML hints for ordered lists
        block_type = context.get('block_type', '')
        if block_type == 'olist':
            # Ordered lists have high procedural probability
            return True
        
        # Check structural signals
        inferred = self.infer_from_structure(context)
        if inferred == 'PROCEDURE':
            return True
        
        # Check if under a troubleshooting heading
        if self.is_troubleshooting_section(context):
            return True
        
        return False
    
    def is_troubleshooting_section(self, context: Dict[str, Any]) -> bool:
        """
        Check if block is in a troubleshooting section.
        
        Troubleshooting sections have special handling - lists under them
        are naturally imperative and parallel by convention.
        """
        troubleshooting_keywords = [
            'troubleshooting', 'debugging', 'solving', 'fixing', 'resolving',
            'common problems', 'known issues', 'error resolution'
        ]
        
        titles = []
        if context.get('title'):
            titles.append(context['title'])
        if context.get('parent_title'):
            titles.append(context['parent_title'])
        
        return self._contains_keywords(titles, troubleshooting_keywords)
    
    def _get_keywords_for_content_type(self, content_type: str) -> List[str]:
        """Get keywords from YAML hints for a content type."""
        keywords = []
        
        # Map content types to their hint keys
        hint_keys = {
            'PROCEDURE': [
                'heading_with_procedure_keywords',
                'heading_with_troubleshooting_keywords',
                'heading_with_verification_keywords'
            ],
            'CONCEPT': ['heading_with_concept_keywords'],
            'REFERENCE': ['heading_with_reference_keywords']
        }
        
        for hint_key in hint_keys.get(content_type, []):
            if hint_key in self.context_hints:
                hint_keywords = self.context_hints[hint_key].get('keywords', [])
                keywords.extend(hint_keywords)
        
        return keywords
    
    def _contains_keywords(self, titles: List[str], keywords: List[str]) -> bool:
        """Check if any title contains any of the keywords."""
        for title in titles:
            if not title:
                continue
            title_lower = title.lower()
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    return True
        return False
    
    def get_procedural_probability(self, context: Dict[str, Any]) -> float:
        """
        Calculate the probability that this block is in procedural content.
        
        Returns:
            float: Probability from 0.0 to 1.0
        """
        # Explicit PROCEDURE content type = 1.0
        if context.get('content_type', '').upper() == 'PROCEDURE':
            return 1.0
        
        # Check YAML hints
        block_type = context.get('block_type', '')
        if block_type in self.context_hints:
            prob = self.context_hints[block_type].get('procedural_probability', 0.5)
            
            # Boost probability if structural inference also suggests procedural
            if self.infer_from_structure(context) == 'PROCEDURE':
                prob = min(1.0, prob + 0.2)
            
            return prob
        
        # Default to structural inference
        if self.infer_from_structure(context) == 'PROCEDURE':
            return 0.7
        
        return 0.3  # Default low probability


# Global singleton instance
_context_service = None

def get_context_inference_service() -> ContextInferenceService:
    """Get the global context inference service instance."""
    global _context_service
    if _context_service is None:
        _context_service = ContextInferenceService()
    return _context_service

