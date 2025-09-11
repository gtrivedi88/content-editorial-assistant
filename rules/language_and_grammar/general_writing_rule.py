"""
General Writing Rule - Core Writing Structure Issues

"""
from typing import List, Dict, Any, Optional, Tuple, Set
import re
from ..base_rule import BaseRule

try:
    from spacy.tokens import Doc, Token, Span
except ImportError:
    Doc = None
    Token = None  
    Span = None

class GeneralWritingRule(BaseRule):
    """
    Analyzes core writing structure issues using evidence-based analysis:
    - Sentence structure: fragments, run-ons, subject-verb agreement
    - Text coherence: pronoun clarity, parallel structure, tense consistency  
    - Basic proofreading: repeated words, wordiness patterns
    - Advanced grammar: comma splices, double negatives

    """
    def __init__(self):
        """Initialize the rule with writing mistake patterns."""
        super().__init__()
        self._initialize_writing_patterns()
    
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'general_writing'
    
    def _initialize_writing_patterns(self):
        """Initialize core writing structure patterns (no duplications with specialized rules)."""
        self.writing_patterns = {
            # === BASIC PROOFREADING (not covered elsewhere) ===
            'repeated_words': re.compile(r'\b(\w+)\s+\1\b', re.IGNORECASE),
            
            # === CORE GRAMMAR STRUCTURE ===
            'double_negative': re.compile(r"\b(don't|doesn't|didn't|won't|can't|isn't|aren't|wasn't|weren't)\b.*?\b(no|nothing|nobody|nowhere|never|neither)\b", re.IGNORECASE),
            'comma_splice': re.compile(r'\w+,\s*[A-Za-z]\w*'),
            
            # === SENTENCE STRUCTURE INDICATORS ===
            'run_on_indicator': re.compile(r'\b(and|but|or|so|yet)\s+\w+.*\b(and|but|or|so|yet)\b'),
        }
    
    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for general writing mistakes:
        - Pattern-based detection for common errors
        - spaCy-enhanced analysis for complex grammar issues
        - Context-aware validation and suggestions
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        
        # Skip analysis for contexts where general writing rules don't apply
        if not self._should_analyze_writing(context):
            return errors
        
        # Fallback analysis when nlp is not available
        if not nlp:
            return self._fallback_writing_analysis(text, sentences, context)

        try:
            doc = nlp(text)
            
            # Pattern-based analysis (reliable for most issues)
            errors.extend(self._analyze_writing_patterns(text, context))
            
            # spaCy-enhanced analysis for complex grammar
            errors.extend(self._analyze_grammar_with_spacy(doc, text, context))
            
            # Sentence-level analysis
            errors.extend(self._analyze_sentence_structure(doc, text, context))
            
        except Exception as e:
            # Graceful degradation for SpaCy errors
            return self._fallback_writing_analysis(text, sentences, context)
        
        # Deduplicate generic errors to prevent multiple identical "writing issue" reports
        errors = self._deduplicate_generic_errors(errors)
        
        return errors
    
    def _should_analyze_writing(self, context: Dict[str, Any]) -> bool:
        """Check if general writing analysis is appropriate."""
        block_type = context.get('block_type', 'paragraph')
        content_type = context.get('content_type', 'general')
        
        # Skip code blocks and technical contexts where different rules apply
        if block_type in ['code_block', 'inline_code', 'literal_block']:
            return False
        
        # Skip creative content where unconventional usage might be intentional
        if content_type in ['creative', 'poetry', 'verse']:
            return False
        
        # Skip very short content like table cells
        if block_type in ['table_cell', 'table_header'] and context.get('word_count', 0) < 5:
            return False
        
        return True
    
    def _fallback_writing_analysis(self, text: str, sentences: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback writing analysis without spaCy."""
        errors = []
        
        # Pattern-based analysis works without spaCy
        errors.extend(self._analyze_writing_patterns(text, context))
        
        # Basic sentence analysis
        errors.extend(self._analyze_sentences_basic(sentences, context))
        
        return errors
    
    def _analyze_writing_patterns(self, text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze writing using regex patterns."""
        errors = []
        
        for pattern_name, pattern in self.writing_patterns.items():
            for match in pattern.finditer(text):
                evidence_score = self._calculate_pattern_evidence(pattern_name, match, text, context)
                
                if evidence_score > 0.1:
                    # Get the message - skip if None (filtered out as low-confidence generic)
                    message = self._get_contextual_writing_message(pattern_name, match, evidence_score, context)
                    if message is None:
                        continue  # Skip this error - filtered out as generic/low-confidence
                    
                    error = self._create_error(
                        sentence=self._get_sentence_for_match(match, text),
                        sentence_index=self._get_sentence_index_for_match(match, text),
                        message=message,
                        suggestions=self._generate_smart_writing_suggestions(pattern_name, match, evidence_score, context),
                        severity=self._get_writing_severity(pattern_name, evidence_score),
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(match.start(), match.end()),
                        flagged_text=match.group(),
                        violation_type=f'writing_{pattern_name}',
                        pattern_name=pattern_name
                    )
                    errors.append(error)
        
        return errors
    
    def _analyze_grammar_with_spacy(self, doc: 'Doc', text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Advanced grammar analysis using spaCy."""
        errors = []
        
        # Subject-verb disagreement analysis
        errors.extend(self._analyze_subject_verb_agreement(doc, text, context))
        
        # Sentence fragment detection
        errors.extend(self._analyze_sentence_fragments(doc, text, context))
        
        # Pronoun reference analysis
        errors.extend(self._analyze_pronoun_references(doc, text, context))
        
        # Parallel structure analysis
        errors.extend(self._analyze_parallel_structure(doc, text, context))
        
        return errors
    
    def _analyze_sentence_structure(self, doc: 'Doc', text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze overall sentence structure and flow."""
        errors = []
        
        # Run-on sentence detection
        errors.extend(self._analyze_run_on_sentences(doc, text, context))
        
        # Tense consistency analysis
        errors.extend(self._analyze_tense_consistency(doc, text, context))
        
        # Wordiness detection
        errors.extend(self._analyze_wordiness(doc, text, context))
        
        return errors
    
    def _analyze_sentences_basic(self, sentences: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Basic sentence analysis without spaCy."""
        errors = []
        
        for i, sentence in enumerate(sentences):
            # Check sentence length
            word_count = len(sentence.split())
            if word_count > 30:  # Very long sentence
                evidence_score = min(0.9, (word_count - 30) / 20.0 + 0.5)
                
                if evidence_score > 0.1:
                    error = self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"This sentence may be too long ({word_count} words) for clarity.",
                        suggestions=self._generate_length_suggestions(word_count, context),
                        severity='low' if word_count < 40 else 'medium',
                        text=sentence,
                        context=context,
                        evidence_score=evidence_score,
                        span=(0, len(sentence)),
                        flagged_text="Sentence length",
                        violation_type='writing_run_on_sentence'
                    )
                    errors.append(error)
        
        return errors

    # === ADVANCED SPACY ANALYSIS METHODS ===
    
    def _analyze_subject_verb_agreement(self, doc: 'Doc', text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze subject-verb agreement using spaCy."""
        errors = []
        
        for sent in doc.sents:
            subjects = []
            verbs = []
            
            # Find subjects and main verbs
            for token in sent:
                if token.dep_ in ['nsubj', 'nsubjpass']:
                    subjects.append(token)
                elif token.dep_ == 'ROOT' and token.pos_ == 'VERB':
                    verbs.append(token)
            
            # Check agreement for each subject-verb pair
            for subject in subjects:
                for verb in verbs:
                    if self._check_subject_verb_mismatch(subject, verb):
                        evidence_score = 0.8  # High confidence for clear grammatical errors
                        
                        error = self._create_error(
                            sentence=sent.text,
                            sentence_index=self._get_sentence_index_for_span(sent, text),
                            message=f"Subject-verb disagreement: '{subject.text}' and '{verb.text}' don't agree.",
                            suggestions=self._generate_agreement_suggestions(subject, verb),
                            severity='medium',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(min(subject.idx, verb.idx), max(subject.idx + len(subject.text), verb.idx + len(verb.text))),
                            flagged_text=f"{subject.text} ... {verb.text}",
                            violation_type='writing_subject_verb_disagreement',
                            subject=subject.text,
                            verb=verb.text
                        )
                        errors.append(error)
        
        return errors
    
    def _analyze_sentence_fragments(self, doc: 'Doc', text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect sentence fragments using spaCy."""
        errors = []
        
        for sent in doc.sents:
            # Skip very short sentences that might be intentional
            if len(sent) < 3:
                continue
            
            # Look for sentences without main verbs
            has_main_verb = any(token.dep_ == 'ROOT' and token.pos_ == 'VERB' for token in sent)
            has_subject = any(token.dep_ in ['nsubj', 'nsubjpass'] for token in sent)
            
            if not has_main_verb or not has_subject:
                # Don't flag fragments in certain contexts
                if self._is_intentional_fragment(sent, context):
                    continue
                
                evidence_score = 0.7  # Good evidence for fragments
                
                error = self._create_error(
                    sentence=sent.text,
                    sentence_index=self._get_sentence_index_for_span(sent, text),
                    message="This appears to be a sentence fragment.",
                    suggestions=self._generate_fragment_suggestions(sent, has_main_verb, has_subject),
                    severity='medium',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=(sent.start_char, sent.end_char),
                    flagged_text=sent.text,
                    violation_type='writing_sentence_fragment'
                )
                errors.append(error)
        
        return errors
    
    def _analyze_pronoun_references(self, doc: 'Doc', text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze unclear pronoun references."""
        errors = []
        
        pronouns = ['it', 'this', 'that', 'they', 'them', 'these', 'those']
        
        for sent in doc.sents:
            for token in sent:
                if token.text.lower() in pronouns and token.pos_ == 'PRON':
                    # Check if pronoun reference is unclear
                    clarity_score = self._assess_pronoun_clarity(token, sent, doc)
                    
                    if clarity_score > 0.1:
                        error = self._create_error(
                            sentence=sent.text,
                            sentence_index=self._get_sentence_index_for_span(sent, text),
                            message=f"The pronoun '{token.text}' may have an unclear reference.",
                            suggestions=self._generate_pronoun_suggestions(token),
                            severity='low',
                            text=text,
                            context=context,
                            evidence_score=clarity_score,
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text,
                            violation_type='writing_unclear_pronoun'
                        )
                        errors.append(error)
        
        return errors
    
    def _analyze_parallel_structure(self, doc: 'Doc', text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze parallel structure in lists and series."""
        errors = []
        
        # Look for coordinating conjunctions that might indicate lists
        for sent in doc.sents:
            conjunctions = [token for token in sent if token.text.lower() in ['and', 'or'] and token.pos_ == 'CCONJ']
            
            for conj in conjunctions:
                parallel_score = self._assess_parallel_structure(conj, sent)
                
                if parallel_score > 0.1:
                    error = self._create_error(
                        sentence=sent.text,
                        sentence_index=self._get_sentence_index_for_span(sent, text),
                        message="This sentence may have parallel structure issues.",
                        suggestions=["Ensure items in series use consistent grammatical structure.", "Check that verb forms match across coordinated elements."],
                        severity='low',
                        text=text,
                        context=context,
                        evidence_score=parallel_score,
                        span=(sent.start_char, sent.end_char),
                        flagged_text=sent.text,
                        violation_type='writing_parallel_structure'
                    )
                    errors.append(error)
        
        return errors
    
    def _analyze_run_on_sentences(self, doc: 'Doc', text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect run-on sentences using spaCy."""
        errors = []
        
        for sent in doc.sents:
            # Count independent clauses
            clause_count = self._count_independent_clauses(sent)
            word_count = len([token for token in sent if token.is_alpha])
            
            # Evidence based on clause count and word count
            evidence_score = 0.0
            
            if clause_count > 3:  # Too many clauses
                evidence_score += 0.4
            elif clause_count > 2:
                evidence_score += 0.2
            
            if word_count > 30:  # Very long
                evidence_score += 0.3
            elif word_count > 25:
                evidence_score += 0.1
            
            if evidence_score > 0.1:
                error = self._create_error(
                    sentence=sent.text,
                    sentence_index=self._get_sentence_index_for_span(sent, text),
                    message=f"This sentence may be too long or complex ({word_count} words, {clause_count} clauses).",
                    suggestions=self._generate_run_on_suggestions(clause_count, word_count),
                    severity='low' if evidence_score < 0.5 else 'medium',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=(sent.start_char, sent.end_char),
                    flagged_text=sent.text,
                    violation_type='writing_run_on_sentence',
                    word_count=word_count,
                    clause_count=clause_count
                )
                errors.append(error)
        
        return errors
    
    def _analyze_tense_consistency(self, doc: 'Doc', text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze tense consistency across sentences."""
        errors = []
        
        # Collect tenses from all sentences
        sentence_tenses = []
        for sent in doc.sents:
            tense = self._determine_primary_tense(sent)
            if tense:
                sentence_tenses.append((sent, tense))
        
        # Check for inconsistencies
        if len(sentence_tenses) > 2:
            tense_counts = {}
            for _, tense in sentence_tenses:
                tense_counts[tense] = tense_counts.get(tense, 0) + 1
            
            # If there's significant tense mixing
            if len(tense_counts) > 1:
                primary_tense = max(tense_counts.items(), key=lambda x: x[1])[0]
                inconsistent_sentences = [(sent, tense) for sent, tense in sentence_tenses if tense != primary_tense]
                
                # Only flag if inconsistency is significant
                if len(inconsistent_sentences) > 0 and len(inconsistent_sentences) < len(sentence_tenses) * 0.8:
                    for sent, inconsistent_tense in inconsistent_sentences:
                        evidence_score = 0.4  # Medium evidence for tense inconsistency
                        
                        error = self._create_error(
                            sentence=sent.text,
                            sentence_index=self._get_sentence_index_for_span(sent, text),
                            message=f"This sentence uses {inconsistent_tense} tense while most of the text uses {primary_tense}.",
                            suggestions=[f"Consider changing to {primary_tense} tense for consistency.", "Check if tense change is intentional and necessary."],
                            severity='low',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(sent.start_char, sent.end_char),
                            flagged_text=sent.text,
                            violation_type='writing_tense_inconsistency',
                            current_tense=inconsistent_tense,
                            expected_tense=primary_tense
                        )
                        errors.append(error)
        
        return errors
    
    def _analyze_wordiness(self, doc: 'Doc', text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect wordy phrases and unnecessary complexity."""
        errors = []
        
        wordy_phrases = {
            'in order to': 'to',
            'due to the fact that': 'because',
            'at this point in time': 'now',
            'for the purpose of': 'for',
            'in the event that': 'if',
            'with regard to': 'about',
            'in spite of the fact that': 'although'
        }
        
        text_lower = text.lower()
        for wordy_phrase, concise_version in wordy_phrases.items():
            if wordy_phrase in text_lower:
                evidence_score = 0.6  # Good evidence for wordiness
                
                # Find the actual position in original text
                start = text_lower.find(wordy_phrase)
                end = start + len(wordy_phrase)
                
                error = self._create_error(
                    sentence=self._get_sentence_for_position(start, text),
                    sentence_index=0,
                    message=f"Consider replacing '{wordy_phrase}' with '{concise_version}' for conciseness.",
                    suggestions=[f"Replace with '{concise_version}'.", "Use more concise phrasing.", "Eliminate unnecessary words."],
                    severity='low',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=(start, end),
                    flagged_text=text[start:end],
                    violation_type='writing_wordiness',
                    wordy_phrase=wordy_phrase,
                    concise_version=concise_version
                )
                errors.append(error)
        
        return errors

    # === EVIDENCE CALCULATION ===
    
    def _calculate_pattern_evidence(self, pattern_name: str, match: re.Match, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence for pattern-based writing violations."""
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        # Check if this is in a context where the "error" might be intentional
        if self._is_intentional_usage(pattern_name, match, text, context):
            return 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        base_scores = {
            # High confidence patterns
            'repeated_words': 0.9,           # Almost always an error
            'double_negative': 0.8,          # Usually an error in formal writing
            'comma_splice': 0.7,             # Clear grammar error
            
            # Medium confidence patterns  
            'run_on_indicator': 0.4,         # Might be acceptable depending on context
        }
        
        evidence_score = base_scores.get(pattern_name, 0.5)
        
        # === STEP 2: PATTERN-SPECIFIC ADJUSTMENTS ===
        evidence_score = self._apply_pattern_specific_adjustments(pattern_name, match, text, evidence_score, context)
        
        # === STEP 3: CONTEXT CLUES ===
        content_type = context.get('content_type', 'general')
        if content_type == 'formal':
            evidence_score += 0.1  # More strict for formal writing
        elif content_type == 'technical':
            evidence_score += 0.05  # Slightly more strict for technical writing
        elif content_type == 'conversational':
            evidence_score -= 0.1  # More permissive for conversational tone
        
        return max(0.0, min(1.0, evidence_score))
    
    def _apply_pattern_specific_adjustments(self, pattern_name: str, match: re.Match, text: str, evidence_score: float, context: Dict[str, Any]) -> float:
        """Apply pattern-specific evidence adjustments."""
        matched_text = match.group().lower()
        
        # Repeated words - check if it's intentional emphasis
        if pattern_name == 'repeated_words':
            if len(matched_text.split()) == 2 and matched_text.split()[0] in ['very', 'so', 'really', 'quite']:
                evidence_score -= 0.3  # Might be intentional emphasis
        
        # Double negative - less problematic in conversational contexts
        elif pattern_name == 'double_negative':
            if context.get('content_type') == 'conversational':
                evidence_score -= 0.2
        
        # Comma splice - check if it might be acceptable stylistic choice
        elif pattern_name == 'comma_splice':
            # Very short clauses might be acceptable
            if len(matched_text) < 20:
                evidence_score -= 0.1
        
        # Run-on indicators - check context
        elif pattern_name == 'run_on_indicator':
            # In lists or procedural content, coordination is normal
            if context.get('block_type') in ['list_item', 'procedural']:
                evidence_score -= 0.3
        
        return evidence_score
    

    # === HELPER METHODS ===
    
    def _is_intentional_usage(self, pattern_name: str, match: re.Match, text: str, context: Dict[str, Any]) -> bool:
        """Check if apparent error might be intentional."""
        # Creative writing might intentionally use fragments, repetition, etc.
        if context.get('content_type') in ['creative', 'poetry', 'dialogue']:
            return True
        
        # Quotes preserve original usage
        if context.get('block_type') in ['quote', 'blockquote']:
            return True
        
        # Some patterns might be intentional in certain contexts
        if pattern_name == 'repeated_words':
            # Check for intentional emphasis
            repeated_word = match.group().split()[0].lower()
            if repeated_word in ['very', 'so', 'really', 'quite', 'yes', 'no']:
                return True
        
        return False
    
    def _check_subject_verb_mismatch(self, subject: 'Token', verb: 'Token') -> bool:
        """Check if subject and verb disagree."""
        # Simplified check - in a full implementation, this would be more complex
        subject_number = self._get_number(subject)
        verb_number = self._get_number(verb)
        
        return subject_number != verb_number and subject_number != 'unknown' and verb_number != 'unknown'
    
    def _get_number(self, token: 'Token') -> str:
        """Get grammatical number (singular/plural) of a token."""
        if token.tag_ in ['NNS', 'NNPS']:  # Plural nouns
            return 'plural'
        elif token.tag_ in ['NN', 'NNP']:  # Singular nouns
            return 'singular'
        elif token.tag_ in ['VBZ']:  # Third person singular verbs
            return 'singular'
        elif token.tag_ in ['VBP']:  # Non-third person singular verbs
            return 'plural'
        else:
            return 'unknown'
    
    def _is_intentional_fragment(self, sent: 'Span', context: Dict[str, Any]) -> bool:
        """Check if sentence fragment might be intentional."""
        # Headlines, titles, list items might be intentional fragments
        block_type = context.get('block_type', '')
        if block_type in ['heading', 'title', 'list_item']:
            return True
        
        # Very short sentences might be intentional
        if len(sent) < 4:
            return True
        
        # Exclamations might be intentional
        if sent.text.endswith('!'):
            return True
        
        return False
    
    def _assess_pronoun_clarity(self, pronoun: 'Token', sent: 'Span', doc: 'Doc') -> float:
        """Assess if pronoun reference is unclear."""
        # Simple heuristic - check if there are multiple possible antecedents
        if pronoun.text.lower() in ['it', 'this', 'that']:
            # Count nearby nouns that could be antecedents
            nearby_nouns = []
            for token in sent:
                if token.pos_ in ['NOUN', 'PROPN'] and token != pronoun:
                    nearby_nouns.append(token)
            
            if len(nearby_nouns) > 2:
                return 0.4  # Potential ambiguity
            elif len(nearby_nouns) == 0:
                return 0.6  # No clear antecedent
        
        return 0.1  # Probably clear
    
    def _assess_parallel_structure(self, conjunction: 'Token', sent: 'Span') -> float:
        """Assess parallel structure around conjunction."""
        # Simplified analysis - check POS tags before and after conjunction
        conj_index = conjunction.i - sent.start
        
        if conj_index > 0 and conj_index < len(sent) - 1:
            before_pos = sent[conj_index - 1].pos_
            after_pos = sent[conj_index + 1].pos_
            
            if before_pos != after_pos:
                return 0.3  # Possible parallel structure issue
        
        return 0.1  # Probably fine
    
    def _count_independent_clauses(self, sent: 'Span') -> int:
        """Count independent clauses in a sentence."""
        # Count coordinating conjunctions and semicolons as clause separators
        clause_count = 1  # At least one clause
        
        for token in sent:
            if token.text.lower() in ['and', 'but', 'or', 'so', 'yet'] and token.pos_ == 'CCONJ':
                clause_count += 1
            elif token.text == ';':
                clause_count += 1
        
        return clause_count
    
    def _determine_primary_tense(self, sent: 'Span') -> Optional[str]:
        """Determine the primary tense of a sentence."""
        verbs = [token for token in sent if token.pos_ == 'VERB']
        
        if not verbs:
            return None
        
        # Simple tense detection based on tags
        past_count = sum(1 for verb in verbs if verb.tag_ in ['VBD', 'VBN'])
        present_count = sum(1 for verb in verbs if verb.tag_ in ['VBZ', 'VBP', 'VBG'])
        future_count = sum(1 for verb in verbs if verb.lemma_ in ['will', 'shall'])
        
        if future_count > 0:
            return 'future'
        elif past_count > present_count:
            return 'past'
        else:
            return 'present'
    
    def _get_context_window(self, match: re.Match, text: str, window_size: int) -> str:
        """Get context window around a match."""
        start = max(0, match.start() - window_size)
        end = min(len(text), match.end() + window_size)
        return text[start:end]
    
    def _get_sentence_for_match(self, match: re.Match, text: str) -> str:
        """Get sentence containing the match."""
        # Find sentence boundaries
        before = text[:match.start()]
        after = text[match.end():]
        
        sent_start = before.rfind('.')
        if sent_start == -1:
            sent_start = 0
        else:
            sent_start += 1
        
        sent_end = after.find('.')
        if sent_end == -1:
            sent_end = len(text)
        else:
            sent_end = match.end() + sent_end + 1
        
        return text[sent_start:sent_end].strip()
    
    def _get_sentence_index_for_match(self, match: re.Match, text: str) -> int:
        """Get sentence index for a match."""
        return text[:match.start()].count('.')
    
    def _get_sentence_index_for_span(self, span: 'Span', text: str) -> int:
        """Get sentence index for a spaCy span."""
        return text[:span.start_char].count('.')
    
    def _get_sentence_for_position(self, position: int, text: str) -> str:
        """Get sentence at a specific position."""
        before = text[:position]
        after = text[position:]
        
        sent_start = before.rfind('.')
        if sent_start == -1:
            sent_start = 0
        else:
            sent_start += 1
        
        sent_end = after.find('.')
        if sent_end == -1:
            sent_end = len(text)
        else:
            sent_end = position + sent_end + 1
        
        return text[sent_start:sent_end].strip()
    
    def _get_writing_severity(self, pattern_name: str, evidence_score: float) -> str:
        """Determine severity based on pattern and evidence."""
        # Grammar errors are more severe
        if pattern_name in ['double_negative', 'comma_splice', 'subject_verb_disagreement']:
            return 'medium' if evidence_score > 0.7 else 'low'
        
        # Clear proofreading errors
        if pattern_name == 'repeated_words':
            return 'medium' if evidence_score > 0.8 else 'low'
        
        # Structural issues are usually low severity
        return 'low'

    # === SMART MESSAGING ===

    def _get_contextual_writing_message(self, pattern_name: str, match: re.Match, evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for writing violations."""
        confidence_phrase = "clearly has" if evidence_score > 0.8 else ("likely has" if evidence_score > 0.6 else "may have")
        matched_text = match.group()
        
        messages = {
            'repeated_words': f"This text {confidence_phrase} repeated words: '{matched_text}'.",
            'double_negative': f"This text {confidence_phrase} a double negative that may be confusing.",
            'comma_splice': f"This sentence {confidence_phrase} a comma splice - independent clauses should be separated properly.",
            'run_on_indicator': f"This sentence {confidence_phrase} multiple coordinating conjunctions that may indicate a run-on structure."
        }
        
        # Only return generic message for unknown patterns with high confidence
        if pattern_name not in messages:
            if evidence_score > 0.6:  # Only report high-confidence unknown issues
                return f"This text {confidence_phrase} a writing issue."
            else:
                return None  # Skip low-confidence unknown issues
        
        return messages.get(pattern_name)

    def _generate_smart_writing_suggestions(self, pattern_name: str, match: re.Match, evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for writing violations."""
        matched_text = match.group()
        
        suggestion_map = {
            'repeated_words': [
                f"Remove the repeated word in '{matched_text}'.",
                "Check for accidental word duplication.", 
                "Proofread for repeated words."
            ],
            'double_negative': [
                "Use a single negative for clarity.",
                "Rewrite to avoid double negatives.",
                "Consider the intended meaning and use appropriate negation."
            ],
            'comma_splice': [
                "Use a period to separate the independent clauses.",
                "Use a semicolon if the clauses are closely related.",
                "Add a coordinating conjunction after the comma."
            ],
            'run_on_indicator': [
                "Consider breaking this sentence into smaller parts.",
                "Use periods to separate independent thoughts.",
                "Limit coordinating conjunctions to avoid run-on sentences."
            ]
        }
        
        suggestions = suggestion_map.get(pattern_name, ["Fix the writing issue."])
        
        # Add context-specific advice
        if evidence_score > 0.8:
            suggestions.append("This issue should be corrected for clarity.")
        elif evidence_score > 0.6:
            suggestions.append("Consider fixing this for better writing quality.")
        
        return suggestions[:3]
    
    def _generate_agreement_suggestions(self, subject: 'Token', verb: 'Token') -> List[str]:
        """Generate suggestions for subject-verb agreement."""
        return [
            f"Check agreement between '{subject.text}' and '{verb.text}'.",
            "Singular subjects need singular verbs; plural subjects need plural verbs.",
            "Consider the grammatical number of the subject."
        ]
    
    def _generate_fragment_suggestions(self, sent: 'Span', has_verb: bool, has_subject: bool) -> List[str]:
        """Generate suggestions for sentence fragments."""
        suggestions = []
        
        if not has_verb:
            suggestions.append("Add a main verb to complete the sentence.")
        if not has_subject:
            suggestions.append("Add a subject to complete the sentence.")
        
        suggestions.extend([
            "Ensure the sentence expresses a complete thought.",
            "Consider combining with another sentence if appropriate."
        ])
        
        return suggestions[:3]
    
    def _generate_pronoun_suggestions(self, pronoun: 'Token') -> List[str]:
        """Generate suggestions for unclear pronouns."""
        return [
            f"Clarify what '{pronoun.text}' refers to.",
            "Consider replacing the pronoun with a specific noun.",
            "Ensure pronoun references are clear to readers."
        ]
    
    def _generate_run_on_suggestions(self, clause_count: int, word_count: int) -> List[str]:
        """Generate suggestions for run-on sentences."""
        suggestions = []
        
        if clause_count > 3:
            suggestions.append(f"Break this sentence into smaller parts ({clause_count} clauses detected).")
        if word_count > 30:
            suggestions.append(f"Consider shortening this {word_count}-word sentence.")
        
        suggestions.extend([
            "Use periods to separate independent thoughts.",
            "Consider using bullet points for complex information."
        ])
        
        return suggestions[:3]
    
    def _generate_length_suggestions(self, word_count: int, context: Dict[str, Any]) -> List[str]:
        """Generate suggestions for sentence length."""
        return [
            f"Consider breaking this {word_count}-word sentence into shorter ones.",
            "Aim for 15-20 words per sentence for better readability.",
            "Use periods to separate independent ideas."
        ]
    
    def _deduplicate_generic_errors(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate generic errors to prevent spam."""
        if not errors:
            return errors
        
        # Group errors by their core identity (message + violation_type)
        error_groups = {}
        
        for error in errors:
            message = error.get('message', '')
            violation_type = error.get('violation_type', '')
            
            # Create a key for grouping similar errors
            key = f"{message}|{violation_type}"
            
            if key not in error_groups:
                error_groups[key] = []
            error_groups[key].append(error)
        
        deduped_errors = []
        
        for key, group in error_groups.items():
            # For generic "writing issue" errors, only keep one per unique text segment
            if "writing issue" in key.lower():
                # Keep unique text segments only
                seen_texts = set()
                for error in group:
                    text_segment = error.get('flagged_text', '')[:50]  # First 50 chars
                    if text_segment not in seen_texts:
                        seen_texts.add(text_segment)
                        deduped_errors.append(error)
                        # Limit to max 2 generic errors per document
                        if len([e for e in deduped_errors if "writing issue" in e.get('message', '').lower()]) >= 2:
                            break
            else:
                # For specific errors, keep all instances (they're legitimately different)
                deduped_errors.extend(group)
        
        return deduped_errors
