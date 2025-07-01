"""
This file implements the IbmDocumentationRule for the writing style linter.
It focuses on codifying the guidelines for citing IBM's official product
documentation platform, as described in the IBM Style Guide.

The rule uses pure spaCy morphological analysis and linguistic anchors to
identify outdated terminology and incorrect naming conventions.
"""

from typing import List, Dict, Any

# Handle imports for different contexts
try:
    from ..base_rule import BaseRule
except ImportError:
    from base_rule import BaseRule


class IbmDocumentationRule(BaseRule):
    """
    Checks for proper citation when referring to IBM Documentation.
    """
    def _get_rule_type(self) -> str:
        return "citations_ibm_documentation"

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """
        Analyzes the text for issues related to citing IBM Documentation.

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
            
            # Enhanced checks with morphological pattern variations
            errors.extend(self._check_for_outdated_terms_comprehensive(doc, sentence, i))
            errors.extend(self._check_improper_naming_comprehensive(doc, sentence, i))
            errors.extend(self._check_alternative_outdated_patterns(doc, sentence, i))
            
        return errors

    def _detect_knowledge_center_patterns(self, doc):
        """
        Uses comprehensive morphological analysis to detect various "Knowledge Center" patterns.
        Handles permutations like: Knowledge Center, Knowledge Centre, Knowledge Base, etc.
        """
        patterns = []
        
        for i, token in enumerate(doc):
            # Base pattern: "Knowledge" + related terms
            if token.lemma_.lower() == "knowledge":
                # Look for various combinations within a window
                window_end = min(len(doc), i + 3)  # Extended window for complex patterns
                for j in range(i + 1, window_end):
                    next_token = doc[j]
                    
                    # Skip articles and prepositions in between
                    if next_token.pos_ in ['DET', 'ADP']:
                        continue
                        
                    # Check for various knowledge-related terms
                    knowledge_terms = {'center', 'centre', 'base', 'repository', 'hub', 'portal'}
                    if next_token.lemma_.lower() in knowledge_terms:
                        patterns.append(('knowledge_center_variant', (token, next_token), i, j))
                        break
                        
            # Compound patterns: "IBM Knowledge" + term
            elif token.text.upper() == "IBM" and i + 2 < len(doc):
                if doc[i+1].lemma_.lower() == "knowledge":
                    knowledge_terms = {'center', 'centre', 'base', 'repository', 'hub', 'portal'}
                    if doc[i+2].lemma_.lower() in knowledge_terms:
                        patterns.append(('ibm_knowledge_variant', (token, doc[i+1], doc[i+2]), i, i+2))
        
        return patterns

    def _check_for_outdated_terms_comprehensive(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Enhanced detection of outdated terminology with morphological pattern matching.
        Handles various permutations: Knowledge Center/Centre, Knowledge Base, etc.
        """
        issues = []
        
        # Use comprehensive pattern detection
        patterns = self._detect_knowledge_center_patterns(doc)
        
        for pattern_type, tokens, start_idx, end_idx in patterns:
            if pattern_type == 'knowledge_center_variant':
                token1, token2 = tokens
                outdated_phrase = f"{token1.text} {token2.text}"
                message = f"Outdated term '{outdated_phrase}' was used."
                suggestion = "Refer to the service as 'IBM Documentation' or 'IBM Docs'."
                
            elif pattern_type == 'ibm_knowledge_variant':
                token1, token2, token3 = tokens
                outdated_phrase = f"{token1.text} {token2.text} {token3.text}"
                message = f"Outdated IBM terminology '{outdated_phrase}' was used."
                suggestion = "Use the current terminology: 'IBM Documentation' or 'IBM Docs'."
            
            issues.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=message,
                suggestions=[suggestion],
                severity="high",
                violating_token=outdated_phrase
            ))
        
        return issues

    def _check_alternative_outdated_patterns(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Detects additional outdated patterns using morphological analysis.
        """
        issues = []
        
        # Check for "IBM Information Center" - another outdated term
        for i, token in enumerate(doc):
            if (token.text.upper() == "IBM" and 
                i + 2 < len(doc) and 
                doc[i+1].lemma_.lower() == "information" and
                doc[i+2].lemma_.lower() in ['center', 'centre']):
                
                outdated_phrase = f"{token.text} {doc[i+1].text} {doc[i+2].text}"
                message = f"Outdated term '{outdated_phrase}' was used."
                suggestion = "Use the current terminology: 'IBM Documentation' or 'IBM Docs'."
                issues.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message=message,
                    suggestions=[suggestion],
                    severity="high",
                    violating_token=outdated_phrase
                ))
        
        return issues

    def _detect_ibm_documentation_patterns(self, doc):
        """
        Comprehensive detection of IBM Documentation/Docs patterns with morphological analysis.
        """
        patterns = []
        
        for i, token in enumerate(doc):
            if token.text.upper() == "IBM":
                # Look for Documentation/Docs within reasonable distance
                window_end = min(len(doc), i + 4)  # Allow for articles/prepositions
                
                for j in range(i + 1, window_end):
                    next_token = doc[j]
                    
                    # Skip intervening articles, prepositions, and conjunctions
                    if next_token.pos_ in ['DET', 'ADP', 'CCONJ']:
                        continue
                    
                    # Check for documentation variants
                    doc_terms = {'documentation', 'docs', 'document', 'documents'}
                    if next_token.lemma_.lower() in doc_terms:
                        # Check for preceding article
                        article_token = None
                        if i > 0 and doc[i-1].lemma_.lower() in ['a', 'an', 'the']:
                            article_token = doc[i-1]
                        
                        patterns.append({
                            'type': 'ibm_docs_pattern',
                            'ibm_token': token,
                            'doc_token': next_token,
                            'article_token': article_token,
                            'start_idx': i,
                            'doc_idx': j
                        })
                        break
        
        return patterns

    def _check_improper_naming_comprehensive(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Enhanced naming check with comprehensive morphological pattern detection.
        Handles various permutations and combinations of IBM Documentation patterns.
        """
        issues = []
        
        # Use comprehensive pattern detection
        patterns = self._detect_ibm_documentation_patterns(doc)
        
        for pattern in patterns:
            ibm_token = pattern['ibm_token']
            doc_token = pattern['doc_token']
            article_token = pattern['article_token']
            
            # Check for incorrect article usage
            if article_token:
                full_phrase = f"{article_token.text} {ibm_token.text} {doc_token.text}"
                message = f"Incorrect article usage with '{ibm_token.text} {doc_token.text}'."
                suggestion = f"Remove the article. Use '{ibm_token.text} {doc_token.text}' without 'a', 'an', or 'the'."
                issues.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message=message,
                    suggestions=[suggestion],
                    severity="medium",
                    violating_token=full_phrase
                ))
        
        # Check for standalone documentation terms
        standalone_patterns = self._detect_standalone_doc_terms(doc)
        for pattern in standalone_patterns:
            doc_token = pattern['doc_token']
            message = f"The term '{doc_token.text}' should be preceded by 'IBM'."
            suggestion = f"Always use 'IBM {doc_token.text}' when referring to the documentation service."
            issues.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=message,
                suggestions=[suggestion],
                severity="medium",
                violating_token=doc_token.text
            ))
        
        return issues

    def _detect_standalone_doc_terms(self, doc):
        """
        Detects standalone documentation terms that should be preceded by 'IBM'.
        """
        patterns = []
        doc_terms = {'documentation', 'docs', 'document', 'documents'}
        
        for i, token in enumerate(doc):
            if token.lemma_.lower() in doc_terms:
                # Check if NOT preceded by IBM within reasonable distance
                is_preceded_by_ibm = False
                
                # Look back for IBM within a small window
                window_start = max(0, i - 3)
                for j in range(window_start, i):
                    if doc[j].text.upper() == "IBM":
                        # Check if there are only articles/prepositions between IBM and docs
                        intervening_tokens = doc[j+1:i]
                        if all(t.pos_ in ['DET', 'ADP', 'CCONJ'] for t in intervening_tokens):
                            is_preceded_by_ibm = True
                            break
                
                if not is_preceded_by_ibm:
                    # Additional context check - avoid false positives
                    if self._is_likely_ibm_documentation_context(doc, token):
                        patterns.append({
                            'type': 'standalone_doc_term',
                            'doc_token': token,
                            'index': i
                        })
        
        return patterns

    def _is_likely_ibm_documentation_context(self, doc, token):
        """
        Uses contextual morphological analysis to determine if a standalone doc term
        is likely referring to IBM Documentation.
        """
        # Look for IBM context words in the broader sentence
        ibm_context_words = {'ibm', 'product', 'service', 'platform', 'portal', 'site', 'website'}
        
        for doc_token in doc:
            if doc_token != token and doc_token.lemma_.lower() in ibm_context_words:
                return True
        
        # Check for capitalization patterns that suggest proper noun usage
        if token.is_title and not token.is_sent_start:
            return True
            
        return False
