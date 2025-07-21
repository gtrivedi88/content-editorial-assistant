"""
Text Span Analyzer

Analyzes text spans in errors to detect overlaps, nested spans, and related text regions
that should be consolidated into single error messages.
"""

import re
from typing import List, Dict, Any, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class TextSpan:
    """Represents a text span with position information."""
    text: str
    start_pos: int
    end_pos: int
    sentence_index: int
    error_id: str  # Unique identifier for the associated error


@dataclass
class SpanGroup:
    """Represents a group of overlapping or related text spans."""
    spans: List[TextSpan]
    errors: List[Dict[str, Any]]
    dominant_span: TextSpan  # The span that should take precedence
    consolidation_type: str  # 'overlap', 'nested', 'adjacent', 'semantic'


class TextSpanAnalyzer:
    """
    Analyzes text spans in errors to identify consolidation opportunities.
    """
    
    def __init__(self):
        self.overlap_threshold = 0.3  # 30% overlap threshold for grouping
        self.adjacency_threshold = 5  # Characters distance for adjacent spans
        
    def analyze_spans(self, errors: List[Dict[str, Any]]) -> List[SpanGroup]:
        """
        Analyze errors to identify overlapping, nested, and related text spans.
        
        Args:
            errors: List of error dictionaries
            
        Returns:
            List of SpanGroup objects representing consolidation opportunities
        """
        # Extract text spans from errors
        spans = self._extract_spans(errors)
        
        # Group spans by sentence to limit comparison scope
        spans_by_sentence = self._group_spans_by_sentence(spans)
        
        # Find consolidation groups within each sentence
        all_groups = []
        for sentence_idx, sentence_spans in spans_by_sentence.items():
            sentence_groups = self._find_consolidation_groups(sentence_spans, errors)
            all_groups.extend(sentence_groups)
            
        return all_groups
    
    def _extract_spans(self, errors: List[Dict[str, Any]]) -> List[TextSpan]:
        """Extract text spans from error objects."""
        spans = []
        
        for i, error in enumerate(errors):
            # Try to find text span in error
            text_segment = self._get_text_segment(error)
            if not text_segment:
                continue
                
            sentence = error.get('sentence', '')
            sentence_index = error.get('sentence_index', 0)
            
            # Find position of text segment in sentence
            start_pos = sentence.lower().find(text_segment.lower())
            if start_pos >= 0:
                end_pos = start_pos + len(text_segment)
                spans.append(TextSpan(
                    text=text_segment,
                    start_pos=start_pos,
                    end_pos=end_pos,
                    sentence_index=sentence_index,
                    error_id=f"error_{i}"
                ))
                
        return spans
    
    def _get_text_segment(self, error: Dict[str, Any]) -> str:
        """Extract the problematic text segment from an error object."""
        # Look for various possible fields containing the problematic text
        for field in ['text_segment', 'segment', 'problematic_text', 'matched_text']:
            if field in error and error[field]:
                return str(error[field]).strip()
        
        # Try to extract from message using common patterns
        message = error.get('message', '')
        
        # Pattern: "Problematic X: 'text'"
        match = re.search(r"['\"](.*?)['\"]", message)
        if match:
            return match.group(1)
            
        # Pattern: "word 'text' is problematic"
        match = re.search(r"\b(\w+)\b.*(?:problematic|issue|error)", message.lower())
        if match:
            return match.group(1)
            
        return ""
    
    def _group_spans_by_sentence(self, spans: List[TextSpan]) -> Dict[int, List[TextSpan]]:
        """Group spans by sentence index."""
        groups = defaultdict(list)
        for span in spans:
            groups[span.sentence_index].append(span)
        return dict(groups)
    
    def _find_consolidation_groups(self, spans: List[TextSpan], 
                                 all_errors: List[Dict[str, Any]]) -> List[SpanGroup]:
        """Find consolidation groups within a sentence's spans."""
        if len(spans) <= 1:
            return []
            
        groups = []
        processed_spans = set()
        
        for i, span1 in enumerate(spans):
            if span1.error_id in processed_spans:
                continue
                
            group_spans = [span1]
            group_errors = [self._get_error_by_id(span1.error_id, all_errors)]
            
            for j, span2 in enumerate(spans[i+1:], i+1):
                if span2.error_id in processed_spans:
                    continue
                    
                overlap_type = self._analyze_span_relationship(span1, span2)
                if overlap_type:
                    group_spans.append(span2)
                    group_errors.append(self._get_error_by_id(span2.error_id, all_errors))
                    processed_spans.add(span2.error_id)
            
            if len(group_spans) > 1:
                # Determine dominant span (usually the longest or most specific)
                dominant_span = self._determine_dominant_span(group_spans)
                consolidation_type = self._determine_consolidation_type(group_spans)
                
                groups.append(SpanGroup(
                    spans=group_spans,
                    errors=group_errors,
                    dominant_span=dominant_span,
                    consolidation_type=consolidation_type
                ))
                
            processed_spans.add(span1.error_id)
            
        return groups
    
    def _analyze_span_relationship(self, span1: TextSpan, span2: TextSpan) -> str:
        """
        Analyze the relationship between two text spans.
        
        Returns:
            'overlap', 'nested', 'adjacent', 'semantic', or None
        """
        # Check for exact overlap
        if span1.start_pos == span2.start_pos and span1.end_pos == span2.end_pos:
            return 'overlap'
            
        # Check for nested spans
        if (span1.start_pos <= span2.start_pos and span1.end_pos >= span2.end_pos) or \
           (span2.start_pos <= span1.start_pos and span2.end_pos >= span1.end_pos):
            return 'nested'
            
        # Check for partial overlap
        if self._calculate_overlap_ratio(span1, span2) >= self.overlap_threshold:
            return 'overlap'
            
        # Check for adjacency
        if abs(span1.end_pos - span2.start_pos) <= self.adjacency_threshold or \
           abs(span2.end_pos - span1.start_pos) <= self.adjacency_threshold:
            return 'adjacent'
            
        # Check for semantic relationship (similar words)
        if self._are_semantically_related(span1.text, span2.text):
            return 'semantic'
            
        return None
    
    def _calculate_overlap_ratio(self, span1: TextSpan, span2: TextSpan) -> float:
        """Calculate the overlap ratio between two spans."""
        start = max(span1.start_pos, span2.start_pos)
        end = min(span1.end_pos, span2.end_pos)
        
        if start >= end:
            return 0.0
            
        overlap_length = end - start
        total_length = max(span1.end_pos - span1.start_pos, span2.end_pos - span2.start_pos)
        
        return overlap_length / total_length if total_length > 0 else 0.0
    
    def _are_semantically_related(self, text1: str, text2: str) -> bool:
        """Check if two text segments are semantically related."""
        # Simple heuristics for semantic relationship
        t1, t2 = text1.lower().strip(), text2.lower().strip()
        
        # One is a substring of the other
        if t1 in t2 or t2 in t1:
            return True
            
        # Similar base words (handle word variations)
        base1 = re.sub(r'(ing|ed|ly|s)$', '', t1)
        base2 = re.sub(r'(ing|ed|ly|s)$', '', t2)
        if base1 == base2:
            return True
            
        # Common interactive terms
        interactive_terms = {'click', 'select', 'choose', 'press', 'tap'}
        if t1 in interactive_terms and t2 in interactive_terms:
            return True
            
        return False
    
    def _determine_dominant_span(self, spans: List[TextSpan]) -> TextSpan:
        """Determine which span should be the dominant one in the group."""
        # Prefer longer spans (more context)
        longest_span = max(spans, key=lambda s: len(s.text))
        
        # If there's a significant length difference, use the longest
        max_length = len(longest_span.text)
        if max_length > max(len(s.text) for s in spans if s != longest_span) * 1.5:
            return longest_span
            
        # Otherwise, prefer spans that appear first (left-to-right reading)
        return min(spans, key=lambda s: s.start_pos)
    
    def _determine_consolidation_type(self, spans: List[TextSpan]) -> str:
        """Determine the overall consolidation type for a group of spans."""
        if len(spans) <= 1:
            return 'single'
            
        # Check relationships between all pairs
        types = set()
        for i, span1 in enumerate(spans):
            for span2 in spans[i+1:]:
                rel_type = self._analyze_span_relationship(span1, span2)
                if rel_type:
                    types.add(rel_type)
        
        # Priority order for consolidation types
        if 'nested' in types:
            return 'nested'
        elif 'overlap' in types:
            return 'overlap'
        elif 'adjacent' in types:
            return 'adjacent'
        elif 'semantic' in types:
            return 'semantic'
        else:
            return 'related'
    
    def _get_error_by_id(self, error_id: str, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Retrieve error object by ID."""
        try:
            index = int(error_id.split('_')[1])
            return errors[index]
        except (IndexError, ValueError):
            return {} 