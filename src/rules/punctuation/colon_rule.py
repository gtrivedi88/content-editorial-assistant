"""
Colon Usage Rule - Ensures proper use of colons using pure SpaCy morphological analysis.
Uses SpaCy dependency parsing, POS tagging, and morphological features to detect colon usage patterns.
No hardcoded patterns - all analysis is based on linguistic morphology and syntax.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict

# Handle imports for different contexts (punctuation subdirectory)
try:
    from ..base_rule import BaseRule
except ImportError:
    try:
        from src.rules.base_rule import BaseRule
    except ImportError:
        from base_rule import BaseRule


class ColonRule(BaseRule):
    """Rule to detect colon usage issues using pure SpaCy morphological analysis."""
    
    def _get_rule_type(self) -> str:
        return 'colon_usage'
    
    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """Analyze text for colon usage issues using pure SpaCy linguistic analysis."""
        if not nlp:
            return []  # Skip analysis if SpaCy not available
        
        errors = []
        
        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            colon_issues = self._find_colon_usage_issues_morphological(doc, text)
            
            for issue in colon_issues:
                suggestions = self._generate_morphological_suggestions(issue, doc)
                
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message=self._create_morphological_message(issue),
                    suggestions=suggestions,
                    severity=self._determine_morphological_severity(issue),
                    colon_issue=issue
                ))
        
        return errors
    
    def _find_colon_usage_issues_morphological(self, doc, full_text: str) -> List[Dict[str, Any]]:
        """Find colon usage issues using SpaCy morphological and syntactic analysis."""
        issues = []
        
        # Find all colon-related structures in the document
        for token in doc:
            if self._is_colon_morphological(token):
                # Analyze colon usage
                colon_issue = self._analyze_colon_usage_morphological(token, doc)
                if colon_issue:
                    issues.append(colon_issue)
        
        # Check for missing colons where they should be present
        missing_colon_issues = self._find_missing_colons_morphological(doc)
        issues.extend(missing_colon_issues)
        
        return issues
    
    def _is_colon_morphological(self, token) -> bool:
        """Check if token is a colon using SpaCy morphological analysis."""
        return token.pos_ == "PUNCT" and token.text == ":"
    
    def _analyze_colon_usage_morphological(self, colon_token, doc) -> Optional[Dict[str, Any]]:
        """Analyze colon usage for potential issues using morphological analysis."""
        issues = []
        
        # Check for time/ratio context first (different rules apply)
        if self._is_time_ratio_context_morphological(colon_token, doc):
            # For time/ratio: no spaces before or after
            spacing_issue = self._check_time_ratio_spacing_morphological(colon_token, doc)
            if spacing_issue:
                issues.append('incorrect_time_ratio_spacing')
        else:
            # For regular colon usage: no space before, one space after
            spacing_issue = self._check_colon_spacing_morphological(colon_token, doc)
            if spacing_issue:
                issues.append('incorrect_spacing')
            
            # Check capitalization after colon
            capitalization_issue = self._check_capitalization_after_colon_morphological(colon_token, doc)
            if capitalization_issue:
                issues.append('incorrect_capitalization')
            
            # Check if colon is at end of heading
            if self._is_colon_after_heading_morphological(colon_token, doc):
                issues.append('colon_after_heading')
            
            # Check if colon usage is appropriate
            if not self._is_appropriate_colon_usage_morphological(colon_token, doc):
                issues.append('inappropriate_usage')
        
        if issues:
            issue_data = {
                'type': 'colon_usage_issue',
                'issues': issues,
                'colon_token': colon_token,
                'position': colon_token.idx
            }
            
            # Add capitalization details if relevant
            if 'incorrect_capitalization' in issues:
                cap_issue = self._check_capitalization_after_colon_morphological(colon_token, doc)
                if cap_issue:
                    issue_data['capitalization_details'] = cap_issue
            
            return issue_data
        
        return None
    
    def _check_colon_spacing_morphological(self, colon_token, doc) -> bool:
        """Check spacing around colon - should be no space before, one space after."""
        # Check for space before colon (should not exist)
        if colon_token.i > 0:
            prev_char_end = doc[colon_token.i - 1].idx + len(doc[colon_token.i - 1].text)
            colon_start = colon_token.idx
            if colon_start > prev_char_end:  # There's a space before
                return True
        
        # Check for space after colon (should exist)
        if colon_token.i < len(doc) - 1:
            colon_end = colon_token.idx + len(colon_token.text)
            next_char_start = doc[colon_token.i + 1].idx
            if next_char_start == colon_end:  # No space after
                return True
        
        return False
    
    def _check_time_ratio_spacing_morphological(self, colon_token, doc) -> bool:
        """Check spacing for time/ratio contexts - no spaces before or after."""
        # Check for space before colon (should not exist)
        if colon_token.i > 0:
            prev_char_end = doc[colon_token.i - 1].idx + len(doc[colon_token.i - 1].text)
            colon_start = colon_token.idx
            if colon_start > prev_char_end:  # There's a space before
                return True
        
        # Check for space after colon (should not exist for time/ratio)
        if colon_token.i < len(doc) - 1:
            colon_end = colon_token.idx + len(colon_token.text)
            next_char_start = doc[colon_token.i + 1].idx
            if next_char_start > colon_end:  # There's a space after
                return True
        
        return False
    
    def _check_capitalization_after_colon_morphological(self, colon_token, doc) -> Optional[Dict[str, Any]]:
        """Check capitalization after colon using morphological analysis."""
        if colon_token.i >= len(doc) - 1:
            return None
        
        # Find the first content word after colon
        following_word = self._find_first_content_word_after_colon_morphological(colon_token, doc)
        if not following_word:
            return None
        
        # Analyze context to determine expected capitalization
        colon_context = self._analyze_colon_context_for_capitalization_morphological(colon_token, doc)
        expected_capitalization = self._determine_expected_capitalization_morphological(colon_context, following_word)
        actual_capitalization = self._analyze_actual_capitalization_morphological(following_word)
        
        if expected_capitalization != actual_capitalization:
            return {
                'type': 'incorrect_capitalization',
                'following_word': following_word,
                'expected': expected_capitalization,
                'actual': actual_capitalization,
                'context': colon_context
            }
        
        return None
    
    def _find_first_content_word_after_colon_morphological(self, colon_token, doc) -> Optional[Any]:
        """Find first content word after colon using morphological analysis."""
        for i in range(colon_token.i + 1, len(doc)):
            token = doc[i]
            if not token.is_space and not token.is_punct:
                return token
        return None
    
    def _analyze_colon_context_for_capitalization_morphological(self, colon_token, doc) -> Dict[str, Any]:
        """Analyze colon context to determine capitalization rules using morphological analysis."""
        context = {
            'introduces_vertical_list': False,
            'introduces_quotation': False,
            'introduces_subtitle': False,
            'introduces_label_text': False,
            'within_sentence': False,
            'introduces_independent_clause': False,
            'is_time_ratio_context': False
        }
        
        # Analyze what follows the colon
        following_structure = self._analyze_following_structure_for_capitalization_morphological(colon_token, doc)
        context.update(following_structure)
        
        # Analyze what precedes the colon
        preceding_structure = self._analyze_preceding_structure_for_capitalization_morphological(colon_token, doc)
        context.update(preceding_structure)
        
        return context
    
    def _analyze_following_structure_for_capitalization_morphological(self, colon_token, doc) -> Dict[str, Any]:
        """Analyze structure following colon for capitalization context."""
        structure = {}
        following_tokens = doc[colon_token.i + 1:]
        
        # Check for quotation marks (indicates quotation)
        structure['introduces_quotation'] = self._has_quotation_markers_morphological(following_tokens)
        
        # Check for vertical list indicators
        structure['introduces_vertical_list'] = self._indicates_vertical_list_morphological(following_tokens)
        
        # Check for independent clause
        structure['introduces_independent_clause'] = self._introduces_independent_clause_morphological(following_tokens)
        
        # Check for inline list
        structure['introduces_inline_list'] = self._introduces_inline_list_morphological(following_tokens)
        
        # Check for time/ratio context
        structure['is_time_ratio_context'] = self._is_time_ratio_context_morphological(colon_token, doc)
        
        return structure
    
    def _analyze_preceding_structure_for_capitalization_morphological(self, colon_token, doc) -> Dict[str, Any]:
        """Analyze structure preceding colon for capitalization context."""
        structure = {}
        preceding_tokens = doc[:colon_token.i]
        
        # Check if this appears to be a label
        structure['follows_label'] = self._follows_label_pattern_morphological(preceding_tokens)
        
        # Check if this appears to be a subtitle/subheading
        structure['is_subtitle_context'] = self._is_subtitle_context_morphological(preceding_tokens)
        
        # Check if within sentence
        structure['within_sentence'] = self._is_within_sentence_morphological(preceding_tokens)
        
        return structure
    
    def _has_quotation_markers_morphological(self, tokens) -> bool:
        """Check for quotation markers using morphological analysis."""
        if not tokens:
            return False
        
        # Look for quotation marks in the first few tokens
        quotation_marks = ['"', "'", '"', '"', ''', ''']
        for token in tokens[:5]:
            if token.is_punct and token.text in quotation_marks:
                return True
        return False
    
    def _indicates_vertical_list_morphological(self, tokens) -> bool:
        """Check if tokens indicate start of vertical list using morphological analysis."""
        if not tokens:
            return False
        
        # Vertical lists often start with line breaks or specific formatting
        # In SpaCy, this might be indicated by sentence structure or specific patterns
        
        # Look for list indicators: capitalized items, numbered items, bullet points
        first_tokens = tokens[:10] if len(tokens) >= 10 else tokens
        
        # Check for multiple capitalized words (indicating list items)
        capitalized_count = 0
        for token in first_tokens:
            if token.text and token.text[0].isupper() and not token.is_punct:
                capitalized_count += 1
        
        # If many words are capitalized, likely a vertical list
        return capitalized_count >= 2
    
    def _introduces_independent_clause_morphological(self, tokens) -> bool:
        """Check if tokens form independent clause using morphological analysis."""
        if not tokens:
            return False
        
        # Independent clause has subject and predicate
        has_subject = any(token.dep_ in ['nsubj', 'nsubjpass'] for token in tokens[:10])
        has_verb = any(token.pos_ == 'VERB' for token in tokens[:10])
        
        return has_subject and has_verb
    
    def _introduces_inline_list_morphological(self, tokens) -> bool:
        """Check if tokens form inline list using morphological analysis."""
        if not tokens:
            return False
        
        # Look for coordination patterns indicating inline list
        coordination_count = sum(1 for token in tokens[:15] if token.pos_ == 'CCONJ')
        comma_count = sum(1 for token in tokens[:15] if token.text == ',')
        
        # Inline lists typically have multiple coordinations and commas
        return coordination_count >= 1 and comma_count >= 1
    
    def _is_time_ratio_context_morphological(self, colon_token, doc) -> bool:
        """Check if colon is used in time or ratio context using morphological analysis."""
        # Look for numeric patterns around the colon
        preceding_token = doc[colon_token.i - 1] if colon_token.i > 0 else None
        following_token = doc[colon_token.i + 1] if colon_token.i < len(doc) - 1 else None
        
        # Time context: number before and after, possibly with AM/PM
        if (preceding_token and following_token and 
            preceding_token.like_num and following_token.like_num):
            
            # Check for time indicators (AM, PM, hours, minutes)
            nearby_tokens = doc[max(0, colon_token.i - 3):min(len(doc), colon_token.i + 4)]
            time_indicators = any(
                token.text.upper() in ['AM', 'PM'] or 
                self._analyze_semantic_field(token) in ['temporal', 'time']
                for token in nearby_tokens
            )
            
            # Check for ratio indicators (increased, consolidation, etc.)
            ratio_indicators = any(
                self._analyze_semantic_field(token) in ['quantitative', 'ratio', 'comparison']
                for token in nearby_tokens
            )
            
            return time_indicators or ratio_indicators
        
        return False
    
    def _follows_label_pattern_morphological(self, tokens) -> bool:
        """Check if preceding tokens form a label pattern."""
        if not tokens:
            return False
        
        # Labels are typically short and end with descriptive words
        if len(tokens) > 5:  # Labels are usually short
            return False
        
        # Check for label-like semantic fields in the last tokens
        last_tokens = tokens[-3:] if len(tokens) >= 3 else tokens
        for token in last_tokens:
            if not token.is_punct:
                semantic_field = self._analyze_semantic_field(token)
                if semantic_field in ['instruction', 'process', 'category', 'label']:
                    return True
        
        return False
    
    def _is_subtitle_context_morphological(self, tokens) -> bool:
        """Check if context indicates subtitle/subheading."""
        if not tokens:
            return False
        
        # Subtitles often have specific patterns: "Lesson 1", "Chapter 2", etc.
        # Look for title-like morphological patterns
        
        title_score = 0
        for token in tokens:
            if not token.is_punct:
                # Check for title morphology
                if self._has_title_morphology_morphological(token):
                    title_score += 1
                
                # Check for numbering (Lesson 1, Chapter 2)
                if token.like_num:
                    title_score += 1
                
                # Check for title words using semantic analysis
                semantic_field = self._analyze_semantic_field(token)
                if semantic_field in ['instruction', 'process', 'section']:
                    title_score += 1
        
        # High title score suggests subtitle context
        return title_score >= 2
    
    def _is_within_sentence_morphological(self, tokens) -> bool:
        """Check if colon appears within a sentence rather than at end."""
        if not tokens:
            return False
        
        # Look for sentence structure before colon
        has_complete_clause = False
        
        # Check for subject-verb structure indicating ongoing sentence
        has_subject = any(token.dep_ in ['nsubj', 'nsubjpass'] for token in tokens)
        has_verb = any(token.pos_ == 'VERB' for token in tokens)
        
        if has_subject and has_verb:
            has_complete_clause = True
        
        # Check if this feels like middle of sentence vs. end
        # End of sentence often has conclusive words
        last_content_tokens = [t for t in tokens[-3:] if not t.is_punct and not t.is_space]
        if last_content_tokens:
            last_token = last_content_tokens[-1]
            semantic_field = self._analyze_semantic_field(last_token)
            # Introductory words suggest continuing sentence
            if semantic_field in ['introduction', 'presentation', 'enumeration']:
                return True
        
        return has_complete_clause
    
    def _determine_expected_capitalization_morphological(self, context: Dict[str, Any], following_word) -> str:
        """Determine expected capitalization based on context."""
        # Always capitalize proper nouns regardless of context
        if self._is_proper_noun_morphological(following_word):
            return 'uppercase'
        
        # Time and ratio contexts: use original capitalization
        if context.get('is_time_ratio_context', False):
            return 'preserve'
        
        # Contexts requiring uppercase
        uppercase_contexts = [
            'introduces_vertical_list',
            'introduces_quotation', 
            'is_subtitle_context',
            'follows_label'
        ]
        
        if any(context.get(ctx, False) for ctx in uppercase_contexts):
            return 'uppercase'
        
        # Within sentence contexts: use lowercase (unless proper noun)
        if (context.get('within_sentence', False) or 
            context.get('introduces_inline_list', False) or
            context.get('introduces_independent_clause', False)):
            return 'lowercase'
        
        # Default to lowercase for inline content
        return 'lowercase'
    
    def _analyze_actual_capitalization_morphological(self, token) -> str:
        """Analyze actual capitalization of token."""
        if not token.text:
            return 'unknown'
        
        first_char = token.text[0]
        if first_char.isupper():
            return 'uppercase'
        elif first_char.islower():
            return 'lowercase'
        else:
            return 'other'
    
    def _is_proper_noun_morphological(self, token) -> bool:
        """Check if token is proper noun using morphological analysis."""
        # Primary check: POS tag
        if token.pos_ == 'PROPN':
            return True
        
        # Secondary check: NER
        if hasattr(token, 'ent_type_') and token.ent_type_:
            return True
        
        # Tertiary check: morphological features
        morph_features = self._get_morphological_features(token)
        if 'Proper' in morph_features.get('morphology', ''):
            return True
        
        return False
    
    def _is_colon_after_heading_morphological(self, colon_token, doc) -> bool:
        """Check if colon appears at end of heading using morphological analysis."""
        # Look at tokens before colon to determine if it's a heading
        preceding_tokens = doc[:colon_token.i]
        
        # Headings typically have specific patterns:
        # - Short phrases
        # - Title case words
        # - Proper nouns
        # - Gerunds (Creating, Setting, etc.)
        
        if len(preceding_tokens) > 6:  # Headings are usually short
            return False
        
        title_indicators = 0
        content_words = 0
        
        for token in preceding_tokens:
            if not token.is_punct and not token.is_space:
                content_words += 1
                
                # Check for title-like morphological features
                if self._has_title_morphology_morphological(token):
                    title_indicators += 1
        
        # High proportion of title indicators suggests heading
        if content_words > 0:
            title_ratio = title_indicators / content_words
            return title_ratio > 0.6
        
        return False
    
    def _has_title_morphology_morphological(self, token) -> bool:
        """Check if token has morphological features typical of titles."""
        # Proper nouns
        if token.pos_ == 'PROPN':
            return True
        
        # Capitalized words
        if token.text and token.text[0].isupper():
            return True
        
        # Gerunds (common in titles like "Creating use cases")
        morph_features = self._get_morphological_features(token)
        if 'VerbForm=Ger' in morph_features.get('morphology', ''):
            return True
        
        return False
    
    def _is_appropriate_colon_usage_morphological(self, colon_token, doc) -> bool:
        """Check if colon usage is appropriate using morphological analysis."""
        preceding_context = self._analyze_preceding_context_morphological(colon_token, doc)
        following_context = self._analyze_following_context_morphological(colon_token, doc)
        
        # Appropriate uses:
        # 1. After labels (Important:, Note:, Tip:)
        if preceding_context.get('is_label', False):
            return True
        
        # 2. After introduction to list
        if (preceding_context.get('is_introduction', False) and 
            following_context.get('is_list', False)):
            return True
        
        # 3. Between independent clauses for amplification
        if (preceding_context.get('is_independent_clause', False) and
            following_context.get('is_independent_clause', False)):
            return True
        
        # 4. Before examples or explanations
        if following_context.get('is_explanation', False):
            return True
        
        return False
    
    def _analyze_preceding_context_morphological(self, colon_token, doc) -> Dict[str, Any]:
        """Analyze context before colon using morphological analysis."""
        context = {
            'is_label': False,
            'is_introduction': False,
            'is_independent_clause': False
        }
        
        preceding_tokens = doc[:colon_token.i]
        if not preceding_tokens:
            return context
        
        # Check for label patterns
        context['is_label'] = self._is_label_pattern_morphological(preceding_tokens)
        
        # Check for introduction patterns
        context['is_introduction'] = self._is_introduction_pattern_morphological(preceding_tokens)
        
        # Check for independent clause
        context['is_independent_clause'] = self._is_independent_clause_morphological(preceding_tokens)
        
        return context
    
    def _analyze_following_context_morphological(self, colon_token, doc) -> Dict[str, Any]:
        """Analyze context after colon using morphological analysis."""
        context = {
            'is_list': False,
            'is_explanation': False,
            'is_independent_clause': False
        }
        
        following_tokens = doc[colon_token.i + 1:]
        if not following_tokens:
            return context
        
        # Check for list structure
        context['is_list'] = self._is_list_structure_morphological(following_tokens)
        
        # Check for explanation
        context['is_explanation'] = self._is_explanation_structure_morphological(following_tokens)
        
        # Check for independent clause
        context['is_independent_clause'] = self._is_independent_clause_morphological(following_tokens)
        
        return context
    
    def _is_label_pattern_morphological(self, tokens) -> bool:
        """Check for label patterns using morphological analysis."""
        if not tokens or len(tokens) > 3:  # Labels are typically short
            return False
        
        # Look for single words or short phrases that could be labels
        for token in tokens:
            if not token.is_punct and not token.is_space:
                semantic_field = self._analyze_semantic_field(token)
                # Labels often have directive or attention-getting semantic fields
                if semantic_field in ['directive', 'attention', 'instruction']:
                    return True
                
                # Check morphological features
                if token.pos_ in ['NOUN', 'ADJ'] and token.text and token.text[0].isupper():
                    return True
        
        return False
    
    def _is_introduction_pattern_morphological(self, tokens) -> bool:
        """Check for introduction patterns using morphological analysis."""
        if not tokens:
            return False
        
        # Look for introductory phrases
        for token in tokens:
            if not token.is_punct and not token.is_space:
                # Check for verbs that introduce
                if token.pos_ == 'VERB':
                    semantic_field = self._analyze_semantic_field(token)
                    if semantic_field in ['presentation', 'enumeration']:
                        return True
                
                # Check for demonstrative pronouns/determiners
                if token.pos_ in ['DET', 'PRON']:
                    morph_features = self._get_morphological_features(token)
                    if 'PronType=Dem' in morph_features.get('morphology', ''):
                        return True
        
        return False
    
    def _is_independent_clause_morphological(self, tokens) -> bool:
        """Check if tokens form an independent clause using morphological analysis."""
        if not tokens:
            return False
        
        has_subject = any(token.dep_ in ['nsubj', 'nsubjpass'] for token in tokens)
        has_verb = any(token.pos_ == 'VERB' for token in tokens)
        
        return has_subject and has_verb
    
    def _is_list_structure_morphological(self, tokens) -> bool:
        """Check if tokens represent a list structure using morphological analysis."""
        if not tokens:
            return False
        
        # Look for coordination patterns
        coordination_count = sum(1 for token in tokens if token.pos_ == 'CCONJ')
        
        # Look for parallel structures (similar POS patterns)
        pos_patterns = [token.pos_ for token in tokens if not token.is_punct and not token.is_space]
        
        # Multiple coordinations or repeated POS patterns suggest list
        return coordination_count >= 1 or len(set(pos_patterns)) < len(pos_patterns) * 0.7
    
    def _is_explanation_structure_morphological(self, tokens) -> bool:
        """Check if tokens represent an explanation using morphological analysis."""
        if not tokens:
            return False
        
        # Look for explanatory patterns
        for token in tokens:
            if not token.is_punct and not token.is_space:
                semantic_field = self._analyze_semantic_field(token)
                if semantic_field in ['explanation', 'elaboration', 'description']:
                    return True
        
        return False
    
    def _find_missing_colons_morphological(self, doc) -> List[Dict[str, Any]]:
        """Find places where colons are missing using morphological analysis."""
        missing_issues = []
        
        for i, token in enumerate(doc):
            # Check if this token should be followed by a colon
            if self._should_have_colon_after_morphological(token, doc, i):
                missing_issues.append({
                    'type': 'missing_colon',
                    'position': token.idx,
                    'token': token
                })
        
        return missing_issues
    
    def _should_have_colon_after_morphological(self, token, doc, position: int) -> bool:
        """Check if a colon should follow this token using morphological analysis."""
        # Skip if next token is already a colon
        if position < len(doc) - 1 and self._is_colon_morphological(doc[position + 1]):
            return False
        
        # Check for patterns that should have colons
        preceding_tokens = doc[:position + 1]
        following_tokens = doc[position + 1:position + 10]  # Look ahead
        
        # Pattern 1: Introduction to list without colon
        if (self._is_introduction_pattern_morphological(preceding_tokens) and
            self._is_list_structure_morphological(following_tokens)):
            return True
        
        # Pattern 2: Label without colon
        if (self._is_label_pattern_morphological([token]) and
            self._is_explanation_structure_morphological(following_tokens)):
            return True
        
        return False
    
    def _generate_morphological_suggestions(self, issue: Dict[str, Any], doc) -> List[str]:
        """Generate suggestions based on morphological analysis."""
        suggestions = []
        
        issue_type = issue.get('type', '')
        issues = issue.get('issues', [])
        
        if issue_type == 'colon_usage_issue':
            for specific_issue in issues:
                if specific_issue == 'incorrect_spacing':
                    suggestions.append("Use no space before colon and one space after colon")
                elif specific_issue == 'incorrect_time_ratio_spacing':
                    suggestions.append("Use no spaces before or after colon in time/ratio format")
                elif specific_issue == 'incorrect_capitalization':
                    cap_details = issue.get('capitalization_details', {})
                    expected = cap_details.get('expected', '')
                    context = cap_details.get('context', {})
                    
                    if expected == 'uppercase':
                        if context.get('introduces_vertical_list'):
                            suggestions.append("Use uppercase after colon when introducing vertical list")
                        elif context.get('introduces_quotation'):
                            suggestions.append("Use uppercase after colon when introducing quotation")
                        elif context.get('is_subtitle_context'):
                            suggestions.append("Use uppercase after colon in subtitle/subheading")
                        else:
                            suggestions.append("Use uppercase after colon in this context")
                    elif expected == 'lowercase':
                        suggestions.append("Use lowercase after colon when within sentence or introducing inline content")
                elif specific_issue == 'colon_after_heading':
                    suggestions.append("Remove colon from end of heading or title")
                elif specific_issue == 'inappropriate_usage':
                    suggestions.append("Use colon only after labels, introductions, or between related clauses")
        
        elif issue_type == 'missing_colon':
            suggestions.append("Add colon after introduction or label")
        
        if not suggestions:
            suggestions.append("Review colon usage according to style guidelines")
        
        return suggestions
    
    def _create_morphological_message(self, issue: Dict[str, Any]) -> str:
        """Create message based on morphological analysis."""
        issue_type = issue.get('type', '')
        
        if issue_type == 'colon_usage_issue':
            issues = issue.get('issues', [])
            if 'incorrect_spacing' in issues:
                return "Incorrect spacing around colon"
            elif 'incorrect_time_ratio_spacing' in issues:
                return "Incorrect spacing in time/ratio format"
            elif 'incorrect_capitalization' in issues:
                cap_details = issue.get('capitalization_details', {})
                expected = cap_details.get('expected', '')
                actual = cap_details.get('actual', '')
                return f"Incorrect capitalization after colon: should be {expected}, found {actual}"
            elif 'colon_after_heading' in issues:
                return "Inappropriate colon at end of heading"
            elif 'inappropriate_usage' in issues:
                return "Inappropriate colon usage"
            else:
                return "Colon usage issue"
        
        elif issue_type == 'missing_colon':
            return "Missing colon after introduction or label"
        
        return "Colon usage issue"
    
    def _determine_morphological_severity(self, issue: Dict[str, Any]) -> str:
        """Determine severity based on morphological analysis."""
        issue_type = issue.get('type', '')
        issues = issue.get('issues', [])
        
        if issue_type == 'colon_usage_issue':
            if 'colon_after_heading' in issues or 'inappropriate_usage' in issues:
                return 'medium'
            elif 'incorrect_capitalization' in issues:
                return 'medium'
            elif 'incorrect_time_ratio_spacing' in issues:
                return 'low'
            else:
                return 'low'
        elif issue_type == 'missing_colon':
            return 'medium'
        
        return 'info' 