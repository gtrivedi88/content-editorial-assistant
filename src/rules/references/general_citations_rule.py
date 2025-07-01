"""
This file implements the GeneralCitationGuidelinesRule for the writing style linter.
It focuses on codifying the "General guidelines" from the "Citations and references"
section of the Style Guide.

The rule uses pure spaCy morphological analysis and linguistic anchors to identify
potential style violations, ensuring a high degree of accuracy and context-awareness.
"""

import re
from typing import List, Dict, Any, Optional

# Handle imports for different contexts
try:
    from ..base_rule import BaseRule
except ImportError:
    from base_rule import BaseRule



class GeneralCitationGuidelinesRule(BaseRule):
    """
    Checks for general citation best practices based on the IBM Style Guide.
    This includes rules for cross-references, titles, and quotations.
    """
    def _get_rule_type(self) -> str:
        return "citations_general_guidelines"

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """
        Analyzes the text for general citation guideline violations.

        Args:
            text: The full text to analyze.
            sentences: A list of sentences from the text.
            nlp: A loaded spaCy NLP model, passed from the main application.

        Returns:
            A list of dictionaries, where each dictionary represents a found error.
        """
        if not nlp:
            return []
            
        errors = []
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            
            doc = nlp(sentence)
            
            # Enhanced comprehensive analysis with morphological pattern detection
            errors.extend(self._check_cross_reference_patterns_comprehensive(doc, sentence, i))
            errors.extend(self._check_title_formatting_comprehensive(doc, sentence, i))
            errors.extend(self._check_quotation_editing_comprehensive(doc, sentence, i))
            errors.extend(self._check_citation_structure_patterns(doc, sentence, i))
            
        return errors

    def _detect_cross_reference_patterns(self, doc):
        """
        Comprehensive detection of cross-reference patterns using morphological analysis.
        Handles various permutations and combinations of reference structures.
        """
        patterns = []
        
        # Enhanced cross-reference terms with morphological variations
        cross_ref_base_terms = {
            'appendix', 'bibliography', 'chapter', 'contents', 'figure', 
            'glossary', 'part', 'preface', 'table', 'volume', 'section',
            'page', 'paragraph', 'subsection', 'annex', 'attachment'
        }
        
        # Reference verbs and prepositions
        reference_indicators = {'see', 'refer', 'check', 'consult', 'view', 'examine'}
        reference_prepositions = {'in', 'on', 'at', 'to', 'for', 'from'}
        
        for i, token in enumerate(doc):
            if token.lemma_.lower() in cross_ref_base_terms:
                pattern = {
                    'token': token,
                    'index': i,
                    'type': 'cross_reference',
                    'context': self._analyze_reference_context(doc, i),
                    'has_number': False,
                    'reference_strength': 0.0  # Confidence that this is a cross-reference
                }
                
                # Check for reference context indicators
                window_start = max(0, i - 4)
                window_end = min(len(doc), i + 4)
                
                for j in range(window_start, window_end):
                    check_token = doc[j]
                    
                    # Reference verbs increase confidence
                    if check_token.lemma_.lower() in reference_indicators:
                        pattern['reference_strength'] += 0.4
                    
                    # Reference prepositions in context
                    elif check_token.lemma_.lower() in reference_prepositions:
                        pattern['reference_strength'] += 0.2
                    
                    # Numbers or identifiers after the reference term
                    elif j > i and (check_token.like_num or check_token.pos_ == 'NUM'):
                        pattern['has_number'] = True
                        pattern['reference_strength'] += 0.3
                    
                    # Check for dependency relationships
                    if check_token.head == token or token.head == check_token:
                        pattern['reference_strength'] += 0.2
                
                patterns.append(pattern)
        
        return patterns

    def _analyze_reference_context(self, doc, token_index):
        """
        Analyze the morphological context around a potential cross-reference.
        """
        token = doc[token_index]
        context = {
            'dependency_role': token.dep_,
            'parent_pos': token.head.pos_,
            'is_object': token.dep_ in ['dobj', 'pobj', 'nmod'],
            'follows_verb': False,
            'in_prepositional_phrase': False
        }
        
        # Check if follows a verb within reasonable distance
        for i in range(max(0, token_index - 3), token_index):
            if doc[i].pos_ == 'VERB':
                context['follows_verb'] = True
                break
        
        # Check if in prepositional phrase
        if token.dep_ == 'pobj':
            context['in_prepositional_phrase'] = True
        
        return context

    def _check_cross_reference_patterns_comprehensive(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Enhanced cross-reference checking with comprehensive morphological analysis.
        """
        issues = []
        patterns = self._detect_cross_reference_patterns(doc)
        
        for pattern in patterns:
            # Only flag if confidence is high enough that this is actually a cross-reference
            if pattern['reference_strength'] >= 0.4:
                token = pattern['token']
                
                if token.is_title:  # Capitalized when it should be lowercase
                    message = f"Cross-reference term '{token.text}' should be lowercase."
                    suggestion = f"In cross-references, use the lowercase form: '{token.lemma_.lower()}' (e.g., 'see {token.lemma_.lower()} 5')."
                    issues.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message=message,
                        suggestions=[suggestion],
                        severity="low",
                        violating_token=token.text
                    ))
        
        return issues

    def _detect_publication_title_patterns(self, doc):
        """
        Comprehensive detection of publication titles using morphological analysis.
        """
        title_patterns = []
        
        # Look for noun phrases that could be titles
        for chunk in doc.noun_chunks:
            if len(chunk) > 1:  # Multi-word titles
                pattern = {
                    'chunk': chunk,
                    'is_title_case': all(t.is_title or not t.is_alpha for t in chunk),
                    'grammatical_role': chunk.root.dep_,
                    'is_quoted': False,
                    'is_italicized': False,  # Would need additional markup analysis
                    'title_confidence': 0.0
                }
                
                # Check grammatical role - titles are often subjects or objects
                if pattern['grammatical_role'] in ['nsubj', 'dobj', 'pobj']:
                    pattern['title_confidence'] += 0.3
                
                # Check for title case
                if pattern['is_title_case']:
                    pattern['title_confidence'] += 0.4
                
                # Check for quotation marks around the chunk
                start_idx = chunk.start
                end_idx = chunk.end
                
                if (start_idx > 0 and doc[start_idx - 1].is_quote and
                    end_idx < len(doc) and doc[end_idx].is_quote):
                    pattern['is_quoted'] = True
                    pattern['title_confidence'] += 0.2
                
                # Check for publication-related context
                pub_context_words = {'published', 'written', 'authored', 'book', 'article', 'journal', 'magazine'}
                for token in doc:
                    if token.lemma_.lower() in pub_context_words:
                        pattern['title_confidence'] += 0.3
                        break
                
                title_patterns.append(pattern)
        
        return title_patterns

    def _check_title_formatting_comprehensive(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Enhanced title formatting check with comprehensive pattern detection.
        """
        issues = []
        title_patterns = self._detect_publication_title_patterns(doc)
        
        for pattern in title_patterns:
            # Only flag potential titles with reasonable confidence
            if pattern['title_confidence'] >= 0.5:
                chunk = pattern['chunk']
                
                if not pattern['is_quoted'] and not pattern['is_italicized']:
                    message = f"Publication title '{chunk.text}' might need emphasis."
                    suggestion = "Style guide recommends using italic font for publication titles. If italics are not possible, consider using quotation marks."
                    issues.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message=message,
                        suggestions=[suggestion],
                        severity="low",
                        violating_token=chunk.text
                    ))
        
        return issues

    def _detect_quotation_edit_patterns(self, doc):
        """
        Comprehensive detection of quotation editing patterns using morphological analysis.
        """
        edit_patterns = []
        in_quote = False
        quote_start = -1
        
        for i, token in enumerate(doc):
            if token.is_quote:
                if not in_quote:
                    in_quote = True
                    quote_start = i
                else:
                    # End of quote - analyze content
                    quote_content = doc[quote_start + 1:i]
                    
                    # Look for editing indicators
                    for j, inner_token in enumerate(quote_content):
                        if inner_token.text in ['...', '…']:
                            # Check if properly bracketed
                            is_bracketed = (j > 0 and quote_content[j-1].text == '[' and
                                          j + 1 < len(quote_content) and quote_content[j+1].text == ']')
                            
                            if not is_bracketed:
                                edit_patterns.append({
                                    'type': 'unbracketed_ellipsis',
                                    'quote_span': (quote_start, i),
                                    'quote_content': quote_content,
                                    'edit_token': inner_token
                                })
                        
                        # Check for other edit indicators
                        elif inner_token.text in ['(', ')'] and self._looks_like_editorial_insertion(quote_content, j):
                            edit_patterns.append({
                                'type': 'parenthetical_edit',
                                'quote_span': (quote_start, i),
                                'quote_content': quote_content,
                                'edit_token': inner_token
                            })
                    
                    in_quote = False
        
        return edit_patterns

    def _looks_like_editorial_insertion(self, quote_content, token_index):
        """
        Determine if parentheses contain editorial insertions using morphological analysis.
        """
        if token_index + 2 < len(quote_content) and quote_content[token_index].text == '(':
            # Look for content between parentheses that looks editorial
            editorial_indicators = {'sic', 'emphasis', 'added', 'clarification', 'note'}
            
            for i in range(token_index + 1, min(len(quote_content), token_index + 4)):
                if quote_content[i].text == ')':
                    break
                if quote_content[i].lemma_.lower() in editorial_indicators:
                    return True
                    
        return False

    def _check_quotation_editing_comprehensive(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Enhanced quotation editing check with comprehensive pattern detection.
        """
        issues = []
        edit_patterns = self._detect_quotation_edit_patterns(doc)
        
        for pattern in edit_patterns:
            quote_content = pattern['quote_content']
            content_text = " ".join(token.text for token in quote_content)
            
            if pattern['type'] == 'unbracketed_ellipsis':
                message = "Omission in a quotation is not marked correctly."
                suggestion = "When omitting text from a quotation, enclose the ellipsis in square brackets: '[...]'."
            elif pattern['type'] == 'parenthetical_edit':
                message = "Editorial insertion in quotation should use square brackets."
                suggestion = "Use square brackets for editorial insertions: '[clarification]' instead of '(clarification)'."
            
            issues.append(self._create_error(
                sentence=sentence, sentence_index=sentence_index, message=message,
                suggestions=[suggestion], severity="medium", violating_token=f'"{content_text}"'
            ))
        
        return issues

    def _check_citation_structure_patterns(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Check for overall citation structure and formatting patterns.
        """
        issues = []
        
        # Check for incomplete citation patterns
        citation_indicators = self._detect_citation_indicators(doc)
        
        for indicator in citation_indicators:
            if indicator['type'] == 'incomplete_citation':
                message = f"Incomplete citation pattern detected: {indicator['issue']}"
                suggestion = indicator['suggestion']
                issues.append(self._create_error(
                    sentence=sentence, sentence_index=sentence_index, message=message,
                    suggestions=[suggestion], severity="medium", violating_token=indicator['token']
                ))
        
        return issues

    def _detect_citation_indicators(self, doc):
        """
        Detect various citation patterns and identify potential issues.
        """
        indicators = []
        
        # Look for author-date patterns that might be incomplete
        for i, token in enumerate(doc):
            # Pattern: Name followed by year in parentheses
            if (token.pos_ == 'PROPN' and i + 3 < len(doc) and 
                doc[i+1].text == '(' and doc[i+2].like_num and doc[i+3].text == ')'):
                
                # Check if missing page numbers or other details
                if not self._has_page_reference_nearby(doc, i):
                    indicators.append({
                        'type': 'incomplete_citation',
                        'issue': 'Author-year citation may be missing page numbers',
                        'suggestion': 'Include page numbers for direct quotes: (Author, 2023, p. 15)',
                        'token': f"{token.text} ({doc[i+2].text})"
                    })
        
        return indicators

    def _has_page_reference_nearby(self, doc, start_index):
        """
        Check if there are page references near a citation using morphological analysis.
        """
        page_indicators = {'p', 'pp', 'page', 'pages'}
        
        # Look in a window around the citation
        window_start = max(0, start_index - 5)
        window_end = min(len(doc), start_index + 8)
        
        for i in range(window_start, window_end):
            if doc[i].lemma_.lower() in page_indicators:
                return True
        
        return False
