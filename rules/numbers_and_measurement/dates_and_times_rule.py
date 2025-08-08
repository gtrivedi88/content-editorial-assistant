"""
Dates and Times Rule
Based on IBM Style Guide topic: "Dates and times"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class DatesAndTimesRule(BaseNumbersRule):
    """
    Checks for correct and internationally understandable date and time formats.
    """
    def _get_rule_type(self) -> str:
        return 'dates_and_times'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Evidence-based analysis for dates and times:
          - Avoid ambiguous all-numeric dates; prefer '14 July 2020' or ISO 8601 in code
          - Use 'AM'/'PM' uppercase without periods (not 'am', 'a.m.')
        """
        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors
        doc = nlp(text)

        numeric_date_pattern = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b')
        am_pm_pattern = re.compile(r'\b\d{1,2}:\d{2}\s?(A\.M\.|p\.m\.|am|pm)\b')
        iso_8601_pattern = re.compile(r'\b\d{4}-\d{2}-\d{2}\b')

        for i, sent in enumerate(doc.sents):
            # Numeric dates
            for match in numeric_date_pattern.finditer(sent.text):
                flagged = match.group(0)
                span = (sent.start_char + match.start(), sent.start_char + match.end())

                ev_date = self._calculate_numeric_date_evidence(flagged, sent, text, context or {}, iso_8601_pattern)
                if ev_date > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=self._get_contextual_numeric_date_message(flagged, ev_date, context or {}),
                        suggestions=self._generate_smart_numeric_date_suggestions(flagged, ev_date, sent, context or {}),
                        severity='medium' if ev_date > 0.6 else 'low',
                        text=text,
                        context=context,
                        evidence_score=ev_date,
                        span=span,
                        flagged_text=flagged
                    ))

            # AM/PM formatting
            for match in am_pm_pattern.finditer(sent.text):
                flagged = match.group(0)
                span = (sent.start_char + match.start(), sent.start_char + match.end())

                ev_ampm = self._calculate_ampm_evidence(flagged, sent, text, context or {})
                if ev_ampm > 0.1:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=self._get_contextual_ampm_message(flagged, ev_ampm, context or {}),
                        suggestions=self._generate_smart_ampm_suggestions(flagged, ev_ampm, sent, context or {}),
                        severity='low' if ev_ampm < 0.7 else 'medium',
                        text=text,
                        context=context,
                        evidence_score=ev_ampm,
                        span=span,
                        flagged_text=flagged
                    ))
        return errors

    # === EVIDENCE CALCULATION ===

    def _calculate_numeric_date_evidence(self, flagged: str, sentence, text: str, context: Dict[str, Any], iso_pat: re.Pattern) -> float:
        """
        Calculate evidence (0.0-1.0) that a numeric date is ambiguous/inappropriate.
        
        Following the 5-step evidence calculation pattern:
        1. Base Evidence Assessment
        2. Linguistic Clues (Micro-Level)
        3. Structural Clues (Meso-Level) 
        4. Semantic Clues (Macro-Level)
        5. Feedback Patterns (Learning Clues)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        # Exempt ISO-8601 patterns (YYYY-MM-DD) used in technical/code contexts
        if iso_pat.search(flagged):
            return 0.0  # ISO format is acceptable
        
        evidence_score = 0.65  # Base evidence for all-numeric dates
        
        # Slash vs dash: slashes more ambiguous
        if '/' in flagged:
            evidence_score += 0.1
        
        # Two-digit year increases ambiguity
        if re.search(r'[/-]\d{2}$', flagged):
            evidence_score += 0.1
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_date(evidence_score, flagged, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_dates(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_dates(evidence_score, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_dates(evidence_score, flagged, context)
        
        return max(0.0, min(1.0, evidence_score))

    def _calculate_ampm_evidence(self, flagged: str, sentence, text: str, context: Dict[str, Any]) -> float:
        """
        Calculate evidence (0.0-1.0) that AM/PM formatting is incorrect.
        
        Following the 5-step evidence calculation pattern:
        1. Base Evidence Assessment
        2. Linguistic Clues (Micro-Level)
        3. Structural Clues (Meso-Level)
        4. Semantic Clues (Macro-Level) 
        5. Feedback Patterns (Learning Clues)
        """
        evidence_score = 0.0
        
        # === STEP 1: BASE EVIDENCE ASSESSMENT ===
        evidence_score = 0.6  # Base for wrong case/periods
        
        # Lowercase increases severity; periods increase severity
        if re.search(r'\b(am|pm)\b', flagged):
            evidence_score += 0.1
        if '.' in flagged:
            evidence_score += 0.1
        
        # === STEP 2: LINGUISTIC CLUES (MICRO-LEVEL) ===
        evidence_score = self._apply_linguistic_clues_ampm(evidence_score, flagged, sentence)
        
        # === STEP 3: STRUCTURAL CLUES (MESO-LEVEL) ===
        evidence_score = self._apply_structural_clues_dates(evidence_score, context)
        
        # === STEP 4: SEMANTIC CLUES (MACRO-LEVEL) ===
        evidence_score = self._apply_semantic_clues_dates(evidence_score, text, context)
        
        # === STEP 5: FEEDBACK PATTERNS (LEARNING CLUES) ===
        evidence_score = self._apply_feedback_clues_dates(evidence_score, flagged, context)
        
        return max(0.0, min(1.0, evidence_score))

    # === LINGUISTIC CLUES (MICRO-LEVEL) ===
    
    def _apply_linguistic_clues_date(self, evidence_score: float, flagged: str, sentence) -> float:
        """Apply SpaCy-based linguistic analysis clues for numeric dates."""
        
        # Check for month names nearby (reduces ambiguity)
        if re.search(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b', sentence.text, flags=re.I):
            evidence_score -= 0.15  # Month name provides context
        
        # Check for ordinal indicators (1st, 2nd, 3rd) which suggest date context
        if re.search(r'\b\d+(st|nd|rd|th)\b', sentence.text, flags=re.I):
            evidence_score -= 0.1
        
        # Check if surrounded by quotes (might be UI text or examples)
        if '"' in sentence.text or "'" in sentence.text:
            evidence_score -= 0.1
        
        # Look for temporal context words nearby
        temporal_words = ['on', 'at', 'by', 'before', 'after', 'during', 'since', 'until', 'from']
        sentence_lower = sentence.text.lower()
        if any(word in sentence_lower for word in temporal_words):
            evidence_score -= 0.05  # Temporal context suggests legitimate date
        
        # Check for contract/legal language patterns
        legal_patterns = ['effective', 'expires', 'dated', 'executed', 'signed']
        if any(pattern in sentence_lower for pattern in legal_patterns):
            evidence_score += 0.1  # Legal contexts need unambiguous dates
        
        # Check sentence structure - very short sentences might be labels/captions
        if len(sentence.text.split()) <= 5:
            evidence_score -= 0.1
        
        return evidence_score
    
    def _apply_linguistic_clues_ampm(self, evidence_score: float, flagged: str, sentence) -> float:
        """Apply SpaCy-based linguistic analysis clues for AM/PM formatting."""
        
        # If sentence shows 24-hour time as alternative, reduce
        if re.search(r'\b\d{2}:\d{2}\b', sentence.text):
            evidence_score -= 0.1
        
        # Check for schedule/timetable context (where 24-hour might be preferred)
        schedule_words = ['schedule', 'timetable', 'agenda', 'itinerary', 'program']
        sentence_lower = sentence.text.lower()
        if any(word in sentence_lower for word in schedule_words):
            evidence_score -= 0.05
        
        # Check for quotes (might be UI text where format is specified)
        if '"' in sentence.text or "'" in sentence.text:
            evidence_score -= 0.1
        
        # Check for multiple times in sentence (consistency becomes important)
        time_matches = re.findall(r'\b\d{1,2}:\d{2}\s?(AM|PM|am|pm|A\.M\.|P\.M\.|a\.m\.|p\.m\.)\b', sentence.text)
        if len(time_matches) > 1:
            # Check consistency - if all have same format, reduce evidence
            formats = [match.split()[-1] if ' ' in match else match[-4:] for match in time_matches]
            if len(set(formats)) == 1:  # All same format
                evidence_score -= 0.1
            else:  # Mixed formats - increase evidence
                evidence_score += 0.2
        
        # Meeting/appointment context
        meeting_words = ['meeting', 'appointment', 'call', 'conference', 'session']
        if any(word in sentence_lower for word in meeting_words):
            evidence_score += 0.05  # Professional contexts prefer proper AM/PM
        
        return evidence_score

    # === CLUE HELPERS ===

    def _apply_structural_clues_dates(self, evidence_score: float, context: Dict[str, Any]) -> float:
        """Apply document structure-based clues for date/time formatting."""
        
        block_type = context.get('block_type', 'paragraph')
        
        # Code contexts have different formatting rules
        if block_type in ['code_block', 'literal_block']:
            evidence_score -= 0.7  # Programming contexts often use specific formats
        elif block_type == 'inline_code':
            evidence_score -= 0.5  # Inline code may show format examples
        
        # Table contexts often need consistent, compact formatting
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.1  # Tables may use abbreviated formats
        
        # Heading contexts
        elif block_type in ['heading', 'title']:
            evidence_score -= 0.05  # Headings may use various formats
        
        # List contexts
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.05  # Lists may use shorthand
            
            # Nested lists more likely to use abbreviated formats
            list_depth = context.get('list_depth', 1)
            if list_depth > 1:
                evidence_score -= 0.05
        
        # Admonition contexts
        elif block_type == 'admonition':
            admonition_type = context.get('admonition_type', '').upper()
            if admonition_type in ['NOTE', 'TIP', 'HINT']:
                evidence_score -= 0.1  # More informal contexts
            elif admonition_type in ['WARNING', 'CAUTION', 'IMPORTANT']:
                evidence_score += 0.05  # Critical information needs clarity
        
        # Quote/citation contexts may preserve original formatting
        elif block_type in ['block_quote', 'citation']:
            evidence_score -= 0.2
        
        # Form/UI contexts need user-friendly formats
        elif block_type in ['form_field', 'ui_element']:
            evidence_score += 0.1
        
        return evidence_score

    def _apply_semantic_clues_dates(self, evidence_score: float, text: str, context: Dict[str, Any]) -> float:
        """Apply semantic and content-type clues for date/time formatting."""
        
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        
        # Content type adjustments
        if content_type == 'technical':
            evidence_score -= 0.1  # Technical content more permissive of specialized formats
        elif content_type == 'api':
            evidence_score -= 0.2  # API docs often show specific date formats
        elif content_type == 'academic':
            evidence_score += 0.05  # Academic writing prefers unambiguous formats
        elif content_type == 'legal':
            evidence_score += 0.2  # Legal documents need absolute clarity
        elif content_type == 'marketing':
            evidence_score -= 0.05  # Marketing may use varied formats for appeal
        elif content_type == 'narrative':
            evidence_score -= 0.1  # Stories may use varied date formats
        elif content_type == 'procedural':
            evidence_score += 0.1  # Procedures need clear, unambiguous dates
        
        # Domain-specific adjustments
        if domain in ['legal', 'finance', 'government']:
            evidence_score += 0.15  # Regulatory domains need precision
        elif domain in ['medical', 'scientific']:
            evidence_score += 0.1  # Medical/scientific contexts need clarity
        elif domain in ['software', 'engineering']:
            evidence_score -= 0.1  # Tech domains familiar with various formats
        elif domain in ['media', 'entertainment']:
            evidence_score -= 0.05  # Creative domains more flexible
        
        # Audience level adjustments
        if audience in ['beginner', 'general']:
            evidence_score += 0.1  # General audiences need clearer formats
        elif audience in ['expert', 'developer']:
            evidence_score -= 0.1  # Expert audiences understand technical formats
        elif audience == 'international':
            evidence_score += 0.15  # International audiences need unambiguous formats
        
        # Document length context
        doc_length = len(text.split())
        if doc_length < 100:  # Short documents
            evidence_score -= 0.05  # Brief content may use shorthand
        elif doc_length > 5000:  # Long documents
            evidence_score += 0.05  # Consistency more important in long docs
        
        # Check for internationalization indicators in the document
        intl_indicators = ['UTC', 'GMT', 'timezone', 'international', 'global', 'worldwide']
        text_lower = text.lower()
        if any(indicator in text_lower for indicator in intl_indicators):
            evidence_score += 0.1  # International context needs clear formats
        
        # Check for date format specifications in the document
        format_indicators = ['YYYY-MM-DD', 'MM/DD/YYYY', 'DD/MM/YYYY', 'ISO 8601']
        if any(indicator in text for indicator in format_indicators):
            evidence_score -= 0.2  # Document specifies acceptable formats
        
        return evidence_score

    def _apply_feedback_clues_dates(self, evidence_score: float, flagged: str, context: Dict[str, Any]) -> float:
        """Apply clues learned from user feedback patterns for date/time formatting."""
        
        feedback_patterns = self._get_cached_feedback_patterns_dates()
        
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
        block_patterns = feedback_patterns.get(f'{block_type}_date_patterns', {})
        if flagged_lower in block_patterns.get('accepted', set()):
            evidence_score -= 0.2
        elif flagged_lower in block_patterns.get('flagged', set()):
            evidence_score += 0.15
        
        # Content-specific patterns
        content_patterns = feedback_patterns.get(f'{content_type}_date_patterns', {})
        if flagged_lower in content_patterns.get('accepted', set()):
            evidence_score -= 0.2
        elif flagged_lower in content_patterns.get('flagged', set()):
            evidence_score += 0.15
        
        # Format family patterns (slashes vs dashes vs words)
        if '/' in flagged:
            slash_acceptance = feedback_patterns.get('slash_date_acceptance', 0.3)
            if slash_acceptance > 0.7:
                evidence_score -= 0.1
            elif slash_acceptance < 0.3:
                evidence_score += 0.1
        
        # AM/PM specific patterns
        ampm_match = re.search(r'(AM|PM|am|pm|A\.M\.|P\.M\.|a\.m\.|p\.m\.)', flagged)
        if ampm_match:
            ampm_format = ampm_match.group()
            ampm_patterns = feedback_patterns.get('ampm_format_acceptance', {})
            acceptance_rate = ampm_patterns.get(ampm_format, 0.5)
            
            if acceptance_rate > 0.8:
                evidence_score -= 0.2  # Highly accepted format
            elif acceptance_rate < 0.2:
                evidence_score += 0.2  # Highly rejected format
        
        return evidence_score

    def _get_cached_feedback_patterns_dates(self) -> Dict[str, Any]:
        """Load feedback patterns for date/time formatting from cache or feedback analysis."""
        return {
            'often_accepted': {'2024-01-15', '15 january 2024', 'january 15, 2024', '3:00 PM', '15:30'},
            'often_flagged': {'01/02/24', '1/2/24', '3:00 pm', '3:00 a.m.', '3:00 P.M.'},
            'slash_date_acceptance': 0.2,  # Generally low acceptance for ambiguous slash dates
            'ampm_format_acceptance': {
                'AM': 0.9, 'PM': 0.9,  # Preferred formats
                'am': 0.3, 'pm': 0.3,  # Less preferred
                'A.M.': 0.2, 'P.M.': 0.2, 'a.m.': 0.2, 'p.m.': 0.2  # Discouraged
            },
            'paragraph_date_patterns': {
                'accepted': {'january 15, 2024', '15 january 2024'},
                'flagged': {'01/15/24', '1/15/24'}
            },
            'technical_date_patterns': {
                'accepted': {'2024-01-15', 'january 15, 2024'},
                'flagged': {'01/15/2024', '1/15/2024'}
            },
            'legal_date_patterns': {
                'accepted': {'january 15, 2024', '15th day of january, 2024'},
                'flagged': {'01/15/24', '1/15/24', '01/15/2024'}
            }
        }

    # === SMART MESSAGING ===

    def _get_contextual_date_time_message(self, flagged: str, evidence_score: float, context: Dict[str, Any], message_type: str = 'date') -> str:
        """Generate context-aware error message for date/time formatting."""
        
        content_type = context.get('content_type', 'general')
        audience = context.get('audience', 'general')
        
        if message_type == 'date':
            if evidence_score > 0.85:
                if content_type == 'legal':
                    return f"Legal documents require unambiguous date formats; avoid '{flagged}'."
                elif audience == 'international':
                    return f"For international audiences, avoid ambiguous dates like '{flagged}'."
                else:
                    return "Avoid all-numeric date formats; they can be ambiguous internationally."
            elif evidence_score > 0.6:
                return f"Consider replacing '{flagged}' with an unambiguous format like '15 January 2024'."
            elif evidence_score > 0.4:
                return f"Date format '{flagged}' may be unclear for some audiences."
            else:
                return "Consider using unambiguous date formats for better clarity."
        
        else:  # AM/PM message
            if evidence_score > 0.8:
                return f"Use 'AM'/'PM' uppercase without periods instead of '{flagged.split()[-1]}'."
            elif evidence_score > 0.6:
                return f"Consider formatting time as 'AM'/'PM' (not '{flagged.split()[-1]}')."
            elif evidence_score > 0.4:
                return "Time format could be clearer with proper AM/PM formatting."
            else:
                return "Consider standard 'AM'/'PM' formatting for consistency."
    
    def _get_contextual_numeric_date_message(self, flagged: str, ev: float, context: Dict[str, Any]) -> str:
        """Legacy method - redirects to new contextual messaging."""
        return self._get_contextual_date_time_message(flagged, ev, context, 'date')

    def _generate_smart_date_time_suggestions(self, flagged: str, evidence_score: float, sentence, context: Dict[str, Any], suggestion_type: str = 'date') -> List[str]:
        """Generate context-aware suggestions for date/time formatting."""
        
        suggestions = []
        content_type = context.get('content_type', 'general')
        domain = context.get('domain', 'general')
        audience = context.get('audience', 'general')
        block_type = context.get('block_type', 'paragraph')
        
        if suggestion_type == 'date':
            # High evidence suggestions
            if evidence_score > 0.7:
                if domain in ['legal', 'finance']:
                    suggestions.append("Use full format: 'January 15, 2024' or '15 January 2024'.")
                    suggestions.append("Legal documents require unambiguous date formats.")
                elif audience == 'international':
                    suggestions.append("Use 'DD Month YYYY' format (e.g., '15 January 2024').")
                    suggestions.append("Avoid numeric formats that vary by country.")
                else:
                    suggestions.append("Use '15 January 2024' or 'January 15, 2024' format.")
                    suggestions.append("Avoid all-numeric dates that can be ambiguous.")
            
            # Medium evidence suggestions
            elif evidence_score > 0.4:
                suggestions.append("Consider '15 January 2024' for international clarity.")
                if content_type in ['technical', 'api']:
                    suggestions.append("In technical contexts, ISO 8601 (2024-01-15) is acceptable.")
            
            # Context-specific suggestions
            if block_type in ['code_block', 'inline_code']:
                suggestions.append("In code: use ISO 8601 format (YYYY-MM-DD).")
            elif content_type == 'procedural':
                suggestions.append("For procedures, use consistent date format throughout.")
            
        else:  # AM/PM suggestions
            if evidence_score > 0.6:
                suggestions.append("Use 'AM'/'PM' uppercase without periods.")
                suggestions.append("Replace with '3:00 PM' or '15:00' (24-hour time).")
            elif evidence_score > 0.3:
                suggestions.append("Consider 'AM'/'PM' format for consistency.")
            
            if content_type in ['technical', 'procedural']:
                suggestions.append("Optionally use 24-hour time (e.g., '15:30').")
        
        # General guidance if few specific suggestions
        if len(suggestions) < 2:
            if suggestion_type == 'date':
                suggestions.append("Choose unambiguous date formats for your audience.")
                suggestions.append("Maintain consistent date formatting throughout document.")
            else:
                suggestions.append("Use standard time formatting conventions.")
        
        return suggestions[:3]
    
    def _generate_smart_numeric_date_suggestions(self, flagged: str, ev: float, sentence, context: Dict[str, Any]) -> List[str]:
        """Legacy method - redirects to new suggestion generator."""
        return self._generate_smart_date_time_suggestions(flagged, ev, sentence, context, 'date')

    def _get_contextual_ampm_message(self, flagged: str, ev: float, context: Dict[str, Any]) -> str:
        """Legacy method - redirects to new contextual messaging."""
        return self._get_contextual_date_time_message(flagged, ev, context, 'ampm')

    def _generate_smart_ampm_suggestions(self, flagged: str, ev: float, sentence, context: Dict[str, Any]) -> List[str]:
        """Legacy method - redirects to new suggestion generator."""
        return self._generate_smart_date_time_suggestions(flagged, ev, sentence, context, 'ampm')
