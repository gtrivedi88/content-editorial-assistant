"""
Adverbs - only Rule
Based on IBM Style Guide topic: "Adverbs - only"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class AdverbsOnlyRule(BaseLanguageRule):
    """
    Checks for the word "only" and advises the user to review its placement
    to ensure the meaning of the sentence is clear and unambiguous.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'adverbs_only'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for potentially ambiguous placement of "only" using evidence-based scoring.
        Uses sophisticated linguistic analysis to distinguish clear usage from ambiguous placement.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        for i, sent in enumerate(doc.sents):
            for token in sent:
                if token.lemma_ == 'only':
                    # Calculate evidence score for potential ambiguity
                    evidence_score = self._calculate_only_ambiguity_evidence(
                        token, sent, text, context
                    )
                    
                    # Only create error if evidence suggests potential ambiguity
                    if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=self._get_contextual_message(token, evidence_score),
                            suggestions=self._generate_smart_suggestions(token, evidence_score, context),
                            severity='low',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,  # Your nuanced assessment
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
        return errors

    # === EVIDENCE-BASED CALCULATION METHODS ===

    def _calculate_only_ambiguity_evidence(self, token, sentence, text: str, context: dict) -> float:
        """
        Calculate evidence score (0.0-1.0) for potential "only" placement ambiguity.
        
        Higher scores indicate stronger evidence of potential ambiguity.
        Lower scores indicate clear, unambiguous placement.
        
        Args:
            token: The "only" token
            sentence: Sentence containing the token
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (no ambiguity) to 1.0 (highly ambiguous)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        if token.lemma_ == 'only':
            evidence_score = 0.5  # Start with moderate evidence for any "only"
        else:
            return 0.0  # No evidence, skip this token
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_only(evidence_score, token, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_only(evidence_score, token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_only(evidence_score, token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_only(evidence_score, token, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    # === LINGUISTIC CLUES (MICRO-LEVEL) ===

    def _apply_linguistic_clues_only(self, evidence_score: float, token, sentence) -> float:
        """Apply SpaCy-based linguistic analysis clues for "only" placement ambiguity."""
        
        # === POSITIONAL ANALYSIS ===
        # Get position within sentence
        sent_tokens = list(sentence)
        token_position = None
        for i, sent_token in enumerate(sent_tokens):
            if sent_token.i == token.i:
                token_position = i
                break
        
        if token_position is not None:
            sentence_length = len(sent_tokens)
            relative_position = token_position / sentence_length if sentence_length > 0 else 0
            
            # "Only" at sentence beginning is often clear (restrictive meaning)
            if relative_position < 0.2:  # First 20% of sentence
                evidence_score -= 0.3  # "Only developers can access..."
            
            # "Only" in middle of sentence more likely ambiguous
            elif 0.3 < relative_position < 0.7:  # Middle 40% of sentence
                evidence_score += 0.2  # "Developers only can access..." - ambiguous
            
            # "Only" near end may be unclear
            elif relative_position > 0.8:  # Last 20% of sentence
                evidence_score += 0.1  # "Developers can access only" - might be unclear
        
        # === DEPENDENCY ANALYSIS ===
        # Check what "only" modifies
        only_children = list(token.children)
        only_head = token.head
        
        # "Only" modifying a noun phrase (clearer)
        if token.dep_ == 'advmod' and only_head.pos_ in ['NOUN', 'PRON']:
            evidence_score -= 0.2  # "only administrators", "only this feature"
        
        # "Only" modifying a verb (potentially ambiguous)
        elif token.dep_ == 'advmod' and only_head.pos_ == 'VERB':
            evidence_score += 0.1  # "only supports" vs "supports only"
        
        # "Only" with unclear dependency relationship
        elif token.dep_ in ['ROOT', 'nsubj']:
            evidence_score += 0.3  # Grammatically unclear
        
        # === ADJACENT WORD ANALYSIS ===
        prev_token = token.nbor(-1) if token.i > 0 else None
        next_token = token.nbor(1) if token.i < len(token.doc) - 1 else None
        
        # Clear patterns with "only"
        if prev_token:
            if prev_token.lemma_ in ['the', 'an', 'a']:
                evidence_score -= 0.2  # "the only way" - clear
            elif prev_token.pos_ == 'VERB':
                evidence_score += 0.1  # "supports only" - could be clearer
            
            # Enhanced morphological analysis of previous token
            if hasattr(prev_token, 'morph') and prev_token.morph:
                morph_str = str(prev_token.morph)
                if 'VerbForm=Fin' in morph_str:  # Finite verb
                    evidence_score += 0.05  # "processes only" - could be clearer
                elif 'VerbForm=Inf' in morph_str:  # Infinitive
                    evidence_score -= 0.05  # "to only process" - clearer
        
        if next_token:
            if next_token.pos_ in ['NOUN', 'PRON', 'PROPN']:
                evidence_score -= 0.2  # "only users", "only John" - clear
            elif next_token.lemma_ in ['if', 'when', 'because']:
                evidence_score -= 0.1  # "only if condition" - clear conditional
            elif next_token.pos_ == 'VERB':
                evidence_score += 0.2  # "only run" vs "run only" - ambiguous
            
            # Enhanced morphological analysis of next token
            if hasattr(next_token, 'morph') and next_token.morph:
                morph_str = str(next_token.morph)
                if 'Number=Sing' in morph_str and next_token.pos_ == 'NOUN':
                    evidence_score -= 0.05  # "only user" - clear singular
                elif 'Number=Plur' in morph_str and next_token.pos_ == 'NOUN':
                    evidence_score -= 0.1  # "only users" - clear plural
                
                # Check for definite/indefinite articles effect
                if 'Definite=Def' in morph_str:
                    evidence_score -= 0.05  # Definite forms clearer
        
        # === ENHANCED POS TAG ANALYSIS ===
        # More detailed part-of-speech analysis
        if hasattr(token, 'tag_'):
            if token.tag_ == 'RB':  # Adverb
                evidence_score -= 0.1  # Standard adverbial use
            elif token.tag_ == 'JJ':  # Adjective (rare but possible)
                evidence_score += 0.2  # Unusual usage, potentially ambiguous
        
        # === ENHANCED ENTITY TYPE ANALYSIS ===
        # Check if "only" is near named entities
        if hasattr(next_token, 'ent_type_') and next_token.ent_type_:
            if next_token.ent_type_ in ['PERSON', 'ORG', 'PRODUCT']:
                evidence_score -= 0.15  # "only Microsoft" - clear entity restriction
            elif next_token.ent_type_ in ['CARDINAL', 'ORDINAL']:
                evidence_score -= 0.1  # "only three", "only first" - clear numeric
        
        if prev_token and hasattr(prev_token, 'ent_type_') and prev_token.ent_type_:
            if prev_token.ent_type_ in ['VERB', 'ACTION']:
                evidence_score += 0.05  # Action + only might be ambiguous
        
        # === SENTENCE COMPLEXITY ===
        # Simple sentences with "only" are usually clearer
        sentence_complexity = len([t for t in sentence if t.pos_ == 'VERB'])
        if sentence_complexity == 1:  # Single verb
            evidence_score -= 0.1  # Simple sentence likely clear
        elif sentence_complexity > 2:  # Multiple verbs
            evidence_score += 0.2  # Complex sentence increases ambiguity
        
        # Check for compound phrases that increase complexity
        if any(child.dep_ in ['conj', 'cc'] for child in sentence):
            evidence_score += 0.1  # Conjunctions increase complexity
        
        return evidence_score

    def _apply_structural_clues_only(self, evidence_score: float, token, context: dict) -> float:
        """Apply document structure-based clues for "only" placement."""
        
        if not context:
            return evidence_score
        
        block_type = context.get('block_type', 'paragraph')
        
        # === TECHNICAL WRITING CONTEXTS ===
        # In technical writing, "only" is often unambiguous
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.8  # Code context has different syntax
        elif block_type == 'inline_code':
            evidence_score -= 0.6  # Technical inline context
        
        # API documentation often uses clear "only" patterns
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.3  # Tables often use concise, clear language
        
        # === HEADING CONTEXTS ===
        # Headlines and headings use "only" more deliberately
        elif block_type == 'heading':
            heading_level = context.get('block_level', 1)
            if heading_level <= 2:  # Main/section headings
                evidence_score -= 0.4  # "Only Enterprise Features"
            else:  # Subsection headings
                evidence_score -= 0.2  # Still clearer than body text
        
        # === LIST CONTEXTS ===
        # Lists often use "only" for clear restrictions
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.3  # "• Only available to premium users"
            
            # Nested lists are more technical/detailed
            if context.get('list_depth', 1) > 1:
                evidence_score -= 0.1  # More specific, often clearer
        
        # === ADMONITION CONTEXTS ===
        # Notes, warnings, etc. often use "only" clearly
        elif block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'WARNING', 'IMPORTANT']:
                evidence_score -= 0.2  # Clear restrictive meaning
        
        return evidence_score

    def _apply_semantic_clues_only(self, evidence_score: float, token, text: str, context: dict) -> float:
        """Apply semantic and content-type clues for "only" usage."""
        
        if not context:
            return evidence_score
        
        content_type = context.get('content_type', 'general')
        
        # === CONTENT TYPE ANALYSIS ===
        # Use helper methods for enhanced content type analysis
        if self._is_api_documentation(text):
            evidence_score -= 0.3  # API docs use "only" for clear restrictions
        elif self._is_procedural_documentation(text):
            evidence_score -= 0.2  # Procedural docs use "only" precisely
        elif self._is_reference_documentation(text):
            evidence_score -= 0.2  # Reference docs use "only" for specifications
        elif self._is_troubleshooting_documentation(text):  # Use base class method
            evidence_score -= 0.1  # Troubleshooting often uses "only" for conditions
        elif self._is_installation_documentation(text):
            evidence_score -= 0.2  # Installation docs use "only" for requirements
        elif self._is_configuration_documentation(text):
            evidence_score -= 0.2  # Config docs use "only" for settings
        
        # General technical content analysis
        elif content_type == 'technical':
            evidence_score -= 0.2  # Technical writing more precise
            
            # Check for technical patterns nearby
            if self._has_technical_context_words(token.sent.text, distance=5):
                evidence_score -= 0.2  # "only supports HTTPS", "read-only access"
        
        # Procedural content uses "only" for clear restrictions
        elif content_type == 'procedural':
            evidence_score -= 0.2  # Step-by-step instructions are precise
        
        # Marketing content may use "only" more creatively
        elif content_type == 'marketing':
            evidence_score += 0.1  # Marketing may be less precise
        
        # Legal content typically uses "only" precisely
        elif content_type == 'legal':
            evidence_score -= 0.3  # Legal writing very precise
        
        # Academic content generally careful with "only"
        elif content_type == 'academic':
            evidence_score -= 0.1  # Academic writing careful
        
        # === DOMAIN-SPECIFIC PATTERNS ===
        domain = context.get('domain', 'general')
        if domain in ['software', 'engineering', 'devops']:
            evidence_score -= 0.2  # Technical domains use "only" precisely
        elif domain in ['api', 'documentation']:
            evidence_score -= 0.3  # API docs use "only" for clear restrictions
        
        # === AUDIENCE CONSIDERATIONS ===
        audience = context.get('audience', 'general')
        if audience in ['developer', 'expert']:
            evidence_score -= 0.2  # Expert audience expects precise language
        elif audience in ['beginner', 'general']:
            evidence_score += 0.1  # General audience needs clearer placement
        
        # === SENTENCE PATTERNS ===
        # Look for common unambiguous patterns
        sentence_text = token.sent.text.lower()
        
        # Clear restrictive patterns
        if any(pattern in sentence_text for pattern in [
            'only if', 'only when', 'only supports', 'only available', 
            'only works', 'only allows', 'only accepts', 'read-only',
            'write-only', 'only applies', 'only required'
        ]):
            evidence_score -= 0.3  # Common clear patterns
        
        # Potentially ambiguous patterns
        if any(pattern in sentence_text for pattern in [
            'can only', 'will only', 'should only'
        ]):
            evidence_score += 0.1  # Could be clearer as "can X only Y"
        
        return evidence_score

    def _apply_feedback_clues_only(self, evidence_score: float, token, context: dict) -> float:
        """Apply clues learned from user feedback patterns for "only" placement."""
        
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns('adverbs_only')
        
        # Get sentence context for pattern matching
        sentence_text = token.sent.text.lower()
        
        # Check if this "only" pattern is consistently accepted
        accepted_patterns = feedback_patterns.get('accepted_only_patterns', set())
        for pattern in accepted_patterns:
            if pattern in sentence_text:
                evidence_score -= 0.4  # Users consistently accept this pattern
                break
        
        # Check if this "only" pattern is consistently flagged as problematic
        flagged_patterns = feedback_patterns.get('flagged_only_patterns', set())
        for pattern in flagged_patterns:
            if pattern in sentence_text:
                evidence_score += 0.3  # Users consistently find this ambiguous
                break
        
        # Check position-based feedback
        sent_tokens = list(token.sent)
        token_position = None
        for i, sent_token in enumerate(sent_tokens):
            if sent_token.i == token.i:
                token_position = i
                break
        
        if token_position is not None:
            position_feedback = feedback_patterns.get('only_position_feedback', {})
            if token_position < 2:  # Beginning positions
                acceptance_rate = position_feedback.get('beginning', 0.8)
            elif token_position > len(sent_tokens) - 3:  # End positions
                acceptance_rate = position_feedback.get('end', 0.6)
            else:  # Middle positions
                acceptance_rate = position_feedback.get('middle', 0.4)
            
            # Adjust evidence based on position acceptance rate
            if acceptance_rate > 0.7:
                evidence_score -= 0.2
            elif acceptance_rate < 0.4:
                evidence_score += 0.2
        
        return evidence_score

    # === HELPER METHODS FOR SMART MESSAGING ===

    def _get_contextual_message(self, token, evidence_score: float) -> str:
        """Generate context-aware error messages based on evidence score."""
        
        if evidence_score > 0.8:
            return f"The placement of 'only' in this sentence is ambiguous and may confuse readers."
        elif evidence_score > 0.5:
            return f"Consider reviewing the placement of 'only' to ensure clarity."
        else:
            return f"The word 'only' could potentially be clearer depending on its intended meaning."

    def _generate_smart_suggestions(self, token, evidence_score: float, context: dict) -> List[str]:
        """Generate context-aware suggestions based on evidence score and context."""
        
        suggestions = []
        
        # Analyze current placement
        sent_tokens = list(token.sent)
        token_position = None
        for i, sent_token in enumerate(sent_tokens):
            if sent_token.i == token.i:
                token_position = i
                break
        
        # Base suggestion
        suggestions.append("Place 'only' immediately before the word or phrase it modifies.")
        
        # Position-specific suggestions
        if token_position is not None:
            if token_position > len(sent_tokens) // 2:  # Second half of sentence
                suggestions.append("Consider moving 'only' earlier in the sentence for clarity.")
            
            # Look for what "only" might be modifying
            next_token = token.nbor(1) if token.i < len(token.doc) - 1 else None
            if next_token and next_token.pos_ in ['NOUN', 'VERB']:
                suggestions.append(f"If 'only' modifies '{next_token.text}', consider: 'only {next_token.text}'.")
        
        # Context-specific suggestions
        if context:
            content_type = context.get('content_type', 'general')
            if content_type == 'technical':
                suggestions.append("In technical writing, be precise about what 'only' restricts or limits.")
            elif content_type == 'procedural':
                suggestions.append("In instructions, clarify exactly what limitation 'only' expresses.")
        
        # Evidence-based suggestions
        if evidence_score > 0.7:
            suggestions.append("Consider rephrasing the sentence entirely to avoid ambiguity.")
        elif evidence_score < 0.3:
            suggestions.append("The current placement may be acceptable, but review for your intended meaning.")
        
        return suggestions
