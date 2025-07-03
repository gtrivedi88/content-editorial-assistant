"""
Second Person Rule
Version: 2.2

Description:
This rule encourages the use of the second person ("you") in user-facing and
instructional content, aligning with the IBM Style Guide. It uses SpaCy's
advanced linguistic features (Part-of-Speech tagging, dependency parsing,
and morphological analysis) to perform a context-aware analysis, minimizing
hard-coded rules and enhancing scalability.

Core Logic:
1.  Context Analysis: First, it determines the document's context (e.g.,
    is it instructional, technical, user-facing?). This is done using a
    weighted system based on linguistic cues.
2.  Pronoun/Substitute Detection: It identifies first-person pronouns,
    third-person pronouns, and nouns used as substitutes for "you" (like
    "the user," "an administrator").
3.  Evaluation: Based on the context, it evaluates whether the detected
    pronoun or substitute should be flagged for conversion to the second
    person. A key part of this is distinguishing between directly addressing
    the user ("You click OK") versus describing an action that affects them
    ("This feature helps users").
4.  Suggestion Generation: It provides targeted, helpful suggestions for
    making the text more direct and user-focused.
"""

from typing import List, Dict, Any, Set, Tuple, Optional
from collections import defaultdict
import re

# Handle imports for different contexts
try:
    from .base_rule import BaseRule
except ImportError:
    from base_rule import BaseRule

class SecondPersonRule(BaseRule):
    """
    A rule to enforce second-person ("you") usage in appropriate contexts,
    leveraging pure SpaCy morphological and dependency analysis.
    """
    
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'second_person'
    
    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for opportunities to use the second person.
        """
        errors = []
        if not nlp:
            return self._run_fallback_analysis(sentences)

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            person_issues = self._find_person_usage_issues(doc)
            
            for issue in person_issues:
                suggestions = self._generate_person_suggestions(issue)
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message=self._create_person_message(issue),
                    suggestions=suggestions,
                    severity=self._determine_person_severity(issue),
                    person_issue=issue
                ))
        
        return errors

    def _find_person_usage_issues(self, doc) -> List[Dict[str, Any]]:
        """
        Finds person usage issues using a pipeline of linguistic analysis.
        """
        issues = []
        context_analysis = self._analyze_document_context(doc)
        
        if not context_analysis.get('is_user_facing') and not context_analysis.get('is_instructional'):
            first_person_patterns = [p for p in self._extract_pronoun_patterns(doc) if p['person'] == 'first']
            if not first_person_patterns:
                 return []
        
        pronoun_patterns = self._extract_pronoun_patterns(doc)
        
        for pattern in pronoun_patterns:
            person_issue = self._evaluate_person_usage(pattern, context_analysis, doc)
            if person_issue:
                issues.append(person_issue)
        
        return issues

    def _analyze_document_context(self, doc) -> Dict[str, Any]:
        """
        Analyzes document context to determine the appropriate person usage.
        """
        return {
            'is_instructional': self._detect_instructional_content(doc),
            'is_technical_documentation': self._detect_technical_documentation(doc),
            'is_user_facing': self._detect_user_facing_content(doc),
            'has_imperatives': self._detect_imperative_mood(doc)
        }

    def _detect_instructional_content(self, doc) -> bool:
        """
        Detects instructional content using a weighted score of linguistic cues.
        """
        instructional_indicators = 0
        for token in doc:
            if self._is_imperative_verb(token):
                instructional_indicators += 2
            if self._has_instructional_keywords(token):
                instructional_indicators += 1.5
            if self._is_instructional_modal(token):
                if token.lemma_.lower() in ["can", "may", "might"]:
                    instructional_indicators += 0.5
                else:
                    instructional_indicators += 1
        return instructional_indicators >= 2

    def _detect_technical_documentation(self, doc) -> bool:
        """
        Detects highly formal or technical documentation.
        """
        technical_indicators = 0
        for ent in doc.ents:
            if self._is_technical_entity(ent):
                technical_indicators += 1
        if self._has_formal_documentation_structure(doc):
            technical_indicators += 2
        return technical_indicators >= 2

    def _detect_user_facing_content(self, doc) -> bool:
        """
        Detects if the content is aimed at an end-user.
        """
        user_facing_indicators = 0
        if any(self._determine_grammatical_person(token) == 'first' for token in doc if token.pos_ == 'PRON'):
            user_facing_indicators += 3
        for token in doc:
            if token.lemma_.lower() in self._get_user_related_terms():
                user_facing_indicators += 1
        if self._has_interactive_language_patterns(doc) or self._has_action_oriented_language(doc):
            user_facing_indicators += 2
        return user_facing_indicators >= 1

    def _is_imperative_verb(self, token) -> bool:
        """Checks if a verb is in the imperative mood."""
        if token.pos_ == "VERB" and token.morph.get("Mood") == ["Imp"]:
            return True
        if token.dep_ == "ROOT" and not any(c.dep_ in ("nsubj", "nsubjpass") for c in token.children):
            return True
        return False

    def _get_instructional_modals(self) -> Set[str]:
        """Returns a set of modal verbs often used in instructions."""
        return {"should", "must", "need", "have", "can", "may", "might", "could"}

    def _is_instructional_modal(self, token) -> bool:
        """Checks if a token is an instructional modal verb."""
        return token.pos_ == "AUX" and token.lemma_.lower() in self._get_instructional_modals()

    def _get_user_related_terms(self) -> Set[str]:
        """Returns a set of nouns that refer to users."""
        return {
            "user", "customer", "client", "visitor", "person", "people", 
            "individual", "developer", "admin", "administrator", "member", 
            "participant", "team", "personnel", "author", "writer", "editor"
        }

    def _has_instructional_keywords(self, token) -> bool:
        """Checks for common instructional verbs."""
        keywords = {"configure", "setup", "install", "update", "enter", "select", 
                    "choose", "click", "navigate", "access", "ensure", "make sure"}
        return token.lemma_.lower() in keywords

    def _has_action_oriented_language(self, doc) -> bool:
        """Checks for verbs that imply direct user action."""
        action_verbs = {"save", "submit", "process", "upload", "download", "create", 
                        "delete", "edit", "modify", "view", "check", "verify", "confirm"}
        return any(token.lemma_.lower() in action_verbs for token in doc)

    def _is_technical_entity(self, ent) -> bool:
        """Checks if a named entity is likely a technical term."""
        return ent.label_ in ["PRODUCT", "WORK_OF_ART"]

    def _has_formal_documentation_structure(self, doc) -> bool:
        """Checks for structures common in formal docs, like numbered lists."""
        return any(token.like_num and token.dep_ == "nummod" for token in doc)
        
    def _has_interactive_language_patterns(self, doc) -> bool:
        """Checks for language patterns common in interactive UI instructions."""
        interactive_verbs = {"click", "select", "choose", "enter", "type", "navigate"}
        return any(token.lemma_.lower() in interactive_verbs for token in doc)

    def _detect_imperative_mood(self, doc) -> bool:
        """Detects if the sentence contains at least one imperative verb."""
        return any(self._is_imperative_verb(token) for token in doc)

    def _extract_pronoun_patterns(self, doc) -> List[Dict[str, Any]]:
        """Extracts pronouns and their substitutes (e.g., 'the user')."""
        patterns = []
        for token in doc:
            if token.pos_ == "PRON" and token.lemma_.lower() in self._get_relevant_pronouns():
                patterns.append(self._analyze_pronoun_context(token))
            elif token.pos_ in ["NOUN", "PROPN"] and token.lemma_.lower() in self._get_user_related_terms():
                patterns.append(self._analyze_pronoun_substitute_context(token))
        return patterns
        
    def _get_relevant_pronouns(self) -> Set[str]:
        """Returns pronouns that are candidates for conversion to 'you'."""
        return {"i", "we", "us", "me", "my", "our", "they", "them", "he", "she", "it", "one"}

    def _analyze_pronoun_context(self, token) -> Dict[str, Any]:
        """Analyzes the grammatical context of a pronoun."""
        return {
            'token': token,
            'pronoun': token.text,
            'person': self._determine_grammatical_person(token),
            'semantic_role': self._analyze_semantic_role(token)
        }

    def _analyze_pronoun_substitute_context(self, token) -> Dict[str, Any]:
        """Analyzes the context of a noun substituting for a pronoun."""
        return {
            'token': token,
            'pronoun': token.text,
            'person': 'third',
            'semantic_role': self._analyze_semantic_role(token),
            'is_substitute': True
        }

    def _determine_grammatical_person(self, token) -> str:
        """Determines grammatical person using morphology."""
        person_map = token.morph.get("Person")
        if person_map:
            if "1" in person_map: return 'first'
            if "2" in person_map: return 'second'
            if "3" in person_map: return 'third'
        lemma = token.lemma_.lower()
        if lemma in {"i", "we", "us", "me", "my", "our"}: return 'first'
        if lemma in {"you", "your"}: return 'second'
        return 'third'

    def _analyze_semantic_role(self, token) -> str:
        """Analyzes the semantic role using dependency parsing."""
        dep_role = token.dep_
        if dep_role in ["nsubj", "nsubjpass"]:
            return 'agent'
        if dep_role in ["dobj", "iobj", "pobj"]:
            return 'patient'
        if dep_role == "poss":
            return 'possessor'
        return 'other'

    def _evaluate_person_usage(self, pattern, context, doc) -> Optional[Dict[str, Any]]:
        """Evaluates if the pronoun usage is inappropriate for the context."""
        if pattern['person'] == 'second':
            return None

        if self._should_use_second_person(pattern, context, doc):
            return {
                'type': 'inappropriate_person_usage',
                'current_person': pattern['person'],
                'pronoun_pattern': pattern,
                'position': pattern['token'].i
            }
        return None

    def _should_use_second_person(self, pattern, context, doc) -> bool:
        """
        Core decision logic: determines if conversion to second person is appropriate.
        """
        if pattern['person'] == 'first':
            return True
        if context['is_user_facing'] and context['is_instructional']:
            return self._is_addressing_users_directly(pattern, doc)
        if context['has_imperatives'] and not context.get('is_technical_documentation'):
            return self._is_addressing_users_directly(pattern, doc)
        return False

    def _is_addressing_users_directly(self, pattern, doc) -> bool:
        """
        Distinguishes between addressing users ("You click...") vs. describing them
        ("This helps users...").
        """
        token = pattern['token']
        if pattern['semantic_role'] == 'patient':
            verb = token.head
            if verb.pos_ == "VERB" and verb.lemma_.lower() in {"help", "allow", "enable", "inform"}:
                return False
        if pattern['semantic_role'] == 'agent' and self._has_action_oriented_language(doc):
            return True
        return True

    def _generate_person_suggestions(self, issue: Dict[str, Any]) -> List[str]:
        """Generates helpful, context-aware suggestions."""
        suggestions = []
        pattern = issue['pronoun_pattern']
        conversion_suggestion = self._get_conversion_suggestion(pattern)
        
        suggestions.append(f"Replace '{pattern['pronoun']}' with '{conversion_suggestion}' for direct user address")
        suggestions.append("Use second person 'you' in instructional content for clarity")
        suggestions.append("Address users directly with 'you' in user-facing content")
        suggestions.append("Second person creates more engaging, direct communication")
        if pattern['person'] == 'first':
            suggestions.append("Avoid first person in user documentation unless necessary")
        return suggestions

    def _get_conversion_suggestion(self, pattern) -> str:
        """Generates the specific word to suggest (e.g., 'you', 'your')."""
        if pattern['semantic_role'] == 'possessor':
            return 'your'
        return 'you'

    def _create_person_message(self, issue: Dict[str, Any]) -> str:
        """Creates the primary error message."""
        pronoun = issue['pronoun_pattern']['pronoun']
        return f"Consider using 'you' instead of '{pronoun}' to directly address the user"

    def _determine_person_severity(self, issue: Dict[str, Any]) -> str:
        """Determines the severity based on the context of the issue."""
        return 'medium'

    def _run_fallback_analysis(self, sentences: List[str]) -> List[Dict[str, Any]]:
        """
        A very basic fallback for when SpaCy is not available.
        """
        errors = []
        first_person_pattern = r'\b(I|we|us|me|my|our)\b'
        user_substitute_pattern = r'\b(users?|administrators?|developers?)\b'

        for i, sentence in enumerate(sentences):
            for match in re.finditer(first_person_pattern, sentence, re.IGNORECASE):
                errors.append(self._create_error(
                    sentence=sentence, sentence_index=i,
                    message=f"Consider using 'you' instead of '{match.group()}'",
                    suggestions=["Avoid first-person pronouns in technical documentation."],
                    severity='low'
                ))
            if any(word in sentence.lower() for word in ['click', 'select', 'enter']):
                for match in re.finditer(user_substitute_pattern, sentence, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sentence, sentence_index=i,
                        message=f"Consider using 'you' instead of '{match.group()}'",
                        suggestions=["Address the user directly with 'you'."],
                        severity='medium'
                    ))
        return errors