"""
Exclamation Points Rule
Based on IBM Style Guide topic: "Exclamation points"
"""
from typing import List, Dict, Any, Set, Tuple, Optional
import re
from .base_punctuation_rule import BasePunctuationRule

class ExclamationPointsRule(BasePunctuationRule):
    """
    Comprehensive exclamation points usage checker using morphological spaCy analysis with linguistic anchors.
    Handles context appropriateness, emotional tone analysis, and alternatives in professional writing.
    """
    
    def _get_rule_type(self) -> str:
        return 'exclamation_points'

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
        """Comprehensive NLP-based exclamation point analysis using linguistic anchors."""
        errors = []
        
        # Find all exclamation points in the sentence
        exclamation_tokens = self._find_exclamation_tokens(doc)
        
        if not exclamation_tokens:
            return errors
        
        # Check various exclamation point usage patterns
        errors.extend(self._check_exclamation_context(doc, exclamation_tokens, sentence, sentence_index))
        errors.extend(self._check_multiple_exclamations(doc, exclamation_tokens, sentence, sentence_index))
        errors.extend(self._check_writing_style_appropriateness(doc, exclamation_tokens, sentence, sentence_index))
        errors.extend(self._check_emotional_tone_analysis(doc, exclamation_tokens, sentence, sentence_index))
        errors.extend(self._check_exclamation_alternatives(doc, exclamation_tokens, sentence, sentence_index))
        errors.extend(self._check_exclamation_combinations(doc, exclamation_tokens, sentence, sentence_index))
        
        return errors

    def _find_exclamation_tokens(self, doc) -> List[int]:
        """Find all exclamation point tokens in the document."""
        exclamation_indices = []
        
        for token in doc:
            if token.text == '!':
                exclamation_indices.append(token.i)
        
        return exclamation_indices

    def _check_exclamation_context(self, doc, exclamation_tokens: List[int], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check exclamation point context using linguistic anchors."""
        errors = []
        
        for token_idx in exclamation_tokens:
            context_type = self._determine_exclamation_context(doc, token_idx)
            
            if context_type == 'command_imperative':
                # Check if appropriate for the command
                if not self._is_appropriate_imperative_exclamation(doc, token_idx):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message="Exclamation point may not be necessary for this imperative statement.",
                        suggestions=["Consider using a period for calm, professional instructions.",
                                   "Reserve exclamation points for urgent commands."],
                        severity='low'
                    ))
            
            elif context_type == 'interjection':
                # Check if appropriate for professional writing
                if self._is_professional_writing_context(doc):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message="Interjections with exclamation points should be avoided in professional writing.",
                        suggestions=["Use more formal language to express the sentiment.",
                                   "Replace with declarative statements.",
                                   "Consider the professional tone requirements."],
                        severity='medium'
                    ))
            
            elif context_type == 'emphatic_statement':
                # Check if emphasis is appropriate
                if self._is_technical_writing_context(doc):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message="Emphatic exclamation points should be avoided in technical writing.",
                        suggestions=["Use strong, clear language instead of exclamation points.",
                                   "Rely on precise terminology for emphasis.",
                                   "Consider restructuring for clarity without emotional punctuation."],
                        severity='medium'
                    ))
            
            elif context_type == 'emotional_expression':
                # Generally inappropriate in formal writing
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Emotional expressions with exclamation points should be avoided in formal writing.",
                    suggestions=["Use objective, professional language.",
                               "Express ideas through clear reasoning rather than emotion.",
                               "Consider the audience and writing context."],
                    severity='medium'
                ))
            
            elif context_type == 'surprise_reaction':
                # Check appropriateness for writing style
                if not self._is_informal_writing_acceptable(doc):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message="Exclamation points expressing surprise should be avoided in formal writing.",
                        suggestions=["Use descriptive language to convey the information.",
                                   "State facts objectively without emotional punctuation.",
                                   "Consider more professional phrasing."],
                        severity='medium'
                    ))
        
        return errors

    def _check_multiple_exclamations(self, doc, exclamation_tokens: List[int], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check for multiple exclamation points."""
        errors = []
        
        # Check for consecutive exclamation points
        consecutive_exclamations = self._find_consecutive_exclamations(doc, exclamation_tokens)
        
        if consecutive_exclamations:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Multiple consecutive exclamation points are unprofessional.",
                suggestions=["Use only one exclamation point for emphasis.",
                           "Consider whether emphasis is truly necessary.",
                           "Use strong, clear language instead of multiple punctuation marks."],
                severity='high'
            ))
        
        # Check for excessive exclamations in one sentence
        if len(exclamation_tokens) > 1:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Multiple exclamation points in one sentence may impact professionalism.",
                suggestions=["Limit to one exclamation point per sentence.",
                           "Consider whether all exclamations are necessary.",
                           "Rewrite to be more direct and professional."],
                severity='medium'
            ))
        
        return errors

    def _check_writing_style_appropriateness(self, doc, exclamation_tokens: List[int], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check appropriateness for writing style."""
        errors = []
        
        writing_style = self._determine_writing_style(doc)
        
        if writing_style == 'technical' and exclamation_tokens:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Exclamation points are generally inappropriate in technical documentation.",
                suggestions=["Use precise, objective language.",
                           "Replace with periods for professional tone.",
                           "Focus on clarity and accuracy rather than emotion."],
                severity='medium'
            ))
        
        elif writing_style == 'academic' and exclamation_tokens:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message="Exclamation points should be avoided in academic writing.",
                suggestions=["Use scholarly, objective tone.",
                           "Express ideas through reasoned argument.",
                           "Replace with appropriate academic punctuation."],
                severity='medium'
            ))
        
        elif writing_style == 'formal_business' and exclamation_tokens:
            # Check if it's appropriate business context
            if not self._is_appropriate_business_exclamation(doc, exclamation_tokens[0]):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Exclamation points should be used sparingly in formal business communication.",
                    suggestions=["Reserve for genuine excitement or urgent matters.",
                               "Use professional, measured tone.",
                               "Consider if the exclamation adds value or seems unprofessional."],
                    severity='low'
                ))
        
        return errors

    def _check_emotional_tone_analysis(self, doc, exclamation_tokens: List[int], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Analyze emotional tone and appropriateness."""
        errors = []
        
        for token_idx in exclamation_tokens:
            emotional_intensity = self._analyze_emotional_intensity(doc, token_idx)
            
            if emotional_intensity == 'high':
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="High emotional intensity may be inappropriate for professional writing.",
                    suggestions=["Use more measured, professional language.",
                               "Express ideas objectively rather than emotionally.",
                               "Consider the impact on professional credibility."],
                    severity='medium'
                ))
            
            elif emotional_intensity == 'excessive':
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Excessive emotional expression should be avoided in professional contexts.",
                    suggestions=["Significantly tone down the emotional language.",
                               "Focus on facts and objective information.",
                               "Rewrite to maintain professional composure."],
                    severity='high'
                ))
        
        return errors

    def _check_exclamation_alternatives(self, doc, exclamation_tokens: List[int], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Suggest alternatives to exclamation points."""
        errors = []
        
        for token_idx in exclamation_tokens:
            alternatives = self._suggest_exclamation_alternatives(doc, token_idx)
            
            if alternatives:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message="Consider alternatives to exclamation points for professional communication.",
                    suggestions=alternatives,
                    severity='low'
                ))
        
        return errors

    def _check_exclamation_combinations(self, doc, exclamation_tokens: List[int], sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """Check combinations with other punctuation."""
        errors = []
        
        for token_idx in exclamation_tokens:
            combination_issues = self._analyze_punctuation_combinations(doc, token_idx)
            
            for issue in combination_issues:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=sentence_index,
                    message=issue['message'],
                    suggestions=issue['suggestions'],
                    severity=issue['severity']
                ))
        
        return errors

    # Helper methods using linguistic anchors

    def _determine_exclamation_context(self, doc, token_idx: int) -> str:
        """Linguistic anchor: Determine the context of exclamation point usage."""
        # Check if it's with a command/imperative
        if self._is_imperative_context(doc, token_idx):
            return 'command_imperative'
        
        # Check if it's with an interjection
        if self._is_interjection_context(doc, token_idx):
            return 'interjection'
        
        # Check if it's for emphasis
        if self._is_emphatic_context(doc, token_idx):
            return 'emphatic_statement'
        
        # Check if it's emotional expression
        if self._is_emotional_context(doc, token_idx):
            return 'emotional_expression'
        
        # Check if it's surprise/reaction
        if self._is_surprise_context(doc, token_idx):
            return 'surprise_reaction'
        
        return 'unknown'

    def _is_imperative_context(self, doc, token_idx: int) -> bool:
        """Check if exclamation point is with imperative statement."""
        # Look for imperative verbs (ROOT verbs without explicit subjects)
        for token in doc:
            if token.pos_ == 'VERB' and token.dep_ == 'ROOT':
                # Check if there's no explicit subject
                has_explicit_subject = any(child.dep_ in ['nsubj', 'nsubjpass'] for child in token.children)
                if not has_explicit_subject:
                    return True
        
        # Look for imperative indicators
        imperative_indicators = {'please', 'note', 'remember', 'ensure', 'make', 'do', 'don\'t', 'stop'}
        sentence_start_words = [token.lemma_.lower() for token in doc[:2]]
        
        return any(word in imperative_indicators for word in sentence_start_words)

    def _is_interjection_context(self, doc, token_idx: int) -> bool:
        """Check if exclamation point is with interjection."""
        # Look for interjection POS tags
        has_interjection = any(token.pos_ == 'INTJ' for token in doc)
        
        # Look for common interjections
        interjections = {
            'wow', 'oh', 'ah', 'hey', 'well', 'yes', 'no', 'great', 'awesome',
            'amazing', 'fantastic', 'wonderful', 'excellent', 'perfect'
        }
        
        doc_words = [token.lemma_.lower() for token in doc]
        has_interjection_word = any(word in interjections for word in doc_words)
        
        return has_interjection or has_interjection_word

    def _is_emphatic_context(self, doc, token_idx: int) -> bool:
        """Check if exclamation point is for emphasis."""
        # Look for emphatic words and structures
        emphatic_words = {
            'very', 'really', 'extremely', 'absolutely', 'definitely', 'certainly',
            'completely', 'totally', 'incredibly', 'amazing', 'outstanding'
        }
        
        # Look for superlatives
        has_superlative = any(token.tag_ in ['JJS', 'RBS'] for token in doc)  # Superlative adjective/adverb
        
        # Look for emphatic adverbs
        doc_words = [token.lemma_.lower() for token in doc]
        has_emphatic_words = any(word in emphatic_words for word in doc_words)
        
        return has_superlative or has_emphatic_words

    def _is_emotional_context(self, doc, token_idx: int) -> bool:
        """Check if exclamation point expresses emotion."""
        # Look for emotional words
        emotional_words = {
            'love', 'hate', 'excited', 'thrilled', 'disappointed', 'frustrated',
            'angry', 'happy', 'sad', 'worried', 'concerned', 'delighted'
        }
        
        # Look for emotional expressions
        emotional_expressions = {
            'can\'t believe', 'so excited', 'totally agree', 'love this',
            'hate when', 'feel like', 'makes me'
        }
        
        doc_text = doc.text.lower()
        doc_words = [token.lemma_.lower() for token in doc]
        
        has_emotional_words = any(word in emotional_words for word in doc_words)
        has_emotional_expressions = any(expr in doc_text for expr in emotional_expressions)
        
        return has_emotional_words or has_emotional_expressions

    def _is_surprise_context(self, doc, token_idx: int) -> bool:
        """Check if exclamation point expresses surprise."""
        # Look for surprise indicators
        surprise_words = {
            'surprise', 'surprised', 'unexpected', 'suddenly', 'wow', 'whoa',
            'incredible', 'unbelievable', 'amazing', 'shocking'
        }
        
        # Look for question-exclamation patterns
        has_question_words = any(token.lemma_.lower() in {'what', 'how', 'why', 'when', 'where'} 
                               for token in doc)
        
        doc_words = [token.lemma_.lower() for token in doc]
        has_surprise_words = any(word in surprise_words for word in doc_words)
        
        return has_surprise_words or has_question_words

    def _is_professional_writing_context(self, doc) -> bool:
        """Determine if this is professional writing context."""
        professional_indicators = {
            'client', 'customer', 'business', 'company', 'organization', 'team',
            'project', 'meeting', 'report', 'analysis', 'strategy', 'proposal',
            'contract', 'agreement', 'policy', 'procedure', 'protocol'
        }
        
        doc_text = doc.text.lower()
        return any(indicator in doc_text for indicator in professional_indicators)

    def _is_technical_writing_context(self, doc) -> bool:
        """Determine if this is technical writing context."""
        technical_indicators = {
            'system', 'process', 'method', 'algorithm', 'function', 'protocol',
            'interface', 'implementation', 'configuration', 'parameter', 'variable',
            'database', 'server', 'client', 'api', 'framework', 'library',
            'documentation', 'specification', 'requirement', 'procedure'
        }
        
        doc_text = doc.text.lower()
        return any(indicator in doc_text for indicator in technical_indicators)

    def _is_appropriate_imperative_exclamation(self, doc, token_idx: int) -> bool:
        """Check if imperative exclamation is appropriate."""
        # Look for urgency indicators
        urgency_words = {'urgent', 'immediately', 'asap', 'emergency', 'critical', 'important'}
        doc_words = [token.lemma_.lower() for token in doc]
        
        return any(word in urgency_words for word in doc_words)

    def _determine_writing_style(self, doc) -> str:
        """Determine the writing style of the document."""
        doc_text = doc.text.lower()
        
        # Technical writing indicators
        if self._is_technical_writing_context(doc):
            return 'technical'
        
        # Academic writing indicators
        academic_indicators = {
            'research', 'study', 'analysis', 'hypothesis', 'methodology', 'conclusion',
            'evidence', 'findings', 'results', 'discussion', 'literature', 'reference'
        }
        if any(indicator in doc_text for indicator in academic_indicators):
            return 'academic'
        
        # Business writing indicators
        business_indicators = {
            'business', 'corporate', 'company', 'client', 'customer', 'proposal',
            'contract', 'meeting', 'presentation', 'strategy', 'revenue'
        }
        if any(indicator in doc_text for indicator in business_indicators):
            return 'formal_business'
        
        # Default to general formal
        return 'formal'

    def _is_appropriate_business_exclamation(self, doc, token_idx: int) -> bool:
        """Check if business exclamation is appropriate."""
        # Look for positive business contexts
        positive_business = {
            'congratulations', 'success', 'achievement', 'milestone', 'celebration',
            'excellent', 'outstanding', 'fantastic', 'great news'
        }
        
        doc_words = [token.lemma_.lower() for token in doc]
        return any(word in positive_business for word in doc_words)

    def _is_informal_writing_acceptable(self, doc) -> bool:
        """Check if informal writing is acceptable in this context."""
        # Look for informal indicators
        informal_indicators = {
            'blog', 'social', 'casual', 'friendly', 'personal', 'chat',
            'conversation', 'informal', 'relaxed'
        }
        
        doc_text = doc.text.lower()
        return any(indicator in doc_text for indicator in informal_indicators)

    def _find_consecutive_exclamations(self, doc, exclamation_tokens: List[int]) -> bool:
        """Find consecutive exclamation points."""
        if len(exclamation_tokens) < 2:
            return False
        
        for i in range(len(exclamation_tokens) - 1):
            if exclamation_tokens[i + 1] - exclamation_tokens[i] == 1:
                return True
        
        return False

    def _analyze_emotional_intensity(self, doc, token_idx: int) -> str:
        """Analyze the emotional intensity of the expression."""
        # Count emotional/emphatic words
        emotional_words = {
            'love', 'hate', 'amazing', 'terrible', 'fantastic', 'awful',
            'incredible', 'outstanding', 'brilliant', 'perfect', 'disaster'
        }
        
        emphatic_words = {
            'very', 'extremely', 'incredibly', 'absolutely', 'totally',
            'completely', 'utterly', 'definitely', 'certainly'
        }
        
        doc_words = [token.lemma_.lower() for token in doc]
        
        emotional_count = sum(1 for word in doc_words if word in emotional_words)
        emphatic_count = sum(1 for word in doc_words if word in emphatic_words)
        
        # Check for all caps (high intensity indicator)
        has_caps = any(token.text.isupper() and len(token.text) > 1 for token in doc)
        
        total_intensity = emotional_count + emphatic_count + (2 if has_caps else 0)
        
        if total_intensity >= 4:
            return 'excessive'
        elif total_intensity >= 2:
            return 'high'
        elif total_intensity >= 1:
            return 'moderate'
        else:
            return 'low'

    def _suggest_exclamation_alternatives(self, doc, token_idx: int) -> List[str]:
        """Suggest alternatives to exclamation points."""
        context_type = self._determine_exclamation_context(doc, token_idx)
        
        alternatives = []
        
        if context_type == 'command_imperative':
            alternatives.extend([
                "Use a period for calm, authoritative instructions.",
                "Add 'please' to make requests more polite.",
                "Use imperative mood without emphatic punctuation."
            ])
        
        elif context_type == 'emphatic_statement':
            alternatives.extend([
                "Use strong, specific adjectives instead of exclamation points.",
                "Employ precise, powerful verbs for emphasis.",
                "Structure sentences for natural emphasis through word choice."
            ])
        
        elif context_type == 'emotional_expression':
            alternatives.extend([
                "Express ideas through clear, reasoned statements.",
                "Use descriptive language rather than emotional punctuation.",
                "Focus on objective facts and their implications."
            ])
        
        elif context_type == 'interjection':
            alternatives.extend([
                "Replace interjections with more formal expressions.",
                "Use complete sentences to express the sentiment.",
                "Consider the professional context and audience."
            ])
        
        # General alternatives
        alternatives.extend([
            "Replace with a period for a more professional tone.",
            "Use strong word choice instead of emphatic punctuation.",
            "Consider whether the emphasis truly adds value."
        ])
        
        return alternatives

    def _analyze_punctuation_combinations(self, doc, token_idx: int) -> List[Dict[str, Any]]:
        """Analyze combinations with other punctuation."""
        issues = []
        
        if token_idx >= len(doc):
            return issues
        
        # Check for combinations with question marks
        if token_idx > 0 and doc[token_idx - 1].text == '?':
            issues.append({
                'message': "Question mark followed by exclamation point (?!) is informal.",
                'suggestions': ["Choose either question mark or exclamation point, not both.",
                             "Use question mark for questions, period for statements."],
                'severity': 'medium'
            })
        
        # Check for multiple punctuation marks
        surrounding_punct = []
        for i in range(max(0, token_idx - 2), min(len(doc), token_idx + 3)):
            if doc[i].text in ['!', '?', '.', ',', ';', ':']:
                surrounding_punct.append(doc[i].text)
        
        if len(surrounding_punct) > 2:
            issues.append({
                'message': "Excessive punctuation marks may impact readability.",
                'suggestions': ["Simplify punctuation for clearer communication.",
                             "Use one appropriate punctuation mark per sentence end."],
                'severity': 'medium'
            })
        
        return issues

    def _analyze_with_regex(self, text: str, sentences: List[str]) -> List[Dict[str, Any]]:
        """Fallback regex-based analysis when NLP is unavailable."""
        errors = []
        
        for i, sentence in enumerate(sentences):
            # Basic exclamation point patterns detectable without NLP
            
            # Pattern 1: Basic exclamation point usage
            if '!' in sentence:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Exclamation points should be used sparingly in professional writing.",
                    suggestions=["Replace with a period for a more professional tone.",
                               "Use strong word choice instead of emphatic punctuation.",
                               "Consider whether the emphasis truly adds value."],
                    severity='low'
                ))
            
            # Pattern 2: Multiple consecutive exclamation points
            if re.search(r'!{2,}', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Multiple consecutive exclamation points are unprofessional.",
                    suggestions=["Use only one exclamation point for emphasis.",
                               "Consider whether emphasis is truly necessary.",
                               "Use strong, clear language instead of multiple punctuation marks."],
                    severity='high'
                ))
            
            # Pattern 3: Question-exclamation combinations
            if re.search(r'\?\!|\!\?', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Combining question marks and exclamation points is informal.",
                    suggestions=["Choose either question mark or exclamation point, not both.",
                               "Use question mark for questions, period for statements."],
                    severity='medium'
                ))
            
            # Pattern 4: Excessive exclamation points in sentence
            exclamation_count = sentence.count('!')
            if exclamation_count > 1:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Multiple exclamation points in one sentence may impact professionalism.",
                    suggestions=["Limit to one exclamation point per sentence.",
                               "Consider whether all exclamations are necessary.",
                               "Rewrite to be more direct and professional."],
                    severity='medium'
                ))
            
            # Pattern 5: Exclamation with all caps (very informal)
            if re.search(r'[A-Z]{3,}.*!|!.*[A-Z]{3,}', sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="All caps with exclamation points appears unprofessional.",
                    suggestions=["Use normal capitalization with strong word choice.",
                               "Avoid shouting-style formatting in professional writing.",
                               "Express emphasis through clear, precise language."],
                    severity='high'
                ))
        
        return errors
