"""
Word Usage Rule for words starting with 'S'.
Pure morphological analysis using linguistic anchors.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class SWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'S',
    using pure morphological analysis with linguistic anchors.
    """
    
    def _get_rule_type(self) -> str:
        return 'word_usage_s'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for S-word violations using pure morphological analysis.
        Uses linguistic anchors for context-aware detection.
        
        Args:
            text: Original text string
            sentences: List of sentences 
            nlp: SpaCy model for morphological analysis
            context: Additional context (unused)
            
        Returns:
            List of error dictionaries
        """
        errors = []
        
        if not nlp or not text.strip():
            return errors
            
        # Process text with SpaCy for morphological analysis
        doc = nlp(text)
            
        # LINGUISTIC ANCHOR 1: setup/set up - Verb vs Noun/Adjective distinction
        for token in doc:
            if token.lemma_.lower() == "setup":
                # Morphological check: If tagged as VERB, should be "set up"
                if token.pos_ == "VERB":
                    errors.append(self._create_error(
                        message="Verb form error: Use 'set up' (two words) for verbs",
                        suggestions=["Change 'setup' to 'set up' when used as a verb"],
                        sentence=token.sent.text,
                        sentence_index=self._get_sentence_index(doc, token.sent),
                        flagged_text=token.text,
                        severity='high'
                    ))
                    
                # Morphological check: If part of verb phrase, should be "set up"
                elif token.dep_ in ["aux", "auxpass"] or any(child.pos_ == "VERB" for child in token.children):
                    errors.append(self._create_error(
                        message="Verb phrase error: Use 'set up' (two words) in verb phrases",
                        suggestions=["Change 'setup' to 'set up' in verb constructions"],
                        sentence=token.sent.text,
                        sentence_index=self._get_sentence_index(doc, token.sent),
                        flagged_text=token.text,
                        severity='high'
                    ))

        # LINGUISTIC ANCHOR 2: shutdown/shut down - Part-of-speech based distinction
        for token in doc:
            # Check for "shut down" used as compound noun (should be "shutdown")
            if (token.lemma_.lower() == "shut" and 
                token.i + 1 < len(doc) and 
                doc[token.i + 1].lemma_.lower() == "down"):
                
                next_token = doc[token.i + 1]
                
                # Morphological anchor: compound modifier or noun phrase
                if (token.dep_ in ["compound", "amod"] or 
                    next_token.dep_ in ["compound", "amod"] or
                    any(child.pos_ == "NOUN" for child in token.head.children)):
                    
                    errors.append(self._create_error(
                        message="Compound noun error: Use 'shutdown' (one word) for nouns/adjectives",
                        suggestions=["Change 'shut down' to 'shutdown' when used as noun or adjective"],
                        sentence=token.sent.text,
                        sentence_index=self._get_sentence_index(doc, token.sent),
                        flagged_text=f"{token.text} {next_token.text}",
                        severity='medium'
                    ))
            
            # Check for "shutdown" used as verb (should be "shut down")
            elif token.lemma_.lower() == "shutdown" and token.pos_ == "VERB":
                errors.append(self._create_error(
                    message="Verb form error: Use 'shut down' (two words) for verbs",
                    suggestions=["Change 'shutdown' to 'shut down' when used as a verb"],
                    sentence=token.sent.text,
                    sentence_index=self._get_sentence_index(doc, token.sent),
                    flagged_text=token.text,
                    severity='medium'
                ))

        # LINGUISTIC ANCHOR 3: Modal verb weakness - shall/should detection
        for token in doc:
            if token.lemma_.lower() in ["shall", "should"] and token.tag_ == "MD":
                # Morphological context: Check if this is a requirement context
                sent_text_lower = token.sent.text.lower()
                
                # Strong linguistic indicators of requirements
                requirement_indicators = ["must", "required", "mandatory", "necessary"]
                is_requirement_context = any(indicator in sent_text_lower for indicator in requirement_indicators)
                
                if is_requirement_context or self._is_imperative_context(token):
                    errors.append(self._create_error(
                        message=f"Weak modal in requirements: '{token.text}' lacks authority",
                        suggestions=["Use 'must' for requirements or imperative mood ('Click Save')"],
                        sentence=token.sent.text,
                        sentence_index=self._get_sentence_index(doc, token.sent),
                        flagged_text=token.text,
                        severity='medium'
                    ))

        # LINGUISTIC ANCHOR 4: Inclusive language - morphological pattern matching
        inclusive_language_map = {
            "slave": {
                "suggestions": ["Use inclusive alternatives: 'secondary', 'replica', 'worker', 'agent'"],
                "severity": "high"
            },
            "sanity check": {
                "suggestions": ["Use professional alternatives: 'validation', 'verification', 'review'"], 
                "severity": "high"
            },
            "segregate": {
                "suggestions": ["Use neutral term: 'separate', 'isolate', 'partition'"],
                "severity": "high"
            }
        }
        
        # Process each sentence for pattern matching
        for sent in doc.sents:
            sent_text_lower = sent.text.lower()
            for pattern, details in inclusive_language_map.items():
                if pattern in sent_text_lower:
                    # Find exact position using regex
                    for match in re.finditer(r'\b' + re.escape(pattern) + r'\b', sent.text, re.IGNORECASE):
                        errors.append(self._create_error(
                            message=f"Language concern: Review usage of '{match.group()}'",
                            suggestions=details['suggestions'],
                            sentence=sent.text,
                            sentence_index=self._get_sentence_index(doc, sent),
                            flagged_text=match.group(),
                            severity=details['severity']
                        ))

        # LINGUISTIC ANCHOR 5: Formatting consistency - morphological detection
        formatting_corrections = {
            "screen shot": {"correct": "screenshot", "severity": "low"},
            "stand-alone": {"correct": "standalone", "severity": "low"},
            "server-side": {"correct": "serverside", "severity": "low"}
        }
        
        for sent in doc.sents:
            for incorrect, details in formatting_corrections.items():
                for match in re.finditer(r'\b' + re.escape(incorrect) + r'\b', sent.text, re.IGNORECASE):
                    errors.append(self._create_error(
                        message=f"Formatting: Use '{details['correct']}' (single word)",
                        suggestions=[f"Change '{match.group()}' to '{details['correct']}'"],
                        sentence=sent.text,
                        sentence_index=self._get_sentence_index(doc, sent),
                        flagged_text=match.group(),
                        severity=details['severity']
                    ))

        return errors

    def _get_sentence_index(self, doc, target_sent) -> int:
        """Get the index of a sentence within the document."""
        for i, sent in enumerate(doc.sents):
            if sent.start == target_sent.start:
                return i
        return 0

    def _is_imperative_context(self, token) -> bool:
        """
        Check if modal is in imperative/instruction context using morphological clues.
        """
        sent = token.sent
        
        # Look for imperative markers in the sentence
        imperative_markers = []
        for sent_token in sent:
            # Imperative often starts with base form verbs
            if (sent_token.pos_ == "VERB" and 
                sent_token.tag_ in ["VB", "VBP"] and 
                sent_token.dep_ == "ROOT"):
                imperative_markers.append(sent_token)
        
        # Check for second person context (instructions)
        has_second_person = any(t.lemma_.lower() in ["you", "your"] for t in sent)
        
        return len(imperative_markers) > 0 or has_second_person
