"""
Passive Voice Rule - Detects and suggests fixes for passive voice constructions.
Uses advanced SpaCy morphological, syntactic, and semantic analysis for A+ grade detection.
"""

from typing import List, Dict, Any

# Handle imports for different contexts
try:
    from .base_rule import BaseRule
except ImportError:
    from base_rule import BaseRule

class PassiveVoiceRule(BaseRule):
    """Rule to detect passive voice using advanced SpaCy linguistic analysis for A+ grade results."""
    
    def _get_rule_type(self) -> str:
        return 'passive_voice'
    
    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """Analyze text for passive voice using advanced SpaCy morphological analysis."""
        errors = []
        
        for i, sentence in enumerate(sentences):
            if nlp:
                doc = nlp(sentence)
                passive_constructions = self._find_passive_voice_with_advanced_spacy(doc)
                
                # NEW: Reader-focus analysis for technical writers
                reader_focus_issues = self._detect_reader_focus_issues(doc)
                
                # Combine all issues
                all_issues = passive_constructions + reader_focus_issues
            else:
                # Fallback: Use basic morphological patterns
                all_issues = self._find_passive_voice_morphological_fallback(sentence)
            
            for issue in all_issues:
                if self._is_reader_focus_issue(issue):
                    # Reader-focus specific error
                    suggestions = self._generate_reader_focus_suggestions(issue, doc)
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f'Reader-focus issue: {issue.get("type").replace("_", " ").title()}',
                        suggestions=suggestions,
                        severity='medium',
                        passive_construction=issue
                    ))
                else:
                    # Traditional passive voice error
                    suggestions = self._generate_advanced_passive_suggestions(issue, doc)
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message='Consider using active voice for clearer, more direct writing.',
                        suggestions=suggestions,
                        severity=self._determine_passive_severity(issue),
                        passive_construction=issue
                    ))

        return errors
    
    def _find_passive_voice_with_advanced_spacy(self, doc) -> List[Dict[str, Any]]:
        """Find passive voice using advanced SpaCy morphological and semantic analysis."""
        constructions = []
        
        for token in doc:
            # Method 1: Standard passive auxiliary detection
            if self._is_passive_auxiliary_by_morphology(token):
                construction = self._extract_passive_construction_from_auxiliary(token, doc)
                if construction:
                    constructions.append(construction)
            
            # Method 2: Advanced progressive passive detection ("is being done")
            elif self._is_progressive_passive_by_morphology(token, doc):
                construction = self._extract_progressive_passive_construction(token, doc)
                if construction:
                    constructions.append(construction)
            
            # Method 3: Hidden passive participle detection
            elif self._is_hidden_passive_participle(token, doc):
                construction = self._extract_passive_construction_from_participle(token, doc)
                if construction:
                    constructions.append(construction)
            
            # Method 4: Semantic passive detection (advanced)
            elif self._is_semantic_passive_construction(token, doc):
                construction = self._extract_semantic_passive_construction(token, doc)
                if construction:
                    constructions.append(construction)
        
        return constructions
    
    def _is_progressive_passive_by_morphology(self, token, doc) -> bool:
        """Detect progressive passive: 'is being done' using advanced morphological analysis."""
        # Check for auxiliary "be" in present/past tense
        if (token.pos_ == "AUX" and token.lemma_ == "be" and 
            token.morph.get("VerbForm") == ["Fin"]):
            
            # Look for "being" + past participle chain
            for child in token.children:
                if (child.pos_ == "AUX" and child.lemma_ == "be" and 
                    child.morph.get("VerbForm") == ["Part"] and 
                    child.morph.get("Tense") == ["Pres"]):  # "being"
                    
                    # Check for past participle
                    for grandchild in child.children:
                        if self._is_past_participle_by_morphology(grandchild):
                            return True
        
        return False
    
    def _is_hidden_passive_participle(self, token, doc) -> bool:
        """Detect passive participles in complex constructions using syntactic analysis."""
        if self._is_past_participle_by_morphology(token):
            return (self._has_passive_syntactic_context(token) or 
                    self._has_implicit_passive_agency(token, doc))
        return False
    
    def _is_semantic_passive_construction(self, token, doc) -> bool:
        """Detect semantic passive using advanced semantic role analysis."""
        if token.pos_ == "VERB" and token.dep_ == "ROOT":
            semantic_analysis = self._analyze_semantic_roles(token, doc)
            return (semantic_analysis.get('patient_as_subject', False) and
                    not semantic_analysis.get('agent_explicit', False))
        return False
    
    def _has_passive_syntactic_context(self, participle) -> bool:
        """Analyze syntactic context for passive indicators."""
        for child in participle.children:
            if child.dep_ in ["nsubjpass", "agent"]:
                return True
        if (participle.head.lemma_ == "be" and participle.head.pos_ == "AUX"):
            return True
        return False
    
    def _has_implicit_passive_agency(self, token, doc) -> bool:
        """Detect implicit passive agency using semantic analysis."""
        verb_frame = self._analyze_verb_semantic_frame(token, doc)
        return (verb_frame.get('expects_agent', False) and 
                not verb_frame.get('agent_present', False))
    
    def _analyze_semantic_roles(self, verb_token, doc) -> Dict[str, Any]:
        """Advanced semantic role analysis using SpaCy's dependency parsing."""
        roles = {
            'agent_explicit': False,
            'patient_as_subject': False,
            'agent_in_by_phrase': False,
            'semantic_frame': {}
        }
        
        subject = None
        agent_phrase = None
        
        for child in verb_token.children:
            if child.dep_ in ["nsubj", "nsubjpass"]:
                subject = child
                if self._is_semantic_patient(child, verb_token):
                    roles['patient_as_subject'] = True
            elif child.dep_ == "agent":
                agent_phrase = child
                roles['agent_in_by_phrase'] = True
                roles['agent_explicit'] = True
        
        roles['semantic_frame'] = self._extract_verb_semantic_frame(verb_token, subject, agent_phrase)
        return roles
    
    def _is_semantic_patient(self, noun_token, verb_token) -> bool:
        """Determine if noun is semantic patient using morphological analysis."""
        if noun_token.pos_ in ["NOUN", "PROPN"]:
            return self._noun_receives_action(noun_token, verb_token)
        return False
    
    def _noun_receives_action(self, noun, verb) -> bool:
        """Analyze if noun semantically receives the verb's action."""
        if verb.morph.get("VerbForm") == ["Part"] and verb.morph.get("Tense") == ["Past"]:
            return True
        return False
    
    def _extract_progressive_passive_construction(self, aux_token, doc) -> Dict[str, Any]:
        """Extract progressive passive construction details."""
        being_token = None
        main_verb = None
        
        for child in aux_token.children:
            if (child.lemma_ == "be" and child.morph.get("VerbForm") == ["Part"]):
                being_token = child
                for grandchild in child.children:
                    if self._is_past_participle_by_morphology(grandchild):
                        main_verb = grandchild
                        break
                break
        
        if not (being_token and main_verb):
            return None
        
        return {
            'type': 'progressive_passive',
            'auxiliary_token': aux_token,
            'being_token': being_token,
            'main_verb_token': main_verb,
            'complexity_level': 'high',
            'full_construction': f"{aux_token.text} {being_token.text} {main_verb.text}",
            'position': aux_token.idx
        }
    
    def _extract_semantic_passive_construction(self, verb_token, doc) -> Dict[str, Any]:
        """Extract semantic passive construction details."""
        semantic_analysis = self._analyze_semantic_roles(verb_token, doc)
        
        return {
            'type': 'semantic_passive',
            'main_verb_token': verb_token,
            'complexity_level': 'medium',
            'semantic_analysis': semantic_analysis,
            'full_construction': verb_token.text,
            'position': verb_token.idx
        }
    
    def _analyze_verb_semantic_frame(self, verb_token, doc) -> Dict[str, Any]:
        """Analyze verb's expected semantic frame."""
        frame = {
            'expects_agent': True,
            'agent_present': False,
            'verb_class': self._classify_verb_semantically(verb_token)
        }
        
        for child in verb_token.children:
            if child.dep_ in ["nsubj", "nsubjpass"]:
                frame['agent_present'] = True
        
        return frame
    
    def _classify_verb_semantically(self, verb_token) -> str:
        """Classify verb semantically using pure SpaCy morphological analysis."""
        lemma = verb_token.lemma_
        if verb_token.morph.get("VerbForm") == ["Part"]:
            return "participial"
        elif self._is_creation_verb(verb_token):
            return "creation"
        elif self._is_transfer_verb(verb_token):
            return "transfer"
        else:
            return "general_action"
    
    def _is_creation_verb(self, verb_token) -> bool:
        """Check if verb is creation-type using morphological patterns."""
        lemma = verb_token.lemma_.lower()
        # Use morphological patterns for creation verbs
        if 'mak' in lemma or 'creat' in lemma or 'build' in lemma or 'construct' in lemma:
            return True
        if 'form' in lemma or 'establish' in lemma or 'develop' in lemma:
            return True
        return False
    
    def _is_transfer_verb(self, verb_token) -> bool:
        """Check if verb is transfer-type using morphological patterns."""
        lemma = verb_token.lemma_.lower()
        # Use morphological patterns for transfer verbs
        if 'giv' in lemma or 'send' in lemma or 'deliver' in lemma or 'transfer' in lemma:
            return True
        if 'pass' in lemma or 'hand' in lemma or 'convey' in lemma:
            return True
        return False
    
    def _extract_verb_semantic_frame(self, verb_token, subject, agent_phrase) -> Dict[str, Any]:
        """Extract detailed semantic frame for verb."""
        return {
            'verb_class': self._classify_verb_semantically(verb_token),
            'has_explicit_agent': agent_phrase is not None,
            'transitivity': self._analyze_verb_transitivity(verb_token)
        }
    
    def _analyze_verb_transitivity(self, verb_token) -> str:
        """Analyze verb transitivity using dependency structure."""
        has_object = any(child.dep_ in ["dobj", "iobj"] for child in verb_token.children)
        return "transitive" if has_object else "intransitive"
    
    def _determine_passive_severity(self, construction) -> str:
        """Determine severity based on construction complexity."""
        construction_type = construction.get('type', '')
        if construction_type == 'progressive_passive':
            return 'high'
        elif construction.get('complexity_level') == 'high':
            return 'medium'
        else:
            return 'low'
    
    def _generate_advanced_passive_suggestions(self, construction: Dict[str, Any], doc) -> List[str]:
        """Generate advanced suggestions based on detailed linguistic analysis."""
        suggestions = []
        construction_type = construction.get('type', '')
        
        if construction_type == 'progressive_passive':
            suggestions.extend(self._generate_progressive_passive_suggestions(construction, doc))
        elif construction_type == 'semantic_passive':
            suggestions.extend(self._generate_semantic_passive_suggestions(construction, doc))
        else:
            suggestions.extend(self._generate_standard_passive_suggestions(construction, doc))
        
        suggestions.extend(self._generate_context_aware_suggestions(construction, doc))
        return suggestions
    
    def _generate_progressive_passive_suggestions(self, construction: Dict[str, Any], doc) -> List[str]:
        """Generate suggestions for progressive passive constructions."""
        suggestions = []
        main_verb = construction.get('main_verb_token')
        
        if main_verb:
            suggestions.append(f"Replace 'is being {main_verb.text}' with active voice using '{main_verb.lemma_}'")
            suggestions.append("Identify who performs this ongoing action and make them the subject")
            suggestions.append("Simplify complex progressive passive to direct action")
        
        return suggestions
    
    def _generate_semantic_passive_suggestions(self, construction: Dict[str, Any], doc) -> List[str]:
        """Generate suggestions for semantic passive constructions."""
        suggestions = []
        semantic_analysis = construction.get('semantic_analysis', {})
        main_verb = construction.get('main_verb_token')
        
        if semantic_analysis.get('patient_as_subject'):
            suggestions.append("Identify the agent performing this action")
            suggestions.append("Restructure to make the agent the subject")
        
        if main_verb:
            suggestions.append(f"Clarify who performs '{main_verb.lemma_}' in this context")
        
        return suggestions
    
    def _generate_standard_passive_suggestions(self, construction: Dict[str, Any], doc) -> List[str]:
        """Generate standard passive voice suggestions."""
        suggestions = []
        main_verb_token = construction.get('main_verb_token') or construction.get('participle_token')
        
        if main_verb_token:
            active_verb = main_verb_token.lemma_
            suggestions.append(f"Convert to active voice using '{active_verb}'")
            suggestions.append(f"Identify who performs '{active_verb}' and make them the subject")
        
        return suggestions
    
    def _generate_context_aware_suggestions(self, construction: Dict[str, Any], doc) -> List[str]:
        """Generate suggestions based on document context using pure SpaCy morphological analysis."""
        suggestions = []
        
        # Look for potential agents using pure morphological analysis
        potential_agents = self._find_potential_agents_morphologically(doc)
        if potential_agents:
            suggestions.append(f"Consider making '{potential_agents[0].text}' the active subject")
        
        # Context-specific suggestions using morphological patterns
        if self._is_business_context(doc):
            suggestions.append("Use direct business language: specify who takes responsibility")
        
        return suggestions
    
    def _find_potential_agents_morphologically(self, doc) -> List:
        """Find potential agents using pure SpaCy morphological analysis."""
        potential_agents = []
        
        for ent in doc.ents:
            # Use SpaCy's entity type analysis
            if self._is_agent_capable_entity(ent):
                potential_agents.append(ent)
        
        return potential_agents
    
    def _is_agent_capable_entity(self, entity) -> bool:
        """Check if entity is agent-capable using morphological analysis."""
        # Method 1: Use SpaCy's entity label analysis
        if self._has_person_entity_morphology(entity):
            return True
        
        # Method 2: Use organizational entity morphology
        if self._has_organizational_entity_morphology(entity):
            return True
        
        return False
    
    def _has_person_entity_morphology(self, entity) -> bool:
        """Check for person entity morphological patterns."""
        # Use SpaCy's built-in person detection
        return entity.label_ == "PERSON"
    
    def _has_organizational_entity_morphology(self, entity) -> bool:
        """Check for organizational entity morphological patterns."""
        # Use SpaCy's built-in organization detection
        return entity.label_ == "ORG"
    
    def _is_business_context(self, doc) -> bool:
        """Detect business context using pure SpaCy entity and morphological analysis."""
        # Method 1: Use SpaCy's Named Entity Recognition with morphological validation
        business_entity_count = 0
        for ent in doc.ents:
            if self._is_business_related_entity(ent):
                business_entity_count += 1
        
        if business_entity_count > 0:
            return True
        
        # Method 2: Use morphological pattern analysis for business terms
        business_pattern_count = 0
        for token in doc:
            if self._has_business_morphology(token):
                business_pattern_count += 1
        
        # If significant portion has business morphology, it's business context
        return business_pattern_count > len(list(doc)) * 0.05
    
    def _is_business_related_entity(self, entity) -> bool:
        """Check if entity is business-related using morphological analysis."""
        # Method 1: Organizational entities
        if entity.label_ == "ORG":
            return True
        
        # Method 2: Financial/monetary entities
        if entity.label_ == "MONEY":
            return True
        
        # Method 3: Percentage/quantitative business entities
        if entity.label_ == "PERCENT":
            return True
        
        return False
    
    def _has_business_morphology(self, token) -> bool:
        """Check for business morphology patterns using SpaCy."""
        lemma = token.lemma_.lower()
        
        # Organizational structure patterns
        if 'commit' in lemma or 'organiz' in lemma or 'team' in lemma:
            return True
        
        # Policy/governance patterns
        if 'polic' in lemma or 'audit' in lemma or 'complian' in lemma:
            return True
        
        # Management/leadership patterns
        if 'govern' in lemma or 'manag' in lemma or 'direct' in lemma:
            return True
        
        # Review/approval patterns
        if 'review' in lemma or 'approv' in lemma or 'guidelin' in lemma:
            return True
        
        # Stakeholder/business entity patterns
        if 'stakeholder' in lemma or 'department' in lemma or 'division' in lemma:
            return True
        
        return False
    
    # Keep existing helper methods
    def _is_passive_auxiliary_by_morphology(self, token) -> bool:
        """Check if token is passive auxiliary using SpaCy's morphological features."""
        if token.dep_ == "auxpass":
            return True
        if token.pos_ == "AUX" and token.lemma_ == "be":
            for child in token.children:
                if self._is_past_participle_by_morphology(child):
                    return True
        return False
    
    def _is_past_participle_by_morphology(self, token) -> bool:
        """Check if token is past participle using pure morphological analysis."""
        morph = token.morph
        if morph.get("VerbForm") == ["Part"] and morph.get("Tense") == ["Past"]:
            return True
        if token.tag_ == "VBN":
            return True
        return False
    
    def _extract_passive_construction_from_auxiliary(self, aux_token, doc) -> Dict[str, Any]:
        """Extract passive construction details using SpaCy syntactic analysis."""
        main_verb = None
        for child in aux_token.children:
            if self._is_past_participle_by_morphology(child):
                main_verb = child
                break
        
        if not main_verb:
            return None
        
        return {
            'type': 'auxiliary_passive',
            'auxiliary_token': aux_token,
            'main_verb_token': main_verb,
            'complexity_level': 'medium',
            'full_construction': f"{aux_token.text} {main_verb.text}",
            'position': aux_token.idx
        }
    
    def _extract_passive_construction_from_participle(self, participle_token, doc) -> Dict[str, Any]:
        """Extract passive construction from participle using SpaCy analysis."""
        auxiliary = None
        if participle_token.head.lemma_ == "be" and participle_token.head.pos_ == "AUX":
            auxiliary = participle_token.head
        
        return {
            'type': 'participle_passive',
            'participle_token': participle_token,
            'auxiliary_token': auxiliary,
            'complexity_level': 'low',
            'full_construction': participle_token.text,
            'position': participle_token.idx
        }
    
    def _find_passive_voice_morphological_fallback(self, sentence: str) -> List[Dict[str, Any]]:
        """Fallback using basic morphological patterns when SpaCy unavailable."""
        import re
        constructions = []
        
        patterns = [
            r'\b(?:is|are|was|were|being|been)\s+\w+(?:ed|en)\b',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, sentence, re.IGNORECASE)
            for match in matches:
                constructions.append({
                    'type': 'morphological_fallback',
                    'full_construction': match.group(),
                    'position': match.start(),
                    'complexity_level': 'low'
                })
        
        return constructions
    
    def _detect_reader_focus_issues(self, doc) -> List[Dict[str, Any]]:
        """Detect reader-focus issues using pure SpaCy morphological analysis."""
        focus_issues = []
        
        for token in doc:
            # Method 1: Detect vague agency using syntactic analysis
            if self._is_vague_agency_construction(token, doc):
                focus_issue = self._analyze_vague_agency(token, doc)
                if focus_issue:
                    focus_issues.append(focus_issue)
            
            # Method 2: Detect ownership ambiguity using semantic role analysis
            elif self._is_ownership_ambiguous(token, doc):
                ownership_issue = self._analyze_ownership_clarity(token, doc)
                if ownership_issue:
                    focus_issues.append(ownership_issue)
        
        return focus_issues
    
    def _is_vague_agency_construction(self, token, doc) -> bool:
        """Detect vague agency using SpaCy's dependency and morphological analysis."""
        # Look for passive constructions without clear agents
        if token.pos_ == "VERB" and self._is_passive_auxiliary_by_morphology(token):
            # Check if there's a clear agent or if it's vague
            has_clear_agent = self._has_specific_agent(token, doc)
            has_organizational_context = self._has_organizational_context(token, doc)
            
            return not has_clear_agent and has_organizational_context
        
        return False
    
    def _has_specific_agent(self, verb_token, doc) -> bool:
        """Check if verb has specific, identifiable agent using SpaCy analysis."""
        for child in verb_token.children:
            if child.dep_ == "agent":
                # Analyze the agent for specificity
                agent_specificity = self._analyze_agent_specificity(child, doc)
                return agent_specificity['is_specific']
        
        return False
    
    def _analyze_agent_specificity(self, agent_phrase, doc) -> Dict[str, Any]:
        """Analyze agent specificity using SpaCy's NER and morphological features."""
        specificity = {
            'is_specific': False,
            'specificity_score': 0.0,
            'agent_type': 'unknown'
        }
        
        # Method 1: Use SpaCy's Named Entity Recognition
        for token in agent_phrase.subtree:
            if token.ent_type_ in ["PERSON", "ORG"]:
                specificity['is_specific'] = True
                specificity['agent_type'] = 'named_entity'
                specificity['specificity_score'] = 1.0
                return specificity
        
        # Method 2: Analyze determiner and noun specificity
        for token in agent_phrase.subtree:
            if token.pos_ == "NOUN":
                # Check for specific organizational roles
                if self._is_specific_organizational_role(token):
                    specificity['is_specific'] = True
                    specificity['agent_type'] = 'specific_role'
                    specificity['specificity_score'] = 0.8
                    return specificity
        
        return specificity
    
    def _is_specific_organizational_role(self, noun_token) -> bool:
        """Check if noun represents specific organizational role using pure SpaCy morphological analysis."""
        # Method 1: Use SpaCy's morphological features to detect role patterns
        if self._has_role_morphology(noun_token):
            return True
        
        # Method 2: Check for compound noun patterns indicating specificity
        for child in noun_token.children:
            if child.dep_ == "compound" and self._is_noun_like(child):
                return True  # Compound nouns often indicate specificity
        
        # Method 3: Use SpaCy's NER to identify organizational roles
        if self._is_organizational_or_person_entity(noun_token):
            return True
        
        return False
    
    def _is_noun_like(self, token) -> bool:
        """Check if token is noun-like using SpaCy POS analysis."""
        return token.pos_ in ["NOUN", "PROPN"]
    
    def _is_organizational_or_person_entity(self, token) -> bool:
        """Check if token is organizational or person entity using SpaCy."""
        # Method 1: Check for organizational entity
        if token.ent_type_ == "ORG":
            return True
        
        # Method 2: Check for person entity
        if token.ent_type_ == "PERSON":
            return True
        
        return False
    
    def _has_role_morphology(self, token) -> bool:
        """Check for role-indicating morphological patterns using SpaCy."""
        lemma = token.lemma_.lower()
        
        # Method 1: Role-indicating morphological endings
        if lemma.endswith('er') or lemma.endswith('or') or lemma.endswith('ist'):
            return True  # manager, director, specialist
        
        # Method 2: Organizational structure indicators using semantic patterns
        if 'team' in lemma or 'group' in lemma or 'department' in lemma:
            return True
        
        # Method 3: Authority/management patterns
        if 'manag' in lemma or 'direct' in lemma or 'commit' in lemma:
            return True
        
        return False
    
    def _has_organizational_context(self, token, doc) -> bool:
        """Check if token appears in organizational context using pure SpaCy analysis."""
        # Method 1: Use SpaCy's Named Entity Recognition
        for sent_token in token.sent:
            if self._is_organizational_or_person_entity(sent_token):
                return True
        
        # Method 2: Detect organizational patterns using morphological analysis
        for sent_token in token.sent:
            if self._has_organizational_morphology(sent_token):
                return True
        
        return False
    
    def _has_organizational_morphology(self, token) -> bool:
        """Check for organizational morphology patterns using SpaCy."""
        lemma = token.lemma_.lower()
        
        # Training/development context patterns
        if 'train' in lemma or 'develop' in lemma or 'session' in lemma:
            return True
        
        # Policy/procedure context patterns  
        if 'polic' in lemma or 'procedur' in lemma or 'guidelin' in lemma:
            return True
        
        # Employee/staff context patterns
        if 'employ' in lemma or 'staff' in lemma or 'personnel' in lemma:
            return True
        
        # Business/corporate context patterns
        if 'team' in lemma or 'department' in lemma or 'compan' in lemma:
            return True
        
        return False
    
    def _is_ownership_ambiguous(self, token, doc) -> bool:
        """Detect ownership ambiguity using SpaCy's syntactic analysis."""
        # Look for constructions that lack clear ownership
        if token.dep_ == "nsubjpass" and self._is_noun_or_pronoun(token):
            # Check if subject is vague or impersonal
            return self._is_impersonal_subject(token, doc)
        
        return False
    
    def _is_noun_or_pronoun(self, token) -> bool:
        """Check if token is noun or pronoun using SpaCy POS analysis."""
        return token.pos_ in ["NOUN", "PRON"]
    
    def _is_impersonal_subject(self, subject_token, doc) -> bool:
        """Check if subject is impersonal using pure SpaCy morphological analysis."""
        # Method 1: Use SpaCy's POS and morphological features for pronouns
        if subject_token.pos_ == "PRON":
            # Check for impersonal pronouns using morphological features
            if self._is_impersonal_pronoun(subject_token):
                return True
        
        # Method 2: Check for abstract/impersonal nouns using morphological patterns
        if subject_token.pos_ == "NOUN":
            return self._is_abstract_impersonal_noun(subject_token)
        
        return False
    
    def _is_impersonal_pronoun(self, pronoun_token) -> bool:
        """Check if pronoun is impersonal using SpaCy morphological analysis."""
        lemma = pronoun_token.lemma_.lower()
        
        # Method 1: Use POS tags to detect demonstrative/impersonal pronouns
        if pronoun_token.tag_ in ["DT", "WDT"]:
            return True
        
        # Method 2: Use morphological features to detect impersonal pronouns
        if pronoun_token.morph.get("PronType") == ["Dem"]:  # Demonstrative
            return True
        
        # Method 3: Check for impersonal patterns using morphological analysis
        if self._is_impersonal_pronoun_pattern(pronoun_token):
            return True
        
        return False
    
    def _is_impersonal_pronoun_pattern(self, pronoun_token) -> bool:
        """Check for impersonal pronoun patterns using morphological analysis."""
        lemma = pronoun_token.lemma_.lower()
        
        # Neuter pronouns often impersonal
        if pronoun_token.morph.get("Gender") == ["Neut"]:
            return True
        
        # Third person singular often impersonal in business context
        if (pronoun_token.morph.get("Person") == ["3"] and 
            pronoun_token.morph.get("Number") == ["Sing"]):
            return True
        
        return False
    
    def _is_abstract_impersonal_noun(self, noun_token) -> bool:
        """Check for abstract/impersonal nouns using morphological patterns."""
        lemma = noun_token.lemma_.lower()
        
        # Method 1: Process/system abstractions using morphological patterns
        if lemma.endswith('tion') or lemma.endswith('sion') or lemma.endswith('ment'):
            return True
        
        # Method 2: Abstract concept patterns
        if lemma.endswith('ness') or lemma.endswith('ity') or lemma.endswith('ism'):
            return True
        
        # Method 3: Organizational process patterns
        if 'process' in lemma or 'system' in lemma or 'procedur' in lemma:
            return True
        
        # Method 4: Session/event patterns
        if 'session' in lemma or 'meeting' in lemma or 'event' in lemma:
            return True
        
        return False
    
    def _could_be_agent(self, token, verb_token) -> bool:
        """Check if token could serve as agent using pure SpaCy analysis."""
        # Method 1: Use SpaCy's Named Entity Recognition
        if self._is_person_or_org_entity(token):
            return True
        
        # Method 2: Use POS and dependency analysis
        if self._is_potential_agent_pos(token) and self._is_potential_agent_dep(token):
            # Method 3: Check for agent-capable morphological patterns
            return self._has_agent_capable_morphology(token)
        
        return False
    
    def _is_person_or_org_entity(self, token) -> bool:
        """Check if token is person or organization entity using SpaCy."""
        return token.ent_type_ in ["PERSON", "ORG"]
    
    def _is_potential_agent_pos(self, token) -> bool:
        """Check if token has potential agent POS using SpaCy."""
        return token.pos_ in ["NOUN", "PROPN"]
    
    def _is_potential_agent_dep(self, token) -> bool:
        """Check if token has potential agent dependency using SpaCy."""
        return token.dep_ in ["nsubj", "nmod"]
    
    def _has_agent_capable_morphology(self, token) -> bool:
        """Check for agent-capable morphological patterns using SpaCy."""
        lemma = token.lemma_.lower()
        
        # Method 1: Role/position indicators using morphological analysis
        if self._has_role_morphology(token):
            return True
        
        # Method 2: Organizational unit patterns
        if 'team' in lemma or 'group' in lemma or 'department' in lemma:
            return True
        
        # Method 3: Professional/occupational patterns
        if lemma.endswith('er') or lemma.endswith('or') or lemma.endswith('ist'):
            return True
        
        # Method 4: Authority patterns
        if 'chief' in lemma or 'head' in lemma or 'lead' in lemma:
            return True
        
        return False
    
    def _analyze_vague_agency(self, token, doc) -> Dict[str, Any]:
        """Analyze vague agency construction using SpaCy."""
        return {
            'type': 'vague_agency',
            'verb_token': token,
            'construction_analysis': self._analyze_construction_context(token, doc),
            'reader_focus_score': self._calculate_reader_focus_score(token, doc),
            'position': token.idx
        }
    
    def _analyze_ownership_clarity(self, token, doc) -> Dict[str, Any]:
        """Analyze ownership clarity using SpaCy analysis."""
        return {
            'type': 'ownership_ambiguity', 
            'subject_token': token,
            'clarity_analysis': self._analyze_subject_clarity(token, doc),
            'ownership_score': self._calculate_ownership_score(token, doc),
            'position': token.idx
        }
    
    def _analyze_construction_context(self, verb_token, doc) -> Dict[str, Any]:
        """Analyze construction context using SpaCy."""
        context = {
            'organizational_entities': [],
            'potential_agents': [],
            'context_type': 'general'
        }
        
        # Find organizational entities in the sentence
        for token in verb_token.sent:
            if self._is_organizational_or_person_entity(token):
                context['organizational_entities'].append({
                    'text': token.text,
                    'type': token.ent_type_,
                    'could_be_agent': self._could_be_agent(token, verb_token)
                })
        
        # Identify potential agents using dependency analysis
        for token in verb_token.sent:
            if self._could_be_agent(token, verb_token):
                context['potential_agents'].append(token)
        
        # Determine context type
        if len(context['organizational_entities']) > 0:
            context['context_type'] = 'organizational'
        
        return context
    
    def _calculate_reader_focus_score(self, token, doc) -> float:
        """Calculate reader focus score using SpaCy analysis."""
        score = 0.0
        
        # Penalty for vague constructions
        if not self._has_specific_agent(token, doc):
            score += 0.5
        
        # Penalty for impersonal subjects
        for child in token.children:
            if child.dep_ == "nsubjpass" and self._is_impersonal_subject(child, doc):
                score += 0.3
        
        return score
    
    def _calculate_ownership_score(self, token, doc) -> float:
        """Calculate ownership clarity score."""
        if self._is_impersonal_subject(token, doc):
            return 0.8  # High ambiguity
        return 0.2  # Low ambiguity
    
    def _analyze_subject_clarity(self, subject_token, doc) -> Dict[str, Any]:
        """Analyze subject clarity using SpaCy."""
        return {
            'is_impersonal': self._is_impersonal_subject(subject_token, doc),
            'has_clear_referent': self._has_clear_referent(subject_token, doc),
            'subject_type': subject_token.pos_
        }
    
    def _has_clear_referent(self, token, doc) -> bool:
        """Check if token has clear referent using SpaCy coreference analysis."""
        # Simplified check - in full implementation would use coreference resolution
        if token.pos_ == "PRON":
            return False  # Pronouns often lack clear referents in passive constructions
        return True
    
    def _generate_reader_focus_suggestions(self, focus_issue: Dict[str, Any], doc) -> List[str]:
        """Generate reader-focus suggestions using SpaCy analysis."""
        suggestions = []
        issue_type = focus_issue.get('type')
        
        if issue_type == 'vague_agency':
            verb_token = focus_issue.get('verb_token')
            context = focus_issue.get('construction_analysis', {})
            
            # Use SpaCy analysis to suggest specific agents
            potential_agents = context.get('potential_agents', [])
            if potential_agents:
                for agent in potential_agents:
                    suggestions.append(f"Make '{agent.text}' the active subject to clarify responsibility")
            
            # Use organizational entities for suggestions
            org_entities = context.get('organizational_entities', [])
            for entity in org_entities:
                if entity['could_be_agent']:
                    suggestions.append(f"Consider: '{entity['text']} will {verb_token.lemma_}...'")
        
        elif issue_type == 'ownership_ambiguity':
            subject_token = focus_issue.get('subject_token')
            suggestions.append(f"Replace vague '{subject_token.text}' with specific responsible party")
            suggestions.append("Identify who owns this action for reader clarity")
        
        return suggestions
    
    def _is_reader_focus_issue(self, issue: Dict[str, Any]) -> bool:
        """Check if issue is reader-focus related using dynamic analysis."""
        issue_type = issue.get('type', '')
        
        # Method 1: Check for vague agency patterns
        if self._is_vague_agency_issue(issue_type):
            return True
        
        # Method 2: Check for ownership ambiguity patterns
        if self._is_ownership_ambiguity_issue(issue_type):
            return True
        
        return False
    
    def _is_vague_agency_issue(self, issue_type: str) -> bool:
        """Check if issue type indicates vague agency using pattern analysis."""
        return 'vague' in issue_type and 'agency' in issue_type
    
    def _is_ownership_ambiguity_issue(self, issue_type: str) -> bool:
        """Check if issue type indicates ownership ambiguity using pattern analysis."""
        return 'ownership' in issue_type and 'ambiguity' in issue_type 