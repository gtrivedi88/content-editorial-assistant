"""
Pronouns Rule (Consolidated)
Based on IBM Style Guide topic: "Pronouns"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class PronounsRule(BaseLanguageRule):
    """
    Checks for specific pronoun style issues:
    1. Use of gender-specific pronouns in technical writing.
    
    Note: Ambiguous pronoun detection is handled by the more sophisticated
    PronounAmbiguityDetector in the ambiguity module to avoid duplication.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'pronouns'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for gender-specific pronouns.
        Calculates a nuanced evidence score for each candidate pronoun
        considering linguistic, structural, semantic, and feedback clues.
        
        Note: Ambiguous reference resolution is handled by the ambiguity module.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        doc = nlp(text)
        gendered_pronouns = {'he', 'him', 'his', 'she', 'her', 'hers'}

        for i, sent in enumerate(doc.sents):
            for token in sent:
                lemma_lower = getattr(token, 'lemma_', '').lower()
                if lemma_lower in gendered_pronouns and getattr(token, 'pos_', '') in {'PRON', 'DET'}:
                    evidence_score = self._calculate_pronoun_evidence(token, sent, text, context or {})
                    if evidence_score > 0.1:
                        message = self._get_contextual_pronouns_message(token, evidence_score, sent)
                        suggestions = self._generate_smart_pronouns_suggestions(token, evidence_score, sent, context or {})
                        severity = 'high' if evidence_score > 0.75 else 'medium'

                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=message,
                            suggestions=suggestions,
                            severity=severity,
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
        return errors

    # === EVIDENCE-BASED CALCULATION ===

    def _calculate_pronoun_evidence(self, token, sentence, text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for gendered pronoun concerns.
        
        Higher scores indicate stronger evidence that the gendered pronoun should be flagged.
        Lower scores indicate acceptable usage in specific contexts.
        
        Args:
            token: The gendered pronoun token
            sentence: Sentence containing the pronoun
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (acceptable) to 1.0 (should be flagged)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_pronoun_evidence(token, sentence)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this pronoun
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_pronouns(evidence_score, token, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_pronouns(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_pronouns(evidence_score, token, sentence, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_pronouns(evidence_score, token, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    # === PRONOUN EVIDENCE METHODS ===

    def _get_base_pronoun_evidence(self, token, sentence) -> float:
        """Get base evidence score for gendered pronoun usage."""
        
        # === PRONOUN TYPE ANALYSIS ===
        lemma_lower = getattr(token, 'lemma_', '').lower()
        token_text = getattr(token, 'text', '')
        
        # Different gendered pronouns have different evidence strengths
        if lemma_lower in ['he', 'him']:
            return 0.7  # Male pronouns in technical writing often problematic
        elif lemma_lower in ['she', 'her']:
            return 0.7  # Female pronouns in technical writing often problematic
        elif lemma_lower in ['his', 'hers']:
            return 0.6  # Possessive pronouns slightly lower evidence
        
        # Default for any other gendered pronouns
        return 0.6

    def _apply_linguistic_clues_pronouns(self, evidence_score: float, token, sentence) -> float:
        """
        Apply linguistic analysis clues for pronoun detection.
        
        Analyzes SpaCy linguistic features including POS tags, dependency parsing,
        morphological features, NER, and surrounding context to determine evidence
        strength for gendered pronoun usage.
        
        Args:
            evidence_score: Current evidence score to modify
            token: The gendered pronoun token
            sentence: Sentence containing the token
            
        Returns:
            float: Modified evidence score based on linguistic analysis
        """
        
        token_text = getattr(token, 'text', '')
        lemma_lower = getattr(token, 'lemma_', '').lower()
        dep = getattr(token, 'dep_', '')
        pos = getattr(token, 'pos_', '')
        
        # === PART-OF-SPEECH ANALYSIS ===
        # Possessive determiners (his/her) in attributive use are often easy to replace
        if lemma_lower in {'his', 'her'} and dep in {'det', 'poss'}:
            evidence_score += 0.1  # Easier to replace possessive determiners
        elif pos == 'PRON':
            evidence_score += 0.05  # Pronoun usage generally concerning
        
        # === DEPENDENCY PARSING ===
        # Subject pronouns are more problematic than object pronouns
        if dep == 'nsubj':
            evidence_score += 0.15  # Subject position more visible
        elif dep in ['dobj', 'iobj', 'pobj']:
            evidence_score += 0.05  # Object position less problematic
        
        # === MORPHOLOGICAL FEATURES ===
        if hasattr(token, 'morph') and token.morph:
            morph_dict = token.morph.to_dict()
            if morph_dict.get('Gender') in ['Masc', 'Fem']:
                evidence_score += 0.1  # Explicitly gendered morphology
        
        # === CAPITALIZATION PATTERNS ===
        if token_text.istitle() and not token.is_sent_start:
            evidence_score -= 0.1  # Might be a proper name
        
        # === SURROUNDING CONTEXT ===
        # Look for contextual clues in surrounding tokens
        prev_token = token.nbor(-1) if token.i > 0 else None
        next_token = token.nbor(1) if token.i < len(token.doc) - 1 else None
        
        # Quoted speech may be reporting; reduce impact
        in_quotes = '"' in sentence.text or "'" in sentence.text
        if in_quotes:
            evidence_score -= 0.15  # Quoted speech often reports specific instances
        
        # Code context indicators
        if '`' in sentence.text:
            evidence_score -= 0.2  # Code examples may use specific pronouns
        
        # === NAMED ENTITY RECOGNITION ===
        # Nearby named entities of type PERSON reduces evidence (specific reference)
        has_person_ner = any(getattr(t, 'ent_type_', '') == 'PERSON' for t in sentence)
        if has_person_ner:
            evidence_score -= 0.3  # Specific person reference
        
        # Check if the pronoun itself is part of a named entity
        if getattr(token, 'ent_type_', '') in ['PERSON', 'ORG']:
            evidence_score -= 0.5  # Part of a name
        
        # === ROLE-BASED CONTEXT ===
        # Nearby generic roles raise evidence
        sent_lower = sentence.text.lower()
        generic_roles = {
            'user', 'developer', 'administrator', 'person', 'individual', 
            'customer', 'client', 'employee', 'manager', 'engineer',
            'designer', 'analyst', 'operator', 'technician', 'specialist'
        }
        if any(term in sent_lower for term in generic_roles):
            evidence_score += 0.2  # Generic roles should use inclusive language
        
        # === INCLUSIVE LANGUAGE INDICATORS ===
        # Check if inclusive alternatives already present
        inclusive_pronouns = {'they', 'them', 'their', 'theirs'}
        if any(t.lemma_.lower() in inclusive_pronouns for t in sentence):
            evidence_score -= 0.1  # Document already uses inclusive language
        
        # Check for mixed pronoun usage in sentence
        other_gendered = {t.lemma_.lower() for t in sentence 
                         if t != token and getattr(t, 'lemma_', '').lower() in {'he', 'him', 'his', 'she', 'her', 'hers'}}
        if other_gendered:
            evidence_score += 0.1  # Multiple gendered pronouns problematic
        
        # === INSTRUCTION CONTEXT ===
        # Instructional language indicators
        instruction_indicators = ['must', 'should', 'can', 'will', 'need to', 'have to']
        if any(indicator in sent_lower for indicator in instruction_indicators):
            evidence_score += 0.15  # Instructions should be inclusive
        
        return evidence_score

    def _apply_structural_clues_pronouns(self, evidence_score: float, context: Dict[str, Any]) -> float:
        """
        Apply document structure clues for pronoun detection.
        
        Analyzes document structure context including block types, heading levels,
        list depth, admonition types, and other structural elements to determine
        appropriate evidence adjustments for gendered pronoun usage.
        
        Args:
            evidence_score: Current evidence score to modify
            context: Document context dictionary
            
        Returns:
            float: Modified evidence score based on structural analysis
        """
        
        block_type = context.get('block_type', 'paragraph')
        
        # === TECHNICAL DOCUMENTATION CONTEXTS ===
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.8  # Code blocks have different language rules
        elif block_type == 'inline_code':
            evidence_score -= 0.6  # Inline code may reference specific examples
        
        # === HEADING CONTEXT ===
        if block_type == 'heading':
            heading_level = context.get('block_level', 1)
            if heading_level == 1:  # H1 - Main headings
                evidence_score += 0.2  # Main headings should be inclusive
            elif heading_level == 2:  # H2 - Section headings
                evidence_score += 0.1  # Section headings should be inclusive
            elif heading_level >= 3:  # H3+ - Subsection headings
                evidence_score += 0.05  # Subsection headings less critical
        
        # === LIST CONTEXT ===
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score += 0.05  # Lists should use inclusive language
            
            # Nested list items are often more technical
            if context.get('list_depth', 1) > 1:
                evidence_score -= 0.05  # Nested items may be more technical
        
        # === TABLE CONTEXT ===
        elif block_type in ['table_cell', 'table_header']:
            if block_type == 'table_header':
                evidence_score += 0.1  # Table headers should be inclusive
            else:
                evidence_score -= 0.05  # Table cells may use examples
        
        # === ADMONITION CONTEXT ===
        elif block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'TIP', 'HINT']:
                evidence_score -= 0.1  # Notes may provide specific examples
            elif admonition_type in ['WARNING', 'CAUTION', 'DANGER']:
                evidence_score += 0.05  # Warnings should be inclusive
            elif admonition_type in ['IMPORTANT', 'ATTENTION']:
                evidence_score += 0.1  # Important notices should be inclusive
        
        # === QUOTE/CITATION CONTEXT ===
        elif block_type in ['block_quote', 'citation']:
            evidence_score -= 0.3  # Quotes may reference specific people
        
        # === SIDEBAR/CALLOUT CONTEXT ===
        elif block_type in ['sidebar', 'callout']:
            evidence_score -= 0.1  # Side content may use examples
        
        # === EXAMPLE/SAMPLE CONTEXT ===
        elif block_type in ['example', 'sample']:
            evidence_score -= 0.2  # Examples may show specific scenarios
        
        return evidence_score

    def _apply_semantic_clues_pronouns(self, evidence_score: float, token, sentence, text: str, context: Dict[str, Any]) -> float:
        """
        Apply semantic and content-type clues for pronoun detection.
        
        Analyzes high-level semantic context including content type, domain, audience,
        document purpose, and inclusive language indicators to determine evidence
        strength for gendered pronoun usage.
        
        Args:
            evidence_score: Current evidence score to modify
            token: The gendered pronoun token
            sentence: Sentence containing the token
            text: Full document text
            context: Document context dictionary
            
        Returns:
            float: Modified evidence score based on semantic analysis
        """
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # === CONTENT TYPE ANALYSIS ===
        # Inclusive expectation is higher in formal and instructional content
        if content_type == 'technical':
            evidence_score += 0.1  # Technical writing should be inclusive
        elif content_type == 'api':
            evidence_score += 0.15  # API docs widely consumed, must be inclusive
        elif content_type == 'procedural':
            evidence_score += 0.2  # Procedures address all users
        elif content_type == 'academic':
            evidence_score += 0.15  # Academic writing has high standards
        elif content_type == 'legal':
            evidence_score += 0.2  # Legal writing must be unambiguous and inclusive
        elif content_type == 'marketing':
            evidence_score += 0.1  # Marketing should appeal to everyone
        elif content_type == 'narrative':
            evidence_score -= 0.05  # Narrative may have specific characters
        elif content_type == 'tutorial':
            evidence_score += 0.15  # Tutorials should be accessible to all
        
        # === DOMAIN-SPECIFIC PATTERNS ===
        if domain in ['software', 'engineering', 'devops']:
            evidence_score += 0.1  # Technical domains emphasize inclusivity
        elif domain in ['legal', 'finance', 'medical']:
            evidence_score += 0.15  # Formal domains require precision and inclusivity
        elif domain in ['compliance', 'regulatory']:
            evidence_score += 0.2  # Regulatory domains must be inclusive
        elif domain in ['user-documentation', 'help']:
            evidence_score += 0.15  # User-facing docs must be inclusive
        elif domain in ['internal', 'team']:
            evidence_score += 0.05  # Internal docs should still be inclusive
        
        # === AUDIENCE CONSIDERATIONS ===
        if audience in ['beginner', 'general', 'consumer']:
            evidence_score += 0.15  # General audiences need inclusive language
        elif audience in ['professional', 'business']:
            evidence_score += 0.1  # Professional content should be inclusive
        elif audience in ['developer', 'technical', 'expert']:
            evidence_score += 0.05  # Even expert audiences expect inclusivity
        elif audience in ['academic', 'scientific']:
            evidence_score += 0.1  # Academic audiences value precision
        
        # === DOCUMENT LENGTH CONTEXT ===
        doc_length = len(text.split())
        if doc_length < 100:  # Short documents
            evidence_score += 0.05  # Even brief content should be inclusive
        elif doc_length > 5000:  # Long documents
            evidence_score += 0.1  # Consistency important in long docs
        
        # === DOCUMENT PURPOSE ANALYSIS ===
        if self._is_specification_documentation(text):
            evidence_score += 0.15  # Specifications must be precise and inclusive
        
        if self._is_policy_documentation(text):
            evidence_score += 0.2  # Policies must be inclusive
        
        if self._is_training_content(text):
            evidence_score += 0.15  # Training should be inclusive
        
        # === INCLUSIVE LANGUAGE INDICATORS ===
        # If document already shows inclusive language awareness, higher standard
        text_lower = text.lower()
        inclusive_indicators = [
            'inclusive language', 'they/them', 'gender-neutral', 'accessibility',
            'diversity', 'equity', 'bias-free', 'non-discriminatory'
        ]
        
        if any(indicator in text_lower for indicator in inclusive_indicators):
            evidence_score += 0.1  # Document shows awareness, should be consistent
        
        # === SENTENCE-LEVEL CONTEXT ===
        sent_lower = sentence.text.lower()
        
        # If sentence contains explicit inclusive alternatives, reduce evidence
        if any(phrase in sent_lower for phrase in ['they/them', 'use inclusive language', 'gender-neutral']):
            evidence_score -= 0.2  # Explicitly discussing inclusive language
        
        # Check for contrasting language patterns
        if 'he or she' in sent_lower or 'his or her' in sent_lower:
            evidence_score += 0.1  # Awkward alternative, should use 'they'
        
        # === INTERNATIONAL CONTEXT ===
        # Check for international audience indicators
        international_indicators = [
            'global', 'international', 'worldwide', 'multi-cultural', 
            'cross-cultural', 'diverse audience', 'inclusive'
        ]
        
        if any(indicator in text_lower for indicator in international_indicators):
            evidence_score += 0.1  # International context demands inclusivity
        
        return evidence_score

    def _apply_feedback_clues_pronouns(self, evidence_score: float, token, context: Dict[str, Any]) -> float:
        """
        Apply feedback patterns for pronoun detection.
        
        Incorporates learned patterns from user feedback including acceptance rates,
        context-specific patterns, role-based feedback, and replacement success rates
        to refine evidence scoring for gendered pronoun usage.
        
        Args:
            evidence_score: Current evidence score to modify
            token: The gendered pronoun token
            context: Document context dictionary
            
        Returns:
            float: Modified evidence score based on feedback analysis
        """
        
        feedback_patterns = self._get_cached_feedback_patterns_pronouns()
        
        # === TOKEN-SPECIFIC FEEDBACK ===
        token_text = getattr(token, 'text', '').lower()
        lemma_lower = getattr(token, 'lemma_', '').lower()
        
        # Check if this specific pronoun is commonly accepted by users
        accepted_pronouns = feedback_patterns.get('accepted_pronouns', set())
        if token_text in accepted_pronouns or lemma_lower in accepted_pronouns:
            evidence_score -= 0.3  # Users consistently accept this pronoun
        
        flagged_pronouns = feedback_patterns.get('flagged_pronouns', set())
        if token_text in flagged_pronouns or lemma_lower in flagged_pronouns:
            evidence_score += 0.3  # Users consistently flag this pronoun
        
        # === CONTEXT-SPECIFIC FEEDBACK ===
        content_type = context.get('content_type', 'general')
        context_patterns = feedback_patterns.get(f'{content_type}_pronoun_patterns', {})
        
        if token_text in context_patterns.get('acceptable', set()):
            evidence_score -= 0.2
        elif token_text in context_patterns.get('problematic', set()):
            evidence_score += 0.2
        
        # === ROLE-BASED FEEDBACK ===
        # Check if this pronoun appears in context with roles that users accept/reject
        sentence_text = token.sent.text.lower() if hasattr(token, 'sent') else ''
        
        role_patterns = feedback_patterns.get('role_based_patterns', {})
        for role, pattern_data in role_patterns.items():
            if role in sentence_text:
                if token_text in pattern_data.get('accepted_pronouns', set()):
                    evidence_score -= 0.2  # Users accept this pronoun with this role
                elif token_text in pattern_data.get('rejected_pronouns', set()):
                    evidence_score += 0.2  # Users reject this pronoun with this role
        
        # === FREQUENCY-BASED PATTERNS ===
        # Pattern: Frequency of this pronoun in documents
        pronoun_frequency = feedback_patterns.get('pronoun_frequencies', {}).get(token_text, 0)
        if pronoun_frequency > 50:  # Commonly seen pronoun
            acceptance_rate = feedback_patterns.get('pronoun_acceptance', {}).get(token_text, 0.5)
            if acceptance_rate > 0.7:
                evidence_score -= 0.2  # Frequently accepted
            elif acceptance_rate < 0.3:
                evidence_score += 0.2  # Frequently rejected
        
        # === REPLACEMENT SUCCESS PATTERNS ===
        # Check success rate of suggesting alternatives for this pronoun
        replacement_patterns = feedback_patterns.get('replacement_success', {})
        replacement_success = replacement_patterns.get(token_text, 0.5)
        
        if replacement_success > 0.8:
            evidence_score += 0.1  # Replacements highly successful
        elif replacement_success < 0.3:
            evidence_score -= 0.1  # Replacements often rejected
        
        return evidence_score

    def _get_cached_feedback_patterns_pronouns(self) -> Dict[str, Any]:
        """Load feedback patterns from cache or feedback analysis for pronouns."""
        # This would load from feedback analysis system
        # For now, return patterns based on common pronoun usage
        return {
            'accepted_pronouns': {
                # Pronouns commonly accepted by users in specific contexts
                # (This would be populated by actual feedback data)
            },
            'flagged_pronouns': {
                # Pronouns commonly flagged by users
                'his', 'her', 'he', 'him'  # Generally flagged in generic contexts
            },
            'technical_pronoun_patterns': {
                'acceptable': {
                    # Pronouns acceptable in technical contexts
                    # (Populated by feedback in technical documents)
                },
                'problematic': {
                    # Pronouns problematic even in technical contexts
                    'his', 'her', 'he', 'him'
                }
            },
            'procedural_pronoun_patterns': {
                'acceptable': {
                    # Pronouns acceptable in procedural contexts
                },
                'problematic': {
                    # Pronouns problematic in procedures
                    'his', 'her', 'he', 'him'
                }
            },
            'role_based_patterns': {
                'developer': {
                    'accepted_pronouns': set(),
                    'rejected_pronouns': {'his', 'her', 'he', 'him'}
                },
                'user': {
                    'accepted_pronouns': set(),
                    'rejected_pronouns': {'his', 'her', 'he', 'him'}
                },
                'administrator': {
                    'accepted_pronouns': set(),
                    'rejected_pronouns': {'his', 'her', 'he', 'him'}
                }
            },
            'pronoun_frequencies': {
                # Frequency of pronoun usage (would be calculated from corpus)
                'his': 100, 'her': 80, 'he': 90, 'him': 70
            },
            'pronoun_acceptance': {
                # Historical acceptance rates (would be calculated from feedback)
                'his': 0.2, 'her': 0.2, 'he': 0.1, 'him': 0.1
            },
            'replacement_success': {
                # Success rate of replacement suggestions
                'his': 0.8, 'her': 0.8, 'he': 0.9, 'him': 0.85
            }
        }

    # === HELPER METHODS FOR SEMANTIC ANALYSIS ===

    def _is_specification_documentation(self, text: str) -> bool:
        """Check if text appears to be specification documentation."""
        spec_indicators = [
            'specification', 'spec', 'standard', 'protocol', 'definition',
            'schema', 'format', 'syntax', 'implementation', 'reference',
            'requirements', 'compliance'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in spec_indicators if indicator in text_lower) >= 2

    def _is_policy_documentation(self, text: str) -> bool:
        """Check if text appears to be policy documentation."""
        policy_indicators = [
            'policy', 'policies', 'guideline', 'guidelines', 'standard',
            'standards', 'procedure', 'procedures', 'compliance', 'regulation',
            'code of conduct', 'best practice', 'governance'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in policy_indicators if indicator in text_lower) >= 2

    def _is_training_content(self, text: str) -> bool:
        """Check if text appears to be training content."""
        training_indicators = [
            'training', 'tutorial', 'course', 'lesson', 'workshop',
            'learning', 'education', 'instruction', 'guide', 'walkthrough',
            'getting started', 'how to', 'step by step'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in training_indicators if indicator in text_lower) >= 2

    def _is_user_documentation(self, text: str) -> bool:
        """Check if text appears to be user-facing documentation."""
        user_doc_indicators = [
            'user guide', 'user manual', 'help', 'documentation',
            'instructions', 'how to use', 'getting started', 'quick start',
            'user interface', 'end user', 'customer', 'client'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in user_doc_indicators if indicator in text_lower) >= 2

    def _is_api_documentation(self, text: str) -> bool:
        """Check if text appears to be API documentation."""
        api_indicators = [
            'api', 'endpoint', 'method', 'parameter', 'request', 'response',
            'authentication', 'authorization', 'rest', 'graphql', 'sdk',
            'integration', 'webhook', 'callback'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in api_indicators if indicator in text_lower) >= 3

    def _is_procedural_documentation(self, text: str) -> bool:
        """Check if text appears to be procedural documentation."""
        procedural_indicators = [
            'procedure', 'step', 'process', 'workflow', 'instruction',
            'follow', 'complete', 'perform', 'execute', 'configure',
            'install', 'setup', 'deploy'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in procedural_indicators if indicator in text_lower) >= 3

    def _is_international_documentation(self, text: str) -> bool:
        """Check if text appears to be for international audiences."""
        international_indicators = [
            'global', 'international', 'worldwide', 'multi-national',
            'cross-cultural', 'diverse', 'inclusive', 'accessibility',
            'localization', 'translation', 'multilingual'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in international_indicators if indicator in text_lower) >= 2

    # === HELPER METHODS FOR SMART MESSAGING ===

    def _get_contextual_pronouns_message(self, token, evidence_score: float, sentence) -> str:
        """Generate context-aware error messages for pronoun patterns."""
        
        token_text = getattr(token, 'text', '')
        lemma_lower = getattr(token, 'lemma_', '').lower()
        
        if evidence_score > 0.9:
            return f"Gender-specific pronoun '{token_text}' used in a generic or instructional context. Prefer inclusive alternatives."
        elif evidence_score > 0.7:
            return f"Gender-specific pronoun '{token_text}' detected. Consider using inclusive language."
        elif evidence_score > 0.5:
            return f"Consider replacing '{token_text}' with a gender-neutral alternative for broader inclusivity."
        else:
            return f"The pronoun '{token_text}' may benefit from a gender-neutral alternative."

    def _generate_smart_pronouns_suggestions(self, token, evidence_score: float, sentence, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for pronoun patterns."""
        
        suggestions = []
        token_text = getattr(token, 'text', '')
        lemma_lower = getattr(token, 'lemma_', '').lower()
        
        # Base suggestions based on evidence strength and pronoun type
        if evidence_score > 0.8:
            # High evidence - provide specific alternatives
            if lemma_lower in ['his', 'her']:
                suggestions.append("Use 'their' as a gender-neutral possessive alternative.")
            elif lemma_lower in ['he', 'she']:
                suggestions.append("Use 'they' as a gender-neutral subject pronoun.")
            elif lemma_lower in ['him', 'her']:
                suggestions.append("Use 'them' as a gender-neutral object pronoun.")
            
            suggestions.append("Address the reader directly as 'you' when giving instructions.")
        else:
            # Lower evidence - provide general guidance
            suggestions.append("Use 'they/them/their' where grammatically appropriate.")
            suggestions.append("Address the reader as 'you' when giving instructions.")
        
        # Context-specific advice
        if context:
            content_type = context.get('content_type', 'general')
            
            if content_type in ['technical', 'api', 'procedural']:
                suggestions.append("Technical writing should use inclusive pronouns consistently.")
            elif content_type in ['academic', 'legal']:
                suggestions.append("Formal writing benefits from gender-neutral language.")
            elif content_type == 'tutorial':
                suggestions.append("Training materials should be accessible to all learners.")
        
        # Structural alternatives
        if evidence_score > 0.6:
            suggestions.append("Rewrite to remove the pronoun by repeating the noun or restructuring the clause.")
        
        return suggestions[:3]
