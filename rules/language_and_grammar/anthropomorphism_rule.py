"""
Anthropomorphism Rule
Based on IBM Style Guide topic: "Anthropomorphism"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class AnthropomorphismRule(BaseLanguageRule):
    """
    Checks for instances where inanimate objects or abstract concepts are
    given human characteristics, using dependency parsing to identify the
    grammatical subject of human-like verbs.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'anthropomorphism'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for anthropomorphism using evidence-based scoring.
        Uses sophisticated linguistic analysis to distinguish inappropriate anthropomorphism
        from acceptable technical metaphors and conventional usage patterns.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        
        for i, sent in enumerate(doc.sents):
            for token in sent:
                # Check for potential anthropomorphic patterns
                anthropomorphism_data = self._detect_potential_anthropomorphism(token, sent)
                
                if anthropomorphism_data:
                    # Calculate evidence score for this potential anthropomorphism
                    evidence_score = self._calculate_anthropomorphism_evidence(
                        token, anthropomorphism_data['subject'], sent, text, context
                    )
                    
                    # Only create error if evidence suggests inappropriate anthropomorphism
                    if evidence_score > 0.1:  # Low threshold - let enhanced validation decide
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=self._get_contextual_message(token, anthropomorphism_data['subject'], evidence_score),
                            suggestions=self._generate_smart_suggestions(token, anthropomorphism_data['subject'], evidence_score, context),
                            severity='low',
                            text=text,
                            context=context,
                            evidence_score=evidence_score,  # Your nuanced assessment
                            span=(anthropomorphism_data['subject'].idx, token.idx + len(token.text)),
                            flagged_text=f"{anthropomorphism_data['subject'].text} {token.text}"
                        ))
        return errors

    # === EVIDENCE-BASED CALCULATION METHODS ===

    def _detect_potential_anthropomorphism(self, token, sent):
        """
        Detect potential anthropomorphic patterns using flexible, context-aware analysis.
        
        Returns:
            dict or None: Contains 'subject' and 'verb' if pattern detected, None otherwise
        """
        # Check if this token could be an anthropomorphic verb
        if not self._could_be_anthropomorphic_verb(token):
            return None
            
        # Find the subject of this verb
        subject_tokens = [child for child in token.children if child.dep_ == 'nsubj']
        if not subject_tokens:
            return None
            
        subject = subject_tokens[0]
        
        # Check if subject could be inappropriately anthropomorphized
        if self._could_be_inappropriately_anthropomorphized(subject):
            return {
                'subject': subject,
                'verb': token
            }
        
        return None

    def _could_be_anthropomorphic_verb(self, token):
        """Check if token could be a verb that anthropomorphizes inanimate subjects."""
        
        # Core human cognitive/emotional verbs (most problematic)
        core_human_verbs = {
            'think', 'believe', 'feel', 'want', 'wish', 'hope', 'fear', 'love', 'hate',
            'worry', 'care', 'remember', 'forget', 'dream', 'imagine', 'doubt', 'know', 'learn'
        }
        
        # Human communication verbs (context-dependent)
        communication_verbs = {
            'say', 'tell', 'speak', 'talk', 'ask', 'answer', 'reply', 'explain',
            'describe', 'mention', 'suggest', 'recommend', 'advise'
        }
        
        # Human decision/judgment verbs (often acceptable in technical contexts)
        decision_verbs = {
            'decide', 'choose', 'select', 'prefer', 'judge', 'evaluate',
            'determine', 'conclude', 'assume', 'expect'
        }
        
        # Human perception verbs (context-dependent)
        perception_verbs = {
            'see', 'look', 'watch', 'observe', 'notice', 'detect',
            'hear', 'listen', 'smell', 'taste', 'touch'
        }
        
        # Human action verbs (often acceptable)
        action_verbs = {
            'allow', 'permit', 'let', 'enable', 'disable', 'prevent',
            'help', 'assist', 'support', 'protect', 'serve'
        }
        
        verb_lemma = token.lemma_.lower()
        
        # Return True if it's any kind of potentially anthropomorphic verb
        return (verb_lemma in core_human_verbs or 
                verb_lemma in communication_verbs or 
                verb_lemma in decision_verbs or 
                verb_lemma in perception_verbs or 
                verb_lemma in action_verbs)

    def _could_be_inappropriately_anthropomorphized(self, subject):
        """Check if subject could be inappropriately anthropomorphized."""
        
        # Technical system entities (context-dependent)
        technical_entities = {
            'system', 'application', 'program', 'software', 'app',
            'server', 'client', 'database', 'api', 'service',
            'module', 'component', 'library', 'framework',
            'algorithm', 'function', 'method', 'process'
        }
        
        # Hardware entities
        hardware_entities = {
            'computer', 'machine', 'device', 'processor', 'cpu',
            'memory', 'disk', 'drive', 'network', 'router'
        }
        
        # Interface entities
        interface_entities = {
            'interface', 'window', 'dialog', 'menu', 'button',
            'form', 'field', 'screen', 'display', 'panel'
        }
        
        # Document/content entities
        content_entities = {
            'document', 'file', 'page', 'section', 'chapter',
            'paragraph', 'text', 'content', 'data', 'information'
        }
        
        # Business/abstract entities
        business_entities = {
            'company', 'organization', 'team', 'department',
            'project', 'product', 'feature', 'tool', 'solution'
        }
        
        subject_lemma = subject.lemma_.lower()
        
        # Check if it's a potentially anthropomorphizable entity
        return (subject_lemma in technical_entities or
                subject_lemma in hardware_entities or
                subject_lemma in interface_entities or
                subject_lemma in content_entities or
                subject_lemma in business_entities)

    def _calculate_anthropomorphism_evidence(self, verb_token, subject_token, sentence, text: str, context: dict) -> float:
        """
        Calculate evidence score (0.0-1.0) for inappropriate anthropomorphism.
        
        Higher scores indicate stronger evidence of inappropriate anthropomorphism.
        Lower scores indicate acceptable usage or conventional technical metaphors.
        
        Args:
            verb_token: The anthropomorphic verb token
            subject_token: The subject being anthropomorphized
            sentence: Sentence containing the pattern
            text: Full document text
            context: Document context (block_type, content_type, etc.)
            
        Returns:
            float: Evidence score from 0.0 (acceptable) to 1.0 (inappropriate)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        # Start with base evidence based on verb type
        evidence_score = self._get_base_verb_evidence(verb_token)
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_anthropomorphism(evidence_score, verb_token, subject_token, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_anthropomorphism(evidence_score, verb_token, subject_token, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_anthropomorphism(evidence_score, verb_token, subject_token, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_anthropomorphism(evidence_score, verb_token, subject_token, context)
        
        return max(0.0, min(1.0, evidence_score))  # Clamp to valid range

    def _get_base_verb_evidence(self, verb_token) -> float:
        """Get base evidence score based on the type of verb."""
        verb_lemma = verb_token.lemma_.lower()
        
        # Core human cognitive/emotional verbs - highest evidence
        if verb_lemma in {'think', 'believe', 'feel', 'want', 'wish', 'hope', 'fear', 'love', 'hate', 'worry', 'care', 'know', 'learn'}:
            return 0.9  # Almost always inappropriate
        
        # Memory/consciousness verbs - high evidence
        elif verb_lemma in {'remember', 'forget', 'dream', 'imagine', 'doubt'}:
            return 0.8  # Usually inappropriate
        
        # Communication verbs - moderate evidence (context-dependent)
        elif verb_lemma in {'say', 'tell', 'speak', 'talk', 'ask', 'answer', 'reply'}:
            return 0.6  # Often inappropriate but has technical uses
        
        # Decision/judgment verbs - lower evidence (often acceptable in tech)
        elif verb_lemma in {'decide', 'choose', 'select', 'determine', 'expect'}:
            return 0.4  # Often acceptable in technical contexts
        
        # Perception verbs - moderate evidence (context-dependent)
        elif verb_lemma in {'see', 'detect', 'notice', 'hear', 'observe'}:
            return 0.5  # Mixed acceptability
        
        # Action/capability verbs - low evidence (usually acceptable)
        elif verb_lemma in {'allow', 'permit', 'enable', 'support', 'help', 'serve'}:
            return 0.3  # Usually acceptable in technical writing
        
        else:
            return 0.5  # Default moderate evidence

    # === LINGUISTIC CLUES (MICRO-LEVEL) ===

    def _apply_linguistic_clues_anthropomorphism(self, evidence_score: float, verb_token, subject_token, sentence) -> float:
        """Apply comprehensive SpaCy-based linguistic analysis clues for anthropomorphism."""
        
        # === VERB TENSE AND MOOD ANALYSIS ===
        # Present tense feels more anthropomorphic than past/future
        if verb_token.tag_ in ['VBZ', 'VBP']:  # Present tense
            evidence_score += 0.1  # "The system thinks" vs "The system thought"
        elif verb_token.tag_ in ['VBD', 'VBN']:  # Past tense/participle
            evidence_score -= 0.1  # Less anthropomorphic feeling
        elif verb_token.tag_ in ['VBG']:  # Present participle
            evidence_score += 0.05  # "The system is thinking" slightly anthropomorphic
        
        # === MORPHOLOGICAL FEATURES ANALYSIS ===
        # Enhanced morphological analysis using SpaCy's morph features
        if hasattr(verb_token, 'morph') and verb_token.morph:
            morph_str = str(verb_token.morph)
            
            # Tense features
            if 'Tense=Pres' in morph_str:
                evidence_score += 0.1  # Present tense more anthropomorphic
            elif 'Tense=Past' in morph_str:
                evidence_score -= 0.05  # Past tense less anthropomorphic
            
            # Person features
            if 'Person=3' in morph_str:
                evidence_score += 0.05  # Third person ("it thinks") more anthropomorphic
            
            # Number features
            if 'Number=Sing' in morph_str:
                evidence_score += 0.03  # Singular subjects often more anthropomorphic
            
            # Voice features
            if 'Voice=Pass' in morph_str:
                evidence_score -= 0.15  # Passive voice less anthropomorphic
        
        # === DEPENDENCY PARSING ENHANCED ANALYSIS ===
        # More detailed dependency relationship analysis
        if verb_token.dep_ == 'ROOT':
            evidence_score += 0.05  # Main verb in sentence more prominent
        elif verb_token.dep_ in ['xcomp', 'ccomp']:
            evidence_score -= 0.1  # Complement clauses less anthropomorphic
        elif verb_token.dep_ in ['acl', 'relcl']:
            evidence_score -= 0.05  # Relative clauses less anthropomorphic
        
        # === ENHANCED SUBJECT ANALYSIS ===
        # More comprehensive subject type analysis
        if hasattr(subject_token, 'morph') and subject_token.morph:
            subj_morph = str(subject_token.morph)
            if 'Number=Plur' in subj_morph:
                evidence_score -= 0.1  # Plural subjects less anthropomorphic
        
        # Check subject's part-of-speech tag for more detail
        if subject_token.tag_ in ['NNP', 'NNPS']:  # Proper nouns
            if subject_token.ent_type_ in ['ORG', 'PRODUCT']:
                evidence_score -= 0.1  # Organizations/products can have agency
        elif subject_token.tag_ in ['NN', 'NNS']:  # Common nouns
            evidence_score += 0.05  # Common nouns more likely to be inappropriate
        
        # === ENHANCED NAMED ENTITY ANALYSIS ===
        # More nuanced entity type handling with IOB tags
        if subject_token.ent_type_:
            # Check entity IOB tags for confidence
            if hasattr(subject_token, 'ent_iob_'):
                if subject_token.ent_iob_ == 'B':  # Beginning of entity
                    evidence_score -= 0.1  # High confidence entity
                elif subject_token.ent_iob_ == 'I':  # Inside entity
                    evidence_score -= 0.05  # Part of entity
        
        # === POS TAG ANALYSIS ===
        # Part-of-speech based evidence adjustment
        if hasattr(subject_token, 'pos_'):
            if subject_token.pos_ == 'PROPN':  # Proper noun
                evidence_score -= 0.2  # Proper nouns can have more agency
            elif subject_token.pos_ == 'NOUN':  # Common noun
                evidence_score += 0.05  # Common nouns more likely inappropriate
            elif subject_token.pos_ == 'PRON':  # Pronoun
                evidence_score -= 0.3  # Pronouns refer to entities with agency
        
        if hasattr(verb_token, 'pos_'):
            if verb_token.pos_ == 'VERB':  # Main verb
                evidence_score += 0.05  # Main verbs more prominent
            elif verb_token.pos_ == 'AUX':  # Auxiliary verb
                evidence_score -= 0.1  # Auxiliary verbs less anthropomorphic
        
        # === SUBJECT ANALYSIS ===
        # Animate vs inanimate subject indicators
        if subject_token.ent_type_ in ['PERSON', 'ORG']:
            evidence_score -= 0.8  # Animate subjects can use human verbs
        elif subject_token.ent_type_ in ['PRODUCT', 'FAC']:
            evidence_score -= 0.2  # Products/facilities have some agency
        
        # === OBJECT/COMPLEMENT ANALYSIS ===
        # Check what the verb acts upon
        direct_objects = [child for child in verb_token.children if child.dep_ == 'dobj']
        if direct_objects:
            obj = direct_objects[0]
            if obj.ent_type_ in ['PERSON']:
                evidence_score += 0.2  # "System wants user" more anthropomorphic
            elif obj.lemma_.lower() in ['data', 'information', 'input', 'output']:
                evidence_score -= 0.2  # Technical objects less anthropomorphic
        
        # === MODIFIER ANALYSIS ===
        # Adverbs can make anthropomorphism more/less problematic
        adverbs = [child for child in verb_token.children if child.dep_ == 'advmod']
        for adv in adverbs:
            if adv.lemma_.lower() in ['automatically', 'dynamically', 'programmatically']:
                evidence_score -= 0.3  # Technical adverbs reduce anthropomorphism
            elif adv.lemma_.lower() in ['carefully', 'thoughtfully', 'intelligently']:
                evidence_score += 0.2  # Human-like adverbs increase anthropomorphism
        
        # === AUXILIARY VERB PATTERNS ===
        # Modal auxiliaries can change perception
        auxiliaries = [child for child in verb_token.children if child.dep_ == 'aux']
        for aux in auxiliaries:
            if aux.lemma_.lower() in ['can', 'will', 'should', 'must']:
                evidence_score -= 0.1  # Modal usage feels more technical
            elif aux.lemma_.lower() in ['might', 'could', 'would']:
                evidence_score += 0.1  # Conditional usage feels more human-like
        
        return evidence_score

    def _apply_structural_clues_anthropomorphism(self, evidence_score: float, verb_token, subject_token, context: dict) -> float:
        """Apply document structure-based clues for anthropomorphism."""
        
        if not context:
            return evidence_score
        
        block_type = context.get('block_type', 'paragraph')
        
        # === TECHNICAL WRITING CONTEXTS ===
        # Code and technical blocks are more permissive
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.9  # Code comments can be very anthropomorphic
        elif block_type == 'inline_code':
            evidence_score -= 0.7  # Inline technical context
        
        # === API DOCUMENTATION CONTEXTS ===
        # API docs often use anthropomorphic language conventionally
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.4  # API tables: "Method expects JSON"
        
        # === PROCEDURAL CONTEXTS ===
        # Instructions and procedures often anthropomorphize systems
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.3  # "The system will ask for confirmation"
            
            # Nested technical procedures even more permissive
            if context.get('list_depth', 1) > 1:
                evidence_score -= 0.2
        
        # === HEADING CONTEXTS ===
        # Headings often use shorthand anthropomorphic phrases
        elif block_type == 'heading':
            heading_level = context.get('block_level', 1)
            if heading_level <= 2:  # Main headings
                evidence_score -= 0.3  # "What the System Knows"
            else:  # Subsection headings
                evidence_score -= 0.2
        
        # === ADMONITION CONTEXTS ===
        # Notes and warnings often personify systems
        elif block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'TIP', 'HINT']:
                evidence_score -= 0.3  # "Note: The system expects..."
            elif admonition_type in ['WARNING', 'CAUTION']:
                evidence_score -= 0.2  # "Warning: The system will reject..."
        
        return evidence_score

    def _apply_semantic_clues_anthropomorphism(self, evidence_score: float, verb_token, subject_token, text: str, context: dict) -> float:
        """Apply semantic and content-type clues for anthropomorphism."""
        
        if not context:
            return evidence_score
        
        content_type = context.get('content_type', 'general')
        
        # === CONTENT TYPE ANALYSIS ===
        # Use helper methods for enhanced content type analysis
        if self._is_api_documentation(text):
            evidence_score -= 0.4  # API docs heavily anthropomorphic by convention
        elif self._is_technical_specification(text, context):
            evidence_score -= 0.3  # Technical specs allow anthropomorphic language
        elif self._is_user_interface_documentation(text):
            evidence_score -= 0.3  # UI docs often anthropomorphize interfaces
        elif self._is_system_administration_content(text, context):
            evidence_score -= 0.3  # Sysadmin content often anthropomorphizes systems
        elif self._is_software_architecture_content(text, context):
            evidence_score -= 0.2  # Architecture docs moderately anthropomorphic
        elif self._is_troubleshooting_content(text, context):
            evidence_score -= 0.2  # Troubleshooting often personalizes systems
        
        # General technical content analysis
        elif content_type == 'technical':
            evidence_score -= 0.3  # Technical writing conventionally anthropomorphic
            
            # Check for technical context words nearby
            if self._has_technical_context_words(verb_token.sent.text, distance=10):
                evidence_score -= 0.3  # "The API expects JSON response"
        
        # API documentation specifically very permissive
        elif content_type == 'api':
            evidence_score -= 0.4  # API docs heavily anthropomorphic by convention
        
        # Procedural content often anthropomorphizes systems
        elif content_type == 'procedural':
            evidence_score -= 0.2  # Step-by-step instructions
        
        # Academic content more careful about anthropomorphism
        elif content_type == 'academic':
            evidence_score += 0.2  # Academic writing more precise
        
        # Legal content very careful about anthropomorphism
        elif content_type == 'legal':
            evidence_score += 0.3  # Legal writing avoids imprecision
        
        # Marketing content often intentionally anthropomorphic
        elif content_type == 'marketing':
            evidence_score -= 0.4  # Marketing often personifies products
        
        # Narrative content allows anthropomorphism
        elif content_type == 'narrative':
            evidence_score -= 0.5  # Storytelling context
        
        # === DOMAIN-SPECIFIC PATTERNS ===
        domain = context.get('domain', 'general')
        if domain in ['software', 'engineering', 'devops', 'api']:
            evidence_score -= 0.3  # Technical domains very permissive
        elif domain in ['documentation', 'tutorial']:
            evidence_score -= 0.2  # Educational content often anthropomorphic
        
        # === AUDIENCE CONSIDERATIONS ===
        audience = context.get('audience', 'general')
        if audience in ['developer', 'technical', 'expert']:
            evidence_score -= 0.2  # Technical audience expects anthropomorphic conventions
        elif audience in ['academic', 'scientific']:
            evidence_score += 0.2  # Academic audience expects precision
        
        # === VERB-SUBJECT COMBINATION PATTERNS ===
        verb_lemma = verb_token.lemma_.lower()
        subject_lemma = subject_token.lemma_.lower()
        
        # Check for highly conventional technical patterns
        conventional_patterns = {
            ('api', 'expect'), ('api', 'return'), ('api', 'accept'), ('api', 'require'),
            ('system', 'allow'), ('system', 'permit'), ('system', 'support'),
            ('application', 'detect'), ('application', 'determine'), ('application', 'select'),
            ('server', 'respond'), ('server', 'serve'), ('server', 'listen'),
            ('database', 'store'), ('database', 'retrieve'), ('database', 'contain'),
            ('interface', 'display'), ('interface', 'show'), ('interface', 'present'),
            ('function', 'return'), ('function', 'accept'), ('function', 'expect'),
            ('method', 'take'), ('method', 'perform'), ('method', 'execute')
        }
        
        if (subject_lemma, verb_lemma) in conventional_patterns:
            evidence_score -= 0.4  # Highly conventional technical usage
        
        # Check for problematic combinations
        problematic_patterns = {
            ('system', 'think'), ('system', 'believe'), ('system', 'feel'),
            ('application', 'want'), ('application', 'wish'), ('application', 'hope'),
            ('software', 'love'), ('software', 'hate'), ('software', 'worry')
        }
        
        if (subject_lemma, verb_lemma) in problematic_patterns:
            evidence_score += 0.4  # Clearly inappropriate combinations
        
        return evidence_score

    def _apply_feedback_clues_anthropomorphism(self, evidence_score: float, verb_token, subject_token, context: dict) -> float:
        """Apply clues learned from user feedback patterns for anthropomorphism."""
        
        # Load cached feedback patterns
        feedback_patterns = self._get_cached_feedback_patterns('anthropomorphism')
        
        verb_lemma = verb_token.lemma_.lower()
        subject_lemma = subject_token.lemma_.lower()
        
        # Check for consistently accepted anthropomorphic patterns
        accepted_patterns = feedback_patterns.get('accepted_anthropomorphic_patterns', set())
        pattern = f"{subject_lemma} {verb_lemma}"
        
        if pattern in accepted_patterns:
            evidence_score -= 0.5  # Users consistently accept this pattern
        
        # Check for consistently flagged patterns
        flagged_patterns = feedback_patterns.get('flagged_anthropomorphic_patterns', set())
        if pattern in flagged_patterns:
            evidence_score += 0.4  # Users consistently find this problematic
        
        # Check verb-specific feedback
        verb_acceptance = feedback_patterns.get('verb_acceptance_rates', {})
        acceptance_rate = verb_acceptance.get(verb_lemma, 0.5)
        
        if acceptance_rate > 0.8:
            evidence_score -= 0.3  # Highly accepted verb
        elif acceptance_rate < 0.2:
            evidence_score += 0.3  # Frequently rejected verb
        
        # Check subject-specific feedback
        subject_acceptance = feedback_patterns.get('subject_acceptance_rates', {})
        subject_rate = subject_acceptance.get(subject_lemma, 0.5)
        
        if subject_rate > 0.8:
            evidence_score -= 0.2  # Subjects commonly anthropomorphized acceptably
        elif subject_rate < 0.2:
            evidence_score += 0.2  # Subjects that shouldn't be anthropomorphized
        
        return evidence_score

    def _is_technical_specification(self, text: str, context: dict) -> bool:
        """Check if content is technical specification."""
        domain = context.get('domain', '')
        content_type = context.get('content_type', '')
        
        # Direct indicators
        if content_type in ['specification', 'technical'] or domain in ['engineering', 'technical']:
            return True
        
        # Text-based indicators
        spec_indicators = [
            'specification', 'requirement', 'protocol', 'standard',
            'implementation', 'architecture', 'design', 'interface',
            'component', 'module', 'system', 'framework', 'library',
            'algorithm', 'data structure', 'performance', 'scalability'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in spec_indicators if indicator in text_lower) >= 3

    # Removed _is_user_interface_documentation - using base class utility

    def _is_system_administration_content(self, text: str, context: dict) -> bool:
        """Check if content is system administration related."""
        domain = context.get('domain', '')
        content_type = context.get('content_type', '')
        
        # Direct indicators
        if domain in ['sysadmin', 'devops', 'administration'] or content_type in ['administration', 'devops']:
            return True
        
        # Text-based indicators
        sysadmin_indicators = [
            'server', 'administrator', 'configuration', 'deployment',
            'monitoring', 'logging', 'backup', 'security', 'firewall',
            'network', 'database', 'service', 'daemon', 'process',
            'install', 'configure', 'manage', 'maintain', 'troubleshoot'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in sysadmin_indicators if indicator in text_lower) >= 4

    def _is_software_architecture_content(self, text: str, context: dict) -> bool:
        """Check if content is software architecture related."""
        domain = context.get('domain', '')
        content_type = context.get('content_type', '')
        
        # Direct indicators
        if domain in ['architecture', 'software'] or content_type in ['architecture', 'design']:
            return True
        
        # Text-based indicators
        architecture_indicators = [
            'architecture', 'design', 'pattern', 'framework', 'structure',
            'component', 'module', 'layer', 'tier', 'microservice',
            'service', 'interface', 'dependency', 'coupling', 'cohesion',
            'scalability', 'performance', 'reliability', 'maintainability'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in architecture_indicators if indicator in text_lower) >= 4

    def _is_troubleshooting_content(self, text: str, context: dict) -> bool:
        """Check if content is troubleshooting/debugging related."""
        content_type = context.get('content_type', '')
        domain = context.get('domain', '')
        
        # Direct indicators
        if content_type in ['troubleshooting', 'debugging'] or domain in ['support', 'troubleshooting']:
            return True
        
        # Text-based indicators
        troubleshooting_indicators = [
            'troubleshoot', 'debug', 'error', 'problem', 'issue', 'fix',
            'solve', 'diagnose', 'identify', 'resolve', 'workaround',
            'symptom', 'cause', 'solution', 'check', 'verify', 'test',
            'validate', 'investigate', 'analyze', 'examine'
        ]
        
        text_lower = text.lower()
        return sum(1 for indicator in troubleshooting_indicators if indicator in text_lower) >= 4


    def _get_contextual_message(self, verb_token, subject_token, evidence_score: float) -> str:
        """Generate context-aware error messages based on evidence score."""
        
        verb = verb_token.text
        subject = subject_token.text
        
        if evidence_score > 0.8:
            return f"Avoid anthropomorphism: '{subject}' {verb}' gives human characteristics to an inanimate object."
        elif evidence_score > 0.5:
            return f"Consider rephrasing: '{subject} {verb}' may be overly anthropomorphic for this context."
        else:
            return f"The phrase '{subject} {verb}' could be less anthropomorphic depending on your style guide."

    def _generate_smart_suggestions(self, verb_token, subject_token, evidence_score: float, context: dict) -> List[str]:
        """Generate context-aware suggestions based on evidence score and context."""
        
        suggestions = []
        verb_lemma = verb_token.lemma_.lower()
        subject_text = subject_token.text
        
        # === VERB-SPECIFIC SUGGESTIONS ===
        verb_alternatives = {
            'think': 'determine, calculate, process, analyze',
            'know': 'store, contain, have, include',
            'believe': 'assume, determine, indicate, suggest',
            'want': 'require, need, expect, request',
            'see': 'detect, identify, recognize, find',
            'tell': 'inform, notify, indicate, show',
            'ask': 'prompt, request, require, expect',
            'decide': 'determine, select, choose, resolve',
            'expect': 'require, anticipate, await, need',
            'feel': 'detect, sense, measure, register'
        }
        
        if verb_lemma in verb_alternatives:
            alternatives = verb_alternatives[verb_lemma]
            suggestions.append(f"Replace '{verb_token.text}' with a more technical verb: {alternatives}.")
        
        # === GENERAL SUGGESTIONS ===
        suggestions.append("Focus on what the system does rather than what it 'thinks' or 'feels'.")
        
        # === CONTEXT-SPECIFIC SUGGESTIONS ===
        if context:
            content_type = context.get('content_type', 'general')
            
            if content_type == 'technical':
                suggestions.append("In technical writing, describe system behavior objectively.")
            elif content_type == 'api':
                suggestions.append("API documentation should describe functionality, not intentions.")
            elif content_type == 'procedural':
                suggestions.append("Focus on the actions users take and system responses.")
        
        # === EVIDENCE-BASED SUGGESTIONS ===
        if evidence_score > 0.7:
            suggestions.append("Consider completely rewriting the sentence to avoid anthropomorphism.")
            suggestions.append(f"Instead of '{subject_text} {verb_token.text}', describe the actual process or user action.")
        elif evidence_score < 0.3:
            suggestions.append("This usage may be acceptable in your context, but consider your style guide.")
        
        return suggestions
