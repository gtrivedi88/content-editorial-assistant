"""
This file implements the SpecialIbmPublicationsRule for the writing style linter.
It focuses on codifying the guidelines for citing special IBM publications, such as
IBM Redbooks, as described in the IBM Style Guide.

The rule uses pure spaCy morphological analysis and linguistic anchors to identify
improperly formatted trademarked publication names.
"""

from typing import List, Dict, Any

# Handle imports for different contexts
try:
    from ..base_rule import BaseRule
except ImportError:
    from base_rule import BaseRule

class SpecialIbmPublicationsRule(BaseRule):
    """
    Checks for proper citation of special IBM publications like IBM Redbooks.
    """
    def _get_rule_type(self) -> str:
        return "citations_special_ibm_pubs"

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """
        Analyzes the text for issues related to citing special IBM publications.

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
        # Enhanced first-mention tracking using morphological analysis
        full_doc = nlp(text.lower())
        is_first_mention = not self._detect_prior_redbooks_mention(full_doc)

        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            
            doc = nlp(sentence)
            
            # Enhanced checks with comprehensive pattern detection
            errors.extend(self._check_redbooks_citation_comprehensive(doc, sentence, i, is_first_mention))
            errors.extend(self._check_redbooks_variations(doc, sentence, i))
            
            # Update first mention tracking with morphological analysis
            if is_first_mention and self._contains_valid_redbooks_mention(doc):
                is_first_mention = False
            
        return errors

    def _detect_prior_redbooks_mention(self, full_doc):
        """
        Uses morphological analysis to detect if "IBM Redbooks" has been mentioned earlier.
        """
        redbook_patterns = self._detect_redbooks_patterns(full_doc)
        
        for pattern in redbook_patterns:
            if (pattern['has_ibm'] and 
                pattern['redbooks_token'].text == "Redbooks" and 
                pattern.get('has_publication', False)):
                return True
        return False

    def _detect_redbooks_patterns(self, doc):
        """
        Comprehensive detection of Redbooks-related patterns using morphological analysis.
        Handles various permutations: Red Books, red books, RedBooks, etc.
        """
        patterns = []
        
        for i, token in enumerate(doc):
            # Base pattern: Look for "redbook" lemma or text variations
            is_redbook_variant = (
                token.lemma_.lower() == "redbook" or
                "redbook" in token.text.lower() or
                token.text.lower() in ["redbooks", "red-books", "red_books"] or
                (token.text.lower() == "red" and i + 1 < len(doc) and 
                 doc[i+1].text.lower() in ["book", "books"])
            )
            
            if is_redbook_variant:
                pattern = {
                    'redbooks_token': token,
                    'index': i,
                    'has_ibm': False,
                    'has_publication': False,
                    'has_trademark': False,
                    'form_issues': []
                }
                
                # Look for IBM within a reasonable window
                window_start = max(0, i - 3)
                window_end = min(len(doc), i + 4)
                
                for j in range(window_start, window_end):
                    check_token = doc[j]
                    
                    # Check for IBM
                    if check_token.text.upper() == "IBM":
                        pattern['has_ibm'] = True
                    
                    # Check for "publication"
                    elif check_token.lemma_.lower() == "publication":
                        pattern['has_publication'] = True
                    
                    # Check for trademark symbols
                    elif "®" in check_token.text or "™" in check_token.text:
                        pattern['has_trademark'] = True
                
                # Analyze form issues
                if token.text != "Redbooks":
                    if token.text.lower() == "redbook":
                        pattern['form_issues'].append('singular_instead_of_plural')
                    elif token.text == "redbooks":
                        pattern['form_issues'].append('lowercase_instead_of_capitalized')
                    elif "red" in token.text.lower() and "book" in token.text.lower():
                        pattern['form_issues'].append('separated_or_hyphenated')
                    else:
                        pattern['form_issues'].append('incorrect_capitalization')
                
                patterns.append(pattern)
        
        return patterns

    def _check_redbooks_citation_comprehensive(self, doc, sentence: str, sentence_index: int, is_first_mention: bool) -> List[Dict[str, Any]]:
        """
        Enhanced Redbooks citation checking with comprehensive morphological analysis.
        Handles various permutations and combinations of citation patterns.
        """
        issues = []
        
        # Use comprehensive pattern detection
        patterns = self._detect_redbooks_patterns(doc)
        
        for pattern in patterns:
            redbooks_token = pattern['redbooks_token']
            
            # Check 1: Form issues (incorrect spelling/capitalization)
            for form_issue in pattern['form_issues']:
                if form_issue == 'singular_instead_of_plural':
                    message = f"Incorrect form '{redbooks_token.text}' used for trademarked term."
                    suggestion = "Always use 'Redbooks' (plural, with an initial capital letter)."
                elif form_issue == 'lowercase_instead_of_capitalized':
                    message = f"Incorrect capitalization '{redbooks_token.text}' used for trademarked term."
                    suggestion = "Always use 'Redbooks' (with an initial capital letter)."
                elif form_issue == 'separated_or_hyphenated':
                    message = f"Incorrect form '{redbooks_token.text}' used for trademarked term."
                    suggestion = "Use 'Redbooks' as a single word, not separated or hyphenated."
                else:
                    message = f"Incorrect form '{redbooks_token.text}' used for trademarked term."
                    suggestion = "Always use 'Redbooks' (plural, with an initial capital letter)."
                
                issues.append(self._create_error(
                    sentence=sentence, sentence_index=sentence_index, message=message,
                    suggestions=[suggestion], severity="high", violating_token=redbooks_token.text
                ))
                continue  # Move to next pattern after finding form issue
            
            # Check 2: Missing "publication" requirement
            if not pattern['has_publication']:
                message = "The term 'Redbooks' should be followed by 'publication'."
                suggestion = "Use the full phrase 'Redbooks publication'."
                issues.append(self._create_error(
                    sentence=sentence, sentence_index=sentence_index, message=message,
                    suggestions=[suggestion], severity="medium", violating_token=redbooks_token.text
                ))
            
            # Check 3: First reference requirements
            if is_first_mention:
                if not pattern['has_ibm']:
                    message = "First reference to 'Redbooks' must be preceded by 'IBM'."
                    suggestion = "On first use, cite the full name: 'IBM Redbooks publication'."
                    issues.append(self._create_error(
                        sentence=sentence, sentence_index=sentence_index, message=message,
                        suggestions=[suggestion], severity="high", violating_token=redbooks_token.text
                    ))
                
                if not pattern['has_trademark']:
                    message = "First reference to 'IBM Redbooks' should include the registered trademark symbol (®)."
                    suggestion = "On first use, write 'IBM Redbooks® publication'."
                    issues.append(self._create_error(
                        sentence=sentence, sentence_index=sentence_index, message=message,
                        suggestions=[suggestion], severity="low", violating_token=redbooks_token.text
                    ))
        
        return issues

    def _check_redbooks_variations(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Checks for common variations and alternative terms that should be standardized.
        """
        issues = []
        
        # Check for alternative terms that might refer to Redbooks
        alternative_terms = {
            'redbook': 'Use "Redbooks" (plural) instead',
            'red book': 'Use "Redbooks" (single word) instead', 
            'red books': 'Use "Redbooks" (single word, capitalized) instead',
            'red-book': 'Use "Redbooks" (no hyphen) instead',
            'red-books': 'Use "Redbooks" (no hyphen) instead'
        }
        
        # Create spans for multi-word detection
        text_lower = sentence.lower()
        for alt_term, suggestion in alternative_terms.items():
            if alt_term in text_lower:
                # Use morphological analysis to confirm it's not part of another context
                if self._is_likely_redbooks_context(doc, alt_term):
                    message = f"Alternative term '{alt_term}' found that should be standardized."
                    issues.append(self._create_error(
                        sentence=sentence, sentence_index=sentence_index, 
                        message=message, suggestions=[suggestion], 
                        severity="medium", violating_token=alt_term
                    ))
                    break  # One error per sentence to avoid redundancy
        
        return issues

    def _is_likely_redbooks_context(self, doc, alt_term):
        """
        Uses morphological analysis to determine if an alternative term is likely referring to IBM Redbooks.
        """
        # Look for IBM context
        has_ibm_context = any(token.text.upper() == "IBM" for token in doc)
        
        # Look for publication/documentation context
        pub_terms = {'publication', 'document', 'documentation', 'series', 'library'}
        has_pub_context = any(token.lemma_.lower() in pub_terms for token in doc)
        
        # Look for technical context (common in Redbooks citations)
        tech_terms = {'technical', 'guide', 'manual', 'reference', 'tutorial', 'implementation'}
        has_tech_context = any(token.lemma_.lower() in tech_terms for token in doc)
        
        return has_ibm_context or has_pub_context or has_tech_context

    def _contains_valid_redbooks_mention(self, doc):
        """
        Check if the sentence contains a valid Redbooks mention for first-use tracking.
        """
        patterns = self._detect_redbooks_patterns(doc)
        
        for pattern in patterns:
            if (pattern['has_ibm'] and 
                not pattern['form_issues'] and 
                pattern['redbooks_token'].text == "Redbooks"):
                return True
        return False