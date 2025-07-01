"""
This file implements the OnlineInformationRule for the writing style linter.
It focuses on codifying the guidelines for citing online sources as described
in the Style Guide.

The rule uses pure spaCy morphological analysis and linguistic anchors to identify
vague link text and links to potentially unreliable sources.
"""

import re
from typing import List, Dict, Any, Optional

# Handle imports for different contexts
try:
    from ..base_rule import BaseRule
except ImportError:
    from base_rule import BaseRule


class OnlineInformationRule(BaseRule):
    """
    Checks for best practices when citing online information, such as websites and blogs.
    """
    def _get_rule_type(self) -> str:
        return "citations_online_information"

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """
        Analyzes the text for issues related to citing online sources.

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
            
            errors.extend(self._check_for_vague_link_text(doc, sentence, i))
            errors.extend(self._check_for_unreliable_links(doc, sentence, i))
            
        return errors

    def _check_for_vague_link_text(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Flags vague link text such as 'click here'.
        Rule: Use meaningful link text that describes the destination.
        """
        issues = []
        # Linguistic Anchor: Find the token "here".
        for token in doc:
            if token.lemma_.lower() == "here":
                # Syntactic Check: Check if its grammatical head is 'click'.
                if token.head.lemma_.lower() == "click":
                    message = "Avoid vague link text like 'click here'."
                    suggestion = "Use meaningful link text that describes the destination (e.g., 'For more details, see the Style Guide.')."
                    issues.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message=message,
                        suggestions=[suggestion],
                        severity="high",
                        violating_token=f"{token.head.text} {token.text}"
                    ))
        return issues
        
    def _check_for_unreliable_links(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Identifies links to potentially unreliable sources using morphological analysis.
        Rule: Link to authoritative, stable sources.
        """
        issues = []
        
        # Linguistic Anchor: Find tokens that spaCy identifies as URLs.
        for token in doc:
            if token.like_url:
                # Morphological Analysis: Check domain characteristics
                url_text = token.text.lower()
                
                # Check for blog indicators using morphological patterns
                has_blog_indicators = any(blog_term in url_text for blog_term in ['blog', 'wordpress', 'blogspot'])
                
                # Check for wiki indicators
                has_wiki_indicators = 'wiki' in url_text
                
                # Check for personal/social indicators
                has_personal_indicators = any(personal_term in url_text for personal_term in ['~', '/users/', '/people/', 'medium.com'])
                
                # Use morphological analysis to identify potentially unreliable characteristics
                if has_blog_indicators or has_wiki_indicators or has_personal_indicators:
                    # Contextual Check: Look for authoritative indicators in surrounding context
                    is_authoritative = self._check_authoritative_context(doc, token)
                    
                    if not is_authoritative:
                        source_type = "blog" if has_blog_indicators else "wiki" if has_wiki_indicators else "personal"
                        message = f"Link to '{token.text}' appears to be from a {source_type} source."
                        suggestion = "Link to authoritative, stable sources. Consider official documentation, academic papers, or established technical resources."
                        issues.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message=message,
                            suggestions=[suggestion],
                            severity="medium",
                            violating_token=token.text
                        ))
        return issues
    
    def _check_authoritative_context(self, doc, url_token) -> bool:
        """
        Uses morphological analysis to check if the URL is presented in an authoritative context.
        """
        # Look for authoritative indicators in the surrounding tokens
        window_start = max(0, url_token.i - 3)
        window_end = min(len(doc), url_token.i + 4)
        context_tokens = doc[window_start:window_end]
        
        authoritative_indicators = {'official', 'documentation', 'specification', 'standard', 'reference'}
        
        for token in context_tokens:
            if token.lemma_.lower() in authoritative_indicators:
                return True
                
        # Check for organizational entities that might indicate authority
        for ent in doc.ents:
            if ent.label_ == 'ORG' and abs(ent.start - url_token.i) <= 5:
                return True
                
        return False
