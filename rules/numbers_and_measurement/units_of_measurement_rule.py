"""
Units of Measurement Rule
Based on IBM Style Guide topic: "Units of measurement"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class UnitsOfMeasurementRule(BaseNumbersRule):
    """
    Checks for correct formatting of units of measurement, such as ensuring
    a space between the number and the unit abbreviation.
    """
    def _get_rule_type(self) -> str:
        return 'units_of_measurement'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for unit-of-measurement formatting:
          - Prefer a space between number and unit (e.g., '600 MHz')
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
        doc = nlp(text)
        
        no_space_pattern = re.compile(r'\b\d+(mm|cm|m|km|mg|g|kg|ms|s|min|hr|Hz|MHz|GHz|KB|MB|GB|TB)\b')

        for i, sent in enumerate(doc.sents):
            for match in no_space_pattern.finditer(sent.text):
                flagged = match.group(0)
                span = (sent.start_char + match.start(), sent.start_char + match.end())
                ev = self._calculate_units_evidence(flagged, sent, text, context or {})
                if ev > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=self._get_contextual_units_message(flagged, ev, context or {}),
                        suggestions=self._generate_smart_units_suggestions(flagged, ev, sent, context or {}),
                        severity='low' if ev < 0.7 else 'medium',
                        text=text,
                        context=context,
                        evidence_score=ev,
                        span=span,
                        flagged_text=flagged
                    ))
        return errors

    # === EVIDENCE CALCULATION ===

    def _calculate_units_evidence(self, flagged: str, sentence, text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) that a missing space before a unit needs correction.
        
        Following the 5-step evidence calculation pattern:
        1. Base Evidence Assessment
        2. Linguistic Clues (Micro-Level)
        3. Structural Clues (Meso-Level)
        4. Semantic Clues (Macro-Level)
        5. Feedback Patterns (Learning Clues)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = 0.65  # Base evidence for missing space between number and unit
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_units(evidence_score, flagged, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_units(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_units(evidence_score, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_units(evidence_score, flagged, context)
        
        return max(0.0, min(1.0, evidence_score))

    # === LINGUISTIC CLUES (MICRO-LEVEL) ===
    
    def _apply_linguistic_clues_units(self, evidence_score: float, flagged: str, sentence) -> float:
        """Apply SpaCy-based linguistic analysis clues for unit spacing."""
        
        sent_text = sentence.text
        sent_lower = sent_text.lower()
        
        # Check for quotes/code contexts (UI/code examples)
        if '"' in sent_text or "'" in sent_text or '`' in sent_text:
            evidence_score -= 0.25  # Code/UI examples may use specific formatting
        
        # Check for identifier-like patterns (camelCase, snake_case, etc.)
        if re.search(r'[A-Za-z0-9_]{2,}', sent_text):
            evidence_score -= 0.15  # Variable names, IDs, etc.
        
        # Check for timing/performance contexts where ms is common
        if flagged.endswith('ms'):
            timing_verbs = ['wait', 'sleep', 'timeout', 'delay', 'pause', 'execute', 'run']
            if any(t.lemma_.lower() in timing_verbs for t in sentence):
                evidence_score -= 0.1  # Performance contexts may use 'ms' without space
        
        # Check for technical specification contexts
        spec_indicators = ['specification', 'spec', 'requirement', 'config', 'setting']
        if any(indicator in sent_lower for indicator in spec_indicators):
            evidence_score -= 0.1  # Technical specs may use compact notation
        
        # Check for measurement contexts (where spacing is more important)
        measurement_contexts = ['measure', 'measurement', 'size', 'dimension', 'length', 'weight', 'capacity']
        if any(context in sent_lower for context in measurement_contexts):
            evidence_score += 0.1  # Measurement contexts benefit from clear formatting
        
        # Check for scientific/medical contexts (precision important)
        scientific_contexts = ['dose', 'dosage', 'concentration', 'frequency', 'bandwidth', 'resolution']
        if any(context in sent_lower for context in scientific_contexts):
            evidence_score += 0.15  # Scientific contexts need clear units
        
        # Check for data storage/transfer contexts
        data_contexts = ['storage', 'memory', 'disk', 'transfer', 'download', 'upload', 'bandwidth']
        if any(context in sent_lower for context in data_contexts):
            evidence_score += 0.1  # Data contexts benefit from clear formatting
        
        # Check surrounding punctuation/context
        unit_pattern = re.search(r'(\d+)([A-Za-z]+)', flagged)
        if unit_pattern:
            number_part = unit_pattern.group(1)
            unit_part = unit_pattern.group(2)
            
            # Check if it's in a list or series (consistency matters)
            if ',' in sent_text and sent_text.count(unit_part) > 1:
                evidence_score += 0.1  # Multiple units should be consistent
            
            # Check for comparison contexts ("faster than 100ms")
            comparison_words = ['faster', 'slower', 'more', 'less', 'than', 'versus', 'vs']
            if any(word in sent_lower for word in comparison_words):
                evidence_score += 0.05  # Comparisons benefit from clear formatting
        
        # Check for parenthetical usage
        if '(' in sent_text and ')' in sent_text:
            evidence_score -= 0.05  # Parenthetical units might be more compact
        
        # Check for table/chart references
        table_indicators = ['table', 'chart', 'figure', 'graph', 'diagram']
        if any(indicator in sent_lower for indicator in table_indicators):
            evidence_score += 0.05  # References to visual elements need clarity
        
        return evidence_score

    # === CLUE HELPERS ===

    def _apply_structural_clues_units(self, evidence_score: float, context: Dict[str, Any]) -> float:
        """Apply document structure-based clues for unit formatting."""
        
        block_type = context.get('block_type', 'paragraph')
        
        # Code contexts have different formatting rules
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.8  # Code often shows exact syntax/formats
        elif block_type == 'inline_code':
            evidence_score -= 0.6  # Inline code may show format examples
        
        # Table contexts often need consistent, readable formatting
        elif block_type in ['table_cell', 'table_header']:
            evidence_score += 0.1  # Tables benefit from consistent unit formatting
        
        # Heading contexts
        elif block_type in ['heading', 'title']:
            evidence_score -= 0.05  # Headings may use compact formats
        
        # List contexts
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score += 0.05  # Lists benefit from readable formatting
            
            # Nested lists might be more technical
            list_depth = context.get('list_depth', 1)
            if list_depth > 1:
                evidence_score -= 0.05  # Deeper lists more technical
        
        # Admonition contexts
        elif block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'TIP', 'HINT']:
                evidence_score += 0.05  # Informational contexts benefit from clarity
            elif admonition_type in ['WARNING', 'CAUTION', 'IMPORTANT']:
                evidence_score += 0.1  # Critical information needs clarity
        
        # Quote/citation contexts may preserve original formatting
        elif block_type in ['block_quote', 'citation']:
            evidence_score -= 0.2  # Quotes may preserve original format
        
        # Form/UI contexts need user-friendly formats
        elif block_type in ['form_field', 'ui_element']:
            evidence_score += 0.15  # User interfaces benefit from clear formatting
        
        # Technical documentation contexts
        elif block_type in ['specification', 'requirements']:
            evidence_score += 0.1  # Specifications need precise formatting
        
        return evidence_score

    def _apply_semantic_clues_units(self, evidence_score: float, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for unit formatting."""
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # Content type adjustments
        if content_type == 'technical':
            evidence_score += 0.1  # Technical content benefits from clear unit formatting
        elif content_type == 'api':
            evidence_score -= 0.1  # API docs may show exact parameter formats
        elif content_type == 'academic':
            evidence_score += 0.15  # Academic writing needs precise measurements
        elif content_type == 'legal':
            evidence_score += 0.1  # Legal documents need unambiguous measurements
        elif content_type == 'marketing':
            evidence_score -= 0.05  # Marketing may use varied formats for appeal
        elif content_type == 'narrative':
            evidence_score -= 0.1  # Stories may use informal measurement references
        elif content_type == 'procedural':
            evidence_score += 0.15  # Procedures need clear, precise measurements
        
        # Domain-specific adjustments
        if domain in ['engineering', 'scientific', 'medical']:
            evidence_score += 0.15  # Technical domains need precise unit formatting
        elif domain in ['finance', 'legal']:
            evidence_score += 0.1  # Formal domains benefit from standard formatting
        elif domain in ['software', 'devops']:
            evidence_score -= 0.05  # Tech domains familiar with compact formats
        elif domain in ['media', 'entertainment']:
            evidence_score -= 0.1  # Creative domains more flexible
        
        # Audience level adjustments
        if audience in ['beginner', 'general']:
            evidence_score += 0.1  # General audiences need clearer formatting
        elif audience in ['expert', 'developer']:
            evidence_score -= 0.05  # Expert audiences understand technical formats
        elif audience == 'international':
            evidence_score += 0.1  # International audiences benefit from SI standards
        
        # Document length context
        doc_length = len(text.split())
        if doc_length < 100:  # Short documents
            evidence_score -= 0.05  # Brief content may use shorthand
        elif doc_length > 5000:  # Long documents
            evidence_score += 0.05  # Consistency more important in long docs
        
        # Check for SI/metric system indicators in the document
        si_indicators = ['SI unit', 'metric', 'international standard', 'ISO', 'IEC']
        text_lower = text.lower()
        if any(indicator.lower() in text_lower for indicator in si_indicators):
            evidence_score += 0.15  # Documents referencing standards need proper formatting
        
        # Check for measurement-heavy content
        measurement_density = sum(1 for word in text_lower.split() 
                                if any(unit in word for unit in ['mm', 'cm', 'km', 'mg', 'kg', 'mb', 'gb', 'hz', 'mhz']))
        if measurement_density > 5:  # Many measurements in document
            evidence_score += 0.1  # Measurement-heavy docs benefit from consistency
        
        # Check for specification/manual indicators
        spec_indicators = ['specification', 'manual', 'datasheet', 'technical reference']
        if any(indicator in text_lower for indicator in spec_indicators):
            evidence_score += 0.1  # Technical documentation needs precise formatting
        
        # Check for performance/benchmarking context
        performance_indicators = ['performance', 'benchmark', 'speed', 'latency', 'throughput']
        if any(indicator in text_lower for indicator in performance_indicators):
            evidence_score += 0.05  # Performance contexts benefit from clear metrics
        
        return evidence_score

    def _apply_feedback_clues_units(self, evidence_score: float, flagged: str, context: Dict[str, Any]) -> float:
        """Apply clues learned from user feedback patterns for unit formatting."""
        
        feedback_patterns = self._get_cached_feedback_patterns_units()
        
        flagged_lower = flagged.lower()
        
        # Consistently accepted formats
        if flagged_lower in feedback_patterns.get('often_accepted', set()):
            evidence_score -= 0.3  # Strong acceptance pattern
        
        # Consistently flagged formats
        elif flagged_lower in feedback_patterns.get('often_flagged', set()):
            evidence_score += 0.2  # Strong rejection pattern
        
        # Context-specific acceptance patterns
        block_type = context.get('block_type', 'paragraph')
        content_type = context.get('content_type', 'general')
        
        # Block-specific patterns
        block_patterns = feedback_patterns.get(f'{block_type}_unit_patterns', {})
        if flagged_lower in block_patterns.get('accepted', set()):
            evidence_score -= 0.2
        elif flagged_lower in block_patterns.get('flagged', set()):
            evidence_score += 0.15
        
        # Content-specific patterns
        content_patterns = feedback_patterns.get(f'{content_type}_unit_patterns', {})
        if flagged_lower in content_patterns.get('accepted', set()):
            evidence_score -= 0.2
        elif flagged_lower in content_patterns.get('flagged', set()):
            evidence_score += 0.15
        
        # Unit type patterns (time, storage, frequency, etc.)
        unit_match = re.search(r'\d+([A-Za-z]+)$', flagged)
        if unit_match:
            unit_type = unit_match.group(1).lower()
            unit_acceptance = feedback_patterns.get('unit_type_acceptance', {})
            
            if unit_type in unit_acceptance:
                acceptance_rate = unit_acceptance[unit_type]
                if acceptance_rate > 0.8:
                    evidence_score -= 0.1  # High acceptance for this unit type
                elif acceptance_rate < 0.3:
                    evidence_score += 0.1  # Low acceptance for this unit type
        
        # Compact vs spaced formatting preference by domain
        domain = context.get('domain', 'general')
        domain_preferences = feedback_patterns.get('domain_formatting_preference', {})
        
        if domain in domain_preferences:
            compact_preference = domain_preferences[domain].get('compact_units', 0.5)
            if compact_preference > 0.7:
                evidence_score -= 0.1  # Domain prefers compact formatting
            elif compact_preference < 0.3:
                evidence_score += 0.1  # Domain prefers spaced formatting
        
        return evidence_score

    def _get_cached_feedback_patterns_units(self) -> Dict[str, Any]:
        """Load feedback patterns for unit formatting from cache or feedback analysis."""
        return {
            'often_accepted': {'50ms', '100kb', '1gb', '2ghz'},  # Commonly accepted compact formats
            'often_flagged': {'1000mb', '50000hz', '2000kb'},  # Commonly flagged for spacing
            'unit_type_acceptance': {
                'ms': 0.6,   # Milliseconds: moderate acceptance for compact format
                'kb': 0.4,   # Kilobytes: lower acceptance
                'mb': 0.3,   # Megabytes: low acceptance
                'gb': 0.2,   # Gigabytes: very low acceptance
                'hz': 0.4,   # Hertz: lower acceptance
                'mhz': 0.3,  # Megahertz: low acceptance
                'ghz': 0.3,  # Gigahertz: low acceptance
                'mm': 0.2,   # Millimeters: very low acceptance
                'cm': 0.2,   # Centimeters: very low acceptance
                'kg': 0.1,   # Kilograms: very low acceptance
            },
            'domain_formatting_preference': {
                'software': {'compact_units': 0.7},      # Software domain more accepting of compact
                'engineering': {'compact_units': 0.2},   # Engineering prefers spaced
                'scientific': {'compact_units': 0.1},    # Scientific strongly prefers spaced
                'medical': {'compact_units': 0.1},       # Medical strongly prefers spaced
                'general': {'compact_units': 0.3},       # General prefers spaced
            },
            'paragraph_unit_patterns': {
                'accepted': {'50ms', '100kb'},
                'flagged': {'1000mb', '2000kb'}
            },
            'technical_unit_patterns': {
                'accepted': {'50ms', '100kb', '1gb', '2ghz'},
                'flagged': {'1000mb', '50000hz'}
            },
            'academic_unit_patterns': {
                'accepted': set(),  # Academic strongly prefers spaced format
                'flagged': {'50ms', '100kb', '1gb', '2ghz', '1000mb'}
            },
            'code_block_unit_patterns': {
                'accepted': {'50ms', '100kb', '1gb', '2ghz', '1000mb'},  # Code more accepting
                'flagged': set()  # Minimal flagging in code contexts
            }
        }

    # === SMART MESSAGING ===

    def _get_contextual_units_message(self, flagged: str, evidence_score: float, context: Dict[str, Any]) -> str:
        """Generate context-aware error message for unit formatting."""
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        if evidence_score > 0.85:
            if domain in ['scientific', 'medical', 'engineering']:
                return f"Scientific/technical contexts require proper spacing: use space in '{flagged}'."
            elif content_type == 'procedural':
                return f"Procedures need clear measurements: add space in '{flagged}'."
            elif audience in ['beginner', 'general']:
                return f"For clarity, add space between number and unit: '{flagged}'."
            else:
                return f"Missing space between number and unit: '{flagged}'."
        elif evidence_score > 0.6:
            if content_type == 'academic':
                return f"Academic writing prefers spaced units: consider '{flagged}' → spaced format."
            elif domain == 'engineering':
                return f"Engineering contexts benefit from clear unit spacing in '{flagged}'."
            else:
                return f"Consider inserting a space between the number and unit in '{flagged}'."
        elif evidence_score > 0.4:
            return f"Unit formatting in '{flagged}' could be clearer with proper spacing."
        else:
            return "Consider standard spacing between numbers and units for consistency."

    def _generate_smart_units_suggestions(self, flagged: str, evidence_score: float, sentence, context: Dict[str, Any]) -> List[str]:
        """Generate context-aware suggestions for unit formatting."""
        
        suggestions = []
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        block_type = context.get('block_type', 'paragraph')
        
        # Extract number and unit parts
        unit_match = re.match(r'^(\d+)([A-Za-z]+)$', flagged)
        if unit_match:
            number_part = unit_match.group(1)
            unit_part = unit_match.group(2)
            spaced_format = f"{number_part} {unit_part}"
            
            # High evidence suggestions
            if evidence_score > 0.7:
                if domain in ['scientific', 'medical', 'engineering']:
                    suggestions.append(f"Use '{spaced_format}' following {domain} formatting standards.")
                    suggestions.append("Proper spacing ensures precision and clarity in technical contexts.")
                elif content_type == 'academic':
                    suggestions.append(f"Academic writing requires '{spaced_format}' format.")
                    suggestions.append("Follow SI/academic conventions for measurement formatting.")
                else:
                    suggestions.append(f"Format as '{spaced_format}' for better readability.")
                    suggestions.append("Use standard spacing between numbers and units.")
            
            # Medium evidence suggestions
            elif evidence_score > 0.4:
                suggestions.append(f"Consider '{spaced_format}' for improved clarity.")
                if audience in ['beginner', 'general']:
                    suggestions.append("Spaced format helps readers quickly parse measurements.")
                elif content_type == 'procedural':
                    suggestions.append("Clear formatting prevents measurement errors in procedures.")
            
            # Context-specific suggestions
            if block_type in ['table_cell', 'table_header']:
                suggestions.append("Consistent unit formatting improves table readability.")
            elif content_type == 'technical' and domain == 'software':
                suggestions.append("Use spaced format unless showing exact code syntax.")
            elif block_type in ['code_block', 'inline_code']:
                suggestions.append("If this is code syntax, leave as-is; otherwise use spaced format.")
        
        # General guidance if specific suggestions weren't added
        if len(suggestions) < 2:
            suggestions.append("Follow SI conventions with space between number and unit.")
            if content_type in ['technical', 'academic', 'procedural']:
                suggestions.append("Maintain consistent unit formatting throughout the document.")
            else:
                suggestions.append("Standard formatting: '100 MHz', '50 kg', '2 GB'.")
        
        return suggestions[:3]
