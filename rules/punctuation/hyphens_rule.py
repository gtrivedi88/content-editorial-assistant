"""
Hyphens Rule
Based on IBM Style Guide topics: "Hyphens" and "Prefixes"

**UPDATED** with evidence-based scoring for nuanced hyphen usage analysis.
"""
from typing import List, Dict, Any, Optional
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens import Doc, Token, Span
except ImportError:
    Doc = None
    Token = None
    Span = None

class HyphensRule(BasePunctuationRule):
    """
    Checks for incorrect hyphenation using evidence-based analysis,
    with context awareness for legitimate hyphenation scenarios.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'hyphens'

    def analyze(self, text: str, sentences: List[str], nlp=None, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for hyphen usage:
          - Common prefixes should generally be closed (unhyphenated)
          - Various contexts may legitimize hyphen usage (compound words, etc.)
        """
        errors: List[Dict[str, Any]] = []
        context = context or {}
        
        # Fallback analysis when nlp is not available
        if not nlp:
            # Apply basic guards for fallback analysis
            content_type = context.get('content_type', 'general')
            block_type = context.get('block_type', 'paragraph')
            
            # Skip if in contexts where hyphens are legitimate
            if content_type in ['creative', 'literary', 'narrative']:
                return errors  # No errors for creative content
            if block_type in ['quote', 'blockquote', 'code_block', 'literal_block']:
                return errors  # No errors for quotes and code
            
            # Simple regex-based fallback for common prefix patterns
            import re
            closed_prefixes = {"pre", "post", "multi", "non", "inter", "intra", "re"}
            
            for i, sentence in enumerate(sentences):
                for prefix in closed_prefixes:
                    pattern = rf'\b{prefix}-(\w+)'
                    for match in re.finditer(pattern, sentence, re.IGNORECASE):
                        # Basic exception handling
                        if prefix.lower() == "re" and match.group(1).startswith('e'):
                            continue
                        
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=f"Incorrect hyphenation with prefix '{prefix}'. IBM Style prefers closed prefixes.",
                            suggestions=[f"Consider removing the hyphen to form '{prefix}{match.group(1)}'."],
                            severity='medium',
                            text=text,
                            context=context,
                            evidence_score=0.8,  # Default evidence for fallback analysis
                            span=(match.start(), match.end()),
                            flagged_text=match.group(0)
                        ))
            return errors

        try:
            doc = nlp(text)
            # Linguistic Anchor: Common prefixes that should be closed (not hyphenated).
            closed_prefixes = {"pre", "post", "multi", "non", "inter", "intra", "re"}

            for i, sent in enumerate(doc.sents):
                for token in sent:
                    if token.text == '-':
                        if token.i > sent.start and token.i < sent.end - 1:
                            prefix_token = sent.doc[token.i - 1]
                            word_token = sent.doc[token.i + 1]
                            
                            if prefix_token.lemma_ in closed_prefixes:
                                evidence_score = self._calculate_hyphen_evidence(token, prefix_token, word_token, sent, text, context)
                                
                                # Only flag if evidence suggests it's worth evaluating
                                if evidence_score > 0.1:
                                    flagged_text = f"{prefix_token.text}-{word_token.text}"
                                    errors.append(self._create_error(
                                        sentence=sent.text,
                                        sentence_index=i,
                                        message=self._get_contextual_hyphen_message(prefix_token, evidence_score, context),
                                        suggestions=self._generate_smart_hyphen_suggestions(prefix_token, word_token, evidence_score, context),
                                        severity='low' if evidence_score < 0.7 else 'medium',
                                        text=text,
                                        context=context,
                                        evidence_score=evidence_score,
                                        span=(prefix_token.idx, word_token.idx + len(word_token.text)),
                                        flagged_text=flagged_text
                                    ))
        except Exception as e:
            # Safeguard for unexpected SpaCy behavior
            errors.append(self._create_error(
                sentence=text,
                sentence_index=0,
                message=f"Rule HyphensRule failed with error: {e}",
                suggestions=["This may be a bug in the rule. Please report it."],
                severity='low',
                text=text,
                context=context,
                evidence_score=0.0  # No evidence when analysis fails
            ))
        return errors

    # === EVIDENCE CALCULATION ===

    def _calculate_hyphen_evidence(self, hyphen_token: 'Token', prefix_token: 'Token', word_token: 'Token', sent: 'Span', text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) that hyphen usage is incorrect.
        
        Higher scores indicate stronger evidence of an error.
        Lower scores indicate acceptable usage or ambiguous cases.
        """
        # === SURGICAL ZERO FALSE POSITIVE GUARDS ===
        # Apply surgical guards FIRST to eliminate false positives
        if self._apply_zero_false_positive_guards_punctuation(hyphen_token, context):
            return 0.0
        
        # Creative content commonly uses hyphens for stylistic effect
        content_type = context.get('content_type', 'general')
        if content_type in ['creative', 'literary', 'narrative']:
            return 0.0
        
        # Software domain uses many legitimate technical compounds
        domain = context.get('domain', 'general')
        if domain in ['software', 'engineering']:
            # Check for established technical terms
            prefix_lemma = prefix_token.lemma_.lower()
            word_lemma = word_token.lemma_.lower()
            
            # Well-established software terms (using lemmatized forms)
            technical_compounds = {
                'multi': ['thread', 'process', 'processor', 'core', 'user', 'tenant', 'layer', 'stage'],
                'pre': ['processor', 'compile', 'build', 'configure', 'load', 'define'],
                'post': ['process', 'processor', 'build', 'deployment', 'installation'],
                'inter': ['process', 'thread', 'service', 'module', 'component'],
                'intra': ['process', 'service', 'cluster', 'node']
            }
            
            if prefix_lemma in technical_compounds:
                if word_lemma in technical_compounds[prefix_lemma]:
                    return 0.0  # Established technical term
        
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        # Start with high evidence for closed prefixes
        evidence_score = 0.8
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_hyphen(evidence_score, prefix_token, word_token, sent)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_hyphen(evidence_score, prefix_token, word_token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_hyphen(evidence_score, prefix_token, word_token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_hyphen(evidence_score, prefix_token, word_token, context)
        
        return max(0.0, min(1.0, evidence_score))

    def _apply_linguistic_clues_hyphen(self, evidence_score: float, prefix_token: 'Token', word_token: 'Token', sent: 'Span') -> float:
        """Apply SpaCy-based linguistic analysis clues for hyphen usage."""
        
        prefix_lemma = prefix_token.lemma_.lower()
        word_lemma = word_token.lemma_.lower()
        
        # === DOCUMENTED EXCEPTIONS ===
        
        # Exception 1: 're' before 'e' (e.g., re-enter, re-examine)
        if prefix_lemma == "re" and word_lemma.startswith("e"):
            evidence_score -= 0.7
        
        # Exception 2: 'multi' has specific exceptions
        if prefix_lemma == "multi":
            if word_lemma in ["agent", "core", "instance", "user", "pass", "step"]:
                evidence_score -= 0.6
        
        # Exception 3: 'pre' before words starting with 'e'
        if prefix_lemma == "pre" and word_lemma.startswith("e"):
            evidence_score -= 0.4
        
        # Exception 4: 'non' before proper nouns or capitalized words
        if prefix_lemma == "non" and word_token.text[0].isupper():
            evidence_score -= 0.5
        
        # Exception 5: Compound adjectives before nouns often need hyphens
        if word_token.i < len(sent) - 1:
            next_token = sent[word_token.i + 1 - sent.start]
            if next_token.pos_ == 'NOUN':
                evidence_score -= 0.3  # May be compound adjective
        
        # === MORPHOLOGICAL PATTERNS ===
        
        # Check if the combination creates an ambiguous reading
        combined_word = f"{prefix_token.text}{word_token.text}"
        
        # Very long combinations may benefit from hyphens for readability
        if len(combined_word) > 15:
            evidence_score -= 0.2
        
        # Words with repeated letters at the junction may need hyphens
        if prefix_token.text.endswith(word_token.text[0]):
            evidence_score -= 0.3
        
        # Check for existing word vs. neologism
        # If the combination would create a very unusual word, hyphen might be better
        unusual_patterns = ['aaaa', 'eeee', 'iiii', 'oooo', 'uuuu']
        if any(pattern in combined_word.lower() for pattern in unusual_patterns):
            evidence_score -= 0.4
        
        return evidence_score

    def _apply_structural_clues_hyphen(self, evidence_score: float, prefix_token: 'Token', word_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply document structure-based clues for hyphen usage."""
        
        block_type = context.get('block_type', 'paragraph')
        
        # Technical documentation may use more hyphens for clarity
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.2
        
        # Headings may use hyphens for compound concepts
        elif block_type in ['heading', 'title']:
            evidence_score -= 0.1
        
        # Lists may contain technical terms with hyphens
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.1
        
        # Table content may need hyphens for compound terms
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.1
        
        # Quotes should preserve original hyphenation
        elif block_type in ['quote', 'blockquote']:
            evidence_score -= 0.5
        
        return evidence_score

    def _apply_semantic_clues_hyphen(self, evidence_score: float, prefix_token: 'Token', word_token: 'Token', text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for hyphen usage."""
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # Technical content may use hyphens for precision
        if content_type == 'technical':
            evidence_score -= 0.05
        
        # Academic writing follows more traditional rules
        elif content_type == 'academic':
            evidence_score += 0.05
        
        # Legal writing prefers standard forms
        elif content_type == 'legal':
            evidence_score += 0.1
        
        # Marketing content may be more flexible
        elif content_type == 'marketing':
            evidence_score -= 0.05
        
        # Creative writing may use hyphens stylistically
        elif content_type == 'creative':
            evidence_score -= 0.1
        
        # Domain-specific adjustments
        if domain in ['software', 'engineering']:
            # Software terms often use hyphens (multi-threaded, pre-processor)
            evidence_score -= 0.1
        elif domain in ['medicine', 'science']:
            # Medical/scientific terms may need hyphens for clarity
            evidence_score -= 0.05
        elif domain in ['journalism', 'publishing']:
            # Publishing follows stricter style guides
            evidence_score += 0.05
        
        # Audience considerations
        if audience in ['expert', 'developer']:
            # Experts familiar with technical compound terms
            evidence_score -= 0.05
        elif audience in ['general', 'consumer']:
            # General audience may benefit from clearer word boundaries
            evidence_score -= 0.05
        
        return evidence_score

    def _apply_feedback_clues_hyphen(self, evidence_score: float, prefix_token: 'Token', word_token: 'Token', context: Dict[str, Any]) -> float:
        """Apply clues learned from user feedback patterns for hyphen usage."""
        
        feedback_patterns = self._get_cached_feedback_patterns_hyphen()
        
        prefix_word = prefix_token.text.lower()
        word_text = word_token.text.lower()
        combination = f"{prefix_word}-{word_text}"
        
        # Check for specific combinations that users commonly accept/reject
        if combination in feedback_patterns.get('accepted_combinations', set()):
            evidence_score -= 0.4
        elif combination in feedback_patterns.get('flagged_combinations', set()):
            evidence_score += 0.3
        
        # Check prefix-specific patterns
        prefix_patterns = feedback_patterns.get(f'{prefix_word}_patterns', {})
        if 'hyphen_acceptance_rate' in prefix_patterns:
            acceptance_rate = prefix_patterns['hyphen_acceptance_rate']
            if acceptance_rate > 0.7:
                evidence_score -= 0.2
            elif acceptance_rate < 0.3:
                evidence_score += 0.2
        
        # Check for word-specific patterns
        if word_text in feedback_patterns.get('commonly_hyphenated_words', set()):
            evidence_score -= 0.2
        elif word_text in feedback_patterns.get('commonly_closed_words', set()):
            evidence_score += 0.2
        
        # Context-specific feedback
        block_type = context.get('block_type', 'paragraph')
        block_patterns = feedback_patterns.get(f'{block_type}_hyphen_patterns', {})
        
        if 'accepted_rate' in block_patterns:
            acceptance_rate = block_patterns['accepted_rate']
            if acceptance_rate > 0.6:
                evidence_score -= 0.1
            elif acceptance_rate < 0.4:
                evidence_score += 0.1
        
        return evidence_score

    def _get_cached_feedback_patterns_hyphen(self) -> Dict[str, Any]:
        """Load feedback patterns for hyphen usage from cache or feedback analysis."""
        return {
            'accepted_combinations': {
                're-enter', 're-examine', 're-edit', 're-evaluate',
                'multi-agent', 'multi-core', 'multi-user', 'multi-step',
                'pre-existing', 'pre-empt', 'non-english'
            },
            'flagged_combinations': {
                'pre-paid', 'post-test', 'non-stop', 'inter-connected'
            },
            'commonly_hyphenated_words': {'agent', 'core', 'user', 'step', 'pass'},
            'commonly_closed_words': {'payment', 'test', 'connected', 'active'},
            're_patterns': {'hyphen_acceptance_rate': 0.8},
            'multi_patterns': {'hyphen_acceptance_rate': 0.6},
            'pre_patterns': {'hyphen_acceptance_rate': 0.3},
            'post_patterns': {'hyphen_acceptance_rate': 0.2},
            'non_patterns': {'hyphen_acceptance_rate': 0.2},
            'paragraph_hyphen_patterns': {'accepted_rate': 0.4},
            'code_block_hyphen_patterns': {'accepted_rate': 0.7},
            'heading_hyphen_patterns': {'accepted_rate': 0.5},
        }

    # === SMART MESSAGING ===

    def _get_contextual_hyphen_message(self, prefix_token: 'Token', evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for hyphen usage."""
        
        prefix = prefix_token.text.lower()
        content_type = context.get('content_type', 'general')
        
        if evidence_score > 0.8:
            if prefix in ['re', 'multi']:
                return f"Consider removing hyphen with '{prefix}': this prefix typically forms closed compounds except in specific cases."
            else:
                return f"Incorrect hyphenation with prefix '{prefix}': IBM Style Guide prefers closed prefixes."
        elif evidence_score > 0.6:
            return f"Hyphen with '{prefix}' may be unnecessary: most combinations with this prefix are written as one word."
        elif evidence_score > 0.4:
            return f"Review hyphenation with '{prefix}': consider whether the hyphen aids readability or creates ambiguity."
        else:
            return f"Evaluate hyphen usage with '{prefix}' for consistency with style guidelines."

    def _generate_smart_hyphen_suggestions(self, prefix_token: 'Token', word_token: 'Token', evidence_score: float, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for hyphen usage."""
        
        suggestions = []
        prefix = prefix_token.text.lower()
        word = word_token.text.lower()
        closed_form = f"{prefix_token.text}{word_token.text}"
        hyphenated_form = f"{prefix_token.text}-{word_token.text}"
        
        # High evidence suggestions
        if evidence_score > 0.7:
            suggestions.append(f"Remove the hyphen to form '{closed_form}' following IBM Style Guide preferences.")
            
            # Prefix-specific guidance
            if prefix == 're':
                if word.startswith('e'):
                    suggestions.append("Exception: 're-' before words starting with 'e' may keep the hyphen for clarity.")
                else:
                    suggestions.append("The prefix 're-' typically forms closed compounds: 'rebuild', 'review', 'reorganize'.")
            elif prefix == 'multi':
                suggestions.append("Most 'multi-' words are closed: 'multimedia', 'multitask', 'multicolor'.")
            elif prefix in ['pre', 'post']:
                suggestions.append(f"The prefix '{prefix}-' typically forms closed compounds in modern usage.")
        
        # Medium evidence suggestions
        elif evidence_score > 0.4:
            suggestions.append(f"Consider '{closed_form}' as the preferred form, unless readability requires the hyphen.")
            suggestions.append("Check if this combination is established in dictionaries or style guides.")
        
        # Context-specific suggestions
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        
        if content_type == 'technical' and evidence_score > 0.5:
            suggestions.append("Technical writing generally follows standard dictionary forms without hyphens.")
        elif domain == 'software' and prefix == 'multi':
            suggestions.append("In software contexts, consider standard terms: 'multithreaded', 'multiprocessor', 'multiuser'.")
        elif evidence_score <= 0.4:
            suggestions.append("If the hyphen aids clarity or pronunciation, it may be acceptable.")
        
        # General guidance
        if len(suggestions) < 2:
            suggestions.append("Most modern style guides prefer closed compound words over hyphenated forms.")
            suggestions.append("Hyphens should be used only when they prevent ambiguity or aid pronunciation.")
        
        return suggestions[:3]