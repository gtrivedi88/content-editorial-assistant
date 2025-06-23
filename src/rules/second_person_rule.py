"""
Second Person Rule - Encourages direct address using "you" unless technical context demands otherwise.
Uses SpaCy POS tagging, dependency parsing, and context analysis to detect pronoun usage patterns.
"""

from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict

# Handle imports for different contexts
try:
    from .base_rule import BaseRule
except ImportError:
    from base_rule import BaseRule

class SecondPersonRule(BaseRule):
    """Rule to encourage second person usage using pure SpaCy linguistic analysis."""
    
    def _get_rule_type(self) -> str:
        return 'second_person'
    
    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """Analyze text for second person usage opportunities using pure SpaCy analysis."""
        errors = []
        
        for i, sentence in enumerate(sentences):
            if nlp:
                doc = nlp(sentence)
                person_issues = self._find_person_usage_issues(doc, sentence)
            else:
                # Fallback: Basic pattern analysis without SpaCy
                person_issues = self._find_person_usage_issues_fallback(sentence)
            
            # Create errors for each person usage issue found
            for issue in person_issues:
                suggestions = self._generate_person_suggestions(issue, doc if nlp else None)
                
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message=self._create_person_message(issue),
                    suggestions=suggestions,
                    severity=self._determine_person_severity(issue),
                    person_issue=issue
                ))
        
        return errors
    
    def _find_person_usage_issues(self, doc, sentence) -> List[Dict[str, Any]]:
        """Find person usage issues using advanced SpaCy linguistic analysis."""
        issues = []
        
        # Step 1: Analyze document context to determine if it's user-facing
        context_analysis = self._analyze_document_context(doc)
        
        # Step 2: Find pronoun usage patterns using SpaCy POS and dependency analysis
        pronoun_patterns = self._extract_pronoun_patterns(doc)
        
        # Step 3: Detect inappropriate person usage based on context
        for pattern in pronoun_patterns:
            person_issue = self._evaluate_person_usage(pattern, context_analysis, doc)
            if person_issue:
                issues.append(person_issue)
        
        return issues
    
    def _analyze_document_context(self, doc) -> Dict[str, Any]:
        """Analyze document context using SpaCy to determine appropriate person usage."""
        context = {
            'is_instructional': False,
            'is_technical_documentation': False,
            'is_user_facing': False,
            'has_imperatives': False,
            'formality_level': 'neutral'
        }
        
        # Method 1: Detect instructional content using dependency patterns
        context['is_instructional'] = self._detect_instructional_content(doc)
        
        # Method 2: Detect technical documentation using domain analysis
        context['is_technical_documentation'] = self._detect_technical_documentation(doc)
        
        # Method 3: Detect user-facing content using semantic analysis
        context['is_user_facing'] = self._detect_user_facing_content(doc)
        
        # Method 4: Detect imperative mood using morphological analysis
        context['has_imperatives'] = self._detect_imperative_mood(doc)
        
        # Method 5: Analyze formality level using lexical features
        context['formality_level'] = self._analyze_formality_level(doc)
        
        return context
    
    def _detect_instructional_content(self, doc) -> bool:
        """Detect instructional content using SpaCy dependency and POS analysis."""
        instructional_indicators = 0
        
        for token in doc:
            # Method 1: Look for imperative verbs using morphological analysis
            if self._is_imperative_verb(token):
                instructional_indicators += 1
            
            # Method 2: Look for instructional phrases using dependency patterns
            if self._has_instructional_dependency_pattern(token, doc):
                instructional_indicators += 1
            
            # Method 3: Look for modal verbs indicating instruction
            if self._is_instructional_modal(token):
                instructional_indicators += 1
            
            # Method 4: Look for instructional keywords
            if self._has_instructional_keywords(token):
                instructional_indicators += 1
        
        # Lowered threshold for better detection
        return instructional_indicators >= 1
    
    def _is_imperative_verb(self, token) -> bool:
        """Check if verb is imperative using SpaCy morphological analysis."""
        if token.pos_ == "VERB":
            # Method 1: Check morphological features for imperative mood
            if token.morph:
                morph_str = str(token.morph)
                if "Mood=Imp" in morph_str:
                    return True
            
            # Method 2: Check dependency patterns typical of imperatives
            if token.dep_ == "ROOT" and not self._has_explicit_subject(token, token.doc):
                return True
        
        return False
    
    def _has_explicit_subject(self, verb_token, doc) -> bool:
        """Check if verb has explicit subject using dependency analysis."""
        for child in verb_token.children:
            if child.dep_ in ["nsubj", "nsubjpass"]:
                return True
        return False
    
    def _has_instructional_dependency_pattern(self, token, doc) -> bool:
        """Check for instructional dependency patterns using SpaCy parsing."""
        # Look for patterns like "to verb", "must verb", "should verb"
        if token.pos_ == "VERB":
            for child in token.children:
                if child.dep_ == "aux" and child.lemma_.lower() in ["must", "should", "need", "have"]:
                    return True
            
            # Check for infinitive constructions
            if token.dep_ == "xcomp" and token.head.lemma_.lower() in ["need", "want", "try"]:
                return True
        
        return False
    
    def _is_instructional_modal(self, token) -> bool:
        """Check for instructional modal verbs using morphological analysis."""
        if token.pos_ == "AUX" or token.pos_ == "VERB":
            instructional_modals = self._extract_instructional_modals()
            return token.lemma_.lower() in instructional_modals
        return False
    
    def _extract_instructional_modals(self) -> List[str]:
        """Extract instructional modal verbs using linguistic patterns."""
        return ["should", "must", "need", "have", "can", "may", "might", "could"]
    
    def _detect_technical_documentation(self, doc) -> bool:
        """Detect technical documentation using domain-specific analysis."""
        technical_indicators = 0
        
        # Method 1: Look for technical terminology using named entities
        for ent in doc.ents:
            if self._is_technical_entity(ent):
                technical_indicators += 1
        
        # Method 2: Look for code-like patterns using morphological analysis
        for token in doc:
            if self._is_technical_term(token):
                technical_indicators += 1
        
        # Method 3: Look for formal documentation patterns
        if self._has_formal_documentation_structure(doc):
            technical_indicators += 2
        
        # Increased threshold to be less aggressive about technical detection
        return technical_indicators >= 4
    
    def _is_technical_entity(self, ent) -> bool:
        """Check if entity is technical using SpaCy NER analysis."""
        # Technical entities often have specific labels
        technical_labels = ["ORG", "PRODUCT", "CARDINAL", "MONEY"]
        
        if ent.label_ in technical_labels:
            return True
        
        # Check for technical naming patterns
        if self._has_technical_naming_pattern(ent.text):
            return True
        
        return False
    
    def _has_technical_naming_pattern(self, text: str) -> bool:
        """Check for technical naming patterns using morphological analysis."""
        import re
        
        # Technical terms often have specific patterns
        patterns = [
            r'[A-Z]+[a-z]*[A-Z]',  # CamelCase
            r'[a-z]+_[a-z]+',      # snake_case
            r'[A-Z]{2,}',          # UPPERCASE
            r'\d+\.\d+',           # Version numbers
        ]
        
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _is_technical_term(self, token) -> bool:
        """Check if token is technical using morphological analysis."""
        # Method 1: Check for technical suffixes
        technical_suffixes = self._extract_technical_suffixes()
        for suffix in technical_suffixes:
            if token.lemma_.lower().endswith(suffix):
                return True
        
        # Method 2: Check for technical POS patterns
        if token.pos_ == "NOUN" and self._has_technical_morphology(token):
            return True
        
        return False
    
    def _extract_technical_suffixes(self) -> List[str]:
        """Extract technical suffixes using morphological patterns."""
        return ["ware", "system", "protocol", "interface", "framework", "library", "module"]
    
    def _has_technical_morphology(self, token) -> bool:
        """Check for technical morphological features."""
        # Technical terms often have specific morphological patterns
        if token.is_alpha and token.is_lower and len(token.text) > 6:
            return True
        return False
    
    def _has_formal_documentation_structure(self, doc) -> bool:
        """Check for formal documentation structure using syntactic analysis."""
        # Look for formal documentation patterns
        formal_indicators = 0
        
        # Method 1: Look for numbered lists or structured content
        for token in doc:
            if token.like_num and token.dep_ == "nummod":
                formal_indicators += 1
        
        # Method 2: Look for formal connectives
        formal_connectives = ["therefore", "furthermore", "moreover", "consequently"]
        for token in doc:
            if token.lemma_.lower() in formal_connectives:
                formal_indicators += 1
        
        return formal_indicators >= 2
    
    def _detect_user_facing_content(self, doc) -> bool:
        """Detect user-facing content using semantic analysis."""
        user_facing_indicators = 0
        
        # Method 1: Look for user-related terminology using semantic fields
        user_terms = self._extract_user_related_terms()
        for token in doc:
            if token.lemma_.lower() in user_terms:
                user_facing_indicators += 1
        
        # Method 2: Look for interactive language patterns
        if self._has_interactive_language_patterns(doc):
            user_facing_indicators += 2
        
        # Method 3: Look for help/guide language using semantic analysis
        if self._has_help_language_patterns(doc):
            user_facing_indicators += 1
        
        # Method 4: Look for action-oriented language
        if self._has_action_oriented_language(doc):
            user_facing_indicators += 1
        
        # Lowered threshold for better detection
        return user_facing_indicators >= 1
    
    def _extract_user_related_terms(self) -> List[str]:
        """Extract user-related terms using semantic field analysis."""
        return ["user", "customer", "client", "visitor", "person", "people", "individual", 
                "developer", "admin", "administrator", "member", "participant"]
    
    def _has_interactive_language_patterns(self, doc) -> bool:
        """Check for interactive language patterns using dependency analysis."""
        # Look for patterns that suggest interaction
        interactive_patterns = ["click", "select", "choose", "enter", "type", "navigate", "access"]
        
        for token in doc:
            if token.lemma_.lower() in interactive_patterns:
                return True
        
        return False
    
    def _has_help_language_patterns(self, doc) -> bool:
        """Check for help/guide language using semantic analysis."""
        help_patterns = ["help", "guide", "tutorial", "instruction", "step", "how"]
        
        for token in doc:
            if token.lemma_.lower() in help_patterns:
                return True
        
        return False
    
    def _detect_imperative_mood(self, doc) -> bool:
        """Detect imperative mood using morphological analysis."""
        imperative_count = 0
        
        for token in doc:
            if self._is_imperative_verb(token):
                imperative_count += 1
        
        return imperative_count >= 1
    
    def _analyze_formality_level(self, doc) -> str:
        """Analyze formality level using lexical and morphological features."""
        formal_indicators = 0
        informal_indicators = 0
        
        for token in doc:
            # Method 1: Check for formal vocabulary using morphological analysis
            if self._is_formal_vocabulary(token):
                formal_indicators += 1
            
            # Method 2: Check for informal vocabulary
            elif self._is_informal_vocabulary(token):
                informal_indicators += 1
        
        # Method 3: Check sentence structure complexity
        if self._has_complex_sentence_structure(doc):
            formal_indicators += 2
        
        if formal_indicators > informal_indicators + 2:
            return 'formal'
        elif informal_indicators > formal_indicators:
            return 'informal'
        else:
            return 'neutral'
    
    def _is_formal_vocabulary(self, token) -> bool:
        """Check for formal vocabulary using morphological analysis."""
        # Formal words often have specific morphological patterns
        formal_suffixes = ["tion", "sion", "ance", "ence", "ment", "ity"]
        
        for suffix in formal_suffixes:
            if token.lemma_.lower().endswith(suffix) and len(token.text) > 6:
                return True
        
        return False
    
    def _is_informal_vocabulary(self, token) -> bool:
        """Check for informal vocabulary using lexical analysis."""
        informal_words = ["yeah", "ok", "okay", "stuff", "thing", "really", "pretty", "kind", "sort"]
        return token.lemma_.lower() in informal_words
    
    def _has_complex_sentence_structure(self, doc) -> bool:
        """Check for complex sentence structure using dependency analysis."""
        # Complex sentences often have subordinate clauses
        subordinate_indicators = 0
        
        for token in doc:
            if token.dep_ in ["ccomp", "xcomp", "acl", "advcl"]:
                subordinate_indicators += 1
        
        return subordinate_indicators >= 2
    
    def _extract_pronoun_patterns(self, doc) -> List[Dict[str, Any]]:
        """Extract pronoun usage patterns using SpaCy POS and dependency analysis."""
        patterns = []
        
        for token in doc:
            if self._is_relevant_pronoun(token):
                pattern = self._analyze_pronoun_context(token, doc)
                if pattern:
                    patterns.append(pattern)
            
            # Also check for pronoun substitutes like "users", "customers", etc.
            elif self._is_pronoun_substitute(token):
                pattern = self._analyze_pronoun_substitute_context(token, doc)
                if pattern:
                    patterns.append(pattern)
        
        return patterns
    
    def _is_relevant_pronoun(self, token) -> bool:
        """Check if pronoun is relevant for person analysis using POS tagging."""
        if token.pos_ == "PRON":
            # Focus on personal pronouns that could be converted to second person
            relevant_pronouns = self._extract_relevant_pronouns()
            return token.lemma_.lower() in relevant_pronouns
        
        return False
    
    def _extract_relevant_pronouns(self) -> List[str]:
        """Extract pronouns relevant for person conversion using morphological analysis."""
        return ["i", "we", "us", "they", "them", "he", "she", "it", "one"]
    
    def _analyze_pronoun_context(self, pronoun_token, doc) -> Dict[str, Any]:
        """Analyze pronoun context using dependency and semantic analysis."""
        context = {
            'pronoun': pronoun_token.text,
            'lemma': pronoun_token.lemma_.lower(),
            'person': self._determine_grammatical_person(pronoun_token),
            'position': pronoun_token.i,
            'dependency_role': pronoun_token.dep_,
            'sentence_function': self._analyze_sentence_function(pronoun_token, doc),
            'semantic_role': self._analyze_semantic_role(pronoun_token, doc)
        }
        
        return context
    
    def _determine_grammatical_person(self, pronoun_token) -> str:
        """Determine grammatical person using morphological analysis."""
        first_person = ["i", "we", "us", "me", "my", "our"]
        second_person = ["you", "your", "yours"]
        third_person = ["he", "she", "it", "they", "them", "his", "her", "its", "their", "one"]
        
        lemma = pronoun_token.lemma_.lower()
        
        if lemma in first_person:
            return 'first'
        elif lemma in second_person:
            return 'second'
        elif lemma in third_person:
            return 'third'
        else:
            return 'unknown'
    
    def _analyze_sentence_function(self, pronoun_token, doc) -> str:
        """Analyze sentence function using dependency analysis."""
        # Determine what role the sentence plays
        root = [token for token in doc if token.dep_ == "ROOT"][0] if doc else None
        
        if root:
            if root.pos_ == "VERB":
                # Check if it's imperative, declarative, or interrogative
                if self._is_imperative_verb(root):
                    return 'imperative'
                elif any(child.dep_ == "nsubj" for child in root.children):
                    return 'declarative'
                else:
                    return 'other'
        
        return 'unknown'
    
    def _analyze_semantic_role(self, pronoun_token, doc) -> str:
        """Analyze semantic role using dependency and context analysis."""
        # Determine who the pronoun refers to in context
        dep_role = pronoun_token.dep_
        
        if dep_role in ["nsubj", "nsubjpass"]:
            return 'agent'  # The one performing the action
        elif dep_role in ["dobj", "iobj", "pobj"]:
            return 'patient'  # The one receiving the action
        elif dep_role in ["poss"]:
            return 'possessor'  # Showing ownership
        else:
            return 'other'
    
    def _evaluate_person_usage(self, pattern, context_analysis, doc) -> Dict[str, Any]:
        """Evaluate if pronoun usage should be converted to second person."""
        current_person = pattern['person']
        
        # Don't suggest changes if already using second person
        if current_person == 'second':
            return None
        
        # Determine if second person would be more appropriate
        should_use_second_person = self._should_use_second_person(pattern, context_analysis)
        
        if should_use_second_person:
            return {
                'type': 'inappropriate_person_usage',
                'current_person': current_person,
                'suggested_person': 'second',
                'pronoun_pattern': pattern,
                'context': context_analysis,
                'position': pattern['position'],
                'conversion_suggestion': self._generate_conversion_suggestion(pattern)
            }
        
        return None
    
    def _should_use_second_person(self, pattern, context_analysis) -> bool:
        """Determine if second person usage is more appropriate."""
        # Method 1: Check if content is user-facing and instructional
        if context_analysis['is_user_facing'] and context_analysis['is_instructional']:
            # Additional check: ensure we're addressing users, not talking about them
            if pattern.get('is_substitute', False):
                if not self._is_addressing_users_directly(pattern, context_analysis):
                    return False
            return True
        
        # Method 2: Check if content has imperatives (usually addresses user directly)
        if context_analysis['has_imperatives'] and not context_analysis['is_technical_documentation']:
            # For imperatives, be more careful about user substitutes
            if pattern.get('is_substitute', False):
                if not self._is_addressing_users_directly(pattern, context_analysis):
                    return False
            return True
        
        # Method 3: Check if first person is used in user-facing content
        if (pattern['person'] == 'first' and 
            context_analysis['is_user_facing'] and 
            context_analysis['formality_level'] != 'formal'):
            return True
        
        # Method 4: Check for pronoun substitutes in user-facing content
        if (pattern.get('is_substitute', False) and 
            context_analysis['is_user_facing'] and
            self._is_addressing_users_directly(pattern, context_analysis)):
            return True
        
        # Method 5: Check for instructional content with third person pronouns
        if (pattern['person'] == 'third' and 
            context_analysis['is_instructional'] and 
            not context_analysis['is_technical_documentation']):
            return True
        
        # Method 6: Avoid second person in formal technical documentation
        if context_analysis['is_technical_documentation'] and context_analysis['formality_level'] == 'formal':
            return False
        
        return False
    
    def _is_addressing_users_directly(self, pattern, context_analysis) -> bool:
        """Check if the content is directly addressing users vs talking about them."""
        # Method 1: Check sentence function - imperatives usually address users
        sentence_function = pattern.get('sentence_function', '')
        if sentence_function == 'imperative':
            # Check if the imperative is about helping/instructing users (indirect)
            # vs telling users what to do (direct)
            semantic_role = pattern.get('semantic_role', '')
            if semantic_role == 'patient':  # Users are receiving the action, not performing it
                return False  # "Help users" - talking about users, not to them
        
        # Method 2: Check dependency role of the user substitute
        dep_role = pattern.get('dependency_role', '')
        if dep_role in ['dobj', 'iobj', 'pobj']:  # Users as object of action
            return False  # "Help users", "for users" - about users, not to them
        
        # Method 3: Check if user substitute is subject of action they should perform
        if dep_role in ['nsubj', 'nsubjpass'] and context_analysis.get('is_instructional', False):
            return True  # "Users should click" - directly instructing users
        
        return True  # Default to direct addressing
    
    def _generate_conversion_suggestion(self, pattern) -> str:
        """Generate specific conversion suggestion using morphological analysis."""
        current_pronoun = pattern['lemma']
        semantic_role = pattern['semantic_role']
        
        # Map pronouns to second person equivalents based on grammatical role
        if semantic_role == 'agent':  # Subject position
            if current_pronoun in ['i', 'we']:
                return 'you'
            elif current_pronoun in ['they', 'he', 'she', 'it', 'one']:
                return 'you'
        elif semantic_role == 'patient':  # Object position
            if current_pronoun in ['me', 'us']:
                return 'you'
            elif current_pronoun in ['them', 'him', 'her', 'it']:
                return 'you'
        elif semantic_role == 'possessor':  # Possessive
            if current_pronoun in ['my', 'our']:
                return 'your'
            elif current_pronoun in ['their', 'his', 'her', 'its']:
                return 'your'
        
        return 'you'  # Default fallback
    
    def _generate_person_suggestions(self, issue: Dict[str, Any], doc=None) -> List[str]:
        """Generate suggestions for person usage issues."""
        suggestions = []
        
        current_person = issue.get('current_person', '')
        pronoun_pattern = issue.get('pronoun_pattern', {})
        conversion_suggestion = issue.get('conversion_suggestion', 'you')
        
        current_pronoun = pronoun_pattern.get('pronoun', '')
        
        # Method 1: Specific conversion suggestion
        suggestions.append(f"Replace '{current_pronoun}' with '{conversion_suggestion}' for direct user address")
        
        # Method 2: Context-specific guidance
        context = issue.get('context', {})
        if context.get('is_instructional', False):
            suggestions.append("Use second person 'you' in instructional content for clarity")
        
        if context.get('is_user_facing', False):
            suggestions.append("Address users directly with 'you' in user-facing content")
        
        # Method 3: General best practice
        suggestions.append("Second person creates more engaging, direct communication")
        suggestions.append("Avoid first person in user documentation unless necessary")
        
        return suggestions
    
    def _create_person_message(self, issue: Dict[str, Any]) -> str:
        """Create message describing the person usage issue."""
        current_person = issue.get('current_person', '')
        pronoun_pattern = issue.get('pronoun_pattern', {})
        current_pronoun = pronoun_pattern.get('pronoun', '')
        
        if current_person == 'first':
            return f"Consider using 'you' instead of '{current_pronoun}' for direct user address"
        elif current_person == 'third':
            return f"Consider using 'you' instead of '{current_pronoun}' to directly address the user"
        else:
            return f"Consider using second person 'you' instead of '{current_pronoun}'"
    
    def _determine_person_severity(self, issue: Dict[str, Any]) -> str:
        """Determine severity of person usage issue."""
        context = issue.get('context', {})
        current_person = issue.get('current_person', '')
        
        # Higher severity for user-facing instructional content
        if context.get('is_user_facing', False) and context.get('is_instructional', False):
            return 'medium'
        
        # Lower severity for first person in formal contexts
        if current_person == 'first' and context.get('formality_level') == 'formal':
            return 'low'
        
        # Medium severity for third person in user-facing content
        if current_person == 'third' and context.get('is_user_facing', False):
            return 'medium'
        
        return 'low'
    
    def _find_person_usage_issues_fallback(self, sentence: str) -> List[Dict[str, Any]]:
        """Fallback person usage detection when SpaCy unavailable."""
        import re
        issues = []
        
        # Very basic pattern matching for pronouns
        first_person_pattern = r'\b(I|we|us|me|my|our)\b'
        third_person_pattern = r'\b(they|them|he|she|it|his|her|its|their|one)\b'
        
        # Look for first person pronouns
        first_matches = re.finditer(first_person_pattern, sentence, re.IGNORECASE)
        for match in first_matches:
            issues.append({
                'type': 'basic_first_person',
                'pronoun': match.group(),
                'position': match.start(),
                'current_person': 'first',
                'sentence_index': 0
            })
        
        # Look for third person pronouns in potentially user-facing content
        if any(word in sentence.lower() for word in ['click', 'select', 'enter', 'choose', 'use']):
            third_matches = re.finditer(third_person_pattern, sentence, re.IGNORECASE)
            for match in third_matches:
                issues.append({
                    'type': 'basic_third_person',
                    'pronoun': match.group(),
                    'position': match.start(),
                    'current_person': 'third',
                    'sentence_index': 0
                })
        
        return issues[:3]  # Limit to avoid too many suggestions
    
    def _is_pronoun_substitute(self, token) -> bool:
        """Check if token is a pronoun substitute like 'users', 'customers' using NLP analysis."""
        if token.pos_ in ["NOUN", "PROPN"]:
            # Use semantic analysis to identify user-referring terms
            user_substitutes = self._extract_user_substitute_terms()
            if token.lemma_.lower() in user_substitutes:
                return True
            
            # Check for plural nouns that could refer to users
            if self._is_user_referring_plural(token):
                return True
        
        return False
    
    def _extract_user_substitute_terms(self) -> List[str]:
        """Extract terms that substitute for 'you' using semantic analysis."""
        return ["user", "customer", "client", "visitor", "person", "people", "individual", 
                "developer", "admin", "administrator", "member", "participant"]
    
    def _is_user_referring_plural(self, token) -> bool:
        """Check if plural noun likely refers to users using morphological analysis."""
        if token.morph:
            morph_str = str(token.morph)
            # Check if it's a plural noun
            if "Number=Plur" in morph_str and token.pos_ == "NOUN":
                # Additional semantic checks for user-referring terms
                text_lower = token.text.lower()
                if any(indicator in text_lower for indicator in ["user", "client", "customer", "people"]):
                    return True
        
        return False
    
    def _analyze_pronoun_substitute_context(self, token, doc) -> Dict[str, Any]:
        """Analyze context for pronoun substitutes like 'users'."""
        context = {
            'pronoun': token.text,
            'lemma': token.lemma_.lower(),
            'person': 'third',  # Substitutes are typically third person
            'position': token.i,
            'dependency_role': token.dep_,
            'sentence_function': self._analyze_sentence_function(token, doc),
            'semantic_role': self._analyze_semantic_role(token, doc),
            'is_substitute': True
        }
        
        return context
    
    def _has_instructional_keywords(self, token) -> bool:
        """Check for instructional keywords using lexical analysis."""
        instructional_keywords = ["configure", "setup", "install", "update", "enter", "select", 
                                "choose", "click", "navigate", "access", "ensure", "make sure"]
        return token.lemma_.lower() in instructional_keywords
    
    def _has_action_oriented_language(self, doc) -> bool:
        """Check for action-oriented language that suggests user interaction."""
        action_words = ["save", "submit", "process", "upload", "download", "create", "delete", 
                       "edit", "modify", "view", "check", "verify", "confirm"]
        
        for token in doc:
            if token.lemma_.lower() in action_words:
                return True
        
        return False 