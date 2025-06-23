"""
Series Comma Rule - Ensures proper use of commas in series using pure SpaCy morphological analysis.
Uses SpaCy dependency parsing, POS tagging, and morphological features to detect series patterns.
No hardcoded patterns - all analysis is based on linguistic morphology and syntax.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
import re

# Handle imports for different contexts (punctuation subdirectory)
try:
    from ...base_rule import BaseRule
except ImportError:
    try:
        from src.rules.base_rule import BaseRule
    except ImportError:
        from base_rule import BaseRule


class SeriesCommaRule(BaseRule):
    """Rule to detect series comma usage issues using pure SpaCy morphological analysis."""
    
    def _get_rule_type(self) -> str:
        return 'series_comma'
    
    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """Analyze text for series comma issues using pure SpaCy linguistic analysis."""
        if not nlp:
            return []  # Skip analysis if SpaCy not available
        
        errors = []
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
                
            doc = nlp(sentence)
            
            # Find series comma issues
            series_issues = self._find_series_comma_issues_morphological(doc, sentence)
            
            for issue in series_issues:
                suggestions = self._generate_morphological_suggestions(issue, doc)
                
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message=self._create_morphological_message(issue),
                    suggestions=suggestions,
                    severity=self._determine_morphological_severity(issue),
                    series_issue=issue
                ))
        
        return errors
    
    def _find_series_comma_issues_morphological(self, doc, sentence: str) -> List[Dict[str, Any]]:
        """Find series comma usage issues using SpaCy morphological and syntactic analysis."""
        issues = []
        
        # Identify all series in the sentence
        series_patterns = self._identify_all_series_morphological(doc)
        
        for series_pattern in series_patterns:
            # Analyze each series for comma issues
            series_issues = self._analyze_series_comma_usage_morphological(series_pattern, doc)
            issues.extend(series_issues)
        
        return issues
    
    def _identify_all_series_morphological(self, doc) -> List[Dict[str, Any]]:
        """Identify all series patterns in the document using morphological analysis."""
        series_patterns = []
        
        # Method 1: Find series through coordinating conjunctions
        conjunction_series = self._find_conjunction_based_series_morphological(doc)
        series_patterns.extend(conjunction_series)
        
        # Method 2: Find series through comma patterns
        comma_series = self._find_comma_based_series_morphological(doc)
        series_patterns.extend(comma_series)
        
        # Method 3: Find colon-introduced series
        colon_series = self._find_colon_introduced_series_morphological(doc)
        series_patterns.extend(colon_series)
        
        # Remove duplicates and merge overlapping series
        return self._merge_overlapping_series_morphological(series_patterns)
    
    def _find_conjunction_based_series_morphological(self, doc) -> List[Dict[str, Any]]:
        """Find series patterns based on coordinating conjunctions."""
        series_patterns = []
        
        for token in doc:
            if self._is_coordinating_conjunction_morphological(token):
                # Look for series pattern around this conjunction
                series_data = self._extract_series_around_conjunction_morphological(token, doc)
                if series_data and len(series_data.get('items', [])) >= 3:
                    series_patterns.append(series_data)
        
        return series_patterns
    
    def _find_comma_based_series_morphological(self, doc) -> List[Dict[str, Any]]:
        """Find series patterns based on comma sequences."""
        series_patterns = []
        
        # Find sequences of commas that might indicate series
        comma_positions = [i for i, token in enumerate(doc) if token.text == ',']
        
        if len(comma_positions) >= 2:  # At least 2 commas for a 3+ item series
            # Group nearby commas into potential series
            series_groups = self._group_nearby_commas_morphological(comma_positions, doc)
            
            for group in series_groups:
                series_data = self._extract_series_from_comma_group_morphological(group, doc)
                if series_data and len(series_data.get('items', [])) >= 3:
                    series_patterns.append(series_data)
        
        return series_patterns
    
    def _find_colon_introduced_series_morphological(self, doc) -> List[Dict[str, Any]]:
        """Find series patterns introduced by colons."""
        series_patterns = []
        
        for i, token in enumerate(doc):
            if token.text == ':':
                # Look for series after colon
                series_data = self._extract_series_after_colon_morphological(i, doc)
                if series_data and len(series_data.get('items', [])) >= 3:
                    series_patterns.append(series_data)
        
        return series_patterns
    
    def _is_coordinating_conjunction_morphological(self, token) -> bool:
        """Check if token is a coordinating conjunction."""
        if token.pos_ == 'CCONJ':
            lemma = token.lemma_.lower()
            # FANBOYS: for, and, nor, but, or, yet, so
            coordinating_lemmas = {'and', 'or', 'nor'}  # Focus on series conjunctions
            return lemma in coordinating_lemmas
        return False
    
    def _extract_series_around_conjunction_morphological(self, conj_token, doc) -> Optional[Dict[str, Any]]:
        """Extract series items around a coordinating conjunction."""
        # Find items before conjunction
        items_before = self._find_series_items_before_morphological(conj_token, doc)
        
        # Find item after conjunction
        item_after = self._find_series_item_after_morphological(conj_token, doc)
        
        if not items_before or not item_after:
            return None
        
        all_items = items_before + [item_after]
        
        return {
            'type': 'conjunction_series',
            'items': all_items,
            'conjunction': conj_token,
            'start_index': all_items[0]['start'] if all_items else conj_token.i,
            'end_index': all_items[-1]['end'] if all_items else conj_token.i,
            'has_oxford_comma': self._check_oxford_comma_morphological(conj_token, doc)
        }
    
    def _find_series_items_before_morphological(self, conj_token, doc) -> List[Dict[str, Any]]:
        """Find series items before a conjunction."""
        items = []
        current_item_tokens = []
        
        # Look backwards from conjunction
        for i in range(conj_token.i - 1, -1, -1):
            token = doc[i]
            
            if token.text == ',':
                # End of current item
                if current_item_tokens:
                    item_data = self._create_item_data_morphological(current_item_tokens[::-1])
                    items.insert(0, item_data)
                    current_item_tokens = []
            elif token.is_sent_start or token.text in ['.', ';', ':', '!', '?']:
                # End of series
                break
            elif not token.is_space:
                current_item_tokens.append(token)
        
        # Add the final item (first in the series)
        if current_item_tokens:
            item_data = self._create_item_data_morphological(current_item_tokens[::-1])
            items.insert(0, item_data)
        
        return items
    
    def _find_series_item_after_morphological(self, conj_token, doc) -> Optional[Dict[str, Any]]:
        """Find the series item after a conjunction."""
        item_tokens = []
        
        # Look forward from conjunction
        for i in range(conj_token.i + 1, len(doc)):
            token = doc[i]
            
            if (token.text in [',', '.', ';', ':', '!', '?'] or 
                token.is_sent_end or
                self._is_coordinating_conjunction_morphological(token)):
                # End of item
                break
            elif not token.is_space:
                item_tokens.append(token)
        
        if item_tokens:
            return self._create_item_data_morphological(item_tokens)
        
        return None
    
    def _create_item_data_morphological(self, tokens) -> Dict[str, Any]:
        """Create item data structure from tokens using morphological analysis."""
        if not tokens:
            return {}
        
        return {
            'tokens': tokens,
            'text': ' '.join([t.text for t in tokens]),
            'start': tokens[0].i,
            'end': tokens[-1].i,
            'type': self._classify_item_type_morphological(tokens),
            'is_special_character': self._is_special_character_item_morphological(tokens),
            'morphological_features': [self._get_morphological_features(t) for t in tokens]
        }
    
    def _classify_item_type_morphological(self, tokens) -> str:
        """Classify the type of series item using morphological analysis."""
        if not tokens:
            return 'unknown'
        
        # Analyze the main content words
        content_tokens = [t for t in tokens if not t.is_punct and not t.is_space and not t.is_stop]
        
        if not content_tokens:
            return 'punctuation'
        
        # Check for special characters
        if self._is_special_character_item_morphological(tokens):
            return 'special_character'
        
        # Analyze primary POS patterns
        pos_counts = defaultdict(int)
        for token in content_tokens:
            pos_counts[token.pos_] += 1
        
        primary_pos = max(pos_counts.keys(), key=lambda x: pos_counts[x]) if pos_counts else 'UNKNOWN'
        
        # Map POS to item types
        pos_to_type = {
            'NOUN': 'noun_phrase',
            'PROPN': 'proper_noun',
            'VERB': 'verb_phrase',
            'ADJ': 'adjective_phrase',
            'ADV': 'adverb_phrase',
            'NUM': 'number',
            'SYM': 'symbol'
        }
        
        return pos_to_type.get(primary_pos, 'phrase')
    
    def _is_special_character_item_morphological(self, tokens) -> bool:
        """Check if item consists of special characters using morphological analysis."""
        if not tokens:
            return False
        
        # Remove spaces and check remaining tokens
        non_space_tokens = [t for t in tokens if not t.is_space]
        
        if len(non_space_tokens) == 1:
            token = non_space_tokens[0]
            
            # Check if it's a punctuation or symbol
            if token.pos_ in ['PUNCT', 'SYM']:
                return True
            
            # Check if it's a single character that's not alphanumeric
            if len(token.text) == 1 and not token.text.isalnum():
                return True
        
        return False
    
    def _check_oxford_comma_morphological(self, conj_token, doc) -> bool:
        """Check if Oxford comma is present before conjunction."""
        if conj_token.i == 0:
            return False
        
        # Look for comma immediately before conjunction (allowing for spaces)
        for i in range(conj_token.i - 1, max(-1, conj_token.i - 3), -1):
            if doc[i].text == ',':
                return True
            elif not doc[i].is_space:
                break
        
        return False
    
    def _group_nearby_commas_morphological(self, comma_positions, doc) -> List[List[int]]:
        """Group nearby commas that likely belong to the same series."""
        if not comma_positions:
            return []
        
        groups = []
        current_group = [comma_positions[0]]
        
        for i in range(1, len(comma_positions)):
            prev_pos = comma_positions[i-1]
            curr_pos = comma_positions[i]
            
            # Check if commas are close enough to be in same series
            tokens_between = curr_pos - prev_pos - 1
            
            # Heuristic: if less than 20 tokens between commas, likely same series
            if tokens_between <= 20:
                current_group.append(curr_pos)
            else:
                if len(current_group) >= 2:  # At least 2 commas for potential 3+ item series
                    groups.append(current_group)
                current_group = [curr_pos]
        
        # Add final group
        if len(current_group) >= 2:
            groups.append(current_group)
        
        return groups
    
    def _extract_series_from_comma_group_morphological(self, comma_positions, doc) -> Optional[Dict[str, Any]]:
        """Extract series items from a group of comma positions."""
        items = []
        
        # Define series boundaries
        start_pos = 0
        end_pos = len(doc)
        
        # Find start boundary (sentence start or punctuation)
        if comma_positions:
            for i in range(comma_positions[0] - 1, -1, -1):
                if doc[i].is_sent_start or doc[i].text in ['.', ';', ':', '!', '?']:
                    start_pos = i + 1 if not doc[i].is_sent_start else i
                    break
        
        # Find end boundary
        if comma_positions:
            for i in range(comma_positions[-1] + 1, len(doc)):
                if doc[i].is_sent_end or doc[i].text in ['.', ';', ':', '!', '?']:
                    end_pos = i
                    break
        
        # Extract items between commas
        item_boundaries = [start_pos] + comma_positions + [end_pos]
        
        for i in range(len(item_boundaries) - 1):
            item_start = item_boundaries[i]
            item_end = item_boundaries[i + 1]
            
            # Skip the comma itself
            if i > 0:
                item_start += 1
            
            # Extract tokens for this item
            item_tokens = []
            for j in range(item_start, item_end):
                if j < len(doc) and not doc[j].is_space:
                    item_tokens.append(doc[j])
            
            if item_tokens:
                item_data = self._create_item_data_morphological(item_tokens)
                items.append(item_data)
        
        if len(items) >= 3:
            # Check for final conjunction
            final_conjunction = self._find_final_conjunction_morphological(items, doc)
            
            return {
                'type': 'comma_series',
                'items': items,
                'conjunction': final_conjunction,
                'start_index': start_pos,
                'end_index': end_pos - 1,
                'has_oxford_comma': self._check_oxford_comma_in_series_morphological(items, final_conjunction, doc)
            }
        
        return None
    
    def _find_final_conjunction_morphological(self, items, doc) -> Optional[object]:
        """Find the final conjunction in a series."""
        if len(items) < 2:
            return None
        
        # Look between last two items for conjunction
        last_item = items[-1]
        second_last_item = items[-2]
        
        for i in range(second_last_item['end'] + 1, last_item['start']):
            if i < len(doc) and self._is_coordinating_conjunction_morphological(doc[i]):
                return doc[i]
        
        return None
    
    def _check_oxford_comma_in_series_morphological(self, items, conjunction, doc) -> bool:
        """Check if Oxford comma is present in series."""
        if not conjunction or len(items) < 3:
            return False
        
        # Look for comma before conjunction
        for i in range(conjunction.i - 1, max(-1, conjunction.i - 5), -1):
            if i < len(doc):
                if doc[i].text == ',':
                    return True
                elif not doc[i].is_space:
                    break
        
        return False
    
    def _extract_series_after_colon_morphological(self, colon_pos, doc) -> Optional[Dict[str, Any]]:
        """Extract series items after a colon."""
        items = []
        current_item_tokens = []
        
        # Look forward from colon
        for i in range(colon_pos + 1, len(doc)):
            token = doc[i]
            
            if token.text == ',':
                # End of current item
                if current_item_tokens:
                    item_data = self._create_item_data_morphological(current_item_tokens)
                    items.append(item_data)
                    current_item_tokens = []
            elif token.is_sent_end or token.text in ['.', ';', '!', '?']:
                # End of series
                break
            elif self._is_coordinating_conjunction_morphological(token):
                # Final conjunction
                if current_item_tokens:
                    item_data = self._create_item_data_morphological(current_item_tokens)
                    items.append(item_data)
                    current_item_tokens = []
                
                # Get final item
                final_item = self._find_series_item_after_morphological(token, doc)
                if final_item:
                    items.append(final_item)
                break
            elif not token.is_space:
                current_item_tokens.append(token)
        
        # Add final item if no conjunction found
        if current_item_tokens:
            item_data = self._create_item_data_morphological(current_item_tokens)
            items.append(item_data)
        
        if len(items) >= 3:
            return {
                'type': 'colon_series',
                'items': items,
                'start_index': colon_pos,
                'end_index': items[-1]['end'] if items else colon_pos,
                'has_oxford_comma': False  # Will be checked separately
            }
        
        return None
    
    def _merge_overlapping_series_morphological(self, series_patterns) -> List[Dict[str, Any]]:
        """Merge overlapping series patterns to avoid duplicates."""
        if not series_patterns:
            return []
        
        # Sort by start position
        sorted_series = sorted(series_patterns, key=lambda x: x.get('start_index', 0))
        
        merged = []
        current = sorted_series[0]
        
        for next_series in sorted_series[1:]:
            # Check for overlap
            if (next_series.get('start_index', 0) <= current.get('end_index', 0) + 5):
                # Merge series (keep the one with more items)
                if len(next_series.get('items', [])) > len(current.get('items', [])):
                    current = next_series
            else:
                merged.append(current)
                current = next_series
        
        merged.append(current)
        return merged
    
    def _analyze_series_comma_usage_morphological(self, series_pattern, doc) -> List[Dict[str, Any]]:
        """Analyze a series pattern for comma usage issues."""
        issues = []
        items = series_pattern.get('items', [])
        
        if len(items) < 3:
            return issues  # Not a proper series
        
        # Check for Oxford comma issues
        oxford_issue = self._check_oxford_comma_issue_morphological(series_pattern, doc)
        if oxford_issue:
            issues.append(oxford_issue)
        
        # Check for special character series with incorrect commas
        special_char_issue = self._check_special_character_series_morphological(series_pattern, doc)
        if special_char_issue:
            issues.append(special_char_issue)
        
        # Check for missing commas between items
        missing_comma_issue = self._check_missing_series_commas_morphological(series_pattern, doc)
        if missing_comma_issue:
            issues.append(missing_comma_issue)
        
        # Check for inappropriate comma usage
        inappropriate_comma_issue = self._check_inappropriate_commas_morphological(series_pattern, doc)
        if inappropriate_comma_issue:
            issues.append(inappropriate_comma_issue)
        
        return issues
    
    def _check_oxford_comma_issue_morphological(self, series_pattern, doc) -> Optional[Dict[str, Any]]:
        """Check for Oxford comma issues in series."""
        items = series_pattern.get('items', [])
        conjunction = series_pattern.get('conjunction')
        has_oxford = series_pattern.get('has_oxford_comma', False)
        
        if len(items) < 3 or not conjunction:
            return None
        
        # Oxford comma should be present in series of 3+ items
        if not has_oxford:
            return {
                'type': 'missing_oxford_comma',
                'series_pattern': series_pattern,
                'conjunction': conjunction,
                'position': conjunction.i,
                'items_count': len(items)
            }
        
        return None
    
    def _check_special_character_series_morphological(self, series_pattern, doc) -> Optional[Dict[str, Any]]:
        """Check for incorrect comma usage in special character series."""
        items = series_pattern.get('items', [])
        
        # Check if all items are special characters
        special_char_count = sum(1 for item in items if item.get('is_special_character', False))
        
        if special_char_count >= len(items) * 0.8:  # 80% or more are special characters
            # Check if there are commas or conjunctions (which there shouldn't be)
            conjunction = series_pattern.get('conjunction')
            
            if conjunction or self._has_commas_between_special_chars_morphological(series_pattern, doc):
                return {
                    'type': 'special_character_series_with_commas',
                    'series_pattern': series_pattern,
                    'items_count': len(items),
                    'special_char_count': special_char_count
                }
        
        return None
    
    def _has_commas_between_special_chars_morphological(self, series_pattern, doc) -> bool:
        """Check if there are commas between special character items."""
        items = series_pattern.get('items', [])
        
        for i in range(len(items) - 1):
            current_item = items[i]
            next_item = items[i + 1]
            
            # Check for comma between items
            for j in range(current_item['end'] + 1, next_item['start']):
                if j < len(doc) and doc[j].text == ',':
                    return True
        
        return False
    
    def _check_missing_series_commas_morphological(self, series_pattern, doc) -> Optional[Dict[str, Any]]:
        """Check for missing commas between series items."""
        items = series_pattern.get('items', [])
        
        if len(items) < 3:
            return None
        
        missing_positions = []
        
        # Check between each pair of items (except last pair which might have conjunction)
        for i in range(len(items) - 2):
            current_item = items[i]
            next_item = items[i + 1]
            
            # Check if there's a comma between items
            has_comma = False
            for j in range(current_item['end'] + 1, next_item['start']):
                if j < len(doc) and doc[j].text == ',':
                    has_comma = True
                    break
            
            if not has_comma:
                missing_positions.append(current_item['end'])
        
        if missing_positions:
            return {
                'type': 'missing_series_commas',
                'series_pattern': series_pattern,
                'missing_positions': missing_positions,
                'items_count': len(items)
            }
        
        return None
    
    def _check_inappropriate_commas_morphological(self, series_pattern, doc) -> Optional[Dict[str, Any]]:
        """Check for inappropriate comma usage in series."""
        # This could check for issues like:
        # - Commas in two-item series
        # - Extra commas
        # - Misplaced commas
        
        items = series_pattern.get('items', [])
        
        # Check for comma in two-item series (should only use conjunction)
        if len(items) == 2:
            # Look for commas between the items
            first_item = items[0]
            second_item = items[1]
            
            for i in range(first_item['end'] + 1, second_item['start']):
                if i < len(doc) and doc[i].text == ',':
                    return {
                        'type': 'comma_in_two_item_series',
                        'series_pattern': series_pattern,
                        'comma_position': i
                    }
        
        return None
    
    def _generate_morphological_suggestions(self, issue: Dict[str, Any], doc) -> List[str]:
        """Generate suggestions based on series comma issue type."""
        issue_type = issue.get('type', '')
        suggestions = []
        
        if issue_type == 'missing_oxford_comma':
            conjunction = issue.get('conjunction')
            conj_text = conjunction.text if conjunction else 'conjunction'
            suggestions.append(f"Add a comma before '{conj_text}' to create an Oxford comma in this series")
            suggestions.append("Use commas to separate items in a series of three or more, including before the final conjunction")
            suggestions.append("Example: 'A, B, and C' (not 'A, B and C')")
        
        elif issue_type == 'special_character_series_with_commas':
            suggestions.append("Remove commas and conjunctions from series of special characters")
            suggestions.append("Present special characters with only spaces: '# & . ^ ~'")
            suggestions.append("Incorrect: '#, &, ., ^, and ~' | Correct: '# & . ^ ~'")
        
        elif issue_type == 'missing_series_commas':
            items_count = issue.get('items_count', 3)
            suggestions.append(f"Add commas between items in this {items_count}-item series")
            suggestions.append("Use commas to separate each item in a series of three or more")
            suggestions.append("Example: 'describes an error, explains how to correct it, and provides controls'")
        
        elif issue_type == 'comma_in_two_item_series':
            suggestions.append("Remove comma from two-item series; use only conjunction")
            suggestions.append("Two items should be connected with just 'and' or 'or'")
            suggestions.append("Example: 'A and B' (not 'A, and B')")
        
        # Generic fallback
        if not suggestions:
            suggestions.append("Review comma usage in this series according to standard grammar rules")
            suggestions.append("Use commas to separate items in a series of three or more")
        
        return suggestions
    
    def _create_morphological_message(self, issue: Dict[str, Any]) -> str:
        """Create error message based on issue type."""
        issue_type = issue.get('type', '')
        
        if issue_type == 'missing_oxford_comma':
            items_count = issue.get('items_count', 3)
            return f"Use a comma before the conjunction in this {items_count}-item series (Oxford comma)."
        
        elif issue_type == 'special_character_series_with_commas':
            return "Do not use commas or conjunctions between items in a series of special characters."
        
        elif issue_type == 'missing_series_commas':
            items_count = issue.get('items_count', 3)
            return f"Add commas between items in this {items_count}-item series."
        
        elif issue_type == 'comma_in_two_item_series':
            return "Do not use commas in a two-item series; use only the conjunction."
        
        return "Review comma usage in this series."
    
    def _determine_morphological_severity(self, issue: Dict[str, Any]) -> str:
        """Determine severity level based on issue type."""
        issue_type = issue.get('type', '')
        
        # Medium severity for clarity and style issues
        medium_severity_types = ['missing_oxford_comma', 'missing_series_commas']
        
        # Low severity for style preferences
        low_severity_types = ['special_character_series_with_commas', 'comma_in_two_item_series']
        
        if issue_type in medium_severity_types:
            return 'medium'
        elif issue_type in low_severity_types:
            return 'low'
        else:
            return 'medium' 