"""
Base Punctuation Rule
A base class that all specific punctuation rules will inherit from.
Provides comprehensive utility methods for morphological spaCy analysis with linguistic anchors.
"""

from typing import List, Dict, Any, Set, Tuple, Optional, Union
import re

# A generic base rule to be inherited from a central location
# in a real application. The # type: ignore comments prevent the
# static type checker from getting confused by the fallback class.
try:
    from rules.base_rule import BaseRule  # type: ignore
except ImportError:
    try:
        from ..base_rule import BaseRule  # type: ignore
    except ImportError:
        class BaseRule:  # type: ignore
            def _get_rule_type(self) -> str:
                return 'base'
            def _create_error(self, **kwargs) -> Dict[str, Any]:
                return kwargs


class BasePunctuationRule(BaseRule):
    """
    Abstract base class for all punctuation rules with comprehensive linguistic analysis utilities.
    Provides morphological spaCy analysis with linguistic anchors for consistent rule implementation.
    """

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """
        Analyzes the text for a specific punctuation violation.
        This method must be implemented by all subclasses.
        """
        raise NotImplementedError("Subclasses must implement the analyze method.")

    # =================== LINGUISTIC ANCHOR UTILITIES ===================

    def _get_writing_context(self, tokens) -> str:
        """Determine the writing context using standardized linguistic anchors."""
        if not tokens:
            return 'general'
        
        # Technical indicators
        technical_indicators = {
            'system', 'file', 'directory', 'folder', 'path', 'url', 'link',
            'server', 'database', 'code', 'programming', 'software', 'hardware',
            'algorithm', 'function', 'method', 'class', 'variable', 'parameter',
            'framework', 'library', 'api', 'protocol', 'interface', 'module'
        }
        
        # Academic indicators
        academic_indicators = {
            'research', 'study', 'analysis', 'theory', 'hypothesis', 'method',
            'result', 'conclusion', 'data', 'statistic', 'experiment', 'evidence',
            'citation', 'reference', 'bibliography', 'journal', 'publication',
            'abstract', 'methodology', 'literature', 'scholarly', 'peer-reviewed'
        }
        
        # Business indicators
        business_indicators = {
            'company', 'business', 'organization', 'department', 'team',
            'meeting', 'project', 'plan', 'strategy', 'goal', 'objective',
            'revenue', 'profit', 'customer', 'client', 'market', 'sales',
            'management', 'leadership', 'budget', 'forecast', 'proposal'
        }
        
        # Legal indicators
        legal_indicators = {
            'contract', 'agreement', 'terms', 'conditions', 'clause', 'provision',
            'statute', 'regulation', 'compliance', 'liability', 'obligation',
            'rights', 'jurisdiction', 'court', 'legal', 'law', 'legislation'
        }
        
        # Medical indicators
        medical_indicators = {
            'patient', 'diagnosis', 'treatment', 'therapy', 'medication', 'dose',
            'symptoms', 'condition', 'disease', 'clinical', 'medical', 'health',
            'procedure', 'surgery', 'examination', 'consultation', 'prognosis'
        }
        
        text_lower = ' '.join([token.text.lower() for token in tokens])
        
        # Check for context indicators with priority order
        if any(indicator in text_lower for indicator in technical_indicators):
            return 'technical'
        elif any(indicator in text_lower for indicator in academic_indicators):
            return 'academic'
        elif any(indicator in text_lower for indicator in legal_indicators):
            return 'legal'
        elif any(indicator in text_lower for indicator in medical_indicators):
            return 'medical'
        elif any(indicator in text_lower for indicator in business_indicators):
            return 'business'
        else:
            return 'general'

    def _get_formality_level(self, tokens) -> str:
        """Determine the formality level using linguistic anchors."""
        if not tokens:
            return 'neutral'
        
        # Formal indicators
        formal_indicators = {
            'shall', 'ought', 'furthermore', 'moreover', 'nevertheless', 'consequently',
            'therefore', 'accordingly', 'subsequently', 'alternatively', 'specifically',
            'particularly', 'essentially', 'ultimately', 'respectively', 'wherein',
            'hereby', 'whereas', 'pursuant', 'aforementioned', 'henceforth'
        }
        
        # Informal indicators
        informal_indicators = {
            'gonna', 'wanna', 'kinda', 'sorta', 'yeah', 'nope', 'okay', 'cool',
            'awesome', 'super', 'really', 'pretty', 'quite', 'very', 'so',
            'totally', 'basically', 'actually', 'literally', 'seriously'
        }
        
        # Casual contractions
        casual_patterns = {
            "don't", "won't", "can't", "shouldn't", "wouldn't", "couldn't",
            "isn't", "aren't", "wasn't", "weren't", "haven't", "hasn't",
            "hadn't", "I'm", "you're", "he's", "she's", "it's", "we're", "they're"
        }
        
        text_lower = ' '.join([token.text.lower() for token in tokens])
        
        formal_count = sum(1 for indicator in formal_indicators if indicator in text_lower)
        informal_count = sum(1 for indicator in informal_indicators if indicator in text_lower)
        casual_count = sum(1 for pattern in casual_patterns if pattern in text_lower)
        
        if formal_count > informal_count + casual_count:
            return 'formal'
        elif informal_count + casual_count > formal_count:
            return 'informal'
        else:
            return 'neutral'

    def _detect_sentence_type(self, tokens) -> str:
        """Detect sentence type using linguistic anchors."""
        if not tokens:
            return 'unknown'
        
        # Question indicators
        question_words = {'what', 'where', 'when', 'why', 'how', 'who', 'which', 'whose'}
        has_question_word = any(token.text.lower() in question_words for token in tokens)
        ends_with_question = tokens and tokens[-1].text == '?'
        
        if has_question_word or ends_with_question:
            return 'question'
        
        # Imperative indicators (commands)
        if tokens and tokens[0].pos_ == 'VERB' and tokens[0].tag_ == 'VB':
            # Check if there's no explicit subject
            has_subject = any('subj' in token.dep_ for token in tokens)
            if not has_subject:
                return 'imperative'
        
        # Exclamatory indicators
        if tokens and tokens[-1].text == '!':
            return 'exclamatory'
        
        # Declarative (default)
        return 'declarative'

    def _get_clause_complexity(self, tokens) -> Dict[str, Any]:
        """Analyze clause complexity using morphological analysis."""
        if not tokens:
            return {'level': 'empty', 'score': 0, 'features': []}
        
        # Count grammatical elements
        subjects = sum(1 for token in tokens if 'subj' in token.dep_)
        verbs = sum(1 for token in tokens if token.pos_ == 'VERB')
        objects = sum(1 for token in tokens if 'obj' in token.dep_)
        clauses = sum(1 for token in tokens if token.dep_ in ['ccomp', 'xcomp', 'advcl', 'acl', 'relcl'])
        conjunctions = sum(1 for token in tokens if token.pos_ == 'CCONJ' or token.pos_ == 'SCONJ')
        modifiers = sum(1 for token in tokens if token.dep_ in ['amod', 'advmod', 'nmod'])
        
        # Calculate complexity score
        complexity_score = (
            subjects * 1 + 
            verbs * 1 + 
            objects * 1 + 
            clauses * 2 + 
            conjunctions * 1.5 + 
            modifiers * 0.5
        )
        
        features = []
        if subjects > 1:
            features.append('multiple_subjects')
        if verbs > 2:
            features.append('multiple_verbs')
        if clauses > 0:
            features.append('subordinate_clauses')
        if conjunctions > 1:
            features.append('compound_structure')
        if len(tokens) > 20:
            features.append('long_sentence')
        
        # Determine complexity level
        if complexity_score < 3:
            level = 'simple'
        elif complexity_score < 8:
            level = 'moderate'
        elif complexity_score < 15:
            level = 'complex'
        else:
            level = 'very_complex'
        
        return {
            'level': level,
            'score': complexity_score,
            'features': features,
            'subjects': subjects,
            'verbs': verbs,
            'objects': objects,
            'clauses': clauses,
            'conjunctions': conjunctions,
            'modifiers': modifiers
        }

    def _detect_text_patterns(self, text: str) -> Dict[str, bool]:
        """Detect common text patterns using linguistic anchors."""
        text_lower = text.lower()
        
        return {
            # URL patterns
            'has_url': bool(re.search(r'https?://|www\.|\.com|\.org|\.edu|\.gov', text_lower)),
            
            # Email patterns
            'has_email': bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)),
            
            # Date patterns
            'has_date': bool(re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\b\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', text_lower)),
            
            # Time patterns
            'has_time': bool(re.search(r'\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:am|pm))?', text_lower)),
            
            # Number patterns
            'has_numbers': bool(re.search(r'\d+', text)),
            
            # Currency patterns
            'has_currency': bool(re.search(r'\$\d+|€\d+|£\d+|\d+\s*(?:dollars?|euros?|pounds?)', text_lower)),
            
            # Percentage patterns
            'has_percentage': bool(re.search(r'\d+\s*%|\d+\s*percent', text_lower)),
            
            # File path patterns
            'has_file_path': bool(re.search(r'[A-Za-z]:\\|/[a-z]+/|\.(?:txt|doc|pdf|exe|jpg|png)', text_lower)),
            
            # Citation patterns
            'has_citation': bool(re.search(r'\([^)]*\d{4}[^)]*\)|\[\d+\]', text)),
            
            # Technical patterns
            'has_code': bool(re.search(r'[{}();]|def\s+\w+|class\s+\w+|function\s+\w+', text_lower)),
            
            # List patterns
            'has_list': bool(re.search(r'^\s*[-*•]\s+|^\s*\d+\.\s+', text, re.MULTILINE)),
            
            # Quotation patterns
            'has_quotes': bool(re.search(r'["\'""'']', text)),
            
            # Abbreviation patterns
            'has_abbreviations': bool(re.search(r'\b[A-Z]{2,}\b|[A-Z]\.[A-Z]\.', text)),
            
            # Mathematical patterns
            'has_math': bool(re.search(r'[+\-*/=<>≤≥≠±√∑∫]|\d+\^\d+', text)),
            
            # Chemical patterns
            'has_chemistry': bool(re.search(r'\b[A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)*\b|pH|mol|°C|°F', text))
        }

    def _get_punctuation_context(self, doc, punct_idx: int, window: int = 5) -> Dict[str, Any]:
        """Get comprehensive context around a punctuation mark."""
        # Tokens before punctuation
        start_idx = max(0, punct_idx - window)
        tokens_before = doc[start_idx:punct_idx]
        
        # Tokens after punctuation
        end_idx = min(len(doc), punct_idx + window + 1)
        tokens_after = doc[punct_idx + 1:end_idx]
        
        # Full context
        full_context = doc[start_idx:end_idx]
        
        return {
            'before': {
                'tokens': tokens_before,
                'text': ''.join([token.text_with_ws for token in tokens_before]),
                'pos_tags': [token.pos_ for token in tokens_before],
                'dependencies': [token.dep_ for token in tokens_before],
                'last_token': tokens_before[-1] if tokens_before else None
            },
            'after': {
                'tokens': tokens_after,
                'text': ''.join([token.text_with_ws for token in tokens_after]),
                'pos_tags': [token.pos_ for token in tokens_after],
                'dependencies': [token.dep_ for token in tokens_after],
                'first_token': tokens_after[0] if tokens_after else None
            },
            'full_context': {
                'tokens': full_context,
                'text': ''.join([token.text_with_ws for token in full_context]),
                'complexity': self._get_clause_complexity(full_context),
                'patterns': self._detect_text_patterns(''.join([token.text for token in full_context])),
                'writing_context': self._get_writing_context(full_context),
                'formality': self._get_formality_level(full_context)
            }
        }

    def _find_linguistic_patterns(self, tokens, pattern_type: str) -> List[Dict[str, Any]]:
        """Find specific linguistic patterns in token sequences."""
        patterns = []
        
        if pattern_type == 'coordination':
            # Find coordinating conjunctions and their scope
            coord_conjunctions = {'and', 'but', 'or', 'nor', 'for', 'yet', 'so'}
            for i, token in enumerate(tokens):
                if token.text.lower() in coord_conjunctions:
                    patterns.append({
                        'type': 'coordination',
                        'position': i,
                        'conjunction': token.text,
                        'connects_clauses': self._connects_clauses(tokens, i)
                    })
        
        elif pattern_type == 'subordination':
            # Find subordinating conjunctions
            subord_conjunctions = {
                'although', 'because', 'since', 'while', 'when', 'where', 'if',
                'unless', 'until', 'after', 'before', 'though', 'whereas', 'as'
            }
            for i, token in enumerate(tokens):
                if token.text.lower() in subord_conjunctions:
                    patterns.append({
                        'type': 'subordination',
                        'position': i,
                        'conjunction': token.text,
                        'clause_type': self._get_subordinate_clause_type(token)
                    })
        
        elif pattern_type == 'apposition':
            # Find appositives using dependency parsing
            for i, token in enumerate(tokens):
                if token.dep_ == 'appos':
                    patterns.append({
                        'type': 'apposition',
                        'position': i,
                        'head': token.head.text,
                        'appositive': token.text
                    })
        
        elif pattern_type == 'parenthetical':
            # Find parenthetical expressions
            for i, token in enumerate(tokens):
                if token.dep_ in ['parataxis', 'discourse', 'intj']:
                    patterns.append({
                        'type': 'parenthetical',
                        'position': i,
                        'expression': token.text,
                        'dependency': token.dep_
                    })
        
        return patterns

    def _connects_clauses(self, tokens, conj_idx: int) -> bool:
        """Check if a conjunction connects independent clauses."""
        # Look for subjects and verbs before and after conjunction
        before_tokens = tokens[:conj_idx]
        after_tokens = tokens[conj_idx + 1:]
        
        before_has_subj = any('subj' in token.dep_ for token in before_tokens)
        before_has_verb = any(token.pos_ == 'VERB' for token in before_tokens)
        
        after_has_subj = any('subj' in token.dep_ for token in after_tokens)
        after_has_verb = any(token.pos_ == 'VERB' for token in after_tokens)
        
        return (before_has_subj and before_has_verb and 
                after_has_subj and after_has_verb)

    def _get_subordinate_clause_type(self, conjunction_token) -> str:
        """Classify the type of subordinate clause."""
        conj_text = conjunction_token.text.lower()
        
        temporal_conjunctions = {'when', 'while', 'after', 'before', 'until', 'since', 'as'}
        causal_conjunctions = {'because', 'since', 'as'}
        conditional_conjunctions = {'if', 'unless', 'provided', 'assuming'}
        concessive_conjunctions = {'although', 'though', 'even though', 'whereas', 'while'}
        
        if conj_text in temporal_conjunctions:
            return 'temporal'
        elif conj_text in causal_conjunctions:
            return 'causal'
        elif conj_text in conditional_conjunctions:
            return 'conditional'
        elif conj_text in concessive_conjunctions:
            return 'concessive'
        else:
            return 'other'

    def _analyze_sentence_boundaries(self, doc) -> List[Dict[str, Any]]:
        """Analyze sentence boundary patterns and structures."""
        boundaries = []
        
        for i, token in enumerate(doc):
            if token.text in ['.', '!', '?']:
                boundary_info = {
                    'position': i,
                    'punctuation': token.text,
                    'sentence_type': self._infer_sentence_type_from_punct(token.text),
                    'follows_abbreviation': self._follows_abbreviation(doc, i),
                    'in_quotation': self._in_quotation_context(doc, i),
                    'appropriate': True  # Default, can be modified by specific rules
                }
                boundaries.append(boundary_info)
        
        return boundaries

    def _infer_sentence_type_from_punct(self, punct: str) -> str:
        """Infer sentence type from ending punctuation."""
        if punct == '?':
            return 'interrogative'
        elif punct == '!':
            return 'exclamatory'
        elif punct == '.':
            return 'declarative'
        else:
            return 'unknown'

    def _follows_abbreviation(self, doc, punct_idx: int) -> bool:
        """Check if punctuation follows a known abbreviation."""
        if punct_idx == 0:
            return False
        
        prev_token = doc[punct_idx - 1]
        
        # Common abbreviations
        abbreviations = {
            'dr', 'mr', 'mrs', 'ms', 'prof', 'inc', 'corp', 'ltd', 'co',
            'etc', 'vs', 'ie', 'eg', 'cf', 'al', 'jr', 'sr', 'st', 'ave'
        }
        
        return prev_token.text.lower() in abbreviations

    def _in_quotation_context(self, doc, punct_idx: int) -> bool:
        """Check if punctuation is within quotation marks."""
        # Simple check for nearby quotation marks
        start_search = max(0, punct_idx - 20)
        end_search = min(len(doc), punct_idx + 5)
        
        context_text = ''.join([token.text for token in doc[start_search:end_search]])
        
        # Count quotation marks before and after
        before_quotes = context_text[:punct_idx - start_search].count('"') + context_text[:punct_idx - start_search].count("'")
        
        return before_quotes % 2 == 1  # Odd number means we're inside quotes

    # =================== STANDARDIZED FALLBACK PATTERNS ===================

    def _get_common_regex_patterns(self) -> Dict[str, str]:
        """Get standardized regex patterns for fallback analysis."""
        return {
            'double_punctuation': r'([.!?]){2,}',
            'space_before_punct': r'\s+([.!?,:;])',
            'missing_space_after': r'([.!?])[A-Za-z]',
            'multiple_spaces': r'  +',
            'trailing_spaces': r'[ \t]+$',
            'leading_spaces': r'^[ \t]+',
            'empty_parentheses': r'\(\s*\)',
            'empty_brackets': r'\[\s*\]',
            'empty_quotes': r'["\']\s*["\']',
            'mixed_quotes': r'["\'"][^"\']*["\']',
            'url_pattern': r'https?://[^\s]+',
            'email_pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'date_pattern': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            'time_pattern': r'\b\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:am|pm))?\b',
            'currency_pattern': r'\$\d+(?:\.\d{2})?|\d+\s*(?:dollars?|euros?|pounds?)',
            'percentage_pattern': r'\d+\s*%|\d+\s*percent',
            'abbreviation_pattern': r'\b[A-Z]{2,}\b|[A-Z]\.[A-Z]\.',
            'file_extension': r'\.\w{2,4}$',
            'version_number': r'v?\d+\.\d+(?:\.\d+)?',
            'phone_number': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        }

    def _apply_regex_fallback(self, text: str, sentences: List[str], error_patterns: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply standardized regex-based fallback analysis."""
        errors = []
        regex_patterns = self._get_common_regex_patterns()
        
        for i, sentence in enumerate(sentences):
            for pattern_name, pattern_config in error_patterns.items():
                if pattern_name in regex_patterns:
                    pattern = regex_patterns[pattern_name]
                    if re.search(pattern, sentence, re.IGNORECASE):
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=pattern_config.get('message', f'{pattern_name} detected'),
                            suggestions=pattern_config.get('suggestions', ['Review and correct the pattern']),
                            severity=pattern_config.get('severity', 'low')
                        ))
        
        return errors

    # =================== UTILITY METHODS ===================

    def _extract_word_features(self, token) -> Dict[str, Any]:
        """Extract comprehensive features from a token using morphological analysis."""
        return {
            'text': token.text,
            'lemma': token.lemma_,
            'pos': token.pos_,
            'tag': token.tag_,
            'dep': token.dep_,
            'shape': token.shape_,
            'is_alpha': token.is_alpha,
            'is_ascii': token.is_ascii,
            'is_digit': token.is_digit,
            'is_punct': token.is_punct,
            'is_space': token.is_space,
            'is_stop': token.is_stop,
            'is_title': token.is_title,
            'is_upper': token.is_upper,
            'is_lower': token.is_lower,
            'like_url': token.like_url,
            'like_email': token.like_email,
            'like_num': token.like_num,
            'head_text': token.head.text if token.head != token else None,
            'children': [child.text for child in token.children],
            'morph_features': str(token.morph) if hasattr(token, 'morph') else None
        }

    def _calculate_text_metrics(self, tokens) -> Dict[str, float]:
        """Calculate various text complexity metrics."""
        if not tokens:
            return {'length': 0, 'complexity': 0, 'readability': 0}
        
        # Basic metrics
        word_count = len([t for t in tokens if t.is_alpha])
        sentence_length = len(tokens)
        avg_word_length = sum(len(t.text) for t in tokens if t.is_alpha) / max(word_count, 1)
        
        # Complexity indicators
        complex_words = sum(1 for t in tokens if len(t.text) > 6 and t.is_alpha)
        syllable_estimate = sum(max(1, len(re.findall(r'[aeiouAEIOU]', t.text))) for t in tokens if t.is_alpha)
        
        # Syntactic complexity
        dependent_clauses = sum(1 for t in tokens if t.dep_ in ['ccomp', 'xcomp', 'advcl'])
        
        return {
            'length': sentence_length,
            'word_count': word_count,
            'avg_word_length': avg_word_length,
            'complex_word_ratio': complex_words / max(word_count, 1),
            'syllable_density': syllable_estimate / max(word_count, 1),
            'syntactic_complexity': dependent_clauses / max(sentence_length, 1),
            'readability_score': self._estimate_readability(word_count, sentence_length, complex_words)
        }

    def _estimate_readability(self, words: int, sentences: int, complex_words: int) -> float:
        """Estimate readability using simplified Flesch-Kincaid approach."""
        if words == 0 or sentences == 0:
            return 0
        
        avg_sentence_length = words / sentences
        complex_word_ratio = complex_words / words
        
        # Simplified readability score (higher = easier to read)
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * complex_word_ratio)
        
        return max(0, min(100, score))

    def _validate_punctuation_context(self, context: Dict[str, Any], punct_type: str) -> Dict[str, Any]:
        """Validate punctuation usage based on comprehensive context analysis."""
        validation_result = {
            'is_appropriate': True,
            'confidence': 1.0,
            'issues': [],
            'suggestions': []
        }
        
        # Context-specific validation logic can be implemented here
        # This provides a framework for subclasses to extend
        
        return validation_result
