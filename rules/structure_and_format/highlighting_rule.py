"""
Highlighting Rule
Based on IBM Style Guide topic: "Highlighting"
Enhanced with pure SpaCy morphological analysis for robust UI element and highlighting detection.
"""
from typing import List, Dict, Any, Tuple, Optional, Set
from .base_structure_rule import BaseStructureRule

class HighlightingRule(BaseStructureRule):
    """
    Checks for correct highlighting of elements like UI controls, software features,
    and interface elements using advanced morphological and semantic analysis.
    Detects when text should be highlighted without requiring pre-existing style information.
    """
    
    def __init__(self):
        super().__init__()
        # Initialize highlighting-specific linguistic anchors
        self._initialize_highlighting_anchors()
    
    def _initialize_highlighting_anchors(self):
        """Initialize morphological patterns specific to highlighting analysis."""
        
        # UI element detection patterns using morphological analysis
        self.ui_element_patterns = {
            'interactive_elements': {
                'buttons': ['button', 'btn', 'submit', 'cancel', 'ok', 'apply', 'save', 'delete'],
                'form_controls': ['field', 'input', 'textbox', 'checkbox', 'dropdown', 'list', 'selector'],
                'navigation': ['menu', 'tab', 'link', 'navigation', 'navbar', 'sidebar', 'breadcrumb'],
                'windows_dialogs': ['window', 'dialog', 'modal', 'popup', 'panel', 'pane', 'frame']
            },
            'interface_terminology': {
                'actions': ['click', 'select', 'choose', 'press', 'tap', 'touch', 'drag', 'drop'],
                'locations': ['toolbar', 'menubar', 'statusbar', 'taskbar', 'desktop', 'workspace'],
                'features': ['option', 'setting', 'preference', 'configuration', 'property', 'parameter']
            },
            'software_elements': {
                'application_parts': ['toolbar', 'ribbon', 'palette', 'inspector', 'explorer', 'browser'],
                'file_system': ['folder', 'directory', 'file', 'document', 'project', 'workspace'],
                'code_elements': ['function', 'method', 'class', 'variable', 'parameter', 'attribute']
            }
        }
        
        # Morphological patterns that indicate highlighting necessity
        self.highlighting_contexts = {
            'imperative_ui_actions': {
                'verb_patterns': ['VB+dobj', 'VB+prep+pobj'],  # Click the button, Select from menu
                'semantic_roles': ['agent+action+patient'],  # User performs action on UI element
                'dependency_patterns': ['ROOT+VERB', 'aux+VERB']  # Imperative constructions
            },
            'reference_patterns': {
                'demonstrative_references': ['this', 'that', 'these', 'those'],  # "this button"
                'definite_references': ['the'],  # "the Save button"
                'possessive_references': ['your', 'its', 'their']  # "your settings"
            },
            'instructional_contexts': {
                'procedure_markers': ['step', 'first', 'next', 'then', 'finally'],
                'location_prepositions': ['in', 'on', 'under', 'within', 'from'],
                'guidance_verbs': ['see', 'refer', 'check', 'view', 'access', 'navigate']
            }
        }
        
        # Semantic fields that typically require highlighting
        self.highlightable_semantic_fields = {
            'ui_interface': True,
            'software_feature': True,
            'user_action': True,
            'system_response': True,
            'technical_term': True,
            'proper_noun_ui': True
        }
        
        # Context patterns for different types of highlighting
        self.highlighting_types = {
            'ui_controls': {
                'examples': ['Save button', 'File menu', 'Options dialog'],
                'morphological_indicators': ['NOUN+compound', 'PROPN+NOUN'],
                'highlighting_style': 'bold'
            },
            'menu_paths': {
                'examples': ['File > Save As', 'Edit > Preferences'],
                'morphological_indicators': ['PROPN+punct+PROPN'],
                'highlighting_style': 'bold'
            },
            'keyboard_shortcuts': {
                'examples': ['Ctrl+S', 'Alt+Tab', 'Shift+Click'],
                'morphological_indicators': ['SYM+punct+SYM'],
                'highlighting_style': 'bold'
            },
            'code_elements': {
                'examples': ['function()', 'className', 'variableName'],
                'morphological_indicators': ['code_pattern'],
                'highlighting_style': 'monospace'
            }
        }

    def _get_rule_type(self) -> str:
        return 'structure_format_highlighting'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for highlighting violations using comprehensive
        morphological and semantic analysis.
        """
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = self._analyze_sentence_structure(sentence, nlp)
            if not doc:
                continue
            
            # Analyze for UI elements that need highlighting
            ui_highlighting_errors = self._analyze_ui_element_highlighting(doc, sentence, i)
            errors.extend(ui_highlighting_errors)
            
            # Analyze for instructional content highlighting
            instructional_errors = self._analyze_instructional_highlighting(doc, sentence, i)
            errors.extend(instructional_errors)
            
            # Analyze for technical terminology highlighting
            technical_errors = self._analyze_technical_terminology_highlighting(doc, sentence, i)
            errors.extend(technical_errors)
            
            # Analyze for menu paths and navigation highlighting
            navigation_errors = self._analyze_navigation_highlighting(doc, sentence, i)
            errors.extend(navigation_errors)

        return errors
    
    def _analyze_sentence_structure(self, sentence: str, nlp=None):
        """Get SpaCy doc for a sentence with error handling."""
        if nlp and sentence.strip():
            try:
                return nlp(sentence)
            except Exception:
                return None
        return None
    
    def _analyze_ui_element_highlighting(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Analyze UI elements that should be highlighted using morphological patterns.
        """
        errors = []
        
        if not doc:
            return errors
        
        # Detect imperative constructions targeting UI elements
        imperative_ui_actions = self._detect_imperative_ui_actions(doc)
        for action in imperative_ui_actions:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"UI element '{action['ui_element']}' should be highlighted in bold.",
                suggestions=[f"Apply bold formatting to '{action['ui_element']}'."],
                severity='high',
                linguistic_analysis={
                    'ui_action': action,
                    'highlighting_type': 'ui_control',
                    'morphological_pattern': action.get('morphological_pattern')
                }
            ))
        
        # Detect UI elements in reference contexts
        ui_references = self._detect_ui_element_references(doc)
        for reference in ui_references:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"UI element '{reference['element']}' should be highlighted in bold.",
                suggestions=[f"Apply bold formatting to '{reference['element']}'."],
                severity='medium',
                linguistic_analysis={
                    'ui_reference': reference,
                    'highlighting_type': 'ui_reference',
                    'reference_type': reference.get('type')
                }
            ))
        
        return errors
    
    def _analyze_instructional_highlighting(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Analyze instructional content for highlighting needs.
        """
        errors = []
        
        if not doc:
            return errors
        
        # Detect procedural instructions with UI elements
        procedural_elements = self._detect_procedural_ui_elements(doc)
        for element in procedural_elements:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Procedural reference '{element['text']}' should be highlighted for clarity.",
                suggestions=[f"Apply bold formatting to '{element['text']}' in procedural context."],
                severity='medium',
                linguistic_analysis={
                    'procedural_element': element,
                    'highlighting_type': 'procedural_instruction',
                    'context_type': element.get('context_type')
                }
            ))
        
        return errors
    
    def _analyze_technical_terminology_highlighting(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Analyze technical terminology that requires highlighting.
        """
        errors = []
        
        if not doc:
            return errors
        
        # Detect technical terms and code elements
        technical_terms = self._detect_technical_terminology(doc)
        for term in technical_terms:
            highlighting_style = self._determine_highlighting_style(term)
            
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Technical term '{term['text']}' should be highlighted with {highlighting_style} formatting.",
                suggestions=[f"Apply {highlighting_style} formatting to '{term['text']}'."],
                severity='low',
                linguistic_analysis={
                    'technical_term': term,
                    'highlighting_type': 'technical_terminology',
                    'recommended_style': highlighting_style
                }
            ))
        
        return errors
    
    def _analyze_navigation_highlighting(self, doc, sentence: str, sentence_index: int) -> List[Dict[str, Any]]:
        """
        Analyze navigation paths and menu sequences for highlighting.
        """
        errors = []
        
        if not doc:
            return errors
        
        # Detect menu paths and navigation sequences
        navigation_paths = self._detect_navigation_paths(doc, sentence)
        for path in navigation_paths:
            errors.append(self._create_error(
                sentence=sentence,
                sentence_index=sentence_index,
                message=f"Navigation path '{path['path']}' should be highlighted in bold.",
                suggestions=[f"Apply bold formatting to the entire path '{path['path']}'."],
                severity='high',
                linguistic_analysis={
                    'navigation_path': path,
                    'highlighting_type': 'navigation_sequence',
                    'path_components': path.get('components')
                }
            ))
        
        return errors
    
    def _detect_imperative_ui_actions(self, doc) -> List[Dict[str, Any]]:
        """
        Detect imperative constructions that target UI elements.
        """
        imperative_actions = []
        
        if not doc:
            return imperative_actions
        
        try:
            # Look for imperative verbs (ROOT verbs in base form)
            for token in doc:
                if (token.dep_ == 'ROOT' and 
                    token.pos_ == 'VERB' and 
                    token.tag_ in ['VB', 'VBP']):  # Base form or present tense
                    
                    # Check if it's a UI action verb
                    if self._is_ui_action_verb(token):
                        # Find the direct object (target of the action)
                        ui_targets = self._find_ui_targets(token, doc)
                        
                        for target in ui_targets:
                            imperative_actions.append({
                                'action_verb': token.text,
                                'ui_element': target['text'],
                                'morphological_pattern': f"{token.pos_}+{token.dep_}>{target['dependency']}",
                                'action_token': self._token_to_dict(token),
                                'target_token': target,
                                'confidence_score': self._calculate_ui_confidence(token, target)
                            })
        
        except Exception:
            pass
        
        return imperative_actions
    
    def _detect_ui_element_references(self, doc) -> List[Dict[str, Any]]:
        """
        Detect references to UI elements in non-imperative contexts.
        """
        ui_references = []
        
        if not doc:
            return ui_references
        
        try:
            for token in doc:
                # Look for nouns that are UI elements
                if token.pos_ in ['NOUN', 'PROPN']:
                    ui_analysis = self._analyze_ui_element_likelihood(token, doc)
                    
                    if ui_analysis['is_ui_element']:
                        # Check the reference context
                        reference_context = self._analyze_reference_context(token, doc)
                        
                        ui_references.append({
                            'element': token.text,
                            'type': ui_analysis['ui_type'],
                            'confidence': ui_analysis['confidence'],
                            'reference_context': reference_context,
                            'morphological_features': self._get_morphological_features(token),
                            'semantic_field': self._analyze_semantic_field(token, doc)
                        })
        
        except Exception:
            pass
        
        return ui_references
    
    def _detect_procedural_ui_elements(self, doc) -> List[Dict[str, Any]]:
        """
        Detect UI elements in procedural/instructional contexts.
        """
        procedural_elements = []
        
        if not doc:
            return procedural_elements
        
        try:
            # Look for procedural markers
            procedural_markers = ['step', 'first', 'next', 'then', 'finally', 'now']
            
            for token in doc:
                if token.lemma_.lower() in procedural_markers:
                    # Find nearby UI elements
                    nearby_ui_elements = self._find_nearby_ui_elements(token, doc, window=5)
                    
                    for ui_element in nearby_ui_elements:
                        procedural_elements.append({
                            'text': ui_element['text'],
                            'procedural_marker': token.text,
                            'context_type': 'procedural_instruction',
                            'ui_element_type': ui_element.get('ui_type'),
                            'distance_from_marker': abs(token.i - ui_element['token_index'])
                        })
        
        except Exception:
            pass
        
        return procedural_elements
    
    def _detect_technical_terminology(self, doc) -> List[Dict[str, Any]]:
        """
        Detect technical terminology that requires highlighting.
        """
        technical_terms = []
        
        if not doc:
            return technical_terms
        
        try:
            for token in doc:
                # Detect code-like patterns
                if self._is_code_element(token):
                    technical_terms.append({
                        'text': token.text,
                        'type': 'code_element',
                        'pattern': self._get_code_pattern(token),
                        'morphological_features': self._get_morphological_features(token)
                    })
                
                # Detect technical terminology using morphological complexity
                elif self._is_technical_term(token, doc):
                    technical_terms.append({
                        'text': token.text,
                        'type': 'technical_term',
                        'complexity_score': self._calculate_morphological_complexity(token),
                        'semantic_field': self._analyze_semantic_field(token, doc)
                    })
        
        except Exception:
            pass
        
        return technical_terms
    
    def _detect_navigation_paths(self, doc, sentence: str) -> List[Dict[str, Any]]:
        """
        Detect menu paths and navigation sequences.
        """
        navigation_paths = []
        
        try:
            # Look for navigation patterns like "File > Save As" or "Edit → Preferences"
            navigation_separators = ['>', '→', '/', '\\', '|', '::']
            
            # Simple pattern matching for menu paths
            for separator in navigation_separators:
                if separator in sentence:
                    # Split and analyze potential menu path
                    parts = sentence.split(separator)
                    if len(parts) >= 2:
                        # Check if parts look like menu items
                        potential_path = separator.join(parts[:2]).strip()
                        if self._is_likely_navigation_path(potential_path, doc):
                            navigation_paths.append({
                                'path': potential_path,
                                'separator': separator,
                                'components': [part.strip() for part in parts[:2]],
                                'confidence': self._calculate_navigation_confidence(potential_path)
                            })
        
        except Exception:
            pass
        
        return navigation_paths
    
    def _is_ui_action_verb(self, token) -> bool:
        """
        Check if a verb is a UI action verb using morphological analysis.
        """
        ui_action_verbs = set()
        for category in self.ui_element_patterns['interface_terminology'].values():
            ui_action_verbs.update(category)
        
        return token.lemma_.lower() in ui_action_verbs
    
    def _find_ui_targets(self, action_verb, doc) -> List[Dict[str, Any]]:
        """
        Find UI elements that are targets of the action verb.
        """
        ui_targets = []
        
        try:
            # Look for direct objects
            for child in action_verb.children:
                if child.dep_ in ['dobj', 'pobj']:
                    ui_analysis = self._analyze_ui_element_likelihood(child, doc)
                    
                    if ui_analysis['is_ui_element']:
                        ui_targets.append({
                            'text': child.text,
                            'dependency': child.dep_,
                            'ui_type': ui_analysis['ui_type'],
                            'confidence': ui_analysis['confidence'],
                            'token_index': child.i
                        })
                    
                    # Also check compound objects or phrases
                    compound_phrase = self._extract_noun_phrase(child, doc)
                    if len(compound_phrase) > 1:
                        full_phrase = ' '.join(compound_phrase)
                        phrase_analysis = self._analyze_phrase_ui_likelihood(compound_phrase, doc)
                        
                        if phrase_analysis['is_ui_element']:
                            ui_targets.append({
                                'text': full_phrase,
                                'dependency': child.dep_,
                                'ui_type': phrase_analysis['ui_type'],
                                'confidence': phrase_analysis['confidence'],
                                'token_index': child.i
                            })
        
        except Exception:
            pass
        
        return ui_targets
    
    def _analyze_ui_element_likelihood(self, token, doc) -> Dict[str, Any]:
        """
        Analyze likelihood that a token represents a UI element.
        """
        try:
            ui_score = 0.0
            ui_type = 'unknown'
            
            # Check against UI element patterns
            lemma = token.lemma_.lower()
            text = token.text.lower()
            
            for category, elements in self.ui_element_patterns['interactive_elements'].items():
                if lemma in elements or text in elements:
                    ui_score += 0.8
                    ui_type = category
                    break
            
            # Check morphological patterns
            if token.pos_ == 'PROPN':  # Proper nouns often represent UI elements
                ui_score += 0.3
            
            # Check capitalization patterns (UI elements often capitalized)
            if token.text[0].isupper() and len(token.text) > 1:
                ui_score += 0.2
            
            # Check context (near UI action verbs)
            context_score = self._calculate_ui_context_score(token, doc)
            ui_score += context_score
            
            return {
                'is_ui_element': ui_score > 0.5,
                'confidence': min(ui_score, 1.0),
                'ui_type': ui_type
            }
        
        except Exception:
            return {
                'is_ui_element': False,
                'confidence': 0.0,
                'ui_type': 'unknown'
            }
    
    def _analyze_reference_context(self, token, doc) -> Dict[str, Any]:
        """
        Analyze the reference context of a UI element.
        """
        try:
            context = {
                'has_definite_article': False,
                'has_demonstrative': False,
                'in_prepositional_phrase': False,
                'reference_type': 'none'
            }
            
            # Check for determiners
            for child in token.children:
                if child.dep_ == 'det':
                    if child.lemma_.lower() == 'the':
                        context['has_definite_article'] = True
                        context['reference_type'] = 'definite'
                    elif child.lemma_.lower() in ['this', 'that', 'these', 'those']:
                        context['has_demonstrative'] = True
                        context['reference_type'] = 'demonstrative'
            
            # Check if in prepositional phrase
            if token.dep_ == 'pobj':
                context['in_prepositional_phrase'] = True
            
            return context
        
        except Exception:
            return {'reference_type': 'unknown'}
    
    def _find_nearby_ui_elements(self, anchor_token, doc, window: int = 5) -> List[Dict[str, Any]]:
        """
        Find UI elements near an anchor token.
        """
        nearby_elements = []
        
        try:
            start_idx = max(0, anchor_token.i - window)
            end_idx = min(len(doc), anchor_token.i + window + 1)
            
            for i in range(start_idx, end_idx):
                if i != anchor_token.i:
                    token = doc[i]
                    ui_analysis = self._analyze_ui_element_likelihood(token, doc)
                    
                    if ui_analysis['is_ui_element']:
                        nearby_elements.append({
                            'text': token.text,
                            'token_index': i,
                            'ui_type': ui_analysis['ui_type'],
                            'confidence': ui_analysis['confidence']
                        })
        
        except Exception:
            pass
        
        return nearby_elements
    
    def _is_code_element(self, token) -> bool:
        """
        Check if token represents a code element.
        """
        try:
            # Check for code-like patterns
            text = token.text
            
            # Function calls
            if '(' in text and ')' in text:
                return True
            
            # Variable naming conventions
            if ('_' in text or 
                (text[0].islower() and any(c.isupper() for c in text[1:])) or  # camelCase
                text.isupper()):  # CONSTANTS
                return True
            
            # File extensions or paths
            if '.' in text and any(text.endswith(ext) for ext in ['.js', '.py', '.java', '.cpp', '.html']):
                return True
            
            return False
        
        except Exception:
            return False
    
    def _is_technical_term(self, token, doc) -> bool:
        """
        Check if token is a technical term using morphological analysis.
        """
        try:
            # High morphological complexity might indicate technical terms
            complexity = self._calculate_morphological_complexity(token)
            
            # Technical terms often have specific morphological patterns
            if complexity > 2.5 and token.pos_ in ['NOUN', 'PROPN', 'ADJ']:
                return True
            
            # Check for technical suffixes
            technical_suffixes = ['tion', 'sion', 'ment', 'ance', 'ence', 'ity', 'ism']
            if any(token.text.lower().endswith(suffix) for suffix in technical_suffixes):
                return True
            
            return False
        
        except Exception:
            return False
    
    def _get_code_pattern(self, token) -> str:
        """
        Identify the type of code pattern.
        """
        text = token.text
        
        if '(' in text and ')' in text:
            return 'function_call'
        elif '_' in text:
            return 'snake_case'
        elif text[0].islower() and any(c.isupper() for c in text[1:]):
            return 'camelCase'
        elif text.isupper():
            return 'CONSTANT'
        elif '.' in text:
            return 'file_or_path'
        else:
            return 'code_identifier'
    
    def _calculate_morphological_complexity(self, token) -> float:
        """
        Calculate morphological complexity (simplified version).
        """
        try:
            complexity = 1.0
            
            # Length contributes to complexity
            complexity += len(token.text) * 0.1
            
            # Morphological features contribute
            if hasattr(token, 'morph') and token.morph:
                complexity += len(str(token.morph).split('|')) * 0.2
            
            return min(complexity, 5.0)
        
        except Exception:
            return 1.0
    
    def _analyze_semantic_field(self, token, doc=None) -> str:
        """
        Analyze semantic field (simplified version).
        """
        try:
            if token.pos_ in ['NOUN', 'PROPN']:
                return 'entity'
            elif token.pos_ == 'VERB':
                return 'action'
            elif token.pos_ in ['ADJ', 'ADV']:
                return 'property'
            else:
                return 'function'
        
        except Exception:
            return 'unknown'
    
    def _get_morphological_features(self, token) -> Dict[str, Any]:
        """
        Extract morphological features (simplified version).
        """
        try:
            return {
                'pos': token.pos_,
                'tag': token.tag_,
                'lemma': token.lemma_,
                'dep': token.dep_
            }
        except Exception:
            return {}
    
    def _token_to_dict(self, token) -> Dict[str, Any]:
        """
        Convert token to dictionary (simplified version).
        """
        try:
            return {
                'text': token.text,
                'lemma': token.lemma_,
                'pos': token.pos_,
                'dep': token.dep_,
                'i': token.i
            }
        except Exception:
            return {'text': str(token)}
    
    def _calculate_ui_confidence(self, action_token, target_token) -> float:
        """
        Calculate confidence that this is a UI action.
        """
        try:
            confidence = 0.5
            
            # Strong UI action verbs
            if action_token.lemma_.lower() in ['click', 'select', 'choose', 'press']:
                confidence += 0.3
            
            # Target is likely UI element
            if target_token.get('ui_type') != 'unknown':
                confidence += 0.2
            
            return min(confidence, 1.0)
        
        except Exception:
            return 0.5
    
    def _calculate_ui_context_score(self, token, doc) -> float:
        """
        Calculate UI context score based on surrounding tokens.
        """
        try:
            context_score = 0.0
            window = 3
            
            start_idx = max(0, token.i - window)
            end_idx = min(len(doc), token.i + window + 1)
            
            for i in range(start_idx, end_idx):
                if i != token.i:
                    neighbor = doc[i]
                    if self._is_ui_action_verb(neighbor):
                        context_score += 0.2
            
            return min(context_score, 0.5)
        
        except Exception:
            return 0.0
    
    def _extract_noun_phrase(self, head_noun, doc) -> List[str]:
        """
        Extract noun phrase including modifiers.
        """
        try:
            phrase = [head_noun.text]
            
            # Add modifiers
            for child in head_noun.children:
                if child.dep_ in ['amod', 'compound', 'det']:
                    phrase.insert(0, child.text)
            
            return phrase
        
        except Exception:
            return [head_noun.text if hasattr(head_noun, 'text') else str(head_noun)]
    
    def _analyze_phrase_ui_likelihood(self, phrase_tokens, doc) -> Dict[str, Any]:
        """
        Analyze likelihood that a phrase represents UI element.
        """
        try:
            # Simple heuristic: if any token in phrase is UI-related, whole phrase likely is
            max_confidence = 0.0
            ui_type = 'unknown'
            
            for token_text in phrase_tokens:
                # Find corresponding token in doc
                for token in doc:
                    if token.text == token_text:
                        analysis = self._analyze_ui_element_likelihood(token, doc)
                        if analysis['confidence'] > max_confidence:
                            max_confidence = analysis['confidence']
                            ui_type = analysis['ui_type']
            
            return {
                'is_ui_element': max_confidence > 0.5,
                'confidence': max_confidence,
                'ui_type': ui_type
            }
        
        except Exception:
            return {
                'is_ui_element': False,
                'confidence': 0.0,
                'ui_type': 'unknown'
            }
    
    def _is_likely_navigation_path(self, path, doc) -> bool:
        """
        Check if a string looks like a navigation path.
        """
        try:
            # Navigation paths typically have proper nouns or title case
            parts = [part.strip() for part in path.split('>') if part.strip()]
            
            if len(parts) < 2:
                return False
            
            # Check if parts look like menu items
            for part in parts:
                if not (part[0].isupper() or any(word[0].isupper() for word in part.split())):
                    return False
            
            return True
        
        except Exception:
            return False
    
    def _calculate_navigation_confidence(self, path) -> float:
        """
        Calculate confidence that this is a navigation path.
        """
        try:
            confidence = 0.5
            
            # Common menu words increase confidence
            menu_words = ['file', 'edit', 'view', 'tools', 'help', 'options', 'settings']
            path_lower = path.lower()
            
            for word in menu_words:
                if word in path_lower:
                    confidence += 0.2
            
            return min(confidence, 1.0)
        
        except Exception:
            return 0.5
    
    def _determine_highlighting_style(self, term) -> str:
        """
        Determine appropriate highlighting style for a term.
        """
        term_type = term.get('type', 'unknown')
        
        if term_type == 'code_element':
            return 'monospace'
        elif term_type == 'technical_term':
            return 'italic'
        else:
            return 'bold'

    # Legacy method for backward compatibility
    def analyze_structured_sentence(self, structured_sentence: List[Tuple[str, str]], nlp=None) -> List[Dict[str, Any]]:
        """
        Legacy method for backward compatibility with structured input.
        Now delegates to the main morphological analysis.
        """
        if not structured_sentence:
            return []
        
        # Extract text from structured input
        full_text = " ".join([word for word, style in structured_sentence])
        
        # Use the main analysis method
        return self.analyze(full_text, [full_text], nlp, None)

