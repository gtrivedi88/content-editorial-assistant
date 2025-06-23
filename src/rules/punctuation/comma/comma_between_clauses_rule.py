"""
Comma Usage Rule - Ensures proper use of commas using pure SpaCy morphological analysis.
Uses SpaCy dependency parsing, POS tagging, and morphological features to detect comma usage patterns.
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


class CommaRule(BaseRule):
    """Rule to detect comma usage issues using pure SpaCy morphological analysis."""
    
    def _get_rule_type(self) -> str:
        return 'comma_usage'
    
    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """Analyze text for comma usage issues using pure SpaCy linguistic analysis."""
        if not nlp:
            return []  # Skip analysis if SpaCy not available
        
        errors = []
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
                
            doc = nlp(sentence)
            
            # Check for long sentences (>32 words) first
            word_count = len([token for token in doc if not token.is_punct and not token.is_space])
            if word_count > 32:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="This sentence is longer than 32 words. Consider rewriting it, separating it into multiple sentences, or presenting its contents in a vertical list.",
                    suggestions=[
                        "Break this sentence into multiple shorter sentences",
                        "Consider using a vertical list format",
                        "Restructure to reduce complexity"
                    ],
                    severity='medium',
                    issue_type='long_sentence',
                    word_count=word_count
                ))
            
            # Find comma usage issues
            comma_issues = self._find_comma_usage_issues_morphological(doc, sentence)
            
            for issue in comma_issues:
                suggestions = self._generate_morphological_suggestions(issue, doc)
                
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message=self._create_morphological_message(issue),
                    suggestions=suggestions,
                    severity=self._determine_morphological_severity(issue),
                    comma_issue=issue
                ))
        
        return errors
    
    def _find_comma_usage_issues_morphological(self, doc, sentence: str) -> List[Dict[str, Any]]:
        """Find comma usage issues using SpaCy morphological and syntactic analysis."""
        issues = []
        
        # Analyze each token and its context
        for i, token in enumerate(doc):
            # Check coordinating conjunction patterns
            if self._is_coordinating_conjunction_morphological(token):
                conj_issue = self._analyze_coordinating_conjunction_usage_morphological(token, doc)
                if conj_issue:
                    issues.append(conj_issue)
            
            # Check "then" usage (not a coordinating conjunction)
            if self._is_then_conjunction_morphological(token):
                then_issue = self._analyze_then_conjunction_usage_morphological(token, doc)
                if then_issue:
                    issues.append(then_issue)
            
            # Check comma usage in series/lists
            if self._is_comma_morphological(token):
                series_issue = self._analyze_series_comma_usage_morphological(token, doc)
                if series_issue:
                    issues.append(series_issue)
                
                # Check comma with introductory elements
                intro_issue = self._analyze_introductory_comma_usage_morphological(token, doc)
                if intro_issue:
                    issues.append(intro_issue)
        
        # Check for missing commas in series
        missing_series_issues = self._find_missing_series_commas_morphological(doc)
        issues.extend(missing_series_issues)
        
        # Check for missing commas with coordinating conjunctions
        missing_conj_issues = self._find_missing_conjunction_commas_morphological(doc)
        issues.extend(missing_conj_issues)
        
        return issues
    
    def _is_coordinating_conjunction_morphological(self, token) -> bool:
        """Check if token is a coordinating conjunction using morphological analysis."""
        # Use SpaCy's dependency labels and POS tags
        if token.pos_ == 'CCONJ':
            # Analyze morphological features to confirm it's coordinating
            lemma = token.lemma_.lower()
            # The FANBOYS coordinating conjunctions: for, and, nor, but, or, yet, so
            coordinating_lemmas = {'and', 'but', 'or', 'nor', 'for', 'so', 'yet'}
            return lemma in coordinating_lemmas
        return False
    
    def _is_then_conjunction_morphological(self, token) -> bool:
        """Check if token is 'then' used as conjunction using morphological analysis."""
        return (token.lemma_.lower() == 'then' and 
                token.pos_ in ['ADV', 'CCONJ'] and
                token.dep_ in ['advmod', 'cc'])
    
    def _is_comma_morphological(self, token) -> bool:
        """Check if token is a comma using morphological analysis."""
        return token.pos_ == "PUNCT" and token.text == ","
    
    def _analyze_coordinating_conjunction_usage_morphological(self, conj_token, doc) -> Optional[Dict[str, Any]]:
        """Analyze coordinating conjunction for comma usage issues."""
        issues = []
        
        # Find clauses on both sides of conjunction
        left_clause = self._extract_clause_before_morphological(conj_token, doc)
        right_clause = self._extract_clause_after_morphological(conj_token, doc)
        
        if not left_clause or not right_clause:
            return None
        
        # Check if both are independent clauses
        left_is_independent = self._is_independent_clause_morphological(left_clause)
        right_is_independent = self._is_independent_clause_morphological(right_clause)
        
        # Check for comma before conjunction
        has_comma_before = self._has_comma_before_morphological(conj_token, doc)
        
        if left_is_independent and right_is_independent:
            # Both are independent - should have comma unless short/closely related
            if not has_comma_before:
                if not self._are_clauses_short_or_related_morphological(left_clause, right_clause):
                    issues.append('missing_comma_independent_clauses')
        else:
            # Mixed independent/dependent - should not have comma unless needed for clarity
            if has_comma_before:
                if not self._needs_comma_for_clarity_morphological(left_clause, right_clause, doc):
                    issues.append('unnecessary_comma_mixed_clauses')
        
        if issues:
            return {
                'type': 'coordinating_conjunction_comma',
                'issues': issues,
                'conjunction_token': conj_token,
                'left_clause': left_clause,
                'right_clause': right_clause,
                'left_is_independent': left_is_independent,
                'right_is_independent': right_is_independent,
                'has_comma_before': has_comma_before
            }
        
        return None
    
    def _analyze_then_conjunction_usage_morphological(self, then_token, doc) -> Optional[Dict[str, Any]]:
        """Analyze 'then' conjunction usage - it's not a coordinating conjunction."""
        # Check if 'then' is being used incorrectly to join independent clauses
        left_clause = self._extract_clause_before_morphological(then_token, doc)
        right_clause = self._extract_clause_after_morphological(then_token, doc)
        
        if not left_clause or not right_clause:
            return None
        
        left_is_independent = self._is_independent_clause_morphological(left_clause)
        right_is_independent = self._is_independent_clause_morphological(right_clause)
        
        if left_is_independent and right_is_independent:
            # Check current punctuation pattern
            has_comma_before = self._has_comma_before_morphological(then_token, doc)
            has_semicolon_before = self._has_semicolon_before_morphological(then_token, doc)
            has_coordinating_conj = self._has_coordinating_conjunction_before_then_morphological(then_token, doc)
            
            issues = []
            if not has_semicolon_before and not has_coordinating_conj:
                if has_comma_before:
                    issues.append('comma_then_incorrect')
                else:
                    issues.append('then_without_proper_punctuation')
            
            if issues:
                return {
                    'type': 'then_conjunction_usage',
                    'issues': issues,
                    'then_token': then_token,
                    'left_clause': left_clause,
                    'right_clause': right_clause,
                    'has_comma_before': has_comma_before,
                    'has_semicolon_before': has_semicolon_before,
                    'has_coordinating_conj': has_coordinating_conj
                }
        
        return None
    
    def _analyze_series_comma_usage_morphological(self, comma_token, doc) -> Optional[Dict[str, Any]]:
        """Analyze comma usage in series/lists using morphological analysis."""
        # Check if this comma is part of a series
        series_context = self._identify_series_context_morphological(comma_token, doc)
        
        if series_context:
            # Analyze series comma placement
            issues = []
            
            # Check for proper comma separation in series
            if not self._has_proper_series_separation_morphological(series_context, doc):
                issues.append('improper_series_separation')
            
            if issues:
                return {
                    'type': 'series_comma_usage',
                    'issues': issues,
                    'comma_token': comma_token,
                    'series_context': series_context
                }
        
        return None
    
    def _analyze_introductory_comma_usage_morphological(self, comma_token, doc) -> Optional[Dict[str, Any]]:
        """Analyze comma usage with introductory elements."""
        # Check if comma follows introductory phrase/clause
        intro_element = self._identify_introductory_element_morphological(comma_token, doc)
        
        if intro_element:
            issues = []
            
            # Introductory elements should be followed by comma
            if not self._has_proper_introductory_comma_morphological(intro_element, comma_token, doc):
                issues.append('missing_introductory_comma')
            
            if issues:
                return {
                    'type': 'introductory_comma_usage',
                    'issues': issues,
                    'comma_token': comma_token,
                    'introductory_element': intro_element
                }
        
        return None
    
    def _extract_clause_before_morphological(self, token, doc) -> Optional[List]:
        """Extract clause before given token using dependency analysis."""
        clause_tokens = []
        
        # Find the start of the clause by looking for clause boundaries
        start_idx = 0
        for i in range(token.i - 1, -1, -1):
            current_token = doc[i]
            
            # Stop at sentence boundaries or other clause boundaries
            if (current_token.is_sent_start or 
                current_token.text in ['.', ';', ':', '!', '?'] or
                (current_token.pos_ == 'SCONJ' and i != token.i - 1)):
                start_idx = i + 1
                break
        
        # Extract tokens from start to current position
        for i in range(start_idx, token.i):
            if not doc[i].is_space:
                clause_tokens.append(doc[i])
        
        return clause_tokens if clause_tokens else None
    
    def _extract_clause_after_morphological(self, token, doc) -> Optional[List]:
        """Extract clause after given token using dependency analysis."""
        clause_tokens = []
        
        # Find the end of the clause
        end_idx = len(doc)
        for i in range(token.i + 1, len(doc)):
            current_token = doc[i]
            
            # Stop at sentence boundaries or other clause boundaries
            if (current_token.is_sent_end or 
                current_token.text in ['.', ';', ':', '!', '?'] or
                (current_token.pos_ == 'CCONJ' and i != token.i + 1)):
                end_idx = i
                break
        
        # Extract tokens from current position to end
        for i in range(token.i + 1, end_idx):
            if not doc[i].is_space:
                clause_tokens.append(doc[i])
        
        return clause_tokens if clause_tokens else None
    
    def _is_independent_clause_morphological(self, clause_tokens) -> bool:
        """Check if clause tokens form an independent clause using morphological analysis."""
        if not clause_tokens:
            return False
        
        # Independent clause needs subject and predicate
        has_subject = False
        has_finite_verb = False
        
        for token in clause_tokens:
            # Check for subject
            if token.dep_ in ['nsubj', 'nsubjpass', 'expl']:
                has_subject = True
            
            # Check for finite verb (main verb, not auxiliary or participle)
            if token.pos_ == 'VERB' and token.dep_ in ['ROOT', 'ccomp', 'xcomp']:
                # Check if it's finite (not participle or infinitive)
                morph_features = self._get_morphological_features(token)
                verb_form = morph_features.get('morph', {}).get('VerbForm', '')
                if verb_form != 'Part' and verb_form != 'Inf':
                    has_finite_verb = True
        
        return has_subject and has_finite_verb
    
    def _has_comma_before_morphological(self, token, doc) -> bool:
        """Check if there's a comma before the given token."""
        if token.i == 0:
            return False
        
        # Look for comma in preceding tokens (allowing for spaces)
        for i in range(token.i - 1, max(-1, token.i - 3), -1):
            if doc[i].text == ',':
                return True
            elif not doc[i].is_space:
                break
        
        return False
    
    def _has_semicolon_before_morphological(self, token, doc) -> bool:
        """Check if there's a semicolon before the given token."""
        if token.i == 0:
            return False
        
        # Look for semicolon in preceding tokens (allowing for spaces)
        for i in range(token.i - 1, max(-1, token.i - 3), -1):
            if doc[i].text == ';':
                return True
            elif not doc[i].is_space:
                break
        
        return False
    
    def _has_coordinating_conjunction_before_then_morphological(self, then_token, doc) -> bool:
        """Check if there's a coordinating conjunction before 'then'."""
        # Look for pattern like "and then" or "but then"
        if then_token.i == 0:
            return False
        
        for i in range(then_token.i - 1, max(-1, then_token.i - 3), -1):
            if self._is_coordinating_conjunction_morphological(doc[i]):
                return True
            elif not doc[i].is_space:
                break
        
        return False
    
    def _are_clauses_short_or_related_morphological(self, left_clause, right_clause) -> bool:
        """Check if clauses are short or closely related."""
        # Count content words in each clause
        left_content = len([t for t in left_clause if not t.is_punct and not t.is_space and not t.is_stop])
        right_content = len([t for t in right_clause if not t.is_punct and not t.is_space and not t.is_stop])
        
        # Consider short if both clauses have few content words
        if left_content <= 3 and right_content <= 3:
            return True
        
        # Check semantic relatedness using morphological similarity
        relatedness_score = self._calculate_clause_relatedness_morphological(left_clause, right_clause)
        return relatedness_score > 0.7
    
    def _calculate_clause_relatedness_morphological(self, clause1, clause2) -> float:
        """Calculate semantic relatedness between clauses using morphological analysis."""
        if not clause1 or not clause2:
            return 0.0
        
        # Extract content words from both clauses
        content1 = [t for t in clause1 if not t.is_punct and not t.is_space and not t.is_stop]
        content2 = [t for t in clause2 if not t.is_punct and not t.is_space and not t.is_stop]
        
        if not content1 or not content2:
            return 0.0
        
        # Calculate morphological similarity
        similarities = []
        for t1 in content1:
            for t2 in content2:
                features1 = self._get_morphological_features(t1)
                features2 = self._get_morphological_features(t2)
                similarity = self._calculate_morphological_similarity(features1, features2)
                similarities.append(similarity)
        
        return max(similarities) if similarities else 0.0
    
    def _needs_comma_for_clarity_morphological(self, left_clause, right_clause, doc) -> bool:
        """Check if comma is needed for clarity between clauses."""
        # Look for potential ambiguity patterns
        if not left_clause or not right_clause:
            return False
        
        # Check for ambiguous attachment - last word of left clause could modify right clause
        if left_clause:
            last_token = left_clause[-1]
            first_token = right_clause[0] if right_clause else None
            
            if first_token:
                # Check if last token could grammatically modify first token of right clause
                if (last_token.pos_ in ['ADJ', 'NOUN'] and 
                    first_token.pos_ in ['NOUN', 'VERB']):
                    return True
        
        return False
    
    def _identify_series_context_morphological(self, comma_token, doc) -> Optional[Dict[str, Any]]:
        """Identify if comma is part of a series using morphological analysis."""
        # Look for coordination patterns around the comma
        series_elements = []
        
        # Find elements before comma
        before_element = self._find_series_element_before_morphological(comma_token, doc)
        if before_element:
            series_elements.append(before_element)
        
        # Find elements after comma
        after_element = self._find_series_element_after_morphological(comma_token, doc)
        if after_element:
            series_elements.append(after_element)
        
        # Check for additional series indicators (more commas, "and", "or")
        has_coordination = self._has_series_coordination_morphological(comma_token, doc)
        
        if len(series_elements) >= 2 or has_coordination:
            return {
                'elements': series_elements,
                'has_coordination': has_coordination,
                'comma_position': comma_token.i
            }
        
        return None
    
    def _find_series_element_before_morphological(self, comma_token, doc) -> Optional[List]:
        """Find series element before comma."""
        if comma_token.i == 0:
            return None
        
        element_tokens = []
        
        # Look backwards for the element
        for i in range(comma_token.i - 1, -1, -1):
            token = doc[i]
            
            # Stop at series boundaries
            if token.text in [',', ';', ':', 'and', 'or', 'but'] and i != comma_token.i - 1:
                break
            
            if not token.is_space:
                element_tokens.insert(0, token)
            
            # Don't go too far back
            if len(element_tokens) > 10:
                break
        
        return element_tokens if element_tokens else None
    
    def _find_series_element_after_morphological(self, comma_token, doc) -> Optional[List]:
        """Find series element after comma."""
        if comma_token.i >= len(doc) - 1:
            return None
        
        element_tokens = []
        
        # Look forward for the element
        for i in range(comma_token.i + 1, len(doc)):
            token = doc[i]
            
            # Stop at series boundaries
            if token.text in [',', ';', ':', '.', 'and', 'or', 'but'] and len(element_tokens) > 0:
                break
            
            if not token.is_space:
                element_tokens.append(token)
            
            # Don't go too far forward
            if len(element_tokens) > 10:
                break
        
        return element_tokens if element_tokens else None
    
    def _has_series_coordination_morphological(self, comma_token, doc) -> bool:
        """Check for coordination patterns indicating series."""
        # Look for "and", "or" or additional commas nearby
        search_range = 5
        
        for i in range(max(0, comma_token.i - search_range), 
                      min(len(doc), comma_token.i + search_range + 1)):
            if i == comma_token.i:
                continue
            
            token = doc[i]
            if (token.text in [',', 'and', 'or'] or 
                self._is_coordinating_conjunction_morphological(token)):
                return True
        
        return False
    
    def _has_proper_series_separation_morphological(self, series_context, doc) -> bool:
        """Check if series has proper comma separation."""
        # This is a basic check - more sophisticated logic could be added
        elements = series_context.get('elements', [])
        return len(elements) >= 2
    
    def _identify_introductory_element_morphological(self, comma_token, doc) -> Optional[Dict[str, Any]]:
        """Identify introductory element before comma."""
        if comma_token.i == 0:
            return None
        
        # Look for introductory patterns at sentence start
        intro_tokens = []
        
        # Find start of sentence or introductory element
        start_idx = 0
        for i in range(comma_token.i - 1, -1, -1):
            token = doc[i]
            if token.is_sent_start or token.text in ['.', ';', ':', '!', '?']:
                start_idx = i + 1 if not token.is_sent_start else i
                break
        
        # Extract tokens from start to comma
        for i in range(start_idx, comma_token.i):
            if not doc[i].is_space:
                intro_tokens.append(doc[i])
        
        if intro_tokens:
            # Check if this looks like an introductory element
            if self._is_introductory_pattern_morphological(intro_tokens):
                return {
                    'tokens': intro_tokens,
                    'type': self._classify_introductory_type_morphological(intro_tokens)
                }
        
        return None
    
    def _is_introductory_pattern_morphological(self, tokens) -> bool:
        """Check if tokens form an introductory pattern."""
        if not tokens:
            return False
        
        # Common introductory patterns:
        # - Prepositional phrases
        # - Subordinate clauses  
        # - Adverbial phrases
        # - Participial phrases
        
        first_token = tokens[0]
        
        # Prepositional phrase
        if first_token.pos_ == 'ADP':
            return True
        
        # Subordinating conjunction
        if first_token.pos_ == 'SCONJ':
            return True
        
        # Adverbial introductory words
        if (first_token.pos_ == 'ADV' and 
            first_token.lemma_.lower() in ['however', 'therefore', 'moreover', 'furthermore', 'meanwhile', 'consequently']):
            return True
        
        # Participial phrases (starting with -ing or -ed forms)
        if (first_token.pos_ == 'VERB' and 
            hasattr(first_token, 'morph') and 
            'VerbForm=Part' in str(first_token.morph)):
            return True
        
        return False
    
    def _classify_introductory_type_morphological(self, tokens) -> str:
        """Classify type of introductory element."""
        if not tokens:
            return 'unknown'
        
        first_token = tokens[0]
        
        if first_token.pos_ == 'ADP':
            return 'prepositional_phrase'
        elif first_token.pos_ == 'SCONJ':
            return 'subordinate_clause'
        elif first_token.pos_ == 'ADV':
            return 'adverbial_phrase'
        elif first_token.pos_ == 'VERB':
            return 'participial_phrase'
        else:
            return 'other'
    
    def _has_proper_introductory_comma_morphological(self, intro_element, comma_token, doc) -> bool:
        """Check if introductory element has proper comma placement."""
        # Basic check - introductory element should be immediately followed by comma
        intro_tokens = intro_element.get('tokens', [])
        if not intro_tokens:
            return True
        
        last_intro_token = intro_tokens[-1]
        return last_intro_token.i + 1 == comma_token.i
    
    def _find_missing_series_commas_morphological(self, doc) -> List[Dict[str, Any]]:
        """Find places where series commas should be added."""
        issues = []
        
        # Look for coordination without proper comma separation
        for token in doc:
            if self._is_coordinating_conjunction_morphological(token):
                # Check if this is part of a series that's missing commas
                series_issue = self._check_missing_series_comma_morphological(token, doc)
                if series_issue:
                    issues.append(series_issue)
        
        return issues
    
    def _check_missing_series_comma_morphological(self, conj_token, doc) -> Optional[Dict[str, Any]]:
        """Check if coordination is missing series comma."""
        # Look for pattern like "A B and C" where comma should be "A, B, and C"
        left_elements = self._find_series_elements_before_conjunction_morphological(conj_token, doc)
        
        if len(left_elements) >= 2:
            # Check if there are missing commas between elements
            missing_positions = []
            
            for i in range(len(left_elements) - 1):
                # Check if there's a comma between elements
                element1_end = left_elements[i][-1].i if left_elements[i] else -1
                element2_start = left_elements[i + 1][0].i if left_elements[i + 1] else -1
                
                if element1_end >= 0 and element2_start >= 0:
                    has_comma = any(doc[j].text == ',' 
                                  for j in range(element1_end + 1, element2_start))
                    if not has_comma:
                        missing_positions.append(element1_end + 1)
            
            if missing_positions:
                return {
                    'type': 'missing_series_comma',
                    'conjunction_token': conj_token,
                    'missing_positions': missing_positions,
                    'series_elements': left_elements
                }
        
        return None
    
    def _find_series_elements_before_conjunction_morphological(self, conj_token, doc) -> List[List]:
        """Find series elements before conjunction."""
        elements = []
        current_element = []
        
        # Look backwards from conjunction
        for i in range(conj_token.i - 1, -1, -1):
            token = doc[i]
            
            if token.text == ',':
                if current_element:
                    elements.insert(0, current_element[::-1])  # Reverse since we're going backwards
                    current_element = []
            elif token.is_sent_start or token.text in ['.', ';', ':']:
                break
            elif not token.is_space and not token.is_punct:
                current_element.append(token)
        
        # Add the final element
        if current_element:
            elements.insert(0, current_element[::-1])
        
        return elements
    
    def _find_missing_conjunction_commas_morphological(self, doc) -> List[Dict[str, Any]]:
        """Find places where commas should be added before coordinating conjunctions."""
        issues = []
        
        for token in doc:
            if self._is_coordinating_conjunction_morphological(token):
                # Check if comma should be present but is missing
                missing_issue = self._check_missing_conjunction_comma_morphological(token, doc)
                if missing_issue:
                    issues.append(missing_issue)
        
        return issues
    
    def _check_missing_conjunction_comma_morphological(self, conj_token, doc) -> Optional[Dict[str, Any]]:
        """Check if conjunction is missing a comma."""
        left_clause = self._extract_clause_before_morphological(conj_token, doc)
        right_clause = self._extract_clause_after_morphological(conj_token, doc)
        
        if not left_clause or not right_clause:
            return None
        
        left_is_independent = self._is_independent_clause_morphological(left_clause)
        right_is_independent = self._is_independent_clause_morphological(right_clause)
        has_comma_before = self._has_comma_before_morphological(conj_token, doc)
        
        # Missing comma if both independent and no comma present and not short/related
        if (left_is_independent and right_is_independent and 
            not has_comma_before and 
            not self._are_clauses_short_or_related_morphological(left_clause, right_clause)):
            
            return {
                'type': 'missing_conjunction_comma',
                'conjunction_token': conj_token,
                'left_clause': left_clause,
                'right_clause': right_clause,
                'position': conj_token.i
            }
        
        return None
    
    def _generate_morphological_suggestions(self, issue: Dict[str, Any], doc) -> List[str]:
        """Generate suggestions based on comma issue type."""
        issue_type = issue.get('type', '')
        suggestions = []
        
        if issue_type == 'coordinating_conjunction_comma':
            issues = issue.get('issues', [])
            conj_token = issue.get('conjunction_token')
            conj_text = conj_token.text if conj_token else 'conjunction'
            
            if 'missing_comma_independent_clauses' in issues:
                suggestions.append(f"Add a comma before '{conj_text}' to separate the independent clauses")
                suggestions.append("Consider if the clauses are short and closely related (comma may be optional)")
            
            if 'unnecessary_comma_mixed_clauses' in issues:
                suggestions.append(f"Remove the comma before '{conj_text}' when connecting independent and dependent clauses")
                suggestions.append("Keep the comma only if needed to prevent misreading")
        
        elif issue_type == 'then_conjunction_usage':
            issues = issue.get('issues', [])
            
            if 'comma_then_incorrect' in issues:
                suggestions.append("Replace 'comma then' with 'semicolon then' or add a coordinating conjunction")
                suggestions.append("Correct: 'Click Start; then select a program'")
                suggestions.append("Correct: 'Click Start, and then select a program'")
            
            if 'then_without_proper_punctuation' in issues:
                suggestions.append("Add a semicolon before 'then' or use a coordinating conjunction")
                suggestions.append("Incorrect: 'Click Start then select'")
                suggestions.append("Correct: 'Click Start; then select' or 'Click Start, and then select'")
        
        elif issue_type == 'series_comma_usage':
            suggestions.append("Use commas to separate elements in a series")
            suggestions.append("Consider using Oxford comma for clarity: 'A, B, and C'")
        
        elif issue_type == 'introductory_comma_usage':
            intro_type = issue.get('introductory_element', {}).get('type', 'element')
            suggestions.append(f"Add a comma after the introductory {intro_type}")
            suggestions.append("Introductory elements should be followed by a comma")
        
        elif issue_type == 'missing_series_comma':
            suggestions.append("Add commas between items in the series")
            suggestions.append("Use consistent comma placement in lists")
        
        elif issue_type == 'missing_conjunction_comma':
            conj_token = issue.get('conjunction_token')
            conj_text = conj_token.text if conj_token else 'conjunction'
            suggestions.append(f"Add a comma before '{conj_text}' to separate independent clauses")
        
        # Generic fallback
        if not suggestions:
            suggestions.append("Review comma usage according to standard grammar rules")
            suggestions.append("Consider the relationship between clauses and elements")
        
        return suggestions
    
    def _create_morphological_message(self, issue: Dict[str, Any]) -> str:
        """Create error message based on issue type."""
        issue_type = issue.get('type', '')
        
        if issue_type == 'coordinating_conjunction_comma':
            issues = issue.get('issues', [])
            conj_token = issue.get('conjunction_token')
            conj_text = conj_token.text if conj_token else 'conjunction'
            
            if 'missing_comma_independent_clauses' in issues:
                return f"Use a comma before '{conj_text}' when connecting independent clauses, unless they are short or closely related."
            
            if 'unnecessary_comma_mixed_clauses' in issues:
                return f"Do not use a comma before '{conj_text}' when connecting independent and dependent clauses unless needed for clarity."
        
        elif issue_type == 'then_conjunction_usage':
            issues = issue.get('issues', [])
            
            if 'comma_then_incorrect' in issues:
                return "'Then' is not a coordinating conjunction. Use a semicolon before 'then' or add a coordinating conjunction."
            
            if 'then_without_proper_punctuation' in issues:
                return "Cannot join independent clauses with 'then' without proper punctuation. Use semicolon or coordinating conjunction."
        
        elif issue_type == 'series_comma_usage':
            return "Use commas to separate elements in a series, such as items, clauses, or phrases."
        
        elif issue_type == 'introductory_comma_usage':
            intro_type = issue.get('introductory_element', {}).get('type', 'element')
            return f"Use a comma after introductory {intro_type.replace('_', ' ')}s."
        
        elif issue_type == 'missing_series_comma':
            return "Add commas between items in this series for proper separation."
        
        elif issue_type == 'missing_conjunction_comma':
            conj_token = issue.get('conjunction_token')
            conj_text = conj_token.text if conj_token else 'conjunction'
            return f"Add a comma before '{conj_text}' when connecting independent clauses."
        
        return "Review comma usage in this sentence."
    
    def _determine_morphological_severity(self, issue: Dict[str, Any]) -> str:
        """Determine severity level based on issue type."""
        issue_type = issue.get('type', '')
        
        # High severity for grammar errors that affect meaning
        high_severity_types = ['then_conjunction_usage', 'missing_conjunction_comma']
        
        # Medium severity for clarity issues
        medium_severity_types = ['coordinating_conjunction_comma', 'missing_series_comma']
        
        # Low severity for style preferences
        low_severity_types = ['series_comma_usage', 'introductory_comma_usage']
        
        if issue_type in high_severity_types:
            return 'high'
        elif issue_type in medium_severity_types:
            return 'medium'
        elif issue_type in low_severity_types:
            return 'low'
        else:
            return 'medium' 