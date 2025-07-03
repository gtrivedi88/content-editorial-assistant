"""
Semicolons Rule
Based on IBM Style Guide topic: "Semicolons"
"""
from typing import List, Dict, Any, Set, Tuple, Optional
import re
from .base_punctuation_rule import BasePunctuationRule

class SemicolonsRule(BasePunctuationRule):
    """
    Comprehensive semicolons checker using morphological spaCy analysis with linguistic anchors.
    Handles independent clauses, complex lists, conjunctive adverbs, series, and formatting.
    """
    
    def _get_rule_type(self) -> str:
        return 'semicolons'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        
        # Fallback to regex-based analysis if nlp is unavailable
        if not nlp:
            return self._analyze_with_regex(text, sentences)
        
        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            errors.extend(self._analyze_sentence_with_nlp(doc, sentence, i))
            
        return errors

    def _analyze_sentence_with_nlp(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Comprehensive NLP-based semicolon analysis using linguistic anchors."""
        errors = []
        
        # Find all semicolon tokens
        semicolon_analysis = self._analyze_semicolon_structure(doc)
        
        # Check each semicolon usage
        for semicolon_info in semicolon_analysis:
            errors.extend(self._analyze_semicolon_context(doc, semicolon_info, sentence, sentence_index))
            errors.extend(self._check_semicolon_spacing(doc, semicolon_info, sentence, sentence_index))
            errors.extend(self._check_semicolon_appropriateness(doc, semicolon_info, sentence, sentence_index))
            errors.extend(self._check_conjunctive_adverb_usage(doc, semicolon_info, sentence, sentence_index))
            errors.extend(self._check_independent_clause_connection(doc, semicolon_info, sentence, sentence_index))
            errors.extend(self._check_complex_list_usage(doc, semicolon_info, sentence, sentence_index))
        
        # Check for missing semicolons
        errors.extend(self._check_missing_semicolons(doc, sentence, sentence_index))
        
        return errors

    def _analyze_semicolon_structure(self, doc) -> List[Dict[str, Any]]:
        """Analyze the structure and position of semicolons in the document."""
        semicolon_positions = []
        
        for i, token in enumerate(doc):
            if token.text == ';':
                semicolon_positions.append({
                    'index': i,
                    'token': token,
                    'before_context': self._get_context_before(doc, i),
                    'after_context': self._get_context_after(doc, i),
                    'clause_before': self._get_clause_before(doc, i),
                    'clause_after': self._get_clause_after(doc, i)
                })
        
        return semicolon_positions

    def _get_context_before(self, doc, semicolon_idx: int) -> Dict[str, Any]:
        """Get context information before the semicolon."""
        start_idx = max(0, semicolon_idx - 10)
        tokens_before = doc[start_idx:semicolon_idx]
        
        return {
            'tokens': tokens_before,
            'last_punctuation': self._find_last_punctuation(tokens_before),
            'has_conjunctive_adverb': self._has_conjunctive_adverb_before(tokens_before),
            'clause_structure': self._analyze_clause_structure(tokens_before)
        }

    def _get_context_after(self, doc, semicolon_idx: int) -> Dict[str, Any]:
        """Get context information after the semicolon."""
        end_idx = min(len(doc), semicolon_idx + 10)
        tokens_after = doc[semicolon_idx + 1:end_idx]
        
        return {
            'tokens': tokens_after,
            'first_word': tokens_after[0] if tokens_after else None,
            'has_conjunctive_adverb': self._has_conjunctive_adverb_after(tokens_after),
            'clause_structure': self._analyze_clause_structure(tokens_after)
        }

    def _get_clause_before(self, doc, semicolon_idx: int) -> Dict[str, Any]:
        """Extract and analyze the clause before the semicolon."""
        # Find the start of the clause (after previous major punctuation)
        start_idx = 0
        for i in range(semicolon_idx - 1, -1, -1):
            if doc[i].text in ['.', '!', '?', ';']:
                start_idx = i + 1
                break
        
        clause_tokens = doc[start_idx:semicolon_idx]
        
        return {
            'tokens': clause_tokens,
            'is_independent': self._is_independent_clause(clause_tokens),
            'has_subject': self._has_subject(clause_tokens),
            'has_predicate': self._has_predicate(clause_tokens),
            'structure_type': self._classify_clause_structure(clause_tokens)
        }

    def _get_clause_after(self, doc, semicolon_idx: int) -> Dict[str, Any]:
        """Extract and analyze the clause after the semicolon."""
        # Find the end of the clause (before next major punctuation)
        end_idx = len(doc)
        for i in range(semicolon_idx + 1, len(doc)):
            if doc[i].text in ['.', '!', '?', ';']:
                end_idx = i
                break
        
        clause_tokens = doc[semicolon_idx + 1:end_idx]
        
        return {
            'tokens': clause_tokens,
            'is_independent': self._is_independent_clause(clause_tokens),
            'has_subject': self._has_subject(clause_tokens),
            'has_predicate': self._has_predicate(clause_tokens),
            'structure_type': self._classify_clause_structure(clause_tokens)
        }

    def _find_last_punctuation(self, tokens) -> Optional[str]:
        """Find the last punctuation mark in a token sequence."""
        for token in reversed(tokens):
            if token.text in ['.', '!', '?', ';', ':', ',']:
                return token.text
        return None

    def _has_conjunctive_adverb_before(self, tokens) -> bool:
        """Check if there's a conjunctive adverb before the semicolon using linguistic anchors."""
        conjunctive_adverbs = {
            'however', 'therefore', 'moreover', 'furthermore', 'nevertheless', 
            'consequently', 'accordingly', 'meanwhile', 'otherwise', 'hence',
            'thus', 'indeed', 'besides', 'likewise', 'nonetheless', 'instead',
            'subsequently', 'additionally', 'similarly', 'conversely', 'alternatively'
        }
        
        # Check last few tokens for conjunctive adverbs
        for token in tokens[-5:]:
            if token.text.lower() in conjunctive_adverbs:
                return True
        
        return False

    def _has_conjunctive_adverb_after(self, tokens) -> bool:
        """Check if there's a conjunctive adverb after the semicolon using linguistic anchors."""
        conjunctive_adverbs = {
            'however', 'therefore', 'moreover', 'furthermore', 'nevertheless', 
            'consequently', 'accordingly', 'meanwhile', 'otherwise', 'hence',
            'thus', 'indeed', 'besides', 'likewise', 'nonetheless', 'instead',
            'subsequently', 'additionally', 'similarly', 'conversely', 'alternatively'
        }
        
        # Check first few tokens for conjunctive adverbs
        for token in tokens[:5]:
            if token.text.lower() in conjunctive_adverbs:
                return True
        
        return False

    def _analyze_clause_structure(self, tokens) -> Dict[str, Any]:
        """Analyze the grammatical structure of a clause using linguistic anchors."""
        if not tokens:
            return {'type': 'empty', 'complexity': 0}
        
        # Count grammatical elements
        subjects = sum(1 for token in tokens if 'subj' in token.dep_)
        verbs = sum(1 for token in tokens if token.pos_ == 'VERB')
        objects = sum(1 for token in tokens if 'obj' in token.dep_)
        
        # Determine clause type
        if subjects > 0 and verbs > 0:
            clause_type = 'independent'
        elif verbs > 0:
            clause_type = 'dependent'
        else:
            clause_type = 'fragment'
        
        return {
            'type': clause_type,
            'subjects': subjects,
            'verbs': verbs,
            'objects': objects,
            'complexity': len(tokens)
        }

    def _is_independent_clause(self, tokens) -> bool:
        """Check if token sequence forms an independent clause using linguistic anchors."""
        if not tokens:
            return False
        
        # Independent clauses need both subject and predicate
        has_subject = any('subj' in token.dep_ for token in tokens)
        has_verb = any(token.pos_ == 'VERB' for token in tokens)
        
        # Check for ROOT dependency (main clause indicator)
        has_root = any(token.dep_ == 'ROOT' for token in tokens)
        
        return has_subject and has_verb and has_root

    def _has_subject(self, tokens) -> bool:
        """Check if clause has a subject using linguistic anchors."""
        return any('subj' in token.dep_ for token in tokens)

    def _has_predicate(self, tokens) -> bool:
        """Check if clause has a predicate using linguistic anchors."""
        return any(token.pos_ == 'VERB' for token in tokens)

    def _classify_clause_structure(self, tokens) -> str:
        """Classify the structure type of a clause using linguistic anchors."""
        if not tokens:
            return 'empty'
        
        # Check for list structure
        if self._is_list_structure(tokens):
            return 'list'
        
        # Check for coordinate structure
        if self._is_coordinate_structure(tokens):
            return 'coordinate'
        
        # Check for subordinate structure
        if self._is_subordinate_structure(tokens):
            return 'subordinate'
        
        # Check for simple structure
        if self._is_simple_structure(tokens):
            return 'simple'
        
        return 'complex'

    def _is_list_structure(self, tokens) -> bool:
        """Check if tokens form a list structure using linguistic anchors."""
        # Look for comma-separated items
        comma_count = sum(1 for token in tokens if token.text == ',')
        
        # Look for coordinating conjunctions (and, or)
        coordinating_conjunctions = {'and', 'or'}
        has_coordination = any(token.text.lower() in coordinating_conjunctions for token in tokens)
        
        return comma_count >= 2 or (comma_count >= 1 and has_coordination)

    def _is_coordinate_structure(self, tokens) -> bool:
        """Check if tokens form a coordinate structure using linguistic anchors."""
        coordinating_conjunctions = {'and', 'but', 'or', 'nor', 'for', 'yet', 'so'}
        return any(token.text.lower() in coordinating_conjunctions for token in tokens)

    def _is_subordinate_structure(self, tokens) -> bool:
        """Check if tokens form a subordinate structure using linguistic anchors."""
        subordinating_conjunctions = {
            'although', 'because', 'since', 'while', 'when', 'where', 'if',
            'unless', 'until', 'after', 'before', 'though', 'whereas', 'as'
        }
        return any(token.text.lower() in subordinating_conjunctions for token in tokens)

    def _is_simple_structure(self, tokens) -> bool:
        """Check if tokens form a simple structure using linguistic anchors."""
        # Simple structure: one subject, one verb, minimal complexity
        subjects = sum(1 for token in tokens if 'subj' in token.dep_)
        verbs = sum(1 for token in tokens if token.pos_ == 'VERB')
        
        return subjects == 1 and verbs == 1

    def _analyze_semicolon_context(self, doc, semicolon_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Analyze the context and appropriateness of semicolon usage."""
        errors = []
        
        # Classify the semicolon usage type
        usage_type = self._classify_semicolon_usage(semicolon_info)
        
        # Check appropriateness based on usage type
        if usage_type == 'independent_clauses':
            errors.extend(self._check_independent_clause_semicolon(semicolon_info, sentence, sentence_index))
        elif usage_type == 'conjunctive_adverb':
            errors.extend(self._check_conjunctive_adverb_semicolon(semicolon_info, sentence, sentence_index))
        elif usage_type == 'complex_list':
            errors.extend(self._check_complex_list_semicolon(semicolon_info, sentence, sentence_index))
        elif usage_type == 'inappropriate':
            errors.extend(self._check_inappropriate_semicolon(semicolon_info, sentence, sentence_index))
        
        return errors

    def _classify_semicolon_usage(self, semicolon_info: Dict[str, Any]) -> str:
        """Classify the type of semicolon usage using linguistic anchors."""
        before_context = semicolon_info['before_context']
        after_context = semicolon_info['after_context']
        clause_before = semicolon_info['clause_before']
        clause_after = semicolon_info['clause_after']
        
        # Check for conjunctive adverb usage
        if (before_context['has_conjunctive_adverb'] or 
            after_context['has_conjunctive_adverb']):
            return 'conjunctive_adverb'
        
        # Check for complex list usage
        if (clause_before['structure_type'] == 'list' or 
            clause_after['structure_type'] == 'list'):
            return 'complex_list'
        
        # Check for independent clause connection
        if (clause_before['is_independent'] and 
            clause_after['is_independent']):
            return 'independent_clauses'
        
        # Check for inappropriate usage
        if (not clause_before['is_independent'] or 
            not clause_after['is_independent']):
            return 'inappropriate'
        
        return 'unclear'

    def _check_independent_clause_semicolon(self, semicolon_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check semicolon usage between independent clauses."""
        errors = []
        
        clause_before = semicolon_info['clause_before']
        clause_after = semicolon_info['clause_after']
        
        # Check if both clauses are truly independent
        if not (clause_before['is_independent'] and clause_after['is_independent']):
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Semicolon used between clauses that are not both independent.",
                suggestions=["Use a period to separate independent clauses.",
                           "Use a comma with a coordinating conjunction.",
                           "Restructure as two separate sentences."],
                severity='medium'
            ))
        
        # Check for closely related content
        if not self._are_clauses_closely_related(clause_before, clause_after):
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Semicolon connects clauses that may not be closely related.",
                suggestions=["Consider using a period for separate thoughts.",
                           "Add a transition word to show the relationship.",
                           "Use a comma with a coordinating conjunction."],
                severity='low'
            ))
        
        return errors

    def _check_conjunctive_adverb_semicolon(self, semicolon_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check semicolon usage with conjunctive adverbs."""
        errors = []
        
        after_context = semicolon_info['after_context']
        
        # Check if conjunctive adverb is properly placed
        if after_context['has_conjunctive_adverb']:
            first_tokens = after_context['tokens'][:3]
            conjunctive_adverb_position = None
            
            for i, token in enumerate(first_tokens):
                if self._is_conjunctive_adverb(token.text.lower()):
                    conjunctive_adverb_position = i
                    break
            
            if conjunctive_adverb_position is None:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Semicolon used but conjunctive adverb not found at beginning of clause.",
                    suggestions=["Place conjunctive adverb immediately after semicolon.",
                               "Consider restructuring the sentence."],
                    severity='medium'
                ))
            elif conjunctive_adverb_position > 0:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Conjunctive adverb should immediately follow semicolon.",
                    suggestions=["Move conjunctive adverb to the beginning of the clause.",
                               "Use proper punctuation around the conjunctive adverb."],
                    severity='low'
                ))
        
        return errors

    def _check_complex_list_semicolon(self, semicolon_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check semicolon usage in complex lists."""
        errors = []
        
        # Check if semicolon is appropriately used in complex list
        clause_before = semicolon_info['clause_before']
        clause_after = semicolon_info['clause_after']
        
        # Complex lists should have internal punctuation
        before_has_internal_punct = any(token.text in [',', ':'] for token in clause_before['tokens'])
        after_has_internal_punct = any(token.text in [',', ':'] for token in clause_after['tokens'])
        
        if not (before_has_internal_punct or after_has_internal_punct):
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Semicolon used in list without internal punctuation.",
                suggestions=["Use commas for simple lists.",
                           "Reserve semicolons for complex lists with internal punctuation.",
                           "Consider restructuring as separate sentences."],
                severity='low'
            ))
        
        return errors

    def _check_inappropriate_semicolon(self, semicolon_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check for inappropriate semicolon usage."""
        errors = []
        
        clause_before = semicolon_info['clause_before']
        clause_after = semicolon_info['clause_after']
        
        # Check for dependent clause usage
        if clause_before['structure_type'] == 'subordinate':
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Semicolon incorrectly used with dependent clause.",
                suggestions=["Use a comma to separate dependent clauses.",
                           "Restructure as independent clauses.",
                           "Consider using a period for separate sentences."],
                severity='high'
            ))
        
        # Check for fragment usage
        if clause_before['structure_type'] == 'fragment' or clause_after['structure_type'] == 'fragment':
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Semicolon used with sentence fragment.",
                suggestions=["Complete the fragment into a full clause.",
                           "Use appropriate punctuation for the sentence structure.",
                           "Consider combining fragments into complete sentences."],
                severity='high'
            ))
        
        return errors

    def _are_clauses_closely_related(self, clause_before: Dict[str, Any], clause_after: Dict[str, Any]) -> bool:
        """Check if clauses are closely related using linguistic anchors."""
        # Simple semantic similarity check
        before_words = {token.text.lower() for token in clause_before['tokens']}
        after_words = {token.text.lower() for token in clause_after['tokens']}
        
        # Check for shared vocabulary
        shared_words = before_words & after_words
        
        # Remove common words for better analysis
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'of', 'is', 'are', 'was', 'were'}
        meaningful_shared = shared_words - common_words
        
        return len(meaningful_shared) > 0

    def _is_conjunctive_adverb(self, word: str) -> bool:
        """Check if word is a conjunctive adverb using linguistic anchors."""
        conjunctive_adverbs = {
            'however', 'therefore', 'moreover', 'furthermore', 'nevertheless', 
            'consequently', 'accordingly', 'meanwhile', 'otherwise', 'hence',
            'thus', 'indeed', 'besides', 'likewise', 'nonetheless', 'instead',
            'subsequently', 'additionally', 'similarly', 'conversely', 'alternatively'
        }
        return word.lower() in conjunctive_adverbs

    def _check_semicolon_spacing(self, doc, semicolon_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check spacing around semicolons using linguistic anchors."""
        errors = []
        
        semicolon_idx = semicolon_info['index']
        
        # Check spacing before semicolon
        if semicolon_idx > 0:
            prev_token = doc[semicolon_idx - 1]
            if prev_token.whitespace_:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Unnecessary space before semicolon.",
                    suggestions=["Remove space before semicolon.",
                               "Semicolons should directly follow the preceding word."],
                    severity='low'
                ))
        
        # Check spacing after semicolon
        if semicolon_idx < len(doc) - 1:
            next_token = doc[semicolon_idx + 1]
            current_token = doc[semicolon_idx]
            
            if not current_token.whitespace_:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Missing space after semicolon.",
                    suggestions=["Add space after semicolon.",
                               "Use proper spacing for readability."],
                    severity='low'
                ))
        
        return errors

    def _check_semicolon_appropriateness(self, doc, semicolon_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check overall appropriateness of semicolon usage."""
        errors = []
        
        # Check if semicolon could be replaced with simpler punctuation
        usage_type = self._classify_semicolon_usage(semicolon_info)
        
        if usage_type == 'independent_clauses':
            # Suggest period for very different topics
            clause_before = semicolon_info['clause_before']
            clause_after = semicolon_info['clause_after']
            
            if not self._are_clauses_closely_related(clause_before, clause_after):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Consider using a period instead of semicolon for unrelated clauses.",
                    suggestions=["Use a period to separate unrelated thoughts.",
                               "Add transitional words to show relationship.",
                               "Consider if clauses belong in the same sentence."],
                    severity='low'
                ))
        
        return errors

    def _check_conjunctive_adverb_usage(self, doc, semicolon_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check conjunctive adverb usage with semicolons."""
        errors = []
        
        after_context = semicolon_info['after_context']
        
        # Check for missing comma after conjunctive adverb
        if after_context['has_conjunctive_adverb']:
            tokens_after = after_context['tokens']
            
            # Find the conjunctive adverb
            adverb_idx = None
            for i, token in enumerate(tokens_after[:5]):
                if self._is_conjunctive_adverb(token.text.lower()):
                    adverb_idx = i
                    break
            
            if adverb_idx is not None and adverb_idx < len(tokens_after) - 1:
                next_token = tokens_after[adverb_idx + 1]
                if next_token.text != ',':
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message="Missing comma after conjunctive adverb.",
                        suggestions=["Add comma after conjunctive adverb.",
                                   "Use pattern: semicolon, adverb, comma."],
                        severity='medium'
                    ))
        
        return errors

    def _check_independent_clause_connection(self, doc, semicolon_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check independent clause connection patterns."""
        errors = []
        
        clause_before = semicolon_info['clause_before']
        clause_after = semicolon_info['clause_after']
        
        # Check for weak connection between clauses
        if (clause_before['is_independent'] and clause_after['is_independent'] and
            not self._are_clauses_closely_related(clause_before, clause_after)):
            
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Independent clauses may be too loosely connected for semicolon.",
                suggestions=["Consider using a period for separate thoughts.",
                           "Add transitional words to clarify relationship.",
                           "Use coordinating conjunction with comma."],
                severity='low'
            ))
        
        return errors

    def _check_complex_list_usage(self, doc, semicolon_info: Dict[str, Any], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check complex list usage patterns."""
        errors = []
        
        # Check if semicolon is needed in list context
        clause_before = semicolon_info['clause_before']
        clause_after = semicolon_info['clause_after']
        
        if (clause_before['structure_type'] == 'list' or 
            clause_after['structure_type'] == 'list'):
            
            # Check for consistent semicolon usage in series
            full_sentence = ' '.join([token.text for token in doc])
            semicolon_count = full_sentence.count(';')
            comma_count = full_sentence.count(',')
            
            if semicolon_count == 1 and comma_count > 2:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Inconsistent use of semicolons in complex list.",
                    suggestions=["Use semicolons consistently throughout the list.",
                               "Consider restructuring as separate sentences.",
                               "Use commas for simple lists."],
                    severity='medium'
                ))
        
        return errors

    def _check_missing_semicolons(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check for places where semicolons might be missing."""
        errors = []
        
        # Look for conjunctive adverbs that might need semicolons
        for i, token in enumerate(doc):
            if self._is_conjunctive_adverb(token.text.lower()):
                # Check if preceded by comma (should be semicolon)
                if i > 0 and doc[i - 1].text == ',':
                    # Check if this connects independent clauses
                    before_clause = self._get_clause_before(doc, i - 1)
                    after_clause = self._get_clause_after(doc, i)
                    
                    if (before_clause['is_independent'] and 
                        after_clause['is_independent']):
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=sentence_index,
                            message="Conjunctive adverb between independent clauses needs semicolon, not comma.",
                            suggestions=["Replace comma with semicolon before conjunctive adverb.",
                                       "Use semicolon; adverb, pattern for independent clauses."],
                            severity='medium'
                        ))
        
        return errors

    def _analyze_with_regex(self, text: str, sentences: List[str]) -> List[Dict[str, Any]]:
        """Fallback regex-based analysis when NLP is unavailable."""
        errors = []
        
        for i, sentence in enumerate(sentences):
            if ';' not in sentence:
                continue
            
            # Pattern 1: Semicolon with space before
            if re.search(r'\s;', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Unnecessary space before semicolon.",
                    suggestions=["Remove space before semicolon.",
                               "Semicolons should directly follow the preceding word."],
                    severity='low'
                ))
            
            # Pattern 2: Semicolon without space after
            if re.search(r';[A-Za-z]', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Missing space after semicolon.",
                    suggestions=["Add space after semicolon.",
                               "Use proper spacing for readability."],
                    severity='low'
                ))
            
            # Pattern 3: Multiple semicolons (potential list)
            semicolon_count = sentence.count(';')
            if semicolon_count > 1:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Multiple semicolons detected - verify complex list usage.",
                    suggestions=["Ensure semicolons are used consistently in complex lists.",
                               "Consider breaking into separate sentences.",
                               "Use commas for simple lists."],
                    severity='low'
                ))
            
            # Pattern 4: Semicolon with conjunctive adverb
            conjunctive_adverb_pattern = r';\s*(however|therefore|moreover|furthermore|nevertheless|consequently|accordingly|meanwhile|otherwise|hence|thus|indeed|besides|likewise|nonetheless|instead|subsequently|additionally|similarly|conversely|alternatively)\s*[^,]'
            if re.search(conjunctive_adverb_pattern, sentence, re.IGNORECASE):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Missing comma after conjunctive adverb.",
                    suggestions=["Add comma after conjunctive adverb.",
                               "Use pattern: semicolon, adverb, comma."],
                    severity='medium'
                ))
            
            # Pattern 5: Semicolon that might be better as period
            if re.search(r';[A-Z]', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Semicolon followed by capital letter - consider using period.",
                    suggestions=["Use period if clauses are not closely related.",
                               "Ensure semicolon connects related independent clauses."],
                    severity='low'
                ))
            
            # Pattern 6: Very short clauses with semicolon
            if len(sentence) < 50 and ';' in sentence:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Short sentence with semicolon - consider simpler punctuation.",
                    suggestions=["Use comma with coordinating conjunction.",
                               "Consider using period for separate thoughts.",
                               "Evaluate if semicolon is necessary."],
                    severity='low'
                ))
            
            # Pattern 7: Semicolon in dialogue (often incorrect)
            if re.search(r'"[^"]*;[^"]*"', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Semicolon in dialogue may be inappropriate.",
                    suggestions=["Use comma or period in dialogue.",
                               "Consider natural speech patterns.",
                               "Verify punctuation appropriateness."],
                    severity='low'
                ))
            
            # Pattern 8: Semicolon after coordinating conjunction
            if re.search(r'(and|but|or|nor|for|yet|so)\s*;', sentence, re.IGNORECASE):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Semicolon after coordinating conjunction is typically incorrect.",
                    suggestions=["Use comma before coordinating conjunction.",
                               "Remove semicolon after coordinating conjunction.",
                               "Restructure sentence for clarity."],
                    severity='medium'
                ))
        
        return errors
