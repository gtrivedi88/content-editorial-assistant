"""
Prepositions Rule
Based on IBM Style Guide topic: "Prepositions"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class PrepositionsRule(BaseLanguageRule):
    """
    Checks for sentences that may be overly complex due to a high number
    of prepositional phrases.
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
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        doc = nlp(text)

        for i, sent in enumerate(doc.sents):
            evidence_score = self._calculate_preposition_evidence(sent, text, context or {})

            if evidence_score > 0.1:
                preposition_count = self._count_prepositions(sent)
                message = self._get_contextual_prepositions_message(preposition_count, evidence_score)
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

    def _calculate_preposition_evidence(self, sentence, text: str, context: Dict[str, Any]) -> float:
        """Calculate evidence (0.0-1.0) that a sentence overuses prepositional phrases."""
        evidence_score: float = 0.0

        preposition_count = self._count_prepositions(sentence)
        token_count = max(1, len([t for t in sentence if not getattr(t, 'is_space', False)]))
        density = preposition_count / token_count

        # === STEP 1: BASE EVIDENCE ===
        # Baseline from count and density with conservative scaling
        if preposition_count <= 2:
            return 0.0

        evidence_score = min(1.0, 0.1 * preposition_count + 0.5 * density)

        # Chaining bonus: consecutive prepositions or nested attachments
        chain_factor = self._estimate_preposition_chain_factor(sentence)
        evidence_score += min(0.25, chain_factor)

        # === STEP 2: LINGUISTIC CLUES ===
        evidence_score = self._apply_linguistic_clues_prepositions(evidence_score, sentence)

        # === STEP 3: STRUCTURAL CLUES ===
        evidence_score = self._apply_structural_clues_prepositions(evidence_score, context)

        # === STEP 4: SEMANTIC CLUES ===
        evidence_score = self._apply_semantic_clues_prepositions(evidence_score, text, context)

        # === STEP 5: FEEDBACK CLUES ===
        evidence_score = self._apply_feedback_clues_prepositions(evidence_score, sentence, context)

        return max(0.0, min(1.0, evidence_score))

    # === LINGUISTIC HELPERS ===

    def _count_prepositions(self, sentence) -> int:
        return sum(1 for token in sentence if getattr(token, 'pos_', '') == 'ADP')

    def _estimate_preposition_chain_factor(self, sentence) -> float:
        """Estimate added complexity from chained/nested prepositional phrases."""
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
            if head is not None and getattr(token, 'pos_', '') == 'ADP' and getattr(head, 'dep_', '') == 'pobj':
                nested_links += 1

        # Scale contributions
        return min(0.15 * max(0, longest_run - 1) + 0.02 * pobj_count + 0.05 * nested_links, 0.4)

    def _apply_linguistic_clues_prepositions(self, evidence_score: float, sentence) -> float:
        """Apply micro-level linguistic clues affecting evidence."""
        tokens = [t for t in sentence]
        token_count = max(1, len(tokens))

        # Long sentence increases impact
        if token_count > 25:
            evidence_score += 0.1
        if token_count > 40:
            evidence_score += 0.05

        # Many objects of prepositions increase evidence
        pobj_tokens = [t for t in tokens if getattr(t, 'dep_', '') == 'pobj']
        if len(pobj_tokens) >= 3:
            evidence_score += 0.1

        # Multiple nominal modifiers with ADP chains
        nmod_like = sum(1 for t in tokens if getattr(t, 'dep_', '') in {'nmod', 'npmod'})
        if nmod_like >= 2:
            evidence_score += 0.05

        # If the sentence already has multiple finite verbs, prepositional density is less harmful
        finite_verbs = [t for t in tokens if getattr(t, 'pos_', '') == 'VERB' and getattr(t, 'morph', None) and 'Tense=' in str(t.morph)]
        if len(finite_verbs) >= 2:
            evidence_score -= 0.05

        return evidence_score

    # === STRUCTURAL/SEMANTIC/FEEDBACK CLUES ===

    def _apply_structural_clues_prepositions(self, evidence_score: float, context: Dict[str, Any]) -> float:
        block_type = (context or {}).get('block_type', 'paragraph')

        if block_type in {'code_block', 'literal_block'}:
            evidence_score -= 0.6
        elif block_type == 'inline_code':
            evidence_score -= 0.4
        elif block_type in {'table_cell', 'table_header'}:
            evidence_score -= 0.2
        elif block_type in {'ordered_list_item', 'unordered_list_item'}:
            evidence_score -= 0.1
        elif block_type == 'heading':
            evidence_score -= 0.15

        if block_type == 'admonition':
            admonition_type = (context or {}).get('admonition_type', '').upper()
            if admonition_type in {'WARNING', 'CAUTION', 'IMPORTANT'}:
                evidence_score += 0.05

        return evidence_score

    def _apply_semantic_clues_prepositions(self, evidence_score: float, text: str, context: Dict[str, Any]) -> float:
        content_type = (context or {}).get('content_type', 'general')
        domain = (context or {}).get('domain', 'general')
        audience = (context or {}).get('audience', 'general')

        # Content type adjustments
        if content_type in {'technical', 'api'}:
            evidence_score -= 0.05  # Prepositions are common in technical clarity
        elif content_type in {'marketing', 'procedural'}:
            evidence_score += 0.05  # Prefer shorter, directive sentences
        elif content_type == 'legal':
            evidence_score += 0.1

        # Domain adjustments
        if domain in {'finance', 'legal'}:
            evidence_score += 0.05
        elif domain in {'software', 'engineering', 'devops'}:
            evidence_score -= 0.05

        # Audience adjustments
        if audience in {'beginner', 'general'}:
            evidence_score += 0.05
        elif audience in {'developer', 'expert'}:
            evidence_score -= 0.05

        # Document length context
        doc_len = len(text.split())
        if doc_len > 3000:
            evidence_score += 0.03

        return evidence_score

    def _apply_feedback_clues_prepositions(self, evidence_score: float, sentence, context: Dict[str, Any]) -> float:
        feedback = self._get_cached_feedback_patterns_prepositions()
        sent_lower = sentence.text.lower()

        # Phrases often accepted or rejected by users
        if any(p in sent_lower for p in feedback.get('accepted_phrases', set())):
            evidence_score -= 0.1
        if any(p in sent_lower for p in feedback.get('flagged_phrases', set())):
            evidence_score += 0.1

        # Content-type specific patterns
        content_type = (context or {}).get('content_type', 'general')
        cpat = feedback.get(f'{content_type}_patterns', {})
        if any(p in sent_lower for p in cpat.get('accepted', set())):
            evidence_score -= 0.1
        if any(p in sent_lower for p in cpat.get('flagged', set())):
            evidence_score += 0.1

        return evidence_score

    def _get_cached_feedback_patterns_prepositions(self) -> Dict[str, Any]:
        """Stub for learned feedback patterns. Replace with real feedback system."""
        return {
            'accepted_phrases': {
                'as part of', 'in accordance with', 'in place of'
            },
            'flagged_phrases': {
                'in order to', 'due to the fact that'
            },
            'technical_patterns': {
                'accepted': {'as part of the configuration', 'in response to'},
                'flagged': {'in order to increase'}
            },
            'marketing_patterns': {
                'accepted': set(),
                'flagged': {'in order to'}
            }
        }

    # === SMART MESSAGING ===

    def _get_contextual_prepositions_message(self, preposition_count: int, evidence_score: float) -> str:
        if evidence_score > 0.8:
            return f"High prepositional density ({preposition_count}) may reduce clarity. Consider restructuring."
        if evidence_score > 0.5:
            return f"Sentence has many prepositional phrases ({preposition_count}). Consider simplifying."
        return f"Consider reducing prepositional phrases (count: {preposition_count}) to improve readability."

    def _generate_smart_prepositions_suggestions(self, preposition_count: int, evidence_score: float, sentence, context: Dict[str, Any]) -> List[str]:
        suggestions: List[str] = []
        sent_text = sentence.text

        # General restructuring advice
        if evidence_score > 0.7:
            suggestions.append("Split the sentence into two shorter sentences focusing on the main action.")

        # Replace common verbose patterns
        if 'in order to' in sent_text.lower():
            suggestions.append("Replace 'in order to' with 'to'.")

        # Convert 'of' chains to possessives when appropriate
        if ' of the ' in sent_text.lower() or ' of a ' in sent_text.lower():
            suggestions.append("Where possible, convert 'of' phrases to possessives or adjectives (e.g., 'the system's configuration' instead of 'the configuration of the system').")

        # Nominalization to verb
        suggestions.append("Prefer verbs over noun phrases to reduce attached prepositional phrases (e.g., 'The report lists' instead of 'The report is a list of').")

        # Limit number of suggestions
        return suggestions[:3]
