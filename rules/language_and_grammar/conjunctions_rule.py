"""
Conjunctions Rule (Enhanced for Accuracy)
Based on IBM Style Guide topic: "Conjunctions"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ConjunctionsRule(BaseLanguageRule):
    """
    Checks for conjunction-related issues, including accurate comma splice detection.
    """
    def _get_rule_type(self) -> str:
        return 'conjunctions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for conjunction errors using evidence-based scoring.
        Uses sophisticated linguistic analysis to distinguish genuine comma splices from 
        acceptable stylistic choices and technical usage patterns.
        """
        errors = []
        if not nlp:
            return errors
        
        for i, sent_text in enumerate(sentences):
            if not sent_text.strip() or ',' not in sent_text:
                continue
            
            doc = nlp(sent_text)

            # Find potential comma splice locations and calculate evidence for each
            potential_comma_splices = self._find_potential_comma_splices(doc, sent_text)
            
            for comma_info in potential_comma_splices:
                # Calculate evidence score for this potential comma splice
                evidence_score = self._calculate_comma_splice_evidence(
                    comma_info, doc, sent_text, text, context
                )
                
                # Only create error if evidence suggests it's worth flagging
                if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                    errors.append(self._create_error(
                        sentence=sent_text,
                        sentence_index=i,
                        message=self._get_contextual_message(comma_info, evidence_score),
                        suggestions=self._generate_smart_suggestions(comma_info, evidence_score, context),
                        severity='medium',
                        text=text,
                        context=context,
                        evidence_score=evidence_score,  # Your nuanced assessment
                        flagged_text=comma_info['flagged_text']
                    ))
        return errors
    
    def _find_potential_comma_splices(self, doc, sent_text: str) -> List[Dict[str, Any]]:
        """
        Find potential comma splice locations for evidence-based analysis.
        Returns list of comma info dicts with location and clause details.
        """
        potential_splices = []
        
        # Find comma positions
        comma_positions = []
        for token in doc:
            if token.text == ',':
                comma_positions.append(token.i)
        
        if not comma_positions:
            return potential_splices
        
        for comma_idx in comma_positions:
            comma_token = doc[comma_idx]
            
            # Check for independent clauses on both sides of the comma
            left_clause = self._has_independent_clause_before(doc, comma_idx)
            right_clause = self._has_independent_clause_after(doc, comma_idx)
            
            if left_clause and right_clause:
                # Get clause information for evidence calculation
                left_clause_info = self._get_clause_info_before(doc, comma_idx)
                right_clause_info = self._get_clause_info_after(doc, comma_idx)
                
                comma_info = {
                    'comma_idx': comma_idx,
                    'comma_token': comma_token,
                    'left_clause': left_clause_info,
                    'right_clause': right_clause_info,
                    'flagged_text': self._get_flagged_text_around_comma(doc, comma_idx),
                    'is_list_comma': self._is_list_comma(doc, comma_idx),
                    'has_nearby_conjunction': self._has_coordinating_conjunction_nearby(doc, comma_idx)
                }
                potential_splices.append(comma_info)
        
        return potential_splices

    def _detect_comma_splice(self, doc, sent_text: str) -> bool:
        """
        Legacy method - now used by _find_potential_comma_splices.
        Improved comma splice detection that looks for independent clauses on both sides of a comma.
        """
        # Find comma positions
        comma_positions = []
        for token in doc:
            if token.text == ',':
                comma_positions.append(token.i)
        
        if not comma_positions:
            return False
        
        for comma_idx in comma_positions:
            comma_token = doc[comma_idx]
            
            # Skip if this comma is part of a list or has coordinating conjunction nearby
            if self._is_list_comma(doc, comma_idx) or self._has_coordinating_conjunction_nearby(doc, comma_idx):
                continue
            
            # Check for independent clauses on both sides of the comma
            left_clause = self._has_independent_clause_before(doc, comma_idx)
            right_clause = self._has_independent_clause_after(doc, comma_idx)
            
            if left_clause and right_clause:
                return True
        
        return False
    
    def _has_independent_clause_before(self, doc, comma_idx: int) -> bool:
        """Check if there's an independent clause before the comma."""
        # Look for a verb (VERB or AUX) with a subject before the comma
        for i in range(comma_idx - 1, -1, -1):
            token = doc[i]
            if token.pos_ in ['VERB', 'AUX']:
                # Check if this verb has a subject
                if self._has_subject(token):
                    return True
        return False
    
    def _has_independent_clause_after(self, doc, comma_idx: int) -> bool:
        """Check if there's an independent clause after the comma."""
        # Look for a verb (VERB or AUX) with a subject after the comma
        for i in range(comma_idx + 1, len(doc)):
            token = doc[i]
            if token.pos_ in ['VERB', 'AUX']:
                # Check if this verb has a subject
                if self._has_subject(token):
                    return True
        return False
    
    def _has_subject(self, verb_token) -> bool:
        """Check if a verb has a subject, indicating it's part of an independent clause."""
        # Look for nsubj (nominal subject) or nsubjpass (passive nominal subject) dependencies
        for child in verb_token.children:
            if child.dep_ in ['nsubj', 'nsubjpass']:
                return True
        
        # Also check if the verb itself is a subject of another verb (for complex structures)
        if verb_token.dep_ in ['nsubj', 'nsubjpass']:
            return True
            
        return False
    
    def _is_list_comma(self, doc, comma_idx: int) -> bool:
        """Check if this comma is part of a list (not a comma splice)."""
        # Simple heuristic: if there are multiple commas or conjunctions nearby, likely a list
        comma_count = sum(1 for token in doc if token.text == ',')
        if comma_count > 1:
            return True
        
        # Check for list patterns like "A, B, and C"
        if comma_idx + 2 < len(doc):
            next_token = doc[comma_idx + 1]
            next_next_token = doc[comma_idx + 2]
            if next_token.text.lower() in ['and', 'or'] or next_next_token.text.lower() in ['and', 'or']:
                return True
        
        return False
    
    def _has_coordinating_conjunction_nearby(self, doc, comma_idx: int) -> bool:
        """Check if there's a coordinating conjunction near the comma."""
        # Check a few tokens before and after the comma
        for i in range(max(0, comma_idx - 2), min(len(doc), comma_idx + 3)):
            if i != comma_idx and doc[i].pos_ == 'CCONJ':  # Coordinating conjunction
                return True
        return False

    # === EVIDENCE-BASED CALCULATION METHODS ===

    def _calculate_comma_splice_evidence(self, comma_info: dict, doc, sentence: str, text: str, context: dict) -> float:
        """
        Calculate evidence score (0.0-1.0) for comma splice error.
        
        Higher scores indicate stronger evidence of a genuine comma splice error.
        Lower scores indicate borderline cases or acceptable stylistic usage.
        
        Args:
            comma_info: Dict with comma location and clause information
            doc: SpaCy document for the sentence
            sentence: The sentence text
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (acceptable) to 1.0 (clear error)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_comma_splice_evidence(comma_info)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this comma
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_comma_splice(evidence_score, comma_info, doc, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_comma_splice(evidence_score, comma_info, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_comma_splice(evidence_score, comma_info, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_comma_splice(evidence_score, comma_info, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    def _get_base_comma_splice_evidence(self, comma_info: dict) -> float:
        """Get base evidence score based on clause structure and comma context."""
        
        # If this looks like a list comma, very low base evidence
        if comma_info['is_list_comma']:
            return 0.1  # Very low evidence for list commas
        
        # If there's a nearby coordinating conjunction, low evidence
        if comma_info['has_nearby_conjunction']:
            return 0.2  # Low evidence when conjunction is present
        
        # Check clause strength and independence
        left_clause = comma_info['left_clause']
        right_clause = comma_info['right_clause']
        
        # Strong independent clauses on both sides = higher base evidence
        if (left_clause.get('has_strong_subject') and left_clause.get('has_main_verb') and
            right_clause.get('has_strong_subject') and right_clause.get('has_main_verb')):
            return 0.8  # High evidence for clear independent clauses
        
        # Moderate clause independence
        if (left_clause.get('has_subject') and left_clause.get('has_verb') and
            right_clause.get('has_subject') and right_clause.get('has_verb')):
            return 0.6  # Moderate evidence for probable independent clauses
        
        # Weak clause independence
        return 0.4  # Lower evidence for weak clause detection

    # === LINGUISTIC CLUES FOR COMMA SPLICE ===

    def _apply_linguistic_clues_comma_splice(self, evidence_score: float, comma_info: dict, doc, sentence: str) -> float:
        """Apply linguistic analysis clues for comma splice detection."""
        
        # === CLAUSE COMPLEXITY ANALYSIS ===
        left_clause = comma_info['left_clause']
        right_clause = comma_info['right_clause']
        
        # Simple, clear independent clauses increase evidence
        if (left_clause.get('is_simple_clause') and right_clause.get('is_simple_clause')):
            evidence_score += 0.2  # Clear, simple clauses likely a splice
        
        # Complex clauses with subordination reduce evidence
        if (left_clause.get('has_subordination') or right_clause.get('has_subordination')):
            evidence_score -= 0.2  # Subordination suggests complex structure
        
        # === VERB ANALYSIS ===
        # Strong main verbs indicate independent clauses
        if (left_clause.get('verb_strength', 0) > 0.7 and right_clause.get('verb_strength', 0) > 0.7):
            evidence_score += 0.1  # Strong verbs support independence
        
        # Auxiliary verbs or weak verbs reduce evidence
        if (left_clause.get('has_auxiliary_only') or right_clause.get('has_auxiliary_only')):
            evidence_score -= 0.2  # Auxiliary-only verbs less independent
        
        # === SUBJECT ANALYSIS ===
        # Explicit subjects in both clauses increase evidence
        if (left_clause.get('subject_type') == 'explicit' and right_clause.get('subject_type') == 'explicit'):
            evidence_score += 0.1  # Explicit subjects support independence
        
        # Pronoun subjects may indicate continuation rather than new clause
        if (left_clause.get('subject_type') == 'pronoun' and right_clause.get('subject_type') == 'pronoun'):
            evidence_score -= 0.1  # Pronoun subjects suggest continuation
        
        # === SENTENCE LENGTH AND COMPLEXITY ===
        # Very short clauses may not be true independent clauses
        comma_idx = comma_info['comma_idx']
        left_length = comma_idx
        right_length = len(doc) - comma_idx - 1
        
        if left_length <= 3 or right_length <= 3:
            evidence_score -= 0.3  # Very short clauses unlikely to be independent
        elif left_length >= 8 and right_length >= 8:
            evidence_score += 0.1  # Longer clauses more likely independent
        
        # === PUNCTUATION PATTERNS ===
        # Check for other punctuation that might indicate intentional structure
        sentence_lower = sentence.lower()
        if '; ' in sentence or ' - ' in sentence or ' : ' in sentence:
            evidence_score -= 0.1  # Other punctuation suggests intentional structure
        
        return evidence_score

    def _apply_structural_clues_comma_splice(self, evidence_score: float, comma_info: dict, context: dict) -> float:
        """Apply document structure-based clues for comma splice detection."""
        
        if not context:
            return evidence_score
        
        block_type = context.get('block_type', 'paragraph')
        
        # === FORMAL WRITING CONTEXTS ===
        # Formal contexts expect proper punctuation
        if block_type in ['heading', 'title']:
            evidence_score += 0.3  # Headings should have proper punctuation
        elif block_type == 'paragraph':
            evidence_score += 0.1  # Body text expects correct grammar
        
        # === TECHNICAL CONTEXTS ===
        # Technical contexts may use abbreviated or list-like structures
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.4  # Code comments may use abbreviated punctuation
        elif block_type == 'inline_code':
            evidence_score -= 0.3  # Inline technical content more flexible
        
        # === LISTS AND TABLES ===
        # Lists and tables often use comma-separated items
        if block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.3  # List items often have comma-separated elements
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.4  # Tables frequently use comma-separated values
        
        # === ADMONITIONS ===
        # Notes and warnings may use informal punctuation
        if block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'TIP']:
                evidence_score -= 0.2  # Notes may be more informal
            elif admonition_type in ['WARNING', 'CAUTION']:
                evidence_score += 0.0  # Warnings should be clear
        
        # === QUOTES AND CITATIONS ===
        # Quoted material may have different punctuation standards
        if block_type in ['block_quote', 'citation']:
            evidence_score -= 0.2  # Quotes may preserve original punctuation
        
        return evidence_score

    def _apply_semantic_clues_comma_splice(self, evidence_score: float, comma_info: dict, text: str, context: dict) -> float:
        """Apply semantic and content-type clues for comma splice detection."""
        
        if not context:
            return evidence_score
        
        content_type = context.get('content_type', 'general')
        
        # === CONTENT TYPE ANALYSIS ===
        # Different content types have different punctuation tolerance
        if content_type == 'technical':
            evidence_score -= 0.2  # Technical writing may use abbreviated structures
        elif content_type == 'api':
            evidence_score -= 0.3  # API documentation very technical and abbreviated
        elif content_type == 'academic':
            evidence_score += 0.2  # Academic writing expects proper punctuation
        elif content_type == 'legal':
            evidence_score += 0.3  # Legal writing demands precision
        elif content_type == 'marketing':
            evidence_score -= 0.2  # Marketing may use stylistic punctuation
        elif content_type == 'narrative':
            evidence_score -= 0.1  # Narrative may use comma splices stylistically
        elif content_type == 'procedural':
            evidence_score -= 0.1  # Instructions may use abbreviated punctuation
        
        # === DOMAIN-SPECIFIC PATTERNS ===
        domain = context.get('domain', 'general')
        if domain in ['software', 'engineering', 'devops']:
            evidence_score -= 0.2  # Technical domains use abbreviated styles
        elif domain in ['documentation', 'tutorial']:
            evidence_score -= 0.1  # Educational content may be more flexible
        elif domain in ['academic', 'research']:
            evidence_score += 0.1  # Academic domains expect precision
        
        # === AUDIENCE CONSIDERATIONS ===
        audience = context.get('audience', 'general')
        if audience in ['developer', 'technical', 'expert']:
            evidence_score -= 0.2  # Technical audiences expect abbreviated styles
        elif audience in ['academic', 'professional']:
            evidence_score += 0.1  # Professional audiences expect correctness
        elif audience in ['beginner', 'general']:
            evidence_score += 0.2  # General audiences need clear grammar
        
        # === WRITING STYLE INDICATORS ===
        # Look for stylistic indicators in the text
        if self._has_creative_writing_indicators(text):
            evidence_score -= 0.2  # Creative writing may use comma splices stylistically
        
        if self._has_formal_writing_indicators(text):
            evidence_score += 0.2  # Formal writing should avoid comma splices
        
        return evidence_score

    def _apply_feedback_clues_comma_splice(self, evidence_score: float, comma_info: dict, context: dict) -> float:
        """Apply feedback patterns for comma splice detection."""
        
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns()
        
        # === CLAUSE PATTERN FEEDBACK ===
        # Check if this type of clause pattern is commonly accepted
        left_pattern = self._get_clause_pattern(comma_info['left_clause'])
        right_pattern = self._get_clause_pattern(comma_info['right_clause'])
        pattern_key = f"{left_pattern}_comma_{right_pattern}"
        
        accepted_patterns = feedback_patterns.get('accepted_comma_patterns', set())
        if pattern_key in accepted_patterns:
            evidence_score -= 0.3  # Users consistently accept this pattern
        
        flagged_patterns = feedback_patterns.get('flagged_comma_patterns', set())
        if pattern_key in flagged_patterns:
            evidence_score += 0.3  # Users consistently flag this pattern
        
        # === CONTEXT-SPECIFIC FEEDBACK ===
        if context:
            block_type = context.get('block_type', 'paragraph')
            context_patterns = feedback_patterns.get(f'{block_type}_comma_patterns', {})
            
            if pattern_key in context_patterns.get('acceptable', set()):
                evidence_score -= 0.2
            elif pattern_key in context_patterns.get('problematic', set()):
                evidence_score += 0.2
        
        # === LENGTH-BASED FEEDBACK ===
        # Short comma-separated phrases often acceptable
        comma_idx = comma_info['comma_idx']
        if comma_idx <= 5:  # Short first clause
            short_patterns = feedback_patterns.get('short_clause_acceptance', {})
            if left_pattern in short_patterns.get('acceptable', set()):
                evidence_score -= 0.2
        
        return evidence_score

    # === HELPER METHODS ===

    def _get_clause_info_before(self, doc, comma_idx: int) -> dict:
        """Get detailed information about the clause before the comma."""
        clause_info = {
            'has_subject': False,
            'has_verb': False,
            'has_strong_subject': False,
            'has_main_verb': False,
            'is_simple_clause': False,
            'has_subordination': False,
            'verb_strength': 0.0,
            'has_auxiliary_only': False,
            'subject_type': 'none'
        }
        
        # Analyze tokens before the comma
        for i in range(comma_idx - 1, -1, -1):
            token = doc[i]
            
            # Check for verbs
            if token.pos_ in ['VERB', 'AUX']:
                clause_info['has_verb'] = True
                if token.pos_ == 'VERB':
                    clause_info['has_main_verb'] = True
                    clause_info['verb_strength'] = 0.8
                else:
                    clause_info['has_auxiliary_only'] = True
                    clause_info['verb_strength'] = 0.3
                
                # Check if this verb has a subject
                if self._has_subject(token):
                    clause_info['has_subject'] = True
                    subject_token = self._get_subject_token(token)
                    if subject_token:
                        if subject_token.pos_ == 'PRON':
                            clause_info['subject_type'] = 'pronoun'
                        elif subject_token.pos_ in ['NOUN', 'PROPN']:
                            clause_info['subject_type'] = 'explicit'
                            clause_info['has_strong_subject'] = True
            
            # Check for subordinating conjunctions
            if token.pos_ == 'SCONJ':
                clause_info['has_subordination'] = True
        
        # Determine if it's a simple clause
        clause_info['is_simple_clause'] = (
            clause_info['has_strong_subject'] and 
            clause_info['has_main_verb'] and 
            not clause_info['has_subordination']
        )
        
        return clause_info

    def _get_clause_info_after(self, doc, comma_idx: int) -> dict:
        """Get detailed information about the clause after the comma."""
        clause_info = {
            'has_subject': False,
            'has_verb': False,
            'has_strong_subject': False,
            'has_main_verb': False,
            'is_simple_clause': False,
            'has_subordination': False,
            'verb_strength': 0.0,
            'has_auxiliary_only': False,
            'subject_type': 'none'
        }
        
        # Analyze tokens after the comma
        for i in range(comma_idx + 1, len(doc)):
            token = doc[i]
            
            # Check for verbs
            if token.pos_ in ['VERB', 'AUX']:
                clause_info['has_verb'] = True
                if token.pos_ == 'VERB':
                    clause_info['has_main_verb'] = True
                    clause_info['verb_strength'] = 0.8
                else:
                    clause_info['has_auxiliary_only'] = True
                    clause_info['verb_strength'] = 0.3
                
                # Check if this verb has a subject
                if self._has_subject(token):
                    clause_info['has_subject'] = True
                    subject_token = self._get_subject_token(token)
                    if subject_token:
                        if subject_token.pos_ == 'PRON':
                            clause_info['subject_type'] = 'pronoun'
                        elif subject_token.pos_ in ['NOUN', 'PROPN']:
                            clause_info['subject_type'] = 'explicit'
                            clause_info['has_strong_subject'] = True
            
            # Check for subordinating conjunctions
            if token.pos_ == 'SCONJ':
                clause_info['has_subordination'] = True
        
        # Determine if it's a simple clause
        clause_info['is_simple_clause'] = (
            clause_info['has_strong_subject'] and 
            clause_info['has_main_verb'] and 
            not clause_info['has_subordination']
        )
        
        return clause_info

    def _get_subject_token(self, verb_token):
        """Get the subject token for a verb."""
        for child in verb_token.children:
            if child.dep_ in ['nsubj', 'nsubjpass']:
                return child
        return None

    def _get_flagged_text_around_comma(self, doc, comma_idx: int) -> str:
        """Get text around the comma for error flagging."""
        start = max(0, comma_idx - 3)
        end = min(len(doc), comma_idx + 4)
        return ' '.join(token.text for token in doc[start:end])

    def _get_clause_pattern(self, clause_info: dict) -> str:
        """Get a pattern string describing the clause structure."""
        if clause_info['is_simple_clause']:
            return 'simple_clause'
        elif clause_info['has_subordination']:
            return 'subordinate_clause'
        elif clause_info['has_main_verb'] and clause_info['has_strong_subject']:
            return 'independent_clause'
        elif clause_info['has_verb'] and clause_info['has_subject']:
            return 'basic_clause'
        else:
            return 'phrase'

    def _has_creative_writing_indicators(self, text: str) -> bool:
        """Check if text has indicators of creative/narrative writing."""
        creative_indicators = [
            'he said', 'she said', 'they said', 'i thought', 'she thought',
            'suddenly', 'meanwhile', 'however', 'moreover', 'furthermore',
            'once upon', 'long ago', 'in the end', 'finally'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in creative_indicators)

    def _has_formal_writing_indicators(self, text: str) -> bool:
        """Check if text has indicators of formal writing."""
        formal_indicators = [
            'therefore', 'consequently', 'furthermore', 'moreover', 'nevertheless',
            'nonetheless', 'accordingly', 'subsequently', 'specifically',
            'in conclusion', 'in summary', 'for example', 'for instance'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in formal_indicators)

    def _get_cached_feedback_patterns(self):
        """Load feedback patterns from cache or feedback analysis."""
        # This would load from feedback analysis system
        # For now, return patterns based on common comma splice usage
        return {
            'accepted_comma_patterns': {
                # Short, common patterns users often accept
                'phrase_comma_phrase', 'basic_clause_comma_phrase',
                'simple_clause_comma_basic_clause'
            },
            'flagged_comma_patterns': {
                # Clear comma splice patterns users flag
                'independent_clause_comma_independent_clause',
                'simple_clause_comma_simple_clause'
            },
            'paragraph_comma_patterns': {
                'acceptable': {
                    'phrase_comma_phrase', 'basic_clause_comma_phrase'
                },
                'problematic': {
                    'independent_clause_comma_independent_clause'
                }
            },
            'ordered_list_item_comma_patterns': {
                'acceptable': {
                    'phrase_comma_phrase', 'basic_clause_comma_phrase',
                    'simple_clause_comma_basic_clause', 'independent_clause_comma_phrase'
                },
                'problematic': set()
            },
            'short_clause_acceptance': {
                'acceptable': {
                    'phrase', 'basic_clause'
                }
            }
        }

    # === HELPER METHODS FOR SMART MESSAGING ===

    def _get_contextual_message(self, comma_info: dict, evidence_score: float) -> str:
        """Generate context-aware error messages for comma splices."""
        
        if evidence_score > 0.8:
            return "Comma splice detected: two independent clauses are joined by only a comma."
        elif evidence_score > 0.5:
            return "Possible comma splice: consider whether these clauses should be separated differently."
        else:
            return "Comma usage: verify that this comma correctly connects the clauses."

    def _generate_smart_suggestions(self, comma_info: dict, evidence_score: float, context: dict) -> List[str]:
        """Generate context-aware suggestions for comma splices."""
        
        suggestions = []
        
        # Base suggestions
        if evidence_score > 0.7:
            suggestions.append("Use a period to create two separate sentences.")
            suggestions.append("Use a semicolon to connect related independent clauses.")
            suggestions.append("Add a coordinating conjunction (and, but, or, so) after the comma.")
        else:
            suggestions.append("Consider using a period, semicolon, or conjunction if these are independent clauses.")
        
        # Context-specific advice
        if context:
            content_type = context.get('content_type', 'general')
            block_type = context.get('block_type', 'paragraph')
            
            if content_type == 'technical' and block_type in ['ordered_list_item', 'unordered_list_item']:
                suggestions.append("In technical lists, comma-separated items may be acceptable.")
            elif content_type in ['academic', 'legal']:
                suggestions.append("Formal writing requires clear separation of independent clauses.")
            elif content_type == 'narrative':
                suggestions.append("Consider whether this comma splice serves a stylistic purpose.")
        
        # Evidence-based advice
        if evidence_score < 0.3:
            suggestions.append("This may be acceptable depending on your writing style and context.")
        elif evidence_score > 0.8:
            suggestions.append("This appears to be a clear comma splice that should be corrected.")
        
        return suggestions
