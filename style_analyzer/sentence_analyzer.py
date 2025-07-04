"""
Sentence Analyzer Module
Handles sentence-level analysis including length, structure, and complexity checks.
Designed for zero false positives with conservative thresholds.
"""

import logging
import re
from typing import List, Optional, Dict, Any

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

from .base_types import (
    ErrorDict, AnalysisMethod, ErrorSeverity, CONSERVATIVE_THRESHOLDS,
    CONFIDENCE_SCORES, DEFAULT_RULES, create_error
)

logger = logging.getLogger(__name__)


class SentenceAnalyzer:
    """Handles sentence-level analysis with SpaCy and fallback mechanisms."""
    
    def __init__(self, rules: Optional[dict] = None):
        """Initialize sentence analyzer with rules."""
        self.rules = rules or DEFAULT_RULES.copy()
    
    def analyze_sentence_length_spacy(self, sentences: List[str], nlp) -> List[ErrorDict]:
        """Analyze sentence length using SpaCy for accurate word counting and complexity detection."""
        errors = []
        
        if not nlp or not sentences:
            return errors
            
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
                
            try:
                doc = nlp(sentence)
                
                # Count actual words (excluding punctuation and spaces)
                word_count = len([token for token in doc if not token.is_punct and not token.is_space])
                
                if word_count > self.rules['max_sentence_length']:
                    # Only flag if SpaCy shows complex sentence structure
                    complex_deps = [token for token in doc if token.dep_ in ['ccomp', 'xcomp', 'advcl', 'acl']]
                    
                    if len(complex_deps) > 1:  # Multiple complex dependencies
                        suggestions = self._generate_length_suggestions_spacy(doc, sentence)
                        
                        error = create_error(
                            error_type='sentence_length',
                            message=f'Sentence is complex and long ({word_count} words). Consider breaking it up.',
                            suggestions=suggestions,
                            sentence=sentence,
                            sentence_index=i,
                            severity=ErrorSeverity.MEDIUM if word_count < 35 else ErrorSeverity.HIGH,
                            confidence=CONFIDENCE_SCORES[AnalysisMethod.SPACY_LEGACY],
                            analysis_method=AnalysisMethod.SPACY_LEGACY,
                            word_count=word_count
                        )
                        errors.append(error)
                        
            except Exception as e:
                logger.error(f"SpaCy sentence length check failed for sentence {i}: {e}")
                continue
                
        return errors
    
    def analyze_sentence_length_conservative(self, sentences: List[str]) -> List[ErrorDict]:
        """Conservative sentence length analysis with higher thresholds."""
        errors = []
        
        if not sentences:
            return errors
            
        threshold = CONSERVATIVE_THRESHOLDS['sentence_length_threshold']
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
                
            word_count = len(sentence.split())
            
            if word_count > threshold:
                suggestions = self._generate_length_suggestions_fallback(sentence)
                
                error = create_error(
                    error_type='sentence_length',
                    message=f'Sentence is very long ({word_count} words). Consider reviewing for clarity.',
                    suggestions=suggestions,
                    sentence=sentence,
                    sentence_index=i,
                    severity=ErrorSeverity.LOW,  # Always low severity in conservative mode
                    confidence=CONFIDENCE_SCORES[AnalysisMethod.CONSERVATIVE_FALLBACK],
                    analysis_method=AnalysisMethod.CONSERVATIVE_FALLBACK,
                    word_count=word_count
                )
                errors.append(error)
                
        return errors
    
    def analyze_sentence_length_minimal_safe(self, sentences: List[str]) -> List[ErrorDict]:
        """Minimal safe sentence length analysis with very high thresholds."""
        errors = []
        
        if not sentences:
            return errors
            
        # Very conservative threshold - only flag extremely long sentences
        threshold = 40
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
                
            word_count = len(sentence.split())
            
            if word_count > threshold:
                error = create_error(
                    error_type='sentence_length',
                    message=f'Sentence is very long ({word_count} words). Consider reviewing for clarity.',
                    suggestions=['Consider breaking this very long sentence into shorter ones'],
                    sentence=sentence,
                    sentence_index=i,
                    severity=ErrorSeverity.LOW,
                    confidence=CONFIDENCE_SCORES[AnalysisMethod.MINIMAL_SAFE],
                    analysis_method=AnalysisMethod.MINIMAL_SAFE,
                    word_count=word_count
                )
                errors.append(error)
                
        return errors
    
    def _generate_length_suggestions_spacy(self, doc, sentence: str) -> List[str]:
        """Generate sentence length suggestions using SpaCy's syntactic analysis."""
        suggestions = []
        
        try:
            # Find coordinating conjunctions (and, but, or)
            coord_conjunctions = [token for token in doc if token.dep_ == 'cc']
            for conj in coord_conjunctions:
                suggestions.append(f"Split at '{conj.text}' to separate compound ideas")
            
            # Find subordinating conjunctions (because, although, while, etc.)
            subord_conjunctions = [token for token in doc if token.dep_ == 'mark']
            for conj in subord_conjunctions:
                suggestions.append(f"Separate the clause beginning with '{conj.text}'")
            
            # Find relative clauses
            relative_pronouns = [token for token in doc if token.dep_ in ['relcl', 'acl:relcl']]
            if relative_pronouns:
                suggestions.append("Consider breaking relative clauses into separate sentences")
            
            # Find adverbial clauses
            advcl_tokens = [token for token in doc if token.dep_ == 'advcl']
            for token in advcl_tokens:
                suggestions.append(f"Consider separating the adverbial clause starting near '{token.text}'")
            
            # Find prepositional phrases that could be sentences
            prep_phrases = [token for token in doc if token.dep_ == 'prep' and len(list(token.subtree)) > 3]
            if len(prep_phrases) > 2:
                suggestions.append("Consider converting some prepositional phrases to separate sentences")
                
        except Exception as e:
            logger.error(f"Error generating SpaCy length suggestions: {e}")
            suggestions = ["Consider breaking this sentence into shorter parts"]
            
        return suggestions if suggestions else ["Consider breaking this sentence into shorter parts"]
    
    def _generate_length_suggestions_fallback(self, sentence: str) -> List[str]:
        """Generate length suggestions without SpaCy using basic analysis."""
        suggestions = []
        
        try:
            # Count conjunctions
            and_count = sentence.lower().count(' and ')
            if and_count >= 2:
                suggestions.append("Split at 'and' conjunctions to separate ideas")
            
            # Look for transition words
            transitions = ['however', 'therefore', 'furthermore', 'moreover', 'consequently', 'nevertheless']
            found_transitions = [t for t in transitions if t in sentence.lower()]
            for trans in found_transitions:
                suggestions.append(f"Start new sentence at '{trans}'")
            
            # Count commas as complexity indicator
            comma_count = sentence.count(',')
            if comma_count >= 3:
                suggestions.append("Break up comma-separated clauses into separate sentences")
                
        except Exception as e:
            logger.error(f"Error generating fallback length suggestions: {e}")
            
        return suggestions if suggestions else ["Consider breaking this sentence into shorter parts"]
    
    def calculate_sentence_statistics(self, sentences: List[str]) -> Dict[str, Any]:
        """Calculate sentence-level statistics safely."""
        stats = {
            'sentence_count': 0,
            'avg_sentence_length': 0.0,
            'median_sentence_length': 0.0,
            'longest_sentence': 0,
            'shortest_sentence': 0,
            'sentence_length_variety': 0.0,
            'sentence_types': {'simple': 0, 'compound': 0, 'complex': 0}
        }
        
        if not sentences:
            return stats
            
        try:
            # Filter out empty sentences
            valid_sentences = [s for s in sentences if s.strip()]
            if not valid_sentences:
                return stats
                
            stats['sentence_count'] = len(valid_sentences)
            
            # Calculate sentence lengths
            sentence_lengths = [len(s.split()) for s in valid_sentences]
            
            stats['avg_sentence_length'] = sum(sentence_lengths) / len(sentence_lengths)
            stats['median_sentence_length'] = sorted(sentence_lengths)[len(sentence_lengths) // 2]
            stats['longest_sentence'] = max(sentence_lengths)
            stats['shortest_sentence'] = min(sentence_lengths)
            
            # Calculate sentence length variety (coefficient of variation)
            if stats['avg_sentence_length'] > 0:
                variance = sum((x - stats['avg_sentence_length']) ** 2 for x in sentence_lengths) / len(sentence_lengths)
                std_dev = variance ** 0.5
                stats['sentence_length_variety'] = std_dev / stats['avg_sentence_length']
            
            # Analyze sentence types (conservative)
            for sentence in valid_sentences:
                if ';' in sentence and (',' in sentence or ' and ' in sentence):
                    stats['sentence_types']['complex'] += 1
                elif ' and ' in sentence or ' or ' in sentence or ' but ' in sentence:
                    stats['sentence_types']['compound'] += 1
                else:
                    stats['sentence_types']['simple'] += 1
                    
        except Exception as e:
            logger.error(f"Error calculating sentence statistics: {e}")
            
        return stats
    
    def split_sentences_safe(self, text: str, nlp=None) -> List[str]:
        """Split text into sentences safely with fallback."""
        if not text.strip():
            return []
            
        try:
            if nlp:
                # Use SpaCy for accurate sentence splitting
                doc = nlp(text)
                sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
            else:
                # Fallback to regex-based splitting
                sentences = re.split(r'[.!?]+', text)
                sentences = [s.strip() for s in sentences if s.strip()]
                
            return sentences
            
        except Exception as e:
            logger.error(f"Error splitting sentences: {e}")
            # Ultimate fallback
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]
    
    def analyze_sentence_variety(self, sentences: List[str]) -> Dict[str, Any]:
        """Analyze sentence variety and patterns."""
        analysis = {
            'variety_score': 0.0,
            'repetitive_patterns': [],
            'variety_rating': 'unknown'
        }
        
        if not sentences or len(sentences) < 3:
            return analysis
            
        try:
            # Calculate length variety
            lengths = [len(s.split()) for s in sentences if s.strip()]
            if len(lengths) < 2:
                return analysis
                
            avg_length = sum(lengths) / len(lengths)
            variance = sum((x - avg_length) ** 2 for x in lengths) / len(lengths)
            std_dev = variance ** 0.5
            
            # Coefficient of variation as variety score
            if avg_length > 0:
                analysis['variety_score'] = std_dev / avg_length
            
            # Rate variety
            if analysis['variety_score'] > 0.7:
                analysis['variety_rating'] = 'high'
            elif analysis['variety_score'] > 0.4:
                analysis['variety_rating'] = 'moderate'
            else:
                analysis['variety_rating'] = 'low'
                
            # Check for repetitive patterns (conservative)
            start_patterns = {}
            for sentence in sentences:
                words = sentence.strip().split()
                if len(words) >= 2:
                    pattern = ' '.join(words[:2]).lower()
                    start_patterns[pattern] = start_patterns.get(pattern, 0) + 1
            
            # Only flag if pattern repeats 3+ times
            repetitive = [pattern for pattern, count in start_patterns.items() if count >= 3]
            analysis['repetitive_patterns'] = repetitive
            
        except Exception as e:
            logger.error(f"Error analyzing sentence variety: {e}")
            
        return analysis 