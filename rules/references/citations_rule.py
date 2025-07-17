"""
Citations and References Rule
Based on IBM Style Guide topic: "Citations and references"
Enhanced with pure SpaCy morphological analysis for robust citation and reference validation.
"""
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict
from .base_references_rule import BaseReferencesRule

class CitationsRule(BaseReferencesRule):
    """
    Checks for incorrect formatting of citations and links using advanced morphological analysis
    to detect problematic link text, improper reference capitalization, and citation formatting issues.
    Uses context-aware detection instead of simple pattern matching.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize citation-specific linguistic anchors
        self._initialize_citation_anchors()
    
    def _initialize_citation_anchors(self):
        """Initialize morphological patterns specific to citation and reference analysis."""
        
        # Citation and link morphological patterns
        self.citation_morphological_patterns = {
            'problematic_link_patterns': {
                'generic_imperatives': ['click here', 'click this', 'see here', 'go here'],
                'vague_demonstratives': ['this link', 'that link', 'the link', 'above link'],
                'action_only': ['click', 'see', 'go', 'visit', 'check'],
                'morphological_indicators': ['VERB+imperative', 'DT+ADV', 'PRON+demonstrative']
            },
            'reference_capitalization': {
                'document_parts': ['chapter', 'section', 'appendix', 'figure', 'table', 'page'],
                'citation_elements': ['volume', 'issue', 'edition', 'version'],
                'formal_references': ['bibliography', 'index', 'glossary', 'footnote'],
                'capitalization_contexts': ['standalone', 'with_number', 'formal_title']
            },
            'citation_formatting': {
                'numeric_patterns': ['chapter 5', 'figure 3', 'table 2', 'page 10'],
                'formal_patterns': ['Chapter 5', 'Figure 3', 'Table 2', 'Page 10'],
                'academic_patterns': ['(Smith, 2023)', '[1]', 'ibid.', 'op. cit.'],
                'web_patterns': ['URL', 'DOI', 'permalink', 'hyperlink']
            }
        }
        
        # Link quality and context patterns
        self.link_quality_patterns = {
            'descriptive_link_text': {
                'good_patterns': ['Installation Guide', 'User Manual', 'API Reference'],
                'content_descriptors': ['guide', 'manual', 'tutorial', 'documentation'],
                'action_descriptors': ['download', 'read more', 'learn about'],
                'specificity_indicators': ['detailed', 'comprehensive', 'step-by-step']
            },
            'link_context_indicators': {
                'navigation_context': ['menu', 'navigation', 'sidebar', 'header'],
                'content_context': ['article', 'blog post', 'white paper', 'report'],
                'resource_context': ['download', 'file', 'document', 'resource'],
                'external_context': ['website', 'external', 'third-party']
            },
            'accessibility_patterns': {
                'screen_reader_friendly': ['descriptive', 'meaningful', 'contextual'],
                'problematic_for_accessibility': ['generic', 'vague', 'ambiguous'],
                'aria_patterns': ['aria-label', 'title attribute', 'alt text']
            }
        }
        
        # Reference formatting and style patterns
        self.reference_style_patterns = {
            'academic_styles': {
                'apa_style': ['(Author, Year)', 'Author (Year)', 'p. 123'],
                'mla_style': ['(Author 123)', 'Author argues', 'Works Cited'],
                'chicago_style': ['footnote', 'endnote', 'bibliography'],
                'ieee_style': ['[1]', '[2]-[5]', 'et al.']
            },
            'digital_references': {
                'url_patterns': ['http://', 'https://', 'www.', '.com', '.org'],
                'doi_patterns': ['DOI:', 'doi:', '10.', 'dx.doi.org'],
                'permalink_patterns': ['permalink', 'permanent link', 'stable URL'],
                'archived_patterns': ['wayback machine', 'archive.org', 'archived']
            },
            'cross_reference_patterns': {
                'internal_references': ['see section', 'refer to', 'as mentioned in'],
                'forward_references': ['see below', 'later in', 'following section'],
                'backward_references': ['see above', 'earlier in', 'previous section'],
                'conditional_references': ['if applicable', 'where relevant', 'as needed']
            }
        }

    def _get_rule_type(self) -> str:
        return 'references_citations'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for citation and linking errors using comprehensive
        morphological and semantic analysis.
        """
        errors = []
        if not nlp:
            return errors

        # Build comprehensive context about citations and references across the text
        citation_context = self._build_citation_context(text, sentences, nlp)

        for i, sentence in enumerate(sentences):
            doc = self._analyze_sentence_structure(sentence, nlp)
            if not doc:
                continue
            
            # Use the base class method for citation pattern analysis
            citation_errors = self._analyze_citation_patterns(doc, sentence, i)
            errors.extend(citation_errors)
            
            # Additional citation-specific analysis
            additional_errors = self._analyze_citation_specific_patterns(
                doc, sentence, i, citation_context
            )
            errors.extend(additional_errors)

        return errors
    
    def _build_citation_context(self, text: str, sentences: List[str], nlp) -> Dict[str, Any]:
        """
        Build comprehensive context about citation and reference usage across the entire text.
        """
        context = {
            'link_patterns': [],
            'reference_patterns': [],
            'citation_style': 'informal',
            'document_type': 'technical',
            'problematic_links': [],
            'reference_capitalization_patterns': defaultdict(set),
            'cross_references': [],
            'external_references': [],
            'accessibility_concerns': []
        }
        
        try:
            # Analyze the entire text to understand citation patterns
            full_doc = self._analyze_sentence_structure(text, nlp)
            if full_doc:
                # Extract all link and citation patterns
                context['link_patterns'] = self._extract_link_patterns(full_doc)
                
                # Analyze reference patterns
                context['reference_patterns'] = self._extract_reference_patterns(full_doc)
                
                # Determine citation style
                context['citation_style'] = self._determine_citation_style(full_doc)
                
                # Find cross-references
                context['cross_references'] = self._find_cross_references(full_doc)
                
                # Detect external references
                context['external_references'] = self._detect_external_references(full_doc)
                
                # Track reference capitalization patterns
                for ref_pattern in context['reference_patterns']:
                    ref_type = ref_pattern['reference_type']
                    cap_pattern = ref_pattern['capitalization_pattern']
                    context['reference_capitalization_patterns'][ref_type].add(cap_pattern)
        
        except Exception:
            pass
        
        return context
    
    def _analyze_citation_specific_patterns(self, doc, sentence: str, sentence_index: int, 
                                          citation_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze citation-specific patterns that require correction.
        """
        errors = []
        
        if not doc:
            return errors
        
        # Detect problematic link text
        link_text_errors = self._detect_problematic_link_text(doc, citation_context)
        for error in link_text_errors:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Problematic link text: '{error['link_text']}'. Use descriptive link text.",
                suggestions=error['suggestions'],
                severity='high',
                linguistic_analysis={
                    'link_text_error': error,
                    'morphological_pattern': error.get('morphological_pattern'),
                    'accessibility_impact': error.get('accessibility_impact')
                }
            ))
        
        # Detect reference capitalization errors
        ref_cap_errors = self._detect_reference_capitalization_errors(doc, citation_context)
        for error in ref_cap_errors:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Reference '{error['reference']}' has incorrect capitalization.",
                suggestions=error['suggestions'],
                severity='medium',
                linguistic_analysis={
                    'reference_cap_error': error,
                    'reference_context': error.get('context_type'),
                    'capitalization_rule': error.get('applicable_rule')
                }
            ))
        
        # Detect citation formatting inconsistencies
        format_errors = self._detect_citation_formatting_errors(doc, citation_context)
        for error in format_errors:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Citation formatting issue: '{error['citation']}'. Use consistent style.",
                suggestions=error['suggestions'],
                severity='medium',
                linguistic_analysis={
                    'format_error': error,
                    'expected_style': error.get('expected_style'),
                    'style_consistency': error.get('consistency_analysis')
                }
            ))
        
        # Detect accessibility concerns
        accessibility_errors = self._detect_accessibility_concerns(doc, citation_context)
        for error in accessibility_errors:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Accessibility concern: '{error['element']}'. Improve for screen readers.",
                suggestions=error['suggestions'],
                severity='low',
                linguistic_analysis={
                    'accessibility_error': error,
                    'impact_type': error.get('impact_type'),
                    'user_groups_affected': error.get('affected_users')
                }
            ))
        
        return errors
    
    def _extract_link_patterns(self, doc) -> List[Dict[str, Any]]:
        """
        Extract link patterns using advanced morphological analysis.
        """
        link_patterns = []
        
        if not doc:
            return link_patterns
        
        try:
            # Detect potential link text using morphological patterns
            for i, token in enumerate(doc):
                # Look for imperative patterns that might be links
                if self._is_potential_link_text(token, doc, i):
                    link_analysis = self._analyze_link_text_quality(token, doc, i)
                    link_patterns.append(link_analysis)
            
            # Also look for explicit link indicators
            explicit_links = self._detect_explicit_link_indicators(doc)
            link_patterns.extend(explicit_links)
        
        except Exception:
            pass
        
        return link_patterns
    
    def _extract_reference_patterns(self, doc) -> List[Dict[str, Any]]:
        """
        Extract reference patterns using morphological analysis.
        """
        reference_patterns = []
        
        if not doc:
            return reference_patterns
        
        try:
            # Look for reference words followed by numbers or titles
            for token in doc:
                if self._is_reference_word(token.text):
                    ref_analysis = self._analyze_reference_pattern(token, doc)
                    
                    if ref_analysis['is_reference']:
                        reference_patterns.append(ref_analysis)
        
        except Exception:
            pass
        
        return reference_patterns
    
    def _determine_citation_style(self, doc) -> str:
        """
        Determine the citation style used in the document.
        """
        try:
            # Look for citation style indicators
            style_indicators = {
                'academic': ['(Author, Year)', 'et al.', 'ibid.'],
                'informal': ['see section', 'refer to', 'check out'],
                'technical': ['Figure 1', 'Table 2', 'Listing 3'],
                'web': ['URL', 'link', 'website']
            }
            
            style_scores = defaultdict(int)
            
            for sent in doc.sents:
                sent_text = sent.text.lower()
                for style, indicators in style_indicators.items():
                    for indicator in indicators:
                        if indicator.lower() in sent_text:
                            style_scores[style] += 1
            
            # Return the most common style
            if style_scores:
                return max(style_scores.keys(), key=lambda k: style_scores[k])
            else:
                return 'informal'
        
        except Exception:
            return 'informal'
    
    def _find_cross_references(self, doc) -> List[Dict[str, Any]]:
        """
        Find cross-references within the document.
        """
        cross_references = []
        
        try:
            cross_ref_patterns = ['see section', 'refer to', 'as mentioned in', 'see above', 'see below']
            
            for sent in doc.sents:
                sent_text = sent.text.lower()
                for pattern in cross_ref_patterns:
                    if pattern in sent_text:
                        cross_ref_analysis = {
                            'pattern': pattern,
                            'sentence': sent.text,
                            'type': self._classify_cross_reference_type(pattern),
                            'morphological_context': self._analyze_cross_ref_morphology(sent)
                        }
                        cross_references.append(cross_ref_analysis)
        
        except Exception:
            pass
        
        return cross_references
    
    def _detect_external_references(self, doc) -> List[Dict[str, Any]]:
        """
        Detect references to external sources.
        """
        external_references = []
        
        try:
            # Look for URL patterns, DOIs, etc.
            for token in doc:
                if self._looks_like_external_reference(token.text):
                    external_ref = {
                        'text': token.text,
                        'type': self._classify_external_reference_type(token.text),
                        'context': self._analyze_external_ref_context(token, doc)
                    }
                    external_references.append(external_ref)
        
        except Exception:
            pass
        
        return external_references
    
    def _detect_problematic_link_text(self, doc, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect problematic link text patterns using morphological analysis.
        """
        problematic_links = []
        
        try:
            for link_pattern in context['link_patterns']:
                if link_pattern.get('is_problematic'):
                    problem_analysis = self._analyze_link_text_problems(link_pattern)
                    
                    error_info = {
                        'link_text': link_pattern['text'],
                        'problem_type': problem_analysis['problem_type'],
                        'suggestions': problem_analysis['suggestions'],
                        'morphological_pattern': link_pattern.get('morphological_pattern'),
                        'accessibility_impact': problem_analysis.get('accessibility_impact')
                    }
                    problematic_links.append(error_info)
        
        except Exception:
            pass
        
        return problematic_links
    
    def _detect_reference_capitalization_errors(self, doc, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect incorrect capitalization in references.
        """
        capitalization_errors = []
        
        try:
            for ref_pattern in context['reference_patterns']:
                if ref_pattern.get('capitalization_error'):
                    cap_analysis = self._analyze_reference_capitalization_error(ref_pattern)
                    
                    error_info = {
                        'reference': ref_pattern['text'],
                        'current_capitalization': ref_pattern['current_pattern'],
                        'expected_capitalization': cap_analysis['expected_pattern'],
                        'context_type': ref_pattern.get('context_type'),
                        'applicable_rule': cap_analysis['rule'],
                        'suggestions': cap_analysis['suggestions']
                    }
                    capitalization_errors.append(error_info)
        
        except Exception:
            pass
        
        return capitalization_errors
    
    def _detect_citation_formatting_errors(self, doc, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect citation formatting inconsistencies.
        """
        formatting_errors = []
        
        try:
            # Check for style consistency
            expected_style = context['citation_style']
            
            for ref_pattern in context['reference_patterns']:
                if ref_pattern.get('style_mismatch'):
                    format_analysis = self._analyze_formatting_inconsistency(ref_pattern, expected_style)
                    
                    error_info = {
                        'citation': ref_pattern['text'],
                        'current_style': ref_pattern['detected_style'],
                        'expected_style': expected_style,
                        'suggestions': format_analysis['suggestions'],
                        'consistency_analysis': format_analysis
                    }
                    formatting_errors.append(error_info)
        
        except Exception:
            pass
        
        return formatting_errors
    
    def _detect_accessibility_concerns(self, doc, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect accessibility concerns in citations and links.
        """
        accessibility_errors = []
        
        try:
            for link_pattern in context['link_patterns']:
                accessibility_analysis = self._analyze_accessibility_impact(link_pattern)
                
                if accessibility_analysis['has_concerns']:
                    for concern in accessibility_analysis['concerns']:
                        error_info = {
                            'element': link_pattern['text'],
                            'concern_type': concern['type'],
                            'impact_type': concern['impact'],
                            'affected_users': concern['affected_users'],
                            'suggestions': concern['suggestions']
                        }
                        accessibility_errors.append(error_info)
        
        except Exception:
            pass
        
        return accessibility_errors
    
    # Helper methods implementation
    def _is_potential_link_text(self, token, doc, token_index: int) -> bool:
        """Check if token is part of potential link text."""
        try:
            # Look for imperative verbs or demonstrative patterns
            if token.pos_ == 'VERB' and token.tag_ == 'VB':  # Imperative verb
                return True
            
            # Look for "click here" patterns
            if (token.text.lower() in ['click', 'see', 'go'] and 
                token_index + 1 < len(doc) and 
                doc[token_index + 1].text.lower() == 'here'):
                return True
            
            # Look for demonstrative patterns
            if token.text.lower() in ['this', 'that'] and self._followed_by_link_word(token, doc):
                return True
            
            return False
        except Exception:
            return False
    
    def _analyze_link_text_quality(self, token, doc, token_index: int) -> Dict[str, Any]:
        """Analyze the quality of link text."""
        try:
            # Extract full link text phrase
            link_phrase = self._extract_link_phrase(token, doc, token_index)
            
            # Analyze quality
            quality_analysis = self._assess_link_text_quality(link_phrase)
            
            return {
                'text': link_phrase,
                'is_problematic': quality_analysis['is_problematic'],
                'quality_score': quality_analysis['score'],
                'morphological_pattern': f"{token.pos_}+{token.dep_}",
                'improvement_suggestions': quality_analysis['suggestions']
            }
        except Exception:
            return {
                'text': token.text,
                'is_problematic': False,
                'quality_score': 0.5
            }
    
    def _detect_explicit_link_indicators(self, doc) -> List[Dict[str, Any]]:
        """Detect explicit link indicators."""
        explicit_links = []
        
        try:
            link_indicators = ['URL', 'link', 'website', 'http', 'www']
            
            for token in doc:
                if any(indicator in token.text.lower() for indicator in link_indicators):
                    explicit_links.append({
                        'text': token.text,
                        'type': 'explicit_link_indicator',
                        'is_problematic': False,  # Usually not problematic
                        'quality_score': 0.7
                    })
        except Exception:
            pass
        
        return explicit_links
    
    def _is_reference_word(self, text: str) -> bool:
        """Check if text is a reference word."""
        reference_words = [
            'chapter', 'section', 'appendix', 'figure', 'table', 'page',
            'volume', 'issue', 'edition', 'version', 'bibliography'
        ]
        return text.lower() in reference_words
    
    def _analyze_reference_pattern(self, token, doc) -> Dict[str, Any]:
        """Analyze a reference pattern."""
        try:
            # Look for following number or title
            next_tokens = []
            for i in range(token.i + 1, min(len(doc), token.i + 3)):
                next_tokens.append(doc[i])
            
            # Check if this looks like a reference
            is_reference = any(t.like_num for t in next_tokens)
            
            # Analyze capitalization
            current_cap = 'title_case' if token.text[0].isupper() else 'sentence_case'
            
            # Determine expected capitalization based on context
            expected_cap = self._determine_expected_reference_capitalization(token, doc)
            
            return {
                'text': token.text,
                'is_reference': is_reference,
                'reference_type': token.text.lower(),
                'current_pattern': current_cap,
                'expected_pattern': expected_cap,
                'capitalization_error': current_cap != expected_cap,
                'context_type': self._determine_reference_context(token, doc),
                'morphological_features': self._get_morphological_features(token)
            }
        except Exception:
            return {
                'text': token.text,
                'is_reference': False
            }
    
    def _classify_cross_reference_type(self, pattern: str) -> str:
        """Classify the type of cross-reference."""
        if 'above' in pattern or 'earlier' in pattern:
            return 'backward_reference'
        elif 'below' in pattern or 'later' in pattern:
            return 'forward_reference'
        else:
            return 'general_reference'
    
    def _analyze_cross_ref_morphology(self, sentence) -> Dict[str, Any]:
        """Analyze morphological features of cross-reference."""
        return {
            'sentence_length': len(list(sentence)),
            'contains_numbers': any(token.like_num for token in sentence),
            'imperative_verbs': [token.text for token in sentence if token.pos_ == 'VERB' and token.tag_ == 'VB']
        }
    
    def _looks_like_external_reference(self, text: str) -> bool:
        """Check if text looks like an external reference."""
        external_patterns = ['http', 'www', '.com', '.org', 'doi:', 'DOI:']
        return any(pattern in text for pattern in external_patterns)
    
    def _classify_external_reference_type(self, text: str) -> str:
        """Classify the type of external reference."""
        if 'http' in text or 'www' in text:
            return 'url'
        elif 'doi' in text.lower():
            return 'doi'
        else:
            return 'unknown'
    
    def _analyze_external_ref_context(self, token, doc) -> Dict[str, Any]:
        """Analyze context around external reference."""
        return {
            'preceding_words': [doc[max(0, token.i - 2):token.i]],
            'following_words': [doc[token.i + 1:min(len(doc), token.i + 3)]],
            'sentence_context': token.sent.text
        }
    
    def _analyze_link_text_problems(self, link_pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze specific problems with link text."""
        try:
            text = link_pattern['text'].lower()
            
            problem_type = 'unknown'
            suggestions = []
            accessibility_impact = 'low'
            
            if 'click here' in text:
                problem_type = 'generic_imperative'
                suggestions = [
                    "Replace 'click here' with descriptive text",
                    "Example: 'Download the User Guide' instead of 'Click here to download'"
                ]
                accessibility_impact = 'high'
            elif text in ['this', 'that', 'here', 'there']:
                problem_type = 'vague_demonstrative'
                suggestions = [
                    "Use specific, descriptive link text",
                    "Describe what the link leads to"
                ]
                accessibility_impact = 'medium'
            elif len(text.split()) == 1 and text in ['click', 'see', 'go']:
                problem_type = 'action_only'
                suggestions = [
                    "Provide context for the action",
                    "Example: 'See the installation instructions'"
                ]
                accessibility_impact = 'medium'
            
            return {
                'problem_type': problem_type,
                'suggestions': suggestions,
                'accessibility_impact': accessibility_impact
            }
        except Exception:
            return {
                'problem_type': 'unknown',
                'suggestions': [],
                'accessibility_impact': 'low'
            }
    
    def _analyze_reference_capitalization_error(self, ref_pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze reference capitalization error."""
        try:
            ref_type = ref_pattern['reference_type']
            context_type = ref_pattern.get('context_type', 'standalone')
            
            # Determine the rule and expected pattern
            if context_type == 'with_number':
                expected_pattern = 'sentence_case'
                rule = 'References with numbers should use sentence case'
            elif context_type == 'formal_title':
                expected_pattern = 'title_case'
                rule = 'Formal titles should use title case'
            else:
                expected_pattern = 'sentence_case'
                rule = 'Generic references should use sentence case'
            
            # Generate suggestions
            current_text = ref_pattern['text']
            if expected_pattern == 'sentence_case':
                corrected = current_text.lower()
                suggestions = [f"Use lowercase: '{corrected}'"]
            else:
                corrected = current_text.capitalize()
                suggestions = [f"Use title case: '{corrected}'"]
            
            suggestions.append(f"Rule: {rule}")
            
            return {
                'expected_pattern': expected_pattern,
                'rule': rule,
                'suggestions': suggestions
            }
        except Exception:
            return {
                'expected_pattern': 'sentence_case',
                'rule': 'Default to sentence case',
                'suggestions': []
            }
    
    def _analyze_formatting_inconsistency(self, ref_pattern: Dict[str, Any], expected_style: str) -> Dict[str, Any]:
        """Analyze formatting inconsistency."""
        return {
            'inconsistency_type': 'style_mismatch',
            'suggestions': [f"Use consistent {expected_style} style throughout the document"],
            'severity': 'medium'
        }
    
    def _analyze_accessibility_impact(self, link_pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze accessibility impact of link pattern."""
        try:
            text = link_pattern['text'].lower()
            concerns = []
            
            # Check for screen reader issues
            if any(problem in text for problem in ['click here', 'here', 'this']):
                concerns.append({
                    'type': 'screen_reader_confusion',
                    'impact': 'high',
                    'affected_users': ['screen_reader_users', 'voice_navigation_users'],
                    'suggestions': ['Use descriptive link text that makes sense out of context']
                })
            
            # Check for keyboard navigation issues
            if len(text.split()) == 1 and text in ['click', 'go']:
                concerns.append({
                    'type': 'keyboard_navigation_confusion',
                    'impact': 'medium',
                    'affected_users': ['keyboard_only_users'],
                    'suggestions': ['Provide sufficient context for keyboard users']
                })
            
            return {
                'has_concerns': len(concerns) > 0,
                'concerns': concerns
            }
        except Exception:
            return {'has_concerns': False, 'concerns': []}
    
    def _followed_by_link_word(self, token, doc) -> bool:
        """Check if token is followed by a link-related word."""
        if token.i + 1 < len(doc):
            next_token = doc[token.i + 1]
            return next_token.text.lower() in ['link', 'page', 'site', 'url']
        return False
    
    def _extract_link_phrase(self, token, doc, token_index: int) -> str:
        """Extract the full link phrase."""
        try:
            phrase_tokens = [token.text]
            
            # Look ahead for related tokens
            for i in range(token_index + 1, min(len(doc), token_index + 4)):
                next_token = doc[i]
                if next_token.text.lower() in ['here', 'this', 'that', 'link']:
                    phrase_tokens.append(next_token.text)
                else:
                    break
            
            return ' '.join(phrase_tokens)
        except Exception:
            return token.text
    
    def _assess_link_text_quality(self, link_phrase: str) -> Dict[str, Any]:
        """Assess the quality of link text."""
        try:
            score = 1.0  # Start with perfect score
            is_problematic = False
            suggestions = []
            
            phrase_lower = link_phrase.lower()
            
            # Check for problematic patterns
            if phrase_lower in ['click here', 'see here', 'go here']:
                score -= 0.8
                is_problematic = True
                suggestions.append("Use descriptive text instead of generic 'click here'")
            
            if phrase_lower in ['this', 'that', 'here', 'there']:
                score -= 0.6
                is_problematic = True
                suggestions.append("Specify what 'this' or 'that' refers to")
            
            if len(phrase_lower.split()) == 1 and phrase_lower in ['click', 'see', 'go']:
                score -= 0.5
                is_problematic = True
                suggestions.append("Provide context for the action")
            
            # Bonus for descriptive text
            if len(link_phrase.split()) > 2 and not is_problematic:
                score = min(score + 0.2, 1.0)
            
            return {
                'score': max(score, 0.0),
                'is_problematic': is_problematic,
                'suggestions': suggestions
            }
        except Exception:
            return {'score': 0.5, 'is_problematic': False, 'suggestions': []}
    
    def _determine_expected_reference_capitalization(self, token, doc) -> str:
        """Determine expected capitalization for reference."""
        try:
            # Look at following tokens to understand context
            if token.i + 1 < len(doc):
                next_token = doc[token.i + 1]
                
                # If followed by a number, use sentence case
                if next_token.like_num:
                    return 'sentence_case'
                
                # If in a formal title context, use title case
                if self._is_in_formal_title_context(token, doc):
                    return 'title_case'
            
            # Default to sentence case
            return 'sentence_case'
        except Exception:
            return 'sentence_case'
    
    def _determine_reference_context(self, token, doc) -> str:
        """Determine the context of a reference."""
        try:
            # Check if followed by number
            if token.i + 1 < len(doc) and doc[token.i + 1].like_num:
                return 'with_number'
            
            # Check if in formal context
            if self._is_in_formal_title_context(token, doc):
                return 'formal_title'
            
            return 'standalone'
        except Exception:
            return 'standalone'
    
    def _is_in_formal_title_context(self, token, doc) -> bool:
        """Check if token is in a formal title context."""
        try:
            # Simple heuristic: check if sentence starts with the reference
            sentence = token.sent
            return token.i == sentence.start
        except Exception:
            return False
