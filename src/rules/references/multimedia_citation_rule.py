"""
This file implements the MultimediaCitationRule for the writing style linter.
It focuses on codifying the guidelines for citing online multimedia such as
videos and podcasts, as described in the IBM Style Guide.

The rule uses pure spaCy morphological analysis and linguistic anchors to identify
incomplete citations for multimedia content.
"""

from typing import List, Dict, Any

# Handle imports for different contexts
try:
    from ..base_rule import BaseRule
except ImportError:
    from base_rule import BaseRule


class MultimediaCitationRule(BaseRule):
    """
    Checks for proper citation of videos, podcasts, and other online multimedia.
    """
    def _get_rule_type(self) -> str:
        return "citations_multimedia"

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """
        Analyzes the text for issues related to citing online multimedia.

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
            errors.extend(self._check_multimedia_link_context(doc, sentence, i))
            
        return errors

    def _check_multimedia_link_context(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Flags incomplete citations for multimedia links.
        Rule: When linking to a video, include the term "video" and the name of the hosting site.
        """
        issues = []
        media_type_lemmas = {'video', 'podcast', 'webcast', 'webinar'}
        
        # Linguistic Anchor: Find tokens that spaCy identifies as URLs.
        for url_token in doc:
            if not url_token.like_url:
                continue

            # Contextual Analysis: Check the entire sentence for required components.
            has_media_type = False
            has_hosting_site = False

            for token in doc:
                # Morphological Check 1: Is a media type mentioned?
                if token.lemma_.lower() in media_type_lemmas:
                    has_media_type = True

                # Syntactic/Morphological Check 2: Is a hosting site mentioned?
                # A hosting site is often a proper noun that is the object of a preposition (e.g., "on YouTube").
                if token.dep_ == 'pobj' and token.head.pos_ == 'ADP':
                    # The object of the preposition should be a proper noun or organization.
                    if token.pos_ == 'PROPN' or token.ent_type_ == 'ORG':
                        has_hosting_site = True
            
            # If the citation is incomplete, create an error.
            if not has_media_type or not has_hosting_site:
                missing_parts = []
                if not has_media_type:
                    missing_parts.append("the media type (e.g., 'video', 'podcast')")
                if not has_hosting_site:
                    missing_parts.append("the name of the hosting site (e.g., 'on YouTube')")
                
                message = f"Incomplete citation for multimedia link. Missing: {', '.join(missing_parts)}."
                suggestion = "When linking to multimedia, include the media type and the name of the hosting site. Example: 'For more information, watch the overview video on YouTube.'"
                
                issues.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message=message,
                    suggestions=[suggestion],
                    severity="medium",
                    violating_token=url_token.text
                ))

        return issues
