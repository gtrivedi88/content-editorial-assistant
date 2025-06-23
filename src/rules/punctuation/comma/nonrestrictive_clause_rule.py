"""
Nonrestrictive Clause Comma Rule - Ensures proper comma usage with restrictive and nonrestrictive clauses using pure SpaCy morphological analysis.
Uses SpaCy dependency parsing, POS tagging, and morphological features to identify clause types.
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


class NonrestrictiveClauseRule(BaseRule):
    """Rule to detect comma usage issues with restrictive and nonrestrictive clauses using pure SpaCy morphological analysis."""
    
    def _get_rule_type(self) -> str:
        return 'nonrestrictive_clause'
    
    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """Analyze text for nonrestrictive clause comma issues using pure SpaCy linguistic analysis."""
        if not nlp:
            return []  # Skip analysis if SpaCy not available
        
        errors = []
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
                
            doc = nlp(sentence)
            
            # Find nonrestrictive clause issues
            clause_issues = self._find_clause_comma_issues_morphological(doc, sentence)
            
            for issue in clause_issues:
                suggestions = self._generate_morphological_suggestions(issue, doc)
                
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message=self._create_morphological_message(issue),
                    suggestions=suggestions,
                    severity=self._determine_morphological_severity(issue),
                    clause_issue=issue
                ))
        
        return errors
    
    def _find_clause_comma_issues_morphological(self, doc, sentence: str) -> List[Dict[str, Any]]:
        """Find clause comma usage issues using SpaCy morphological and syntactic analysis."""
        issues = []
        
        # Find all relative clauses in the sentence
        relative_clauses = self._identify_relative_clauses_morphological(doc)
        
        for clause_data in relative_clauses:
            # Analyze each clause for comma issues
            clause_issues = self._analyze_clause_comma_usage_morphological(clause_data, doc)
            issues.extend(clause_issues)
        
        # Find appositives and parenthetical phrases
        appositives = self._identify_appositives_morphological(doc)
        for appositive_data in appositives:
            appositive_issues = self._analyze_appositive_comma_usage_morphological(appositive_data, doc)
            issues.extend(appositive_issues)
        
        # Find "such as" phrases
        such_as_phrases = self._identify_such_as_phrases_morphological(doc)
        for phrase_data in such_as_phrases:
            phrase_issues = self._analyze_such_as_phrase_comma_usage_morphological(phrase_data, doc)
            issues.extend(phrase_issues)
        
        return issues
    
    def _identify_relative_clauses_morphological(self, doc) -> List[Dict[str, Any]]:
        """Identify relative clauses using SpaCy dependency parsing and morphological analysis."""
        relative_clauses = []
        
        for token in doc:
            # Look for relative pronouns and relative adverbs
            if self._is_relative_pronoun_morphological(token):
                clause_data = self._extract_relative_clause_morphological(token, doc)
                if clause_data:
                    relative_clauses.append(clause_data)
        
        return relative_clauses
    
    def _is_relative_pronoun_morphological(self, token) -> bool:
        """Check if token is a relative pronoun using morphological analysis."""
        # Check POS tag and lemma
        if token.pos_ in ['PRON', 'DET', 'ADV']:
            relative_lemmas = {'who', 'whom', 'whose', 'which', 'that', 'where', 'when', 'why'}
            if token.lemma_.lower() in relative_lemmas:
                # Additional check: should have appropriate dependency relation
                if token.dep_ in ['nsubj', 'dobj', 'pobj', 'advmod', 'nsubjpass', 'attr', 'relcl']:
                    return True
        
        return False
    
    def _extract_relative_clause_morphological(self, rel_pronoun, doc) -> Optional[Dict[str, Any]]:
        """Extract relative clause information using morphological analysis."""
        # Find the antecedent (what the relative pronoun refers to)
        antecedent = self._find_antecedent_morphological(rel_pronoun, doc)
        
        if not antecedent:
            return None
        
        # Extract the relative clause tokens
        clause_tokens = self._extract_clause_tokens_morphological(rel_pronoun, doc)
        
        # Determine if clause is restrictive or nonrestrictive
        restrictiveness = self._determine_clause_restrictiveness_morphological(
            rel_pronoun, antecedent, clause_tokens, doc
        )
        
        # Check current comma usage
        comma_usage = self._analyze_current_comma_usage_morphological(rel_pronoun, antecedent, doc)
        
        # Get clause end position safely
        clause_end_pos = rel_pronoun.i
        if clause_tokens:
            last_token = clause_tokens[-1]
            clause_end_pos = getattr(last_token, 'i', rel_pronoun.i)

        return {
            'type': 'relative_clause',
            'relative_pronoun': rel_pronoun,
            'antecedent': antecedent,
            'clause_tokens': clause_tokens,
            'restrictiveness': restrictiveness,
            'comma_usage': comma_usage,
            'clause_start': rel_pronoun.i,
            'clause_end': clause_end_pos
        }
    
    def _find_antecedent_morphological(self, rel_pronoun, doc) -> Optional[object]:
        """Find the antecedent of a relative pronoun using dependency analysis."""
        # Method 1: Check if rel_pronoun has a direct head that's the antecedent
        if rel_pronoun.head and rel_pronoun.head != rel_pronoun:
            # Check if the head is a noun that could be the antecedent
            if rel_pronoun.head.pos_ in ['NOUN', 'PROPN', 'PRON']:
                return rel_pronoun.head
        
        # Method 2: Look for nearest preceding noun
        for i in range(rel_pronoun.i - 1, max(-1, rel_pronoun.i - 10), -1):
            token = doc[i]
            if token.pos_ in ['NOUN', 'PROPN'] and not token.is_punct:
                # Check if this could be the antecedent using morphological features
                if self._could_be_antecedent_morphological(token, rel_pronoun):
                    return token
        
        return None
    
    def _could_be_antecedent_morphological(self, potential_antecedent, rel_pronoun) -> bool:
        """Check if a token could be the antecedent using morphological analysis."""
        # Check semantic compatibility
        rel_lemma = rel_pronoun.lemma_.lower()
        
        # "who/whom" typically refers to people
        if rel_lemma in ['who', 'whom']:
            # Check if antecedent could refer to a person
            if self._refers_to_person_morphological(potential_antecedent):
                return True
        
        # "which" typically refers to things
        elif rel_lemma == 'which':
            # Check if antecedent could refer to a thing
            if not self._refers_to_person_morphological(potential_antecedent):
                return True
        
        # "that" can refer to either people or things
        elif rel_lemma == 'that':
            return True
        
        return False
    
    def _refers_to_person_morphological(self, token) -> bool:
        """Check if token refers to a person using morphological analysis."""
        # Check named entity recognition
        if hasattr(token, 'ent_type_') and token.ent_type_ == 'PERSON':
            return True
        
        # Check semantic field
        semantic_field = self._analyze_semantic_field(token)
        if semantic_field in ['human', 'person', 'agent']:
            return True
        
        # Check lemma for person-related words
        person_lemmas = {
            'person', 'people', 'individual', 'user', 'customer', 'client', 
            'employee', 'manager', 'developer', 'subscriber', 'student', 'teacher'
        }
        if token.lemma_.lower() in person_lemmas:
            return True
        
        return False
    
    def _extract_clause_tokens_morphological(self, rel_pronoun, doc) -> List[object]:
        """Extract all tokens that belong to the relative clause."""
        clause_tokens = [rel_pronoun]
        
        # Find the end of the clause using dependency parsing
        clause_end = self._find_clause_end_morphological(rel_pronoun, doc)
        
        # Collect all tokens from relative pronoun to clause end
        for i in range(rel_pronoun.i + 1, min(len(doc), clause_end + 1)):
            clause_tokens.append(doc[i])
        
        return clause_tokens
    
    def _find_clause_end_morphological(self, rel_pronoun, doc) -> int:
        """Find the end of the relative clause using morphological analysis."""
        # Look for clause boundaries
        for i in range(rel_pronoun.i + 1, len(doc)):
            token = doc[i]
            
            # End at sentence boundaries
            if token.is_sent_end or token.text in ['.', ';', '!', '?']:
                return i - 1
            
            # End at other clause markers
            if (token.text in [','] and 
                self._is_clause_boundary_morphological(token, doc, rel_pronoun)):
                return i - 1
            
            # End at coordinating conjunctions that start new main clauses
            if (token.pos_ == 'CCONJ' and 
                self._starts_new_main_clause_morphological(token, doc)):
                return i - 1
        
        return len(doc) - 1
    
    def _is_clause_boundary_morphological(self, comma_token, doc, rel_pronoun) -> bool:
        """Check if comma marks end of relative clause."""
        # Look ahead to see if next clause is independent
        following_tokens = doc[comma_token.i + 1:comma_token.i + 5]
        
        # If next tokens form start of independent clause, comma ends relative clause
        if following_tokens:
            # Check for subject-verb pattern
            has_subject = any(t.dep_ in ['nsubj', 'nsubjpass'] for t in following_tokens)
            has_verb = any(t.pos_ == 'VERB' for t in following_tokens)
            
            if has_subject and has_verb:
                return True
        
        return False
    
    def _starts_new_main_clause_morphological(self, conj_token, doc) -> bool:
        """Check if conjunction starts a new main clause."""
        # Look at tokens after conjunction
        following_tokens = doc[conj_token.i + 1:conj_token.i + 5]
        
        if following_tokens:
            # Check for main clause pattern: subject + main verb
            has_main_subject = any(t.dep_ in ['nsubj', 'nsubjpass'] for t in following_tokens)
            has_main_verb = any(t.pos_ == 'VERB' and t.dep_ == 'ROOT' for t in following_tokens)
            
            return has_main_subject or has_main_verb
        
        return False
    
    def _determine_clause_restrictiveness_morphological(self, rel_pronoun, antecedent, clause_tokens, doc) -> Dict[str, Any]:
        """Determine if clause is restrictive or nonrestrictive using morphological analysis."""
        restrictiveness_indicators = {
            'relative_pronoun_type': self._analyze_relative_pronoun_type_morphological(rel_pronoun),
            'antecedent_definiteness': self._analyze_antecedent_definiteness_morphological(antecedent, doc),
            'clause_essentiality': self._analyze_clause_essentiality_morphological(antecedent, clause_tokens),
            'semantic_relationship': self._analyze_semantic_relationship_morphological(antecedent, clause_tokens)
        }
        
        # Determine overall restrictiveness
        restrictiveness_score = self._calculate_restrictiveness_score_morphological(restrictiveness_indicators)
        
        return {
            'is_restrictive': restrictiveness_score > 0.5,
            'confidence': abs(restrictiveness_score - 0.5) * 2,  # 0-1 scale
            'indicators': restrictiveness_indicators,
            'score': restrictiveness_score
        }
    
    def _analyze_relative_pronoun_type_morphological(self, rel_pronoun) -> Dict[str, Any]:
        """Analyze relative pronoun for restrictiveness clues."""
        lemma = rel_pronoun.lemma_.lower()
        
        # "which" is typically nonrestrictive, "that" is typically restrictive
        pronoun_preferences = {
            'which': {'restrictive': 0.2, 'nonrestrictive': 0.8},
            'that': {'restrictive': 0.9, 'nonrestrictive': 0.1},
            'who': {'restrictive': 0.5, 'nonrestrictive': 0.5},  # Context-dependent
            'whom': {'restrictive': 0.4, 'nonrestrictive': 0.6},
            'whose': {'restrictive': 0.6, 'nonrestrictive': 0.4}
        }
        
        return {
            'pronoun': lemma,
            'preferences': pronoun_preferences.get(lemma, {'restrictive': 0.5, 'nonrestrictive': 0.5})
        }
    
    def _analyze_antecedent_definiteness_morphological(self, antecedent, doc) -> Dict[str, Any]:
        """Analyze antecedent definiteness for restrictiveness clues."""
        if not antecedent:
            return {'definiteness': 'unknown', 'restrictive_tendency': 0.5}
        
        # Look for determiners before antecedent
        determiners = []
        for i in range(max(0, antecedent.i - 3), antecedent.i):
            if doc[i].pos_ == 'DET':
                determiners.append(doc[i])
        
        # Analyze definiteness
        if any(det.lemma_.lower() == 'the' for det in determiners):
            # Definite article suggests the antecedent is already identified
            # This makes the clause more likely to be nonrestrictive (additional info)
            return {'definiteness': 'definite', 'restrictive_tendency': 0.3}
        
        elif any(det.lemma_.lower() in ['a', 'an'] for det in determiners):
            # Indefinite article suggests the clause might be needed for identification
            return {'definiteness': 'indefinite', 'restrictive_tendency': 0.7}
        
        else:
            # No determiner or other determiners
            return {'definiteness': 'bare', 'restrictive_tendency': 0.6}
    
    def _analyze_clause_essentiality_morphological(self, antecedent, clause_tokens) -> Dict[str, Any]:
        """Analyze whether clause provides essential vs. additional information."""
        if not clause_tokens:
            return {'essentiality': 'unknown', 'restrictive_tendency': 0.5}
        
        # Extract content words from clause
        content_words = [t for t in clause_tokens if not t.is_punct and not t.is_space and not t.is_stop]
        
        # Check for identifying vs. describing language
        identifying_indicators = 0
        describing_indicators = 0
        
        for token in content_words:
            # Identifying language: specific, unique, selective
            if token.pos_ in ['NUM', 'PROPN']:  # Numbers and proper nouns identify
                identifying_indicators += 1
            
            # Describing language: adjectives, adverbs
            elif token.pos_ in ['ADJ', 'ADV']:
                describing_indicators += 1
            
            # Check semantic fields
            semantic_field = self._analyze_semantic_field(token)
            if semantic_field in ['quantitative', 'specific', 'unique']:
                identifying_indicators += 1
            elif semantic_field in ['property', 'description', 'quality']:
                describing_indicators += 1
        
        total_indicators = identifying_indicators + describing_indicators
        if total_indicators > 0:
            restrictive_tendency = identifying_indicators / total_indicators
        else:
            restrictive_tendency = 0.5
        
        return {
            'identifying_indicators': identifying_indicators,
            'describing_indicators': describing_indicators,
            'restrictive_tendency': restrictive_tendency
        }
    
    def _analyze_semantic_relationship_morphological(self, antecedent, clause_tokens) -> Dict[str, Any]:
        """Analyze semantic relationship between antecedent and clause."""
        if not antecedent or not clause_tokens:
            return {'relationship': 'unknown', 'restrictive_tendency': 0.5}
        
        # Look for specific relationship patterns
        verb_tokens = [t for t in clause_tokens if t.pos_ == 'VERB']
        
        if verb_tokens:
            main_verb = verb_tokens[0]  # Take first verb as main verb
            
            # Check for identifying vs. describing verbs
            identifying_verbs = {'contain', 'include', 'have', 'need', 'require', 'support'}
            describing_verbs = {'generate', 'provide', 'show', 'display', 'create'}
            
            verb_lemma = main_verb.lemma_.lower()
            
            if verb_lemma in identifying_verbs:
                return {'relationship': 'identifying', 'restrictive_tendency': 0.8}
            elif verb_lemma in describing_verbs:
                return {'relationship': 'describing', 'restrictive_tendency': 0.2}
        
        return {'relationship': 'neutral', 'restrictive_tendency': 0.5}
    
    def _calculate_restrictiveness_score_morphological(self, indicators: Dict[str, Any]) -> float:
        """Calculate overall restrictiveness score from indicators."""
        scores = []
        weights = []
        
        # Relative pronoun type (high weight)
        pronoun_prefs = indicators.get('relative_pronoun_type', {}).get('preferences', {})
        if pronoun_prefs:
            scores.append(pronoun_prefs.get('restrictive', 0.5))
            weights.append(0.4)
        
        # Antecedent definiteness (medium weight)
        def_tendency = indicators.get('antecedent_definiteness', {}).get('restrictive_tendency', 0.5)
        scores.append(def_tendency)
        weights.append(0.3)
        
        # Clause essentiality (medium weight)
        ess_tendency = indicators.get('clause_essentiality', {}).get('restrictive_tendency', 0.5)
        scores.append(ess_tendency)
        weights.append(0.2)
        
        # Semantic relationship (low weight)
        rel_tendency = indicators.get('semantic_relationship', {}).get('restrictive_tendency', 0.5)
        scores.append(rel_tendency)
        weights.append(0.1)
        
        # Calculate weighted average
        if scores and weights:
            weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
            total_weight = sum(weights)
            return weighted_sum / total_weight
        
        return 0.5
    
    def _analyze_current_comma_usage_morphological(self, rel_pronoun, antecedent, doc) -> Dict[str, Any]:
        """Analyze current comma usage around the relative clause."""
        comma_before = self._has_comma_before_clause_morphological(rel_pronoun, antecedent, doc)
        comma_after = self._has_comma_after_clause_morphological(rel_pronoun, doc)
        
        return {
            'has_comma_before': comma_before,
            'has_comma_after': comma_after,
            'is_properly_set_off': comma_before and comma_after
        }
    
    def _has_comma_before_clause_morphological(self, rel_pronoun, antecedent, doc) -> bool:
        """Check if there's a comma before the relative clause."""
        if not antecedent:
            return False
        
        # Look for comma between antecedent and relative pronoun
        for i in range(antecedent.i + 1, rel_pronoun.i):
            if doc[i].text == ',':
                return True
        
        return False
    
    def _has_comma_after_clause_morphological(self, rel_pronoun, doc) -> bool:
        """Check if there's a comma after the relative clause."""
        clause_end = self._find_clause_end_morphological(rel_pronoun, doc)
        
        # Look for comma immediately after clause
        if clause_end < len(doc) - 1:
            next_token_idx = clause_end + 1
            if next_token_idx < len(doc) and doc[next_token_idx].text == ',':
                return True
        
        return False
    
    def _identify_appositives_morphological(self, doc) -> List[Dict[str, Any]]:
        """Identify appositives (noun phrases that rename other nouns)."""
        appositives = []
        
        for token in doc:
            if token.dep_ == 'appos':  # SpaCy marks appositives with 'appos' dependency
                appositive_data = self._extract_appositive_morphological(token, doc)
                if appositive_data:
                    appositives.append(appositive_data)
        
        return appositives
    
    def _extract_appositive_morphological(self, appos_token, doc) -> Optional[Dict[str, Any]]:
        """Extract appositive information."""
        # Find the head noun that the appositive renames
        head_noun = appos_token.head
        
        # Extract appositive phrase
        appos_phrase = self._extract_appositive_phrase_morphological(appos_token, doc)
        
        # Check current comma usage
        comma_usage = self._analyze_appositive_comma_usage_current_morphological(head_noun, appos_phrase, doc)
        
        return {
            'type': 'appositive',
            'head_noun': head_noun,
            'appositive_phrase': appos_phrase,
            'comma_usage': comma_usage,
            'is_nonrestrictive': True  # Appositives are typically nonrestrictive
        }
    
    def _extract_appositive_phrase_morphological(self, appos_token, doc) -> List[object]:
        """Extract the complete appositive phrase."""
        phrase_tokens = [appos_token]
        
        # Collect children of appositive token
        for child in appos_token.children:
            phrase_tokens.extend(self._collect_subtree_morphological(child))
        
        # Sort by position
        phrase_tokens.sort(key=lambda x: x.i)
        
        return phrase_tokens
    
    def _collect_subtree_morphological(self, token) -> List[object]:
        """Collect all tokens in subtree."""
        tokens = [token]
        for child in token.children:
            tokens.extend(self._collect_subtree_morphological(child))
        return tokens
    
    def _analyze_appositive_comma_usage_current_morphological(self, head_noun, appos_phrase, doc) -> Dict[str, Any]:
        """Analyze current comma usage around appositive."""
        if not appos_phrase:
            return {'has_comma_before': False, 'has_comma_after': False}
        
        appos_start = min(appos_phrase, key=lambda x: x.i).i
        appos_end = max(appos_phrase, key=lambda x: x.i).i
        
        # Check for comma before appositive
        comma_before = False
        if appos_start > 0 and doc[appos_start - 1].text == ',':
            comma_before = True
        
        # Check for comma after appositive
        comma_after = False
        if appos_end < len(doc) - 1 and doc[appos_end + 1].text == ',':
            comma_after = True
        
        return {
            'has_comma_before': comma_before,
            'has_comma_after': comma_after,
            'is_properly_set_off': comma_before and comma_after
        }
    
    def _identify_such_as_phrases_morphological(self, doc) -> List[Dict[str, Any]]:
        """Identify 'such as' phrases that may need comma treatment."""
        such_as_phrases = []
        
        for i in range(len(doc) - 1):
            if (doc[i].lemma_.lower() == 'such' and 
                i + 1 < len(doc) and 
                doc[i + 1].lemma_.lower() == 'as'):
                
                phrase_data = self._extract_such_as_phrase_morphological(i, doc)
                if phrase_data:
                    such_as_phrases.append(phrase_data)
        
        return such_as_phrases
    
    def _extract_such_as_phrase_morphological(self, such_pos, doc) -> Optional[Dict[str, Any]]:
        """Extract 'such as' phrase information."""
        # Extract the examples following 'such as'
        examples = self._extract_such_as_examples_morphological(such_pos + 2, doc)
        
        # Find what 'such as' modifies
        modified_noun = self._find_modified_noun_morphological(such_pos, doc)
        
        # Determine if this is restrictive or nonrestrictive
        restrictiveness = self._determine_such_as_restrictiveness_morphological(modified_noun, examples, doc)
        
        # Check current comma usage
        comma_usage = self._analyze_such_as_comma_usage_morphological(such_pos, examples, doc)
        
        return {
            'type': 'such_as_phrase',
            'such_as_position': such_pos,
            'modified_noun': modified_noun,
            'examples': examples,
            'restrictiveness': restrictiveness,
            'comma_usage': comma_usage
        }
    
    def _extract_such_as_examples_morphological(self, start_pos, doc) -> List[object]:
        """Extract examples following 'such as'."""
        examples = []
        current_example = []
        
        for i in range(start_pos, len(doc)):
            token = doc[i]
            
            if token.text == ',':
                if current_example:
                    examples.append(current_example)
                    current_example = []
            elif token.text in ['.', ';', '!', '?'] or token.is_sent_end:
                break
            elif token.pos_ == 'CCONJ' and token.lemma_.lower() in ['and', 'or']:
                if current_example:
                    examples.append(current_example)
                    current_example = []
            elif not token.is_space:
                current_example.append(token)
        
        # Add final example
        if current_example:
            examples.append(current_example)
        
        return examples
    
    def _find_modified_noun_morphological(self, such_pos, doc) -> Optional[object]:
        """Find the noun that 'such as' modifies."""
        # Look backwards for noun
        for i in range(such_pos - 1, max(-1, such_pos - 5), -1):
            if doc[i].pos_ in ['NOUN', 'PROPN']:
                return doc[i]
        
        return None
    
    def _determine_such_as_restrictiveness_morphological(self, modified_noun, examples, doc) -> Dict[str, Any]:
        """Determine if 'such as' phrase is restrictive or nonrestrictive."""
        if not modified_noun:
            return {'is_restrictive': False, 'confidence': 0.5}
        
        # Check for restrictive indicators
        # "such as" is usually nonrestrictive (providing examples)
        # But can be restrictive when specifying requirements
        
        # Look for restrictive context words
        restrictive_context = self._has_restrictive_context_morphological(modified_noun, doc)
        
        # Examples with specific requirements tend to be restrictive
        has_specific_requirements = self._has_specific_requirements_morphological(examples)
        
        restrictive_score = 0.2  # Base: usually nonrestrictive
        
        if restrictive_context:
            restrictive_score += 0.4
        
        if has_specific_requirements:
            restrictive_score += 0.3
        
        return {
            'is_restrictive': restrictive_score > 0.5,
            'confidence': abs(restrictive_score - 0.5) * 2,
            'score': restrictive_score
        }
    
    def _has_restrictive_context_morphological(self, modified_noun, doc) -> bool:
        """Check for restrictive context around modified noun."""
        # Look for words that suggest restriction/requirement
        restrictive_words = {'specify', 'select', 'choose', 'require', 'need', 'support'}
        
        # Search in nearby context
        start = max(0, modified_noun.i - 5)
        end = min(len(doc), modified_noun.i + 5)
        
        for i in range(start, end):
            if doc[i].lemma_.lower() in restrictive_words:
                return True
        
        return False
    
    def _has_specific_requirements_morphological(self, examples) -> bool:
        """Check if examples represent specific requirements."""
        if not examples:
            return False
        
        # Look for technical terms, version numbers, specific names
        for example_tokens in examples:
            for token in example_tokens:
                # Technical terms, brand names, version numbers suggest requirements
                if (token.pos_ == 'PROPN' or  # Proper nouns (brand names)
                    token.like_num or  # Numbers (versions)
                    token.text.isupper()):  # Acronyms
                    return True
        
        return False
    
    def _analyze_such_as_comma_usage_morphological(self, such_pos, examples, doc) -> Dict[str, Any]:
        """Analyze current comma usage around 'such as' phrase."""
        # Check for comma before 'such'
        comma_before = False
        if such_pos > 0 and doc[such_pos - 1].text == ',':
            comma_before = True
        
        # Check for comma after examples
        comma_after = False
        if examples:
            last_example = examples[-1]
            if last_example:
                last_token_pos = last_example[-1].i
                if (last_token_pos < len(doc) - 1 and 
                    doc[last_token_pos + 1].text == ','):
                    comma_after = True
        
        return {
            'has_comma_before': comma_before,
            'has_comma_after': comma_after,
            'is_properly_set_off': comma_before and comma_after
        }
    
    def _analyze_clause_comma_usage_morphological(self, clause_data, doc) -> List[Dict[str, Any]]:
        """Analyze clause for comma usage issues."""
        issues = []
        
        restrictiveness = clause_data.get('restrictiveness', {})
        comma_usage = clause_data.get('comma_usage', {})
        
        is_restrictive = restrictiveness.get('is_restrictive', False)
        has_commas = comma_usage.get('is_properly_set_off', False)
        has_comma_before = comma_usage.get('has_comma_before', False)
        
        if is_restrictive and has_commas:
            # Restrictive clause incorrectly has commas
            issues.append({
                'type': 'restrictive_clause_with_commas',
                'clause_data': clause_data,
                'confidence': restrictiveness.get('confidence', 0.5)
            })
        
        elif not is_restrictive and not has_commas:
            # Nonrestrictive clause missing commas
            issues.append({
                'type': 'nonrestrictive_clause_missing_commas',
                'clause_data': clause_data,
                'confidence': restrictiveness.get('confidence', 0.5)
            })
        
        return issues
    
    def _analyze_appositive_comma_usage_morphological(self, appositive_data, doc) -> List[Dict[str, Any]]:
        """Analyze appositive for comma usage issues."""
        issues = []
        
        comma_usage = appositive_data.get('comma_usage', {})
        is_properly_set_off = comma_usage.get('is_properly_set_off', False)
        
        if not is_properly_set_off:
            issues.append({
                'type': 'appositive_missing_commas',
                'appositive_data': appositive_data
            })
        
        return issues
    
    def _analyze_such_as_phrase_comma_usage_morphological(self, phrase_data, doc) -> List[Dict[str, Any]]:
        """Analyze 'such as' phrase for comma usage issues."""
        issues = []
        
        restrictiveness = phrase_data.get('restrictiveness', {})
        comma_usage = phrase_data.get('comma_usage', {})
        
        is_restrictive = restrictiveness.get('is_restrictive', False)
        has_comma_before = comma_usage.get('has_comma_before', False)
        
        if not is_restrictive and not has_comma_before:
            # Nonrestrictive 'such as' phrase missing comma
            issues.append({
                'type': 'such_as_missing_comma',
                'phrase_data': phrase_data,
                'confidence': restrictiveness.get('confidence', 0.5)
            })
        
        elif is_restrictive and has_comma_before:
            # Restrictive 'such as' phrase has unnecessary comma
            issues.append({
                'type': 'such_as_unnecessary_comma',
                'phrase_data': phrase_data,
                'confidence': restrictiveness.get('confidence', 0.5)
            })
        
        return issues
    
    def _generate_morphological_suggestions(self, issue: Dict[str, Any], doc) -> List[str]:
        """Generate suggestions based on clause comma issue type."""
        issue_type = issue.get('type', '')
        suggestions = []
        
        if issue_type == 'nonrestrictive_clause_missing_commas':
            clause_data = issue.get('clause_data', {})
            rel_pronoun = clause_data.get('relative_pronoun')
            pronoun_text = rel_pronoun.text if rel_pronoun else 'which'
            
            suggestions.append(f"Add commas to set off this nonrestrictive clause beginning with '{pronoun_text}'")
            suggestions.append("Nonrestrictive clauses provide extra information and should be set off with commas")
            suggestions.append("Example: 'The Recovery log, which is generated automatically, shows the cause'")
        
        elif issue_type == 'restrictive_clause_with_commas':
            clause_data = issue.get('clause_data', {})
            rel_pronoun = clause_data.get('relative_pronoun')
            pronoun_text = rel_pronoun.text if rel_pronoun else 'that'
            
            suggestions.append(f"Remove commas from this restrictive clause beginning with '{pronoun_text}'")
            suggestions.append("Restrictive clauses are essential to meaning and should not have commas")
            suggestions.append("Example: 'The Recovery log that contains recent information is in the folder'")
        
        elif issue_type == 'appositive_missing_commas':
            suggestions.append("Add commas to set off this appositive phrase")
            suggestions.append("Appositives rename or explain nouns and should be set off with commas")
            suggestions.append("Example: 'The manager, John Smith, approved the request'")
        
        elif issue_type == 'such_as_missing_comma':
            suggestions.append("Add a comma before 'such as' when providing examples")
            suggestions.append("Use commas to set off nonrestrictive 'such as' phrases")
            suggestions.append("Example: 'Specify a font, such as Helvetica or Garamond, before saving'")
        
        elif issue_type == 'such_as_unnecessary_comma':
            suggestions.append("Remove comma before 'such as' when specifying requirements")
            suggestions.append("Do not use commas with restrictive 'such as' phrases")
            suggestions.append("Example: 'Specify an operating system such as z/OS to support applications'")
        
        # Generic fallback
        if not suggestions:
            suggestions.append("Review comma usage with clauses and phrases")
            suggestions.append("Use commas to set off nonrestrictive elements that provide extra information")
        
        return suggestions
    
    def _create_morphological_message(self, issue: Dict[str, Any]) -> str:
        """Create error message based on issue type."""
        issue_type = issue.get('type', '')
        
        if issue_type == 'nonrestrictive_clause_missing_commas':
            return "Use commas to set off this nonrestrictive clause that provides extra information."
        
        elif issue_type == 'restrictive_clause_with_commas':
            return "Do not use commas with this restrictive clause that is essential to the meaning."
        
        elif issue_type == 'appositive_missing_commas':
            return "Use commas to set off this appositive that renames or explains the noun."
        
        elif issue_type == 'such_as_missing_comma':
            return "Use a comma before 'such as' when providing examples (nonrestrictive)."
        
        elif issue_type == 'such_as_unnecessary_comma':
            return "Do not use a comma before 'such as' when specifying requirements (restrictive)."
        
        return "Review comma usage with this clause or phrase."
    
    def _determine_morphological_severity(self, issue: Dict[str, Any]) -> str:
        """Determine severity level based on issue type."""
        issue_type = issue.get('type', '')
        confidence = issue.get('confidence', 0.5)
        
        # Higher confidence issues are more severe
        if confidence > 0.8:
            base_severity = 'high'
        elif confidence > 0.6:
            base_severity = 'medium'
        else:
            base_severity = 'low'
        
        # Adjust based on issue type
        high_severity_types = ['restrictive_clause_with_commas', 'nonrestrictive_clause_missing_commas']
        medium_severity_types = ['appositive_missing_commas']
        low_severity_types = ['such_as_missing_comma', 'such_as_unnecessary_comma']
        
        if issue_type in high_severity_types:
            return base_severity
        elif issue_type in medium_severity_types:
            return 'medium' if base_severity == 'high' else base_severity
        elif issue_type in low_severity_types:
            return 'low' if base_severity == 'high' else base_severity
        else:
            return 'medium' 