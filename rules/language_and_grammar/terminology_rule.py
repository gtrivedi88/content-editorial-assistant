"""
Terminology Rule
Based on IBM Style Guide topic: "Terminology" and "Word usage"
"""
from typing import List, Dict, Any
import re
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class TerminologyRule(BaseLanguageRule):
    """
    Checks for the use of non-preferred or outdated terminology and suggests
    the correct IBM-approved terms.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'terminology'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for non-preferred/outdated terminology.
        Calculates a nuanced evidence score per match using
        linguistic, structural, semantic, and feedback clues.
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
        doc = nlp(text)

        term_map = {
            "info center": "IBM Documentation", "infocenter": "IBM Documentation",
            "knowledge center": "IBM Documentation", "dialog box": "dialog",
            "un-install": "uninstall", "de-install": "uninstall",
            "e-mail": "email", "end user": "user", "log on to": "log in to",
            "logon": "log in", "web site": "website", "work station": "workstation",
        }

        for i, sent in enumerate(doc.sents):
            for term, replacement in term_map.items():
                pattern = r'\b' + re.escape(term) + r'\b'
                for match in re.finditer(pattern, sent.text, re.IGNORECASE):
                    start = sent.start_char + match.start()
                    end = sent.start_char + match.end()
                    found = match.group(0)

                    # Try to align a token (best-effort; match may span tokens)
                    token = None
                    for t in sent:
                        if t.idx == start:
                            token = t
                            break

                    evidence_score = self._calculate_terminology_evidence(
                        found, replacement, token, sent, text, context or {}
                    )

                    if evidence_score > 0.1:
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=self._get_contextual_terminology_message(found, replacement, evidence_score),
                            suggestions=self._generate_smart_terminology_suggestions(found, replacement, evidence_score, sent, context or {}),
                            severity='medium',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,
                            span=(start, end),
                            flagged_text=found
                        ))
        return errors

    # === EVIDENCE-BASED CALCULATION ===

    def _calculate_terminology_evidence(self, found: str, preferred: str, token, sentence, text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence score (0.0-1.0) for terminology concerns.
        
        Higher scores indicate stronger evidence that non-preferred terminology should be replaced.
        Lower scores indicate acceptable usage in specific contexts.
        
        Args:
            found: The non-preferred term found
            preferred: The preferred replacement term
            token: The SpaCy token (if found)
            sentence: Sentence containing the term
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (acceptable) to 1.0 (should be replaced)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = self._get_base_terminology_evidence(found, preferred, token, sentence)
        
        if evidence_score == 0.0:
            return 0.0  # No evidence, skip this term
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_terminology(evidence_score, found, token, sentence, preferred)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_terminology(evidence_score, context, found)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_terminology(evidence_score, found, preferred, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_terminology(evidence_score, found, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    # === TERMINOLOGY EVIDENCE METHODS ===

    def _get_base_terminology_evidence(self, found: str, preferred: str, token, sentence) -> float:
        """Get base evidence score for terminology concerns."""
        
        # === TERM TYPE ANALYSIS ===
        # Different non-preferred terms have different evidence strengths
        
        # High-priority corrections (critical terminology issues)
        high_priority_terms = {
            'dialog box': 'dialog', 'e-mail': 'email', 'web site': 'website',
            'log on to': 'log in to', 'logon': 'log in', 'end user': 'user'
        }
        
        # Medium-priority corrections (important but less critical)
        medium_priority_terms = {
            'info center': 'IBM Documentation', 'infocenter': 'IBM Documentation',
            'knowledge center': 'IBM Documentation', 'work station': 'workstation'
        }
        
        # Low-priority corrections (style preferences)
        low_priority_terms = {
            'un-install': 'uninstall', 'de-install': 'uninstall'
        }
        
        # Check priority level
        found_lower = found.lower()
        if found_lower in high_priority_terms:
            return 0.8  # High evidence for critical terminology
        elif found_lower in medium_priority_terms:
            return 0.7  # Medium evidence for important corrections
        elif found_lower in low_priority_terms:
            return 0.6  # Lower evidence for style preferences
        else:
            return 0.65  # Default evidence for other non-preferred terms

    def _apply_linguistic_clues_terminology(self, evidence_score: float, found: str, token, sentence, preferred: str) -> float:
        """
        Apply linguistic analysis clues for terminology detection.
        
        Analyzes SpaCy linguistic features including NER, POS tags, morphological features,
        and surrounding context to determine evidence strength for terminology corrections.
        
        Args:
            evidence_score: Current evidence score to modify
            found: The non-preferred term found
            token: The SpaCy token (if found)
            sentence: Sentence containing the term
            preferred: The preferred replacement term
            
        Returns:
            float: Modified evidence score based on linguistic analysis
        """
        
        sent_text = sentence.text
        sent_lower = sent_text.lower()
        
        # === NAMED ENTITY RECOGNITION ===
        # Named entities should not be corrected
        if token is not None:
            ent_type = getattr(token, 'ent_type_', '')
            
            if ent_type in ['ORG', 'PRODUCT', 'WORK_OF_ART']:
                evidence_score -= 0.8  # Strong reduction for named entities
            elif ent_type in ['PERSON', 'GPE']:
                evidence_score -= 0.6  # Moderate reduction for person/place names
            elif ent_type in ['EVENT', 'LAW']:
                evidence_score -= 0.5  # Some reduction for events/laws
            
            # === PENN TREEBANK TAG ANALYSIS ===
            # Detailed grammatical analysis using Penn Treebank tags
            if hasattr(token, 'tag_'):
                tag = token.tag_
                
                # Proper noun tags analysis
                if tag in ['NNP', 'NNPS']:  # Proper nouns (singular and plural)
                    evidence_score -= 0.4  # Proper nouns may maintain original terminology
                # Common noun tags analysis
                elif tag in ['NN', 'NNS']:  # Common nouns
                    evidence_score += 0.1  # Common nouns should follow preferred terminology
                # Verb tags analysis
                elif tag in ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']:  # All verb forms
                    evidence_score += 0.12  # Verbs should be consistent with preferred terms
                # Adjective tags analysis
                elif tag in ['JJ', 'JJR', 'JJS']:  # Adjectives
                    evidence_score += 0.08  # Adjectives should follow preferred terminology
                # Modal verbs often in procedural contexts
                elif tag == 'MD':  # Modal verb
                    evidence_score += 0.05  # Modal contexts should use preferred terms
            
            # === DEPENDENCY PARSING ===
            # Analyze syntactic role which affects terminology importance
            if hasattr(token, 'dep_'):
                dep = token.dep_
                
                # Subject positions are more visible
                if dep in ['nsubj', 'nsubjpass']:
                    evidence_score += 0.05  # Subject position more prominent
                # Object positions
                elif dep in ['dobj', 'iobj', 'pobj']:
                    evidence_score += 0.03  # Object positions somewhat visible
                # Compound words may have specific terminology conventions
                elif dep == 'compound':
                    evidence_score -= 0.1  # Compounds may preserve specific terminology
                # Modifiers
                elif dep in ['amod', 'advmod']:
                    evidence_score += 0.02  # Modifiers should be consistent
                # Root words in sentences are more important
                elif dep == 'ROOT':
                    evidence_score += 0.08  # Root words are central to meaning
            
            # === LEMMA ANALYSIS ===
            # Base form analysis for terminology consistency
            if hasattr(token, 'lemma_'):
                lemma = token.lemma_.lower()
                
                # Check if the lemma itself suggests preferred terminology patterns
                preferred_lemmas = {'email', 'website', 'dialog', 'user', 'login', 'uninstall'}
                non_preferred_lemmas = {'e-mail', 'web site', 'dialog box', 'end user', 'log on', 'logon'}
                
                if lemma in preferred_lemmas:
                    evidence_score -= 0.1  # Lemma suggests this is actually preferred form
                elif lemma in non_preferred_lemmas:
                    evidence_score += 0.15  # Non-preferred lemma should be corrected
            
            # === MORPHOLOGICAL FEATURES ===
            # Morphological analysis for terminology patterns
            if hasattr(token, 'morph') and token.morph:
                morph_dict = token.morph.to_dict()
                
                # Check for foreign language markers
                if morph_dict.get('Foreign') == 'Yes':
                    evidence_score -= 0.3  # Foreign words may keep original terminology
                
                # Tense information can affect terminology decisions
                if morph_dict.get('Tense') == 'Past':
                    evidence_score += 0.02  # Past tense contexts should use preferred terms
                elif morph_dict.get('Tense') == 'Pres':
                    evidence_score += 0.05  # Present tense contexts should be current
            
            # === PART-OF-SPEECH ANALYSIS ===
            pos = getattr(token, 'pos_', '')
            
            if pos == 'PROPN':  # Proper noun
                evidence_score -= 0.4  # Proper nouns may maintain original terminology
            elif pos in ['NOUN', 'VERB']:
                evidence_score += 0.1  # Common words should follow preferred terminology
            
            # === CAPITALIZATION PATTERNS ===
            token_text = getattr(token, 'text', '')
            
            # All caps likely an acronym
            if token_text.isupper() and len(token_text) <= 15:
                evidence_score -= 0.4  # Acronyms should not be corrected
            
            # Title case mid-sentence might be a proper term
            if token_text.istitle() and not getattr(token, 'is_sent_start', False):
                evidence_score -= 0.2  # Proper terms may maintain original form
        
        # === SURROUNDING CONTEXT ===
        # Look for contextual clues in surrounding text
        
        # Quoted text often reports UI labels or specific names
        if '"' in sent_text or "'" in sent_text:
            evidence_score -= 0.2  # Quoted text may preserve original terminology
            
            # UI/UX strings: if found within quotes and includes typical UI nouns
            ui_indicators = ['button', 'menu', 'tab', 'dialog', 'window', 'field', 'label', 'option']
            if any(indicator in sent_lower for indicator in ui_indicators):
                evidence_score -= 0.15  # UI strings often preserve original terminology
        
        # Code context indicators
        if '`' in sent_text:
            evidence_score -= 0.3  # Code examples may use specific terminology
        
        # Parenthetical explanations might preserve legacy terms
        if '(' in sent_text and ')' in sent_text:
            # Check if the term is within parentheses
            import re
            paren_content = re.findall(r'\([^)]*\)', sent_text)
            if any(found.lower() in content.lower() for content in paren_content):
                evidence_score -= 0.2  # Parenthetical content may explain legacy terms
        
        # === LINGUISTIC PATTERNS ===
        # Check for patterns that suggest intentional usage
        
        # Legacy/historical context indicators
        legacy_indicators = [
            'formerly', 'previously', 'legacy', 'old', 'deprecated', 'historical',
            'original', 'traditional', 'classic', 'vintage'
        ]
        
        if any(indicator in sent_lower for indicator in legacy_indicators):
            evidence_score -= 0.3  # Legacy context may justify original terminology
        
        # Technical specification language
        spec_indicators = [
            'specification', 'standard', 'protocol', 'format', 'schema',
            'definition', 'requirement', 'compliance'
        ]
        
        if any(indicator in sent_lower for indicator in spec_indicators):
            evidence_score -= 0.1  # Specifications may preserve exact terminology
        
        # === FREQUENCY AND CONSISTENCY ===
        # Check for multiple instances of the same term
        found_count = sent_text.lower().count(found.lower())
        if found_count > 1:
            evidence_score += 0.1  # Multiple instances suggest intentional usage
        
        # Check for mixed terminology (both old and new terms present)
        if preferred.lower() in sent_lower:
            evidence_score += 0.2  # Mixed usage suggests need for consistency
        
        # === INSTRUCTION CONTEXT ===
        # Instructional language indicators
        instruction_indicators = ['click', 'select', 'choose', 'enter', 'type', 'configure']
        if any(indicator in sent_lower for indicator in instruction_indicators):
            evidence_score += 0.1  # Instructions should use preferred terminology
        
        # === COMPOUND TERM ANALYSIS ===
        # Check if this is part of a compound term or phrase
        if '-' in found or ' ' in found:
            # Multi-word terms may have specific usage patterns
            if len(found.split()) > 1:
                evidence_score += 0.05  # Multi-word terms often have standard forms
        
        return evidence_score

    def _apply_structural_clues_terminology(self, evidence_score: float, context: Dict[str, Any], found: str) -> float:
        """
        Apply document structure clues for terminology detection.
        
        Analyzes document structure context including block types, heading levels,
        list depth, and other structural elements to determine appropriate evidence
        adjustments for terminology corrections.
        
        Args:
            evidence_score: Current evidence score to modify
            context: Document context dictionary
            found: The non-preferred term found
            
        Returns:
            float: Modified evidence score based on structural analysis
        """
        
        block_type = context.get('block_type', 'paragraph')
        
        # === TECHNICAL DOCUMENTATION CONTEXTS ===
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.9  # Code blocks often contain exact terminology
        elif block_type == 'inline_code':
            evidence_score -= 0.7  # Inline code may reference specific terms
        
        # === HEADING CONTEXT ===
        if block_type == 'heading':
            heading_level = context.get('block_level', 1)
            if heading_level == 1:  # H1 - Main headings
                evidence_score += 0.1  # Main headings should use preferred terminology
            elif heading_level == 2:  # H2 - Section headings  
                evidence_score += 0.08  # Section headings should be consistent
            elif heading_level >= 3:  # H3+ - Subsection headings
                evidence_score += 0.05  # Subsection headings less critical
        elif block_type == 'title':
            evidence_score += 0.12  # Titles should use preferred terminology
        
        # === LIST CONTEXT ===
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score += 0.05  # Lists should use preferred terminology
            
            # Nested list items may be more technical
            if context.get('list_depth', 1) > 1:
                evidence_score -= 0.02  # Nested items may use specific terms
        
        # === TABLE CONTEXT ===
        elif block_type in ['table_cell', 'table_header']:
            if block_type == 'table_header':
                evidence_score += 0.08  # Table headers should be consistent
            else:
                evidence_score += 0.03  # Table cells should follow conventions
        
        # === ADMONITION CONTEXT ===
        elif block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'TIP', 'HINT']:
                evidence_score += 0.05  # Notes should use preferred terminology
            elif admonition_type in ['WARNING', 'CAUTION', 'DANGER']:
                evidence_score += 0.1  # Warnings should be clear and consistent
            elif admonition_type in ['IMPORTANT', 'ATTENTION']:
                evidence_score += 0.08  # Important notices should be consistent
        
        # === QUOTE/CITATION CONTEXT ===
        elif block_type in ['block_quote', 'citation']:
            evidence_score -= 0.4  # Quotes may preserve original terminology
        
        # === SIDEBAR/CALLOUT CONTEXT ===
        elif block_type in ['sidebar', 'callout']:
            evidence_score += 0.02  # Side content should be consistent
        
        # === EXAMPLE/SAMPLE CONTEXT ===
        elif block_type in ['example', 'sample']:
            evidence_score -= 0.2  # Examples may show legacy terminology
        
        # === FOOTNOTE/REFERENCE CONTEXT ===
        elif block_type in ['footnote', 'reference']:
            evidence_score -= 0.1  # References may preserve original terminology
        
        # === METADATA CONTEXT ===
        elif block_type in ['metadata', 'frontmatter']:
            evidence_score -= 0.3  # Metadata may preserve specific terms
        
        # === NAVIGATION CONTEXT ===
        elif block_type in ['menu', 'navigation', 'breadcrumb']:
            evidence_score += 0.05  # Navigation should use consistent terminology
        
        # === FORM CONTEXT ===
        elif block_type in ['form_field', 'form_label', 'form_description']:
            evidence_score += 0.08  # Forms should use preferred terminology
        
        return evidence_score

    def _apply_semantic_clues_terminology(self, evidence_score: float, found: str, preferred: str, text: str, context: Dict[str, Any]) -> float:
        """
        Apply semantic and content-type clues for terminology detection.
        
        Analyzes high-level semantic context including content type, domain, audience,
        document purpose, and terminology indicators to determine evidence strength
        for terminology corrections.
        
        Args:
            evidence_score: Current evidence score to modify
            found: The non-preferred term found
            preferred: The preferred replacement term
            text: Full document text
            context: Document context dictionary
            
        Returns:
            float: Modified evidence score based on semantic analysis
        """
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # === CONTENT TYPE ANALYSIS ===
        # Formal/technical content expects preferred terminology
        if content_type == 'technical':
            evidence_score += 0.15  # Technical writing should use standard terminology
        elif content_type == 'api':
            evidence_score += 0.2  # API docs need consistent terminology
        elif content_type == 'procedural':
            evidence_score += 0.18  # Procedures should use clear, standard terms
        elif content_type == 'legal':
            evidence_score += 0.25  # Legal writing must use precise terminology
        elif content_type == 'academic':
            evidence_score += 0.2  # Academic writing should follow standards
        elif content_type == 'marketing':
            evidence_score += 0.1  # Marketing should use current terminology
        elif content_type == 'narrative':
            evidence_score += 0.05  # Narrative may be more flexible
        elif content_type == 'tutorial':
            evidence_score += 0.15  # Tutorials should be clear and current
        
        # === DOMAIN-SPECIFIC PATTERNS ===
        if domain in ['software', 'engineering', 'devops']:
            evidence_score += 0.1  # Technical domains need standard terminology
        elif domain in ['legal', 'finance', 'medical']:
            evidence_score += 0.15  # Formal domains require precise terminology
        elif domain in ['compliance', 'regulatory']:
            evidence_score += 0.2  # Regulatory domains need official terminology
        elif domain in ['user-documentation', 'help']:
            evidence_score += 0.15  # User-facing docs should use current terms
        elif domain in ['training', 'education']:
            evidence_score += 0.12  # Educational content should be current
        elif domain in ['support', 'troubleshooting']:
            evidence_score += 0.1  # Support docs should use standard terms
        
        # === AUDIENCE CONSIDERATIONS ===
        if audience in ['beginner', 'general', 'consumer']:
            evidence_score += 0.1  # General audiences need current terminology
        elif audience in ['professional', 'business']:
            evidence_score += 0.12  # Professional content should be current
        elif audience in ['developer', 'technical', 'expert']:
            evidence_score += 0.08  # Technical audiences expect standard terms
        elif audience in ['academic', 'scientific']:
            evidence_score += 0.1  # Academic audiences value precision
        elif audience in ['support', 'help-desk']:
            evidence_score += 0.15  # Support staff need consistent terminology
        
        # === DOCUMENT LENGTH CONTEXT ===
        doc_length = len(text.split())
        if doc_length < 100:  # Short documents
            evidence_score += 0.05  # Even brief content should be current
        elif doc_length > 5000:  # Long documents
            evidence_score += 0.1  # Consistency important in long docs
        
        # === DOCUMENT PURPOSE ANALYSIS ===
        if self._is_ui_documentation(text):
            evidence_score += 0.2  # UI docs should use current terminology
        
        if self._is_installation_documentation(text):
            evidence_score += 0.15  # Installation docs should be current
        
        if self._is_troubleshooting_documentation(text):
            evidence_score += 0.18  # Troubleshooting should use standard terms
        
        if self._is_migration_documentation(text):
            evidence_score -= 0.1  # Migration docs may reference legacy terms
        
        if self._is_api_documentation(text):
            evidence_score += 0.2  # API docs need consistent terminology
        
        if self._is_policy_documentation(text):
            evidence_score += 0.25  # Policies must use official terminology
        
        # === HISTORICAL/LEGACY CONTEXT ANALYSIS ===
        # Reduce if explicitly referencing past terms
        legacy_indicators = [
            'legacy', 'formerly known as', 'previously called', 'historical term',
            'old terminology', 'deprecated', 'obsolete', 'previous version',
            'earlier version', 'original name', 'former name'
        ]
        
        text_lower = text.lower()
        legacy_count = sum(1 for indicator in legacy_indicators if indicator in text_lower)
        
        if legacy_count >= 1:
            evidence_score -= 0.15  # Some legacy context
        elif legacy_count >= 3:
            evidence_score -= 0.25  # Strong legacy context
        
        # === TERMINOLOGY CONSISTENCY ANALYSIS ===
        # Check document-wide terminology patterns
        if self._has_mixed_terminology(text, found, preferred):
            evidence_score += 0.15  # Mixed usage suggests need for consistency
        
        # === PRODUCT/VERSION CONTEXT ===
        # Check for product version indicators
        version_indicators = ['version', 'release', 'update', 'upgrade', 'new', 'latest']
        if any(indicator in text_lower for indicator in version_indicators):
            evidence_score += 0.1  # New versions should use current terminology
        
        # === BRAND/COMPANY CONTEXT ===
        # Check for IBM-specific context
        ibm_indicators = ['ibm', 'international business machines', 'red hat', 'watson']
        if any(indicator in text_lower for indicator in ibm_indicators):
            evidence_score += 0.1  # IBM contexts should use official terminology
        
        # === INDUSTRY STANDARDS ===
        # Some industries may have established terminology
        if self._is_technical_documentation(text):
            evidence_score += 0.2  # Standards docs should use official terminology
        
        if self._is_tutorial_content(text):
            evidence_score += 0.18  # Certification docs need precise terminology
        
        return evidence_score

    def _apply_feedback_clues_terminology(self, evidence_score: float, found: str, context: Dict[str, Any]) -> float:
        """
        Apply feedback patterns for terminology detection.
        
        Incorporates learned patterns from user feedback including acceptance rates,
        context-specific patterns, and correction success rates to refine evidence
        scoring for terminology corrections.
        
        Args:
            evidence_score: Current evidence score to modify
            found: The non-preferred term found
            context: Document context dictionary
            
        Returns:
            float: Modified evidence score based on feedback analysis
        """
        
        feedback_patterns = self._get_cached_feedback_patterns('terminology')
        
        # === TERM-SPECIFIC FEEDBACK ===
        found_lower = found.lower()
        
        # Check if this specific term is commonly accepted by users
        accepted_terms = feedback_patterns.get('accepted_terms', set())
        if found_lower in accepted_terms:
            evidence_score -= 0.4  # Users consistently accept this term
        
        flagged_terms = feedback_patterns.get('often_flagged_terms', set())
        if found_lower in flagged_terms:
            evidence_score += 0.2  # Users consistently flag this term
        
        # === CONTEXT-SPECIFIC FEEDBACK ===
        content_type = context.get('content_type', 'general')
        context_patterns = feedback_patterns.get(f'{content_type}_patterns', {})
        
        if found_lower in context_patterns.get('accepted', set()):
            evidence_score -= 0.3
        elif found_lower in context_patterns.get('flagged', set()):
            evidence_score += 0.2
        
        # === FREQUENCY-BASED PATTERNS ===
        # Pattern: Frequency of this term in documents
        term_frequency = feedback_patterns.get('term_frequencies', {}).get(found_lower, 0)
        if term_frequency > 15:  # Commonly seen term
            acceptance_rate = feedback_patterns.get('term_acceptance', {}).get(found_lower, 0.5)
            if acceptance_rate > 0.7:
                evidence_score -= 0.2  # Frequently accepted
            elif acceptance_rate < 0.3:
                evidence_score += 0.3  # Frequently corrected
        
        # === CORRECTION SUCCESS PATTERNS ===
        # Check success rate of corrections for this term
        correction_patterns = feedback_patterns.get('correction_success', {})
        correction_success = correction_patterns.get(found_lower, 0.5)
        
        if correction_success > 0.8:
            evidence_score += 0.1  # Corrections highly successful
        elif correction_success < 0.3:
            evidence_score -= 0.2  # Corrections often rejected
        
        # === UI/LEGACY TERM PATTERNS ===
        # Check if this is a known UI term that users accept
        ui_patterns = feedback_patterns.get('ui_term_patterns', set())
        if found_lower in ui_patterns:
            evidence_score -= 0.3  # UI terms may be acceptable in context
        
        # === DOMAIN-SPECIFIC PATTERNS ===
        # Check if users in certain domains prefer this term
        domain = context.get('domain', 'general')
        domain_patterns = feedback_patterns.get(f'{domain}_patterns', {})
        if found_lower in domain_patterns.get('accepted', set()):
            evidence_score -= 0.2  # Domain-specific acceptance
        elif found_lower in domain_patterns.get('flagged', set()):
            evidence_score += 0.2  # Domain-specific rejection
        
        # === MIGRATION/LEGACY FEEDBACK ===
        # Check patterns for migration/legacy contexts
        legacy_patterns = feedback_patterns.get('legacy_context_patterns', {})
        if found_lower in legacy_patterns.get('acceptable_in_legacy', set()):
            # Check if document seems to be legacy/migration focused
            doc_text = context.get('document_text', '').lower()
            legacy_indicators = ['migration', 'legacy', 'upgrade', 'transition']
            if any(indicator in doc_text for indicator in legacy_indicators):
                evidence_score -= 0.2  # Legacy context acceptance
        
        return evidence_score

    # Removed _get_cached_feedback_patterns_terminology - using base class utility

    # === HELPER METHODS FOR SEMANTIC ANALYSIS ===

    # Removed _is_user_interface_documentation - using base class utility

    # Removed _is_installation_documentation - using base class utility

    # Removed _is_troubleshooting_documentation - using base class utility

    def _is_migration_documentation(self, text: str) -> bool:
        """Check if text appears to be migration documentation."""
        migration_indicators = [
            'migration', 'migrate', 'upgrade', 'transition', 'move', 'convert',
            'legacy', 'old version', 'new version', 'compatibility', 'backward'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in migration_indicators if indicator in text_lower) >= 3

    def _is_ui_documentation(self, text: str) -> bool:
        """Check if text appears to be user interface documentation."""
        ui_indicators = [
            'user interface', 'ui', 'gui', 'dialog', 'window', 'button', 'menu',
            'toolbar', 'tab', 'panel', 'form', 'field', 'dropdown', 'checkbox',
            'click', 'select', 'enter', 'type'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in ui_indicators if indicator in text_lower) >= 3

    # Removed _is_api_documentation - using base class utility

    # Removed _is_policy_documentation - using base class utility

    # Removed _is_standards_documentation - using base class utility

    # Removed _is_certification_documentation - using base class utility

    def _has_mixed_terminology(self, text: str, found: str, preferred: str) -> bool:
        """Check if document has mixed usage of old and new terminology."""
        text_lower = text.lower()
        found_count = text_lower.count(found.lower())
        preferred_count = text_lower.count(preferred.lower())
        
        # If both terms appear, there's mixed usage
        return found_count > 0 and preferred_count > 0

    # === HELPER METHODS FOR SMART MESSAGING ===

    def _get_contextual_terminology_message(self, found: str, preferred: str, evidence_score: float) -> str:
        """Generate context-aware error messages for terminology patterns."""
        
        if evidence_score > 0.9:
            return f"Non-preferred term '{found}' detected. Use '{preferred}' per IBM Style guidelines."
        elif evidence_score > 0.7:
            return f"Consider using preferred term '{preferred}' instead of '{found}'."
        elif evidence_score > 0.5:
            return f"Preferred term '{preferred}' is recommended instead of '{found}' for consistency."
        else:
            return f"The term '{found}' may benefit from using '{preferred}' for current standards."

    def _generate_smart_terminology_suggestions(self, found: str, preferred: str, evidence_score: float, sentence, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for terminology patterns."""
        
        suggestions = []
        
        # Base suggestions based on evidence strength
        if evidence_score > 0.8:
            suggestions.append(f"Replace '{found}' with '{preferred}' to follow current IBM terminology.")
            suggestions.append("Ensure consistent terminology throughout the document.")
        else:
            suggestions.append(f"Consider using '{preferred}' instead of '{found}' for consistency.")
        
        # Context-specific advice
        if context:
            content_type = context.get('content_type', 'general')
            
            if content_type in ['technical', 'api']:
                suggestions.append("Technical documentation should use current, standard terminology.")
            elif content_type in ['procedural', 'tutorial']:
                suggestions.append("Step-by-step instructions should use clear, current terminology.")
            elif content_type in ['legal', 'policy']:
                suggestions.append("Official documentation must use precise, approved terminology.")
            elif content_type == 'marketing':
                suggestions.append("Marketing content should use current, customer-facing terminology.")
        
        # Special handling for quoted/code contexts
        sentence_text = getattr(sentence, 'text', '')
        if '"' in sentence_text or "'" in sentence_text:
            suggestions.append("If this is a quoted label or UI string, verify it matches the actual interface.")
        elif '`' in sentence_text:
            suggestions.append("If this is code or a system identifier, confirm it's not a specific term.")
        
        # Legacy/historical context handling
        if any(word in sentence_text.lower() for word in ['legacy', 'formerly', 'previously', 'old']):
            suggestions.append("If discussing historical terms, consider clarifying with current terminology.")
        
        # IBM Style alignment
        suggestions.append("Align terminology with IBM Style for consistency across documents.")
        
        return suggestions[:3]
