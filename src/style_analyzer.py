"""
Style Analyzer Module - Analyzes text content against style guide rules using NLP libraries.
Enhanced for technical writing with comprehensive readability and grade-level analysis.
Now uses a modular rules system for easy extensibility.
"""

import re
import logging
import math
from typing import List, Dict, Any
import spacy
import nltk
import textstat
from collections import defaultdict, Counter

# Import the modular rules system
try:
    from .rules import registry
    RULES_AVAILABLE = True
    print("✅ Modular rules system loaded successfully")
except ImportError:
    try:
        # Try alternative import path for standalone execution
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        rules_path = os.path.join(current_dir, 'rules')
        sys.path.insert(0, rules_path)
        
        # Import the registry module directly
        import importlib.util
        registry_path = os.path.join(rules_path, '__init__.py')
        spec = importlib.util.spec_from_file_location("rules", registry_path)
        rules_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rules_module)
        registry = rules_module.registry
        
        RULES_AVAILABLE = True
        print("✅ Modular rules system loaded successfully (standalone)")
    except Exception as e:
        RULES_AVAILABLE = False
        print(f"⚠️ Modular rules system not available: {e}")

# Use built-in syllable estimation - no external library needed
SYLLABLES_AVAILABLE = False

logger = logging.getLogger(__name__)

class StyleAnalyzer:
    """Analyzes text against comprehensive style guide rules for technical writing."""
    
    def __init__(self):
        """Initialize the style analyzer with NLP tools."""
        try:
            # Load SpaCy model (install with: python -m spacy download en_core_web_sm)
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("SpaCy model 'en_core_web_sm' not found. Please install it.")
            self.nlp = None
        
        # Download required NLTK data
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('cmudict', quiet=True)  # For syllable counting
        except:
            pass
        
        # Technical writing style guide rules
        self.rules = {
            'max_sentence_length': 25,
            'target_grade_level': (9, 11),  # 9th to 11th grade target
            'min_readability_score': 60.0,
            'max_fog_index': 12.0,  # Gunning Fog Index for technical writing
            'passive_voice_threshold': 0.15,  # Max 15% passive voice
            'word_repetition_threshold': 3,
            'max_syllables_per_word': 2.5,  # Average syllables per word
            'min_sentence_variety': 0.7,  # Sentence length variety
        }
        
        # Note: All readability metrics are handled by textstat library
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Perform comprehensive style analysis on text for technical writing."""
        if not text or not text.strip():
            return {
                'errors': [], 
                'suggestions': [], 
                'statistics': {}, 
                'technical_writing_metrics': {},
                'overall_score': 0
            }
        
        try:
            sentences = self._split_sentences(text)
            paragraphs = self._split_paragraphs(text)
            
            errors = []
            
            # Use modular rules system if available
            if RULES_AVAILABLE:
                modular_errors = registry.analyze_with_all_rules(text, sentences, self.nlp)
                errors.extend(modular_errors)
                print(f"✅ Analyzed with {len(registry.get_all_rules())} modular rules")
            else:
                # Fallback to legacy analysis methods
                print("⚠️ Using legacy analysis methods")
                
                # Comprehensive readability analysis
                readability_issues = self._check_comprehensive_readability(text)
                errors.extend(readability_issues)
                
                # Grade level analysis
                grade_level_issues = self._check_grade_level(text)
                errors.extend(grade_level_issues)
                
                # Sentence length and variety
                length_errors = self._check_sentence_length_and_variety(sentences)
                errors.extend(length_errors)
                
                # Legacy rule checks (keeping for backward compatibility)
                legacy_errors = self._run_legacy_checks(sentences)
                errors.extend(legacy_errors)
            
            # Always run readability and statistics (not rule-based)
            readability_issues = self._check_comprehensive_readability(text)
            grade_level_issues = self._check_grade_level(text)
            length_errors = self._check_sentence_length_and_variety(sentences)
            
            # Add these if not already added by modular rules
            if not RULES_AVAILABLE:
                errors.extend(readability_issues)
                errors.extend(grade_level_issues)
                errors.extend(length_errors)
            
            # Calculate comprehensive statistics
            statistics = self._calculate_comprehensive_statistics(text, sentences, paragraphs)
            
            # Calculate technical writing specific metrics
            technical_metrics = self._calculate_technical_writing_metrics(text, sentences, errors)
            
            # Generate suggestions
            suggestions = self._generate_suggestions(errors)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(errors, statistics, technical_metrics)
            
            return {
                'errors': errors,
                'suggestions': suggestions,
                'statistics': statistics,
                'technical_writing_metrics': technical_metrics,
                'overall_score': overall_score
            }
            
        except Exception as e:
            logger.error(f"Error in style analysis: {str(e)}")
            return {
                'errors': [{'type': 'system_error', 'message': f'Analysis failed: {str(e)}'}],
                'suggestions': [],
                'statistics': {},
                'technical_writing_metrics': {},
                'overall_score': 0
            }
    
    def _run_legacy_checks(self, sentences: List[str]) -> List[Dict[str, Any]]:
        """Run legacy analysis methods when modular rules not available."""
        errors = []
        
        # Basic passive voice check
        for i, sentence in enumerate(sentences):
            passive_patterns = [
                r'\b(is|are|was|were|being|been)\s+\w*ed\b',
                r'\b(is|are|was|were|being|been)\s+\w*en\b'
            ]
            has_passive = any(re.search(pattern, sentence, re.IGNORECASE) for pattern in passive_patterns)
            if has_passive:
                errors.append({
                    'type': 'passive_voice',
                    'message': 'Consider using active voice for clearer, more direct writing.',
                    'suggestions': ['Convert to active voice', 'Identify who performs the action'],
                    'sentence': sentence,
                    'sentence_index': i,
                    'severity': 'low'
                })
        
        return errors
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        if not self.nlp:
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]
        
        doc = self.nlp(text)
        return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _check_comprehensive_readability(self, text: str) -> List[Dict[str, Any]]:
        """Check readability scores."""
        errors = []
        try:
            flesch_score = textstat.flesch_reading_ease(text)
            if flesch_score < self.rules['min_readability_score']:
                errors.append({
                    'type': 'readability',
                    'message': f'Text is difficult to read (Flesch score: {flesch_score:.1f}). Aim for 60+ for good readability.',
                    'suggestions': ['Use shorter sentences', 'Use simpler words', 'Break up complex ideas'],
                    'severity': 'medium',
                    'score': flesch_score
                })
        except Exception as e:
            logger.error(f"Readability check failed: {e}")
        return errors
    
    def _check_grade_level(self, text: str) -> List[Dict[str, Any]]:
        """Check grade level of the text."""
        errors = []
        try:
            grade_level = textstat.text_standard(text, float_output=True)
            if grade_level < self.rules['target_grade_level'][0] or grade_level > self.rules['target_grade_level'][1]:
                errors.append({
                    'type': 'grade_level',
                    'message': f'Text is at grade level {grade_level:.1f}. Aim for {self.rules["target_grade_level"][0]}-{self.rules["target_grade_level"][1]} for optimal readability.',
                    'suggestions': ['Use simpler words', 'Break up complex ideas'],
                    'severity': 'medium',
                    'score': grade_level
                })
        except Exception as e:
            logger.error(f"Grade level check failed: {e}")
        return errors
    
    def _check_sentence_length_and_variety(self, sentences: List[str]) -> List[Dict[str, Any]]:
        """Check for overly long sentences and sentence length variety."""
        errors = []
        for i, sentence in enumerate(sentences):
            word_count = len(sentence.split())
            if word_count > self.rules['max_sentence_length']:
                # Generate dynamic suggestions using NLP analysis
                dynamic_suggestions = self._analyze_sentence_structure(sentence, 'length')
                errors.append({
                    'type': 'sentence_length',
                    'message': f'Sentence is too long ({word_count} words). Consider breaking it up.',
                    'suggestions': dynamic_suggestions,
                    'sentence': sentence,
                    'sentence_index': i,
                    'word_count': word_count,
                    'severity': 'medium' if word_count < 35 else 'high'
                })
        return errors
    
    def _check_passive_voice(self, sentences: List[str]) -> List[Dict[str, Any]]:
        """Detect passive voice usage."""
        errors = []
        for i, sentence in enumerate(sentences):
            if self.nlp:
                doc = self.nlp(sentence)
                passive_constructions = self._find_passive_constructions(doc)
                if passive_constructions:
                    # Generate dynamic suggestions using NLP analysis
                    dynamic_suggestions = self._analyze_sentence_structure(sentence, 'passive_voice', doc)
                    errors.append({
                        'type': 'passive_voice',
                        'message': 'Consider using active voice for clearer, more direct writing.',
                        'suggestions': dynamic_suggestions,
                        'sentence': sentence,
                        'sentence_index': i,
                        'severity': 'low',
                        'passive_constructions': passive_constructions
                    })
            else:
                # Fallback regex detection when SpaCy not available
                passive_patterns = [
                    r'\b(is|are|was|were|being|been)\s+\w*ed\b',
                    r'\b(is|are|was|were|being|been)\s+\w*en\b'
                ]
                has_passive = any(re.search(pattern, sentence, re.IGNORECASE) for pattern in passive_patterns)
                if has_passive:
                    dynamic_suggestions = self._analyze_sentence_structure(sentence, 'passive_voice')
                    errors.append({
                        'type': 'passive_voice',
                        'message': 'Consider using active voice for clearer, more direct writing.',
                        'suggestions': dynamic_suggestions,
                        'sentence': sentence,
                        'sentence_index': i,
                        'severity': 'low'
                    })
        return errors
    
    def _check_conciseness(self, sentences: List[str]) -> List[Dict[str, Any]]:
        """Check for wordy phrases and redundancy."""
        errors = []
        for i, sentence in enumerate(sentences):
            if self.nlp:
                doc = self.nlp(sentence)
                wordy_elements = self._find_wordy_elements(doc, sentence)
                if wordy_elements:
                    # Generate dynamic suggestions using NLP analysis
                    dynamic_suggestions = self._analyze_sentence_structure(sentence, 'conciseness', doc, wordy_elements)
                    errors.append({
                        'type': 'conciseness',
                        'message': 'Consider using more concise language.',
                        'suggestions': dynamic_suggestions,
                        'sentence': sentence,
                        'sentence_index': i,
                        'severity': 'low',
                        'wordy_elements': wordy_elements
                    })
            else:
                # Fallback when SpaCy not available
                wordy_elements = self._find_wordy_elements_regex(sentence)
                if wordy_elements:
                    dynamic_suggestions = self._analyze_sentence_structure(sentence, 'conciseness', None, wordy_elements)
                    errors.append({
                        'type': 'conciseness',
                        'message': 'Consider using more concise language.',
                        'suggestions': dynamic_suggestions,
                        'sentence': sentence,
                        'sentence_index': i,
                        'severity': 'low',
                        'wordy_elements': wordy_elements
                    })
        return errors
    
    def _check_clarity(self, sentences: List[str]) -> List[Dict[str, Any]]:
        """Check for clarity issues like jargon, complex words."""
        errors = []
        for i, sentence in enumerate(sentences):
            if self.nlp:
                doc = self.nlp(sentence)
                complex_elements = self._find_complex_elements(doc, sentence)
                if complex_elements:
                    # Generate dynamic suggestions using NLP analysis
                    dynamic_suggestions = self._analyze_sentence_structure(sentence, 'clarity', doc, complex_elements)
                    errors.append({
                        'type': 'clarity',
                        'message': 'Consider using simpler, clearer language.',
                        'suggestions': dynamic_suggestions,
                        'sentence': sentence,
                        'sentence_index': i,
                        'severity': 'low',
                        'complex_elements': complex_elements
                    })
            else:
                # Fallback when SpaCy not available
                complex_elements = self._find_complex_elements_regex(sentence)
                if complex_elements:
                    dynamic_suggestions = self._analyze_sentence_structure(sentence, 'clarity', None, complex_elements)
                    errors.append({
                        'type': 'clarity',
                        'message': 'Consider using simpler, clearer language.',
                        'suggestions': dynamic_suggestions,
                        'sentence': sentence,
                        'sentence_index': i,
                        'severity': 'low',
                        'complex_elements': complex_elements
                    })
        return errors
    
    def _check_technical_writing_patterns(self, sentences: List[str]) -> List[Dict[str, Any]]:
        """Check for technical writing specific patterns."""
        errors = []
        # Implement technical writing specific pattern checks
        return errors
    
    def _generate_suggestions(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate improvement suggestions based on detected errors."""
        suggestions = []
        error_counts = defaultdict(int)
        for error in errors:
            error_counts[error['type']] += 1
        
        if error_counts['sentence_length'] > 2:
            suggestions.append({
                'type': 'general',
                'title': 'Sentence Length',
                'message': 'Multiple long sentences detected. Consider breaking them into shorter, clearer sentences.',
                'priority': 'high'
            })
        
        if error_counts['passive_voice'] > 3:
            suggestions.append({
                'type': 'general',
                'title': 'Active Voice',
                'message': 'Use active voice more frequently for clearer, more engaging writing.',
                'priority': 'medium'
            })
        
        return suggestions
    
    def _calculate_comprehensive_statistics(self, text: str, sentences: List[str], paragraphs: List[str]) -> Dict[str, Any]:
        """Calculate comprehensive text statistics for technical writing."""
        words = text.split()
        stats = {
            # Basic counts
            'word_count': len(words),
            'sentence_count': len(sentences),
            'paragraph_count': len(paragraphs),
            'character_count': len(text),
            'character_count_no_spaces': len(text.replace(' ', '')),
            
            # Sentence analysis
            'avg_sentence_length': 0,
            'median_sentence_length': 0,
            'sentence_length_variety': 0,
            'longest_sentence': 0,
            'shortest_sentence': 0,
            
            # Word analysis
            'avg_word_length': 0,
            'avg_syllables_per_word': 0,
            'complex_words_count': 0,
            'complex_words_percentage': 0,
            
            # Readability scores
            'flesch_reading_ease': 0,
            'flesch_kincaid_grade': 0,
            'gunning_fog_index': 0,
            'smog_index': 0,
            'coleman_liau_index': 0,
            'automated_readability_index': 0,
            'dale_chall_readability': 0,
            'linsear_write_formula': 0,
            
            # Technical writing metrics
            'passive_voice_percentage': 0,
            'grade_level_assessment': '',
            'readability_grade_target_met': False,
            'technical_complexity_score': 0,
            
            # Language patterns
            'most_common_words': [],
            'word_frequency_distribution': {},
            'sentence_types': {'simple': 0, 'compound': 0, 'complex': 0}
        }
        
        try:
            if sentences:
                sentence_lengths = [len(s.split()) for s in sentences]
                stats['avg_sentence_length'] = sum(sentence_lengths) / len(sentence_lengths)
                stats['median_sentence_length'] = sorted(sentence_lengths)[len(sentence_lengths) // 2]
                stats['longest_sentence'] = max(sentence_lengths)
                stats['shortest_sentence'] = min(sentence_lengths)
                
                # Calculate sentence length variety (coefficient of variation)
                if stats['avg_sentence_length'] > 0:
                    variance = sum((x - stats['avg_sentence_length']) ** 2 for x in sentence_lengths) / len(sentence_lengths)
                    std_dev = math.sqrt(variance)
                    stats['sentence_length_variety'] = std_dev / stats['avg_sentence_length']
            
            # Word analysis
            if words:
                word_lengths = [len(word.strip('.,!?;:"()[]{}')) for word in words]
                stats['avg_word_length'] = sum(word_lengths) / len(word_lengths)
                
                # Count complex words (3+ syllables)
                complex_words = 0
                total_syllables = 0
                
                for word in words:
                    clean_word = re.sub(r'[^a-zA-Z]', '', word.lower())
                    if clean_word:
                        syllable_count = self._estimate_syllables(clean_word)
                        total_syllables += syllable_count
                        if syllable_count >= 3:
                            complex_words += 1
                
                stats['complex_words_count'] = complex_words
                stats['complex_words_percentage'] = (complex_words / len(words)) * 100 if words else 0
                stats['avg_syllables_per_word'] = total_syllables / len(words) if words else 0
            
            # Comprehensive readability analysis
            stats['flesch_reading_ease'] = textstat.flesch_reading_ease(text)
            stats['flesch_kincaid_grade'] = textstat.flesch_kincaid_grade(text)
            stats['gunning_fog_index'] = textstat.gunning_fog(text)
            stats['smog_index'] = textstat.smog_index(text)
            stats['coleman_liau_index'] = textstat.coleman_liau_index(text)
            stats['automated_readability_index'] = textstat.automated_readability_index(text)
            stats['dale_chall_readability'] = textstat.dale_chall_readability_score(text)
            stats['linsear_write_formula'] = textstat.linsear_write_formula(text)
            
            # Grade level assessment
            grade_level = textstat.text_standard(text, float_output=True)
            stats['grade_level_assessment'] = f"{grade_level:.1f}"
            stats['readability_grade_target_met'] = (
                self.rules['target_grade_level'][0] <= grade_level <= self.rules['target_grade_level'][1]
            )
            
            # Calculate passive voice percentage
            passive_count = sum(1 for error in self._check_passive_voice(sentences) if error['type'] == 'passive_voice')
            stats['passive_voice_percentage'] = (passive_count / len(sentences) * 100) if sentences else 0
            
            # Technical complexity score (custom formula)
            complexity_factors = [
                stats['avg_sentence_length'] / 20,  # Normalize to ~20 words
                stats['avg_syllables_per_word'] / 2,  # Normalize to ~2 syllables
                stats['complex_words_percentage'] / 10,  # Normalize to ~10%
                (100 - stats['flesch_reading_ease']) / 100  # Invert Flesch score
            ]
            stats['technical_complexity_score'] = sum(complexity_factors) / len(complexity_factors) * 100
            
            # Word frequency analysis
            word_counter = Counter(word.lower().strip('.,!?;:"()[]{}') for word in words)
            stats['most_common_words'] = word_counter.most_common(10)
            stats['word_frequency_distribution'] = dict(word_counter.most_common(20))
            
            # Sentence type analysis (simplified)
            for sentence in sentences:
                if ';' in sentence or ' and ' in sentence or ' or ' in sentence:
                    if ',' in sentence and len(sentence.split(',')) > 2:
                        stats['sentence_types']['complex'] += 1
                    else:
                        stats['sentence_types']['compound'] += 1
                else:
                    stats['sentence_types']['simple'] += 1
                    
        except Exception as e:
            logger.error(f"Error calculating comprehensive statistics: {e}")
        
        return stats
    
    def _estimate_syllables(self, word: str) -> int:
        """Fallback syllable estimation when syllables library is not available."""
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        if word[0] in vowels:
            count += 1
        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] not in vowels:
                count += 1
        if word.endswith("e"):
            count -= 1
        if count == 0:
            count += 1
        return count
    
    def _calculate_technical_writing_metrics(self, text: str, sentences: List[str], errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate technical writing specific metrics."""
        metrics = {
            # Core readability metrics
            'flesch_reading_ease': 0,
            'flesch_kincaid_grade': 0,
            'gunning_fog_index': 0,
            'smog_index': 0,
            'coleman_liau_index': 0,
            'automated_readability_index': 0,
            'dale_chall_readability': 0,
            
            # Grade level analysis
            'estimated_grade_level': 0,
            'grade_level_category': '',
            'meets_target_grade': False,
            
            # Technical writing assessments
            'sentence_complexity_score': 0,
            'vocabulary_complexity_score': 0,
            'overall_readability_rating': '',
            'passive_voice_ratio': 0,
            'avg_syllables_per_word': 0,
            
            # Recommendations
            'improvement_priority': [],
            'readability_recommendations': []
        }
        
        try:
            # Calculate all readability metrics
            metrics['flesch_reading_ease'] = textstat.flesch_reading_ease(text)
            metrics['flesch_kincaid_grade'] = textstat.flesch_kincaid_grade(text)
            metrics['gunning_fog_index'] = textstat.gunning_fog(text)
            metrics['smog_index'] = textstat.smog_index(text)
            metrics['coleman_liau_index'] = textstat.coleman_liau_index(text)
            metrics['automated_readability_index'] = textstat.automated_readability_index(text)
            metrics['dale_chall_readability'] = textstat.dale_chall_readability_score(text)
            
            # Grade level assessment
            grade_level = textstat.text_standard(text, float_output=True)
            metrics['estimated_grade_level'] = grade_level
            metrics['meets_target_grade'] = (
                self.rules['target_grade_level'][0] <= grade_level <= self.rules['target_grade_level'][1]
            )
            
            # Categorize grade level
            if grade_level <= 8:
                metrics['grade_level_category'] = 'Elementary/Middle School'
            elif grade_level <= 12:
                metrics['grade_level_category'] = 'High School'
            elif grade_level <= 16:
                metrics['grade_level_category'] = 'College Level'
            else:
                metrics['grade_level_category'] = 'Graduate Level'
            
            # Overall readability rating based on Flesch Reading Ease
            flesch_score = metrics['flesch_reading_ease']
            if flesch_score >= 90:
                metrics['overall_readability_rating'] = 'Very Easy'
            elif flesch_score >= 80:
                metrics['overall_readability_rating'] = 'Easy'
            elif flesch_score >= 70:
                metrics['overall_readability_rating'] = 'Fairly Easy'
            elif flesch_score >= 60:
                metrics['overall_readability_rating'] = 'Standard'
            elif flesch_score >= 50:
                metrics['overall_readability_rating'] = 'Fairly Difficult'
            elif flesch_score >= 30:
                metrics['overall_readability_rating'] = 'Difficult'
            else:
                metrics['overall_readability_rating'] = 'Very Difficult'
            
            # Calculate passive voice ratio
            passive_errors = [e for e in errors if e.get('type') == 'passive_voice']
            metrics['passive_voice_ratio'] = len(passive_errors) / len(sentences) if sentences else 0
            
            # Generate improvement priorities
            if not metrics['meets_target_grade']:
                if grade_level > self.rules['target_grade_level'][1]:
                    metrics['improvement_priority'].append('Reduce complexity')
                    metrics['readability_recommendations'].extend([
                        'Use shorter sentences',
                        'Replace complex words with simpler alternatives',
                        'Break up long paragraphs'
                    ])
                else:
                    metrics['improvement_priority'].append('Increase sophistication')
            
            if flesch_score < 60:
                metrics['improvement_priority'].append('Improve readability')
                metrics['readability_recommendations'].extend([
                    'Simplify sentence structure',
                    'Use active voice more frequently',
                    'Reduce average sentence length'
                ])
            
            if metrics['gunning_fog_index'] > 12:
                metrics['improvement_priority'].append('Reduce fog index')
                metrics['readability_recommendations'].append('Eliminate jargon and complex terminology')
            
        except Exception as e:
            logger.error(f"Error calculating technical writing metrics: {e}")
        
        return metrics
    
    def _calculate_overall_score(self, errors: List[Dict[str, Any]], statistics: Dict[str, Any], technical_metrics: Dict[str, Any]) -> float:
        """Calculate overall style score (0-100) with technical writing focus."""
        base_score = 100.0
        
        # Deduct points for errors
        for error in errors:
            severity = error.get('severity', 'medium')
            if severity == 'high':
                base_score -= 8
            elif severity == 'medium':
                base_score -= 5
            else:
                base_score -= 2
        
        # Technical writing specific adjustments
        try:
            # Grade level assessment (major factor)
            if technical_metrics.get('meets_target_grade', False):
                base_score += 10  # Bonus for meeting target grade level
            else:
                grade_level = technical_metrics.get('estimated_grade_level', 0)
                target_min, target_max = self.rules['target_grade_level']
                if grade_level > target_max:
                    # Penalty for being too complex
                    penalty = min(15, (grade_level - target_max) * 3)
                    base_score -= penalty
                elif grade_level < target_min:
                    # Smaller penalty for being too simple
                    penalty = min(5, (target_min - grade_level) * 2)
                    base_score -= penalty
            
            # Readability score adjustments
            flesch_score = statistics.get('flesch_reading_ease', 0)
            if flesch_score >= 70:
                base_score += 5  # Bonus for good readability
            elif flesch_score >= 60:
                base_score += 2  # Small bonus for acceptable readability
            elif flesch_score < 40:
                base_score -= 10  # Penalty for poor readability
            elif flesch_score < 50:
                base_score -= 5  # Smaller penalty for difficult readability
            
            # Gunning Fog Index penalty
            fog_index = statistics.get('gunning_fog_index', 0)
            if fog_index > 15:
                base_score -= 8  # High penalty for very complex text
            elif fog_index > 12:
                base_score -= 5  # Moderate penalty for complex text
            
            # Passive voice penalty
            passive_percentage = statistics.get('passive_voice_percentage', 0)
            if passive_percentage > 25:
                base_score -= 8  # High penalty for excessive passive voice
            elif passive_percentage > 15:
                base_score -= 4  # Moderate penalty for high passive voice
            
            # Sentence length variety bonus
            sentence_variety = statistics.get('sentence_length_variety', 0)
            if sentence_variety > 0.5:  # Good variety
                base_score += 3
            elif sentence_variety < 0.2:  # Poor variety
                base_score -= 3
            
            # Complex words penalty
            complex_percentage = statistics.get('complex_words_percentage', 0)
            if complex_percentage > 20:
                base_score -= 6  # High penalty for too many complex words
            elif complex_percentage > 15:
                base_score -= 3  # Moderate penalty
            
            # Technical complexity score adjustment
            complexity_score = statistics.get('technical_complexity_score', 0)
            if complexity_score > 75:
                base_score -= 5  # Penalty for high complexity
            elif complexity_score < 40:
                base_score += 3  # Bonus for appropriate simplicity
            
        except Exception as e:
            logger.error(f"Error in technical writing score calculation: {e}")
        
        # Ensure score is within bounds
        final_score = max(0, min(100, base_score))
        
        # Round to 1 decimal place
        return round(final_score, 1)
    
    def _analyze_sentence_structure(self, sentence: str, error_type: str, doc=None, elements=None) -> List[str]:
        """
        Dynamically analyze sentence structure using SpaCy and generate contextual suggestions.
        This is the core NLP-driven suggestion engine - no hardcoded strings.
        """
        suggestions = []
        
        # Use SpaCy analysis if available
        if self.nlp and doc is None:
            doc = self.nlp(sentence)
        
        if error_type == 'length' and doc:
            suggestions.extend(self._generate_length_suggestions_from_syntax(doc, sentence))
        elif error_type == 'length':
            suggestions.extend(self._generate_length_suggestions_fallback(sentence))
            
        elif error_type == 'passive_voice' and doc:
            suggestions.extend(self._generate_passive_suggestions_from_syntax(doc, sentence))
        elif error_type == 'passive_voice':
            suggestions.extend(self._generate_passive_suggestions_fallback(sentence))
            
        elif error_type == 'conciseness' and doc and elements:
            suggestions.extend(self._generate_conciseness_suggestions_from_syntax(doc, sentence, elements))
        elif error_type == 'conciseness' and elements:
            suggestions.extend(self._generate_conciseness_suggestions_fallback(sentence, elements))
            
        elif error_type == 'clarity' and doc and elements:
            suggestions.extend(self._generate_clarity_suggestions_from_syntax(doc, sentence, elements))
        elif error_type == 'clarity' and elements:
            suggestions.extend(self._generate_clarity_suggestions_fallback(sentence, elements))
        
        return suggestions if suggestions else [f"Improve {error_type} in this sentence"]
    
    def _generate_length_suggestions_from_syntax(self, doc, sentence: str) -> List[str]:
        """Generate sentence length suggestions using SpaCy's syntactic analysis."""
        suggestions = []
        
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
        
        return suggestions
    
    def _generate_length_suggestions_fallback(self, sentence: str) -> List[str]:
        """Generate length suggestions without SpaCy using basic analysis."""
        suggestions = []
        
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
        
        return suggestions
    
    def _generate_passive_suggestions_from_syntax(self, doc, sentence: str) -> List[str]:
        """Generate passive voice suggestions using SpaCy's syntactic analysis."""
        suggestions = []
        
        # Find all passive constructions
        passive_constructions = self._find_passive_constructions(doc)
        
        for construction in passive_constructions:
            auxiliary = construction['auxiliary']
            main_verb = construction['main_verb']
            subject = construction['subject']
            agent = construction['agent']
            passive_type = construction['type']
            
            if passive_type == 'auxpass':
                if agent:
                    suggestions.append(f"Make '{agent}' the active subject instead of '{subject}'")
                    suggestions.append(f"Convert '{auxiliary} {main_verb}' to '{agent} {main_verb}s'")
                elif subject:
                    suggestions.append(f"Identify who performed the action and make them the subject instead of '{subject}'")
                    suggestions.append(f"Convert passive '{auxiliary} {main_verb}' to active voice")
            
            elif passive_type == 'being_passive':
                if subject:
                    suggestions.append(f"Convert 'being {main_verb}' to active voice with '{subject}' as subject")
                else:
                    suggestions.append(f"Convert 'being {main_verb}' construction to active voice")
            
            elif passive_type == 'future_passive':
                if subject:
                    suggestions.append(f"Convert '{auxiliary} {main_verb}' to active future tense")
                    suggestions.append(f"Make the doer of the action the subject instead of '{subject}'")
            
            elif passive_type == 'progressive_passive':
                if subject:
                    suggestions.append(f"Convert '{auxiliary} {main_verb}' to active progressive form")
                    suggestions.append(f"Identify who is performing the action on '{subject}'")
        
        # Find agent phrases (by + noun) for additional suggestions
        agents = []
        for token in doc:
            if token.text.lower() == 'by' and token.dep_ == 'agent':
                agent_noun = [child for child in token.children if child.pos_ in ['NOUN', 'PROPN']]
                if agent_noun:
                    agents.extend(agent_noun)
        
        for agent in agents:
            suggestions.append(f"Make '{agent.text}' the active subject performing the action")
        
        # Look for implicit passive patterns using dependency analysis
        for token in doc:
            # Find past participles that might be passive
            if token.tag_ == 'VBN' and token.dep_ not in ['auxpass']:
                # Check if it's part of a passive construction we missed
                has_be_auxiliary = any(child.lemma_ == 'be' for child in token.children)
                if has_be_auxiliary:
                    suggestions.append(f"Convert past participle '{token.text}' to active voice")
        
        return suggestions
    
    def _generate_passive_suggestions_fallback(self, sentence: str) -> List[str]:
        """Generate passive voice suggestions without SpaCy."""
        suggestions = []
        
        # Look for "by" phrases that indicate agents
        by_matches = re.finditer(r'\bby\s+(\w+(?:\s+\w+)*)', sentence, re.IGNORECASE)
        for match in by_matches:
            agent = match.group(1)
            suggestions.append(f"Make '{agent}' the subject performing the action")
        
        # Look for common passive patterns
        if re.search(r'\bit was (decided|determined|found|concluded)', sentence, re.IGNORECASE):
            suggestions.append("Identify who made the decision and make them the subject")
        
        if re.search(r'\b(was|were|is|are) (conducted|performed|carried out)', sentence, re.IGNORECASE):
            suggestions.append("Identify who performed the action and make them the subject")
        
        return suggestions
    
    def _find_passive_constructions(self, doc) -> List[Dict[str, str]]:
        """Find passive voice constructions using SpaCy analysis."""
        constructions = []
        
        for token in doc:
            # Method 1: Traditional auxpass detection
            if token.dep_ == 'auxpass':  # Passive auxiliary
                main_verb = token.head
                subject = None
                agent = None
                
                # Find passive subject
                for child in main_verb.children:
                    if child.dep_ == 'nsubjpass':
                        subject = child.text
                    elif child.dep_ == 'agent':
                        # Find the actual agent noun
                        for grandchild in child.children:
                            if grandchild.pos_ in ['NOUN', 'PROPN']:
                                agent = grandchild.text
                
                constructions.append({
                    'auxiliary': token.text,
                    'main_verb': main_verb.text,
                    'subject': subject,
                    'agent': agent,
                    'type': 'auxpass'
                })
            
            # Method 2: Detect "being + past participle" patterns
            elif token.lemma_ == 'be' and token.pos_ == 'AUX':
                # Look for past participles following "being"
                for child in token.children:
                    if child.pos_ == 'VERB' and child.tag_ in ['VBN']:  # Past participle
                        # Find the subject
                        subject = None
                        for sibling in token.head.children if token.head else []:
                            if sibling.dep_ in ['nsubj', 'nsubjpass']:
                                subject = sibling.text
                                break
                        
                        constructions.append({
                            'auxiliary': token.text,
                            'main_verb': child.text,
                            'subject': subject,
                            'agent': None,
                            'type': 'being_passive'
                        })
            
            # Method 3: Detect "will be + past participle" patterns
            elif token.lemma_ == 'will' and token.pos_ == 'AUX':
                # Look for "be" followed by past participle
                be_token = None
                for child in token.children:
                    if child.lemma_ == 'be':
                        be_token = child
                        break
                
                if be_token:
                    for child in be_token.children:
                        if child.pos_ == 'VERB' and child.tag_ == 'VBN':
                            # Find subject
                            subject = None
                            for sibling in token.head.children if token.head else []:
                                if sibling.dep_ in ['nsubj', 'nsubjpass']:
                                    subject = sibling.text
                                    break
                            
                            constructions.append({
                                'auxiliary': f"{token.text} {be_token.text}",
                                'main_verb': child.text,
                                'subject': subject,
                                'agent': None,
                                'type': 'future_passive'
                            })
            
            # Method 4: Detect "are being + past participle" patterns
            elif token.lemma_ == 'be' and token.tag_ in ['VBP', 'VBZ']:  # Present tense "are/is"
                # Look for "being" followed by past participle
                being_token = None
                for child in token.children:
                    if child.lemma_ == 'be' and child.tag_ == 'VBG':  # "being"
                        being_token = child
                        break
                
                if being_token:
                    for child in being_token.children:
                        if child.pos_ == 'VERB' and child.tag_ == 'VBN':
                            # Find subject
                            subject = None
                            for sibling in token.head.children if token.head else []:
                                if sibling.dep_ in ['nsubj', 'nsubjpass']:
                                    subject = sibling.text
                                    break
                            
                            constructions.append({
                                'auxiliary': f"{token.text} {being_token.text}",
                                'main_verb': child.text,
                                'subject': subject,
                                'agent': None,
                                'type': 'progressive_passive'
                            })
        
        return constructions
    
    def _find_wordy_elements(self, doc, sentence: str) -> List[Dict[str, str]]:
        """Find wordy elements using SpaCy analysis."""
        elements = []
        
        # Find nominalizations (verbs turned into nouns)
        for token in doc:
            if token.pos_ == 'NOUN' and token.text.endswith(('tion', 'sion', 'ment', 'ance', 'ence')):
                # Check if there's a simpler verb form
                root = token.lemma_.replace('tion', '').replace('sion', '').replace('ment', '').replace('ance', '').replace('ence', '')
                if len(root) > 3:  # Avoid very short roots
                    elements.append({
                        'type': 'nominalization',
                        'original': token.text,
                        'suggested_root': root,
                        'context': f"Consider using the verb form instead of '{token.text}'"
                    })
        
        # Find redundant phrases using dependency parsing
        redundant_patterns = self._find_redundant_patterns(doc)
        elements.extend(redundant_patterns)
        
        return elements
    
    def _find_wordy_elements_regex(self, sentence: str) -> List[Dict[str, str]]:
        """Find wordy elements using regex patterns when SpaCy unavailable."""
        elements = []
        
        wordy_phrases = {
            r'\bin order to\b': 'to',
            r'\bdue to the fact that\b': 'because',
            r'\bat this point in time\b': 'now',
            r'\ba large number of\b': 'many',
            r'\bfor the purpose of\b': 'to',
            r'\bin spite of the fact that\b': 'although'
        }
        
        for pattern, replacement in wordy_phrases.items():
            matches = re.finditer(pattern, sentence, re.IGNORECASE)
            for match in matches:
                elements.append({
                    'type': 'wordy_phrase',
                    'original': match.group(),
                    'replacement': replacement,
                    'context': f"Replace '{match.group()}' with '{replacement}'"
                })
        
        return elements
    
    def _find_complex_elements(self, doc, sentence: str) -> List[Dict[str, str]]:
        """Find complex language elements using SpaCy analysis."""
        elements = []
        
        # Find complex words (3+ syllables, formal register)
        for token in doc:
            if token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV'] and len(token.text) > 6:
                syllable_count = self._estimate_syllables(token.text)
                if syllable_count >= 3:
                    # Check if it's a common complex word with simpler alternative
                    simpler = self._find_simpler_alternative(token.text.lower())
                    if simpler:
                        elements.append({
                            'type': 'complex_word',
                            'original': token.text,
                            'alternative': simpler,
                            'context': f"Consider replacing '{token.text}' with '{simpler}'"
                        })
        
        return elements
    
    def _find_complex_elements_regex(self, sentence: str) -> List[Dict[str, str]]:
        """Find complex elements using regex when SpaCy unavailable."""
        elements = []
        
        complex_words = {
            'utilize': 'use', 'facilitate': 'help', 'demonstrate': 'show',
            'implement': 'do', 'commence': 'start', 'terminate': 'end',
            'endeavor': 'try', 'ascertain': 'find out', 'subsequent': 'next'
        }
        
        for complex_word, simple_word in complex_words.items():
            if re.search(r'\b' + complex_word + r'\b', sentence, re.IGNORECASE):
                elements.append({
                    'type': 'complex_word',
                    'original': complex_word,
                    'alternative': simple_word,
                    'context': f"Replace '{complex_word}' with '{simple_word}'"
                })
        
        return elements
    
    def _find_redundant_patterns(self, doc) -> List[Dict[str, str]]:
        """Find redundant patterns using dependency analysis."""
        patterns = []
        
        # Look for "make a decision" type patterns
        for token in doc:
            if token.lemma_ == 'make' and token.pos_ == 'VERB':
                # Look for object that could be a verb
                for child in token.children:
                    if child.dep_ == 'dobj' and child.text in ['decision', 'choice', 'selection']:
                        verb_form = {'decision': 'decide', 'choice': 'choose', 'selection': 'select'}.get(child.text)
                        if verb_form:
                            patterns.append({
                                'type': 'nominalization_phrase',
                                'original': f"{token.text} a {child.text}",
                                'alternative': verb_form,
                                'context': f"Use '{verb_form}' instead of '{token.text} a {child.text}'"
                            })
        
        return patterns
    
    def _find_simpler_alternative(self, word: str) -> str:
        """Find simpler alternatives for complex words using linguistic knowledge."""
        # This could be expanded with a more comprehensive dictionary
        alternatives = {
            'utilize': 'use', 'facilitate': 'help', 'demonstrate': 'show',
            'implement': 'do', 'commence': 'start', 'terminate': 'end',
            'endeavor': 'try', 'ascertain': 'find out', 'subsequent': 'next',
            'prior': 'before', 'initiate': 'start', 'finalize': 'finish',
            'approximately': 'about', 'sufficient': 'enough', 'numerous': 'many'
        }
        return alternatives.get(word)
    
    def _generate_conciseness_suggestions_from_syntax(self, doc, sentence: str, elements: List[Dict]) -> List[str]:
        """Generate conciseness suggestions using syntactic analysis."""
        suggestions = []
        
        for element in elements:
            if element['type'] == 'nominalization':
                suggestions.append(f"Convert nominalization '{element['original']}' to verb form")
            elif element['type'] == 'wordy_phrase':
                suggestions.append(f"Replace '{element['original']}' with '{element['replacement']}'")
            elif element['type'] == 'nominalization_phrase':
                suggestions.append(f"Use '{element['alternative']}' instead of '{element['original']}'")
        
        return suggestions
    
    def _generate_conciseness_suggestions_fallback(self, sentence: str, elements: List[Dict]) -> List[str]:
        """Generate conciseness suggestions without SpaCy."""
        suggestions = []
        
        for element in elements:
            suggestions.append(element['context'])
        
        return suggestions
    
    def _generate_clarity_suggestions_from_syntax(self, doc, sentence: str, elements: List[Dict]) -> List[str]:
        """Generate clarity suggestions using syntactic analysis."""
        suggestions = []
        
        for element in elements:
            if element['type'] == 'complex_word':
                suggestions.append(f"Replace '{element['original']}' with simpler '{element['alternative']}'")
        
        return suggestions
    
    def _generate_clarity_suggestions_fallback(self, sentence: str, elements: List[Dict]) -> List[str]:
        """Generate clarity suggestions without SpaCy."""
        suggestions = []
        
        for element in elements:
            suggestions.append(element['context'])
        
        return suggestions 