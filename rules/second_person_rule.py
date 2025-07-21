"""
Second Person Rule (Consolidated)
Based on IBM Style Guide topic: "Verbs: Person"
Enhanced with pure SpaCy morphological analysis and linguistic anchors.
"""
from typing import List, Dict, Any, Set, Optional
from .language_and_grammar.base_language_rule import BaseLanguageRule

class SecondPersonRule(BaseLanguageRule):
    """
    Enforces the use of second person ("you") using pure spaCy morphological analysis.
    Uses linguistic anchors to detect first-person pronouns and third-person substitutes
    while avoiding false positives in compound nouns and proper names.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize linguistic anchors for person analysis
        self._initialize_person_anchors()
    
    def _initialize_person_anchors(self):
        """Initialize morphological and semantic anchors for person analysis."""
        
        # First person morphological patterns
        self.first_person_patterns = {
            'pronoun_indicators': {
                'subject_pronouns': {'i', 'we'},
                'object_pronouns': {'me', 'us'},
                'possessive_pronouns': {'my', 'our', 'mine', 'ours'},
                'morphological_features': ['Person=1', 'PRON+Person=1'],
                'dependency_patterns': ['nsubj+PRON', 'poss+PRON', 'dobj+PRON']
            },
            'contextual_exceptions': {
                'proper_name_contexts': True,  # "Our Company Inc."
                'quotation_contexts': True,    # Direct quotes
                'compound_constructions': ['our+PROPN', 'we+NOUN+PROPN'],
                'brand_names': ['our', 'we']  # When part of brand/company names
            }
        }
        
        # Third person substitute patterns
        self.third_person_substitute_patterns = {
            'user_substitutes': {
                'generic_users': {'user', 'users'},
                'role_substitutes': {'administrator', 'admin', 'developer', 'operator', 'customer'},
                'system_agents': {'person', 'individual', 'someone', 'anyone'},
                'morphological_context': ['NOUN+user', 'det+NOUN+user']
            },
            'compound_exceptions': {
                'interface_compounds': {'user interface', 'user account', 'user profile', 'user name'},
                'technical_compounds': {'user id', 'user credentials', 'user group', 'user data'},
                'system_compounds': {'user session', 'user settings', 'user preferences'},
                'compound_followers': {'interface', 'id', 'account', 'profile', 'name', 'group', 'credentials', 
                                     'session', 'settings', 'preferences', 'data', 'input', 'output'}
            },
            'acceptable_contexts': {
                'reference_documentation': True,  # Technical specifications
                'system_descriptions': True,      # Describing system behavior
                'error_messages': True           # System-generated messages
            }
        }
        
        # Context-aware detection patterns
        self.context_detection_patterns = {
            'document_styles': {
                'instructional': ['instruction', 'procedure', 'step', 'guide', 'tutorial'],
                'conversational': ['help', 'how-to', 'getting started', 'walkthrough'],
                'technical': ['specification', 'reference', 'api', 'documentation']
            },
            'engagement_indicators': {
                'direct_address': ['you', 'your', 'yourself'],
                'imperative_verbs': ['click', 'select', 'enter', 'choose', 'type', 'press'],
                'user_actions': ['action', 'task', 'operation', 'process']
            }
        }

    def _get_rule_type(self) -> str:
        return 'second_person'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for person violations using comprehensive
        morphological and syntactic analysis with linguistic anchors.
        """
        errors = []
        if not nlp:
            return errors

        # Build document context for person analysis
        doc_context = self._build_person_context(text, nlp)

        for i, sentence in enumerate(sentences):
            sent_doc = self._analyze_sentence_structure(sentence, nlp)
            if not sent_doc:
                continue
            
            # LINGUISTIC ANCHOR 1: First-person pronoun detection
            first_person_errors = self._analyze_first_person_patterns(sent_doc, sentence, i, doc_context)
            errors.extend(first_person_errors)
            
            # LINGUISTIC ANCHOR 2: Third-person substitute detection
            substitute_errors = self._analyze_third_person_substitutes(sent_doc, sentence, i, doc_context)
            errors.extend(substitute_errors)

        return errors

    def _build_person_context(self, text: str, nlp) -> Dict[str, Any]:
        """Build comprehensive context for person analysis."""
        context = {
            'document_style': 'instructional',  # Default
            'engagement_level': 'high',
            'direct_address_present': False,
            'compound_noun_density': 0.0,
            'technical_content': False
        }
        
        try:
            doc = self._analyze_sentence_structure(text, nlp)
            if doc:
                # Determine document style
                context['document_style'] = self._determine_document_style(doc)
                
                # Check for existing direct address
                context['direct_address_present'] = self._has_direct_address(doc)
                
                # Calculate compound noun density
                context['compound_noun_density'] = self._calculate_compound_density(doc)
                
                # Determine if content is technical
                context['technical_content'] = self._is_technical_content(doc)
                
        except Exception:
            pass
        
        return context

    def _analyze_first_person_patterns(self, doc, sentence: str, sentence_index: int, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect first-person pronouns using morphological analysis."""
        errors = []
        
        for sent in doc.sents:
            for token in sent:
                # Check for first-person pronouns using morphological analysis
                if self._is_first_person_pronoun(token):
                    # Apply contextual exceptions
                    if self._is_acceptable_first_person_context(token, sent, context):
                        continue
                    
                    # Generate context-appropriate suggestions
                    suggestions = self._generate_first_person_suggestions(token, context)
                    
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message=f"Avoid first-person pronoun '{token.text}'; use second person instead",
                        suggestions=suggestions,
                        severity='high',
                        flagged_text=token.text,
                        span=(token.idx, token.idx + len(token.text))
                    ))
        
        return errors

    def _analyze_third_person_substitutes(self, doc, sentence: str, sentence_index: int, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect third-person substitutes using morphological analysis."""
        errors = []
        
        for sent in doc.sents:
            for token in sent:
                # Check for user substitutes
                if self._is_user_substitute(token):
                    # Check if it's part of a compound noun (technical term)
                    if self._is_compound_noun_context(token, sent):
                        continue
                    
                    # Check if it's in an acceptable context
                    if self._is_acceptable_substitute_context(token, sent, context):
                        continue
                    
                    # Generate context-appropriate suggestions
                    suggestions = self._generate_substitute_suggestions(token, context)
                    
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=sentence_index,
                        message=f"Consider using 'you' instead of '{token.text}' for direct user engagement",
                        suggestions=suggestions,
                        severity='medium',
                        flagged_text=token.text,
                        span=(token.idx, token.idx + len(token.text))
                    ))
        
        return errors

    def _is_first_person_pronoun(self, token) -> bool:
        """Check if token is a first-person pronoun using morphological analysis."""
        # Check lemma against first-person pronouns
        lemma_lower = token.lemma_.lower()
        text_lower = token.text.lower()
        
        # Primary check: lemma in first-person pronouns
        all_first_person = (self.first_person_patterns['pronoun_indicators']['subject_pronouns'] |
                           self.first_person_patterns['pronoun_indicators']['object_pronouns'] |
                           self.first_person_patterns['pronoun_indicators']['possessive_pronouns'])
        
        return (lemma_lower in all_first_person or text_lower in all_first_person)

    def _is_user_substitute(self, token) -> bool:
        """Check if token is a user substitute using morphological analysis."""
        lemma_lower = token.lemma_.lower()
        
        all_substitutes = (self.third_person_substitute_patterns['user_substitutes']['generic_users'] |
                          self.third_person_substitute_patterns['user_substitutes']['role_substitutes'] |
                          self.third_person_substitute_patterns['user_substitutes']['system_agents'])
        
        return lemma_lower in all_substitutes

    def _is_acceptable_first_person_context(self, token, sent, context: Dict[str, Any]) -> bool:
        """Determine if first-person pronoun is acceptable in this context."""
        # Check if it's part of a proper name
        if token.lemma_.lower() == 'our' and token.head.pos_ == 'PROPN':
            return True
        
        # Check if it's in a quotation context
        if self._is_in_quotation(token, sent):
            return True
        
        # Check if it's part of a brand/company name
        if self._is_brand_name_context(token, sent):
            return True
        
        return False

    def _is_compound_noun_context(self, token, sent) -> bool:
        """Check if token is part of a compound noun using dependency analysis."""
        # Check if next token is a compound follower
        if token.i + 1 < len(sent):
            next_token = sent[token.i + 1]
            if next_token.lemma_.lower() in self.third_person_substitute_patterns['compound_exceptions']['compound_followers']:
                return True
        
        # Check dependency relationships for compound nouns
        if token.dep_ in ['compound', 'nmod']:
            return True
        
        # Check if part of a multi-word technical term
        return self._is_technical_compound(token, sent)

    def _is_acceptable_substitute_context(self, token, sent, context: Dict[str, Any]) -> bool:
        """Determine if user substitute is acceptable in this context."""
        # More acceptable in technical documentation
        if context.get('technical_content', False):
            return True
        
        # Acceptable in system descriptions vs user instructions
        if context.get('document_style') == 'technical':
            return True
        
        return False

    def _is_in_quotation(self, token, sent) -> bool:
        """Check if token is within quotation marks."""
        # Check if token is actually positioned between quotes
        sent_text = sent.text
        
        # If no quotes in sentence, definitely not in quotation
        if '"' not in sent_text and "'" not in sent_text:
            return False
        
        # Get token's position in the sentence text
        token_start = token.idx - sent.start_char
        token_end = token_start + len(token.text)
        
        # Check if token is between quote pairs
        quote_chars = ['"', "'"]
        for quote_char in quote_chars:
            quote_positions = [i for i, c in enumerate(sent_text) if c == quote_char]
            
            # Need at least 2 quotes to form a pair
            if len(quote_positions) >= 2:
                # Check each quote pair
                for i in range(0, len(quote_positions) - 1, 2):
                    start_quote = quote_positions[i]
                    end_quote = quote_positions[i + 1]
                    
                    # Check if token is between this quote pair
                    if start_quote < token_start and token_end < end_quote:
                        return True
        
        return False

    def _is_brand_name_context(self, token, sent) -> bool:
        """Check if token is part of a brand or company name."""
        # Look for capitalization patterns and proper nouns nearby
        if token.head.pos_ == 'PROPN':
            return True
        
        # Check if surrounded by capitalized words
        nearby_caps = 0
        for nearby_token in sent[max(0, token.i-2):min(len(sent), token.i+3)]:
            if nearby_token.is_title and nearby_token != token:
                nearby_caps += 1
        
        return nearby_caps >= 2

    def _is_technical_compound(self, token, sent) -> bool:
        """Check if token is part of a technical compound noun."""
        # Look for technical compound patterns in the sentence
        for compound_phrase in self.third_person_substitute_patterns['compound_exceptions']['technical_compounds']:
            if compound_phrase in sent.text.lower():
                return True
        return False

    def _determine_document_style(self, doc) -> str:
        """Determine document style based on linguistic markers."""
        instructional_count = sum(1 for token in doc 
                                if token.lemma_ in self.context_detection_patterns['document_styles']['instructional'])
        conversational_count = sum(1 for token in doc 
                                 if token.lemma_ in self.context_detection_patterns['document_styles']['conversational'])
        technical_count = sum(1 for token in doc 
                            if token.lemma_ in self.context_detection_patterns['document_styles']['technical'])
        
        if instructional_count > max(conversational_count, technical_count):
            return 'instructional'
        elif conversational_count > technical_count:
            return 'conversational'
        else:
            return 'technical'

    def _has_direct_address(self, doc) -> bool:
        """Check if document already uses direct address (you/your)."""
        return any(token.lemma_.lower() in self.context_detection_patterns['engagement_indicators']['direct_address'] 
                  for token in doc)

    def _calculate_compound_density(self, doc) -> float:
        """Calculate density of compound noun constructions."""
        if not doc:
            return 0.0
        
        compound_count = sum(1 for token in doc if token.dep_ in ['compound', 'nmod'])
        return compound_count / len(doc) if len(doc) > 0 else 0.0

    def _is_technical_content(self, doc) -> bool:
        """Determine if content is technical based on vocabulary."""
        technical_terms = sum(1 for token in doc 
                            if token.lemma_ in self.context_detection_patterns['document_styles']['technical'])
        return technical_terms / len(doc) > 0.05 if len(doc) > 0 else False

    def _generate_first_person_suggestions(self, token, context: Dict[str, Any]) -> List[str]:
        """Generate context-appropriate suggestions for first-person violations."""
        suggestions = ["Rewrite using second person ('you') to directly address the user"]
        
        if context.get('document_style') == 'instructional':
            suggestions.extend([
                "Use imperative mood for instructions",
                f"Example: Replace '{token.text}' with 'you' or remove the pronoun"
            ])
        else:
            suggestions.append("Focus on user actions rather than author perspective")
        
        return suggestions

    def _generate_substitute_suggestions(self, token, context: Dict[str, Any]) -> List[str]:
        """Generate context-appropriate suggestions for substitute violations."""
        suggestions = [f"Replace '{token.text}' with 'you' for direct engagement"]
        
        if context.get('document_style') == 'instructional':
            suggestions.extend([
                "Use direct address to make instructions clearer",
                "Example: 'You can click...' instead of 'The user can click...'"
            ])
        else:
            suggestions.append("Consider if direct address would improve clarity")
        
        return suggestions

    def _get_sentence_index(self, doc, sent) -> int:
        """Helper method to get sentence index within document."""
        for i, doc_sent in enumerate(doc.sents):
            if sent == doc_sent:
                return i
        return 0
