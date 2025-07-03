"""
Colons Rule
Based on IBM Style Guide topic: "Colons"
"""
from typing import List, Dict, Any, Set
import re
from .base_punctuation_rule import BasePunctuationRule

class ColonsRule(BasePunctuationRule):
    """
    Comprehensive colon usage checker using morphological spaCy analysis with linguistic anchors.
    Handles multiple colon contexts: lists, explanations, time, ratios, titles, and more.
    """
    
    def _get_rule_type(self) -> str:
        return 'colons'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        
        # Fallback to regex-based analysis if nlp is unavailable
        if not nlp:
            return self._analyze_with_regex(text, sentences)
        
        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            errors.extend(self._analyze_sentence_with_nlp(doc, sentence, i))
            
        return errors

    def _analyze_sentence_with_nlp(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Comprehensive NLP-based colon analysis using linguistic anchors."""
        errors = []
        
        for token in doc:
            if token.text == ':':
                # Skip legitimate contexts using linguistic anchors
                if self._is_legitimate_colon_context(token, doc):
                    continue
                
                # Check various colon usage patterns
                errors.extend(self._check_incomplete_clause_before_colon(token, doc, sentence, sentence_index))
                errors.extend(self._check_verb_colon_pattern(token, doc, sentence, sentence_index))
                errors.extend(self._check_capitalization_after_colon(token, doc, sentence, sentence_index))
                errors.extend(self._check_list_introduction_pattern(token, doc, sentence, sentence_index))
                
        return errors

    def _is_legitimate_colon_context(self, colon_token, doc) -> bool:
        """
        Use linguistic anchors to identify legitimate colon contexts.
        Returns True if colon is in a valid context that should be ignored.
        """
        # Linguistic Anchor: Time expressions (digits:digits)
        if self._is_time_expression(colon_token, doc):
            return True
        
        # Linguistic Anchor: Ratios (number:number)
        if self._is_ratio_expression(colon_token, doc):
            return True
        
        # Linguistic Anchor: URLs and technical paths
        if self._is_technical_context(colon_token, doc):
            return True
        
        # Linguistic Anchor: Title/subtitle patterns (proper noun : title case)
        if self._is_title_subtitle_pattern(colon_token, doc):
            return True
        
        # Linguistic Anchor: Citation patterns
        if self._is_citation_pattern(colon_token, doc):
            return True
        
        return False

    def _is_time_expression(self, colon_token, doc) -> bool:
        """Linguistic anchor: Detect time expressions like 3:30, 12:45."""
        if (colon_token.i > 0 and colon_token.i < len(doc) - 1):
            prev_token = doc[colon_token.i - 1]
            next_token = doc[colon_token.i + 1]
            
            # Check if surrounded by numbers
            if (prev_token.like_num and next_token.like_num):
                # Additional check: typical time format patterns
                if (len(prev_token.text) <= 2 and len(next_token.text) == 2):
                    return True
        return False

    def _is_ratio_expression(self, colon_token, doc) -> bool:
        """Linguistic anchor: Detect ratio expressions like 2:1, 3:4."""
        if (colon_token.i > 0 and colon_token.i < len(doc) - 1):
            prev_token = doc[colon_token.i - 1]
            next_token = doc[colon_token.i + 1]
            
            # Check for number:number pattern in mathematical context
            if (prev_token.like_num and next_token.like_num):
                # Look for mathematical context clues
                context_tokens = doc[max(0, colon_token.i-3):min(len(doc), colon_token.i+4)]
                math_indicators = any(token.lemma_ in {'ratio', 'proportion', 'scale', 'compare', 'versus'} 
                                    for token in context_tokens)
                return math_indicators
        return False

    def _is_technical_context(self, colon_token, doc) -> bool:
        """Linguistic anchor: Detect technical contexts like URLs, file paths."""
        # Check for URL patterns
        sentence_text = doc.text.lower()
        url_indicators = ['http:', 'https:', 'ftp:', 'file:', 'mailto:']
        
        for indicator in url_indicators:
            if indicator in sentence_text:
                # Check if our colon is part of this URL
                colon_pos = colon_token.idx
                url_start = sentence_text.find(indicator)
                if abs(colon_pos - url_start) < 10:  # Colon is near URL indicator
                    return True
        
        # Check for file path patterns using linguistic anchors
        if colon_token.i > 0:
            prev_token = doc[colon_token.i - 1]
            # Drive letter patterns (C:, D:, etc.)
            if (len(prev_token.text) == 1 and prev_token.text.isupper() and 
                prev_token.pos_ in ['NOUN', 'PROPN']):
                return True
        
        return False

    def _is_title_subtitle_pattern(self, colon_token, doc) -> bool:
        """Linguistic anchor: Detect title/subtitle patterns."""
        if colon_token.i > 0 and colon_token.i < len(doc) - 1:
            # Check if preceded by proper noun or title-like structure
            prev_tokens = doc[max(0, colon_token.i-3):colon_token.i]
            next_tokens = doc[colon_token.i+1:min(len(doc), colon_token.i+4)]
            
            # Look for proper nouns or title indicators before colon
            has_title_before = any(token.pos_ == 'PROPN' or token.is_title for token in prev_tokens)
            # Look for capitalized words after colon (subtitle pattern)
            has_subtitle_after = any(token.is_title for token in next_tokens)
            
            return has_title_before and has_subtitle_after
        return False

    def _is_citation_pattern(self, colon_token, doc) -> bool:
        """Linguistic anchor: Detect citation patterns."""
        # Look for academic/citation context
        citation_indicators = {'page', 'vol', 'chapter', 'section', 'verse', 'line'}
        context_tokens = doc[max(0, colon_token.i-3):min(len(doc), colon_token.i+4)]
        
        return any(token.lemma_ in citation_indicators for token in context_tokens)

    def _check_incomplete_clause_before_colon(self, colon_token, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check if colon is preceded by an incomplete clause."""
        errors = []
        
        if colon_token.i == 0:
            return errors
        
        # Analyze the clause before the colon using dependency parsing
        clause_tokens = doc[:colon_token.i]
        
        # Linguistic anchor: Look for incomplete clause indicators
        has_subject = any(token.dep_ in ['nsubj', 'nsubjpass', 'csubj'] for token in clause_tokens)
        has_main_verb = any(token.pos_ == 'VERB' and token.dep_ in ['ROOT', 'ccomp'] for token in clause_tokens)
        
        # Check for incomplete introductory phrases
        incomplete_indicators = any(token.dep_ in ['prep', 'mark'] and token.head.i >= colon_token.i 
                                  for token in clause_tokens)
        
        if incomplete_indicators or (not has_subject and not has_main_verb):
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Colon should be preceded by a complete clause that can stand alone.",
                suggestions=["Rewrite to include a complete clause before the colon.", 
                           "Consider using a different punctuation mark."],
                severity='high'
            ))
        
        return errors

    def _check_verb_colon_pattern(self, colon_token, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Enhanced verb-colon pattern check using linguistic anchors."""
        errors = []
        
        if colon_token.i == 0:
            return errors
        
        prev_token = doc[colon_token.i - 1]
        
        # Linguistic anchor: Check for problematic verb-colon patterns
        if prev_token.pos_ == 'VERB':
            # Check if it's a legitimate context (e.g., reporting verbs)
            if self._is_legitimate_verb_colon_context(prev_token, colon_token, doc):
                return errors
            
            # Check for specific problematic patterns
            if prev_token.dep_ in ['ROOT', 'ccomp']:  # Main verbs
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Colon should not directly follow a main verb without completing the clause.",
                    suggestions=["Complete the clause before the colon.", 
                               "Use 'the following' or similar to introduce the list.",
                               "Consider using a different sentence structure."],
                    severity='medium'
                ))
        
        return errors

    def _is_legitimate_verb_colon_context(self, verb_token, colon_token, doc) -> bool:
        """Check if verb-colon pattern is legitimate (e.g., reporting verbs)."""
        # Linguistic anchor: Reporting verbs that can introduce direct speech/quotations
        if verb_token.lemma_ in {'say', 'state', 'declare', 'announce', 'proclaim', 'assert'}:
            return True
        
        # Check if followed by quoted material
        if colon_token.i < len(doc) - 1:
            following_tokens = doc[colon_token.i + 1:min(len(doc), colon_token.i + 5)]
            has_quotation = any(token.text in ['"', "'", '"', '"'] for token in following_tokens)
            return has_quotation
        
        return False

    def _check_capitalization_after_colon(self, colon_token, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check capitalization after colon using linguistic anchors."""
        errors = []
        
        if colon_token.i >= len(doc) - 1:
            return errors
        
        # Find first non-whitespace token after colon
        next_word_token = None
        for i in range(colon_token.i + 1, len(doc)):
            if doc[i].is_alpha:
                next_word_token = doc[i]
                break
        
        if not next_word_token:
            return errors
        
        # Linguistic anchor: Determine if what follows should be capitalized
        following_tokens = doc[colon_token.i + 1:]
        
        # Check if it's a complete sentence (should be capitalized)
        is_complete_sentence = self._is_complete_sentence_after_colon(following_tokens)
        
        # Check if it's a proper noun (should be capitalized)
        is_proper_noun = next_word_token.pos_ == 'PROPN'
        
        # Apply capitalization rules
        if is_complete_sentence and not next_word_token.text[0].isupper():
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Capitalize the first word after a colon when it begins a complete sentence.",
                suggestions=[f"Capitalize '{next_word_token.text}'."],
                severity='low'
            ))
        elif not is_complete_sentence and not is_proper_noun and next_word_token.text[0].isupper():
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Do not capitalize after a colon unless it's a proper noun or complete sentence.",
                suggestions=[f"Use lowercase '{next_word_token.text.lower()}'."],
                severity='low'
            ))
        
        return errors

    def _is_complete_sentence_after_colon(self, tokens) -> bool:
        """Determine if tokens after colon form a complete sentence."""
        if not tokens:
            return False
        
        # Linguistic anchor: Look for sentence structure
        has_subject = any(token.dep_ in ['nsubj', 'nsubjpass'] for token in tokens)
        has_verb = any(token.pos_ == 'VERB' for token in tokens)
        
        return has_subject and has_verb

    def _check_list_introduction_pattern(self, colon_token, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check if colon properly introduces a list."""
        errors = []
        
        if colon_token.i >= len(doc) - 1:
            return errors
        
        # Check if this appears to be introducing a list
        following_text = doc[colon_token.i + 1:].text.strip()
        
        # Linguistic anchor: Look for list patterns
        list_indicators = [
            r'^\s*[-•*]\s+',  # Bullet points
            r'^\s*\d+\.\s+',  # Numbered lists
            r'^\s*\([a-zA-Z0-9]+\)\s+',  # Lettered/numbered in parentheses
            r'^\s*[a-zA-Z0-9]+\)\s+',  # Simple lettered/numbered
        ]
        
        appears_to_be_list = any(re.match(pattern, following_text) for pattern in list_indicators)
        
        if appears_to_be_list:
            # Check if properly introduced
            clause_before = doc[:colon_token.i]
            
            # Look for proper list introduction phrases using linguistic anchors
            has_list_introduction = any(
                token.lemma_ in {'follow', 'include', 'contain', 'comprise', 'consist'} 
                for token in clause_before
            )
            
            if not has_list_introduction:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Lists should be introduced with phrases like 'the following' or 'include'.",
                    suggestions=["Add an introductory phrase before the colon.", 
                               "Use 'the following' or 'include' to introduce the list."],
                    severity='medium'
                ))
        
        return errors

    def _analyze_with_regex(self, text: str, sentences: List[str]) -> List[Dict[str, Any]]:
        """Fallback regex-based analysis when NLP is unavailable."""
        errors = []
        
        for i, sentence in enumerate(sentences):
            # Basic patterns that can be detected without NLP
            
            # Pattern 1: Colon at start of sentence
            if sentence.strip().startswith(':'):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Sentence should not begin with a colon.",
                    suggestions=["Remove the colon or rewrite the sentence."],
                    severity='high'
                ))
            
            # Pattern 2: Multiple colons in close proximity
            if sentence.count(':') > 1:
                # Check if they're not in legitimate contexts (basic check)
                if not re.search(r'\d+:\d+', sentence):  # Not time expressions
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Multiple colons in one sentence may indicate unclear structure.",
                        suggestions=["Review sentence structure and colon usage."],
                        severity='medium'
                    ))
            
            # Pattern 3: Colon followed immediately by punctuation
            if re.search(r':[.!?;,]', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Colon should not be immediately followed by other punctuation.",
                    suggestions=["Remove redundant punctuation after the colon."],
                    severity='medium'
                ))
        
        return errors
