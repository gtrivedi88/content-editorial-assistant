"""
Headings Rule (Enhanced with Evidence-Based Analysis)
Based on IBM Style Guide topic: "Headings"
Enhanced to follow evidence-based rule development methodology for zero false positives.
"""
from typing import List, Dict, Any, Optional
from .base_structure_rule import BaseStructureRule
import re

try:
    from spacy.tokens import Doc, Token
except ImportError:
    Doc = None
    Token = None

class HeadingsRule(BaseStructureRule):
    """
    Checks for style issues in headings using evidence-based analysis with surgical precision.
    Implements rule-specific evidence calculation for optimal false positive reduction.
    
    Violations detected:
    - Headings ending with periods
    - Incorrect capitalization (title case vs sentence case)
    - Question-style headings
    - Weak lead-in words (gerunds in non-procedural content)
    """
    
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'headings'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes headings for style violations using evidence-based scoring.
        Each potential violation gets nuanced evidence assessment for precision.
        """
        errors = []
        if not context or context.get('block_type') != 'heading' or not nlp:
            return errors
        
        topic_type = context.get('topic_type', 'Concept')

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            
            # === EVIDENCE-BASED ANALYSIS 1: Period Endings ===
            if sentence.strip().endswith('.'):
                evidence_score = self._calculate_period_ending_evidence(
                    sentence, doc, text, context
                )
                
                if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                    errors.append(self._create_error(
                        sentence=sentence, sentence_index=i,
                        message=self._get_contextual_message('period_ending', evidence_score, context),
                        suggestions=self._generate_smart_suggestions('period_ending', evidence_score, context),
                        severity='medium',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(len(sentence) - 1, len(sentence)),
                        flagged_text='.'
                    ))

            # === EVIDENCE-BASED ANALYSIS 2: Capitalization Style ===
            words = sentence.split()
            if len(words) > 1:
                capitalization_issues = self._find_capitalization_issues(sentence, doc, nlp)
                if capitalization_issues:
                    evidence_score = self._calculate_capitalization_evidence(
                        sentence, capitalization_issues, doc, text, context
                    )
                    
                    if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                        errors.append(self._create_error(
                            sentence=sentence, sentence_index=i,
                            message=self._get_contextual_message('capitalization', evidence_score, context),
                            suggestions=self._generate_smart_suggestions('capitalization', evidence_score, context),
                            severity='low',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(0, len(sentence)),
                            flagged_text=sentence
                        ))

            # === EVIDENCE-BASED ANALYSIS 3: Question Style ===
            if sentence.strip().endswith('?'):
                evidence_score = self._calculate_question_style_evidence(
                    sentence, doc, text, context
                )
                
                if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                    errors.append(self._create_error(
                        sentence=sentence, sentence_index=i,
                        message=self._get_contextual_message('question_style', evidence_score, context),
                        suggestions=self._generate_smart_suggestions('question_style', evidence_score, context),
                        severity='low',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,
                        span=(len(sentence) - 1, len(sentence)),
                        flagged_text='?'
                    ))

            # === EVIDENCE-BASED ANALYSIS 4: Gerund Lead-ins ===
            if doc and len(doc) > 0:
                first_token = doc[0]
                if first_token.tag_ == 'VBG':  # Gerund detected
                    evidence_score = self._calculate_gerund_evidence(
                        sentence, first_token, topic_type, doc, text, context
                    )
                    
                    if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                        errors.append(self._create_error(
                            sentence=sentence, sentence_index=i,
                            message=self._get_contextual_message('gerund_leadin', evidence_score, context, topic_type=topic_type),
                            suggestions=self._generate_smart_suggestions('gerund_leadin', evidence_score, context, first_token=first_token),
                            severity='low',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(first_token.idx, first_token.idx + len(first_token.text)),
                            flagged_text=first_token.text
                        ))
        return errors

    # === EVIDENCE CALCULATION METHODS ===

    def _calculate_period_ending_evidence(self, sentence: str, doc: 'Doc', text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for potential period ending violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            sentence: Heading text
            doc: SpaCy document
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === ZERO FALSE POSITIVE GUARDS ===
        # CRITICAL: Apply rule-specific guards FIRST to eliminate common exceptions
        
        # Kill evidence immediately for contexts where this specific rule should never apply
        if not context or context.get('block_type') != 'heading':
            return 0.0  # Only apply to heading blocks
        
        # Don't flag headings in quoted examples
        if self._is_heading_in_actual_quotes(sentence, text, context):
            return 0.0  # Quoted examples are not heading errors
        
        # Don't flag headings in technical documentation contexts with approved patterns
        if self._is_heading_in_technical_context(sentence, text, context):
            return 0.0  # Technical docs may use different conventions
        
        # Don't flag headings in citation or reference context
        if self._is_heading_in_citation_context(sentence, text, context):
            return 0.0  # Academic papers, documentation references, etc.
        
        # Apply inherited zero false positive guards
        violation = {'sentence': sentence, 'text': sentence}
        if self._apply_zero_false_positive_guards_structure(violation, context):
            return 0.0
        
        # Special guard: Abbreviations and acronyms ending with periods
        if self._is_abbreviation_ending(sentence):
            return 0.0
        
        # Special guard: Sentence fragments that are actually complete thoughts
        if self._is_legitimate_sentence_ending(sentence, doc):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_period_ending_base_evidence_score(sentence, doc, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this heading
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        # Check if it's a single word heading (might be abbreviation)
        words = sentence.strip().split()
        if len(words) == 1:
            evidence_score -= 0.3  # Could be abbreviation
        
        # Check if heading contains multiple sentences (might be legitimate)
        sentence_count = len([s for s in sentence.split('.') if s.strip()])
        if sentence_count > 1:
            evidence_score -= 0.4  # Multiple sentences might legitimately end with period
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._adjust_evidence_for_structure_context(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        # Content type adjustments
        content_type = context.get('content_type', 'general')
        if content_type in ['academic', 'legal']:
            evidence_score -= 0.1  # Formal content sometimes uses periods in headings
        elif content_type in ['marketing', 'creative']:
            evidence_score += 0.1  # Creative content should avoid period in headings
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_period_endings(evidence_score, sentence, context)
        
        # Period ending-specific final adjustments (moderate to avoid evidence inflation)
        evidence_score += 0.05  # Period endings are generally inappropriate but context-dependent
        
        return max(0.0, min(1.0, evidence_score))

    def _calculate_capitalization_evidence(self, sentence: str, capitalization_issues: List[str], 
                                         doc: 'Doc', text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for potential capitalization violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            sentence: Heading text
            capitalization_issues: List of improperly capitalized words
            doc: SpaCy document
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === ZERO FALSE POSITIVE GUARDS ===
        # CRITICAL: Apply rule-specific guards FIRST to eliminate common exceptions
        
        # Kill evidence immediately for contexts where this specific rule should never apply
        if not context or context.get('block_type') != 'heading':
            return 0.0  # Only apply to heading blocks
        
        # Don't flag headings in quoted examples
        if self._is_heading_in_actual_quotes(sentence, text, context):
            return 0.0  # Quoted examples are not heading errors
        
        # Don't flag headings in technical documentation contexts with approved patterns
        if self._is_heading_in_technical_context(sentence, text, context):
            return 0.0  # Technical docs may use different conventions
        
        # Don't flag headings in citation or reference context
        if self._is_heading_in_citation_context(sentence, text, context):
            return 0.0  # Academic papers, documentation references, etc.
        
        # Apply inherited zero false positive guards
        violation = {'sentence': sentence, 'text': sentence}
        if self._apply_zero_false_positive_guards_structure(violation, context):
            return 0.0
        
        # Special guard: Technical terms and brand names
        if self._has_legitimate_title_case(sentence, capitalization_issues):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_capitalization_base_evidence_score(sentence, capitalization_issues, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this heading
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        # Check for proper nouns and named entities
        for word in capitalization_issues:
            if doc:
                word_doc = doc.vocab[word]
                # Reduce evidence if words are likely proper nouns
                if hasattr(word_doc, 'is_title') and word_doc.is_title:
                    evidence_score -= 0.1
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._adjust_evidence_for_structure_context(evidence_score, context)
        
        # Heading level adjustments
        heading_level = context.get('block_level', 1)
        if heading_level == 1:  # H1 headings are most visible
            evidence_score += 0.1
        elif heading_level >= 4:  # Lower level headings less critical
            evidence_score -= 0.1
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        # Content type adjustments
        content_type = context.get('content_type', 'general')
        if content_type == 'marketing':
            evidence_score += 0.2  # Marketing should follow clear style guidelines
        elif content_type == 'technical':
            evidence_score -= 0.1  # Technical content might have technical terms
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_capitalization(evidence_score, sentence, capitalization_issues, context)
        
        # Capitalization-specific final adjustments (moderate to avoid evidence inflation)
        evidence_score += 0.05  # Capitalization consistency is important but context-dependent
        
        return max(0.0, min(1.0, evidence_score))

    def _calculate_question_style_evidence(self, sentence: str, doc: 'Doc', text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for potential question-style heading violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            sentence: Heading text
            doc: SpaCy document  
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === ZERO FALSE POSITIVE GUARDS ===
        # CRITICAL: Apply rule-specific guards FIRST to eliminate common exceptions
        
        # Kill evidence immediately for contexts where this specific rule should never apply
        if not context or context.get('block_type') != 'heading':
            return 0.0  # Only apply to heading blocks
        
        # Don't flag headings in quoted examples
        if self._is_heading_in_actual_quotes(sentence, text, context):
            return 0.0  # Quoted examples are not heading errors
        
        # Don't flag headings in technical documentation contexts with approved patterns
        if self._is_heading_in_technical_context(sentence, text, context):
            return 0.0  # Technical docs may use different conventions
        
        # Don't flag headings in citation or reference context
        if self._is_heading_in_citation_context(sentence, text, context):
            return 0.0  # Academic papers, documentation references, etc.
        
        # Apply inherited zero false positive guards
        violation = {'sentence': sentence, 'text': sentence}
        if self._apply_zero_false_positive_guards_structure(violation, context):
            return 0.0
        
        # Special guard: FAQ sections and help content
        if self._is_legitimate_question_heading(sentence, text, context):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_question_style_base_evidence_score(sentence, doc, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this heading
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        # Check question type - some questions more acceptable than others
        if doc and len(doc) > 0:
            first_word = doc[0].text.lower()
            
            # Direct questions (what, how, why) in user-facing docs might be acceptable
            if first_word in ['what', 'how', 'why', 'when', 'where']:
                evidence_score -= 0.2
            
            # Yes/no questions less acceptable
            elif first_word in ['is', 'are', 'can', 'will', 'do', 'does']:
                evidence_score += 0.1
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._adjust_evidence_for_structure_context(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        # Content type adjustments
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        
        if content_type in ['user_guide', 'help', 'faq']:
            evidence_score -= 0.3  # User-facing content more accepting of questions
        elif content_type in ['technical', 'api', 'reference']:
            evidence_score += 0.2  # Technical content should avoid questions
        
        if audience in ['beginner', 'general']:
            evidence_score -= 0.2  # Questions might help beginner audiences
        elif audience in ['expert', 'developer']:
            evidence_score += 0.1  # Expert audiences prefer direct statements
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_question_style(evidence_score, sentence, context)
        
        # Question style-specific final adjustments (moderate to avoid evidence inflation)
        evidence_score += 0.05  # Question headings are generally inappropriate but context-dependent
        
        return max(0.0, min(1.0, evidence_score))

    def _calculate_gerund_evidence(self, sentence: str, first_token: 'Token', topic_type: str,
                                 doc: 'Doc', text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for potential gerund lead-in violations.
        
        Higher scores indicate stronger evidence of an actual error.
        Lower scores indicate acceptable usage or ambiguous cases.
        
        Args:
            sentence: Heading text
            first_token: First token (gerund)
            topic_type: Topic type (Concept, Procedure, Reference)
            doc: SpaCy document
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no evidence) to 1.0 (strong evidence)
        """
        
        # === ZERO FALSE POSITIVE GUARDS ===
        # CRITICAL: Apply rule-specific guards FIRST to eliminate common exceptions
        
        # Kill evidence immediately for contexts where this specific rule should never apply
        if not context or context.get('block_type') != 'heading':
            return 0.0  # Only apply to heading blocks
        
        # Don't flag headings in quoted examples
        if self._is_heading_in_actual_quotes(sentence, text, context):
            return 0.0  # Quoted examples are not heading errors
        
        # Don't flag headings in technical documentation contexts with approved patterns
        if self._is_heading_in_technical_context(sentence, text, context):
            return 0.0  # Technical docs may use different conventions
        
        # Don't flag headings in citation or reference context
        if self._is_heading_in_citation_context(sentence, text, context):
            return 0.0  # Academic papers, documentation references, etc.
        
        # Apply inherited zero false positive guards
        violation = {'sentence': sentence, 'text': sentence}
        if self._apply_zero_false_positive_guards_structure(violation, context):
            return 0.0
        
        # Special guard: Procedural content allows gerunds
        if topic_type == 'Procedure':
            return 0.0
        
        # Special guard: Legitimate gerund usage in specific contexts
        if self._is_legitimate_gerund_heading(sentence, first_token, context):
            return 0.0
        
        # === STEP 1: DYNAMIC BASE EVIDENCE ASSESSMENT ===
        # REFINED: Set base score based on violation specificity
        evidence_score = self._get_gerund_base_evidence_score(sentence, first_token, topic_type, context)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this heading
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        # Check gerund type - some more acceptable than others
        gerund_lemma = first_token.lemma_.lower()
        
        # Common weak gerunds
        weak_gerunds = ['understanding', 'getting', 'learning', 'knowing', 'using']
        if gerund_lemma in weak_gerunds:
            evidence_score += 0.2
        
        # More acceptable gerunds
        acceptable_gerunds = ['configuring', 'installing', 'troubleshooting', 'debugging']
        if gerund_lemma in acceptable_gerunds:
            evidence_score -= 0.2
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._adjust_evidence_for_structure_context(evidence_score, context)
        
        # Topic type adjustments
        if topic_type == 'Concept':
            evidence_score += 0.2  # Concept topics should avoid gerunds
        elif topic_type == 'Reference':
            evidence_score += 0.1  # Reference topics prefer direct statements
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        # Content type adjustments
        content_type = context.get('content_type', 'general')
        if content_type in ['procedural', 'tutorial']:
            evidence_score -= 0.3  # Procedural content more accepting of gerunds
        elif content_type in ['reference', 'api']:
            evidence_score += 0.2  # Reference content should be direct
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_gerunds(evidence_score, sentence, first_token, context)
        
        # Gerund-specific final adjustments (moderate to avoid evidence inflation)
        evidence_score += 0.05  # Gerund headings can be weak but context-dependent
        
        return max(0.0, min(1.0, evidence_score))

    # === HELPER METHODS FOR VIOLATION DETECTION ===

    def _find_capitalization_issues(self, sentence: str, doc: 'Doc', nlp) -> List[str]:
        """Find words that are incorrectly capitalized in title case."""
        words = sentence.split()
        if len(words) <= 1:
            return []
        
        capitalized_words = []
        for word in words[1:]:  # Skip first word
            if word.istitle():
                # Check if this individual word should be excepted
                if self._is_excepted(word):
                    continue
                
                # Use spaCy to check if this word is a proper noun
                word_doc = nlp(word)
                if word_doc and len(word_doc) > 0:
                    is_proper_noun = (word_doc[0].pos_ == 'PROPN' or 
                                    any(ent.text == word for ent in word_doc.ents))
                    if not is_proper_noun:
                        capitalized_words.append(word)
                else:
                    # If we can't analyze with spaCy, be conservative and flag it
                    capitalized_words.append(word)
        
        return capitalized_words

    def _is_excepted(self, text: str) -> bool:
        """Check if text is in exception list."""
        # Common exceptions that should be capitalized
        exceptions = {
            'API', 'SDK', 'HTTP', 'HTTPS', 'JSON', 'XML', 'HTML', 'CSS', 'SQL',
            'REST', 'SOAP', 'URL', 'URI', 'UI', 'UX', 'AI', 'ML', 'CI', 'CD',
            'AWS', 'GCP', 'IBM', 'Microsoft', 'Google', 'Apple', 'Oracle',
            'GitHub', 'GitLab', 'Docker', 'Kubernetes', 'Node.js', 'React',
            'Vue.js', 'Angular', 'TypeScript', 'JavaScript', 'Python', 'Java'
        }
        return text in exceptions

    def _is_abbreviation_ending(self, sentence: str) -> bool:
        """Check if sentence ends with a legitimate abbreviation."""
        sentence = sentence.strip()
        if not sentence.endswith('.'):
            return False
        
        # Check if last word before period is an abbreviation
        words = sentence[:-1].split()  # Remove period and split
        if not words:
            return False
        
        last_word = words[-1]
        
        # Common abbreviations that end with periods
        abbreviations = {'Inc', 'Corp', 'Ltd', 'Co', 'LLC', 'Dr', 'Mr', 'Ms', 'Mrs', 'etc', 'vs', 'e.g', 'i.e'}
        return last_word in abbreviations

    def _is_legitimate_sentence_ending(self, sentence: str, doc: 'Doc') -> bool:
        """Check if this is actually a complete sentence that should end with period."""
        if not doc:
            return False
        
        # Very long headings might be complete sentences
        if len(sentence.split()) > 10:
            return True
        
        # Check for sentence structure (subject + verb)
        has_subject = any(token.dep_ in ['nsubj', 'nsubjpass'] for token in doc)
        has_verb = any(token.pos_ == 'VERB' for token in doc)
        
        return has_subject and has_verb

    def _has_legitimate_title_case(self, sentence: str, capitalization_issues: List[str]) -> bool:
        """Check if title case is legitimate (e.g., proper nouns, brand names)."""
        # If all capitalized words are brand names or technical terms
        for word in capitalization_issues:
            if self._is_excepted(word):
                continue
            
            # Check if it's a brand name or technical term
            if not self._is_brand_or_technical_term(word):
                return False
        
        return True

    def _is_brand_or_technical_term(self, word: str) -> bool:
        """Check if word is a legitimate brand name or technical term."""
        # Technical terms that are commonly capitalized
        technical_terms = {
            'JavaScript', 'TypeScript', 'PowerShell', 'GitHub', 'GitLab',
            'Docker', 'Kubernetes', 'Node.js', 'React', 'Vue.js', 'Angular'
        }
        
        # Brand names (proper nouns)
        brand_names = {
            'Microsoft', 'Google', 'Apple', 'Amazon', 'Oracle', 'IBM',
            'Facebook', 'Twitter', 'LinkedIn', 'Slack', 'Zoom'
        }
        
        return word in technical_terms or word in brand_names

    def _is_legitimate_question_heading(self, sentence: str, text: str, context: Dict[str, Any]) -> bool:
        """Check if question heading is legitimate in this context."""
        sentence_lower = sentence.lower()
        text_lower = text.lower()
        
        # FAQ sections
        if 'faq' in text_lower or 'frequently asked' in text_lower:
            return True
        
        # Help sections
        if 'help' in text_lower or 'support' in text_lower:
            return True
        
        # Troubleshooting sections
        if 'troubleshoot' in text_lower or 'problem' in text_lower:
            return True
        
        # User guide context
        content_type = context.get('content_type', '')
        if content_type in ['user_guide', 'help', 'support', 'faq']:
            return True
        
        return False

    def _is_legitimate_gerund_heading(self, sentence: str, first_token: 'Token', context: Dict[str, Any]) -> bool:
        """Check if gerund heading is legitimate in this context."""
        gerund_lemma = first_token.lemma_.lower()
        
        # Action-oriented content might legitimately use gerunds
        content_type = context.get('content_type', '')
        if content_type in ['procedural', 'tutorial', 'guide']:
            return True
        
        # Technical procedures often use gerunds appropriately
        if gerund_lemma in ['configuring', 'installing', 'troubleshooting', 'debugging', 'monitoring']:
            return True
        
        return False

    # === CONTEXTUAL MESSAGING AND SUGGESTIONS ===

    def _get_contextual_message(self, violation_type: str, evidence_score: float, 
                               context: Dict[str, Any], **kwargs) -> str:
        """Generate contextual error messages based on violation type and evidence."""
        if violation_type == 'period_ending':
            if evidence_score > 0.8:
                return "Headings should not end with a period."
            elif evidence_score > 0.6:
                return "Consider removing the period from this heading."
            else:
                return "This heading may not need a period ending."
        
        elif violation_type == 'capitalization':
            if evidence_score > 0.8:
                return "Headings should use sentence-style capitalization, not headline-style."
            elif evidence_score > 0.6:
                return "Consider using sentence-style capitalization for this heading."
            else:
                return "This heading's capitalization could be reviewed for consistency."
        
        elif violation_type == 'question_style':
            if evidence_score > 0.8:
                return "Avoid using questions in headings for technical documentation."
            elif evidence_score > 0.6:
                return "Consider rephrasing this heading as a statement."
            else:
                return "Question-style headings may not be optimal for this content type."
        
        elif violation_type == 'gerund_leadin':
            topic_type = kwargs.get('topic_type', 'Concept')
            if evidence_score > 0.8:
                return f"Headings for '{topic_type}' topics should not start with a gerund."
            elif evidence_score > 0.6:
                return f"Consider using a more direct heading style for '{topic_type}' content."
            else:
                return "This gerund-style heading could be more direct."
        
        return "Heading formatting issue detected."

    def _generate_smart_suggestions(self, violation_type: str, evidence_score: float,
                                  context: Dict[str, Any], **kwargs) -> List[str]:
        """Generate smart suggestions based on violation type and evidence confidence."""
        suggestions = []
        
        if violation_type == 'period_ending':
            suggestions.append("Remove the period from the end of the heading.")
            if evidence_score > 0.7:
                suggestions.append("Headings are titles, not sentences, and should not end with periods.")
        
        elif violation_type == 'capitalization':
            suggestions.append("Capitalize only the first word and any proper nouns in the heading.")
            suggestions.append("Use sentence-style capitalization instead of title case.")
            if evidence_score > 0.7:
                suggestions.append("Consistent capitalization improves document professionalism.")
        
        elif violation_type == 'question_style':
            suggestions.append("Rewrite the heading as a statement or a noun phrase.")
            suggestions.append("Use declarative language that tells readers what they'll learn.")
            if context.get('content_type') == 'technical':
                suggestions.append("Technical documentation benefits from direct, informative headings.")
        
        elif violation_type == 'gerund_leadin':
            first_token = kwargs.get('first_token')
            if first_token:
                lemma = first_token.lemma_
                suggestions.append(f"Consider rewriting to be more direct, for example: 'Overview of {lemma}' or '{lemma.title()} Guide'.")
            suggestions.append("Use noun phrases or direct statements instead of gerunds.")
            if evidence_score > 0.7:
                suggestions.append("Direct headings help readers quickly understand content structure.")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    # === ENHANCED HELPER METHODS FOR 6-STEP EVIDENCE PATTERN ===
    
    def _is_heading_in_actual_quotes(self, sentence: str, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Surgical check: Is the heading actually within quotation marks?
        Only returns True for genuine quoted content, not incidental apostrophes.
        """
        if not text:
            return False
        
        # Look for quote pairs that actually enclose the heading
        import re
        
        # Find all potential quote pairs
        quote_patterns = [
            (r'"([^"]*)"', '"'),  # Double quotes
            (r"'([^']*)'", "'"),  # Single quotes
            (r'`([^`]*)`', '`')   # Backticks
        ]
        
        for pattern, quote_char in quote_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                quoted_content = match.group(1)
                if sentence.lower() in quoted_content.lower():
                    return True
        
        return False
    
    def _is_heading_in_technical_context(self, sentence: str, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if heading appears in technical documentation context with approved patterns.
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for technical documentation indicators
        technical_indicators = [
            'api documentation', 'technical specification', 'developer guide',
            'software documentation', 'system documentation', 'installation guide',
            'configuration guide', 'troubleshooting guide', 'reference manual'
        ]
        
        for indicator in technical_indicators:
            if indicator in text_lower:
                # Allow some technical-specific headings in strong technical contexts
                if self._is_technical_heading_pattern(sentence):
                    return True
        
        # Check content type for technical context
        content_type = context.get('content_type', '') if context else ''
        if content_type == 'technical':
            # Common technical heading patterns that might be acceptable
            if self._is_technical_heading_pattern(sentence):
                return True
        
        return False
    
    def _is_heading_in_citation_context(self, sentence: str, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if heading appears in citation or reference context.
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for citation indicators
        citation_indicators = [
            'according to', 'as stated in', 'reference:', 'cited in',
            'documentation shows', 'manual states', 'guide recommends',
            'specification defines', 'standard requires'
        ]
        
        for indicator in citation_indicators:
            if indicator in text_lower:
                return True
        
        # Check for reference formatting patterns
        if any(pattern in text_lower for pattern in ['see also', 'refer to', 'as described']):
            return True
        
        return False
    
    def _is_technical_heading_pattern(self, sentence: str) -> bool:
        """
        Check if heading follows a technical pattern that might be acceptable.
        """
        sentence_lower = sentence.lower()
        
        # Technical patterns that might be acceptable with periods or different capitalization
        technical_patterns = [
            r'\b(api|sdk|cli|gui|ui|url|uri|http|https)\b',
            r'\b(json|xml|yaml|csv|sql|html|css|js)\b',
            r'\b(get|post|put|delete|patch)\b',  # HTTP methods
            r'\b(200|404|500|401|403)\b',  # HTTP status codes
            r'v?\d+\.\d+(\.\d+)?',  # Version numbers
            r'\b[A-Z_]{3,}\b',  # Constants
            r'\w+\(\)',  # Function calls
            r'<\w+>',  # XML/HTML tags or placeholders
        ]
        
        import re
        for pattern in technical_patterns:
            if re.search(pattern, sentence_lower):
                return True
        
        return False
    
    def _get_period_ending_base_evidence_score(self, sentence: str, doc: 'Doc', context: Dict[str, Any] = None) -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Simple heading with period → 0.8 (very specific)
        - Complex sentence-like heading → 0.5 (moderate specificity)
        - Abbreviation-like heading → 0.3 (needs context analysis)
        """
        if not sentence.strip().endswith('.'):
            return 0.0
        
        # Enhanced specificity analysis
        if self._is_exact_period_violation(sentence):
            return 0.8  # Very specific, clear violation
        elif self._is_pattern_period_violation(sentence):
            return 0.5  # Pattern-based, moderate specificity
        elif self._is_minor_period_issue(sentence):
            return 0.3  # Minor issue, needs context
        else:
            return 0.2  # Possible issue, needs more evidence
    
    def _get_capitalization_base_evidence_score(self, sentence: str, capitalization_issues: List[str], context: Dict[str, Any] = None) -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Many title-case words → 0.7 (very specific)
        - Few title-case words → 0.5 (moderate specificity)
        - Proper nouns mixed → 0.3 (needs context analysis)
        """
        if not capitalization_issues:
            return 0.0
        
        # Enhanced specificity analysis based on ratio of issues
        issue_ratio = len(capitalization_issues) / len(sentence.split())
        
        if self._is_exact_capitalization_violation(sentence, capitalization_issues):
            return 0.7  # Very specific, clear violation
        elif self._is_pattern_capitalization_violation(sentence, capitalization_issues):
            return 0.5  # Pattern-based, moderate specificity
        elif self._is_minor_capitalization_issue(sentence, capitalization_issues):
            return 0.3  # Minor issue, needs context
        else:
            return 0.2  # Possible issue, needs more evidence
    
    def _get_question_style_base_evidence_score(self, sentence: str, doc: 'Doc', context: Dict[str, Any] = None) -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Yes/no questions → 0.7 (very specific)
        - Wh-questions → 0.5 (moderate specificity)
        - Ambiguous questions → 0.3 (needs context analysis)
        """
        if not sentence.strip().endswith('?'):
            return 0.0
        
        # Enhanced specificity analysis
        if self._is_exact_question_violation(sentence, doc):
            return 0.7  # Very specific, clear violation
        elif self._is_pattern_question_violation(sentence, doc):
            return 0.5  # Pattern-based, moderate specificity
        elif self._is_minor_question_issue(sentence, doc):
            return 0.3  # Minor issue, needs context
        else:
            return 0.2  # Possible issue, needs more evidence
    
    def _get_gerund_base_evidence_score(self, sentence: str, first_token: 'Token', topic_type: str, context: Dict[str, Any] = None) -> float:
        """
        REFINED: Set dynamic base evidence score based on violation specificity.
        More specific violations get higher base scores for better precision.
        
        Examples:
        - Weak gerunds in concept topics → 0.7 (very specific)
        - Acceptable gerunds in wrong context → 0.5 (moderate specificity)
        - Borderline gerunds → 0.3 (needs context analysis)
        """
        if not first_token or first_token.tag_ != 'VBG':
            return 0.0
        
        # Enhanced specificity analysis
        if self._is_exact_gerund_violation(sentence, first_token, topic_type):
            return 0.7  # Very specific, clear violation
        elif self._is_pattern_gerund_violation(sentence, first_token, topic_type):
            return 0.5  # Pattern-based, moderate specificity
        elif self._is_minor_gerund_issue(sentence, first_token, topic_type):
            return 0.3  # Minor issue, needs context
        else:
            return 0.2  # Possible issue, needs more evidence
    
    def _is_exact_period_violation(self, sentence: str) -> bool:
        """
        Check if heading represents an exact period ending violation.
        """
        sentence = sentence.strip()
        
        # Simple, short headings with periods are clear violations
        words = sentence[:-1].split()  # Remove period for analysis
        if len(words) <= 5 and not self._is_abbreviation_ending(sentence):
            return True
        
        return False
    
    def _is_pattern_period_violation(self, sentence: str) -> bool:
        """
        Check if heading shows a pattern of period ending violation.
        """
        sentence = sentence.strip()
        
        # Medium-length headings that aren't sentence-like
        words = sentence[:-1].split()
        if 6 <= len(words) <= 10:
            # Check if it's not a complete sentence
            import re
            if not re.search(r'\b(is|are|was|were|has|have|will|would|can|could)\b', sentence.lower()):
                return True
        
        return False
    
    def _is_minor_period_issue(self, sentence: str) -> bool:
        """
        Check if heading has minor period ending issues.
        """
        sentence = sentence.strip()
        
        # Longer headings that might be legitimate sentences
        words = sentence[:-1].split()
        if len(words) > 10:
            return True
        
        return False
    
    def _is_exact_capitalization_violation(self, sentence: str, capitalization_issues: List[str]) -> bool:
        """
        Check if heading represents an exact capitalization violation.
        """
        # High ratio of capitalized words suggests title case
        total_words = len(sentence.split())
        issue_ratio = len(capitalization_issues) / total_words if total_words > 0 else 0
        
        if issue_ratio > 0.6:  # More than 60% of words are title case
            return True
        
        return False
    
    def _is_pattern_capitalization_violation(self, sentence: str, capitalization_issues: List[str]) -> bool:
        """
        Check if heading shows a pattern of capitalization violation.
        """
        # Moderate ratio suggests some title case usage
        total_words = len(sentence.split())
        issue_ratio = len(capitalization_issues) / total_words if total_words > 0 else 0
        
        if 0.3 < issue_ratio <= 0.6:  # 30-60% of words are title case
            return True
        
        return False
    
    def _is_minor_capitalization_issue(self, sentence: str, capitalization_issues: List[str]) -> bool:
        """
        Check if heading has minor capitalization issues.
        """
        # Low ratio suggests few capitalized words
        total_words = len(sentence.split())
        issue_ratio = len(capitalization_issues) / total_words if total_words > 0 else 0
        
        if 0 < issue_ratio <= 0.3:  # Up to 30% of words are title case
            return True
        
        return False
    
    def _is_exact_question_violation(self, sentence: str, doc: 'Doc') -> bool:
        """
        Check if heading represents an exact question violation.
        """
        if not doc or len(doc) == 0:
            return False
        
        first_word = doc[0].text.lower()
        
        # Yes/no questions are clear violations in most contexts
        if first_word in ['is', 'are', 'can', 'will', 'do', 'does', 'did', 'has', 'have']:
            return True
        
        return False
    
    def _is_pattern_question_violation(self, sentence: str, doc: 'Doc') -> bool:
        """
        Check if heading shows a pattern of question violation.
        """
        if not doc or len(doc) == 0:
            return False
        
        first_word = doc[0].text.lower()
        
        # Wh-questions might be violations depending on context
        if first_word in ['what', 'how', 'why', 'when', 'where', 'which', 'who']:
            return True
        
        return False
    
    def _is_minor_question_issue(self, sentence: str, doc: 'Doc') -> bool:
        """
        Check if heading has minor question issues.
        """
        # Questions that might be borderline acceptable
        if len(sentence.split()) <= 3:  # Very short questions
            return True
        
        return False
    
    def _is_exact_gerund_violation(self, sentence: str, first_token: 'Token', topic_type: str) -> bool:
        """
        Check if heading represents an exact gerund violation.
        """
        gerund_lemma = first_token.lemma_.lower()
        
        # Weak gerunds in concept topics are clear violations
        weak_gerunds = ['understanding', 'getting', 'learning', 'knowing', 'using']
        if gerund_lemma in weak_gerunds and topic_type == 'Concept':
            return True
        
        return False
    
    def _is_pattern_gerund_violation(self, sentence: str, first_token: 'Token', topic_type: str) -> bool:
        """
        Check if heading shows a pattern of gerund violation.
        """
        gerund_lemma = first_token.lemma_.lower()
        
        # Any gerund in concept or reference topics might be a violation
        if topic_type in ['Concept', 'Reference']:
            return True
        
        return False
    
    def _is_minor_gerund_issue(self, sentence: str, first_token: 'Token', topic_type: str) -> bool:
        """
        Check if heading has minor gerund issues.
        """
        gerund_lemma = first_token.lemma_.lower()
        
        # Acceptable gerunds in any context are minor issues
        acceptable_gerunds = ['configuring', 'installing', 'troubleshooting', 'debugging', 'monitoring']
        if gerund_lemma in acceptable_gerunds:
            return True
        
        return False
    
    def _apply_feedback_clues_period_endings(self, evidence_score: float, sentence: str, context: Dict[str, Any] = None) -> float:
        """
        Apply clues learned from user feedback patterns specific to period endings.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_period_endings()
        
        sentence_lower = sentence.lower().strip()
        
        # Consistently Accepted Period Endings
        if sentence_lower in feedback_patterns.get('accepted_period_endings', set()):
            evidence_score -= 0.5  # Users consistently accept this period ending
        
        # Consistently Rejected Suggestions
        if sentence_lower in feedback_patterns.get('rejected_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: Period ending acceptance rates by heading type
        heading_patterns = feedback_patterns.get('period_ending_acceptance', {})
        
        # Classify heading type
        heading_type = self._classify_heading_type(sentence)
        acceptance_rate = heading_patterns.get(heading_type, 0.5)
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # High acceptance for this heading type
        elif acceptance_rate < 0.2:
            evidence_score += 0.2  # Low acceptance, strong violation
        
        # Pattern: Context-specific acceptance
        content_type = context.get('content_type', 'general') if context else 'general'
        content_patterns = feedback_patterns.get(f'{content_type}_period_acceptance', {})
        
        acceptance_rate = content_patterns.get(heading_type, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Accepted in this content type
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Consistently flagged in this content type
        
        return evidence_score
    
    def _apply_feedback_clues_capitalization(self, evidence_score: float, sentence: str, capitalization_issues: List[str], context: Dict[str, Any] = None) -> float:
        """
        Apply clues learned from user feedback patterns specific to capitalization.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_capitalization()
        
        sentence_lower = sentence.lower()
        
        # Consistently Accepted Capitalization Patterns
        if sentence_lower in feedback_patterns.get('accepted_capitalization_patterns', set()):
            evidence_score -= 0.5  # Users consistently accept this capitalization
        
        # Consistently Rejected Suggestions
        if sentence_lower in feedback_patterns.get('rejected_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: Capitalization acceptance rates by heading level
        heading_level = context.get('block_level', 1) if context else 1
        level_patterns = feedback_patterns.get('capitalization_level_acceptance', {})
        
        acceptance_rate = level_patterns.get(f'h{heading_level}', 0.5)
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # High acceptance for this heading level
        elif acceptance_rate < 0.2:
            evidence_score += 0.2  # Low acceptance, strong violation
        
        # Pattern: Word-specific capitalization acceptance
        for word in capitalization_issues:
            word_acceptance = feedback_patterns.get('word_capitalization_acceptance', {})
            acceptance_rate = word_acceptance.get(word.lower(), 0.5)
            if acceptance_rate > 0.8:
                evidence_score -= 0.1  # This word is often accepted when capitalized
            elif acceptance_rate < 0.2:
                evidence_score += 0.1  # This word is often flagged when capitalized
        
        return evidence_score
    
    def _apply_feedback_clues_question_style(self, evidence_score: float, sentence: str, context: Dict[str, Any] = None) -> float:
        """
        Apply clues learned from user feedback patterns specific to question style.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_question_style()
        
        sentence_lower = sentence.lower()
        
        # Consistently Accepted Question Headings
        if sentence_lower in feedback_patterns.get('accepted_question_headings', set()):
            evidence_score -= 0.5  # Users consistently accept this question
        
        # Consistently Rejected Suggestions
        if sentence_lower in feedback_patterns.get('rejected_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: Question type acceptance rates
        question_patterns = feedback_patterns.get('question_type_acceptance', {})
        
        # Classify question type
        question_type = self._classify_question_type(sentence)
        acceptance_rate = question_patterns.get(question_type, 0.5)
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # High acceptance for this question type
        elif acceptance_rate < 0.2:
            evidence_score += 0.2  # Low acceptance, strong violation
        
        # Pattern: Audience-specific question acceptance
        audience = context.get('audience', 'general') if context else 'general'
        audience_patterns = feedback_patterns.get(f'{audience}_question_acceptance', {})
        
        acceptance_rate = audience_patterns.get(question_type, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Accepted for this audience
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Consistently flagged for this audience
        
        return evidence_score
    
    def _apply_feedback_clues_gerunds(self, evidence_score: float, sentence: str, first_token: 'Token', context: Dict[str, Any] = None) -> float:
        """
        Apply clues learned from user feedback patterns specific to gerunds.
        """
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns_gerunds()
        
        gerund_lemma = first_token.lemma_.lower()
        
        # Consistently Accepted Gerund Headings
        if gerund_lemma in feedback_patterns.get('accepted_gerund_headings', set()):
            evidence_score -= 0.5  # Users consistently accept this gerund
        
        # Consistently Rejected Suggestions
        if gerund_lemma in feedback_patterns.get('rejected_suggestions', set()):
            evidence_score += 0.3  # Users consistently reject flagging this
        
        # Pattern: Gerund acceptance rates by type
        gerund_patterns = feedback_patterns.get('gerund_type_acceptance', {})
        
        # Classify gerund type
        gerund_type = self._classify_gerund_type(gerund_lemma)
        acceptance_rate = gerund_patterns.get(gerund_type, 0.5)
        if acceptance_rate > 0.8:
            evidence_score -= 0.4  # High acceptance for this gerund type
        elif acceptance_rate < 0.2:
            evidence_score += 0.2  # Low acceptance, strong violation
        
        # Pattern: Topic type-specific gerund acceptance
        topic_type = context.get('topic_type', 'Concept') if context else 'Concept'
        topic_patterns = feedback_patterns.get(f'{topic_type.lower()}_gerund_acceptance', {})
        
        acceptance_rate = topic_patterns.get(gerund_type, 0.5)
        if acceptance_rate > 0.7:
            evidence_score -= 0.3  # Accepted for this topic type
        elif acceptance_rate < 0.3:
            evidence_score += 0.2  # Consistently flagged for this topic type
        
        return evidence_score
    
    def _classify_heading_type(self, sentence: str) -> str:
        """
        Classify the type of heading for feedback analysis.
        """
        sentence_lower = sentence.lower()
        word_count = len(sentence.split())
        
        # Technical patterns
        if self._is_technical_heading_pattern(sentence):
            return 'technical'
        
        # Short vs long headings
        if word_count <= 3:
            return 'short'
        elif word_count <= 6:
            return 'medium'
        else:
            return 'long'
    
    def _classify_question_type(self, sentence: str) -> str:
        """
        Classify the type of question for feedback analysis.
        """
        sentence_lower = sentence.lower()
        first_word = sentence_lower.split()[0] if sentence_lower.split() else ''
        
        # Question word types
        if first_word in ['what', 'why', 'when', 'where', 'which', 'who']:
            return 'wh_question'
        elif first_word in ['how']:
            return 'how_question'
        elif first_word in ['is', 'are', 'can', 'will', 'do', 'does', 'did', 'has', 'have']:
            return 'yes_no_question'
        else:
            return 'other_question'
    
    def _classify_gerund_type(self, gerund_lemma: str) -> str:
        """
        Classify the type of gerund for feedback analysis.
        """
        # Weak gerunds
        if gerund_lemma in ['understanding', 'getting', 'learning', 'knowing', 'using']:
            return 'weak_gerund'
        
        # Action gerunds
        if gerund_lemma in ['configuring', 'installing', 'troubleshooting', 'debugging', 'monitoring']:
            return 'action_gerund'
        
        # Process gerunds
        if gerund_lemma in ['creating', 'building', 'developing', 'implementing', 'managing']:
            return 'process_gerund'
        
        return 'other_gerund'
    
    def _get_cached_feedback_patterns_period_endings(self) -> Dict[str, Any]:
        """
        Load feedback patterns from cache or feedback analysis for period endings.
        """
        # This would load from feedback analysis system
        # For now, return basic patterns with some realistic examples
        return {
            'accepted_period_endings': {
                'fig. 1', 'table 1', 'appendix a.', 'section 1.1.',
                'version 2.0.', 'step 1.', 'example 1.'
            },
            'rejected_suggestions': set(),  # Headings users don't want flagged
            'period_ending_acceptance': {
                'technical': 0.7,           # Technical headings often acceptable
                'short': 0.3,               # Short headings rarely need periods
                'medium': 0.2,              # Medium headings rarely need periods
                'long': 0.6                 # Long headings might be sentences
            },
            'technical_period_acceptance': {
                'technical': 0.9,           # Very acceptable in technical writing
                'short': 0.4,               # Sometimes acceptable in technical
                'medium': 0.3,              # Less acceptable in technical
                'long': 0.8                 # Often acceptable in technical
            },
            'business_period_acceptance': {
                'technical': 0.5,           # Sometimes acceptable in business
                'short': 0.2,               # Rarely acceptable in business
                'medium': 0.1,              # Very rarely acceptable in business
                'long': 0.4                 # Sometimes acceptable in business
            }
        }
    
    def _get_cached_feedback_patterns_capitalization(self) -> Dict[str, Any]:
        """
        Load feedback patterns from cache or feedback analysis for capitalization.
        """
        # This would load from feedback analysis system
        # For now, return basic patterns with some realistic examples
        return {
            'accepted_capitalization_patterns': {
                'getting started with api', 'working with json data',
                'using http requests', 'configuring ssl certificates'
            },
            'rejected_suggestions': set(),  # Patterns users don't want flagged
            'capitalization_level_acceptance': {
                'h1': 0.2,                  # H1 headings should follow sentence case
                'h2': 0.3,                  # H2 headings sometimes acceptable
                'h3': 0.4,                  # H3 headings more lenient
                'h4': 0.5,                  # H4 headings quite lenient
                'h5': 0.6,                  # H5 headings very lenient
                'h6': 0.7                   # H6 headings most lenient
            },
            'word_capitalization_acceptance': {
                'api': 0.9,                 # API almost always acceptable capitalized
                'json': 0.9,                # JSON almost always acceptable capitalized
                'http': 0.9,                # HTTP almost always acceptable capitalized
                'ssl': 0.9,                 # SSL almost always acceptable capitalized
                'xml': 0.9,                 # XML almost always acceptable capitalized
                'css': 0.8,                 # CSS often acceptable capitalized
                'html': 0.8,                # HTML often acceptable capitalized
                'sql': 0.8,                 # SQL often acceptable capitalized
                'the': 0.1,                 # 'The' rarely acceptable capitalized
                'and': 0.1,                 # 'And' rarely acceptable capitalized
                'or': 0.1,                  # 'Or' rarely acceptable capitalized
                'of': 0.1,                  # 'Of' rarely acceptable capitalized
                'in': 0.1,                  # 'In' rarely acceptable capitalized
                'with': 0.1,                # 'With' rarely acceptable capitalized
                'for': 0.1,                 # 'For' rarely acceptable capitalized
                'to': 0.1                   # 'To' rarely acceptable capitalized
            }
        }
    
    def _get_cached_feedback_patterns_question_style(self) -> Dict[str, Any]:
        """
        Load feedback patterns from cache or feedback analysis for question style.
        """
        # This would load from feedback analysis system
        # For now, return basic patterns with some realistic examples
        return {
            'accepted_question_headings': {
                'what is rest?', 'how to install?', 'why use this approach?',
                'when to upgrade?', 'where to find documentation?'
            },
            'rejected_suggestions': set(),  # Questions users don't want flagged
            'question_type_acceptance': {
                'wh_question': 0.6,         # What/why/when questions sometimes acceptable
                'how_question': 0.8,        # How questions often acceptable
                'yes_no_question': 0.2,     # Yes/no questions rarely acceptable
                'other_question': 0.3       # Other questions sometimes acceptable
            },
            'beginner_question_acceptance': {
                'wh_question': 0.8,         # Very acceptable for beginners
                'how_question': 0.9,        # Very acceptable for beginners
                'yes_no_question': 0.4,     # Sometimes acceptable for beginners
                'other_question': 0.5       # Sometimes acceptable for beginners
            },
            'expert_question_acceptance': {
                'wh_question': 0.3,         # Less acceptable for experts
                'how_question': 0.5,        # Sometimes acceptable for experts
                'yes_no_question': 0.1,     # Rarely acceptable for experts
                'other_question': 0.2       # Rarely acceptable for experts
            },
            'general_question_acceptance': {
                'wh_question': 0.6,         # Moderately acceptable for general
                'how_question': 0.7,        # Often acceptable for general
                'yes_no_question': 0.2,     # Rarely acceptable for general
                'other_question': 0.3       # Sometimes acceptable for general
            }
        }
    
    def _get_cached_feedback_patterns_gerunds(self) -> Dict[str, Any]:
        """
        Load feedback patterns from cache or feedback analysis for gerunds.
        """
        # This would load from feedback analysis system
        # For now, return basic patterns with some realistic examples
        return {
            'accepted_gerund_headings': {
                'configuring', 'installing', 'troubleshooting', 'debugging', 'monitoring'
            },
            'rejected_suggestions': set(),  # Gerunds users don't want flagged
            'gerund_type_acceptance': {
                'weak_gerund': 0.2,         # Weak gerunds rarely acceptable
                'action_gerund': 0.8,       # Action gerunds often acceptable
                'process_gerund': 0.6,      # Process gerunds sometimes acceptable
                'other_gerund': 0.4         # Other gerunds sometimes acceptable
            },
            'concept_gerund_acceptance': {
                'weak_gerund': 0.1,         # Very rarely acceptable in concepts
                'action_gerund': 0.3,       # Sometimes acceptable in concepts
                'process_gerund': 0.2,      # Rarely acceptable in concepts
                'other_gerund': 0.2         # Rarely acceptable in concepts
            },
            'procedure_gerund_acceptance': {
                'weak_gerund': 0.5,         # Sometimes acceptable in procedures
                'action_gerund': 0.9,       # Very acceptable in procedures
                'process_gerund': 0.8,      # Very acceptable in procedures
                'other_gerund': 0.7         # Often acceptable in procedures
            },
            'reference_gerund_acceptance': {
                'weak_gerund': 0.1,         # Rarely acceptable in reference
                'action_gerund': 0.4,       # Sometimes acceptable in reference
                'process_gerund': 0.3,      # Sometimes acceptable in reference
                'other_gerund': 0.3         # Sometimes acceptable in reference
            }
        }
