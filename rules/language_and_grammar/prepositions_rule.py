"""
Prepositions Rule
Based on IBM Style Guide topic: "Prepositions"

Evidence-Based Implementation:
- Analyzes prepositional density and complexity in sentences
- Provides nuanced scoring based on linguistic, structural, semantic, and feedback clues
- Considers context-specific acceptability of prepositional phrases
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc, Span, Token
except ImportError:
    Doc = None
    Span = None
    Token = None

class PrepositionsRule(BaseLanguageRule):
    """
    Evidence-based rule for analyzing prepositional phrase density and complexity.
    
    This rule identifies sentences that may be overly complex due to excessive
    prepositional phrases while considering writing context, audience, and domain
    to provide nuanced evidence scoring rather than binary flagging.
    
    The rule follows the 5-step evidence pattern:
    1. Base evidence assessment (prepositional density and chaining)
    2. Linguistic clues (sentence structure, verb patterns, objects)
    3. Structural clues (document blocks, lists, headings, code)
    4. Semantic clues (content type, domain, audience, purpose)
    5. Feedback patterns (learned user acceptance/rejection patterns)
    """
    
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'prepositions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for excessive prepositional phrasing.
        
        Calculates a nuanced evidence score per sentence that considers
        linguistic density, chaining, sentence complexity, structure,
        semantics, and learned feedback patterns.
        
        Args:
            text: Full document text for context analysis
            sentences: List of sentence strings (unused, we use spacy sentences)
            nlp: SpaCy NLP pipeline for linguistic analysis
            context: Document context including block_type, content_type, domain, audience
            
        Returns:
            List of error dictionaries with evidence scores and contextual messaging
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        doc = nlp(text)

        for i, sent in enumerate(doc.sents):
            evidence_score = self._calculate_preposition_evidence(sent, text, context or {})

            if evidence_score > 0.1:  # Universal low threshold
                preposition_count = self._count_prepositions(sent)
                message = self._get_contextual_prepositions_message(preposition_count, evidence_score, context or {})
                suggestions = self._generate_smart_prepositions_suggestions(preposition_count, evidence_score, sent, context or {})

                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message=message,
                    suggestions=suggestions,
                    severity='low',
                    text=text,
                    context=context,
                    evidence_score=evidence_score,
                    span=(sent.start_char, sent.end_char),
                    flagged_text=sent.text
                ))

        return errors

    # === EVIDENCE-BASED CALCULATION METHODS ===

    def _calculate_preposition_evidence(self, sentence: 'Span', text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for prepositional phrase overuse.
        
        Implements the 5-step evidence pattern to assess whether a sentence
        has problematic prepositional density based on linguistic patterns,
        document structure, semantic context, and learned feedback.
        
        Args:
            sentence: SpaCy sentence span to analyze
            text: Full document text for broader context
            context: Document context (block_type, content_type, domain, audience)
            
        Returns:
            float: Evidence score from 0.0 (no issue) to 1.0 (strong evidence of problem)
        """
        evidence_score: float = 0.0

        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_preposition_evidence(sentence)
        if evidence_score == 0.0:
            return 0.0  # No baseline evidence, skip further analysis

        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_prepositions(evidence_score, sentence)

        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_prepositions(evidence_score, context)

        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_prepositions(evidence_score, text, context)

        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_prepositions(evidence_score, sentence, context)

        return max(0.0, min(1.0, evidence_score))

    def _get_base_preposition_evidence(self, sentence: 'Span') -> float:
        """
        Calculate base evidence score from prepositional density and chaining patterns.
        
        Establishes the foundation evidence score based on objective metrics:
        - Raw prepositional count vs sentence length
        - Prepositional phrase chaining complexity
        - Nested prepositional structures
        
        Args:
            sentence: SpaCy sentence span to analyze
            
        Returns:
            float: Base evidence score (0.0 if no issue, 0.3-0.8 for concerning patterns)
        """
        preposition_count = self._count_prepositions(sentence)
        token_count = max(1, len([t for t in sentence if not getattr(t, 'is_space', False)]))
        density = preposition_count / token_count

        # No evidence for low prepositional counts
        if preposition_count <= 2:
            return 0.0

        # Base evidence from count and density with conservative scaling
        # 3 prepositions = ~0.3, 4 = ~0.4, 5+ with high density can reach 0.7-0.8
        evidence_score = min(0.8, 0.1 * preposition_count + 0.5 * density)

        # Chaining bonus: consecutive prepositions or nested attachments
        chain_factor = self._estimate_preposition_chain_factor(sentence)
        evidence_score += min(0.25, chain_factor)

        return evidence_score

    def _apply_linguistic_clues_prepositions(self, evidence_score: float, sentence: 'Span') -> float:
        """
        Apply micro-level linguistic clues that affect prepositional phrase acceptability.
        
        Analyzes SpaCy-derived linguistic features:
        - Sentence length and complexity
        - Objects of prepositions (pobj) density
        - Nominal modification patterns
        - Finite verb distribution
        - Dependency parsing patterns
        - Morphological features
        
        Args:
            evidence_score: Current evidence score to modify
            sentence: SpaCy sentence span for linguistic analysis
            
        Returns:
            float: Modified evidence score based on linguistic patterns
        """
        tokens = [t for t in sentence if not getattr(t, 'is_space', False)]
        token_count = len(tokens)

        # Long sentence length increases impact of prepositional density
        if token_count > 25:
            evidence_score += 0.1
        if token_count > 40:
            evidence_score += 0.05

        # Many objects of prepositions increase evidence
        pobj_tokens = [t for t in tokens if getattr(t, 'dep_', '') == 'pobj']
        if len(pobj_tokens) >= 3:
            evidence_score += 0.1
        if len(pobj_tokens) >= 5:
            evidence_score += 0.05

        # Multiple nominal modifiers with ADP chains indicate complexity
        nmod_like = sum(1 for t in tokens if getattr(t, 'dep_', '') in {'nmod', 'npmod'})
        if nmod_like >= 2:
            evidence_score += 0.05
        if nmod_like >= 4:
            evidence_score += 0.05

        # Complex dependency chains (prep -> pobj -> prep -> pobj)
        prep_pobj_chains = self._count_prep_pobj_chains(sentence)
        if prep_pobj_chains >= 2:
            evidence_score += 0.08

        # Multiple finite verbs reduce harm of prepositional density
        finite_verbs = [t for t in tokens if (getattr(t, 'pos_', '') == 'VERB' and 
                       getattr(t, 'morph', None) and 'Tense=' in str(t.morph))]
        if len(finite_verbs) >= 2:
            evidence_score -= 0.05
        if len(finite_verbs) >= 3:
            evidence_score -= 0.03

        # Passive voice constructions often require prepositional clarity
        passive_indicators = [t for t in tokens if (getattr(t, 'tag_', '') in ['VBN'] and
                             any(getattr(h, 'lemma_', '') in ['be', 'get'] for h in [getattr(t, 'head', None)] if h))]
        if passive_indicators:
            evidence_score -= 0.05

        # Gerund constructions often naturally use prepositions
        gerund_count = sum(1 for t in tokens if getattr(t, 'tag_', '') == 'VBG')
        if gerund_count >= 2:
            evidence_score -= 0.03

        # Coordinated structures may justify prepositional repetition
        coordination_markers = sum(1 for t in tokens if getattr(t, 'dep_', '') in ['cc', 'conj'])
        if coordination_markers >= 2:
            evidence_score -= 0.05

        # Named entities often require prepositional precision
        entity_tokens = [t for t in tokens if getattr(t, 'ent_type_', '')]
        if entity_tokens:
            for token in entity_tokens:
                ent_type = getattr(token, 'ent_type_', '')
                if ent_type in ['ORG', 'PRODUCT', 'GPE']:
                    evidence_score -= 0.02  # Organizations, products, places need precision
                elif ent_type in ['PERSON', 'MONEY', 'DATE']:
                    evidence_score -= 0.01  # Other entities may need prepositional clarity

        return evidence_score

    def _apply_structural_clues_prepositions(self, evidence_score: float, context: Dict[str, Any]) -> float:
        """
        Apply meso-level structural clues from document organization.
        
        Considers how document structure affects acceptability of prepositional density:
        - Code blocks (very permissive)
        - Tables and lists (somewhat permissive)
        - Headings (titles often use prepositions)
        - Admonitions (context-dependent)
        - Quote and citation blocks
        
        Args:
            evidence_score: Current evidence score to modify
            context: Document context including block_type, block_level, admonition_type
            
        Returns:
            float: Modified evidence score based on structural context
        """
        block_type = context.get('block_type', 'paragraph')

        # Code-related blocks are very permissive (technical precision)
        if block_type in {'code_block', 'literal_block'}:
            evidence_score -= 0.6
        elif block_type == 'inline_code':
            evidence_score -= 0.4

        # Tabular data often requires prepositional precision
        elif block_type in {'table_cell', 'table_header'}:
            evidence_score -= 0.2

        # List items often use shorthand with prepositions
        elif block_type in {'ordered_list_item', 'unordered_list_item'}:
            evidence_score -= 0.1
            # Nested lists are more technical and permissive
            list_depth = context.get('list_depth', 1)
            if list_depth > 1:
                evidence_score -= 0.05

        # Headings often use prepositional phrases for clarity
        elif block_type == 'heading':
            evidence_score -= 0.15
            # Higher-level headings are more permissive
            heading_level = context.get('block_level', 1)
            if heading_level <= 2:
                evidence_score -= 0.05

        # Admonition context varies by type
        elif block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in {'WARNING', 'CAUTION', 'IMPORTANT'}:
                evidence_score += 0.05  # Prefer clarity in warnings
            elif admonition_type in {'NOTE', 'TIP', 'HINT'}:
                evidence_score -= 0.05  # More conversational

        # Quotes and citations may have different style conventions
        elif block_type in {'block_quote', 'citation'}:
            evidence_score -= 0.1

        # Sidebar and callout content often condensed
        elif block_type in {'sidebar', 'callout'}:
            evidence_score -= 0.1

        return evidence_score

    def _apply_semantic_clues_prepositions(self, evidence_score: float, text: str, context: Dict[str, Any]) -> float:
        """
        Apply macro-level semantic clues from content meaning and purpose.
        
        Analyzes high-level document characteristics:
        - Content type (technical vs marketing vs legal)
        - Domain expertise requirements
        - Target audience sophistication
        - Document purpose and goals
        - International context considerations
        - Consistency with document style
        
        Args:
            evidence_score: Current evidence score to modify
            text: Full document text for analysis
            context: Document context including content_type, domain, audience
            
        Returns:
            float: Modified evidence score based on semantic context
        """
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')

        # Content type adjustments
        if content_type in {'technical', 'api'}:
            evidence_score -= 0.05  # Technical writing often needs prepositional precision
        elif content_type in {'tutorial', 'how-to'}:
            evidence_score -= 0.03  # Step-by-step instructions use prepositions
        elif content_type in {'marketing', 'procedural'}:
            evidence_score += 0.05  # Prefer shorter, directive sentences
        elif content_type == 'legal':
            evidence_score += 0.1  # Legal writing should be precise but clear
        elif content_type == 'academic':
            evidence_score -= 0.03  # Academic writing often complex

        # Domain-specific adjustments
        if domain in {'finance', 'legal', 'medical'}:
            evidence_score += 0.05  # Formal domains prefer clarity
        elif domain in {'software', 'engineering', 'devops'}:
            evidence_score -= 0.05  # Technical domains accept complexity
        elif domain in {'scientific', 'research'}:
            evidence_score -= 0.03  # Research writing often detailed

        # Audience sophistication adjustments
        if audience in {'beginner', 'general', 'consumer'}:
            evidence_score += 0.05  # General audience needs simpler sentences
        elif audience in {'developer', 'expert', 'professional'}:
            evidence_score -= 0.05  # Expert audience handles complexity
        elif audience in {'business', 'academic'}:
            evidence_score -= 0.02  # Professional audiences somewhat tolerant

        # Document purpose detection
        if self._is_installation_documentation(text):
            evidence_score -= 0.03  # Installation steps often use prepositions
        elif self._is_troubleshooting_documentation(text):
            evidence_score += 0.03  # Troubleshooting should be clear and direct
        elif self._is_api_documentation(text):
            evidence_score -= 0.05  # API docs need prepositional precision
        elif self._is_policy_documentation(text):
            evidence_score += 0.05  # Policy docs should be clear and accessible
        elif self._is_specification_documentation(text):
            evidence_score -= 0.03  # Specifications often detailed
        elif self._is_user_documentation(text):
            evidence_score += 0.03  # User docs should be accessible

        # Document length context
        doc_length = len(text.split())
        if doc_length > 3000:
            evidence_score += 0.03  # Longer docs benefit from sentence clarity
        elif doc_length < 500:
            evidence_score -= 0.02  # Short docs can be denser

        # International audience considerations
        if self._is_international_documentation(context):
            evidence_score += 0.05  # International readers prefer simpler structures

        return evidence_score

    def _apply_feedback_clues_prepositions(self, evidence_score: float, sentence: 'Span', context: Dict[str, Any]) -> float:
        """
        Apply learning clues from historical user feedback patterns.
        
        Incorporates patterns learned from user acceptance/rejection:
        - Phrase-specific acceptance rates
        - Context-specific patterns
        - Content-type specific feedback
        - Frequency-based adjustments
        - Replacement success patterns
        
        Args:
            evidence_score: Current evidence score to modify
            sentence: SpaCy sentence span for pattern matching
            context: Document context for pattern lookup
            
        Returns:
            float: Modified evidence score based on learned feedback patterns
        """
        feedback = self._get_cached_feedback_patterns('prepositions')
        sent_lower = sentence.text.lower()

        # Phrase-specific feedback patterns
        accepted_phrases = feedback.get('accepted_phrases', set())
        if any(phrase in sent_lower for phrase in accepted_phrases):
            evidence_score -= 0.1

        flagged_phrases = feedback.get('flagged_phrases', set())
        if any(phrase in sent_lower for phrase in flagged_phrases):
            evidence_score += 0.1

        # Context-specific feedback patterns
        content_type = context.get('content_type', 'general')
        content_patterns = feedback.get(f'{content_type}_patterns', {})
        
        accepted_in_context = content_patterns.get('accepted', set())
        if any(phrase in sent_lower for phrase in accepted_in_context):
            evidence_score -= 0.1
            
        flagged_in_context = content_patterns.get('flagged', set())
        if any(phrase in sent_lower for phrase in flagged_in_context):
            evidence_score += 0.1

        # Domain-specific feedback
        domain = context.get('domain', 'general')
        domain_patterns = feedback.get(f'{domain}_patterns', {})
        
        if any(phrase in sent_lower for phrase in domain_patterns.get('accepted', set())):
            evidence_score -= 0.08
        if any(phrase in sent_lower for phrase in domain_patterns.get('flagged', set())):
            evidence_score += 0.08

        # Frequency-based adjustment for common patterns
        preposition_density = self._count_prepositions(sentence) / max(1, len(sentence))
        density_ranges = feedback.get('density_acceptance', {})
        
        for density_range, acceptance_rate in density_ranges.items():
            if self._density_in_range(preposition_density, density_range):
                if acceptance_rate > 0.7:
                    evidence_score -= 0.05  # High acceptance for this density
                elif acceptance_rate < 0.3:
                    evidence_score += 0.05  # Low acceptance for this density

        # Block type specific feedback
        block_type = context.get('block_type', 'paragraph')
        block_patterns = feedback.get(f'{block_type}_patterns', {})
        
        if any(phrase in sent_lower for phrase in block_patterns.get('accepted', set())):
            evidence_score -= 0.05
        if any(phrase in sent_lower for phrase in block_patterns.get('flagged', set())):
            evidence_score += 0.05

        return evidence_score

    # === LINGUISTIC ANALYSIS HELPERS ===

    def _count_prepositions(self, sentence: 'Span') -> int:
        """
        Count prepositions (ADP part-of-speech) in sentence.
        
        Args:
            sentence: SpaCy sentence span
            
        Returns:
            int: Number of prepositional tokens
        """
        return sum(1 for token in sentence if getattr(token, 'pos_', '') == 'ADP')

    def _estimate_preposition_chain_factor(self, sentence: 'Span') -> float:
        """
        Estimate added complexity from chained/nested prepositional phrases.
        
        Analyzes patterns like "in response to requests from users in the system"
        which create complex dependency chains that can reduce readability.
        
        Args:
            sentence: SpaCy sentence span
            
        Returns:
            float: Chaining complexity factor (0.0-0.4)
        """
        if not sentence:
            return 0.0

        # Longest run of consecutive ADP tokens
        longest_run = 0
        current_run = 0
        pobj_count = 0
        nested_links = 0

        for token in sentence:
            if getattr(token, 'pos_', '') == 'ADP':
                current_run += 1
                longest_run = max(longest_run, current_run)
            else:
                current_run = 0

            if getattr(token, 'dep_', '') == 'pobj':
                pobj_count += 1

            # Count nesting if a preposition depends on an object of a preposition
            head = getattr(token, 'head', None)
            if (head is not None and 
                getattr(token, 'pos_', '') == 'ADP' and 
                getattr(head, 'dep_', '') == 'pobj'):
                nested_links += 1

        # Scale contributions
        return min(0.15 * max(0, longest_run - 1) + 0.02 * pobj_count + 0.05 * nested_links, 0.4)

    def _count_prep_pobj_chains(self, sentence: 'Span') -> int:
        """
        Count prepositional phrase chains (prep -> pobj -> prep -> pobj).
        
        Args:
            sentence: SpaCy sentence span
            
        Returns:
            int: Number of prepositional chains found
        """
        chains = 0
        for token in sentence:
            if (getattr(token, 'pos_', '') == 'ADP' and
                hasattr(token, 'children')):
                # Look for pobj child that has ADP children
                for child in token.children:
                    if (getattr(child, 'dep_', '') == 'pobj' and
                        hasattr(child, 'children')):
                        for grandchild in child.children:
                            if getattr(grandchild, 'pos_', '') == 'ADP':
                                chains += 1
                                break
        return chains

    def _density_in_range(self, density: float, range_spec: str) -> bool:
        """
        Check if prepositional density falls within specified range.
        
        Args:
            density: Calculated prepositional density (0.0-1.0)
            range_spec: Range specification like "0.2-0.3" or "0.4+"
            
        Returns:
            bool: Whether density falls in specified range
        """
        try:
            if '-' in range_spec:
                low, high = map(float, range_spec.split('-'))
                return low <= density <= high
            elif range_spec.endswith('+'):
                threshold = float(range_spec[:-1])
                return density >= threshold
            else:
                return False
        except (ValueError, IndexError):
            return False

    # === SEMANTIC ANALYSIS HELPERS ===

    # Removed _is_installation_documentation - using base class utility

    # Removed _is_troubleshooting_documentation - using base class utility

    # Removed _is_api_documentation - using base class utility

    # Removed _is_policy_documentation - using base class utility

    # Removed _is_specification_documentation - using base class utility

    # Removed _is_user_documentation - using base class utility

    def _is_international_documentation(self, context: Dict[str, Any]) -> bool:
        """
        Detect if content targets international/non-native English audiences.
        
        International docs should use simpler sentence structures.
        
        Args:
            context: Document context
            
        Returns:
            bool: True if international audience detected
        """
        audience = context.get('audience', '')
        domain = context.get('domain', '')
        return (audience in {'international', 'global'} or
                'global' in domain or 'international' in domain)

    # Removed _get_cached_feedback_patterns_prepositions - using base class utility

    # === SMART MESSAGING AND SUGGESTIONS ===

    def _get_contextual_prepositions_message(self, preposition_count: int, evidence_score: float, context: Dict[str, Any]) -> str:
        """
        Generate context-aware error message for prepositional overuse.
        
        Tailors the message based on evidence strength, context, and audience
        to provide meaningful feedback that respects the writing situation.
        
        Args:
            preposition_count: Number of prepositions in sentence
            evidence_score: Calculated evidence score
            context: Document context for message customization
            
        Returns:
            str: Contextual error message
        """
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        
        if evidence_score > 0.8:
            if content_type in {'technical', 'api'}:
                return f"High prepositional density ({preposition_count}) may reduce technical clarity. Consider restructuring for better comprehension."
            elif audience in {'beginner', 'general'}:
                return f"Sentence has many prepositional phrases ({preposition_count}) that may confuse readers. Consider simplifying."
            else:
                return f"High prepositional density ({preposition_count}) may reduce clarity. Consider restructuring."
                
        elif evidence_score > 0.5:
            if content_type == 'marketing':
                return f"Sentence has many prepositional phrases ({preposition_count}). Consider shorter, more direct phrasing."
            elif content_type == 'legal':
                return f"Complex prepositional structure ({preposition_count} phrases) may affect accessibility. Consider clarification."
            else:
                return f"Sentence has many prepositional phrases ({preposition_count}). Consider simplifying."
                
        else:
            if audience in {'beginner', 'general'}:
                return f"Consider reducing prepositional phrases (count: {preposition_count}) to improve readability for general audiences."
            else:
                return f"Consider reducing prepositional phrases (count: {preposition_count}) to improve readability."

    def _generate_smart_prepositions_suggestions(self, preposition_count: int, evidence_score: float, sentence: 'Span', context: Dict[str, Any]) -> List[str]:
        """
        Generate context-aware suggestions for reducing prepositional complexity.
        
        Provides actionable suggestions that consider the document type,
        audience, and specific prepositional patterns found in the sentence.
        
        Args:
            preposition_count: Number of prepositions in sentence
            evidence_score: Calculated evidence score
            sentence: SpaCy sentence span for pattern analysis
            context: Document context for suggestion customization
            
        Returns:
            List[str]: Context-appropriate suggestions for improvement
        """
        suggestions: List[str] = []
        sent_text = sentence.text
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')

        # High evidence cases need restructuring
        if evidence_score > 0.7:
            if content_type in {'technical', 'api'}:
                suggestions.append("Split into two sentences focusing on the main technical concept first, then supporting details.")
            elif audience in {'beginner', 'general'}:
                suggestions.append("Break this into simpler sentences that introduce one concept at a time.")
            else:
                suggestions.append("Split the sentence into two shorter sentences focusing on the main action.")

        # Replace common verbose patterns
        if 'in order to' in sent_text.lower():
            suggestions.append("Replace 'in order to' with 'to' for conciseness.")

        if 'due to the fact that' in sent_text.lower():
            suggestions.append("Replace 'due to the fact that' with 'because' for clarity.")

        if 'for the purpose of' in sent_text.lower():
            suggestions.append("Replace 'for the purpose of' with 'to' for directness.")

        # Convert 'of' chains to possessives when appropriate
        if ' of the ' in sent_text.lower() or ' of a ' in sent_text.lower():
            if content_type not in {'legal', 'academic'}:  # Legal/academic may prefer 'of' constructions
                suggestions.append("Where possible, convert 'of' phrases to possessives or adjectives (e.g., 'the system's configuration' instead of 'the configuration of the system').")

        # Nominalization to verb conversion
        if preposition_count >= 4:
            suggestions.append("Prefer active verbs over noun phrases to reduce prepositional dependencies (e.g., 'The report lists' instead of 'The report is a list of').")

        # Context-specific suggestions
        if content_type == 'api' and 'parameter' in sent_text.lower():
            suggestions.append("Consider using a bulleted list to describe multiple parameters instead of linking them with prepositions.")

        if content_type == 'tutorial' and preposition_count >= 3:
            suggestions.append("Break procedural steps into numbered items to reduce prepositional complexity.")

        if audience in {'international', 'global'} and evidence_score > 0.5:
            suggestions.append("Use shorter sentences with familiar prepositions to improve comprehension for international readers.")

        # Coordination suggestion for complex sentences
        if evidence_score > 0.6:
            suggestions.append("Consider using coordinating conjunctions (and, but, or) to link related ideas instead of embedding them in prepositional phrases.")

        # Limit to most relevant suggestions
        return suggestions[:3]
