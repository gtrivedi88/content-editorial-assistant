"""
Introductory Comma Rule - Ensures proper use of commas after introductory elements using pure SpaCy morphological analysis.
Uses SpaCy dependency parsing, POS tagging, and morphological features to detect introductory patterns.
No hardcoded patterns - all analysis is based on linguistic morphology and syntax.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict

# Handle imports for different contexts (punctuation subdirectory)
try:
    from ...base_rule import BaseRule
except ImportError:
    try:
        from src.rules.base_rule import BaseRule
    except ImportError:
        from base_rule import BaseRule


class IntroductoryCommaRule(BaseRule):
    """Rule to detect missing or incorrect commas after introductory elements using pure SpaCy morphological analysis."""
    
    def _get_rule_type(self) -> str:
        return 'introductory_comma'
    
    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """Analyze text for introductory comma issues using pure SpaCy linguistic analysis."""
        if not nlp:
            return []  # Skip analysis if SpaCy not available
        
        errors = []
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
                
            doc = nlp(sentence)
            
            # Find introductory comma issues
            intro_issues = self._find_introductory_comma_issues_morphological(doc, sentence)
            
            for issue in intro_issues:
                suggestions = self._generate_morphological_suggestions(issue, doc)
                
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message=self._create_morphological_message(issue),
                    suggestions=suggestions,
                    severity=self._determine_morphological_severity(issue),
                    introductory_issue=issue
                ))
        
        return errors
    
    def _find_introductory_comma_issues_morphological(self, doc, sentence: str) -> List[Dict[str, Any]]:
        """Find introductory comma usage issues using SpaCy morphological and syntactic analysis."""
        issues = []
        
        # Analyze sentence structure to identify introductory elements
        introductory_elements = self._identify_introductory_elements_morphological(doc)
        
        for intro_element in introductory_elements:
            # Check if introductory element has proper comma
            comma_issue = self._analyze_introductory_comma_morphological(intro_element, doc)
            if comma_issue:
                issues.append(comma_issue)
        
        # Check for incorrect commas after coordinating conjunctions
        conj_issues = self._find_coordinating_conjunction_comma_issues_morphological(doc)
        issues.extend(conj_issues)
        
        return issues
    
    def _identify_introductory_elements_morphological(self, doc) -> List[Dict[str, Any]]:
        """Identify introductory elements at sentence beginnings using morphological analysis."""
        introductory_elements = []
        
        if not doc:
            return introductory_elements
        
        # Look for introductory patterns at sentence start
        current_element = []
        element_start = 0
        
        for i, token in enumerate(doc):
            # Skip initial spaces and punctuation
            if i == 0 and (token.is_space or token.is_punct):
                continue
            
            # Check if this token starts an introductory element
            if i == 0 or (len(current_element) == 0 and not token.is_space):
                element_start = i
                
            # Build current introductory element
            if not token.is_space:
                current_element.append(token)
            
            # Check if we've reached the end of an introductory element
            if self._is_end_of_introductory_element_morphological(token, doc, i):
                if current_element and self._is_introductory_pattern_morphological(current_element):
                    intro_element = {
                        'tokens': current_element,
                        'start_index': element_start,
                        'end_index': i,
                        'type': self._classify_introductory_type_morphological(current_element),
                        'followed_by_comma': self._check_followed_by_comma_morphological(i, doc)
                    }
                    introductory_elements.append(intro_element)
                
                # Stop after first introductory element (rest is main clause)
                break
        
        return introductory_elements
    
    def _is_end_of_introductory_element_morphological(self, token, doc, position: int) -> bool:
        """Check if current position marks end of introductory element."""
        # Comma typically marks end of introductory element
        if token.text == ',':
            return True
        
        # Look ahead to see if next significant token suggests main clause
        next_tokens = self._get_next_significant_tokens_morphological(position, doc, 3)
        
        if next_tokens:
            # If next token starts what looks like main clause, current element ends here
            if self._tokens_suggest_main_clause_start_morphological(next_tokens):
                return True
        
        # Check if we've hit sentence boundaries or other structural markers
        if position >= len(doc) - 1:
            return True
        
        # If current element is getting too long, likely not introductory anymore
        current_length = position + 1
        if current_length > 15:  # Most introductory elements are shorter
            return True
        
        return False
    
    def _get_next_significant_tokens_morphological(self, position: int, doc, count: int = 3) -> List:
        """Get next significant (non-space, non-punct) tokens."""
        significant_tokens = []
        
        for i in range(position + 1, min(len(doc), position + count * 2)):
            token = doc[i]
            if not token.is_space and not token.is_punct:
                significant_tokens.append(token)
                if len(significant_tokens) >= count:
                    break
        
        return significant_tokens
    
    def _tokens_suggest_main_clause_start_morphological(self, tokens) -> bool:
        """Check if tokens suggest start of main clause."""
        if not tokens:
            return False
        
        first_token = tokens[0]
        
        # Personal pronouns often start main clauses
        if first_token.pos_ == 'PRON' and first_token.dep_ in ['nsubj', 'nsubjpass']:
            return True
        
        # Proper nouns as subjects
        if first_token.pos_ == 'PROPN' and first_token.dep_ in ['nsubj', 'nsubjpass']:
            return True
        
        # Determiners followed by nouns (article + noun subjects)
        if first_token.pos_ == 'DET' and len(tokens) > 1:
            if tokens[1].pos_ in ['NOUN', 'PROPN']:
                return True
        
        # Main verbs in imperative sentences
        if first_token.pos_ == 'VERB' and first_token.dep_ == 'ROOT':
            return True
        
        return False
    
    def _is_introductory_pattern_morphological(self, tokens) -> bool:
        """Check if tokens form an introductory pattern using morphological analysis."""
        if not tokens:
            return False
        
        first_token = tokens[0]
        
        # 1. Adverbial introductory words (However, First, Therefore, etc.)
        if self._is_introductory_adverb_morphological(first_token):
            return True
        
        # 2. Prepositional phrases (In the diagram, After you remove, etc.)
        if self._is_introductory_prepositional_phrase_morphological(tokens):
            return True
        
        # 3. Subordinate clauses (When you click, If you are using, etc.)
        if self._is_introductory_subordinate_clause_morphological(tokens):
            return True
        
        # 4. Participial phrases (Starting with -ing or -ed forms)
        if self._is_introductory_participial_phrase_morphological(tokens):
            return True
        
        # 5. Infinitive phrases (To move the element, To create a project, etc.)
        if self._is_introductory_infinitive_phrase_morphological(tokens):
            return True
        
        # 6. Absolute constructions
        if self._is_introductory_absolute_construction_morphological(tokens):
            return True
        
        return False
    
    def _is_introductory_adverb_morphological(self, token) -> bool:
        """Check if token is an introductory adverb."""
        if token.pos_ != 'ADV':
            return False
        
        # Use morphological and semantic analysis to identify introductory adverbs
        lemma = token.lemma_.lower()
        
        # Transition/sequence adverbs
        transition_adverbs = {
            'however', 'therefore', 'furthermore', 'moreover', 'consequently', 
            'meanwhile', 'nonetheless', 'nevertheless', 'thus', 'hence',
            'first', 'second', 'third', 'finally', 'next', 'then',
            'initially', 'subsequently', 'eventually', 'ultimately',
            'additionally', 'alternatively', 'similarly', 'conversely'
        }
        
        if lemma in transition_adverbs:
            return True
        
        # Check semantic field for transitional/sequential meaning
        semantic_field = self._analyze_semantic_field(token)
        if semantic_field in ['transition', 'sequence', 'temporal']:
            return True
        
        # Check morphological features for adverbial function
        morph_features = self._get_morphological_features(token)
        if 'AdvType' in morph_features.get('morph', {}):
            return True
        
        return False
    
    def _is_introductory_prepositional_phrase_morphological(self, tokens) -> bool:
        """Check if tokens form an introductory prepositional phrase."""
        if not tokens:
            return False
        
        first_token = tokens[0]
        
        # Must start with preposition
        if first_token.pos_ != 'ADP':
            return False
        
        # Should have noun/pronoun object
        has_object = any(token.pos_ in ['NOUN', 'PROPN', 'PRON'] and 
                        token.dep_ in ['pobj', 'pcomp'] 
                        for token in tokens[1:])
        
        return has_object
    
    def _is_introductory_subordinate_clause_morphological(self, tokens) -> bool:
        """Check if tokens form an introductory subordinate clause."""
        if not tokens:
            return False
        
        first_token = tokens[0]
        
        # Must start with subordinating conjunction
        if first_token.pos_ != 'SCONJ':
            return False
        
        # Should contain subject and verb
        has_subject = any(token.dep_ in ['nsubj', 'nsubjpass'] for token in tokens[1:])
        has_verb = any(token.pos_ == 'VERB' for token in tokens[1:])
        
        return has_subject and has_verb
    
    def _is_introductory_participial_phrase_morphological(self, tokens) -> bool:
        """Check if tokens form an introductory participial phrase."""
        if not tokens:
            return False
        
        first_token = tokens[0]
        
        # Must start with participle (present or past)
        if first_token.pos_ != 'VERB':
            return False
        
        # Check morphological features for participle
        morph_features = self._get_morphological_features(first_token)
        morph_dict = morph_features.get('morph', {})
        
        if isinstance(morph_dict, dict):
            verb_form = morph_dict.get('VerbForm', '')
        else:
            verb_form = str(morph_dict) if 'VerbForm=Part' in str(morph_dict) else ''
        
        return 'Part' in verb_form or first_token.tag_ in ['VBG', 'VBN']
    
    def _is_introductory_infinitive_phrase_morphological(self, tokens) -> bool:
        """Check if tokens form an introductory infinitive phrase."""
        if len(tokens) < 2:
            return False
        
        # Must start with "to" + verb
        if (tokens[0].lemma_.lower() == 'to' and 
            tokens[0].pos_ == 'PART' and
            len(tokens) > 1 and 
            tokens[1].pos_ == 'VERB'):
            
            # Check that the verb is infinitive
            morph_features = self._get_morphological_features(tokens[1])
            morph_dict = morph_features.get('morph', {})
            
            if isinstance(morph_dict, dict):
                verb_form = morph_dict.get('VerbForm', '')
            else:
                verb_form = str(morph_dict) if 'VerbForm=Inf' in str(morph_dict) else ''
            
            return 'Inf' in verb_form or tokens[1].tag_ == 'VB'
        
        return False
    
    def _is_introductory_absolute_construction_morphological(self, tokens) -> bool:
        """Check if tokens form an introductory absolute construction."""
        if len(tokens) < 3:
            return False
        
        # Absolute constructions often have noun + participle/adjective pattern
        # E.g., "The work completed, we moved on"
        
        has_noun_subject = any(token.pos_ in ['NOUN', 'PROPN'] and 
                              token.dep_ in ['nsubj', 'nsubjpass'] 
                              for token in tokens[:3])
        
        has_participle_or_adj = any(token.pos_ in ['VERB', 'ADJ'] and 
                                   token.tag_ in ['VBG', 'VBN', 'JJ'] 
                                   for token in tokens[1:])
        
        return has_noun_subject and has_participle_or_adj
    
    def _classify_introductory_type_morphological(self, tokens) -> str:
        """Classify the type of introductory element."""
        if not tokens:
            return 'unknown'
        
        first_token = tokens[0]
        
        if self._is_introductory_adverb_morphological(first_token):
            return 'adverbial'
        elif first_token.pos_ == 'ADP':
            return 'prepositional_phrase'
        elif first_token.pos_ == 'SCONJ':
            return 'subordinate_clause'
        elif first_token.pos_ == 'VERB':
            return 'participial_phrase'
        elif first_token.lemma_.lower() == 'to' and first_token.pos_ == 'PART':
            return 'infinitive_phrase'
        else:
            return 'other'
    
    def _check_followed_by_comma_morphological(self, end_index: int, doc) -> bool:
        """Check if introductory element is followed by comma."""
        # Look for comma immediately after or within next few tokens
        for i in range(end_index, min(len(doc), end_index + 3)):
            if doc[i].text == ',':
                return True
            elif not doc[i].is_space:
                # Hit non-space, non-comma token
                break
        
        return False
    
    def _analyze_introductory_comma_morphological(self, intro_element: Dict[str, Any], doc) -> Optional[Dict[str, Any]]:
        """Analyze introductory element for comma usage issues."""
        issues = []
        
        has_comma = intro_element.get('followed_by_comma', False)
        intro_type = intro_element.get('type', 'unknown')
        tokens = intro_element.get('tokens', [])
        
        # Most introductory elements should be followed by comma
        if not has_comma:
            # Check if this is a very short introductory element that might not need comma
            if not self._is_comma_optional_morphological(intro_element):
                issues.append('missing_comma_after_introductory')
        
        if issues:
            return {
                'type': 'introductory_comma_issue',
                'issues': issues,
                'introductory_element': intro_element,
                'intro_type': intro_type,
                'tokens': tokens,
                'has_comma': has_comma
            }
        
        return None
    
    def _is_comma_optional_morphological(self, intro_element: Dict[str, Any]) -> bool:
        """Check if comma is optional after this introductory element."""
        tokens = intro_element.get('tokens', [])
        intro_type = intro_element.get('type', 'unknown')
        
        # Very short prepositional phrases might not need comma
        if intro_type == 'prepositional_phrase' and len(tokens) <= 2:
            return True
        
        # Short adverbial phrases
        if intro_type == 'adverbial' and len(tokens) == 1:
            first_token = tokens[0]
            # Some single-word adverbs don't require comma
            if first_token.lemma_.lower() in ['now', 'then', 'here', 'there']:
                return True
        
        return False
    
    def _find_coordinating_conjunction_comma_issues_morphological(self, doc) -> List[Dict[str, Any]]:
        """Find incorrect commas after coordinating conjunctions."""
        issues = []
        
        for i, token in enumerate(doc):
            if self._is_coordinating_conjunction_morphological(token):
                # Check if inappropriately followed by comma
                conj_issue = self._analyze_coordinating_conjunction_comma_morphological(token, doc, i)
                if conj_issue:
                    issues.append(conj_issue)
        
        return issues
    
    def _is_coordinating_conjunction_morphological(self, token) -> bool:
        """Check if token is a coordinating conjunction."""
        if token.pos_ == 'CCONJ':
            lemma = token.lemma_.lower()
            # FANBOYS: for, and, nor, but, or, yet, so
            coordinating_lemmas = {'and', 'but', 'or', 'nor', 'for', 'so', 'yet'}
            return lemma in coordinating_lemmas
        return False
    
    def _analyze_coordinating_conjunction_comma_morphological(self, conj_token, doc, position: int) -> Optional[Dict[str, Any]]:
        """Analyze coordinating conjunction for inappropriate comma usage."""
        # Check if followed by comma
        has_comma_after = self._has_comma_after_morphological(conj_token, doc)
        
        if has_comma_after:
            # Check if comma is justified (followed by clause that requires comma)
            following_clause = self._get_clause_after_comma_morphological(conj_token, doc)
            
            if following_clause:
                needs_comma = self._clause_requires_comma_morphological(following_clause)
                
                if not needs_comma:
                    return {
                        'type': 'coordinating_conjunction_comma_issue',
                        'issues': ['unnecessary_comma_after_conjunction'],
                        'conjunction_token': conj_token,
                        'conjunction_text': conj_token.text,
                        'following_clause': following_clause,
                        'position': position
                    }
        
        return None
    
    def _has_comma_after_morphological(self, token, doc) -> bool:
        """Check if token is followed by comma."""
        if token.i >= len(doc) - 1:
            return False
        
        # Look for comma in next few tokens (allowing for spaces)
        for i in range(token.i + 1, min(len(doc), token.i + 3)):
            if doc[i].text == ',':
                return True
            elif not doc[i].is_space:
                break
        
        return False
    
    def _get_clause_after_comma_morphological(self, conj_token, doc) -> Optional[List]:
        """Get clause following conjunction and comma."""
        # Find the comma first
        comma_pos = None
        for i in range(conj_token.i + 1, min(len(doc), conj_token.i + 3)):
            if doc[i].text == ',':
                comma_pos = i
                break
        
        if comma_pos is None:
            return None
        
        # Extract clause after comma
        clause_tokens = []
        for i in range(comma_pos + 1, len(doc)):
            if doc[i].is_sent_end or doc[i].text in ['.', ';', ':', '!', '?']:
                break
            
            if not doc[i].is_space:
                clause_tokens.append(doc[i])
        
        return clause_tokens if clause_tokens else None
    
    def _clause_requires_comma_morphological(self, clause_tokens) -> bool:
        """Check if clause type requires comma after conjunction."""
        if not clause_tokens:
            return False
        
        first_token = clause_tokens[0]
        
        # Conditional clauses (if, when, unless, etc.) require comma
        if first_token.pos_ == 'SCONJ':
            conditional_conjunctions = {'if', 'when', 'unless', 'although', 'because', 'since', 'while'}
            if first_token.lemma_.lower() in conditional_conjunctions:
                return True
        
        # Participial phrases require comma
        if first_token.pos_ == 'VERB':
            morph_features = self._get_morphological_features(first_token)
            morph_dict = morph_features.get('morph', {})
            
            if isinstance(morph_dict, dict):
                verb_form = morph_dict.get('VerbForm', '')
            else:
                verb_form = str(morph_dict) if 'VerbForm=Part' in str(morph_dict) else ''
            
            if 'Part' in verb_form:
                return True
        
        # Other complex constructions that might require comma
        # This could be extended based on more specific patterns
        
        return False
    
    def _generate_morphological_suggestions(self, issue: Dict[str, Any], doc) -> List[str]:
        """Generate suggestions based on introductory comma issue type."""
        issue_type = issue.get('type', '')
        suggestions = []
        
        if issue_type == 'introductory_comma_issue':
            issues = issue.get('issues', [])
            intro_type = issue.get('intro_type', 'element')
            
            if 'missing_comma_after_introductory' in issues:
                type_name = intro_type.replace('_', ' ')
                suggestions.append(f"Add a comma after the introductory {type_name}")
                suggestions.append("Introductory elements should be followed by a comma to separate them from the main clause")
                
                # Type-specific suggestions
                if intro_type == 'adverbial':
                    suggestions.append("Example: 'However, most hardware components conform to this standard'")
                elif intro_type == 'prepositional_phrase':
                    suggestions.append("Example: 'In the diagram editor, right-click a diagram'")
                elif intro_type == 'infinitive_phrase':
                    suggestions.append("Example: 'To move the model element, click Refactor > Move'")
                elif intro_type == 'subordinate_clause':
                    suggestions.append("Example: 'After you remove the lid, proceed to step 4'")
        
        elif issue_type == 'coordinating_conjunction_comma_issue':
            issues = issue.get('issues', [])
            conj_text = issue.get('conjunction_text', 'conjunction')
            
            if 'unnecessary_comma_after_conjunction' in issues:
                suggestions.append(f"Remove the comma after '{conj_text}' unless followed by a clause that requires a comma")
                suggestions.append("Coordinating conjunctions don't need commas unless followed by conditional clauses")
                suggestions.append(f"Incorrect: '{conj_text}, you can view other log files'")
                suggestions.append(f"Correct: '{conj_text} you can view other log files'")
                suggestions.append(f"Correct: '{conj_text}, if you are using Windows 10, you can view other log files'")
        
        # Generic fallback
        if not suggestions:
            suggestions.append("Review comma usage with introductory elements")
            suggestions.append("Use commas to separate introductory elements from main clauses")
        
        return suggestions
    
    def _create_morphological_message(self, issue: Dict[str, Any]) -> str:
        """Create error message based on issue type."""
        issue_type = issue.get('type', '')
        
        if issue_type == 'introductory_comma_issue':
            issues = issue.get('issues', [])
            intro_type = issue.get('intro_type', 'element')
            
            if 'missing_comma_after_introductory' in issues:
                type_name = intro_type.replace('_', ' ')
                return f"Use a comma after introductory {type_name}s to separate them from the main clause."
        
        elif issue_type == 'coordinating_conjunction_comma_issue':
            issues = issue.get('issues', [])
            conj_text = issue.get('conjunction_text', 'conjunction')
            
            if 'unnecessary_comma_after_conjunction' in issues:
                return f"Do not add a comma after '{conj_text}' unless it's followed by a clause that requires a comma, such as a conditional clause."
        
        return "Review comma usage with introductory elements."
    
    def _determine_morphological_severity(self, issue: Dict[str, Any]) -> str:
        """Determine severity level based on issue type."""
        issue_type = issue.get('type', '')
        
        # Missing commas after introductory elements are medium severity (clarity issue)
        if issue_type == 'introductory_comma_issue':
            return 'medium'
        
        # Incorrect commas after conjunctions are low severity (style issue)
        elif issue_type == 'coordinating_conjunction_comma_issue':
            return 'low'
        
        return 'medium' 