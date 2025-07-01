"""
This file implements the ThirdPartyPublicationsRule for the writing style linter.
It focuses on codifying the guidelines for citing publications from other
organizations or individuals, as described in the IBM Style Guide.

The rule uses pure spaCy morphological analysis and linguistic anchors to identify
incomplete or improperly formatted third-party citations.
"""

import re
from typing import List, Dict, Any

# Handle imports for different contexts
try:
    from ..base_rule import BaseRule
except ImportError:
    from base_rule import BaseRule


class ThirdPartyPublicationsRule(BaseRule):
    """
    Checks for proper citation of publications from other organizations or individuals.
    """
    def __init__(self):
        super().__init__()

    def _get_rule_type(self) -> str:
        return "citations_third_party_pubs"

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """
        Analyzes the text for issues related to citing third-party publications.

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
            errors.extend(self._check_citation_completeness(doc, sentence, i))
            
        return errors

    def _detect_publication_context(self, doc):
        """
        Uses morphological analysis to detect publication citation contexts.
        """
        publication_indicators = []
        
        # Morphological Analysis: Look for publication-related patterns
        publication_terms = {'report', 'study', 'survey', 'analysis', 'whitepaper', 'paper', 'research', 'publication'}
        citation_verbs = {'according', 'states', 'reports', 'found', 'shows', 'indicates'}
        
        # Check for publication terminology
        for token in doc:
            if token.lemma_.lower() in publication_terms:
                publication_indicators.append(('publication_term', token))
            elif token.lemma_.lower() in citation_verbs:
                publication_indicators.append(('citation_verb', token))
        
        # Check for organizational entities (potential publishers)
        for ent in doc.ents:
            if ent.label_ == 'ORG' and ent.text.lower() != 'ibm':
                # Use morphological analysis to determine if it's likely a publisher/research org
                if self._is_likely_publisher(ent):
                    publication_indicators.append(('publisher', ent))
        
        return publication_indicators

    def _is_likely_publisher(self, org_entity):
        """
        Uses morphological patterns to identify likely publishers.
        """
        org_text = org_entity.text.lower()
        
        # Morphological patterns that suggest research/publishing organizations
        publisher_patterns = [
            'research' in org_text,
            'institute' in org_text,
            'foundation' in org_text,
            'group' in org_text,
            'consulting' in org_text,
            'inc' in org_text or 'corp' in org_text,
            len(org_text.split()) == 1 and org_text.isupper(),  # Acronyms like "IDC", "NASA"
        ]
        
        return any(publisher_patterns)

    def _check_citation_completeness(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Flags incomplete citations for third-party publications using morphological analysis.
        Rule: A citation should include the title, organization name, and date.
        """
        issues = []
        
        # Linguistic Anchor: Use morphological analysis to detect publication contexts
        publication_context = self._detect_publication_context(doc)
        
        if not publication_context:
            return []
        
        # Extract publishers from the context
        publishers = [item[1] for item in publication_context if item[0] == 'publisher']
        
        if not publishers:
            return []
        
        for publisher in publishers:
            # Morphological & Contextual Analysis: Check for required citation components
            has_date = any(e.label_ == 'DATE' for e in doc.ents)
            has_title = self._find_publication_title(doc)
            has_url = any(t.like_url for t in doc)
            is_title_quoted = self._check_quoted_title(doc)

            # Check for incompleteness.
            if not (has_title and has_date):
                message = f"Incomplete citation for third-party publication from '{publisher.text}'."
                suggestion = "Citations for publications from other organizations should include the title, organization name, and date."
                issues.append(self._create_error(
                    sentence=sentence, sentence_index=sentence_index, message=message,
                    suggestions=[suggestion], severity="medium", violating_token=publisher.text
                ))
            
            # Check for incorrect formatting (URL present but title not quoted).
            if has_url and has_title and not is_title_quoted:
                message = f"Citation with a URL may be missing quotation marks around the title."
                suggestion = "For printed material citations that include a URL, the title should be enclosed in quotation marks."
                issues.append(self._create_error(
                    sentence=sentence, sentence_index=sentence_index, message=message,
                    suggestions=[suggestion], severity="low", violating_token=publisher.text
                ))

            # One analysis per sentence is sufficient to avoid duplicate errors
            break
                
        return issues

    def _find_publication_title(self, doc) -> bool:
        """
        Uses morphological analysis to determine if a publication title is present.
        """
        # Check for quotation marks indicating titles
        if any(token.is_quote for token in doc):
            return True
            
        # Morphological Check: Look for noun chunks that are in title case.
        for chunk in doc.noun_chunks:
            if len(chunk) > 1:  # Multi-word titles are more likely
                # Check if all alphabetic tokens in the chunk are title-cased.
                if all(t.is_title or not t.is_alpha for t in chunk):
                    return True
        
        return False

    def _check_quoted_title(self, doc) -> bool:
        """
        Uses morphological analysis to check if titles are properly quoted.
        """
        return any(token.is_quote for token in doc)
